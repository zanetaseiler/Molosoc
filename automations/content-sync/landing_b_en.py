#!/usr/bin/env python3
"""
English Landing B + CZ/EN menu links (Issue #288) — read-only `list` by default,
guarded `apply`.

What it does (production, https://molosoc.com only):

  list   (default, read-only — makes GET requests only)
         * CZ Landing B (page 1037, slug hydratacni-navleky-molosoc): exists, status, language
         * EN Landing B (proposed slug hydrating-foot-covers-molosoc): exists?, status, language,
           Polylang link to 1037 (needs the molosoc-migration-helper mu-plugin; reported, not fatal)
         * CZ menu 68 and EN menu 67: every item with its real id, parent, order, type,
           object, label and url, plus which items currently point at Landing Page A
           (CZ page 886 /cz/navleky-na-nohy/hydratacni-navlek-na-nohy/, EN page 869
           /foot-covers/moisture-lock-foot-cover/) — the candidates. Item ids are NEVER
           assumed: `apply` takes them from the operator after reading this output.
         * the plan `apply` would execute.

  apply  (needs --confirm APPLY-LANDING-B-288, --cz-menu-item <id>, --en-menu-item <id>;
          run only after a separate ZANETA_DECISION on Issue #288)
         Preflight first — if ANY check fails nothing is written:
           CZ 1037 is the expected slug, published, language cz; the Polylang helper
           endpoint answers; each menu item exists in the right menu and currently points at
           Landing A (or already at B = idempotent no-op); EN slug is free or already the EN
           draft/page (never another language).
         Then, in this order, each step verified before the next:
           1. create the EN page as a DRAFT (skipped when it exists), language must be en
           2. link it to 1037 as a Polylang CZ<->EN pair, re-read to confirm
           3. publish it, then fetch the public URL and require the EN Landing B <title>
              (proves the theme with page-hydrating-foot-covers-molosoc.php is deployed);
              on failure it is set back to draft and the run stops BEFORE any menu change
           4. repoint ONLY the two named menu items to their language's Landing B
              (page items: object_id; custom links: url). Label, parent, order, every other
              item and the language switcher are left exactly as they were; checked after.

Never: redirects, canonical/robots changes, page deletion, other menu edits, merging.
Requires WP_URL to be exactly https://molosoc.com (checked before any request) and
WP_USER / WP_APP_PASSWORD. Polylang state is read and written through the
molosoc-migration-helper mu-plugin (the free Polylang REST API does not expose it); if it is
not deployed, `apply` stops before writing anything and says how to get it deployed.
"""

import argparse
import html
import os
import re
import sys
from urllib.parse import urlparse

HOST = "molosoc.com"
CONFIRM = "APPLY-LANDING-B-288"

CZ_PAGE = {"id": 1037, "slug": "hydratacni-navleky-molosoc", "lang": "cz"}
EN_SLUG = "hydrating-foot-covers-molosoc"
EN_TITLE = "Hydrating Foot Covers – Landing Page B (EN)"
EN_DOC_TITLE_MARKER = "Reusable Hydrating Foot Mask"  # inc/landing-b-en.php document title

EN_MENU, CZ_MENU = 67, 68
# Landing Page A: the pages the menus currently point at (page ids from functions.php /
# docs/landing-page-b-580.md) and their public paths.
LANDING_A = {
    "cz": {"object_ids": {886}, "paths": {"/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/"}},
    "en": {"object_ids": {869}, "paths": {"/foot-covers/moisture-lock-foot-cover/"}},
}


def validate_url(url):
    p = urlparse(url or "")
    if p.scheme != "https" or p.hostname != HOST or p.port or p.username or p.path.strip("/") or p.query or p.fragment:
        sys.exit(f"REFUSING: WP_URL must be exactly https://{HOST}. No request was made.")


def strip_tags(text):
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def label_of(item):
    t = item.get("title")
    if isinstance(t, dict):
        return strip_tags(t.get("raw") or t.get("rendered") or "")
    return strip_tags(t or "")


def path_of(url):
    return urlparse(url or "").path


def points_at(item, lang, target):
    """True if the menu item targets the given page spec ('A' or 'B' key sets)."""
    return (
        (item.get("object") == "page" and int(item.get("object_id") or 0) in target["object_ids"])
        or path_of(item.get("url")) in target["paths"]
    )


class Abort(Exception):
    pass


class Client:
    """Thin requests wrapper; tests substitute a fake with the same methods."""

    def __init__(self, base, auth):
        import requests  # imported late so the module is importable without it

        self.requests = requests
        self.base = base
        self.auth = auth

    def get(self, path, **params):
        return self.requests.get(self.base + path, params=params or None, auth=self.auth, timeout=30)

    def post(self, path, json):
        return self.requests.post(self.base + path, json=json, auth=self.auth, timeout=60)

    def public(self, url):
        return self.requests.get(url, timeout=30, allow_redirects=False)


def ok(resp, what):
    if resp.status_code not in (200, 201):
        raise Abort(f"{what}: HTTP {resp.status_code} {resp.text[:300]}")
    return resp.json()


def get_page(c, pid):
    return ok(c.get(f"/wp-json/wp/v2/pages/{pid}", context="edit"), f"read page {pid}")


def find_page(c, slug):
    rows = ok(c.get("/wp-json/wp/v2/pages", slug=slug, status="draft,publish,future,pending,private"), f"find {slug}")
    return rows[0] if rows else None


def get_pll(c, pid):
    """(language, translations) via the helper, or None when the helper route is absent."""
    r = c.get(f"/wp-json/molosoc-migrate/v1/status/{pid}")
    if r.status_code in (404, 401, 403):
        try:
            code = r.json().get("code")
        except ValueError:
            code = None
        if code in (None, "rest_no_route"):
            return None
    d = ok(r, f"polylang status {pid}")
    return d.get("language"), (d.get("translations") or {})


def get_menu(c, menu_id):
    r = c.get("/wp-json/wp/v2/menu-items", menus=menu_id, per_page=100, context="edit")
    return sorted(ok(r, f"list menu {menu_id}"), key=lambda i: (i.get("menu_order", 0), i["id"]))


def describe(item):
    return (
        f"id={item['id']} order={item.get('menu_order')} parent={item.get('parent')} type={item.get('type')} "
        f"object={item.get('object')}#{item.get('object_id')} label={label_of(item)!r} url={item.get('url')}"
    )


def snapshot(items):
    return {i["id"]: (label_of(i), i.get("parent"), i.get("menu_order"), i.get("url"), i.get("object_id")) for i in items}


def report(c):
    """Read-only survey; returns the state apply() needs."""
    st = {}
    cz = get_page(c, CZ_PAGE["id"])
    st["cz_page"] = cz
    print(f"CZ Landing B: id={cz['id']} slug={cz.get('slug')!r} status={cz.get('status')} link={cz.get('link')}")
    en = find_page(c, EN_SLUG)
    st["en_page"] = en
    if en:
        print(f"EN Landing B (proposed slug {EN_SLUG!r}): EXISTS id={en['id']} status={en['status']} link={en.get('link')}")
    else:
        print(f"EN Landing B (proposed slug {EN_SLUG!r}): does not exist yet -> https://{HOST}/{EN_SLUG}/ would be created as a draft")
    pll_cz = get_pll(c, CZ_PAGE["id"])
    st["helper"] = pll_cz is not None
    if pll_cz is None:
        print("Polylang helper (/wp-json/molosoc-migrate/v1/status): NOT deployed — language/translation state cannot be read or linked.")
    else:
        print(f"CZ B language={pll_cz[0]!r} translations={pll_cz[1]}")
        if en:
            pll_en = get_pll(c, en["id"])
            print(f"EN B language={pll_en[0]!r} translations={pll_en[1]}")
            st["en_pll"] = pll_en
    st["pll_cz"] = pll_cz
    for lang, menu_id in (("en", EN_MENU), ("cz", CZ_MENU)):
        items = get_menu(c, menu_id)
        st[f"menu_{lang}"] = items
        print(f"\n=== {lang.upper()} menu ({menu_id}) ===")
        for it in items:
            mark = ""
            if points_at(it, lang, LANDING_A[lang]):
                mark = "   <== points at Landing Page A (candidate)"
            elif EN_SLUG in (it.get("url") or "") or CZ_PAGE["slug"] in (it.get("url") or ""):
                mark = "   <== already points at Landing Page B"
            print(describe(it) + mark)
    return st


def preflight(st, cz_item_id, en_item_id):
    """Pure checks on the report() state; returns (problems, targets)."""
    problems = []
    cz = st["cz_page"]
    if cz.get("slug") != CZ_PAGE["slug"] or cz.get("status") != "publish":
        problems.append(f"CZ page {CZ_PAGE['id']} is slug={cz.get('slug')!r} status={cz.get('status')!r}; expected a published {CZ_PAGE['slug']!r}")
    if not st["helper"]:
        problems.append(
            "Polylang helper endpoint is not deployed, so the EN page cannot be language-checked or linked to 1037. "
            "Needs Zaneta's approval to deploy molosoc-migration-helper (migrate-to-production.yml phase=deploy-helper), "
            "or link the pair in wp-admin (Languages box) and re-run. Nothing was changed."
        )
    elif st["pll_cz"][0] != "cz":
        problems.append(f"CZ page 1037 language is {st['pll_cz'][0]!r}, expected 'cz'")
    en = st["en_page"]
    if en and st["helper"] and st.get("en_pll") and st["en_pll"][0] != "en":
        problems.append(f"page with slug {EN_SLUG!r} (id {en['id']}) is language {st['en_pll'][0]!r}, expected 'en'")
    if en and st.get("en_pll"):
        linked = st["en_pll"][1].get("cz")
        if linked and int(linked) != CZ_PAGE["id"]:
            problems.append(f"EN page {en['id']} is already linked to CZ page {linked}, not {CZ_PAGE['id']}")
    targets = {}
    for lang, item_id in (("cz", cz_item_id), ("en", en_item_id)):
        items = {i["id"]: i for i in st[f"menu_{lang}"]}
        item = items.get(item_id)
        if item is None:
            problems.append(f"menu item {item_id} is not in the {lang.upper()} menu ({CZ_MENU if lang == 'cz' else EN_MENU})")
            continue
        already_b = EN_SLUG in (item.get("url") or "") or CZ_PAGE["slug"] in (item.get("url") or "")
        if not (points_at(item, lang, LANDING_A[lang]) or already_b):
            problems.append(f"{lang.upper()} menu item {item_id} does not point at Landing Page A or B: {describe(item)}")
        if not label_of(item):
            problems.append(f"{lang.upper()} menu item {item_id} has no label; refusing to repoint (the label would change)")
        targets[lang] = item
    return problems, targets


def repoint(c, item, target_id, target_url, lang):
    """Change only what the item points at; keep its label explicitly."""
    label = label_of(item)
    if item.get("type") == "post_type" and item.get("object") == "page":
        body = {"object_id": target_id, "title": label}
    else:
        body = {"url": target_url, "title": label}
    resp = c.post(f"/wp-json/wp/v2/menu-items/{item['id']}", body)
    ok(resp, f"update {lang.upper()} menu item {item['id']}")


def apply(c, st, cz_item_id, en_item_id):
    problems, targets = preflight(st, cz_item_id, en_item_id)
    if problems:
        print("PREFLIGHT FAILED — nothing was changed:")
        for p in problems:
            print("  -", p)
        return 3
    before = {lang: snapshot(st[f"menu_{lang}"]) for lang in ("cz", "en")}

    # 1. EN page (draft)
    en = st["en_page"]
    if en is None:
        en = ok(c.post("/wp-json/wp/v2/pages", {"title": EN_TITLE, "slug": EN_SLUG, "status": "draft", "content": ""}), "create EN page")
        print(f"created EN draft id={en['id']} link={en.get('link')}")
        if en.get("slug") != EN_SLUG or "/cz/" in (en.get("link") or ""):
            raise Abort(f"created page has slug={en.get('slug')!r} link={en.get('link')!r}; stopping (draft left for inspection)")
        pll = get_pll(c, en["id"])
        if pll is None or pll[0] != "en":
            raise Abort(f"new page language is {pll and pll[0]!r}, expected 'en'; stopping (draft id {en['id']} left for inspection)")
    else:
        print(f"EN page already exists id={en['id']} status={en['status']}")

    # 2. Polylang link
    translations = (get_pll(c, en["id"]) or (None, {}))[1]
    if translations.get("cz") and int(translations["cz"]) == CZ_PAGE["id"]:
        print("translation link already set")
    else:
        ok(c.post("/wp-json/molosoc-migrate/v1/link-translations", {"translations": {"cz": CZ_PAGE["id"], "en": en["id"]}}), "link translations")
        a = get_pll(c, en["id"])[1]
        b = get_pll(c, CZ_PAGE["id"])[1]
        if not (int(a.get("cz") or 0) == CZ_PAGE["id"] and int(b.get("en") or 0) == en["id"]):
            raise Abort("translation link not confirmed after write; EN page left as is, no menu touched")
        print("translation link verified")

    # 3. publish + public check
    if en["status"] != "publish":
        ok(c.post(f"/wp-json/wp/v2/pages/{en['id']}", {"status": "publish"}), "publish EN page")
    en = get_page(c, en["id"])
    page = c.public(en["link"])
    body = page.text if page.status_code == 200 else ""
    if page.status_code != 200 or EN_DOC_TITLE_MARKER not in body:
        c.post(f"/wp-json/wp/v2/pages/{en['id']}", {"status": "draft"})
        raise Abort(
            f"public check of {en['link']} failed (HTTP {page.status_code}, title marker present: {EN_DOC_TITLE_MARKER in body}). "
            "The theme with page-hydrating-foot-covers-molosoc.php is probably not deployed yet. "
            "The page was set back to draft and NO menu was changed."
        )
    print(f"EN page published and verified: {en['link']}")

    # 4. menus
    cz_url = get_page(c, CZ_PAGE["id"]).get("link")
    repoint(c, targets["cz"], CZ_PAGE["id"], cz_url, "cz")
    repoint(c, targets["en"], en["id"], en["link"], "en")

    after = {lang: snapshot(get_menu(c, mid)) for lang, mid in (("cz", CZ_MENU), ("en", EN_MENU))}
    for lang, item_id in (("cz", cz_item_id), ("en", en_item_id)):
        for iid, row in before[lang].items():
            now = after[lang].get(iid)
            if now is None:
                raise Abort(f"VERIFY FAILED: {lang.upper()} menu item {iid} disappeared")
            if iid != item_id and now != row:
                raise Abort(f"VERIFY FAILED: untouched {lang.upper()} menu item {iid} changed: {row} -> {now}")
            if iid == item_id and (now[0], now[1], now[2]) != (row[0], row[1], row[2]):
                raise Abort(f"VERIFY FAILED: {lang.upper()} item {iid} label/parent/order changed: {row} -> {now}")
        if set(after[lang]) != set(before[lang]):
            raise Abort(f"VERIFY FAILED: {lang.upper()} menu item set changed")
    print("VERIFIED: pages published + linked, only the two named menu items repointed; everything else unchanged")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("action", nargs="?", choices=("list", "apply"), default="list")
    ap.add_argument("--cz-menu-item", type=int, help="CZ menu (68) item id to repoint to CZ Landing B (from `list`)")
    ap.add_argument("--en-menu-item", type=int, help="EN menu (67) item id to repoint to EN Landing B (from `list`)")
    ap.add_argument("--confirm", default="", help=f"required for apply: {CONFIRM}")
    args = ap.parse_args(argv)

    base = os.environ.get("WP_URL", "").rstrip("/")
    validate_url(base)
    user, pw = os.environ.get("WP_USER", ""), os.environ.get("WP_APP_PASSWORD", "")
    if not (user and pw):
        sys.exit("Missing WP_USER / WP_APP_PASSWORD.")
    if args.action == "apply" and not (args.confirm == CONFIRM and args.cz_menu_item and args.en_menu_item):
        sys.exit(f"REFUSING: apply needs --cz-menu-item, --en-menu-item and --confirm {CONFIRM}. Nothing was requested.")

    c = Client(base, (user, pw))
    try:
        st = report(c)
        if args.action == "list":
            print(
                "\nPLAN (apply, only after a separate ZANETA_DECISION): create EN draft "
                f"/{EN_SLUG}/ if missing -> link to CZ {CZ_PAGE['id']} -> publish + public check -> repoint the ONE CZ "
                f"item and the ONE EN item you name (marked above) to their language's Landing B."
            )
            if not st["helper"]:
                print("BLOCKER for apply: the Polylang helper mu-plugin is not deployed (see above).")
            print("Read-only run: nothing was changed.")
            return 0
        return apply(c, st, args.cz_menu_item, args.en_menu_item)
    except Abort as e:
        print(f"ABORT: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
