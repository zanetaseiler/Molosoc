# One-time setup: WordPress Application Password (needed before content-sync works)

This is a 5-minute manual step, done once, no plugin required (built into WordPress since 5.6).

## 1. Create the application password
1. Log into `wp-admin` on **staging** first (not live — test the pipe before it touches the real site)
2. Go to **Users → Profile** (your own admin user, or better: create a dedicated `content-bot` user with the **Author** or **Editor** role — not Administrator, so a leaked credential can't do full site damage)
3. Scroll to **Application Passwords**
4. Name it `content-sync-github-action`, click **Add New**
5. Copy the generated password immediately — WordPress shows it once and never again. Format looks like `abcd EFGH ijkl MNOP qrst UVWX`.

## 2. Add as GitHub repo secrets
Repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret name | Value |
|---|---|
| `WP_URL` | `https://staging.molosoc.com` (no trailing slash) |
| `WP_USER` | `content-bot` (or whichever user you created) |
| `WP_APP_PASSWORD` | the generated password, spaces included, exactly as shown |

## 3. Confirm the REST API is reachable
From your machine or Claude Code's terminal:
```bash
curl -u "content-bot:abcd EFGH ijkl MNOP qrst UVWX" \
  https://staging.molosoc.com/wp-json/wp/v2/pages
```
Should return JSON (an array, even if empty) — not a 401 or an HTML error page. If it 404s, check that pretty permalinks are enabled (Settings → Permalinks → anything but "Plain").

## 4. Test with one real file
```bash
export WP_URL=https://staging.molosoc.com
export WP_USER=content-bot
export WP_APP_PASSWORD="abcd EFGH ijkl MNOP qrst UVWX"

python3 automations/content-sync/push_to_wp.py seo/pillars/cracked-heels.md
```
Check wp-admin → Pages → you should see "Cracked Heels..." sitting as a **draft**. Open it, confirm it looks right, then hit Publish yourself.

## 5. Once confirmed, repeat steps 1–2 for the **live** site
Separate `content-bot` user, separate Application Password, separate GitHub secrets (`WP_URL_PROD`, `WP_USER_PROD`, `WP_APP_PASSWORD_PROD`) — keep staging and live credentials fully independent so a staging leak can't touch production.

## Going forward
Any `.md` file added or edited under `seo/pillars/`, `seo/spokes/`, or `content/` and pushed to the `staging` branch auto-lands in WordPress as a draft within a minute or two. You still click Publish. That's the whole automation — write markdown, git push, review, publish.
