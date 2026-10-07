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
    assert found["client_id"] == []  # case differs: not the client_id parameter
    assert dpa.classify_identity_dimensions(["customUser:client_id"])["client_id"] == [
        "customUser:client_id"]
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
    for _, dims, metrics, limit, match in dpa.AGGREGATE_PURCHASE_REPORTS + dpa.PURCHASE_REPORTS + dpa.NOT_SET_REPORTS:
        assert dims and metrics and limit > 0 and len(match) == 2


def test_every_purchase_report_keeps_transaction_id():
    for title, dims, *_ in dpa.PURCHASE_REPORTS:
        assert "transactionId" in dims, title


def test_no_ga4_incompatible_event_scoped_attribution_reports():
    for title, dims, metrics, *_ in dpa.PURCHASE_REPORTS:
        assert "event-scoped" not in title, title
        assert not ({"manualSourceMedium", "source", "medium"} & set(dims)), title


def test_duplicate_purchase_check_counts_hits_per_transaction():
    by_title = {r[0]: r for r in dpa.AGGREGATE_PURCHASE_REPORTS}
    _, dims, metrics, limit, match = by_title[
        "Purchase: hits per transactionId (duplicate check)"]
    assert dims == ("transactionId",) and metrics == ("eventCount",)
    assert match == ("eventName", "purchase") and limit > 0


def test_purchase_by_host_and_page_is_aggregate_purchase_only():
    by_title = {r[0]: r for r in dpa.AGGREGATE_PURCHASE_REPORTS}
    _, dims, metrics, _, match = by_title["Purchase: hits by host and page"]
    assert dims == ("hostName", "pagePath") and metrics == ("eventCount",)
    assert match == ("eventName", "purchase")


def test_aggregate_reports_run_first_and_are_read_only(monkeypatch):
    seen = []
    monkeypatch.setattr(dpa, "ga4_report",
                        lambda c, p, s, e, dims, m, lim, match: seen.append(match) or [])
    sections, errors = dpa.run_reports(None, "1", "2026-10-05", "2026-10-05",
                                       dpa.AGGREGATE_PURCHASE_REPORTS)
    assert len(sections) == len(dpa.AGGREGATE_PURCHASE_REPORTS) and errors == []
    assert set(seen) == {("eventName", "purchase")}


def test_not_set_reports_are_not_labelled_as_event_paths():
    for title, *_ in dpa.NOT_SET_REPORTS:
        assert "path" not in title.lower().replace("pagepath", "")


def test_funnel_report_is_the_single_requested_shape():
    assert len(dpa.FUNNEL_REPORTS) == 1
    title, dims, metrics, limit, (field, values) = dpa.FUNNEL_REPORTS[0]
    assert dims == ("eventName", "sessionSource", "sessionMedium", "platform", "streamId")
    assert metrics == ("eventCount",) and field == "eventName"
    assert set(values) == {"session_start", "first_visit", "page_view", "view_item",
                           "add_to_cart", "begin_checkout", "add_payment_info", "purchase"}


def test_funnel_report_renders_and_failure_is_isolated(monkeypatch):
    row = ["page_view", "(not set)", "(not set)", "web", "1", "5"]
    monkeypatch.setattr(dpa, "ga4_report", lambda *a, **k: [row])
    sections, errors = dpa.run_reports(None, "1", "2026-10-05", "2026-10-05", dpa.FUNNEL_REPORTS)
    assert errors == []
    assert "page_view" in sections[0] and "streamId" in sections[0]

    def boom(*a, **k):
        raise RuntimeError("rejected")

    monkeypatch.setattr(dpa, "ga4_report", boom)
    sections, errors = dpa.run_reports(None, "1", "2026-10-05", "2026-10-05", dpa.FUNNEL_REPORTS)
    assert len(errors) == 1 and "REPORT FAILED" in sections[0]


def test_ga4_report_uses_in_list_filter_for_funnel(monkeypatch):
    pytest = __import__("pytest")
    pytest.importorskip("google.analytics.data_v1beta")
    captured = {}

    class Client:
        def run_report(self, request):
            captured["req"] = request
            return SimpleNamespace(rows=[])

    dpa.ga4_report(Client(), "1", "2026-10-05", "2026-10-05",
                   ("eventName",), ("eventCount",), 10, ("eventName", dpa.FUNNEL_EVENTS))
    assert list(captured["req"].dimension_filter.filter.in_list_filter.values) == list(
        dpa.FUNNEL_EVENTS)
