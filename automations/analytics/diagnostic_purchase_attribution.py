#!/usr/bin/env python3
"""
Purchase-attribution diagnostic (read-only): GA4 Data API only (Issue #112).

GA4 shows purchase attribution as `(not set)` while WooCommerce keeps
`ig / paid`. This prints the evidence needed to say where the session identity
is lost, for a short window (default: 2026-10-05, the day of order 1026):

  1. purchase events: hits per transactionId (duplicate check), hits by
     hostName x pagePath, and per-transactionId attribution (session,
     session-manual, first-user, event-scoped) with purchase metrics;
  2. an aggregate event inventory (eventName x pagePath, and x pageReferrer) of
     sessions whose sessionSourceMedium is `(not set)`, including whether
     `session_start` exists. These are counts only: no session id, timestamp or
     event order, so they do NOT establish an event path or funnel sequence;
  3. whether `ga_session_id` / `client_id` are registered as custom
     dimensions (property metadata), i.e. whether they can be reported at all.

Only runReport and getMetadata calls are made. Nothing is written, no GA4,
WordPress, WooCommerce, WPConsent or GTM setting is touched. A dimension or
metric GA4 rejects is reported and skipped; it never aborts the other
reports, and an absent value is never turned into a zero.

Usage:
    export GOOGLE_SERVICE_ACCOUNT_JSON='...'
    python3 automations/analytics/diagnostic_purchase_attribution.py [--start D --end D]
"""

import argparse
import sys

from analytics_common import describe_error
from diagnostic_window import table, window_dates
from google_hydrate import DEFAULT_GA4_PROPERTY_ID

DEFAULT_START = "2026-10-05"
DEFAULT_END = "2026-10-05"
MAX_DAYS = 7
NOT_SET = "(not set)"
SESSION_IDENTITY_NAMES = ("ga_session_id", "client_id")

PURCHASE_METRICS = ("eventCount", "purchaseRevenue", "ecommercePurchases")
PATH_METRICS = ("eventCount", "totalUsers")

# Purchase reports carry transactionId so each attribution row stays tied to its
# order (a row can never blend several orders' metrics). The two aggregate
# reports in AGGREGATE_PURCHASE_REPORTS deliberately do not: they count purchase
# hits per transactionId (duplicates) and per host / page.
# (title, dimensions, metrics, row limit, (filter field, value)). Dimension
# groups are split because GA4 rejects some scope combinations; each report
# succeeds or fails on its own. The event-scoped attribution dimensions are
# requested one group at a time with transactionId: the single combined query
# (manualSourceMedium + source + medium) was rejected by GA4 as incompatible.
PURCHASE_FILTER = ("eventName", "purchase")
AGGREGATE_PURCHASE_REPORTS = (
    ("Purchase: hits per transactionId (duplicate check)", ("transactionId",),
     ("eventCount",), 100, PURCHASE_FILTER),
    ("Purchase: hits by host and page", ("hostName", "pagePath"),
     ("eventCount",), 100, PURCHASE_FILTER),
)
PURCHASE_REPORTS = (
    ("Purchase: transaction, host, page", ("transactionId", "hostName", "pagePath"),
     PURCHASE_METRICS, 50, PURCHASE_FILTER),
    ("Purchase: session-scoped attribution",
     ("transactionId", "sessionSourceMedium", "sessionManualSourceMedium",
      "sessionDefaultChannelGroup", "landingPage"), PURCHASE_METRICS, 50, PURCHASE_FILTER),
    ("Purchase: first-user attribution",
     ("transactionId", "firstUserSourceMedium", "firstUserManualSourceMedium"),
     PURCHASE_METRICS, 50, PURCHASE_FILTER),
    ("Purchase: event-scoped manual source / medium",
     ("transactionId", "manualSourceMedium"), ("eventCount",), 50, PURCHASE_FILTER),
    ("Purchase: event-scoped source",
     ("transactionId", "source"), ("eventCount",), 50, PURCHASE_FILTER),
    ("Purchase: event-scoped medium",
     ("transactionId", "medium"), ("eventCount",), 50, PURCHASE_FILTER),
)
NOT_SET_REPORTS = (
    ("(not set) sessions: aggregate event inventory by page", ("eventName", "pagePath"), PATH_METRICS, 200,
     ("sessionSourceMedium", NOT_SET)),
    ("(not set) sessions: aggregate event inventory by referrer", ("eventName", "pageReferrer"),
     PATH_METRICS, 200, ("sessionSourceMedium", NOT_SET)),
    ("(not set) sessions: landing page and device",
     ("landingPage", "deviceCategory", "sessionDefaultChannelGroup"),
     ("sessions", "engagedSessions", "totalUsers"), 50, ("sessionSourceMedium", NOT_SET)),
    ("All sessions: events by source / medium", ("sessionSourceMedium", "eventName"),
     ("eventCount",), 500, ("eventName", "session_start")),
)


def ga4_report(client, property_id, start, end, dimensions, metrics, limit, match):
    """One read-only runReport with an exact-match dimension filter."""
    from google.analytics.data_v1beta.types import (
        DateRange, Dimension, Filter, FilterExpression, Metric, OrderBy,
        RunReportRequest,
    )

    field, value = match
    response = client.run_report(RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        dimension_filter=FilterExpression(filter=Filter(
            field_name=field,
            string_filter=Filter.StringFilter(
                value=value, match_type=Filter.StringFilter.MatchType.EXACT))),
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name=metrics[0]), desc=True)],
        limit=limit))
    return [[v.value for v in r.dimension_values] + [v.value for v in r.metric_values]
            for r in response.rows]


def run_reports(client, property_id, start, end, reports):
    sections, errors = [], []
    for title, dims, metrics, limit, match in reports:
        try:
            rows = ga4_report(client, property_id, start, end, dims, metrics, limit, match)
        except Exception as exc:  # noqa: BLE001 — reported, redacted, skipped
            errors.append(f"{title}: {describe_error(exc)}")
            sections.append(f"\n### GA4 — {title}\n(REPORT FAILED, not checked)")
            continue
        note = (f"\n(WARN: GA4 row limit {limit} reached; rows may be truncated)"
                if len(rows) >= limit else "")
        sections.append(table(f"GA4 — {title} [{match[0]} = {match[1]}]",
                              list(dims) + list(metrics), rows) + note)
    return sections, errors


def classify_identity_dimensions(api_names):
    """Which of ga_session_id / client_id are registered custom dimensions.

    `api_names` are the property's dimension API names (from getMetadata).
    The suffix is compared exactly (case-sensitive): `customUser:Client_ID` does
    not register `client_id`.
    Returns {name: [matching api names]}; an empty list means NOT registered
    (so not reportable), never "absent from the data".
    """
    found = {name: [] for name in SESSION_IDENTITY_NAMES}
    for api_name in api_names:
        if not api_name.startswith(("customEvent:", "customUser:")):
            continue
        suffix = api_name.split(":", 1)[1]
        for name in SESSION_IDENTITY_NAMES:
            if suffix == name:
                found[name].append(api_name)
    return found


def identity_section(client, property_id):
    name = f"properties/{property_id}/metadata"
    try:
        metadata = client.get_metadata(name=name)
    except Exception as exc:  # noqa: BLE001
        return ("\n### GA4 — ga_session_id / client_id custom dimensions\n"
                "(METADATA CALL FAILED, not checked)"), [
            f"metadata: {describe_error(exc)}"]
    api_names = [d.api_name for d in metadata.dimensions]
    custom = sorted(n for n in api_names if n.startswith(("customEvent:", "customUser:")))
    found = classify_identity_dimensions(api_names)
    lines = ["\n### GA4 — ga_session_id / client_id custom dimensions"]
    for ident in SESSION_IDENTITY_NAMES:
        lines.append(f"{ident}: " + (", ".join(found[ident]) if found[ident]
                                     else "NOT registered as a custom dimension"))
    lines.append(f"registered custom dimensions ({len(custom)}): " + (", ".join(custom) or "none"))
    return "\n".join(lines), []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--property-id", default=DEFAULT_GA4_PROPERTY_ID)
    args = parser.parse_args(argv)
    try:
        dates = window_dates(args.start, args.end)
        if len(dates) > MAX_DAYS:
            raise ValueError(f"window longer than {MAX_DAYS} days; this is a narrow diagnostic")
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print(f"# Purchase attribution diagnostic {args.start}..{args.end} (read-only GA4 Data API)")
    failures = []
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google_connection_test import GA4_SCOPE, build_credentials, load_service_account_info

        client = BetaAnalyticsDataClient(
            credentials=build_credentials(load_service_account_info(), [GA4_SCOPE]))
        for reports in (AGGREGATE_PURCHASE_REPORTS, PURCHASE_REPORTS, NOT_SET_REPORTS):
            sections, errors = run_reports(client, args.property_id, args.start, args.end, reports)
            print("\n".join(sections))
            failures += [f"GA4 {e}" for e in errors]
        section, errors = identity_section(client, args.property_id)
        print(section)
        failures += [f"GA4 {e}" for e in errors]
    except (Exception, SystemExit) as exc:  # noqa: BLE001 — load/build helpers sys.exit
        failures.append(f"GA4 unavailable: {describe_error(exc)}")

    for failure in failures:
        print(f"WARN {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
