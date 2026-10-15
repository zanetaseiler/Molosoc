"""Issue #194: CZ bank-transfer unpaid-order reminder after 24 hours.

Runs site/theme/inc/bacs-payment-reminder.php under PHP against minimal
WordPress/WooCommerce stand-ins (same approach as test_thank_you_gift.py).
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

THEME = Path(__file__).resolve().parents[1] / "site/theme"
REMINDER = THEME / "inc/bacs-payment-reminder.php"
FUNCTIONS = THEME / "functions.php"

NOW = 1_800_000_000
HOUR = 3600

STUBS = r"""<?php
define( 'ABSPATH', '/' );
define( 'HOUR_IN_SECONDS', 3600 );
$T = json_decode( getenv( 'SCENARIO' ), true );
$GLOBALS['T'] = $T;
$GLOBALS['hooks'] = array();
$GLOBALS['scheduled'] = array();
$GLOBALS['mails'] = array();
$GLOBALS['notes'] = array();
$GLOBALS['meta'] = $T['meta'];
function add_action( $tag, $cb, $prio = 10, $args = 1 ) { $GLOBALS['hooks'][ $tag ] = $cb; }
function time_now() { return $GLOBALS['T']['now']; }
function wp_strip_all_tags( $v ) { return strip_tags( $v ); }
function wc_price( $v, $a = array() ) { return '<span>' . number_format( $v, 0, ',', ' ' ) . '&nbsp;<span>K&#269;</span></span>'; }
function as_schedule_single_action( $ts, $hook, $args, $group, $unique ) {
	foreach ( $GLOBALS['scheduled'] as $s ) { if ( $unique && $s['hook'] === $hook && $s['args'] === $args ) { return 0; } }
	$GLOBALS['scheduled'][] = array( 'ts' => $ts, 'hook' => $hook, 'args' => $args, 'group' => $group );
	return 1;
}
function wp_mail( $to, $subject, $body ) { $GLOBALS['mails'][] = array( $to, $subject, $body ); return ! $GLOBALS['T']['mail_fails']; }
function wc_get_order( $id ) { return $GLOBALS['T']['order'] ? new FakeOrder( $GLOBALS['T']['order'] ) : false; }
class FakeOrder {
	function __construct( $d ) { $this->d = $d; }
	function get_payment_method() { return $this->d['payment_method']; }
	function get_billing_country() { return $this->d['billing_country']; }
	function get_shipping_country() { return $this->d['shipping_country']; }
	function get_meta( $k ) { return $GLOBALS['meta'][ $k ] ?? ''; }
	function update_meta_data( $k, $v ) { $GLOBALS['meta'][ $k ] = $v; }
	function delete_meta_data( $k ) { unset( $GLOBALS['meta'][ $k ] ); }
	function save() {}
	function has_status( $s ) { return in_array( $this->d['status'], (array) $s, true ); }
	function is_paid() { return in_array( $this->d['status'], array( 'processing', 'completed' ), true ); }
	function get_date_paid() { return $this->d['date_paid'] ? new FakeDate( $this->d['date_paid'] ) : null; }
	function get_date_created() { return new FakeDate( $this->d['created'] ); }
	function get_order_number() { return '1234'; }
	function get_total() { return 458; }
	function get_currency() { return 'CZK'; }
	function get_billing_email() { return $this->d['email']; }
	function add_order_note( $n ) { $GLOBALS['notes'][] = $n; }
}
class FakeDate { function __construct( $t ) { $this->t = $t; } function getTimestamp() { return $this->t; } }
"""

# `time()` cannot be stubbed in-namespace-free PHP, so the reminder code's
# time() is replaced with time_now() when the file is loaded for the test.
RUNNER = r"""
$code = file_get_contents( $argv[1] );
$code = str_replace( array( '<?php', 'time()' ), array( '', 'time_now()' ), $code );
eval( $code );
$GLOBALS['hooks']['woocommerce_order_status_on-hold']( 1 );
$GLOBALS['hooks']['woocommerce_order_status_on-hold']( 1 );
$after_schedule = $GLOBALS['scheduled'];
// The action being executed is still pending/running: model it so unique=true collides.
$GLOBALS['scheduled'] = array( array( 'ts' => 0, 'hook' => 'molosoc_bacs_unpaid_reminder', 'args' => array( 1 ), 'group' => 'molosoc', 'running' => true ) );
for ( $i = 0; $i < $GLOBALS['T']['runs']; $i++ ) { $GLOBALS['hooks']['molosoc_bacs_unpaid_reminder']( 1 ); }
echo json_encode( array(
	'scheduled' => $after_schedule,
	'rescheduled' => array_values( array_filter( $GLOBALS['scheduled'], function ( $s ) { return empty( $s['running'] ); } ) ),
	'mails' => $GLOBALS['mails'],
	'notes' => $GLOBALS['notes'],
	'meta' => $GLOBALS['meta'],
), JSON_UNESCAPED_UNICODE );
"""


def run_php(**over):
    missing = "order" in over and over["order"] is None
    order = dict(
        payment_method="bacs", billing_country="CZ", shipping_country="CZ",
        status="on-hold", date_paid=None, created=NOW - 25 * HOUR,
        email="zakaznik@example.cz",
    )
    order.update(over.pop("order", None) or {})
    scenario = dict(now=NOW, order=None if missing else order, meta={}, mail_fails=False, runs=1)
    scenario.update(over)
    with tempfile.TemporaryDirectory() as d:
        stubs = Path(d) / "stubs.php"
        stubs.write_text(STUBS + RUNNER)
        env = dict(os.environ, SCENARIO=json.dumps(scenario))
        out = subprocess.run(
            ["php", "-d", "display_errors=1", str(stubs), str(REMINDER)],
            capture_output=True, text=True, env=env,
        )
    assert out.returncode == 0, out.stdout + out.stderr
    return json.loads(out.stdout)


@unittest.skipUnless(shutil.which("php"), "php not installed")
class BacsReminderTests(unittest.TestCase):
    def test_cz_bacs_unpaid_sends_after_24h(self):
        r = run_php()
        self.assertEqual(len(r["mails"]), 1)
        to, subject, body = r["mails"][0]
        self.assertEqual(to, "zakaznik@example.cz")
        self.assertEqual(subject, "Připomínka k platbě objednávky č. 1234")
        self.assertIn("č. 1234 v hodnotě 458 Kč", body)
        self.assertIn("Zatím ji u objednávky nevidíme", body)
        self.assertIn("tuto zprávu prosím ignorujte", body)
        self.assertIn("odpovědět na tento e-mail", body)

    def test_no_bank_credentials_or_marketing_language(self):
        body = run_php()["mails"][0][2].lower()
        for word in ("iban", "účet", "swift", "odhlásit", "newsletter", "unsubscribe"):
            self.assertNotIn(word, body)

    def test_pending_order_also_sends(self):
        self.assertEqual(len(run_php(order={"status": "pending"})["mails"]), 1)

    def test_timing_scheduled_24h_after_creation_and_unique(self):
        r = run_php()
        self.assertEqual(len(r["scheduled"]), 1)  # two status hooks -> one action
        s = r["scheduled"][0]
        self.assertEqual(s["ts"], NOW - 25 * HOUR + 24 * HOUR)
        self.assertEqual(s["hook"], "molosoc_bacs_unpaid_reminder")
        self.assertEqual(s["args"], [1])

    def test_early_run_does_not_send_and_reschedules_at_due_time(self):
        created = NOW - 2 * HOUR
        r = run_php(order={"created": created})
        self.assertEqual(r["mails"], [])
        self.assertEqual(len(r["rescheduled"]), 1)  # not rejected as dup of the running action
        self.assertEqual(r["rescheduled"][0]["ts"], created + 24 * HOUR)
        self.assertEqual(r["rescheduled"][0]["args"], [1, 1])

    def test_paid_order_suppressed(self):
        self.assertEqual(run_php(order={"date_paid": NOW - HOUR})["mails"], [])

    def test_non_bacs_suppressed(self):
        for method in ("comgate", "cod", "stripe"):
            r = run_php(order={"payment_method": method})
            self.assertEqual(r["mails"], [], method)
            self.assertEqual(r["scheduled"], [], method)

    def test_non_cz_suppressed(self):
        r = run_php(order={"billing_country": "DE", "shipping_country": "DE"})
        self.assertEqual((r["mails"], r["scheduled"]), ([], []))

    def test_terminal_statuses_suppressed(self):
        for status in ("processing", "completed", "cancelled", "refunded",
                       "failed", "trash"):
            self.assertEqual(run_php(order={"status": status})["mails"], [], status)

    def test_missing_order_suppressed(self):
        self.assertEqual(run_php(order=None)["mails"], [])

    def test_duplicate_execution_sends_once(self):
        r = run_php(runs=3)
        self.assertEqual(len(r["mails"]), 1)
        self.assertIn("_molosoc_bacs_reminder_sent", r["meta"])

    def test_already_sent_order_not_resent_or_rescheduled(self):
        r = run_php(meta={"_molosoc_bacs_reminder_sent": "1"})
        self.assertEqual((r["mails"], r["scheduled"]), ([], []))

    def test_failed_mail_releases_claim_for_retry(self):
        r = run_php(mail_fails=True)
        self.assertNotIn("_molosoc_bacs_reminder_sent", r["meta"])
        self.assertEqual(len(r["rescheduled"]), 1)
        self.assertEqual(r["rescheduled"][0]["ts"], NOW + HOUR)
        self.assertEqual(r["rescheduled"][0]["args"], [1, 1])

    def test_no_marketing_consent_dependency(self):
        # Executable code only (comments stripped): no subscription/consent gate.
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", REMINDER.read_text(), flags=re.S).lower()
        for token in ("wc_subscription_status", "consent", "newsletter",
                      "brevo", "sib_", "get_user_meta"):
            self.assertNotIn(token, code, token)
        # Works for a guest order with no user and no stored consent at all.
        self.assertEqual(len(run_php()["mails"]), 1)

    def test_required_from_functions(self):
        self.assertIn("inc/bacs-payment-reminder.php", FUNCTIONS.read_text())


if __name__ == "__main__":
    unittest.main()
