# Email marketing reporting

Email is the first channel in this system whose evidence comes from a producer
that is **not** the analytics automation in this repository. Three repositories
are involved, each doing the one thing it is already equipped to do.

```
molosoc-private                    trafficdom-growth-engine        this repository
───────────────                    ────────────────────────        ───────────────
email/intel/  (GET-only Brevo)
  collect · normalize · diagnose
  publish  ──▶ GCS reports/email/
                    │
                    ├──────────────▶ email-report workflow
                    │                 2 GETs, render index.html
                    │                 upload artifact ─────────▶ download, verify
                    │                                            publish_dashboard.py
                    │                                              --section email-marketing
                    │                                                      │
                    │                                                      ▼
                    │            /public_html/Trafficdom.com/reports/molosoc/email-marketing/
                    │
                    └──────────────────────────────────────────▶ weekly-marketing-report
                                                                  reads the same document
                                                                  → the Email card on
                                                                    reports/molosoc/
```

## One artifact, three consumers

The orchestrator publishes **one** normalized evidence document per week:

| Object | Purpose |
| --- | --- |
| `reports/email/latest.json` | the pointer — the only object ever rewritten |
| `reports/email/data/YYYY/MM/YYYY-MM-DD/email.json` | the document — written once, never overwritten |

Three things read it, and none of them ever sees a Brevo response:

1. the **dedicated Email Marketing report**, rendered by the Growth Engine;
2. the **Email card** on the weekly Analytics dashboard, rendered here by
   `automations/analytics/email_summary.py`;
3. the Growth Engine's **email channel**, as evidence for cross-channel
   prioritisation.

The card reads the artifact, never the rendered email page. A dashboard that
scraped another report for numbers would empty itself the first time that
report's layout changed, and would do it silently.

## The read is two GETs, and the second key is untrusted

`email_summary.fetch()` reads the pointer, then reads the one document the
pointer names — after checking that the key it names lives under
`reports/email/data/` and ends in `.json`. That key arrives **inside a
document**, so it is input rather than instruction: a partially written pointer,
a publish bug or a tampered object could name any object in the bucket.

A pointer naming anything else is a hard failure in the workflow. Everything
else about email — a missing pointer, an unpublished week, an unreadable
document — is a **warning**: it costs the Email card and nothing else. A weekly
report that failed because a second channel was quiet would be a worse report
than one whose card says the channel is not yet publishing evidence.

## Publishing the page

Identical to the Growth report, one fixed segment different:

```
publish_dashboard.py --section email-marketing
  → /public_html/Trafficdom.com/reports/molosoc/email-marketing/index.html
```

Same publisher, same connection, same guards: a derived destination, a
WordPress-directory refusal, a server-side working-directory check, one file
named `index.html`, and no deletion or rename. `ALLOWED_SECTIONS` is a closed
set — `--section` is an argparse choice, so an unknown value is rejected by the
parser before any path exists.

The three reports are siblings-and-parent and can never overwrite each other:

| Report | Address |
| --- | --- |
| Weekly Analytics | `https://trafficdom.com/reports/molosoc/` |
| Growth | `https://trafficdom.com/reports/molosoc/growth/` |
| Email Marketing | `https://trafficdom.com/reports/molosoc/email-marketing/` |

With a section set, the path check refuses a destination ending in `molosoc`, so
a sectioned publish can never land on the Analytics report. The publish workflow
also checks the other two pages from the outside afterwards, rather than only
asserting beforehand.

`GROWTH_ENGINE_ARTIFACT_TOKEN` is reused unchanged — it already grants
Actions: Read-only on the Growth Engine repository, which is exactly what
downloading the email report artifact needs. No new credential is required in
this repository.

## Nothing here can send email

Worth saying plainly for a set of workflows with "email" in their names.

| Repository | Holds a Brevo key | Can send |
| --- | --- | --- |
| `molosoc-private` | yes | **no** — its client class has one method and it hard-codes `GET` |
| `trafficdom-growth-engine` | no | no — it imports no SMTP or platform SDK, and does not know the credential's name |
| this repository | no | no — it downloads an HTML file and uploads it over SFTP |

Each of those is asserted by a test rather than left to review.

## What the report cannot measure yet

Order and revenue attribution. Every document marks both `unavailable` with a
stated reason, and both reports show that at reading level rather than behind a
disclosure. Two things would have to change, and both are decisions rather than
code:

1. the shop would need to send a purchase event carrying the message that
   preceded the order, so an order can be attributed to a send rather than
   merely coincide with one;
2. someone would have to choose the attribution rule — the window, and what
   happens when a customer received three automations before ordering.

Until then the reports say so. A revenue figure of `0` would be read as "email
sold nothing", which is a different claim from "we cannot see what email sold",
and only the second one is true.

## Running it

| Step | Where | Trigger |
| --- | --- | --- |
| Collect and publish evidence | `molosoc-private` → **Email intelligence** | Wednesdays 07:00 UTC, or manual |
| Render the report | Growth Engine → **Email Marketing Report** | Manual, type `render` |
| Publish the page | here → **Publish Email Marketing Report** | Manual, type `publish` |
| Email card on the overall report | here → **Weekly Marketing Analysis** | Automatic, Wednesdays 06:15 UTC |

The collection runs 45 minutes after the weekly analysis so both describe the
same Monday–Sunday week and can be read side by side. The card picks up whatever
evidence exists at that moment; on the first week it will correctly say the
channel is not yet publishing.
