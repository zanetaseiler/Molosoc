# Review rollout (Issue #335)

No live site, WP-admin, mail log or secrets are reachable from this session
(`curl https://molosoc.com` fails from the sandbox), so nothing below was
verified or changed in production. Everything stays default-off.

## Shipped (repo only)
- Option `molosoc_hide_cusrev_checkbox` (default `0`): when `1`, the CusRev
  checkout opt-in row is hidden on checkout via CSS. Input stays unchecked, so
  no consent is recorded. Set it only after the checks below.

## Owner/ops steps (WP-admin), in order
1. WooCommerce > Settings > Products: reviews enabled; check the Reviews tab on
   the CZ and EN product pages and that the form submits.
2. CusRev: note mode, disable invitation sending/reminders.
3. Staging: `molosoc_review_request_mode`=`dry_run`, then
   `molosoc_review_request_test_emails`=<owner address> with `live` (legal flag
   on staging only); check language, review link and opt-out link.
4. Set `molosoc_hide_cusrev_checkbox`=1.
5. Production `live` only after the blocker below is cleared.

## The ONE blocker
Czech compliance (Act 480/2004 §7(3)): a collection-time notice at checkout
that the customer will get one review e-mail and can opt out. No notice is in
the theme and its wording needs owner/counsel sign-off. Until then
`molosoc_review_request_legal_confirmed` must stay unset and live sending stays
disabled. If the wording in docs/review-request-333.md is approved, adding it is a
small follow-up change.
