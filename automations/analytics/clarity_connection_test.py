#!/usr/bin/env python3
"""
Molosoc analytics: read-only connection test for Microsoft Clarity.

Proves that CLARITY_API_TOKEN can authenticate against the Project Live
Insights API and read behavioural/UX data. Read-only: the Data Export API
exposes no write operation at all, and this script only issues a single GET.

RATE LIMIT — READ THIS BEFORE CHANGING ANYTHING HERE.
Clarity allows 10 API calls per project per day, shared across everything that
talks to the project. This script therefore makes exactly ONE call per run, and
the tests assert that. Do not add a second request "just to check something",
and do not loop or retry on a successful-but-empty response: a retry storm
would exhaust the day's budget and lock out the real reporting job later.
Failed calls are not retried for the same reason.

The token is never printed. It is read from the environment, registered with
the shared redactor so any error text quoting it is scrubbed, and only ever
sent in an Authorization header — never in a URL, a log line, or an exception
message.

Usage:
    export CLARITY_API_TOKEN='...'
    python3 automations/analytics/clarity_connection_test.py

Exit code is 0 when Clarity authenticates and returns a well-formed response.
An authenticated project with no data in the window is a pass, reported
explicitly — only auth, permission, rate-limit and malformed-response failures
exit non-zero.
"""

import argparse
import os
import sys

import requests

from analytics_common import as_number, describe_error, redact, register_secret

CLARITY_API_URL = "https://www.clarity.ms/export-data/api/v1/project-live-insights"

# The API accepts 1, 2 or 3 — the last 24, 48 or 72 hours. Nothing longer is
# available from this endpoint.
ALLOWED_NUM_DAYS = (1, 2, 3)
DEFAULT_NUM_DAYS = 3

# Optional breakdown dimensions the endpoint accepts. Passing a value outside
# this set makes Clarity return an empty body rather than an error, which then
# fails to parse as JSON — so validate locally instead of spending a call to
# find out.
ALLOWED_DIMENSIONS = (
    "Browser", "Device", "Country", "OS", "Source", "Medium", "Campaign", "Channel", "URL",
)

DAILY_CALL_BUDGET = 10
HTTP_TIMEOUT = 60

# How many fields of a metric's first row to print. Enough to see the shape of
# what came back without dumping the whole payload into a CI log.
MAX_FIELDS_SHOWN = 8


def load_api_token():
    """Return the Clarity token from the environment, or exit with guidance.

    The value is registered with the redactor immediately, so from this point
    on any string containing it is scrubbed before printing.
    """
    token = os.environ.get("CLARITY_API_TOKEN", "").strip()
    if not token:
        sys.exit(
            "Missing credentials: set CLARITY_API_TOKEN (the Clarity project API "
            "token, generated under Settings -> Data Export in the Clarity project)."
        )
    register_secret(token)
    return token


def validate_request(num_days, dimensions):
    """Reject bad arguments locally, before spending one of the day's calls."""
    if num_days not in ALLOWED_NUM_DAYS:
        sys.exit(
            f"--num-days must be one of {', '.join(str(d) for d in ALLOWED_NUM_DAYS)} "
            f"(the last 24/48/72 hours); got {num_days}."
        )

    unknown = [d for d in dimensions if d not in ALLOWED_DIMENSIONS]
    if unknown:
        sys.exit(
            f"Unknown Clarity dimension(s): {', '.join(unknown)}. "
            f"Allowed: {', '.join(ALLOWED_DIMENSIONS)}."
        )

    if len(dimensions) > 3:
        sys.exit("Clarity accepts at most 3 dimensions per request.")


def fetch_live_insights(session, token, num_days, dimensions):
    """Make the one and only API call and return the parsed body.

    Exactly one request. No retries — see the rate-limit note at the top.
    """
    params = {"numOfDays": str(num_days)}
    for index, dimension in enumerate(dimensions, start=1):
        params[f"dimension{index}"] = dimension

    response = session.get(
        CLARITY_API_URL,
        params=params,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=HTTP_TIMEOUT,
    )

    if response.status_code == 401:
        raise PermissionError(
            "401 Unauthorized — CLARITY_API_TOKEN was rejected. The token may be "
            "expired, revoked, or generated for a different Clarity project."
        )
    if response.status_code == 403:
        raise PermissionError(
            "403 Forbidden — the token authenticated but is not allowed to read "
            "this project's live insights."
        )
    if response.status_code == 429:
        raise RuntimeError(
            f"429 Too Many Requests — Clarity's limit of {DAILY_CALL_BUDGET} calls per "
            "project per day is exhausted. It resets on Clarity's daily schedule; do "
            "not retry in a loop."
        )
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code} from Clarity: {redact(response.text[:500])}")

    # A valid token with an out-of-range dimension returns 200 and an empty
    # body, which is not JSON. Say so plainly instead of surfacing a decode error.
    if not (response.text or "").strip():
        raise RuntimeError(
            "Clarity returned an empty body with HTTP 200. This usually means a "
            "dimension value the API does not recognise; the request itself "
            "authenticated fine."
        )

    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"Clarity returned a non-JSON body: {redact(exc)}") from exc


def summarise_insights(payload):
    """Normalise the response into [{name, rowCount, sample}] without assuming
    which metrics Clarity chose to return.

    The endpoint's metric list varies by project and by what data exists, so
    this reads whatever came back rather than hard-coding field names. That
    matters when you only get one call to get it right.
    """
    if isinstance(payload, dict):
        # Some responses wrap the array; take the first list-valued key.
        payload = next(
            (value for value in payload.values() if isinstance(value, list)),
            [payload],
        )

    if not isinstance(payload, list):
        raise RuntimeError(
            f"Unexpected Clarity response shape: expected a list of metrics, got "
            f"{type(payload).__name__}."
        )

    metrics = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        rows = entry.get("information") or []
        if not isinstance(rows, list):
            rows = [rows]
        sample = rows[0] if rows and isinstance(rows[0], dict) else {}
        metrics.append({
            "name": str(entry.get("metricName", "<unnamed>")),
            "rowCount": len(rows),
            "sample": sample,
        })
    return metrics


def check_clarity(token, num_days, dimensions, session=None):
    """Run the single read-only call and shape the result like the GA4 and
    Search Console checks, so all three report identically."""
    try:
        session = session or requests.Session()
        payload = fetch_live_insights(session, token, num_days, dimensions)
        metrics = summarise_insights(payload)
    except Exception as exc:  # noqa: BLE001 — reported, not raised
        return {
            "ok": False,
            "error": describe_error(exc),
            "numDays": num_days,
            "dimensions": list(dimensions),
            "apiCallsMade": 1,
        }

    return {
        "ok": True,
        "numDays": num_days,
        "dimensions": list(dimensions),
        "apiCallsMade": 1,
        "metrics": metrics,
    }


def format_sample(sample):
    """One readable line of a metric's first row, redacted and truncated."""
    if not sample:
        return "(no rows)"
    parts = []
    for key, value in list(sample.items())[:MAX_FIELDS_SHOWN]:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            value = as_number(value)
        text = redact(value)
        if len(text) > 60:
            text = text[:57] + "..."
        parts.append(f"{key}={text}")
    if len(sample) > MAX_FIELDS_SHOWN:
        parts.append(f"(+{len(sample) - MAX_FIELDS_SHOWN} more fields)")
    return ", ".join(parts)


def print_clarity_result(result):
    print("\n--- Microsoft Clarity ---")
    window = f"last {result['numDays']} day(s)"
    breakdown = ", ".join(result["dimensions"]) if result["dimensions"] else "none"

    if not result["ok"]:
        print(f"FAIL  project live insights ({window})")
        print(f"      {result['error']}")
        print(f"      API calls used this run: {result['apiCallsMade']} "
              f"of {DAILY_CALL_BUDGET}/project/day")
        return

    print(f"PASS  project live insights ({window}, dimensions: {breakdown})")
    print(f"      API calls used this run: {result['apiCallsMade']} "
          f"of {DAILY_CALL_BUDGET}/project/day")

    if not result["metrics"]:
        print("      no metrics returned for this window "
              "(authenticated fine — the project has no data in the last "
              f"{result['numDays']} day(s))")
        return

    print(f"      metrics returned: {len(result['metrics'])}")
    for metric in result["metrics"]:
        rows = f"{metric['rowCount']} row(s)"
        print(f"        {metric['name']} [{rows}]: {format_sample(metric['sample'])}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Read-only Microsoft Clarity connection test for Molosoc. Makes exactly "
            f"one API call (Clarity allows {DAILY_CALL_BUDGET} per project per day)."
        )
    )
    parser.add_argument(
        "--num-days",
        type=int,
        default=int(os.environ.get("CLARITY_NUM_DAYS", DEFAULT_NUM_DAYS)),
        choices=ALLOWED_NUM_DAYS,
        help=f"Window in days: 1, 2 or 3 (default: {DEFAULT_NUM_DAYS})",
    )
    parser.add_argument(
        "--dimension",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Optional breakdown dimension, repeatable up to 3 times. "
            f"One of: {', '.join(ALLOWED_DIMENSIONS)}. Adding dimensions does not "
            "cost extra calls, but changes which rows come back."
        ),
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    dimensions = list(args.dimension)
    validate_request(args.num_days, dimensions)

    token = load_api_token()

    print("Molosoc — Microsoft Clarity read-only connection test")
    print("  endpoint:  project-live-insights")
    print("  auth:      CLARITY_API_TOKEN (bearer, never printed)")
    print(f"  budget:    1 call this run, of {DAILY_CALL_BUDGET} per project per day")

    result = check_clarity(token, args.num_days, dimensions)
    print_clarity_result(result)

    print("\n" + ("Clarity authenticated and returned data."
                  if result["ok"] else "Clarity check failed — see above."))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
