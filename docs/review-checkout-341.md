# Checkout notice, opt-out and legal copy (Issue #341)

Repo-only. Nothing sent, no option changed, no deploy. Builds on #333/#335/#337/#339;
no new review system.

## Changed
- Checkout notice (CZ/EN, `inc/review-request.php`) now says: order/payment/delivery
  e-mails are automatic; the review message is separate, is not a newsletter, can be
  refused at checkout or in the message; accepting the Terms is not marketing consent;
  buying is unaffected. Links to the privacy page. Checkbox stays an unchecked opt-out
  (default = eligible, ticked = this order and address suppressed), persisted per order
  (`_molosoc_review_request_optout`; notice shown = `_molosoc_review_request_notice`).
- CZ Terms and Privacy drafts in `seo/cz-pages/` (the repo source synced to WordPress as
  drafts; publishing is manual): Terms acceptance != marketing consent; new
  "Žádost o hodnocení po nákupu" privacy section.

## Unchanged / safeguards
Mode `off` default shows nothing and makes no order eligible; live needs
`molosoc_review_request_legal_confirmed`; test allowlist, signed opt-out, suppression,
no retroactive orders (notice meta required), payments/fees/transactional mail untouched,
CusRev checkbox untouched (disable its reminders in CusRev first, then
`molosoc_hide_cusrev_checkbox`=1).

## Needs counsel / owner
- Notice and privacy wording are not legal advice; legal basis (Act 480/2004 §7(3) vs
  GDPR legitimate interest) is deliberately NOT stated in the privacy text.
- EN Terms/Privacy source is not in the repo (only the CZ markdown is); the EN pages
  must be updated in WP-admin with equivalent wording after approval.
- Privacy page is dated 21.01.2026 and lists no retention period for the opt-out record.
