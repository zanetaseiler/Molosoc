"""Issue #358: live adapter gate, wp_mail mailer, Packeta fetch-only provider,
retry/idempotency through the shared state machine. Real PHP, no network, no mail."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / "site/mu-plugins" / f for f in (
    "molosoc-carrier-label-dispatch.php", "molosoc-carrier-label-delivery.php", "molosoc-carrier-label-live.php")]
LIVE = FILES[2]
HAVE_PHP = shutil.which("php") is not None
PDF = "molosoc_ld3_mock_pdf('Zásilkovna','Z1234567')"
SNAP = dict(status="processing", payment_method="cod", comgate_confirmed=False, carrier="Zásilkovna",
            created_ts=2000, since_ts=1000, done=False, sizes={"M": 1, "L": 2})


def q(x):
    """PHP expression for any JSON-able value (single-quoted, non-ASCII kept)."""
    raw = json.dumps(x, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'")
    return "json_decode('%s',true)" % raw


def php(code):
    pre = ("define('ABSPATH','/x/'); function add_action(){} " +
           " ".join("require %s;" % json.dumps(str(f)) for f in FILES))
    return json.loads(subprocess.run(["php", "-r", pre + code], capture_output=True, text=True, check=True).stdout)


def pipeline(provider, mailer, snap=None, state="", ref="", tries=0, runs=1):
    code = """
$S=['state'=>%s,'ref'=>%s,'tries'=>%d,'log'=>[],'sent'=>0,'prov'=>0];
$snap=%s;
$io=['allow_live'=>true,'snapshot'=>function() use ($snap){return $snap;},
 'state'=>function() use (&$S){return $S['state'];},'set_state'=>function($s) use (&$S){$S['state']=$s;},
 'ref'=>function() use (&$S){return $S['ref'];},'set_ref'=>function($r) use (&$S){$S['ref']=$r;},
 'tries'=>function() use (&$S){return $S['tries'];},'set_tries'=>function($n) use (&$S){$S['tries']=$n;},
 'lock'=>function(){return true;},'unlock'=>function(){},'audit'=>function($r) use (&$S){$S['log'][]=$r;},
 'provider'=>function($c,$ref) use (&$S){ $S['prov']++; %s },
 'mailer'=>function($m) use (&$S){ %s }];
$res=[]; for($i=0;$i<%d;$i++){ $res[]=molosoc_ld3_process(7,$io); }
echo json_encode(['res'=>$res,'S'=>$S]);
""" % (q(state), q(ref), tries, q(snap or SNAP), provider, mailer, runs)
    return php(code)


GOOD_PROV = ("return molosoc_ll_provider($c,$ref,['packet_meta_key'=>'k','packet_id'=>'Z1234567','api_password'=>'pw',"
             "'fetch'=>function(){return " + PDF + ";}]);")
GOOD_MAIL = ("$r=molosoc_ll_mail($m,function(){$GLOBALS['n']=($GLOBALS['n']??0)+1;return true;},"
             "function($n,$b){return '/tmp/x';},function(){}); if($r['ok']){$S['sent']++;} return $r;")


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Gate(unittest.TestCase):
    def g(self, enabled="true", ids="[7]", mock="false", oid=7):
        return php("echo json_encode(molosoc_ll_gate(%s,%s,%s,%d));" % (enabled, ids, mock, oid))

    def test_allowed(self):
        self.assertEqual(self.g(), [True, "allowed"])

    def test_off_by_default_and_truthy_not_enough(self):
        for e in ("null", "false", "'1'", "1"):
            self.assertEqual(self.g(enabled=e), [False, "live_disabled"])

    def test_exactly_one_order(self):
        for ids in ("null", "[]", "[7,8]", "'7'"):
            self.assertEqual(self.g(ids=ids)[1], "allowlist_must_be_exactly_one_order")
        for ids in ("['7']", "[0]", "[-1]"):
            self.assertEqual(self.g(ids=ids)[1], "allowlist_invalid_id")

    def test_other_order_and_mock_conflict(self):
        self.assertEqual(self.g(oid=8), [False, "order_not_allowlisted"])
        self.assertEqual(self.g(mock="true"), [False, "mock_delivery_also_enabled"])

    def test_entry_point_inert_without_constants(self):
        self.assertEqual(php("echo json_encode(molosoc_ll_run(7));"), "live_disabled")

    def test_hook_not_registered_without_opt_in(self):
        src = LIVE.read_text()
        self.assertIn("true === MOLOSOC_LABEL_LIVE_ENABLED", src)
        self.assertNotIn("wp_remote", src)
        self.assertNotIn("update_status", src)
        self.assertNotIn("set_status", src)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Mailer(unittest.TestCase):
    def m(self, to="jarka01@atlas.cz", subj="Zásilkovna | 3 kusy | 1x M, 2x L", fn="zasilkovna-7.pdf", pdf=PDF, send="return true;"):
        return php("""$log=['rm'=>0,'att'=>null];
$r=molosoc_ll_mail(['to'=>%s,'subject'=>%s,'filename'=>%s,'pdf'=>%s],
 function($to,$s,$b,$h,$a) use (&$log){ $log['att']=$a; %s },
 function(){return '/tmp/lbl.pdf';}, function() use (&$log){$log['rm']++;});
echo json_encode([$r,$log]);""" % (q(to), q(subj), q(fn), pdf, send))

    def test_success_removes_temp_file(self):
        r, log = self.m()
        self.assertEqual(r, {"ok": True, "live": True})
        self.assertEqual(log, {"rm": 1, "att": ["/tmp/lbl.pdf"]})

    def test_wp_mail_false_is_definite_failure_and_cleans_up(self):
        r, log = self.m(send="return false;")
        self.assertEqual((r["ok"], r["reason"], log["rm"]), (False, "wp_mail_false", 1))

    def test_wp_mail_throw_cleans_up(self):
        res = php("""$rm=0; try{ molosoc_ll_mail(['to'=>'jarka01@atlas.cz','subject'=>'PPL | 1 kus | 1x M','filename'=>'ppl-1.pdf','pdf'=>molosoc_ld3_mock_pdf('PPL','R')],
 function(){throw new Exception('x');}, function(){return '/tmp/a';}, function() use (&$rm){$rm++;}); }catch(Throwable $e){}
echo json_encode($rm);""")
        self.assertEqual(res, 1)

    def test_rejects_bad_message_without_sending(self):
        for kw, why in ((dict(to="x@example.com"), "recipient_mismatch"), (dict(subj="Hello"), "subject_mismatch"),
                        (dict(fn="../x.pdf"), "filename_mismatch"), (dict(pdf="'<html>err</html>'"), "pdf_too_small")):
            r, log = self.m(send="$GLOBALS['sent']=1; return true;", **kw)
            self.assertEqual(r["reason"], why)
            self.assertIsNone(log["att"])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Provider(unittest.TestCase):
    def p(self, carrier="Zásilkovna", ref="", **d):
        base = dict(packet_meta_key="k", packet_id="Z1234567", api_password="pw")
        base.update(d)
        code = "$d=%s; $d['fetch']=function() use (&$f){ $GLOBALS['fetches']=($GLOBALS['fetches']??0)+1; return %s; }; $r=molosoc_ll_provider(%s,%s,$d); unset($r['pdf']); echo json_encode([$r,$GLOBALS['fetches']??0]);" % (
            q(base), PDF, q(carrier), q(ref))
        return php(code)

    def test_ok_fetches_only(self):
        r, n = self.p()
        self.assertEqual((r["ok"], r["ref"], n), (True, "Z1234567", 1))

    def test_ppl_is_manual_permanent(self):
        r, n = self.p(carrier="PPL")
        self.assertEqual((r["ok"], r["permanent"], r["reason"], n), (False, True, "ppl_manual_label_required", 0))

    def test_unconfigured_is_permanent_no_fetch(self):
        for k in ("packet_meta_key", "api_password"):
            r, n = self.p(**{k: ""})
            self.assertEqual((r["reason"], n), ("packeta_unconfigured", 0))

    def test_not_submitted_is_retryable_and_never_creates(self):
        r, n = self.p(packet_id="")
        self.assertEqual((r["reason"], r.get("permanent"), n), ("packet_not_submitted", None, 0))
        self.assertNotIn("createPacket", LIVE.read_text())

    def test_malformed_packet_id(self):
        r, n = self.p(packet_id="abc; DROP")
        self.assertEqual((r["reason"], n), ("packet_id_malformed", 0))


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Pipeline(unittest.TestCase):
    def test_happy_path_mails_once_and_audits_live(self):
        o = pipeline(GOOD_PROV, GOOD_MAIL, runs=3)
        self.assertEqual(o["res"], ["mailed", "already_mailed", "already_mailed"])
        self.assertEqual((o["S"]["sent"], o["S"]["state"], o["S"]["ref"], o["S"]["prov"]), (1, "mailed", "Z1234567", 1))
        self.assertTrue(any(r.get("result") == "mailed" and r.get("live") is True for r in o["S"]["log"]))
        self.assertNotIn("pdf", json.dumps(o["S"]["log"]))

    def test_without_allow_live_flag_live_is_still_refused(self):
        code = "$S=0; $io=['snapshot'=>function(){return %s;},'state'=>function(){return '';},'set_state'=>function(){},'ref'=>function(){return '';},'set_ref'=>function(){},'tries'=>function(){return 0;},'set_tries'=>function(){},'lock'=>function(){return true;},'unlock'=>function(){},'audit'=>function(){},'provider'=>function($c,$r){ return ['ok'=>true,'live'=>true,'ref'=>'Z1','pdf'=>%s]; },'mailer'=>function() use (&$S){ $S++; return ['ok'=>true,'live'=>false]; }]; echo json_encode([molosoc_ld3_process(7,$io),$S]);" % (q(SNAP), PDF)
        self.assertEqual(php(code), ["live_provider_refused", 0])

    def test_packet_not_submitted_retries_without_mail_then_succeeds(self):
        prov = "$id = $S['prov']>=2 ? 'Z1234567' : ''; return molosoc_ll_provider($c,$ref,['packet_meta_key'=>'k','packet_id'=>$id,'api_password'=>'pw','fetch'=>function(){return %s;}]);" % PDF
        o = pipeline(prov, GOOD_MAIL, runs=3)
        self.assertEqual(o["res"], ["provider_failed", "mailed", "already_mailed"])
        self.assertEqual(o["S"]["sent"], 1)

    def test_mailer_failure_retries_then_attention_never_double_sends(self):
        mail = "$S['sent']++; return ['ok'=>false,'live'=>true,'reason'=>'wp_mail_false'];"
        o = pipeline(GOOD_PROV, mail, runs=5)
        self.assertEqual(o["res"][:3], ["mailer_failed"] * 3)
        self.assertEqual((o["res"][3], o["S"]["state"], o["S"]["sent"]), ("max_tries", "attention", 3))

    def test_crash_after_mailing_goes_to_attention_no_resend(self):
        o = pipeline(GOOD_PROV, GOOD_MAIL, state="mailing", ref="Z1234567")
        self.assertEqual((o["res"], o["S"]["sent"], o["S"]["state"]), (["mail_state_unknown"], 0, "attention"))

    def test_packet_id_change_is_attention_not_mail(self):
        o = pipeline(GOOD_PROV, GOOD_MAIL, ref="Z9999999")
        self.assertEqual((o["res"], o["S"]["sent"], o["S"]["state"]), (["ref_changed"], 0, "attention"))

    def test_ppl_permanent_attention_no_mail(self):
        snap = dict(SNAP, carrier="PPL")
        o = pipeline(GOOD_PROV, GOOD_MAIL, snap=snap)
        self.assertEqual((o["res"], o["S"]["sent"], o["S"]["state"]), (["provider_permanent"], 0, "attention"))

    def test_ineligible_orders_never_reach_carrier_or_mail(self):
        cases = {
            "bank_transfer": dict(payment_method="bacs"),
            "on_hold": dict(status="on-hold"),
            "unconfirmed_comgate": dict(payment_method="wf-woo-comgate", comgate_confirmed=False),
            "before_cutoff": dict(created_ts=10),
        }
        for name, ch in cases.items():
            o = pipeline(GOOD_PROV, GOOD_MAIL, snap=dict(SNAP, **ch))
            self.assertEqual((o["S"]["prov"], o["S"]["sent"]), (0, 0), name)

    def test_confirmed_comgate_card_is_mailed(self):
        o = pipeline(GOOD_PROV, GOOD_MAIL, snap=dict(SNAP, payment_method="wf-woo-comgate", comgate_confirmed=True))
        self.assertEqual(o["res"], ["mailed"])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Retry(unittest.TestCase):
    def test_retry_decision(self):
        r = php("echo json_encode([molosoc_ll_should_retry('provider_failed',1),molosoc_ll_should_retry('provider_failed',3),"
                "molosoc_ll_should_retry('mail_state_unknown',0),molosoc_ll_should_retry('mailed',0),molosoc_ll_should_retry('ref_changed',0)]);")
        self.assertEqual(r, [True, False, False, False, False])

    def test_exhausted_decision(self):
        r = php("echo json_encode([molosoc_ll_exhausted('provider_failed',3),molosoc_ll_exhausted('mailer_failed',3),"
                "molosoc_ll_exhausted('provider_failed',2),molosoc_ll_exhausted('mailed',3),molosoc_ll_exhausted('ref_changed',3)]);")
        self.assertEqual(r, [True, True, False, False, False])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Comgate(unittest.TestCase):
    F = dict(status="processing", payment_method="wf-woo-comgate", transaction_id="AB12", tmp_transaction_id="AB12", is_paid=True)

    def paid(self, **ch):
        return php("echo json_encode(molosoc_ld_comgate_paid(%s));" % q(dict(self.F, **ch)))

    def test_strict_default_rejects_equal_ids(self):
        self.assertFalse(self.paid())

    def test_paid_status_rule_accepts_legit_paid_order(self):
        self.assertTrue(self.paid(tmp_rule="paid_status"))

    def test_paid_status_rule_still_fail_closed(self):
        for ch in (dict(status="on-hold"), dict(transaction_id=""), dict(is_paid=False), dict(payment_method="bacs")):
            self.assertFalse(self.paid(tmp_rule="paid_status", **ch))


if __name__ == "__main__":
    unittest.main()
