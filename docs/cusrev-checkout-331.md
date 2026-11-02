# CusRev checkout invitation audit (Issue #331)

Repo-side findings only. No live site, WP-admin, mail log or CusRev account
access exists from this repo/session, so anything marked UNVERIFIED needs an
owner check. Nothing here disables the plugin, changes consent, or touches
production settings.

## Verified from the repo
- Since #267 the theme (`site/theme/inc/checkout-cleanup.php`) translates the
  plugin's opt-in sentence on the Czech checkout through the core `gettext`
  filter (any domain). The box is not pre-checked, not hidden, and reminders
  are not touched. The English checkout keeps the plugin text.
- The owner screenshot shows English on the CZ checkout, so the filter did not
  take effect live. Likely causes (UNVERIFIED): the text is a saved plugin
  option (not a translatable string), or the plugin renders it before
  Polylang's language is resolved/cached. Fix needs the option value from
  WP-admin (see steps).
- The opt-in is CusRev's own review-invitation consent, separate from any
  newsletter checkbox. No repo code conflates them; any overlap is plugin or
  WPConsent configuration (UNVERIFIED).

## Changed in this PR
- `site/theme/assets/css/checkout.css`: CSS-only restyle of the CusRev
  checkbox row (bordered, padded, flex-aligned, 18px checkbox, focus ring,
  mobile tweak), separated from the payment methods. Markup, input name,
  default state and submission are unchanged.
- The selectors target the plugin's known wrapper/input name
  (`cr_customer_consent`); UNVERIFIED against the live markup.

## UNVERIFIED - owner steps (WP-admin, read-only unless stated)
1. Plugins: confirm Customer Reviews for WooCommerce version.
2. Settings > Customer Reviews > Reviews: note mode (CusRev-hosted vs local),
   trigger status(es), delay in days, "Checkout checkbox" setting and its text
   field, language, sender/email template.
3. Check Orders for the CusRev meta/notes showing invitations sent, and the
   Reviews tab/WooCommerce > Products > Reviews for published reviews.
4. If the checkbox text is a saved setting, paste it (or replace it with the
   Czech text) in that field; the English text can then be set separately.
5. On a staging/test order: confirm the unchecked box sends no invitation.
