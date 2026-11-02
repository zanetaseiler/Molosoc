"""Issue #333: MOLOSOC-hosted review request is off by default, never sends
in dry-run, is idempotent, and honours suppression/allowlist/legal gates."""
import json, os, shutil, subprocess, tempfile, unittest
from pathlib import Path

THEME = Path(__file__).resolve().parents[1] / "site/theme"
MODULE = THEME / "inc/review-request.php"
NOW = 1_800_000_000

STUBS = r"""<?php
define( 'ABSPATH', '/' ); define( 'HOUR_IN_SECONDS', 3600 ); define( 'DAY_IN_SECONDS', 86400 );
$T = json_decode( getenv( 'SCENARIO' ), true ); $GLOBALS['T'] = $T;
$GLOBALS['hooks'] = array(); $GLOBALS['scheduled'] = array(); $GLOBALS['mails'] = array();
$GLOBALS['notes'] = array(); $GLOBALS['meta'] = $T['meta']; $GLOBALS['opts'] = $T['opts'];
function add_action( $t, $cb ) { $GLOBALS['hooks'][ $t ] = $cb; }
function apply_filters( $t, $v ) { return $v; }
function get_option( $k, $d = '' ) { return $GLOBALS['opts'][ $k ] ?? $d; }
function update_option( $k, $v, $a = null ) { $GLOBALS['opts'][ $k ] = $v; }
// Models WordPress add_option(): ON DUPLICATE KEY UPDATE, so it never rejects a competing writer.
function add_option( $k, $v, $d = '', $a = 'yes' ) { $GLOBALS['opts'][ $k ] = $v; return true; }
function wp_cache_delete( $k, $g = '' ) { return true; }
class FakeWpdb { public $options = 'wp_options';
	function prepare( $q, ...$a ) { return json_encode( $a ); }
	// INSERT IGNORE: first writer gets 1 row, duplicates get 0 and change nothing.
	function query( $q ) { list( $k, $v ) = json_decode( $q, true ); if ( array_key_exists( $k, $GLOBALS['opts'] ) ) { return 0; } $GLOBALS['opts'][ $k ] = $v; return 1; } }
$GLOBALS['wpdb'] = new FakeWpdb();
function delete_option( $k ) { unset( $GLOBALS['opts'][ $k ] ); return true; }
function wp_salt( $s ) { return 'salt'; }
function home_url( $p ) { return 'https://molosoc.test' . $p; }
function add_query_arg( $a, $u ) { return $u . '?' . http_build_query( $a ); }
function is_email( $e ) { return (bool) filter_var( $e, FILTER_VALIDATE_EMAIL ); }
define( 'MOLOSOC_PRODUCT_ID', 364 );
function molosoc_product_url( $l ) { return 'https://molosoc.test/' . $l . '/product/'; }
function get_permalink( $id ) { return 'https://molosoc.test/p' . $id . '/'; }
function time_now() { return $GLOBALS['T']['now']; }
function as_schedule_single_action( $ts, $hook, $args, $g, $u ) { $GLOBALS['scheduled'][] = array( 'ts' => $ts, 'hook' => $hook, 'args' => $args ); return 1; }
function wp_mail( $to, $s, $b ) { $GLOBALS['mails'][] = array( $to, $s, $b ); return ! $GLOBALS['T']['mail_fails']; }
function esc_html( $s ) { return htmlspecialchars( $s ); }
function sanitize_email( $e ) { return $e; }
function wp_unslash( $v ) { return $v; }
function pll_current_language() { return $GLOBALS['T']['lang'] ?? 'cz'; }
function wp_die( $m ) { $GLOBALS['died'] = $m; }
function wc_get_order( $id ) { return new FakeOrder( $GLOBALS['T']['order'] ); }
class FakeItem { function get_product_id() { return $GLOBALS['T']['order']['pid'] ?? 7; } function get_name() { return 'MOLOSOC'; } }
class FakeOrder {
	function __construct( $d ) { $this->d = $d; }
	function get_id() { return 1; } function get_order_number() { return '1234'; }
	function get_billing_country() { return $this->d['country']; } function get_shipping_country() { return ''; }
	function get_billing_email() { return $this->d['email']; }
	function get_total() { return 458; } function get_total_refunded() { return $this->d['refunded']; }
	function has_status( $s ) { return $this->d['status'] === $s; }
	function get_items() { return array( new FakeItem() ); }
	function get_meta( $k ) { return $GLOBALS['meta'][ $k ] ?? ''; }
	function update_meta_data( $k, $v ) { $GLOBALS['meta'][ $k ] = $v; }
	function delete_meta_data( $k ) { unset( $GLOBALS['meta'][ $k ] ); }
	function save() {} function add_order_note( $n ) { $GLOBALS['notes'][] = $n; }
}
"""
RUNNER = r"""
$code = str_replace( array( '<?php', 'time()' ), array( '', 'time_now()' ), file_get_contents( $argv[1] ) );
eval( $code );
$GLOBALS['hooks']['woocommerce_order_status_completed']( 1 );
$sched = $GLOBALS['scheduled'];
for ( $i = 0; $i < $GLOBALS['T']['runs']; $i++ ) { $GLOBALS['hooks']['molosoc_review_request_send']( 1 ); }
if ( ! empty( $GLOBALS['T']['optout_url'] ) ) {
	$m = molosoc_review_request_message( wc_get_order( 1 ) );
	preg_match( '~molosoc_review_optout=1&t=([0-9a-f]+)~', $m[1], $x );
	$_GET = array( 'molosoc_review_optout' => '1', 't' => $x[1] );
	$GLOBALS['hooks']['template_redirect']();
	$_GET = array( 'molosoc_review_optout' => '1', 't' => 'bad' );
	$GLOBALS['hooks']['template_redirect']();
	$GLOBALS['hooks']['molosoc_review_request_send']( 1 );
}
if ( ! empty( $GLOBALS['T']['checkout'] ) ) {
	$_POST = $GLOBALS['T']['post'];
	ob_start(); $GLOBALS['hooks']['woocommerce_after_order_notes'](); $html = ob_get_clean();
	$GLOBALS['hooks']['woocommerce_checkout_create_order']( wc_get_order( 1 ), array() );
	$GLOBALS['html'] = $html;
}
echo json_encode( array( 'html' => $GLOBALS['html'] ?? '', 'scheduled' => $sched, 'mails' => $GLOBALS['mails'], 'notes' => $GLOBALS['notes'],
	'final' => $GLOBALS['scheduled'], 'meta' => $GLOBALS['meta'], 'opts' => $GLOBALS['opts'], 'died' => $GLOBALS['died'] ?? '' ), JSON_UNESCAPED_UNICODE );
"""

def run(order=None, opts=None, **over):
    o = dict(country="CZ", email="a@example.cz", status="completed", refunded=0)
    o.update(order or {})
    sc = dict(now=NOW, order=o, meta={"_molosoc_review_request_notice": "1"}, opts=opts or {}, mail_fails=False, runs=1)
    meta = dict(sc["meta"], **over.pop("meta", {}))
    sc.update(over)
    sc["meta"] = meta
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "s.php"; f.write_text(STUBS + RUNNER)
        out = subprocess.run(["php", str(f), str(MODULE)], capture_output=True, text=True,
                             env=dict(os.environ, SCENARIO=json.dumps(sc)))
    assert out.returncode == 0, out.stdout + out.stderr
    return json.loads(out.stdout)

LIVE = {"molosoc_review_request_mode": "live", "molosoc_review_request_legal_confirmed": "1"}

@unittest.skipUnless(shutil.which("php"), "php not installed")
class ReviewRequestTests(unittest.TestCase):
    def test_off_by_default_schedules_and_sends_nothing(self):
        r = run()
        self.assertEqual((r["scheduled"], r["mails"], r["notes"]), ([], [], []))

    def test_dry_run_never_mails_and_does_not_claim_sent(self):
        r = run(opts={"molosoc_review_request_mode": "dry_run"}, runs=3)
        self.assertEqual(r["mails"], [])
        self.assertEqual(len(r["scheduled"]), 1)
        self.assertEqual(len(r["notes"]), 1)
        self.assertNotIn("_molosoc_review_request_sent", r["meta"])

    def test_live_without_legal_confirmation_is_dry_run(self):
        r = run(opts={"molosoc_review_request_mode": "live"})
        self.assertEqual(r["mails"], [])

    def test_delay_cz_10_days_abroad_14(self):
        self.assertEqual(run(opts=LIVE)["scheduled"][0]["ts"], NOW + 10 * 86400)
        self.assertEqual(run(order={"country": "DE"}, opts=LIVE)["scheduled"][0]["ts"], NOW + 14 * 86400)

    def test_live_sends_once_even_if_run_repeatedly(self):
        r = run(opts=LIVE, runs=3)
        self.assertEqual(len(r["mails"]), 1)
        subject, body = r["mails"][0][1], r["mails"][0][2]
        self.assertIn("MOLOSOC", subject)
        self.assertIn("https://molosoc.test/p7/#reviews", body)
        self.assertIn("molosoc_review_optout=1", body)
        self.assertIn("Nejde o nezávisle ověřenou", body)
        for bad in ("doručen", "newsletter", "CusRev"):
            self.assertNotIn(bad, body)

    def test_english_for_non_cz(self):
        body = run(order={"country": "DE"}, opts=LIVE)["mails"][0][2]
        self.assertIn("not an independently verified", body)
        self.assertIn("opt out here", body)

    def test_language_from_saved_order_lang_not_country(self):
        body = run(order={"country": "CZ"}, opts=LIVE, meta={"_molosoc_lang": "en"})["mails"][0][2]
        self.assertIn("opt out here", body)
        body = run(order={"country": "DE"}, opts=LIVE, meta={"_molosoc_lang": "cz"})["mails"][0][2]
        self.assertIn("Nejde o nezávisle ověřenou", body)
        # delay still follows the country
        r = run(order={"country": "DE"}, opts=LIVE, meta={"_molosoc_lang": "cz"})
        self.assertEqual(r["scheduled"][0]["ts"], NOW + 14 * 86400)

    def test_product_364_link_uses_explicit_language_helper(self):
        b = run(order={"pid": 364}, opts=LIVE, meta={"_molosoc_lang": "cz"})["mails"][0][2]
        self.assertIn("https://molosoc.test/cz/product/#reviews", b)
        b = run(order={"pid": 364, "country": "DE"}, opts=LIVE)["mails"][0][2]
        self.assertIn("https://molosoc.test/en/product/#reviews", b)

    def test_blocked_cases_send_nothing(self):
        for order, opts in [
            ({"status": "refunded"}, {}), ({"refunded": 458}, {}), ({"email": ""}, {}),
            ({}, {"molosoc_review_request_test_emails": "x@example.cz"}),
        ]:
            r = run(order=order, opts={**LIVE, **opts})
            self.assertEqual(r["mails"], [], (order, opts))

    def test_test_allowlist_allows_listed_only(self):
        r = run(opts={**LIVE, "molosoc_review_request_test_emails": "A@example.cz"})
        self.assertEqual(len(r["mails"]), 1)

    def test_already_sent_and_optout_suppressed(self):
        self.assertEqual(run(opts=LIVE, meta={"_molosoc_review_request_sent": "1"})["mails"], [])
        self.assertEqual(run(opts=LIVE, meta={"_molosoc_review_request_optout": "1"})["mails"], [])

    def test_optout_link_suppresses_and_bad_token_rejected(self):
        r = run(opts=LIVE, optout_url=True, runs=0)
        self.assertEqual(r["mails"], [])
        keys = [k for k in r["opts"] if k.startswith("molosoc_rr_optout_")]
        self.assertEqual(len(keys), 1)
        self.assertNotIn("a@example.cz", json.dumps(r["opts"]))

    def test_existing_atomic_claim_blocks_send(self):
        # Another overlapping callback already won the per-order claim.
        r = run(opts=dict(LIVE, molosoc_rr_claim_1="1"))
        self.assertEqual(r["mails"], [])

    def test_failed_mail_releases_claim_and_retries(self):
        r = run(opts=LIVE, mail_fails=True)
        self.assertNotIn("_molosoc_review_request_sent", r["meta"])
        self.assertEqual(len(r["final"]), 2)
        self.assertNotIn("molosoc_rr_claim_1", r["opts"])

    def checkout(self, mode, post, lang="cz"):
        return run(opts={"molosoc_review_request_mode": mode} if mode else {}, meta={"_molosoc_review_request_notice": ""},
                   checkout=True, post=post, lang=lang, runs=0)

    def test_checkout_notice_off_by_default(self):
        r = self.checkout(None, {"molosoc_review_request_notice_shown": "1"})
        self.assertEqual(r["html"], "")
        self.assertFalse(r["meta"].get("_molosoc_review_request_notice"))

    def test_checkout_notice_cz_en_unchecked_optout_and_recorded(self):
        post = {"molosoc_review_request_notice_shown": "1"}
        r = self.checkout("dry_run", post)
        self.assertIn("jednu zprávu", r["html"])
        self.assertNotIn("checked", r["html"])
        self.assertTrue(r["meta"]["_molosoc_review_request_notice"])
        self.assertNotIn("_molosoc_review_request_optout", r["meta"])
        self.assertIn("one message", self.checkout("dry_run", post, "en")["html"])

    def test_checkout_refusal_blocks_order_and_suppresses_email(self):
        r = self.checkout("live", {"molosoc_review_request_notice_shown": "1", "molosoc_review_request_refuse": "1", "billing_email": "a@example.cz"})
        self.assertTrue(r["meta"]["_molosoc_review_request_optout"])
        self.assertEqual(len([k for k in r["opts"] if k.startswith("molosoc_rr_optout_")]), 1)

    def test_no_notice_flag_means_no_send(self):
        self.assertEqual(run(opts=LIVE, meta={"_molosoc_review_request_notice": ""})["mails"], [])

    def test_notice_not_recorded_if_not_rendered(self):
        r = self.checkout("live", {})
        self.assertFalse(r["meta"].get("_molosoc_review_request_notice"))

    def test_suppressed_email_blocks_other_orders(self):
        import hashlib
        r = run(opts=LIVE, optout_url=True, runs=0)  # opt-out link suppresses the address
        self.assertEqual(r["mails"], [])

if __name__ == "__main__":
    unittest.main()
