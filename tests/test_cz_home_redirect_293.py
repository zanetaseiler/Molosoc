"""Issue #293: bare `/` -> Polylang CZ home 302 for Czech/Slovak browsers.

Static checks always run. Behavioural checks run the plugin's pure helper
functions in the real PHP (no WordPress needed); skipped if php is absent.
"""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "site/mu-plugins/molosoc-cz-home-redirect.php"
PLUGIN_SRC = PLUGIN.read_text(encoding="utf-8")
DEPLOY_WF = (ROOT / ".github/workflows/deploy-mu-plugins.yml").read_text(encoding="utf-8")
FRONT_PAGE = (ROOT / "site/theme/front-page.php").read_text(encoding="utf-8")

CZ_HOME = "https://molosoc.com/cz/molosoc-home-cestina/"
CHROME = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
BINGBOT = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
FACEBOOK = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
CURL = "curl/8.7.1"

PURE_FUNCTIONS = (
    "molosoc_cz_home_languages",
    "molosoc_cz_home_is_bare_home_path",
    "molosoc_cz_home_preferred_language",
    "molosoc_cz_home_is_bot",
    "molosoc_cz_home_should_redirect",
    "molosoc_cz_home_redirect_target",
)


def php_function_source(name):
    m = re.search(r"function %s\(.*?\n}\n" % re.escape(name), PLUGIN_SRC, re.S)
    assert m, name
    return m.group(0)


def php(code):
    src = "".join(php_function_source(n) for n in PURE_FUNCTIONS)
    return subprocess.run(["php", "-r", src + code], capture_output=True, text=True, check=True).stdout


def php_arg(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def bot_pattern():
    m = re.search(r"\$pattern = '~(.*?)~i';", PLUGIN_SRC)
    assert m
    return re.compile(m.group(1), re.I)


class StaticContract(unittest.TestCase):
    def test_plugin_header_and_hook(self):
        self.assertIn("Plugin Name: MOLOSOC CZ Home Redirect", PLUGIN_SRC)
        self.assertIn("add_action( 'plugins_loaded', 'molosoc_cz_home_maybe_redirect', 20 );", PLUGIN_SRC)
        self.assertIn("if ( ! defined( 'ABSPATH' ) )", PLUGIN_SRC)

    def test_bare_home_is_kept_out_of_the_page_cache_and_varies(self):
        self.assertIn("define( 'DONOTCACHEPAGE', true );", PLUGIN_SRC)
        self.assertIn("header( 'Vary: Accept-Language', false );", PLUGIN_SRC)
        self.assertIn("nocache_headers();", PLUGIN_SRC)

    def test_redirect_is_302_to_polylang_home_not_hard_coded(self):
        self.assertIn("wp_safe_redirect( $target, 302, 'MOLOSOC CZ Home Redirect' );", PLUGIN_SRC)
        self.assertIn("pll_home_url( MOLOSOC_CZ_HOME_POLYLANG_SLUG )", PLUGIN_SRC)
        self.assertIn("define( 'MOLOSOC_CZ_HOME_POLYLANG_SLUG', 'cz' );", PLUGIN_SRC)
        self.assertNotIn("molosoc-home-cestina", PLUGIN_SRC)

    def test_manual_choice_switcher_and_bots_are_respected(self):
        self.assertIn("defined( 'PLL_COOKIE' ) ? PLL_COOKIE : 'pll_language'", PLUGIN_SRC)
        self.assertIn("(bool) wp_get_referer()", PLUGIN_SRC)
        self.assertIn("array( 'GET', 'HEAD' )", PLUGIN_SRC)
        self.assertIn("return array( 'cs', 'sk' );", PLUGIN_SRC)

    def test_bot_pattern_matches_crawlers_not_browsers(self):
        pattern = bot_pattern()
        for ua in (GOOGLEBOT, BINGBOT, FACEBOOK, "Twitterbot/1.0", "Mozilla/5.0 (compatible; YandexBot/3.0)",
                   "Mozilla/5.0 (compatible; AhrefsBot/7.0)", "Chrome-Lighthouse", "Mozilla/5.0 (compatible; SemrushBot/7)"):
            self.assertTrue(pattern.search(ua), ua)
        for ua in (CHROME, CURL, "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/604.1",
                   "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"):
            self.assertFalse(pattern.search(ua), ua)

    def test_deploy_workflow_verifies_the_file(self):
        self.assertIn("need molosoc-cz-home-redirect.php", DEPLOY_WF)
        self.assertIn("need sitemap-404-status-fix.php", DEPLOY_WF)
        self.assertIn("need brevo-checkout-capture-shim.php", DEPLOY_WF)

    def test_front_page_script_still_covers_cz_cookie_holders(self):
        # The theme is deliberately untouched (evergreen guard in test_landing_xmas_251);
        # its client-side script keeps sending pll_language=cz direct entries to the CZ home.
        self.assertIn('<script id="molosoc-home-lang-redirect">', FRONT_PAGE)
        self.assertIn('window.location.replace( "%s" );' % CZ_HOME, FRONT_PAGE)


@unittest.skipUnless(shutil.which("php"), "php not installed")
class PhpBehaviour(unittest.TestCase):
    def preferred(self, header):
        return php("echo molosoc_cz_home_preferred_language(%s);" % php_arg(header))

    def bare(self, uri, home="/"):
        return php("echo molosoc_cz_home_is_bare_home_path(%s, %s) ? 'y' : 'n';" % (php_arg(uri), php_arg(home)))

    def should(self, accept, ua=CHROME, cookie=False, referer=False, method="GET"):
        args = ", ".join(php_arg(v) for v in (accept, ua, cookie, referer, method))
        return php("echo molosoc_cz_home_should_redirect(%s) ? 'y' : 'n';" % args)

    def target(self, home, query):
        return php("echo molosoc_cz_home_redirect_target(%s, %s);" % (php_arg(home), php_arg(query)))

    def test_preferred_language_takes_the_highest_q_entry(self):
        cases = {
            "cs-CZ,cs;q=0.9,en;q=0.8": "cs",
            "en-US,en;q=0.9,cs;q=0.8": "en",
            "cs": "cs",
            "CS-cz": "cs",
            "sk-SK,sk;q=0.9": "sk",
            "en;q=0.8,cs;q=0.9": "cs",
            " cs-cz ; q = 0.9 , en ; q=0.8": "cs",
            "en;q=0,cs;q=0.1": "cs",
            "cs;q=abc,en": "en",
            "de,cs;q=1": "de",
            "cs,en": "cs",
            "en,cs": "en",
            "*": "",
            "": "",
        }
        for header, expected in cases.items():
            self.assertEqual(self.preferred(header), expected, header)

    def test_only_the_bare_home_path_matches(self):
        for uri in ("/", "/?utm_source=test", "/?fbclid=abc&gclid=1"):
            self.assertEqual(self.bare(uri), "y", uri)
        for uri in ("", "/cz/", "/cz/molosoc-home-cestina/", "/foot-covers/", "/christmas-gift-molosoc/",
                    "/index.php", "/wp-json/wp/v2/pages", "/feed/", "/wp-sitemap.xml", "/checkout/", "/wp-admin/"):
            self.assertEqual(self.bare(uri), "n", uri)
        self.assertEqual(self.bare("/shop/", "/shop/"), "y")
        self.assertEqual(self.bare("/", "/shop/"), "n")

    def test_redirect_decision_matrix(self):
        cs = "cs-CZ,cs;q=0.9,en;q=0.8"
        self.assertEqual(self.should(cs), "y")
        self.assertEqual(self.should(cs, method="HEAD"), "y")
        self.assertEqual(self.should("sk-SK,sk;q=0.9,cs;q=0.8"), "y")
        self.assertEqual(self.should(cs, ua=CURL), "y")
        self.assertEqual(self.should("en-US,en;q=0.9,cs;q=0.8"), "n")
        self.assertEqual(self.should(""), "n")
        self.assertEqual(self.should(cs, cookie=True), "n")
        self.assertEqual(self.should(cs, referer=True), "n")
        self.assertEqual(self.should(cs, ua=GOOGLEBOT), "n")
        self.assertEqual(self.should(cs, ua=BINGBOT), "n")
        self.assertEqual(self.should(cs, ua=FACEBOOK), "n")
        self.assertEqual(self.should(cs, ua=""), "n")
        self.assertEqual(self.should(cs, method="POST"), "n")

    def test_query_string_is_kept(self):
        self.assertEqual(self.target(CZ_HOME, "utm_source=test"), CZ_HOME + "?utm_source=test")
        self.assertEqual(self.target(CZ_HOME, "?fbclid=x&gclid=y"), CZ_HOME + "?fbclid=x&gclid=y")
        self.assertEqual(self.target(CZ_HOME, ""), CZ_HOME)
        self.assertEqual(self.target(CZ_HOME + "?lang=cz", "utm_source=t"), CZ_HOME + "?lang=cz&utm_source=t")
        self.assertEqual(self.target("", "utm_source=t"), "")


if __name__ == "__main__":
    unittest.main()
