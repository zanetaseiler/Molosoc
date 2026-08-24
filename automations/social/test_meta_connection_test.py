#!/usr/bin/env python3
"""
Offline tests for the Meta (Facebook + Instagram) connection test.

No network and no real token. What matters most and is asserted directly:

1. Every request is a GET — never /media, /photos, /videos or /video_reels,
   the endpoints that would actually create content.
2. The access token and app secret never appear in printed output.
3. A language whose secrets aren't set is reported as SKIP, not FAIL.
4. The capability matrix correctly reflects scopes + page tasks + IG pairing,
   including the "unknown" case when /debug_token wasn't available.

Run with:  python3 -m pytest automations/social/
"""

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import meta_common  # noqa: E402
import meta_connection_test as mct  # noqa: E402


FAKE_TOKEN_CZ = "EAABfake-cz-page-token-0123456789abcdef"
FAKE_TOKEN_EN = "EAABfake-en-page-token-0123456789abcdef"
FAKE_APP_SECRET = "fakeappsecret0123456789abcdef"


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch):
    for var in (
        "META_FB_PAGE_ID_CZ", "META_ACCESS_TOKEN_CZ", "META_IG_ACCOUNT_ID_CZ",
        "META_APP_ID_CZ", "META_APP_SECRET_CZ",
        "META_FB_PAGE_ID_EN", "META_ACCESS_TOKEN_EN", "META_IG_ACCOUNT_ID_EN",
        "META_APP_ID_EN", "META_APP_SECRET_EN",
        "META_GRAPH_API_VERSION",
    ):
        monkeypatch.delenv(var, raising=False)
    meta_common.reset_secrets()
    yield
    meta_common.reset_secrets()


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        import json as _json
        self.text = _json.dumps(payload)

    def json(self):
        return self._payload


def make_fake_get(routes):
    """routes: dict of node-name substring -> payload (or callable(params)->payload).
    Records every call for assertions."""
    calls = []

    def fake_get(url, params):
        calls.append((url, dict(params)))
        for key, value in routes.items():
            if key in url:
                payload = value(params) if callable(value) else value
                return FakeResponse(payload)
        raise AssertionError(f"unexpected request to {url}")

    return fake_get, calls


PAGE_PAYLOAD = {
    "id": "1000000000001",
    "name": "MOLOSOC EN",
    "tasks": ["MANAGE", "CREATE_CONTENT", "MODERATE", "ANALYZE", "ADVERTISE"],
    "instagram_business_account": {
        "id": "17800000000001",
        "username": "molosoc_",
        "media_count": 3,
        "profile_picture_url": "https://example.com/pic.jpg",
    },
}

DEBUG_TOKEN_PAYLOAD_FULL_SCOPES = {
    "data": {
        "app_id": "999",
        "type": "PAGE",
        "is_valid": True,
        "expires_at": 0,
        "scopes": [
            "pages_show_list", "pages_read_engagement", "pages_manage_posts",
            "instagram_basic", "instagram_content_publish", "business_management",
        ],
    }
}


# --------------------------------------------------------------------------
# Read-only guarantee
# --------------------------------------------------------------------------

def test_every_request_is_a_get_to_a_read_endpoint(monkeypatch):
    fake_get, calls = make_fake_get({
        "/me": {"id": "1000000000001", "name": "MOLOSOC EN"},
        f"/{PAGE_PAYLOAD['id']}": PAGE_PAYLOAD,
        "/debug_token": DEBUG_TOKEN_PAYLOAD_FULL_SCOPES,
    })
    monkeypatch.setattr(mct, "_http_get", fake_get)

    mct.check_language(
        "en", PAGE_PAYLOAD["id"], FAKE_TOKEN_EN,
        expected_ig_id=None, app_id="999", app_secret=FAKE_APP_SECRET,
    )

    write_endpoints = ("/media", "/photos", "/videos", "/video_reels", "/feed")
    for url, _params in calls:
        for endpoint in write_endpoints:
            assert endpoint not in url, f"unexpected write-shaped call: {url}"
    assert len(calls) == 3  # /me, /{page}, /debug_token — nothing else


# --------------------------------------------------------------------------
# Credential hygiene
# --------------------------------------------------------------------------

def test_token_never_appears_in_printed_output(monkeypatch):
    fake_get, _calls = make_fake_get({
        "/me": {"id": "1000000000001", "name": "MOLOSOC EN"},
        f"/{PAGE_PAYLOAD['id']}": PAGE_PAYLOAD,
        "/debug_token": DEBUG_TOKEN_PAYLOAD_FULL_SCOPES,
    })
    monkeypatch.setattr(mct, "_http_get", fake_get)

    result = mct.check_language(
        "en", PAGE_PAYLOAD["id"], FAKE_TOKEN_EN,
        expected_ig_id=None, app_id="999", app_secret=FAKE_APP_SECRET,
    )

    buf = io.StringIO()
    with redirect_stdout(buf):
        mct.print_result(result)
    output = buf.getvalue()

    assert FAKE_TOKEN_EN not in output
    assert FAKE_APP_SECRET not in output


def test_error_message_with_token_in_body_is_redacted(monkeypatch):
    def fake_get(url, params):
        if "/me" in url:
            # Simulate a Graph API error that echoes the query string back,
            # the way some upstream error bodies do.
            return FakeResponse(
                {"error": {"message": f"bad request to {url}?access_token={FAKE_TOKEN_EN}", "code": 190}},
                status_code=400,
            )
        raise AssertionError("should not reach further calls after /me fails")

    monkeypatch.setattr(mct, "_http_get", fake_get)
    result = mct.check_language("en", "123", FAKE_TOKEN_EN)

    assert result["ok"] is False
    joined = " ".join(result["errors"])
    assert FAKE_TOKEN_EN not in joined


# --------------------------------------------------------------------------
# SKIP vs FAIL for unconfigured languages
# --------------------------------------------------------------------------

def test_unconfigured_language_is_skip_not_fail(monkeypatch, capsys):
    exit_code = mct.main(["--lang", "cz"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "SKIP" in out


def test_unconfigured_language_with_require_flag_fails(monkeypatch, capsys):
    exit_code = mct.main(["--lang", "cz", "--require"])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "SKIP" in out


# --------------------------------------------------------------------------
# Pairing verification
# --------------------------------------------------------------------------

def test_ig_pairing_mismatch_fails():
    fake_get, _calls = make_fake_get({
        "/me": {"id": "1000000000001", "name": "MOLOSOC EN"},
        f"/{PAGE_PAYLOAD['id']}": PAGE_PAYLOAD,
    })

    import types
    original = mct._http_get
    mct._http_get = fake_get
    try:
        result = mct.check_language(
            "en", PAGE_PAYLOAD["id"], FAKE_TOKEN_EN,
            expected_ig_id="99999999999999",  # doesn't match PAGE_PAYLOAD's IG id
        )
    finally:
        mct._http_get = original

    assert result["ok"] is False
    assert any("pairing mismatch" in e for e in result["errors"])


def test_ig_pairing_match_passes(monkeypatch):
    fake_get, _calls = make_fake_get({
        "/me": {"id": "1000000000001", "name": "MOLOSOC EN"},
        f"/{PAGE_PAYLOAD['id']}": PAGE_PAYLOAD,
    })
    monkeypatch.setattr(mct, "_http_get", fake_get)

    result = mct.check_language(
        "en", PAGE_PAYLOAD["id"], FAKE_TOKEN_EN,
        expected_ig_id=PAGE_PAYLOAD["instagram_business_account"]["id"],
    )

    assert result["ok"] is True


def test_no_linked_instagram_account_warns(monkeypatch):
    page_no_ig = {**PAGE_PAYLOAD, "instagram_business_account": None}
    fake_get, _calls = make_fake_get({
        "/me": {"id": "1000000000001", "name": "MOLOSOC EN"},
        f"/{page_no_ig['id']}": page_no_ig,
    })
    monkeypatch.setattr(mct, "_http_get", fake_get)

    result = mct.check_language("en", page_no_ig["id"], FAKE_TOKEN_EN)

    assert result["ok"] is True  # no expectation set, so no failure — just a warning
    assert any("no linked Instagram" in w for w in result["warnings"])


# --------------------------------------------------------------------------
# Capability matrix
# --------------------------------------------------------------------------

def test_capability_matrix_all_true_with_full_scopes():
    caps = mct.capability_matrix(
        scopes=list(DEBUG_TOKEN_PAYLOAD_FULL_SCOPES["data"]["scopes"]),
        page_tasks=["CREATE_CONTENT", "MANAGE"],
        ig_paired=True,
    )
    assert caps == {
        "facebook_image_post": True,
        "facebook_reels": True,
        "instagram_image_post": True,
        "instagram_reels": True,
    }


def test_capability_matrix_missing_ig_scope():
    caps = mct.capability_matrix(
        scopes=["pages_show_list", "pages_read_engagement", "pages_manage_posts", "instagram_basic"],
        page_tasks=["CREATE_CONTENT"],
        ig_paired=True,
    )
    assert caps["facebook_image_post"] is True
    assert caps["facebook_reels"] is True
    assert caps["instagram_image_post"] is False
    assert caps["instagram_reels"] is False


def test_capability_matrix_unknown_without_scopes():
    caps = mct.capability_matrix(scopes=None, page_tasks=["CREATE_CONTENT"], ig_paired=True)
    assert caps["facebook_image_post"] is True  # proxy: page task present
    assert caps["instagram_image_post"] is True  # proxy: pairing present
    # But neither is a confirmed scope check — the report layer must call
    # this out as UNKNOWN rather than a hard guarantee. That distinction is
    # encoded by scopes=None triggering print_result's "needs
    # META_APP_ID_*/META_APP_SECRET_*" branch, not by the boolean value
    # itself.


def test_capability_matrix_false_without_page_task_or_pairing():
    caps = mct.capability_matrix(scopes=None, page_tasks=[], ig_paired=False)
    assert caps["facebook_image_post"] is None
    assert caps["instagram_image_post"] is None


def test_missing_scopes_lists_only_the_gaps():
    gaps = mct.missing_scopes(["pages_show_list", "pages_manage_posts"])
    assert "pages_read_engagement" in gaps
    assert "instagram_basic" in gaps
    assert "instagram_content_publish" in gaps
    assert "pages_manage_posts" not in gaps


def test_missing_scopes_none_when_introspection_unavailable():
    assert mct.missing_scopes(None) is None


# --------------------------------------------------------------------------
# Per-language app isolation — CZ and EN never share an app id/secret
# --------------------------------------------------------------------------

def test_load_language_config_reads_only_that_languages_suffix(monkeypatch):
    monkeypatch.setenv("META_FB_PAGE_ID_CZ", "670138019527343")
    monkeypatch.setenv("META_ACCESS_TOKEN_CZ", FAKE_TOKEN_CZ)
    monkeypatch.setenv("META_APP_ID_CZ", "1811329706700638")
    monkeypatch.setenv("META_APP_SECRET_CZ", "cz-secret")
    # EN deliberately left unset.

    cz_config = mct.load_language_config("cz")
    en_config = mct.load_language_config("en")

    assert cz_config == {
        "page_id": "670138019527343",
        "access_token": FAKE_TOKEN_CZ,
        "expected_ig_id": None,
        "app_id": "1811329706700638",
        "app_secret": "cz-secret",
    }
    assert en_config is None  # nothing set for EN at all -> SKIP, not a fallback to CZ's app


def test_debug_token_call_uses_each_languages_own_app_credentials(monkeypatch):
    """The /debug_token call for CZ must authorize with CZ's app id|secret,
    never EN's (or any hard-coded value) — this is the core of the
    per-language-app change: no shared META_APP_ID/META_APP_SECRET."""
    seen_auth_tokens = []

    def fake_get(url, params):
        if "/debug_token" in url:
            seen_auth_tokens.append(params.get("access_token"))
            return FakeResponse(DEBUG_TOKEN_PAYLOAD_FULL_SCOPES)
        if "/me" in url:
            return FakeResponse({"id": "1000000000001", "name": "MOLOSOC CZ"})
        if PAGE_PAYLOAD["id"] in url:
            return FakeResponse(PAGE_PAYLOAD)
        raise AssertionError(f"unexpected request to {url}")

    monkeypatch.setattr(mct, "_http_get", fake_get)

    mct.check_language(
        "cz", PAGE_PAYLOAD["id"], FAKE_TOKEN_CZ,
        app_id="1811329706700638", app_secret="cz-only-secret",
    )

    assert seen_auth_tokens == ["1811329706700638|cz-only-secret"]


def test_main_treats_cz_and_en_as_fully_independent(monkeypatch, capsys):
    """CZ configured with its own app id/secret, EN left completely unset.
    EN must SKIP cleanly and CZ's checks must never reference EN's secrets,
    proving there's no cross-language fallback or hard-coded default."""
    monkeypatch.setenv("META_FB_PAGE_ID_CZ", PAGE_PAYLOAD["id"])
    monkeypatch.setenv("META_ACCESS_TOKEN_CZ", FAKE_TOKEN_CZ)
    monkeypatch.setenv("META_APP_ID_CZ", "1811329706700638")
    monkeypatch.setenv("META_APP_SECRET_CZ", "cz-only-secret")

    fake_get, calls = make_fake_get({
        "/me": {"id": "1000000000001", "name": "MOLOSOC CZ"},
        f"/{PAGE_PAYLOAD['id']}": PAGE_PAYLOAD,
        "/debug_token": DEBUG_TOKEN_PAYLOAD_FULL_SCOPES,
    })
    monkeypatch.setattr(mct, "_http_get", fake_get)

    exit_code = mct.main(["--lang", "both"])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "SKIP" in out  # EN
    assert "PASS" in out  # CZ
    for _url, params in calls:
        assert params.get("access_token") != "cz-only-secret"  # never sent bare
    assert "cz-only-secret" not in out
