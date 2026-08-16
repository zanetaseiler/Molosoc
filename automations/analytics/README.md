# Analytics connection tests (read-only)

Verifies that Molosoc's three analytics sources can be authenticated and read.
Nothing here writes to any of them.

| Source | API | Credential | Calls per run |
|---|---|---|---|
| GA4 (property `521643495`) | Google Analytics Data API v1beta | `GOOGLE_SERVICE_ACCOUNT_JSON` | `runReport` × 2 |
| Search Console (`sc-domain:molosoc.com`) | Search Console API v3 | `GOOGLE_SERVICE_ACCOUNT_JSON` | `sites.list`, `searchAnalytics.query` × 3 |
| Microsoft Clarity | Project Live Insights API | `CLARITY_API_TOKEN` | **exactly 1 GET** |

Google credentials are requested with `analytics.readonly` and
`webmasters.readonly` scopes and every endpoint used is a read endpoint. The
Clarity Data Export API has no write operation at all.

## Layout

- `analytics_common.py` — shared helpers: secret redaction, number coercion,
  date windows. Every source uses the same ones so they behave identically.
- `google_connection_test.py` — GA4 + Search Console.
- `clarity_connection_test.py` — Microsoft Clarity.
- `test_*.py` — offline tests for each of the above.

## Clarity's rate limit — read before editing

**Clarity allows 10 API calls per project per day**, shared across everything
that reads the project. `clarity_connection_test.py` therefore makes **exactly
one** call per run, never retries a failure, and never loops on an empty
response. `test_clarity_connection_test.py` asserts the call count directly, so
an accidental second request fails the suite rather than silently eating the
budget.

The CI workflow enforces the same discipline: the Google checks run on every
push to this folder, but the live Clarity call runs **only** on a manual
dispatch or on a push whose commit message contains `[clarity]`.

## What each test reports

**GA4** — last 7 full days (ending yesterday): users (`activeUsers`), sessions,
views (`screenPageViews`), and the top 5 landing pages by sessions.

**Search Console** — 7 days ending 3 days ago: clicks, impressions, CTR, average
position, plus the top 5 queries and top 5 pages. The 3-day offset is Search
Console's data-finalisation lag; a window ending today is normally empty and
would look like a broken connection.

**Clarity** — the last 3 days (the endpoint's maximum) of live insights:
whichever behavioural metrics the project returns — traffic, engagement time,
scroll depth, rage clicks, dead clicks, quick backs, script errors. The output
is rendered from whatever comes back rather than from a hard-coded metric list,
because the metric set varies by project and the call budget leaves no room for
a second attempt.

An authenticated source with zero rows is reported as a **pass** with an
explicit "no data yet" note — only auth, permission, rate-limit and
malformed-response failures exit non-zero.

## Running

In CI: the **Analytics Connection Test (read-only)** workflow. Dispatch it
manually (with `run_clarity` ticked to include the live Clarity call), or push
to this folder — pushes run the Google checks and the unit tests, and add
`[clarity]` to the commit message when you also want the Clarity call.

Locally:

```bash
pip install -r automations/analytics/requirements.txt

# Google — either the JSON itself (raw or base64) ...
export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat ~/molosoc-analytics-key.json)"
# ... or a path to the key file
export GOOGLE_APPLICATION_CREDENTIALS=~/molosoc-analytics-key.json
python3 automations/analytics/google_connection_test.py

# Clarity — one call, mind the daily budget
export CLARITY_API_TOKEN='...'
python3 automations/analytics/clarity_connection_test.py
```

Flags — Google: `--days N`, `--property-id`, `--site-url`, `--skip-ga4`,
`--skip-search-console`. Clarity: `--num-days {1,2,3}`, `--dimension NAME`
(repeatable up to 3; one of `Browser`, `Device`, `Country`, `OS`, `Source`,
`Medium`, `Campaign`, `Channel`, `URL`). Dimensions do not cost extra calls, but
an unrecognised value makes Clarity return an empty body — the script validates
locally first so a typo does not spend one of the ten.

Never commit a key file or token. `.gitignore` already excludes `.env`, `*.env`
and `secrets/`; keep local credentials outside the repo.

## Credential hygiene

No credential is ever printed. The Google service account JSON is parsed in
memory and the run header shows only a masked identity
(`mo***@project.iam.gserviceaccount.com`). The Clarity token is registered with
the shared redactor the moment it is read, and is sent only in an
`Authorization` header — never in a URL or query string.

All error text passes through `redact()`, which strips PEM private-key blocks,
secret-looking JSON fields (`private_key`, `client_secret`, `token`, `api_key`),
`Bearer` tokens, and any literal secret registered at runtime. That last part is
what catches an API echoing the token back inside an error body. Tests assert
this directly, including that a malformed-key error never quotes the payload and
that a 400 response containing the token is scrubbed before printing.

## Tests

```bash
pip install -r automations/analytics/requirements.txt pytest
python3 -m pytest automations/analytics/ -q
```

64 tests, fully offline against stubbed API clients — no credentials, no
network, and no Clarity calls. They cover credential loading and its failure
modes, redaction, date windows including the Search Console lag, response
parsing for all three APIs (empty-property, permission-denied, rate-limited and
malformed-shape cases included), and the assertions that only read calls are
issued and that Clarity is called exactly once.

---

# Phase 1 — historical collection foundation

The connection tests above prove the three sources can be read. Phase 1 adds
the collection and data-quality layer underneath them. It collects and
normalizes; it does not analyse, compare, recommend, or report.

## Why Clarity needs a collector and the Google sources do not

GA4 and Search Console can reconstruct any past period on demand, so their
history needs no daily job — `normalize.py` simply reshapes their existing
verified output into the shared schema when it is needed.

Clarity cannot. Its Live Insights endpoint returns at most three days, so any
day not captured is gone permanently. `clarity_daily_collect.py` exists solely
to make sure that does not happen.

## How Clarity daily history is collected

```bash
export CLARITY_API_TOKEN='...'
python3 automations/analytics/clarity_daily_collect.py --store-root ./analytics-data

# check coverage and today's budget without calling the API
python3 automations/analytics/clarity_daily_collect.py --status
```

**One call per run, one bucket per UTC day.** `numOfDays=1` means "the trailing
24 hours", not "the calendar day", which has two consequences the collector
enforces:

- Snapshots are **always** `numOfDays=1`. It is a constant, not a flag.
  Consecutive 2- or 3-day windows overlap, so summing them double-counts.
- **At most one daily bucket per UTC date.** A second run the same day would
  cover an overlapping window, so it is refused before any call is spent.
  `--force` stores it as an extra raw revision that never becomes a bucket.

Two independent guards back this up: `records.sum_metric()` refuses to
aggregate anything with `window_days > 1`, refuses to mix performance with
data-quality metrics, and refuses duplicate date/entity/metric rows — so even a
hand-written aggregation cannot double-count.

Budget is reserved from a persisted per-UTC-day ledger *before* the call, so a
crash loses the budget rather than the limit. The automated cap (3) sits below
Clarity's hard limit (10) so a human can still investigate on a day the
collector has run.

Each run stores three things: the raw payload (so a normalization bug is
fixable later without re-querying data that no longer exists), the normalized
production-only records, and the excluded rows plus quality flags.

## How URLs are canonicalized

`canonical_url.py`. GA4 reports paths, Search Console reports absolute URLs,
Clarity reports whatever the browser saw — without one identity, nothing joins.

Applied in order: lowercase scheme and host, `http`→`https`, `www.` folded into
the apex, default ports and fragments dropped, duplicate slashes collapsed,
trailing slash added for directory-style paths (but not for `robots.txt`-style
file paths), bare paths given the site origin, remaining query parameters
sorted for a stable identity.

Tracking parameters are removed by **denylist**: `utm_*` and the `pk_`/`mtm_`/
`hsa_` families by prefix, plus exact matches for `fbclid`, `gclid`, `gbraid`,
`wbraid`, `msclkid`, `dclid`, `ttclid`, `twclid`, `srsltid`, `mc_cid`, `mc_eid`,
`_ga`, `_gl` and others. Everything unknown is **kept** — dropping a parameter
that genuinely identifies content (`?lang=cs` under Polylang, a product
variation, an on-site search term) silently fuses two pages into one, which is
invisible; keeping one splits a page in two, which is obvious. Dropped
parameters are recorded on the record, never silently discarded.

This was not theoretical: GA4's first verified run split the homepage across
`/` and two `?fbclid=…` variants. Those three rows now resolve to one page.

## How staging and other non-production traffic is excluded

Host classification is separate from canonicalization — a staging URL still
canonicalizes correctly, it is simply labelled. Hosts resolve to one of three
states: `production` (`molosoc.com`, `www.molosoc.com`), `non_production`
(`staging.molosoc.com`, plus `dev.`/`test.`/`preview.`/`uat.`/`stage.` prefixes
and `.local`/`.test` suffixes), or `unknown`.

`quality.split_production()` removes non-production **page** records; site
totals and non-page dimensions pass through. Unknown hosts are excluded by
default — a host nobody has classified should surface for a decision rather
than quietly count.

Exclusions are always reported. `quality.exclusion_flags()` turns them into a
counted finding with a per-host breakdown, because "the number dropped" and "we
stopped counting some rows" otherwise look identical.

**Nothing here touches WordPress.** This is an analytics-layer filter only; no
staging or production configuration is changed.

## How bot and data-quality metrics are handled

Data-quality metrics live in a different class from performance metrics
(`metric_class` on every record) and `sum_metric()` refuses to mix them.

From Clarity's `Traffic` metric the collector derives four records:
`clarity_sessions` (performance, includes bots), `clarity_bot_sessions` and
`clarity_bot_share` (both data quality), and `clarity_human_sessions`
(performance) — the last is what a traffic trend should read.

`quality.assess_bot_share()` flags each snapshot: normal below 30%, `warn` at
30–50%, `critical` above 50% (where total sessions stop being a usable proxy
for human traffic). Below 20 sessions it returns "not assessable" rather than a
verdict on noise. The first verified run sat at 40% — a `warn`.

Clarity's `ScriptErrorCount` is classified as data quality rather than
behaviour: a script-error spike means measurement may be broken, which is a
different kind of problem from a UX one.

## Storage

`storage.py` defines one interface (`SnapshotStore`) with three backends:

| Backend | Durable | Use |
|---|---|---|
| `GCSStore` (`storage_gcs.py`) | yes | Production historical store |
| `LocalFileStore` | no | Development, workstation runs |
| `InMemoryStore` | no | Tests |

Layout is identical across all three, so a local store can be copied into the
bucket without translation:

```
raw/{source}/{date}/{collected_at}.json     one object per collection
facts/{source}/{date}.json                  normalized records
facts/{source}/{date}.quality.json          flags and excluded rows
state/clarity_call_budget/{date}.json       per-UTC-day call ledger
```

Raw payloads are kept separate from normalized records deliberately: if
normalization has a bug, the facts layer can be rebuilt from raw — and for
Clarity there is no other way, because the API cannot return the day again.

**Nothing overwrites an authoritative snapshot silently.** Creates go out with
`if_generation_match=0`, GCS's atomic create-if-absent, so the write fails
server-side if the object already exists — even under a race between two
collectors. Overwriting requires an explicit `overwrite=True`, used only for
derived facts. Raw snapshots are keyed by collection instant, so a
re-collection is a new object and the precondition never even fires.

`store_from_env()` raises rather than falling back to a local store when the
bucket is unconfigured: a silent downgrade would report success and preserve
nothing.

### Storage credentials

A **separate identity** from the read-only GA4/Search Console service account,
which stays read-only. The writer key is read from `ANALYTICS_STORAGE_SA_JSON`
(raw or base64), parsed in memory, registered with the redactor, and never
logged. When the variable is absent the client falls back to Application
Default Credentials, so Workload Identity works without a code change.

Required permissions are exactly three — `storage.objects.create`, `.get`,
`.list`. No delete, no admin. A test asserts the list stays that narrow.

`analytics-data/` is gitignored. Git is deliberately not the analytics
database.

## Language and conversions

Every **page** record carries `language` and `language_source`. The site runs
Polylang with per-language slugs and no language path prefix — the Czech
product page and the English legal pages both sit at the root — so language is
detected in order of reliability: path prefix (`/cs/`), then `?lang=`, then a
slug lexicon seeded from the theme's own links. Anything else is `und`
(undetermined), which is a legitimate answer rather than a guess, and every
record keeps its full `path` so language can be back-filled later without
re-collecting.

Reporting is **not** split by language yet — current volume does not justify it
— but the history supports it when it does.

Conversion events, when GA4 reports them: `purchase` is the headline business
conversion, with `begin_checkout` and `add_to_cart` as supporting funnel steps.
Each is its own metric (`ga4_key_event_purchase`, …) with site sessions as its
`sample_basis`, never a single blended "conversions" figure.

## What Phase 1 does not include

No Marketing Analysis Agent, no recurring report, no report frequency, no
scheduling or cron, no LLM-generated recommendations, no dashboards, no SEO or
content changes, and no staging de-indexing. The collector has no automated
trigger: wiring it to CI requires the durable-storage decision first.

---

# Phase 2 — Marketing Analysis Agent

Answers one question from the Phase 1 history: **what changed, why does it
matter, and what should we adjust next?**

Analysis only. It reads the durable store, calls no API, and changes nothing —
not the site, not GA4, not Search Console, not Clarity, not WordPress. No
recommendation is ever applied anywhere, and there is no report schedule.

Running it costs **zero** Clarity API calls: Clarity comes from the ledger, not
from fresh overlapping API windows.

## Modules

| Module | Responsibility |
|---|---|
| `analysis_model.py` | Fact / Inference / Anomaly / Recommendation / Report schema and its invariants |
| `periods.py` | Comparison windows, anchored to Search Console's 3-day lag; ledger coverage |
| `thresholds.py` | Eligibility, significance, and the site readiness gate |
| `history.py` | Loading and aggregating stored records (counts sum, rates recompute, positions weight) |
| `anomalies.py` | Performance vs instrumentation anomaly detection |
| `signals.py` | The six named cross-source signals |
| `recommend.py` | Signal → recommendation, priority rubric, measurement plans |
| `tracking.py` | Recommendation ledger and outcome classification |
| `analysis.py` | Orchestrator: builds facts, runs signals, assembles the report |
| `render.py` | Human-readable Markdown renderer |
| `analyze_cli.py` | Manual entry point (no schedule) |
| `fixtures.py` | Deterministic scenarios: low volume, healthy, broken instrumentation |

## Facts and inferences stay separate

Structurally, not by convention. An `Inference` cannot be constructed without
referencing the fact ids it rests on, must carry at least one alternative
explanation, holds `causal_claim=False` as an invariant, and is **rejected at
construction** if its statement uses causal language ("caused", "led to",
"because of"). A sentence that asserts causation from this data is
unfalsifiable, and the cheapest place to stop it is before it exists.

## The readiness gate

Below 100 sessions in the period the agent reports every fact it measured and
says **`insufficient data for recommendation`**, issuing nothing above Monitor.
At Molosoc's current volume that is the expected state, and it is the correct
one — a report that manufactures advice from four clicks is worse than one that
says it cannot tell yet.

Three gates stand between a signal and an action: the site readiness gate,
instrumentation suppression, and per-entity eligibility plus significance.

## Signals

`demand_up_capture_down`, `capture_up_satisfaction_down`,
`friction_against_intent`, `hidden_gem`, `threshold_proximity`,
`source_disagreement`. Each is a named rule with declared inputs that either
fires or does not. `source_disagreement` never becomes an action — it is a
reason *not* to act.

## Running it

```bash
# deterministic fixture — no storage, no credentials
python3 automations/analytics/analyze_cli.py --fixture healthy
python3 automations/analytics/analyze_cli.py --fixture low_volume

# against the durable store
export ANALYTICS_BUCKET=molosoc-analytics-history
export ANALYTICS_STORAGE_SA_JSON='...'
python3 automations/analytics/analyze_cli.py --format both --out analysis.md
```

`--update-ledger` is off by default: analysing is read-only, and writing the
recommendation ledger is an explicit choice.

## Not included

No report schedule, no frequency decision, no email or delivery, no dashboard,
no LLM-generated recommendations, and no automatic application of any
recommendation. Staging remediation remains a separate task.

---

# Weekly marketing analysis report

One Markdown report per week, uploaded as a GitHub Actions artifact. Nothing is
delivered anywhere else — no email, no Slack, no dashboard — and nothing is
committed back to the repository.

## Schedule

`.github/workflows/weekly-marketing-report.yml`, **Wednesdays 06:15 UTC**
(`15 6 * * 3`), plus `workflow_dispatch` for a manual run or a re-run of a past
week via the `today` input.

Wednesday is not arbitrary. Search Console finalises on a ~3-day lag, so the
analysis anchor is `today - 3`. A Wednesday run puts that anchor on a Sunday,
which makes the analysed period the previous **Monday-to-Sunday** week and the
comparison the Monday-to-Sunday week before it. Whole calendar weeks compare
like with like; a mid-week boundary would split weekend traffic across both
windows. 06:15 UTC sits ~4 hours after the daily Clarity collector (02:20 UTC)
so the two never contend, is off the hour to avoid scheduler congestion, and
lands early morning in Prague.

## Zero Clarity API calls

The daily collector owns Clarity's 10-calls-per-day budget, and a missed day of
Clarity history **cannot be backfilled**. A report that spent from that budget
could permanently cost real data. So the report reads Clarity from the durable
ledger only, and `test_weekly_report.py` makes any live Clarity call raise —
completing the run is the proof.

GA4 and Search Console are hydrated read-only for exactly the two compared
windows: four API calls, cached so a window is never fetched twice.

## Tracking coverage diagnostic

`coverage.py` compares GA4 sessions against Clarity bot-adjusted sessions for
the same period. It is reported as a **coverage indicator and explicitly not a
consent rate** — the ratio is moved by differing session definitions, Clarity's
own bot estimation and sampling, script placement, ad blockers, and separate
consent gating, none of which this number can distinguish. Every result carries
those caveats, and the ratio is suppressed below 30 sessions on either side.

## Low volume

Thresholds are unchanged. Below them the report states **`insufficient data for
recommendation`**, reports every fact and trend it measured, and proposes
nothing above Monitor.

## Running it manually

```bash
# live
export ANALYTICS_BUCKET=molosoc-analytics-history
export ANALYTICS_STORAGE_SA_JSON='...'
export GOOGLE_SERVICE_ACCOUNT_JSON='...'
python3 automations/analytics/weekly_report.py --out-dir reports --also-json

# deterministic fixture, no credentials or storage
python3 automations/analytics/weekly_report.py --fixture low_volume --out-dir /tmp
```

`reports/` is gitignored: the report is a build output, never a commit.
