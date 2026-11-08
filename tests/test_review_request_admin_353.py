"""Issue #353: admin settings screen for the review request. Registers only;
writes nothing on load; validation guards go-live."""
import json, shutil, subprocess, tempfile, unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "site/theme/inc/review-request-admin.php"
FUNCTIONS = Path(__file__).resolve().parents[1] / "site/theme/functions.php"

PHP = r"""<?php
define( 'ABSPATH', '/' ); $h = array(); $w = 0;
function add_action( $t, $cb ) { global $h; $h[ $t ] = $cb; }
function add_submenu_page() {} function is_email( $e ) { return (bool) filter_var( $e, FILTER_VALIDATE_EMAIL ); }
eval( str_replace( '<?php', '', file_get_contents( $argv[1] ) ) );
$cases = json_decode( $argv[2], true ); $out = array();
foreach ( $cases as $c ) { list( $v, $e ) = molosoc_review_request_admin_validate( $c ); $out[] = array( $v, $e ); }
echo json_encode( array( 'hooks' => array_keys( $h ), 'res' => $out ) );
"""

def run(cases):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "s.php"; f.write_text(PHP)
        o = subprocess.run(["php", str(f), str(MODULE), json.dumps(cases)], capture_output=True, text=True)
    assert o.returncode == 0, o.stdout + o.stderr
    return json.loads(o.stdout)

@unittest.skipUnless(shutil.which("php"), "php not installed")
class AdminTests(unittest.TestCase):
    def test_load_only_registers_hooks(self):
        r = run([])
        self.assertEqual(sorted(r["hooks"]), ["admin_menu", "admin_post_molosoc_review_request_save"])

    def test_required_from_functions(self):
        self.assertIn("inc/review-request-admin.php", FUNCTIONS.read_text())

    def test_validation(self):
        r = run([
            {"mode": "bogus"},
            {"mode": "live", "test_emails": "a@x.cz"},                                   # no legal
            {"mode": "live", "legal_confirmed": "1"},                                    # empty list, no ack
            {"mode": "live", "legal_confirmed": "1", "ack_all_orders": "1"},             # ack ok
            {"mode": "live", "legal_confirmed": "1", "test_emails": "a@x.cz, bad, A@x.cz"},
            {"mode": "dry_run"},
        ])["res"]
        self.assertIsNone(r[0][0]); self.assertIsNone(r[1][0]); self.assertIsNone(r[2][0])
        self.assertEqual(r[3][0]["mode"], "live")
        self.assertEqual(r[4][0]["emails"], "a@x.cz")
        self.assertEqual(r[5][0], {"mode": "dry_run", "emails": "", "legal": ""})

    def test_live_persists_restrictions_before_mode(self):
        src = MODULE.read_text()
        body = src[src.index("function molosoc_review_request_admin_save"):]
        live = body[body.index("if ( 'live' === $v['mode'] )"):body.index("} else {")]
        self.assertLess(live.index("test_emails"), live.index("review_request_mode"))
        self.assertLess(live.index("legal_confirmed"), live.index("review_request_mode"))

if __name__ == "__main__":
    unittest.main()
