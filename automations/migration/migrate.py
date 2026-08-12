#!/usr/bin/env python3
"""Staging -> production content migration for Molosoc.

Reads pages from staging (read-only) and creates/updates them on
production via the WP REST API plus the temporary molosoc-migrate/v1
helper endpoints. Idempotent: pages are matched by slug+parent on every
run, so re-running a phase is safe.

Phases (run in order):
  pages-en   rename prod page 24 blog->blog-legacy-2018, create/update EN pages, set lang=en
  pages-cz   create/update CZ pages, set lang=cz
  link       link EN<->CZ translation pairs from translation-map.json
  menus      create both menus + items, assign primary location per language
  frontpage  point page_on_front at the new homepage
  verify     read-only comparison of production against staging

Env: WP_URL/WP_USER/WP_APP_PASSWORD (staging, read-only),
     PROD_WP_URL/PROD_WP_USER/PROD_WP_APP_PASSWORD (production).
"""

import json
import os
import re
import sys
import time
import urllib.parse

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
TR_MAP = json.load(open(os.path.join(HERE, "translation-map.json")))

STAGING = os.environ["WP_URL"].rstrip("/")
PROD = os.environ["PROD_WP_URL"].rstrip("/")
S_AUTH = (os.environ["WP_USER"], os.environ["WP_APP_PASSWORD"])
P_AUTH = (os.environ["PROD_WP_USER"], os.environ["PROD_WP_APP_PASSWORD"])

# Staging page IDs in dependency order (parents before children).
EN_PAGES = [953, 949, 951, 982, 1012, 1013, 1014, 993, 1009, 1010, 995,
            1000, 1001, 1011, 1021, 1025, 1026]
CZ_PAGES = [1032, 1035, 1039, 1036, 1040, 1041, 1037, 1038, 1061, 1062,
            1066, 1067]

session = requests.Session()
session.headers["User-Agent"] = "molosoc-migration/1.0"


def req(method, base, auth, path, retries=5, **kw):
    """Request with retries for the host's intermittent firewall blocks."""
    url = f"{base}/wp-json/{path.lstrip('/')}"
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = session.request(method, url, auth=auth, timeout=60, **kw)
            if r.status_code < 500 and r.text.strip():
                return r
            last = f"HTTP {r.status_code}: {r.text[:200]}"
        except requests.RequestException as e:
            last = str(e)
        print(f"  retry {attempt}/{retries} {method} {path}: {last}")
        time.sleep(10 * attempt)
    sys.exit(f"FATAL: {method} {url} failed after {retries} tries: {last}")


def jget(base, auth, path, **kw):
    r = req("GET", base, auth, path, **kw)
    return r.json()


def staging_page(sid):
    return jget(STAGING, S_AUTH, f"wp/v2/pages/{sid}?context=edit")


def prod_pages_all():
    out, page = [], 1
    while True:
        r = req("GET", PROD, P_AUTH,
                f"wp/v2/pages?status=any&per_page=100&page={page}&context=edit"
                "&_fields=id,slug,parent,status,title,template,menu_order")
        batch = r.json()
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def build_idmap():
    """staging page id -> prod page id, matched by slug (+parent chain)."""
    sp = {p: staging_page(p) for p in EN_PAGES + CZ_PAGES}
    prod = prod_pages_all()
    by_slug = {}
    for p in prod:
        by_slug.setdefault(p["slug"], []).append(p)
    idmap = {20: 20, 22: 22, 24: 24, 213: 213, 220: 220}  # shared legacy IDs
    for sid, s in sp.items():
        cands = by_slug.get(s["slug"], [])
        if len(cands) == 1:
            idmap[sid] = cands[0]["id"]
        elif len(cands) > 1:
            want_parent = idmap.get(s["parent"], 0)
            match = [c for c in cands if c["parent"] == want_parent]
            if len(match) == 1:
                idmap[sid] = match[0]["id"]
    return sp, idmap


def helper(path, payload):
    r = req("POST", PROD, P_AUTH, f"molosoc-migrate/v1/{path}", json=payload)
    if r.status_code != 200:
        sys.exit(f"FATAL helper {path}: HTTP {r.status_code} {r.text[:300]}")
    return r.json()


def upsert_pages(staging_ids, lang):
    sp, idmap = build_idmap()
    for sid in staging_ids:
        s = sp[sid]
        body = {
            "slug": s["slug"],
            "title": s["title"]["raw"],
            "content": s["content"]["raw"].replace(STAGING, PROD),
            "status": s["status"],
            "parent": idmap.get(s["parent"], 0) if s["parent"] else 0,
            "menu_order": s["menu_order"],
            "template": s.get("template") or "",
            "comment_status": s.get("comment_status", "closed"),
            "ping_status": s.get("ping_status", "closed"),
        }
        if s.get("featured_media"):
            body["featured_media"] = s["featured_media"]  # media 64 exists on prod
        if sid in idmap:
            pid = idmap[sid]
            r = req("POST", PROD, P_AUTH, f"wp/v2/pages/{pid}", json=body)
            action = "UPDATE"
        else:
            r = req("POST", PROD, P_AUTH, "wp/v2/pages", json=body)
            action = "CREATE"
        if r.status_code not in (200, 201):
            sys.exit(f"FATAL {action} {s['slug']}: HTTP {r.status_code} {r.text[:300]}")
        pid = r.json()["id"]
        idmap[sid] = pid
        lang_res = helper("set-language", {"post_id": pid, "lang": lang})
        print(f"{action} staging {sid} -> prod {pid} slug={s['slug']!r} "
              f"status={s['status']} lang={lang_res['language']}")
    return idmap


def phase_pages_en():
    # Free the 'blog' slug exactly as staging did.
    cur = jget(PROD, P_AUTH, "wp/v2/pages/24?context=edit&_fields=id,slug")
    if cur["slug"] == "blog":
        r = req("POST", PROD, P_AUTH, "wp/v2/pages/24",
                json={"slug": "blog-legacy-2018"})
        print(f"RENAME prod 24: blog -> {r.json()['slug']}")
    else:
        print(f"prod 24 slug already {cur['slug']!r}, no rename needed")
    upsert_pages(EN_PAGES, "en")
    # Legacy EN pages that participate in translation pairs need explicit lang.
    for pid in (20, 22):
        res = helper("set-language", {"post_id": pid, "lang": "en"})
        print(f"legacy prod {pid} lang={res['language']}")


def phase_pages_cz():
    upsert_pages(CZ_PAGES, "cz")


def phase_link():
    _, idmap = build_idmap()
    for pair in TR_MAP["pairs"]:
        en_sid, cz_sid = pair["en"], pair["cz"]
        if en_sid not in idmap or cz_sid not in idmap:
            sys.exit(f"FATAL: missing prod page for pair {pair}")
        res = helper("link-translations",
                     {"translations": {"en": idmap[en_sid], "cz": idmap[cz_sid]}})
        print(f"LINK en:{idmap[en_sid]} <-> cz:{idmap[cz_sid]} saved={res['saved']}")


MENUS = {
    "en": {"name": "Molosoc Main Menu", "items": [
        {"title": "Foot Cover", "type": "custom", "url": "/foot-covers/", "key": "fc"},
        {"title": "Molosoc Foot Cover", "page": 951, "parent_key": "fc"},
        {"title": "Blog", "page": 1021},
        {"title": "Contact/Kontakt", "page": 220},
        {"title": "Languages", "type": "custom", "url": "#pll_switcher"},
    ]},
    "cz": {"name": "Molosoc CZ Menu", "items": [
        {"title": "Kuří oko a mozoly", "page": 1036},
        {"title": "Popraskané paty", "page": 1037},
        {"title": "Zarostlý nehet", "page": 1038},
        {"title": "Návleky na nohy", "page": 1035, "key": "nn"},
        {"title": "Návlek na nohy", "page": 1039, "parent_key": "nn"},
        {"title": "Languages", "type": "custom", "url": "#pll_switcher"},
    ]},
}


def phase_menus():
    _, idmap = build_idmap()
    existing = {m["name"]: m for m in jget(PROD, P_AUTH, "wp/v2/menus?context=edit&per_page=100")}
    menu_ids = {}
    for lang, spec in MENUS.items():
        if spec["name"] in existing:
            menu_ids[lang] = existing[spec["name"]]["id"]
            print(f"menu exists: {spec['name']} id={menu_ids[lang]} (items left untouched)")
            continue
        r = req("POST", PROD, P_AUTH, "wp/v2/menus", json={"name": spec["name"]})
        menu_ids[lang] = r.json()["id"]
        print(f"CREATE menu {spec['name']} id={menu_ids[lang]}")
        item_ids = {}
        for order, item in enumerate(spec["items"], start=1):
            body = {"menus": menu_ids[lang], "menu_order": order,
                    "title": item["title"], "status": "publish",
                    "parent": item_ids.get(item.get("parent_key"), 0)}
            if "page" in item:
                body |= {"type": "post_type", "object": "page",
                         "object_id": idmap[item["page"]]}
            else:
                url = item["url"]
                body |= {"type": "custom",
                         "url": url if url.startswith("#") else PROD + url}
            ri = req("POST", PROD, P_AUTH, "wp/v2/menu-items", json=body)
            if ri.status_code not in (200, 201):
                sys.exit(f"FATAL menu item {item['title']!r}: {ri.status_code} {ri.text[:300]}")
            if "key" in item:
                item_ids[item["key"]] = ri.json()["id"]
            print(f"  item {order}: {item['title']}")
    # Assign theme location: EN menu on 'primary', per-language map via helper.
    req("POST", PROD, P_AUTH, f"wp/v2/menus/{menu_ids['en']}",
        json={"locations": ["primary"]})
    res = helper("set-nav-menus", {"theme": "molosoc", "location": "primary",
                                   "assignments": {"en": menu_ids["en"],
                                                   "cz": menu_ids["cz"]}})
    print("nav_menus:", json.dumps(res["saved_nav_menus"]))


def phase_frontpage():
    _, idmap = build_idmap()
    home = idmap[953]
    r = req("POST", PROD, P_AUTH, "wp/v2/settings",
            json={"show_on_front": "page", "page_on_front": home})
    got = r.json()
    print(f"page_on_front: {got['page_on_front']} (expected {home}), "
          f"show_on_front: {got['show_on_front']}")


def phase_verify():
    _, idmap = build_idmap()
    missing = [s for s in EN_PAGES + CZ_PAGES if s not in idmap]
    print("idmap size:", len(idmap), "missing:", missing or "none")
    langs = jget(PROD, P_AUTH, "pll/v1/languages")
    for l in langs:
        print(f"lang {l['slug']}: count={l['term_props']['language']['count']} "
              f"front={l['page_on_front']} home={l['home_url']}")
    for pair in TR_MAP["pairs"]:
        pid = idmap.get(pair["en"])
        st = jget(PROD, P_AUTH, f"molosoc-migrate/v1/status/{pid}")
        ok = set(st["translations"] or {}) >= {"en", "cz"}
        print(f"pair {pair['en_slug']}: {'OK' if ok else 'NOT LINKED'} {st['translations']}")
    # Front-end spot checks (unauthenticated, cache-busted).
    for path in ("/", "/cz/molosoc-home-cestina/", "/foot-covers/",
                 "/cz/navleky-na-nohy/", "/cz/kurici-oko/jak-odstranit/"):
        u = f"{PROD}{path}?nc={int(time.time())}"
        html = session.get(u, timeout=60).text
        alts = re.findall(r'hreflang="(\w+)"', html)
        print(f"{path}: HTTP ok, hreflang={sorted(set(alts)) or 'none'}")


PHASES = {"pages-en": phase_pages_en, "pages-cz": phase_pages_cz,
          "link": phase_link, "menus": phase_menus,
          "frontpage": phase_frontpage, "verify": phase_verify}

if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else ""
    if phase not in PHASES:
        sys.exit(f"usage: migrate.py [{'|'.join(PHASES)}]")
    print(f"=== phase: {phase} ===")
    PHASES[phase]()
    print(f"=== phase {phase} done ===")
