#!/usr/bin/env python3
"""
Offline tests for the ecommerce tracking boundary.

WooCommerce Google Analytics Integration was enabled on a specific date. Before
it, the property received no usable ecommerce stream data; after it, ecommerce
events are real measurements.

The distinction these tests protect is the whole point:

    before the boundary  ->  no conversion data means UNMEASURED
    after the boundary   ->  no conversion data means ZERO SALES

Conflating the two would either invent a catastrophic decline (real sales
compared against a period that could not record any) or invent growth from
nothing. Both are worse than saying "not comparable".

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analysis  # noqa: E402
import fixtures as fx  # noqa: E402
import google_hydrate as gh  # noqa: E402
import periods as pr  # noqa: E402
import render  # noqa: E402
from records import CLARITY  # noqa: E402
from storage import InMemoryStore  # noqa: E402
from test_google_hydrate import ga4_payload, gsc_payload  # noqa: E402

NOW = dt.datetime(2026, 8, 17, 6, 0, tzinfo=dt.timezone.utc)
TODAY = "2026-08-17"

# With today = 2026-08-17: period is 08-08..08-14, prior is 08-01..08-07.
BEFORE_BOTH = "2026-09-01"      # boundary after both windows
AFTER_BOTH = "2026-07-01"       # boundary before both windows
BETWEEN = "2026-08-08"          # boundary exactly at the period start
MID_PERIOD = "2026-08-11"       # boundary inside the current period


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    monkeypatch.delenv(gh.ECOMMERCE_TRACKING_START_ENV, raising=False)


@pytest.fixture
def windows():
    return pr.build_windows(today=TODAY)


# --------------------------------------------------------------------------
# Window classification
# --------------------------------------------------------------------------

def test_a_window_entirely_after_the_boundary_is_active(windows):
    assert gh.tracking_state_for_window(windows[pr.PERIOD], BETWEEN) == gh.TRACKING_ACTIVE


def test_a_window_entirely_before_the_boundary_is_unavailable(windows):
    assert gh.tracking_state_for_window(windows[pr.PRIOR], BETWEEN) == gh.TRACKING_UNAVAILABLE


def test_a_window_straddling_the_boundary_is_partial(windows):
    assert gh.tracking_state_for_window(windows[pr.PERIOD], MID_PERIOD) == gh.TRACKING_PARTIAL


def test_both_windows_before_a_future_boundary(windows):
    assert gh.tracking_state_for_window(windows[pr.PERIOD], BEFORE_BOTH) == gh.TRACKING_UNAVAILABLE
    assert gh.tracking_state_for_window(windows[pr.PRIOR], BEFORE_BOTH) == gh.TRACKING_UNAVAILABLE


def test_both_windows_after_an_old_boundary(windows):
    assert gh.tracking_state_for_window(windows[pr.PERIOD], AFTER_BOTH) == gh.TRACKING_ACTIVE
    assert gh.tracking_state_for_window(windows[pr.PRIOR], AFTER_BOTH) == gh.TRACKING_ACTIVE


def test_an_unusable_boundary_value_yields_unknown_not_a_guess(windows):
    # The committed default now applies when nothing is configured, so
    # "unknown" is reached only when a supplied value cannot be parsed. The
    # agent still never invents a date in that case.
    assert gh.tracking_state_for_window(windows[pr.PERIOD], "") == gh.TRACKING_UNKNOWN
    assert gh.tracking_state_for_window(windows[pr.PERIOD], "garbage") == gh.TRACKING_UNKNOWN


def test_the_boundary_is_read_from_the_environment(monkeypatch, windows):
    monkeypatch.setenv(gh.ECOMMERCE_TRACKING_START_ENV, BETWEEN)
    assert gh.ecommerce_tracking_start() == dt.date(2026, 8, 8)
    assert gh.tracking_state_for_window(windows[pr.PERIOD]) == gh.TRACKING_ACTIVE


def test_a_malformed_boundary_is_treated_as_unset():
    assert gh.ecommerce_tracking_start("not-a-date") is None
    assert gh.ecommerce_tracking_start("") is None


def test_an_iso_timestamp_boundary_is_accepted():
    assert gh.ecommerce_tracking_start("2026-08-08T14:30:00+00:00") == dt.date(2026, 8, 8)


# --------------------------------------------------------------------------
# Comparison validity
# --------------------------------------------------------------------------

def test_a_comparison_needs_both_windows_inside_the_tracked_era():
    assert gh.comparison_is_valid(gh.TRACKING_ACTIVE, gh.TRACKING_ACTIVE)
    assert not gh.comparison_is_valid(gh.TRACKING_ACTIVE, gh.TRACKING_UNAVAILABLE)
    assert not gh.comparison_is_valid(gh.TRACKING_PARTIAL, gh.TRACKING_ACTIVE)
    assert not gh.comparison_is_valid(gh.TRACKING_UNKNOWN, gh.TRACKING_UNKNOWN)


def test_a_partial_window_is_not_valid_conversion_data():
    # Half a window of tracking is incomplete, not comparable.
    assert not gh.conversion_data_is_valid(gh.TRACKING_PARTIAL)


# --------------------------------------------------------------------------
# The message a reader actually sees
# --------------------------------------------------------------------------

def test_pre_tracking_absence_is_described_as_unmeasured_not_zero():
    readiness = gh.assess_conversions(
        {}, period_state=gh.TRACKING_UNAVAILABLE,
        prior_state=gh.TRACKING_UNAVAILABLE, boundary=BEFORE_BOTH,
    )
    assert readiness["state"] == gh.CONVERSIONS_BEFORE_TRACKING
    assert "not an absence of sales" in readiness["message"]
    assert readiness["comparison_valid"] is False


def test_crossing_the_boundary_reports_current_period_only():
    readiness = gh.assess_conversions(
        {"purchase": 3}, period_state=gh.TRACKING_ACTIVE,
        prior_state=gh.TRACKING_UNAVAILABLE, boundary=BETWEEN,
    )
    assert readiness["state"] == gh.CONVERSIONS_OK
    assert readiness["comparison_valid"] is False
    assert "no period-over-period conversion comparison is made" in readiness["message"]
    assert "missing data, not zero sales" in readiness["message"]


def test_both_periods_tracked_permits_a_comparison():
    readiness = gh.assess_conversions(
        {"purchase": 3, "begin_checkout": 8, "add_to_cart": 19},
        period_state=gh.TRACKING_ACTIVE, prior_state=gh.TRACKING_ACTIVE,
        boundary=AFTER_BOTH,
    )
    assert readiness["state"] == gh.CONVERSIONS_OK
    assert readiness["comparison_valid"] is True


def test_a_partial_current_period_is_called_incomplete():
    readiness = gh.assess_conversions(
        {}, period_state=gh.TRACKING_PARTIAL, prior_state=gh.TRACKING_UNAVAILABLE,
        boundary=MID_PERIOD,
    )
    assert readiness["state"] == gh.CONVERSIONS_BEFORE_TRACKING
    assert "incomplete rather than comparable" in readiness["message"]


def test_an_unresolvable_boundary_says_so_and_stays_conservative():
    readiness = gh.assess_conversions({}, period_state=gh.TRACKING_UNKNOWN,
                                      prior_state=gh.TRACKING_UNKNOWN, boundary="")
    assert readiness["comparison_valid"] is False
    assert "never as zero sales" in readiness["message"]


# --------------------------------------------------------------------------
# End to end: the transition from pre-tracking to tracked periods
# --------------------------------------------------------------------------

def _store_with_clarity():
    store = InMemoryStore()
    period, prior = fx.low_volume_records()
    fx.store_with(store, [r for r in period + prior if r.source == CLARITY]
                  + fx.baseline_records())
    return store


def _run(boundary, period_key_events=None, prior_key_events=None):
    """Hydrate with different key events per window, as a real transition would."""
    store = _store_with_clarity()

    def ga4(start, end):
        events = period_key_events if start == "2026-08-08" else prior_key_events
        return ga4_payload(key_events=events)

    hydrator = gh.GoogleHydrator(ga4_fetcher=ga4,
                                 gsc_fetcher=lambda s, e: gsc_payload(),
                                 collected_at=NOW.isoformat())
    return analysis.analyse_from_store(store, today=TODAY, now=NOW, hydrator=hydrator,
                                       ecommerce_tracking_start=boundary)


def test_a_fully_pre_tracking_run_reports_unavailable_not_zero():
    report = _run(BEFORE_BOTH)

    conversions = report.data_quality["conversions"]
    assert conversions["state"] == gh.CONVERSIONS_BEFORE_TRACKING
    assert "not an absence of sales" in conversions["message"]
    # No conversion fact was invented.
    assert not [f for f in report.facts if f.metric.startswith("ga4_key_event_")]


def test_the_transition_run_reports_conversions_without_a_false_comparison():
    # Current period tracked with 3 purchases; comparison period predates the fix.
    report = _run(BETWEEN, period_key_events={"purchase": 3, "add_to_cart": 12})

    purchases = [f for f in report.facts if f.metric == "ga4_key_event_purchase"]
    assert purchases, "the tracked period's purchases must be reported"
    fact = purchases[0]
    assert fact.period_value == 3
    # The crucial assertion: no comparison, no delta, no significance — and a
    # stated reason rather than a silent blank.
    assert fact.comparison_value is None
    assert fact.delta_abs is None
    assert fact.delta_pct is None
    assert fact.significant is False
    assert "not zero sales" in fact.notes["comparison_unavailable_reason"]


def test_the_transition_never_reports_growth_from_nothing():
    report = _run(BETWEEN, period_key_events={"purchase": 3})
    for fact in report.facts:
        if fact.metric.startswith("ga4_key_event_"):
            assert fact.delta_pct is None, "a delta across the boundary is meaningless"


def test_once_both_periods_are_tracked_the_comparison_is_allowed():
    report = _run(AFTER_BOTH,
                  period_key_events={"purchase": 5},
                  prior_key_events={"purchase": 2})

    boundary = report.data_quality["ecommerce_boundary"]
    assert boundary["comparison_valid"] is True

    fact = [f for f in report.facts if f.metric == "ga4_key_event_purchase"][0]
    assert fact.period_value == 5
    assert fact.comparison_value == 2  # a real comparison, now that both are tracked


def test_a_measured_zero_after_the_boundary_is_kept_as_zero():
    # Tracking live, nothing sold: that is a real observation, not missing data.
    report = _run(AFTER_BOTH,
                  period_key_events={"purchase": 0},
                  prior_key_events={"purchase": 0})

    fact = [f for f in report.facts if f.metric == "ga4_key_event_purchase"][0]
    assert fact.period_value == 0
    assert report.data_quality["ecommerce_boundary"]["comparison_valid"] is True


def test_the_boundary_state_is_recorded_in_the_report():
    report = _run(BETWEEN, period_key_events={"purchase": 3})
    boundary = report.data_quality["ecommerce_boundary"]

    assert boundary["start_date"] == BETWEEN
    assert boundary["period_state"] == gh.TRACKING_ACTIVE
    assert boundary["prior_state"] == gh.TRACKING_UNAVAILABLE
    assert boundary["comparison_valid"] is False


def test_the_rendered_report_explains_the_boundary():
    report = _run(BETWEEN, period_key_events={"purchase": 3})
    text = render.render_markdown(report)

    assert f"Ecommerce tracking boundary ({BETWEEN})" in text
    assert "missing data, not zero sales" in text
    assert "conversion comparison valid: False" in text


def test_an_unresolvable_boundary_is_flagged_in_the_report():
    report = _run("")  # supplied but unusable
    text = render.render_markdown(report)
    assert "Ecommerce tracking boundary not configured" in text


def test_thresholds_are_untouched_by_the_boundary_work():
    import thresholds as th

    assert th.MIN_SITE_SESSIONS_FOR_RECOMMENDATIONS == 100
    assert th.MIN_QUERY_IMPRESSIONS == 50
    assert th.MIN_PAGE_SESSIONS == 30
    assert th.MIN_SESSIONS_FOR_CONVERSION == 100


def test_the_boundary_does_not_unlock_recommendations_at_low_volume():
    report = _run(AFTER_BOTH, period_key_events={"purchase": 5},
                  prior_key_events={"purchase": 2})
    assert report.readiness == "insufficient_data"
    assert all(r.priority == "Monitor" for r in report.recommendations)


# --------------------------------------------------------------------------
# The committed activation date
# --------------------------------------------------------------------------

def test_the_verified_activation_date_is_the_default():
    # WooCommerce Google Analytics Integration went live on this date.
    assert gh.ECOMMERCE_TRACKING_START_DEFAULT == "2026-08-16"
    assert gh.ecommerce_tracking_start() == dt.date(2026, 8, 16)


def test_the_environment_still_overrides_the_default(monkeypatch):
    monkeypatch.setenv(gh.ECOMMERCE_TRACKING_START_ENV, "2026-01-01")
    assert gh.ecommerce_tracking_start() == dt.date(2026, 1, 1)


def test_an_explicit_argument_beats_both(monkeypatch):
    monkeypatch.setenv(gh.ECOMMERCE_TRACKING_START_ENV, "2026-01-01")
    assert gh.ecommerce_tracking_start("2026-03-05") == dt.date(2026, 3, 5)


def test_periods_before_the_real_activation_date_are_unavailable():
    # A week entirely before 2026-08-16 can hold no ecommerce measurement.
    windows = pr.build_windows(today="2026-08-17")
    assert gh.tracking_state_for_window(windows[pr.PRIOR]) == gh.TRACKING_UNAVAILABLE
    assert gh.tracking_state_for_window(windows[pr.PERIOD]) == gh.TRACKING_UNAVAILABLE


def test_periods_after_the_real_activation_date_are_active():
    windows = pr.build_windows(today="2026-09-01")  # period 2026-08-23..08-29
    assert gh.tracking_state_for_window(windows[pr.PERIOD]) == gh.TRACKING_ACTIVE
