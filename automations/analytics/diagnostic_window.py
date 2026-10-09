#!/usr/bin/env python3
"""
Short-window funnel diagnostic (read-only): GA4 + stored Clarity daily facts.

Prints the aggregated evidence for a few complete days (default 2026-09-29 ..
2026-10-01, the window of Issue #96) so a paid-traffic question can be
answered without building a new reporting system:

  * GA4 (live Data API, read-only): sessions/users/engagement by day, by
    source/medium/campaign, by device, by landing page, and the funnel events
    view_item / add_to_cart / begin_checkout / purchase overall, per
    source/medium and per device.
  * Clarity (stored daily facts in the existing bucket, read-only): every
    normalized record for each day in the window, grouped by entity type.
    Makes ZERO Clarity API calls, so the 10-calls-a-day budget is untouched.

Nothing is written anywhere. GA4 runs six small runReport calls. A dimension
or metric GA4 rejects is reported and skipped; it never aborts the others, and
an absent value is never turned into a zero.

Usage:
    export GOOGLE_SERVICE_ACCOUNT_JSON='...'   # GA4
    export ANALYTICS_STORAGE_SA_JSON='...'     # Clarity history
    export ANALYTICS_BUCKET='molosoc-analytics-history'
    python3 automations/analytics/diagnostic_window.py [--start D --end D]
"""

import argparse
import datetime as dt
import sys

from analytics_common import describe_error
from google_hydrate import DEFAULT_GA4_PROPERTY_ID
from storage import StorageError, facts_key

DEFAULT_START = "2026-09-29"
DEFAULT_END = "2026-10-01"
MAX_DAYS = 14
FUNNEL_EVENTS = ("session_start", "page_view", "scroll", "click", "view_item_list",
                 "view_item", "add_to_cart", "view_cart", "begin_checkout",
                 "add_shipping_info", "add_payment_info", "purchase")
TOP_N = 15

SESSION_METRICS = ("sessions", "totalUsers", "engagedSessions", "engagementRate",
                   "averageSessionDuration", "bounceRate")
# (title, dimensions, metrics, row limit, dimension filter on eventName)
GA4_REPORTS = (
    ("Daily totals", ("date",), SESSION_METRICS, 50, False),
    ("Source / medium / campaign", ("sessionSourceMedium", "sessionCampaignName"),
     SESSION_METRICS, 40, False),
    ("Device", ("deviceCategory",), SESSION_METRICS, 10, False),
    ("Landing pages", ("landingPagePlusQueryString",), SESSION_METRICS, 40, False),
    ("Funnel events (overall)", ("eventName",), ("eventCount", "totalUsers"), 50, True),
    ("Funnel events by source / medium", ("sessionSourceMedium", "eventName"),
     ("eventCount", "totalUsers"), 1000, True),
    ("Funnel events by device", ("deviceCategory", "eventName"),
     ("eventCount", "totalUsers"), 200, True),
)
# Reports whose rows are grouped by their first dimension: keep the top groups
# with ALL of their event rows, never a global top-N that drops rare stages.
GROUPED_REPORTS = ("Funnel events by source / medium", "Funnel events by device")


def window_dates(start, end):
    first, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    if last < first:
        raise ValueError("--end is before --start")
    if (last - first).days + 1 > MAX_DAYS:
        raise ValueError(f"window longer than {MAX_DAYS} days; this is a short-window tool")
    return [(first + dt.timedelta(days=i)).isoformat()
            for i in range((last - first).days + 1)]


def _fmt(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(number)) if number == int(number) else f"{number:.3f}"


def table(title, header, rows):
    lines = [f"\n### {title}"]
    if not rows:
        lines.append("(no rows returned)")
        return "\n".join(lines)
    lines.append(" | ".join(header))
    lines += [" | ".join(_fmt(c) for c in row) for row in rows]
    return "\n".join(lines)


def ga4_report(client, property_id, start, end, dimensions, metrics, limit,
               events_only=False):
    """One read-only runReport; rows are returned as lists of strings."""
    from google.analytics.data_v1beta.types import (
        DateRange, Dimension, Filter, FilterExpression, Metric, OrderBy,
        RunReportRequest,
    )

    kwargs = {}
    if events_only:
        # True -> the module's FUNNEL_EVENTS; a tuple/list -> that explicit event set.
        names = FUNNEL_EVENTS if events_only is True else tuple(events_only)
        kwargs["dimension_filter"] = FilterExpression(filter=Filter(
            field_name="eventName",
            in_list_filter=Filter.InListFilter(values=list(names))))
    order = (OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))
             if dimensions[0] == "date"
             else OrderBy(metric=OrderBy.MetricOrderBy(metric_name=metrics[0]), desc=True))
    response = client.run_report(RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        order_bys=[order], limit=limit, **kwargs))
    return [[v.value for v in r.dimension_values] + [v.value for v in r.metric_values]
            for r in response.rows]


def top_groups(rows, n=TOP_N):
    """Top n groups (first column) by total eventCount, keeping every row of each."""
    totals = {}
    for row in rows:
        try:
            totals[row[0]] = totals.get(row[0], 0) + float(row[2])
        except (TypeError, ValueError, IndexError):
            totals.setdefault(row[0], 0)
    keep = set(sorted(totals, key=lambda g: -totals[g])[:n])
    shown = [row for row in rows if row[0] in keep]
    note = (f"\n(showing top {n} of {len(totals)} groups by eventCount, all events kept)"
            if len(totals) > n else "")
    return shown, note


def run_ga4(client, property_id, start, end):
    sections, errors = [], []
    for title, dims, metrics, limit, events_only in GA4_REPORTS:
        try:
            rows = ga4_report(client, property_id, start, end, dims, metrics,
                              limit, events_only)
        except Exception as exc:  # noqa: BLE001 — reported, redacted, skipped
            errors.append(f"{title}: {describe_error(exc)}")
            continue
        note = ""
        if dims[0] == "date":
            shown = rows
        elif title in GROUPED_REPORTS:
            shown, note = top_groups(rows)
        else:
            shown = rows[:TOP_N * 4]
        if len(rows) >= limit:
            note += f"\n(WARN: GA4 row limit {limit} reached; rows may be truncated)"
        sections.append(table(f"GA4 — {title}", list(dims) + list(metrics), shown) + note)
    return sections, errors


def clarity_section(store, dates):
    """Every stored Clarity fact for each day, grouped by entity type."""
    sections, found, failures = [], [], []
    for date in dates:
        key = facts_key("clarity", date)
        try:
            if not store.exists(key):
                sections.append(f"\n### Clarity {date}\n(no stored snapshot for this date)")
                continue
            document = store.get_json(key)
        except StorageError as exc:
            # Not "missing": the read itself failed, so the day was NOT checked.
            sections.append(f"\n### Clarity {date}\n(READ FAILED, day not checked)")
            failures.append(f"Clarity {date} read failed: {describe_error(exc)}")
            continue
        found.append(date)
        records = document.get("records", [])
        rows = sorted(
            ([r.get("entity_type"), r.get("entity_id"), r.get("metric"), r.get("value"),
              r.get("sample_basis"), r.get("window_days")] for r in records),
            key=lambda row: (str(row[0]) != "site", str(row[0]), str(row[2]),
                             -(float(row[3]) if isinstance(row[3], (int, float)) else 0)))
        sections.append(table(
            f"Clarity {date} — {len(records)} records (trailing-24h snapshot)",
            ["entity_type", "entity_id", "metric", "value", "sample_basis", "window_days"],
            rows))
    return sections, found, failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--property-id", default=DEFAULT_GA4_PROPERTY_ID)
    args = parser.parse_args(argv)
    try:
        dates = window_dates(args.start, args.end)
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print(f"# Diagnostic window {args.start}..{args.end} (read-only; no Clarity API call)")
    failures = []

    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google_connection_test import GA4_SCOPE, build_credentials, load_service_account_info

        client = BetaAnalyticsDataClient(
            credentials=build_credentials(load_service_account_info(), [GA4_SCOPE]))
        sections, errors = run_ga4(client, args.property_id, args.start, args.end)
        print("\n".join(sections))
        failures += [f"GA4 {e}" for e in errors]
    except (Exception, SystemExit) as exc:  # noqa: BLE001 — load/build helpers sys.exit
        failures.append(f"GA4 unavailable: {describe_error(exc)}")

    try:
        from storage_gcs import store_from_env

        sections, found, read_failures = clarity_section(store_from_env(), dates)
        failures += read_failures
        print("\n".join(sections))
        print(f"\nClarity snapshots found: {len(found)}/{len(dates)} ({', '.join(found) or 'none'})")
    except (Exception, SystemExit) as exc:  # noqa: BLE001
        failures.append(f"Clarity history unavailable: {describe_error(exc)}")

    for failure in failures:
        print(f"WARN {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
