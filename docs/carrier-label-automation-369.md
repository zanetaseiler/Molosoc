# Carrier labels: hands-off processing of all eligible new orders (Issue #369)

Follows the `ZANETA_DECISION — APPROVED CHANGE OF SCOPE` of 2026-11-11 on #369. Builds on the merged pipeline (#351/#354/#355/#357/#359/#362/#365/#370/#371).

**Status: repository only, OFF by default.** Merging deploys `site/mu-plugins/**` to production. The new file does nothing there until the wp-config constants below are set. No shipment was created, no mail was sent and no order was changed while building this. This cloud session cannot reach production (proxy `403`), so nothing here was verified live.

## What the installed plugins can actually do (read from upstream source)

Sources: PPL CZ **1.1.3** (`PPL-CZ/PPL-WooCommerce`, tag `1.1.3`) and Packeta **2.3.2** (`Zasilkovna/WooCommerce`, tag `v2.3.2`). Both were cloned and read in this session.

### PPL CZ 1.1.3: no headless label path. **PPL stays manual.**
- A label exists only after `CPLOperation::createPackages($batchId)`. That call creates the shipments live through the CPL API (`createShipmentsWithHttpInfo`) from a local batch. The batch is built in the admin UI (`wp_ajax_pplcz_*` handlers, REST `ppl-cz/v1/shipment-batch/*` behind `check_permission`). The plugin has no order-status or payment hook that creates a shipment.
- `CPLOperation::getLabelContents()` downloads the PDF, then calls `header()` and `exit($response['body'])`. It streams the PDF to the admin's browser and ends the request, so it cannot return bytes to other code.
- The only plugin cron jobs are status refresh, settings refresh and log cleanup (`ShipmentPhaseCron`, `RefreshAboutCron`, `DeleteLogCron`). None of them creates a label.
- **Conclusion:** a PPL label cannot be obtained without the manual batch step, unless we create shipments ourselves through CPL internals. That would be shipment creation, which is out of scope and not a stable API. The automation therefore puts every eligible PPL order into `attention` and sends **one alert**. Nothing is fetched or mailed for PPL.

### Packeta 2.3.2: supported, fetch only
- **Packet creation is Packeta's own job.** `PacketAutoSubmitter` submits a packet when an order reaches `processing` or `completed`, depending on the `packetery_auto_submission` option (`allow` plus an event per payment gateway). Without it, Žaneta exports the order by hand. Our code never creates a packet.
- The packet id, carrier and packet status are stored in `{prefix}packetery_order` (`packet_id`, `carrier_id`, `packet_status`). We read them with one prepared, read-only `SELECT`.
- `carrier_id` that is **not numeric** means a Packeta internal pickup point (`zpoint…`, `zbox…`). The Packeta label (`packetLabelPdf`) is the right one there. A **numeric** `carrier_id` means an external courier, which needs a courier label (`packetsCourierLabelsPdf`, which also needs the courier number). That case is not automated: it goes to `attention` with an alert.

## The automatic path (`site/mu-plugins/molosoc-carrier-label-auto.php`)

```
order -> processing ──queue (3 min, so Packeta's auto-submission runs first)──> worker
worker: gate -> lock -> plan
   skip       not eligible (bank transfer, unpaid Comgate, before cut-off, not processing, bad sizes): one audit row, done
   wait       Zásilkovna, no packet yet: check again every 15 min, up to 72 h, then attention + alert
   attention  PPL / external Packeta carrier / cancelled or moving packet / malformed id / no API password: one alert
   send       Phase 3 state machine: fetch the existing label -> validate PDF -> wp_mail to the dispatcher (Cc hello@)
                 transient failure: retry in 10 min, at most 3 tries, then attention + alert
sweep (every 15 min): queues processing orders after the cut-off that the automation has never seen
                 + recovery: seen orders after the cut-off that never finished (no done marker), are not
                   mailed/attention, have no pending run and no live lock -> queued again; a run lost
                   mid-mail then ends in attention (mail_state_unknown) + one alert, never a resend
                 both passes share one budget of 100 queued orders per run
```

| Requirement | How |
|---|---|
| OFF by default | Hooks only with `MOLOSOC_LABEL_AUTO_ENABLED === true` **and** a valid `MOLOSOC_LABEL_DISPATCH_SINCE` constant. The gate is re-checked on every queued run, so removing the constant stops pending work. It refuses to run while the single-order live path or the mock stage is on. |
| No retroactive sends | The cut-off must be a wp-config constant, not earlier than 2026-11-11 (the DB option is not accepted). Only orders created at or after it, with status exactly `processing`, are processed. |
| Payment / COD | Unchanged `molosoc_ld_decide()`: COD, or a Comgate card payment confirmed by `paid_status`. Bank transfer is never processed. |
| Carrier | Zásilkovna with a Packeta internal pickup point is automated. PPL and Packeta external couriers go to `attention` with one alert. |
| Real label | Packeta SOAP `packetLabelPdf` for the packet **already stored by Packeta**. The row is checked again right before the fetch. |
| Never duplicate | Phase 3 state machine: `mailing` is written before `wp_mail`, so a crash ends in `attention`, never a resend. The packet ref is stored, and a different packet means `ref_changed` and `attention`. A per-order lock with stale takeover (15 min, compare-and-swap) applies, and a pending queue entry is never duplicated. |
| Never mail a customer | Label mail: fixed `jarka01@atlas.cz`, Cc `hello@molosoc.com`, through the existing validated mailer. Alerts go only to `hello@molosoc.com`. No customer field is read in the new file. |
| Queue / retry | Action Scheduler (WooCommerce), with WP-Cron as a fallback. All retries are bounded: 72 h wait, 3 tries, and exceptions only inside the 72 h window. |
| Logging | Append-only order audit (`_molosoc_label_dispatch_audit`, stage `auto`) plus the WooCommerce log, source `molosoc-carrier-label` (ids and reason codes only). |
| Failure alerts | At most one per order, written **before** sending, to `hello@molosoc.com`. It has an order id, a reason code and a Czech hint, with no customer data. |
| Visibility | **Tools → MOLOSOC štítky – automat** (`manage_woocommerce`) is read-only. It shows the gate, cut-off, Packeta password (present or not), Packeta auto-submission settings for COD and Comgate, and the last 30 orders with carrier, packet, packet status, label state, the next step and any alert. It does not fetch a PDF, send mail or write anything. |

The single-order path (`molosoc-carrier-label-live.php`) is unchanged in behaviour. Its wp_mail I/O was moved into `molosoc_ll_io()` / `molosoc_ll_mail_now()` so both paths share one mailer.

## Remaining blockers / unverified facts

1. **PPL:** manual label only (see above). Automating it would need a separate decision on creating PPL shipments through CPL. Not done.
2. **Packeta external couriers:** manual (courier label). Not automated.
3. **`packetLabelPdf` has never run against production.** It is expected to be read-only on Packeta's side, but that is not proven. The first live order is the end-to-end proof.
4. **Packeta auto-submission on production:** unknown. If it is off for COD and Comgate, each Zásilkovna order waits for a manual export (up to 72 h) and is then mailed.
5. **Action Scheduler / WP-Cron on production:** must actually run (WooCommerce → Status → Scheduled Actions shows no large "past due" backlog).
6. **Order completed too early:** if an order is marked `completed` before the worker runs, it is skipped (`status_not_processing`) and nothing is mailed. The label must then be sent by hand.

## One browser-enabled verification step (read-only, requested)

With wp-admin access (Žaneta, or Claude in Chrome on a logged-in session), **change nothing**, and post only ids, settings and yes/no answers on #369:
1. Packeta → Settings → **Automatic packet submission**: is it allowed? Which event is set for **Cash on delivery** and for **Comgate**?
2. WooCommerce → Status → **Scheduled Actions**: is the "Past due" count about 0? Did `packetery_*` / `woocommerce_*` actions run in the last hour?
3. For the last 5 Zásilkovna orders: Packeta carrier internal (pickup point) or external courier, and was the packet created by hand or automatically?

## Activation plan (each step needs its own ZANETA_DECISION)

**A. Merge + deploy** this PR. Nothing changes.

**B. Read-only status page on production.** Nothing is sent. Add to `wp-config.php`:
```php
define( 'MOLOSOC_LABEL_DISPATCH_SINCE', '2026-11-20T00:00:00+01:00' ); // example: the go-live time, not earlier
define( 'MOLOSOC_LABEL_AUTO_PREVIEW', true );
```
Open **Tools → MOLOSOC štítky – automat** and check that the "Automat udělá" column is right for real orders (Zásilkovna COD and Comgate → `send` or `wait`, PPL → `attention: ppl_manual_label_required`, bank transfer → `skip`). Post the result on #369 without customer data.

**C. Go live** (needs a separate decision, after B looks right):
```php
// Keep MOLOSOC_LABEL_DISPATCH_SINCE = go-live time. Do NOT set MOLOSOC_LABEL_LIVE_ENABLED.
define( 'MOLOSOC_LABEL_AUTO_ENABLED', true );
```
Then check the first real Zásilkovna order end to end: exactly one mail to `jarka01@atlas.cz` (Cc `hello@`), the right subject, a readable PDF, the Brevo log, the order audit `label_ready` → `mailed`, and one packet in Packeta. PPL orders produce one alert each.

**Kill switch:** remove `MOLOSOC_LABEL_AUTO_ENABLED`. Pending queue entries then do nothing. Optional clean-up: `wp action-scheduler clean` or delete the `molosoc_la_*` actions in Scheduled Actions.

**Operator retry of one order** (only after the cause is fixed and with a decision; never reset `mailing` or `mailed`): `wp eval 'echo molosoc_la_worker( N );'`.

## Tests

`tests/test_carrier_label_auto_369.py` (real PHP, injected I/O, no network, no mail, no DB writes):
- the gate: off by default, strict `true`, exclusive with live and mock, cut-off constant required and valid;
- the Packeta row check: internal vs. external carrier, missing, malformed, cancelled or moving packet;
- the plan for COD, Comgate, bank transfer, pre-cut-off, PPL, unconfigured, waiting, and terminal states;
- the provider: re-check at fetch time, fetch only the stored packet, PPL never fetches;
- alerts: fixed recipient, header-injection-safe reason, at most once, marker written before the send;
- the worker step: wait and timeout, retry and exhaustion, lock, permanent failures, resuming `mailing`;
- end to end through the real Phase 3 state machine: exactly one mail across repeated runs, zero mails for PPL, bank transfer, pre-cut-off, a cancelled packet, a changed packet ref or a crash after `mailing`;
- the source contract: no packet or shipment creation, no order-status change, no customer getters, the only `$wpdb->update` is the lock CAS, the status page is read-only, and no hooks without the opt-in.
