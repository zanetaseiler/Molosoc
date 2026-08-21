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

## The IAM this depends on

Two conditioned grants have to exist before any of this runs, and both are
specified in `molosoc-private/docs/email-evidence-identity.md`:

| Identity | Needs | Why |
| --- | --- | --- |
| The email evidence **writer** (new, keyless, in `molosoc-private`) | `objects.create` + `objects.get` under `reports/email/`, and `objects.delete` on **exactly** `reports/email/latest.json` | to publish the document and advance the pointer, and nothing else |
| The evidence **reader** (existing, used by the Growth Engine) | its existing `objects.get` condition widened to name `reports/email/latest.json` and `reports/email/data/**` | the Growth Engine reads email as a second feed; without this its email channel reports unavailable |
| **This repository's** existing storage identity | `objects.get` on `reports/email/` added | the Email card on the weekly dashboard reads the same document. Read only — this repository never writes the email feed |

No service-account JSON key is involved in the first two. `objects.list` is
absent everywhere: every read here follows a pointer, and an identity that can
list can enumerate the whole bucket.

## Nothing here can send email

Worth saying plainly for a set of workflows with "email" in their names.

| Repository | Holds a Brevo key | Can send |
| --- | --- | --- |
| `molosoc-private` | yes — and it is the **only** secret that workflow reads | **no** — its client class has one method and it hard-codes `GET` |
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
| — its cloud credential | keyless (Workload Identity Federation) | no key exists to rotate |
| Render the report | Growth Engine → **Email Marketing Report** | Manual, type `render` |
| Publish the page | here → **Publish Email Marketing Report** | Manual, type `publish` |
| Email card on the overall report | here → **Weekly Marketing Analysis** | Automatic, Wednesdays 06:15 UTC |

The collection runs 45 minutes after the weekly analysis so both describe the
same Monday–Sunday week and can be read side by side. The card picks up whatever
evidence exists at that moment; on the first week it will correctly say the
channel is not yet publishing.

## Verifying a password-protected report

The MOLOSOC reports directory is protected by HTTP Basic Auth
(`Protected 'public_html/Trafficdom.com/reports/molosoc'`), deliberately and
permanently. Client reports are not public.

That makes an unauthenticated GET useless as a check: it returns 401 whether the
report is perfect, corrupt or absent. Every live verification therefore goes
through the realm, and **a 401 remains a failure** — it is never accepted as
"protected, therefore fine".

### The one mechanism

`automations/analytics/verify_published_report.sh`, wrapped by the composite
action `.github/actions/verify-report`. One implementation, five call sites:

| Workflow | What it verifies |
| --- | --- |
| `publish-email-report.yml` | the Email report, plus Analytics and Growth untouched |
| `publish-growth-report.yml` | the Growth report, plus Analytics untouched |
| `weekly-marketing-report.yml` | the overall dashboard |

`diagnose-report-serving.yml` authenticates too, but deliberately does **not**
use the action: its requests are probes whose status code is the finding, and a
tool you reach for when serving looks wrong has to be able to report a 401
rather than exit on one.

### What it asserts, in order

1. **Credentials are configured** — exit **2**, distinct from a failure. An
   unset secret and a wrong password are indistinguishable on the wire, and
   reporting the first as the second sends you to cPanel to debug a GitHub
   setting.
2. **HTTP 200.** A 401 fails, and says the realm rejected the credentials
   rather than implying the protection should be removed.
3. **The marker** — case-insensitive, because a title-case change has broken
   this check before.
4. **SHA256, where known.** The email and growth publishers pass the artifact
   hash, so the bytes *served* are compared to the bytes *published* — rather
   than trusting the upload's own report of success.

### Credentials

`REPORT_BASIC_AUTH_USER` and `REPORT_BASIC_AUTH_PASSWORD`, from Actions secrets
only. They are written to a mode-600 curl config under `RUNNER_TEMP` and removed
on exit; nothing passes a credential on a command line, where `ps` could read it
and `set -x` would echo it. `--location-trusted` is deliberately unused, so
credentials are never replayed to another host on a redirect.

### Adding another protected client folder

The action names no client and no secret. Add a secret pair — for example
`REPORT_BASIC_AUTH_USER_CLIENTX` — and pass it at the call site. No change to
the action or the script.
