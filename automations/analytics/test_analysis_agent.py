#!/usr/bin/env python3
"""
Offline tests for the agent end to end: anomalies, signals, recommendations,
tracking, and the rendered report.

Everything runs against the deterministic fixtures in fixtures.py — no network,
no credentials, no live API. The three scenarios cover the states that matter:
Molosoc's real low volume, a healthy site with signals firing, and a site whose
instrumentation is broken.

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analysis  # noqa: E402
import anomalies as an  # noqa: E402
import fixtures as fx  # noqa: E402
import periods as pr  # noqa: E402
import recommend as rc  # noqa: E402
import render  # noqa: E402
import signals as sg  # noqa: E402
import tracking as tr  # noqa: E402
from analysis_model import (  # noqa: E402
    INSTRUMENTATION_ANOMALY, INSUFFICIENT_DATA, MeasurementPlan,
    OUTCOME_CONFOUNDED, OUTCOME_IMPROVED, OUTCOME_INCONCLUSIVE,
    OUTCOME_NO_CHANGE, OUTCOME_PENDING, OUTCOME_WORSENED, PERFORMANCE_ANOMALY,
    PRIORITY_HIGH, PRIORITY_MONITOR, READY, STATUS_IMPLEMENTED, SUPPRESSED,
)
from storage import InMemoryStore  # noqa: E402

NOW = dt.datetime(2026, 8, 17, 6, 0, tzinfo=dt.timezone.utc)
TODAY = "2026-08-17"

COVERAGE = {
    "days_available": 40, "first_date": "2026-07-08", "last_date": "2026-08-16",
    "period_days_present": 7, "prior_days_present": 7,
    "supports_period": True, "supports_comparison": True, "supports_seasonal": False,
}


def run(scenario, baseline=None):
    windows = pr.build_windows(today=TODAY)
    period, prior = scenario()
    return analysis.analyse(
        period, prior, baseline or fx.baseline_records(), windows,
        clarity_coverage=COVERAGE, now=NOW,
    )


@pytest.fixture
def low():
    return run(fx.low_volume_records)


@pytest.fixture
def healthy():
    return run(fx.healthy_records)


@pytest.fixture
def broken():
    return run(fx.broken_instrumentation_records)


# --------------------------------------------------------------------------
# Low volume — the agent must decline to advise
# --------------------------------------------------------------------------

def test_low_volume_reports_insufficient_data(low):
    assert low.readiness == INSUFFICIENT_DATA
    assert "insufficient data for recommendation" in low.readiness_note


def test_low_volume_still_reports_facts(low):
    # Declining to advise is not declining to measure.
    assert low.facts
    assert any(f.metric == "ga4_sessions" for f in low.facts)


def test_low_volume_produces_no_actionable_recommendations(low):
    assert all(r.priority == PRIORITY_MONITOR for r in low.recommendations)
    assert not [r for r in low.recommendations if r.readiness == READY
                and r.priority != PRIORITY_MONITOR]


def test_low_volume_facts_are_marked_below_minimum(low):
    page_facts = [f for f in low.facts if f.entity_type == "page"]
    assert page_facts
    assert all(not f.meets_minimum for f in page_facts)


def test_low_volume_fires_no_signals(low):
    # Nothing clears significance, so nothing to interpret.
    assert low.inferences == []


def test_staging_is_excluded_from_the_analysis(low, healthy):
    for report in (low, healthy):
        assert not any("staging" in f.entity_id for f in report.facts)
        assert report.data_quality["excluded_non_production_records"] >= 1
        assert "staging.molosoc.com" in report.data_quality["excluded_hosts"]


# --------------------------------------------------------------------------
# Healthy volume — signals fire and become recommendations
# --------------------------------------------------------------------------

def test_healthy_volume_is_ready(healthy):
    assert healthy.readiness == READY


def test_the_expected_signals_fire(healthy):
    fired = {i.signal for i in healthy.inferences}
    assert sg.DEMAND_UP_CAPTURE_DOWN in fired
    assert sg.FRICTION_AGAINST_INTENT in fired
    assert sg.HIDDEN_GEM in fired
    assert sg.THRESHOLD_PROXIMITY in fired


def test_demand_up_capture_down_names_the_right_page(healthy):
    inference = next(i for i in healthy.inferences
                     if i.signal == sg.DEMAND_UP_CAPTURE_DOWN)
    assert inference.entity_id == fx.HOME
    assert "impressions" in inference.statement


def test_friction_signal_names_the_page_with_dead_clicks(healthy):
    inference = next(i for i in healthy.inferences
                     if i.signal == sg.FRICTION_AGAINST_INTENT)
    assert inference.entity_id == fx.PRODUCT


def test_every_inference_references_facts_that_exist(healthy):
    fact_ids = {f.id for f in healthy.facts}
    for inference in healthy.inferences:
        assert inference.based_on
        assert set(inference.based_on) <= fact_ids


def test_every_inference_carries_alternative_explanations(healthy):
    for inference in healthy.inferences:
        assert len(inference.alternative_explanations) >= 1
        assert inference.causal_claim is False


def test_recommendations_are_produced_and_prioritised(healthy):
    assert healthy.recommendations
    assert any(r.priority == PRIORITY_HIGH for r in healthy.recommendations)


def test_every_recommendation_has_the_required_fields(healthy):
    for rec in healthy.recommendations:
        assert rec.priority in ("High", "Medium", "Monitor")
        assert rec.action and rec.rationale
        assert rec.supporting_facts
        assert rec.measurement_plan.metric and rec.measurement_plan.direction
        assert rec.readiness in (READY, INSUFFICIENT_DATA, SUPPRESSED)
        assert rec.confidence in ("high", "medium", "low")


def test_recommendations_are_ordered_by_priority(healthy):
    ranks = [rc._priority_rank(r.priority) for r in healthy.recommendations]
    assert ranks == sorted(ranks, reverse=True)


def test_source_disagreement_never_becomes_an_action():
    # It is a reason not to act, not an action.
    assert sg.SOURCE_DISAGREEMENT in rc.NON_ACTIONABLE_SIGNALS
    assert sg.SOURCE_DISAGREEMENT not in rc.TEMPLATES


def test_the_same_condition_does_not_create_duplicate_recommendations(healthy):
    fingerprints = [r.fingerprint for r in healthy.recommendations]
    assert len(fingerprints) == len(set(fingerprints))


def test_conversion_metrics_appear_with_the_approved_hierarchy(healthy):
    metrics = {f.metric for f in healthy.facts}
    assert "ga4_key_event_purchase" in metrics
    assert "ga4_key_event_begin_checkout" in metrics
    assert "ga4_key_event_add_to_cart" in metrics


def test_language_metadata_survives_into_facts(healthy):
    languages = {f.language for f in healthy.facts if f.entity_type == "page"}
    assert "cs" in languages
    assert "en" in languages


# --------------------------------------------------------------------------
# Instrumentation anomaly suppression
# --------------------------------------------------------------------------

def test_broken_instrumentation_raises_an_anomaly(broken):
    instrumentation = [a for a in broken.anomalies if a.is_instrumentation]
    assert instrumentation
    assert any(a.metric == "clarity_bot_share" for a in instrumentation)


def test_instrumentation_anomaly_suppresses_every_recommendation(broken):
    assert broken.recommendations
    assert all(r.readiness == SUPPRESSED for r in broken.recommendations)
    assert all(r.priority == PRIORITY_MONITOR for r in broken.recommendations)


def test_suppression_is_explained_in_the_rationale(broken):
    assert any("instrumentation anomaly" in r.rationale for r in broken.recommendations)


def test_signals_still_fire_under_suppression(broken):
    # The analysis still reports what it saw; it just refuses to act on it.
    assert broken.inferences


def test_site_level_suppression_covers_pages_beneath_it(broken):
    suppressed = an.suppressed_entities(broken.anomalies)
    assert "site" in suppressed
    assert an.is_suppressed(fx.PRODUCT, broken.anomalies)


# --------------------------------------------------------------------------
# Anomaly detection primitives
# --------------------------------------------------------------------------

def test_a_spike_against_a_stable_series_is_a_performance_anomaly():
    report = run(fx.healthy_records, baseline=fx.baseline_with_spike())
    outliers = [a for a in report.anomalies
                if a.anomaly_class == PERFORMANCE_ANOMALY]
    assert outliers
    assert outliers[0].method == "robust_z(median/MAD)"


def test_a_collapse_to_zero_is_an_instrumentation_anomaly_not_a_traffic_finding():
    report = run(fx.healthy_records, baseline=fx.baseline_with_collapse())
    collapses = [a for a in report.anomalies if a.method == "collapse_to_zero"]
    assert collapses
    assert collapses[0].anomaly_class == INSTRUMENTATION_ANOMALY


def test_source_divergence_is_detected():
    found = an.detect_source_divergence(ga4_sessions=100, clarity_sessions=0)
    assert found and found[0].is_instrumentation
    assert "Clarity" in found[0].description


def test_matching_sources_raise_nothing():
    assert an.detect_source_divergence(100, 95) == []


def test_a_bot_share_jump_is_flagged_even_below_critical():
    found = an.detect_bot_share_anomaly(0.35, 0.10)
    assert found and "Bot share" in found[0].description


def test_a_stable_bot_share_is_not_flagged():
    assert an.detect_bot_share_anomaly(0.12, 0.10) == []


def test_script_error_spike_is_instrumentation():
    found = an.detect_script_error_spike(0.15, 0.01)
    assert found and found[0].is_instrumentation


def test_robust_z_ignores_short_series():
    assert an.robust_z(100, [1, 2, 3]) is None


def test_robust_z_handles_a_perfectly_flat_series():
    assert an.robust_z(10, [10] * 10) == 0.0
    assert an.robust_z(500, [10] * 10) is not None


# --------------------------------------------------------------------------
# Recommendation tracking
# --------------------------------------------------------------------------

def _plan(metric="gsc_ctr", direction="increase", min_sample=50):
    return MeasurementPlan(metric=metric, entity_id=fx.HOME, entity_type="page",
                           direction=direction, min_sample=min_sample)


def test_an_improvement_in_the_intended_direction_is_recorded():
    verdict = tr.classify_outcome(_plan(), before=0.02, after=0.06,
                                  before_sample=1000, after_sample=1000)
    assert verdict.outcome == OUTCOME_IMPROVED


def test_a_move_against_the_intended_direction_is_recorded():
    verdict = tr.classify_outcome(_plan(), before=0.06, after=0.02,
                                  before_sample=1000, after_sample=1000)
    assert verdict.outcome == OUTCOME_WORSENED


def test_a_movement_below_the_significance_bar_is_no_material_change():
    verdict = tr.classify_outcome(_plan(), before=0.0500, after=0.0505,
                                  before_sample=1000, after_sample=1000)
    assert verdict.outcome == OUTCOME_NO_CHANGE


def test_an_overlapping_change_makes_the_outcome_confounded():
    verdict = tr.classify_outcome(
        _plan(), before=0.02, after=0.06, before_sample=1000, after_sample=1000,
        confounders=("site-wide bot-share anomaly overlapped the window",),
    )
    assert verdict.outcome == OUTCOME_CONFOUNDED
    assert verdict.confounded_by


def test_a_sample_below_the_recorded_minimum_is_inconclusive():
    verdict = tr.classify_outcome(_plan(min_sample=100), before=0.02, after=0.06,
                                  before_sample=10, after_sample=1000)
    assert verdict.outcome == OUTCOME_INCONCLUSIVE


def test_missing_history_on_one_side_is_inconclusive():
    verdict = tr.classify_outcome(_plan(), before=None, after=0.06)
    assert verdict.outcome == OUTCOME_INCONCLUSIVE
    assert "cannot be backfilled" in verdict.detail


def test_a_decrease_plan_treats_a_fall_as_improvement():
    plan = _plan(metric="gsc_position", direction="decrease")
    verdict = tr.classify_outcome(plan, before=12.0, after=6.0,
                                  before_sample=500, after_sample=500)
    assert verdict.outcome == OUTCOME_IMPROVED


def test_the_ledger_merges_repeats_as_recurrences_not_duplicates(healthy):
    ledger = tr.merge_into_ledger({}, healthy.recommendations, now=NOW)
    assert len(ledger) == len(healthy.recommendations)

    again = tr.merge_into_ledger(ledger, healthy.recommendations, now=NOW)
    assert len(again) == len(ledger)
    assert all(entry["recurrence_count"] == 2 for entry in again.values())


def test_human_decisions_survive_regeneration(healthy):
    ledger = tr.merge_into_ledger({}, healthy.recommendations, now=NOW)
    key = sorted(ledger)[0]
    ledger[key]["status"] = STATUS_IMPLEMENTED
    ledger[key]["implemented_at"] = "2026-08-01T00:00:00+00:00"

    regenerated = tr.merge_into_ledger(ledger, healthy.recommendations, now=NOW)
    assert regenerated[key]["status"] == STATUS_IMPLEMENTED
    assert regenerated[key]["implemented_at"] == "2026-08-01T00:00:00+00:00"


def test_due_for_review_finds_implemented_recommendations_past_their_date(healthy):
    ledger = tr.merge_into_ledger({}, healthy.recommendations, now=NOW)
    key = sorted(ledger)[0]
    ledger[key]["status"] = STATUS_IMPLEMENTED
    ledger[key]["review_after_date"] = "2026-08-10"

    due = tr.due_for_review(ledger, today="2026-08-17")
    assert [e["fingerprint"] for e in due] == [key]


def test_a_recommendation_not_yet_due_is_not_reviewed(healthy):
    ledger = tr.merge_into_ledger({}, healthy.recommendations, now=NOW)
    key = sorted(ledger)[0]
    ledger[key]["status"] = STATUS_IMPLEMENTED
    ledger[key]["review_after_date"] = "2026-12-01"
    assert tr.due_for_review(ledger, today="2026-08-17") == []


def test_a_verdict_is_written_back_onto_the_ledger_entry(healthy):
    ledger = tr.merge_into_ledger({}, healthy.recommendations, now=NOW)
    key = sorted(ledger)[0]
    verdict = tr.classify_outcome(_plan(), 0.02, 0.06, 1000, 1000)
    updated = tr.apply_verdict(ledger[key], verdict, now=NOW)

    assert updated["outcome"] == OUTCOME_IMPROVED
    assert updated["outcome_before"] == 0.02
    assert updated["outcome_measured_at"] == NOW.isoformat()


def test_the_ledger_round_trips_through_the_store(healthy):
    store = InMemoryStore()
    ledger = tr.merge_into_ledger({}, healthy.recommendations, now=NOW)
    tr.save_ledger(store, ledger)
    assert set(tr.load_ledger(store)) == set(ledger)


def test_ledger_summary_counts_status_and_outcome(healthy):
    ledger = tr.merge_into_ledger({}, healthy.recommendations, now=NOW)
    summary = tr.summarise(ledger)
    assert summary["total"] == len(healthy.recommendations)
    assert summary["by_outcome"][OUTCOME_PENDING] == len(healthy.recommendations)


# --------------------------------------------------------------------------
# Report structure and rendering
# --------------------------------------------------------------------------

def test_the_report_serialises_to_json_safe_data(healthy):
    import json

    payload = json.dumps(healthy.to_dict())
    assert "\"facts\"" in payload and "\"inferences\"" in payload


def test_facts_and_inferences_are_separate_collections(healthy):
    assert healthy.facts and healthy.inferences
    fact_ids = {f.id for f in healthy.facts}
    inference_ids = {i.id for i in healthy.inferences}
    assert fact_ids.isdisjoint(inference_ids)


def test_sections_reference_ids_rather_than_duplicating_data(healthy):
    exec_section = healthy.sections["executive_health"]
    for ref in exec_section["traffic_trend"]:
        assert healthy.fact_by_id(ref) is not None


def test_all_eight_report_sections_render(healthy):
    text = render.render_markdown(healthy)
    for heading in ("## Executive summary", "## What changed", "## SEO opportunities",
                    "## Landing-page and CRO findings", "## UX and Clarity findings",
                    "## Cross-source conclusions", "## Prioritized actions",
                    "## Data quality and readiness"):
        assert heading in text, heading


def test_the_low_volume_report_says_so_prominently(low):
    text = render.render_markdown(low)
    assert "Insufficient data for recommendation" in text
    assert "No actions are proposed above Monitor" in text


def test_the_rendered_report_keeps_facts_and_interpretation_apart(healthy):
    text = render.render_markdown(healthy)
    assert "Measured facts" in text
    assert "correlations, not causes" in text


def test_alternative_explanations_are_rendered(healthy):
    text = render.render_markdown(healthy)
    assert "Could also be explained by:" in text


def test_measurement_plans_are_rendered(healthy):
    text = render.render_markdown(healthy)
    assert "Measurement plan: track" in text


def test_the_report_states_it_changed_nothing(healthy):
    text = render.render_markdown(healthy)
    assert "No change has been made to the site" in text


def test_rendering_is_deterministic(healthy):
    assert render.render_markdown(healthy) == render.render_markdown(healthy)


def test_rates_and_counts_are_formatted_appropriately():
    assert render.format_value("gsc_ctr", 0.125) == "12.50%"
    assert render.format_value("gsc_position", 8.0) == "8.0"
    assert render.format_value("ga4_sessions", 1234) == "1,234"
    assert render.format_value("ga4_sessions", None) == "—"


# --------------------------------------------------------------------------
# Reading from the store
# --------------------------------------------------------------------------

def test_the_agent_reads_history_from_the_durable_store():
    store = InMemoryStore()
    period, prior = fx.healthy_records()
    fx.store_with(store, period + prior + fx.baseline_records())

    report = analysis.analyse_from_store(store, today=TODAY, now=NOW)

    assert report.facts
    assert report.data_coverage["clarity_ledger"]["days_available"] > 0


def test_an_empty_store_produces_an_honest_empty_report():
    report = analysis.analyse_from_store(InMemoryStore(), today=TODAY, now=NOW)

    assert report.readiness == INSUFFICIENT_DATA
    assert report.recommendations == []
    assert "No Clarity history stored yet" in report.data_coverage["clarity_note"]
