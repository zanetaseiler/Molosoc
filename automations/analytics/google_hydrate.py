#!/usr/bin/env python3
"""
Hydrate GA4 and Search Console for an analysis window, on demand.

GA4 and Search Console can reconstruct any past period, so they need no daily
collection — the agent asks for exactly the windows it is about to compare and
normalizes the answers through the Phase 1 model. Clarity is the opposite: its
API cannot return history, so it comes only from the durable ledger. Nothing
here touches Clarity.

Read-only throughout. This calls the same verified read-only functions the
connection tests use (`run_ga4_checks`, `run_gsc_checks`), with the analysis
window's dates rather than a fixed lookback.

Determinism and cost control:

* Results are cached per (source, start, end) for the life of the hydrator, so
  a window requested twice in one run costs one set of calls. `calls_made`
  reports the real total.
* Fetchers are injected, so the whole layer is exercised offline against
  fixtures with no credentials and no network.

Conversions are never fabricated. If GA4 does not return `purchase`, no
purchase record is created and the run reports why — a zero would read as "no
sales", which is a different and much worse claim than "not measured".
"""

from analytics_common import describe_error
from normalize import (
    HEADLINE_CONVERSION, SUPPORTING_FUNNEL_EVENTS, TRACKED_KEY_EVENTS,
    ga4_records, gsc_records,
)
from records import utc_now_iso

DEFAULT_GA4_PROPERTY_ID = "521643495"
DEFAULT_GSC_SITE_URL = "sc-domain:molosoc.com"

# Conversion readiness states, surfaced in the report's data-quality section.
CONVERSIONS_OK = "ok"
CONVERSIONS_MISSING_PRIMARY = "missing_primary_conversion"
CONVERSIONS_NONE = "no_key_events"
CONVERSIONS_NOT_FETCHED = "not_fetched"


class HydrationResult:
    """Records for one window, plus what it cost and what was missing."""

    __slots__ = ("records", "window", "calls_made", "errors", "key_events")

    def __init__(self, records, window, calls_made=0, errors=(), key_events=None):
        self.records = records
        self.window = window
        self.calls_made = calls_made
        self.errors = tuple(errors)
        self.key_events = key_events or {}

    @property
    def ok(self):
        return not self.errors

    def __repr__(self):
        return f"HydrationResult({self.window.name}, {len(self.records)} records)"


class GoogleHydrator:
    """Fetches and normalizes GA4 + Search Console for arbitrary windows.

    `ga4_fetcher` and `gsc_fetcher` are callables taking (start_date, end_date)
    and returning the same result shape the verified connection checks produce.
    Passing fakes is how the offline tests run.
    """

    def __init__(self, ga4_fetcher=None, gsc_fetcher=None, collected_at=None):
        self.ga4_fetcher = ga4_fetcher
        self.gsc_fetcher = gsc_fetcher
        self.collected_at = collected_at or utc_now_iso()
        self._cache = {}
        self.calls_made = 0
        self.errors = []

    def _fetch(self, source, fetcher, window):
        """One cached fetch. A window asked for twice costs one call."""
        key = (source, window.start, window.end)
        if key in self._cache:
            return self._cache[key]
        if fetcher is None:
            self._cache[key] = None
            return None
        try:
            result = fetcher(window.start, window.end)
            self.calls_made += 1
        except Exception as exc:  # noqa: BLE001 — reported, redacted, not raised
            message = f"{source} hydration failed for {window.start}..{window.end}: " \
                      f"{describe_error(exc)}"
            self.errors.append(message)
            result = {"ok": False, "error": message}
        self._cache[key] = result
        return result

    def hydrate(self, window):
        """Normalized GA4 + Search Console records for one window."""
        records, errors, key_events = [], [], {}
        before = self.calls_made

        ga4 = self._fetch("ga4", self.ga4_fetcher, window)
        if ga4 and ga4.get("ok"):
            records += ga4_records(ga4, self.collected_at)
            key_events = ga4.get("keyEvents") or {}
        elif ga4 is not None:
            errors.append(ga4.get("error", "GA4 hydration returned no data"))

        gsc = self._fetch("gsc", self.gsc_fetcher, window)
        if gsc and gsc.get("ok"):
            records += gsc_records(gsc, self.collected_at)
        elif gsc is not None:
            errors.append(gsc.get("error", "Search Console hydration returned no data"))

        return HydrationResult(records, window, self.calls_made - before,
                               errors, key_events)

    def hydrate_all(self, windows):
        """Hydrate several windows, reusing the cache across them."""
        return {name: self.hydrate(window) for name, window in windows.items()}


# --------------------------------------------------------------------------
# Conversion readiness
# --------------------------------------------------------------------------

def assess_conversions(key_events, fetched=True):
    """Report whether GA4 is returning the commerce events the model needs.

    Never fabricates. A missing `purchase` produces a message, not a zero.
    """
    if not fetched:
        return {
            "state": CONVERSIONS_NOT_FETCHED,
            "primary": HEADLINE_CONVERSION,
            "present": [],
            "missing": [HEADLINE_CONVERSION] + list(SUPPORTING_FUNNEL_EVENTS),
            "message": "GA4 was not hydrated, so conversion data was not requested.",
        }

    present = [name for name in TRACKED_KEY_EVENTS if name in (key_events or {})]
    missing = [name for name in TRACKED_KEY_EVENTS if name not in present]

    if not present:
        message = (
            f"GA4 returned no key events. `{HEADLINE_CONVERSION}` is the primary "
            "business conversion for this analysis, so conversion trends, "
            "conversion-rate comparisons and every conversion-linked "
            "recommendation are unavailable until it is configured as a key "
            "event in GA4. No conversion figures have been inferred or "
            "substituted."
        )
        state = CONVERSIONS_NONE
    elif HEADLINE_CONVERSION not in present:
        message = (
            f"GA4 returned {', '.join(f'`{p}`' for p in present)} but not "
            f"`{HEADLINE_CONVERSION}`. Funnel steps are reported; the primary "
            "conversion is not, so conversion-rate analysis and any "
            "recommendation that depends on it remain unavailable. No purchase "
            "figure has been inferred."
        )
        state = CONVERSIONS_MISSING_PRIMARY
    else:
        message = (
            f"GA4 returned the primary conversion `{HEADLINE_CONVERSION}`"
            + (f" and {', '.join(f'`{p}`' for p in present if p != HEADLINE_CONVERSION)}"
               if len(present) > 1 else "")
            + "."
        )
        state = CONVERSIONS_OK

    return {
        "state": state,
        "primary": HEADLINE_CONVERSION,
        "present": present,
        "missing": missing,
        "message": message,
    }


def conversions_available(readiness):
    return readiness.get("state") == CONVERSIONS_OK


# --------------------------------------------------------------------------
# Live fetchers — thin wrappers over the verified read-only integrations
# --------------------------------------------------------------------------

def live_ga4_fetcher(service_account_info, property_id=DEFAULT_GA4_PROPERTY_ID):
    """Build a window-parameterised GA4 fetcher.

    Reuses run_ga4_checks from the verified connection test rather than
    reimplementing the report, and adds one key-events report so the conversion
    hierarchy can be populated when GA4 actually has it.
    """
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google_connection_test import GA4_SCOPE, build_credentials, run_ga4_checks

    credentials = build_credentials(service_account_info, [GA4_SCOPE])
    client = BetaAnalyticsDataClient(credentials=credentials)

    def fetch(start_date, end_date):
        data = run_ga4_checks(client, property_id, start_date, end_date)
        data["keyEvents"] = fetch_key_events(client, property_id, start_date, end_date)
        return {"ok": True, **data}

    return fetch


def fetch_key_events(client, property_id, start_date, end_date):
    """Read the tracked key events for a window.

    Returns only the events GA4 actually reports. An event the property has not
    configured is simply absent — it is never defaulted to zero, because zero
    means "none happened" and absent means "not measured".
    """
    from google.analytics.data_v1beta.types import (
        DateRange, Dimension, Metric, RunReportRequest,
    )

    response = client.run_report(RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=[Dimension(name="eventName")],
        metrics=[Metric(name="keyEvents")],
        limit=100,
    ))

    found = {}
    for row in response.rows:
        name = row.dimension_values[0].value
        if name not in TRACKED_KEY_EVENTS:
            continue
        try:
            count = float(row.metric_values[0].value)
        except (TypeError, ValueError):
            continue
        # A key event GA4 reports as 0 is still measured; keep it.
        found[name] = count
    return found


def live_gsc_fetcher(service_account_info, site_url=DEFAULT_GSC_SITE_URL):
    """Build a window-parameterised Search Console fetcher."""
    from google.auth.transport.requests import AuthorizedSession
    from google_connection_test import GSC_SCOPE, build_credentials, run_gsc_checks

    credentials = build_credentials(service_account_info, [GSC_SCOPE])
    session = AuthorizedSession(credentials)

    def fetch(start_date, end_date):
        data = run_gsc_checks(session, site_url, start_date, end_date)
        return {"ok": True, **data}

    return fetch


def live_hydrator(service_account_info=None, property_id=DEFAULT_GA4_PROPERTY_ID,
                  site_url=DEFAULT_GSC_SITE_URL, collected_at=None):
    """A hydrator wired to the real, verified read-only integrations."""
    from google_connection_test import load_service_account_info

    info = service_account_info or load_service_account_info()
    return GoogleHydrator(
        ga4_fetcher=live_ga4_fetcher(info, property_id),
        gsc_fetcher=live_gsc_fetcher(info, site_url),
        collected_at=collected_at,
    )
