#!/usr/bin/env python3
"""Offline tests for diagnostic_purchase_attribution (no network or credentials)."""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import diagnostic_purchase_attribution as dpa  # noqa: E402


def test_defaults_target_order_1026_day_only():
    assert (dpa.DEFAULT_START, dpa.DEFAULT_END) == ("2026-10-05", "2026-10-05")


def test_classify_identity_dimensions():
    names = ["date", "customEvent:ga_session_id", "customUser:Client_ID",
             "customEvent:other", "sessionSourceMedium"]
    found = dpa.classify_identity_dimensions(names)
    assert found["ga_session_id"] == ["customEvent:ga_session_id"]
    assert found["client_id"] == ["customUser:Client_ID"]
    assert dpa.classify_identity_dimensions(["date"]) == {"ga_session_id": [], "client_id": []}


def test_identity_section_reports_not_registered_and_failure():
    class Ok:
        def get_metadata(self, name):
            return SimpleNamespace(dimensions=[SimpleNamespace(api_name="date")])

    text, errors = dpa.identity_section(Ok(), "1")
    assert "ga_session_id: NOT registered" in text and errors == []

    class Broken:
        def get_metadata(self, name):
            raise RuntimeError("denied")

    text, errors = dpa.identity_section(Broken(), "1")
    assert "not checked" in text and len(errors) == 1


def test_one_failing_report_does_not_abort_others(monkeypatch):
    calls = []

    def fake(client, pid, start, end, dims, metrics, limit, match):
        calls.append(dims)
        if len(calls) == 1:
            raise RuntimeError("incompatible dimensions")
        return [["x"] * (len(dims) + len(metrics))]

    monkeypatch.setattr(dpa, "ga4_report", fake)
    sections, errors = dpa.run_reports(None, "1", "2026-10-05", "2026-10-05",
                                       dpa.PURCHASE_REPORTS)
    assert len(calls) == len(dpa.PURCHASE_REPORTS) == len(sections)
    assert len(errors) == 1 and "REPORT FAILED" in sections[0]


def test_empty_result_is_not_zero(monkeypatch):
    monkeypatch.setattr(dpa, "ga4_report", lambda *a, **k: [])
    sections, errors = dpa.run_reports(None, "1", "2026-10-05", "2026-10-05",
                                       dpa.NOT_SET_REPORTS[:1])
    assert "(no rows returned)" in sections[0] and errors == []


def test_reports_are_read_only_exact_filters():
    for _, dims, metrics, limit, match in dpa.PURCHASE_REPORTS + dpa.NOT_SET_REPORTS:
        assert dims and metrics and limit > 0 and len(match) == 2
