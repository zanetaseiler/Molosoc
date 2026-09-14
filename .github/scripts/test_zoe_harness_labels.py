#!/usr/bin/env python3
"""
Offline tests for the shared harness label-lifecycle contract.

Run with:  python3 -m pytest .github/scripts/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zoe_harness_labels as zhl  # noqa: E402


def test_transient_labels_are_removable():
    assert zhl.is_removable("READY_FOR_CLAUDE_CLOUD")
    assert zhl.is_removable("READY_FOR_SANTIAGO")


def test_retired_labels_are_removable():
    for name in [
        "CHANGES_REQUESTED",
        "SANTIAGO_REVIEWING",
        "WORK_IN_PROGRESS",
        "SANTIAGO_STALLED",
        "CLAUDE_DISPATCHED",
        "CLAUDE_WORKING",
        "CLAUDE_STALLED",
        "NEEDS_ZANETA",
    ]:
        assert zhl.is_removable(name), name


def test_controller_prefix_labels_are_removable():
    assert zhl.is_removable("controller:READY_FOR_SANTIAGO")
    assert zhl.is_removable("controller:anything")


def test_durable_label_is_never_removable():
    assert zhl.is_durable("VERIFIED")
    assert not zhl.is_removable("VERIFIED")


def test_unrelated_labels_are_untouched():
    for name in ["bug", "enhancement", "molosoc:seo", "priority:high"]:
        assert not zhl.is_removable(name)
        assert not zhl.is_durable(name)


def test_remove_label_success(monkeypatch):
    calls = []

    class FakeResult:
        returncode = 0
        stderr = ""

    def fake_run(argv, capture_output, text, check):
        calls.append(argv)
        return FakeResult()

    monkeypatch.setattr(zhl.subprocess, "run", fake_run)
    removed = zhl.remove_label("owner/repo", 12, "READY_FOR_SANTIAGO")

    assert removed is True
    assert calls[0][:4] == ["gh", "api", "--method", "DELETE"]
    assert calls[0][-1] == "repos/owner/repo/issues/12/labels/READY_FOR_SANTIAGO"


def test_remove_label_already_absent_is_not_an_error(monkeypatch):
    class FakeResult:
        returncode = 1
        stderr = "HTTP 404: Not Found (https://api.github.com/...)"

    monkeypatch.setattr(zhl.subprocess, "run", lambda *a, **k: FakeResult())
    removed = zhl.remove_label("owner/repo", 12, "READY_FOR_SANTIAGO")

    assert removed is False


def test_remove_label_genuine_failure_raises(monkeypatch):
    class FakeResult:
        returncode = 1
        stderr = "HTTP 403: Forbidden"

    monkeypatch.setattr(zhl.subprocess, "run", lambda *a, **k: FakeResult())

    try:
        zhl.remove_label("owner/repo", 12, "READY_FOR_SANTIAGO")
        assert False, "expected HarnessLabelError"
    except zhl.HarnessLabelError:
        pass


def test_remove_label_encodes_colon_prefixed_names(monkeypatch):
    calls = []

    class FakeResult:
        returncode = 0
        stderr = ""

    def fake_run(argv, capture_output, text, check):
        calls.append(argv)
        return FakeResult()

    monkeypatch.setattr(zhl.subprocess, "run", fake_run)
    zhl.remove_label("owner/repo", 12, "controller:READY_FOR_SANTIAGO")

    assert calls[0][-1] == "repos/owner/repo/issues/12/labels/controller%3AREADY_FOR_SANTIAGO"
