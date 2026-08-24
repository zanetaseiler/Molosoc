#!/usr/bin/env python3
"""
Molosoc Meta (Facebook + Instagram) connection test — read-only, per language.

CZ and EN are two entirely separate Meta apps — separate App ID, separate
App Secret, separate system-user token, separate Page — not one shared app
used for both. Every secret below is per-language; there is no shared
META_APP_ID/META_APP_SECRET/META_ACCESS_TOKEN fallback.

Proves, for each configured language (CZ / EN), that:
  1. the stored access token is valid and belongs to the expected identity;
  2. the Facebook Page it names is reachable and this token can act on it;
  3. that Page's linked Instagram professional account is the expected one
     (Page <-> Instagram pairing);
  4. the token's granted permissions (when that language's META_APP_ID_*/
     META_APP_SECRET_* are also set, via the /debug_token introspection
     endpoint) cover what Instagram image posts, Instagram Reels, Facebook
     image posts and Facebook Reels each require.

Nothing here writes. Every call is a GET against a read endpoint
(/me, /{page-id}, /me/accounts, /debug_token) — never /media, /photos,
/videos or /video_reels, which are the endpoints that actually create
content. A
"capability" in the report below means "the credentials and permissions this
would need are present", not "a post was made" — no post is ever made by
this script.

Credentials never reach stdout: tokens are registered with redact() the
moment they are read, and every access_token is sent as a query parameter
that mask_token() summarizes before printing, never the raw value.

Usage:
    export META_APP_ID_CZ='...'
    export META_APP_SECRET_CZ='...'
    export META_ACCESS_TOKEN_CZ='...'
    export META_FB_PAGE_ID_CZ='...'

    export META_APP_ID_EN='...'
    export META_APP_SECRET_EN='...'
    export META_ACCESS_TOKEN_EN='...'
    export META_FB_PAGE_ID_EN='...'

    # optional, cross-checks the Page's linked IG account against this id:
    export META_IG_ACCOUNT_ID_CZ='...'
    export META_IG_ACCOUNT_ID_EN='...'
    python3 automations/social/meta_connection_test.py

META_APP_ID_*/META_APP_SECRET_* are optional per language — without them,
/debug_token scope introspection for that language is skipped and its
capability checks fall back to the page-task/pairing proxy (reported as
UNKNOWN rather than YES/NO). A language whose token/page secrets are not set
at all is reported as SKIP, not FAIL — this script is meant to be run as
each language's Meta assets get connected, not only once both exist. Exit
code is non-zero only when a language that IS configured fails a check, or
when --require was passed for a language that turns out not to be
configured.
"""

import argparse
import os
import sys

from meta_common import describe_error, mask_token, redact, register_secret

DEFAULT_GRAPH_API_VERSION = "v21.0"
HTTP_TIMEOUT = 30

# What each publishing capability actually needs. Facebook Reels and Facebook
# image posts both go through pages_manage_posts (Reels is just a different
# upload endpoint, /video_reels vs /photos) plus the CREATE_CONTENT page task.
# Instagram image posts and Reels both go through the same two IG scopes plus
# a correctly paired professional account (Reels is media_type=REELS on the
# same /media endpoint).
REQUIRED_PAGE_SCOPES = ("pages_show_list", "pages_read_engagement", "pages_manage_posts")
REQUIRED_IG_SCOPES = ("instagram_basic", "instagram_content_publish")
RECOMMENDED_SCOPES = ("business_management", "pages_manage_metadata")

LANGUAGES = ("cz", "en")


def graph_api_base():
    version = os.environ.get("META_GRAPH_API_VERSION", DEFAULT_GRAPH_API_VERSION)
    return f"https://graph.facebook.com/{version}"


def _http_get(url, params):
    """Isolated so tests can monkeypatch this one function instead of the
    network. Real runs go through requests; nothing else in this module
    touches the network directly."""
    import requests

    return requests.get(url, params=params, timeout=HTTP_TIMEOUT)


def graph_get(node, access_token, **params):
    """A single read-only Graph API GET. Raises RuntimeError with a redacted,
    one-line message on any error envelope or transport failure."""
    url = f"{graph_api_base()}/{node}"
    query = dict(params)
    query["access_token"] = access_token

    try:
        response = _http_get(url, query)
    except Exception as exc:  # noqa: BLE001 — reported, not raised
        raise RuntimeError(f"request to {node} failed: {describe_error(exc)}") from exc

    try:
        body = response.json()
    except ValueError:
        raise RuntimeError(
            f"HTTP {response.status_code} from {node}: non-JSON response "
            f"({redact(response.text[:300])})"
        )

    if response.status_code >= 400 or "error" in body:
        err = body.get("error", {}) if isinstance(body, dict) else {}
        message = err.get("message", f"HTTP {response.status_code}")
        code = err.get("code")
        subcode = err.get("error_subcode")
        code_str = f"{code}/{subcode}" if subcode else str(code)
        raise RuntimeError(f"Graph API error on {node} (code {code_str}): {redact(message)}")

    return body


# --------------------------------------------------------------------------
# Per-check functions — each one GET, each read-only
# --------------------------------------------------------------------------

def check_identity(access_token):
    """GET /me — proves the token is valid and shows what it authenticates
    as. For a Page/System User token this is the Page or system user, not a
    personal profile."""
    return graph_get("me", access_token, fields="id,name")


def check_page(page_id, access_token):
    """GET /{page-id} — proves this token can read the Page by id, and pulls
    the linked Instagram professional account in the same call so pairing
    can be checked without a second round trip.

    Deliberately does NOT request `tasks` here: that field only exists on
    the Page-as-list-item shape returned by /me/accounts, not on the Page
    node itself — requesting it directly on /{page-id} fails with
    "(#100) Tried accessing nonexisting field (tasks)". See check_page_tasks
    below for where `tasks` actually comes from."""
    return graph_get(
        page_id,
        access_token,
        fields="id,name,instagram_business_account{id,username,media_count,profile_picture_url}",
    )


def check_page_tasks(access_token):
    """GET /me/accounts — the only place `tasks` (what this token can
    actually do on a Page — CREATE_CONTENT is the one that matters for
    posting) is exposed by the Graph API. Returns the raw list of Pages this
    token has access to; the caller matches the one it cares about by id."""
    body = graph_get("me/accounts", access_token, fields="id,name,tasks", limit=100)
    return body.get("data", [])


def check_debug_token(access_token, app_id, app_secret):
    """GET /debug_token — introspects the token itself: granted scopes,
    expiry, and what identity it resolves to. Uses an app access token
    (APP_ID|APP_SECRET) to authorize the introspection call; the token being
    inspected is only ever sent as input_token, never as the auth token."""
    app_access_token = f"{app_id}|{app_secret}"
    body = graph_get("debug_token", app_access_token, input_token=access_token)
    return body.get("data", {})


# --------------------------------------------------------------------------
# Capability matrix
# --------------------------------------------------------------------------

def capability_matrix(scopes, page_tasks, ig_paired):
    """Returns True/False/None (unknown) for each of the four publishing
    capabilities the task cares about. None means the scope list wasn't
    available (that language's META_APP_ID_*/META_APP_SECRET_* weren't set),
    so only the weaker proxy signals (page tasks, IG pairing) could be
    checked."""
    tasks = set(page_tasks or [])
    can_create_on_page = "CREATE_CONTENT" in tasks

    if scopes is None:
        return {
            "facebook_image_post": can_create_on_page or None,
            "facebook_reels": can_create_on_page or None,
            "instagram_image_post": (True if ig_paired else None),
            "instagram_reels": (True if ig_paired else None),
        }

    scopes = set(scopes)
    fb_ok = can_create_on_page and "pages_manage_posts" in scopes
    ig_ok = ig_paired and all(scope in scopes for scope in REQUIRED_IG_SCOPES)
    return {
        "facebook_image_post": fb_ok,
        "facebook_reels": fb_ok,
        "instagram_image_post": ig_ok,
        "instagram_reels": ig_ok,
    }


def missing_scopes(scopes):
    if scopes is None:
        return None
    scopes = set(scopes)
    return [s for s in (*REQUIRED_PAGE_SCOPES, *REQUIRED_IG_SCOPES) if s not in scopes]


# --------------------------------------------------------------------------
# Per-language check
# --------------------------------------------------------------------------

def check_language(lang, page_id, access_token, expected_ig_id=None, app_id=None, app_secret=None):
    register_secret(access_token)
    if app_secret:
        register_secret(app_secret)

    result = {"lang": lang, "ok": True, "errors": [], "warnings": []}

    try:
        identity = check_identity(access_token)
        result["identity"] = identity
    except RuntimeError as exc:
        result["ok"] = False
        result["errors"].append(f"token identity check failed: {exc}")
        return result

    try:
        page = check_page(page_id, access_token)
        result["page"] = page
    except RuntimeError as exc:
        result["ok"] = False
        result["errors"].append(f"page check failed: {exc}")
        return result

    page_tasks = []
    try:
        accounts = check_page_tasks(access_token)
        matched = next((a for a in accounts if str(a.get("id")) == str(page_id)), None)
        if matched is not None:
            page_tasks = matched.get("tasks", []) or []
        else:
            result["warnings"].append(
                f"Page {page_id} did not appear in this token's /me/accounts list "
                f"({len(accounts)} Page(s) visible) — cannot confirm page tasks "
                "(e.g. CREATE_CONTENT). The Page may not be assigned to this "
                "System User as an asset in Business Manager."
            )
    except RuntimeError as exc:
        result["warnings"].append(f"/me/accounts lookup failed: {exc}")
    result["page_tasks"] = page_tasks

    ig = page.get("instagram_business_account")
    result["ig"] = ig
    ig_paired = ig is not None
    if not ig_paired:
        result["warnings"].append(
            "this Page has no linked Instagram professional account — "
            "Instagram posting will not be possible until one is connected "
            "in Meta Business Suite."
        )

    if expected_ig_id and ig_paired and str(ig.get("id")) != str(expected_ig_id):
        result["ok"] = False
        result["errors"].append(
            f"Page's linked Instagram account is {ig.get('id')} "
            f"({ig.get('username')}), but META_IG_ACCOUNT_ID_{lang.upper()} "
            f"expects {expected_ig_id} — pairing mismatch."
        )
    elif expected_ig_id and not ig_paired:
        result["ok"] = False
        result["errors"].append(
            f"expected Instagram account {expected_ig_id} to be paired with "
            "this Page, but the Page has no linked Instagram account at all."
        )

    scopes = None
    if app_id and app_secret:
        try:
            debug = check_debug_token(access_token, app_id, app_secret)
            result["debug_token"] = debug
            if debug.get("is_valid") is False:
                result["ok"] = False
                result["errors"].append("token reports is_valid=false via /debug_token")
            scopes = debug.get("scopes")
        except RuntimeError as exc:
            result["warnings"].append(f"/debug_token introspection failed: {exc}")
    else:
        result["warnings"].append(
            f"META_APP_ID_{lang.upper()}/META_APP_SECRET_{lang.upper()} not set — "
            "skipping /debug_token scope introspection; capability checks below "
            "fall back to the Page's task list and Instagram pairing only."
        )

    result["missing_scopes"] = missing_scopes(scopes)
    result["capabilities"] = capability_matrix(scopes, page_tasks, ig_paired)

    if scopes is not None and result["missing_scopes"]:
        result["ok"] = False
        result["errors"].append(
            "token is missing required permission(s): " + ", ".join(result["missing_scopes"])
        )

    return result


# --------------------------------------------------------------------------
# Config loading
# --------------------------------------------------------------------------

def load_language_config(lang):
    """Returns a dict of this language's own secrets (page id, access token,
    expected IG id, app id, app secret) or None if NONE of them are set at
    all — i.e. this language hasn't been touched yet. Each language's app id
    and app secret are its own; there is no shared fallback."""
    suffix = lang.upper()
    page_id = os.environ.get(f"META_FB_PAGE_ID_{suffix}", "").strip()
    access_token = os.environ.get(f"META_ACCESS_TOKEN_{suffix}", "").strip()
    expected_ig_id = os.environ.get(f"META_IG_ACCOUNT_ID_{suffix}", "").strip() or None
    app_id = os.environ.get(f"META_APP_ID_{suffix}", "").strip() or None
    app_secret = os.environ.get(f"META_APP_SECRET_{suffix}", "").strip() or None

    if not any((page_id, access_token, expected_ig_id, app_id, app_secret)):
        return None
    return {
        "page_id": page_id,
        "access_token": access_token,
        "expected_ig_id": expected_ig_id,
        "app_id": app_id,
        "app_secret": app_secret,
    }


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def print_result(result):
    lang = result["lang"].upper()
    print(f"\n--- {lang} ---")

    if result.get("skipped"):
        print("SKIP  META_FB_PAGE_ID_{0}/META_ACCESS_TOKEN_{0} not set — nothing to test yet.".format(lang))
        return

    identity = result.get("identity")
    if identity:
        print(f"      token identity: {identity.get('name')} ({identity.get('id')})")

    page = result.get("page")
    if page:
        tasks = ", ".join(result.get("page_tasks") or []) or "(none confirmed — see WARN below)"
        print(f"      Facebook Page:  {page.get('name')} ({page.get('id')})")
        print(f"      Page tasks:     {tasks}")

    ig = result.get("ig")
    if ig:
        print(f"      Instagram:      @{ig.get('username')} ({ig.get('id')}) — {ig.get('media_count', '?')} media")
    elif page is not None:
        print("      Instagram:      not linked to this Page")

    debug = result.get("debug_token")
    if debug:
        expires = debug.get("expires_at", 0)
        expiry_note = "never expires" if not expires else f"expires_at={expires}"
        print(f"      token type:     {debug.get('type', '?')} ({expiry_note})")
        print(f"      granted scopes: {', '.join(debug.get('scopes', []) or []) or '(none)'}")

    caps = result.get("capabilities") or {}
    def fmt(v):
        if v is True:
            return "YES"
        if v is False:
            return "NO"
        return f"UNKNOWN (needs META_APP_ID_{lang}/META_APP_SECRET_{lang} to confirm)"

    print("      capability check:")
    print(f"        Facebook image posts:  {fmt(caps.get('facebook_image_post'))}")
    print(f"        Facebook Reels:        {fmt(caps.get('facebook_reels'))}")
    print(f"        Instagram image posts: {fmt(caps.get('instagram_image_post'))}")
    print(f"        Instagram Reels:       {fmt(caps.get('instagram_reels'))}")

    for warning in result.get("warnings", []):
        print(f"      WARN  {warning}")

    if result["ok"]:
        print("      PASS")
    else:
        print("      FAIL")
        for error in result.get("errors", []):
            print(f"        {error}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only Meta (Facebook + Instagram) connection test for Molosoc."
    )
    parser.add_argument(
        "--lang",
        choices=("cz", "en", "both"),
        default="both",
        help="which language's Meta assets to test (default: both)",
    )
    parser.add_argument(
        "--require",
        action="store_true",
        help="treat an unconfigured requested language as a failure instead of a SKIP",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    langs = LANGUAGES if args.lang == "both" else (args.lang,)

    print("Molosoc — Meta (Facebook + Instagram) read-only connection test")
    print(f"  Graph API version: {os.environ.get('META_GRAPH_API_VERSION', DEFAULT_GRAPH_API_VERSION)}")
    print("  CZ and EN each use their own Meta app (separate App ID/Secret) — no shared app.")

    all_ok = True
    for lang in langs:
        config = load_language_config(lang)
        if config is None:
            result = {"lang": lang, "skipped": True, "ok": not args.require}
            if args.require:
                all_ok = False
            print_result(result)
            continue

        if config["app_secret"]:
            register_secret(config["app_secret"])

        if not config["page_id"] or not config["access_token"]:
            suffix = lang.upper()
            missing = f"META_FB_PAGE_ID_{suffix}" if not config["page_id"] else f"META_ACCESS_TOKEN_{suffix}"
            print(f"\n--- {suffix} ---")
            print(f"FAIL  {missing} is not set.")
            all_ok = False
            continue

        result = check_language(
            lang,
            config["page_id"],
            config["access_token"],
            config["expected_ig_id"],
            config["app_id"],
            config["app_secret"],
        )
        print_result(result)
        if not result["ok"]:
            all_ok = False

    print()
    if all_ok:
        print("Overall: PASS")
        return 0
    print("Overall: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
