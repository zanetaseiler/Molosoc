#!/usr/bin/env python3
"""
Molosoc analytics: read-only connection test for GA4 + Google Search Console.

Proves that the service account in GOOGLE_SERVICE_ACCOUNT_JSON can authenticate
and read from both properties. Nothing here writes: the GA4 side only calls
runReport, the Search Console side only calls sites.list and
searchAnalytics.query. Both are GET/POST read endpoints and both credentials
are requested with *.readonly scopes, so even a mistake can't mutate anything
upstream.

Credentials never reach stdout. The JSON is parsed in memory, the service
account email is masked before printing, and every error message is passed
through redact() so a stack trace or an API error echoing the payload can't
leak the private key.

Usage:
    export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
    python3 automations/analytics/google_connection_test.py

    # or point at a key file instead (local dev)
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
    python3 automations/analytics/google_connection_test.py

Exit code is 0 only when both GA4 and Search Console authenticate and return a
well-formed response. "Authenticated but zero rows" is a pass, not a failure —
a brand-new property legitimately has no data yet, and that is reported
explicitly rather than being mistaken for a broken connection.
"""

import argparse
import base64
import binascii
import datetime as dt
import json
import os
import re
import sys
from urllib.parse import quote

# Defaults for the Molosoc properties. Neither value is a secret — the GA4
# property id and the Search Console property string are both visible in the
# respective UIs — so they live here rather than in GitHub secrets, and can
# still be overridden per-run via env vars or CLI flags.
DEFAULT_GA4_PROPERTY_ID = "521643495"
DEFAULT_GSC_SITE_URL = "sc-domain:molosoc.com"

GA4_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

GSC_API_BASE = "https://searchconsole.googleapis.com/webmasters/v3"

# Search Console finalises data on a 2-3 day lag, so a window ending today is
# usually empty and would read as a broken connection. Default the window to
# end 3 days back. GA4 has no equivalent lag and ends yesterday.
GSC_LAG_DAYS = 3

HTTP_TIMEOUT = 60

_REDACT_PATTERNS = [
    # PEM blocks, with or without the \n escaping used inside JSON.
    re.compile(r"-----BEGIN[^-]*PRIVATE KEY-----.*?-----END[^-]*PRIVATE KEY-----", re.S),
    # Any JSON field whose name suggests a secret, e.g. "private_key": "...".
    re.compile(r'"(private_key|private_key_id|client_secret|refresh_token|access_token)"\s*:\s*"[^"]*"'),
    # Bearer tokens in case an HTTP layer echoes a request header.
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
]


def redact(text):
    """Strip anything credential-shaped out of a string before it is printed."""
    out = str(text)
    for pattern in _REDACT_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def mask_email(email):
    """mo***@molosoc-analytics.iam.gserviceaccount.com — enough to identify the
    service account when debugging a permission error, not enough to be a
    useful copy/paste of the identity into somewhere it doesn't belong."""
    if not email or "@" not in email:
        return "<unknown>"
    local, _, domain = email.partition("@")
    return f"{local[:2]}***@{domain}"


def _decode_key_material(raw):
    """Accept the key as raw JSON or as base64-encoded JSON.

    Base64 is supported because it survives copy/paste into secret stores that
    mangle newlines — a common way for the private_key field to arrive broken.
    """
    text = raw.strip()
    if text.startswith("{"):
        return text
    try:
        decoded = base64.b64decode(text, validate=True).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return text
    return decoded.strip()


def load_service_account_info():
    """Return the parsed service account dict from env, or exit with a message
    that never contains the payload itself."""
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    source = "GOOGLE_SERVICE_ACCOUNT_JSON"

    if not raw.strip():
        key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if not key_path:
            sys.exit(
                "Missing credentials: set GOOGLE_SERVICE_ACCOUNT_JSON (the service "
                "account JSON, raw or base64) or GOOGLE_APPLICATION_CREDENTIALS "
                "(path to a key file)."
            )
        if not os.path.isfile(key_path):
            sys.exit(f"GOOGLE_APPLICATION_CREDENTIALS points at a missing file: {key_path}")
        with open(key_path, "r", encoding="utf-8") as handle:
            raw = handle.read()
        source = f"GOOGLE_APPLICATION_CREDENTIALS ({key_path})"

    try:
        info = json.loads(_decode_key_material(raw))
    except json.JSONDecodeError as exc:
        # Deliberately reports only the position, never the content.
        sys.exit(
            f"Could not parse the credentials from {source} as JSON "
            f"(error at line {exc.lineno}, column {exc.colno}). "
            "Expected the full service account JSON, raw or base64-encoded."
        )

    if not isinstance(info, dict):
        sys.exit(f"Credentials from {source} are not a JSON object.")

    missing = [f for f in ("type", "client_email", "private_key", "token_uri") if not info.get(f)]
    if missing:
        sys.exit(
            f"Credentials from {source} are missing required field(s): {', '.join(missing)}. "
            "Expected a service account key, not an OAuth client or an API key."
        )

    return info


def build_credentials(info, scopes):
    from google.oauth2 import service_account

    try:
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    except Exception as exc:  # noqa: BLE001 — surfaced as a clean message below
        sys.exit(f"Could not build credentials from the service account key: {redact(exc)}")


def date_window(days, end_offset_days):
    """Inclusive [start, end] window of `days` days, ending `end_offset_days`
    before today, as YYYY-MM-DD strings."""
    end = dt.date.today() - dt.timedelta(days=end_offset_days)
    start = end - dt.timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


# --------------------------------------------------------------------------
# GA4
# --------------------------------------------------------------------------

def run_ga4_checks(client, property_id, start_date, end_date):
    """Pull two small read-only reports: site totals and top landing pages.

    Takes the client as an argument so tests can drive it with a stub instead
    of real credentials.
    """
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        OrderBy,
        RunReportRequest,
    )

    prop = f"properties/{property_id}"
    date_range = DateRange(start_date=start_date, end_date=end_date)

    totals_response = client.run_report(
        RunReportRequest(
            property=prop,
            date_ranges=[date_range],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="screenPageViews"),
            ],
        )
    )

    totals = {"activeUsers": 0, "sessions": 0, "screenPageViews": 0}
    for row in totals_response.rows:
        for header, value in zip(totals_response.metric_headers, row.metric_values):
            totals[header.name] = _as_number(value.value)

    landing_response = client.run_report(
        RunReportRequest(
            property=prop,
            date_ranges=[date_range],
            dimensions=[Dimension(name="landingPagePlusQueryString")],
            metrics=[Metric(name="sessions"), Metric(name="activeUsers")],
            order_bys=[
                OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)
            ],
            limit=5,
        )
    )

    landing_pages = [
        {
            "landingPage": row.dimension_values[0].value,
            "sessions": _as_number(row.metric_values[0].value),
            "activeUsers": _as_number(row.metric_values[1].value),
        }
        for row in landing_response.rows
    ]

    return {
        "propertyId": str(property_id),
        "dateRange": {"start": start_date, "end": end_date},
        "users": totals["activeUsers"],
        "sessions": totals["sessions"],
        "views": totals["screenPageViews"],
        "landingPages": landing_pages,
        "rowCount": int(getattr(totals_response, "row_count", 0) or 0),
    }


def _as_number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0


def check_ga4(info, property_id, days):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient

    start_date, end_date = date_window(days, end_offset_days=1)
    credentials = build_credentials(info, [GA4_SCOPE])

    try:
        client = BetaAnalyticsDataClient(credentials=credentials)
        data = run_ga4_checks(client, property_id, start_date, end_date)
    except Exception as exc:  # noqa: BLE001 — reported, not raised, so GSC still runs
        return {"ok": False, "error": _describe_error(exc), "propertyId": str(property_id)}

    return {"ok": True, **data}


# --------------------------------------------------------------------------
# Search Console
# --------------------------------------------------------------------------

def run_gsc_checks(session, site_url, start_date, end_date):
    """Confirm the property is visible to the service account, then pull
    totals, top queries and top pages. All read-only."""
    sites = _gsc_request(session, "GET", f"{GSC_API_BASE}/sites")
    visible = [entry.get("siteUrl") for entry in sites.get("siteEntry", [])]
    if site_url not in visible:
        raise PermissionError(
            f"{site_url} is not in the list of properties this service account can "
            f"see ({len(visible)} visible). Add the service account as a user on the "
            "property in Search Console."
        )

    query_url = f"{GSC_API_BASE}/sites/{quote(site_url, safe='')}/searchAnalytics/query"
    base_body = {"startDate": start_date, "endDate": end_date, "type": "web"}

    # No dimensions => a single row of property-wide totals.
    totals_rows = _gsc_request(
        session, "POST", query_url, json={**base_body, "rowLimit": 1}
    ).get("rows", [])
    totals = _gsc_row_metrics(totals_rows[0]) if totals_rows else _gsc_row_metrics({})

    top_queries = [
        {"query": row.get("keys", [""])[0], **_gsc_row_metrics(row)}
        for row in _gsc_request(
            session, "POST", query_url, json={**base_body, "dimensions": ["query"], "rowLimit": 5}
        ).get("rows", [])
    ]

    top_pages = [
        {"page": row.get("keys", [""])[0], **_gsc_row_metrics(row)}
        for row in _gsc_request(
            session, "POST", query_url, json={**base_body, "dimensions": ["page"], "rowLimit": 5}
        ).get("rows", [])
    ]

    return {
        "siteUrl": site_url,
        "dateRange": {"start": start_date, "end": end_date},
        "visiblePropertyCount": len(visible),
        **totals,
        "topQueries": top_queries,
        "topPages": top_pages,
    }


def _gsc_row_metrics(row):
    return {
        "clicks": _as_number(row.get("clicks", 0)),
        "impressions": _as_number(row.get("impressions", 0)),
        "ctr": float(row.get("ctr", 0.0) or 0.0),
        "position": float(row.get("position", 0.0) or 0.0),
    }


def _gsc_request(session, method, url, **kwargs):
    response = session.request(method, url, timeout=HTTP_TIMEOUT, **kwargs)
    if response.status_code >= 400:
        # Google returns a JSON error envelope; fall back to raw text, redacted.
        try:
            detail = response.json().get("error", {}).get("message", "")
        except ValueError:
            detail = response.text[:500]
        raise RuntimeError(f"HTTP {response.status_code} from {url.split('?')[0]}: {redact(detail)}")
    return response.json()


def check_search_console(info, site_url, days):
    from google.auth.transport.requests import AuthorizedSession

    start_date, end_date = date_window(days, end_offset_days=GSC_LAG_DAYS)
    credentials = build_credentials(info, [GSC_SCOPE])

    try:
        session = AuthorizedSession(credentials)
        data = run_gsc_checks(session, site_url, start_date, end_date)
    except Exception as exc:  # noqa: BLE001 — reported, not raised
        return {"ok": False, "error": _describe_error(exc), "siteUrl": site_url}

    return {"ok": True, **data}


def _describe_error(exc):
    return f"{type(exc).__name__}: {redact(exc)}"


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def print_ga4_result(result):
    print("\n--- Google Analytics 4 ---")
    if not result["ok"]:
        print(f"FAIL  property {result['propertyId']}")
        print(f"      {result['error']}")
        return

    window = result["dateRange"]
    print(f"PASS  property {result['propertyId']}  ({window['start']} to {window['end']}, 7 days)")
    print(f"      users:    {result['users']}")
    print(f"      sessions: {result['sessions']}")
    print(f"      views:    {result['views']}")
    if result["landingPages"]:
        print("      top landing pages by sessions:")
        for row in result["landingPages"]:
            print(f"        {row['sessions']:>6} sessions  {row['activeUsers']:>6} users  {row['landingPage']}")
    else:
        print("      top landing pages: no rows returned for this window "
              "(authenticated fine — the property simply has no traffic yet)")


def print_gsc_result(result):
    print("\n--- Google Search Console ---")
    if not result["ok"]:
        print(f"FAIL  {result['siteUrl']}")
        print(f"      {result['error']}")
        return

    window = result["dateRange"]
    print(f"PASS  {result['siteUrl']}  ({window['start']} to {window['end']}, 7 days)")
    print(f"      properties visible to this service account: {result['visiblePropertyCount']}")
    print(f"      clicks:           {result['clicks']}")
    print(f"      impressions:      {result['impressions']}")
    print(f"      CTR:              {result['ctr'] * 100:.2f}%")
    print(f"      avg position:     {result['position']:.2f}")

    if result["topQueries"]:
        print("      top queries:")
        for row in result["topQueries"]:
            print(f"        {row['clicks']:>5} clicks  {row['impressions']:>6} impr  "
                  f"pos {row['position']:>6.2f}  {row['query']}")
    else:
        print("      top queries: no rows for this window "
              "(authenticated fine — no search data yet)")

    if result["topPages"]:
        print("      top pages:")
        for row in result["topPages"]:
            print(f"        {row['clicks']:>5} clicks  {row['impressions']:>6} impr  "
                  f"pos {row['position']:>6.2f}  {row['page']}")
    else:
        print("      top pages: no rows for this window "
              "(authenticated fine — no search data yet)")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only GA4 + Search Console connection test for Molosoc."
    )
    parser.add_argument(
        "--property-id",
        default=os.environ.get("GA4_PROPERTY_ID", DEFAULT_GA4_PROPERTY_ID),
        help=f"GA4 numeric property id (default: {DEFAULT_GA4_PROPERTY_ID})",
    )
    parser.add_argument(
        "--site-url",
        default=os.environ.get("GSC_SITE_URL", DEFAULT_GSC_SITE_URL),
        help=f"Search Console property (default: {DEFAULT_GSC_SITE_URL})",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Length of the reporting window in days (default: 7)"
    )
    parser.add_argument(
        "--skip-ga4", action="store_true", help="Only test Search Console"
    )
    parser.add_argument(
        "--skip-search-console", action="store_true", help="Only test GA4"
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    info = load_service_account_info()

    print("Molosoc — Google read-only connection test")
    print(f"  service account: {mask_email(info.get('client_email'))}")
    print(f"  project:         {info.get('project_id', '<unknown>')}")
    print("  mode:            read-only (runReport, sites.list, searchAnalytics.query)")

    results = []

    if args.skip_ga4:
        print("\n--- Google Analytics 4 ---\nSKIPPED (--skip-ga4)")
    else:
        ga4 = check_ga4(info, args.property_id, args.days)
        print_ga4_result(ga4)
        results.append(ga4["ok"])

    if args.skip_search_console:
        print("\n--- Google Search Console ---\nSKIPPED (--skip-search-console)")
    else:
        gsc = check_search_console(info, args.site_url, args.days)
        print_gsc_result(gsc)
        results.append(gsc["ok"])

    passed = all(results) and bool(results)
    print("\n" + ("All checked integrations authenticated and returned data."
                  if passed else "One or more integrations failed — see above."))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
