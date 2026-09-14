#!/usr/bin/env python3
"""
Offline tests for the event-driven closed-item label cleanup.

No network. Three properties matter most:

1. An open item is never touched (no-op, defense in depth against a race
   between the close event firing and this script running).
2. Only transient/retired labels are removed; durable and unrelated labels
   are left alone.
3. A label already absent from the item is a benign no-op, not a failure.

Run with:  python3 -m pytest .github/scripts/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zoe_harness_label_close_cleanup as cleanup_mod  # noqa: E402


def test_open_item_is_a_noop(monkeypatch):
    monkeypatch.setattr(
        cleanup_mod, "fetch_state_and_labels",
        lambda repo, number: ("open", ["READY_FOR_SANTIAGO"]),
    )
    removed = []
    monkeypatch.setattr(cleanup_mod, "remove_label", lambda repo, number, name: removed.append(name) or True)

    result = cleanup_mod.cleanup("owner/repo", "issue", 7)

    assert result == 0
    assert removed == []


def test_closed_item_removes_only_transient_and_retired_labels(monkeypatch):
    monkeypatch.setattr(
        cleanup_mod, "fetch_state_and_labels",
        lambda repo, number: (
            "closed",
            ["READY_FOR_SANTIAGO", "VERIFIED", "controller:stale", "bug"],
        ),
    )
    removed = []
    monkeypatch.setattr(cleanup_mod, "remove_label", lambda repo, number, name: removed.append(name) or True)

    result = cleanup_mod.cleanup("owner/repo", "pr", 9)

    assert result == 0
    assert sorted(removed) == ["READY_FOR_SANTIAGO", "controller:stale"]


def test_closed_item_with_nothing_to_remove_is_a_noop(monkeypatch):
    monkeypatch.setattr(
        cleanup_mod, "fetch_state_and_labels",
        lambda repo, number: ("closed", ["VERIFIED", "bug"]),
    )
    removed = []
    monkeypatch.setattr(cleanup_mod, "remove_label", lambda repo, number, name: removed.append(name) or True)

    result = cleanup_mod.cleanup("owner/repo", "issue", 3)

    assert result == 0
    assert removed == []


def test_already_absent_label_does_not_fail(monkeypatch):
    monkeypatch.setattr(
        cleanup_mod, "fetch_state_and_labels",
        lambda repo, number: ("closed", ["READY_FOR_CLAUDE_CLOUD"]),
    )
    monkeypatch.setattr(cleanup_mod, "remove_label", lambda repo, number, name: False)

    result = cleanup_mod.cleanup("owner/repo", "issue", 3)

    assert result == 0


def test_reopen_between_removals_stops_remaining_removals(monkeypatch):
    """Item is closed on the initial fetch but is reopened after the first
    label is removed; the second removable label must never be touched."""
    states = iter(["closed", "closed", "open"])
    monkeypatch.setattr(
        cleanup_mod, "fetch_state_and_labels",
        lambda repo, number: (next(states), ["READY_FOR_SANTIAGO", "controller:stale"]),
    )
    removed = []
    monkeypatch.setattr(cleanup_mod, "remove_label", lambda repo, number, name: removed.append(name) or True)

    result = cleanup_mod.cleanup("owner/repo", "pr", 11)

    assert result == 0
    assert removed == ["READY_FOR_SANTIAGO"]
