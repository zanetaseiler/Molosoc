# Carrier label: read-only preview + one approved live order (Issue #369)

Builds on #345/#352/#356/#358/#361/#363/#366 (PRs #351, #354, #355, #357, #359, #362, #365).

> **Scope changed on 2026-11-11** (`ZANETA_DECISION — APPROVED CHANGE OF SCOPE` on #369): the goal is now hands-off processing of all eligible new orders. See **`docs/carrier-label-automation-369.md`**. The single-order path below stays as it is and must not be enabled together with the automation.

**Status: repository-only.** This cloud session cannot reach molosoc.com or wp-admin (the proxy returns `403`, and there are no admin credentials). So **no** real order was identified, and no plugin, Comgate or Packeta fact was checked live. Nothing has been sent, activated or changed in production.

> Deploy note: a merge to `main` that touches `site/mu-plugins/**` runs `deploy-mu-plugins.yml` and syncs these files to production. Both files are **inert** there until the wp-config constants below are set. Merging still needs Žaneta's approval.

## Gap found in the merged pipeline (#358)

Once `MOLOSOC_LABEL_LIVE_ENABLED` was set, the allowlisted order's label was fetched and mailed in the same step. There was no way to see the exact label, packet and subject first. #369 requires that Žaneta approve **the specific order, recipient and label after a read-only check**. Two minimal safeguards close that gap:

| Change | File | Behaviour |
|---|---|---|
| Read-only preview | `site/mu-plugins/molosoc-carrier-label-preview.php` (new) | Active only with `MOLOSOC_LABEL_LIVE_PREVIEW === true`, a one-order allowlist, live **off** and mock off. **Tools → MOLOSOC náhled štítku** (`manage_woocommerce`) shows the order id, eligibility decision, carrier, subject, attachment name, To/Cc, delivery state, the Packeta packet id and any blockers. A nonce-checked POST button fetches the PDF for the **existing** packet and shows it only in the admin's browser (`no-store`). No mail, no writes (meta, options, audit, status, cron), no packet creation. |
| Approved-packet pin | `site/mu-plugins/molosoc-carrier-label-live.php` | The live gate now also needs `MOLOSOC_LABEL_LIVE_APPROVED_PACKET`, a well-formed packet id (`Z?\d{5,20}`). Without it, `molosoc_ll_run()` returns `approved_packet_missing` before any order lookup. If Packeta returns any other packet id, the result is a permanent failure `packet_not_approved` (state `attention`), and nothing is mailed. |

Everything else in #358 is unchanged: OFF by default, exactly one order, at-most-once mail, fixed recipient and Cc, no customer mail, no bulk processing, and PPL left manual.

## Blocker fixes after the live read-only check (follow-up PR)

The live read-only check on 2026-11-11 (`NEEDS_ZANETA` on #369) found four blockers. The `ZANETA_DECISION` of 2026-11-11 approved fixing them. Everything stays OFF by default, the preview stays read-only, and live sending stays off.

| # | Blocker | Fix | Where |
|---|---|---|---|
| 1 | Packeta 2.3.2 keeps the packet id in its own table `{prefix}packetery_order.packet_id`, not in order meta. No meta key existed, so the preview always said `packet_not_submitted`. | `molosoc_ll_packeta_packet_id()` runs one prepared, read-only `SELECT packet_id FROM {prefix}packetery_order WHERE id = %d`. It first checks that the table exists. A missing table, row or NULL gives `''`, which means `packet_not_submitted`. A malformed value gives `packet_id_malformed` (fail closed). `MOLOSOC_LL_PACKETA_PACKET_META` is no longer used. | `molosoc-carrier-label-live.php`, used by the preview and the live provider |
| 2 | The API password had to be typed into wp-config. | `molosoc_ll_packeta_password()`: uses `MOLOSOC_LL_PACKETA_API_PASSWORD` if it is a non-empty string. Otherwise it uses `api_password` from Packeta's own `packetery` option. Control characters are rejected. With no usable password the result is `packeta_unconfigured`. The password is never logged, audited, shown or returned in a provider result. | `molosoc-carrier-label-live.php` |
| 3 | The cut-off option `molosoc_label_dispatch_since` could not be set safely from wp-admin. | `molosoc_ld_since_ts()`: the wp-config constant `MOLOSOC_LABEL_DISPATCH_SINCE` takes precedence over the option. It accepts a Unix timestamp (int or digit string) or an ISO 8601 date-time with an offset (e.g. `'2026-11-12T00:00:00+01:00'`). It must not be earlier than `MOLOSOC_LD_SINCE_FLOOR` (2026-11-11T00:00:00Z). A constant that is defined but invalid or too early gives `0`, so the result is `before_cutoff_no_retroactive`. There is no silent fallback to the option. | `molosoc-carrier-label-dispatch.php` |
| 4 | Default `strict` rejected every real paid Comgate order: on live data all 34 paid orders have `_transaction_id` equal to `wf_gateway_tmp_transaction_id`, and unpaid orders have an empty `_transaction_id`. | `paid_status` is now the default and the documented rule for Comgate 1.1.40. Paid means: gateway `wf-woo-comgate`, status `processing`, non-empty `_transaction_id`, and `is_paid()`. Only `MOLOSOC_LABEL_COMGATE_TMPID_RULE === 'strict'` brings back the old placeholder comparison. | `molosoc-carrier-label-dispatch.php` (`molosoc_ld_comgate_tmp_rule()`) |

Tests: `tests/test_carrier_label_blockers_369.py`. It uses a fake `$wpdb` with read methods only, so any write would be a fatal error. It also uses a fake `get_option`, makes no network calls and sends no mail. The existing tests in `test_carrier_label_live_358.py` and `test_carrier_label_staging_352.py` were changed to match the new Comgate default and the removed meta key.

**Order candidate (from the live check):** none is eligible right now. The next suitable order is a new Zásilkovna order, paid by COD or by a completed Comgate card payment, that has been exported to Packeta by hand and is still `processing`.

## What the repository shows vs. what still needs a live read

| Question | Repo evidence | Live status |
|---|---|---|
| Comgate paid-order eligibility | `molosoc_ld_comgate_paid()` needs: status `processing`, Comgate gateway, a non-empty transaction id and `is_paid()`. Default rule is `paid_status` (fix 4). | Live data checked (34 paid orders, ids equal). The preview's `Rozhodnutí` row shows the real decision for the chosen order. |
| Packeta existing-packet PDF | Fetch-only SOAP `packetLabelPdf(apiPassword, packetId, 'A6 on A6', 0)` via `https://www.zasilkovna.cz/api/soap.wsdl`. The packet id comes from Packeta's `packetery_order` table (fix 1). | **Unverified.** The preview button is the first real call. Expected to be read-only on Packeta's side, but that is not proven. |
| PPL | PPL CZ 1.1.3 has no hook or headless label path, only the admin-authenticated REST batch flow. | Unchanged: `ppl_manual_label_required`. The preview lists it as a blocker. **Use a Zásilkovna order.** |
| Mail transport | #366: Brevo delivery confirmed (per the #369 ZANETA_DECISION). | WP Mail SMTP forced sender applies. Leave `MOLOSOC_LL_MAIL_FROM_EXPLICIT` unset. |

## Exact minimal operator step (blocked here)

Production and wp-admin are not reachable from the cloud session. Before anything else, someone with wp-admin access (Žaneta, or Claude in Chrome on a logged-in session) must choose the candidate order. Paste **only ids and statuses on GitHub, never customer data**:

1. A **Zásilkovna** order that is currently `processing`, paid by **COD** or by a **Comgate card payment that has completed**, with no label already handled by hand, and **already exported to Packeta** (it has a packet). Record its order id `N`.
2. (Answered by the live check: there is no meta key. The packet id is read from Packeta's own table, see fix 1. For Comgate, the ids are `equal`, see fix 4.)

## Concrete activation plan (each step needs its own ZANETA_DECISION)

**A. Merge + deploy this PR** (inert).

**B. Read-only preview.** Nothing is sent.
1. Add to `wp-config.php` on the server. Do **not** add `MOLOSOC_LABEL_LIVE_ENABLED`. No password and no DB/option edit is needed: the password comes from Packeta's own settings (fix 2) and the packet id from Packeta's table (fix 1):
   ```php
   // Cut-off at or before order N was created, not before 2026-11-11T00:00:00Z (fix 3):
   define( 'MOLOSOC_LABEL_DISPATCH_SINCE', '2026-11-12T00:00:00+01:00' ); // example; use a time at or before order N
   define( 'MOLOSOC_LABEL_LIVE_ORDER_IDS', array( N ) );
   define( 'MOLOSOC_LABEL_LIVE_PREVIEW', true );
   // Comgate uses `paid_status` by default (fix 4); do not set MOLOSOC_LABEL_COMGATE_TMPID_RULE.
   ```
2. (Removed: no separate cut-off step is needed any more.)
3. Go to wp-admin → **Tools → MOLOSOC náhled štítku**. `Překážky` must be `(žádné)`. Click **Zobrazit PDF štítku** once and check that the PDF is the right parcel.
4. Post on #369, with no customer data: order id, `Rozhodnutí`, `Předmět`, `Příloha`, `Komu`/`Kopie`, packet id, and "PDF ok / not ok".

**C. Žaneta approves the specific order + recipient + label** (packet id) in a `ZANETA_DECISION`.

**D. One live send.**
1. In wp-config: remove `MOLOSOC_LABEL_LIVE_PREVIEW`, then add
   ```php
   define( 'MOLOSOC_LABEL_LIVE_APPROVED_PACKET', '<approved packet id>' );
   define( 'MOLOSOC_LABEL_LIVE_ENABLED', true ); // last
   ```
2. Trigger it once. The order is already `processing`, so the status hook will not fire again. Use WP-CLI on the server: `wp eval 'echo molosoc_ll_run( N );'`. Expected output: `mailed`.
3. Verify: exactly one email to `jarka01@atlas.cz` with Cc `hello@molosoc.com`, the right subject and a readable PDF (also in the Brevo log). The order audit shows `label_ready` and then `mailed live:true`. Packeta still has exactly one packet.
4. Run `wp eval 'echo molosoc_ll_run( N );'` once more. Expect `already_mailed`, and no new email.
5. **Immediately** remove `MOLOSOC_LABEL_LIVE_ENABLED`, `MOLOSOC_LABEL_LIVE_APPROVED_PACKET` and `MOLOSOC_LABEL_LIVE_ORDER_IDS`. `MOLOSOC_LABEL_DISPATCH_SINCE` may stay; it does nothing without the other constants.
6. Stop on any `attention` state. Read the audit `reason`: `mail_state_unknown` means check the mailbox first; `ref_changed` or `packet_not_approved` means check Packeta for duplicates. Never reset the state meta to retry without a new decision.

**Still out of scope:** multi-order or automatic operation, PPL automation, packet creation, and customer email. Each needs a separate, reviewed change.

## Tests

`tests/test_carrier_label_preview_369.py` (real PHP, injected I/O, no network, no mail):
- the preview gate (off by default, refused while live or mock is on, exactly one order);
- the report and its blockers (cut-off, bank transfer, unverified Comgate, PPL, terminal states, unconfigured, not submitted, malformed packet);
- PDF validation;
- the source contract: the preview file contains no mail, meta, option, status, cron or state-machine call;
- no hooks without the opt-in;
- the approved-packet gate, and that a different packet goes to `attention` with zero mails through the real state machine.

`tests/test_carrier_label_live_358.py` gate tests now pass the approved packet.
