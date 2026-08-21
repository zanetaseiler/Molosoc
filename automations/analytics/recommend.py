#!/usr/bin/env python3
"""
Turning inferences into recommendations, with the priority rubric applied
mechanically rather than by judgement.

Three gates stand between a signal and an action:

  1. The site readiness gate. Below the minimum session volume the agent says
     "insufficient data for recommendation" and issues nothing above Monitor.
  2. Instrumentation suppression. An entity touched by an instrumentation
     anomaly produces no recommendation at all — the measurement is suspect,
     so any advice built on it is guesswork wearing a number.
  3. Per-entity eligibility and significance, already decided when the facts
     were built.

Every recommendation carries a measurement_plan recorded at creation. Choosing
the metric afterwards is how a system ends up marking its own homework.
"""

import datetime as dt

from analysis_model import (
    AREA_CONTENT, AREA_CONVERSION, AREA_SEO, AREA_UX, HIGH, INSUFFICIENT_DATA,
    LOW, MEDIUM, MeasurementPlan, PRIORITY_HIGH, PRIORITY_MEDIUM,
    PRIORITY_MONITOR, READY, Recommendation, SUPPRESSED,
    recommendation_fingerprint,
)
import anomalies as an
import signals as sg

DEFAULT_REVIEW_DAYS = 28

# Estimated impact is expressed relative to site totals, so "material" means
# material to the business rather than large as a percentage of a tiny number.
MATERIAL_IMPACT_SHARE = 0.10


class Template:
    """How one signal becomes an action."""

    __slots__ = ("area", "action_kind", "action", "measure_metric", "direction",
                 "base_confidence")

    def __init__(self, area, action_kind, action, measure_metric, direction,
                 base_confidence=MEDIUM):
        self.area = area
        self.action_kind = action_kind
        self.action = action
        self.measure_metric = measure_metric
        self.direction = direction
        self.base_confidence = base_confidence


TEMPLATES = {
    sg.DEMAND_UP_CAPTURE_DOWN: Template(
        AREA_SEO, "improve_serp_presentation",
        "Rewrite the title tag and meta description for {entity} to match the "
        "queries now generating impressions. The listing is being seen and not "
        "chosen, so the change belongs in the SERP snippet before the page body.",
        "gsc_ctr", "increase", HIGH,
    ),
    sg.CAPTURE_UP_SATISFACTION_DOWN: Template(
        AREA_CONTENT, "align_content_to_intent",
        "Review {entity} against the queries now driving clicks and make the "
        "first screen answer them directly. Arrivals are rising while on-page "
        "signals weaken, which points at an intent mismatch rather than volume.",
        "ga4_engagement_rate", "increase", MEDIUM,
    ),
    sg.FRICTION_AGAINST_INTENT: Template(
        AREA_UX, "investigate_page_friction",
        "Watch a sample of Clarity session recordings for {entity} and identify "
        "what users are clicking that does not respond. Fix or make "
        "non-interactive whatever is absorbing the clicks.",
        "clarity_rage_click_rate", "decrease", MEDIUM,
    ),
    sg.HIDDEN_GEM: Template(
        AREA_SEO, "increase_visibility",
        "Add internal links to {entity} from the highest-traffic related pages "
        "and expand its coverage of the queries it already half-answers. The "
        "content holds the visitors it gets; visibility is the constraint.",
        "gsc_impressions", "increase", MEDIUM,
    ),
    sg.THRESHOLD_PROXIMITY: Template(
        AREA_SEO, "push_ranking_threshold",
        "Strengthen {entity} for the queries it already ranks near the "
        "threshold on: tighten the on-page match, add the sub-topics "
        "competitors cover, and secure at least one internal link from a "
        "stronger page.",
        "gsc_position", "decrease", MEDIUM,
    ),
}

# Source disagreement never becomes an action — it is a reason not to act.
NON_ACTIONABLE_SIGNALS = (sg.SOURCE_DISAGREEMENT,)


def entity_label(entity_id):
    """How an entity id reads inside a sentence a client is meant to follow.

    The templates are written as instructions — "Watch a sample of Clarity
    session recordings for {entity}" — and the site-level id is the literal
    string "site", which rendered as "recordings for site". A noun needs its
    article.

    Presentation only, and safe for tracking: recommendation fingerprints are
    hashed from `entity_id` itself, so how its sentence reads has no bearing on
    whether a recommendation is recognised again next week.
    """
    text = str(entity_id or "").strip()
    return "the site" if not text or text == "site" else text


def estimate_impact_share(inference, index, site_totals):
    """How much of the site's total this entity represents.

    A page that is 40% of search impressions matters more than one that is 2%,
    whatever the percentage change on each looks like.
    """
    metric_by_signal = {
        sg.DEMAND_UP_CAPTURE_DOWN: "gsc_impressions",
        sg.HIDDEN_GEM: "ga4_sessions",
        sg.THRESHOLD_PROXIMITY: "gsc_impressions",
        sg.CAPTURE_UP_SATISFACTION_DOWN: "gsc_clicks",
        sg.FRICTION_AGAINST_INTENT: "ga4_sessions",
    }
    metric = metric_by_signal.get(inference.signal)
    if not metric:
        return 0.0
    total = site_totals.get(metric)
    entity_value = index.value(inference.entity_id, metric)
    if not total or entity_value is None:
        return 0.0
    return entity_value / total


def assign_priority(inference, impact_share, readiness_ready, suppressed):
    """The rubric, applied the same way every run."""
    if suppressed:
        return PRIORITY_MONITOR, SUPPRESSED
    if not readiness_ready:
        return PRIORITY_MONITOR, INSUFFICIENT_DATA
    if inference.confidence == LOW:
        return PRIORITY_MONITOR, READY
    if inference.confidence == HIGH and impact_share >= MATERIAL_IMPACT_SHARE:
        return PRIORITY_HIGH, READY
    if impact_share >= MATERIAL_IMPACT_SHARE or inference.confidence == HIGH:
        return PRIORITY_MEDIUM, READY
    return PRIORITY_MONITOR, READY


def build_recommendation(inference, index, site_totals, readiness_ready,
                         anomaly_list, now=None, review_days=DEFAULT_REVIEW_DAYS):
    """One recommendation from one inference, or None if the signal is not
    actionable."""
    if inference.signal in NON_ACTIONABLE_SIGNALS:
        return None
    template = TEMPLATES.get(inference.signal)
    if template is None:
        return None

    suppressed = an.is_suppressed(inference.entity_id, anomaly_list)
    impact_share = estimate_impact_share(inference, index, site_totals)
    priority, readiness = assign_priority(
        inference, impact_share, readiness_ready, suppressed
    )

    now = now or dt.datetime.now(dt.timezone.utc)
    review_after = (now.date() + dt.timedelta(days=review_days)).isoformat()

    rationale_parts = [inference.statement]
    if suppressed:
        rationale_parts.append(
            "Held at Monitor: an instrumentation anomaly covers this entity, so "
            "its measurements are not currently trustworthy."
        )
    elif not readiness_ready:
        rationale_parts.append(
            "Held at Monitor: site volume is below the minimum for actionable "
            "recommendations — insufficient data for recommendation."
        )
    else:
        rationale_parts.append(
            f"This entity represents {impact_share:.0%} of the relevant site total."
        )

    fingerprint = recommendation_fingerprint(
        template.area, inference.entity_id, template.action_kind
    )
    return Recommendation(
        id=fingerprint,
        fingerprint=fingerprint,
        priority=priority,
        area=template.area,
        action=template.action.format(
            entity=entity_label(inference.entity_id)),
        rationale=" ".join(rationale_parts),
        supporting_facts=tuple(inference.based_on),
        supporting_inferences=(inference.id,),
        measurement_plan=MeasurementPlan(
            metric=template.measure_metric,
            entity_id=inference.entity_id,
            entity_type=inference.entity_type,
            direction=template.direction,
            min_observation_days=review_days,
            min_sample=_min_sample_for(template.measure_metric),
        ),
        confidence=inference.confidence,
        readiness=readiness,
        created_at=now.replace(microsecond=0).isoformat(),
        review_after_date=review_after,
    )


def _min_sample_for(metric):
    import thresholds as th

    if metric.startswith("gsc_"):
        return th.MIN_QUERY_IMPRESSIONS
    if metric.startswith("clarity_"):
        return th.MIN_PAGE_SESSIONS_CLARITY
    return th.MIN_PAGE_SESSIONS


def build_all(inferences, facts, site_totals, readiness_ready, anomaly_list,
              now=None, review_days=DEFAULT_REVIEW_DAYS):
    """Recommendations for every actionable inference, highest priority first.

    Deduplicated by fingerprint: the same condition produces the same
    recommendation on every run, and a repeat is a recurrence rather than a new
    record.
    """
    index = sg.FactIndex(facts)
    by_fingerprint = {}

    for inference in inferences:
        recommendation = build_recommendation(
            inference, index, site_totals, readiness_ready, anomaly_list,
            now=now, review_days=review_days,
        )
        if recommendation is None:
            continue
        existing = by_fingerprint.get(recommendation.fingerprint)
        if existing is None:
            by_fingerprint[recommendation.fingerprint] = recommendation
        else:
            # Same action reached by two signals: keep the stronger, and record
            # that more than one route led here.
            keep = max((existing, recommendation), key=lambda r: _priority_rank(r.priority))
            merged_facts = tuple(dict.fromkeys(existing.supporting_facts
                                               + recommendation.supporting_facts))
            merged_inferences = tuple(dict.fromkeys(existing.supporting_inferences
                                                    + recommendation.supporting_inferences))
            by_fingerprint[recommendation.fingerprint] = Recommendation(
                **{**keep.to_dict(),
                   "supporting_facts": merged_facts,
                   "supporting_inferences": merged_inferences,
                   "measurement_plan": keep.measurement_plan,
                   "recurrence_count": existing.recurrence_count + 1}
            )

    return sorted(
        by_fingerprint.values(),
        key=lambda r: (-_priority_rank(r.priority), r.area, r.id),
    )


def _priority_rank(priority):
    return {PRIORITY_HIGH: 3, PRIORITY_MEDIUM: 2, PRIORITY_MONITOR: 1}.get(priority, 0)
