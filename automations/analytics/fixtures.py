#!/usr/bin/env python3
"""
Deterministic fixtures for the analysis layer.

Not test-only: they are also how the report renderer is exercised without live
data. Everything is fixed — no clock, no randomness — so two runs over the same
fixture produce byte-identical output.

Three scenarios, matching the states the agent must handle:

  low_volume    Molosoc as it actually is today: real numbers from the verified
                runs. Nothing clears the thresholds, and the agent must say so
                rather than manufacture advice.
  healthy       Volume well above the minimums, with several cross-source
                signals genuinely firing.
  broken        Sufficient volume, but an instrumentation anomaly that must
                suppress recommendations for the entities it touches.
"""

from records import (
    CLARITY, DATA_QUALITY, GA4, GSC, MetricRecord, PAGE, PERFORMANCE, QUERY,
    SITE, SITE_ENTITY_ID,
)

HOME = "https://molosoc.com/"
PRODUCT = "https://molosoc.com/product/molosoc-hydratacni-navleky-na-nohy/"
CRACKED = "https://molosoc.com/cracked-heels/"
STAGING = "https://staging.molosoc.com/"

COLLECTED_AT = "2026-08-15T02:20:00+00:00"


def record(date, source, entity_type, entity_id, metric, value, **kw):
    kw.setdefault("window_days", 1)
    kw.setdefault("collected_at", COLLECTED_AT)
    kw.setdefault("metric_class", PERFORMANCE)
    return MetricRecord(date=date, source=source, entity_type=entity_type,
                        entity_id=entity_id, metric=metric, value=value, **kw)


def _daily(dates, source, entity_type, entity_id, metric, per_day, **kw):
    return [record(d, source, entity_type, entity_id, metric, per_day, **kw) for d in dates]


def _window_dates(start, days):
    import datetime as dt

    first = dt.date.fromisoformat(start)
    return [(first + dt.timedelta(days=i)).isoformat() for i in range(days)]


# --------------------------------------------------------------------------
# Scenario 1 — low volume (Molosoc today)
# --------------------------------------------------------------------------

def low_volume_records(period_start="2026-08-08", prior_start="2026-08-01", days=7):
    """Real magnitudes from the verified connection runs: 21 GA4 sessions and
    8 Search Console impressions across a week. Nothing here should clear an
    eligibility threshold."""
    period = _window_dates(period_start, days)
    prior = _window_dates(prior_start, days)

    def build(dates, sessions_per_day, impressions_per_day, clicks_total):
        rows = []
        rows += _daily(dates, GA4, SITE, SITE_ENTITY_ID, "ga4_sessions", sessions_per_day)
        rows += _daily(dates, GA4, SITE, SITE_ENTITY_ID, "ga4_users", sessions_per_day - 1)
        rows += _daily(dates, GA4, SITE, SITE_ENTITY_ID, "ga4_views", sessions_per_day + 1)
        rows += _daily(dates, GSC, SITE, SITE_ENTITY_ID, "gsc_impressions", impressions_per_day)
        rows.append(record(dates[0], GSC, SITE, SITE_ENTITY_ID, "gsc_clicks", clicks_total))
        rows += _daily(dates, CLARITY, SITE, SITE_ENTITY_ID, "clarity_sessions", 12)
        rows += _daily(dates, CLARITY, SITE, SITE_ENTITY_ID, "clarity_human_sessions", 7)
        rows += _daily(dates, CLARITY, SITE, SITE_ENTITY_ID, "clarity_bot_sessions", 5,
                       metric_class=DATA_QUALITY, sample_basis=12)
        rows += _daily(dates, GA4, PAGE, HOME, "ga4_sessions", 1, language="und")
        rows += _daily(dates, GA4, PAGE, PRODUCT, "ga4_sessions", 1, language="cs")
        # A staging row that must be excluded before any total is computed.
        rows.append(record(dates[0], GSC, PAGE, STAGING, "gsc_impressions", 1))
        return rows

    return build(period, 3, 1, 1), build(prior, 3, 1, 1)


# --------------------------------------------------------------------------
# Scenario 2 — healthy volume, signals firing
# --------------------------------------------------------------------------

def healthy_records(period_start="2026-08-08", prior_start="2026-08-01", days=7):
    """Enough volume to clear every gate, constructed so that four of the six
    named signals fire and two deliberately do not."""
    period = _window_dates(period_start, days)
    prior = _window_dates(prior_start, days)
    rows_period, rows_prior = [], []

    # --- site totals ---
    rows_period += _daily(period, GA4, SITE, SITE_ENTITY_ID, "ga4_sessions", 120)
    rows_prior += _daily(prior, GA4, SITE, SITE_ENTITY_ID, "ga4_sessions", 100)
    rows_period += _daily(period, GA4, SITE, SITE_ENTITY_ID, "ga4_users", 95)
    rows_prior += _daily(prior, GA4, SITE, SITE_ENTITY_ID, "ga4_users", 80)
    rows_period += _daily(period, GA4, SITE, SITE_ENTITY_ID, "ga4_views", 210)
    rows_prior += _daily(prior, GA4, SITE, SITE_ENTITY_ID, "ga4_views", 190)
    rows_period += _daily(period, GA4, SITE, SITE_ENTITY_ID, "ga4_engaged_sessions", 70)
    rows_prior += _daily(prior, GA4, SITE, SITE_ENTITY_ID, "ga4_engaged_sessions", 62)

    # Conversions, in the approved hierarchy.
    rows_period += _daily(period, GA4, SITE, SITE_ENTITY_ID, "ga4_key_event_purchase", 3,
                          sample_basis=120)
    rows_prior += _daily(prior, GA4, SITE, SITE_ENTITY_ID, "ga4_key_event_purchase", 2,
                         sample_basis=100)
    rows_period += _daily(period, GA4, SITE, SITE_ENTITY_ID,
                          "ga4_key_event_begin_checkout", 8, sample_basis=120)
    rows_prior += _daily(prior, GA4, SITE, SITE_ENTITY_ID,
                         "ga4_key_event_begin_checkout", 7, sample_basis=100)
    rows_period += _daily(period, GA4, SITE, SITE_ENTITY_ID,
                          "ga4_key_event_add_to_cart", 19, sample_basis=120)
    rows_prior += _daily(prior, GA4, SITE, SITE_ENTITY_ID,
                         "ga4_key_event_add_to_cart", 15, sample_basis=100)

    rows_period += _daily(period, GSC, SITE, SITE_ENTITY_ID, "gsc_impressions", 900)
    rows_prior += _daily(prior, GSC, SITE, SITE_ENTITY_ID, "gsc_impressions", 700)
    rows_period += _daily(period, GSC, SITE, SITE_ENTITY_ID, "gsc_clicks", 40)
    rows_prior += _daily(prior, GSC, SITE, SITE_ENTITY_ID, "gsc_clicks", 42)

    rows_period += _daily(period, CLARITY, SITE, SITE_ENTITY_ID, "clarity_sessions", 130)
    rows_prior += _daily(prior, CLARITY, SITE, SITE_ENTITY_ID, "clarity_sessions", 120)
    rows_period += _daily(period, CLARITY, SITE, SITE_ENTITY_ID, "clarity_human_sessions", 118)
    rows_prior += _daily(prior, CLARITY, SITE, SITE_ENTITY_ID, "clarity_human_sessions", 110)
    rows_period += _daily(period, CLARITY, SITE, SITE_ENTITY_ID, "clarity_bot_sessions", 12,
                          metric_class=DATA_QUALITY, sample_basis=130)
    rows_prior += _daily(prior, CLARITY, SITE, SITE_ENTITY_ID, "clarity_bot_sessions", 10,
                         metric_class=DATA_QUALITY, sample_basis=120)
    rows_period += _daily(period, CLARITY, SITE, SITE_ENTITY_ID, "clarity_scroll_depth",
                          41.0, sample_basis=130)
    rows_prior += _daily(prior, CLARITY, SITE, SITE_ENTITY_ID, "clarity_scroll_depth",
                         44.0, sample_basis=120)
    rows_period += _daily(period, CLARITY, SITE, SITE_ENTITY_ID,
                          "clarity_script_error_rate", 0.02,
                          metric_class=DATA_QUALITY, sample_basis=130)
    rows_prior += _daily(prior, CLARITY, SITE, SITE_ENTITY_ID,
                         "clarity_script_error_rate", 0.02,
                         metric_class=DATA_QUALITY, sample_basis=120)

    # --- HOME: demand up, capture down (impressions climb, clicks flat, CTR falls) ---
    rows_period += _daily(period, GSC, PAGE, HOME, "gsc_impressions", 90, language="und")
    rows_prior += _daily(prior, GSC, PAGE, HOME, "gsc_impressions", 50, language="und")
    rows_period += _daily(period, GSC, PAGE, HOME, "gsc_clicks", 3, language="und")
    rows_prior += _daily(prior, GSC, PAGE, HOME, "gsc_clicks", 4, language="und")
    rows_period += _daily(period, GSC, PAGE, HOME, "gsc_position", 9.5,
                          sample_basis=90, language="und")
    rows_prior += _daily(prior, GSC, PAGE, HOME, "gsc_position", 9.0,
                         sample_basis=50, language="und")
    rows_period += _daily(period, GA4, PAGE, HOME, "ga4_sessions", 40, language="und")
    rows_prior += _daily(prior, GA4, PAGE, HOME, "ga4_sessions", 38, language="und")

    # --- PRODUCT: friction against intent (real traffic + high dead-click rate) ---
    rows_period += _daily(period, GA4, PAGE, PRODUCT, "ga4_sessions", 45, language="cs")
    rows_prior += _daily(prior, GA4, PAGE, PRODUCT, "ga4_sessions", 44, language="cs")
    rows_period += _daily(period, CLARITY, PAGE, PRODUCT, "clarity_visits", 50,
                          language="cs")
    rows_prior += _daily(prior, CLARITY, PAGE, PRODUCT, "clarity_visits", 48, language="cs")
    rows_period += _daily(period, CLARITY, PAGE, PRODUCT, "clarity_dead_click_rate", 0.11,
                          sample_basis=50, language="cs")
    rows_prior += _daily(prior, CLARITY, PAGE, PRODUCT, "clarity_dead_click_rate", 0.10,
                         sample_basis=48, language="cs")
    rows_period += _daily(period, CLARITY, PAGE, PRODUCT, "clarity_rage_click_rate", 0.06,
                          sample_basis=50, language="cs")
    rows_prior += _daily(prior, CLARITY, PAGE, PRODUCT, "clarity_rage_click_rate", 0.02,
                         sample_basis=48, language="cs")

    # --- CRACKED: hidden gem (strong engagement, almost no impressions) ---
    rows_period += _daily(period, GA4, PAGE, CRACKED, "ga4_sessions", 30, language="en")
    rows_prior += _daily(prior, GA4, PAGE, CRACKED, "ga4_sessions", 29, language="en")
    rows_period += _daily(period, GA4, PAGE, CRACKED, "ga4_engaged_sessions", 24,
                          language="en")
    rows_prior += _daily(prior, GA4, PAGE, CRACKED, "ga4_engaged_sessions", 23, language="en")
    rows_period += _daily(period, GSC, PAGE, CRACKED, "gsc_impressions", 3, language="en")
    rows_prior += _daily(prior, GSC, PAGE, CRACKED, "gsc_impressions", 3, language="en")

    # --- query: threshold proximity (position 12, plenty of impressions) ---
    rows_period += _daily(period, GSC, QUERY, "cracked heels cream", "gsc_impressions", 30)
    rows_prior += _daily(prior, GSC, QUERY, "cracked heels cream", "gsc_impressions", 28)
    rows_period += _daily(period, GSC, QUERY, "cracked heels cream", "gsc_position", 12.0,
                          sample_basis=30)
    rows_prior += _daily(prior, GSC, QUERY, "cracked heels cream", "gsc_position", 12.5,
                         sample_basis=28)
    rows_period += _daily(period, GSC, QUERY, "cracked heels cream", "gsc_clicks", 2)
    rows_prior += _daily(prior, GSC, QUERY, "cracked heels cream", "gsc_clicks", 2)

    # Staging, always excluded.
    rows_period.append(record(period[0], GSC, PAGE, STAGING, "gsc_impressions", 12))
    rows_prior.append(record(prior[0], GSC, PAGE, STAGING, "gsc_impressions", 10))

    return rows_period, rows_prior


# --------------------------------------------------------------------------
# Scenario 3 — instrumentation anomaly suppresses recommendations
# --------------------------------------------------------------------------

def broken_instrumentation_records(period_start="2026-08-08", prior_start="2026-08-01",
                                   days=7):
    """Healthy volume and a firing signal, but bot share jumps past the
    critical level — so nothing may be recommended."""
    rows_period, rows_prior = healthy_records(period_start, prior_start, days)
    period = _window_dates(period_start, days)

    # Replace the bot figures with a majority-bot period.
    rows_period = [r for r in rows_period if r.metric != "clarity_bot_sessions"]
    rows_period += _daily(period, CLARITY, SITE, SITE_ENTITY_ID, "clarity_bot_sessions",
                          85, metric_class=DATA_QUALITY, sample_basis=130)
    return rows_period, rows_prior


def baseline_records(start="2026-07-04", days=28, per_day=110):
    """A stable trailing series for anomaly detection.

    Deliberately ends before the prior window starts. The two would otherwise
    both emit the same metric for the same dates, and records.sum_metric
    correctly refuses to aggregate duplicate date/entity/metric rows.
    """
    dates = _window_dates(start, days)
    return _daily(dates, CLARITY, SITE, SITE_ENTITY_ID, "clarity_human_sessions", per_day)


def baseline_with_spike(start="2026-07-04", days=28, per_day=110, spike=900):
    rows = baseline_records(start, days - 1, per_day)
    last = _window_dates(start, days)[-1]
    rows.append(record(last, CLARITY, SITE, SITE_ENTITY_ID,
                       "clarity_human_sessions", spike))
    return rows


def baseline_with_collapse(start="2026-07-04", days=28, per_day=110):
    rows = baseline_records(start, days - 1, per_day)
    last = _window_dates(start, days)[-1]
    rows.append(record(last, CLARITY, SITE, SITE_ENTITY_ID,
                       "clarity_human_sessions", 0))
    return rows


def store_with(store, records_by_date_source):
    """Write fixture records into a store using Phase 1's key layout."""
    from storage import facts_key

    grouped = {}
    for row in records_by_date_source:
        grouped.setdefault((row.source, row.date), []).append(row)
    for (source, date), rows in grouped.items():
        store.put_records(facts_key(source, date), rows, overwrite=True)
    return store
