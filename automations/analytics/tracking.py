#!/usr/bin/env python3
"""
Recommendation tracking: did the change we suggested actually help?

This is what turns a report generator into something that learns. Each
recommendation carries a measurement_plan written when it was created, and a
later run compares the window before `implemented_at` against the window after,
using the same significance rules any other finding must clear.

Two design choices worth knowing:

* Judgement uses the **original** plan, not a metric chosen afterwards. That is
  the difference between measuring an outcome and marking your own homework.
* If anything else touched the same entity during the measurement window — an
  anomaly, or another implemented recommendation — the outcome is marked
  confounded and downgraded to inconclusive. At Molosoc's volume confounding
  will be common, and an honest "we cannot tell" is more useful than a
  flattering attribution.

The ledger is stored as one JSON document. Implementation status is set by a
human: an automated guess about whether advice was followed would poison the
outcome data it feeds.
"""

import datetime as dt

from analysis_model import (
    OUTCOME_CONFOUNDED, OUTCOME_IMPROVED, OUTCOME_INCONCLUSIVE,
    OUTCOME_NO_CHANGE, OUTCOME_PENDING, OUTCOME_WORSENED, STATUS_IMPLEMENTED,
    STATUS_PROPOSED, Recommendation, MeasurementPlan,
)
import thresholds as th
from storage import StorageError

LEDGER_KEY = "state/recommendations/ledger.json"

IMPROVED_DIRECTIONS = {"increase": 1, "decrease": -1}


def load_ledger(store):
    """Every tracked recommendation, keyed by fingerprint."""
    try:
        document = store.get_json(LEDGER_KEY)
    except StorageError:
        return {}
    return {entry["fingerprint"]: entry for entry in document.get("recommendations", [])}


def save_ledger(store, ledger):
    store.put_json(
        LEDGER_KEY,
        {"recommendations": [ledger[k] for k in sorted(ledger)]},
        overwrite=True,
    )


def merge_into_ledger(ledger, recommendations, now=None):
    """Fold this run's recommendations into the ledger.

    A regenerated recommendation attaches to its existing record as a
    recurrence rather than creating a duplicate — without this the ledger fills
    with copies within a month and tracking becomes unusable. Human-set fields
    (status, implemented_at, outcome) are never overwritten by a new run.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    stamp = now.replace(microsecond=0).isoformat()
    updated = dict(ledger)

    for recommendation in recommendations:
        fingerprint = recommendation.fingerprint
        existing = updated.get(fingerprint)
        entry = recommendation.to_dict()
        if existing:
            entry["recurrence_count"] = existing.get("recurrence_count", 1) + 1
            entry["created_at"] = existing.get("created_at", entry["created_at"])
            # Human decisions survive regeneration.
            for preserved in ("status", "implemented_at", "outcome",
                              "outcome_detail", "review_after_date"):
                if existing.get(preserved) not in (None, STATUS_PROPOSED, OUTCOME_PENDING):
                    entry[preserved] = existing[preserved]
        entry["last_seen_at"] = stamp
        updated[fingerprint] = entry

    return updated


def due_for_review(ledger, today=None):
    """Implemented recommendations whose review date has arrived."""
    today = today or dt.date.today()
    if isinstance(today, str):
        today = dt.date.fromisoformat(today)
    due = []
    for entry in ledger.values():
        if entry.get("status") != STATUS_IMPLEMENTED:
            continue
        if entry.get("outcome") not in (None, OUTCOME_PENDING):
            continue
        review_after = entry.get("review_after_date")
        if review_after and dt.date.fromisoformat(review_after) <= today:
            due.append(entry)
    return sorted(due, key=lambda e: e["fingerprint"])


class OutcomeVerdict:
    __slots__ = ("outcome", "detail", "before", "after", "confounded_by")

    def __init__(self, outcome, detail, before=None, after=None, confounded_by=()):
        self.outcome = outcome
        self.detail = detail
        self.before = before
        self.after = after
        self.confounded_by = tuple(confounded_by)

    def to_dict(self):
        return {
            "outcome": self.outcome, "detail": self.detail,
            "before": self.before, "after": self.after,
            "confounded_by": list(self.confounded_by),
        }

    def __repr__(self):
        return f"OutcomeVerdict({self.outcome})"


def classify_outcome(plan, before, after, before_sample=None, after_sample=None,
                     confounders=()):
    """Judge one implemented recommendation against its original plan.

    `plan` is the MeasurementPlan recorded at creation. `before` and `after` are
    the aggregated values of its named metric on either side of implementation.
    """
    if isinstance(plan, dict):
        plan = MeasurementPlan(**plan)

    if before is None or after is None:
        return OutcomeVerdict(
            OUTCOME_INCONCLUSIVE,
            "Not enough stored history on one side of the implementation date to "
            "compare. Clarity history in particular cannot be backfilled.",
            before, after,
        )

    if plan.min_sample:
        for sample, side in ((before_sample, "before"), (after_sample, "after")):
            if sample is not None and sample < plan.min_sample:
                return OutcomeVerdict(
                    OUTCOME_INCONCLUSIVE,
                    f"Sample on the {side} side ({sample:.0f}) is below the "
                    f"{plan.min_sample:.0f} minimum recorded in the measurement "
                    "plan — too small to judge.",
                    before, after,
                )

    if confounders:
        return OutcomeVerdict(
            OUTCOME_CONFOUNDED,
            "Another change or anomaly overlapped the measurement window, so the "
            "movement cannot be attributed to this recommendation: "
            + "; ".join(confounders),
            before, after, confounders,
        )

    wanted = IMPROVED_DIRECTIONS.get(plan.direction)
    if wanted is None:
        return OutcomeVerdict(
            OUTCOME_INCONCLUSIVE,
            f"Measurement plan has an unrecognised direction {plan.direction!r}.",
            before, after,
        )

    significant = _significant_for(plan.metric, after, before, after_sample, before_sample)
    if not significant:
        return OutcomeVerdict(
            OUTCOME_NO_CHANGE,
            f"{plan.metric} moved from {before:.4g} to {after:.4g}, which does not "
            "clear the same significance bar any other finding must meet.",
            before, after,
        )

    moved = 1 if after > before else -1
    if moved == wanted:
        return OutcomeVerdict(
            OUTCOME_IMPROVED,
            f"{plan.metric} moved from {before:.4g} to {after:.4g}, the intended "
            f"direction ({plan.direction}), by a significant margin.",
            before, after,
        )
    return OutcomeVerdict(
        OUTCOME_WORSENED,
        f"{plan.metric} moved from {before:.4g} to {after:.4g}, against the "
        f"intended direction ({plan.direction}), by a significant margin.",
        before, after,
    )


def _significant_for(metric, current, prior, current_sample, prior_sample):
    """Reuse the same gates the analysis uses, chosen by metric shape."""
    if metric == "gsc_position":
        return th.is_significant_position(current, prior, current_sample)
    if metric.endswith(("_rate", "_ctr", "_share")) or metric == "gsc_ctr":
        if current_sample and prior_sample:
            return th.is_significant_rate(
                current * current_sample, current_sample,
                prior * prior_sample, prior_sample,
            )
        rel = th.relative_change(current, prior)
        return rel is not None and abs(rel) >= th.MIN_RELATIVE_CHANGE
    return th.is_significant_count(metric, current, prior)


def apply_verdict(entry, verdict, now=None):
    """Write a verdict back onto a ledger entry."""
    now = now or dt.datetime.now(dt.timezone.utc)
    updated = dict(entry)
    updated["outcome"] = verdict.outcome
    updated["outcome_detail"] = verdict.detail
    updated["outcome_measured_at"] = now.replace(microsecond=0).isoformat()
    updated["outcome_before"] = verdict.before
    updated["outcome_after"] = verdict.after
    if verdict.confounded_by:
        updated["outcome_confounded_by"] = list(verdict.confounded_by)
    return updated


def summarise(ledger):
    """Counts by status and outcome, for the report's tracking section."""
    by_status, by_outcome = {}, {}
    for entry in ledger.values():
        by_status[entry.get("status", STATUS_PROPOSED)] = \
            by_status.get(entry.get("status", STATUS_PROPOSED), 0) + 1
        outcome = entry.get("outcome", OUTCOME_PENDING)
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
    return {"total": len(ledger), "by_status": by_status, "by_outcome": by_outcome}
