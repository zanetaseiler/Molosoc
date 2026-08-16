#!/usr/bin/env python3
"""
Offline tests for the weekly report layer.

Four properties matter most here, and each is asserted directly:

  1. The report makes ZERO Clarity API calls. The daily collector owns
     Clarity's 10-per-day budget and a missed day cannot be backfilled, so a
     report that spent from it could permanently cost real data.
  2. At Molosoc's current volume it says "insufficient data for
     recommendation" and proposes nothing above Monitor.
  3. Periods before 2026-08-16 report conversions as unmeasured, never zero.
  4. It writes a Markdown file for the workflow to upload, and nothing else.

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import clarity_api  # noqa: E402
import coverage as cov  # noqa: E402
import fixtures as fx  # noqa: E402
import google_hydrate as gh  # noqa: E402
import periods as pr  # noqa: E402
import weekly_report as wr  # noqa: E402
from analysis_model import INSUFFICIENT_DATA, PRIORITY_MONITOR, READY  # noqa: E402
from records import CLARITY  # noqa: E402
from storage import InMemoryStore  # noqa: E402

NOW = dt.datetime(2026, 8, 17, 6, 0, tzinfo=dt.timezone.utc)


@pytest.fixture(autouse=True)
def no_live_clarity(monkeypatch):
    """Make any live Clarity call explode.

    If the report ever reaches the Clarity API, every test in this file fails
    loudly instead of quietly spending the collector's budget.
    """
    def forbidden(*_args, **_kwargs):
        raise AssertionError(
            "the weekly report must never call the Clarity API — Clarity comes "
            "from the durable ledger only"
        )

    monkeypatch.setattr(clarity_api, "fetch_live_insights", forbidden)
    monkeypatch.setattr(clarity_api, "load_api_token", forbidden)


# --------------------------------------------------------------------------
# Zero Clarity API calls
# --------------------------------------------------------------------------

def test_the_report_makes_no_clarity_api_call():
    # The autouse fixture turns any Clarity call into a failure; completing
    # the run is the proof.
    report, markdown = wr.generate_from_fixture("low_volume")
    assert markdown
    assert wr.summarise_run(report)["clarity_api_calls"] == 0


def test_clarity_facts_still_come_from_the_ledger():
    report, _ = wr.generate_from_fixture("low_volume")
    clarity_facts = [f for f in report.facts if f.source == CLARITY]
    assert clarity_facts, "Clarity must still contribute, via storage"
    assert report.data_coverage["clarity_ledger"]["days_available"] > 0


def test_google_hydration_is_exactly_two_windows():
    report, _ = wr.generate_from_fixture("low_volume")
    # Two sources across the period and prior windows, cached, no repeats.
    assert report.data_quality["hydration"]["api_calls_made"] == 4
    assert report.data_quality["hydration"]["persisted"] is False


# --------------------------------------------------------------------------
# Comparison period
# --------------------------------------------------------------------------

def test_the_period_is_the_latest_complete_week_against_the_previous_one():
    report, _ = wr.generate_from_fixture("low_volume", today="2026-08-17")
    assert report.period["start"] == "2026-08-08"
    assert report.period["end"] == "2026-08-14"
    assert report.period["days"] == 7
    assert report.comparison_periods[0]["start"] == "2026-08-01"
    assert report.comparison_periods[0]["end"] == "2026-08-07"


def test_a_wednesday_run_analyses_whole_monday_to_sunday_weeks():
    # The reason the schedule is Wednesday: the anchor lands on a Sunday.
    windows = pr.build_windows(today="2026-09-02")  # a Wednesday
    start = dt.date.fromisoformat(windows[pr.PERIOD].start)
    end = dt.date.fromisoformat(windows[pr.PERIOD].end)
    assert start.weekday() == 0   # Monday
    assert end.weekday() == 6     # Sunday


# --------------------------------------------------------------------------
# Low-volume behaviour
# --------------------------------------------------------------------------

def test_low_volume_reports_insufficient_data_for_recommendation():
    report, markdown = wr.generate_from_fixture("low_volume")

    assert report.readiness == INSUFFICIENT_DATA
    assert "insufficient data for recommendation" in markdown
    assert all(r.priority == PRIORITY_MONITOR for r in report.recommendations)


def test_low_volume_still_reports_facts_and_trends():
    report, markdown = wr.generate_from_fixture("low_volume")
    assert report.facts
    assert "## What changed" in markdown
    assert "Sessions (GA4)" in markdown


def test_no_strategic_recommendation_is_manufactured_at_low_volume():
    report, _ = wr.generate_from_fixture("low_volume")
    assert not [r for r in report.recommendations if r.readiness == READY
                and r.priority != PRIORITY_MONITOR]


def test_a_healthy_volume_fixture_does_produce_recommendations():
    # Proves the gate is a threshold, not a permanent block.
    report, _ = wr.generate_from_fixture("healthy")
    assert report.readiness == READY
    assert report.recommendations


# --------------------------------------------------------------------------
# Ecommerce boundary
# --------------------------------------------------------------------------

def test_a_pre_boundary_week_reports_conversions_as_unmeasured():
    # 2026-08-08..14 is entirely before the 2026-08-16 activation date.
    report, markdown = wr.generate_from_fixture("low_volume", today="2026-08-17")

    conversions = report.data_quality["conversions"]
    assert conversions["state"] == gh.CONVERSIONS_BEFORE_TRACKING
    assert "not an absence of sales" in conversions["message"]
    assert "not an absence of sales" in markdown


def test_a_pre_boundary_week_invents_no_conversion_facts():
    report, _ = wr.generate_from_fixture("low_volume", today="2026-08-17")
    assert not [f for f in report.facts if f.metric.startswith("ga4_key_event_")]


def test_a_post_boundary_week_reports_conversions_normally():
    # 2026-09-02 is a Wednesday: period 2026-08-24..30, entirely tracked.
    report, _ = wr.generate_from_fixture("healthy", today="2026-09-02")

    boundary = report.data_quality["ecommerce_boundary"]
    assert boundary["period_state"] == gh.TRACKING_ACTIVE
    assert boundary["comparison_valid"] is True
    assert [f for f in report.facts if f.metric == "ga4_key_event_purchase"]


def test_the_boundary_is_stated_in_the_rendered_report():
    _, markdown = wr.generate_from_fixture("low_volume")
    assert "Ecommerce tracking boundary (2026-08-16)" in markdown


# --------------------------------------------------------------------------
# Tracking coverage diagnostic
# --------------------------------------------------------------------------

def test_coverage_compares_ga4_against_clarity_human_sessions():
    result = cov.assess_tracking_coverage(120, 150, clarity_total_sessions=180)
    assert result["ratio"] == pytest.approx(0.8)
    assert result["state"] == cov.COVERAGE_ALIGNED
    assert "120" in result["headline"] and "150" in result["headline"]


def test_coverage_flags_ga4_capturing_materially_less():
    result = cov.assess_tracking_coverage(40, 200)
    assert result["state"] == cov.COVERAGE_GA4_LOWER
    assert "materially less" in result["headline"]


def test_coverage_flags_ga4_higher_without_blaming_ga4():
    result = cov.assess_tracking_coverage(300, 150)
    assert result["state"] == cov.COVERAGE_GA4_HIGHER
    assert "session definitions" in result["headline"]


def test_coverage_refuses_to_judge_tiny_samples():
    result = cov.assess_tracking_coverage(10, 12)
    assert result["state"] == cov.COVERAGE_INSUFFICIENT
    assert "Too few sessions" in result["headline"]


def test_coverage_handles_a_missing_source():
    assert cov.assess_tracking_coverage(None, 100)["state"] == cov.COVERAGE_UNAVAILABLE
    assert cov.assess_tracking_coverage(100, None)["state"] == cov.COVERAGE_UNAVAILABLE


def test_coverage_is_never_presented_as_a_consent_rate():
    result = cov.assess_tracking_coverage(120, 200)
    text = result["headline"] + " " + " ".join(result["caveats"])
    assert "consent rate" in text  # only ever to deny it
    assert "not a consent rate" in text
    assert "coverage indicator" in text


def test_every_coverage_result_carries_its_caveats():
    for args in ((120, 150), (10, 12), (None, 100), (300, 100)):
        assert len(cov.assess_tracking_coverage(*args)["caveats"]) >= 4


def test_the_coverage_diagnostic_appears_in_the_report():
    report, markdown = wr.generate_from_fixture("healthy")
    assert report.data_quality["tracking_coverage"]["state"]
    assert "Tracking coverage (GA4 vs Clarity)" in markdown
    assert "not a consent rate" in markdown


# --------------------------------------------------------------------------
# Report artifact generation
# --------------------------------------------------------------------------

def test_the_report_file_is_written_with_a_dated_name(tmp_path):
    exit_code = wr.main(["--fixture", "low_volume", "--out-dir", str(tmp_path)])
    assert exit_code == 0

    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == ["molosoc-marketing-analysis-2026-08-14.md"]


def test_the_json_analysis_object_can_also_be_written(tmp_path):
    wr.main(["--fixture", "low_volume", "--out-dir", str(tmp_path), "--also-json"])
    files = sorted(p.suffix for p in tmp_path.iterdir())
    assert files == [".json", ".md"]


def test_the_written_report_contains_all_eight_sections(tmp_path):
    wr.main(["--fixture", "healthy", "--out-dir", str(tmp_path)])
    text = next(tmp_path.iterdir()).read_text(encoding="utf-8")

    for heading in ("## Executive summary", "## What changed", "## SEO opportunities",
                    "## Landing-page and CRO findings", "## UX and Clarity findings",
                    "## Cross-source conclusions", "## Prioritized actions",
                    "## Data quality and readiness"):
        assert heading in text, heading


def test_the_report_states_it_changed_nothing(tmp_path):
    wr.main(["--fixture", "low_volume", "--out-dir", str(tmp_path)])
    text = next(tmp_path.iterdir()).read_text(encoding="utf-8")
    assert "No change has been made to the site" in text


def test_report_generation_is_deterministic():
    first = wr.generate_from_fixture("healthy")[1]
    second = wr.generate_from_fixture("healthy")[1]
    assert first == second


def test_the_filename_is_stable_for_a_given_period():
    report, _ = wr.generate_from_fixture("low_volume", today="2026-08-17")
    assert wr.report_filename(report) == "molosoc-marketing-analysis-2026-08-14.md"
    assert wr.report_filename(report, "json").endswith(".json")


def test_the_run_summary_reports_the_api_budget():
    report, _ = wr.generate_from_fixture("low_volume")
    summary = wr.summarise_run(report)

    assert summary["clarity_api_calls"] == 0
    assert summary["google_api_calls"] == 4
    assert summary["readiness"] == INSUFFICIENT_DATA


def test_nothing_is_written_outside_the_output_directory(tmp_path):
    before = set(Path(".").glob("**/*.md"))
    wr.main(["--fixture", "low_volume", "--out-dir", str(tmp_path)])
    after = set(Path(".").glob("**/*.md"))
    assert before == after, "the report must not land anywhere but --out-dir"
