#!/usr/bin/env python3
"""
Data-quality assessment, kept separate from performance measurement.

Two jobs, both aimed at the same failure mode: a number that looks like a
business result but is really a measurement artifact.

* Bot share. The very first Clarity verification run reported 34 bot sessions
  out of 85 — 40%. A week where bot traffic doubles produces a session count
  that rises for no commercial reason at all. Bot share is tracked explicitly,
  and a run whose bot share is high or has moved sharply is flagged so nothing
  downstream reads it as growth.

* Non-production exclusion. Search Console reported staging.molosoc.com URLs
  under the domain property. Those rows are excluded from marketing analysis —
  but the exclusion is counted and reported, never silent, because "the number
  dropped" and "we stopped counting some rows" look identical otherwise.

Flags produced here are advisory metadata. They never modify a performance
metric; they travel alongside it so a reader knows what they are looking at.
"""

from canonical_url import UNKNOWN, canonicalize
from records import PAGE, SITE_ENTITY_ID

# Above this share of sessions, Clarity totals stop being a usable proxy for
# human traffic. Starting value — expected to be tuned once a baseline exists.
BOT_SHARE_WARN = 0.30
BOT_SHARE_CRITICAL = 0.50

# Below this many sessions, a bot share is not meaningfully estimable.
MIN_SESSIONS_FOR_BOT_ASSESSMENT = 20

INFO = "info"
WARN = "warn"
CRITICAL = "critical"


class QualityFlag:
    """One advisory finding about the trustworthiness of a snapshot."""

    __slots__ = ("code", "severity", "message", "details")

    def __init__(self, code, severity, message, details=None):
        self.code = code
        self.severity = severity
        self.message = message
        self.details = details or {}

    def to_dict(self):
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }

    def __repr__(self):
        return f"QualityFlag({self.code}, {self.severity})"


def _value(records, metric, default=0.0):
    for record in records:
        if record.metric == metric and record.entity_id == SITE_ENTITY_ID:
            return record.value
    return default


def assess_bot_share(records, warn=BOT_SHARE_WARN, critical=BOT_SHARE_CRITICAL):
    """Flag a snapshot whose bot share makes its traffic figures unreliable."""
    flags = []
    sessions = _value(records, "clarity_sessions")
    bots = _value(records, "clarity_bot_sessions")

    if sessions < MIN_SESSIONS_FOR_BOT_ASSESSMENT:
        flags.append(QualityFlag(
            "bot_share_not_assessable", INFO,
            f"Only {sessions:.0f} Clarity sessions in this window — too few to "
            "assess bot share meaningfully.",
            {"sessions": sessions, "minimum": MIN_SESSIONS_FOR_BOT_ASSESSMENT},
        ))
        return flags

    share = bots / sessions if sessions else 0.0
    details = {"sessions": sessions, "bot_sessions": bots, "bot_share": round(share, 4)}

    if share >= critical:
        flags.append(QualityFlag(
            "bot_share_critical", CRITICAL,
            f"{share:.0%} of Clarity sessions are bots. Treat total session counts "
            "as unusable for traffic trends; use clarity_human_sessions.",
            details,
        ))
    elif share >= warn:
        flags.append(QualityFlag(
            "bot_share_high", WARN,
            f"{share:.0%} of Clarity sessions are bots. A change in total sessions "
            "may reflect bot volume rather than real traffic.",
            details,
        ))
    else:
        flags.append(QualityFlag(
            "bot_share_normal", INFO,
            f"{share:.0%} of Clarity sessions are bots.", details,
        ))
    return flags


def split_production(records, keep_unknown=False):
    """Partition page records into production and excluded.

    Non-page records pass through untouched — only page entities carry a host.
    """
    kept, excluded = [], []
    for record in records:
        if record.entity_type != PAGE:
            kept.append(record)
            continue
        canonical = canonicalize(record.entity_id)
        allowed = canonical.is_production or (keep_unknown and canonical.classification == UNKNOWN)
        (kept if allowed else excluded).append(record)
    return kept, excluded


def exclusion_flags(excluded):
    """Turn excluded page records into a reported, countable finding."""
    if not excluded:
        return []

    by_host = {}
    for record in excluded:
        host = canonicalize(record.entity_id).host or "(none)"
        by_host[host] = by_host.get(host, 0) + 1

    hosts = ", ".join(f"{h} ({n})" for h, n in sorted(by_host.items()))
    return [QualityFlag(
        "non_production_excluded", WARN,
        f"Excluded {len(excluded)} non-production page record(s) from: {hosts}. "
        "These are real search/analytics rows and their exclusion changes reported "
        "totals — it is deliberate, not data loss.",
        {"excluded_records": len(excluded), "by_host": by_host},
    )]


def assess_snapshot(records, keep_unknown=False):
    """Full data-quality pass over one snapshot.

    Returns the production-only records and every flag raised, so a caller
    cannot take the filtered data without also receiving what was filtered.
    """
    kept, excluded = split_production(records, keep_unknown=keep_unknown)
    flags = assess_bot_share(records) + exclusion_flags(excluded)
    return kept, excluded, flags


def worst_severity(flags):
    order = {INFO: 0, WARN: 1, CRITICAL: 2}
    return max((f.severity for f in flags), key=lambda s: order.get(s, 0), default=INFO)


def performance_is_trustworthy(flags):
    """False when a flag means performance figures should not be read as trends."""
    return worst_severity(flags) != CRITICAL
