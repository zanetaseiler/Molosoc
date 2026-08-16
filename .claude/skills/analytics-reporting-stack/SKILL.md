---
name: analytics-reporting-stack
description: Deployment playbook for a read-only marketing analytics stack — GA4, Search Console and Microsoft Clarity collected into durable Cloud Storage, analysed weekly into Markdown/JSON with facts kept separate from inferences, persisted with latest/index pointers, and published as a static dashboard over SFTP. Use when setting up analytics, reporting, or a marketing-analysis agent for a new client site, or when extending/debugging an existing deployment of this architecture.
---

# Analytics & reporting stack

A parameterized playbook for standing up the whole measurement chain for a
client site: collection, durable history, weekly analysis, reporting, a
published dashboard, and a clean handoff to a downstream strategy agent.

Extracted from a completed production deployment. It is not a case study —
it is the build order, the exact decisions, the mistakes that cost real
time, and the checks that prove each layer works before the next one is
built on it.

**Read `client-config.template.yml` first.** Every `{{PLACEHOLDER}}` below is
defined there. Fill that file before writing any code; the rest of this
playbook assumes those values exist.

---

## What gets built

```
  GA4 ─┐                                   ┌─→ Markdown report ─→ GitHub artifact (90d)
       ├─→ on-demand hydration ─┐          │
  GSC ─┘   (weekly, 4 calls)    │          ├─→ JSON report ──────→ GCS history (immutable)
                                ├─→ analysis engine ─┤
  Clarity ─→ DAILY collector ───┘          ├─→ latest.json / index.json (mutable pointers)
             (1 call/day, forever)         │
                                           └─→ static HTML dashboard ─→ SFTP ─→ public URL
                                                                                    │
                                                     downstream strategy agent ←────┘
                                                     (reads GCS, never the HTML)
```

Two collection modes, and the difference drives the whole build order:

| Source | Historical API? | Mode | Consequence |
|---|---|---|---|
| GA4 | yes | fetch any window on demand | can be backfilled at any time |
| Search Console | yes (~3-day lag) | fetch any window on demand | can be backfilled at any time |
| **Clarity** | **no** | **daily snapshot, accumulated forward** | **a missed day is lost permanently** |

---

## New client quick-start

Execute in this order. The ordering is not stylistic — steps 1–4 create data
that later steps cannot reconstruct.

```
 1. Fill client-config.template.yml completely.            (§1)
 2. Get read access granted to GA4, Search Console, Clarity. (§3, owner action)
 3. Create the GCP project, bucket and two service accounts. (§4)
 4. ► START THE DAILY CLARITY COLLECTOR. ◄                   (§6)
       Do this BEFORE building anything else. Every day it is
       not running is a day of history that can never exist.
 5. Run the three connection tests; fix credentials until green. (§10)
 6. Establish the ecommerce tracking boundary date.           (§2)
 7. Build/port the analysis engine and thresholds.            (§7)
 8. Build weekly Markdown + JSON reporting; verify on fixtures. (§8)
 9. Add durable report storage + pointers; verify live.        (§8)
10. Add the dashboard renderer and SFTP publishing.            (§9)
11. Work the go-live checklist.                                (§14)
12. Only then hand off to the strategy agent.                  (§15)
```

Steps 5–11 can each be a separate reviewed change. Step 4 should be the same
day the engagement starts, even if nothing else is ready — the collector is
independently useful and its cost is one API call a day.

---

## 1. Client inputs required

Collect all of these before starting. Chasing them mid-build is where
deployments stall.

| Input | Placeholder | Notes |
|---|---|---|
| Client name | `{{CLIENT_NAME}}` | display only |
| Slug | `{{CLIENT_SLUG}}` | storage namespace; permanent once history exists |
| Production domain | `{{PRODUCTION_DOMAIN}}` | canonicalization + staging exclusion |
| Staging/preview hosts | `{{STAGING_HOST}}` | must be excluded from analysis |
| GA4 property ID | `{{GA4_PROPERTY_ID}}` | numeric; **not** the measurement ID |
| GA4 measurement ID | `{{GA4_MEASUREMENT_ID}}` | `G-…`; for install verification |
| Conversion event | `{{CONVERSION_EVENT}}` | the GA4 key event that means revenue |
| Search Console property | `{{GSC_PROPERTY}}` | `sc-domain:` or `url-prefix:`, exactly as verified |
| Clarity project ID | `{{CLARITY_PROJECT_ID}}` | from the project URL |
| Clarity API token | secret | Clarity → Settings → API |
| GCP project | `{{GCP_PROJECT_ID}}` | new or existing |
| Bucket name | `{{GCS_BUCKET}}` | globally unique |
| GitHub repo | `{{GITHUB_REPO}}` | where workflows run |
| Ecommerce tracking start | `{{ECOMMERCE_TRACKING_START}}` | see §2 — get this right |
| Report host SSH details | `{{SSH_HOST}}` / `{{SSH_USER}}` / `{{SSH_BASE_PATH}}` | see §9 |
| Dashboard URL | `{{DASHBOARD_URL}}` | must match base path + slug |
| Report schedule | `{{REPORT_CRON}}` / `{{COLLECTOR_CRON}}` | derive per §9, don't copy |

**Ask the client explicitly, do not infer:**

- *When did ecommerce/conversion tracking actually start working?* The answer
  is often "we thought it always did" and is often wrong. Verify against GA4
  before accepting it.
- *Is there more than one analytics tag on the site?* A plugin and a manual
  `gtag` snippet both firing is common and doubles every count.
- *Which hostnames are not production?* Staging traffic in the numbers is
  invisible until it distorts a recommendation.

---

## 2. The ecommerce tracking boundary

The single most important data-quality decision. It exists because a real
deployment shipped conversion analysis against a period that predated working
purchase tracking, and zero purchases read as "no sales" rather than "no
data".

Define `{{ECOMMERCE_TRACKING_START}}` and classify every analysis window
against it into exactly four states:

| State | Meaning | Report behaviour |
|---|---|---|
| `active` | window entirely after the boundary | conversion figures are real; analyse |
| `unavailable` | window entirely before it | **report "not tracked", never 0** |
| `partial` | window straddles the boundary | figures are incomplete; label, never compare |
| `unknown` | no boundary configured | say so; withhold conversion conclusions |

Rules that must hold in code, not just in prose:

- A `unavailable` or `partial` window must never produce a percentage change
  against an `active` one. The comparison is meaningless and looks authoritative.
- Every suppressed comparison carries a machine-readable reason
  (e.g. `comparison_unavailable_reason`) so the renderer can print *why*
  instead of a bare dash. A dash next to a real purchase count reads as zero.
- The boundary is a repository variable with a committed default. An unset
  variable must not silently become "unknown" every week.

---

## 3. Secrets and credentials

Four credentials, each with the narrowest scope that works.

| Secret | Holds | Scope |
|---|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | analytics reader key | GA4 **Viewer**, GSC **restricted/full user** — read only |
| `ANALYTICS_STORAGE_SA_JSON` | storage writer key | the history bucket only |
| `CLARITY_API_TOKEN` | Clarity API token | that project only |
| `REPORTS_SSH_KEY` | SFTP private key | that hosting account only |

Rules:

- **Two service accounts, not one.** The analytics reader never touches
  storage; the storage writer never touches analytics. A leaked key then
  costs one surface, not both.
- **Never print a secret**, not even a prefix or length, and not in an error
  path. Register secrets with the redactor so exception text is scrubbed —
  library exceptions quote the input that failed.
- **Diagnose shape, not value.** When a credential is wrong you may report
  that a username contains `@`, or that a key is missing its BEGIN line. You
  may not print the username or the key. This distinction resolved several
  real failures without ever disclosing a secret (§13).
- Public keys and fingerprints are **not** secret and printing them is the
  fastest way to diagnose an auth failure.
- Rotation: replace the GitHub secret, re-run the connection test, then
  revoke the old key. Never the other way round.

**Owner actions required** (a coding agent cannot do these — see §16):
granting the service account access in the GA4 and Search Console UIs,
generating the Clarity token, and authorizing the SSH key in the hosting
control panel.

---

## 4. Google Cloud setup

```bash
PROJECT="{{GCP_PROJECT_ID}}"
BUCKET="{{GCS_BUCKET}}"
LOCATION="{{GCS_LOCATION}}"

gcloud services enable \
  analyticsdata.googleapis.com \
  searchconsole.googleapis.com \
  storage.googleapis.com --project "$PROJECT"

# One bucket. Private, uniform access (required for IAM conditions later).
gcloud storage buckets create "gs://$BUCKET" \
  --project="$PROJECT" --location="$LOCATION" \
  --uniform-bucket-level-access --public-access-prevention

gcloud iam service-accounts create analytics-reader --project="$PROJECT"
gcloud iam service-accounts create analytics-storage --project="$PROJECT"
```

Grant the storage writer object create/get/list on the bucket only — not
project-wide, and **not** `storage.objects.delete`.

### The one conditional permission

GCS models an object overwrite as delete-then-create. The design keeps every
dated report immutable, but `latest.json` and `index.json` must be rewritten
every week. So grant `storage.objects.delete` **conditioned on exactly those
two object names**:

```
resource.name == "projects/_/buckets/{{GCS_BUCKET}}/objects/reports/weekly/latest.json" ||
resource.name == "projects/_/buckets/{{GCS_BUCKET}}/objects/reports/weekly/index.json"
```

Never grant unconditional delete. With this condition the writer physically
cannot destroy a dated report, Clarity history, or a raw snapshot — the
guarantee comes from IAM, not from code being careful. Conditions require
uniform bucket-level access, which is why it is set at creation.

Generate the CEL string from the bucket name in code rather than pasting it,
so a typo cannot silently widen the grant.

### Retention

Lifecycle rules can match a prefix but cannot express an exclusion. Therefore
**dated reports live under their own prefix** (`reports/weekly/data/`) so a
lifecycle rule can expire them without ever touching the pointers beside them.
Layout deliberately supports this — see `reference/storage-layout.md`.

Default `{{report_retention_days}}` = 400 (a year plus comparison headroom).
Reports are small JSON; the dominant cost is operations, not bytes. Do not
apply a deletion rule until the client has agreed to lose that history.

---

## 5. GitHub setup

Repository **variables** (non-secret, visible in logs): `ANALYTICS_BUCKET`,
`ECOMMERCE_TRACKING_START`, `REPORTS_BASE_PATH`.
Repository **secrets**: the four in §3, plus `REPORTS_SSH_HOST`,
`REPORTS_SSH_USER`, `REPORTS_SSH_HOST_KEY`.

Workflows to create:

| Workflow | Trigger | Purpose |
|---|---|---|
| `analytics-connection-test` | manual | prove GA4 + GSC credentials read |
| `clarity-connection-test` | manual | prove Clarity token reads (costs 1 call) |
| `analytics-storage-verify` | manual | prove bucket read/write/pointer rewrite |
| `clarity-daily-collect` | cron `{{COLLECTOR_CRON}}` | the irreplaceable one |
| `weekly-marketing-report` | cron `{{REPORT_CRON}}` + manual | analyse, persist, publish |

Non-negotiable workflow properties:

- `permissions: contents: read` — nothing here writes to the repository.
- `concurrency` group per workflow, `cancel-in-progress: false`. Cancelling a
  half-written collection is worse than queueing.
- A `workflow_dispatch` input to override "today", so a past week can be
  re-run without editing code.
- A step that asserts every required secret/variable is present, printing
  names only, before any real work.
- **Cron only fires on the default branch.** Nothing is scheduled until
  merged. Test with `workflow_dispatch` from the branch.
- Artifact upload with `if: always()` so a downstream failure cannot cost the
  report that already succeeded.

Repository visibility: if the repo is **public**, Actions artifacts are
downloadable by any authenticated GitHub user. Analytics artifacts are
client-confidential. Either make the repo private or accept this explicitly —
raise it with the client rather than deciding silently.

---

## 6. Analytics collection

### Daily Clarity collection — build this first

Clarity's Live Insights API returns at most a 3-day window, allows
**10 calls per project per day**, and offers **no historical endpoint**.
History exists only if something has been recording it.

- One call per day, `numOfDays=1`, at `{{COLLECTOR_CRON}}`.
- Automated cap **3/day** against the hard limit of 10, leaving headroom for
  manual diagnostics. A budget ledger in the bucket tracks spend so a retry
  storm cannot exhaust the day.
- Write the raw payload **and** normalized facts, both keyed by date. Raw is
  immutable evidence; facts are derived and safe to recompute.
- Re-running a day must not double-write: a create-if-absent write
  (`if_generation_match=0`) makes the collector idempotent.
- The collector must be tolerant of a missing day and never backfill-guess.
  A gap is recorded as a gap.

Record `{{CLARITY_COLLECTION_START}}` in the config. Every later report states
how many ledger days it had, so a thin Clarity section is explained rather
than mysterious.

### On-demand GA4 / Search Console hydration

- Fetched at report time only, for exactly the two compared windows —
  **4 API calls per report**, cached so a window is never fetched twice.
- No daily collector. Both APIs serve history, so storing it would duplicate
  a system Google already runs.
- Search Console finalises on a ~3-day lag. Never analyse a window whose end
  is within 3 days of today; it will silently under-report.
- Exclude non-production hostnames at normalization, not in the renderer.

### Canonicalization and quality

Normalize URLs once, centrally: strip query strings and fragments except
where a parameter is genuinely a distinct page, unify trailing slashes, drop
non-production hosts, and fold language prefixes consistently. Two spellings
of one URL split its metrics and quietly halve them.

---

## 7. Analysis logic

### Facts and inferences are different types

Not a naming convention — a type distinction enforced at construction.

- A **fact** is a measured quantity with its source, window and sample size.
  It carries `causal_claim = False` as an invariant and is **rejected at
  construction if its statement uses causal language**. "Sessions fell 18%"
  is a fact. "Sessions fell because the page slowed" is not.
- An **inference** is explicitly typed `correlation`, `pattern` or
  `hypothesis`, carries a confidence level, and names the facts it rests on.

This is what makes the output safe to hand to an agent that will act on it:
a downstream consumer can take every fact at face value and treat every
inference as a claim needing evidence.

### Readiness gate

Three site-level states: `ready`, `insufficient_data`, `suppressed`.

Below `{{min_site_sessions_for_recommendations}}` (default 100) sessions in
the analysed week, the report emits facts and **withholds recommendations
entirely**. A low-volume report that reports numbers and declines to advise
is a *successful* run, not a failure — it must exit 0 and must not alert.

### Thresholds — conservative by design

An entity must pass **eligibility** (enough volume to analyse at all) and
**significance** (change distinguishable from noise) before it can produce a
recommendation. Passing one but not the other is exactly what the `Monitor`
priority is for.

Relative change alone never triggers a finding: 1 click becoming 3 is +200%
and means nothing. Both a relative gate (≥20%) and a per-metric absolute gate
must pass; rate changes use a two-proportion z-test at 95%.

Full table and rationale: `reference/thresholds.md`.

**Do not lower these to make a quiet report look busier.** At low volume
almost nothing clears them, and that is correct. A report that manufactures
advice from four clicks is worse than one that says it cannot tell yet.

### Anomaly classification

Separate `performance` anomalies (the business changed) from
`instrumentation` anomalies (the measurement changed). A metric going to zero
is nearly always the second. Conflating them sends clients chasing traffic
drops that are broken tags.

---

## 8. Report generation and history

### The weekly report

Wednesday run → anchor `today - 3` = Sunday → analyses the previous
Monday–Sunday week against the week before. Whole calendar weeks compare like
with like; a mid-week boundary splits weekend traffic across both windows.

Outputs, all from **one analysis object** so the views cannot disagree:
Markdown (human), JSON (machine), HTML (dashboard). Never re-query a source
to build a second view.

**Zero Clarity API calls at report time.** The report reads Clarity from the
durable ledger only. The daily collector owns the budget, and a report that
spent from it could cost a day of history permanently. Assert this with a test.

### Durable history

- Dated reports are written **once**, under `reports/weekly/data/…`, and never
  overwritten. Re-running a stored week is rejected by default (exit code 3);
  an explicit `revision` policy files the re-run *alongside* the original
  rather than replacing it.
- A duplicate week is the storage layer **succeeding**. The workflow treats
  that exit code as a warning and continues to publish the dashboard —
  publishing must not be coupled to the history being novel.
- `latest.json` and `index.json` are the only mutable objects. If the pointer
  write fails but the reports were stored, that is a distinct exit code (2),
  not a generic failure: nothing was lost and a rebuild command fixes it.
- `index.json` holds one small entry per week (headline metrics + keys), not
  copies of reports. Bound it (`{{index_max_entries}}`, ~5 years) and measure
  the *marginal* bytes per entry when testing growth, not the total.
- Version the schema (`schema_version`, `report_kind`) so a future consumer
  can detect an old shape instead of misreading it.

Layout, schema and exit codes: `reference/storage-layout.md`.

---

## 9. Dashboard deployment

### The dashboard is a presentation layer

It renders the already-computed report. It does **not** query analytics, hold
its own thresholds, or decide what is significant. If the dashboard would
need a number the report does not contain, fix the report.

Concretely: the recommendations section prints the report's recommendations
**verbatim**. That is what keeps the readiness gate effective — otherwise the
view quietly re-decides what the engine deliberately withheld.

### Page requirements

- One self-contained HTML file. No JavaScript, no external CSS/fonts/CDN, no
  analytics on the analytics page.
- `<meta name="robots" content="noindex, nofollow, noarchive">`.
- Responsive, in the client's brand tokens.
- Trends render only once ≥3 weeks are stored — two points is not a trend.
- Direction is judged by **outcome, not sign**: for position, bounce, rage
  clicks and error rates, down is good. A naive "green = up" reads backwards.
- Where a comparison was suppressed (§2), show the reason, not a dash.

### Transport: SFTP over SSH, not FTPS

On typical shared hosting the FTPS service presents the provider's own
wildcard certificate (e.g. `*.internal.hostingprovider.net`). Verifying it
honestly requires a hostname under a domain the client does not control, so
the only route to a working FTPS upload is to stop checking the certificate.

Use SSH instead: it authenticates the server by **host key**, a check that can
actually be performed. Print the fingerprint on every run; pin it via
`{{SSH_HOST_KEY}}` so a changed key aborts rather than passing silently.

Never disable TLS or host-key verification to make a deploy succeed.

### Destination guards

The report host usually also serves the client's live site, so the entire
risk is writing to the wrong path. Required, in this order:

1. **Derive** the destination — always `{{SSH_BASE_PATH}}/{{CLIENT_SLUG}}`.
   Never accept a free-text remote path.
2. Refuse it if relative, containing `..`, or containing a CMS directory
   (`wp-content`, `wp-admin`, `wp-includes`, `wp-json`).
3. A dry-run mode that prints the resolved path **without connecting**.
4. After connecting, compare the **server's own** working directory against
   the expected path and abandon unless the final segment is the client slug.
   The server's opinion of where you are is the one that counts.
5. Create only the leaf directory, only inside a base path that must already
   exist. Never build a missing tree — that is how a typo becomes a new folder
   in someone's web root.
6. Upload exactly one file, `index.html`. Never delete, rename or move.
   Assert this with a test that greps the source for destructive calls.

**Path gotcha:** cPanel FTP presents the account home as the root, so a path
recorded as `/public_html/…` from the FTP view does not exist at the
filesystem root over SSH. Resolve the base path relative to the session home
as a *second reading* of the same path — after the literal path fails, subject
to the identical guards.

**Username gotcha:** cPanel grants SSH to the **main account user only**. An
FTP sub-account (`name@domain`) authenticates over FTP and is refused over SSH
no matter how correct the key is.

### Ordering inside the workflow

Publish **last**. GCS persistence and the artifact must already be done, so a
problem with the report host cannot cost either. Finish with a `curl` that
asserts HTTP 200 *and* that the body contains a known dashboard string — a 200
from a hosting placeholder page is not a deployed dashboard.

### Deriving the schedule

```
report_weekday = (desired_week_end_weekday + 3) mod 7     # +3 = GSC lag
```

Mon–Sun weeks → Wednesday. Put the collector several hours earlier so the
ledger is settled. Use off-the-hour minutes. Fix the time in UTC and accept
that local time shifts with DST — the windows are whole UTC days either way.

---

## 10. Validation and tests

Every layer gets a check that can fail before the next layer is built on it.

**Connection tests** (manual workflows, read-only): GA4 returns totals for a
known window; Search Console returns rows for the verified property; Clarity
returns one snapshot (costs 1 of 10 calls — never put this on a schedule);
storage writes, reads back, and rewrites a pointer.

**Offline suite** — no network, no credentials, no bucket. Runs in CI before
every live step. Must assert at least:

- zero Clarity API calls in the report path;
- causal language is rejected at fact construction;
- the readiness gate withholds recommendations below the threshold;
- a pre-tracking window reports `unavailable`, never `0`;
- a stored week is not overwritten; the revision policy files alongside;
- the resolved remote path is refused when relative/traversing/CMS;
- the publisher contains no delete/rename/move calls;
- no FTP/TLS-bypass symbols remain in the publisher.

**Fixtures** for three shapes: low volume, healthy, broken instrumentation.
A fixture run must be **refused** from writing into real history — synthetic
numbers a year from now are indistinguishable from real ones.

**Live synthetic verification** for storage: publish a synthetic report under
an isolated prefix, then exercise the pointer rewrite against the *real*
pointer object idempotently. An isolated prefix alone cannot prove a
condition scoped to the real object names — the check would pass whether the
IAM binding were perfect or absent.

### Test doubles must match reality

A fake that is stricter than the real service hides bugs the real one will
find. One deployment's fake bucket denied *all* overwrites including creates,
so a fresh-prefix check passed while production failed. Model the actual
semantics: GCS denies an overwrite only when the object already exists.

---

## 11. Security requirements

- Read-only against every analytics source. Nothing writes to GA4, Search
  Console, Clarity, the CMS or the site.
- Bucket private, public access prevention enforced, **no** signed URLs, no
  public objects.
- Two least-privilege service accounts (§3); delete permission conditioned to
  two object names (§4).
- Secrets never printed; error text scrubbed; diagnose shape not value.
- Host-key pinning for SFTP; never disable certificate or host-key checks.
- Reports are never committed to the repository. A workflow step asserts the
  working tree stayed clean, so generated output cannot leak into git.
- The dashboard is unlisted and noindexed — **that is not access control.**
  Anyone with the URL can read it. If the data warrants real protection, put
  HTTP auth in front of it and say so in the config.
- If the repository is public, Actions artifacts are readable by any
  authenticated GitHub user (§5). Decide deliberately.

---

## 12. Cost and retention decisions

Costs are dominated by operations and egress, not storage — the whole dataset
is small JSON.

| Layer | Volume | Policy |
|---|---|---|
| Clarity raw + facts | 2 small objects/day | keep; irreplaceable |
| Dated weekly reports | ~2 objects/week | `{{report_retention_days}}` (400) |
| Pointers | 2 objects, rewritten | **never expire** |
| GitHub artifact | 1 zip/week | `{{artifact_retention_days}}` (90) |
| Dashboard | 1 file, overwritten | n/a |

- Clarity history is the one thing money cannot rebuy. Retention rules must
  never touch it — which the `data/` prefix separation guarantees.
- Do not apply a lifecycle deletion rule without explicit client agreement;
  it is irreversible.
- Standard storage class is correct — these objects are read weekly, and
  Nearline/Coldline early-deletion fees exceed any saving at this size.
- Budget: one Clarity call/day, four Google calls/week. Free tier at this
  scale; the real ceiling is Clarity's 10/day, which the cap protects.

---

## 13. Common failure modes and fixes

Each of these cost real debugging time on the first deployment.

**Data correctness**

| Symptom | Cause | Fix |
|---|---|---|
| Conversions show 0 for old periods | window predates tracking | §2 boundary; report `unavailable` |
| Every count roughly doubled | two GA4 mechanisms (plugin + manual tag) | remove one; verify with tag debugger |
| Tracking "works" but sessions are low | verified while logged in as admin | **test logged out, incognito, real device** |
| Metrics split across two URLs | canonicalization inconsistency | normalize centrally, once |
| Traffic spike nobody recognises | staging/preview host counted | exclude non-production hosts |
| Clarity section thin/empty | collector started recently | expected; state ledger days — cannot be backfilled |

**Storage**

| Symptom | Cause | Fix |
|---|---|---|
| Pointer write denied, reports fine | overwrite needs `storage.objects.delete` | conditional grant (§4); exit 2, then rebuild pointers |
| Live check green but production fails | test double stricter than GCS | model real semantics (§10) |
| Verification passes with no IAM binding | isolated prefix outside the condition | probe the real pointer object idempotently |
| "Permission denied" naming the wrong key | error printed store-relative key | print the full `gs://bucket/object` name |

**Deployment**

| Symptom | Cause | Fix |
|---|---|---|
| TLS hostname verification fails on FTPS | host serves provider wildcard cert | switch to SFTP (§9); do not disable verification |
| `does not contain a private key` | the `.pub` half was pasted | paste the private key incl. BEGIN/END lines |
| `AuthenticationException` | FTP sub-account used for SSH | use the cPanel **account** username |
| `base path does not exist` after auth succeeds | FTP-view path vs SSH filesystem root | resolve relative to session home (§9) |
| Repository variable arrives empty | variable unset in that environment | committed default, variable still overrides |
| Duplicate week skips publishing | publish coupled to novelty | treat exit 3 as warning, continue |
| Live check passes on the wrong page | only HTTP 200 asserted | also grep the body for known content |

**Process**

| Symptom | Cause | Fix |
|---|---|---|
| Offline suite suddenly slow | a test opened a real socket | stub network probes; suites stay seconds |
| Test fails on prose | scanned docstrings for forbidden strings | scan the code body only |
| Cron never fires | workflow not on default branch | merge; use `workflow_dispatch` meanwhile |

---

## 14. Go-live checklist

Data
- [ ] Clarity collector running daily for ≥14 days; ledger has no gaps
- [ ] GA4 + GSC connection tests green
- [ ] `{{ECOMMERCE_TRACKING_START}}` set and verified against GA4
- [ ] Single GA4 mechanism confirmed (no double counting)
- [ ] Tracking verified **logged out**, incognito, on a real device
- [ ] Staging hosts excluded; URL canonicalization spot-checked

Storage
- [ ] Bucket private, public access prevention enforced, UBLA on
- [ ] Two service accounts, least privilege
- [ ] Delete permission conditioned to the two pointer objects only
- [ ] Live synthetic verification passed, including the real pointer probe
- [ ] Retention decision made and agreed; no lifecycle rule applied without consent

Analysis
- [ ] Thresholds reviewed, not lowered
- [ ] Readiness gate produces `insufficient_data` on the low-volume fixture and exits 0
- [ ] Facts reject causal language; inferences typed and confidence-tagged
- [ ] Pre-tracking window reports `unavailable`, never `0`

Reporting
- [ ] Weekly workflow: correct cron, `contents: read`, concurrency, dispatch override
- [ ] Markdown + JSON + HTML all from one analysis object
- [ ] Zero Clarity API calls at report time (asserted by test)
- [ ] Dated report immutable; duplicate rejected; revision policy works
- [ ] `latest.json` + `index.json` update; rebuild command exists
- [ ] Artifact uploads with `if: always()`, retention set

Dashboard
- [ ] Static, no JS, no external requests, `noindex`
- [ ] Trends hidden below 3 weeks; direction judged by outcome
- [ ] Dry run prints correct path without connecting
- [ ] Server-side directory check passes; only `index.html` uploaded
- [ ] Host key pinned via `{{SSH_HOST_KEY}}`
- [ ] Live URL returns 200 **and** contains expected content

Operations
- [ ] Everything merged to the default branch so cron actually fires
- [ ] One full unattended run observed green end to end
- [ ] Repository visibility decision made (artifact exposure)
- [ ] Client told what the dashboard URL is and that it is unlisted, not private

---

## 15. Downstream strategy-agent handoff

The reporting stack ends at published facts. A strategy or content agent is a
separate system with a separate approval, and this is the contract between them.

**The consumer reads GCS, never the HTML.** `reports/weekly/latest.json` is
the entry point; `index.json` gives history. The dashboard is for humans and
its markup is not an interface.

Guarantees the consumer can rely on:

- `schema_version` and `report_kind` identify the shape; an unknown version
  must be refused, not guessed at.
- Facts are measured and non-causal. Inferences are typed and confidence-tagged.
- `readiness` states whether recommendations were withheld. An
  `insufficient_data` report is valid data, **not** an error to retry.
- Conversion figures carry a tracking state; `unavailable` must never be read
  as zero.
- Dated reports are immutable, so a cached read stays valid forever.

Obligations on the consumer:

- Never write to this bucket's report tree.
- Never act on an inference as if it were a fact.
- Respect the readiness gate — do not synthesize advice the engine withheld.
- Record which report version drove any action, so outcomes can be attributed.

Do not start the strategy agent until the checklist in §14 is complete and at
least one report has been produced unattended.

---

## 16. What still requires a human account owner

A coding agent cannot do these. Schedule them early — they block §6 onward.

| Action | Where | Blocks |
|---|---|---|
| Add service account as GA4 **Viewer** | GA4 Admin → Property Access | GA4 hydration |
| Add service account to Search Console property | GSC → Settings → Users | GSC hydration |
| Verify the GSC property (DNS/HTML) if unverified | GSC | GSC hydration |
| Generate the Clarity API token | Clarity → Settings → API | daily collector |
| Create GCP project / enable billing | Cloud Console | all storage |
| Apply the conditional IAM binding | Cloud Console / gcloud | pointer updates |
| Create + authorize the SSH key | hosting control panel | dashboard publishing |
| Add GitHub secrets and variables | repo settings | every workflow |
| Confirm the ecommerce tracking start date | client knowledge | conversion analysis |
| Decide repository visibility | client | artifact confidentiality |
| Approve any lifecycle deletion rule | client | retention |

---

## Lessons learned

The nine that changed the design:

1. **Clarity history cannot be backfilled — start the daily collector first.**
   Every other component can be built late and catch up. This one cannot.
   Ship it on day one even if nothing else is ready.
2. **Never treat missing pre-tracking ecommerce data as zero.** "No data" and
   "no sales" look identical in a number and mean opposite things. Model the
   boundary explicitly with four states.
3. **Avoid duplicate GA4 mechanisms.** A plugin plus a manual tag doubles
   every count, and the error is invisible in the data itself — only the
   install reveals it.
4. **Verify tracking logged out, separately from admin sessions.** Logged-in
   admin traffic is often excluded or behaves differently. "It works for me"
   is not verification.
5. **Preserve immutable historical records.** Write dated reports once, keep
   mutation to two pointer objects, and enforce it in IAM rather than trusting
   code to be careful.
6. **Use conservative recommendation thresholds.** Withholding advice at low
   volume is the product working. Lowering thresholds to fill a page destroys
   the credibility of every report that follows.
7. **The dashboard is a presentation layer, not a new analytics
   architecture.** It renders the report verbatim. The moment it computes its
   own numbers, two sources of truth exist and they will diverge.
8. **Keep staging/indexing cleanup separate from analytics work.** They share
   vocabulary and nothing else. Mixing them turns one reviewable change into
   two half-verified ones.
9. **Prefer SSH/SFTP with host-key pinning.** When a transport cannot be
   verified honestly, replace the transport rather than switching its
   verification off. Print the fingerprint every run so a changed host key
   surfaces instead of passing silently.

One more, earned the hard way: **when a credential fails, report the shape of
what is wrong, never the value.** "The username contains `@`, which is the FTP
sub-account form" resolved in one run what several runs of "authentication
failed" could not — and disclosed nothing.
