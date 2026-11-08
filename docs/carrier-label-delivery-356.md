# Carrier label PDF + dispatch mail, Phase 3 (disabled, mocks only) — Issue #356

Follow-up to #345, #352 (PRs #351, #354, #355). **Nothing here is live.** No carrier call, no real label, no mail, no order-status change, no historical order, no production enablement. Inspected sources: PPL CZ **1.1.3** (tag `1.1.3`) and Packeta **2.3.2** (tag `v2.3.2`), read from the public GitHub repositories this session.

## Carrier findings (from the actual plugin source)

### Packeta 2.3.2 — native auto-submission exists, label retrieval is admin-only
- `Order/PacketAutoSubmitter` is registered only if the plugin option "allow auto-submission" is on. Per payment gateway an admin maps one event: `onOrderProcessing` (hook `woocommerce_order_status_processing`), `onOrderCompleted` (`woocommerce_order_status_completed`) or `onOrderCreationFE` (async, at checkout). On the event it calls `PacketSubmitter::submitPacket()`.
- **Duplicate protection:** `submitPacket()` only creates a packet when `! $order->isExported()`, so a repeated event for an already-exported order does not create a second packet.
- **Danger:** `onOrderCreationFE` fires at order creation, before payment. It must never be mapped for Comgate or bank transfer. Use `onOrderProcessing` only. Whether the Comgate plugin moves a card order to `processing` only after PAID is exactly what the paid check below relies on.
- **Label PDF:** `Order/LabelPrint::outputLabelsPdf()` is an admin page: it reads order ids from a transient, calls SOAP `packetsLabelsPdf` / `packetsCarrierLabelsPdf`, then `echo`es the PDF and `exit`s. It cannot be called headless without re-implementing it against plugin internals (`Client`, labelPrintParametersService). No filter or action exposes the PDF.
- **Choice:** keep native auto-submission (not re-implemented). The delivery stage waits for the packet (the provider reports `packet_not_submitted` until it exists). Fetching the PDF unattended is the open blocker.

### PPL CZ 1.1.3 — no hook, no headless path
- No `woocommerce_order_status_*` or payment hook exists anywhere in the plugin; shipments are created from the admin UI only.
- Labels: `Admin\CPLOperation::createPackages($batchId)` (live CPL call, locks the batch) then `getLabelContents($remoteBatchId, ...)`. They need `BatchData`/`ShipmentData` built from internals. The REST controller (`/wp-json/ppl-cz/v1/shipment-batch/{id}/create-labels`, `refresh-labels`) is protected by `check_permission` (logged-in admin capability).
- **Choice:** no automated PPL integration. Safe options are (a) manual "Tisk etiket" by an admin, or (b) a later, separately approved authenticated call to the REST batch endpoints with PPL sandbox credentials. Calling `CPLOperation` directly is not a stable API and is not done.

### Comgate transaction-id condition (`wf_gateway_tmp_transaction_id`)
- The WisdomFactory Comgate plugin source (`wf-woo-comgate`) is not public and was not retrievable, so the claim "a paid transaction id differs from the temporary id" **cannot be verified from code** and is not assumed.
- Current rule (PR #355) is fail-closed: a card order is accepted only when `processing`, Comgate gateway, non-empty transaction id, `is_paid()`, **and** transaction id ≠ tmp id. If the real plugin stores the same value in both after payment, every card order is *rejected* (safe, but nothing would be mailed). It can never accept an unpaid order on this condition.
- **Required controlled check (Žaneta, staging, one Comgate test order, read-only):** after paying, report whether `get_transaction_id()` equals the `wf_gateway_tmp_transaction_id` meta. If equal, the comparison must be dropped and replaced by another signal (e.g. a Comgate "PAID" order note) — decided by Žaneta, not guessed.

## What this PR adds (inert)

`site/mu-plugins/molosoc-carrier-label-delivery.php`:
- Gate: `wp_get_environment_type()` is `staging`/`local` **and** `MOLOSOC_LABEL_DELIVERY_ENABLED === true`. Hook `woocommerce_order_status_processing` priority 30. Production: nothing registers.
- Eligibility reuses Phase 1 `molosoc_ld_decide()` (processing; Comgate-confirmed card or COD; never bank transfer; after the `molosoc_label_dispatch_since` cut-off; known carrier; sizes incl. zero-price gift pairs and multiple lines).
- Stages `label_ready` → `mailing` → `mailed` (+ `attention`), persisted in order meta `_molosoc_label_delivery_state`, carrier ref in `_molosoc_label_delivery_ref`, tries in `_molosoc_label_delivery_tries`. Audit rows (append-only, `stage: delivery`) in `_molosoc_label_dispatch_audit`: ids, subject, sha256 and size only.
- PDF validation (`%PDF-` header, `%%EOF`, page object, 200 B–5 MB); an HTML error page or truncated file is never mailed.
- Provider and mailer are injected (`molosoc_label_delivery_provider`, `molosoc_label_delivery_mailer`). Any result with `live=true` is refused. Shipped implementations are mocks (per-order options outbox `molosoc_ld3_mock_outbox_<order id>`, no `wp_mail`).
- Idempotency: `mailed` is terminal; per-order lock; eligibility and state re-read after the lock. The provider is called with the stored ref (a real one must fetch, not create); a different ref returned → `attention` (possible duplicate shipment).
- Mail is **at-most-once**: `mailing` is written before the mailer call; if a run dies after it, the next run goes to `attention` and does not resend. A definite mailer failure returns to `label_ready` and retries (max 3 tries, then `attention`).
- Subject `{PPL|Zásilkovna} | {N} kus/kusy/kusů | {qty}x {size}, ...` to `jarka01@atlas.cz` (CC `hello@molosoc.com`, same message, Issue #361), attachment `ppl-<id>.pdf` / `zasilkovna-<id>.pdf`.

Tests: `tests/test_carrier_label_delivery_356.py` (real PHP) cover happy paths, Comgate/COD/bank transfer/on-hold/cut-off, duplicates, lock, provider/mailer failure and retry, invalid PDF, ref change, crash-after-mailing, exception, max tries, live refusal, recheck after lock, gate, and static bans on any live call.

## Operator instructions (staging only; nothing performed by this PR)
1. Stage only: `WP_ENVIRONMENT_TYPE=staging`; in `wp-config.php` add `MOLOSOC_LABEL_DISPATCH_DRY_RUN`, `MOLOSOC_LABEL_DISPATCH_STAGING`, `MOLOSOC_LABEL_DELIVERY_ENABLED` (all `true`) and set option `molosoc_label_dispatch_since` to "now".
2. Place one test order; read order meta `_molosoc_label_delivery_state` and the audit rows; read option `molosoc_ld3_mock_outbox_<order id>` for the (mock) message.
3. State `attention`: investigate from the audit (`mail_state_unknown` = check the real mailbox before anything else; `ref_changed` = check the carrier for a duplicate shipment). Clear by deleting `_molosoc_label_delivery_state` (and the tries meta) only after that check; a stuck `molosoc_ld3_lock_<id>` option older than a few minutes may be deleted.
4. Retry: `molosoc_ld3_run( <order_id> )` (e.g. `wp eval`) on staging.

## Blockers before any live provider/mailer (all need Žaneta)
1. Packeta: label PDF fetch has no headless API (admin-page `exit`). Needs approval to build a provider on `Client::packetsLabelsPdf` and a Packeta sandbox API password, and the staging check from #352 (which status triggers native auto-submission; one packet id only).
2. PPL: no hook/headless path; needs sandbox credentials and approval for authenticated REST batch calls.
3. Comgate: tmp-id vs transaction-id check above.
4. Mail: a live mailer (with SPF/DKIM-ready sender) is a separate approved phase; this PR defines the contract only.
5. A controlled single-order end-to-end test on staging, then explicit `ZANETA_DECISION` to activate. Nothing is activated by merging this PR.
