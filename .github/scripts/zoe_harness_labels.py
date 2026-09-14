#!/usr/bin/env python3
"""
Shared label-lifecycle contract and GitHub helpers for the Zoe-derived
Claude/Santiago harness label cleanup layer.

Comments preserve history. Labels represent current actionable state only.
This module is the single place that decides which labels must never
survive on a closed Issue/PR, so the event-driven cleanup workflow and the
periodic reconciler fallback cannot drift from each other.
"""
import subprocess
import urllib.parse

TRANSIENT_LABELS = frozenset({
    "READY_FOR_CLAUDE_CLOUD",
    "READY_FOR_SANTIAGO",
})

# Retired/forbidden: must never be written by active transport, and must be
# removed on sight from a closed item. `controller:*` is a prefix, not a
# fixed name, so it is matched separately below.
RETIRED_LABELS = frozenset({
    "CHANGES_REQUESTED",
    "SANTIAGO_REVIEWING",
    "WORK_IN_PROGRESS",
    "SANTIAGO_STALLED",
    "CLAUDE_DISPATCHED",
    "CLAUDE_WORKING",
    "CLAUDE_STALLED",
    "NEEDS_ZANETA",
})

RETIRED_LABEL_PREFIXES = ("controller:",)

# Durable labels are never touched by this cleanup layer. They are listed
# here only so tests can assert they are excluded from is_removable().
DURABLE_LABELS = frozenset({
    "VERIFIED",
})


def is_removable(label_name):
    """True if a label must never remain on a closed Issue/PR."""
    if label_name in TRANSIENT_LABELS or label_name in RETIRED_LABELS:
        return True
    return any(label_name.startswith(prefix) for prefix in RETIRED_LABEL_PREFIXES)


def is_durable(label_name):
    return label_name in DURABLE_LABELS


class HarnessLabelError(RuntimeError):
    pass


def gh(argv):
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise HarnessLabelError(f"GitHub command failed ({result.returncode}): {result.stderr.strip()}")
    return result.stdout


def fetch_state_and_labels(repo, number):
    """Read-only. Returns (state, [label names]) for an Issue or PR number.

    Uses the /issues/{number} endpoint, which GitHub also exposes for pull
    requests, so callers never need to branch on issue-vs-PR to read state.
    """
    raw = gh([
        "gh", "api", f"repos/{repo}/issues/{number}",
        "--jq", "{state: .state, labels: [.labels[].name]}",
    ])
    import json
    data = json.loads(raw or "{}")
    return data.get("state", ""), list(data.get("labels", []))


def remove_label(repo, number, label_name):
    """Idempotent, removal-only. Returns True if a label was actually removed,
    False if it was already absent (treated as success, not an error)."""
    encoded = urllib.parse.quote(label_name, safe="")
    result = subprocess.run(
        ["gh", "api", "--method", "DELETE", f"repos/{repo}/issues/{number}/labels/{encoded}"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode == 0:
        return True
    stderr = result.stderr or ""
    if "404" in stderr or "Not Found" in stderr:
        return False
    raise HarnessLabelError(f"failed to remove label '{label_name}' from #{number}: {stderr.strip()}")
