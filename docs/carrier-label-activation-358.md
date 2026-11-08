# Carrier label activation gate — Issue #358 (OFF by default)

Builds on #345/#352/#356 (PRs #351, #354, #355, #357). **Merging this PR activates nothing.** No carrier call, packet, e-mail, order change or production configuration happens until Žaneta adds the wp-config constants below, in a separate approved step.

## What this adds

`site/mu-plugins/molosoc-carrier-label-live.php` (inert unless both constants are set):

| Concern | Behaviour |
|---|---|
| Opt-in | `MOLOSOC_LABEL_LIVE_ENABLED === true` (truthy values do not count). |
| Allowlist | `MOLOSOC_LABEL_LIVE_ORDER_IDS` must be an array of **exactly one** positive int. Any other order returns before any lookup or audit. No bulk/historic processing is possible (also the Phase 1 `molosoc_label_dispatch_since` cut-off and `processing` status). |
| Mock conflict | Refused while `MOLOSOC_LABEL_DELIVERY_ENABLED` (mock stage) is also true. |
| Eligibility | Unchanged `molosoc_ld_decide()`: status `processing`; Comgate-confirmed card **or** COD; bank transfer and unknown methods excluded; known carrier; sizes/quantities → subject `{PPL\|Zásilkovna} \| N kus/kusy/kusů \| 1x M, 2x L`. |
| Mailer | Real `wp_mail()` to `jarka01@atlas.cz` with one `Cc: hello@molosoc.com` header (fixed constant, exact-match validated, Issue #361; a single message), PDF attached from a temp file that is always removed (also on exception). Recipient, subject, filename, `%PDF` structure re-validated immediately before sending. `wp_mail` true = accepted for sending, not delivered. |
| Idempotency | Shared state machine: `mailing` is written **before** `wp_mail`; a crash afterwards → `attention`, never a resend (at-most-once). `mailed` is terminal. Per-order lock. Stored carrier ref; a different ref → `attention` (possible duplicate shipment). Max 3 failed tries, then `attention`. |
| Retry | Retryable outcomes (`packet_not_submitted`, fetch/mail failure, bad PDF) schedule one WP-cron retry (5 min) under the tries limit; `attention` outcomes never retry. |
| Audit | Append-only order meta `_molosoc_label_dispatch_audit` (`stage: live`): ids, subject, sha256, size, outcome — never the PDF or customer data. `result: mailed, live: true` on success. |
| Never | Creates packets/shipments, changes order status, mails customers, touches other orders. |

### Comgate transaction-id rule (blocker, resolved by choice)
Plugin source is not public, so whether a paid order's transaction id differs from `wf_gateway_tmp_transaction_id` is unverified. Default stays **strict** (equal ids = unpaid; a legitimate order might be *rejected*, never accepted unpaid). New opt-in `MOLOSOC_LABEL_COMGATE_TMPID_RULE = 'paid_status'` drops only that comparison; still required: `processing`, Comgate gateway, non-empty transaction id, `is_paid()`. Choose it only if the staging/test-order read shows the ids are equal after payment.

### Packeta (submission + PDF)
- **Submission:** native Packeta auto-submission is kept (it skips already exported orders → no double packets). Map **only** `onOrderProcessing` for Comgate/COD; **never** `onOrderCreationFE` (fires before payment). This file never submits.
- **PDF:** the plugin's label output is an admin page that `exit`s; it has no headless API. The provider instead calls Packeta's own documented SOAP method `packetLabelPdf` for the packet id read from order meta. **Not verified against the live API** — the controlled test is where it is verified. The packet-id meta key and API password are *not guessed*: operator defines `MOLOSOC_LL_PACKETA_PACKET_META` (order meta key holding the packet id — read it off the Packeta-exported test order) and `MOLOSOC_LL_PACKETA_API_PASSWORD`. Missing → fail closed (`attention`, nothing sent).

### PPL
PPL CZ 1.1.3 has no hook or headless label path; only an admin-authenticated REST batch flow. Not automated: PPL orders go to `attention` (`ppl_manual_label_required`), nothing is mailed. The one-order test therefore uses a **Zásilkovna** order. PPL automation needs separate approval + sandbox credentials.

### Honest limits
Packeta SOAP label call and `wp_mail` deliverability (SPF/DKIM, host mail config) are untested here (no network/credentials in CI). Tests cover all logic with injected I/O (`tests/test_carrier_label_live_358.py`).

## Operator steps needed from Žaneta (no secrets in GitHub)
1. Read (do not paste secrets): the order meta key holding the Packeta packet id on a Packeta-exported order; whether Comgate `get_transaction_id()` equals `wf_gateway_tmp_transaction_id` after payment.
2. Ensure Packeta auto-submission maps `onOrderProcessing` only.
3. Put the Packeta API password into `wp-config.php` directly on the server (never in chat/GitHub).

## One-order controlled live test plan (needs separate `ZANETA_DECISION`)
1. Prereqs: this PR merged+deployed (inert); items 1–3 above; test mail host verified by sending a plain `wp_mail` to `jarka01@atlas.cz` by hand once.
2. Place **one** Zásilkovna order (COD is simplest, or a Comgate card order). Note its id `N`, with `molosoc_label_dispatch_since` set to just before it.
3. wp-config: `MOLOSOC_LABEL_LIVE_ORDER_IDS = [N]`, `MOLOSOC_LL_PACKETA_PACKET_META`, `MOLOSOC_LL_PACKETA_API_PASSWORD`, `MOLOSOC_LABEL_LIVE_ENABLED = true` (last). Optionally `MOLOSOC_LABEL_COMGATE_TMPID_RULE`.
4. Move/let the order reach `processing`. Expect: one Packeta packet (native), meta state `mailed`, audit rows `label_ready` then `mailed live:true`, **one** e-mail with correct subject and a readable PDF.
5. Verify in the Packeta admin there is exactly one packet; re-run `molosoc_ll_run(N)` once: expect `already_mailed`, no new mail.
6. Immediately afterwards set `MOLOSOC_LABEL_LIVE_ENABLED` back to false/remove it. Stop on any `attention` state (see audit `reason`: `mail_state_unknown` → check the mailbox first; `ref_changed` → check Packeta for duplicates).

## Activation checklist (after a good test; each step separately approved)
- [ ] Packeta SOAP label call proven; mail received with correct PDF
- [ ] Comgate rule decided from evidence
- [ ] Allowlist replaced by a reviewed multi-order mechanism (this PR deliberately supports one order only)
- [ ] PPL path decided (manual vs authenticated REST), if wanted
- [ ] Monitoring of `attention` states agreed
