#!/usr/bin/env python3
"""
Shared helpers for the read-only Meta (Facebook + Instagram) connection test.

Same approach as automations/analytics/analytics_common.py — redact secrets
before anything reaches stdout — kept as its own copy rather than a shared
import so automations/social has no dependency on automations/analytics.
"""

import re

# Credential shapes that should never reach stdout.
_REDACT_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r'"(access_token|token|client_secret|app_secret)"\s*:\s*"[^"]*"', re.I),
    re.compile(r"access_token=[^&\s\"']+"),
]

# Literal secret values registered at runtime — catches a token echoed back
# inside a Graph API error body, which pattern matching alone would miss.
_REGISTERED_SECRETS = []

MIN_REGISTERABLE_SECRET_LENGTH = 8


def register_secret(value):
    """Register a literal secret to scrub from every later redact() call."""
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


def mask_token(token):
    """First 6 / last 4 chars only — enough to tell two tokens apart in logs,
    never enough to reconstruct or reuse one."""
    if not token:
        return "<missing>"
    text = str(token)
    if len(text) <= 12:
        return "*" * len(text)
    return f"{text[:6]}...{text[-4:]}"
