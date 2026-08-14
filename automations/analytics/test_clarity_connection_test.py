#!/usr/bin/env python3
"""
Offline tests for the Microsoft Clarity connection test.

No network and no real token. Two things matter most here and both are
asserted directly:

1. Exactly one API call per run. Clarity allows 10 per project per day, so a
   stray second request or a retry loop is a real defect, not a style issue.
2. The token never appears in output, errors, or the request URL.

Run with:  python3 -m pytest automations/analytics/
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analytics_common  # noqa: E402
import clarity_connection_test as cct  # noqa: E402


FAKE_TOKEN = "eyJhbGciOiJIUzI1NiJ9.fake-clarity-token-value.abcdef123456"

# Shaped like a real project-live-insights body: a list of metrics, each with
# an "information" array whose fields differ per metric.
SAMPLE_PAYLOAD = [
    {
        "metricName": "Traffic",
        "information": [{
            "totalSessionCount": "412",
            "totalBotSessionCount": "18",
            "distinctUserCount": "301",
            "pagesPerSessionPercentage": 1.87,
        }],
    },
    {
        "metricName": "EngagementTime",
        "information": [{
            "totalTime": "83000",
            "activeTime": "41000",
            "activeTimeSpent": "99",
        }],
    },
    {
        "metricName": "ScrollDepth",
        "information": [{"averageScrollDepth": 46.3}],
    },
    {
        "metricName": "RageClickCount",
        "information": [{
            "sessionsWithMetricPercentage": 2.4,
            "sessionsWithoutMetricPercentage": 97.6,
            "subTotal": "10",
        }],
    },
    {
        "metricName": "DeadClickCount",
        "information": [
            {"sessionsWithMetricPercentage": 5.1, "subTotal": "21"},
            {"sessionsWithMetricPercentage": 1.2, "subTotal": "5"},
        ],
    },
]


@pytest.fixture(autouse=True)
def isolate_secrets(monkeypatch):
    monkeypatch.delenv("CLARITY_API_TOKEN", raising=False)
    monkeypatch.delenv("CLARITY_NUM_DAYS", raising=False)
    analytics_common.reset_secrets()
    yield
    analytics_common.reset_secrets()


class FakeResponse:
    def __init__(self, payload=None, status_code=200, text=None):
        self._payload = payload
        self.status_code = status_code
        if text is not None:
            self.text = text
        else:
            import json as _json
            self.text = _json.dumps(payload) if payload is not None else ""

    def json(self):
        if self._payload is None:
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return self._payload


class FakeSession:
    """Records every request so tests can assert the call count and the fact
    that the token only ever travels in a header."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self.responses.pop(0)


# --------------------------------------------------------------------------
# Rate-limit discipline — the reason this file exists
# --------------------------------------------------------------------------

def test_exactly_one_api_call_per_successful_run():
    session = FakeSession([FakeResponse(SAMPLE_PAYLOAD)])

    result = cct.check_clarity(FAKE_TOKEN, 3, [], session=session)

    assert result["ok"] is True
    assert len(session.calls) == 1
    assert result["apiCallsMade"] == 1


def test_a_failed_call_is_not_retried():
    # Only one response is queued; a retry would raise IndexError from the stub.
    session = FakeSession([FakeResponse(status_code=500, text="upstream boom")])

    result = cct.check_clarity(FAKE_TOKEN, 3, [], session=session)

    assert result["ok"] is False
    assert len(session.calls) == 1


def test_rate_limit_response_is_reported_without_retrying():
    session = FakeSession([FakeResponse(status_code=429, text="too many requests")])

    result = cct.check_clarity(FAKE_TOKEN, 3, [], session=session)

    assert result["ok"] is False
    assert "429" in result["error"]
    assert str(cct.DAILY_CALL_BUDGET) in result["error"]
    assert len(session.calls) == 1


def test_bad_arguments_are_rejected_before_any_call_is_spent():
    # validate_request must fail locally — no session is even constructed.
    with pytest.raises(SystemExit) as exc:
        cct.validate_request(7, [])
    assert "1, 2, 3" in str(exc.value)

    with pytest.raises(SystemExit) as exc:
        cct.validate_request(3, ["PopularPages"])
    assert "PopularPages" in str(exc.value)

    with pytest.raises(SystemExit):
        cct.validate_request(3, ["OS", "Device", "Country", "Browser"])


def test_valid_arguments_pass_validation():
    assert cct.validate_request(1, []) is None
    assert cct.validate_request(3, ["OS", "Channel"]) is None


# --------------------------------------------------------------------------
# Token handling
# --------------------------------------------------------------------------

def test_token_is_sent_only_in_the_authorization_header():
    session = FakeSession([FakeResponse(SAMPLE_PAYLOAD)])

    cct.fetch_live_insights(session, FAKE_TOKEN, 3, ["OS"])

    call = session.calls[0]
    assert call["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert FAKE_TOKEN not in call["url"]
    assert FAKE_TOKEN not in str(call["params"])
    assert call["params"] == {"numOfDays": "3", "dimension1": "OS"}


def test_dimensions_are_numbered_in_order():
    session = FakeSession([FakeResponse(SAMPLE_PAYLOAD)])

    cct.fetch_live_insights(session, FAKE_TOKEN, 1, ["OS", "Device", "Country"])

    assert session.calls[0]["params"] == {
        "numOfDays": "1", "dimension1": "OS", "dimension2": "Device", "dimension3": "Country",
    }


def test_missing_token_exits_with_guidance():
    with pytest.raises(SystemExit) as exc:
        cct.load_api_token()
    assert "CLARITY_API_TOKEN" in str(exc.value)


def test_loading_the_token_registers_it_for_redaction(monkeypatch):
    monkeypatch.setenv("CLARITY_API_TOKEN", FAKE_TOKEN)

    assert cct.load_api_token() == FAKE_TOKEN
    # Anything quoting the token afterwards is scrubbed.
    assert FAKE_TOKEN not in analytics_common.redact(f"failed with token {FAKE_TOKEN}")


def test_an_api_error_echoing_the_token_is_redacted(monkeypatch):
    monkeypatch.setenv("CLARITY_API_TOKEN", FAKE_TOKEN)
    cct.load_api_token()
    session = FakeSession([
        FakeResponse(status_code=400, text=f"bad request for Bearer {FAKE_TOKEN}"),
    ])

    result = cct.check_clarity(FAKE_TOKEN, 3, [], session=session)

    assert result["ok"] is False
    assert FAKE_TOKEN not in result["error"]
    assert "[REDACTED]" in result["error"]


def test_token_never_reaches_stdout(monkeypatch, capsys):
    monkeypatch.setenv("CLARITY_API_TOKEN", FAKE_TOKEN)
    monkeypatch.setattr(cct, "check_clarity", lambda *a, **k: {
        "ok": True, "numDays": 3, "dimensions": [], "apiCallsMade": 1,
        "metrics": cct.summarise_insights(SAMPLE_PAYLOAD),
    })

    assert cct.main([]) == 0
    out = capsys.readouterr().out
    assert FAKE_TOKEN not in out
    assert "Bearer" not in out.replace("(bearer, never printed)", "")


# --------------------------------------------------------------------------
# Response parsing
# --------------------------------------------------------------------------

def test_summarise_reads_whatever_metrics_came_back():
    metrics = cct.summarise_insights(SAMPLE_PAYLOAD)

    assert [m["name"] for m in metrics] == [
        "Traffic", "EngagementTime", "ScrollDepth", "RageClickCount", "DeadClickCount",
    ]
    assert metrics[0]["sample"]["totalSessionCount"] == "412"
    assert metrics[0]["rowCount"] == 1
    assert metrics[4]["rowCount"] == 2


def test_summarise_handles_a_wrapped_response_object():
    metrics = cct.summarise_insights({"result": SAMPLE_PAYLOAD})
    assert [m["name"] for m in metrics] == [
        "Traffic", "EngagementTime", "ScrollDepth", "RageClickCount", "DeadClickCount",
    ]


def test_summarise_handles_a_metric_with_no_information_rows():
    metrics = cct.summarise_insights([{"metricName": "Traffic"}])
    assert metrics[0]["rowCount"] == 0
    assert metrics[0]["sample"] == {}


def test_summarise_rejects_a_shape_it_cannot_read():
    with pytest.raises(RuntimeError) as exc:
        cct.summarise_insights("not a list")
    assert "Unexpected Clarity response shape" in str(exc.value)


def test_empty_project_is_a_pass_not_a_failure():
    session = FakeSession([FakeResponse([])])

    result = cct.check_clarity(FAKE_TOKEN, 3, [], session=session)

    assert result["ok"] is True
    assert result["metrics"] == []


def test_empty_body_is_explained_rather_than_surfaced_as_a_decode_error():
    session = FakeSession([FakeResponse(status_code=200, text="")])

    result = cct.check_clarity(FAKE_TOKEN, 3, ["OS"], session=session)

    assert result["ok"] is False
    assert "empty body" in result["error"]
    assert "dimension" in result["error"]


@pytest.mark.parametrize(
    "status,expected",
    [(401, "401 Unauthorized"), (403, "403 Forbidden")],
)
def test_auth_failures_are_named_clearly(status, expected):
    session = FakeSession([FakeResponse(status_code=status, text="denied")])

    result = cct.check_clarity(FAKE_TOKEN, 3, [], session=session)

    assert result["ok"] is False
    assert expected in result["error"]


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def test_output_shows_metrics_and_the_call_budget(capsys):
    cct.print_clarity_result({
        "ok": True, "numDays": 3, "dimensions": ["OS"], "apiCallsMade": 1,
        "metrics": cct.summarise_insights(SAMPLE_PAYLOAD),
    })

    out = capsys.readouterr().out
    assert "PASS" in out
    assert "Traffic" in out
    assert "totalSessionCount=412" in out
    assert f"1 of {cct.DAILY_CALL_BUDGET}/project/day" in out


def test_output_distinguishes_an_empty_project_from_a_failure(capsys):
    cct.print_clarity_result({
        "ok": True, "numDays": 3, "dimensions": [], "apiCallsMade": 1, "metrics": [],
    })

    out = capsys.readouterr().out
    assert "PASS" in out
    assert "no metrics returned" in out


def test_long_field_values_are_truncated():
    line = cct.format_sample({"url": "https://molosoc.com/" + "x" * 200})
    assert len(line) < 120
    assert line.endswith("...")


def test_main_returns_nonzero_when_clarity_fails(monkeypatch):
    monkeypatch.setenv("CLARITY_API_TOKEN", FAKE_TOKEN)
    monkeypatch.setattr(cct, "check_clarity", lambda *a, **k: {
        "ok": False, "numDays": 3, "dimensions": [], "apiCallsMade": 1,
        "error": "PermissionError: 401 Unauthorized",
    })

    assert cct.main([]) == 1


def test_defaults_match_the_documented_api_limits():
    args = cct.parse_args([])
    assert args.num_days == cct.DEFAULT_NUM_DAYS
    assert args.dimension == []
    assert cct.DEFAULT_NUM_DAYS in cct.ALLOWED_NUM_DAYS
    assert cct.DAILY_CALL_BUDGET == 10
