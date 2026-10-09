#!/usr/bin/env python3
"""
Daily conversion-funnel report (read-only): GA4 + WooCommerce + stored Clarity.

Issue #120. Replaces the manual "run three diagnostics, paste dates, assemble by
hand" routine with one consolidated, non-PII Markdown/JSON report that compares
a window with the immediately preceding window of equal length.

Reuses the EXISTING read-only collectors and credentials, adds no service:
  * GA4         diagnostic_window.ga4_report   (GOOGLE_SERVICE_ACCOUNT_JSON)
  * WooCommerce order_window.Client/fetch_orders/sanitize_order
                                               (WOO_RO_CONSUMER_KEY/SECRET)
  * Clarity     stored daily facts in the existing bucket
                                               (ANALYTICS_STORAGE_SA_JSON, ANALYTICS_BUCKET)
                Makes ZERO Clarity API calls; the 10-calls/day budget is untouched.

Reporting days are Europe/Prague calendar days. WooCommerce is queried with the
exact UTC instants of Prague midnight (DST-correct). GA4 buckets days in the
property's own timezone; this tool cannot read that setting, so the report
states the assumption instead of hiding it.

Honesty rules: a source that fails or returns nothing is reported as
"unavailable" / "no data", never as zero. Zero sales is reported as zero only
when WooCommerce was actually read successfully. Metrics no source provides
(LCP/INP: neither GA4 here nor Clarity's export API exposes them) are listed as
not collected, not estimated.

Usage:
    python3 daily_funnel_report.py                      # last 3 complete Prague days
    python3 daily_funnel_report.py --start 2026-10-06 --end 2026-10-09
    python3 daily_funnel_report.py --days 3 --out-dir report-out
"""

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote
from zoneinfo import ZoneInfo

from analytics_common import describe_error
from google_hydrate import DEFAULT_GA4_PROPERTY_ID

PRAGUE = ZoneInfo("Europe/Prague")
MAX_DAYS = 14
SOURCE_MEDIUM_LIMIT = 250
LANDING_LIMIT = 1000
# Allowlists: only these known static values are ever published; anything else is `*`/`other`.
ROUTE_SEGMENTS = frozenset({
    "foot-covers", "moisture-lock-foot-cover", "cracked-heels", "ingrown-toenails",
    "hardened-skin-calluses", "dry-skin-feet", "foot-cream-that-works", "product",
    "molosoc-hydratacni-navleky-na-nohy", "cart", "checkout", "order-received",
    "shop", "blog", "about", "contact", "faq", "my-account", "search", "404",
    "cs", "en", "sk", "de", "pl", "hu"})
SOURCES = frozenset({
    "google", "bing", "yahoo", "duckduckgo", "seznam.cz", "seznam", "ecosia.org",
    "facebook", "m.facebook.com", "l.facebook.com", "lm.facebook.com", "fb", "instagram",
    "l.instagram.com", "ig", "meta", "youtube", "linkedin", "pinterest", "tiktok",
    "klaviyo", "newsletter", "email", "chatgpt.com", "(direct)", "(not set)",
    "(data not available)"})
MEDIUMS = frozenset({
    "organic", "cpc", "ppc", "paid", "paid_social", "paidsocial", "paid-social",
    "referral", "email", "social", "display", "affiliate", "(none)", "(not set)",
    "(data not available)"})
DEFAULT_DAYS = 3
FUNNEL = ("view_item", "add_to_cart", "begin_checkout", "purchase")
FUNNEL_EVENTS = ("session_start", "page_view") + FUNNEL
SESSION_METRICS = ("sessions", "engagedSessions", "engagementRate",
                   "averageSessionDuration", "bounceRate")
META_TOKENS = ("facebook", "fb", "instagram", "ig", "meta")
PAID_MEDIUMS = ("cpc", "ppc", "paid", "paid_social", "paidsocial", "paid-social")
PAID_STATUSES = ("processing", "completed")
IGNORED_STATUSES = ("checkout-draft", "trash")
CLARITY_SUM = ("clarity_sessions", "clarity_human_sessions", "clarity_bot_sessions",
               "clarity_rage_click_count", "clarity_dead_click_count",
               "clarity_quickback_count", "clarity_script_error_count",
               "clarity_active_time", "clarity_total_time")  # SUM metrics in history.py
CLARITY_AVG = ("clarity_pages_per_session", "clarity_scroll_depth")
NOT_COLLECTED = (
    "LCP / INP: not collected. No web-vitals event exists in GA4 and Clarity's "
    "Data Export API does not return Core Web Vitals; nothing is estimated here. "
    "Use PageSpeed Insights / CrUX manually until a collector is approved.")


# --------------------------------------------------------------------------- dates

def parse_day(text):
    return dt.date.fromisoformat(text)


def today_prague(now=None):
    return (now or dt.datetime.now(dt.timezone.utc)).astimezone(PRAGUE).date()


def default_window(days=DEFAULT_DAYS, now=None):
    """Last `days` COMPLETE Prague days (ends yesterday): GA4 has not settled today."""
    end = today_prague(now) - dt.timedelta(days=1)
    return end - dt.timedelta(days=days - 1), end


def prior_window(start, end):
    length = (end - start).days + 1
    return start - dt.timedelta(days=length), start - dt.timedelta(days=1)


def validate_window(start, end):
    if end < start:
        raise ValueError("end is before start")
    if (end - start).days + 1 > MAX_DAYS:
        raise ValueError(f"window longer than {MAX_DAYS} days")


def days_of(start, end):
    return [(start + dt.timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]


def utc_bounds(start, end):
    """(after, before) naive-UTC ISO strings: Prague midnight of start .. Prague
    midnight after end. Uses zoneinfo so 23h/25h DST days are exact."""
    def midnight(day):
        return dt.datetime(day.year, day.month, day.day, tzinfo=PRAGUE).astimezone(
            dt.timezone.utc).replace(tzinfo=None).isoformat()
    return midnight(start), midnight(end + dt.timedelta(days=1))


# -------------------------------------------------------------------------- helpers

def num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def delta(cur, prev):
    """Change vs prior window; None (shown n/a) when it cannot be computed honestly."""
    if cur is None or prev is None:
        return None
    return cur - prev


def pct(cur, prev):
    if cur is None or prev is None or prev == 0:
        return None
    return (cur - prev) / prev * 100.0


def fmt(value, digits=0):
    if value is None:
        return "n/a"
    return f"{value:,.{digits}f}" if digits else f"{value:,.0f}"


def fmt_change(cur, prev, digits=0):
    d, p = delta(cur, prev), pct(cur, prev)
    if d is None:
        return "n/a"
    sign = "+" if d > 0 else ""
    tail = f" ({'+' if p > 0 else ''}{p:.0f}%)" if p is not None else ""
    return f"{sign}{d:,.{digits}f}{tail}"


def ratio(numerator, denominator):
    if numerator is None or not denominator:
        return None
    return numerator / denominator * 100.0


def is_meta_paid(source_medium):
    """Paid/Meta session classification from GA4 'source / medium'."""
    source, _, medium = (source_medium or "").lower().partition(" / ")
    tokens = source.replace(".", " ").replace("_", " ").replace("-", " ").split()
    meta = any(t in META_TOKENS for t in tokens)
    return meta or medium.strip() in PAID_MEDIUMS


# ----------------------------------------------------------------------------- GA4

def ga4_window(client, property_id, start, end, report=None):
    """Aggregated GA4 facts for one window. Raises on total failure of every report;
    individual failures land in `errors` so one bad dimension never aborts the rest."""
    if report is None:
        from diagnostic_window import ga4_report
        report = ga4_report
    s, e = start.isoformat(), end.isoformat()
    out = {"errors": [], "totals": None, "source_medium": None, "landing": [],
           "source_medium_truncated": False, "landing_truncated": False,
           "events": {}, "events_paid": {}, "events_paid_truncated": False}

    def run(name, dims, metrics, limit, events_only=False):
        try:
            return report(client, property_id, s, e, dims, metrics, limit, events_only)
        except Exception as exc:  # noqa: BLE001 — recorded, redacted, others continue
            out["errors"].append(f"{name}: {describe_error(exc)}")
            return None

    rows = run("totals", ("date",), SESSION_METRICS, 50)
    if rows is not None:
        out["days_with_data"] = sorted(r[0] for r in rows)
        sessions = sum(num(r[1]) or 0 for r in rows)
        if rows and sessions:
            def weighted(idx):
                return sum((num(r[idx]) or 0) * (num(r[1]) or 0) for r in rows) / sessions
            out["totals"] = {"sessions": sessions,
                             "engagedSessions": sum(num(r[2]) or 0 for r in rows),
                             "engagementRate": weighted(3) * 100,
                             "averageSessionDuration": weighted(4),
                             "bounceRate": weighted(5) * 100}
    rows = run("source/medium", ("sessionSourceMedium",), SESSION_METRICS,
               SOURCE_MEDIUM_LIMIT)
    if rows is not None:
        if len(rows) >= SOURCE_MEDIUM_LIMIT:
            out["source_medium_truncated"] = True
            out["errors"].append("source/medium: row limit reached; source/medium "
                                 "table and paid/Meta session total are incomplete "
                                 "and are not reported")
        else:
            out["source_medium"] = merge_source_medium(rows)
    rows = run("landing pages", ("landingPage",), SESSION_METRICS, LANDING_LIMIT)
    if rows is not None:
        if len(rows) >= LANDING_LIMIT:
            # Merging canonical paths from a truncated list would under-count pages.
            out["landing_truncated"] = True
            out["errors"].append("landing pages: row limit reached; landing-page "
                                 "table is incomplete and not reported")
        else:
            out["landing"] = merge_landing(rows)
    rows = run("funnel events", ("eventName",), ("eventCount", "totalUsers"), 50, True)
    if rows is not None:
        out["events"] = {r[0]: {"count": num(r[1]), "users": num(r[2])} for r in rows}
    rows = run("funnel events by source/medium", ("sessionSourceMedium", "eventName"),
               ("eventCount", "totalUsers"), 1000, True)
    if rows is not None:
        paid = {}
        for sm, ev, count, users in rows:
            if is_meta_paid(sm):
                slot = paid.setdefault(ev, {"count": 0.0, "users": 0.0})
                slot["count"] += num(count) or 0
                # Users are summed across sources: an upper bound (labelled as such in render).
                slot["users"] += num(users) or 0
        out["events_paid"] = paid
        if len(rows) >= 1000:
            out["events_paid"] = {}
            out["events_paid_truncated"] = True
            out["errors"].append("funnel events by source/medium: row limit reached; "
                                 "paid funnel figures are incomplete and not reported")
    return out


def redact_source_medium(value):
    """Allowlisted `source / medium` label; visitor-controlled utm text becomes `other`."""
    source, _, medium = (value or "").lower().partition(" / ")
    source, medium = source.strip(), medium.strip()
    return (f"{source if source in SOURCES else 'other'} / "
            f"{medium if medium in MEDIUMS else 'other'}")


def merge_source_medium(rows):
    """Redact labels (paid flag computed from the raw value first), merge collisions."""
    merged = {}
    for r in rows:
        label = redact_source_medium(r[0])
        slot = merged.setdefault(label, {"source_medium": label, "sessions": 0.0,
                                         "engaged": 0.0, "paid": False})
        slot["sessions"] += num(r[1]) or 0.0
        slot["engaged"] += num(r[2]) or 0.0
        slot["paid"] = slot["paid"] or is_meta_paid(r[0])
    return sorted(merged.values(), key=lambda x: -x["sessions"])


def redact_path(path):
    """Canonical, non-PII landing path: query/fragment dropped, percent-decoded, and any
    segment not on the static route allowlist (names, emails, ids, tokens) replaced by `*`."""
    path = unquote((path or "").split("?")[0].split("#")[0]) or "/"
    segments = [seg for seg in path.split("/") if seg]
    kept = []
    for seg in segments[:4]:
        kept.append(seg.lower() if seg.lower() in ROUTE_SEGMENTS else "*")
    if len(segments) > 4:
        kept.append("…")
    return "/" + "/".join(kept)


def merge_landing(rows):
    """Redact paths, then merge rows that collapse to the same path (session-weighted)."""
    merged = {}
    for r in rows:
        key = redact_path(r[0])
        sessions = num(r[1]) or 0.0
        slot = merged.setdefault(key, {"page": key, "sessions": 0.0, "engaged": 0.0,
                                       "_rate": 0.0, "_dur": 0.0})
        slot["sessions"] += sessions
        slot["engaged"] += num(r[2]) or 0.0
        slot["_rate"] += (num(r[3]) or 0.0) * sessions
        slot["_dur"] += (num(r[4]) or 0.0) * sessions
    out = []
    for slot in merged.values():
        n = slot["sessions"]
        out.append({"page": slot["page"], "sessions": n, "engaged": slot["engaged"],
                    "engagement_rate": slot["_rate"] / n * 100 if n else 0.0,
                    "avg_duration": slot["_dur"] / n if n else 0.0})
    return sorted(out, key=lambda x: -x["sessions"])


def paid_sessions(ga4):
    """Paid/Meta sessions, or None when the source/medium data is unavailable/truncated."""
    if not ga4 or ga4.get("source_medium") is None or ga4.get("source_medium_truncated"):
        return None
    return sum(r["sessions"] or 0 for r in ga4["source_medium"] if r["paid"])


def funnel_steps(events):
    """[(stage, users, ratio % of this stage's users to the previous stage's)].
    Per-event user sets are independent (not a cohort), so the ratio can exceed 100."""
    steps, previous = [], None
    for stage in FUNNEL:
        users = (events.get(stage) or {}).get("users")
        steps.append((stage, users, ratio(users, previous) if previous else None))
        previous = users
    return steps


# -------------------------------------------------------------------------- Woo

def summarize_orders(orders):
    """Aggregate sanitized orders. paid = processing/completed; refunded counted apart;
    everything else (pending, on-hold, failed, cancelled) is unpaid."""
    orders = [o for o in orders if o.get("status") not in IGNORED_STATUSES]
    out = {"orders": len(orders), "paid": 0, "unpaid": 0, "refunded": 0,
           "paid_revenue": 0.0, "currency": None, "by_status": {},
           "paid_meta": 0, "paid_other": 0, "sources_paid": {}}
    for o in orders:
        status = o.get("status") or "unknown"
        out["by_status"][status] = out["by_status"].get(status, 0) + 1
        out["currency"] = out["currency"] or o.get("currency")
        if status in PAID_STATUSES:
            out["paid"] += 1
            out["paid_revenue"] += num(o.get("total")) or 0.0
            attr = o.get("attribution") or {}
            label = " / ".join(str(attr.get(k) or "(none)")
                               for k in ("utm_source", "utm_medium"))
            paid_meta = is_meta_paid(label)  # classify before the display label is redacted
            if attr.get("utm_source") == "[redacted]":
                label = "[redacted source] / " + str(attr.get("utm_medium") or "(none)")
            out["sources_paid"][label] = out["sources_paid"].get(label, 0) + 1
            if paid_meta:
                out["paid_meta"] += 1
            else:
                out["paid_other"] += 1
        elif status == "refunded":
            out["refunded"] += 1
        else:
            out["unpaid"] += 1
    return out


def woo_window(client, start, end, fetch=None, sanitize=None):
    if fetch is None or sanitize is None:
        from woocommerce_adapter import load
        fetch, sanitize = load()
    after, before = utc_bounds(start, end)
    return summarize_orders([sanitize(o) for o in fetch(client, after, before)])


# ----------------------------------------------------------------------- Clarity

def clarity_mean(rows):
    """Mean per history.aggregate: weighted by each record's stored sample_basis, else
    the unweighted mean (every snapshot covers an equal-length window)."""
    total = sum(b for _, b in rows)
    if total:
        return sum(v * b for v, b in rows) / total
    return sum(v for v, _ in rows) / len(rows) if rows else None


def clarity_window(store, start, end):
    """Aggregate stored Clarity daily facts for Prague days start..end.

    A snapshot dated D is a trailing-24h window collected ~02:20 UTC on D, i.e.
    ~03:20-04:20 Prague on D, so it approximates Prague day D-1: Prague day X
    maps to the snapshot dated X+1. Approximate by construction; stated in the
    report. Missing days are listed, never zero-filled."""
    from storage import StorageError, facts_key
    sums = {m: 0.0 for m in CLARITY_SUM}
    avg_rows = {m: [] for m in CLARITY_AVG}  # (value, stored sample_basis) per day
    absent = set()  # metrics missing from at least one found day -> n/a, never zero
    found, missing, failures, failed_days = [], [], [], []
    for day in days_of(start, end):
        snap = (parse_day(day) + dt.timedelta(days=1)).isoformat()
        key = facts_key("clarity", snap)
        try:
            if not store.exists(key):
                missing.append(day)
                continue
            records = store.get_json(key).get("records", [])
        except StorageError as exc:
            failures.append(f"Clarity {snap}: {describe_error(exc)}")
            failed_days.append(day)
            continue
        site = {r.get("metric"): num(r.get("value")) for r in records
                if r.get("entity_type") == "site"}
        basis = {r.get("metric"): num(r.get("sample_basis")) for r in records
                 if r.get("entity_type") == "site"}
        if "clarity_sessions" not in site:
            missing.append(day)
            continue
        found.append(day)
        for m in CLARITY_SUM:
            if site.get(m) is None:
                absent.add(m)
            else:
                sums[m] += site[m]
        for m in CLARITY_AVG:
            if site.get(m) is None:
                absent.add(m)
            else:
                avg_rows[m].append((site[m], basis.get(m) or 0.0))
    out = {"days_found": found, "days_missing": missing, "days_failed": failed_days,
           "failures": failures}
    if found:
        out["sums"] = {m: (None if m in absent else v) for m, v in sums.items()}
        out["averages"] = {m: (None if m in absent else clarity_mean(avg_rows[m]))
                           for m in CLARITY_AVG}
    return out


# ----------------------------------------------------------------------- rendering

def render(report):
    cur, prev = report["window"], report["prior_window"]
    g, gp = report["ga4"], report["ga4_prior"]
    w, wp = report["woo"], report["woo_prior"]
    c, cp = report["clarity"], report["clarity_prior"]
    L = []
    add = L.append
    add(f"# MOLOSOC daily conversion funnel — {cur['start']} .. {cur['end']}")
    add(f"\nCompared with the previous equal window {prev['start']} .. {prev['end']}. "
        f"Days are Europe/Prague. Generated {report['generated_at']} (UTC).")
    for note in report["notes"]:
        add(f"\n> {note}")

    add("\n## Source status")
    for name, status in report["status"].items():
        add(f"- **{name}**: {status}")

    add("\n## Traffic (GA4)")
    if g is None or g.get("totals") is None:
        add("No GA4 session data for this window "
            "(unavailable, or genuinely zero sessions — see source status).")
    else:
        t, tp = g["totals"], (gp or {}).get("totals") or {}
        add("| Metric | This window | Previous | Change |\n|---|---:|---:|---:|")
        for label, key, digits in (("Sessions", "sessions", 0),
                                   ("Engaged sessions", "engagedSessions", 0),
                                   ("Engagement rate %", "engagementRate", 1),
                                   ("Avg session duration (s)", "averageSessionDuration", 0),
                                   ("Bounce rate %", "bounceRate", 1)):
            add(f"| {label} | {fmt(t.get(key), digits)} | {fmt(tp.get(key), digits)} | "
                f"{fmt_change(t.get(key), tp.get(key), digits)} |")
        paid = paid_sessions(g)
        paid_prev = paid_sessions(gp)
        add(f"\nPaid / Meta sessions: **{fmt(paid)}** "
            f"(previous {fmt(paid_prev)}; {fmt_change(paid, paid_prev)}). "
            "Classified from GA4 source/medium (facebook, instagram, meta, fb, ig, or a "
            "paid medium).")
        add("\n### Source / medium (top 10)\n| Source / medium | Sessions | Engaged | Paid |\n|---|---:|---:|:-:|")
        if g["source_medium"] is None:
            add("| unavailable | n/a | n/a | |")
        for r in (g["source_medium"] or [])[:10]:
            add(f"| {r['source_medium']} | {fmt(r['sessions'])} | {fmt(r['engaged'])} | "
                f"{'yes' if r['paid'] else ''} |")
        add("\n### Landing-page engagement (top 10 by sessions)\n"
            "| Landing page | Sessions | Engagement % | Avg duration (s) |\n|---|---:|---:|---:|")
        for r in g["landing"][:10]:
            add(f"| {r['page']} | {fmt(r['sessions'])} | {fmt(r['engagement_rate'], 1)} | "
                f"{fmt(r['avg_duration'])} |")

    add("\n## Funnel (GA4 observed users per event; not a cohort)")
    if g is None or not g.get("events"):
        add("No GA4 funnel-event data (unavailable or none recorded).")
    else:
        add("| Stage | Users | Ratio to previous stage % | Previous users | Change |\n|---|---:|---:|---:|---:|")
        prev_steps = dict((s, u) for s, u, _ in funnel_steps((gp or {}).get("events") or {}))
        for stage, users, step in funnel_steps(g["events"]):
            add(f"| {stage} | {fmt(users)} | {fmt(step, 1)} | {fmt(prev_steps.get(stage))} | "
                f"{fmt_change(users, prev_steps.get(stage))} |")
        add("\nRatio = users who fired this event / users who fired the previous stage's "
            "event. These are independent per-event user counts, NOT a cohort funnel: a "
            "returning customer can purchase without a checkout event in the window, so "
            "the ratio can exceed 100% and is not a true conversion or drop-off rate. "
            "Events that GA4 never recorded show n/a, not 0.")
        if g.get("events_paid_truncated"):
            add("\n**Paid / Meta funnel**: unavailable (GA4 row limit reached; figures "
                "would be incomplete).")
        elif g.get("events_paid"):
            add("\n**Paid / Meta funnel** (events: count / users)")
            add("Users are summed across paid source/medium rows, so a user seen under "
                "two paid sources is counted twice: treat Users as an upper bound.")
            add("| Stage | Events | Users (upper bound) |\n|---|---:|---:|")
            for stage in FUNNEL:
                p = g["events_paid"].get(stage)
                add(f"| {stage} | {fmt(p['count']) if p else 'n/a'} | "
                    f"{fmt(p['users']) if p else 'n/a'} |")

    add("\n## Orders (WooCommerce, read-only)")
    if w is None:
        add("WooCommerce unavailable — no order figures reported (see source status).")
    else:
        add("| Metric | This window | Previous | Change |\n|---|---:|---:|---:|")
        for label, key in (("Orders (all, excl. drafts)", "orders"), ("Paid", "paid"),
                           ("Unpaid (pending / on-hold / failed / cancelled)", "unpaid"),
                           ("Refunded", "refunded"), ("Paid via Meta/paid attribution", "paid_meta")):
            pv = wp.get(key) if wp else None
            add(f"| {label} | {fmt(w[key])} | {fmt(pv)} | {fmt_change(w[key], pv)} |")
        pr = wp.get("paid_revenue") if wp else None
        add(f"| Paid revenue ({w['currency'] or 'n/a'}) | {fmt(w['paid_revenue'], 2)} | "
            f"{fmt(pr, 2)} | {fmt_change(w['paid_revenue'], pr, 2)} |")
        if w["orders"] == 0:
            add("\n**Zero orders in this window** (WooCommerce was read successfully).")
        if w["by_status"]:
            add("\nStatuses: " + ", ".join(f"{k} {v}" for k, v in sorted(w["by_status"].items())))
        if w["sources_paid"]:
            add("Paid-order attribution (utm_source / utm_medium; unrecognised values redacted): "
                + ", ".join(f"{k} ×{v}" for k, v in sorted(w["sources_paid"].items())))
        if g and g.get("events", {}).get("purchase") and w["paid"] != g["events"]["purchase"]["count"]:
            add(f"\nNote: GA4 `purchase` events ({fmt(g['events']['purchase']['count'])}) differ "
                f"from paid Woo orders ({w['paid']}); Woo is the source of truth for sales.")

    add("\n## Behaviour (Clarity, stored daily snapshots)")
    if not c.get("days_found"):
        add(f"No Clarity snapshot available for this window (missing days: "
            f"{', '.join(c.get('days_missing') or []) or 'n/a'}).")
    else:
        s, a = c["sums"], c["averages"]
        sp, ap = (cp.get("sums"), cp.get("averages")) if cp.get("days_found") else ({}, {})
        gaps = lambda x: list(x.get("days_missing") or []) + list(x.get("days_failed") or [])  # noqa: E731
        comparable = not gaps(c) and not gaps(cp) and bool(cp.get("days_found"))

        def chg(cur_v, prev_v, digits=0):
            return fmt_change(cur_v, prev_v, digits) if comparable else "n/a"
        add(f"Days covered: {len(c['days_found'])}/{len(c['days_found']) + len(gaps(c))}"
            + (f" (missing or unreadable {', '.join(sorted(gaps(c)))})" if gaps(c) else "")
            + ". Each snapshot is a trailing 24 h window ending ~03:20–04:20 Prague, so a "
              "Prague day is approximated by the next UTC date's snapshot; session counts "
              "include bots.")
        if gaps(cp):
            add(f"Previous window coverage: {len(cp.get('days_found') or [])}/"
                f"{len(cp.get('days_found') or []) + len(gaps(cp))} days "
                f"(missing or unreadable {', '.join(sorted(gaps(cp)))}).")
        if not comparable:
            add("Changes are n/a because snapshot coverage is incomplete in one or both "
                "windows, so the sums are not comparable.")
        add("| Metric | This window | Previous | Change |\n|---|---:|---:|---:|")
        labels = {"clarity_sessions": "Sessions (total)", "clarity_human_sessions": "Human sessions",
                  "clarity_bot_sessions": "Bot sessions", "clarity_rage_click_count": "Rage clicks",
                  "clarity_dead_click_count": "Dead clicks", "clarity_quickback_count": "Quick-backs",
                  "clarity_script_error_count": "Script errors",
                  "clarity_active_time": "Active time (sum of daily totals)",
                  "clarity_total_time": "Total time (sum of daily totals)"}
        for m in CLARITY_SUM:
            add(f"| {labels[m]} | {fmt(s[m])} | {fmt(sp.get(m))} | {chg(s[m], sp.get(m))} |")
        for m, label in (("clarity_pages_per_session", "Pages / session"),
                         ("clarity_scroll_depth", "Avg scroll depth")):
            add(f"| {label} | {fmt(a.get(m), 2)} | {fmt(ap.get(m), 2)} | "
                f"{chg(a.get(m), ap.get(m), 2)} |")
        add("\nClarity's export API provides no paid/Meta split and no per-landing-page "
            "engagement here; those come from GA4 above.")

    add("\n## Not collected")
    add(f"- {NOT_COLLECTED}")
    add("\n## Method & limits")
    for line in report["limits"]:
        add(f"- {line}")
    return "\n".join(L) + "\n"


LIMITS = (
    "GA4 data can lag up to ~24-48 h; the most recent day may still rise. Scheduled runs "
    "use complete Prague days ending yesterday.",
    "GA4 daily buckets follow the GA4 property's timezone, which this tool cannot read; "
    "Europe/Prague is assumed and must be confirmed in GA4 Admin → Property settings.",
    "WooCommerce windows use exact Europe/Prague midnights converted to UTC.",
    "Output is aggregate only: no customer data, order ids, landing-page query strings "
    "or free-text attribution values are printed.",
    "A source that errors or has no data is shown as unavailable / n/a — never as zero.",
)


# ---------------------------------------------------------------------------- main

def build_report(start, end, ga4_fn, woo_fn, clarity_fn, now=None):
    """Assemble the full report dict from three callables (window -> dict)."""
    p_start, p_end = prior_window(start, end)
    now = now or dt.datetime.now(dt.timezone.utc)
    report = {"generated_at": now.replace(microsecond=0).isoformat(),
              "window": {"start": start.isoformat(), "end": end.isoformat()},
              "prior_window": {"start": p_start.isoformat(), "end": p_end.isoformat()},
              "status": {}, "notes": [], "limits": list(LIMITS), "failed": False}
    for key, fn in (("ga4", ga4_fn), ("woo", woo_fn), ("clarity", clarity_fn)):
        for suffix, (a, b) in (("", (start, end)), ("_prior", (p_start, p_end))):
            try:
                report[key + suffix] = fn(a, b)
            except (Exception, SystemExit) as exc:  # noqa: BLE001 — load helpers sys.exit
                report[key + suffix] = None if key != "clarity" else {"days_found": [], "days_missing": days_of(a, b)}
                report["status"].setdefault(key, f"UNAVAILABLE — {describe_error(exc)}")
                report["failed"] = True
    for key, label in (("ga4", "GA4"), ("woo", "WooCommerce"), ("clarity", "Clarity (stored)")):
        if key in report["status"]:
            continue
        problems = []
        for suffix, tag in (("", ""), ("_prior", "previous window: ")):
            part = report[key + suffix]
            if part:
                problems += [tag + p for p in
                             list(part.get("errors", [])) + list(part.get("failures", []))]
        if problems:
            report["failed"] = True
            report["status"][key] = "PARTIAL — " + "; ".join(problems)
        else:
            report["status"][key] = "ok"
    report["status"] = {{"ga4": "GA4", "woo": "WooCommerce", "clarity": "Clarity (stored)"}[k]: v
                        for k, v in report["status"].items()}
    if end >= today_prague(now):
        report["notes"].append("The window includes today (Prague): it is partial and GA4 "
                               "will revise it. Treat as indicative.")
    if report["woo"] and report["woo"]["orders"] == 0 and report["woo"]["paid"] == 0:
        report["notes"].append("Zero WooCommerce orders in this window.")
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--start", help="First Prague day (YYYY-MM-DD)")
    ap.add_argument("--end", help="Last Prague day, inclusive (YYYY-MM-DD)")
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS,
                    help="Rolling length when --start/--end are omitted")
    ap.add_argument("--property-id", default=DEFAULT_GA4_PROPERTY_ID)
    ap.add_argument("--out-dir", default="funnel-report")
    args = ap.parse_args(argv)
    try:
        if bool(args.start) != bool(args.end):
            raise ValueError("pass both --start and --end, or neither")
        if args.start:
            start, end = parse_day(args.start), parse_day(args.end)
        else:
            start, end = default_window(args.days)
        validate_window(start, end)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    lazy = {}

    def ga4_fn(a, b):
        if "ga4" not in lazy:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google_connection_test import GA4_SCOPE, build_credentials, load_service_account_info
            lazy["ga4"] = BetaAnalyticsDataClient(
                credentials=build_credentials(load_service_account_info(), [GA4_SCOPE]))
        return ga4_window(lazy["ga4"], args.property_id, a, b)

    def woo_fn(a, b):
        if "woo" not in lazy:
            from woocommerce_adapter import make_client
            lazy["woo"] = make_client()
        return woo_window(lazy["woo"], a, b)

    def clarity_fn(a, b):
        if "clarity" not in lazy:
            from storage_gcs import store_from_env
            lazy["clarity"] = store_from_env()
        return clarity_window(lazy["clarity"], a, b)

    report = build_report(start, end, ga4_fn, woo_fn, clarity_fn)
    markdown = render(report)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    name = f"funnel-{start.isoformat()}_{end.isoformat()}"
    (out / f"{name}.md").write_text(markdown, encoding="utf-8")
    (out / f"{name}.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(markdown)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(markdown)
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
