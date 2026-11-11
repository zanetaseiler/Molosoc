"""Issue #369 (ZANETA_DECISION 2026-11-11, change of scope): hands-off carrier labels for
ALL eligible new orders, OFF by default.

Real PHP, injected fakes only: no network, no mail, no DB writes, no packet creation.
"""
import base64
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MU = ROOT / "site/mu-plugins"
AUTO = MU / "molosoc-carrier-label-auto.php"
FILES = [MU / f for f in (
    "molosoc-carrier-label-auto.php", "molosoc-carrier-label-delivery.php",
    "molosoc-carrier-label-dispatch.php", "molosoc-carrier-label-live.php")]
HAVE_PHP = shutil.which("php") is not None
FLOOR = 1794355200  # 2026-11-11T00:00:00Z

PDF = ("%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
       "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 283 425]>>endobj\n% " + "x" * 150 + "\ntrailer<</Root 1 0 R>>\n%%EOF\n")


def q(x):
    raw = json.dumps(x, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'")
    return "json_decode('%s',true)" % raw


def php(code, pre_extra=""):
    pre = ("define('ABSPATH','/x/'); function add_action(){$GLOBALS['hooks'][]=func_get_arg(0);} " + pre_extra +
           " ".join("require %s;" % json.dumps(str(f)) for f in FILES))
    out = subprocess.run(["php", "-r", pre + code], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def snap(**kw):
    s = dict(status="processing", payment_method="cod", comgate_confirmed=False, carrier="Zásilkovna",
             created_ts=FLOOR + 100, since_ts=FLOOR, done=False, sizes={"M": 1})
    s.update(kw)
    return s


ROW_OK = {"packet_id": "4123456789", "carrier_id": "zpointcz", "packet_status": None}


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Gate(unittest.TestCase):
    def gate(self, enabled="true", live="false", mock="false", since_def="true", since="'2026-11-12T00:00:00+01:00'"):
        return php("echo json_encode(molosoc_la_gate(%s,%s,%s,%s,%s));" % (enabled, live, mock, since_def, since))

    def test_allowed(self):
        self.assertEqual(self.gate(), [True, "allowed"])
        self.assertEqual(self.gate(since=str(FLOOR)), [True, "allowed"])

    def test_off_by_default_and_strict(self):
        for v in ("null", "false", "1", "'true'", "'1'"):
            self.assertEqual(self.gate(enabled=v), [False, "auto_disabled"], v)

    def test_exclusive_with_single_order_live_and_mock(self):
        self.assertEqual(self.gate(live="true"), [False, "single_order_live_also_enabled"])
        self.assertEqual(self.gate(mock="true"), [False, "mock_delivery_also_enabled"])

    def test_cutoff_constant_required_and_valid(self):
        self.assertEqual(self.gate(since_def="false", since="null"), [False, "cutoff_constant_required"])
        for bad in ("null", "0", "'yesterday'", str(FLOOR - 1), "'2026-11-10T00:00:00Z'"):
            self.assertEqual(self.gate(since=bad), [False, "cutoff_invalid"], bad)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class PacketaCheckAndPlan(unittest.TestCase):
    def check(self, row):
        return php("echo json_encode(molosoc_la_packeta_check(%s));" % ("null" if row is None else q(row)))

    def test_packeta_check(self):
        self.assertEqual(self.check(ROW_OK), "")
        self.assertEqual(self.check(dict(ROW_OK, packet_status="received data")), "")
        self.assertEqual(self.check(dict(ROW_OK, packet_id="Z4123456789")), "")
        self.assertEqual(self.check(None), "wait")
        self.assertEqual(self.check(dict(ROW_OK, packet_id=None)), "wait")
        self.assertEqual(self.check(dict(ROW_OK, packet_id="  ")), "wait")
        self.assertEqual(self.check(dict(ROW_OK, carrier_id="")), "packeta_carrier_unknown")
        self.assertEqual(self.check(dict(ROW_OK, carrier_id="13")), "packeta_external_carrier_manual")
        self.assertEqual(self.check(dict(ROW_OK, packet_id="x; DROP")), "packet_id_malformed")
        self.assertEqual(self.check(dict(ROW_OK, packet_status="cancelled")), "packet_cancelled")
        for st in ("delivered", "posted", "returned", "unknown"):
            self.assertEqual(self.check(dict(ROW_OK, packet_status=st)), "packet_already_moving", st)

    def plan(self, s, state="", row=ROW_OK, configured=True):
        return php("echo json_encode(molosoc_la_plan(%s,%s,%s,%s));" % (
            q(s), json.dumps(state), "null" if row is None else q(row), "true" if configured else "false"))

    def test_send_for_eligible_packeta_order_with_packet(self):
        self.assertEqual(self.plan(snap()), ["send", "ready"])
        self.assertEqual(self.plan(snap(payment_method="wf-woo-comgate", comgate_confirmed=True)), ["send", "ready"])

    def test_terminal_and_in_flight_states(self):
        self.assertEqual(self.plan(snap(), "mailed"), ["done", "already_mailed"])
        self.assertEqual(self.plan(snap(), "attention"), ["attention_existing", "needs_attention"])
        self.assertEqual(self.plan(snap(), "mailing"), ["check", "mailing_in_progress_or_unknown"])

    def test_skips_never_alert(self):
        self.assertEqual(self.plan(snap(payment_method="bacs")), ["skip", "payment_method_excluded"])
        self.assertEqual(self.plan(snap(payment_method="wf-woo-comgate")), ["skip", "comgate_unverified"])
        self.assertEqual(self.plan(snap(created_ts=FLOOR - 1)), ["skip", "before_cutoff_no_retroactive"])
        self.assertEqual(self.plan(snap(since_ts=0)), ["skip", "before_cutoff_no_retroactive"])
        self.assertEqual(self.plan(snap(status="completed")), ["skip", "status_not_processing"])
        self.assertEqual(self.plan(snap(sizes={})), ["skip", "sizes_unusable"])

    def test_ppl_and_packeta_problems_need_attention(self):
        self.assertEqual(self.plan(snap(carrier="PPL"), row=None), ["attention", "ppl_manual_label_required"])
        self.assertEqual(self.plan(snap(), configured=False), ["attention", "packeta_unconfigured"])
        self.assertEqual(self.plan(snap(), row=dict(ROW_OK, carrier_id="106")), ["attention", "packeta_external_carrier_manual"])
        self.assertEqual(self.plan(snap(), row=dict(ROW_OK, packet_status="cancelled")), ["attention", "packet_cancelled"])

    def test_wait_for_packet(self):
        self.assertEqual(self.plan(snap(), row=None), ["wait", "packet_not_submitted"])
        self.assertEqual(self.plan(snap(), row=dict(ROW_OK, packet_id=None)), ["wait", "packet_not_submitted"])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Provider(unittest.TestCase):
    def prov(self, carrier, row, pw="secret", pdf="PDF"):
        return php(
            "$calls=[]; $r=molosoc_la_provider(%s,'',['row'=>%s,'api_password'=>%s,'fetch'=>function($id,$p) use (&$calls){"
            "$calls[]=[$id,$p]; return %s;}]); unset($r['pdf']); echo json_encode([$r,$calls]);" % (
                json.dumps(carrier, ensure_ascii=False), "null" if row is None else q(row), json.dumps(pw),
                "false" if pdf is None else json.dumps(PDF)))

    def test_fetches_existing_packet_only(self):
        r, calls = self.prov("Zásilkovna", ROW_OK)
        self.assertEqual(r, {"ok": True, "live": True, "ref": "4123456789"})
        self.assertEqual(calls, [["4123456789", "secret"]])

    def test_rechecks_row_at_fetch_time(self):
        r, calls = self.prov("Zásilkovna", None)
        self.assertEqual((r["reason"], r.get("permanent"), calls), ("packet_not_submitted", None, []))
        r, calls = self.prov("Zásilkovna", dict(ROW_OK, carrier_id="13"))
        self.assertEqual((r["reason"], r["permanent"], calls), ("packeta_external_carrier_manual", True, []))
        r, calls = self.prov("Zásilkovna", dict(ROW_OK, packet_status="cancelled"))
        self.assertEqual((r["reason"], r["permanent"], calls), ("packet_cancelled", True, []))

    def test_ppl_and_unconfigured_never_fetch(self):
        r, calls = self.prov("PPL", ROW_OK)
        self.assertEqual((r["reason"], r["permanent"], calls), ("ppl_manual_label_required", True, []))
        r, calls = self.prov("Zásilkovna", ROW_OK, pw="")
        self.assertEqual((r["reason"], calls), ("packeta_unconfigured", []))

    def test_fetch_failure_is_retryable(self):
        r, _ = self.prov("Zásilkovna", ROW_OK, pdf=None)
        self.assertEqual((r["reason"], r.get("permanent")), ("packeta_fetch_failed", None))


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Alerts(unittest.TestCase):
    def test_message_is_fixed_recipient_ids_only(self):
        m = php("echo json_encode(molosoc_la_alert_message(1234,'ppl_manual_label_required'));")
        self.assertEqual(m["to"], "hello@molosoc.com")
        self.assertEqual(m["subject"], "MOLOSOC štítek: objednávka #1234 vyžaduje ruční kontrolu (ppl_manual_label_required)")
        self.assertIn("PPL", m["body"])
        self.assertNotIn("jarka", json.dumps(m))

    def test_unexpected_reason_is_sanitized(self):
        m = php("echo json_encode(molosoc_la_alert_message(5,\"x\\r\\nBcc: a@b.c\"));")
        self.assertTrue(m["subject"].endswith("(unknown)"))
        self.assertNotIn("Bcc", json.dumps(m))

    def alert(self, stored, send_ok="true"):
        return php(
            "$st=%s; $sent=[]; $order=[]; $r=molosoc_la_alert(9,'max_tries',function() use (&$st){return $st;},"
            "function($v) use (&$st,&$order){$order[]='set'; $st=$v;},"
            "function($to,$s,$b,$h) use (&$sent,&$order){$order[]='send'; $sent[]=[$to,$s,$h]; return %s;});"
            "echo json_encode([$r,$st,$sent,$order]);" % (json.dumps(stored), send_ok))

    def test_at_most_once_marker_before_send(self):
        r, st, sent, order = self.alert("")
        self.assertEqual((r, st, order), ("alert_sent", "max_tries", ["set", "send"]))
        self.assertEqual(sent, [["hello@molosoc.com", "MOLOSOC štítek: objednávka #9 vyžaduje ruční kontrolu (max_tries)",
                                 ["Content-Type: text/plain; charset=UTF-8"]]])
        self.assertEqual(self.alert("ppl_manual_label_required")[0:3:2], ["alert_already_sent", []])
        r, st, sent, _ = self.alert("", send_ok="false")
        self.assertEqual((r, st, len(sent)), ("alert_failed", "max_tries", 1))


# A fake I/O for molosoc_la_step: everything recorded in $L; deliver/state are scriptable.
STEP_IO = r"""
function mk_io(array $cfg, array &$L) {
 $L = ['calls'=>[], 'audit'=>[], 'alerts'=>[], 'attention'=>[], 'seen_set'=>null];
 $st = $cfg['state'] ?? '';
 return [
  'now' => function() use ($cfg) { return $cfg['now'] ?? 1000; },
  'state' => function() use (&$st, &$L) { return $st; },
  'seen' => function() use ($cfg) { return $cfg['seen'] ?? 0; },
  'set_seen' => function($t) use (&$L) { $L['seen_set'] = $t; },
  'snapshot' => function() use ($cfg, &$L) { $L['calls'][]='snapshot'; return $cfg['snap']; },
  'packeta_row' => function() use ($cfg, &$L) { $L['calls'][]='row'; return $cfg['row'] ?? null; },
  'configured' => function() use ($cfg) { return $cfg['configured'] ?? true; },
  'deliver' => function() use ($cfg, &$L, &$st) { $L['calls'][]='deliver'; if (isset($cfg['state_after'])) { $st=$cfg['state_after']; } return $cfg['deliver'] ?? ['mailed','']; },
  'tries' => function() use ($cfg) { return $cfg['tries'] ?? 0; },
  'attention' => function($r) use (&$L, &$st) { $L['attention'][]=$r; $st='attention'; },
  'alert' => function($r) use (&$L) { $L['alerts'][]=$r; },
  'audit' => function($row) use (&$L) { $L['audit'][]=$row; },
 ];
}
"""


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Step(unittest.TestCase):
    def step(self, **cfg):
        cfg.setdefault("snap", snap())
        return php(STEP_IO + "$L=[]; $io=mk_io(%s,$L); $r=molosoc_la_step(7,$io); echo json_encode([$r,$L]);" % q(cfg))

    def test_send_path(self):
        (res, delay), L = self.step(row=ROW_OK)
        self.assertEqual((res, delay), ("mailed", 0))
        self.assertEqual(L["calls"], ["snapshot", "row", "deliver"])
        self.assertEqual((L["alerts"], L["attention"], L["seen_set"]), ([], [], 1000))

    def test_terminal_states_do_nothing(self):
        for st, want in (("mailed", "already_mailed"), ("attention", "needs_attention")):
            (res, delay), L = self.step(state=st, row=ROW_OK)
            self.assertEqual((res, delay, L["calls"], L["audit"], L["seen_set"]), (want, 0, [], [], None))

    def test_mailing_state_goes_to_state_machine_without_new_decision(self):
        (res, _), L = self.step(state="mailing", deliver=["mail_state_unknown", ""], state_after="attention")
        self.assertEqual(L["calls"], ["deliver"])
        self.assertEqual(L["alerts"], ["mail_state_unknown"])

    def test_skip_audits_once_no_retry_no_alert(self):
        (res, delay), L = self.step(snap=snap(payment_method="bacs"))
        self.assertEqual((res, delay, L["alerts"]), ("payment_method_excluded", 0, []))
        self.assertEqual([a["reason"] for a in L["audit"]], ["payment_method_excluded"])
        self.assertNotIn("deliver", L["calls"])

    def test_ppl_attention_and_one_alert_never_delivers(self):
        (res, delay), L = self.step(snap=snap(carrier="PPL"))
        self.assertEqual((res, delay), ("ppl_manual_label_required", 0))
        self.assertEqual((L["attention"], L["alerts"]), (["ppl_manual_label_required"], ["ppl_manual_label_required"]))
        self.assertEqual(L["calls"], ["snapshot"])  # No Packeta lookup, no fetch, no mail.

    def test_wait_for_packet_then_timeout(self):
        (res, delay), L = self.step(row=None, now=1000, seen=0)
        self.assertEqual((res, delay), ("waiting_for_packet", 900))
        self.assertEqual([a["result"] for a in L["audit"]], ["waiting"])
        (res, delay), L = self.step(row=None, now=5000, seen=1000)
        self.assertEqual((res, delay, L["audit"], L["alerts"]), ("waiting_for_packet", 900, [], []))
        (res, delay), L = self.step(row=None, now=1000 + 259200, seen=1000)
        self.assertEqual((res, delay), ("packet_wait_timeout", 0))
        self.assertEqual((L["attention"], L["alerts"]), (["packet_wait_timeout"], ["packet_wait_timeout"]))
        self.assertNotIn("deliver", L["calls"])

    def test_retryable_failure_retries_then_exhausts(self):
        (res, delay), L = self.step(row=ROW_OK, deliver=["provider_failed", ""], tries=1)
        self.assertEqual((res, delay, L["alerts"]), ("provider_failed", 600, []))
        (res, delay), L = self.step(row=ROW_OK, deliver=["mailer_failed", ""], tries=3)
        self.assertEqual((res, delay), ("max_tries", 0))
        self.assertEqual((L["attention"], L["alerts"]), (["max_tries"], ["max_tries"]))

    def test_locked_retries(self):
        (res, delay), L = self.step(row=ROW_OK, deliver=["locked", ""])
        self.assertEqual((res, delay, L["alerts"]), ("locked", 600, []))

    def test_permanent_provider_failure_alerts_with_detail(self):
        (res, delay), L = self.step(row=ROW_OK, deliver=["provider_permanent", "packet_cancelled"], state_after="attention")
        self.assertEqual((res, delay, L["alerts"]), ("provider_permanent", 0, ["packet_cancelled"]))
        (res, _), L = self.step(row=ROW_OK, deliver=["ref_changed", ""], state_after="attention")
        self.assertEqual(L["alerts"], ["ref_changed"])

    # Codex #372 finding 1: an `exception` RESULT from the state machine must never strand the order.
    def test_exception_result_after_mailing_goes_to_attention_without_resend(self):
        (res, delay), L = self.step(row=ROW_OK, deliver=["exception", ""], state_after="mailing")
        self.assertEqual((res, delay), ("mail_state_unknown", 0))
        self.assertEqual((L["attention"], L["alerts"]), (["mail_state_unknown"], ["mail_state_unknown"]))
        self.assertEqual(L["calls"].count("deliver"), 1)

    def test_exception_result_before_mailing_retries_inside_window_then_alerts(self):
        (res, delay), L = self.step(row=ROW_OK, deliver=["exception", ""], state_after="label_ready", now=5000, seen=1000)
        self.assertEqual((res, delay, L["attention"], L["alerts"]), ("exception", 600, [], []))
        (res, delay), L = self.step(row=ROW_OK, deliver=["exception", ""], state_after="label_ready",
                                    now=1000 + 259200, seen=1000)
        self.assertEqual((res, delay), ("exception", 0))
        self.assertEqual((L["attention"], L["alerts"]), (["exception"], ["exception"]))

    def test_exception_result_when_already_attention_alerts_once(self):
        (res, delay), L = self.step(row=ROW_OK, deliver=["exception", ""], state_after="attention")
        self.assertEqual((res, delay, L["attention"], L["alerts"]), ("exception", 0, [], ["exception"]))


# End to end through the REAL Phase 3 state machine (molosoc_ld3_process) with in-memory meta.
E2E = r"""
function e2e(array $snap, $row, array &$M, array &$mails, $fetch_ok = true) {
 $io = [
  'allow_live'=>true,
  'snapshot'=>function() use ($snap){ return $snap; },
  'state'=>function() use (&$M){ return $M['state'] ?? ''; }, 'set_state'=>function($s) use (&$M){ $M['state']=$s; },
  'ref'=>function() use (&$M){ return $M['ref'] ?? ''; }, 'set_ref'=>function($r) use (&$M){ $M['ref']=$r; },
  'tries'=>function() use (&$M){ return $M['tries'] ?? 0; }, 'set_tries'=>function($n) use (&$M){ $M['tries']=$n; },
  'lock'=>function(){ return true; }, 'unlock'=>function(){},
  'audit'=>function($r) use (&$M){ $M['audit'][]=$r; },
  'provider'=>function($c,$ref) use ($row, $fetch_ok, &$M){ $r = molosoc_la_provider($c,$ref,['row'=>$row,'api_password'=>'pw','fetch'=>function($id,$p) use ($fetch_ok){ return $fetch_ok ? base64_decode('PDFB64') : false; }]); $M['detail']=$r['reason'] ?? ''; return $r; },
  'mailer'=>function($mail) use (&$mails){ return molosoc_ll_mail($mail, function($to,$s,$b,$h,$a) use (&$mails){ $mails[]=[$to,$s,$h,basename($a[0])]; return true; }, function($n,$b){ return '/tmp/'.$n; }, function($p){}); },
 ];
 $step = [
  'now'=>function(){ return 2000; }, 'state'=>$io['state'], 'seen'=>function() use (&$M){ return $M['seen'] ?? 0; },
  'set_seen'=>function($t) use (&$M){ $M['seen']=$t; }, 'snapshot'=>$io['snapshot'],
  'packeta_row'=>function() use ($row){ return $row; }, 'configured'=>function(){ return true; },
  'deliver'=>function() use ($io, &$M){ $r = molosoc_ld3_process(77, $io); return [$r, 'provider_permanent'===$r ? $M['detail'] : '']; },
  'tries'=>$io['tries'], 'attention'=>function($r) use (&$M){ $M['state']='attention'; $M['audit'][]=['result'=>'attention','reason'=>$r]; },
  'alert'=>function($r) use (&$M){ $M['alerts'][]=$r; }, 'audit'=>$io['audit'],
 ];
 return molosoc_la_step(77, $step);
}
"""


@unittest.skipUnless(HAVE_PHP, "php not installed")
class EndToEnd(unittest.TestCase):
    def run_e2e(self, s, row, runs=1, pre=None, fetch_ok=True):
        code = (E2E.replace("PDFB64", base64.b64encode(PDF.encode()).decode()) +
                "$M=%s; $mails=[]; $out=[]; for($i=0;$i<%d;$i++){ $out[]=e2e(%s,%s,$M,$mails,%s); } echo json_encode([$out,$M,$mails]);" % (
                    q(pre or {}) if pre else "[]", runs, q(s), "null" if row is None else q(row),
                    "true" if fetch_ok else "false"))
        return php(code)

    def test_mails_exactly_once_to_fixed_recipient(self):
        out, M, mails = self.run_e2e(snap(sizes={"M": 1, "L": 2}), ROW_OK, runs=3)
        self.assertEqual(out, [["mailed", 0], ["already_mailed", 0], ["already_mailed", 0]])
        self.assertEqual(mails, [["jarka01@atlas.cz", "Zásilkovna | 3 kusy | 1x M, 2x L",
                                  ["Content-Type: text/plain; charset=UTF-8", "Cc: hello@molosoc.com"], "zasilkovna-77.pdf"]])
        self.assertEqual((M["state"], M["ref"], M.get("alerts")), ("mailed", "4123456789", None))

    def test_ppl_zero_mails(self):
        out, M, mails = self.run_e2e(snap(carrier="PPL"), None, runs=2)
        self.assertEqual(out, [["ppl_manual_label_required", 0], ["needs_attention", 0]])
        self.assertEqual((mails, M["alerts"]), ([], ["ppl_manual_label_required"]))

    def test_ref_change_stops_duplicate(self):
        out, M, mails = self.run_e2e(snap(), dict(ROW_OK, packet_id="4999999999"), pre={"ref": "4123456789", "state": "label_ready"})
        self.assertEqual(out, [["ref_changed", 0]])
        self.assertEqual((mails, M["state"], M["alerts"]), ([], "attention", ["ref_changed"]))

    def test_cancelled_packet_zero_mails(self):
        out, M, mails = self.run_e2e(snap(), dict(ROW_OK, packet_status="cancelled"))
        self.assertEqual((out, mails, M["alerts"]), ([["packet_cancelled", 0]], [], ["packet_cancelled"]))

    def test_fetch_failures_retry_then_attention(self):
        out, M, mails = self.run_e2e(snap(), ROW_OK, runs=4, fetch_ok=False)
        self.assertEqual(out, [["provider_failed", 600], ["provider_failed", 600], ["max_tries", 0], ["needs_attention", 0]])
        self.assertEqual((mails, M["alerts"], M["state"]), ([], ["max_tries"], "attention"))

    def test_mailer_throw_through_real_state_machine_never_strands_or_resends(self):
        code = (E2E.replace("PDFB64", base64.b64encode(PDF.encode()).decode())
                .replace("$mails[]=[$to,$s,$h,basename($a[0])]; return true;", "$mails[]=[$to]; throw new RuntimeException('smtp');") +
                "$M=[]; $mails=[]; $out=[]; for($i=0;$i<2;$i++){ $out[]=e2e(%s,%s,$M,$mails); } echo json_encode([$out,$M,$mails]);" % (
                    q(snap()), q(ROW_OK)))
        out, M, mails = php(code)
        self.assertEqual(out, [["mail_state_unknown", 0], ["needs_attention", 0]])
        self.assertEqual((len(mails), M["state"], M["alerts"]), (1, "attention", ["mail_state_unknown"]))

    def test_crash_after_mailing_never_resends(self):
        out, M, mails = self.run_e2e(snap(), ROW_OK, pre={"state": "mailing", "ref": "4123456789"})
        self.assertEqual((out, mails, M["alerts"]), ([["mail_state_unknown", 0]], [], ["mail_state_unknown"]))

    def test_bacs_and_pre_cutoff_never_mail(self):
        for s in (snap(payment_method="bacs"), snap(created_ts=FLOOR - 5), snap(payment_method="wf-woo-comgate")):
            out, M, mails = self.run_e2e(s, ROW_OK)
            self.assertEqual((mails, M.get("alerts"), M.get("state")), ([], None, None), s)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Helpers(unittest.TestCase):
    def test_lock_stale(self):
        r = php("echo json_encode([molosoc_la_lock_stale(false,5000), molosoc_la_lock_stale(null,5000),"
                "molosoc_la_lock_stale(4100,5000), molosoc_la_lock_stale(4099,5000), molosoc_la_lock_stale('100',5000)]);")
        self.assertEqual(r, [False, False, False, True, True])

    def test_exception_retry_bounded(self):
        r = php("echo json_encode([molosoc_la_exception_retry(0,10), molosoc_la_exception_retry(10,20),"
                "molosoc_la_exception_retry(10,10+259200)]);")
        self.assertEqual(r, [False, True, False])

    def test_autosubmit_summary(self):
        r = php("echo json_encode([molosoc_la_packeta_autosubmit_summary(null),"
                "molosoc_la_packeta_autosubmit_summary(['allow'=>'1','payment_method_events'=>['cod'=>'onOrderProcessing','wf-woo-comgate'=>'onOrderProcessing','bacs'=>'x']])]);")
        self.assertEqual(r, [{"allow": "ne", "cod": "-", "comgate": "-"},
                             {"allow": "ano", "cod": "onOrderProcessing", "comgate": "onOrderProcessing"}])

    def test_packeta_row_read_only_prepared(self):
        fake = r"""
class FakeWpdb { public $prefix='wp_'; public $calls=[];
 function esc_like($s){ return $s; }
 function prepare($q,...$a){ $this->calls[]=[$q,$a]; return ['q'=>$q,'a'=>$a]; }
 function get_var($p){ return 'wp_packetery_order'; }
 function get_row($p,$o){ $this->calls[]=['get_row',$o]; return ['packet_id'=>'4123456789','carrier_id'=>'zpointcz','packet_status'=>null]; } }
$GLOBALS['wpdb']=new FakeWpdb();"""
        r = php(fake + "echo json_encode([molosoc_la_packeta_row(7), molosoc_la_packeta_row(0), $GLOBALS['wpdb']->calls]);")
        self.assertEqual(r[0], ROW_OK)
        self.assertIsNone(r[1])
        self.assertIn(["SELECT `packet_id`, `carrier_id`, `packet_status` FROM `wp_packetery_order` WHERE `id` = %d LIMIT 1", [7]], r[2])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class SafetyContract(unittest.TestCase):
    def code(self):
        return re.sub(r"/\*.*?\*/", "", AUTO.read_text(encoding="utf-8"), flags=re.S)

    def test_no_hooks_without_opt_in(self):
        hooks = php("echo json_encode($GLOBALS['hooks'] ?? []);")
        self.assertEqual(hooks, [])

    def test_hooks_with_opt_in_are_deferred(self):
        for const in ("MOLOSOC_LABEL_AUTO_PREVIEW", "MOLOSOC_LABEL_AUTO_ENABLED"):
            hooks = php("echo json_encode($GLOBALS['hooks'] ?? []);", pre_extra="define('%s', true);" % const)
            self.assertEqual(hooks, ["muplugins_loaded"], const)

    def test_never_creates_packets_changes_orders_or_reads_customer_data(self):
        code = self.code()
        for banned in ("submitPacket", "createPacket", "packetAttributes", "createPackages", "CPLOperation",
                       "update_status", "set_status", "get_billing_", "get_shipping_", "get_customer",
                       "->query(", "->insert(", "->delete(", "->replace(", "curl_", "wp_remote_"):
            self.assertNotIn(banned, code, banned)

    def test_only_writes_are_own_meta_lock_options_and_queue(self):
        code = self.code()
        # The one $wpdb->update is the compare-and-swap of our own lock option.
        self.assertEqual(code.count("->update("), 1)
        self.assertIn("'option_name'  => $key", code)
        self.assertEqual(code.count("wp_mail"), 1)  # The alert; label mail goes through the shared fixed-recipient mailer.
        self.assertIn("'mailer'     => 'molosoc_ll_mail_now'", (MU / "molosoc-carrier-label-live.php").read_text(encoding="utf-8"))

    def test_status_page_is_read_only(self):
        src = self.code()
        body = re.search(r"function molosoc_la_render_page\(.*?\n}\n", src, re.S).group(0)
        for w in ("meta_set", "update_option", "add_option", "delete_option", "wp_mail", "_fetch", "schedule",
                  "add_meta_data", "save"):
            self.assertNotIn(w, body, w)
        self.assertIn("current_user_can( MOLOSOC_LA_CAP )", body)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class SweepCollect(unittest.TestCase):
    """Codex #372 finding 2: handled orders must never hide a newer missed order."""

    def collect(self, pages, handled):
        code = ("$P=%s; $H=%s; $read=[]; $q=[];"
                "$n=molosoc_la_sweep_collect(function($p) use ($P,&$read){ $read[]=$p; return $P[$p-1] ?? []; },"
                "function($id) use ($H){ return !in_array($id,$H,true); }, function($id) use (&$q){ $q[]=$id; });"
                "echo json_encode([$n,$q,$read]);") % (q(pages), q(handled))
        return php(code)

    def test_pages_past_handled_orders(self):
        pages = [list(range(1, 101)), list(range(101, 201)), [201, 202]]
        n, queued, read = self.collect(pages, list(range(1, 201)))
        self.assertEqual((n, queued, read), (2, [201, 202], [1, 2, 3]))

    def test_queue_bound_and_page_bound(self):
        pages = [list(range(1, 101)), list(range(101, 201))]
        n, queued, read = self.collect(pages, [])
        self.assertEqual((n, len(queued), read), (100, 100, [1]))
        full = [list(range(i * 100 + 1, i * 100 + 101)) for i in range(30)]
        n, queued, read = self.collect(full, list(range(1, 3001)))
        self.assertEqual((n, read), (0, list(range(1, 21))))

    def test_sweep_query_skips_seen_orders_and_pages(self):
        src = AUTO.read_text(encoding="utf-8")
        body = re.search(r"function molosoc_la_sweep\(\).*?\n}\n", src, re.S).group(0)
        for w in ("'key'     => MOLOSOC_LA_SEEN_META", "'compare' => 'NOT EXISTS'", "'paged'        => $p", "molosoc_la_sweep_collect("):
            self.assertIn(w, body, w)


if __name__ == "__main__":
    unittest.main()
