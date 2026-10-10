#!/usr/bin/env python3
"""Offline tests for daily_funnel_report (no network, credentials or bucket)."""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import daily_funnel_report as d  # noqa: E402
from storage import InMemoryStore, StorageError, facts_key  # noqa: E402

D = dt.date


def test_utc_bounds_follow_prague_dst():
    # CEST (UTC+2) in October before the 25th; CET (UTC+1) after.
    assert d.utc_bounds(D(2026, 10, 6), D(2026, 10, 9)) == (
        "2026-10-05T22:00:00", "2026-10-09T22:00:00")
    # 25-hour day: 2026-10-25 (DST ends).
    assert d.utc_bounds(D(2026, 10, 25), D(2026, 10, 25)) == (
        "2026-10-24T22:00:00", "2026-10-25T23:00:00")


def test_default_window_is_complete_days_in_prague():
    # 23:30 UTC on 10-09 is already 10-10 01:30 in Prague -> yesterday is 10-09.
    now = dt.datetime(2026, 10, 9, 23, 30, tzinfo=dt.timezone.utc)
    assert d.default_window(3, now) == (D(2026, 10, 7), D(2026, 10, 9))
    assert d.prior_window(D(2026, 10, 6), D(2026, 10, 9)) == (D(2026, 10, 2), D(2026, 10, 5))


def test_validate_window():
    with pytest.raises(ValueError):
        d.validate_window(D(2026, 10, 9), D(2026, 10, 6))
    with pytest.raises(ValueError):
        d.validate_window(D(2026, 9, 1), D(2026, 10, 1))


def test_paid_meta_classification():
    assert d.is_meta_paid("fb / paid")
    assert d.is_meta_paid("facebook / cpc")
    assert d.is_meta_paid("l.facebook.com / referral")
    assert d.is_meta_paid("google / cpc")  # paid medium
    assert not d.is_meta_paid("google / organic")
    assert not d.is_meta_paid("(direct) / (none)")


def test_change_helpers_never_invent_numbers():
    assert d.fmt_change(None, 5) == "n/a"
    assert d.fmt_change(5, 0) == "+5"  # no % against a zero base
    assert d.fmt_change(10, 5) == "+5 (+100%)"
    assert d.fmt(None) == "n/a"


def test_summarize_orders_paid_unpaid_zero():
    assert d.summarize_orders([])["orders"] == 0
    orders = [
        {"status": "processing", "total": "500.00", "currency": "CZK",
         "attribution": {"utm_source": "fb", "utm_medium": "paid"}},
        {"status": "completed", "total": "250", "currency": "CZK", "attribution": {}},
        {"status": "pending", "total": "999", "currency": "CZK"},
        {"status": "failed", "total": "1", "currency": "CZK"},
        {"status": "refunded", "total": "10", "currency": "CZK"},
        {"status": "checkout-draft", "total": "0"},
    ]
    s = d.summarize_orders(orders)
    assert (s["orders"], s["paid"], s["unpaid"], s["refunded"]) == (5, 2, 2, 1)
    assert s["paid_revenue"] == 750.0 and s["paid_meta"] == 1 and s["paid_other"] == 1


def test_woo_window_uses_prague_bounds():
    seen = {}

    def fetch(client, after, before):
        seen["b"] = (after, before)
        return []

    out = d.woo_window(object(), D(2026, 10, 6), D(2026, 10, 9), fetch, lambda o: o)
    assert seen["b"] == ("2026-10-05T22:00:00", "2026-10-09T22:00:00")
    assert out["orders"] == 0


def _snap(store, date, sessions, pages=2.0):
    store.put_json(facts_key("clarity", date), {"records": [
        {"entity_type": "site", "metric": "clarity_sessions", "value": sessions},
        {"entity_type": "site", "metric": "clarity_pages_per_session", "value": pages,
         "sample_basis": sessions},
        {"entity_type": "site", "metric": "clarity_scroll_depth", "value": pages * 10},
        {"entity_type": "site", "metric": "clarity_rage_click_count", "value": 3}]})


def test_clarity_window_maps_to_next_day_snapshot_and_reports_missing():
    store = InMemoryStore()
    _snap(store, "2026-10-07", 100, 1.0)   # Prague 10-06
    _snap(store, "2026-10-08", 300, 3.0)   # Prague 10-07
    out = d.clarity_window(store, D(2026, 10, 6), D(2026, 10, 8))
    assert out["days_found"] == ["2026-10-06", "2026-10-07"]
    assert out["days_missing"] == ["2026-10-08"]
    assert out["sums"]["clarity_sessions"] == 400
    assert out["averages"]["clarity_pages_per_session"] == pytest.approx(2.5)  # weighted


def test_clarity_window_all_missing_has_no_zero_metrics():
    out = d.clarity_window(InMemoryStore(), D(2026, 10, 6), D(2026, 10, 7))
    assert out["days_found"] == [] and "sums" not in out


def test_ga4_window_aggregates_and_isolates_failures():
    def report(client, prop, s, e, dims, metrics, limit, events_only):
        if dims == ("date",):
            return [["20261006", "100", "60", "0.6", "30", "0.4"],
                    ["20261007", "300", "240", "0.8", "50", "0.2"]]
        if dims == ("sessionSourceMedium",):
            return [["fb / paid", "250", "150", "0.6", "10", "0.4"],
                    ["google / organic", "150", "100", "0.6", "10", "0.4"]]
        if dims == ("landingPage",):
            raise RuntimeError("boom token=abcdefghijk")
        if dims == ("eventName",):
            return [["view_item", "400", "200"], ["add_to_cart", "40", "20"],
                    ["purchase", "2", "2"]]
        return [["fb / paid", "add_to_cart", "30", "15"],
                ["google / organic", "add_to_cart", "10", "5"]]

    out = d.ga4_window(None, "1", D(2026, 10, 6), D(2026, 10, 7), report)
    assert out["totals"]["sessions"] == 400
    assert out["totals"]["engagementRate"] == pytest.approx(75.0)  # session-weighted
    assert out["events_paid"]["add_to_cart"] == {"count": 30.0, "users": 15.0}
    assert len(out["errors"]) == 1 and out["errors"][0].startswith("landing pages")
    steps = d.funnel_steps(out["events"])
    assert steps[0] == ("view_item", 200.0, None)
    assert steps[1][2] == pytest.approx(10.0)
    assert steps[2][1] is None  # begin_checkout never recorded -> n/a, not 0


def test_build_report_marks_failures_and_renders_honestly():
    start, end = D(2026, 10, 6), D(2026, 10, 9)
    now = dt.datetime(2026, 10, 9, 12, tzinfo=dt.timezone.utc)

    def broken(a, b):
        raise RuntimeError("no creds")

    woo = lambda a, b: d.summarize_orders([])  # noqa: E731
    clarity = lambda a, b: {"days_found": [], "days_missing": d.days_of(a, b)}  # noqa: E731
    report = d.build_report(start, end, broken, woo, clarity, now)
    text = d.render(report)
    assert report["failed"] is True
    assert "UNAVAILABLE" in text and "Zero orders" in text
    assert "includes today" in text  # 10-09 is today in Prague
    assert "LCP / INP: not collected" in text
    assert "No Clarity snapshot" in text


def test_main_rejects_half_window(capsys):
    assert d.main(["--start", "2026-10-06"]) == 2


def _ga4_report(fail_dims=None, sm_rows=None):
    def report(client, prop, s, e, dims, metrics, limit, events_only):
        if dims == fail_dims:
            raise RuntimeError("boom")
        if dims == ("date",):
            days = d.days_of(dt.date.fromisoformat(s), dt.date.fromisoformat(e))
            return [[x.replace("-", ""), "100", "60", "0.6", "30", "0.4"] for x in days]
        if dims == ("sessionSourceMedium",):
            return sm_rows if sm_rows is not None else [["fb / paid", "50", "30", "0.6", "10", "0.4"]]
        if dims == ("landingPage",):
            return [["/reset/jana@example.com", "5", "3", "0.6", "10", "0.4"],
                    ["/reset/%6Aana@example.org?x=1", "5", "2", "0.4", "20", "0.6"],
                    ["/Products/abc", "4", "2", "0.5", "10", "0.5"],
                    ["/t/abcdef0123456789abcdef", "1", "1", "1", "1", "0"]]
        return []
    return report


def test_landing_paths_are_redacted_and_merged():
    out = d.ga4_window(None, "1", D(2026, 10, 6), D(2026, 10, 6), _ga4_report())
    pages = {r["page"]: r for r in out["landing"]}
    assert set(pages) == {"/*/*"}
    assert pages["/*/*"]["sessions"] == 15
    assert "example" not in str(out["landing"])


def test_landing_path_allowlist_blocks_short_pii_shaped_segments():
    for pii in ("/reset/Jana-Novakova", "/customer/420123456", "/profile/jana.novakova"):
        assert d.redact_path(pii) == "/*/*"
    assert d.redact_path("/foot-covers/moisture-lock-foot-cover/?x=1") == \
        "/foot-covers/moisture-lock-foot-cover"
    assert d.redact_path("/") == "/"


def test_source_medium_is_allowlisted_and_paid_flag_kept():
    rows = [["jana@example.com / promo|x", "5", "3", "0.6", "10", "0.4"],
            ["other-thing / whatever", "2", "1", "0.5", "10", "0.5"],
            ["facebook / paid_social", "7", "4", "0.5", "10", "0.5"],
            ["fb-jana@example.com / cpc", "1", "1", "1", "1", "0"]]
    out = d.merge_source_medium(rows)
    labels = {r["source_medium"]: r for r in out}
    assert set(labels) == {"other / other", "facebook / paid_social", "other / cpc"}
    assert labels["other / other"]["sessions"] == 7 and not labels["other / other"]["paid"]
    assert labels["other / cpc"]["paid"]
    assert "example" not in str(out)


def test_failed_source_medium_is_unavailable_not_zero():
    out = d.ga4_window(None, "1", D(2026, 10, 6), D(2026, 10, 6),
                       _ga4_report(fail_dims=("sessionSourceMedium",)))
    assert out["source_medium"] is None and d.paid_sessions(out) is None


def test_source_medium_row_limit_is_partial_not_total():
    rows = [[f"s{i} / x", "1", "1", "1", "1", "0"] for i in range(d.SOURCE_MEDIUM_LIMIT)]
    out = d.ga4_window(None, "1", D(2026, 10, 6), D(2026, 10, 6), _ga4_report(sm_rows=rows))
    assert d.paid_sessions(out) is None
    assert any("row limit" in e for e in out["errors"])


def test_funnel_does_not_skip_absent_stage():
    events = {"view_item": {"users": 100.0}, "add_to_cart": {"users": 20.0},
              "purchase": {"users": 2.0}}
    steps = dict((s, c) for s, _, c in d.funnel_steps(events))
    assert steps["begin_checkout"] is None and steps["purchase"] is None


def test_funnel_is_labelled_non_cohort_and_ratio_may_exceed_100():
    report = {"window": {"start": "2026-10-06", "end": "2026-10-06"},
              "prior_window": {"start": "2026-10-05", "end": "2026-10-05"},
              "generated_at": "x", "notes": [], "status": {}, "limits": [],
              "ga4": {"totals": None, "events": {"begin_checkout": {"users": 1.0},
                                                 "purchase": {"users": 3.0}}},
              "ga4_prior": None, "woo": None, "woo_prior": None,
              "clarity": {"days_found": [], "days_missing": []},
              "clarity_prior": {}}
    text = d.render(report)
    assert "NOT a cohort funnel" in text and "Ratio to previous stage" in text
    assert "drop-off" not in text.lower().replace("not a true conversion or drop-off rate", "")


def test_paid_funnel_withheld_when_truncated():
    def report(client, prop, s, e, dims, metrics, limit, events_only):
        if dims == ("sessionSourceMedium", "eventName"):
            return [["fb / paid", "add_to_cart", "1", "1"]] * 1000
        return []
    out = d.ga4_window(None, "1", D(2026, 10, 6), D(2026, 10, 6), report)
    assert out["events_paid"] is None and out["events_paid_truncated"] is True
    assert any("not reported" in e for e in out["errors"])


def test_clarity_read_failure_counts_as_gap_and_suppresses_comparison():
    class Boom(InMemoryStore):
        def get_json(self, key):
            if "2026-10-08" in key:
                raise StorageError("unreadable")
            return super().get_json(key)
    store = Boom()
    _snap(store, "2026-10-07", 100, 1.0)
    _snap(store, "2026-10-08", 100, 1.0)
    out = d.clarity_window(store, D(2026, 10, 6), D(2026, 10, 7))
    assert out["days_failed"] == ["2026-10-07"] and out["days_found"] == ["2026-10-06"]
    report = {"window": {"start": "2026-10-06", "end": "2026-10-07"},
              "prior_window": {"start": "2026-10-04", "end": "2026-10-05"},
              "generated_at": "x", "notes": [], "status": {}, "limits": [],
              "ga4": None, "ga4_prior": None, "woo": None, "woo_prior": None,
              "clarity": out, "clarity_prior": out}
    text = d.render(report)
    assert "Days covered: 1/2" in text and "unreadable 2026-10-07" in text
    assert "Changes are n/a" in text


def test_clarity_omitted_metric_is_na_and_gaps_suppress_comparison():
    store = InMemoryStore()
    _snap(store, "2026-10-07", 100, 1.0)
    out = d.clarity_window(store, D(2026, 10, 6), D(2026, 10, 6))
    assert out["sums"]["clarity_script_error_count"] is None
    assert out["sums"]["clarity_rage_click_count"] == 3


def test_prior_window_errors_fail_the_run():
    start, end = D(2026, 10, 6), D(2026, 10, 7)

    def ga4(a, b):
        out = d.ga4_window(None, "1", a, b,
                           _ga4_report(fail_dims=("sessionSourceMedium",) if a < start else None))
        return out

    woo = lambda a, b: d.summarize_orders([])  # noqa: E731
    clarity = lambda a, b: {"days_found": [], "days_missing": d.days_of(a, b)}  # noqa: E731
    now = dt.datetime(2026, 10, 20, 12, tzinfo=dt.timezone.utc)
    report = d.build_report(start, end, ga4, woo, clarity, now)
    assert report["failed"] is True
    assert "previous window: source/medium" in report["status"]["GA4"]
    assert "(previous n/a;" in d.render(report)


def test_clarity_time_metrics_are_summed_not_session_weighted():
    store = InMemoryStore()
    for date, sessions, active in (("2026-10-07", 10, 100), ("2026-10-08", 20, 200)):
        store.put_json(facts_key("clarity", date), {"records": [
            {"entity_type": "site", "metric": "clarity_sessions", "value": sessions},
            {"entity_type": "site", "metric": "clarity_active_time", "value": active}]})
    out = d.clarity_window(store, D(2026, 10, 6), D(2026, 10, 7))
    assert out["sums"]["clarity_active_time"] == 300
    assert "clarity_active_time" not in out["averages"]


def test_redacted_source_keeps_paid_medium_classification():
    orders = [{"status": "completed", "total": "10",
               "attribution": {"utm_source": "[redacted]", "utm_medium": "cpc"}}]
    out = d.summarize_orders(orders)
    assert out["paid_meta"] == 1 and out["paid_other"] == 0
    assert "[redacted source] / cpc" in out["sources_paid"]


def test_clarity_scroll_depth_uses_unweighted_mean_without_sample_basis():
    store = InMemoryStore()
    _snap(store, "2026-10-07", 1, 1.0)     # scroll 10, no basis
    _snap(store, "2026-10-08", 100, 5.0)   # scroll 50, no basis
    out = d.clarity_window(store, D(2026, 10, 6), D(2026, 10, 7))
    assert out["averages"]["clarity_scroll_depth"] == pytest.approx(30.0)
    assert out["averages"]["clarity_pages_per_session"] == pytest.approx(
        (1.0 * 1 + 5.0 * 100) / 101)


def test_landing_truncation_withholds_table_and_flags_error():
    def report(client, prop, s, e, dims, metrics, limit, events_only):
        if dims == ("landingPage",):
            return [(f"/p{i}", 1, 1, 0.5, 1, 0.5) for i in range(d.LANDING_LIMIT)]
        return []
    out = d.ga4_window(object(), "1", D(2026, 10, 6), D(2026, 10, 7), report)
    assert out["landing"] is None and out["landing_truncated"]
    assert any(e.startswith("landing pages: row limit") for e in out["errors"])


def test_source_medium_truncation_withholds_table_and_paid_total():
    def report(client, prop, s, e, dims, metrics, limit, events_only):
        if dims == ("sessionSourceMedium",):
            return [(f"src{i} / referral", 1, 1, 0.5, 1, 0.5)
                    for i in range(d.SOURCE_MEDIUM_LIMIT)]
        return []
    out = d.ga4_window(object(), "1", D(2026, 10, 6), D(2026, 10, 7), report)
    assert out["source_medium"] is None and out["source_medium_truncated"]
    assert d.paid_sessions(out) is None
    assert any(e.startswith("source/medium: row limit") for e in out["errors"])


def test_colliding_redacted_bucket_counts_only_paid_row_sessions():
    rows = [["facebook.com / referral", "10", "5", "0.5", "10", "0.5"],
            ["partner.example / referral", "90", "40", "0.4", "10", "0.5"],
            ["facebook / paid_social", "4", "2", "0.5", "10", "0.5"]]
    out = d.merge_source_medium(rows)
    bucket = {r["source_medium"]: r for r in out}["other / referral"]
    assert bucket["sessions"] == 100
    assert bucket["paid_sessions"] == 10
    assert d.paid_sessions({"source_medium": out}) == 14


def test_missing_ga4_date_withholds_totals_and_flags_partial():
    def report(client, prop, s, e, dims, metrics, limit, events_only):
        if dims == ("date",):
            return [["20261006", "100", "60", "0.6", "30", "0.4"]]
        return []
    out = d.ga4_window(None, "1", D(2026, 10, 6), D(2026, 10, 7), report)
    assert out["totals"] is None and out["days_missing"] == ["20261007"]
    assert any("20261007" in e for e in out["errors"])


def test_landing_allowlist_keeps_known_public_routes_distinct():
    assert d.redact_path("/cz/magazin") == "/cz/magazin"
    assert d.redact_path("/cz/kosik") == "/cz/kosik"
    assert d.redact_path("/cz/callus-remover") == "/cz/callus-remover"
    assert d.redact_path("/reset/jana-novakova") == "/*/*"


def test_missing_ga4_date_withholds_funnel_aggregates():
    def report(client, prop, s, e, dims, metrics, limit, events_only):
        if dims == ("date",):
            return [["20261006", "100", "60", "0.6", "30", "0.4"]]
        if dims == ("eventName",):
            return [["purchase", "3", "2"]]
        if dims == ("sessionSourceMedium", "eventName"):
            return [["fb / paid", "purchase", "3", "2"]]
        return []
    out = d.ga4_window(None, "1", D(2026, 10, 6), D(2026, 10, 7), report)
    assert out["events"] == {} and out["events_paid"] is None
    assert all(u is None for _, u, _ in d.funnel_steps(out["events"]))


def test_funnel_queries_use_the_report_event_list():
    seen = {}

    def report(client, prop, s, e, dims, metrics, limit, events_only):
        if dims[-1] == "eventName":
            seen[dims] = events_only
        return []
    d.ga4_window(None, "1", D(2026, 10, 6), D(2026, 10, 6), report)
    assert seen and all(v == d.FUNNEL_EVENTS for v in seen.values())


def test_clarity_missing_snapshots_mark_status_partial_and_failed():
    start, end = D(2026, 10, 6), D(2026, 10, 8)
    now = dt.datetime(2026, 10, 12, 12, tzinfo=dt.timezone.utc)
    ga4 = lambda a, b: {"errors": [], "failures": []}  # noqa: E731
    woo = lambda a, b: d.summarize_orders([])  # noqa: E731

    def clarity(a, b):
        missing = [d.days_of(a, b)[0]] if a == start else []
        return {"days_found": [x for x in d.days_of(a, b) if x not in missing],
                "days_missing": missing, "days_failed": [], "errors": [], "failures": []}

    report = d.build_report(start, end, ga4, woo, clarity, now)
    assert report["failed"] is True
    assert report["status"]["Clarity (stored)"].startswith("PARTIAL")
    assert "no stored snapshot" in report["status"]["Clarity (stored)"]
    assert report["status"]["GA4"] == "ok"


def test_paid_funnel_compares_with_prior_window():
    ev = {"view_item": {"users": 10.0}}
    report = {"window": {"start": "2026-10-06", "end": "2026-10-06"},
              "prior_window": {"start": "2026-10-05", "end": "2026-10-05"},
              "generated_at": "x", "notes": [], "status": {}, "limits": [],
              "ga4": {"totals": None, "events": ev,
                      "events_paid": {"add_to_cart": {"count": 30.0, "users": 15.0}}},
              "ga4_prior": {"events_paid": {"add_to_cart": {"count": 20.0, "users": 10.0}}},
              "woo": None, "woo_prior": None,
              "clarity": {"days_found": [], "days_missing": []}, "clarity_prior": {}}
    text = d.render(report)
    row = [ln for ln in text.splitlines() if ln.startswith("| add_to_cart |")][-1]
    assert "| 20 | +10 (+50%) |" in row and "| 10 | +5 (+50%) |" in row

    report["ga4_prior"]["events_paid_truncated"] = True
    row = [ln for ln in d.render(report).splitlines() if ln.startswith("| add_to_cart |")][-1]
    assert "| n/a | n/a |" in row


def test_breakdown_tables_compare_with_prior_window():
    def ga4(rows_sm, rows_lp):
        return {"errors": [], "totals": {"sessions": 1, "engagedSessions": 1, "engagementRate": 1,
                                         "averageSessionDuration": 1, "bounceRate": 1},
                "source_medium": rows_sm, "landing": rows_lp, "events": {}, "events_paid": {},
                "source_medium_truncated": False, "landing_truncated": False}
    cur = ga4([{"source_medium": "google / organic", "sessions": 30.0, "engaged": 20.0,
                "paid": False, "paid_sessions": 0.0}],
              [{"page": "/cz", "sessions": 30.0, "engaged": 20.0, "engagement_rate": 60.0,
                "avg_duration": 50.0}])
    prior = ga4([{"source_medium": "google / organic", "sessions": 20.0, "engaged": 10.0,
                  "paid": False, "paid_sessions": 0.0}],
                [{"page": "/cz", "sessions": 20.0, "engaged": 10.0, "engagement_rate": 40.0,
                  "avg_duration": 40.0}])
    empty = {"days_found": [], "days_missing": []}
    base = {"window": {"start": "a", "end": "b"}, "prior_window": {"start": "c", "end": "d"},
            "woo": None, "woo_prior": None, "clarity": empty, "clarity_prior": empty,
            "generated_at": "x", "notes": [], "status": {}, "limits": []}
    out = d.render({**base, "ga4": cur, "ga4_prior": prior})
    assert "| google / organic | 30 | 20 | +10 (+50%) |" in out
    assert "| /cz | 30 | 20 | +10 (+50%) | 60.0 | 40.0 | +20.0 (+50%) |" in out
    # Prior table truncated -> no fabricated comparison.
    out = d.render({**base, "ga4": cur, "ga4_prior": {**prior, "landing_truncated": True,
                                                       "source_medium_truncated": True}})
    assert "| google / organic | 30 | n/a | n/a |" in out
    assert "| /cz | 30 | n/a | n/a | 60.0 | n/a | n/a |" in out


def test_prior_only_labels_and_mixed_paid_buckets_are_shown():
    def ga4(rows_sm, rows_lp):
        return {"errors": [], "totals": {"sessions": 1, "engagedSessions": 1, "engagementRate": 1,
                                         "averageSessionDuration": 1, "bounceRate": 1},
                "source_medium": rows_sm, "landing": rows_lp, "events": {}, "events_paid": {},
                "source_medium_truncated": False, "landing_truncated": False}
    cur = ga4([{"source_medium": "other / referral", "sessions": 100.0, "engaged": 50.0,
                "paid": True, "paid_sessions": 10.0}],
              [{"page": "/cz", "sessions": 30.0, "engaged": 20.0, "engagement_rate": 60.0,
                "avg_duration": 50.0}])
    prior = ga4([{"source_medium": "facebook / cpc", "sessions": 40.0, "engaged": 10.0,
                  "paid": True, "paid_sessions": 40.0}],
                [{"page": "/cz/magazin", "sessions": 20.0, "engaged": 10.0,
                  "engagement_rate": 40.0, "avg_duration": 40.0}])
    empty = {"days_found": [], "days_missing": []}
    out = d.render({"window": {"start": "a", "end": "b"}, "prior_window": {"start": "c", "end": "d"},
                    "woo": None, "woo_prior": None, "clarity": empty, "clarity_prior": empty,
                    "generated_at": "x", "notes": [], "status": {}, "limits": [],
                    "ga4": cur, "ga4_prior": prior})
    assert "| other / referral | 100 | n/a |" not in out  # prior known -> 0, not n/a
    assert "| other / referral | 100 | 0 | +100 |" in out
    assert "mixed (10 paid)" in out
    assert "| facebook / cpc | 0 | 40 | -40 (-100%) |" in out
    assert "| /cz/magazin | 0 | 20 | -20 (-100%) |" in out


def test_prior_leader_below_current_top_ten_and_engaged_comparison():
    def row(label, sessions, engaged):
        return {"source_medium": label, "sessions": sessions, "engaged": engaged,
                "paid": False, "paid_sessions": 0.0}

    def ga4(rows_sm):
        return {"errors": [], "totals": {"sessions": 1, "engagedSessions": 1, "engagementRate": 1,
                                         "averageSessionDuration": 1, "bounceRate": 1},
                "source_medium": rows_sm, "landing": [], "events": {}, "events_paid": {},
                "source_medium_truncated": False, "landing_truncated": False}
    # Current: ten bigger sources, "old / leader" fell to 11th with 5 sessions (2 engaged).
    cur_rows = [row(f"s{i} / organic", 100.0 - i, 50.0) for i in range(10)]
    cur_rows.append(row("old / leader", 5.0, 2.0))
    prior = ga4([row("old / leader", 200.0, 120.0), row("s0 / organic", 90.0, 30.0)])
    empty = {"days_found": [], "days_missing": []}
    out = d.render({"window": {"start": "a", "end": "b"}, "prior_window": {"start": "c", "end": "d"},
                    "woo": None, "woo_prior": None, "clarity": empty, "clarity_prior": empty,
                    "generated_at": "x", "notes": [], "status": {}, "limits": [],
                    "ga4": ga4(cur_rows), "ga4_prior": prior})
    # Real current value (not zero) for the label that dropped out of the top ten.
    assert "| old / leader | 5 | 200 | -195 (-98%) | 2 | 120 | -118 (-98%) |" in out
    # Engaged gets its own previous/change columns for a displayed label.
    assert "| s0 / organic | 100 | 90 | +10 (+11%) | 50 | 30 | +20 (+67%) |" in out


def _funnel_report(ga4, ga4_prior):
    return {"window": {"start": "2026-10-06", "end": "2026-10-06"},
            "prior_window": {"start": "2026-10-05", "end": "2026-10-05"},
            "generated_at": "x", "notes": [], "status": {}, "limits": [],
            "ga4": ga4, "ga4_prior": ga4_prior, "woo": None, "woo_prior": None,
            "clarity": {"days_found": [], "days_missing": []}, "clarity_prior": {}}


def test_paid_funnel_shown_when_current_paid_empty_but_prior_had_paid():
    ev = {"view_item": {"users": 10.0}}
    report = _funnel_report(
        {"totals": None, "events": ev, "events_paid": {}},
        {"events_paid": {"add_to_cart": {"count": 20.0, "users": 10.0}}})
    row = [ln for ln in d.render(report).splitlines() if ln.startswith("| add_to_cart |")][-1]
    assert "| 0 | 20 |" in row and "-20" in row
    # unavailable current query (None) still hides the table
    report["ga4"]["events_paid"] = None
    assert "Paid / Meta funnel" not in d.render(report)


def test_funnel_ratio_compared_with_prior_window():
    cur = {"view_item": {"users": 100.0}, "add_to_cart": {"users": 20.0}}
    prior = {"view_item": {"users": 100.0}, "add_to_cart": {"users": 40.0}}
    report = _funnel_report({"totals": None, "events": cur, "events_paid": None},
                            {"events": prior})
    row = [ln for ln in d.render(report).splitlines() if ln.startswith("| add_to_cart |")][0]
    assert "| 20.0 | 40.0 |" in row and "-20" in row


def _woo_report(w, wp):
    base = _funnel_report({"totals": None, "events": {}, "events_paid": None}, {})
    return {**base, "woo": w, "woo_prior": wp}


def test_revenue_currency_falls_back_to_prior_window_when_current_has_no_orders():
    empty, prior = d.summarize_orders([]), d.summarize_orders(
        [{"status": "completed", "total": "250", "currency": "CZK", "attribution": {}}])
    assert empty["currency"] is None and prior["currency"] == "CZK"
    out = d.render(_woo_report(empty, prior))
    assert "Paid revenue (CZK)" in out and "n/a)" not in out.split("Paid revenue")[1].split("\n")[0]
    # differing currencies are labelled and not compared
    eur = d.summarize_orders([{"status": "completed", "total": "5", "currency": "EUR", "attribution": {}}])
    out = d.render(_woo_report(eur, prior))
    assert "this: EUR, previous: CZK" in out and "currencies differ" in out
