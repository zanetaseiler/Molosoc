#!/usr/bin/env bash
#
# Verify ONE published client report that sits behind HTTP Basic Auth.
#
# The reports directory is password-protected on purpose, and stays that way.
# That makes an unauthenticated GET useless for verification: it returns 401
# whether the report is perfect, corrupt or absent. This script is the one
# place that knows how to look behind the realm, so the publishers do not each
# grow their own copy of it.
#
# INPUTS ARRIVE AS ENVIRONMENT VARIABLES, NEVER AS ARGUMENTS
#
# `curl -u user:pass` puts the password in the process's argv, where `ps` can
# read it and `set -x` will echo it. Nothing here ever passes a credential on a
# command line: the pair is written to a mode-600 curl config under RUNNER_TEMP
# and removed on exit, including on failure.
#
#   VERIFY_URL              the page to fetch                        (required)
#   VERIFY_MARKER           text the page must contain, case-insensitive
#   VERIFY_USER             Basic Auth user                          (required)
#   VERIFY_PASSWORD         Basic Auth password                      (required)
#   VERIFY_EXPECT_SHA256    if set, the bytes served must hash to this
#   VERIFY_LABEL            human name for messages; defaults to the URL
#
# EXIT CODES
#
#   0  the page is live, authentic and — where asked — byte-identical
#   1  it is not, and the reason is on stderr
#   2  this check is not configured, so nothing was verified
#
# 2 is deliberately separate from 1. A missing secret produces a 401 exactly
# like a wrong password does, and reporting that as "the server refused us"
# sends you to cPanel to debug a GitHub setting. The two failures look
# identical from the wire and must not read identically in the log.

set -uo pipefail

URL="${VERIFY_URL-}"
MARKER="${VERIFY_MARKER-}"
AUTH_USER="${VERIFY_USER-}"
AUTH_PASSWORD="${VERIFY_PASSWORD-}"
EXPECT_SHA="${VERIFY_EXPECT_SHA256-}"
LABEL="${VERIFY_LABEL:-${URL}}"

if [ -z "$URL" ]; then
  echo "::error::verify_published_report: VERIFY_URL is required" >&2
  exit 2
fi

# Not configured is not the same as not serving.
if [ -z "$AUTH_USER" ] || [ -z "$AUTH_PASSWORD" ]; then
  echo "::error::Basic Auth credentials for the report directory are not configured." >&2
  echo "  Set REPORT_BASIC_AUTH_USER and REPORT_BASIC_AUTH_PASSWORD in this" >&2
  echo "  repository's Actions secrets, matching the cPanel Directory Privacy" >&2
  echo "  user for public_html/Trafficdom.com/reports/molosoc." >&2
  echo "  Nothing was verified. This is a configuration gap, not a serving failure." >&2
  exit 2
fi

WORK="${RUNNER_TEMP:-${TMPDIR:-/tmp}}"
CURLRC="$(mktemp "${WORK%/}/curlrc.XXXXXX")"
BODY="$(mktemp "${WORK%/}/body.XXXXXX")"
trap 'rm -f "$CURLRC" "$BODY"' EXIT INT TERM

# umask before the write, so the file is never briefly world-readable.
( umask 077; printf 'user = "%s:%s"\n' "$AUTH_USER" "$AUTH_PASSWORD" > "$CURLRC" )

# -L follows redirects; --location-trusted is deliberately NOT used, so the
# credentials are never replayed to a different host if one is interposed.
code="$(curl --silent --show-error --location --max-time 30 \
             --config "$CURLRC" \
             --output "$BODY" --write-out '%{http_code}' \
             "$URL" 2>/dev/null || echo 000)"

bytes="$(wc -c < "$BODY" 2>/dev/null | tr -d ' ')"
bytes="${bytes:-0}"

if [ "$code" = "401" ]; then
  echo "::error::$LABEL — HTTP 401: the realm rejected these credentials." >&2
  echo "  The directory is password-protected by design, so this means the" >&2
  echo "  configured user or password does not match the .htpasswd entry." >&2
  echo "  Basic Auth stays enabled; the credentials are what need correcting." >&2
  exit 1
fi

if [ "$code" != "200" ]; then
  echo "::error::$LABEL — HTTP $code from $URL" >&2
  head -c 400 "$BODY" >&2 2>/dev/null || true
  echo >&2
  exit 1
fi

if [ -n "$MARKER" ] && ! grep -qi -- "$MARKER" "$BODY"; then
  echo "::error::$LABEL — HTTP 200, but the page is not this report." >&2
  echo "  Expected to find: $MARKER" >&2
  head -c 400 "$BODY" >&2 2>/dev/null || true
  echo >&2
  exit 1
fi

if [ -n "$EXPECT_SHA" ]; then
  got="$(sha256sum "$BODY" | cut -d' ' -f1)"
  if [ "$got" != "$EXPECT_SHA" ]; then
    echo "::error::$LABEL — the bytes served are not the bytes published." >&2
    echo "  expected sha256: $EXPECT_SHA" >&2
    echo "  served   sha256: $got" >&2
    echo "  The upload reported success, so something between the file on disk" >&2
    echo "  and the response has changed it." >&2
    exit 1
  fi
  echo "PASS $LABEL is live, authentic and byte-identical ($bytes bytes)"
  exit 0
fi

echo "PASS $LABEL is live and authentic ($bytes bytes)"
exit 0
