# Carrier label: read-only preview + one approved live order (Issue #369)

Builds on #345/#352/#356/#358/#361/#363/#366 (PRs #351, #354, #355, #357, #359, #362, #365).

**Status: repository-only.** This cloud session cannot reach molosoc.com or wp-admin (the proxy returns `403`, and there are no admin credentials). So **no** real order was identified, and no plugin, Comgate or Packeta fact was checked live. Nothing has been sent, activated or changed in production.

> Deploy note: a merge to `main` that touches `site/mu-plugins/**` runs `deploy-mu-plugins.yml` and syncs these files to production. Both files are **inert** there until the wp-config constants below are set. Merging still needs Žaneta's approval.

## Gap found in the merged pipeline (#358)

Once `MOLOSOC_LABEL_LIVE_ENABLED` was set, the allowlisted order's label was fetched and mailed in the same step. There was no way to see the exact label, packet and subject first. #369 requires that Žaneta approve **the specific order, recipient and label after a read-only check**. Two minimal safeguards close that gap:

| Change | File | Behaviour |
|---|---|---|
| Read-only preview | `site/mu-plugins/molosoc-carrier-label-preview.php` (new) | Active only with `MOLOSOC_LABEL_LIVE_PREVIEW === true`, a one-order allowlist, live **off** and mock off. **Tools → MOLOSOC náhled štítku** (`manage_woocommerce`) shows the order id, eligibility decision, carrier, subject, attachment name, To/Cc, delivery state, the Packeta packet id and any blockers. A nonce-checked POST button fetches the PDF for the **existing** packet and shows it only in the admin's browser (`no-store`). No mail, no writes (meta, options, audit, status, cron), no packet creation. |
| Approved-packet pin | `site/mu-plugins/molosoc-carrier-label-live.php` | The live gate now also needs `MOLOSOC_LABEL_LIVE_APPROVED_PACKET`, a well-formed packet id (`Z?\d{5,20}`). Without it, `molosoc_ll_run()` returns `approved_packet_missing` before any order lookup. If Packeta returns any other packet id, the result is a permanent failure `packet_not_approved` (state `attention`), and nothing is mailed. |

Everything else in #358 is unchanged: OFF by default, exactly one order, at-most-once mail, fixed recipient and Cc, no customer mail, no bulk processing, and PPL left manual.

## What the repository shows vs. what still needs a live read

| Question | Repo evidence | Live status |
|---|---|---|
| Comgate paid-order eligibility | `molosoc_ld_comgate_paid()` needs: status `processing`, Comgate gateway, a non-empty transaction id, `is_paid()`, and (strict rule) a transaction id that differs from `wf_gateway_tmp_transaction_id`. | **Unverified.** The preview's `Rozhodnutí` row shows the real decision for the chosen order (`eligible` / `comgate_unverified` / …) without writing anything. |
| Packeta existing-packet PDF | Fetch-only SOAP `packetLabelPdf(apiPassword, packetId, 'A6 on A6', 0)` via `https://www.zasilkovna.cz/api/soap.wsdl`. The packet id comes from the operator meta key. | **Unverified.** The preview button is the first real call. Expected to be read-only on Packeta's side, but that is not proven. |
| PPL | PPL CZ 1.1.3 has no hook or headless label path, only the admin-authenticated REST batch flow. | Unchanged: `ppl_manual_label_required`. The preview lists it as a blocker. **Use a Zásilkovna order.** |
| Mail transport | #366: Brevo delivery confirmed (per the #369 ZANETA_DECISION). | WP Mail SMTP forced sender applies. Leave `MOLOSOC_LL_MAIL_FROM_EXPLICIT` unset. |

## Exact minimal operator step (blocked here)

Production and wp-admin are not reachable from the cloud session. Before anything else, someone with wp-admin access (Žaneta, or Claude in Chrome on a logged-in session) must choose the candidate order. Paste **only ids and statuses on GitHub, never customer data**:

1. A **Zásilkovna** order that is currently `processing`, paid by **COD** or by a **Comgate card payment that has completed**, with no label already handled by hand, and **already exported to Packeta** (it has a packet). Record its order id `N`.
2. The **meta key name** on that order that holds the Packeta packet id (Packeta box / custom fields). Record the key name only.
3. Comgate only: is `_transaction_id` equal to `wf_gateway_tmp_transaction_id`? Answer only `equal` or `different`.

## Concrete activation plan (each step needs its own ZANETA_DECISION)

**A. Merge + deploy this PR** (inert).

**B. Read-only preview.** Nothing is sent.
1. Set `molosoc_label_dispatch_since` (option) to a timestamp at or before order `N` was created. The cut-off is otherwise `before_cutoff_no_retroactive`.
2. Add to `wp-config.php` on the server. Do **not** add `MOLOSOC_LABEL_LIVE_ENABLED`:
   ```php
   define( 'MOLOSOC_LABEL_LIVE_ORDER_IDS', array( N ) );
   define( 'MOLOSOC_LL_PACKETA_PACKET_META', '<meta key from step 2>' );
   define( 'MOLOSOC_LL_PACKETA_API_PASSWORD', '<typed directly on the server, never in GitHub/chat>' );
   define( 'MOLOSOC_LABEL_LIVE_PREVIEW', true );
   // Comgate order only, and only if step 3 said "equal":
   // define( 'MOLOSOC_LABEL_COMGATE_TMPID_RULE', 'paid_status' );
   ```
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
5. **Immediately** remove `MOLOSOC_LABEL_LIVE_ENABLED`, `MOLOSOC_LABEL_LIVE_APPROVED_PACKET` and `MOLOSOC_LABEL_LIVE_ORDER_IDS`.
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
