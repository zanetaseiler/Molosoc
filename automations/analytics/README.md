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

---

# Phase 3, Stage 1 — Durable report storage

GitHub artifacts expire after 90 days and need a human with repository access
and a short-lived signed URL. That is a good download path and a poor
foundation for an agent. Every successful weekly report is therefore also
written to the existing private bucket, `gs://molosoc-analytics-history`, and
that copy is the machine-readable source of truth.

The artifact is unchanged: still uploaded, still 90 days.

## Canonical paths

Bucket: **`gs://molosoc-analytics-history`** (private, unchanged).

| Path | Mutability | Retention |
| --- | --- | --- |
| `reports/weekly/latest.json` | overwritten weekly | **indefinite** |
| `reports/weekly/index.json` | overwritten weekly | **indefinite** |
| `reports/weekly/data/YYYY/MM/YYYY-MM-DD/report.json` | write-once | 400 days (intended) |
| `reports/weekly/data/YYYY/MM/YYYY-MM-DD/report.md` | write-once | 400 days (intended) |
| `reports/weekly/data/YYYY/MM/YYYY-MM-DD/revisions/<stamp>/report.json` | write-once | 400 days (intended) |
| `reports/weekly/data/YYYY/MM/YYYY-MM-DD/revisions/<stamp>/report.md` | write-once | 400 days (intended) |

`YYYY-MM-DD` is the report date — the last day of the analysed week — and it
appears in the path exactly once as a directory. `<stamp>` is the generation
instant as `YYYYMMDDTHHMMSSZ`.

Those six lines are the whole contract. **`reports/weekly/latest.json` and
`reports/weekly/index.json` are the only objects this system ever overwrites**
(`report_store.MUTABLE_KEYS`), and everything under `reports/weekly/data/` is
written once and never modified.

The `data/` segment exists for retention isolation. A GCS lifecycle condition
can match a prefix but cannot express an exclusion, so a rule that expired
`reports/weekly/` would take the pointer and the index with it. Giving the
expiring reports their own prefix makes the eventual rule one safe line, and
keeps the two permanent metadata objects structurally out of its reach.

Untouched by this stage, listed so the bucket layout is readable in one place:
`raw/`, `facts/` and `state/` hold the Clarity ledger from Phase 1, and
`_verification/` holds synthetic connection-test objects.

## Reading it

```python
import report_store as rs

pointer = rs.load_latest(store)          # reports/weekly/latest.json
report  = store.get_json(pointer["json_key"])
markdown = store.get_text(pointer["markdown_key"])

rs.load_index(store)                     # every published week, newest first
rs.load_report(store, "2026-08-14")      # one named week
rs.published_dates(store)                # authoritative, straight from listing
```

A consumer needs one GET to find the newest report and one more to read it. No
bucket listing, no Actions API, no repository access.

## Schema

`schema_version` is semver. Additive fields bump the minor; anything a reader
could break on bumps the major. **A consumer should refuse a major it does not
know** rather than guess.

Current version: **1.0.0**, `kind: molosoc.weekly_marketing_analysis`.

| Field | What it holds |
| --- | --- |
| `schema_version`, `kind` | Envelope identity |
| `report_date`, `generated_at`, `report_id` | Identity of this run |
| `period`, `comparison_period` | The two compared windows |
| `comparison_periods` | All windows, including the 28-day baseline |
| `facts` | Measured comparisons. Never opinions |
| `inferences` | Interpretations, each citing the fact ids beneath it |
| `anomalies` | Outliers, split into performance and instrumentation |
| `recommendations` | Proposed actions, each with a measurement plan |
| `prioritized_actions` | Recommendation ids in priority order |
| `readiness`, `readiness_note` | Whether advice was permitted at all |
| `findings` | Named views — see below |
| `headline_metrics` | Site-level totals, flat |
| `conversions` | Conversion measurement state |
| `ecommerce_tracking_boundary` | Which side of 2026-08-16 each window falls |
| `tracking_coverage` | GA4-vs-Clarity diagnostic. **Not a consent rate** |
| `data_quality` | Exclusions, hydration, suppressions, anomaly counts |
| `source_coverage` | What each source could actually cover |
| `storage` | Own keys, revision, and the declared retention intent |

`findings` names the views an agent will ask for — `ga4`, `search_console`,
`clarity`, `seo`, `landing_pages_and_cro`, `ux`, `cross_source`,
`executive_health`. Their values are **fact and inference ids**, not copies, so
a finding exists once in `facts`/`inferences` and two versions of it can never
drift apart. `sections` is the older internal view that `render.py` uses;
`findings` is the stable public one.

Facts and inferences remain separate types, and readiness thresholds are
unchanged from Phase 2.

## Duplicates and revisions

A published week is **never silently overwritten**. The weekly report is the
only record of what the site looked like that week, and once Search Console's
window rolls past it cannot be regenerated.

* Default (`--on-duplicate reject`): republishing a week raises
  `DuplicateReport` and writes nothing.
* `--on-duplicate revision`: the re-run is filed under
  `revisions/<YYYYMMDDTHHMMSSZ>/`, the authoritative `report.json` is untouched,
  and the index records how many revisions a week has.

`latest.json` never moves backwards: re-running an older week stores it without
disturbing the pointer.

## Write order

Markdown, then JSON, then — only once both are confirmed present — the index
and the pointer. A reader following `latest.json` cannot land on half a report;
the worst case is a pointer one week stale, which is visibly old rather than
quietly wrong. A failed report write leaves the pointer entirely alone.

## The narrow delete grant

`latest.json` and `index.json` are updated in place. **GCS implements replacing
an object as delete-then-create**, so overwriting needs `storage.objects.delete`
in addition to `storage.objects.create`. The analytics writer was scoped to
create/get/list, so out of the box it can store reports but cannot move the
pointer.

The grant is therefore **conditional and exact**, never blanket. The writer may
delete precisely two object names and nothing else:

```
resource.name == "projects/_/buckets/molosoc-analytics-history/objects/reports/weekly/latest.json" ||
resource.name == "projects/_/buckets/molosoc-analytics-history/objects/reports/weekly/index.json"
```

Equality, not `startsWith` — a prefix match on `reports/weekly/` would also
cover every dated report. With this condition the Clarity ledger, the raw
snapshots and every dated report stay undeletable by this identity, which is
the guarantee the whole Phase 1 design rests on.

`report_store.MUTABLE_KEYS` holds the same two keys, and a test asserts that
`publish()` and `rebuild_pointers()` never overwrite anything outside it — so
the code cannot quietly drift outside the grant and turn a design error into a
mysterious weekly failure.

Until the condition is in place, this degrades rather than losing anything:

* the immutable report objects are written and confirmed first;
* `publish()` returns `degraded=True` with the exact permission required;
* the CLI exits **2** — distinct from 1 (real failure) and 3 (duplicate);
* `rs.rebuild_pointers(store)` reconstructs both mutable objects from a
  listing afterwards, so a gap costs nothing but a stale pointer.

Note the gap only bites from the **second** week: creating `latest.json` the
first time needs no delete permission, because there is nothing to replace.

## Retention

Measured, uncompressed, per week: **~45 KB** at current volume (41 KB JSON +
4 KB Markdown), **~72 KB** for the busiest fixture.

| Horizon | At today's volume | At a 75 KB/week ceiling |
| --- | --- | --- |
| 3 months (13 weeks) | 0.6 MB | 1.0 MB |
| 12 months (52 weeks) | 2.4 MB | 3.8 MB |
| 3 years (157 weeks) | 7.1 MB | 11.5 MB |

At roughly $0.023/GB/month for standard storage, three years of reports costs
well under **$0.01 per year**. Storage cost is not a reason to delete anything
here; the reason to have a policy is predictability.

Agreed target: **400 days for dated weekly reports.** 400 rather than 365
because a 365-day rule deletes the week you need for a year-over-year
comparison days before you need it.

`latest.json` and `index.json` are **kept indefinitely**. Each index entry
carries the week's headline numbers, so trend continuity outlives the reports
it points at, at ~550 bytes per week (~29 KB a year).

**No lifecycle rule has been applied, and none is applied by this stage.**
Every document declares `retention.policy_applied: false`. The rule below is
documented for a later, separate decision — do not add it as a side effect of
some other change:

```jsonc
// Intended future rule — NOT applied.
{
  "lifecycle": {
    "rule": [
      {
        "action": { "type": "Delete" },
        "condition": {
          "age": 400,
          "matchesPrefix": ["reports/weekly/data/"]
        }
      }
    ]
  }
}
```

The prefix is exactly **`reports/weekly/data/`** — with the trailing slash, and
never `reports/weekly/`, which would take the two permanent metadata objects
with it. That single-character difference is the reason the `data/` segment
exists at all.

## Verifying it against the real bucket

```bash
python3 automations/analytics/report_store_verify.py
```

Writes only under `_verification/reports/<run stamp>/`. No real report, Clarity
ledger object, or analytics history is read, written, overwritten or deleted,
and no Clarity API call is made. Also available as a step in the
**Analytics Storage Verification** workflow.

The run stamp is unique per run, so each verification gets a fresh namespace.
That matters for one check in particular: with a fresh prefix the first
`latest.json` is a *create*, which needs no delete permission. The script
therefore publishes a **second** week as well, because replacing that pointer
is what production does every week and is the only operation that exercises the
conditional delete grant. A verification that stopped at the first publish
would pass against a create-only writer while the weekly job failed from its
second run onward.

Exit codes: 0 all checks passed, 1 something is genuinely broken, 2 the
immutable storage works but the pointer grant is missing.

### Sweeping the verification objects

The writer has no delete permission for `_verification/`, by design — the
conditional grant covers the two pointer objects and nothing else, so this
script cannot clean up after itself even in principle. The objects it leaves
are synthetic, a few hundred KB in total, and confined to that prefix.

Deleting them is a manual action for someone with broader access, whenever it
is convenient:

```bash
gsutil -m rm -r gs://molosoc-analytics-history/_verification/
```

Do **not** widen the writer's permissions to automate this.
