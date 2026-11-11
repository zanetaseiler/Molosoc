"""Issue #369: read-only label preview for the one allowlisted order, and the live send
pinned to the approved Packeta packet id. Real PHP, no network, no mail, no writes."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MU = ROOT / "site/mu-plugins"
FILES = [MU / f for f in (
    "molosoc-carrier-label-dispatch.php", "molosoc-carrier-label-delivery.php",
    "molosoc-carrier-label-live.php", "molosoc-carrier-label-preview.php")]
PREVIEW = FILES[3]
LIVE = FILES[2]
HAVE_PHP = shutil.which("php") is not None
PDF = "molosoc_ld3_mock_pdf('Zásilkovna','Z1234567')"
SNAP = dict(status="processing", payment_method="cod", comgate_confirmed=False, carrier="Zásilkovna",
            created_ts=2000, since_ts=1000, done=False, sizes={"M": 1, "L": 2})


def q(x):
    raw = json.dumps(x, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'")
    return "json_decode('%s',true)" % raw


def php(code, pre_extra=""):
    pre = ("define('ABSPATH','/x/'); function add_action(){$GLOBALS['hooks'][]=func_get_arg(0);} " + pre_extra +
           " ".join("require %s;" % json.dumps(str(f)) for f in FILES))
    return json.loads(subprocess.run(["php", "-r", pre + code], capture_output=True, text=True, check=True).stdout)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class LiveApprovedPacket(unittest.TestCase):
    def g(self, approved):
        return php("echo json_encode(molosoc_ll_gate(true,[7],false,7,%s));" % approved)

    def test_gate_requires_well_formed_approved_packet(self):
        self.assertEqual(self.g("'Z1234567'"), [True, "allowed"])
        self.assertEqual(self.g("'1234567'"), [True, "allowed"])
        for bad in ("null", "''", "'abc'", "1234567", "'Z12'", "'Z1234567 '", "['Z1234567']"):
            self.assertEqual(self.g(bad), [False, "approved_packet_missing"], bad)

    def test_entry_point_refuses_without_approved_packet(self):
        out = php("function wp_mail(){$GLOBALS['m']=1;return true;} function wc_get_order(){throw new Exception('lookup');}"
                  " echo json_encode([molosoc_ll_run(7), $GLOBALS['m']??0]);",
                  "define('MOLOSOC_LABEL_LIVE_ENABLED',true); define('MOLOSOC_LABEL_LIVE_ORDER_IDS',[7]);")
        self.assertEqual(out, ["approved_packet_missing", 0])

    def r(self, res, approved):
        return php("echo json_encode(molosoc_ll_require_approved(%s,%s));" % (res, q(approved)))

    def test_matching_packet_passes_through(self):
        out = self.r("['ok'=>true,'live'=>true,'ref'=>'Z1234567','pdf'=>'x']", "Z1234567")
        self.assertEqual(out, {"ok": True, "live": True, "ref": "Z1234567", "pdf": "x"})

    def test_other_packet_is_permanent_attention(self):
        for ref in ("Z7654321", "1234567", ""):
            out = self.r("['ok'=>true,'live'=>true,'ref'=>%s,'pdf'=>'x']" % q(ref), "Z1234567")
            self.assertEqual(out, {"ok": False, "live": True, "permanent": True, "reason": "packet_not_approved"})

    def test_failures_pass_through(self):
        out = self.r("['ok'=>false,'live'=>true,'reason'=>'packet_not_submitted']", "Z1234567")
        self.assertEqual(out["reason"], "packet_not_submitted")

    def test_unapproved_packet_never_mailed_through_state_machine(self):
        code = """$S=['state'=>'','log'=>[],'sent'=>0];
$io=['allow_live'=>true,'snapshot'=>function(){return %s;},
 'state'=>function() use (&$S){return $S['state'];},'set_state'=>function($s) use (&$S){$S['state']=$s;},
 'ref'=>function(){return '';},'set_ref'=>function(){},'tries'=>function(){return 0;},'set_tries'=>function(){},
 'lock'=>function(){return true;},'unlock'=>function(){},'audit'=>function($r) use (&$S){$S['log'][]=$r;},
 'provider'=>function($c,$r){ return molosoc_ll_require_approved(['ok'=>true,'live'=>true,'ref'=>'Z7654321','pdf'=>%s],'Z1234567'); },
 'mailer'=>function() use (&$S){ $S['sent']++; return ['ok'=>true,'live'=>true]; }];
echo json_encode([molosoc_ld3_process(7,$io),$S]);""" % (q(SNAP), PDF)
        res, S = php(code)
        self.assertEqual(res, "provider_permanent")
        self.assertEqual(S["state"], "attention")
        self.assertEqual(S["sent"], 0)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class PreviewGate(unittest.TestCase):
    def g(self, preview="true", live="null", ids="[7]", mock="false"):
        return php("echo json_encode(molosoc_lp_gate(%s,%s,%s,%s));" % (preview, live, ids, mock))

    def test_allowed(self):
        self.assertEqual(self.g(), [True, "allowed", 7])
        self.assertEqual(self.g(live="false"), [True, "allowed", 7])

    def test_off_by_default_and_truthy_not_enough(self):
        for p in ("null", "false", "1", "'true'"):
            self.assertEqual(self.g(preview=p), [False, "preview_disabled", 0])

    def test_refused_while_live_or_mock_enabled(self):
        self.assertEqual(self.g(live="true"), [False, "live_enabled_preview_refused", 0])
        self.assertEqual(self.g(mock="true"), [False, "mock_delivery_also_enabled", 0])

    def test_exactly_one_order(self):
        for ids in ("null", "[]", "[7,8]", "'7'"):
            self.assertEqual(self.g(ids=ids)[1], "allowlist_must_be_exactly_one_order")
        for ids in ("['7']", "[0]", "[-1]"):
            self.assertEqual(self.g(ids=ids)[1], "allowlist_invalid_id")


@unittest.skipUnless(HAVE_PHP, "php not installed")
class PreviewReport(unittest.TestCase):
    def rep(self, snap=None, state="", packet="Z1234567", configured="true"):
        return php("echo json_encode(molosoc_lp_report(7,%s,%s,%s,%s));" % (q(snap or SNAP), q(state), q(packet), configured))

    def test_ready_report(self):
        r = self.rep()
        self.assertTrue(r["ready"])
        self.assertEqual(r["blockers"], [])
        self.assertEqual(r["subject"], "Zásilkovna | 3 kusy | 1x M, 2x L")
        self.assertEqual(r["filename"], "zasilkovna-7.pdf")
        self.assertEqual((r["to"], r["cc"]), ("jarka01@atlas.cz", "hello@molosoc.com"))
        self.assertEqual(r["packet_id"], "Z1234567")

    def test_blockers(self):
        self.assertIn("before_cutoff_no_retroactive", self.rep(dict(SNAP, since_ts=3000))["blockers"])
        self.assertIn("payment_method_excluded", self.rep(dict(SNAP, payment_method="bacs"))["blockers"])
        self.assertIn("comgate_unverified", self.rep(dict(SNAP, payment_method="wf-woo-comgate"))["blockers"])
        self.assertIn("ppl_manual_label_required", self.rep(dict(SNAP, carrier="PPL"))["blockers"])
        for st in ("mailed", "attention", "mailing"):
            self.assertIn("delivery_state_" + st, self.rep(state=st)["blockers"])
        self.assertIn("packeta_unconfigured", self.rep(configured="false")["blockers"])
        self.assertIn("packet_not_submitted", self.rep(packet="")["blockers"])
        r = self.rep(packet="evil<script>")
        self.assertIn("packet_id_malformed", r["blockers"])
        self.assertEqual(r["packet_id"], "")
        self.assertFalse(r["ready"])

    def test_label_check(self):
        ok = php("echo json_encode(molosoc_lp_label(['ok'=>true,'pdf'=>%s]));" % PDF)
        self.assertTrue(ok["ok"])
        self.assertEqual(len(ok["sha256"]), 64)
        bad = php("echo json_encode(molosoc_lp_label(['ok'=>true,'pdf'=>'nope']));")
        self.assertFalse(bad["ok"])
        fail = php("echo json_encode(molosoc_lp_label(['ok'=>false,'reason'=>'packeta_fetch_failed']));")
        self.assertEqual(fail, {"ok": False, "reason": "packeta_fetch_failed"})


class PreviewSourceContract(unittest.TestCase):
    def test_read_only_source(self):
        src = PREVIEW.read_text()
        for forbidden in ("wp_mail", "update_meta_data", "add_meta_data", "save_meta_data", "update_option",
                          "add_option", "delete_option", "set_status", "update_status", "wp_schedule",
                          "molosoc_ld3_process", "molosoc_ll_run", "molosoc_ld3_meta_set", "file_put_contents"):
            self.assertNotIn(forbidden, src, forbidden)
        self.assertIn("true === MOLOSOC_LABEL_LIVE_PREVIEW", src)
        self.assertIn("check_admin_referer( MOLOSOC_LP_ACTION )", src)
        self.assertIn("current_user_can( MOLOSOC_LP_CAP )", src)

    @unittest.skipUnless(HAVE_PHP, "php not installed")
    def test_no_hooks_without_opt_in(self):
        self.assertEqual(php("echo json_encode($GLOBALS['hooks']??[]);"), [])

    def test_live_send_requires_approved_packet_constant(self):
        self.assertIn("MOLOSOC_LABEL_LIVE_APPROVED_PACKET", LIVE.read_text())


if __name__ == "__main__":
    unittest.main()
