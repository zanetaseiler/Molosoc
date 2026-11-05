"""Issue #345 Phase 1: dry-run carrier label dispatch. Runs the real PHP
(no WordPress needed: only pure functions + injected I/O are exercised)."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "site/mu-plugins/molosoc-carrier-label-dispatch.php"
SRC = PLUGIN.read_text(encoding="utf-8")
HAVE_PHP = shutil.which("php") is not None

BASE = dict(status="processing", payment_method="cod", comgate_confirmed=False,
            carrier="PPL", created_ts=2000, since_ts=1000, done=False, sizes={"M": 1, "L": 1})


def php(code):
    prelude = "define('ABSPATH','/x/'); require %s;" % json.dumps(str(PLUGIN))
    out = subprocess.run(["php", "-r", prelude + code], capture_output=True, text=True, check=True)
    return out.stdout


def decide(**kw):
    snap = dict(BASE, **kw)
    return json.loads(php("echo json_encode(molosoc_ld_decide(json_decode(%s,true)));" % json.dumps(json.dumps(snap))))


def subject(carrier, sizes):
    return json.loads(php("echo json_encode(molosoc_ld_subject(%s, json_decode(%s,true)));"
                          % (json.dumps(carrier, ensure_ascii=False), json.dumps(json.dumps(sizes)))))


def run_process(snaps, lock_ok=True, adapter_ok=True, adapter_raises=False):
    """snaps: list of snapshots returned by successive snapshot() calls."""
    code = """
$snaps = json_decode(%s, true); $i = 0; $log = []; $done = 0; $adapter_calls = 0; $unlocked = 0;
$io = [
 'snapshot' => function() use (&$snaps, &$i) { return $snaps[min($i++, count($snaps)-1)]; },
 'lock' => function() { return %s; },
 'unlock' => function() use (&$unlocked) { $unlocked++; },
 'audit' => function($r) use (&$log) { $log[] = $r; },
 'mark_done' => function() use (&$done) { $done++; },
 'adapter' => function($c) use (&$adapter_calls) { $adapter_calls++; %s return ['ok' => %s]; },
];
$res = molosoc_ld_process(7, $io);
echo json_encode(['res'=>$res,'log'=>$log,'done'=>$done,'adapter'=>$adapter_calls,'unlocked'=>$unlocked]);
""" % (json.dumps(json.dumps(snaps)), "true" if lock_ok else "false",
       "throw new RuntimeException('boom');" if adapter_raises else "",
       "true" if adapter_ok else "false")
    return json.loads(php(code))


class StaticContract(unittest.TestCase):
    def test_no_mail_no_live_calls(self):
        import re
        code = re.sub(r"/\*.*?\*/", "", SRC, flags=re.S)
        code = re.sub(r"(?m)^\s*//.*$", "", code)
        for banned in ("wp_mail(", "wp_remote_", "curl_", "createPackages", "getLabelContents",
                       "packetsLabelsPdf", "set_status(", "update_status("):
            self.assertNotIn(banned, code)

    def test_inert_without_constant_and_no_live_mode(self):
        self.assertIn("defined( 'MOLOSOC_LABEL_DISPATCH_DRY_RUN' ) && true ===", SRC)
        self.assertNotIn("LABEL_DISPATCH_LIVE", SRC)

    def test_recipient(self):
        self.assertIn("'jarka01@atlas.cz'", SRC)

    def test_comgate_default_fails_closed(self):
        self.assertIn("'molosoc_label_dispatch_comgate_confirmed', false", SRC)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Subject(unittest.TestCase):
    def test_examples_and_plurals(self):
        self.assertEqual(subject("PPL", {"L": 1, "M": 1}), "PPL | 2 kusy | 1x M, 1x L")
        self.assertEqual(subject("Zásilkovna", {"M": 1}), "Zásilkovna | 1 kus | 1x M")
        self.assertEqual(subject("PPL", {"S": 2, "M": 1, "L": 1}), "PPL | 4 kusy | 2x S, 1x M, 1x L")
        self.assertEqual(subject("PPL", {"M": 3, "L": 2}), "PPL | 5 kusů | 3x M, 2x L")
        self.assertEqual(subject("PPL", {"XL": 1, "S": 7}), "PPL | 8 kusů | 7x S, 1x XL")

    def test_live_size_slugs_normalize(self):
        def n(v):
            return json.loads(php("echo json_encode(molosoc_ld_normalize_size(%s));" % json.dumps(v)))
        self.assertEqual(n("m-medium"), "M")
        self.assertEqual(n(" L-Large "), "L")
        self.assertEqual(n("xl"), "XL")
        self.assertEqual(n(""), "")
        self.assertEqual(subject("PPL", {n("l-large"): 1, n("m-medium"): 1}), "PPL | 2 kusy | 1x M, 1x L")

    def test_expired_lock_reclaim_is_compare_and_swap(self):
        i = SRC.index("'lock'      =>")
        block = SRC[i:SRC.index("'unlock'", i)]
        self.assertIn("$wpdb->update", block)
        self.assertIn("'option_value' => (string) $observed", block)
        self.assertNotIn("delete_option", block)

    def test_bad_input_returns_null(self):
        self.assertIsNone(subject("DHL", {"M": 1}))
        self.assertIsNone(subject("PPL", {}))
        self.assertIsNone(subject("PPL", {"M": 0}))

    def test_carrier_detection(self):
        def d(ids):
            return json.loads(php("echo json_encode(molosoc_ld_detect_carrier(json_decode(%s,true)));" % json.dumps(json.dumps(ids))))
        self.assertEqual(d(["pplcz_parcelshop"]), "PPL")
        self.assertEqual(d(["packetery_shipping_method"]), "Zásilkovna")
        self.assertEqual(d(["packeta_method_13161"]), "Zásilkovna")
        self.assertIsNone(d(["flat_rate"]))
        self.assertIsNone(d([]))
        self.assertIsNone(d(["pplcz_x", "packetery_shipping_method"]))


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Eligibility(unittest.TestCase):
    def test_cod_eligible_both_carriers(self):
        self.assertEqual(decide(), [True, "eligible"])
        self.assertEqual(decide(carrier="Zásilkovna"), [True, "eligible"])

    def test_confirmed_card_eligible_only_when_verified(self):
        self.assertEqual(decide(payment_method="wf_woo_comgate", comgate_confirmed=True), [True, "eligible"])
        self.assertEqual(decide(payment_method="wf_woo_comgate", comgate_confirmed=False), [False, "comgate_unverified"])

    def test_excluded_payment_and_status(self):
        self.assertEqual(decide(payment_method="bacs"), [False, "payment_method_excluded"])
        self.assertEqual(decide(payment_method=""), [False, "payment_method_excluded"])
        for st in ("on-hold", "pending", "failed", "cancelled", "refunded", "completed", "missing"):
            self.assertEqual(decide(status=st), [False, "status_not_processing"], st)

    def test_no_retroactive(self):
        self.assertEqual(decide(created_ts=500), [False, "before_cutoff_no_retroactive"])
        self.assertEqual(decide(since_ts=0), [False, "before_cutoff_no_retroactive"])

    def test_unknown_carrier_or_sizes(self):
        self.assertEqual(decide(carrier=None), [False, "carrier_unknown"])
        self.assertEqual(decide(sizes={}), [False, "sizes_unusable"])

    def test_already_done(self):
        self.assertEqual(decide(done=True), [False, "already_processed"])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class Pipeline(unittest.TestCase):
    def test_happy_path_dry_run(self):
        r = run_process([BASE])
        self.assertEqual(r["res"], "dry_run_would_send")
        self.assertEqual((r["done"], r["adapter"], r["unlocked"]), (1, 1, 1))
        row = r["log"][-1]
        self.assertEqual(row["subject"], "PPL | 2 kusy | 1x M, 1x L")
        self.assertEqual(row["to"], "jarka01@atlas.cz")
        self.assertFalse(row["live"])
        self.assertNotIn("email", json.dumps(row).replace("jarka01@atlas.cz", ""))

    def test_duplicate_event_second_run_skips(self):
        r = run_process([dict(BASE, done=True)])
        self.assertEqual(r["res"], "already_processed")
        self.assertEqual((r["adapter"], r["done"]), (0, 0))

    def test_lock_held_means_no_action(self):
        r = run_process([BASE], lock_ok=False)
        self.assertEqual(r["res"], "locked")
        self.assertEqual((r["adapter"], r["done"], r["unlocked"]), (0, 0, 0))

    def test_recheck_after_lock_blocks_status_change(self):
        r = run_process([BASE, dict(BASE, status="on-hold")])
        self.assertEqual(r["res"], "recheck_status_not_processing")
        self.assertEqual((r["adapter"], r["done"], r["unlocked"]), (0, 0, 1))

    def test_recheck_blocks_concurrent_completion(self):
        r = run_process([BASE, dict(BASE, done=True)])
        self.assertEqual(r["res"], "recheck_already_processed")
        self.assertEqual(r["adapter"], 0)

    def test_adapter_failure_leaves_no_marker_and_unlocks(self):
        r = run_process([BASE], adapter_ok=False)
        self.assertEqual(r["res"], "adapter_failed")
        self.assertEqual((r["done"], r["unlocked"]), (0, 1))

    def test_adapter_exception_is_safe_and_retryable(self):
        r = run_process([BASE], adapter_raises=True)
        self.assertEqual(r["res"], "exception")
        self.assertEqual((r["done"], r["unlocked"]), (0, 1))
        self.assertEqual(r["log"][-1]["class"], "RuntimeException")
        self.assertNotIn("boom", json.dumps(r["log"]))

    def test_transfer_and_unconfirmed_card_never_reach_adapter(self):
        for snap in (dict(BASE, payment_method="bacs", status="on-hold"),
                     dict(BASE, payment_method="wf_woo_comgate", comgate_confirmed=False)):
            r = run_process([snap])
            self.assertEqual(r["adapter"], 0)
            self.assertEqual(r["log"][-1]["result"], "skipped")

    def test_adapter_stub_is_not_live(self):
        out = json.loads(php("echo json_encode(molosoc_ld_adapter_generate_label('PPL', 1));"))
        self.assertFalse(out["live"])


if __name__ == "__main__":
    unittest.main()
