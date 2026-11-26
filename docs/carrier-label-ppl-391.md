# PPL labels: automatic shipment, label and email (Issue #391)

This adds a PPL path to the #369 automation, which has run Zásilkovna since 2026-11-26 16:20 CET. An eligible PPL order gets **exactly one** PPL shipment, created through the PPL CZ plugin's own models and batch. Its label PDF is then emailed through the same mailer as Zásilkovna (`jarka01@atlas.cz`, Cc `hello@molosoc.com`).

The path is **OFF by default**. Merging and deploying it changes nothing until `MOLOSOC_LABEL_AUTO_PPL_ENABLED` is set. Until then PPL orders go to `attention` (`ppl_manual_label_required`) with one alert, as today.

> **Incident 2026-11-26 (Issue #393).** The first deploy of this file (PR #392, merge `2072c92`, deployed 15:40 UTC) took molosoc.com down with HTTP 500 on every page: `molosoc_lp_gate()` was also declared by the #370 label preview mu-plugin (`molosoc-carrier-label-preview.php`), and WordPress loads all mu-plugins unconditionally, so the OFF-by-default constants could not prevent the `Cannot redeclare` fatal. See section 7.

Files:

- `site/mu-plugins/molosoc-carrier-label-ppl.php`: new. It holds the PPL steps (create or adopt, settle, fetch-only provider).
- `site/mu-plugins/molosoc-carrier-label-auto.php`: routes PPL orders to that file only when the path is on. The #369 gate, cut-off, eligibility, queue, lock, audit, alerts and the at-most-once mail state machine are reused unchanged.
- `tests/test_carrier_label_ppl_391.py`: 47 tests.
- `tests/test_mu_plugins_coexist_393.py`: all mu-plugins load together (Issue #393).

## 1. Investigation (PPL CZ 1.1.3 source, tag `1.1.3` of `PPL-CZ/PPL-WooCommerce`)

| Question | Finding in 1.1.3 | Decision |
|---|---|---|
| Create through the plugin or call CPL directly? | The batch screen does three things: `add_shipment_to_batch` (order → `ShipmentModel` → `ShipmentData`, `set_batch_local_id`, `reorder_batch_shipments`), then `prepare_shipments` (`pplcz_validate`), then `create_labels` → `CPLOperation::createPackages($batchId, $print)`. All of these are plain PHP calls. Only the REST wrapper needs an admin session. | Use the **plugin's own path**: `pplcz_denormalize($order, ShipmentModel)`, `pplcz_validate`, `pplcz_denormalize($model, ShipmentData)`, `new BatchData()`, `createPackages`. The shipment is in the plugin's tables, so the order's PPL box, `ShipmentPhaseCron` tracking and status sync keep working. No direct CPL create call. |
| How does the shipment get its number? | `createPackages` sets `import_state = InProgress` and the remote `batch_id` (a UUID). `CPLOperation::loadingShipmentNumbers([batch])` (also run by `ShipmentPhaseCron`) sets `Complete`, the package `shipment_number` and the `label_id`. | While the shipment is pending, the automation calls `loadingShipmentNumbers` for **its own** batch only. It checks again every 5 min, for up to 6 h. |
| Label bytes without `exit()` | `getLabelContents()` does `wp_remote_get(BASE_URL/shipment/batch/{id}/label?…)` with `Bearer getAccessToken()`, then `header()` + `exit($body)`. CPL has no other label endpoint. | Make the **same request** with the plugin's own `getAccessToken()` and `CPLOperation::BASE_URL`, and return the body. Format `4/PDF` = A4, first position, the same as the manual "A4 4×". Output buffering cannot capture `exit()`, so it is not used. |
| "Already shipped" marker | `{prefix}pplcz_shipment` rows per `wc_order_id`. `import_state` is `None`/empty for a local draft, and `InProgress`/`Accepted`/`Complete`/`Error` after it was sent. The batch screen skips orders that already have a row (`find_shipments_by_wc_order`). | Same rule. A sent shipment is **adopted** (never a second one). A local draft means someone is working on it by hand → `attention`. |
| Create failure | On an API error the plugin resets the shipment to `import_state = None` and records `import_errors`. On a timeout the outcome is unknown: PPL may have created the shipment. | A create is **never retried**. Any failure or interruption after `creating` → `attention` + one alert. |

## 2. How one PPL order is handled

```
processing order (after cut-off, COD or Comgate-confirmed card)  ── #369 queue, lock, eligibility
  └─ PPL path on?  no  → attention ppl_manual_label_required (one alert), as today
                   yes ↓
  PPL state (order meta _molosoc_label_ppl_state)
    creating          → attention ppl_create_state_unknown (one alert), NEVER a second create
    created/adopted   → settle own shipment: pending → refresh + wait 5 min | Complete → label
    ''                → plugin rows for the order:
                          >1 sent           → attention ppl_multiple_shipments
                          1 sent            → ADOPT it (state adopted), no create
                          local draft only  → attention ppl_manual_draft_exists
                          none              → refusal check → state `creating` → plugin draft + batch
                                              → createPackages → state `created` → wait
  Complete → fetch label for this one shipment → #369 state machine: label_ready → mailing → mailed
```

Duplicate protection, layer by layer:

1. **Idempotency key = the order.** `creating` is written to order meta **before** anything is saved in the plugin or sent to PPL. Every later run that finds `creating` stops with one alert. Retries, crashes, exceptions, timeouts and a status change made in the meantime all lead to the same result. The step checks `creating` *before* the eligibility check, so a completed or cancelled order cannot hide an interrupted create.
2. **Plugin rows.** An existing sent shipment is adopted, not duplicated. A second sent shipment that appears later (a manual click after the automation's create) → `attention`, and nothing is mailed.
3. **Mail.** The #369 state machine stores the PPL shipment number as `ref`. A different number later → `ref_changed` → `attention`. `mailing` is written before `wp_mail`, so the label is sent at most once.
4. **Locks.** The whole step runs under the #369 per-order worker lock (stale takeover after 15 min). The draft step re-checks `find_shipments_by_wc_order` right before saving.

Refusals → `attention` + one alert, no create. Each refusal is a check on the plugin's own model for the order:

| Reason | Condition |
|---|---|
| `ppl_validation_failed` | The plugin's validator (`pplcz_validate`, the same one as the batch screen) reports any error. |
| `ppl_method_ambiguous` / `ppl_method_unknown` | Not exactly one `pplcz_*` method, or not `pplcz_SMAR` / `pplcz_SBOX` / `pplcz_PRIV`. |
| `ppl_parcel_missing` / `ppl_parcel_unexpected` | SMAR/SBOX without a pickup point or ParcelBox code; PRIV with one. |
| `ppl_not_cz`, `ppl_currency_unexpected` | Recipient country is not `CZ`, or the currency is not `CZK`. |
| `ppl_sender_mismatch` | The sender address is not id **3**. |
| `ppl_cod_mismatch`, `ppl_cod_vs_invalid`, `ppl_cod_unexpected` | COD order: the plugin's COD amount or currency differs from the order total, or the variable symbol is not 1 to 10 digits. Card order: a COD amount is set. |
| `ppl_service_missing`, `ppl_packages_unexpected` | No service code, or not exactly one package. |
| `ppl_shared_batch_manual` | An adopted shipment sits in a manual batch together with other orders. Its labels were printed by hand, so nothing is mailed. |
| `ppl_import_error`, `ppl_shipment_cancelled`, `ppl_create_failed`, `ppl_wait_timeout` | PPL rejected the shipment, it was cancelled, the create failed, or it was not `Complete` within 6 h. |

Audit rows and alerts carry only ids, states and reason codes. Credentials come only from the PPL plugin's stored settings, through its own `getAccessToken()`. Nothing secret is written to code, meta, audit or logs.

## 3. Configuration (wp-config.php)

| Constant | Meaning |
|---|---|
| `MOLOSOC_LABEL_AUTO_ENABLED` + `MOLOSOC_LABEL_DISPATCH_SINCE` | Unchanged from #369. Required. |
| `MOLOSOC_LABEL_AUTO_PPL_ENABLED` | `true` turns the PPL path on. Anything else = off. The path also stays off if the PPL CZ plugin classes are not loaded. |
| `MOLOSOC_LABEL_AUTO_PPL_LIMIT` | Optional, an int from 1 to 20. Only the first N eligible PPL orders take the path, claimed through atomic options `molosoc_lp_slot_1..N`. Later PPL orders stay manual (`ppl_manual_label_required`). Any other value turns the PPL path off. |

The status page (**Tools → MOLOSOC štítky – automat**) shows the `PPL automat` row. For PPL orders it shows `ppl: ppl_auto (PPL: created)` and similar values. The page stays read-only.

## 4. Activation plan

Each step needs Žaneta's separate decision on GitHub.

**Step 0: merge + deploy (path OFF).** Deploy with no new constant. Check that the status page shows `PPL automat: vypnuto (PPL ručně)` and that PPL orders still go to `attention: ppl_manual_label_required`. Zásilkovna must be unaffected.

**Step 1: single-order live test.** Before it, check in wp-admin → PPL → settings that the default sender address is id 3 and that the print format and API credentials work, for example with one manual label as on #1137. Then add:

```php
define( 'MOLOSOC_LABEL_AUTO_PPL_ENABLED', true );
define( 'MOLOSOC_LABEL_AUTO_PPL_LIMIT', 1 );
```

The **next** eligible PPL order takes slot 1. Every later PPL order stays manual. For that one order, check:

- the order's PPL box shows exactly **one** shipment with a shipment number, and PPL's myAPI2/portal shows one shipment;
- the audit shows `ppl_creating` → `ppl_created` → `label_ready` → `mailed`, and the status page shows `mailed`;
- exactly **one** mail reached `jarka01@atlas.cz` (Cc `hello@`), with subject `PPL | …` and attachment `ppl-<id>.pdf`. The PDF is A4 and readable, and its label matches the shipment number, pickup point/ParcelBox and COD amount;
- the Brevo log; tracking (`ShipmentPhaseCron`) moves the package phase later.

Post the result on #391 without customer data. To stop at any point, remove `MOLOSOC_LABEL_AUTO_PPL_ENABLED`.

**Step 2: general enablement.** After Žaneta's decision, remove `MOLOSOC_LABEL_AUTO_PPL_LIMIT`. Optionally delete the option `molosoc_lp_slot_1`; it is harmless if kept. PPL orders that went to `attention` during the test stay manual: `attention` is final.

**Rollback:** remove `MOLOSOC_LABEL_AUTO_PPL_ENABLED`. Pending runs fall back to the manual alert. Shipments that already exist stay in the PPL plugin as normal shipments.

## 5. Not verified yet (verified only by the single-order live test)

- CPL accepts the label request from a cron context with the cached plugin token. It is the same URL and parameters as the plugin's own download.
- How fast `Complete` follows `InProgress`. The 6 h timeout is an assumption.
- Side effects of the plugin's own order → model conversion: it may cache a `ParcelData` row, exactly as when the admin opens the PPL box.

## 6. Tests

`python3 -m unittest tests.test_carrier_label_ppl_391` runs real PHP with injected I/O: no network, no plugin, no DB, no mail. It covers:

- the gates (off by default, strict constant, plugin required, live-test limit and slot claim);
- every refusal;
- shipment classification;
- **exactly one create** across repeated runs, an exception or failure in the create, a crash after `creating`, an adopted manual shipment, a manual draft, a second manual shipment after the create, and a status change after an interrupted create;
- label fetch only for a single-shipment batch, a shared batch never mailed, and fetch retries that end in `attention`;
- end to end through the real #369 step, the PPL step, the Phase 3 state machine and the fixed-recipient mailer: one mail, the right subject and file name, and zero mails for refused, ineligible, failed or timed-out orders;
- static checks: no `wp_mail`, hooks, status changes or secrets in the PPL file, one `createPackages` and one `wp_remote_get`, `creating` written before stage and submit, the provider never creates, and the #369 file has no PPL internals.

The existing #345 to #369 carrier-label suites pass unchanged.

## 7. Incident 2026-11-26 and fix (Issue #393)

**What happened.** PR #392 shipped `molosoc-carrier-label-ppl.php` with the `molosoc_lp_` prefix, which the #370 label preview already uses (`lp` = label preview). `molosoc_lp_gate()` existed in both files. Production logged `PHP Fatal error: Cannot redeclare molosoc_lp_gate()` from 15:41:03 to 15:47:05 UTC and every page (shop, checkout, wp-admin) returned 500. The per-feature test suites each load only their own files, so none of them loaded the PPL and preview files together.

**Mitigation on production (~15:50 UTC, by hand in cPanel).** `wp-content/mu-plugins/molosoc-carrier-label-ppl.php` was renamed to `molosoc-carrier-label-ppl.php.disabled-fatal-392`. WordPress only loads `*.php` files from `mu-plugins/`, so that copy is inert. wp-config was not changed: Zásilkovna automation stays ON, and no `MOLOSOC_LABEL_AUTO_PPL_*` constant exists. The status page shows `PPL automat: vypnuto (PPL ručně)`.

**Fix (this PR).**

- Every function and constant in `molosoc-carrier-label-ppl.php` now uses its own prefix: `molosoc_lppl_*` and `MOLOSOC_LPPL_*`. Callers in `molosoc-carrier-label-auto.php` and `tests/test_carrier_label_ppl_391.py` were updated. Behaviour is identical and still OFF by default. Stored names are unchanged: order meta `_molosoc_label_ppl_state` / `_molosoc_label_ppl_shipment` and the slot options `molosoc_lp_slot_1..N` (section 3) keep their values, so nothing already on the server needs to be migrated.
- `tests/test_mu_plugins_coexist_393.py` loads **all** `site/mu-plugins/*.php` together in one PHP process (minimal WP stubs; constants OFF, then the registration constants ON, then in reverse order) and fails on any fatal, warning, notice or output. It also statically checks that no function name or `const`/`define()` name is declared in more than one mu-plugin. Two tests prove that both guards catch the #392 file.
- `deploy-mu-plugins.yml` now runs that test before it touches the server. A collision like #392 fails the deploy job instead of reaching production.

**What the deploy does with the files on the server.** The FTPS sync compares file hashes with its state file (`.molosoc-mu-plugins-state.json`). That file still records the #392 hash of `molosoc-carrier-label-ppl.php`. The fixed file has a different hash, so the deploy uploads it again to `molosoc-carrier-label-ppl.php`. The deploy does **not** delete `molosoc-carrier-label-ppl.php.disabled-fatal-392`: it removes only exact names it is told to, and that file is inert. It stays as evidence until it is deleted by hand (safe at any time).

After the merge, check that the homepage, `/cz/`, a product page, checkout and wp-admin return 200, and that the status page still shows `PPL automat: vypnuto (PPL ručně)`. If a 500 appears, rename `molosoc-carrier-label-ppl.php` again as on 2026-11-26.

**Activation plan unchanged.** Section 4 still applies. Step 0 is now "deploy this fix and verify the site". The Step 1 single-order PPL test still needs a separate ZANETA_DECISION after the fix is deployed and the site verified.
