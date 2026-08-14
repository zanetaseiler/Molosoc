#!/usr/bin/env python3
"""
Offline tests for the GA4 / Search Console connection test.

Everything here runs against stubs — no network, no credentials. The point is
to cover the parts that are easy to get wrong and expensive to debug from a CI
log: credential loading and its failure modes, the redaction that keeps the
private key out of stdout, the date windows (including the Search Console
lag), and the response parsing for both APIs.

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import google_connection_test as gct  # noqa: E402


FAKE_KEY = {
    "type": "service_account",
    "project_id": "molosoc-analytics",
    "private_key_id": "abc123",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBg\n-----END PRIVATE KEY-----\n",
    "client_email": "molosoc-reader@molosoc-analytics.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}


@pytest.fixture(autouse=True)
def clear_credential_env(monkeypatch):
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)


# --------------------------------------------------------------------------
# Credential loading
# --------------------------------------------------------------------------

def test_loads_raw_json_from_env(monkeypatch):
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", json.dumps(FAKE_KEY))
    assert gct.load_service_account_info()["client_email"] == FAKE_KEY["client_email"]


def test_loads_base64_encoded_json_from_env(monkeypatch):
    import base64

    encoded = base64.b64encode(json.dumps(FAKE_KEY).encode()).decode()
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", encoded)
    assert gct.load_service_account_info()["project_id"] == "molosoc-analytics"


def test_loads_from_key_file(monkeypatch, tmp_path):
    key_file = tmp_path / "key.json"
    key_file.write_text(json.dumps(FAKE_KEY), encoding="utf-8")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(key_file))
    assert gct.load_service_account_info()["client_email"] == FAKE_KEY["client_email"]


def test_missing_credentials_exits_with_guidance():
    with pytest.raises(SystemExit) as exc:
        gct.load_service_account_info()
    assert "GOOGLE_SERVICE_ACCOUNT_JSON" in str(exc.value)


def test_incomplete_key_names_the_missing_fields(monkeypatch):
    partial = {k: v for k, v in FAKE_KEY.items() if k != "client_email"}
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", json.dumps(partial))
    with pytest.raises(SystemExit) as exc:
        gct.load_service_account_info()
    assert "client_email" in str(exc.value)


def test_malformed_json_error_never_echoes_the_payload(monkeypatch):
    # A truncated key: still contains real private key material, so the error
    # message must describe the failure without quoting any of it back.
    broken = json.dumps(FAKE_KEY)[:120]
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", broken)
    with pytest.raises(SystemExit) as exc:
        gct.load_service_account_info()
    message = str(exc.value)
    assert "PRIVATE KEY" not in message
    assert "MIIEvQIBADANBg" not in message
    assert "line" in message


# --------------------------------------------------------------------------
# Redaction / masking
# --------------------------------------------------------------------------

def test_redact_strips_pem_blocks():
    assert "MIIEvQIBADANBg" not in gct.redact(FAKE_KEY["private_key"])


def test_redact_strips_secret_json_fields():
    out = gct.redact(json.dumps(FAKE_KEY))
    assert "MIIEvQIBADANBg" not in out
    assert "abc123" not in out
    # Non-secret fields survive so errors stay debuggable.
    assert "molosoc-analytics" in out


def test_redact_strips_bearer_tokens():
    out = gct.redact("Authorization: Bearer ya29.a0AfB_ABCdef-123~xyz")
    assert "ya29" not in out


def test_mask_email_keeps_domain_hides_identity():
    assert gct.mask_email(FAKE_KEY["client_email"]) == "mo***@molosoc-analytics.iam.gserviceaccount.com"
    assert gct.mask_email("") == "<unknown>"


# --------------------------------------------------------------------------
# Date windows
# --------------------------------------------------------------------------

def test_ga4_window_is_seven_days_ending_yesterday():
    start, end = gct.date_window(7, end_offset_days=1)
    today = dt.date.today()
    assert end == (today - dt.timedelta(days=1)).isoformat()
    assert start == (today - dt.timedelta(days=7)).isoformat()


def test_search_console_window_accounts_for_reporting_lag():
    start, end = gct.date_window(7, end_offset_days=gct.GSC_LAG_DAYS)
    today = dt.date.today()
    assert end == (today - dt.timedelta(days=gct.GSC_LAG_DAYS)).isoformat()
    assert (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days == 6


# --------------------------------------------------------------------------
# GA4 parsing
# --------------------------------------------------------------------------

class _Value:
    def __init__(self, value):
        self.value = value


class _Header:
    def __init__(self, name):
        self.name = name


class _Row:
    def __init__(self, dimensions, metrics):
        self.dimension_values = [_Value(d) for d in dimensions]
        self.metric_values = [_Value(m) for m in metrics]


class _Response:
    def __init__(self, headers, rows, row_count=0):
        self.metric_headers = [_Header(h) for h in headers]
        self.rows = rows
        self.row_count = row_count


class FakeGa4Client:
    """Returns the totals report first, then the landing-page report, and
    records both requests so the test can assert what was asked for."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def run_report(self, request):
        self.requests.append(request)
        return self.responses.pop(0)


def test_run_ga4_checks_parses_totals_and_landing_pages():
    client = FakeGa4Client([
        _Response(
            ["activeUsers", "sessions", "screenPageViews"],
            [_Row([], ["128", "156", "402"])],
            row_count=1,
        ),
        _Response(
            ["sessions", "activeUsers"],
            [
                _Row(["/"], ["90", "72"]),
                _Row(["/cracked-heels"], ["41", "38"]),
            ],
        ),
    ])

    result = gct.run_ga4_checks(client, "521643495", "2026-08-07", "2026-08-13")

    assert result["users"] == 128
    assert result["sessions"] == 156
    assert result["views"] == 402
    assert result["landingPages"][0] == {"landingPage": "/", "sessions": 90, "activeUsers": 72}
    assert len(result["landingPages"]) == 2

    totals_request, landing_request = client.requests
    assert totals_request.property == "properties/521643495"
    assert [m.name for m in totals_request.metrics] == [
        "activeUsers", "sessions", "screenPageViews",
    ]
    assert [d.name for d in landing_request.dimensions] == ["landingPagePlusQueryString"]
    assert landing_request.limit == 5
    assert totals_request.date_ranges[0].start_date == "2026-08-07"


def test_run_ga4_checks_handles_a_property_with_no_data():
    client = FakeGa4Client([
        _Response(["activeUsers", "sessions", "screenPageViews"], []),
        _Response(["sessions", "activeUsers"], []),
    ])

    result = gct.run_ga4_checks(client, "521643495", "2026-08-07", "2026-08-13")

    assert result["users"] == 0
    assert result["landingPages"] == []


def test_check_ga4_reports_api_failure_instead_of_raising(monkeypatch):
    monkeypatch.setattr(gct, "build_credentials", lambda info, scopes: object())

    def explode(*_args, **_kwargs):
        raise RuntimeError("403 User does not have sufficient permissions")

    monkeypatch.setattr(gct, "run_ga4_checks", explode)

    result = gct.check_ga4(FAKE_KEY, "521643495", 7)

    assert result["ok"] is False
    assert "403" in result["error"]


# --------------------------------------------------------------------------
# Search Console parsing
# --------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeGscSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs.get("json")))
        return self.responses.pop(0)


def _gsc_session_with_data():
    return FakeGscSession([
        FakeResponse({"siteEntry": [
            {"siteUrl": "sc-domain:molosoc.com", "permissionLevel": "siteFullUser"},
        ]}),
        FakeResponse({"rows": [
            {"clicks": 34, "impressions": 1290, "ctr": 0.0264, "position": 18.4},
        ]}),
        FakeResponse({"rows": [
            {"keys": ["molosoc"], "clicks": 20, "impressions": 60, "ctr": 0.33, "position": 1.2},
        ]}),
        FakeResponse({"rows": [
            {"keys": ["https://molosoc.com/"], "clicks": 25, "impressions": 800,
             "ctr": 0.031, "position": 12.0},
        ]}),
    ])


def test_run_gsc_checks_parses_totals_queries_and_pages():
    session = _gsc_session_with_data()

    result = gct.run_gsc_checks(session, "sc-domain:molosoc.com", "2026-08-05", "2026-08-11")

    assert result["clicks"] == 34
    assert result["impressions"] == 1290
    assert result["ctr"] == pytest.approx(0.0264)
    assert result["position"] == pytest.approx(18.4)
    assert result["topQueries"][0]["query"] == "molosoc"
    assert result["topPages"][0]["page"] == "https://molosoc.com/"
    assert result["visiblePropertyCount"] == 1


def test_run_gsc_checks_url_encodes_the_sc_domain_property():
    session = _gsc_session_with_data()

    gct.run_gsc_checks(session, "sc-domain:molosoc.com", "2026-08-05", "2026-08-11")

    _, query_url, body = session.calls[1]
    assert "sc-domain%3Amolosoc.com" in query_url
    assert query_url.endswith("/searchAnalytics/query")
    assert body["startDate"] == "2026-08-05"
    assert body["endDate"] == "2026-08-11"
    # Read-only: the only calls made are the sites list and three queries.
    assert [call[0] for call in session.calls] == ["GET", "POST", "POST", "POST"]


def test_run_gsc_checks_requests_the_expected_dimensions():
    session = _gsc_session_with_data()

    gct.run_gsc_checks(session, "sc-domain:molosoc.com", "2026-08-05", "2026-08-11")

    bodies = [call[2] for call in session.calls[1:]]
    assert "dimensions" not in bodies[0]  # totals row
    assert bodies[1]["dimensions"] == ["query"]
    assert bodies[2]["dimensions"] == ["page"]
    assert all(body["rowLimit"] <= 5 for body in bodies)


def test_run_gsc_checks_handles_a_property_with_no_search_data():
    session = FakeGscSession([
        FakeResponse({"siteEntry": [{"siteUrl": "sc-domain:molosoc.com"}]}),
        FakeResponse({}),
        FakeResponse({}),
        FakeResponse({}),
    ])

    result = gct.run_gsc_checks(session, "sc-domain:molosoc.com", "2026-08-05", "2026-08-11")

    assert result["clicks"] == 0
    assert result["topQueries"] == []
    assert result["topPages"] == []


def test_run_gsc_checks_rejects_a_property_the_account_cannot_see():
    session = FakeGscSession([
        FakeResponse({"siteEntry": [{"siteUrl": "sc-domain:example.com"}]}),
    ])

    with pytest.raises(PermissionError) as exc:
        gct.run_gsc_checks(session, "sc-domain:molosoc.com", "2026-08-05", "2026-08-11")
    assert "sc-domain:molosoc.com" in str(exc.value)


def test_gsc_http_error_surfaces_the_api_message():
    session = FakeGscSession([
        FakeResponse({"error": {"message": "User does not have sufficient permission"}}, 403),
    ])

    with pytest.raises(RuntimeError) as exc:
        gct.run_gsc_checks(session, "sc-domain:molosoc.com", "2026-08-05", "2026-08-11")
    assert "403" in str(exc.value)
    assert "sufficient permission" in str(exc.value)


def test_check_search_console_reports_failure_instead_of_raising(monkeypatch):
    import google.auth.transport.requests as google_requests

    monkeypatch.setattr(gct, "build_credentials", lambda info, scopes: object())
    monkeypatch.setattr(
        google_requests,
        "AuthorizedSession",
        lambda creds: FakeGscSession([FakeResponse({"error": {"message": "nope"}}, 403)]),
    )

    result = gct.check_search_console(FAKE_KEY, "sc-domain:molosoc.com", 7)

    assert result["ok"] is False
    assert "403" in result["error"]


# --------------------------------------------------------------------------
# CLI wiring
# --------------------------------------------------------------------------

def test_defaults_point_at_the_molosoc_properties():
    args = gct.parse_args([])
    assert args.property_id == "521643495"
    assert args.site_url == "sc-domain:molosoc.com"
    assert args.days == 7


def test_env_vars_override_defaults(monkeypatch):
    monkeypatch.setenv("GA4_PROPERTY_ID", "999")
    monkeypatch.setenv("GSC_SITE_URL", "sc-domain:example.com")
    args = gct.parse_args([])
    assert args.property_id == "999"
    assert args.site_url == "sc-domain:example.com"


def test_main_returns_nonzero_when_an_integration_fails(monkeypatch, capsys):
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", json.dumps(FAKE_KEY))
    monkeypatch.setattr(gct, "check_ga4", lambda *a: {
        "ok": True, "propertyId": "521643495",
        "dateRange": {"start": "2026-08-07", "end": "2026-08-13"},
        "users": 1, "sessions": 1, "views": 1, "landingPages": [], "rowCount": 1,
    })
    monkeypatch.setattr(gct, "check_search_console", lambda *a: {
        "ok": False, "siteUrl": "sc-domain:molosoc.com", "error": "RuntimeError: HTTP 403",
    })

    assert gct.main([]) == 1
    out = capsys.readouterr().out
    assert "PASS" in out and "FAIL" in out
    # The masked identity is printed; the key material is not.
    assert "mo***@" in out
    assert "MIIEvQIBADANBg" not in out


def test_main_returns_zero_when_both_pass(monkeypatch):
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", json.dumps(FAKE_KEY))
    monkeypatch.setattr(gct, "check_ga4", lambda *a: {
        "ok": True, "propertyId": "521643495",
        "dateRange": {"start": "2026-08-07", "end": "2026-08-13"},
        "users": 0, "sessions": 0, "views": 0, "landingPages": [], "rowCount": 0,
    })
    monkeypatch.setattr(gct, "check_search_console", lambda *a: {
        "ok": True, "siteUrl": "sc-domain:molosoc.com",
        "dateRange": {"start": "2026-08-05", "end": "2026-08-11"},
        "visiblePropertyCount": 1, "clicks": 0, "impressions": 0, "ctr": 0.0,
        "position": 0.0, "topQueries": [], "topPages": [],
    })

    assert gct.main([]) == 0
