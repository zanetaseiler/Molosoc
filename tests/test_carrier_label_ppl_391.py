"""Issue #391: hands-off PPL labels (create exactly one shipment through the PPL CZ 1.1.3
plugin's own models/batch, fetch its label, mail it through the #369 path). OFF by default.

Real PHP, injected fakes only: no network, no mail, no DB, no PPL plugin, no shipment.
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
PPL = MU / "molosoc-carrier-label-ppl.php"
AUTO = MU / "molosoc-carrier-label-auto.php"
FILES = [MU / f for f in (
    "molosoc-carrier-label-auto.php", "molosoc-carrier-label-delivery.php",
    "molosoc-carrier-label-dispatch.php", "molosoc-carrier-label-live.php",
    "molosoc-carrier-label-ppl.php")]
HAVE_PHP = shutil.which("php") is not None
FLOOR = 1794355200  # 2026-11-11T00:00:00Z
UUID = "3f2b8c1e-9a4d-4e6f-8b7a-1c2d3e4f5a6b"

PDF = ("%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
       "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>endobj\n% " + "x" * 150 + "\ntrailer<</Root 1 0 R>>\n%%EOF\n")


def q(x):
    raw = json.dumps(x, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'")
    return "json_decode('%s',true)" % raw


def php(code, pre_extra=""):
    pre = ("define('ABSPATH','/x/'); function add_action(){$GLOBALS['hooks'][]=func_get_arg(0);} " + pre_extra +
           " ".join("require %s;" % json.dumps(str(f)) for f in FILES))
    out = subprocess.run(["php", "-r", pre + code], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def snap(**kw):
    s = dict(status="processing", payment_method="cod", comgate_confirmed=False, carrier="PPL",
             created_ts=FLOOR + 100, since_ts=FLOOR, done=False, sizes={"M": 1})
    s.update(kw)
    return s


def facts(**kw):
    f = dict(method_ids=["pplcz_SMAR"], errors=0, service_code="SMAD", has_parcel=True, parcel_code="KM12345",
             country="CZ", sender_id=3, payment_cod=True, order_total=1290.0, currency="CZK",
             cod_value=1290.0, cod_currency="CZK", cod_vs="0000000077", packages=1)
    f.update(kw)
    return f


def ship(id_=11, state="Complete", batch=UUID, errors="", number="40123456789", phase="None", packages=None):
    return dict(id=id_, batch_id=batch, batch_local_id=5, import_state=state, import_errors=errors,
                packages=packages if packages is not None else [dict(shipment_number=number, phase=phase)])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Gates(unittest.TestCase):
    def test_ppl_gate_strict_and_off_by_default(self):
        r = php("echo json_encode([molosoc_lp_gate(true), molosoc_lp_gate(null), molosoc_lp_gate(1),"
                "molosoc_lp_gate('true'), molosoc_lp_gate(false)]);")
        self.assertEqual(r, [True, False, False, False, False])

    def test_auto_ppl_gate_needs_constant_file_and_plugin(self):
        r = php("echo json_encode([molosoc_la_ppl_gate(true,true,true), molosoc_la_ppl_gate(null,true,true),"
                "molosoc_la_ppl_gate(1,true,true), molosoc_la_ppl_gate(true,false,true), molosoc_la_ppl_gate(true,true,false)]);")
        self.assertEqual(r, [True, False, False, False, False])

    def test_ppl_off_without_constant_and_without_plugin(self):
        self.assertEqual(php("echo json_encode([molosoc_la_ppl_on(), molosoc_lp_enabled_now()]);"), [False, False])
        # Constant on, but the PPL CZ plugin classes are not loaded: still off (fail closed).
        r = php("echo json_encode([molosoc_la_ppl_on(), molosoc_lp_enabled_now()]);",
                pre_extra="define('MOLOSOC_LABEL_AUTO_PPL_ENABLED', true);")
        self.assertEqual(r, [False, False])

    def test_live_test_limit_validation(self):
        r = php("echo json_encode([molosoc_lp_limit_ok(false,null), molosoc_lp_limit_ok(true,1), molosoc_lp_limit_ok(true,20),"
                "molosoc_lp_limit_ok(true,0), molosoc_lp_limit_ok(true,21), molosoc_lp_limit_ok(true,'1'), molosoc_lp_limit_ok(true,null)]);")
        self.assertEqual(r, [True, True, True, False, False, False, False])

    def test_slot_claim_first_n_orders_only(self):
        code = ("$S=[]; $get=function($i) use (&$S){ return $S[$i] ?? 0; };"
                "$add=function($i,$id) use (&$S){ if (isset($S[$i])) return false; $S[$i]=$id; return true; };"
                "$r=[molosoc_lp_claim(1,77,$get,$add), molosoc_lp_claim(1,78,$get,$add), molosoc_lp_claim(1,77,$get,$add),"
                "molosoc_lp_claim(2,78,$get,$add), molosoc_lp_claim(2,79,$get,$add)];"
                # A lost race: the slot looks free but another request wins add_option.
                "$race=molosoc_lp_claim(1,80,function($i){ return 0; },function($i,$id){ return false; });"
                "echo json_encode([$r,$S,$race]);")
        r, S, race = php(code)
        self.assertEqual(r, [True, False, True, True, False])
        self.assertEqual(S, {"1": 77, "2": 78})
        self.assertFalse(race)

    def test_state_meta_key_shared(self):
        self.assertEqual(php("echo json_encode(MOLOSOC_LA_PPL_STATE_META === MOLOSOC_LP_STATE_META);"), True)

    def test_ppl_file_registers_no_hooks(self):
        for pre in ("", "define('MOLOSOC_LABEL_AUTO_PPL_ENABLED', true);"):
            self.assertEqual(php("echo json_encode($GLOBALS['hooks'] ?? []);", pre_extra=pre), [])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Check(unittest.TestCase):
    def check(self, **kw):
        return php("echo json_encode(molosoc_lp_check(%s));" % q(facts(**kw)))

    def test_ok_for_smar_sbox_priv(self):
        self.assertEqual(self.check(), "")
        self.assertEqual(self.check(method_ids=["pplcz_SBOX"]), "")
        self.assertEqual(self.check(method_ids=["pplcz_PRIV"], has_parcel=False, parcel_code=""), "")
        self.assertEqual(self.check(payment_cod=False, cod_value=None, cod_vs="", cod_currency=""), "")

    def test_refusals(self):
        cases = {
            "ppl_method_ambiguous": dict(method_ids=[]),
            "ppl_method_unknown": dict(method_ids=["pplcz_CONN"]),
            "ppl_validation_failed": dict(errors=2),
            "ppl_service_missing": dict(service_code=""),
            "ppl_not_cz": dict(country="SK"),
            "ppl_currency_unexpected": dict(currency="EUR", cod_currency="EUR"),
            "ppl_parcel_missing": dict(has_parcel=False),
            "ppl_parcel_unexpected": dict(method_ids=["pplcz_PRIV"]),
            "ppl_sender_mismatch": dict(sender_id=1),
            "ppl_cod_mismatch": dict(cod_value=1000.0),
            "ppl_cod_vs_invalid": dict(cod_vs=""),
            "ppl_cod_unexpected": dict(payment_cod=False),
            "ppl_packages_unexpected": dict(packages=2),
        }
        for want, kw in cases.items():
            self.assertEqual(self.check(**kw), want, kw)
        self.assertEqual(self.check(method_ids=["pplcz_SMAR", "pplcz_PRIV"]), "ppl_method_ambiguous")
        self.assertEqual(self.check(method_ids=["pplcz_SBOX"], parcel_code=" "), "ppl_parcel_missing")
        self.assertEqual(self.check(cod_currency="EUR"), "ppl_cod_mismatch")
        self.assertEqual(self.check(cod_vs="12345678901"), "ppl_cod_vs_invalid")
        self.assertEqual(self.check(cod_value=None), "ppl_cod_mismatch")

    def test_missing_facts_fail_closed(self):
        self.assertNotEqual(php("echo json_encode(molosoc_lp_check([]));"), "")
        self.assertEqual(php("echo json_encode(molosoc_lp_check(['method_ids'=>['pplcz_SMAR']]));"), "ppl_validation_failed")


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Classify(unittest.TestCase):
    def c(self, s):
        return php("echo json_encode(molosoc_lp_classify(%s));" % q(s))

    def test_states(self):
        self.assertEqual(self.c(ship()), ["ready", "40123456789"])
        for st in ("InProgress", "InProcess", "Accepted"):
            self.assertEqual(self.c(ship(state=st, number="")), ["wait", "ppl_import_pending"], st)
        self.assertEqual(self.c(ship(state="Error")), ["attention", "ppl_import_error"])
        self.assertEqual(self.c(ship(state="InProgress", errors="bad zip")), ["attention", "ppl_import_error"])
        self.assertEqual(self.c(ship(state="None", batch="")), ["attention", "ppl_create_failed"])
        self.assertEqual(self.c(ship(state="", batch="")), ["attention", "ppl_create_failed"])
        self.assertEqual(self.c(ship(state="Weird")), ["attention", "ppl_import_state_unknown"])
        self.assertEqual(self.c(ship(number="")), ["attention", "ppl_shipment_number_missing"])
        self.assertEqual(self.c(ship(number="1; DROP")), ["attention", "ppl_shipment_number_missing"])
        self.assertEqual(self.c(ship(packages=[])), ["attention", "ppl_shipment_number_missing"])
        self.assertEqual(self.c(ship(phase="Canceled")), ["attention", "ppl_shipment_cancelled"])

    def test_is_remote(self):
        r = php("echo json_encode([molosoc_lp_is_remote(%s), molosoc_lp_is_remote(%s), molosoc_lp_is_remote(%s),"
                "molosoc_lp_is_remote(%s)]);" % (q(ship()), q(ship(state="None", batch="")),
                                                 q(ship(state="InProgress", batch="")), q(ship(state="", batch=""))))
        self.assertEqual(r, [True, False, True, False])


# Fake PPL plugin + order meta for molosoc_lp_prepare. $P is the plugin's table for ONE order.
PREP = r"""
function mk_prep(array &$P, array &$M, array $cfg = []) {
 return [
  'state'=>function() use (&$M){ return $M['ppl_state'] ?? ''; },
  'set_state'=>function($s) use (&$M){ $M['ppl_state']=$s; $M['writes'][]='state:'.$s; },
  'shipment_id'=>function() use (&$M){ return (int)($M['ppl_shipment'] ?? 0); },
  'set_shipment_id'=>function($id) use (&$M){ $M['ppl_shipment']=$id; $M['writes'][]='shipment:'.$id; },
  'shipments'=>function() use (&$P){ return array_values($P['shipments'] ?? []); },
  'refresh'=>function($b) use (&$P, $cfg){ $P['refreshes'][]=$b; foreach ($P['shipments'] as $k=>$s) {
      if ($s['batch_id']===$b && ($cfg['import'] ?? 'Complete')!=='keep') { $P['shipments'][$k]['import_state']=$cfg['import'] ?? 'Complete';
        $P['shipments'][$k]['packages'][0]['shipment_number']='40123456789'; } } },
  'facts'=>function() use ($cfg, &$P){ $P['facts_calls']=($P['facts_calls'] ?? 0)+1; if (!empty($cfg['facts_throw'])) throw new RuntimeException('x'); return $cfg['facts']; },
  'api_ready'=>function() use ($cfg){ return $cfg['api'] ?? true; },
  'stage'=>function() use (&$P, $cfg){ $P['stages']=($P['stages'] ?? 0)+1; if (!empty($cfg['stage_fail'])) return ['ok'=>false,'reason'=>'x'];
      $id = 100 + count($P['shipments'] ?? []); $P['shipments'][$id]=['id'=>$id,'batch_id'=>'','batch_local_id'=>9,'import_state'=>'','import_errors'=>'',
      'packages'=>[['shipment_number'=>'','phase'=>'None']]]; return ['ok'=>true,'shipment_id'=>$id,'batch_local_id'=>9]; },
  'submit'=>function($bl) use (&$P, $cfg){ $P['creates']=($P['creates'] ?? 0)+1; if (!empty($cfg['submit_throw'])) throw new RuntimeException('timeout');
      if (!empty($cfg['submit_fail'])) return ['ok'=>false,'reason'=>'x'];
      foreach ($P['shipments'] as $k=>$s) { if ($s['batch_local_id']===$bl) { $P['shipments'][$k]['import_state']='InProgress'; $P['shipments'][$k]['batch_id']='UUID'; } }
      return ['ok'=>true]; },
  'claim'=>function() use ($cfg, &$P){ $P['claims']=($P['claims'] ?? 0)+1; return $cfg['claim'] ?? true; },
  'audit'=>function($r) use (&$M){ $M['audit'][]=$r; },
 ];
}
""".replace("UUID", UUID)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Prepare(unittest.TestCase):
    def run_prep(self, P=None, M=None, runs=1, **cfg):
        cfg.setdefault("facts", facts())
        code = (PREP + "$P=%s; $M=%s; $out=[]; for($i=0;$i<%d;$i++){ $out[]=molosoc_lp_prepare(77, mk_prep($P,$M,%s)); }"
                       " echo json_encode([$out,$P,$M]);" % (q(P) if P else "['shipments'=>[]]", q(M) if M else "[]", runs, q(cfg)))
        return php(code)

    def test_creates_exactly_once_then_settles(self):
        out, P, M = self.run_prep(runs=4)
        self.assertEqual(out, [["wait", "ppl_import_pending"], ["ready", "40123456789"],
                               ["ready", "40123456789"], ["ready", "40123456789"]])
        self.assertEqual((P["stages"], P["creates"]), (1, 1))
        self.assertEqual((M["ppl_state"], M["ppl_shipment"]), ("created", 100))
        # `creating` is persisted BEFORE the plugin draft and the PPL call.
        self.assertEqual(M["writes"][:2], ["state:creating", "shipment:100"])
        self.assertEqual([a["result"] for a in M["audit"]], ["ppl_creating", "ppl_created"])
        self.assertEqual(P["refreshes"], [UUID])  # Refreshed once while pending, never once Complete.

    def test_crash_after_creating_never_creates_again(self):
        out, P, M = self.run_prep(M={"ppl_state": "creating"}, runs=3)
        self.assertEqual(out, [["attention", "ppl_create_state_unknown"]] * 3)
        self.assertEqual((P.get("stages"), P.get("creates")), (None, None))

    def test_submit_throw_or_failure_is_attention_and_final(self):
        for k in ("submit_throw", "submit_fail", "stage_fail"):
            out, P, M = self.run_prep(runs=3, **{k: True})
            self.assertEqual(out, [["attention", "ppl_create_failed"], ["attention", "ppl_create_state_unknown"],
                                   ["attention", "ppl_create_state_unknown"]], k)
            self.assertEqual(P["stages"], 1, k)
            self.assertLessEqual(P.get("creates", 0), 1, k)
            self.assertEqual(M["ppl_state"], "creating", k)

    def test_refusal_and_api_unavailable_write_nothing(self):
        out, P, M = self.run_prep(facts=facts(country="SK"))
        self.assertEqual((out, P.get("stages"), M), ([["attention", "ppl_not_cz"]], None, []))
        out, P, M = self.run_prep(api=False, runs=2)
        self.assertEqual((out, P.get("stages"), M), ([["wait", "ppl_api_unavailable"]] * 2, None, []))

    def test_facts_exception_before_create_writes_nothing(self):
        code = (PREP + "$P=['shipments'=>[]]; $M=[]; try { molosoc_lp_prepare(77, mk_prep($P,$M,%s)); $r='no'; }"
                       " catch (RuntimeException $e) { $r='thrown'; } echo json_encode([$r,$P,$M]);" % q(dict(facts=facts(), facts_throw=True)))
        r, P, M = php(code)
        self.assertEqual((r, P.get("stages"), M), ("thrown", None, []))

    def test_manual_remote_shipment_is_adopted_never_duplicated(self):
        P = {"shipments": {"55": ship(id_=55, state="InProgress", number="")}}
        out, P, M = self.run_prep(P=P, runs=2)
        self.assertEqual(out, [["ready", "40123456789"], ["ready", "40123456789"]])
        self.assertEqual((P.get("stages"), P.get("creates"), M["ppl_state"], M["ppl_shipment"]), (None, None, "adopted", 55))
        self.assertEqual([a["result"] for a in M["audit"]], ["ppl_adopted"])
        self.assertIsNone(P.get("facts_calls"))

    def test_manual_draft_multiple_and_missing(self):
        P = {"shipments": {"55": ship(id_=55, state="None", batch="", number="")}}
        out, P2, M = self.run_prep(P=P, runs=2)
        self.assertEqual((out, P2.get("stages"), M), ([["attention", "ppl_manual_draft_exists"]] * 2, None, []))
        P = {"shipments": {"55": ship(id_=55), "56": ship(id_=56)}}
        out, P2, M = self.run_prep(P=P)
        self.assertEqual((out, P2.get("stages"), M), ([["attention", "ppl_multiple_shipments"]], None, []))
        # A manual click AFTER our create: a second remote shipment appears → stop, never mail.
        P = {"shipments": {"100": ship(id_=100), "101": ship(id_=101)}}
        out, _, _ = self.run_prep(P=P, M={"ppl_state": "created", "ppl_shipment": 100})
        self.assertEqual(out, [["attention", "ppl_multiple_shipments"]])
        out, _, _ = self.run_prep(P={"shipments": {}}, M={"ppl_state": "created", "ppl_shipment": 100})
        self.assertEqual(out, [["attention", "ppl_shipment_missing"]])
        out, _, _ = self.run_prep(M={"ppl_state": "bogus"})
        self.assertEqual(out, [["attention", "ppl_state_unknown"]])

    def test_live_test_limit_keeps_other_orders_manual(self):
        out, P, M = self.run_prep(claim=False, runs=2)
        self.assertEqual(out, [["attention", "ppl_manual_label_required"]] * 2)
        self.assertEqual((P.get("stages"), P.get("creates"), P.get("facts_calls"), M), (None, None, None, []))
        # Once created, the slot is not asked again.
        out, P, M = self.run_prep(runs=3)
        self.assertEqual(P["claims"], 1)

    def test_import_error_after_create(self):
        code = (PREP + "$P=['shipments'=>[]]; $M=[]; $o=[]; for($i=0;$i<3;$i++){ $o[]=molosoc_lp_prepare(77, mk_prep($P,$M,%s)); }"
                       " echo json_encode([$o,$P]);" % q(dict(facts=facts(), **{"import": "Error"})))
        o, P = php(code)
        self.assertEqual(o, [["wait", "ppl_import_pending"], ["attention", "ppl_import_error"], ["attention", "ppl_import_error"]])
        self.assertEqual(P["creates"], 1)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class ProviderAndLabel(unittest.TestCase):
    def prov(self, state="created", own=None, batch=None, fetch_ok=True, carrier="PPL"):
        own = ship() if own is None else own
        batch = [own] if batch is None else batch
        code = ("$calls=[]; $r=molosoc_lp_provider(%s,'',['state'=>%s,'own'=>%s,'batch_shipments'=>%s,"
                "'fetch'=>function($b,$o,$l) use (&$calls){ $calls[]=[$b,$o,$l]; return %s; }]);"
                "if(isset($r['pdf'])) $r['pdf']=strlen($r['pdf']); echo json_encode([$r,$calls]);" % (
                    json.dumps(carrier), json.dumps(state), "null" if own == "null" else q(own), q(batch),
                    "str_repeat('P',300)" if fetch_ok else "false"))
        return php(code)

    def test_ready_fetches_one_window(self):
        r, calls = self.prov()
        self.assertEqual(r, {"ok": True, "live": True, "ref": "40123456789", "pdf": 300})
        self.assertEqual(calls, [[UUID, 0, 1]])

    def test_refusals_never_fetch(self):
        cases = [
            (dict(carrier="Zásilkovna"), "unknown_carrier", True),
            (dict(state=""), "ppl_shipment_not_ready", True),
            (dict(state="creating"), "ppl_shipment_not_ready", True),
            (dict(own="null"), "ppl_shipment_not_ready", True),
            (dict(own=ship(state="Error")), "ppl_import_error", True),
            (dict(own=ship(phase="Canceled")), "ppl_shipment_cancelled", True),
            (dict(own=ship(batch="../x")), "ppl_batch_id_invalid", True),
            (dict(batch=[ship(), ship(id_=12)]), "ppl_shared_batch_manual", True),
            (dict(batch=[ship(id_=12)]), "ppl_shared_batch_manual", True),
            (dict(own=ship(state="InProgress", number="")), "ppl_import_pending", False),
        ]
        for kw, why, permanent in cases:
            r, calls = self.prov(**kw)
            self.assertEqual((r["ok"], r["reason"], bool(r.get("permanent"))), (False, why, permanent), kw)
            self.assertEqual(calls, [], kw)

    def test_fetch_failure_is_retryable(self):
        r, calls = self.prov(fetch_ok=False)
        self.assertEqual((r["ok"], r["reason"], r.get("permanent")), (False, "ppl_label_fetch_failed", None))

    def test_label_window_and_url(self):
        r = php("echo json_encode([molosoc_lp_label_window(%s,%s), molosoc_lp_label_window(%s,%s), molosoc_lp_label_window(%s,[])]);" % (
            q(ship(packages=[{"shipment_number": "1"}, {"shipment_number": "2"}])),
            q([ship()]), q(ship()), q([ship(), ship(id_=2)]), q(ship())))
        self.assertEqual(r, [[0, 2], None, None])
        url = php("echo json_encode(molosoc_lp_label_url('https://api.dhl.com/ecs/ppl/myapi2', %s, 0, 1));" % json.dumps(UUID))
        self.assertEqual(url, "https://api.dhl.com/ecs/ppl/myapi2/shipment/batch/%s/label?limit=1&offset=0&pageSize=A4&position=1&orderBy=ReferenceId" % UUID)
        self.assertEqual(php("echo json_encode([molosoc_lp_batch_id_valid(%s), molosoc_lp_batch_id_valid('x'), molosoc_lp_batch_id_valid(null)]);"
                             % json.dumps(UUID)), [True, False, False])


# Step-level fake I/O (PPL keys added to the #369 fake).
STEP_IO = r"""
function mk_io(array $cfg, array &$L) {
 $L = ['calls'=>[], 'audit'=>[], 'alerts'=>[], 'attention'=>[]];
 $st = $cfg['state'] ?? '';
 return [
  'now' => function() use ($cfg) { return $cfg['now'] ?? 1000; },
  'state' => function() use (&$st) { return $st; },
  'seen' => function() use ($cfg) { return $cfg['seen'] ?? 0; },
  'set_seen' => function($t) {},
  'snapshot' => function() use ($cfg, &$L) { $L['calls'][]='snapshot'; return $cfg['snap']; },
  'packeta_row' => function() use (&$L) { $L['calls'][]='row'; return null; },
  'configured' => function() { return true; },
  'resolve_mailing' => function() { return 'locked'; },
  'deliver' => function() use ($cfg, &$L) { $L['calls'][]='deliver'; return $cfg['deliver'] ?? ['mailed','']; },
  'tries' => function() { return 0; },
  'attention' => function($r) use (&$L, &$st) { $L['attention'][]=$r; $st='attention'; },
  'alert' => function($r) use (&$L) { $L['alerts'][]=$r; },
  'audit' => function($row) use (&$L) { $L['audit'][]=$row; },
  'alert_sent' => function() { return true; },
  'attention_reason' => function() { return 'needs_attention'; },
  'ppl_enabled' => function() use ($cfg) { return $cfg['ppl'] ?? true; },
  'ppl_state' => function() use ($cfg) { return $cfg['ppl_state'] ?? ''; },
  'ppl_prepare' => function() use ($cfg, &$L) { $L['calls'][]='prepare'; return $cfg['prepare'] ?? ['ready','40123456789']; },
 ];
}
"""


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Step(unittest.TestCase):
    def step(self, **cfg):
        cfg.setdefault("snap", snap())
        return php(STEP_IO + "$L=[]; $io=mk_io(%s,$L); $r=molosoc_la_step(7,$io); echo json_encode([$r,$L]);" % q(cfg))

    def test_plan(self):
        r = php("echo json_encode([molosoc_la_plan(%s,'',null,false), molosoc_la_plan(%s,'',null,false,true),"
                "molosoc_la_plan(%s,'',null,false,true), molosoc_la_plan(%s,'mailed',null,false,true)]);" % (
                    q(snap()), q(snap()), q(snap(payment_method="bacs")), q(snap())))
        self.assertEqual(r, [["attention", "ppl_manual_label_required"], ["ppl", "ppl_auto"],
                             ["skip", "payment_method_excluded"], ["done", "already_mailed"]])

    def test_disabled_keeps_manual_alert(self):
        (res, delay), L = self.step(ppl=False)
        self.assertEqual((res, delay, L["alerts"]), ("ppl_manual_label_required", 0, ["ppl_manual_label_required"]))
        self.assertNotIn("prepare", L["calls"])
        self.assertNotIn("deliver", L["calls"])

    def test_ready_delivers_once(self):
        (res, delay), L = self.step()
        self.assertEqual((res, delay, L["alerts"]), ("mailed", 0, []))
        self.assertEqual(L["calls"], ["snapshot", "prepare", "deliver"])

    def test_wait_then_timeout(self):
        (res, delay), L = self.step(prepare=["wait", "ppl_import_pending"], now=2000, seen=1000)
        self.assertEqual((res, delay, L["alerts"]), ("ppl_import_pending", 300, []))
        (res, delay), L = self.step(prepare=["wait", "ppl_api_unavailable"], now=1000 + 21600, seen=1000)
        self.assertEqual((res, delay, L["attention"], L["alerts"]), ("ppl_wait_timeout", 0, ["ppl_wait_timeout"], ["ppl_wait_timeout"]))

    def test_attention_alerts_once(self):
        (res, delay), L = self.step(prepare=["attention", "ppl_create_failed"])
        self.assertEqual((res, delay, L["attention"], L["alerts"]), ("ppl_create_failed", 0, ["ppl_create_failed"], ["ppl_create_failed"]))
        self.assertNotIn("deliver", L["calls"])

    def test_skips_never_prepare(self):
        for s in (snap(payment_method="bacs"), snap(created_ts=FLOOR - 1), snap(payment_method="wf-woo-comgate")):
            (res, delay), L = self.step(snap=s)
            self.assertNotIn("prepare", L["calls"], s)
            self.assertEqual(L["alerts"], [], s)

    def test_interrupted_create_settled_before_eligibility(self):
        for s in (snap(), snap(status="completed"), snap(status="cancelled")):
            (res, delay), L = self.step(snap=s, ppl_state="creating")
            self.assertEqual((res, delay, L["attention"], L["alerts"]),
                             ("ppl_create_state_unknown", 0, ["ppl_create_state_unknown"], ["ppl_create_state_unknown"]), s)
            self.assertNotIn("prepare", L["calls"])


# End to end: REAL molosoc_la_step + REAL molosoc_lp_prepare (fake plugin) + REAL Phase 3 state
# machine + REAL PPL provider + REAL fixed-recipient mailer (fake wp_mail).
E2E = PREP + r"""
function e2e(array $snap, array &$P, array &$M, array &$mails, array $cfg) {
 $io = [
  'allow_live'=>true,
  'snapshot'=>function() use ($snap){ return $snap; },
  'state'=>function() use (&$M){ return $M['state'] ?? ''; }, 'set_state'=>function($s) use (&$M){ $M['state']=$s; },
  'ref'=>function() use (&$M){ return $M['ref'] ?? ''; }, 'set_ref'=>function($r) use (&$M){ $M['ref']=$r; },
  'tries'=>function() use (&$M){ return $M['tries'] ?? 0; }, 'set_tries'=>function($n) use (&$M){ $M['tries']=$n; },
  'lock'=>function(){ return true; }, 'unlock'=>function(){},
  'audit'=>function($r) use (&$M){ $M['audit'][]=$r; },
  'provider'=>function($c,$ref) use (&$P, &$M, $cfg){
     $own = molosoc_lp_find(array_values($P['shipments']), $M['ppl_shipment'] ?? 0);
     $batch = $own ? array_values(array_filter($P['shipments'], function($s) use ($own){ return $s['batch_id']===$own['batch_id']; })) : [];
     $r = molosoc_lp_provider($c,$ref,['state'=>$M['ppl_state'] ?? '','own'=>$own,'batch_shipments'=>$batch,
        'fetch'=>function($b,$o,$l) use (&$P, $cfg){ $P['fetches'][]=[$b,$o,$l]; return empty($cfg['fetch_fail']) ? base64_decode('PDFB64') : false; }]);
     $M['detail']=$r['reason'] ?? ''; return $r; },
  'mailer'=>function($mail) use (&$mails){ return molosoc_ll_mail($mail, function($to,$s,$b,$h,$a) use (&$mails){ $mails[]=[$to,$s,$h,basename($a[0])]; return true; }, function($n,$b){ return '/tmp/'.$n; }, function($p){}); },
 ];
 $step = [
  'now'=>function() use ($cfg){ return $cfg['now'] ?? 2000; }, 'state'=>$io['state'], 'seen'=>function() use (&$M){ return $M['seen'] ?? 0; },
  'set_seen'=>function($t) use (&$M){ $M['seen']=$t; }, 'snapshot'=>$io['snapshot'],
  'packeta_row'=>function(){ return null; }, 'configured'=>function(){ return true; },
  'resolve_mailing'=>function() use ($io){ return molosoc_la_resolve_mailing(77, $io); },
  'deliver'=>function() use ($io, &$M){ $r = molosoc_ld3_process(77, $io); return [$r, 'provider_permanent'===$r ? $M['detail'] : '']; },
  'tries'=>$io['tries'], 'attention'=>function($r) use (&$M){ $M['state']='attention'; $M['audit'][]=['result'=>'attention','reason'=>$r]; },
  'alert'=>function($r) use (&$M){ if (empty($M['alerts'])) { $M['alerts'][]=$r; } },
  'audit'=>$io['audit'],
  'alert_sent'=>function() use (&$M){ return !empty($M['alerts']); },
  'attention_reason'=>function() use (&$M){ return molosoc_la_attention_reason($M['audit'] ?? []); },
  'ppl_enabled'=>function(){ return true; },
  'ppl_state'=>function() use (&$M){ return $M['ppl_state'] ?? ''; },
  'ppl_prepare'=>function() use (&$P, &$M, $cfg){ return molosoc_lp_prepare(77, mk_prep($P, $M, $cfg)); },
 ];
 return molosoc_la_step(77, $step);
}
""".replace("PDFB64", base64.b64encode(PDF.encode()).decode())


@unittest.skipUnless(HAVE_PHP, "php not installed")
class EndToEnd(unittest.TestCase):
    def run_e2e(self, s=None, runs=1, P=None, M=None, **cfg):
        cfg.setdefault("facts", facts())
        code = E2E + ("$P=%s; $M=%s; $mails=[]; $out=[]; for($i=0;$i<%d;$i++){ $out[]=e2e(%s,$P,$M,$mails,%s); }"
                      " echo json_encode([$out,$P,$M,$mails]);" % (
                          q(P) if P else "['shipments'=>[]]", q(M) if M else "[]", runs, q(s or snap()), q(cfg)))
        return php(code)

    def test_one_shipment_one_mail_across_runs(self):
        out, P, M, mails = self.run_e2e(snap(sizes={"M": 1, "L": 2}), runs=5)
        self.assertEqual(out, [["ppl_import_pending", 300], ["mailed", 0], ["already_mailed", 0],
                               ["already_mailed", 0], ["already_mailed", 0]])
        self.assertEqual((P["stages"], P["creates"], P["fetches"]), (1, 1, [[UUID, 0, 1]]))
        self.assertEqual(mails, [["jarka01@atlas.cz", "PPL | 3 kusy | 1x M, 2x L",
                                  ["Content-Type: text/plain; charset=UTF-8", "Cc: hello@molosoc.com"], "ppl-77.pdf"]])
        self.assertEqual((M["state"], M["ref"], M["ppl_state"], M.get("alerts")), ("mailed", "40123456789", "created", None))
        # The created shipment stays in the plugin's table for this order, linked to its batch.
        self.assertEqual(P["shipments"]["100"]["batch_id"], UUID)
        self.assertEqual(P["shipments"]["100"]["batch_local_id"], 9)

    def test_crash_during_create_one_alert_zero_mails_never_recreates(self):
        out, P, M, mails = self.run_e2e(runs=4, submit_throw=True)
        self.assertEqual(out, [["ppl_create_failed", 0], ["needs_attention", 0], ["needs_attention", 0], ["needs_attention", 0]])
        self.assertEqual((P["creates"], mails, M["alerts"]), (1, [], ["ppl_create_failed"]))

    def test_interrupted_creating_state(self):
        out, P, M, mails = self.run_e2e(runs=2, M={"ppl_state": "creating", "seen": 1000})
        self.assertEqual(out, [["ppl_create_state_unknown", 0], ["needs_attention", 0]])
        self.assertEqual((P.get("creates"), mails, M["alerts"]), (None, [], ["ppl_create_state_unknown"]))

    def test_manual_shipment_overlap_adopted_no_create(self):
        P = {"shipments": {"55": ship(id_=55, state="Complete", number="40999999999")}}
        out, P, M, mails = self.run_e2e(runs=3, P=P)
        self.assertEqual(out, [["mailed", 0], ["already_mailed", 0], ["already_mailed", 0]])
        self.assertEqual((P.get("stages"), P.get("creates"), M["ppl_state"], M["ref"]), (None, None, "adopted", "40999999999"))
        self.assertEqual(len(mails), 1)

    def test_manual_shipment_in_shared_batch_is_not_mailed(self):
        P = {"shipments": {"55": ship(id_=55)}}
        code = E2E + ("$P=%s; $M=[]; $mails=[]; $out=[];"
                      "$out[]=e2e(%s,$P,$M,$mails,%s); echo json_encode([$out,$P,$M,$mails]);" % (
                          q(P), q(snap()), q(dict(facts=facts()))))
        # Shared batch simulated by a second shipment in the same remote batch for ANOTHER order:
        code = code.replace("$batch = $own ? array_values(", "$batch = $own ? array_merge([['id'=>999,'batch_id'=>$own['batch_id']]], array_values(")
        code = code.replace("return $s['batch_id']===$own['batch_id']; })) : [];", "return $s['batch_id']===$own['batch_id']; }))) : [];")
        out, P, M, mails = php(code)
        self.assertEqual(out, [["provider_permanent", 0]])
        self.assertEqual((mails, M["state"], M["alerts"], P.get("fetches")), ([], "attention", ["ppl_shared_batch_manual"], None))

    def test_second_manual_shipment_after_create_stops(self):
        out, P, M, mails = self.run_e2e(runs=1)
        self.assertEqual(out, [["ppl_import_pending", 300]])
        code = E2E + ("$P=%s; $M=%s; $P['shipments']['200']=%s; $mails=[]; $out=[]; for($i=0;$i<2;$i++){ $out[]=e2e(%s,$P,$M,$mails,%s); }"
                      " echo json_encode([$out,$P,$M,$mails]);" % (q(P), q(M), q(ship(id_=200)), q(snap()), q(dict(facts=facts()))))
        out, P, M, mails = php(code)
        self.assertEqual(out, [["ppl_multiple_shipments", 0], ["needs_attention", 0]])
        self.assertEqual((P["creates"], mails, M["alerts"]), (1, [], ["ppl_multiple_shipments"]))

    def test_label_fetch_failures_retry_then_attention_one_create(self):
        out, P, M, mails = self.run_e2e(runs=5, fetch_fail=True)
        self.assertEqual(out, [["ppl_import_pending", 300], ["provider_failed", 600], ["provider_failed", 600],
                               ["max_tries", 0], ["needs_attention", 0]])
        self.assertEqual((P["creates"], mails, M["alerts"], M["state"]), (1, [], ["max_tries"], "attention"))

    def test_refused_order_creates_nothing(self):
        out, P, M, mails = self.run_e2e(runs=2, facts=facts(has_parcel=False))
        self.assertEqual(out, [["ppl_parcel_missing", 0], ["needs_attention", 0]])
        self.assertEqual((P.get("stages"), mails, M["alerts"], M.get("ppl_state")), (None, [], ["ppl_parcel_missing"], None))

    def test_ineligible_orders_touch_nothing(self):
        for s in (snap(payment_method="bacs"), snap(created_ts=FLOOR - 5), snap(payment_method="wf-woo-comgate"),
                  snap(status="on-hold")):
            out, P, M, mails = self.run_e2e(s)
            self.assertEqual((P.get("stages"), mails, M.get("alerts"), M.get("ppl_state")), (None, [], None, None), s)

    def test_import_timeout_alerts_once(self):
        out, P, M, mails = self.run_e2e(runs=2, now=1000 + 21600, M={"seen": 1000}, **{"import": "keep"})
        self.assertEqual(out[0], ["ppl_wait_timeout", 0])
        self.assertEqual((P["creates"], mails, M["alerts"]), (1, [], ["ppl_wait_timeout"]))


@unittest.skipUnless(HAVE_PHP, "php not installed")
class SafetyContract(unittest.TestCase):
    def code(self):
        return re.sub(r"/\*.*?\*/", "", PPL.read_text(encoding="utf-8"), flags=re.S)

    def test_no_mail_no_hooks_no_status_changes_no_secrets(self):
        code = self.code()
        for banned in ("wp_mail", "add_action", "add_filter", "update_status", "set_status", "->query(",
                       "getClientSecret", "getClientId", "client_secret", "get_billing_", "get_shipping_address",
                       "cancelPackage", "error_log", "var_dump", "print_r", "curl_", "wp_remote_post", "header(", "exit("):
            self.assertNotIn(banned, code, banned)

    def test_single_create_call_and_single_label_call(self):
        code = self.code()
        self.assertEqual(code.count("->createPackages("), 1)
        self.assertEqual(code.count("wp_remote_get("), 1)
        self.assertIn("CPLOperation::BASE_URL", code)
        # The create call is reachable only through molosoc_lp_prepare()'s `submit` after `creating`.
        prep = re.search(r"function molosoc_lp_prepare\(.*?\n}\n", code, re.S).group(0)
        self.assertLess(prep.index("set_state']( 'creating' )"), prep.index("$io['stage']()"))
        self.assertLess(prep.index("$io['stage']()"), prep.index("$io['submit']("))

    def test_provider_never_creates(self):
        code = self.code()
        for fn in ("molosoc_lp_provider", "molosoc_lp_provider_now", "molosoc_lp_fetch_now"):
            body = re.search(r"function %s\(.*?\n}\n" % fn, code, re.S).group(0)
            for w in ("createPackages", "stage", "submit", "->save(", "meta_set"):
                self.assertNotIn(w, body, (fn, w))

    def test_uses_the_plugins_own_batch_flow(self):
        body = re.search(r"function molosoc_lp_stage_now\(.*?\n}\n", self.code(), re.S).group(0)
        for w in ("pplcz_denormalize( $model, \\PPLCZ\\Data\\ShipmentData::class )", "new \\PPLCZ\\Data\\BatchData()",
                  "set_batch_local_id", "reorder_batch_shipments", "molosoc_lp_check(", "find_shipments_by_wc_order"):
            self.assertIn(w, body, w)

    def test_auto_file_still_has_no_ppl_internals(self):
        code = re.sub(r"/\*.*?\*/", "", AUTO.read_text(encoding="utf-8"), flags=re.S)
        for banned in ("createPackages", "CPLOperation", "wp_remote_", "PPLCZ"):
            self.assertNotIn(banned, code, banned)


if __name__ == "__main__":
    unittest.main()
