#!/usr/bin/env python3
"""
The Email Marketing card on the weekly dashboard.

Concise by construction. The full email report is a separate page with its own
address; this is the four things a reader of the *overall* report needs — is
the channel healthy, what did it do, what is the one thing worth knowing, and
what should happen next — plus a link to the rest.

IT READS THE ARTIFACT, NOT THE PAGE

The input is the normalized email evidence document the orchestrator publishes:
the same document the dedicated report renders from and the same one the Growth
Engine reads as channel evidence. It is never the rendered HTML. Scraping a
page for numbers couples this report to another report's layout, and the first
design change silently empties the card.

    reports/email/latest.json  →  reports/email/data/<week>/email.json
                                            │
                                            ├→ the dedicated Email report
                                            ├→ THIS CARD
                                            └→ the Growth Engine's email channel

THE ONE RULE IT INHERITS

A figure the email platform could not measure carries no value, and this module
renders it as words rather than as a number. `0` and "we could not see it" mean
opposite things, and the whole email contract exists to keep them apart — a
summary card that flattened them would undo that at the last step, on the page
most people actually read.

Nothing here computes a new number. Rates are derived from the counts in the
same document by the same arithmetic the contract publishes, and a rate with no
denominator is an absence rather than a zero.
"""

import trafficdom_design as td

#: The four figures the overall report gets. Each one can change a decision on
#: its own: whether it arrived, whether it worked, whether it is costing
#: permission, and whether it sold anything.
SUMMARY_METRICS = (
    ("delivered", "Delivered", "count"),
    ("click_rate", "Click rate", "ratio"),
    ("unsubscribe_rate", "Unsubscribe rate", "ratio"),
    ("revenue", "Revenue", "currency"),
)

#: Derived here from counts, never read from the document's own `rates` block —
#: so this card cannot disagree with the dedicated report about what a rate is.
RATES = {
    "delivery_rate": ("delivered", "sent"),
    "click_rate": ("unique_clicks", "delivered"),
    "unsubscribe_rate": ("unsubscribes", "delivered"),
    "bounce_rate": ("bounced", "sent"),
}

COVERAGE_TONE = {"available": "ready", "partial": "waiting",
                 "unavailable": "blocked"}
COVERAGE_LABEL = {"available": "Reporting", "partial": "Reporting with gaps",
                  "unavailable": "Not reporting"}

NOT_AVAILABLE = "Not available"

#: What the card says when no document exists at all. Distinct from "the
#: channel sent nothing": one is a reporting gap, the other is a result.
NOT_CONNECTED = (
    "The email programme is not yet publishing evidence to this report. "
    "Nothing here is a statement about how email is performing."
)


def _value(entry):
    """A count from the document, or ``None`` when it carries no value.

    Two shapes are accepted because the contract publishes both: a bare number,
    and an object carrying a basis. An object whose basis is `unavailable`
    carries no value at all, and this returns ``None`` for it — never 0.0.
    """
    if entry is None or isinstance(entry, bool):
        return None
    if isinstance(entry, (int, float)):
        return float(entry)
    if isinstance(entry, dict):
        if entry.get("basis") == "unavailable":
            return None
        value = entry.get("value")
        return float(value) if isinstance(value, (int, float)) else None
    return None


def _counts(document):
    return ((document.get("channel") or {}).get("counts") or {})


def _count(document, field):
    return _value(_counts(document).get(field))


def _rate(document, name):
    numerator, denominator = RATES[name]
    top, bottom = _count(document, numerator), _count(document, denominator)
    if top is None or not bottom:
        return None
    return top / bottom


def _format(value, kind):
    if value is None:
        return NOT_AVAILABLE
    if kind == "ratio":
        return f"{value * 100:.1f}%"
    if kind == "currency":
        return f"{value:,.2f}"
    return f"{value:,.0f}"


def _basis_note(document, field):
    """What qualifies this figure, when something does."""
    entry = _counts(document).get(field)
    if not isinstance(entry, dict):
        return ""
    if entry.get("basis") == "unavailable":
        return "Not reported for this account"
    if entry.get("basis") == "assisted":
        return "Associated, not attributed"
    return ""


def _trend(document):
    """The one movement worth a line on a summary card."""
    previous = (document.get("channel") or {}).get("previous_counts") or {}
    if not previous:
        return "", "unknown"
    for field in ("unique_clicks", "delivered", "sent"):
        current, before = _count(document, field), _value(previous.get(field))
        if current is None or not before:
            continue
        change = (current - before) / before
        if abs(change) < 0.005:
            return "no change vs previous period", "flat"
        sign = "+" if change > 0 else "−"
        return (f"{sign}{abs(change) * 100:.1f}% vs previous period",
                "up" if change > 0 else "down")
    return "", "unknown"


def strongest_observation(document):
    """The single most decision-useful thing in the document.

    Concerns before watches, and the first of them. The dedicated report shows
    all of them; a summary card that listed three has stopped being a summary.
    """
    observations = document.get("observations") or []
    for severity in ("concern", "watch", "info"):
        for entry in observations:
            if entry.get("severity") == severity and entry.get("headline"):
                return entry["headline"]
    return ""


def next_action(document):
    """The first recommendation, in urgency order. Advisory, like all of them."""
    order = ("revise", "investigate", "test", "monitor", "keep")
    labels = {"revise": "Revise", "investigate": "Investigate", "test": "Test",
              "monitor": "Monitor", "keep": "Keep as is"}
    recommendations = document.get("recommendations") or []
    for action in order:
        for entry in recommendations:
            if entry.get("action") == action and entry.get("headline"):
                return f"{labels[action]}: {entry['headline']}"
    return ""


def summary_metrics(document):
    """The rendered metric cards. An unmeasured figure appears, in words."""
    cards = []
    for field, label, kind in SUMMARY_METRICS:
        if field in RATES:
            value = _rate(document, field)
            note = ""
        else:
            value = _count(document, field)
            note = _basis_note(document, field)
        cards.append(td.metric(_format(value, kind), label, note=note or None,
                               muted=value is None))
    return cards


def email_section(document, report_url=None):
    """The Email Marketing block for the overall report.

    ``document`` is the normalized artifact, or ``None`` when none has been
    published. ``report_url`` is supplied by the caller — never taken from the
    document, which would be untrusted input pointing wherever it liked.
    """
    if not isinstance(document, dict) or not document:
        return td.section(
            "Email marketing",
            td.empty_state(NOT_CONNECTED),
            eyebrow="Channel", anchor="email")

    coverage = ((document.get("coverage") or {}).get("state") or "available")
    period = document.get("period") or {}
    change, direction = _trend(document)

    observation = strongest_observation(document)
    action = next_action(document)

    # Named for what the card holds rather than for the channel: the section
    # heading already says "Email marketing", and a card repeating it wraps to
    # two lines and reads as a duplicate rather than as a status.
    card = td.channel_card(
        name="Channel status",
        state_label=COVERAGE_LABEL.get(coverage, "Reporting"),
        tone=COVERAGE_TONE.get(coverage, "waiting"),
        observation=observation or "Nothing in this period's email evidence "
                                   "rises above routine monitoring.",
        figures=[("sent", _format(_count(document, "sent"), "count")),
                 ("delivery", _format(_rate(document, "delivery_rate"), "ratio"))],
    )

    band = td.metric_band(summary_metrics(document))
    trend = td.note_panel("Period", (
        f"{period.get('start', '')} to {period.get('end', '')}"
        + (f" · {change}" if change else "")))
    advice = td.note_panel("Recommended next action", action) if action else ""
    link = td.onward_link(
        "Open the full Email Marketing report", report_url,
        "Automation by automation, split by language, with what could not be "
        "measured stated in full.") if report_url else ""

    return td.section(
        "Email marketing",
        td.channel_grid([card]) + band + trend + advice + link,
        eyebrow="Channel",
        lede="A summary of the email programme. The full report is a separate "
             "page.",
        anchor="email")


def load(path):
    """Read a published email document from a local file, or return ``None``.

    A missing file is not an error: the dashboard is generated whether or not
    email evidence was collected this week, and a weekly report that failed
    because a second channel was quiet would be a worse report.
    """
    import json
    import os

    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            document = json.load(handle)
    except (OSError, ValueError):
        return None
    return document if isinstance(document, dict) and document.get("kind") else None


# --------------------------------------------------------------------------
# Fetching the published document
# --------------------------------------------------------------------------

#: The email orchestrator's feed. Same layout as this system's own weekly feed,
#: deliberately: one mutable pointer naming one write-once document.
POINTER_KEY = "reports/email/latest.json"

#: The only prefix the pointer may name. It arrives inside a document, which
#: makes it input rather than instruction — a partially-written pointer or a
#: publish bug could name any object in the bucket, and this report has no
#: business reading anything else.
DATA_PREFIX = "reports/email/data/"


class PointerRefused(ValueError):
    """The pointer named a key this report may not read."""


def referenced_key(pointer):
    """The document key the pointer names, validated before it is requested."""
    if not isinstance(pointer, dict):
        raise PointerRefused("the email pointer is not a JSON object")
    key = pointer.get("json_key")
    if not isinstance(key, str) or not key.strip():
        raise PointerRefused("the email pointer names no document")
    key = key.strip()
    if not key.startswith(DATA_PREFIX) or not key.endswith(".json"):
        raise PointerRefused(
            f"refusing to read {key!r}: the email pointer may only name a "
            f".json object under {DATA_PREFIX!r}")
    if ".." in key or key.startswith("/") or "//" in key:
        raise PointerRefused(f"refusing to read {key!r}: unusable object key")
    return key


def fetch(store):
    """Follow the pointer and return the document, or ``None``.

    Two reads and no listing, the same shape as every other pointer-following
    read in this system. Any failure returns ``None``: the weekly report is
    generated whether or not email evidence exists, and a dashboard that failed
    because a second channel was quiet would be a worse dashboard.
    """
    try:
        pointer = store.get_json(POINTER_KEY)
    except Exception:                              # noqa: BLE001 — see docstring
        return None
    if pointer is None:
        return None
    try:
        key = referenced_key(pointer)
    except PointerRefused:
        raise
    try:
        document = store.get_json(key)
    except Exception:                              # noqa: BLE001
        return None
    return document if isinstance(document, dict) and document.get("kind") else None
