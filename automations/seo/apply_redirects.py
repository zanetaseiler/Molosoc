#!/usr/bin/env python3
"""
Create the Step 3A 301 redirects — but only for mappings that re-verify clean.

This script re-runs the full pre-flight itself rather than trusting an earlier
run. Site state can change between a check and an apply — someone edits a page,
the Redirection plugin's slug monitor auto-creates a rule — and a redirect
written against stale facts is exactly the failure this whole step exists to
avoid. A mapping that does not come back OK is skipped and reported, never
forced.

What it will not do:

  * create a rule whose source already has a rule (idempotent: an identical
    rule is reported and left alone; a conflicting one is an error)
  * create a rule whose target is itself a redirect source (chain)
  * create a rule whose target redirects back to the source (loop)
  * create a rule whose target does not return a direct 200
  * touch a mapping marked "conditional" unless --include-conditional is
    passed AND it re-verifies clean
  * delete, disable or edit any existing rule
  * touch the sitemap, Search Console, or any page content

--dry-run prints exactly what would be created and exits without writing.
"""

import argparse
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import preflight_redirects as pf  # noqa: E402

REDIRECT_CODE = 301


def monitor_setting(sess, base, auth):
    """Whether the plugin's 'monitor slug changes' feature is on.

    It is the reason this step is delicate: with it enabled, renaming a page
    silently creates a rule nobody asked for, which is how /blog/ came to
    point at /blog-legacy-2018/. Reported, never changed here — turning it off
    is a separate decision with its own consequences.
    """
    data, err = pf.wp_get(sess, base, "redirection/v1/setting", auth)
    if err:
        return None, err
    monitor = data.get("settings", {}).get("monitor_post") \
        if isinstance(data.get("settings"), dict) else data.get("monitor_post")
    return {"monitor_post": monitor, "raw": data.get("settings", data)}, None


def default_group(rules):
    """Reuse the group the existing rules live in, so nothing lands orphaned."""
    for r in rules or []:
        if r.get("group"):
            return r["group"]
    return 1


def create_rule(sess, base, auth, source, target, group_id):
    payload = {
        "url": source,
        "match_type": "url",
        "action_type": "url",
        "action_code": REDIRECT_CODE,
        "action_data": {"url": target},
        "group_id": group_id,
        "status": "enabled",
        "position": 0,
    }
    r = sess.post(f"{base.rstrip('/')}/wp-json/redirection/v1/redirect",
                  auth=auth, json=payload, timeout=pf.TIMEOUT)
    if r.status_code not in (200, 201):
        return None, f"HTTP {r.status_code}: {r.text[:300]}"
    try:
        return r.json(), None
    except ValueError:
        return None, "non-JSON response"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be created; write nothing")
    ap.add_argument("--include-conditional", action="store_true",
                    help="also apply mappings marked conditional (blog-legacy-2018)")
    ap.add_argument("--only", type=str, default="",
                    help="comma-separated mapping ids to consider (default: all)")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    cfg = json.load(open(os.path.join(here, "redirect-map.json"), encoding="utf-8"))

    base = (os.environ.get("WP_URL") or cfg["site"]).rstrip("/")
    site = cfg["site"].rstrip("/")
    auth = (os.environ.get("WP_USER", ""), os.environ.get("WP_APP_PASSWORD", ""))
    if not all(auth):
        print("FAIL WordPress credentials are required.", file=sys.stderr)
        return 1

    only = {int(x) for x in args.only.split(",") if x.strip()} if args.only else None
    sess = pf.session()

    print("=" * 74)
    print("STEP 3A APPLY" + ("  — DRY RUN, nothing will be written" if args.dry_run else ""))
    print("=" * 74)

    rules, err = pf.redirection_rules(sess, base, auth)
    if err:
        print(f"FAIL could not read existing rules: {err}", file=sys.stderr)
        return 1
    by_source = pf.rule_index(rules)
    group_id = default_group(rules)
    print(f"Existing rules: {len(rules)}   target group: {group_id}")

    monitor, merr = monitor_setting(sess, base, auth)
    if merr:
        print(f"NOTE could not read plugin settings: {merr}")
    else:
        print(f"Plugin slug-change monitor (monitor_post): "
              f"{monitor.get('monitor_post')!r}")
        if monitor.get("monitor_post"):
            print("  !! Enabled. It can auto-create rules when a slug changes. "
                  "Not changed by this script. Re-list rules afterwards to "
                  "confirm nothing extra appeared.")

    _sm_url, sm_urls = pf.sitemap_urls(sess, site)

    created, skipped, refused = [], [], []
    for m in cfg["mappings"]:
        if only and m["id"] not in only:
            continue
        if m.get("conditional") and not args.include_conditional:
            skipped.append((m, "conditional — not requested"))
            continue

        live = {"chain": pf.trace(sess, site + m["source"])[0],
                "facts": pf.page_facts(sess, site + m["source"])}
        dest = {"chain": pf.trace(sess, site + m["target"])[0],
                "facts": pf.page_facts(sess, site + m["target"])}
        verdict, problems, notes, _ = pf.analyse(m, live, dest, by_source, sm_urls)

        print("\n" + "-" * 74)
        print(f"[{m['id']}] {m['source']} -> {m['target']}   verdict={verdict}")
        for n in notes:
            print(f"  note: {n}")
        for p in problems:
            print(f"  ** {p}")

        if verdict == pf.VERDICT_ALREADY:
            skipped.append((m, "already redirects correctly"))
            continue
        if verdict != pf.VERDICT_OK:
            refused.append((m, problems))
            print("  REFUSED — not safe to apply")
            continue

        if args.dry_run:
            print(f"  would create: 301 {m['source']} -> {m['target']}")
            created.append((m, None))
            continue

        result, cerr = create_rule(sess, base, auth, m["source"], m["target"], group_id)
        if cerr:
            refused.append((m, [f"create failed: {cerr}"]))
            print(f"  FAILED to create: {cerr}")
            continue
        print(f"  created rule id={result.get('id')} (301)")
        created.append((m, result))

    # ---- post-verification -------------------------------------------------
    if not args.dry_run and created:
        print("\n" + "=" * 74)
        print("POST-VERIFICATION")
        print("=" * 74)
        ok = True
        for m, _ in created:
            chain, _kind = pf.trace(sess, site + m["source"])
            n = pf.hops(chain)
            final = pf.final_status(chain)
            landing = pf.normalize_path(
                pf.urlparse(chain[-1]["url"]).path) if chain else None
            good = (n == 1 and final == 200
                    and landing == pf.normalize_path(m["target"]))
            ok = ok and good
            print(f"  [{m['id']}] {'PASS' if good else 'FAIL'} "
                  f"hops={n} final={final} -> {landing}")
            print(f"        {pf.describe(chain)}")
        # destinations must still be healthy
        for m, _ in created:
            f = pf.page_facts(sess, site + m["target"])
            robots = (f.get("robots") or "").lower()
            canon_ok = (not f.get("canonical")) or pf.normalize_path(
                pf.urlparse(f["canonical"]).path) == pf.normalize_path(m["target"])
            noindex = "noindex" in robots
            print(f"  [{m['id']}] destination status={f.get('status')} "
                  f"canonical_self={canon_ok} noindex={noindex}")
            ok = ok and f.get("status") == 200 and canon_ok and not noindex
        if not ok:
            print("\n::error::post-verification FAILED — review before continuing")
            return 1

    print("\n" + "=" * 74)
    print("SUMMARY")
    print("=" * 74)
    print(f"  created/would-create : {[m['id'] for m, _ in created]}")
    print(f"  skipped              : {[(m['id'], why) for m, why in skipped]}")
    print(f"  refused              : {[m['id'] for m, _ in refused]}")
    for m, problems in refused:
        for p in problems:
            print(f"    [{m['id']}] {p}")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
