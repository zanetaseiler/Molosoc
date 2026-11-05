"""Issue #343 (URGENT): the CusRev hide/restyle CSS must never hide or wrap the
Place order button.

On the live checkout the CusRev consent box (`p.cr-customer-consent` >
`input#cr_customer_consent`) is rendered INSIDE `#payment .form-row.place-order`
(within `.woocommerce-terms-and-conditions-wrapper`), next to `#place_order`.
The former selector `.form-row:has(input[name="cr_customer_consent"])` therefore
matched the whole place-order row and `display:none` hid the button.

Two layers:
- static guards on the PHP inline style and on checkout.css (no `:has()` on a
  wrapper, consent-only selectors);
- a headless-Chrome layout test (skipped when Chrome is missing): a fixture
  reproducing the live markup is rendered at 390px and 1200px with BOTH
  stylesheets applied; `#place_order` must keep a non-zero box for Comgate,
  Dobírka and Bankovní převod while `p.cr-customer-consent` is hidden. The
  fixture also proves it reproduces the bug: the old selector still matches
  the place-order row in that DOM.
"""
import html
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHP = ROOT / "site/theme/inc/checkout-cleanup.php"
CSS = ROOT / "site/theme/assets/css/checkout.css"
CHROME = shutil.which("google-chrome") or shutil.which("chromium") or next(
    (p for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",) if Path(p).exists()),
    None,
)

HIDE_SELECTORS = (
    ".woocommerce-checkout .cr-customer-consent-checkout",
    ".woocommerce-checkout #cr_customer_consent_checkout_wrap",
    ".woocommerce-checkout p.cr-customer-consent",
)
OLD_SELECTOR = '.form-row:has(input[name="cr_customer_consent"])'


def inline_hide_css():
    m = re.search(r"<style id=\"molosoc-hide-cusrev\">(.*?)</style>", PHP.read_text(encoding="utf-8"))
    assert m, "inline style missing"
    return m.group(1)


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


# Mirrors the live /cz/pokladna/ markup around the button (WooCommerce classic
# checkout + CusRev consent hooked into the terms-and-conditions wrapper).
CHECKOUT_FIXTURE = """<!doctype html><html><head><meta charset="utf-8">
<style>{checkout_css}</style>
<style id="molosoc-hide-cusrev">{hide_css}</style>
</head><body class="woocommerce-checkout woocommerce-page">
<form name="checkout" method="post" class="checkout woocommerce-checkout">
<div id="payment" class="woocommerce-checkout-payment">
<ul class="wc_payment_methods payment_methods methods">
<li class="wc_payment_method payment_method_wf_woo_comgate"><input id="payment_method_wf_woo_comgate" type="radio" class="input-radio" name="payment_method" value="wf_woo_comgate" checked><label for="payment_method_wf_woo_comgate">Kartou, Apple Pay nebo Google Pay (bez příplatku)</label></li>
<li class="wc_payment_method payment_method_cod"><input id="payment_method_cod" type="radio" class="input-radio" name="payment_method" value="cod"><label for="payment_method_cod">Dobírka</label></li>
<li class="wc_payment_method payment_method_bacs"><input id="payment_method_bacs" type="radio" class="input-radio" name="payment_method" value="bacs"><label for="payment_method_bacs">Bankovní převod (platba předem)</label></li>
</ul>
<div class="form-row place-order">
<noscript>JavaScript</noscript>
<div class="woocommerce-terms-and-conditions-wrapper">
<p class="form-row validate-required"><label class="woocommerce-form__label woocommerce-form__label-for-checkbox checkbox"><input type="checkbox" class="woocommerce-form__input woocommerce-form__input-checkbox input-checkbox" name="terms" id="terms"> <span class="woocommerce-terms-and-conditions-checkbox-text">Přečetl(a) jsem si obchodní podmínky a souhlasím s nimi</span>&nbsp;<span class="required">*</span></label></p>
<p class="cr-customer-consent"><label for="cr_customer_consent"><input type="checkbox" id="cr_customer_consent" name="cr_customer_consent" value="1"> Would you like to be invited to review your order?</label></p>
</div>
<button type="submit" class="button alt wp-element-button" name="woocommerce_checkout_place_order" id="place_order" value="Objednávka zavazující k platbě" data-value="Objednávka zavazující k platbě">Objednávka zavazující k platbě</button>
</div>
</div>
</form>
</body></html>"""

HARNESS = """<!doctype html><html><head><meta charset="utf-8"></head><body>
<iframe id="m" style="width:390px;height:900px;border:0" srcdoc="{doc}"></iframe>
<iframe id="d" style="width:1200px;height:900px;border:0" srcdoc="{doc}"></iframe>
<pre id="molosoc-result"></pre>
<script>
function probe(doc) {{
  var out = {{}};
  var radios = doc.querySelectorAll('input[name="payment_method"]');
  radios.forEach(function (r) {{
    r.checked = true;
    r.dispatchEvent(new Event('change', {{bubbles: true}}));
    var b = doc.getElementById('place_order');
    var br = b.getBoundingClientRect();
    var c = doc.querySelector('p.cr-customer-consent');
    var cr = c.getBoundingClientRect();
    var row = doc.querySelector('#payment .form-row.place-order');
    var rs = doc.defaultView.getComputedStyle(row);
    out[r.value] = {{
      button: {{w: br.width, h: br.height, display: doc.defaultView.getComputedStyle(b).display,
               visibility: doc.defaultView.getComputedStyle(b).visibility, text: b.textContent.trim()}},
      consent: {{w: cr.width, h: cr.height, display: doc.defaultView.getComputedStyle(c).display}},
      row: {{display: rs.display, border: rs.borderTopWidth, padding: rs.paddingTop}}
    }};
  }});
  var old = doc.querySelector('{old_selector}');
  out.old_selector_matches = old ? (old.className || '(no class)') : null;
  out.width = doc.documentElement.clientWidth;
  return out;
}}
window.addEventListener('load', function () {{
  var res = {{mobile: probe(document.getElementById('m').contentDocument),
             desktop: probe(document.getElementById('d').contentDocument)}};
  document.getElementById('molosoc-result').textContent = JSON.stringify(res);
}});
</script></body></html>"""


def render_fixture():
    doc = CHECKOUT_FIXTURE.format(checkout_css=CSS.read_text(encoding="utf-8"), hide_css=inline_hide_css())
    page = HARNESS.format(doc=html.escape(doc, quote=True), old_selector=OLD_SELECTOR)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "checkout.html"
        path.write_text(page, encoding="utf-8")
        out = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             "--window-size=1400,1000", "--virtual-time-budget=3000", "--dump-dom", path.as_uri()],
            capture_output=True, text=True, check=True, timeout=90,
        ).stdout
    m = re.search(r'<pre id="molosoc-result">(.*?)</pre>', out, re.S)
    assert m and m.group(1).strip(), "probe produced no result"
    return json.loads(html.unescape(m.group(1)))


class StaticGuards(unittest.TestCase):
    def test_inline_style_targets_only_consent_elements(self):
        css = inline_hide_css()
        self.assertNotIn(":has(", css)
        self.assertNotIn(".form-row", css)
        for sel in HIDE_SELECTORS:
            self.assertIn(sel, css)
        self.assertTrue(css.endswith("{display:none!important}"))

    def test_php_file_has_no_has_selector(self):
        src = PHP.read_text(encoding="utf-8")
        self.assertNotIn(OLD_SELECTOR, src.split("function molosoc_hide_cusrev_checkbox_css", 1)[1].split("add_action", 1)[0].split("echo", 1)[1])

    def test_checkout_css_has_no_wrapper_has_selector(self):
        css = strip_comments(CSS.read_text(encoding="utf-8"))
        self.assertNotIn(":has(", css)
        self.assertNotIn(".form-row", css)
        self.assertIn(".woocommerce-checkout p.cr-customer-consent {", css)

    def test_hidden_rule_still_opt_in(self):
        fn = PHP.read_text(encoding="utf-8").split("function molosoc_hide_cusrev_checkbox_css", 1)[1].split("add_action", 1)[0]
        self.assertIn("'molosoc_hide_cusrev_checkbox', '0'", fn)
        self.assertIn("is_checkout()", fn)


@unittest.skipUnless(CHROME, "Chrome not available")
class PlaceOrderVisible(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = render_fixture()

    def test_fixture_reproduces_the_bug(self):
        # The old selector would have matched the place-order row in this DOM.
        for vp in ("mobile", "desktop"):
            self.assertIn("place-order", self.res[vp]["old_selector_matches"] or "")

    def test_viewports(self):
        self.assertLessEqual(self.res["mobile"]["width"], 390)
        self.assertGreaterEqual(self.res["desktop"]["width"], 1100)

    def test_place_order_visible_for_all_methods_consent_hidden(self):
        for vp in ("mobile", "desktop"):
            methods = [k for k in self.res[vp] if k not in ("old_selector_matches", "width")]
            self.assertEqual(sorted(methods), ["bacs", "cod", "wf_woo_comgate"])
            for m in methods:
                r = self.res[vp][m]
                with self.subTest(viewport=vp, method=m):
                    self.assertGreater(r["button"]["w"], 0)
                    self.assertGreater(r["button"]["h"], 0)
                    self.assertNotEqual(r["button"]["display"], "none")
                    self.assertEqual(r["button"]["visibility"], "visible")
                    self.assertEqual(r["button"]["text"], "Objednávka zavazující k platbě")
                    self.assertEqual(r["consent"]["display"], "none")
                    self.assertEqual(r["consent"]["w"], 0)
                    self.assertNotEqual(r["row"]["display"], "none")
                    # the #331 restyle box must not be painted around the place-order row
                    self.assertEqual(r["row"]["border"], "0px")


if __name__ == "__main__":
    unittest.main()
