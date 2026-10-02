#!/usr/bin/env python3
"""Offline tests for diagnostic_window (no network, credentials or bucket)."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import diagnostic_window as dw  # noqa: E402
from storage import InMemoryStore, StorageError, facts_key  # noqa: E402


def test_window_dates_default_and_limits():
    assert dw.window_dates("2026-09-29", "2026-10-01") == [
        "2026-09-29", "2026-09-30", "2026-10-01"]
    with pytest.raises(ValueError):
        dw.window_dates("2026-10-01", "2026-09-29")
    with pytest.raises(ValueError):
        dw.window_dates("2026-09-01", "2026-10-01")


def test_clarity_section_reports_missing_days_without_zeroing():
    store = InMemoryStore()
    store.put_json(facts_key("clarity", "2026-09-29"), {"records": [
        {"entity_type": "site", "entity_id": "site", "metric": "clarity_sessions",
         "value": 120, "sample_basis": None, "window_days": 1},
        {"entity_type": "device", "entity_id": "Mobile", "metric": "clarity_visits",
         "value": 90, "sample_basis": None, "window_days": 1}]})
    sections, found, failures = dw.clarity_section(store, ["2026-09-29", "2026-09-30"])
    assert found == ["2026-09-29"]
    assert "clarity_sessions" in sections[0] and "Mobile" in sections[0]
    assert "no stored snapshot" in sections[1]
    assert failures == []


def test_clarity_section_read_error_is_a_failure_not_missing():
    class Broken(InMemoryStore):
        def exists(self, key):
            return True

        def get_json(self, key):
            raise StorageError("GCS read failed: denied")

    sections, found, failures = dw.clarity_section(Broken(), ["2026-09-29"])
    assert found == [] and len(failures) == 1
    assert "no stored snapshot" not in sections[0] and "READ FAILED" in sections[0]


def test_top_groups_keeps_all_events_of_top_sources():
    rows = [["a", "page_view", "1000", "1"], ["b", "page_view", "500", "1"],
            ["c", "page_view", "400", "1"], ["a", "purchase", "1", "1"],
            ["c", "purchase", "1", "1"]]
    shown, note = dw.top_groups(rows, n=2)
    assert ["c", "purchase", "1", "1"] not in shown  # c is outside the top 2 groups
    assert ["a", "purchase", "1", "1"] in shown
    assert "top 2 of 3" in note


class FakeClient:
    def __init__(self, fail_on=None):
        self.fail_on = fail_on
        self.calls = []

    def run_report(self, request):
        dims = [d.name for d in request.dimensions]
        self.calls.append(dims)
        if self.fail_on and self.fail_on in dims:
            raise RuntimeError("bad dimension")
        row = SimpleNamespace(
            dimension_values=[SimpleNamespace(value="x") for _ in dims],
            metric_values=[SimpleNamespace(value="3") for _ in request.metrics])
        return SimpleNamespace(rows=[row])


def test_run_ga4_one_failure_does_not_abort_others():
    client = FakeClient(fail_on="deviceCategory")
    sections, errors = dw.run_ga4(client, "1", "2026-09-29", "2026-10-01")
    assert len(client.calls) == len(dw.GA4_REPORTS)
    assert len(errors) == 2 and all("bad dimension" in e for e in errors)
    assert len(sections) == len(dw.GA4_REPORTS) - 2
