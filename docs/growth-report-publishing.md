# Publishing the TrafficDom Growth report

The Growth report is rendered in the **Growth Engine** repository
(`zanetaseiler/trafficdom-growth-engine`) and published from **this** one, using
the SFTP path that already publishes the weekly Analytics dashboard.

```
Growth Engine                            this repository
─────────────                            ───────────────
real evidence (2 GETs)
1 gpt-5.6-terra request
render index.html
upload artifact  ──────────────────────▶ download artifact
                                         verify it
                                         publish_dashboard.py --section growth
                                                     │
                                                     ▼
                         /public_html/Trafficdom.com/reports/molosoc/growth/index.html
```

## Why the split

The report-host credentials (`REPORTS_SSH_*`, `REPORTS_SFTP_USER`,
`REPORTS_BASE_PATH`) can write `reports/molosoc/index.html` — the live Analytics
dashboard. They stay in the one repository that already needs them. The Growth
Engine holds no report-host credential of any kind and has no transport at all;
its output reaches this job as a GitHub Actions artifact, which cannot reach a
website by itself.

There is **no second publisher**. `automations/analytics/publish_dashboard.py`
does the upload, with the guards it already had: a derived destination, a
WordPress-directory refusal, a server-side working-directory check, one file
named `index.html`, and no deletion or rename. `--section growth` deepens the
destination by one fixed segment from a closed set.

## The one credential that has to be added

Downloading an artifact from **another repository's** workflow run is not
covered by the automatic `GITHUB_TOKEN`: that token is scoped to this repository
only. One secret is required here:

| Secret | `GROWTH_ENGINE_ARTIFACT_TOKEN` |
| --- | --- |
| Kind | **Fine-grained** personal access token — not a classic PAT |
| Resource owner | `zanetaseiler` |
| Repository access | **Only select repositories** → `zanetaseiler/trafficdom-growth-engine` and nothing else |
| Repository permissions | **Actions: Read-only**. Metadata: Read-only is added automatically and is the only other permission. |
| Everything else | Left at "No access" — no Contents, no Secrets, no Workflows, no organisation permissions |
| Expiry | Set one. 90 days is a reasonable default; the workflow fails closed when it lapses. |

A classic PAT is not acceptable here: its narrowest useful scope (`repo`) grants
read **and write** across every repository the account can reach. The
fine-grained token above can do exactly one thing — list and download Actions
artifacts from one repository — and can do nothing at all to this one.

The secret goes in **this** repository (Settings → Secrets and variables →
Actions → Secrets). Nothing is added to the Growth Engine.

## Running it

1. In the Growth Engine, run **Growth Report (manual only)** with
   `client: molosoc` and `confirm: render`. It prints the artifact name and the
   file's sha256, and publishes nothing.
2. Copy that run's id from its URL.
3. Here, run **Publish Growth Report (manual only)**:

   | Input | Value |
   | --- | --- |
   | `run_id` | the Growth Engine run id from step 2 |
   | `artifact` | `growth-report-molosoc` (the default) |
   | `sha256` | optional — paste what step 1 printed, to check the bytes |
   | `confirm` | `publish` |

The job refuses unless the artifact holds exactly one non-empty `index.html`
that looks like a Growth report and does not look like the Analytics dashboard.
It then dry-runs the publisher, publishes, checks the Growth page is live, and
finally re-checks that `https://trafficdom.com/reports/molosoc/` is still
serving the Analytics dashboard.

## What this does not do

* No schedule — both workflows are manual dispatch only.
* No deletion, rename or recursive upload, at either end.
* No write to `reports/molosoc/index.html`: with `--section growth` the path
  check refuses a destination ending in `molosoc`, and the server's own working
  directory is compared before anything is sent.
* No new transport. FTPS and WebDAV were both abandoned; this is the same SFTP
  connection the weekly dashboard has used all along.
