# MOLOSOC-hosted review request (Issue #333)

Decision (ZANETA_DECISION, Option B): reviews live on MOLOSOC, one branded
review-request e-mail after purchase, no newsletter coupling. This PR ships
the **non-sending** parts only. Nothing is enabled and no production setting
was changed.

## What the code does (`site/theme/inc/review-request.php`)
- Mode option `molosoc_review_request_mode`: `off` (default) / `dry_run` / `live`.
- `live` sends ONLY if `molosoc_review_request_legal_confirmed` = `1`;
  otherwise it behaves as dry run. Dry run writes a private order note and
  never calls `wp_mail()`.
- Optional `molosoc_review_request_test_emails` (comma list): when set, only
  those addresses are ever mailed, in any mode.
- Trigger: Woo status `completed` + 10 days (CZ) / 14 days (abroad). This is a
  **proxy**: it does not mean a carrier delivered the parcel. No PPL/Zasilkovna
  delivered signal exists in the repo and none is claimed.
- Idempotent: one unique Action Scheduler action per order; an atomic per-order claim (insert-only `INSERT IGNORE` on the unique option name — not `add_option()`, which is ON DUPLICATE KEY UPDATE, `molosoc_rr_claim_<order>`) must be acquired before sending, so overlapping callbacks cannot double-send. A failed send releases the claim with at most 3 hourly retries.
- Suppression: per-order opt-out, hashed e-mail suppression (one atomic option per hash) (opt-out link
  in every mail), refunded/non-completed orders, invalid e-mail, and the
  `molosoc_review_request_suppressed` filter (use it to plug in a marketing-unsubscribe
  list, e.g. Brevo, before going live).
- E-mail (CZ/EN, plain text) links to the product page `#reviews` in the order
  language, says reviews are moderated on MOLOSOC and **not independently
  verified**, and carries an opt-out link.

## NOT done on purpose
- CusRev checkout checkbox is **not** removed or hidden: its plugin version,
  review mode and settings are unverified (no WP-admin access here), and
  removing it is the owner's call after the checks below.
- No collection-time opt-out notice added to checkout: wording depends on the
  legal review. Suggested concise text for counsel: "Po doručení vám pošleme
  jednu zprávu s prosbou o hodnocení; odhlásit se můžete v ní." (CZ) /
  "After delivery we will send one message asking for a product review; you can
  opt out in it." (EN).
- No e-mail is sent, nothing scheduled while mode is `off`.

## Owner checklist (WP-admin)
1. Legal: confirm with counsel the basis for the review e-mail (Act 480/2004
   §7(3) existing-customer rule needs the address obtained during the sale, a
   chance to refuse at collection, and an opt-out in every message) and add the
   collection notice. Only then set `molosoc_review_request_legal_confirmed`=1.
2. WooCommerce > Settings > Products: enable reviews, "reviews can only be left
   by verified owners" (optional), "show verified owner label" (Woo's own,
   accurate for the buyer), enable star ratings; Settings > Discussion: hold
   comments for moderation. Confirm the product pages show the Reviews tab in
   both CZ and EN.
3. CusRev: confirm plugin version, review mode (hosted vs local), trigger and
   delay. Disable its invitation sending BEFORE going live here, to avoid two
   requests, and only then remove its checkout checkbox.
4. Staging: set mode `dry_run`, complete a test order (test e-mail only), check
   the order note; then set `test_emails` to your own address plus `live` +
   legal flag on staging to preview the mail. Never run live against customers
   before step 1.
5. Wire the marketing-unsubscribe list into the suppression filter if one exists.
