#!/usr/bin/env python3
"""
Anomaly detection, split into two classes that call for opposite responses.

A **performance** anomaly is a business event: something really moved.
An **instrumentation** anomaly means the measurement is suspect, and every
finding downstream of it must be suppressed rather than acted on. Advice built
on broken measurement is worse than silence.

Outlier detection uses a median/MAD robust z-score rather than mean/standard
deviation. At Molosoc's volumes a single spiky day would inflate the standard
deviation enough to hide everything else, including itself.
"""

from statistics import median

from analysis_model import (
    INSTRUMENTATION_ANOMALY, PERFORMANCE_ANOMALY, Anomaly, _short_hash,
)

ROBUST_Z_THRESHOLD = 3.5
MIN_SERIES_FOR_OUTLIER = 7

# A bot share moving by more than this between periods changes the meaning of
# every other Clarity number in the window.
BOT_SHARE_SHIFT = 0.15
BOT_SHARE_CRITICAL = 0.50

# Script errors are an instrumentation signal: a deploy regression that breaks
# measurement looks exactly like a behaviour change otherwise.
SCRIPT_ERROR_SPIKE = 0.10

MAD_TO_SIGMA = 0.6745


def robust_z(value, series):
    """Modified z-score against a series' median absolute deviation.

    None when the series is too short, or when the MAD is zero and the value
    matches the median (a perfectly flat series has no outliers).
    """
    values = [v for v in series if v is not None]
    if len(values) < MIN_SERIES_FOR_OUTLIER:
        return None
    centre = median(values)
    deviations = [abs(v - centre) for v in values]
    mad = median(deviations)
    if mad == 0:
        # Degenerate series: fall back to mean absolute deviation so a genuine
        # spike against a flat baseline is still caught.
        mean_dev = sum(deviations) / len(deviations)
        if mean_dev == 0:
            # A perfectly constant series has no scale to measure against, but
            # any departure from it is maximally unusual — returning None here
            # would silently miss the most obvious outlier there is.
            if value == centre:
                return 0.0
            return float("inf") if value > centre else float("-inf")
        return (value - centre) / mean_dev
    return MAD_TO_SIGMA * (value - centre) / mad


def _anomaly_id(kind, entity_id, metric):
    return f"a_{kind}_{_short_hash(entity_id)}_{metric}"


def detect_outliers(series_by_entity, metric, entity_type, threshold=ROBUST_Z_THRESHOLD):
    """Flag the most recent point of each series when it is a robust outlier."""
    found = []
    for entity_id, series in series_by_entity.items():
        values = list(series.values())
        if len(values) < MIN_SERIES_FOR_OUTLIER + 1:
            continue
        current, history = values[-1], values[:-1]
        score = robust_z(current, history)
        if score is None or abs(score) < threshold:
            continue
        direction = "above" if score > 0 else "below"
        found.append(Anomaly(
            id=_anomaly_id("outlier", entity_id, metric),
            anomaly_class=PERFORMANCE_ANOMALY,
            entity_id=entity_id, entity_type=entity_type, metric=metric,
            method="robust_z(median/MAD)", score=round(score, 2),
            description=(
                f"{metric} for {entity_id} is {abs(score):.1f} robust deviations "
                f"{direction} its trailing median ({current:g} vs {median(history):g})."
            ),
        ))
    return found


def detect_collapse_to_zero(series_by_entity, metric, entity_type, min_history=MIN_SERIES_FOR_OUTLIER):
    """A consistently non-zero metric hitting zero.

    Treated as suspected collection failure rather than a performance finding:
    "the site got no traffic" and "we stopped recording traffic" look identical
    in the data, and only one of them is a marketing problem.
    """
    found = []
    for entity_id, series in series_by_entity.items():
        values = list(series.values())
        if len(values) < min_history + 1:
            continue
        current, history = values[-1], values[:-1]
        if current == 0 and all(v > 0 for v in history):
            found.append(Anomaly(
                id=_anomaly_id("collapse", entity_id, metric),
                anomaly_class=INSTRUMENTATION_ANOMALY,
                entity_id=entity_id, entity_type=entity_type, metric=metric,
                method="collapse_to_zero", score=0.0,
                description=(
                    f"{metric} for {entity_id} dropped to zero after "
                    f"{len(history)} consecutive non-zero day(s). Suspected "
                    "collection failure until confirmed otherwise."
                ),
                suppresses=(entity_id,),
            ))
    return found


def detect_source_divergence(ga4_sessions, clarity_sessions, entity_id="site"):
    """GA4 recording traffic while Clarity records none, or vice versa.

    Suggests one tracking script stopped firing — not that traffic vanished.
    """
    if ga4_sessions is None or clarity_sessions is None:
        return []
    if ga4_sessions > 0 and clarity_sessions == 0:
        missing, present = "Clarity", "GA4"
    elif clarity_sessions > 0 and ga4_sessions == 0:
        missing, present = "GA4", "Clarity"
    else:
        return []
    return [Anomaly(
        id=_anomaly_id("divergence", entity_id, "sessions"),
        anomaly_class=INSTRUMENTATION_ANOMALY,
        entity_id=entity_id, entity_type="site", metric="sessions",
        method="source_divergence", score=None,
        description=(
            f"{present} recorded sessions for this period while {missing} recorded "
            f"none. Suspected {missing} tracking failure; treat both sources' "
            "figures as unreliable until resolved."
        ),
        suppresses=(entity_id,),
    )]


def detect_bot_share_anomaly(bot_share_now, bot_share_prior=None, entity_id="site"):
    """A bot-share level or shift that makes traffic figures unreadable."""
    if bot_share_now is None:
        return []
    found = []
    if bot_share_now >= BOT_SHARE_CRITICAL:
        found.append(Anomaly(
            id=_anomaly_id("botshare", entity_id, "clarity_bot_share"),
            anomaly_class=INSTRUMENTATION_ANOMALY,
            entity_id=entity_id, entity_type="site", metric="clarity_bot_share",
            method="bot_share_level", score=round(bot_share_now, 3),
            description=(
                f"{bot_share_now:.0%} of Clarity sessions are bots. Total session "
                "counts are not a usable proxy for human traffic in this period."
            ),
            suppresses=(entity_id,),
        ))
    elif bot_share_prior is not None and abs(bot_share_now - bot_share_prior) >= BOT_SHARE_SHIFT:
        direction = "rose" if bot_share_now > bot_share_prior else "fell"
        found.append(Anomaly(
            id=_anomaly_id("botshift", entity_id, "clarity_bot_share"),
            anomaly_class=INSTRUMENTATION_ANOMALY,
            entity_id=entity_id, entity_type="site", metric="clarity_bot_share",
            method="bot_share_shift",
            score=round(bot_share_now - bot_share_prior, 3),
            description=(
                f"Bot share {direction} from {bot_share_prior:.0%} to {bot_share_now:.0%}. "
                "A change in total sessions this period may reflect bot volume "
                "rather than real traffic."
            ),
            suppresses=(entity_id,),
        ))
    return found


def detect_script_error_spike(rate_now, rate_prior=None, entity_id="site"):
    """A jump in Clarity script errors — a deploy-regression candidate."""
    if rate_now is None or rate_now < SCRIPT_ERROR_SPIKE:
        return []
    if rate_prior is not None and rate_now - rate_prior < SCRIPT_ERROR_SPIKE:
        return []
    prior_text = f" (from {rate_prior:.1%})" if rate_prior is not None else ""
    return [Anomaly(
        id=_anomaly_id("scripterror", entity_id, "clarity_script_error_rate"),
        anomaly_class=INSTRUMENTATION_ANOMALY,
        entity_id=entity_id, entity_type="site", metric="clarity_script_error_rate",
        method="script_error_spike", score=round(rate_now, 3),
        description=(
            f"Script errors affect {rate_now:.1%} of Clarity sessions{prior_text}. "
            "Check recent deploys: broken JavaScript can distort every other "
            "behavioural metric on the page."
        ),
        suppresses=(entity_id,),
    )]


def suppressed_entities(anomaly_list):
    """Every entity an instrumentation anomaly says we cannot trust."""
    suppressed = set()
    for anomaly in anomaly_list:
        if anomaly.is_instrumentation:
            suppressed.update(anomaly.suppresses or (anomaly.entity_id,))
    return suppressed


def is_suppressed(entity_id, anomaly_list):
    """Site-level suppression covers everything: if the site's measurement is
    broken, no page beneath it can be trusted either."""
    suppressed = suppressed_entities(anomaly_list)
    return entity_id in suppressed or "site" in suppressed
