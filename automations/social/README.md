# Meta (Facebook + Instagram) connection — read-only

Stage 1 of MOLOSOC's social account connections: **Instagram + Facebook only**,
for both the CZ and EN accounts. TikTok and YouTube are out of scope here.
Reddit is not a MOLOSOC platform and is never referenced by this automation.

This folder proves the Meta side of publishing can authenticate and read —
it does **not** publish or schedule anything. Nothing in it calls a write
endpoint (`/media`, `/photos`, `/videos`, `/video_reels`, `/feed`); the
`test_every_request_is_a_get_to_a_read_endpoint` test in
`test_meta_connection_test.py` asserts that directly, so an accidental write
call fails the suite rather than silently posting something.

## What this does and doesn't tell you

**Proves:** the stored token authenticates, can read the named Facebook
Page, that Page's linked Instagram professional account matches what's
expected (Page ↔ Instagram pairing), and — when that language's
`META_APP_ID_*`/`META_APP_SECRET_*` are also set — exactly which
permissions the token was granted.

**Does not prove:** that an actual image or Reels upload will succeed. Reels
specifically go through a multi-step upload-and-poll flow (create a video
container, poll until Meta finishes processing it, then publish) that has
failure modes — wrong aspect ratio, duration limits, encoding issues — no
read-only call can catch. Confirming that end-to-end requires an actual test
upload, which is explicitly out of scope until publishing is approved.

## Why CZ and EN are fully separate — separate apps, not just separate tokens

CZ and EN are **two entirely separate Meta apps**, each with its own App ID,
App Secret, and system-user token — not one shared app used for both. There
is no `META_APP_ID`/`META_APP_SECRET`/`META_ACCESS_TOKEN` fallback anywhere
in this code; every credential is looked up with a `_CZ` or `_EN` suffix and
nothing else. Confirmed identities:

| | CZ | EN |
|---|---|---|
| Facebook Page ID | `670138019527343` | `1225373770662335` |
| Meta App ID | `1811329706700638` | `1537667540920982` |
| System-user token | separate, per language | separate, per language |

(Page IDs and App IDs are not secrets — they're visible on the Page/App
dashboard to anyone with access — but they're still stored as GitHub
secrets alongside the real secrets, `META_APP_SECRET_*` and
`META_ACCESS_TOKEN_*`, for consistency and so nothing is hard-coded in this
repo. Nothing in `meta_connection_test.py` hard-codes any of the four
values above — everything above is documentation, not defaults; the script
reads all eight secrets from the environment only.)

This is what makes "support separate CZ and EN accounts" and "the Google
Drive publishing schedule as the source of truth" actually work later:
`MOLOSOC_Master_Publishing_Schedule` tags every row with a `Language` column
(CZ/EN) and each row needs to land on that language's own Page/Instagram
account, through that language's own app credentials — not a shared one.

## Authentication approach: System User token, not a personal login

Two ways to get a token that can act on a Page:

1. **A personal user's long-lived token** (from a login flow) — expires in
   ~60 days and stops working the moment that person's session/password
   changes. Wrong fit for "no ongoing dependency on my Mac" — someone would
   have to re-authenticate every two months.
2. **A Meta Business System User token** — created once in Business Manager,
   scoped to exactly the Page + Instagram assets it needs, and does not
   expire on its own. This is the right fit for a GitHub Actions secret: set
   it once, it keeps working.

Use a System User token for each language's `META_ACCESS_TOKEN_*` secret.

## Setting it up — what you need to do in the browser

This part needs your Meta Business Suite access; nothing here can do it for
you. Repeat the Page/Instagram/System-User steps once per language (CZ, EN).

1. **Confirm CZ/EN Pages + Instagram pairing.** In
   [Meta Business Suite](https://business.facebook.com/), under
   **Settings → Accounts → Pages**, identify the MOLOSOC CZ Facebook Page and
   the MOLOSOC EN Facebook Page (or confirm there's only one Page today).
   Under **Accounts → Instagram accounts**, confirm each Page has its own
   linked Instagram *professional* (Business or Creator) account — an
   Instagram account only shows up as `instagram_business_account` on a Page
   if it's already converted to Business/Creator and linked to that Page. If
   a CZ or EN Instagram account is still a personal account, convert it in
   the Instagram app first (Settings → Account type) and link it to the
   right Page from Business Suite.

2. **Use each language's own Meta Developer App** — CZ App ID
   `1811329706700638`, EN App ID `1537667540920982` (already created; see
   [developers.facebook.com/apps](https://developers.facebook.com/apps) if
   you need to open either one). For each app, note its **App Secret**
   (App Settings → Basic) — these become `META_APP_SECRET_CZ` and
   `META_APP_SECRET_EN` respectively. Never use CZ's secret for EN or vice
   versa. The App Secret is only used here to introspect tokens via
   `/debug_token`; it never authorizes posting by itself.

3. **Add the Instagram Graph API + Facebook Login for Business products** to
   each app (App Dashboard → Add Product), so it can request `pages_*` and
   `instagram_*` permissions.

4. **Create a System User for each app** in that app's Business Manager:
   **Settings → Users → System Users → Add** — e.g.
   `molosoc-social-cz` under the CZ app's Business Manager,
   `molosoc-social-en` under the EN app's. Keep them one-per-language; a
   system user created under the wrong app can't be assigned across apps.

5. **Assign that language's Page to its own System User.** **Add
   Assets → Pages** → select the matching Page (CZ Page ID
   `670138019527343`, EN Page ID `1225373770662335`) → grant it at least
   "Manage Page" access (this is what's needed for `pages_manage_posts`).
   The linked Instagram account doesn't need a separate asset assignment —
   it inherits from the Page.

6. **Generate each System User's access token, from its own app.** On the
   System User's detail page, **Generate New Token** → select that
   language's app from step 2 (CZ token generated from the CZ app, EN token
   from the EN app) → select these permissions:
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `instagram_basic`
   - `instagram_content_publish`
   - `business_management` (recommended — lets the token see its own asset
     assignments, useful for debugging)

   Copy the generated token immediately — Meta shows it once. This is
   `META_ACCESS_TOKEN_CZ` or `META_ACCESS_TOKEN_EN`.

7. **App Review.** `instagram_content_publish` and `pages_manage_posts` are
   both permissions Meta gates behind **App Review** before they work for
   anyone outside the app's own Business Manager. If the MOLOSOC Page and
   Instagram account are already added as assets to the same Business
   Manager that owns the app (steps 1 and 4-5 above), Meta grants these
   permissions to System User tokens **without needing App Review** — that's
   standard behavior for internal/first-party use, not a loophole. If a
   permission request is rejected outside that setup, App Review is the
   Meta-side reason and requires submitting the app for review with a
   screencast of the intended use — a separate browser task if it comes to
   that.

8. **Get the Page ID and (optionally) the Instagram Account ID.** The Page
   ID is visible on the Page itself (About → Page ID, or Business Suite
   Settings). You don't strictly need the Instagram Account ID separately —
   this script reads it live off the Page's `instagram_business_account`
   field — but setting `META_IG_ACCOUNT_ID_CZ`/`META_IG_ACCOUNT_ID_EN` (from
   the Instagram professional account's own settings page, or
   Business Suite → Instagram accounts) makes the connection test actively
   verify the pairing instead of just trusting whatever the Page reports.

9. **Add everything as GitHub repository secrets** — Settings → Secrets and
   variables → Actions, on this repo. Eight secrets total, four per
   language, no sharing between CZ and EN:

   | Secret | What it is |
   |---|---|
   | `META_APP_ID_CZ` | `1811329706700638` (CZ Meta App ID) |
   | `META_APP_SECRET_CZ` | CZ App Secret from step 2 |
   | `META_FB_PAGE_ID_CZ` | `670138019527343` (MOLOSOC CZ Facebook Page ID) |
   | `META_ACCESS_TOKEN_CZ` | CZ System User token from step 6 |
   | `META_APP_ID_EN` | `1537667540920982` (EN Meta App ID) |
   | `META_APP_SECRET_EN` | EN App Secret from step 2 |
   | `META_FB_PAGE_ID_EN` | `1225373770662335` (MOLOSOC EN Facebook Page ID) |
   | `META_ACCESS_TOKEN_EN` | EN System User token from step 6 |

   Optional, for a stricter Page↔Instagram pairing cross-check:
   `META_IG_ACCOUNT_ID_CZ`, `META_IG_ACCOUNT_ID_EN`.

   You can add just one language's secrets first — the connection test
   reports an unconfigured language as `SKIP`, not a failure.

## Running the connection test

In CI: the **Meta Connection Test (read-only)** workflow
(`.github/workflows/meta-connection-test.yml`). Dispatch it manually, or push
to this folder.

Locally:

```bash
pip install -r automations/social/requirements.txt pytest

export META_APP_ID_CZ='1811329706700638'
export META_APP_SECRET_CZ='...'
export META_FB_PAGE_ID_CZ='670138019527343'
export META_ACCESS_TOKEN_CZ='...'

export META_APP_ID_EN='1537667540920982'
export META_APP_SECRET_EN='...'
export META_FB_PAGE_ID_EN='1225373770662335'
export META_ACCESS_TOKEN_EN='...'

python3 automations/social/meta_connection_test.py
```

Flags: `--lang {cz,en,both}` (default `both`), `--require` (fail instead of
skip when the requested language isn't configured yet).

## Reading the output

For each configured language the report shows:

- the token's identity (`/me`)
- the Facebook Page it can reach, and the **page tasks** the token can
  perform on it (`CREATE_CONTENT` is the one that matters for posting)
- the linked Instagram account, or a warning if none is linked
- (if that language's `META_APP_ID_*`/`META_APP_SECRET_*` are set) the
  token's exact granted scopes and expiry, via `/debug_token`
- a capability line for each of the four things Stage 1 needs to support:
  **Facebook image posts, Facebook Reels, Instagram image posts, Instagram
  Reels** — `YES` when the required permission(s) and pairing are confirmed
  present, `NO` when something required is missing, `UNKNOWN` when scope
  introspection wasn't available (add that language's `META_APP_ID_*`/
  `META_APP_SECRET_*` to resolve it) and only the weaker page-task/pairing
  proxy could be checked

## Tests

```bash
pip install -r automations/social/requirements.txt pytest
python3 -m pytest automations/social/ -q
```

Fully offline against a stubbed Graph API client — no credentials, no
network, no live Meta calls. Covers: every request is a GET to a read
endpoint (never `/media`, `/photos`, `/videos`, `/video_reels`, `/feed`);
tokens and app secrets never reach printed output, including when a Graph
API error echoes a token back in its message; an unconfigured language
reports `SKIP` (or fails only with `--require`); Page↔Instagram pairing
matches/mismatches are both handled; and the capability matrix is correct
for full scopes, partial scopes, and the "scopes unknown" fallback case.

## Credential hygiene

No credential is ever printed. Every token is registered with `redact()` the
moment it's read (see `meta_common.py`, same approach as
`automations/analytics/analytics_common.py`), and `access_token` is always
sent as a query parameter, summarized with `mask_token()` before it would
ever reach a log line — the raw value is not printed anywhere in this
module. `redact()` also strips `access_token=...` query strings and
`"access_token": "..."`-shaped JSON fields wholesale, so even a Graph API
error that echoes the request URL back can't leak one.

Never commit a token, App Secret, or key file. `.gitignore` already excludes
`.env`, `*.env` and `secrets/`; keep local credentials outside the repo.

## Next steps after this Stage 1 passes

Not part of this task — flagged here so the source-of-truth trail is clear:

- Reading `MOLOSOC_Master_Publishing_Schedule` from Google Drive and mapping
  its `Language` column to the right CZ/EN credential set.
- An actual (test, then real) upload flow for Instagram Reels and Facebook
  Reels, which needs the container-create-then-poll-then-publish sequence
  this read-only script deliberately does not exercise.
- TikTok and YouTube connections (explicitly out of scope for this task).
- Wiring up scheduling/publishing itself — still gated on manual approval
  per the task's "do NOT publish/schedule anything yet".
