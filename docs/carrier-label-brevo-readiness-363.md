# Carrier label: Brevo mail + carrier readiness (Issue #363)

**Status: repository-only.** Nothing in this document has been checked against the live site. The cloud session cannot reach molosoc.com or wp-admin: the proxy returns 403 and the session has no credentials. Every live fact below is **unverified** until the operator runs the read-only checks.

## What the repository shows

| Topic | Repo evidence | Verdict |
|---|---|---|
| Brevo plugin | Only *Brevo for WooCommerce* is referenced (`site/mu-plugins/brevo-checkout-capture-shim.php`). | Whether it relays `wp_mail()` (transactional SMTP/API) is **unverified**. |
| Mail overrides | No `pre_wp_mail`, `wp_mail_from` or SMTP `phpmailer_init` hook in `site/`. | The transport is whatever WordPress or the active plugin provides. |
| Label mail To/Cc | `molosoc_ll_mail()` sends one `wp_mail` to `jarka01@atlas.cz` with `Cc: hello@molosoc.com` (fixed constants, exact-match validated). | Covered by tests. |
| Attachment | The PDF is validated, written to a private temp file, passed to `wp_mail` as an attachment, and always removed. | Covered by tests. Whether Brevo relays the attachment is unverified. |
| From | Before #363: **no From header**. WordPress then defaults to `wordpress@<host>` unless a plugin forces a sender. | Gap. Closed by an opt-in (below). |
| WooCommerce emails | No code in this PR touches WooCommerce mail. The new header applies only to the label mail, and only when opted in. | Unchanged by construction. |
| Comgate 1.1.40 | Strict rule by default. `MOLOSOC_LABEL_COMGATE_TMPID_RULE = 'paid_status'` is opt-in (#358). | Choosing the rule needs the live read (check 5). |
| Packeta 2.3.2 | Fetch-only, via SOAP `packetLabelPdf`. The meta key and password are supplied by the operator. | Unverified until the one-order test. |
| PPL CZ 1.1.3 | No headless label path. Orders go to `attention` with reason `ppl_manual_label_required`. | Unchanged. Kept manual. |

## Code change in this PR (OFF by default)

`MOLOSOC_LL_MAIL_FROM_EXPLICIT === true` in `wp-config.php` adds exactly one header: `From: MOLOSOC <hello@molosoc.com>`. It is built only from constants.

- Without the constant, or with any truthy value other than `true`, the headers are byte-identical to before.
- The opt-in changes nothing else: recipient, Cc, subject, filename and PDF validation, at-most-once state and the allowlist gate all still apply. The label pipeline itself stays inert unless `MOLOSOC_LABEL_LIVE_ENABLED` and the one-order allowlist are set (#358).
- A `wp_mail_from` filter from an SMTP or Brevo plugin may still override the sender. Brevo also rejects senders that are not validated. So enable this option only after checks 1 and 2 below.

## Smallest read-only operator checks (no secrets, no sends, no setting changes)

These are suitable for Claude with Chrome on a logged-in wp-admin, or for Žaneta. Paste only the statuses.

1. **Transport.** In wp-admin → Brevo → Transactional emails (SMTP): is "Enable Brevo to send transactional emails" ON? List any other SMTP plugin (WP Mail SMTP, Post SMTP, FluentSMTP) and its version. Note the configured sender name and address.
2. **Sender authentication.** In Brevo → Senders, domains & dedicated IPs: is `molosoc.com` authenticated (DKIM and DMARC green)? Is `hello@molosoc.com` a verified sender?
3. **Existing WooCommerce mail.** In the Brevo transactional log, check the most recent WooCommerce order email. Record its sender, and whether it appears in the log at all. This confirms the transport and the effective From without sending anything.
4. **Attachments.** These are proven only by one hand-run `wp_mail` with a small PDF to `jarka01@atlas.cz`, Cc `hello@`. That is a **send**, so it needs a separate `ZANETA_DECISION`.
5. **Comgate.** On one paid and one unpaid Comgate order, compare `_transaction_id` with `wf_gateway_tmp_transaction_id`. Report only "equal" or "different".
6. **Packeta.** On one exported order, record the meta **key name** that holds the packet id.

## Decision rule for `MOLOSOC_LL_MAIL_FROM_EXPLICIT`

- If check 3 shows WooCommerce mail already leaves as `hello@molosoc.com`, leave the option unset. The same transport applies to the label mail.
- If the sender is `wordpress@…` or something else, and check 2 shows `hello@molosoc.com` is verified, set the option to `true` for the one-order test (#358 plan).
