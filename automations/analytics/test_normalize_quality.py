#!/usr/bin/env python3
"""
Offline tests for normalization and data-quality assessment.

The Clarity fixture below is the real payload shape from the verified
connection run on 2026-08-14 — 85 sessions of which 34 were bots, and the same
16 metrics that project actually returns. Testing against real numbers rather
than invented ones is what caught the bot-share and float-truncation issues.

Run with:  python3 -m pytest automations/analytics/
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import normalize as nz  # noqa: E402
import quality as ql  # noqa: E402
from records import CLARITY, DATA_QUALITY, GA4, GSC, PAGE, PERFORMANCE, SITE  # noqa: E402

COLLECTED_AT = "2026-08-14T17:34:03+00:00"

# Shape and values as returned by the live project.
CLARITY_PAYLOAD = [
    {"metricName": "DeadClickCount", "information": [
        {"sessionsCount": "85", "sessionsWithMetricPercentage": 8.24,
         "sessionsWithoutMetricPercentage": 91.76, "pagesViews": "7", "subTotal": "8"}]},
    {"metricName": "ExcessiveScroll", "information": [
        {"sessionsCount": "85", "sessionsWithMetricPercentage": 0,
         "pagesViews": "0", "subTotal": "0"}]},
    {"metricName": "RageClickCount", "information": [
        {"sessionsCount": "85", "sessionsWithMetricPercentage": 0, "subTotal": "0"}]},
    {"metricName": "QuickbackClick", "information": [
        {"sessionsCount": "85", "sessionsWithMetricPercentage": 0, "subTotal": "0"}]},
    {"metricName": "ScriptErrorCount", "information": [
        {"sessionsCount": "85", "sessionsWithMetricPercentage": 15.29,
         "pagesViews": "13", "subTotal": "30"}]},
    {"metricName": "ErrorClickCount", "information": [
        {"sessionsCount": "85", "sessionsWithMetricPercentage": 0, "subTotal": "0"}]},
    {"metricName": "ScrollDepth", "information": [{"averageScrollDepth": 35.38}]},
    {"metricName": "Traffic", "information": [
        {"totalSessionCount": "85", "totalBotSessionCount": "34",
         "distinctUserCount": "120", "pagesPerSessionPercentage": 1.0166666666666666}]},
    {"metricName": "EngagementTime", "information": [
        {"totalTime": "157", "activeTime": "109"}]},
    {"metricName": "Browser", "information": [
        {"name": "Chrome", "sessionsCount": "78"}, {"name": "Safari", "sessionsCount": "5"}]},
    {"metricName": "Device", "information": [{"name": "PC", "sessionsCount": "82"}]},
    {"metricName": "OS", "information": [{"name": "MacOSX", "sessionsCount": "78"}]},
    {"metricName": "Country", "information": [
        {"name": "Czech Republic", "sessionsCount": "85"}]},
    {"metricName": "PageTitle", "information": [
        {"name": "Molosoc – Moisture Lock Sock", "sessionsCount": "48"}]},
    {"metricName": "ReferrerUrl", "information": [{"name": "None", "sessionsCount": "44"}]},
    {"metricName": "PopularPages", "information": [
        {"url": "https://molosoc.com/", "visitsCount": "42"},
        {"url": "https://molosoc.com/?fbclid=abc123", "visitsCount": "6"},
        {"url": "https://staging.molosoc.com/", "visitsCount": "3"}]},
]


@pytest.fixture
def clarity_rows():
    return nz.clarity_records(CLARITY_PAYLOAD, date="2026-08-14",
                              collected_at=COLLECTED_AT, num_days=1)


def find(rows, metric, entity_id=None):
    for row in rows:
        if row.metric == metric and (entity_id is None or row.entity_id == entity_id):
            return row
    raise AssertionError(f"no record for {metric} / {entity_id}")


# --------------------------------------------------------------------------
# Clarity normalization
# --------------------------------------------------------------------------

def test_traffic_totals_are_read(clarity_rows):
    assert find(clarity_rows, "clarity_sessions").value == 85
    assert find(clarity_rows, "clarity_distinct_users").value == 120


def test_bot_metrics_are_classified_as_data_quality_not_performance(clarity_rows):
    assert find(clarity_rows, "clarity_bot_sessions").metric_class == DATA_QUALITY
    assert find(clarity_rows, "clarity_bot_share").metric_class == DATA_QUALITY
    assert find(clarity_rows, "clarity_sessions").metric_class == PERFORMANCE


def test_human_sessions_are_derived_so_trends_can_exclude_bots(clarity_rows):
    # 85 total - 34 bots. A traffic trend should read this, not the total.
    assert find(clarity_rows, "clarity_human_sessions").value == 51


def test_bot_share_is_computed_from_the_real_numbers(clarity_rows):
    assert find(clarity_rows, "clarity_bot_share").value == pytest.approx(34 / 85)


def test_rates_carry_their_denominator(clarity_rows):
    dead = find(clarity_rows, "clarity_dead_click_rate")
    assert dead.value == pytest.approx(0.0824)
    assert dead.sample_basis == 85


def test_friction_counts_are_stored_alongside_rates(clarity_rows):
    assert find(clarity_rows, "clarity_dead_click_count").value == 8
    assert find(clarity_rows, "clarity_rage_click_rate").value == 0


def test_script_errors_are_data_quality_not_a_behaviour_metric(clarity_rows):
    # A script-error spike means measurement may be broken, so it must not sit
    # in the same class as user-behaviour signals.
    assert find(clarity_rows, "clarity_script_error_rate").metric_class == DATA_QUALITY
    assert find(clarity_rows, "clarity_error_click_rate").metric_class == PERFORMANCE


def test_floats_are_not_truncated(clarity_rows):
    assert find(clarity_rows, "clarity_scroll_depth").value == pytest.approx(35.38)
    assert find(clarity_rows, "clarity_pages_per_session").value == pytest.approx(1.0166666, rel=1e-5)


def test_dimension_rows_become_their_own_entities(clarity_rows):
    assert find(clarity_rows, "clarity_sessions", "Chrome").value == 78
    assert find(clarity_rows, "clarity_sessions", "PC").value == 82
    assert find(clarity_rows, "clarity_sessions", "Czech Republic").value == 85


def test_missing_referrer_becomes_an_explicit_direct_entity(clarity_rows):
    assert find(clarity_rows, "clarity_sessions", nz.DIRECT_REFERRER).value == 44


def test_popular_pages_are_canonicalized_and_merged(clarity_rows):
    # The tracking-parameter variant is the same page, so its visits add.
    pages = [r for r in clarity_rows if r.entity_type == PAGE]
    ids = [r.entity_id for r in pages]

    assert ids.count("https://molosoc.com/") == 1
    home = [r for r in pages if r.entity_id == "https://molosoc.com/"][0]
    assert home.value == 48  # 42 plain + 6 from the fbclid variant
    assert "https://staging.molosoc.com/" in ids


def test_page_records_carry_their_host_classification(clarity_rows):
    staging = [r for r in clarity_rows
               if r.entity_type == PAGE and "staging" in r.entity_id][0]
    assert staging.notes["host_classification"] == "non_production"


def test_every_clarity_record_is_a_single_day_window(clarity_rows):
    assert all(r.window_days == 1 for r in clarity_rows)
    assert all(r.is_aggregatable for r in clarity_rows)
    assert all(r.source == CLARITY for r in clarity_rows)


def test_window_end_records_the_exact_instant(clarity_rows):
    # numOfDays=1 is a trailing 24h window, not a calendar day.
    assert all(r.window_end == COLLECTED_AT for r in clarity_rows)


def test_an_empty_payload_normalizes_to_nothing():
    assert nz.clarity_records([], date="2026-08-14", collected_at=COLLECTED_AT) == []


def test_an_unreadable_payload_shape_is_rejected():
    with pytest.raises(ValueError, match="expected a list"):
        nz.clarity_records("nonsense", date="2026-08-14", collected_at=COLLECTED_AT)


def test_unknown_metric_names_are_ignored_not_fatal():
    payload = [{"metricName": "SomethingNew", "information": [{"x": 1}]},
               {"metricName": "ScrollDepth", "information": [{"averageScrollDepth": 10}]}]
    rows = nz.clarity_records(payload, date="2026-08-14", collected_at=COLLECTED_AT)
    assert find(rows, "clarity_scroll_depth").value == 10


# --------------------------------------------------------------------------
# GA4 / Search Console normalization
# --------------------------------------------------------------------------

GA4_RESULT = {
    "ok": True, "propertyId": "521643495",
    "dateRange": {"start": "2026-08-07", "end": "2026-08-13"},
    "users": 10, "sessions": 21, "views": 23,
    "landingPages": [
        {"landingPage": "/", "sessions": 8, "activeUsers": 5},
        {"landingPage": "/product/molosoc-hydratacni-navleky-na-nohy/",
         "sessions": 8, "activeUsers": 0},
        {"landingPage": "/?fbclid=IwcGRvZg", "sessions": 1, "activeUsers": 1},
        {"landingPage": "", "sessions": 1, "activeUsers": 1},
    ],
}

GSC_RESULT = {
    "ok": True, "siteUrl": "sc-domain:molosoc.com",
    "dateRange": {"start": "2026-08-05", "end": "2026-08-11"},
    "clicks": 1, "impressions": 8, "ctr": 0.125, "position": 8.0,
    "topQueries": [{"query": "molosoc", "clicks": 1, "impressions": 3,
                    "ctr": 0.333, "position": 1.0}],
    "topPages": [
        {"page": "https://molosoc.com/", "clicks": 1, "impressions": 8,
         "ctr": 0.125, "position": 8.0},
        {"page": "https://staging.molosoc.com/legal-disclaimer/", "clicks": 0,
         "impressions": 1, "ctr": 0.0, "position": 5.0},
    ],
}


def test_ga4_site_totals_normalize():
    rows = nz.ga4_records(GA4_RESULT, COLLECTED_AT)
    assert find(rows, "ga4_sessions", "site").value == 21
    assert all(r.source == GA4 for r in rows)


def test_ga4_window_length_is_carried_so_it_cannot_be_summed_as_daily():
    rows = nz.ga4_records(GA4_RESULT, COLLECTED_AT)
    assert all(r.window_days == 7 for r in rows)
    assert not rows[0].is_aggregatable


def test_ga4_landing_pages_are_canonicalized_and_merged():
    # The real GA4 report returns / and ?fbclid= variants as separate rows for
    # one page. They must become one record whose sessions are added, not
    # several records competing for the same identity.
    rows = nz.ga4_records(GA4_RESULT, COLLECTED_AT)
    page_ids = [r.entity_id for r in rows if r.entity_type == PAGE]

    assert "https://molosoc.com/" in page_ids
    assert not any("fbclid" in pid for pid in page_ids)
    session_ids = [r.entity_id for r in rows
                   if r.entity_type == PAGE and r.metric == "ga4_sessions"]
    assert session_ids.count("https://molosoc.com/") == 1  # one record per metric

    home_sessions = [r for r in rows if r.entity_id == "https://molosoc.com/"
                     and r.metric == "ga4_sessions"][0]
    assert home_sessions.value == 9  # 8 from "/" plus 1 from the fbclid variant


def test_a_merged_page_records_what_folded_into_it():
    rows = nz.ga4_records(GA4_RESULT, COLLECTED_AT)
    home = [r for r in rows if r.entity_id == "https://molosoc.com/"][0]

    assert len(home.notes["merged_from"]) == 2
    assert home.notes["dropped_params"] == ["fbclid"]


def test_an_unmerged_page_carries_no_merge_note():
    rows = nz.ga4_records(GA4_RESULT, COLLECTED_AT)
    product = [r for r in rows if "hydratacni" in r.entity_id][0]
    assert "merged_from" not in product.notes


def test_ga4_blank_landing_page_becomes_an_explicit_entity():
    rows = nz.ga4_records(GA4_RESULT, COLLECTED_AT)
    assert any(r.entity_id == "(unattributed)" for r in rows)


def test_ga4_recent_windows_are_marked_provisional():
    rows = nz.ga4_records(GA4_RESULT, "2026-08-14T00:00:00+00:00")
    assert all(r.is_final is False for r in rows)


def test_ga4_old_windows_are_final():
    rows = nz.ga4_records(GA4_RESULT, "2026-09-01T00:00:00+00:00")
    assert all(r.is_final is True for r in rows)


def test_failed_checks_normalize_to_nothing():
    assert nz.ga4_records({"ok": False, "error": "boom"}, COLLECTED_AT) == []
    assert nz.gsc_records({"ok": False, "error": "boom"}, COLLECTED_AT) == []


def test_gsc_site_metrics_normalize():
    rows = nz.gsc_records(GSC_RESULT, COLLECTED_AT)
    assert find(rows, "gsc_impressions", "site").value == 8
    assert find(rows, "gsc_ctr", "site").value == pytest.approx(0.125)
    assert all(r.source == GSC for r in rows)


def test_gsc_rates_carry_impressions_as_their_denominator():
    rows = nz.gsc_records(GSC_RESULT, COLLECTED_AT)
    assert find(rows, "gsc_ctr", "site").sample_basis == 8
    assert find(rows, "gsc_position", "site").sample_basis == 8


def test_gsc_queries_become_query_entities():
    rows = nz.gsc_records(GSC_RESULT, COLLECTED_AT)
    assert find(rows, "gsc_clicks", "molosoc").value == 1


def test_gsc_staging_pages_are_normalized_and_labelled():
    rows = nz.gsc_records(GSC_RESULT, COLLECTED_AT)
    staging = [r for r in rows if "staging" in r.entity_id]
    assert staging
    assert all(r.notes["host_classification"] == "non_production" for r in staging)


# --------------------------------------------------------------------------
# Data quality
# --------------------------------------------------------------------------

def test_the_real_bot_share_raises_a_warning(clarity_rows):
    # 34/85 = 40%, above the warn threshold and below critical.
    flags = ql.assess_bot_share(clarity_rows)
    assert [f.code for f in flags] == ["bot_share_high"]
    assert flags[0].severity == ql.WARN
    assert flags[0].details["bot_share"] == pytest.approx(0.4, abs=0.01)


def test_a_majority_bot_snapshot_is_critical():
    payload = [{"metricName": "Traffic", "information": [
        {"totalSessionCount": "100", "totalBotSessionCount": "70",
         "distinctUserCount": "80", "pagesPerSessionPercentage": 1.0}]}]
    rows = nz.clarity_records(payload, date="2026-08-14", collected_at=COLLECTED_AT)
    flags = ql.assess_bot_share(rows)
    assert flags[0].severity == ql.CRITICAL
    assert not ql.performance_is_trustworthy(flags)


def test_a_low_bot_share_is_reported_as_normal():
    payload = [{"metricName": "Traffic", "information": [
        {"totalSessionCount": "200", "totalBotSessionCount": "10",
         "distinctUserCount": "180", "pagesPerSessionPercentage": 2.0}]}]
    rows = nz.clarity_records(payload, date="2026-08-14", collected_at=COLLECTED_AT)
    flags = ql.assess_bot_share(rows)
    assert flags[0].code == "bot_share_normal"
    assert ql.performance_is_trustworthy(flags)


def test_tiny_samples_do_not_get_a_bot_verdict():
    payload = [{"metricName": "Traffic", "information": [
        {"totalSessionCount": "4", "totalBotSessionCount": "3",
         "distinctUserCount": "4", "pagesPerSessionPercentage": 1.0}]}]
    rows = nz.clarity_records(payload, date="2026-08-14", collected_at=COLLECTED_AT)
    flags = ql.assess_bot_share(rows)
    assert flags[0].code == "bot_share_not_assessable"


def test_production_split_removes_staging_pages_only(clarity_rows):
    kept, excluded = ql.split_production(clarity_rows)
    assert all("staging" not in r.entity_id for r in kept)
    assert excluded and all("staging" in r.entity_id for r in excluded)
    # Non-page records (site totals, browsers, countries) pass through.
    assert any(r.entity_type == SITE for r in kept)


def test_exclusions_are_reported_never_silent(clarity_rows):
    _, excluded = ql.split_production(clarity_rows)
    flags = ql.exclusion_flags(excluded)
    assert flags[0].code == "non_production_excluded"
    assert flags[0].details["by_host"] == {"staging.molosoc.com": 1}
    assert "deliberate, not data loss" in flags[0].message


def test_no_exclusions_raises_no_flag():
    assert ql.exclusion_flags([]) == []


def test_assess_snapshot_returns_data_and_what_it_removed(clarity_rows):
    kept, excluded, flags = ql.assess_snapshot(clarity_rows)
    assert len(kept) + len(excluded) == len(clarity_rows)
    codes = {f.code for f in flags}
    assert "bot_share_high" in codes
    assert "non_production_excluded" in codes


def test_worst_severity_picks_the_highest():
    flags = [ql.QualityFlag("a", ql.INFO, ""), ql.QualityFlag("b", ql.CRITICAL, ""),
             ql.QualityFlag("c", ql.WARN, "")]
    assert ql.worst_severity(flags) == ql.CRITICAL
    assert ql.worst_severity([]) == ql.INFO
