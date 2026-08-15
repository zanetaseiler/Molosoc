#!/usr/bin/env python3
"""
Read-only Microsoft Clarity Project Live Insights client.

Extracted unchanged from clarity_connection_test.py so the connection test and
the daily collector share one implementation rather than drifting apart. The
connection test re-exports these names, and its existing tests continue to
exercise them.

The endpoint has no write operation. This module only ever issues GET.

RATE LIMIT: Clarity allows 10 calls per project per day, shared with everything
else reading the project. fetch_live_insights makes exactly one request and
never retries — a retry storm would exhaust the day's budget and lock out the
collector. Callers reserve budget before calling; see call_budget.py.
"""

import os
import sys

from analytics_common import redact, register_secret

CLARITY_API_URL = "https://www.clarity.ms/export-data/api/v1/project-live-insights"

# The API accepts 1, 2 or 3 — the last 24, 48 or 72 hours. Nothing longer is
# available from this endpoint, which is why history has to be accumulated.
ALLOWED_NUM_DAYS = (1, 2, 3)
DEFAULT_NUM_DAYS = 3

# Optional breakdown dimensions. A value outside this set makes Clarity return
# an empty body rather than an error, so validate locally instead of spending a
# call to find out.
ALLOWED_DIMENSIONS = (
    "Browser", "Device", "Country", "OS", "Source", "Medium", "Campaign", "Channel", "URL",
)

DAILY_CALL_BUDGET = 10
HTTP_TIMEOUT = 60


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
