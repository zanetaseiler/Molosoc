#!/usr/bin/env python3
"""Offline tests for daily_funnel_report (no network, credentials or bucket)."""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import daily_funnel_report as d  # noqa: E402
from storage import InMemoryStore, facts_key  # noqa: E402

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
        {"entity_type": "site", "metric": "clarity_pages_per_session", "value": pages},
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
