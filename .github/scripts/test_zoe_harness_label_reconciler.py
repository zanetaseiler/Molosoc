#!/usr/bin/env python3
"""
Offline tests for the periodic label reconciler.

No network. The properties that matter most:

1. Only labels that actually exist in the repo are ever searched for, so a
   fixed constant list never drives an unbounded number of search calls.
2. An item that has been reopened since the search ran is skipped, never
   written to (defense in depth against a reconciler/reopen race).
3. Reconciling never invents an add/comment/reopen/requeue/wake call —
   there is no such function in this module to call in the first place.

Run with:  python3 -m pytest .github/scripts/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import zoe_harness_label_reconciler as reconciler_mod  # noqa: E402


def test_removable_label_names_in_repo_filters_to_known_set(monkeypatch):
    monkeypatch.setattr(
        reconciler_mod, "repo_label_names",
        lambda repo: ["bug", "READY_FOR_SANTIAGO", "controller:foo", "VERIFIED", "WORK_IN_PROGRESS"],
    )

    names = reconciler_mod.removable_label_names_in_repo("owner/repo")

    assert names == ["READY_FOR_SANTIAGO", "WORK_IN_PROGRESS", "controller:foo"]


def test_reconcile_skips_item_reopened_since_search(monkeypatch):
    monkeypatch.setattr(reconciler_mod, "removable_label_names_in_repo", lambda repo: ["READY_FOR_SANTIAGO"])
    monkeypatch.setattr(reconciler_mod, "closed_items_with_label", lambda repo, name: [42])
    monkeypatch.setattr(reconciler_mod, "fetch_state_and_labels", lambda repo, number: ("open", ["READY_FOR_SANTIAGO"]))

    removed = []
    monkeypatch.setattr(reconciler_mod, "remove_label", lambda repo, number, name: removed.append((number, name)) or True)

    result = reconciler_mod.reconcile("owner/repo")

    assert result == 0
    assert removed == []


def test_reconcile_removes_from_still_closed_items(monkeypatch):
    monkeypatch.setattr(reconciler_mod, "removable_label_names_in_repo", lambda repo: ["READY_FOR_SANTIAGO", "controller:stale"])
    monkeypatch.setattr(
        reconciler_mod, "closed_items_with_label",
        lambda repo, name: [1] if name == "READY_FOR_SANTIAGO" else [2],
    )
    monkeypatch.setattr(reconciler_mod, "fetch_state_and_labels", lambda repo, number: ("closed", []))

    removed = []
    monkeypatch.setattr(reconciler_mod, "remove_label", lambda repo, number, name: removed.append((number, name)) or True)

    result = reconciler_mod.reconcile("owner/repo")

    assert result == 0
    assert sorted(removed) == [(1, "READY_FOR_SANTIAGO"), (2, "controller:stale")]


def test_reconcile_treats_already_absent_label_as_noop(monkeypatch):
    monkeypatch.setattr(reconciler_mod, "removable_label_names_in_repo", lambda repo: ["READY_FOR_SANTIAGO"])
    monkeypatch.setattr(reconciler_mod, "closed_items_with_label", lambda repo, name: [5])
    monkeypatch.setattr(reconciler_mod, "fetch_state_and_labels", lambda repo, number: ("closed", []))
    monkeypatch.setattr(reconciler_mod, "remove_label", lambda repo, number, name: False)

    result = reconciler_mod.reconcile("owner/repo")

    assert result == 0


def test_closed_items_with_label_paginates_until_short_page(monkeypatch):
    pages = {
        1: [1] * reconciler_mod.PAGE_SIZE,
        2: [2, 3],
    }
    calls = []

    def fake_gh(argv):
        page = int(next(a for a in argv if a.startswith("page=")).split("=", 1)[1])
        calls.append(page)
        import json
        return json.dumps(pages.get(page, []))

    monkeypatch.setattr(reconciler_mod, "gh", fake_gh)

    numbers = reconciler_mod.closed_items_with_label("owner/repo", "READY_FOR_SANTIAGO")

    assert calls == [1, 2]
    assert numbers == pages[1] + pages[2]


def test_closed_items_with_label_forces_get_method(monkeypatch):
    """`-f` params otherwise make `gh api` default to POST, which 404s
    against the read-only search/issues endpoint; --method GET must be
    explicit."""
    captured = []

    def fake_gh(argv):
        captured.append(argv)
        import json
        return json.dumps([])

    monkeypatch.setattr(reconciler_mod, "gh", fake_gh)

    reconciler_mod.closed_items_with_label("owner/repo", "READY_FOR_SANTIAGO")

    assert len(captured) == 1
    argv = captured[0]
    method_index = argv.index("--method")
    assert argv[method_index + 1] == "GET"
    assert argv.index("search/issues") > method_index
