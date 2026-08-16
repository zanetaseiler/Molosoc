#!/usr/bin/env python3
"""
Tracking-coverage diagnostic: GA4 sessions against Clarity human sessions.

WPConsent gates analytics scripts on molosoc.com, so GA4 records only what
consenting visitors allow. Clarity is subject to its own consent handling and
its own definition of a session. Comparing the two over the same window says
something useful about measurement coverage.

WHAT THIS IS NOT

It is **not a consent rate**, and this module will not call it one. The ratio
between the two numbers is moved by at least six things besides consent:

  * GA4 and Clarity define a session differently (timeout, campaign restart).
  * Clarity's totals include bots; the bot-adjusted figure used here is
    Clarity's own estimate, not ground truth.
  * The two scripts can load at different points in the page lifecycle, so a
    fast bounce may register in one and not the other.
  * Either script can be blocked independently by an ad blocker.
  * Consent tooling can gate the two tags separately.
  * Clarity applies its own sampling on higher-traffic projects.

So the output is a coverage indicator with the ratio stated plainly and its
limits attached. Calling it a consent rate would be a precise-sounding number
that nobody could defend, which is worse than an honest range.
"""

COVERAGE_ALIGNED = "aligned"
COVERAGE_GA4_LOWER = "ga4_lower"
COVERAGE_GA4_HIGHER = "ga4_higher"
COVERAGE_INSUFFICIENT = "insufficient_data"
COVERAGE_UNAVAILABLE = "unavailable"

# Below this many sessions on either side the ratio is noise.
MIN_SESSIONS_FOR_COVERAGE = 30

# The two tools never agree exactly. Within this band, treat them as aligned.
ALIGNED_BAND = (0.80, 1.20)

# Below this, GA4 is capturing materially less than Clarity — worth explaining.
MATERIALLY_LOWER = 0.60

CAVEATS = (
    "GA4 and Clarity define a session differently, so exact agreement is not "
    "expected even with perfect tracking.",
    "The Clarity figure is bot-adjusted using Clarity's own bot detection, "
    "which is an estimate rather than ground truth.",
    "Consent tooling, ad blockers and script placement can each affect one "
    "tool without affecting the other.",
    "This ratio is a coverage indicator, not a consent rate. Deriving a "
    "consent percentage from it would overstate what the data supports.",
)


def assess_tracking_coverage(ga4_sessions, clarity_human_sessions,
                             clarity_total_sessions=None):
    """Compare the two session counts for one window.

    Returns a diagnostic dict. Never asserts causation, and never labels the
    result a consent rate.
    """
    if ga4_sessions is None or clarity_human_sessions is None:
        return {
            "state": COVERAGE_UNAVAILABLE,
            "ga4_sessions": ga4_sessions,
            "clarity_human_sessions": clarity_human_sessions,
            "clarity_total_sessions": clarity_total_sessions,
            "ratio": None,
            "headline": "Tracking coverage could not be compared — one source "
                        "reported no session data for this period.",
            "caveats": list(CAVEATS),
        }

    smaller = min(ga4_sessions, clarity_human_sessions)
    ratio = (ga4_sessions / clarity_human_sessions) if clarity_human_sessions else None

    base = (f"GA4 recorded {ga4_sessions:,.0f} sessions; Clarity recorded "
            f"{clarity_human_sessions:,.0f} bot-adjusted sessions")
    if clarity_total_sessions:
        base += f" (of {clarity_total_sessions:,.0f} total including bots)"
    base += "."

    if smaller < MIN_SESSIONS_FOR_COVERAGE:
        return {
            "state": COVERAGE_INSUFFICIENT,
            "ga4_sessions": ga4_sessions,
            "clarity_human_sessions": clarity_human_sessions,
            "clarity_total_sessions": clarity_total_sessions,
            "ratio": round(ratio, 3) if ratio is not None else None,
            "headline": (
                f"{base} Too few sessions on at least one side (minimum "
                f"{MIN_SESSIONS_FOR_COVERAGE}) for the ratio to mean anything — "
                "reported for visibility only."
            ),
            "caveats": list(CAVEATS),
        }

    if ratio is None:
        state = COVERAGE_UNAVAILABLE
        headline = base
    elif ALIGNED_BAND[0] <= ratio <= ALIGNED_BAND[1]:
        state = COVERAGE_ALIGNED
        headline = (f"{base} The two sources are within "
                    f"{ALIGNED_BAND[0]:.0%}–{ALIGNED_BAND[1]:.0%} of each other "
                    f"(ratio {ratio:.2f}), which is normal agreement.")
    elif ratio < ALIGNED_BAND[0]:
        severity = "materially " if ratio < MATERIALLY_LOWER else ""
        state = COVERAGE_GA4_LOWER
        headline = (
            f"{base} GA4 is capturing {severity}less than Clarity "
            f"(ratio {ratio:.2f}). Consent gating, ad blockers or tag placement "
            "could each contribute; this figure alone does not distinguish them."
        )
    else:
        state = COVERAGE_GA4_HIGHER
        headline = (
            f"{base} GA4 is recording more sessions than Clarity "
            f"(ratio {ratio:.2f}), which usually points at differing session "
            "definitions or Clarity sampling rather than a GA4 problem."
        )

    return {
        "state": state,
        "ga4_sessions": ga4_sessions,
        "clarity_human_sessions": clarity_human_sessions,
        "clarity_total_sessions": clarity_total_sessions,
        "ratio": round(ratio, 3) if ratio is not None else None,
        "headline": headline,
        "caveats": list(CAVEATS),
    }


def coverage_from_facts(index, site_entity="site"):
    """Build the diagnostic from an analysis FactIndex."""
    return assess_tracking_coverage(
        index.value(site_entity, "ga4_sessions"),
        index.value(site_entity, "clarity_human_sessions"),
        index.value(site_entity, "clarity_sessions"),
    )
