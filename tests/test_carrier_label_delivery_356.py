"""Issue #356 Phase 3: label PDF validation, delivery state machine, mock
provider/mailer, idempotency, retry and fail-closed behaviour. Real PHP."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "site/mu-plugins/molosoc-carrier-label-dispatch.php"
DELIV = ROOT / "site/mu-plugins/molosoc-carrier-label-delivery.php"
HAVE_PHP = shutil.which("php") is not None

SNAP = dict(status="processing", payment_method="cod", comgate_confirmed=False, carrier="PPL",
            created_ts=2000, since_ts=1000, done=False, sizes={"M": 1, "L": 2})


def php(code):
    pre = ("define('ABSPATH','/x/'); function wp_get_environment_type(){return 'production';} "
           "function add_action(){ $GLOBALS['hooked']=true; } "
           "require %s; require %s;" % (json.dumps(str(CORE)), json.dumps(str(DELIV))))
    return subprocess.run(["php", "-r", pre + code], capture_output=True, text=True, check=True).stdout


def j(code):
    return json.loads(php(code))


def run(snap=None, state="", ref="", tries=0, provider=None, mailer=None, lock=True, runs=1):
    """Runs the pipeline `runs` times against ONE persistent store; returns results + store + log."""
    code = """
$S = ['state'=>%s,'ref'=>%s,'tries'=>%d,'snap'=>json_decode(%s,true),'log'=>[],'mails'=>[],'prov'=>0,'lock'=>%s,'unlocked'=>0];
$io = [
 'snapshot'=>function() use (&$S){ return $S['snap']; },
 'state'=>function() use (&$S){ return $S['state']; }, 'set_state'=>function($s) use (&$S){ $S['state']=$s; },
 'ref'=>function() use (&$S){ return $S['ref']; }, 'set_ref'=>function($r) use (&$S){ $S['ref']=$r; },
 'tries'=>function() use (&$S){ return $S['tries']; }, 'set_tries'=>function($n) use (&$S){ $S['tries']=$n; },
 'lock'=>function() use (&$S){ return $S['lock']; }, 'unlock'=>function() use (&$S){ $S['unlocked']++; },
 'audit'=>function($r) use (&$S){ $S['log'][]=$r; },
 'provider'=>function($c,$ref) use (&$S){ $S['prov']++; %s },
 'mailer'=>function($m) use (&$S){ %s },
];
$res=[]; for($i=0;$i<%d;$i++){ $res[]=molosoc_ld3_process(7,$io); }
unset($S['snap']); echo json_encode(['res'=>$res,'S'=>$S]);
""" % (json.dumps(state), json.dumps(ref), tries, json.dumps(json.dumps(snap or SNAP)),
       "true" if lock else "false",
       provider or "return molosoc_ld3_mock_provider($c,7,$ref,true);",
       mailer or "[$r,$o]=molosoc_ld3_mock_mailer($m,$S['mails']); $S['mails']=$o; return $r;", runs)
    return j(code)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Pdf(unittest.TestCase):
    def v(self, expr):
        return j("echo json_encode(molosoc_ld3_validate_pdf(%s));" % expr)

    def test_mock_pdf_valid(self):
        self.assertEqual(self.v("molosoc_ld3_mock_pdf('PPL','MOCK-1')"), [True, "ok"])

    def test_invalid_variants(self):
        good = "molosoc_ld3_mock_pdf('PPL','MOCK-1')"
        self.assertEqual(self.v("''")[1], "pdf_empty")
        self.assertEqual(self.v("null")[1], "pdf_empty")
        self.assertEqual(self.v("'%PDF-1.4 x'")[1], "pdf_too_small")
        self.assertEqual(self.v("'X'.substr(%s,1)" % good)[1], "pdf_bad_header")
        self.assertEqual(self.v("str_replace('%%%%EOF','',%s)" % good)[1], "pdf_truncated")
        self.assertEqual(self.v("str_replace('/Type/Page/','/Type/Pagx/',%s)" % good)[1], "pdf_no_page")
        self.assertEqual(self.v("%s.str_repeat('a',6000000).'%%%%EOF'" % good)[1], "pdf_too_large")

    def test_html_error_page_is_not_a_label(self):
        self.assertEqual(self.v("'<html>Error 500</html>'.str_repeat(' ',300)")[1], "pdf_bad_header")


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Delivery(unittest.TestCase):
    def test_happy_path_ppl(self):
        r = run()
        self.assertEqual(r["res"], ["mocked_mailed"])
        S = r["S"]
        self.assertEqual(S["state"], "mailed")
        self.assertEqual(len(S["mails"]), 1)
        m = S["mails"][0]
        self.assertEqual(m["to"], "jarka01@atlas.cz")
        self.assertEqual(m["subject"], "PPL | 3 kusy | 1x M, 2x L")
        self.assertEqual(m["filename"], "ppl-7.pdf")
        self.assertEqual(S["unlocked"], 1)

    def test_packeta_and_cod_and_multiline_gift(self):
        s = dict(SNAP, carrier="Zásilkovna", sizes={"M": 3, "L": 3})  # gift lines folded into sizes
        r = run(snap=s)
        self.assertEqual(r["S"]["mails"][0]["subject"], "Zásilkovna | 6 kusů | 3x M, 3x L")

    def test_comgate_confirmed_ok_unconfirmed_blocked_and_bank_transfer_blocked(self):
        ok = run(snap=dict(SNAP, payment_method="wf-woo-comgate", comgate_confirmed=True))
        self.assertEqual(ok["res"], ["mocked_mailed"])
        for snap, why in ((dict(SNAP, payment_method="wf-woo-comgate", comgate_confirmed=False), "comgate_unverified"),
                          (dict(SNAP, payment_method="bacs"), "payment_method_excluded"),
                          (dict(SNAP, status="on-hold"), "status_not_processing"),
                          (dict(SNAP, since_ts=0), "before_cutoff_no_retroactive"),
                          (dict(SNAP, created_ts=500), "before_cutoff_no_retroactive")):
            r = run(snap=snap)
            self.assertEqual(r["res"], [why])
            self.assertEqual(r["S"]["prov"], 0)
            self.assertEqual(r["S"]["mails"], [])

    def test_duplicate_trigger_sends_once(self):
        r = run(runs=3)
        self.assertEqual(r["res"], ["mocked_mailed", "already_mailed", "already_mailed"])
        self.assertEqual(len(r["S"]["mails"]), 1)
        self.assertEqual(r["S"]["prov"], 1)

    def test_lock_held_does_nothing(self):
        r = run(lock=False)
        self.assertEqual(r["res"], ["locked"])
        self.assertEqual(r["S"]["prov"], 0)
        self.assertEqual(r["S"]["unlocked"], 0)  # never unlock a lock we did not take

    def test_provider_failure_then_retry_succeeds(self):
        prov = "return $S['prov']<2 ? ['ok'=>false,'live'=>false,'reason'=>'boom'] : molosoc_ld3_mock_provider($c,7,$ref,true);"
        r = run(provider=prov, runs=2)
        self.assertEqual(r["res"], ["provider_failed", "mocked_mailed"])
        self.assertEqual(len(r["S"]["mails"]), 1)

    def test_packeta_not_submitted_fails_closed_without_mail(self):
        s = dict(SNAP, carrier="Zásilkovna")
        r = run(snap=s, provider="return molosoc_ld3_mock_provider($c,7,$ref,false);")
        self.assertEqual(r["res"], ["provider_failed"])
        self.assertEqual(r["S"]["mails"], [])
        self.assertEqual(r["S"]["tries"], 1)

    def test_invalid_pdf_is_never_mailed(self):
        r = run(provider="return ['ok'=>true,'live'=>false,'ref'=>'R1','pdf'=>'<html>err</html>'.str_repeat(' ',300)];")
        self.assertEqual(r["res"], ["pdf_bad_header"])
        self.assertEqual(r["S"]["mails"], [])
        self.assertEqual(r["S"]["state"], "")

    def test_missing_ref_blocks(self):
        r = run(provider="return ['ok'=>true,'live'=>false,'pdf'=>molosoc_ld3_mock_pdf($c,'x')];")
        self.assertEqual(r["res"], ["ref_missing"])
        self.assertEqual(r["S"]["mails"], [])

    def test_mailer_failure_resumes_from_label_ready_with_same_ref(self):
        mail = "if(count($S['log'])<3||$S['tries']<1){return ['ok'=>false,'live'=>false,'reason'=>'smtp'];} [$r,$o]=molosoc_ld3_mock_mailer($m,$S['mails']); $S['mails']=$o; return $r;"
        r = run(mailer=mail, runs=2)
        self.assertEqual(r["res"], ["mailer_failed", "mocked_mailed"])
        S = r["S"]
        self.assertEqual(len(S["mails"]), 1)
        self.assertEqual(S["prov"], 2)           # provider asked again ...
        self.assertTrue(S["ref"].startswith("MOCK-"))  # ... but with the stored ref (mock keeps it identical)

    def test_provider_receives_stored_ref_on_retry(self):
        r = run(ref="MOCK-ABC", provider="$S['seen']=$ref; return molosoc_ld3_mock_provider($c,7,$ref,true);")
        self.assertEqual(r["S"]["seen"], "MOCK-ABC")
        self.assertEqual(r["S"]["ref"], "MOCK-ABC")

    def test_changed_ref_means_possible_duplicate_shipment_stop(self):
        r = run(ref="MOCK-OLD", provider="return ['ok'=>true,'live'=>false,'ref'=>'NEW-1','pdf'=>molosoc_ld3_mock_pdf($c,'NEW-1')];")
        self.assertEqual(r["res"], ["ref_changed"])
        self.assertEqual(r["S"]["state"], "attention")
        self.assertEqual(r["S"]["mails"], [])

    def test_crash_after_mailing_never_resends(self):
        r = run(state="mailing", runs=2)
        self.assertEqual(r["res"], ["mail_state_unknown", "needs_attention"])
        self.assertEqual(r["S"]["mails"], [])
        self.assertEqual(r["S"]["prov"], 0)

    def test_exception_in_mailer_leaves_mailing_then_attention(self):
        r = run(mailer="throw new RuntimeException('x');", runs=2)
        self.assertEqual(r["res"], ["exception", "mail_state_unknown"])
        self.assertEqual(r["S"]["state"], "attention")
        self.assertEqual(r["S"]["unlocked"], 2)

    def test_max_tries_goes_to_attention(self):
        r = run(provider="return ['ok'=>false,'live'=>false,'reason'=>'x'];", runs=5)
        self.assertEqual(r["res"], ["provider_failed"] * 3 + ["max_tries", "needs_attention"])
        self.assertEqual(r["S"]["prov"], 3)

    def test_live_provider_and_live_mailer_refused(self):
        r = run(provider="return ['ok'=>true,'live'=>true,'ref'=>'R','pdf'=>molosoc_ld3_mock_pdf($c,'R')];")
        self.assertEqual(r["res"], ["live_provider_refused"])
        self.assertEqual(r["S"]["mails"], [])
        r = run(mailer="return ['ok'=>true,'live'=>true];")
        self.assertEqual(r["res"], ["live_mailer_refused"])
        self.assertEqual(r["S"]["state"], "attention")

    def test_eligibility_flip_after_lock_is_rechecked(self):
        code = """
$n=0; $S=['state'=>'','log'=>[]]; $snap=json_decode(%s,true);
$io=['snapshot'=>function() use (&$n,$snap){ $n++; return $n>=2 ? array_merge($snap,['status'=>'cancelled']) : $snap; },
 'state'=>function() use (&$S){return $S['state'];}, 'set_state'=>function($s){}, 'ref'=>function(){return '';}, 'set_ref'=>function($r){},
 'tries'=>function(){return 0;}, 'set_tries'=>function($n){}, 'lock'=>function(){return true;}, 'unlock'=>function(){},
 'audit'=>function($r) use (&$S){ $S['log'][]=$r; },
 'provider'=>function($c,$r){ throw new Exception('must not run'); }, 'mailer'=>function($m){ throw new Exception('must not run'); }];
echo json_encode(molosoc_ld3_process(7,$io));""" % json.dumps(json.dumps(SNAP))
        self.assertEqual(j(code), "recheck_status_not_processing")

    def test_mock_mailer_rejects_bad_messages(self):
        base = "['to'=>'jarka01@atlas.cz','subject'=>'PPL | 1 kus | 1x M','filename'=>'ppl-7.pdf','pdf'=>molosoc_ld3_mock_pdf('PPL','R')]"
        for mut, why in (("['to'=>'x@y.cz']", "recipient_mismatch"), ("['subject'=>'hello']", "subject_mismatch"),
                         ("['filename'=>'../a.pdf']", "filename_mismatch"), ("['pdf'=>'nope']", "pdf_too_small")):
            out = j("[$r,$o]=molosoc_ld3_mock_mailer(array_merge(%s,%s),[]); echo json_encode([$r,$o]);" % (base, mut))
            self.assertEqual(out[0]["reason"], why)
            self.assertEqual(out[1], [])
        out = j("[$r,$o]=molosoc_ld3_mock_mailer(%s,[]); echo json_encode([$r,$o]);" % base)
        self.assertTrue(out[0]["ok"])
        self.assertNotIn("pdf", out[1][0])  # outbox never keeps the PDF

    def test_audit_has_no_pdf_or_personal_data(self):
        r = run()
        blob = json.dumps(r["S"]["log"])
        self.assertNotIn("%PDF", blob)
        for row in r["S"]["log"]:
            self.assertFalse(set(row) & {"pdf", "email", "address", "name", "phone"})


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Gate(unittest.TestCase):
    def g(self, env, const):
        return j("echo json_encode(molosoc_ld3_enabled(%s,%s));" % (json.dumps(env), const))

    def test_disabled_by_default_and_in_production(self):
        self.assertFalse(self.g("production", "true"))
        self.assertFalse(self.g("development", "true"))
        self.assertFalse(self.g("staging", "null"))
        self.assertFalse(self.g("staging", "'true'"))
        self.assertFalse(self.g("staging", "1"))
        self.assertTrue(self.g("staging", "true"))
        self.assertTrue(self.g("local", "true"))

    def test_loading_in_production_registers_nothing(self):
        self.assertEqual(php("echo isset($GLOBALS['hooked']) ? 'hooked' : 'inert';"), "inert")

    def test_alphabetical_load_order_registers_after_muplugins_loaded(self):
        # delivery loads BEFORE dispatch (alphabetical); registration must still happen.
        code = ("define('ABSPATH','/x/'); define('MOLOSOC_LABEL_DELIVERY_ENABLED', true); "
                "function wp_get_environment_type(){return 'staging';} "
                "$GLOBALS['h']=[]; function add_action($n,$cb){ $GLOBALS['h'][]=[$n,$cb]; } "
                "require %s; require %s; "
                "$early=count(array_filter($GLOBALS['h'],fn($x)=>$x[0]==='woocommerce_order_status_processing')); "
                "foreach($GLOBALS['h'] as $x){ if($x[0]==='muplugins_loaded'){ ($x[1])(); } } "
                "$late=count(array_filter($GLOBALS['h'],fn($x)=>$x[0]==='woocommerce_order_status_processing')); "
                "echo json_encode([$early,$late]);" % (json.dumps(str(DELIV)), json.dumps(str(CORE))))
        out = subprocess.run(["php", "-r", code], capture_output=True, text=True, check=True).stdout
        self.assertEqual(json.loads(out), [0, 1])


class Static(unittest.TestCase):
    def code(self):
        src = DELIV.read_text(encoding="utf-8")
        src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        return re.sub(r"(?m)^\s*//.*$", "", src)

    def test_no_live_calls(self):
        code = self.code()
        for banned in ("wp_mail(", "mail(", "wp_remote_", "curl_", "file_get_contents(", "fopen(", "createPackages",
                       "getLabelContents", "packetsLabelsPdf", "packetsCarrierLabelsPdf", "submitPacket",
                       "set_status(", "update_status(", "payment_complete", "'production'", "DELIVERY_LIVE"):
            self.assertNotIn(banned, code)

    def test_gate_and_cutoff_present(self):
        src = DELIV.read_text(encoding="utf-8")
        self.assertIn("MOLOSOC_LABEL_DELIVERY_ENABLED", src)
        self.assertIn("molosoc_ld3_enabled( wp_get_environment_type()", src)
        self.assertIn("molosoc_ld_decide( $snap )", src)  # cut-off + payment rules reused

    def test_mailing_state_written_before_mailer_call(self):
        code = self.code()
        self.assertLess(code.index("set_state']( 'mailing' )"), code.index("$io['mailer']( $mail )"))


if __name__ == "__main__":
    unittest.main()
