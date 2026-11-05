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

### Comgate — authoritative paid confirmation
- `processing` is **not** proof of payment. Any plugin or admin can set it.
- The plugin source is unavailable, so the real confirmation signal is **unverified**. Phase 2 therefore replaces the bare filter with `molosoc_ld_comgate_paid()`: paid only if the order has a transaction id **and** a configured order-meta key holds exactly a configured value. The key and value are read from `MOLOSOC_LD_COMGATE_CONFIRM_KEY` / `_VALUE`. Neither is defined anywhere in the repo, so the default stays fail-closed (`comgate_unverified`).

### Order item size meta
- Landing B and the Christmas bundle add the parent product (id 364) with a variation (424 = L, 425 = M). WooCommerce stores the chosen variation attribute on the order line as item meta whose key is the attribute name and whose value is the term slug. The live slugs are `m-medium` / `l-large` (Issue #220).
- Phase 1 read this meta but only upper-cased it, so `m-medium` would have become `M-MEDIUM` in the subject. **Fixed in Phase 2:** the snapshot now uses `molosoc_ld_normalize_size()` and accepts only canonical sizes (`MOLOSOC_LD_SIZE_ORDER`); anything else fails closed (`sizes_unusable`).
- The **exact meta key** (`pa_size`? `size`?) is still unverified; Phase 1 tries `pa_size`, `size`, `pa_velikost`, `velikost`.

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

1. **Comgate paid signal**: unknown order-meta key/value. Needs the read-only check below.
2. **Order item size meta key**: unverified (see below).
3. **Real label generation** for both carriers needs the carriers' sandbox/test credentials and Žaneta's approval to call non-public plugin internals. Not requested here.
4. **Staging site**: this repo has no staging environment definition; one must exist with `WP_ENVIRONMENT_TYPE=staging`.
5. **Mail**: no sender exists by design. A mail step is a later, separately approved phase.

## Read-only verification for Žaneta (WP admin, no credentials)

Use a **test/past paid card order** (open it only to read):
1. WooCommerce → Orders → open one order paid by Comgate and in `processing`. Note the **Transaction ID** field (Payment section).
2. Screens → Custom Fields (enable in Screen Options), or the order's meta box: copy the **meta key names and values** that Comgate wrote (names only, e.g. `_comgate_state` = `PAID`). Do **not** copy tokens, emails or addresses.
3. Repeat on one order whose card payment failed/was cancelled, to confirm the value differs.
4. On any order, expand an order line and copy the **size meta label and value** shown (e.g. `Size: m-medium`); Custom Fields shows the raw key.
5. Comment the key/value pairs on #352.

## Activation prerequisites (none performed here)

1. Merge approval from Žaneta; no deploy performed by this PR.
2. Read-only findings above, then in `wp-config.php` of **staging only**: `MOLOSOC_LD_COMGATE_CONFIRM_KEY`, `MOLOSOC_LD_COMGATE_CONFIRM_VALUE`, `MOLOSOC_LABEL_DISPATCH_DRY_RUN`, `MOLOSOC_LABEL_DISPATCH_STAGING`, plus the option `molosoc_label_dispatch_since` (cut-off so no historical order is processed).
3. Place staging test orders (mock gateway data) and read the audit meta `_molosoc_label_dispatch_audit`.
4. A later phase, separately approved, for sandbox-credential live adapters and mail.
