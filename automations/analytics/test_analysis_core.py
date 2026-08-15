#!/usr/bin/env python3
"""
Offline tests for the analysis model, periods, thresholds and history.

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import history as hist  # noqa: E402
import periods as pr  # noqa: E402
import thresholds as th  # noqa: E402
from analysis_model import (  # noqa: E402
    HIGH, INSUFFICIENT_DATA, Inference, MeasurementPlan, ModelError,
    PRIORITY_HIGH, PRIORITY_MONITOR, READY, Recommendation, SUPPRESSED,
    fact_id, recommendation_fingerprint,
)
from records import CLARITY, GA4, GSC, MetricRecord, PAGE, QUERY, SITE, SITE_ENTITY_ID  # noqa: E402


def rec(date, metric, value, source=CLARITY, entity_type=SITE,
        entity_id=SITE_ENTITY_ID, **kw):
    return MetricRecord(date=date, source=source, entity_type=entity_type,
                        entity_id=entity_id, metric=metric, value=value, **kw)


# --------------------------------------------------------------------------
# Facts and inferences stay structurally separate
# --------------------------------------------------------------------------

def test_an_inference_cannot_exist_without_supporting_facts():
    with pytest.raises(ModelError, match="references no facts"):
        Inference(id="i1", statement="something moved", signal="s",
                  based_on=(), entity_id="e", entity_type=PAGE,
                  alternative_explanations=("noise",))


def test_an_inference_must_offer_an_alternative_explanation():
    with pytest.raises(ModelError, match="alternative explanations"):
        Inference(id="i1", statement="impressions and clicks moved together",
                  signal="s", based_on=("f1",), entity_id="e", entity_type=PAGE,
                  alternative_explanations=())


def test_causal_language_is_rejected():
    for statement in (
        "the redesign caused the drop in clicks",
        "impressions fell because of the algorithm update",
        "the change led to lower engagement",
        "slow loading resulted in rage clicks",
    ):
        with pytest.raises(ModelError, match="causal language"):
            Inference(id="i1", statement=statement, signal="s", based_on=("f1",),
                      entity_id="e", entity_type=PAGE,
                      alternative_explanations=("something else",))


def test_correlational_language_is_accepted():
    inference = Inference(
        id="i1", statement="impressions rose while CTR fell over the same window",
        signal="s", based_on=("f1", "f2"), entity_id="e", entity_type=PAGE,
        alternative_explanations=("query mix shifted",),
    )
    assert inference.causal_claim is False


def test_causal_claim_cannot_be_set_true():
    with pytest.raises(ModelError, match="causal_claim must be False"):
        Inference(id="i1", statement="x and y moved together", signal="s",
                  based_on=("f1",), entity_id="e", entity_type=PAGE,
                  alternative_explanations=("noise",), causal_claim=True)


def test_fact_ids_are_stable_across_runs():
    first = fact_id(GSC, PAGE, "https://molosoc.com/", "gsc_ctr")
    second = fact_id(GSC, PAGE, "https://molosoc.com/", "gsc_ctr")
    assert first == second
    assert first != fact_id(GSC, PAGE, "https://molosoc.com/other/", "gsc_ctr")


def test_recommendation_fingerprints_are_stable():
    a = recommendation_fingerprint("seo", "https://molosoc.com/", "improve_serp_presentation")
    b = recommendation_fingerprint("seo", "https://molosoc.com/", "improve_serp_presentation")
    assert a == b


# --------------------------------------------------------------------------
# Recommendation invariants
# --------------------------------------------------------------------------

def _plan():
    return MeasurementPlan(metric="gsc_ctr", entity_id="e", entity_type=PAGE,
                           direction="increase")


def test_a_recommendation_must_cite_facts():
    with pytest.raises(ModelError, match="cites no facts"):
        Recommendation(id="r1", fingerprint="r1", priority=PRIORITY_MONITOR,
                       area="seo", action="do a thing", rationale="because",
                       supporting_facts=(), measurement_plan=_plan())


def test_an_unready_recommendation_cannot_be_high_priority():
    with pytest.raises(ModelError, match="readiness"):
        Recommendation(id="r1", fingerprint="r1", priority=PRIORITY_HIGH,
                       area="seo", action="do a thing", rationale="because",
                       supporting_facts=("f1",), measurement_plan=_plan(),
                       readiness=INSUFFICIENT_DATA)


def test_a_suppressed_recommendation_cannot_be_high_priority():
    with pytest.raises(ModelError, match="readiness"):
        Recommendation(id="r1", fingerprint="r1", priority=PRIORITY_HIGH,
                       area="seo", action="do a thing", rationale="because",
                       supporting_facts=("f1",), measurement_plan=_plan(),
                       readiness=SUPPRESSED)


def test_monitor_is_allowed_when_not_ready():
    recommendation = Recommendation(
        id="r1", fingerprint="r1", priority=PRIORITY_MONITOR, area="seo",
        action="watch this", rationale="volume too low",
        supporting_facts=("f1",), measurement_plan=_plan(),
        readiness=INSUFFICIENT_DATA,
    )
    assert recommendation.priority == PRIORITY_MONITOR


# --------------------------------------------------------------------------
# Periods
# --------------------------------------------------------------------------

def test_the_anchor_accounts_for_search_console_lag():
    assert pr.anchor_date("2026-08-17") == dt.date(2026, 8, 14)


def test_windows_are_whole_weeks_and_adjacent():
    w = pr.build_windows(today="2026-08-17")
    assert w[pr.PERIOD].days == 7 and w[pr.PRIOR].days == 7
    assert w[pr.PERIOD].start == "2026-08-08" and w[pr.PERIOD].end == "2026-08-14"
    assert w[pr.PRIOR].end == "2026-08-07"


def test_partial_weeks_are_refused():
    with pytest.raises(ValueError, match="whole number of weeks"):
        pr.build_windows(today="2026-08-17", period_days=5)


def test_seasonal_window_is_52_whole_weeks_back():
    w = pr.build_windows(today="2026-08-17")
    assert w[pr.SEASONAL].days == 7
    delta = dt.date.fromisoformat(w[pr.PERIOD].start) - dt.date.fromisoformat(w[pr.SEASONAL].start)
    assert delta.days == 364


def test_ledger_coverage_reports_partial_windows_as_unusable():
    w = pr.build_windows(today="2026-08-17")
    partial = [d for d in w[pr.PERIOD].dates()][:3]
    coverage = pr.ledger_coverage(partial, w)
    assert coverage["supports_period"] is False
    assert coverage["supports_comparison"] is False
    assert "not yet fully covered" in pr.describe_coverage(coverage)


def test_ledger_coverage_supports_comparison_when_both_windows_are_complete():
    w = pr.build_windows(today="2026-08-17")
    coverage = pr.ledger_coverage(w[pr.PERIOD].dates() + w[pr.PRIOR].dates(), w)
    assert coverage["supports_period"] and coverage["supports_comparison"]
    assert coverage["supports_seasonal"] is False


def test_empty_ledger_is_described_plainly():
    w = pr.build_windows(today="2026-08-17")
    assert "No Clarity history stored yet" in pr.describe_coverage(pr.ledger_coverage([], w))


# --------------------------------------------------------------------------
# Thresholds
# --------------------------------------------------------------------------

def test_relative_change_alone_never_triggers_a_finding():
    # 1 click -> 3 clicks is +200% and means nothing.
    assert th.is_significant_count("gsc_clicks", 3, 1) is False


def test_absolute_change_alone_never_triggers_a_finding():
    # A big absolute move that is a tiny relative one.
    assert th.is_significant_count("gsc_impressions", 10050, 10000) is False


def test_both_gates_together_do_trigger():
    assert th.is_significant_count("gsc_clicks", 40, 20) is True


def test_position_needs_both_movement_and_impressions():
    assert th.is_significant_position(6.0, 9.0, impressions=500) is True
    assert th.is_significant_position(6.0, 9.0, impressions=10) is False
    assert th.is_significant_position(8.5, 9.0, impressions=500) is False


def test_rate_significance_uses_a_two_proportion_test():
    assert th.is_significant_rate(50, 1000, 100, 1000) is True
    assert th.is_significant_rate(50, 1000, 52, 1000) is False


def test_rate_significance_is_none_safe_on_empty_samples():
    assert th.two_proportion_z(0, 0, 1, 10) is None
    assert th.is_significant_rate(0, 0, 1, 10) is False


def test_confidence_intervals_are_clamped_to_valid_probabilities():
    low, high = th.proportion_confidence_interval(1, 5)
    assert 0.0 <= low <= high <= 1.0
    assert th.proportion_confidence_interval(0, 0) is None


def test_eligibility_minimums_are_conservative():
    assert th.query_eligible_for_ctr(50, 50) is True
    assert th.query_eligible_for_ctr(49, 100) is False
    assert th.page_eligible_for_engagement(30, 30) is True
    assert th.page_eligible_for_engagement(29, 100) is False


def test_readiness_gate_refuses_advice_at_molosoc_current_volume():
    # The verified week was 21 GA4 sessions.
    readiness = th.assess_readiness(21)
    assert readiness.ready is False
    assert "insufficient data for recommendation" in readiness.reason


def test_readiness_gate_opens_at_the_minimum():
    assert th.assess_readiness(100).ready is True


def test_readiness_with_no_data_at_all():
    readiness = th.assess_readiness(None)
    assert readiness.ready is False


# --------------------------------------------------------------------------
# History aggregation
# --------------------------------------------------------------------------

def test_counts_sum_across_days():
    rows = [rec("2026-08-1%d" % i, "clarity_sessions", 10) for i in range(1, 5)]
    assert hist.aggregate(rows, "clarity_sessions").value == 40


def test_overlapping_multi_day_windows_are_refused():
    from records import RecordError

    rows = [rec("2026-08-11", "clarity_sessions", 85, window_days=3),
            rec("2026-08-12", "clarity_sessions", 85, window_days=3)]
    with pytest.raises(RecordError, match="overlap"):
        hist.aggregate(rows, "clarity_sessions")


def test_a_single_multi_day_record_is_used_as_is():
    rows = [rec("2026-08-14", "ga4_sessions", 21, source=GA4, window_days=7)]
    assert hist.aggregate(rows, "ga4_sessions").value == 21


def test_ctr_is_recomputed_from_parts_not_averaged():
    # Averaging 100% and 0% would give 50%; the true CTR is 1/101.
    rows = [rec("2026-08-11", "gsc_clicks", 1, source=GSC),
            rec("2026-08-11", "gsc_impressions", 1, source=GSC),
            rec("2026-08-12", "gsc_clicks", 0, source=GSC),
            rec("2026-08-12", "gsc_impressions", 100, source=GSC)]
    aggregate = hist.aggregate(rows, "gsc_ctr")
    assert aggregate.value == pytest.approx(1 / 101)
    assert aggregate.sample == 101


def test_a_ratio_is_available_even_though_no_record_stores_it():
    rows = [rec("2026-08-11", "clarity_bot_sessions", 34, sample_basis=85),
            rec("2026-08-11", "clarity_sessions", 85)]
    assert hist.aggregate(rows, "clarity_bot_share").value == pytest.approx(34 / 85)


def test_position_is_impression_weighted_not_a_plain_mean():
    # A plain mean would be 6.0; weighted by impressions it is far closer to 2.
    rows = [rec("2026-08-11", "gsc_position", 2.0, source=GSC, sample_basis=1000),
            rec("2026-08-12", "gsc_position", 10.0, source=GSC, sample_basis=10)]
    value = hist.aggregate(rows, "gsc_position").value
    assert value == pytest.approx((2.0 * 1000 + 10.0 * 10) / 1010)
    assert value < 3.0


def test_weighted_mean_falls_back_to_a_plain_mean_without_weights():
    rows = [rec("2026-08-11", "clarity_scroll_depth", 30.0),
            rec("2026-08-12", "clarity_scroll_depth", 50.0)]
    assert hist.aggregate(rows, "clarity_scroll_depth").value == pytest.approx(40.0)


def test_aggregating_a_missing_metric_returns_none():
    assert hist.aggregate([], "gsc_clicks") is None


def test_entities_are_listed_per_type():
    rows = [rec("2026-08-11", "gsc_clicks", 1, source=GSC, entity_type=QUERY,
                entity_id="molosoc"),
            rec("2026-08-11", "gsc_clicks", 1, source=GSC, entity_type=PAGE,
                entity_id="https://molosoc.com/")]
    assert hist.entities(rows, QUERY) == ["molosoc"]
    assert hist.entities(rows, PAGE) == ["https://molosoc.com/"]


def test_daily_series_only_includes_single_day_records():
    rows = [rec("2026-08-11", "clarity_sessions", 10),
            rec("2026-08-12", "clarity_sessions", 20),
            rec("2026-08-13", "clarity_sessions", 99, window_days=3)]
    assert hist.daily_series(rows, "clarity_sessions") == {
        "2026-08-11": 10, "2026-08-12": 20,
    }


def test_conversion_hierarchy_is_declared():
    assert hist.PRIMARY_CONVERSION == "ga4_key_event_purchase"
    assert hist.SUPPORTING_CONVERSIONS == (
        "ga4_key_event_begin_checkout", "ga4_key_event_add_to_cart",
    )
