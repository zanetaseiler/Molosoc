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

## Not built yet

The recurring/scheduled analytics report. This directory currently proves the
three connections work; the reporting system comes after.
