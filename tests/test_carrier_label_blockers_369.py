"""Issue #369 (ZANETA_DECISION 2026-11-11): fixes for the four live-check blockers.

1. Packeta packet id is read read-only from Packeta 2.3.2's own `{prefix}packetery_order`
   table, not from order meta.
2. Packeta API password falls back to the password Packeta stores in its `packetery` option.
3. The cut-off can come from the wp-config constant MOLOSOC_LABEL_DISPATCH_SINCE.
4. Comgate `paid_status` is the default rule.

Real PHP, injected fakes for $wpdb / get_option, no network, no mail, no writes.
"""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MU = ROOT / "site/mu-plugins"
FILES = [MU / f for f in (
    "molosoc-carrier-label-dispatch.php", "molosoc-carrier-label-delivery.php",
    "molosoc-carrier-label-live.php", "molosoc-carrier-label-preview.php")]
DISPATCH, _, LIVE, PREVIEW = FILES
HAVE_PHP = shutil.which("php") is not None
FLOOR = 1794355200  # 2026-11-11T00:00:00Z

# Fake $wpdb that records every method call. Only prepare/esc_like/get_var exist, so any
# write method (query/insert/update/delete/replace) would be a fatal error in the test.
FAKE_WPDB = r"""
class FakeWpdb { public $prefix='wp_'; public $calls=[]; public $tables=['wp_packetery_order']; public $rows=[];
 function esc_like($s){ $this->calls[]=['esc_like',$s]; return addcslashes($s,'_%\\'); }
 function prepare($q,...$a){ $this->calls[]=['prepare',$q,$a]; return ['q'=>$q,'a'=>$a]; }
 function get_var($p){ $this->calls[]=['get_var',$p['q']];
  if (0===strpos($p['q'],'SHOW TABLES LIKE')) { $t=stripcslashes($p['a'][0]); return in_array($t,$this->tables,true)?$t:null; }
  return array_key_exists($p['a'][0],$this->rows) ? $this->rows[$p['a'][0]] : null; } }
"""


def q(x):
    raw = json.dumps(x, ensure_ascii=False).replace("\\", "\\\\").replace("'", "\\'")
    return "json_decode('%s',true)" % raw


def php(code, pre_extra=""):
    pre = ("define('ABSPATH','/x/'); function add_action(){$GLOBALS['hooks'][]=func_get_arg(0);} " + pre_extra +
           " ".join("require %s;" % json.dumps(str(f)) for f in FILES))
    out = subprocess.run(["php", "-r", pre + code], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class PacketIdFromPacketaTable(unittest.TestCase):
    def lookup(self, order_id=7, rows=None, tables=None):
        setup = "$GLOBALS['wpdb']=new FakeWpdb();"
        if rows is not None:
            setup += "$GLOBALS['wpdb']->rows=%s;" % q(rows)
        if tables is not None:
            setup += "$GLOBALS['wpdb']->tables=%s;" % q(tables)
        return php(FAKE_WPDB + setup +
                   "echo json_encode([molosoc_ll_packeta_packet_id(%d), $GLOBALS['wpdb']->calls]);" % order_id)

    def test_reads_packet_id_with_prepared_select(self):
        val, calls = self.lookup(rows={"7": "4123456789"})
        self.assertEqual(val, "4123456789")
        selects = [c for c in calls if c[0] == "prepare" and c[1].startswith("SELECT")]
        self.assertEqual(len(selects), 1)
        self.assertEqual(selects[0][1], "SELECT `packet_id` FROM `wp_packetery_order` WHERE `id` = %d LIMIT 1")
        self.assertEqual(selects[0][2], [7])

    def test_missing_row_null_or_table_is_empty(self):
        self.assertEqual(self.lookup(rows={})[0], "")
        self.assertEqual(self.lookup(rows={"7": None})[0], "")
        val, calls = self.lookup(rows={"7": "4123456789"}, tables=[])
        self.assertEqual(val, "")
        self.assertFalse(any(c[0] == "prepare" and c[1].startswith("SELECT") for c in calls))

    def test_invalid_order_id_never_queries(self):
        val, calls = self.lookup(order_id=0)
        self.assertEqual((val, calls), ("", []))

    def test_no_wpdb_is_empty(self):
        self.assertEqual(php("echo json_encode(molosoc_ll_packeta_packet_id(7));"), "")

    def test_value_is_trimmed_and_validated_downstream(self):
        self.assertEqual(self.lookup(rows={"7": " 4123456789 "})[0], "4123456789")
        r = php("echo json_encode(molosoc_lp_report(7,%s,'','x; DROP',true));" % q(dict(
            status="processing", payment_method="cod", comgate_confirmed=False, carrier="Zásilkovna",
            created_ts=2000, since_ts=1000, done=False, sizes={"M": 1})))
        self.assertIn("packet_id_malformed", r["blockers"])
        self.assertEqual(r["packet_id"], "")

    def test_read_only_source(self):
        src = LIVE.read_text(encoding="utf-8")
        body = re.search(r"function molosoc_ll_packeta_packet_id\(.*?\n}\n", src, re.S).group(0)
        for w in ("->query(", "->insert(", "->update(", "->delete(", "->replace(", "INSERT", "UPDATE", "DELETE"):
            self.assertNotIn(w, body, w)
        code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
        self.assertNotIn("MOLOSOC_LL_PACKETA_PACKET_META", code)
        self.assertNotIn("MOLOSOC_LL_PACKETA_PACKET_META", re.sub(r"/\*.*?\*/", "", PREVIEW.read_text(encoding="utf-8"), flags=re.S))


@unittest.skipUnless(HAVE_PHP, "php not installed")
class PacketaPassword(unittest.TestCase):
    def pw(self, const, option):
        return php("echo json_encode(molosoc_ll_packeta_password(%s,%s));" % (const, option))

    def test_constant_wins(self):
        self.assertEqual(self.pw("'from-config'", "['api_password'=>'from-packeta']"), "from-config")

    def test_falls_back_to_packeta_setting(self):
        self.assertEqual(self.pw("null", "['api_password'=>'from-packeta','api_key'=>'k']"), "from-packeta")
        self.assertEqual(self.pw("'   '", "['api_password'=>'from-packeta']"), "from-packeta")

    def test_fail_closed(self):
        for const, opt in (("null", "null"), ("null", "false"), ("null", "'str'"), ("null", "[]"),
                           ("null", "['api_password'=>'']"), ("null", "['api_password'=>123]"),
                           ("null", "['api_password'=>\"a\\nb\"]"), ("123", "null"), ("\"a\\rb\"", "null")):
            self.assertEqual(self.pw(const, opt), "", (const, opt))

    def test_provider_now_uses_packeta_storage_without_fetching_or_leaking(self):
        # No packet yet (missing row): password from the packetery option, no fetch, no password in result.
        out = php(FAKE_WPDB + "$GLOBALS['wpdb']=new FakeWpdb();"
                  "function get_option($k,$d=false){ $GLOBALS['opts'][]=$k; return 'packetery'===$k?['api_password'=>'s3cret-pw']:$d; }"
                  "echo json_encode([molosoc_ll_provider_now(7,'Zásilkovna',''), $GLOBALS['opts']]);")
        res, opts = out
        self.assertEqual(res["reason"], "packet_not_submitted")
        self.assertEqual(opts, ["packetery"])
        self.assertNotIn("s3cret-pw", json.dumps(res))

    def test_provider_now_unconfigured_without_any_password(self):
        out = php(FAKE_WPDB + "$GLOBALS['wpdb']=new FakeWpdb(); $GLOBALS['wpdb']->rows=['7'=>'4123456789'];"
                  "function get_option($k,$d=false){ return $d; }"
                  "echo json_encode(molosoc_ll_provider_now(7,'Zásilkovna',''));")
        self.assertEqual((out["reason"], out["permanent"]), ("packeta_unconfigured", True))

    def test_ppl_reads_nothing(self):
        out = php("function get_option(){ throw new Exception('read'); }"
                  "echo json_encode(molosoc_ll_provider_now(7,'PPL',''));")
        self.assertEqual(out["reason"], "ppl_manual_label_required")

    def test_password_never_shown_by_preview(self):
        src = PREVIEW.read_text(encoding="utf-8")
        self.assertNotIn("api_password", src)
        self.assertEqual(src.count("molosoc_ll_packeta_password_now()"), 1)
        self.assertIn("'' !== molosoc_ll_packeta_password_now()", src)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class CutoffConstant(unittest.TestCase):
    def since(self, defined, const, option="0"):
        return php("echo json_encode(molosoc_ld_since_ts(%s,%s,%s));" % (defined, const, option))

    def test_option_used_without_constant(self):
        self.assertEqual(self.since("false", "null", "1234"), 1234)
        self.assertEqual(self.since("false", "null", "false"), 0)
        self.assertEqual(self.since("false", "null", "-5"), 0)

    def test_constant_timestamp_and_iso(self):
        self.assertEqual(self.since("true", str(FLOOR + 3600)), FLOOR + 3600)
        self.assertEqual(self.since("true", "'%d'" % (FLOOR + 60)), FLOOR + 60)
        self.assertEqual(self.since("true", "'2026-11-12T00:00:00Z'"), FLOOR + 86400)
        self.assertEqual(self.since("true", "'2026-11-12T01:00:00+01:00'"), FLOOR + 86400)

    def test_constant_wins_and_invalid_fails_closed_without_fallback(self):
        for bad in ("null", "true", "''", "'tomorrow'", "'2026-11-12'", "'2026-11-12 00:00:00'",
                    "'2026-13-40T00:00:00Z'", "1.8e9", str(FLOOR - 1), "'%d'" % (FLOOR - 1), "-1",
                    "'2025-01-01T00:00:00Z'", "[%d]" % (FLOOR + 1)):
            self.assertEqual(self.since("true", bad, str(FLOOR + 5)), 0, bad)

    def test_no_retroactive_processing(self):
        snap = dict(status="processing", payment_method="cod", comgate_confirmed=False, carrier="Zásilkovna",
                    done=False, sizes={"M": 1})
        decide = "echo json_encode(molosoc_ld_decide(array_merge(%s,['created_ts'=>%%d,'since_ts'=>molosoc_ld_since_ts(true,%%s,0)])));" % q(snap)
        self.assertEqual(php(decide % (FLOOR + 10, "'2026-11-11T00:00:05Z'"))[0], True)
        self.assertEqual(php(decide % (FLOOR, "'2026-11-11T00:00:05Z'")), [False, "before_cutoff_no_retroactive"])
        self.assertEqual(php(decide % (FLOOR + 10, "'garbage'")), [False, "before_cutoff_no_retroactive"])

    def test_glue_reads_constant(self):
        src = DISPATCH.read_text(encoding="utf-8")
        self.assertIn("defined( 'MOLOSOC_LABEL_DISPATCH_SINCE' ) ? 0 : get_option( 'molosoc_label_dispatch_since', 0 )", src)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class ComgatePaidStatusDefault(unittest.TestCase):
    # Live Comgate 1.1.40 shape: transaction id equals the tmp id after payment.
    PAID = dict(status="processing", payment_method="wf-woo-comgate", transaction_id="ABCD-1234-EFGH",
                tmp_transaction_id="ABCD-1234-EFGH", is_paid=True)

    def rule(self, v):
        return php("echo json_encode(molosoc_ld_comgate_tmp_rule(%s));" % v)

    def paid(self, rule_const="null", **ch):
        f = dict(self.PAID, **ch)
        return php("$f=%s; $f['tmp_rule']=molosoc_ld_comgate_tmp_rule(%s); echo json_encode(molosoc_ld_comgate_paid($f));" % (q(f), rule_const))

    def test_rule_resolution(self):
        self.assertEqual(self.rule("null"), "paid_status")
        self.assertEqual(self.rule("'paid_status'"), "paid_status")
        self.assertEqual(self.rule("'strict'"), "strict")
        for v in ("'STRICT'", "true", "''", "'other'"):
            self.assertEqual(self.rule(v), "paid_status", v)

    def test_live_paid_order_accepted_by_default(self):
        self.assertTrue(self.paid())

    def test_unpaid_and_other_cases_still_rejected(self):
        for ch in (dict(transaction_id=""), dict(transaction_id="  "), dict(is_paid=False), dict(status="on-hold"),
                   dict(status="completed"), dict(status="cancelled"), dict(payment_method="bacs"),
                   dict(payment_method="cod")):
            self.assertFalse(self.paid(**ch), ch)

    def test_explicit_strict_still_available(self):
        self.assertFalse(self.paid(rule_const="'strict'"))
        self.assertTrue(self.paid(rule_const="'strict'", tmp_transaction_id="TMP-9"))

    def test_glue_uses_resolver(self):
        src = DISPATCH.read_text(encoding="utf-8")
        self.assertIn("molosoc_ld_comgate_tmp_rule( defined( 'MOLOSOC_LABEL_COMGATE_TMPID_RULE' )", src)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class StillOffByDefault(unittest.TestCase):
    def test_no_hooks_without_opt_in(self):
        self.assertEqual(php("echo json_encode($GLOBALS['hooks']??[]);"), [])

    def test_never_creates_packets_or_mails_from_preview(self):
        for f in (LIVE, PREVIEW):
            self.assertNotIn("createPacket", f.read_text(encoding="utf-8"))
        self.assertNotIn("wp_mail", PREVIEW.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
