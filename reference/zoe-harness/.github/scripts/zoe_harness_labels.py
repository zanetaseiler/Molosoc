"""Authoritative GitHub label lifecycle classification (Issue #167).

`docs/HARNESS_GOLDEN_PATH.md`'s "Minimal visible states" section and
`AGENTS.md` already say, in prose, which harness labels are transient
transport, which are durable final state, and which are retired and must
never be written again. This module gives that classification a single,
pure, testable home instead of leaving it to be reimplemented (and
re-guessed) piecemeal by every workflow that needs it -- exactly the
"prefer a small, explicit helper... over duplicated cleanup lists" this
Issue asks for.

Like `zoe_controller_state.py`, this module makes no GitHub API calls and
decides nothing about *when* to act -- callers (currently
`zoe_harness_label_close_cleanup.py`) do that.

Classification, grounded in text already in this repository rather than
guessed:

  * **transient** -- the two non-durable entries in `docs/HARNESS_GOLDEN_PATH.md`'s
    "Minimal visible states": `READY_FOR_CLAUDE_CLOUD` (the live Claude
    Cloud Routine dispatch ticket) and `READY_FOR_SANTIAGO` (the live
    Codex-review handoff ticket). Each must disappear once its phase ends;
    the existing golden-path workflows already do that at every in-flight
    transition (queue claim, correction requeue, clean verification). This
    module's own job is the transition those workflows do not cover:
    close/merge, where the item leaves the actionable state machine
    entirely.

  * **durable** -- `VERIFIED` (explicitly durable per this Issue, `AGENTS.md`,
    and the golden-path doc) and `COMPLETED` (the sole terminal state in
    `zoe_controller_state.TERMINAL_STATES`; the same durability logic as
    `VERIFIED` applies once Žaneta approves completion). `COMPLETED` is not
    currently written as a literal GitHub label by any workflow -- it is
    classified explicitly anyway, per this Issue's instruction not to guess
    by omission.

  * **retired** -- every `controller:*`-prefixed label (the Issue #160
    projection that must never return; this Issue's explicit minimum), plus
    the bare legacy labels `docs/HARNESS_GOLDEN_PATH.md` already names as
    forbidden transport dependencies (`CHANGES_REQUESTED`,
    `SANTIAGO_REVIEWING`, `WORK_IN_PROGRESS`) and `SANTIAGO_STALLED` (named
    in this Issue's own historical-sweep examples); also `CLAUDE_DISPATCHED`,
    `CLAUDE_WORKING`, and `CLAUDE_STALLED` -- bare (non-`controller:`-prefixed)
    labels that the retired `zoe_top_level_label.py`'s `CANONICAL_LABELS` and
    `zoe_controller_watchdog_cli.py::sync_top_level_label` actually wrote
    through the GitHub API (`git show 12f325a^:.github/scripts/zoe_top_level_label.py`),
    contrary to an earlier draft of this module's claim that no bare
    `CLAUDE_*` label was ever written. Also `NEEDS_ZANETA` -- the same
    historical `CANONICAL_LABELS`/`sync_top_level_label` projection wrote
    this bare label too, so it belongs beside its `CLAUDE_*` siblings
    rather than being left unclassified. A closed/merged item still
    carrying one of these from before Issue #160 retired the projection is
    exactly the historical leftover this Issue's cleanup goal targets.

Bare `NEEDS_ZANETA` remains, separately, comment-marker-only vocabulary
per `docs/AGENT_WORKFLOW.md` for the human-lane protocol -- that usage is
untouched. Classifying it here only governs the literal GitHub label the
retired projection wrote; it says nothing about the comment marker.

A label this module does not recognise at all (e.g. `bug`, `enhancement`,
or any future non-harness label) is left alone: `classify()` returns
`"unclassified"` and `labels_to_strip_on_close()` never includes it.
"""

from __future__ import annotations

TRANSIENT_LABELS = frozenset({
    "READY_FOR_CLAUDE_CLOUD",
    "READY_FOR_SANTIAGO",
})

DURABLE_LABELS = frozenset({
    "VERIFIED",
    "COMPLETED",
})

#: Bare (non-`controller:`-prefixed) legacy labels explicitly named
#: forbidden/retired in `docs/HARNESS_GOLDEN_PATH.md` or this Issue's own
#: historical-sweep examples.
RETIRED_BARE_LABELS = frozenset({
    "CHANGES_REQUESTED",
    "SANTIAGO_REVIEWING",
    "WORK_IN_PROGRESS",
    "SANTIAGO_STALLED",
    "CLAUDE_DISPATCHED",
    "CLAUDE_WORKING",
    "CLAUDE_STALLED",
    "NEEDS_ZANETA",
})

#: Any label starting with this prefix is retired, whatever follows it --
#: the entire `controller:*` GitHub-label projection (Issue #160) is
#: forbidden, not just the specific suffixes anyone has seen so far.
RETIRED_LABEL_PREFIX = "controller:"

TRANSIENT = "transient"
DURABLE = "durable"
RETIRED = "retired"
UNCLASSIFIED = "unclassified"


def is_retired(label: str) -> bool:
    return label.startswith(RETIRED_LABEL_PREFIX) or label in RETIRED_BARE_LABELS


def classify(label: str) -> str:
    """Classify a single label name. Order matters: durable and retired are
    checked before transient so a future name collision fails closed
    (durable/retired win) rather than silently becoming strippable.
    """
    if label in DURABLE_LABELS:
        return DURABLE
    if is_retired(label):
        return RETIRED
    if label in TRANSIENT_LABELS:
        return TRANSIENT
    return UNCLASSIFIED


def labels_to_strip_on_close(current_labels) -> list[str]:
    """Labels to remove when an Issue or PR closes or merges.

    Required behavior #4: closing/merging must remove every harness label
    classified transient or retired, and must never touch a durable label
    (`VERIFIED`, `COMPLETED`) or any label this module does not recognise.
    Pure and idempotent: an already-clean label set returns an empty list,
    and calling this twice on the same input is always safe.
    """
    return [label for label in current_labels if classify(label) in (TRANSIENT, RETIRED)]
