# Review e-mail activation, Option B (Issue #337)

Repo-only change. No WP-admin, production site, mail log or secret is reachable
from this session, so **nothing is live, nothing was sent, no setting changed**.

## Added in code
- Checkout (classic, after order notes, CZ/EN): a collection-time notice that
  one review-request message will follow and an **unchecked opt-out** box
  ("I do not want to receive this one review-request message"). Not an opt-in.
  Rendered only when `molosoc_review_request_mode` is `dry_run` or `live`.
- The order stores `_molosoc_review_request_notice` only when the notice was
  submitted with the order. Orders without it are never mailed
  (`no-checkout-notice`), so prior customers, and orders placed while the
  feature was off, are excluded.
- Ticking the box sets the order opt-out and a hashed e-mail suppression
  (also blocks that address on future orders). Existing suppression, the
  one-mail claim, 3-retry cap and opt-out link in the mail are unchanged.

## Czech Act 480/2004 §7(3) prerequisites (not substituted by owner preference)
1. Address obtained in connection with the sale: yes (checkout).
2. Same seller, own similar goods/services: a review request for the bought
   product is arguably in scope; counsel should confirm it counts as a
   commercial communication at all.
3. Clear, free, easy refusal at collection and in every message: added.
4. Clearly identified sender and valid opt-out address: sender is the shop
   mail; the link is in the body.
Whether this satisfies §7(3) is a legal judgment this repo cannot make, so
`molosoc_review_request_legal_confirmed` stays unset until the owner confirms.

## Single owner action to activate (after merge + deploy approval)
In WP-admin set `molosoc_review_request_legal_confirmed`=1 and
`molosoc_review_request_mode`=`live`. Before that, do these checks (all
UNVERIFIED here): native review form submits on CZ and EN product pages;
CusRev invitations/reminders disabled in its settings (cannot be done from
code), then `molosoc_hide_cusrev_checkbox`=1; owner-only test with
`molosoc_review_request_test_emails`=<owner address> in `live` first, placing
a test order with the box unticked and checking the mail, then with it ticked
and checking none is sent. Remove the test list afterwards.

Until the notice has been shown, no customer is eligible; the earliest real
send is 10 days (CZ) / 14 days (abroad) after a notified order is completed.
