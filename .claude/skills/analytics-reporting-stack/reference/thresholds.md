# Thresholds reference

Companion to `SKILL.md` §7. These are the default values. They are
conservative on purpose.

Two independent questions, deliberately kept separate:

- **eligibility** — does this entity have enough volume to be analysed at all?
- **significance** — is the observed change distinguishable from noise?

An entity must pass **both** before it can produce an actionable
recommendation. Passing eligibility but failing significance is not nothing —
it is exactly what the `Monitor` priority is for.

## Eligibility minimums

| Constant | Default | Gates |
|---|---:|---|
| `MIN_QUERY_IMPRESSIONS` | 50 | CTR / position analysis, **both** periods |
| `MIN_QUERY_CLICKS_PRIOR` | 10 | before "losing clicks" is meaningful |
| `MIN_PAGE_SESSIONS` | 30 | GA4 page-level engagement, both periods |
| `MIN_PAGE_SESSIONS_CLARITY` | 30 | before quoting a page friction rate |
| `MIN_SESSIONS_FOR_CONVERSION` | 100 | conversion-rate statements |
| `MIN_IMPRESSIONS_FOR_POSITION` | 100 | average-position statements |

## Site-level readiness

| Constant | Default | Effect |
|---|---:|---|
| `LOW_VOLUME_SESSIONS` | 100 | below this the site is flagged low-volume |
| `MIN_SITE_SESSIONS_FOR_RECOMMENDATIONS` | 100 | below this **all** recommendations are withheld |

Below the readiness floor the report emits facts and declines to advise,
`readiness = insufficient_data`. This is a successful run: exit 0, no alert.

## Significance

Relative change alone never triggers a finding — 1 click becoming 3 is +200%
and means nothing. **Both** gates must pass.

| Constant | Default |
|---|---:|
| `MIN_RELATIVE_CHANGE` | 0.20 |
| `MIN_POSITION_CHANGE` | 1.0 |
| `Z_CRITICAL_95` | 1.96 |

Per-metric absolute minimums (`MIN_ABSOLUTE_CHANGE`):

| Metric | Minimum |
|---|---:|
| `gsc_clicks` | 5 |
| `gsc_impressions` | 50 |
| `ga4_sessions` | 20 |
| `ga4_users` | 15 |
| `ga4_views` | 25 |
| `clarity_sessions` | 20 |
| `clarity_human_sessions` | 20 |
| *(default for anything else)* | 10 |

Rate changes (CTR, engagement, conversion) use a two-proportion z-test at 95%
rather than a flat percentage. Clamp impossible inputs — an upstream row can
report more clicks than impressions, and a proportion above 1 makes the pooled
variance negative. One malformed row must not kill a whole analysis.

## Opportunity thresholds

| Constant | Default | Meaning |
|---|---:|---|
| `WEAK_CTR_MAX` | 0.02 | impressions without clicks to match |
| `STRONG_IMPRESSIONS_MIN` | 100 | enough visibility to be worth acting on |
| `THRESHOLD_PROXIMITY_RANGE` | (8.0, 20.0) | realistic push to page one / top three |
| `WEAK_ENGAGEMENT_MAX` | 0.35 | |
| `STRONG_ENGAGEMENT_MIN` | 0.60 | |
| `LOW_VISIBILITY_IMPRESSIONS` | 50 | |
| `FRICTION_RATE_WARN` | 0.05 | rage/dead click rate worth naming |

## Tracking-coverage diagnostic

Compares GA4 sessions against bot-adjusted Clarity sessions for the same
window.

| Constant | Default |
|---|---:|
| `MIN_SESSIONS_FOR_COVERAGE` | 30 |
| `ALIGNED_BAND` | 0.80 – 1.20 |
| `MATERIALLY_LOWER` | 0.60 |

States: `aligned`, `ga4_lower`, `ga4_higher`, `insufficient_data`,
`unavailable`.

**This ratio is a coverage indicator, not a consent rate.** Deriving a consent
percentage from it would be a precise-sounding number nobody could defend.
Always ship the caveats: the two tools define a session differently; Clarity's
bot detection is an estimate; consent tooling, ad blockers and script
placement can each affect one tool without the other.

## Metrics where lower is better

Direction must be judged by outcome, not sign. For these, a decrease is an
improvement and must render as positive:

`gsc_position`, `clarity_bot_share`, `clarity_rage_click_rate`,
`clarity_dead_click_rate`, `clarity_quickback_rate`,
`clarity_script_error_rate`

## Tuning policy

- **Raising** a threshold is always safe.
- **Lowering** one requires a written reason in the commit, and should be
  driven by the client's actual volume, never by a report looking empty.
- At genuinely low volume almost nothing clears these gates. That is the
  correct behaviour: a report that manufactures advice from four clicks is
  worse than one that says it cannot tell yet.
- Never lower a threshold to make a dashboard look busier. The dashboard
  renders what the engine decided (`SKILL.md` §9).
