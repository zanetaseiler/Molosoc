# One-time TEST mail: Brevo / WordPress delivery (Issue #366)

**Status:** repository-only. Nothing has been sent. Merging or deploying this file sends nothing. It stays inert until the wp-config flag below is set, and nothing is sent until an admin clicks the button once.

## What it is

`site/mu-plugins/molosoc-test-mail-366.php` adds one admin-only screen, **Tools → MOLOSOC TEST e-mail**, with one button. The button sends **exactly one** email through the existing path: `wp_mail()` → WP Mail SMTP → Brevo.

| Field | Value (fixed in code, not editable) |
|---|---|
| To | `jarka01@atlas.cz` |
| Cc | `hello@molosoc.com` |
| From | Not set by this plugin. WP Mail SMTP's forced sender applies (`hello@molosoc.com`, verified in Brevo per ZANETA_DECISION). |
| Subject | `MOLOSOC – TEST doručování přepravních štítků (není skutečná objednávka)` |
| Body | The Czech text from the issue body, as plain UTF-8 text |
| Attachment | `MOLOSOC-TEST-neni-stitek.pdf`. This is a generated one-page PDF (under 1 KB) reading "TEST - NENI SKUTECNY STITEK / TEST ONLY - NOT A SHIPPING LABEL". |

## Safety

- **OFF by default.** Hooks, the menu and the handler are registered only when `wp-config.php` sets `define( 'MOLOSOC_TEST_MAIL_366_ENABLED', true );`. The value must be exactly `true`; `1` or `'true'` does not count.
- **Admin only.** The action needs `manage_options` and a valid nonce, and it is a POST to `admin-post.php`.
- **Exactly once, durably.** Before `wp_mail()` runs, the code claims the option `molosoc_test_mail_366_lock` with an atomic `INSERT IGNORE`. The lock is never released, even if the send fails or errors. A double-click, a reload or a second admin gets `already_used`, and the screen then shows the stored result instead of the button.
- **No ability to change anything.** No request field reaches the recipient, subject, body or attachment.
- **No other effects.** It does not touch orders, packets, shipping, checkout or payment. It does not load WooCommerce or the carrier label pipeline. It adds no mail filters and never reads or changes WP Mail SMTP or Brevo settings or keys.
- The temporary PDF is written to a private temp directory and always removed.
- The tests (`tests/test_test_mail_366.py`) run real PHP with injected I/O. They never call a real `wp_mail()` and make no network calls.

## Operator steps (only after Žaneta approves merge + deploy)

1. Deploy the mu-plugin file. It stays inert.
2. In `wp-config.php`, add `define( 'MOLOSOC_TEST_MAIL_366_ENABLED', true );`.
3. Go to wp-admin → **Tools → MOLOSOC TEST e-mail**. Check that the To, Cc, subject and body are shown. Click **Odeslat jediný TEST e-mail** **once** and confirm the dialog.
4. Note the result code: `sent`, `wp_mail_false` or `tempfile_failed`. `sent` means only that `wp_mail()` returned true.
5. Check Brevo → Transactional → Logs for the message to `jarka01@atlas.cz` (and the Cc). Record the status (Delivered / Bounced / …) and the sender shown. The WP Mail SMTP → Email Log, if enabled, may show the same.
6. Disable it right away (below). Report the result code and Brevo status on Issue #366.

If the result is not `sent`, **do not** try to reset the lock to retry. A retry is a second send and needs a new `ZANETA_DECISION`.

## Disable / remove

- **Disable:** remove the `MOLOSOC_TEST_MAIL_366_ENABLED` line from `wp-config.php`. All hooks, the menu and the handler disappear.
- **Remove:** delete `wp-content/mu-plugins/molosoc-test-mail-366.php` from the server, and remove it from the repo in a follow-up PR.
- **Lock record:** you may keep the `molosoc_test_mail_366_lock` option as an audit record. It holds the result, the user id and a timestamp, and no secrets. Delete it only **after** the plugin file is removed. If you delete it while the file and flag are still present, one more send becomes possible.
