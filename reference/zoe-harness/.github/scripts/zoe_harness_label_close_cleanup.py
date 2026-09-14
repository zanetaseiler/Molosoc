#!/usr/bin/env python3
"""Close/merge harness label cleanup (Issue #167, Required behavior #4).

Run by `.github/workflows/harness-label-close-cleanup.yml` whenever an
Issue or PR closes (a PR's `closed` event fires identically whether or not
it was merged, so no merged/closed branching is needed -- Required
behavior #4's "merging a PR behaves equivalently for label cleanup").

This script only ever removes labels; it never adds one, reopens anything,
or posts a comment, so it cannot requeue Claude, wake Codex, or start a new
state transition. It is safe to run against an item that already carries
no transient/retired labels (returns an empty list; deletes nothing).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from zoe_harness_labels import labels_to_strip_on_close  # noqa: E402


class CleanupError(RuntimeError):
    pass


def current_labels(repo: str, kind: str, number: int) -> list[str]:
    subcommand = "issue" if kind == "issue" else "pr"
    result = subprocess.run(
        ["gh", subcommand, "view", str(number), "--repo", repo, "--json", "labels"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise CleanupError(f"could not read labels for {kind} #{number}: {result.stderr.strip()}")
    data = json.loads(result.stdout or "{}")
    return [entry.get("name", "") for entry in data.get("labels", [])]


def remove_label(repo: str, number: int, label: str) -> None:
    encoded = urllib.parse.quote(label, safe="")
    result = subprocess.run(
        ["gh", "api", "--method", "DELETE", f"repos/{repo}/issues/{number}/labels/{encoded}"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0 and "404" not in result.stderr:
        raise CleanupError(f"failed to remove label {label!r} from #{number}: {result.stderr.strip()}")


def cleanup(repo: str, kind: str, number: int) -> list[str]:
    labels = current_labels(repo, kind, number)
    to_strip = labels_to_strip_on_close(labels)
    for label in to_strip:
        remove_label(repo, number, label)
    return to_strip


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--kind", required=True, choices=["issue", "pr"])
    parser.add_argument("--number", required=True, type=int)
    args = parser.parse_args(argv)

    removed = cleanup(args.repo, args.kind, args.number)
    if removed:
        print(f"Removed transient/retired harness labels from #{args.number}: {', '.join(removed)}")
    else:
        print(f"#{args.number} already carries no transient/retired harness labels; nothing to remove.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
