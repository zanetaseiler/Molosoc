"""Issue #222: exact-match CZ product 301 + host-gated staging noindex.

Behavioural checks run the real PHP (stubbed WP helpers); skipped if php is absent.
"""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS = (ROOT / "site/theme/functions.php").read_text(encoding="utf-8")
NOINDEX = ROOT / "automations/staging/staging-noindex.php"
STAGING_WF = (ROOT / ".github/workflows/deploy-mu-plugins-staging.yml").read_text(encoding="utf-8")

SRC = "/product/molosoc-hydratacni-navleky-na-nohy"
DST = "/cz/produkt/hydratacni-navlek-na-nohy/"


# header() is a PHP builtin and cannot be redefined; swap in a capturing stub.
PLUGIN_SRC = NOINDEX.read_text(encoding="utf-8").replace("<?php", "", 1).replace("header(", "molosoc_test_header(")


def php(code):
    return subprocess.run(["php", "-r", code], capture_output=True, text=True, check=True).stdout


def redirect_fn_source():
    m = re.search(r"function molosoc_cz_product_redirect_target\(.*?\n}\n", FUNCTIONS, re.S)
    return m.group(0)


@unittest.skipUnless(shutil.which("php"), "php not installed")
class CzProductRedirect(unittest.TestCase):
    def target(self, uri, home="https://molosoc.com"):
        stubs = (
            "function wp_parse_url($u,$c){return parse_url($u,$c);}"
            "function untrailingslashit($s){return rtrim($s,'/\\\\');}"
            f"function home_url($p){{return '{home}'.$p;}}"
        )
        code = stubs + redirect_fn_source() + f"echo molosoc_cz_product_redirect_target({uri!r});"
        return php(code)

    def test_exact_source_redirects_with_and_without_slash_and_query(self):
        for uri in (SRC + "/", SRC, SRC + "/?utm_source=x"):
            self.assertEqual(self.target(uri), "https://molosoc.com" + DST)

    def test_staging_stays_on_staging(self):
        self.assertEqual(self.target(SRC + "/", "https://staging.molosoc.com"), "https://staging.molosoc.com" + DST)

    def test_other_urls_untouched(self):
        for uri in (
            "/product/moisture-lock-foot-cover/",
            "/foot-covers/moisture-lock-foot-cover/",
            DST,
            "/cz/hydratacni-navleky-molosoc/",
            SRC + "-2/",
            SRC + "/extra/",
            "/cz" + SRC + "/",
            "/",
        ):
            self.assertEqual(self.target(uri), "", uri)

    def test_target_never_equals_source_so_no_loop(self):
        self.assertNotEqual(self.target(SRC + "/").rstrip("/").split("molosoc.com")[1], SRC)

    def test_hook_is_301_early_and_single(self):
        m = re.search(r"add_action\( 'template_redirect', function \(\) \{\s*\$target = molosoc_cz_product_redirect_target.*?\}, (\d+) \);", FUNCTIONS, re.S)
        self.assertIsNotNone(m)
        self.assertLess(int(m.group(1)), 10)  # before wp_old_slug_redirect
        self.assertIn("wp_redirect( $target, 301", m.group(0))
        self.assertEqual(FUNCTIONS.count("molosoc_cz_product_redirect_target( $_SERVER"), 1)


@unittest.skipUnless(shutil.which("php"), "php not installed")
class StagingNoindex(unittest.TestCase):
    def run_plugin(self, host):
        code = (
            "$hdr=[];$f=[];$a=[];"
            "function molosoc_test_header($h,$r=true){global $hdr;$hdr[]=$h;}"
            "function add_action($n,$cb){global $a;$a[$n]=$cb;}"
            "function add_filter($n,$cb,$p=10){global $f;$f[$n]=$cb;}"
            f"$_SERVER['HTTP_HOST']={host!r};"
            + PLUGIN_SRC +
            "$a['send_headers']();"
            "$r=$f['wp_robots'](['index'=>true,'follow'=>true,'max-image-preview'=>'large']);"
            "echo json_encode([$hdr,$r]);"
        )
        import json
        return json.loads(php(code))

    def test_staging_host_gets_header_and_meta(self):
        for host in ("staging.molosoc.com", "STAGING.molosoc.com:443"):
            hdr, robots = self.run_plugin(host)
            self.assertEqual(hdr, ["X-Robots-Tag: noindex, nofollow"])
            self.assertTrue(robots["noindex"] and robots["nofollow"])
            self.assertNotIn("index", robots)

    def test_live_host_untouched(self):
        for host in ("molosoc.com", "www.molosoc.com", "staging.molosoc.com.evil.example", "xstaging.molosoc.com"):
            hdr, robots = self.run_plugin(host)
            self.assertEqual(hdr, [])
            self.assertEqual(robots, {"index": True, "follow": True, "max-image-preview": "large"})


class StagingDeployWiring(unittest.TestCase):
    def test_plugin_not_in_production_mu_plugin_dir(self):
        self.assertFalse((ROOT / "site/mu-plugins/staging-noindex.php").exists())

    def test_no_robots_disallow(self):
        self.assertNotRegex(NOINDEX.read_text(encoding="utf-8"), r"(?i)disallow\s*:|robots_txt")

    def test_staging_workflow_ships_and_checks_it(self):
        self.assertIn("cp automations/staging/staging-noindex.php build/mu-plugins/", STAGING_WF)
        self.assertIn('[ "$n" = "2" ]', STAGING_WF)
        self.assertIn("staging.molosoc.com/?noindex-check", STAGING_WF)
        self.assertIn("https://molosoc.com/", STAGING_WF)

    def test_live_probe_must_connect(self):
        live = [l for l in STAGING_WF.splitlines() if "live.hdr" in l and "curl" in l]
        self.assertEqual(len(live), 1)
        idx = STAGING_WF.index(live[0])
        probe = STAGING_WF[idx:idx + 400]
        self.assertNotIn("|| true", probe.split("grep -qi")[0])
        self.assertIn("exit 1", probe)
        self.assertIn("grep -q '^HTTP/' /tmp/live.hdr", STAGING_WF)

    def test_production_workflow_untouched_by_staging_plugin(self):
        prod = (ROOT / ".github/workflows/deploy-mu-plugins.yml").read_text(encoding="utf-8")
        self.assertNotIn("staging-noindex", prod)


if __name__ == "__main__":
    unittest.main()
