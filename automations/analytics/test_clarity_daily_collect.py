#!/usr/bin/env python3
"""
Offline tests for the Clarity daily collector.

No network and no token. Three properties matter most, and each is asserted
directly rather than left to code review:

1. Exactly one API call per collection, and none at all when the day is
   already collected or the budget is spent.
2. One daily bucket per UTC date. A second numOfDays=1 call the same day
   covers an overlapping 24-hour window and must never become a second bucket.
3. Snapshots are always numOfDays=1, so nothing overlapping can ever be summed.

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analytics_common  # noqa: E402
import clarity_daily_collect as cdc  # noqa: E402
import storage as st  # noqa: E402
from call_budget import BudgetExhausted, ClarityCallBudget  # noqa: E402
from test_normalize_quality import CLARITY_PAYLOAD  # noqa: E402

FAKE_TOKEN = "eyJhbGciOiJIUzI1NiJ9.fake-collector-token.abcdef"
NOW = dt.datetime(2026, 8, 14, 6, 0, tzinfo=dt.timezone.utc)
LATER = dt.datetime(2026, 8, 14, 18, 0, tzinfo=dt.timezone.utc)
TOMORROW = dt.datetime(2026, 8, 15, 6, 0, tzinfo=dt.timezone.utc)


@pytest.fixture(autouse=True)
def isolate_secrets(monkeypatch):
    monkeypatch.delenv("CLARITY_API_TOKEN", raising=False)
    analytics_common.reset_secrets()
    yield
    analytics_common.reset_secrets()


class FakeResponse:
    def __init__(self, payload, status_code=200):
        import json
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeSession:
    """Records every request so the call count can be asserted."""

    def __init__(self, responses=None):
        self.responses = list(responses or [FakeResponse(CLARITY_PAYLOAD)])
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self.responses.pop(0)


@pytest.fixture
def store():
    return st.InMemoryStore()


# --------------------------------------------------------------------------
# Call discipline
# --------------------------------------------------------------------------

def test_collection_makes_exactly_one_api_call(store):
    session = FakeSession()
    summary = cdc.collect(store, FAKE_TOKEN, session=session, now=NOW)

    assert len(session.calls) == 1
    assert summary["api_calls_made"] == 1


def test_snapshots_are_always_single_day(store):
    session = FakeSession()
    cdc.collect(store, FAKE_TOKEN, session=session, now=NOW)

    # numOfDays=1 is not configurable — overlapping windows cannot be summed.
    assert session.calls[0]["params"]["numOfDays"] == "1"
    assert cdc.SNAPSHOT_NUM_DAYS == 1


def test_token_travels_only_in_the_authorization_header(store):
    session = FakeSession()
    cdc.collect(store, FAKE_TOKEN, session=session, now=NOW)

    call = session.calls[0]
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert FAKE_TOKEN not in call["url"]
    assert FAKE_TOKEN not in str(call["params"])


def test_budget_is_reserved_before_the_call(store):
    budget = ClarityCallBudget(store, automated_cap=3)
    cdc.collect(store, FAKE_TOKEN, session=FakeSession(), budget=budget, now=NOW)

    assert budget.used(now=NOW) == 1
    assert budget.remaining(now=NOW) == 2


def test_an_exhausted_budget_prevents_the_call_entirely(store):
    budget = ClarityCallBudget(store, automated_cap=1)
    budget.reserve(1, now=NOW)
    session = FakeSession()

    with pytest.raises(BudgetExhausted):
        cdc.collect(store, FAKE_TOKEN, session=session, budget=budget, now=NOW)

    assert session.calls == []


# --------------------------------------------------------------------------
# Non-overlapping daily buckets
# --------------------------------------------------------------------------

def test_a_second_collection_the_same_day_is_refused(store):
    cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)
    session = FakeSession()

    with pytest.raises(cdc.AlreadyCollected, match="overlapping 24-hour window"):
        cdc.collect(store, FAKE_TOKEN, session=session, now=LATER)

    assert session.calls == []  # refused before spending a call


def test_forcing_a_second_collection_stores_a_revision_not_a_second_bucket(store):
    cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)
    summary = cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=LATER, force=True)

    assert summary["is_daily_bucket"] is False
    # Two raw revisions, still exactly one facts document for the date.
    assert len(store.list_keys("raw/clarity/2026-08-14/")) == 2
    assert store.exists("facts/clarity/2026-08-14.json")


def test_a_forced_revision_does_not_overwrite_the_authoritative_facts(store):
    first = cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)
    before = store.get_records("facts/clarity/2026-08-14.json")

    quiet = [{"metricName": "Traffic", "information": [
        {"totalSessionCount": "1", "totalBotSessionCount": "0",
         "distinctUserCount": "1", "pagesPerSessionPercentage": 1.0}]}]
    cdc.collect(store, FAKE_TOKEN, session=FakeSession([FakeResponse(quiet)]),
                now=LATER, force=True)

    assert store.get_records("facts/clarity/2026-08-14.json") == before
    assert first["is_daily_bucket"] is True


def test_the_next_day_collects_normally(store):
    cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)
    summary = cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=TOMORROW)

    assert summary["is_daily_bucket"] is True
    assert summary["date"] == "2026-08-15"
    assert store.exists("facts/clarity/2026-08-15.json")


def test_consecutive_daily_buckets_can_be_summed_without_double_counting(store):
    from records import sum_metric

    cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)
    cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=TOMORROW)

    rows = (store.get_records("facts/clarity/2026-08-14.json")
            + store.get_records("facts/clarity/2026-08-15.json"))
    site_sessions = [r for r in rows
                     if r.metric == "clarity_sessions" and r.entity_id == "site"]
    assert sum_metric(site_sessions) == 170  # 85 + 85, no overlap


# --------------------------------------------------------------------------
# What gets stored
# --------------------------------------------------------------------------

def test_raw_payload_is_stored_before_normalization(store):
    cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)

    key = store.list_keys("raw/clarity/2026-08-14/")[0]
    raw = store.get_json(key)
    # The untouched payload survives, so a normalization bug is fixable later.
    assert raw["payload"] == CLARITY_PAYLOAD
    assert raw["window_days"] == 1
    assert raw["is_daily_bucket"] is True


def test_normalized_facts_are_stored_production_only(store):
    cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)

    rows = store.get_records("facts/clarity/2026-08-14.json")
    assert rows
    assert not any("staging" in r.entity_id for r in rows)


def test_excluded_rows_and_flags_are_stored_alongside(store):
    summary = cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)

    quality = store.get_json("facts/clarity/2026-08-14.quality.json")
    codes = {f["code"] for f in quality["flags"]}
    assert "non_production_excluded" in codes
    assert "bot_share_high" in codes
    assert quality["excluded_records"]
    assert summary["records_excluded"] == len(quality["excluded_records"])


def test_bot_and_performance_metrics_are_both_preserved(store):
    cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)

    rows = store.get_records("facts/clarity/2026-08-14.json")
    metrics = {r.metric for r in rows}
    assert {"clarity_sessions", "clarity_human_sessions",
            "clarity_bot_sessions", "clarity_bot_share"} <= metrics


def test_summary_reports_the_budget_state(store):
    summary = cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)
    assert summary["budget"]["hard_limit"] == 10
    assert summary["budget"]["used"] == 1


def test_api_failure_leaves_no_partial_snapshot(store):
    session = FakeSession([FakeResponse({"error": "denied"}, status_code=403)])

    with pytest.raises(PermissionError):
        cdc.collect(store, FAKE_TOKEN, session=session, now=NOW)

    assert store.list_keys("raw/clarity/") == []
    assert store.list_keys("facts/") == []


def test_a_failed_call_still_consumes_budget(store):
    # The call was made; the limit must reflect that or the cap is meaningless.
    budget = ClarityCallBudget(store, automated_cap=3)
    session = FakeSession([FakeResponse({"error": "denied"}, status_code=403)])

    with pytest.raises(PermissionError):
        cdc.collect(store, FAKE_TOKEN, session=session, budget=budget, now=NOW)

    assert budget.used(now=NOW) == 1


# --------------------------------------------------------------------------
# CLI surface
# --------------------------------------------------------------------------

def test_cli_defaults(store):
    args = cdc.parse_args([])
    assert args.store_root == "analytics-data"
    assert args.force is False
    assert args.date is None


def test_status_mode_makes_no_api_call(tmp_path, capsys):
    exit_code = cdc.main(["--status", "--store-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "days collected: 0" in out


def test_summary_output_warns_that_the_local_store_is_not_durable(store, capsys):
    summary = cdc.collect(store, FAKE_TOKEN, session=FakeSession(), now=NOW)
    cdc.print_summary(summary, store)

    out = capsys.readouterr().out
    assert "not durable" in out
    assert "cannot be backfilled" in out
    assert FAKE_TOKEN not in out
