# Analytics connection test (read-only)

Verifies that Molosoc's Google service account can authenticate against, and
read from, both reporting APIs:

| Source | API | Calls made |
|---|---|---|
| GA4 (property `521643495`) | Google Analytics Data API v1beta | `runReport` × 2 |
| Search Console (`sc-domain:molosoc.com`) | Search Console API v3 | `sites.list`, `searchAnalytics.query` × 3 |

Nothing here writes. Credentials are requested with `analytics.readonly` and
`webmasters.readonly` scopes, and every endpoint used is a read endpoint, so the
script cannot modify anything in Google even by mistake.

## What it reports

**GA4** — last 7 full days (ending yesterday): users (`activeUsers`), sessions,
views (`screenPageViews`), and the top 5 landing pages by sessions.

**Search Console** — 7 days ending 3 days ago: clicks, impressions, CTR, average
position, plus the top 5 queries and top 5 pages. The 3-day offset is Search
Console's data-finalisation lag; a window ending today is normally empty and
would look like a broken connection.

An authenticated property with zero rows is reported as a **pass** with an
explicit "no data yet" note — only auth/permission/API failures exit non-zero.

## Running it

In CI: the **Analytics Connection Test (read-only)** workflow, either manually
(`workflow_dispatch`) or automatically on any push touching
`automations/analytics/**`. It reads the `GOOGLE_SERVICE_ACCOUNT_JSON` repo
secret.

Locally:

```bash
pip install -r automations/analytics/requirements.txt

# either the JSON itself (raw or base64) ...
export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat ~/molosoc-analytics-key.json)"
# ... or a path to the key file
export GOOGLE_APPLICATION_CREDENTIALS=~/molosoc-analytics-key.json

python3 automations/analytics/google_connection_test.py
```

Useful flags: `--days N`, `--property-id`, `--site-url`, `--skip-ga4`,
`--skip-search-console`.

Never commit the key file. `.gitignore` already excludes `.env`, `*.env` and
`secrets/`; keep local keys outside the repo.

## Credential hygiene

The service account JSON is parsed in memory and never printed. The run header
shows a masked identity (`mo***@project.iam.gserviceaccount.com`) so permission
errors stay debuggable, and all error text passes through `redact()`, which
strips PEM private-key blocks, secret-looking JSON fields (`private_key`,
`private_key_id`, `client_secret`, tokens) and `Bearer` tokens before anything
reaches stdout. Tests cover this directly.

## Tests

```bash
pip install -r automations/analytics/requirements.txt pytest
python3 -m pytest automations/analytics/ -q
```

They run fully offline against stubbed API clients — no credentials, no
network — and cover credential loading and its failure modes, redaction, the
date windows including the Search Console lag, response parsing for both APIs
(including empty-property and permission-denied cases), and the assertion that
only read calls are issued.

## Not built yet

Scheduled daily reporting. This directory currently proves the connection
works; the reporting system comes after.
