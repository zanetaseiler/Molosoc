#!/usr/bin/env python3
"""
Shared helpers for the read-only analytics connection tests.

Small on purpose: the pieces every source needs (secret redaction, number
coercion, date windows) live here so GA4, Search Console and Clarity all
behave the same way, especially around never printing a credential.
"""

import datetime as dt
import re

# Credential shapes that should never reach stdout, whatever the source.
_REDACT_PATTERNS = [
    # PEM blocks, with or without the \n escaping used inside JSON.
    re.compile(r"-----BEGIN[^-]*PRIVATE KEY-----.*?-----END[^-]*PRIVATE KEY-----", re.S),
    # Any JSON field whose name suggests a secret, e.g. "private_key": "...".
    re.compile(
        r'"(private_key|private_key_id|client_secret|refresh_token|access_token|token|api_?key)"'
        r'\s*:\s*"[^"]*"',
        re.I,
    ),
    # Bearer tokens in case an HTTP layer echoes a request header.
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
]

# Literal secret values registered at runtime. Pattern matching catches
# credentials in a recognisable shape; this catches the specific string we are
# actually holding, wherever it turns up — an API that echoes the token back in
# an error body, a requests exception that quotes the URL, a stack trace.
_REGISTERED_SECRETS = []

MIN_REGISTERABLE_SECRET_LENGTH = 8


def register_secret(value):
    """Register a literal secret to scrub from every later redact() call.

    Very short values are ignored: redacting a 3-character string would blank
    out unrelated substrings of ordinary output and make logs unreadable.
    """
    text = str(value or "").strip()
    if len(text) >= MIN_REGISTERABLE_SECRET_LENGTH and text not in _REGISTERED_SECRETS:
        _REGISTERED_SECRETS.append(text)


def reset_secrets():
    """Drop all registered secrets. Used by tests to isolate cases."""
    _REGISTERED_SECRETS.clear()


def redact(text):
    """Strip anything credential-shaped out of a string before it is printed."""
    out = str(text)
    for secret in _REGISTERED_SECRETS:
        out = out.replace(secret, "[REDACTED]")
    for pattern in _REDACT_PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out


def describe_error(exc):
    """A one-line, redacted description of an exception, safe to print."""
    return f"{type(exc).__name__}: {redact(exc)}"


def as_number(value):
    """Coerce an API's string-or-number metric into a real number.

    Values that are already numeric are returned untouched — int() on a float
    would silently truncate, turning Clarity's 1.87 pages/session into 1.
    Google's APIs hand back numbers as strings, so both paths are needed.
    """
    if isinstance(value, (int, float)):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0


def date_window(days, end_offset_days):
    """Inclusive [start, end] window of `days` days, ending `end_offset_days`
    before today, as YYYY-MM-DD strings."""
    end = dt.date.today() - dt.timedelta(days=end_offset_days)
    start = end - dt.timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()
