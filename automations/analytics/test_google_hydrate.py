#!/usr/bin/env python3
"""
Offline tests for on-demand GA4 / Search Console hydration.

No credentials, no network. The fetchers are injected, so the whole path —
window selection, caching, normalization, conversion readiness — is exercised
deterministically.

The behaviour that matters most: Clarity is never hydrated (its API cannot
return history), and a missing `purchase` produces a message rather than a
fabricated zero.

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
from analysis_model import INSUFFICIENT_DATA, PRIORITY_MONITOR, READY  # noqa: E402
from records import CLARITY, GA4, GSC, PAGE, SITE  # noqa: E402
from storage import InMemoryStore  # noqa: E402

NOW = dt.datetime(2026, 8, 17, 6, 0, tzinfo=dt.timezone.utc)
TODAY = "2026-08-17"
COLLECTED_AT = "2026-08-17T06:00:00+00:00"


def ga4_payload(sessions=21, users=14, views=28, key_events=None, pages=None):
    payload = {
        "ok": True, "propertyId": "521643495",
        "dateRange": {"start": "2026-08-08", "end": "2026-08-14"},
        "users": users, "sessions": sessions, "views": views,
        "landingPages": pages if pages is not None else [
            {"landingPage": "/", "sessions": 8, "activeUsers": 5},
            {"landingPage": "/?fbclid=abc", "sessions": 1, "activeUsers": 1},
            {"landingPage": "/product/molosoc-hydratacni-navleky-na-nohy/",
             "sessions": 8, "activeUsers": 4},
        ],
    }
    if key_events is not None:
        payload["keyEvents"] = key_events
    return payload


def gsc_payload(clicks=1, impressions=8, include_staging=True):
    pages = [{"page": "https://molosoc.com/", "clicks": clicks,
              "impressions": impressions, "ctr": 0.125, "position": 8.0}]
    if include_staging:
        pages.append({"page": "https://staging.molosoc.com/legal-disclaimer/",
                      "clicks": 0, "impressions": 1, "ctr": 0.0, "position": 5.0})
    return {
        "ok": True, "siteUrl": "sc-domain:molosoc.com",
        "dateRange": {"start": "2026-08-08", "end": "2026-08-14"},
        "clicks": clicks, "impressions": impressions, "ctr": 0.125, "position": 8.0,
        "topQueries": [{"query": "molosoc", "clicks": clicks,
                        "impressions": max(3, clicks * 3),
                        "ctr": 0.333, "position": 1.0}],
        "topPages": pages,
    }


class RecordingFetcher:
    """Counts calls and records the windows requested."""

    def __init__(self, payload_factory):
        self.payload_factory = payload_factory
        self.calls = []

    def __call__(self, start, end):
        self.calls.append((start, end))
        return self.payload_factory(start, end)


@pytest.fixture
def windows():
    return pr.build_windows(today=TODAY)


@pytest.fixture
def hydrator():
    return gh.GoogleHydrator(
        ga4_fetcher=RecordingFetcher(lambda s, e: ga4_payload()),
        gsc_fetcher=RecordingFetcher(lambda s, e: gsc_payload()),
        collected_at=COLLECTED_AT,
    )


# --------------------------------------------------------------------------
# Fetching and caching
# --------------------------------------------------------------------------

def test_hydration_returns_normalized_records(hydrator, windows):
    result = hydrator.hydrate(windows[pr.PERIOD])

    assert result.ok
    assert result.records
    assert {r.source for r in result.records} == {GA4, GSC}


def test_hydration_requests_the_analysis_window(hydrator, windows):
    hydrator.hydrate(windows[pr.PERIOD])
    assert hydrator.ga4_fetcher.calls == [("2026-08-08", "2026-08-14")]
    assert hydrator.gsc_fetcher.calls == [("2026-08-08", "2026-08-14")]


def test_different_windows_are_fetched_separately(hydrator, windows):
    hydrator.hydrate(windows[pr.PERIOD])
    hydrator.hydrate(windows[pr.PRIOR])
    assert len(hydrator.ga4_fetcher.calls) == 2
    assert hydrator.calls_made == 4  # two sources x two windows


def test_the_same_window_is_never_fetched_twice(hydrator, windows):
    hydrator.hydrate(windows[pr.PERIOD])
    hydrator.hydrate(windows[pr.PERIOD])
    hydrator.hydrate(windows[pr.PERIOD])

    assert len(hydrator.ga4_fetcher.calls) == 1
    assert len(hydrator.gsc_fetcher.calls) == 1
    assert hydrator.calls_made == 2


def test_hydrate_all_shares_the_cache_across_windows(hydrator, windows):
    results = hydrator.hydrate_all(
        {pr.PERIOD: windows[pr.PERIOD], "again": windows[pr.PERIOD]}
    )
    assert len(hydrator.ga4_fetcher.calls) == 1
    assert all(r.records for r in results.values())


def test_a_fetch_failure_is_reported_not_raised(windows):
    def explode(start, end):
        raise RuntimeError("403 insufficient permissions")

    hydrator = gh.GoogleHydrator(ga4_fetcher=explode,
                                 gsc_fetcher=lambda s, e: gsc_payload(),
                                 collected_at=COLLECTED_AT)
    result = hydrator.hydrate(windows[pr.PERIOD])

    assert not result.ok
    assert any("403" in e for e in result.errors)
    # The other source still contributes.
    assert any(r.source == GSC for r in result.records)


def test_an_absent_fetcher_simply_contributes_nothing(windows):
    hydrator = gh.GoogleHydrator(ga4_fetcher=None,
                                 gsc_fetcher=lambda s, e: gsc_payload(),
                                 collected_at=COLLECTED_AT)
    result = hydrator.hydrate(windows[pr.PERIOD])

    assert result.ok
    assert {r.source for r in result.records} == {GSC}


def test_clarity_is_never_hydrated(hydrator, windows):
    result = hydrator.hydrate(windows[pr.PERIOD])
    assert not any(r.source == CLARITY for r in result.records)


# --------------------------------------------------------------------------
# Normalization is reused, not reimplemented
# --------------------------------------------------------------------------

def test_hydrated_urls_are_canonicalized(hydrator, windows):
    result = hydrator.hydrate(windows[pr.PERIOD])
    page_ids = {r.entity_id for r in result.records if r.entity_type == PAGE}

    assert "https://molosoc.com/" in page_ids
    assert not any("fbclid" in pid for pid in page_ids)


def test_hydrated_records_carry_language_metadata(hydrator, windows):
    result = hydrator.hydrate(windows[pr.PERIOD])
    languages = {r.language for r in result.records if r.entity_type == PAGE}
    assert "cs" in languages


def test_staging_rows_are_labelled_for_exclusion(hydrator, windows):
    result = hydrator.hydrate(windows[pr.PERIOD])
    staging = [r for r in result.records if "staging" in r.entity_id]
    assert staging
    assert all(r.notes["host_classification"] == "non_production" for r in staging)


def test_hydrated_records_cover_the_whole_window_not_a_day(hydrator, windows):
    result = hydrator.hydrate(windows[pr.PERIOD])
    assert all(r.window_days == 7 for r in result.records)


# --------------------------------------------------------------------------
# Conversions are never fabricated
# --------------------------------------------------------------------------

def test_missing_key_events_are_reported_not_zeroed(windows):
    hydrator = gh.GoogleHydrator(
        ga4_fetcher=lambda s, e: ga4_payload(key_events=None),
        gsc_fetcher=lambda s, e: gsc_payload(), collected_at=COLLECTED_AT,
    )
    result = hydrator.hydrate(windows[pr.PERIOD])

    assert not any(r.metric.startswith("ga4_key_event_") for r in result.records)
    readiness = gh.assess_conversions(result.key_events, fetched=result.ok)
    assert readiness["state"] == gh.CONVERSIONS_NONE
    assert "purchase" in readiness["message"]
    assert "No conversion figures have been inferred" in readiness["message"]


def test_supporting_events_without_purchase_are_reported_as_incomplete():
    readiness = gh.assess_conversions({"add_to_cart": 12, "begin_checkout": 4})

    assert readiness["state"] == gh.CONVERSIONS_MISSING_PRIMARY
    assert "purchase" in readiness["missing"]
    assert "add_to_cart" in readiness["present"]
    assert "No purchase figure has been inferred" in readiness["message"]


def test_a_complete_conversion_set_is_reported_ok():
    readiness = gh.assess_conversions(
        {"purchase": 3, "begin_checkout": 8, "add_to_cart": 19}
    )
    assert readiness["state"] == gh.CONVERSIONS_OK
    assert gh.conversions_available(readiness)


def test_a_zero_purchase_count_is_kept_because_it_was_measured():
    # Zero purchases is a real observation; absent is not the same thing.
    readiness = gh.assess_conversions({"purchase": 0})
    assert readiness["state"] == gh.CONVERSIONS_OK


def test_conversions_not_fetched_is_its_own_state():
    readiness = gh.assess_conversions({}, fetched=False)
    assert readiness["state"] == gh.CONVERSIONS_NOT_FETCHED
    assert "not hydrated" in readiness["message"]


def test_present_key_events_become_records(windows):
    hydrator = gh.GoogleHydrator(
        ga4_fetcher=lambda s, e: ga4_payload(
            key_events={"purchase": 3, "add_to_cart": 19}),
        gsc_fetcher=lambda s, e: gsc_payload(), collected_at=COLLECTED_AT,
    )
    result = hydrator.hydrate(windows[pr.PERIOD])
    metrics = {r.metric for r in result.records}

    assert "ga4_key_event_purchase" in metrics
    assert "ga4_key_event_add_to_cart" in metrics
    assert "ga4_key_event_begin_checkout" not in metrics  # absent, not zeroed


# --------------------------------------------------------------------------
# End to end: hydrated Google + stored Clarity
# --------------------------------------------------------------------------

def _clarity_ledger_store():
    """Only Clarity in the store — Google arrives by hydration."""
    store = InMemoryStore()
    period, prior = fx.low_volume_records()
    clarity = [r for r in period + prior if r.source == CLARITY]
    fx.store_with(store, clarity + fx.baseline_records())
    return store


def test_the_agent_combines_hydrated_google_with_stored_clarity():
    store = _clarity_ledger_store()
    hydrator = gh.GoogleHydrator(
        ga4_fetcher=lambda s, e: ga4_payload(),
        gsc_fetcher=lambda s, e: gsc_payload(), collected_at=COLLECTED_AT,
    )

    report = analysis.analyse_from_store(store, today=TODAY, now=NOW, hydrator=hydrator)

    sources = {f.source for f in report.facts}
    assert GA4 in sources and GSC in sources and CLARITY in sources
    assert report.data_quality["hydration"]["used"] is True
    assert report.data_quality["hydration"]["persisted"] is False


def test_hydration_costs_exactly_two_windows_of_calls():
    store = _clarity_ledger_store()
    ga4 = RecordingFetcher(lambda s, e: ga4_payload())
    gsc = RecordingFetcher(lambda s, e: gsc_payload())
    hydrator = gh.GoogleHydrator(ga4_fetcher=ga4, gsc_fetcher=gsc,
                                 collected_at=COLLECTED_AT)

    analysis.analyse_from_store(store, today=TODAY, now=NOW, hydrator=hydrator)

    # Period and prior, once each, per source — no redundant repeats.
    assert len(ga4.calls) == 2
    assert len(gsc.calls) == 2
    assert sorted(ga4.calls) == [("2026-08-01", "2026-08-07"), ("2026-08-08", "2026-08-14")]


def test_clarity_still_comes_only_from_the_ledger():
    store = _clarity_ledger_store()
    hydrator = gh.GoogleHydrator(
        ga4_fetcher=lambda s, e: ga4_payload(),
        gsc_fetcher=lambda s, e: gsc_payload(), collected_at=COLLECTED_AT,
    )

    report = analysis.analyse_from_store(store, today=TODAY, now=NOW, hydrator=hydrator)

    clarity_facts = [f for f in report.facts if f.source == CLARITY]
    assert clarity_facts
    assert report.data_coverage["clarity_ledger"]["days_available"] > 0


def test_hydrated_run_at_real_volume_still_refuses_to_recommend():
    # The whole point: hydration does not lower the bar.
    store = _clarity_ledger_store()
    hydrator = gh.GoogleHydrator(
        ga4_fetcher=lambda s, e: ga4_payload(sessions=21),
        gsc_fetcher=lambda s, e: gsc_payload(), collected_at=COLLECTED_AT,
    )

    report = analysis.analyse_from_store(store, today=TODAY, now=NOW, hydrator=hydrator)

    assert report.readiness == INSUFFICIENT_DATA
    assert all(r.priority == PRIORITY_MONITOR for r in report.recommendations)


def test_a_hydrated_run_at_healthy_volume_is_ready():
    store = _clarity_ledger_store()
    hydrator = gh.GoogleHydrator(
        ga4_fetcher=lambda s, e: ga4_payload(sessions=900, users=700, views=1500),
        gsc_fetcher=lambda s, e: gsc_payload(clicks=40, impressions=900),
        collected_at=COLLECTED_AT,
    )

    report = analysis.analyse_from_store(store, today=TODAY, now=NOW, hydrator=hydrator)
    assert report.readiness == READY


def test_staging_is_excluded_from_a_hydrated_run():
    store = _clarity_ledger_store()
    hydrator = gh.GoogleHydrator(
        ga4_fetcher=lambda s, e: ga4_payload(),
        gsc_fetcher=lambda s, e: gsc_payload(include_staging=True),
        collected_at=COLLECTED_AT,
    )

    report = analysis.analyse_from_store(store, today=TODAY, now=NOW, hydrator=hydrator)

    assert not any("staging" in f.entity_id for f in report.facts)
    assert report.data_quality["excluded_non_production_records"] >= 1


def test_the_report_states_conversions_are_unavailable():
    store = _clarity_ledger_store()
    hydrator = gh.GoogleHydrator(
        ga4_fetcher=lambda s, e: ga4_payload(key_events=None),
        gsc_fetcher=lambda s, e: gsc_payload(), collected_at=COLLECTED_AT,
    )

    report = analysis.analyse_from_store(store, today=TODAY, now=NOW, hydrator=hydrator)
    text = render.render_markdown(report)

    # With the committed activation date (2026-08-16), this window predates
    # ecommerce tracking — so the correct answer is "not tracked then", not
    # "purchase is unconfigured in GA4".
    assert report.data_quality["conversions"]["state"] == gh.CONVERSIONS_BEFORE_TRACKING
    assert "Conversions unavailable" in text
    assert "not persisted" in text


def test_the_non_hydrated_path_still_works_from_storage_alone():
    store = InMemoryStore()
    period, prior = fx.healthy_records()
    fx.store_with(store, period + prior + fx.baseline_records())

    report = analysis.analyse_from_store(store, today=TODAY, now=NOW)

    assert report.facts
    assert report.data_quality["hydration"]["used"] is False


def test_no_google_records_are_written_to_the_store_by_hydration():
    store = _clarity_ledger_store()
    before = set(store.list_keys())
    hydrator = gh.GoogleHydrator(
        ga4_fetcher=lambda s, e: ga4_payload(),
        gsc_fetcher=lambda s, e: gsc_payload(), collected_at=COLLECTED_AT,
    )

    analysis.analyse_from_store(store, today=TODAY, now=NOW, hydrator=hydrator)

    # Hydration introduces no new persistent storage of any kind.
    assert set(store.list_keys()) == before
