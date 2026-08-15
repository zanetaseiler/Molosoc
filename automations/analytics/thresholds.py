#!/usr/bin/env python3
"""
Eligibility and significance gates, plus the site-wide readiness gate.

Two independent questions, deliberately kept separate:

  eligibility  — does this entity have enough volume to be analysed at all?
  significance — is the observed change distinguishable from noise?

An entity must pass both before it can produce an actionable recommendation.
Passing eligibility but failing significance is not nothing — it is exactly
what the Monitor priority is for.

The values here are conservative on purpose. At Molosoc's current volume
(21 GA4 sessions and 8 Search Console impressions in the verified week) almost
nothing clears them, and that is the correct behaviour: a report that
manufactures advice from four clicks is worse than a report that says it cannot
tell yet.
"""

import math

# --- eligibility minimums --------------------------------------------------
MIN_QUERY_IMPRESSIONS = 50      # for CTR / position analysis, both periods
MIN_QUERY_CLICKS_PRIOR = 10     # before "losing clicks" is meaningful
MIN_PAGE_SESSIONS = 30          # GA4 page-level engagement, both periods
MIN_PAGE_SESSIONS_CLARITY = 30  # before quoting a page friction rate
MIN_SESSIONS_FOR_CONVERSION = 100
MIN_IMPRESSIONS_FOR_POSITION = 100

# --- site-level readiness --------------------------------------------------
LOW_VOLUME_SESSIONS = 100       # below this the site is flagged low-volume
MIN_SITE_SESSIONS_FOR_RECOMMENDATIONS = 100

# --- significance ----------------------------------------------------------
# Relative change alone never triggers a finding: 1 click becoming 3 is +200%
# and means nothing. Both gates must pass.
MIN_RELATIVE_CHANGE = 0.20
MIN_ABSOLUTE_CHANGE = {
    "gsc_clicks": 5,
    "gsc_impressions": 50,
    "ga4_sessions": 20,
    "ga4_users": 15,
    "ga4_views": 25,
    "clarity_sessions": 20,
    "clarity_human_sessions": 20,
}
DEFAULT_MIN_ABSOLUTE_CHANGE = 10

MIN_POSITION_CHANGE = 1.0
Z_CRITICAL_95 = 1.96

# --- opportunity thresholds ------------------------------------------------
WEAK_CTR_MAX = 0.02             # impressions without clicks to match
STRONG_IMPRESSIONS_MIN = 100
THRESHOLD_PROXIMITY_RANGE = (8.0, 20.0)   # realistic push to page one / top three
WEAK_ENGAGEMENT_MAX = 0.35
STRONG_ENGAGEMENT_MIN = 0.60
LOW_VISIBILITY_IMPRESSIONS = 50
FRICTION_RATE_WARN = 0.05


def min_absolute_change(metric):
    return MIN_ABSOLUTE_CHANGE.get(metric, DEFAULT_MIN_ABSOLUTE_CHANGE)


def relative_change(current, prior):
    """Signed relative change; None when there is no baseline to divide by."""
    if prior in (None, 0):
        return None
    return (current - prior) / abs(prior)


def is_significant_count(metric, current, prior):
    """A count moved enough to be worth reporting.

    Requires both a relative and an absolute move. Either alone produces
    findings that are technically true and practically meaningless.
    """
    if prior is None:
        return False
    delta = abs(current - prior)
    if delta < min_absolute_change(metric):
        return False
    rel = relative_change(current, prior)
    if rel is None:
        # No prior volume at all: significant only if the absolute move is
        # large enough on its own.
        return delta >= min_absolute_change(metric)
    return abs(rel) >= MIN_RELATIVE_CHANGE


def two_proportion_z(successes_a, trials_a, successes_b, trials_b):
    """Z statistic for two rates. None when either sample is empty."""
    if not trials_a or not trials_b:
        return None
    p1 = successes_a / trials_a
    p2 = successes_b / trials_b
    pooled = (successes_a + successes_b) / (trials_a + trials_b)
    if pooled in (0, 1):
        return 0.0
    se = math.sqrt(pooled * (1 - pooled) * (1 / trials_a + 1 / trials_b))
    if se == 0:
        return 0.0
    return (p1 - p2) / se


def is_significant_rate(successes_a, trials_a, successes_b, trials_b, z_critical=Z_CRITICAL_95):
    z = two_proportion_z(successes_a, trials_a, successes_b, trials_b)
    return z is not None and abs(z) >= z_critical


def proportion_confidence_interval(successes, trials, z=Z_CRITICAL_95):
    """Wald interval, clamped to [0, 1]. None for an empty sample.

    Reported alongside every rate so a reader can see how much of a movement is
    measurement noise rather than a change in behaviour.
    """
    if not trials:
        return None
    p = successes / trials
    margin = z * math.sqrt(max(p * (1 - p), 0) / trials)
    return (max(0.0, p - margin), min(1.0, p + margin))


def is_significant_position(current, prior, impressions):
    """Position moves need both a real shift and enough impressions behind it."""
    if prior is None or impressions is None:
        return False
    return (abs(current - prior) >= MIN_POSITION_CHANGE
            and impressions >= MIN_IMPRESSIONS_FOR_POSITION)


# --- eligibility -----------------------------------------------------------

def query_eligible_for_ctr(impressions_period, impressions_prior):
    return (impressions_period >= MIN_QUERY_IMPRESSIONS
            and impressions_prior >= MIN_QUERY_IMPRESSIONS)


def query_eligible_for_click_loss(clicks_prior):
    return clicks_prior >= MIN_QUERY_CLICKS_PRIOR


def page_eligible_for_engagement(sessions_period, sessions_prior):
    return sessions_period >= MIN_PAGE_SESSIONS and sessions_prior >= MIN_PAGE_SESSIONS


def page_eligible_for_friction(sessions_period):
    return sessions_period >= MIN_PAGE_SESSIONS_CLARITY


def eligible_for_conversion(sessions_period, sessions_prior):
    return (sessions_period >= MIN_SESSIONS_FOR_CONVERSION
            and sessions_prior >= MIN_SESSIONS_FOR_CONVERSION)


# --- site readiness gate ---------------------------------------------------

class Readiness:
    """Whether the site as a whole has enough volume to support advice."""

    __slots__ = ("ready", "sessions", "reason")

    def __init__(self, ready, sessions, reason):
        self.ready = ready
        self.sessions = sessions
        self.reason = reason

    def to_dict(self):
        return {"ready": self.ready, "sessions": self.sessions, "reason": self.reason}


def assess_readiness(site_sessions, minimum=MIN_SITE_SESSIONS_FOR_RECOMMENDATIONS):
    """The gate that lets the agent say 'insufficient data for recommendation'.

    Below the minimum the agent still reports every fact it measured — it
    simply declines to turn them into actions, and says so.
    """
    if site_sessions is None:
        return Readiness(
            False, None,
            "No session data available for the period — recommendations withheld.",
        )
    if site_sessions < minimum:
        return Readiness(
            False, site_sessions,
            f"insufficient data for recommendation: {site_sessions:.0f} sessions in the "
            f"period, below the {minimum} minimum. Facts are reported; actions are "
            "withheld until volume supports them.",
        )
    return Readiness(
        True, site_sessions,
        f"{site_sessions:.0f} sessions in the period, at or above the {minimum} minimum.",
    )
