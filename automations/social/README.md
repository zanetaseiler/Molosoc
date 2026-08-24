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
expected (Page ↔ Instagram pairing), and — when `META_APP_ID`/
`META_APP_SECRET` are also set — exactly which permissions the token was
granted.

**Does not prove:** that an actual image or Reels upload will succeed. Reels
specifically go through a multi-step upload-and-poll flow (create a video
container, poll until Meta finishes processing it, then publish) that has
failure modes — wrong aspect ratio, duration limits, encoding issues — no
read-only call can catch. Confirming that end-to-end requires an actual test
upload, which is explicitly out of scope until publishing is approved.

## Why CZ and EN are separate credentials

Each language gets its own Facebook Page, its own linked Instagram
professional account, and its own access token/secret set — never a shared
token. That's what makes "support separate CZ and EN accounts" and "the
Google Drive publishing schedule as the source of truth" actually work later:
`MOLOSOC_Master_Publishing_Schedule` tags every row with a `Language` column
(CZ/EN) and each row needs to land on that language's own Page/Instagram
account, not on a shared one.

**Before wiring up secrets, confirm in Meta Business Suite whether MOLOSOC
already has two separate Facebook Pages + Instagram accounts (one CZ, one
EN), or a single shared Page/Instagram pair.** The live site currently links
to exactly one of each — `facebook.com/molosoc` and `instagram.com/molosoc_`
(see `site/theme/footer.php`) — so if a second CZ or EN pair doesn't exist
yet in Business Suite, that's a decision (and Business Suite setup step) for
a person, not something this script can discover or create.

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

2. **Create (or reuse) a Meta Developer App.** At
   [developers.facebook.com/apps](https://developers.facebook.com/apps),
   create an app of type "Business" (or use an existing one already
   associated with the MOLOSOC Business Manager). Note the **App ID** and
   **App Secret** (App Settings → Basic) — these become `META_APP_ID` /
   `META_APP_SECRET`. The App Secret is only used here to introspect tokens
   via `/debug_token`; it never authorizes posting by itself.

3. **Add the Instagram Graph API + Facebook Login for Business products** to
   that app (App Dashboard → Add Product), so the app can request
   `pages_*` and `instagram_*` permissions.

4. **Create a System User** in Business Manager: **Settings → Users → System
   Users → Add**. Create one per language (`molosoc-social-cz`,
   `molosoc-social-en`) or one shared system user assigned to both Pages —
   either works, since the token itself is what gets scoped per-Page below.

5. **Assign assets to the System User.** For each system user, **Add
   Assets → Pages** → select that language's MOLOSOC Page → grant it at
   least "Manage Page" access (this is what's needed for
   `pages_manage_posts`). The linked Instagram account doesn't need a
   separate asset assignment — it inherits from the Page.

6. **Generate the System User's access token.** On the System User's detail
   page, **Generate New Token** → select the app from step 2 → select these
   permissions:
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
   variables → Actions, on this repo:

   | Secret | Required | What it is |
   |---|---|---|
   | `META_APP_ID` | recommended | App ID from step 2 |
   | `META_APP_SECRET` | recommended | App Secret from step 2 |
   | `META_FB_PAGE_ID_CZ` | for CZ | MOLOSOC CZ Facebook Page ID |
   | `META_ACCESS_TOKEN_CZ` | for CZ | CZ System User token from step 6 |
   | `META_IG_ACCOUNT_ID_CZ` | optional | CZ Instagram professional account ID, for pairing cross-check |
   | `META_FB_PAGE_ID_EN` | for EN | MOLOSOC EN Facebook Page ID |
   | `META_ACCESS_TOKEN_EN` | for EN | EN System User token from step 6 |
   | `META_IG_ACCOUNT_ID_EN` | optional | EN Instagram professional account ID, for pairing cross-check |

   You can add just one language's secrets first — the connection test
   reports an unconfigured language as `SKIP`, not a failure.

## Running the connection test

In CI: the **Meta Connection Test (read-only)** workflow
(`.github/workflows/meta-connection-test.yml`). Dispatch it manually, or push
to this folder.

Locally:

```bash
pip install -r automations/social/requirements.txt pytest

export META_APP_ID='...'
export META_APP_SECRET='...'

export META_FB_PAGE_ID_EN='...'
export META_ACCESS_TOKEN_EN='...'

export META_FB_PAGE_ID_CZ='...'
export META_ACCESS_TOKEN_CZ='...'

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
- (if `META_APP_ID`/`META_APP_SECRET` are set) the token's exact granted
  scopes and expiry, via `/debug_token`
- a capability line for each of the four things Stage 1 needs to support:
  **Facebook image posts, Facebook Reels, Instagram image posts, Instagram
  Reels** — `YES` when the required permission(s) and pairing are confirmed
  present, `NO` when something required is missing, `UNKNOWN` when scope
  introspection wasn't available (add `META_APP_ID`/`META_APP_SECRET` to
  resolve it) and only the weaker page-task/pairing proxy could be checked

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
