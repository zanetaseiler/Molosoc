#!/usr/bin/env python3
"""Offline tests for order_window (no network or credentials)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import order_window as ow  # noqa: E402

PII = ["Jana Novakova", "jana@example.com", "+420123456789", "Hlavni 1", "203.0.113.9",
       "Mozilla/5.0 SECRETUA", "SECRET-TXN-ID", "private customer note"]

RAW = {
    "id": 1234, "status": "processing", "currency": "CZK", "total": "799.00",
    "discount_total": "0.00", "shipping_total": "79.00", "total_tax": "0.00",
    "date_created_gmt": "2026-10-04T10:00:00", "date_paid_gmt": "2026-10-04T10:05:00",
    "date_completed_gmt": None, "payment_method": "stripe",
    "payment_method_title": "Card", "transaction_id": "SECRET-TXN-ID",
    "customer_id": 77, "customer_ip_address": "203.0.113.9",
    "customer_note": "private customer note",
    "billing": {"first_name": "Jana", "last_name": "Novakova", "email": "jana@example.com",
                "phone": "+420123456789", "address_1": "Hlavni 1"},
    "shipping": {"first_name": "Jana", "address_1": "Hlavni 1"},
    "line_items": [{"product_id": 5, "name": "Navlek", "quantity": 1, "total": "720.00",
                    "meta_data": [{"key": "x", "value": "Jana Novakova"}]}],
    "shipping_lines": [{"method_id": "flat_rate", "method_title": "Zasilkovna",
                        "total": "79.00"}],
    "coupon_lines": [{"code": "WELCOME10"}],
    "meta_data": [
        {"key": "_wc_order_attribution_source_type", "value": "utm"},
        {"key": "_wc_order_attribution_utm_source", "value": "fb"},
        {"key": "_wc_order_attribution_utm_medium", "value": "paid"},
        {"key": "_wc_order_attribution_referrer", "value": "https://m.facebook.com/l/?u=abc"},
        {"key": "_wc_order_attribution_session_entry",
         "value": "https://molosoc.com/cz/lp/?utm_source=fb&email=jana@example.com&fbclid=Z"},
        {"key": "_wc_order_attribution_user_agent", "value": "Mozilla/5.0 SECRETUA"},
        {"key": "_billing_email", "value": "jana@example.com"},
    ],
}


def test_window_bounds_inclusive_and_limits():
    assert ow.window_bounds("2026-10-03", "2026-10-05") == (
        "2026-10-03T00:00:00", "2026-10-06T00:00:00")
    with pytest.raises(ValueError):
        ow.window_bounds("2026-10-05", "2026-10-03")
    with pytest.raises(ValueError):
        ow.window_bounds("2026-10-01", "2026-10-15")
    ow.window_bounds("2026-10-01", "2026-10-14")


def test_sanitized_output_contains_no_pii():
    out = ow.sanitize_order(RAW)
    text = json.dumps(out, ensure_ascii=False)
    for secret in PII:
        assert secret not in text
    assert out["has_transaction_id"] is True
    assert out["coupons"] == ["WELCOME10"]
    assert out["shipping_lines"][0]["method_title"] == "Zasilkovna"
    assert out["line_items"][0] == {"product_id": 5, "name": "Navlek", "quantity": 1,
                                    "total": "720.00"}
    assert set(out) == {
        "id", "status", "created_gmt", "paid_gmt", "completed_gmt", "currency", "total",
        "discount_total", "shipping_total", "total_tax", "payment_method",
        "payment_method_title", "has_transaction_id", "line_items", "shipping_lines",
        "coupons", "attribution"}


def test_attribution_allowlist_and_url_reduction():
    attr = ow.sanitize_order(RAW)["attribution"]
    assert attr["source_type"] == "utm" and attr["utm_medium"] == "paid"
    assert "user_agent" not in attr
    assert attr["referrer"] == "m.facebook.com"
    assert attr["session_entry"] == "molosoc.com?utm_source=fb [fbclid present]"


def test_fetch_orders_paginates_and_only_gets():
    calls = []

    class Fake:
        def get(self, path, params):
            calls.append((path, params["page"]))
            return [{"id": i} for i in range(ow.PER_PAGE)] if params["page"] == 1 else [{"id": 999}]

    assert len(ow.fetch_orders(Fake(), "2026-10-01T00:00:00", "2026-10-02T00:00:00")) == ow.PER_PAGE + 1
    assert calls == [("/orders", 1), ("/orders", 2)]


def test_http_error_does_not_leak_body(monkeypatch):
    import io
    import urllib.error

    def boom(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url, 401, "x", {}, io.BytesIO(b"secret body"))

    monkeypatch.setattr(ow._OPENER, "open", boom)
    with pytest.raises(RuntimeError) as exc:
        ow.Client("https://x.test", "ck", "cs").get("/orders", {})
    assert "401" in str(exc.value) and "secret body" not in str(exc.value)
    assert "ck" not in str(exc.value)


def test_clean_url_strips_userinfo():
    out = ow.clean_url("https://name:tok3n@molosoc.com:8443/p?utm_source=fb")
    assert out == "molosoc.com?utm_source=fb"
    assert "name" not in out and "tok3n" not in out and "@" not in out


def test_cross_origin_redirect_is_refused_without_sending_credentials():
    import http.server
    import threading

    seen = []

    class Target(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"[]")

        def log_message(self, *a):
            pass

    target = http.server.HTTPServer(("127.0.0.1", 0), Target)

    class Redirector(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{target.server_port}/x")
            self.end_headers()

        def log_message(self, *a):
            pass

    redirector = http.server.HTTPServer(("127.0.0.1", 0), Redirector)
    for srv in (target, redirector):
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        client = ow.Client(f"http://127.0.0.1:{redirector.server_port}", "ck", "cs",
                           allow_loopback_http=True)
        with pytest.raises(RuntimeError) as exc:
            client.get("/orders", {})
        assert "302" in str(exc.value)
        assert seen == []
    finally:
        for srv in (target, redirector):
            srv.shutdown()


def test_clean_url_redacts_visitor_controlled_values():
    out = ow.clean_url("https://molosoc.com/reset/jana@example.com?utm_campaign=jana@example.com&utm_source=fb")
    assert "jana" not in out and "@" not in out
    assert out == "molosoc.com?utm_source=fb&utm_campaign=%5Bredacted%5D"
    attrs = ow.attribution([{"key": "_wc_order_attribution_utm_term", "value": "jana@example.com"}])
    assert attrs["utm_term"] == "[redacted]"


def test_name_shaped_values_are_redacted_not_echoed():
    out = ow.clean_url("https://molosoc.com/customers/jana-novakova?utm_campaign=Jana Novakova&utm_medium=paid")
    assert "jana" not in out.lower() and "novakova" not in out.lower()
    assert out == "molosoc.com?utm_medium=paid&utm_campaign=%5Bredacted%5D"
    attrs = ow.attribution([{"key": "_wc_order_attribution_utm_campaign", "value": "Jana Novakova"}])
    assert attrs["utm_campaign"] == "[redacted]"
    assert ow.clean_url("/customers/jana-novakova") == "[redacted]"


def test_fetch_orders_lower_bound_includes_window_start():
    seen = []

    class C:
        def get(self, path, params):
            seen.append(params["after"])
            return []

    ow.fetch_orders(C(), "2026-10-01T00:00:00", "2026-10-02T00:00:00")
    assert seen == ["2026-09-30T23:59:59"]


def test_every_attribution_field_is_validated():
    def meta(**kw):
        return [{"key": f"_wc_order_attribution_{k}", "value": v} for k, v in kw.items()]

    bad = ow.attribution(meta(
        source_type="jana@example.com", device_type="Jana Novakova",
        session_pages="jana@example.com", session_count="Jana",
        session_start_time="Jana Novakova"))
    assert set(bad.values()) == {ow.REDACTED}
    good = ow.attribution(meta(
        source_type="organic", device_type="Mobile", session_pages="3",
        session_count="2", session_start_time="2026-10-01 12:30:00"))
    assert good == {"source_type": "organic", "device_type": "Mobile", "session_pages": "3",
                    "session_count": "2", "session_start_time": "2026-10-01 12:30:00"}


def test_malformed_url_is_redacted_not_raised():
    assert ow.clean_url("https://[") == ow.REDACTED
    assert ow.attribution([{"key": "_wc_order_attribution_referrer",
                            "value": "https://["}]) == {"referrer": ow.REDACTED}


def test_non_string_url_metadata_is_redacted():
    for bad in ({"email": "jana@example.com"}, ["jana@example.com"], 42, True):
        assert ow.clean_url(bad) == ow.REDACTED
    attrs = ow.attribution([{"key": "_wc_order_attribution_referrer",
                             "value": {"email": "jana@example.com"}}])
    assert "jana" not in json.dumps(attrs)


def test_unapproved_hostnames_are_redacted():
    for url in ("https://jana-novakova.example/", "http://203.0.113.9/", "http://[2001:db8::1]/"):
        out = ow.clean_url(url)
        assert out == ow.REDACTED and "jana" not in out and "203" not in out
    assert ow.clean_url("https://l.facebook.com/x?utm_source=fb") == "l.facebook.com?utm_source=fb"
    assert ow.clean_url("https://evilmolosoc.com/") == ow.REDACTED


def test_only_enumerated_hostnames_are_emitted():
    for url in ("https://jana-novakova.molosoc.com/", "https://secret.wordpress.com/",
                "https://a.l.facebook.com/"):
        assert ow.clean_url(url) == ow.REDACTED
    assert ow.clean_url("https://www.molosoc.com/x") == "www.molosoc.com"


def test_plaintext_api_endpoints_are_rejected():
    for site in ("http://molosoc.com", "http://127.0.0.1:8000", "ftp://molosoc.com", "molosoc.com"):
        with pytest.raises(ValueError):
            ow.Client(site, "ck", "cs")
    ow.Client("https://molosoc.com", "ck", "cs")
    ow.Client("http://127.0.0.1:8000", "ck", "cs", allow_loopback_http=True)
    with pytest.raises(ValueError):
        ow.Client("http://molosoc.com", "ck", "cs", allow_loopback_http=True)


def test_window_with_exactly_page_cap_is_accepted():
    cap = ow.MAX_PAGES * ow.PER_PAGE

    class C:
        def get(self, path, params):
            if params["page"] <= ow.MAX_PAGES:
                return [{"id": i} for i in range(ow.PER_PAGE)]
            return []

    assert len(ow.fetch_orders(C(), "2026-10-01T00:00:00", "2026-10-02T00:00:00")) == cap

    class Over(C):
        def get(self, path, params):
            return [{"id": 1}] if params["page"] > ow.MAX_PAGES else super().get(path, params)

    with pytest.raises(RuntimeError):
        ow.fetch_orders(Over(), "2026-10-01T00:00:00", "2026-10-02T00:00:00")


def meta_entry(value, key="session_entry"):
    return [{"key": f"_wc_order_attribution_{key}", "value": value}]


def test_landing_page_is_host_and_path_only():
    attr = ow.attribution(meta_entry(
        "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/"
        "?utm_source=fb&fbclid=SECRETCLICK&email=jana@example.com#frag-jana"))
    assert attr["landing_page"] == "molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/"
    text = json.dumps(attr)
    for bad in ("SECRETCLICK", "jana", "frag", "?", "#"):
        assert bad not in attr["landing_page"] and "SECRETCLICK" not in text
    assert attr["session_entry"] == "molosoc.com?utm_source=fb [fbclid present]"


def test_landing_page_redacts_unapproved_path_segments_and_hosts():
    out = ow.clean_landing("https://molosoc.com/cz/reset/jana@example.com/hydratacni-navlek-na-nohy")
    assert out == "molosoc.com/cz/[redacted]/[redacted]/hydratacni-navlek-na-nohy/"
    assert "jana" not in out
    assert ow.clean_landing("https://jana-novakova.example/cz/") == "[redacted]/cz/"
    assert ow.clean_landing("https://name:tok3n@molosoc.com:8443/cz/") == "molosoc.com/cz/"
    assert ow.clean_landing("https://molosoc.com") == "molosoc.com/"
    long = "https://molosoc.com/" + "/".join(["cz"] * 10)
    assert ow.clean_landing(long).count("cz") == ow.MAX_PATH_SEGMENTS


def test_landing_page_missing_empty_and_malformed():
    assert "landing_page" not in ow.attribution([])
    assert "landing_page" not in ow.attribution(meta_entry("x", key="utm_source"))
    assert ow.attribution(meta_entry(""))["landing_page"] == ""
    assert ow.attribution(meta_entry(None))["landing_page"] is None
    for bad in ("https://[", "/cz/jana-novakova", {"email": "jana@example.com"}, ["a"], 42):
        assert ow.attribution(meta_entry(bad))["landing_page"] == ow.REDACTED


def test_campaign_and_content_numeric_and_free_text_redacted():
    def meta(**kw):
        return [{"key": f"_wc_order_attribution_{k}", "value": v} for k, v in kw.items()]

    # numeric shape is visitor-controlled and can be a phone number/customer id
    num = ow.attribution(meta(utm_campaign="420123456789", utm_content=" 987654321 "))
    assert num == {"utm_campaign": ow.REDACTED, "utm_content": ow.REDACTED}
    bad = ow.attribution(meta(utm_campaign="Jana Novakova", utm_content="jana@example.com"))
    assert set(bad.values()) == {ow.REDACTED}
    assert ow.attribution(meta(utm_source="12345678"))["utm_source"] == ow.REDACTED
    assert ow.attribution(meta(utm_campaign=None)) == {"utm_campaign": None}


def test_arbitrary_metadata_never_leaks_with_landing_fields():
    raw = dict(RAW, meta_data=RAW["meta_data"] + [
        {"key": "_wc_order_attribution_landing_secret", "value": "jana@example.com"},
        {"key": "_wc_order_attribution_session_entry_extra", "value": "jana@example.com"},
        {"key": "_wc_order_attribution_utm_campaign", "value": "120210000000001"},
        {"key": "_wc_order_attribution_utm_content", "value": "ad-jana@example.com"},
        {"key": "custom_landing", "value": "https://molosoc.com/jana"}])
    out = ow.sanitize_order(raw)
    text = json.dumps(out, ensure_ascii=False)
    for secret in PII + ["custom_landing", "landing_secret", "extra"]:
        assert secret not in text
    assert out["attribution"]["landing_page"] == "molosoc.com/cz/lp/"
    assert out["attribution"]["utm_campaign"] == ow.REDACTED
    assert out["attribution"]["utm_content"] == ow.REDACTED


def test_landing_page_keeps_all_existing_site_routes():
    for path in ("/cz/kurici-oko/jak-odstranit/", "/cz/kurici-oko/na-chodidle/",
                 "/ingrown-toenails/treatment/", "/cracked-heels/cracked-heels-cream/",
                 "/hardened-skin-calluses/callus-remover/", "/cz/popraskane-paty/",
                 "/dry-skin-feet/vs-cracked-heels/", "/cz/zasady-dopravy/",
                 "/cz/magazin/", "/cz/kosik/", "/cz/pokladna/"):
        assert ow.clean_landing("https://molosoc.com" + path) == "molosoc.com" + path
    assert ow.clean_landing("https://molosoc.com/cz/kurici-oko/jana@example.com/") == \
        "molosoc.com/cz/kurici-oko/[redacted]/"
