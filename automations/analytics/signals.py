#!/usr/bin/env python3
"""
The six approved cross-source signals.

Each is a named, testable rule with declared inputs and thresholds: it either
fires or it does not, and the reason is inspectable. That is the whole point of
naming them rather than letting an analysis narrate whatever it noticed.

Every signal produces an Inference, which by construction is correlational,
references the facts it rests on, and carries at least one alternative
explanation. The model rejects causal language outright, so a signal cannot
quietly graduate into a causal claim.

The signals:
  demand_up_capture_down   impressions up, clicks flat/down, CTR down
  capture_up_satisfaction_down clicks up, engagement down or quick-backs up
  friction_against_intent  rage/dead clicks up on a page with real traffic
  hidden_gem               strong engagement, weak search visibility
  threshold_proximity      position 8-20 with enough impressions to matter
  source_disagreement      two sources moving opposite ways on one entity
"""

from analysis_model import (
    CORRELATION, HIGH, LOW, MEDIUM, PATTERN, Inference, inference_id,
)
import thresholds as th

DEMAND_UP_CAPTURE_DOWN = "demand_up_capture_down"
CAPTURE_UP_SATISFACTION_DOWN = "capture_up_satisfaction_down"
FRICTION_AGAINST_INTENT = "friction_against_intent"
HIDDEN_GEM = "hidden_gem"
THRESHOLD_PROXIMITY = "threshold_proximity"
SOURCE_DISAGREEMENT = "source_disagreement"

ALL_SIGNALS = (
    DEMAND_UP_CAPTURE_DOWN, CAPTURE_UP_SATISFACTION_DOWN, FRICTION_AGAINST_INTENT,
    HIDDEN_GEM, THRESHOLD_PROXIMITY, SOURCE_DISAGREEMENT,
)


class FactIndex:
    """Lookup over a report's facts by (entity, metric)."""

    def __init__(self, facts):
        self._by_key = {}
        for fact in facts:
            self._by_key[(fact.entity_id, fact.metric)] = fact

    def get(self, entity_id, metric):
        return self._by_key.get((entity_id, metric))

    def value(self, entity_id, metric, default=None):
        fact = self.get(entity_id, metric)
        return default if fact is None else fact.period_value

    def prior(self, entity_id, metric, default=None):
        fact = self.get(entity_id, metric)
        if fact is None or fact.comparison_value is None:
            return default
        return fact.comparison_value

    def ids(self, entity_id, *metrics):
        return tuple(self._by_key[(entity_id, m)].id
                     for m in metrics if (entity_id, m) in self._by_key)

    def entities(self, entity_type):
        return sorted({eid for (eid, _), f in self._by_key.items()
                       if f.entity_type == entity_type})


def _entity_type(index, entity_id):
    for (eid, _), fact in index._by_key.items():
        if eid == entity_id:
            return fact.entity_type
    return "page"


def demand_up_capture_down(index, entity_id):
    """Impressions rising while clicks stall and CTR falls.

    The listing is being seen and not chosen — which points at the SERP
    presentation (title, meta description), not at the page body.
    """
    impressions = index.get(entity_id, "gsc_impressions")
    clicks = index.get(entity_id, "gsc_clicks")
    ctr = index.get(entity_id, "gsc_ctr")
    if not (impressions and clicks and ctr):
        return None
    if impressions.comparison_value is None or ctr.comparison_value is None:
        return None

    if not (impressions.direction == "up" and impressions.significant):
        return None
    if clicks.direction == "up" and clicks.significant:
        return None
    if not (ctr.period_value < ctr.comparison_value and ctr.significant):
        return None

    return Inference(
        id=inference_id(DEMAND_UP_CAPTURE_DOWN, entity_id),
        signal=DEMAND_UP_CAPTURE_DOWN,
        statement=(
            f"{entity_id} gained impressions ({impressions.comparison_value:.0f} → "
            f"{impressions.period_value:.0f}) while clicks did not follow, and CTR "
            f"moved from {ctr.comparison_value:.2%} to {ctr.period_value:.2%}."
        ),
        based_on=index.ids(entity_id, "gsc_impressions", "gsc_clicks", "gsc_ctr"),
        entity_id=entity_id, entity_type=_entity_type(index, entity_id),
        type=CORRELATION,
        confidence=HIGH if ctr.meets_minimum else MEDIUM,
        alternative_explanations=(
            "New impressions may come from broader, less relevant queries that "
            "were never likely to convert to clicks.",
            "A SERP feature or ad block may have pushed the organic listing "
            "further down without any change to the page.",
            "Seasonal query mix can shift CTR without the listing changing.",
        ),
    )


def capture_up_satisfaction_down(index, entity_id):
    """More arrivals, less satisfaction once they land."""
    clicks = index.get(entity_id, "gsc_clicks")
    engagement = index.get(entity_id, "ga4_engagement_rate")
    quickback = index.get(entity_id, "clarity_quickback_rate")
    if not clicks or clicks.comparison_value is None:
        return None
    if not (clicks.direction == "up" and clicks.significant):
        return None

    worsened = []
    if engagement and engagement.comparison_value is not None and \
            engagement.direction == "down" and engagement.significant:
        worsened.append(
            f"engagement rate {engagement.comparison_value:.0%} → {engagement.period_value:.0%}"
        )
    if quickback and quickback.comparison_value is not None and \
            quickback.direction == "up" and quickback.significant:
        worsened.append(
            f"quick-backs {quickback.comparison_value:.1%} → {quickback.period_value:.1%}"
        )
    if not worsened:
        return None

    return Inference(
        id=inference_id(CAPTURE_UP_SATISFACTION_DOWN, entity_id),
        signal=CAPTURE_UP_SATISFACTION_DOWN,
        statement=(
            f"{entity_id} gained search clicks while on-page signals weakened "
            f"({'; '.join(worsened)})."
        ),
        based_on=index.ids(entity_id, "gsc_clicks", "ga4_engagement_rate",
                           "clarity_quickback_rate"),
        entity_id=entity_id, entity_type=_entity_type(index, entity_id),
        type=CORRELATION, confidence=MEDIUM,
        alternative_explanations=(
            "The new clicks may come from queries with different intent, so the "
            "page is being judged against an expectation it never set.",
            "A measurement change (consent banner, tag update) can move "
            "engagement metrics without any change in behaviour.",
            "Traffic-mix shifts between device types move engagement rates on "
            "their own.",
        ),
    )


def friction_against_intent(index, entity_id):
    """People trying to do something the page is not letting them do."""
    rage = index.get(entity_id, "clarity_rage_click_rate")
    dead = index.get(entity_id, "clarity_dead_click_rate")
    sessions = index.get(entity_id, "clarity_visits") or index.get(entity_id, "ga4_sessions")
    if sessions is None or sessions.period_value < th.MIN_PAGE_SESSIONS_CLARITY:
        return None

    signals = []
    for fact, label in ((rage, "rage clicks"), (dead, "dead clicks")):
        if fact and fact.period_value >= th.FRICTION_RATE_WARN:
            signals.append(f"{label} on {fact.period_value:.1%} of sessions")
    if not signals:
        return None

    return Inference(
        id=inference_id(FRICTION_AGAINST_INTENT, entity_id),
        signal=FRICTION_AGAINST_INTENT,
        statement=(
            f"{entity_id} shows interaction friction ({'; '.join(signals)}) on "
            f"{sessions.period_value:.0f} sessions."
        ),
        based_on=index.ids(entity_id, "clarity_rage_click_rate",
                           "clarity_dead_click_rate", "clarity_visits", "ga4_sessions"),
        entity_id=entity_id, entity_type=_entity_type(index, entity_id),
        type=PATTERN, confidence=MEDIUM,
        alternative_explanations=(
            "Non-interactive elements that look clickable (styled headings, "
            "product images) generate dead clicks without anything being broken.",
            "Slow loading can produce repeated clicks that register as rage "
            "clicks even when the control eventually works.",
            "A single bot or automated session can concentrate clicks on one page.",
        ),
    )


def hidden_gem(index, entity_id):
    """The content works for whoever reaches it; visibility is the constraint."""
    engagement = index.get(entity_id, "ga4_engagement_rate")
    impressions = index.get(entity_id, "gsc_impressions")
    if not (engagement and impressions):
        return None
    if engagement.period_value < th.STRONG_ENGAGEMENT_MIN:
        return None
    if impressions.period_value >= th.LOW_VISIBILITY_IMPRESSIONS:
        return None

    return Inference(
        id=inference_id(HIDDEN_GEM, entity_id),
        signal=HIDDEN_GEM,
        statement=(
            f"{entity_id} holds {engagement.period_value:.0%} engagement on only "
            f"{impressions.period_value:.0f} search impressions."
        ),
        based_on=index.ids(entity_id, "ga4_engagement_rate", "gsc_impressions",
                           "ga4_sessions"),
        entity_id=entity_id, entity_type=_entity_type(index, entity_id),
        type=PATTERN, confidence=MEDIUM,
        alternative_explanations=(
            "High engagement on very few sessions is unstable and may regress "
            "once more traffic arrives.",
            "The page may serve an audience that arrives from elsewhere "
            "(email, social) and have no meaningful search demand behind it.",
            "Low impressions can reflect a genuinely small query space rather "
            "than a ranking problem.",
        ),
    )


def threshold_proximity(index, entity_id):
    """Close enough to page one, or the top three, for work to pay off."""
    position = index.get(entity_id, "gsc_position")
    impressions = index.get(entity_id, "gsc_impressions")
    if not (position and impressions):
        return None
    low, high = th.THRESHOLD_PROXIMITY_RANGE
    if not (low <= position.period_value <= high):
        return None
    if impressions.period_value < th.MIN_QUERY_IMPRESSIONS:
        return None

    target = "the top three" if position.period_value <= 10 else "page one"
    return Inference(
        id=inference_id(THRESHOLD_PROXIMITY, entity_id),
        signal=THRESHOLD_PROXIMITY,
        statement=(
            f"{entity_id} sits at average position {position.period_value:.1f} on "
            f"{impressions.period_value:.0f} impressions — within reach of {target}."
        ),
        based_on=index.ids(entity_id, "gsc_position", "gsc_impressions", "gsc_clicks"),
        entity_id=entity_id, entity_type=_entity_type(index, entity_id),
        type=PATTERN, confidence=MEDIUM,
        alternative_explanations=(
            "Average position blends many queries; the page may already rank "
            "first for some and far lower for others.",
            "Competitor strength at the target positions may make the gap much "
            "larger than the numeric distance suggests.",
            "Position is measured only where impressions occurred, so it can "
            "improve while total visibility falls.",
        ),
    )


def source_disagreement(index, entity_id):
    """Two sources moving opposite ways on one entity.

    A data-quality flag, not a finding. It exists to stop a recommendation
    being built on numbers that contradict each other.
    """
    ga4 = index.get(entity_id, "ga4_sessions")
    clarity = index.get(entity_id, "clarity_visits")
    if not (ga4 and clarity):
        return None
    if ga4.comparison_value is None or clarity.comparison_value is None:
        return None
    if ga4.direction == "flat" or clarity.direction == "flat":
        return None
    if ga4.direction == clarity.direction:
        return None
    if not (ga4.significant or clarity.significant):
        return None

    return Inference(
        id=inference_id(SOURCE_DISAGREEMENT, entity_id),
        signal=SOURCE_DISAGREEMENT,
        statement=(
            f"{entity_id} moved {ga4.direction} in GA4 sessions but "
            f"{clarity.direction} in Clarity visits over the same window."
        ),
        based_on=index.ids(entity_id, "ga4_sessions", "clarity_visits"),
        entity_id=entity_id, entity_type=_entity_type(index, entity_id),
        type=CORRELATION, confidence=LOW,
        alternative_explanations=(
            "GA4 and Clarity define and filter sessions differently, and Clarity "
            "totals include bots — the two are not expected to match exactly.",
            "One tracking script may be failing on a subset of pages or devices.",
            "Consent choices can exclude traffic from one tool but not the other.",
        ),
    )


SIGNAL_FUNCTIONS = {
    DEMAND_UP_CAPTURE_DOWN: demand_up_capture_down,
    CAPTURE_UP_SATISFACTION_DOWN: capture_up_satisfaction_down,
    FRICTION_AGAINST_INTENT: friction_against_intent,
    HIDDEN_GEM: hidden_gem,
    THRESHOLD_PROXIMITY: threshold_proximity,
    SOURCE_DISAGREEMENT: source_disagreement,
}


def evaluate(facts, entity_ids=None, signal_names=None):
    """Run every signal against every candidate entity.

    Returns the inferences that fired, in a deterministic order so two runs
    over the same data produce byte-identical output.
    """
    index = FactIndex(facts)
    candidates = sorted(entity_ids) if entity_ids is not None else sorted(
        {f.entity_id for f in facts}
    )
    names = signal_names or ALL_SIGNALS

    fired = []
    for name in names:
        function = SIGNAL_FUNCTIONS[name]
        for entity_id in candidates:
            inference = function(index, entity_id)
            if inference is not None:
                fired.append(inference)
    return fired
