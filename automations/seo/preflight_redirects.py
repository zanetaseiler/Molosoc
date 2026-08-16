#!/usr/bin/env python3
"""
READ-ONLY pre-flight for the Step 3A legacy-URL retirement.

Makes no change of any kind: every HTTP call is a GET, every WordPress call
is a GET, and nothing is written to the site, the database, the Redirection
plugin, Search Console or the sitemap. Running this twice is identical to
running it once.

It answers, per mapping in redirect-map.json:

  * what the legacy URL does today — the FULL redirect chain, hop by hop
  * whether the destination is a DIRECT 200 and not itself a redirect
  * the destination's canonical and hreflang tags
  * whether a proposed rule would create a chain or a loop against the
    rules that already exist
  * which pages/posts still link to the legacy URL internally
  * whether the legacy URL appears in the sitemap

and site-wide:

  * every rule currently in the Redirection plugin
  * whether WordPress or Polylang already redirects the URL on its own
  * a content comparison for the conditional /blog-legacy-2018/ mapping

Exit codes: 0 = report produced (read it), 1 = could not complete.
A mapping being unsafe is NOT an error exit — it is reported as AMBIGUOUS
and the report is still printed in full.
"""

import html
import json
import os
import re
import sys
from urllib.parse import urljoin, urlparse

import requests

TIMEOUT = 30
MAX_HOPS = 10
UA = "molosoc-seo-preflight/1.0 (read-only)"

VERDICT_OK = "OK"
VERDICT_AMBIGUOUS = "AMBIGUOUS"
VERDICT_ALREADY = "ALREADY-DONE"


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def session():
    s = requests.Session()
    s.headers["User-Agent"] = UA
    return s


def trace(sess, url):
    """Walk the redirect chain one hop at a time.

    requests' allow_redirects would collapse this into a final answer; the
    whole point here is the shape of the path, because a two-hop chain and a
    one-hop redirect look identical from the destination.
    """
    chain = []
    current = url
    seen = set()
    for _ in range(MAX_HOPS):
        if current in seen:
            chain.append({"url": current, "status": "LOOP", "location": None})
            return chain, "loop"
        seen.add(current)
        try:
            r = sess.get(current, allow_redirects=False, timeout=TIMEOUT)
        except requests.RequestException as exc:
            chain.append({"url": current, "status": f"ERROR {type(exc).__name__}",
                          "location": None})
            return chain, "error"
        location = r.headers.get("Location")
        chain.append({"url": current, "status": r.status_code, "location": location})
        if r.status_code in (301, 302, 303, 307, 308) and location:
            current = urljoin(current, location)
            continue
        return chain, "final"
    chain.append({"url": current, "status": "MAX-HOPS", "location": None})
    return chain, "too-long"


def describe(chain):
    return " -> ".join(
        f"{path_of(h['url'])} [{h['status']}]" for h in chain
    )


def path_of(url):
    p = urlparse(url)
    return (p.path or "/") + (f"?{p.query}" if p.query else "")


def hops(chain):
    """Number of redirect responses in the chain."""
    return sum(1 for h in chain if isinstance(h["status"], int)
               and 300 <= h["status"] < 400)


def final_status(chain):
    last = chain[-1]["status"]
    return last if isinstance(last, int) else None


# --------------------------------------------------------------------------
# HTML facts
# --------------------------------------------------------------------------

CANONICAL_RE = re.compile(
    r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', re.I)
CANONICAL_RE_ALT = re.compile(
    r'<link[^>]+href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', re.I)
HREFLANG_RE = re.compile(
    r'<link[^>]+hreflang=["\']([^"\']+)["\'][^>]*href=["\']([^"\']+)["\']', re.I)
HREFLANG_RE_ALT = re.compile(
    r'<link[^>]+href=["\']([^"\']+)["\'][^>]*hreflang=["\']([^"\']+)["\']', re.I)
ROBOTS_RE = re.compile(
    r'<meta[^>]+name=["\']robots["\'][^>]*content=["\']([^"\']+)["\']', re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def page_facts(sess, url):
    """Canonical, hreflang, robots and title for a URL, following redirects."""
    try:
        r = sess.get(url, allow_redirects=True, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
    body = r.text

    canonical = None
    m = CANONICAL_RE.search(body) or CANONICAL_RE_ALT.search(body)
    if m:
        canonical = html.unescape(m.group(1))

    hreflang = {}
    for lang, href in HREFLANG_RE.findall(body):
        hreflang[lang] = html.unescape(href)
    for href, lang in HREFLANG_RE_ALT.findall(body):
        hreflang.setdefault(lang, html.unescape(href))

    robots = None
    m = ROBOTS_RE.search(body)
    if m:
        robots = m.group(1)

    title = None
    m = TITLE_RE.search(body)
    if m:
        title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()

    return {
        "final_url": r.url,
        "status": r.status_code,
        "canonical": canonical,
        "hreflang": hreflang,
        "robots": robots,
        "title": title,
        "bytes": len(body),
        "text_len": len(strip_tags(body)),
        "body": body,
    }


def strip_tags(body):
    body = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", body)
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", body)).strip()


# --------------------------------------------------------------------------
# WordPress (authenticated GETs only)
# --------------------------------------------------------------------------

def wp_get(sess, base, path, auth, **params):
    url = f"{base.rstrip('/')}/wp-json/{path.lstrip('/')}"
    try:
        r = sess.get(url, auth=auth, params=params, timeout=TIMEOUT)
    except requests.RequestException as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"
    try:
        return r.json(), None
    except ValueError:
        return None, "non-JSON response"


def redirection_rules(sess, base, auth):
    """Every rule the Redirection plugin currently holds."""
    data, err = wp_get(sess, base, "redirection/v1/redirect", auth, per_page=200)
    if err:
        return None, err
    rules = []
    for r in data.get("items", []):
        rules.append({
            "id": r.get("id"),
            "enabled": r.get("enabled"),
            "source": r.get("url"),
            "target": (r.get("action_data") or {}).get("url"),
            "code": r.get("action_code"),
            "hits": r.get("hits"),
            "group": r.get("group_id"),
        })
    return rules, None


def search_internal_links(sess, base, auth, needles):
    """Published content whose HTML still contains a legacy path.

    Uses the REST search parameter, then confirms by substring against the
    rendered content — search alone matches loosely and would over-report.
    """
    found = {n: [] for n in needles}
    for post_type in ("pages", "posts"):
        page = 1
        while page <= 10:
            data, err = wp_get(sess, base, f"wp/v2/{post_type}", auth,
                               per_page=100, page=page, status="publish",
                               _fields="id,link,title,content,slug")
            if err or not data:
                break
            for item in data:
                content = ((item.get("content") or {}).get("rendered") or "")
                for needle in needles:
                    if needle in content:
                        found[needle].append({
                            "type": post_type,
                            "id": item.get("id"),
                            "slug": item.get("slug"),
                            "link": item.get("link"),
                            "title": ((item.get("title") or {}).get("rendered") or "")[:80],
                        })
            if len(data) < 100:
                break
            page += 1
    return found


# --------------------------------------------------------------------------
# Sitemap
# --------------------------------------------------------------------------

SITEMAP_CANDIDATES = ("/wp-sitemap.xml", "/sitemap_index.xml", "/sitemap.xml")
LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)


def sitemap_urls(sess, site):
    """Every URL in the sitemap, following one level of index nesting."""
    for candidate in SITEMAP_CANDIDATES:
        url = site.rstrip("/") + candidate
        try:
            r = sess.get(url, timeout=TIMEOUT)
        except requests.RequestException:
            continue
        if r.status_code != 200 or "<" not in r.text:
            continue
        locs = LOC_RE.findall(r.text)
        if "sitemapindex" in r.text[:2000].lower():
            all_urls = []
            for sub in locs[:50]:
                try:
                    rs = sess.get(sub, timeout=TIMEOUT)
                except requests.RequestException:
                    continue
                if rs.status_code == 200:
                    all_urls.extend(LOC_RE.findall(rs.text))
            return url, all_urls
        return url, locs
    return None, []


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------

def rule_index(rules):
    by_source = {}
    for r in rules or []:
        by_source.setdefault(normalize_path(r["source"]), []).append(r)
    return by_source


def normalize_path(path):
    if not path:
        return path
    p = path if path.startswith("/") else "/" + path
    if not p.endswith("/") and "." not in p.rsplit("/", 1)[-1]:
        p += "/"
    return p


def analyse(mapping, live, dest, rules_by_source, sitemap):
    """Decide whether this mapping is safe to implement as-is."""
    src = normalize_path(mapping["source"])
    tgt = normalize_path(mapping["target"])
    problems = []
    notes = []

    # 1. Does a rule already exist for this source?
    existing = rules_by_source.get(src, [])
    for r in existing:
        if normalize_path(r["target"]) == tgt:
            notes.append(f"rule id={r['id']} already maps {src} -> {tgt} "
                         f"(enabled={r['enabled']}, {r['hits']} hits)")
        else:
            problems.append(f"CONFLICT: rule id={r['id']} already maps {src} -> "
                            f"{r['target']!r}, which is NOT the proposed target")

    # 2. THE LOOP CHECK: does anything redirect the target back to the source?
    for r in rules_by_source.get(tgt, []):
        if normalize_path(r["target"]) == src:
            problems.append(
                f"LOOP: rule id={r['id']} maps {tgt} -> {src}. Adding "
                f"{src} -> {tgt} would create an infinite redirect.")
        else:
            problems.append(
                f"CHAIN: the target {tgt} is itself a redirect source "
                f"(rule id={r['id']} -> {r['target']!r}), so this would be multi-hop")

    # 3. Destination must be a direct 200, not a redirect.
    dest_hops = hops(dest["chain"])
    dest_status = final_status(dest["chain"])
    if dest_status != 200:
        problems.append(f"destination does not return 200 (got {dest_status})")
    if dest_hops:
        problems.append(f"destination itself redirects ({dest_hops} hop(s)): "
                        f"{describe(dest['chain'])}")

    # 4. Destination must not be noindexed.
    robots = (dest["facts"].get("robots") or "").lower()
    if "noindex" in robots:
        problems.append(f"destination carries robots={robots!r}")

    # 5. Destination canonical should be self-referencing.
    canonical = dest["facts"].get("canonical")
    if canonical:
        if normalize_path(urlparse(canonical).path) != tgt:
            problems.append(f"destination canonical points elsewhere: {canonical}")
    else:
        notes.append("destination has no canonical tag")

    # 6. What does the legacy URL do today?
    live_status = final_status(live["chain"])
    live_hops = hops(live["chain"])
    if live_hops:
        landing = normalize_path(urlparse(live["chain"][-1]["url"]).path)
        if landing == tgt and live_hops == 1:
            notes.append("already a single-hop 301 to the target — nothing to do")
        else:
            notes.append(f"already redirects: {describe(live['chain'])}")
    elif live_status == 404:
        notes.append("currently 404 — redirecting it still recovers any residual "
                     "link equity and stops the soft-404 signal")
    elif live_status == 200:
        notes.append("currently live with its own 200 — this is the duplicate "
                     "being retired")

    # 7. Sitemap presence.
    in_sitemap = [u for u in sitemap if normalize_path(urlparse(u).path) == src]
    if in_sitemap:
        notes.append(f"listed in sitemap ({len(in_sitemap)} entry) — needs cleanup later")

    if problems:
        verdict = VERDICT_AMBIGUOUS
    elif any("nothing to do" in n for n in notes):
        verdict = VERDICT_ALREADY
    else:
        verdict = VERDICT_OK
    return verdict, problems, notes, bool(in_sitemap)


def compare_content(legacy, target):
    """Evidence for the conditional /blog-legacy-2018/ decision.

    Deliberately reports measurements and does not decide. Whether unique
    content would be lost is a judgement a human should be able to check.
    """
    lt = strip_tags(legacy.get("body", ""))
    tt = strip_tags(target.get("body", ""))
    lw = set(re.findall(r"\w{5,}", lt.lower()))
    tw = set(re.findall(r"\w{5,}", tt.lower()))
    only_legacy = lw - tw
    overlap = (len(lw & tw) / len(lw)) if lw else 0.0
    return {
        "legacy_text_chars": len(lt),
        "target_text_chars": len(tt),
        "legacy_vocab": len(lw),
        "shared_vocab_ratio": round(overlap, 3),
        "words_only_on_legacy": sorted(only_legacy)[:60],
        "words_only_on_legacy_count": len(only_legacy),
        "legacy_title": legacy.get("title"),
        "target_title": target.get("title"),
        "legacy_excerpt": lt[:600],
    }


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "redirect-map.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)

    base = (os.environ.get("WP_URL") or cfg["site"]).rstrip("/")
    site = cfg["site"].rstrip("/")
    user = os.environ.get("WP_USER", "")
    password = os.environ.get("WP_APP_PASSWORD", "")
    auth = (user, password) if user and password else None

    sess = session()

    print("=" * 74)
    print("STEP 3A PRE-FLIGHT — READ-ONLY. Nothing is modified by this run.")
    print("=" * 74)
    print(f"Site: {site}")
    print(f"WordPress REST: {'authenticated' if auth else 'ANONYMOUS (limited)'}")

    # --- Redirection plugin rules -----------------------------------------
    print("\n" + "-" * 74)
    print("EXISTING REDIRECTION PLUGIN RULES")
    print("-" * 74)
    rules, err = (None, "no credentials") if not auth else redirection_rules(sess, base, auth)
    if err:
        print(f"  could not read rules: {err}")
        print("  !! Loop/chain detection is UNRELIABLE without this. Treat every")
        print("     mapping as AMBIGUOUS until the rule list can be read.")
        rules = None
    else:
        if not rules:
            print("  (none)")
        for r in sorted(rules, key=lambda x: str(x["source"])):
            flag = "" if r["enabled"] else "  [DISABLED]"
            print(f"  id={r['id']:<5} {r['source']!r} -> {r['target']!r} "
                  f"({r['code']}, {r['hits']} hits){flag}")
    by_source = rule_index(rules)

    # --- sitemap -----------------------------------------------------------
    print("\n" + "-" * 74)
    print("SITEMAP")
    print("-" * 74)
    sm_url, sm_urls = sitemap_urls(sess, site)
    print(f"  sitemap: {sm_url or 'NOT FOUND'} ({len(sm_urls)} URLs)")

    # --- per-mapping -------------------------------------------------------
    results = []
    for m in cfg["mappings"]:
        src_url = site + m["source"]
        tgt_url = site + m["target"]

        live_chain, _ = trace(sess, src_url)
        dest_chain, _ = trace(sess, tgt_url)
        live = {"chain": live_chain, "facts": page_facts(sess, src_url)}
        dest = {"chain": dest_chain, "facts": page_facts(sess, tgt_url)}

        verdict, problems, notes, in_sitemap = analyse(
            m, live, dest, by_source, sm_urls)
        if rules is None:
            verdict = VERDICT_AMBIGUOUS
            problems = ["Redirection rules unreadable — cannot rule out a loop"] + problems

        results.append({"m": m, "verdict": verdict, "problems": problems,
                        "notes": notes, "live": live, "dest": dest,
                        "in_sitemap": in_sitemap})

        print("\n" + "-" * 74)
        cond = "  (CONDITIONAL)" if m.get("conditional") else ""
        print(f"[{m['id']}] {m['source']}  ->  {m['target']}{cond}")
        print("-" * 74)
        print(f"  verdict: {verdict}")
        print(f"  legacy today : {describe(live_chain)}")
        print(f"  destination  : {describe(dest_chain)}  "
              f"(hops={hops(dest_chain)})")
        df = dest["facts"]
        print(f"  dest title   : {df.get('title')!r}")
        print(f"  dest canonical: {df.get('canonical')}")
        print(f"  dest robots  : {df.get('robots')}")
        if df.get("hreflang"):
            for lang, href in sorted(df["hreflang"].items()):
                print(f"  dest hreflang: {lang} -> {href}")
        else:
            print("  dest hreflang: (none)")
        for n in notes:
            print(f"  note: {n}")
        for p in problems:
            print(f"  ** {p}")

    # --- conditional content comparison -----------------------------------
    conditional = [r for r in results if r["m"].get("conditional")]
    for r in conditional:
        print("\n" + "=" * 74)
        print(f"CONTENT COMPARISON for {r['m']['source']} (conditional mapping)")
        print("=" * 74)
        cmp = compare_content(r["live"]["facts"], r["dest"]["facts"])
        for k in ("legacy_title", "target_title", "legacy_text_chars",
                  "target_text_chars", "legacy_vocab", "shared_vocab_ratio",
                  "words_only_on_legacy_count"):
            print(f"  {k}: {cmp[k]}")
        print(f"  words appearing ONLY on the legacy page (first 60):")
        print(f"    {', '.join(cmp['words_only_on_legacy']) or '(none)'}")
        print(f"  legacy visible text, first 600 chars:")
        print(f"    {cmp['legacy_excerpt']!r}")

    # --- internal links ----------------------------------------------------
    print("\n" + "=" * 74)
    print("INTERNAL LINKS STILL POINTING AT LEGACY URLS (report only, not fixed)")
    print("=" * 74)
    if not auth:
        print("  skipped — needs WordPress credentials")
    else:
        needles = [m["source"] for m in cfg["mappings"]]
        found = search_internal_links(sess, base, auth, needles)
        for needle in needles:
            hits = found.get(needle) or []
            print(f"\n  {needle}  — {len(hits)} page(s)/post(s)")
            for h in hits:
                print(f"    {h['type']} id={h['id']} {h['link']}")

    # --- summary -----------------------------------------------------------
    print("\n" + "=" * 74)
    print("SUMMARY")
    print("=" * 74)
    for r in results:
        m = r["m"]
        print(f"  [{m['id']}] {r['verdict']:<12} {m['source']} -> {m['target']}")
    safe = [r for r in results
            if r["verdict"] == VERDICT_OK and not r["m"].get("conditional")]
    print(f"\n  unconditional mappings safe to implement: "
          f"{[r['m']['id'] for r in safe]}")
    print("  NOTHING HAS BEEN CHANGED. This was a read-only pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
