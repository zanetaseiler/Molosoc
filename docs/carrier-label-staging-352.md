# Carrier label dispatch, Phase 2 (staging only) — Issue #352

Follow-up to #345 / PR #351. **Nothing here is live.** No real label, no carrier API call, no mail, no order-status change, no production constant, no historical order.

## What was inspected

| Component | Version | Source inspected |
|---|---|---|
| PPL CZ | 1.1.3 | GitHub tag `1.1.3` of `PPL-CZ/PPL-WooCommerce` (`ppl-cz/ppl-cz.php` reports `Version: 1.1.3`). The WordPress.org SVN/zip host is unreachable from the cloud sandbox. |
| Packeta | 2.3.2 | GitHub tag `v2.3.2` of `Zasilkovna/WooCommerce` (`packeta/packeta.php` `Version: 2.3.2`). |
| Comgate (`wf_woo_comgate`) | unknown | **Not retrievable.** No public source under that gateway id was found (GitHub search finds only this repo's references; the two public Comgate plugins found use other ids). |

## Findings

### PPL CZ 1.1.3 — label path
- A PDF exists only after `CPLOperation::createPackages($batchId, $print)` (a live CPL API call) and `CPLOperation::getLabelContents(...)`. Both need `BatchData`/`ShipmentData` built from plugin internals; neither is a hook or filter.
- Public integration points are after-the-fact actions (`pplcz_package`, `pplcz_package_phase`, `pplcz_package_change_phase`) and filters (`pplcz_variable_number`, `pplcz_package_reference`). None triggers generation.
- Shipping method ids start with `pplcz_` (used by the carrier detection).
- **Safest supported path:** the plugin's own admin "Tisk etiket" flow (manual) or its admin REST batch controller, run by a logged-in admin. An unattended call into `CPLOperation` is feasible but is not a stable API and cannot be verified without PPL sandbox credentials.

### Packeta 2.3.2 — label path
- A label PDF exists only after the packet was submitted to the Packeta API (`PacketSubmitter`), then fetched via `Client::packetsLabelsPdf` / `packetsCarrierLabelsPdf` (used by `Order\LabelPrint`). Both are live SOAP calls.
- The only filter on the path is `packeta_create_packet` (adjusts packet data). There is no "generate label" hook.
- Shipping method ids: `packetery_shipping_method` or `packeta_method_*`.
- **Safest supported path:** the plugin's own order-list "Submit" + "Print labels" actions, or its documented bulk actions, run by an admin. Automated submission needs a Packeta API password and a sandbox/test packet.

### Comgate — authoritative paid confirmation (updated 2026-11-08, ZANETA_DECISION)
Read-only production findings from Žaneta: WisdomFactory Comgate plugin **1.1.40**, payment method id **`wf-woo-comgate`** (the code also accepts the legacy `wf_woo_comgate`; the theme in this repo already uses the hyphen id). The plugin calls `$order->payment_complete($transId)` only on a Comgate PAID callback.

A card order is paid only if **all** hold (`molosoc_ld_comgate_paid()`):
1. status exactly `processing`;
2. payment method is the Comgate gateway;
3. non-empty `$order->get_transaction_id()`;
4. `$order->is_paid()` is true;
5. the transaction id differs from `wf_gateway_tmp_transaction_id` (a placeholder written even for unpaid orders; it is never accepted as a signal).

Live audit supporting this: 34 paid card orders have transaction ids, 8 unpaid do not. `date_paid`/`processing` alone are unsafe (order #775 was cancelled after processing). The earlier configurable meta-key approach (`MOLOSOC_LD_COMGATE_CONFIRM_KEY/_VALUE`) is removed. Plugin source is still not public, so the behaviour rests on Žaneta's live audit, not on code reading.

### Order item size meta (updated)
Product 364; variation **424 = L**, **425 = M**. New order item meta `pa_size`, older orders `pa_velikost`; values `l-large` / `m-medium`. `molosoc_ld_item_size()` reads the meta (new key first), falls back to the variation id, and **fails closed** (`sizes_unusable`) on an unknown size or variation, or when meta and variation disagree. Quantities are summed across lines (e.g. order #1100); zero-price gift lines are physical pairs and count.

### Packeta native auto-submission (not activated)
The Packeta plugin has a per-payment-method "Allow packet auto-submission" setting, currently **OFF**. The v2.3.2 source could not be re-downloaded in this sandbox, so how it triggers (status change? which status?), whether it also creates the label, and its duplicate protection are **unverified**. It is not enabled and nothing here depends on it. Preferred over a custom API once verified. Minimum approval step: Žaneta enables it for **one** staging payment method with a Packeta test/sandbox API password, places one test order, and reports (a) the status that triggers it, (b) whether a packet id appears once only after a second status save, (c) whether the label must still be fetched manually.

### PPL batch flow
Existing manual flow: orders bulk action adds to a PPL batch, the plugin submits it to PPL and returns a 4/A4 PDF. Internal endpoints live under `/wp-json/ppl-cz/v1/`; the plugin may mark delivered orders Completed, so Completed is never used as a payment signal. Unattended batch creation would call non-public internals and PPL's live API; it stays out of scope until sandbox credentials and approval exist. The mock adapters keep modelling this boundary.

## What was implemented (all inert by default)

- `site/mu-plugins/molosoc-carrier-label-dispatch.php` (Phase 1, edited):
  - `molosoc_ld_comgate_paid()` + config-driven `molosoc_ld_comgate_from_order()`;
  - size normalisation and canonical-only check;
  - new filter `molosoc_label_dispatch_adapter`; the pipeline **refuses** any adapter result with `live=true` (`live_adapter_refused`);
  - audit row records `mock_ref` (null in Phase 1 dry-run).
  - Still no mail function, no live constant, still needs `MOLOSOC_LABEL_DISPATCH_DRY_RUN`.
- `site/mu-plugins/molosoc-carrier-label-staging.php` (new): mock adapters for PPL and Packeta. Active only if `wp_get_environment_type()` is `staging` or `local` **and** `MOLOSOC_LABEL_DISPATCH_STAGING === true`. Mocks return `MOCK-…` refs, are idempotent per order, and the Packeta mock fails with `packet_not_submitted` until a packet exists, mirroring the real path The submitted state is explicit per-order mock state (option `molosoc_ls_mock_submitted`, default false; set via `molosoc_ls_mock_submit_packet($order_id)`), so a fresh Packeta order fails until simulated submission.
- `tests/test_carrier_label_staging_352.py`: both carriers; Comgate confirmed/unconfirmed; COD; transfer/on-hold; duplicates/retries/failed-then-retry; live-adapter refusal; environment gate; subject `{carrier} | {N} kus/kusy/kusů | {sizes}` with live slugs; static checks that no live call exists.

## Exact blockers

1. **Comgate paid signal**: resolved by Žaneta's live audit (see above); only the plugin source remains unread.
2. **Size meta**: resolved (`pa_size`/`pa_velikost` + variation fallback).
3. **Real label generation** for both carriers needs the carriers' sandbox/test credentials and Žaneta's approval to call non-public plugin internals. Not requested here.
4. **Staging site**: this repo has no staging environment definition; one must exist with `WP_ENVIRONMENT_TYPE=staging`.
5. **Mail**: no sender exists by design. A mail step is a later, separately approved phase.

## Remaining read-only checks for Žaneta
Only the Packeta auto-submission behaviour above (staging, test API password) is still open. Do not paste tokens, emails or addresses.

## Activation prerequisites (none performed here)

1. Merge approval from Žaneta; no deploy performed by this PR.
2. In `wp-config.php` of **staging only**: `MOLOSOC_LABEL_DISPATCH_DRY_RUN`, `MOLOSOC_LABEL_DISPATCH_STAGING`, plus the option `molosoc_label_dispatch_since` (cut-off so no historical order is processed).
3. Place staging test orders and read the audit meta `_molosoc_label_dispatch_audit`.
4. A later phase, separately approved, for sandbox-credential live adapters, Packeta auto-submission and mail.
