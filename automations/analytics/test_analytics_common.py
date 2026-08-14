#!/usr/bin/env python3
"""
Offline tests for the helpers shared by all three connection tests.

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analytics_common as common  # noqa: E402


@pytest.fixture(autouse=True)
def isolate_secrets():
    common.reset_secrets()
    yield
    common.reset_secrets()


# --------------------------------------------------------------------------
# as_number
# --------------------------------------------------------------------------

def test_numeric_strings_become_numbers():
    assert common.as_number("128") == 128
    assert common.as_number("1.87") == pytest.approx(1.87)


def test_floats_are_not_truncated():
    # Regression: int() first turned Clarity's 1.87 pages/session into 1.
    assert common.as_number(1.87) == pytest.approx(1.87)
    assert common.as_number(46.3) == pytest.approx(46.3)
    assert common.as_number(0.0264) == pytest.approx(0.0264)


def test_integers_pass_through():
    assert common.as_number(42) == 42


def test_unparseable_values_fall_back_to_zero():
    assert common.as_number(None) == 0
    assert common.as_number("") == 0
    assert common.as_number("n/a") == 0


# --------------------------------------------------------------------------
# Redaction
# --------------------------------------------------------------------------

def test_registered_secret_is_scrubbed_anywhere_it_appears():
    common.register_secret("eyJhbGciOiJIUzI1NiJ9.super-secret-token.xyz")
    out = common.redact("request failed: eyJhbGciOiJIUzI1NiJ9.super-secret-token.xyz rejected")
    assert "super-secret-token" not in out
    assert "[REDACTED]" in out


def test_short_values_are_not_registered():
    # Redacting a 3-character string would blank out unrelated output.
    common.register_secret("abc")
    assert common.redact("abcdef") == "abcdef"


def test_blank_values_are_ignored():
    common.register_secret("")
    common.register_secret(None)
    assert common.redact("nothing to hide") == "nothing to hide"


def test_registering_the_same_secret_twice_is_harmless():
    common.register_secret("repeated-secret-value")
    common.register_secret("repeated-secret-value")
    assert "repeated-secret-value" not in common.redact("x repeated-secret-value y")


def test_pattern_redaction_still_applies_without_registration():
    assert "ya29" not in common.redact("Authorization: Bearer ya29.abc-123_x")
    assert "hunter2" not in common.redact('{"api_key": "hunter2"}')
    assert "hunter2" not in common.redact('{"token": "hunter2"}')


def test_reset_secrets_clears_registrations():
    common.register_secret("temporary-secret-value")
    common.reset_secrets()
    assert "temporary-secret-value" in common.redact("temporary-secret-value")


def test_describe_error_is_one_redacted_line():
    common.register_secret("leaky-token-value-123")
    described = common.describe_error(RuntimeError("failed with leaky-token-value-123"))
    assert described.startswith("RuntimeError: ")
    assert "leaky-token-value-123" not in described


# --------------------------------------------------------------------------
# date_window
# --------------------------------------------------------------------------

def test_window_is_inclusive_of_both_ends():
    start, end = common.date_window(7, end_offset_days=1)
    assert (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days == 6


def test_window_offset_shifts_the_end_date():
    _, end = common.date_window(7, end_offset_days=3)
    assert end == (dt.date.today() - dt.timedelta(days=3)).isoformat()


def test_single_day_window():
    start, end = common.date_window(1, end_offset_days=0)
    assert start == end == dt.date.today().isoformat()
