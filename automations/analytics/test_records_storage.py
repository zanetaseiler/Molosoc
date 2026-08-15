#!/usr/bin/env python3
"""
Offline tests for the record schema, the storage interface, and the Clarity
call budget.

The aggregation guard is the important part: summing overlapping Clarity
windows produces a plausible-looking but inflated number that nobody catches
by eye, so it has to fail loudly instead.

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import records as rec  # noqa: E402
import storage as st  # noqa: E402
from call_budget import BudgetExhausted, ClarityCallBudget  # noqa: E402


def make(date="2026-08-14", metric="clarity_sessions", value=10, window_days=1,
         metric_class=rec.PERFORMANCE, entity_id=rec.SITE_ENTITY_ID,
         entity_type=rec.SITE, source=rec.CLARITY, **kw):
    return rec.MetricRecord(
        date=date, source=source, entity_type=entity_type, entity_id=entity_id,
        metric=metric, value=value, window_days=window_days,
        metric_class=metric_class, **kw,
    )


# --------------------------------------------------------------------------
# Record invariants
# --------------------------------------------------------------------------

def test_valid_record_round_trips_through_a_dict():
    original = make(sample_basis=85, collected_at="2026-08-14T17:34:03+00:00")
    assert rec.MetricRecord.from_dict(original.to_dict()) == original


def test_unknown_source_is_rejected():
    with pytest.raises(rec.RecordError, match="unknown source"):
        make(source="mixpanel")


def test_unknown_entity_type_is_rejected():
    with pytest.raises(rec.RecordError, match="unknown entity_type"):
        make(entity_type="widget")


def test_unknown_metric_class_is_rejected():
    with pytest.raises(rec.RecordError, match="unknown metric_class"):
        make(metric_class="vibes")


def test_malformed_date_is_rejected():
    with pytest.raises(rec.RecordError, match="YYYY-MM-DD"):
        make(date="14/08/2026")


def test_empty_entity_id_is_rejected():
    with pytest.raises(rec.RecordError, match="entity_id"):
        make(entity_id="")


def test_single_day_records_are_aggregatable_multi_day_are_not():
    assert make(window_days=1).is_aggregatable
    assert not make(window_days=3).is_aggregatable


# --------------------------------------------------------------------------
# The double-counting guard
# --------------------------------------------------------------------------

def test_daily_snapshots_sum_normally():
    daily = [make(date=f"2026-08-{d:02d}", value=10) for d in (11, 12, 13)]
    assert rec.sum_metric(daily, "clarity_sessions") == 30


def test_summing_overlapping_three_day_windows_is_refused():
    # Three consecutive numOfDays=3 snapshots overlap by two days each. Summing
    # them would roughly triple the real figure.
    overlapping = [make(date=f"2026-08-{d:02d}", value=85, window_days=3)
                   for d in (11, 12, 13)]
    with pytest.raises(rec.RecordError, match="window_days > 1"):
        rec.sum_metric(overlapping, "clarity_sessions")


def test_a_single_multi_day_record_is_still_refused():
    with pytest.raises(rec.RecordError, match="window_days > 1"):
        rec.sum_metric([make(window_days=2)], "clarity_sessions")


def test_mixing_performance_and_data_quality_is_refused():
    mixed = [
        make(date="2026-08-11", metric="clarity_sessions"),
        make(date="2026-08-12", metric="clarity_sessions", metric_class=rec.DATA_QUALITY),
    ]
    with pytest.raises(rec.RecordError, match="metric classes"):
        rec.sum_metric(mixed, "clarity_sessions")


def test_duplicate_records_for_one_day_are_refused():
    # Two snapshots for the same date must never both count.
    duplicated = [make(date="2026-08-14"), make(date="2026-08-14")]
    with pytest.raises(rec.RecordError, match="duplicate record"):
        rec.sum_metric(duplicated, "clarity_sessions")


def test_class_filters_split_performance_from_data_quality():
    rows = [
        make(metric="clarity_sessions"),
        make(metric="clarity_bot_share", metric_class=rec.DATA_QUALITY),
    ]
    assert [r.metric for r in rec.performance_only(rows)] == ["clarity_sessions"]
    assert [r.metric for r in rec.data_quality_only(rows)] == ["clarity_bot_share"]


# --------------------------------------------------------------------------
# Storage
# --------------------------------------------------------------------------

@pytest.fixture(params=["memory", "local"])
def store(request, tmp_path):
    return st.InMemoryStore() if request.param == "memory" else st.LocalFileStore(tmp_path)


def test_json_documents_round_trip(store):
    store.put_json("raw/clarity/2026-08-14/x.json", {"payload": [{"metricName": "Traffic"}]})
    assert store.get_json("raw/clarity/2026-08-14/x.json")["payload"][0]["metricName"] == "Traffic"


def test_missing_key_raises(store):
    with pytest.raises(st.StorageError, match="no such key"):
        store.get_json("nope.json")


def test_writes_do_not_overwrite_by_default(store):
    store.put_json("a.json", {"v": 1})
    with pytest.raises(st.StorageError, match="already exists"):
        store.put_json("a.json", {"v": 2})
    assert store.get_json("a.json") == {"v": 1}


def test_overwrite_is_explicit(store):
    store.put_json("a.json", {"v": 1})
    store.put_json("a.json", {"v": 2}, overwrite=True)
    assert store.get_json("a.json") == {"v": 2}


def test_keys_list_by_prefix(store):
    store.put_json("raw/clarity/2026-08-13/a.json", {})
    store.put_json("raw/clarity/2026-08-14/b.json", {})
    store.put_json("facts/clarity/2026-08-14.json", {})
    assert len(store.list_keys("raw/clarity/")) == 2
    assert store.list_keys("facts/") == ["facts/clarity/2026-08-14.json"]


def test_exists(store):
    assert not store.exists("a.json")
    store.put_json("a.json", {})
    assert store.exists("a.json")


def test_records_round_trip(store):
    rows = [make(metric="clarity_sessions", value=85),
            make(metric="clarity_bot_share", value=0.4, metric_class=rec.DATA_QUALITY)]
    store.put_records("facts/clarity/2026-08-14.json", rows)
    loaded = store.get_records("facts/clarity/2026-08-14.json")
    assert loaded == rows


def test_stored_documents_are_isolated_from_caller_mutation(store):
    document = {"payload": {"n": 1}}
    store.put_json("a.json", document)
    document["payload"]["n"] = 999
    assert store.get_json("a.json")["payload"]["n"] == 1


def test_local_store_rejects_path_traversal(tmp_path):
    local = st.LocalFileStore(tmp_path)
    with pytest.raises(st.StorageError, match="unsafe key"):
        local.put_json("../escape.json", {})
    with pytest.raises(st.StorageError, match="unsafe key"):
        local.put_json("/etc/passwd", {})


def test_no_shipped_backend_claims_durability(tmp_path):
    # Both shipped backends are for development and tests. A collector that
    # cares checks this before trusting that history was preserved.
    assert st.InMemoryStore().is_durable() is False
    assert st.LocalFileStore(tmp_path).is_durable() is False


def test_key_layout_keeps_revisions_separate():
    first = st.raw_key("clarity", "2026-08-14", "2026-08-14T06:00:00+00:00")
    second = st.raw_key("clarity", "2026-08-14", "2026-08-14T18:00:00+00:00")
    assert first != second
    assert first.startswith("raw/clarity/2026-08-14/")
    assert st.facts_key("clarity", "2026-08-14") == "facts/clarity/2026-08-14.json"


# --------------------------------------------------------------------------
# Clarity call budget
# --------------------------------------------------------------------------

NOW = dt.datetime(2026, 8, 14, 9, 0, tzinfo=dt.timezone.utc)


def test_budget_starts_full():
    budget = ClarityCallBudget(st.InMemoryStore(), automated_cap=3)
    assert budget.used(now=NOW) == 0
    assert budget.remaining(now=NOW) == 3


def test_reserving_consumes_budget():
    budget = ClarityCallBudget(st.InMemoryStore(), automated_cap=3)
    budget.reserve(1, reason="daily snapshot", now=NOW)
    assert budget.remaining(now=NOW) == 2


def test_budget_refuses_beyond_the_automated_cap():
    budget = ClarityCallBudget(st.InMemoryStore(), automated_cap=2)
    budget.reserve(1, now=NOW)
    budget.reserve(1, now=NOW)
    with pytest.raises(BudgetExhausted, match="budget for 2026-08-14 is spent"):
        budget.reserve(1, now=NOW)


def test_automated_cap_leaves_headroom_below_claritys_hard_limit():
    budget = ClarityCallBudget(st.InMemoryStore())
    assert budget.hard_limit == 10
    assert budget.automated_cap < budget.hard_limit


def test_a_cap_above_the_hard_limit_is_rejected():
    with pytest.raises(ValueError, match="hard limit"):
        ClarityCallBudget(st.InMemoryStore(), automated_cap=11)


def test_budget_persists_across_processes():
    # Each collector run is a fresh process; an in-memory counter would make
    # the limit unenforceable.
    store = st.InMemoryStore()
    ClarityCallBudget(store, automated_cap=3).reserve(1, now=NOW)
    assert ClarityCallBudget(store, automated_cap=3).used(now=NOW) == 1


def test_budget_resets_on_the_next_utc_day():
    store = st.InMemoryStore()
    budget = ClarityCallBudget(store, automated_cap=1)
    budget.reserve(1, now=NOW)
    tomorrow = NOW + dt.timedelta(days=1)
    assert budget.remaining(now=tomorrow) == 1


def test_status_reports_the_full_picture():
    budget = ClarityCallBudget(st.InMemoryStore(), automated_cap=3)
    budget.reserve(1, now=NOW)
    assert budget.status(now=NOW) == {
        "date": "2026-08-14", "used": 1, "automated_cap": 3,
        "hard_limit": 10, "remaining": 2,
    }
