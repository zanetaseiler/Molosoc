#!/usr/bin/env python3
"""
Periodic, idempotent, removal-only fallback reconciler for stray transient
or retired harness labels on closed Issues/PRs.

This exists purely for eventual consistency when the event-driven
harness-label-close-cleanup workflow missed an item (workflow outage, an
item closed by some other means, a run that failed mid-way). It only ever
removes labels; it never adds a label, comments, reopens an item, requeues
Claude, or wakes Codex. It never touches an item that is currently open:
the search itself is scoped to closed items, and each candidate's state is
re-checked immediately before the removal call as defense in depth against
a reopen racing the reconciler.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from zoe_harness_labels import (  # noqa: E402
    RETIRED_LABEL_PREFIXES,
    RETIRED_LABELS,
    TRANSIENT_LABELS,
    fetch_state_and_labels,
    gh,
    remove_label,
)

MAX_ITEMS_PER_LABEL = 300
PAGE_SIZE = 100


def repo_label_names(repo):
    raw = gh(["gh", "api", f"repos/{repo}/labels", "--paginate", "--jq", ".[].name"])
    return [line for line in raw.splitlines() if line]


def removable_label_names_in_repo(repo):
    """Only reconcile labels that actually exist in the repo today, so a
    fixed constant list never drives an unbounded number of search calls."""
    names = repo_label_names(repo)
    return sorted({
        name for name in names
        if name in TRANSIENT_LABELS
        or name in RETIRED_LABELS
        or any(name.startswith(prefix) for prefix in RETIRED_LABEL_PREFIXES)
    })


def closed_items_with_label(repo, label_name):
    query = f'repo:{repo} state:closed label:"{label_name}"'
    numbers = []
    page = 1
    while len(numbers) < MAX_ITEMS_PER_LABEL:
        raw = gh([
            "gh", "api", "--method", "GET", "search/issues",
            "-f", f"q={query}",
            "-f", f"per_page={PAGE_SIZE}",
            "-f", f"page={page}",
            "--jq", "[.items[].number]",
        ])
        batch = json.loads(raw or "[]")
        if not batch:
            break
        numbers.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        page += 1
    return numbers[:MAX_ITEMS_PER_LABEL]


def reconcile(repo):
    removed_total = 0
    for label_name in removable_label_names_in_repo(repo):
        for number in closed_items_with_label(repo, label_name):
            state, _ = fetch_state_and_labels(repo, number)
            if state != "closed":
                print(f"#{number} is now '{state or 'unknown'}'; skipping (never touch open items).")
                continue
            if remove_label(repo, number, label_name):
                removed_total += 1
                print(f"Removed '{label_name}' from closed #{number}.")
            else:
                print(f"'{label_name}' was already absent from #{number}; no-op.")
    print(f"Reconciler removed {removed_total} stray label(s).")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args(argv)
    return reconcile(args.repo)


if __name__ == "__main__":
    raise SystemExit(main())
