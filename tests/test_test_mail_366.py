"""Issue #366: admin-only one-time TEST mail. Real PHP with injected I/O; no WordPress,
no network, no mail is ever sent."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "site/mu-plugins/molosoc-test-mail-366.php"
SRC = PLUGIN.read_text(encoding="utf-8")
# Executable code only: doc/line comments removed (the safety contract mentions what it avoids).
CODE = re.sub(r"^\s*//.*$", "", re.sub(r"/\*.*?\*/", "", SRC, flags=re.S), flags=re.M)
HAVE_PHP = shutil.which("php") is not None

STUBS = ("define('ABSPATH','/x/'); $GLOBALS['hooks']=[]; $GLOBALS['wp_mail']=0;"
         "function add_action($h){ $GLOBALS['hooks'][]=$h; }"
         "function wp_mail(){ $GLOBALS['wp_mail']++; return true; }")


def php(code, pre=""):
    full = STUBS + pre + "require %s;" % json.dumps(str(PLUGIN)) + code
    out = subprocess.run(["php", "-r", full], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


# One shared in-memory lock; send counts calls and records arguments.
RUN = """
$S=['lock'=>%s,'sent'=>[],'tmp'=>0,'rm'=>[],'rec'=>[]];
$io=['enabled'=>%s,'can'=>%s,'nonce_ok'=>%s,
 'claim'=>function() use (&$S){ if($S['lock']){return false;} $S['lock']=true; return true; },
 'tmp'=>function($n,$b) use (&$S){ $S['tmp']++; $S['pdf']=$b; $S['name']=$n; return %s; },
 'rm'=>function($p) use (&$S){ $S['rm'][]=$p; },
 'send'=>function($to,$su,$bo,$h,$a) use (&$S){ $S['sent'][]=[$to,$su,$bo,$h,$a,$S['lock']]; %s },
 'record'=>function($r) use (&$S){ $S['rec'][]=$r; }];
$res=[]; for($i=0;$i<%d;$i++){ $res[]=molosoc_tm366_execute($io); }
unset($S['pdf']); echo json_encode(['res'=>$res,'S'=>$S]);
"""


def run(enabled="true", can="true", nonce="true", lock="false", tmp="'/tmp/d/x.pdf'",
        send="return true;", runs=1):
    return php(RUN % (lock, enabled, can, nonce, tmp, send, runs))


@unittest.skipUnless(HAVE_PHP, "php not installed")
class OffByDefault(unittest.TestCase):
    def test_no_hooks_without_constant(self):
        self.assertEqual(php("echo json_encode($GLOBALS['hooks']);"), [])

    def test_truthy_non_true_constant_registers_nothing(self):
        for v in ("1", "'1'", "'true'", "false"):
            pre = "define('MOLOSOC_TEST_MAIL_366_ENABLED',%s);" % v
            self.assertEqual(php("echo json_encode($GLOBALS['hooks']);", pre), [], v)

    def test_true_registers_only_admin_hooks(self):
        pre = "define('MOLOSOC_TEST_MAIL_366_ENABLED',true);"
        self.assertEqual(php("echo json_encode($GLOBALS['hooks']);", pre),
                         ["admin_post_molosoc_test_mail_366", "admin_menu"])

    def test_loading_never_sends(self):
        pre = "define('MOLOSOC_TEST_MAIL_366_ENABLED',true);"
        self.assertEqual(php("echo json_encode($GLOBALS['wp_mail']);", pre), 0)

    def test_disabled_core_sends_nothing(self):
        for e in ("false", "null", "1"):
            r = run(enabled=e)
            self.assertEqual(r["res"], ["disabled"])
            self.assertEqual(r["S"]["sent"], [])
            self.assertFalse(r["S"]["lock"])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Authorization(unittest.TestCase):
    def test_non_admin_refused_without_claiming_lock(self):
        r = run(can="false")
        self.assertEqual(r["res"], ["forbidden"])
        self.assertEqual(r["S"]["sent"], [])
        self.assertFalse(r["S"]["lock"])

    def test_bad_nonce_refused_without_claiming_lock(self):
        r = run(nonce="false")
        self.assertEqual(r["res"], ["bad_nonce"])
        self.assertEqual(r["S"]["sent"], [])
        self.assertFalse(r["S"]["lock"])

    def test_handler_checks_capability_and_nonce(self):
        self.assertIn("current_user_can( MOLOSOC_TM366_CAP )", SRC)
        self.assertIn("wp_verify_nonce(", SRC)
        self.assertIn("const MOLOSOC_TM366_CAP      = 'manage_options';", SRC)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class ExactlyOnce(unittest.TestCase):
    def test_single_send_then_locked(self):
        r = run(runs=3)
        self.assertEqual(r["res"], ["sent", "already_used", "already_used"])
        self.assertEqual(len(r["S"]["sent"]), 1)
        self.assertEqual(r["S"]["rec"], [{"result": "sent"}])

    def test_lock_claimed_before_send(self):
        r = run()
        self.assertTrue(r["S"]["sent"][0][5])

    def test_failed_send_still_consumes_lock(self):
        r = run(send="return false;", runs=2)
        self.assertEqual(r["res"], ["wp_mail_false", "already_used"])
        self.assertEqual(len(r["S"]["sent"]), 1)

    def test_throwing_send_still_consumes_lock_and_removes_file(self):
        code = ((RUN % ("false", "true", "true", "true", "'/tmp/d/x.pdf'", "throw new Exception('x');", 0)).rsplit("unset(", 1)[0] +
                "try{molosoc_tm366_execute($io);}catch(Exception $e){} "
                "echo json_encode([molosoc_tm366_execute($io),$S['rm'],count($S['sent'])]);")
        self.assertEqual(php(code), ["already_used", ["/tmp/d/x.pdf"], 1])

    def test_preexisting_lock_blocks(self):
        r = run(lock="true")
        self.assertEqual(r["res"], ["already_used"])
        self.assertEqual(r["S"]["sent"], [])
        self.assertEqual(r["S"]["tmp"], 0)

    def test_tempfile_failure_sends_nothing_and_stays_locked(self):
        r = run(tmp="''", runs=2)
        self.assertEqual(r["res"], ["tempfile_failed", "already_used"])
        self.assertEqual(r["S"]["sent"], [])

    def test_temp_file_always_removed(self):
        for send in ("return true;", "return false;"):
            self.assertEqual(run(send=send)["S"]["rm"], ["/tmp/d/x.pdf"])

    def test_real_tempfile_written_with_fixed_name_then_removed(self):
        pre = ("function get_temp_dir(){return sys_get_temp_dir();} function trailingslashit($p){return rtrim($p,'/').'/';}"
               "function wp_generate_password(){return bin2hex(random_bytes(8));} function wp_mkdir_p($d){return mkdir($d,0700,true);}")
        r = php("$p=molosoc_tm366_tmp(MOLOSOC_TM366_FILENAME,molosoc_tm366_pdf()); $a=[basename($p),is_file($p),"
                "filesize($p)===strlen(molosoc_tm366_pdf())]; molosoc_tm366_rm($p); $a[]=file_exists($p);"
                "$a[]=file_exists(dirname($p)); echo json_encode($a);", pre)
        self.assertEqual(r, ["MOLOSOC-TEST-neni-stitek.pdf", True, True, False, False])

    def test_db_claim_is_atomic_insert_ignore(self):
        self.assertIn("INSERT IGNORE INTO {$wpdb->options}", CODE)
        self.assertIn("return 1 === (int) $rows;", CODE)
        self.assertFalse("add_option(" in CODE or "delete_option(" in CODE)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class FixedContent(unittest.TestCase):
    BODY = ("Ahoj mami,\n\nposíláme pouze zkušební e-mail, abychom ověřili, že správně funguje "
            "automatické zasílání přepravních štítků z MOLOSOC.\n\nV příloze je testovací PDF, nejde o "
            "skutečnou objednávku ani o štítek k odeslání zásilky.\n\nNemusíš nic tisknout ani odesílat."
            "\n\nDěkujeme!")

    def test_message_exact(self):
        r = run()
        to, subj, body, headers, att, _ = r["S"]["sent"][0]
        self.assertEqual(to, "jarka01@atlas.cz")
        self.assertEqual(subj, "MOLOSOC – TEST doručování přepravních štítků (není skutečná objednávka)")
        self.assertEqual(body, self.BODY)
        self.assertEqual(headers, ["Content-Type: text/plain; charset=UTF-8", "Cc: hello@molosoc.com"])
        self.assertEqual(att, ["/tmp/d/x.pdf"])
        self.assertEqual(r["S"]["name"], "MOLOSOC-TEST-neni-stitek.pdf")

    def test_no_request_data_reaches_message(self):
        # The only superglobal reads are the nonce and the result code shown on the screen.
        self.assertEqual(sorted(set(re.findall(r"\$_(?:POST|GET|REQUEST)\['(\w+)'\]", SRC))),
                         ["_wpnonce", "tm366"])
        self.assertNotIn("$_REQUEST", SRC)
        msg = SRC[SRC.index("function molosoc_tm366_message()"):SRC.index("function molosoc_tm366_pdf()")]
        self.assertNotIn("$", msg.replace("$m", ""))

    def test_no_order_shipping_payment_or_settings_effects(self):
        for bad in ("wc_get_order", "WC_Order", "update_status", "update_meta", "set_status",
                    "molosoc_ld", "packet", "Packeta", "comgate", "wp_mail_from", "phpmailer_init",
                    "pre_wp_mail", "api_key", "From:", "wp_schedule", "add_filter("):
            self.assertFalse(bad.lower() in CODE.lower(), bad)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class TestPdf(unittest.TestCase):
    def setUp(self):
        self.pdf = subprocess.run(["php", "-r", "define('ABSPATH','/x/'); function add_action(){} require %s;"
                                   " echo molosoc_tm366_pdf();" % json.dumps(str(PLUGIN))],
                                  capture_output=True, check=True).stdout

    def test_valid_small_marked_test_pdf(self):
        p = self.pdf
        self.assertTrue(p.startswith(b"%PDF-1.4\n"))
        self.assertTrue(p.rstrip().endswith(b"%%EOF"))
        self.assertRegex(p, rb"/Type /Page(?![s\w])")
        self.assertLess(len(p), 4096)
        for t in (b"TEST - NENI SKUTECNY STITEK", b"TEST ONLY - NOT A SHIPPING LABEL"):
            self.assertIn(t, p)
        self.assertTrue(all(b < 128 for b in p))

    def test_xref_offsets_point_at_objects(self):
        p = self.pdf
        start = int(re.search(rb"startxref\n(\d+)\n", p).group(1))
        self.assertTrue(p[start:].startswith(b"xref\n0 6\n"))
        offs = [int(m) for m in re.findall(rb"(\d{10}) 00000 n ", p)]
        self.assertEqual(len(offs), 5)
        for i, off in enumerate(offs, 1):
            self.assertTrue(p[off:].startswith(b"%d 0 obj\n" % i), i)
        length = int(re.search(rb"/Length (\d+) >>\nstream\n", p).group(1))
        body = p.split(b"stream\n", 1)[1]
        self.assertEqual(body[length:length + 9], b"endstream")

    def test_deterministic(self):
        self.assertEqual(self.pdf, subprocess.run(
            ["php", "-r", "define('ABSPATH','/x/'); function add_action(){} require %s; echo molosoc_tm366_pdf();"
             % json.dumps(str(PLUGIN))], capture_output=True, check=True).stdout)


if __name__ == "__main__":
    unittest.main()
