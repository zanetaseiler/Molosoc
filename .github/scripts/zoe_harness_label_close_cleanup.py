#!/usr/bin/env python3
"""
Event-driven, idempotent, removal-only label cleanup for one closed Issue/PR.

Fired by harness-label-close-cleanup.yml on `issues: closed` / `pull_request:
closed`. It only ever removes transient (READY_FOR_CLAUDE_CLOUD,
READY_FOR_SANTIAGO) or retired/forbidden labels, and only from an item that
is closed right now. It never adds a label, posts a comment, reopens an
item, requeues Claude, or wakes Codex. Durable labels (VERIFIED) and any
other MOLOSOC label are left untouched.

Defense in depth: state is re-checked immediately before every removal
call, rather than trusted from the triggering event payload or from a
single fetch at the start, since the item could be reopened at any point
while multiple labels are being removed.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from zoe_harness_labels import fetch_state_and_labels, is_removable, remove_label  # noqa: E402


def cleanup(repo, kind, number):
    state, current_labels = fetch_state_and_labels(repo, number)
    if state != "closed":
        print(f"{kind} #{number} is not closed (state={state or 'unknown'}); no-op.")
        return 0

    to_remove = [name for name in current_labels if is_removable(name)]
    if not to_remove:
        print(f"{kind} #{number} carries no transient/retired labels; no-op.")
        return 0

    for name in to_remove:
        state, _ = fetch_state_and_labels(repo, number)
        if state != "closed":
            print(f"{kind} #{number} is now '{state or 'unknown'}'; stopping remaining removals (never touch open items).")
            return 0
        if remove_label(repo, number, name):
            print(f"Removed '{name}' from closed {kind} #{number}.")
        else:
            print(f"'{name}' was already absent from {kind} #{number}; no-op.")

    return 0


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--issue", type=int)
    group.add_argument("--pr", type=int)
    args = parser.parse_args(argv)

    kind = "issue" if args.issue is not None else "pr"
    number = args.issue if args.issue is not None else args.pr
    return cleanup(args.repo, kind, number)


if __name__ == "__main__":
    raise SystemExit(main())
