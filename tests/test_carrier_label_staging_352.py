"""Issue #352 Phase 2: staging-only mock harness, Comgate paid evaluator, size
normalisation, live-adapter refusal. Real PHP, no WordPress needed."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "site/mu-plugins/molosoc-carrier-label-dispatch.php"
STAGE = ROOT / "site/mu-plugins/molosoc-carrier-label-staging.php"
HAVE_PHP = shutil.which("php") is not None

BASE = dict(status="processing", payment_method="cod", comgate_confirmed=False,
            carrier="PPL", created_ts=2000, since_ts=1000, done=False, sizes={"M": 1, "L": 1})


def php(code):
    # The staging file calls wp_get_environment_type()/add_filter at load; stub them (production).
    pre = ("define('ABSPATH','/x/'); function wp_get_environment_type(){return 'production';} "
           "function add_filter(){ $GLOBALS['hooked']=true; } "
           "function get_option($k,$d=false){ return $GLOBALS['opt'][$k] ?? $d; } "
           "function update_option($k,$v){ $GLOBALS['opt'][$k]=$v; return true; } require %s; require %s;"
           % (json.dumps(str(CORE)), json.dumps(str(STAGE))))
    return subprocess.run(["php", "-r", pre + code], capture_output=True, text=True, check=True).stdout


def j(code):
    return json.loads(php(code))


def process(snaps, adapter_body):
    code = """
$snaps = json_decode(%s, true); $i = 0; $log = []; $done = 0; $store = [];
$io = [
 'snapshot' => function() use (&$snaps, &$i) { return $snaps[min($i++, count($snaps)-1)]; },
 'lock' => function() { return true; }, 'unlock' => function() {},
 'audit' => function($r) use (&$log) { $log[] = $r; },
 'mark_done' => function() use (&$done) { $done++; },
 'adapter' => function($c) use (&$store) { %s },
];
$res = molosoc_ld_process(7, $io);
echo json_encode(['res'=>$res,'log'=>$log,'done'=>$done]);
""" % (json.dumps(json.dumps(snaps)), adapter_body)
    return j(code)


MOCK = "[$r, $store] = molosoc_ls_mock_adapter($c, ['order_id'=>7,'submitted'=>true,'store'=>$store]); return $r;"


class Static(unittest.TestCase):
    def test_staging_file_has_no_live_calls(self):
        src = STAGE.read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        code = re.sub(r"(?m)^\s*//.*$", "", code)
        for banned in ("wp_mail(", "wp_remote_", "curl_", "createPackages", "getLabelContents",
                       "packetsLabelsPdf", "packetsCarrierLabelsPdf", "set_status(", "update_status(", "'production'"):
            self.assertNotIn(banned, code)

    def test_gate_requires_env_and_constant(self):
        src = STAGE.read_text(encoding="utf-8")
        self.assertIn("molosoc_ls_enabled( wp_get_environment_type()", src)
        self.assertIn("MOLOSOC_LABEL_DISPATCH_STAGING", src)

    def test_core_has_no_live_constant_or_mail(self):
        src = CORE.read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        for banned in ("wp_mail(", "wp_remote_", "LABEL_DISPATCH_LIVE", "update_status("):
            self.assertNotIn(banned, code)

    def test_comgate_config_has_no_default_value(self):
        src = CORE.read_text(encoding="utf-8")
        self.assertNotIn("define( 'MOLOSOC_LD_COMGATE_CONFIRM_KEY'", src)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Gate(unittest.TestCase):
    def enabled(self, env, const):
        return j("echo json_encode(molosoc_ls_enabled(%s, %s));" % (json.dumps(env), const))

    def test_only_staging_or_local_with_constant(self):
        self.assertTrue(self.enabled("staging", "true"))
        self.assertTrue(self.enabled("local", "true"))
        self.assertFalse(self.enabled("production", "true"))
        self.assertFalse(self.enabled("development", "true"))
        self.assertFalse(self.enabled("staging", "false"))
        self.assertFalse(self.enabled("staging", "null"))
        self.assertFalse(self.enabled("staging", "'1'"))

    def test_not_hooked_in_production_stub(self):
        self.assertFalse(j("echo json_encode(isset($GLOBALS['hooked']));"))


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Comgate(unittest.TestCase):
    def paid(self, **kw):
        f = dict(transaction_id="T1", confirm_key="_k", confirm_value="PAID", confirm_actual="PAID")
        f.update(kw)
        return j("echo json_encode(molosoc_ld_comgate_paid(json_decode(%s,true)));" % json.dumps(json.dumps(f)))

    def test_confirmed(self):
        self.assertTrue(self.paid())

    def test_unconfirmed_variants_fail_closed(self):
        self.assertFalse(self.paid(confirm_key=""))
        self.assertFalse(self.paid(confirm_value=""))
        self.assertFalse(self.paid(transaction_id=""))
        self.assertFalse(self.paid(confirm_actual=""))
        self.assertFalse(self.paid(confirm_actual="PENDING"))
        self.assertFalse(self.paid(confirm_actual="paid"))


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Mock(unittest.TestCase):
    def test_both_carriers_confirmed_card(self):
        for carrier, subj in (("PPL", "PPL | 2 kusy | 1x M, 1x L"), ("Zásilkovna", "Zásilkovna | 2 kusy | 1x M, 1x L")):
            r = process([dict(BASE, payment_method="wf_woo_comgate", comgate_confirmed=True, carrier=carrier)], MOCK)
            self.assertEqual(r["res"], "dry_run_would_send")
            row = r["log"][-1]
            self.assertEqual(row["subject"], subj)
            self.assertTrue(row["mock_ref"].startswith("MOCK-"))
            self.assertFalse(row["live"])

    def test_cod_both_carriers(self):
        for carrier in ("PPL", "Zásilkovna"):
            self.assertEqual(process([dict(BASE, carrier=carrier)], MOCK)["res"], "dry_run_would_send")

    def test_unconfirmed_card_transfer_onhold_never_reach_adapter(self):
        for snap in (dict(BASE, payment_method="wf_woo_comgate"),
                     dict(BASE, payment_method="bacs", status="on-hold"),
                     dict(BASE, payment_method="bacs")):
            r = process([snap], "throw new Exception('adapter must not run');")
            self.assertEqual(r["log"][-1]["result"], "skipped")
            self.assertEqual(r["done"], 0)

    def test_duplicate_and_retry(self):
        r = process([dict(BASE, done=True)], "throw new Exception('adapter must not run');")
        self.assertEqual(r["res"], "already_processed")
        a = j("[$r,$s]=molosoc_ls_mock_adapter('PPL',['order_id'=>5,'submitted'=>true,'store'=>[]]);"
              "[$r2,$s2]=molosoc_ls_mock_adapter('PPL',['order_id'=>5,'submitted'=>true,'store'=>$s]);"
              "echo json_encode([$r['mock_ref']===$r2['mock_ref'], count($s2)]);")
        self.assertEqual(a, [True, 1])

    def test_failed_adapter_leaves_no_marker_then_retry_succeeds(self):
        fail = "return ['ok'=>false,'live'=>false];"
        r = process([BASE], fail)
        self.assertEqual((r["res"], r["done"]), ("adapter_failed", 0))
        self.assertEqual(process([BASE], MOCK)["res"], "dry_run_would_send")

    def test_packeta_unsubmitted_packet_fails(self):
        r = process([dict(BASE, carrier="Zásilkovna")],
                    "[$r,$s]=molosoc_ls_mock_adapter($c,['order_id'=>7,'submitted'=>false,'store'=>[]]); return $r;")
        self.assertEqual((r["res"], r["done"]), ("adapter_failed", 0))

    def test_packeta_registered_callback_fails_then_succeeds_after_submit(self):
        # Exercise the real registered filter callback with explicit per-order mock state.
        cb = "$c = molosoc_ls_adapter_filter(null, 'Zásilkovna', 7);"
        r = j(cb + "echo json_encode([$c['ok'], $c['reason'] ?? null]);")
        self.assertEqual(r, [False, "packet_not_submitted"])
        # Via the pipeline: fresh order fails, is not marked done, and retry after submit succeeds.
        adapter = "return molosoc_ls_adapter_filter(null, $c, 7);"
        r = process([dict(BASE, carrier="Zásilkovna")], adapter)
        self.assertEqual((r["res"], r["done"]), ("adapter_failed", 0))
        r = j("molosoc_ls_mock_submit_packet(7); $c = molosoc_ls_adapter_filter(null, 'Zásilkovna', 7);"
              "echo json_encode([$c['ok'], $c['live'], strpos($c['mock_ref'], 'MOCK-')]);")
        self.assertEqual(r, [True, False, 0])
        # Other orders stay unsubmitted; PPL never needs a submit.
        r = j("molosoc_ls_mock_submit_packet(7); $a = molosoc_ls_adapter_filter(null, 'Zásilkovna', 8);"
              "$b = molosoc_ls_adapter_filter(null, 'PPL', 9); echo json_encode([$a['ok'], $b['ok']]);")
        self.assertEqual(r, [False, True])

    def test_live_adapter_is_refused(self):
        r = process([BASE], "return ['ok'=>true,'live'=>true];")
        self.assertEqual((r["res"], r["done"]), ("live_adapter_refused", 0))

    def test_unknown_carrier_mock_fails(self):
        self.assertFalse(j("[$r]=molosoc_ls_mock_adapter('DHL',['order_id'=>1]); echo json_encode($r['ok']);"))

    def test_sizes_slugs_in_subject(self):
        n = lambda v: j("echo json_encode(molosoc_ld_normalize_size(%s));" % json.dumps(v))
        sizes = {n("l-large"): 2, n("m-medium"): 1}
        r = process([dict(BASE, sizes=sizes)], MOCK)
        self.assertEqual(r["log"][-1]["subject"], "PPL | 3 kusy | 1x M, 2x L")


if __name__ == "__main__":
    unittest.main()
