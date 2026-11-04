#!/usr/bin/env node
/**
 * Issue #343 live smoke: on /cz/pokladna/ (logged-out guest, one pair in the
 * cart) the Place order button („Objednávka zavazující k platbě“, #place_order)
 * must be visible (width > 0, height > 0, not display:none) for every payment
 * method (Card/Comgate, Dobírka, Bankovní převod), and the CusRev consent box
 * (p.cr-customer-consent) must stay hidden. Checked at 390px (mobile) and
 * 1280px (desktop). Exit code 1 on any failure. The cart is emptied afterwards;
 * no order is placed.
 *
 * Dependency-free: Node 22 (global WebSocket) + local Chrome over CDP.
 *
 *   node scripts/checkout_place_order_smoke.mjs [--base https://molosoc.com]
 *        [--variation 425] [--shots DIR] [--chrome "/path/to/chrome"]
 */
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith("--") ? [...a, [v.slice(2), arr[i + 1]]] : a), []),
);
const BASE = (args.base || "https://molosoc.com").replace(/\/$/, "");
const VARIATION = Number(args.variation || 425); // MOLOSOC Moisture Lock Foot Cover, M
const SHOTS = args.shots || "";
const CHROME =
  args.chrome ||
  ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/usr/bin/google-chrome", "/usr/bin/chromium"].find(existsSync);
if (!CHROME) {
  console.error("Chrome not found; pass --chrome");
  process.exit(2);
}
const PORT = 9300 + Math.floor(Math.random() * 300);
const profile = mkdtempSync(join(tmpdir(), "molosoc-smoke-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`, "about:blank",
], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function cdp() {
  let info;
  for (let i = 0; i < 50; i++) {
    try { info = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json(); break; } catch { await sleep(200); }
  }
  if (!info) throw new Error("Chrome did not start");
  const ws = new WebSocket(info.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pending = new Map(); const events = [];
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pending.has(d.id)) { const { res, rej } = pending.get(d.id); pending.delete(d.id); d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result); }
    else if (d.method) events.push(d);
  };
  const send = (method, params = {}, sessionId) => new Promise((res, rej) => {
    const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params, sessionId }));
  });
  return { send, events, close: () => ws.close() };
}

async function main() {
  const { send, events, close } = await cdp();
  const { targetId } = await send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
  const s = (m, p) => send(m, p, sessionId);
  await s("Page.enable"); await s("Runtime.enable");
  const evaluate = async (expression) => {
    const r = await s("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.text + " " + JSON.stringify(r.exceptionDetails.exception));
    return r.result.value;
  };
  const navigate = async (url) => {
    const before = events.length;
    await s("Page.navigate", { url });
    for (let i = 0; i < 150; i++) { if (events.slice(before).some((e) => e.method === "Page.loadEventFired")) break; await sleep(200); }
    await sleep(800);
  };
  const setViewport = (w, h, mobile) => s("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: mobile ? 2 : 1, mobile });
  const shot = async (name) => {
    if (!SHOTS) return;
    mkdirSync(SHOTS, { recursive: true });
    const { data } = await s("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    writeFileSync(join(SHOTS, name), Buffer.from(data, "base64"));
  };

  await setViewport(390, 844, true);
  await navigate(`${BASE}/cz/`);
  // Guest cart via the Store API (same-origin fetch keeps the woocommerce session cookie).
  const added = await evaluate(`(async () => {
    const r0 = await fetch('/wp-json/wc/store/v1/cart'); const nonce = r0.headers.get('Nonce');
    const r = await fetch('/wp-json/wc/store/v1/cart/add-item', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Nonce': nonce }, body: JSON.stringify({ id: ${VARIATION}, quantity: 1 }) });
    const j = await r.json(); return { status: r.status, count: j.items_count, nonce: !!nonce, msg: j.message };
  })()`);
  if (added.status !== 201 && added.status !== 200) throw new Error("add-item failed: " + JSON.stringify(added));

  const results = {}; let ok = true;
  for (const [vp, w, h, mobile] of [["mobile", 390, 844, true], ["desktop", 1280, 900, false]]) {
    await setViewport(w, h, mobile);
    await navigate(`${BASE}/cz/pokladna/`);
    // Reject the WPConsent banner so screenshots show the checkout (shadow DOM; harmless if absent).
    await evaluate(`(() => { const h = document.getElementById('wpconsent-container'); const b = h && h.shadowRoot && h.shadowRoot.getElementById('wpconsent-cancel-all'); if (b) b.click(); return !!b; })()`);
    await sleep(500);
    const r = await evaluate(`(async () => {
      const out = { url: location.href, hideStyle: (document.getElementById('molosoc-hide-cusrev') || {}).textContent || null, methods: {} };
      const radios = [...document.querySelectorAll('input[name="payment_method"]')];
      for (const radio of radios) {
        radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
        await new Promise((r) => setTimeout(r, 700));
        const b = document.getElementById('place_order'); const br = b ? b.getBoundingClientRect() : { width: 0, height: 0 };
        const c = document.querySelector('p.cr-customer-consent, .cr-customer-consent-checkout, #cr_customer_consent_checkout_wrap');
        const cs = c ? getComputedStyle(c) : null; const cr = c ? c.getBoundingClientRect() : null;
        const consentInput = document.querySelector('input[name="cr_customer_consent"]');
        out.methods[radio.value] = {
          label: (document.querySelector('label[for="' + radio.id + '"]') || {}).textContent?.trim().slice(0, 40),
          button: b ? { w: br.width, h: br.height, display: getComputedStyle(b).display, visibility: getComputedStyle(b).visibility, text: b.textContent.trim() } : null,
          consent: c ? { display: cs.display, w: cr.width, h: cr.height, inPlaceOrderRow: !!c.closest('.form-row.place-order') } : null,
          consentInputChecked: consentInput ? consentInput.checked : null,
        };
      }
      return out;
    })()`);
    results[vp] = r;
    for (const [m, d] of Object.entries(r.methods)) {
      const pass = d.button && d.button.w > 0 && d.button.h > 0 && d.button.display !== "none" && d.button.visibility === "visible" && (!d.consent || d.consent.display === "none") && d.consentInputChecked !== true;
      if (!pass) ok = false;
      console.log(`${pass ? "PASS" : "FAIL"} ${vp.padEnd(7)} ${m.padEnd(16)} button=${d.button ? `${Math.round(d.button.w)}x${Math.round(d.button.h)} ${d.button.display}` : "MISSING"} consent=${d.consent ? d.consent.display : "absent"}`);
    }
    const values = Object.keys(r.methods);
    const expected = { comgate: values.some((v) => v.includes("comgate")), cod: values.includes("cod"), bacs: values.includes("bacs") };
    for (const [k, v] of Object.entries(expected)) if (!v) { ok = false; console.log(`FAIL ${vp} payment method '${k}' not offered (${values.join(", ")})`); }
    await shot(`checkout-${vp}.png`);
  }
  console.log("inline molosoc-hide-cusrev:", results.desktop.hideStyle);
  // Empty the guest cart.
  await evaluate(`(async () => { const r0 = await fetch('/wp-json/wc/store/v1/cart'); const nonce = r0.headers.get('Nonce'); const r = await fetch('/wp-json/wc/store/v1/cart/items', { method: 'DELETE', headers: { 'Nonce': nonce } }); return r.status; })()`);
  close();
  console.log(ok ? "RESULT: PASS" : "RESULT: FAIL");
  process.exitCode = ok ? 0 : 1;
}

main().catch((e) => { console.error("ERROR", e); process.exitCode = 1; }).finally(() => chrome.kill());
