"""Issue #301: on the two Christmas pages gtag.js (WooCommerce Google Analytics
Integration, handle `google-tag-manager`) is downloaded after the first screen:
the script tag becomes an inert placeholder plus a tiny loader that injects the
real script on the first interaction or load + idle. Static checks, no PHP or
WordPress runtime: gate (Christmas pages only, never cart/checkout/thank-you),
the filter contract, the loader's triggers, untouched inline gtag/consent code,
additive functions.php, theme version."""
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
INC = (ROOT / "inc/delayed-third-party.php").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")


def block(src, start, end):
    i = src.index(start)
    return src[i: src.index(end, i)]


def loader_js():
    fn = block(INC, "function molosoc_delayed_third_party_loader_js()", "\n}")
    return "".join(re.findall(r"'((?:[^'\\]|\\.)*)'", fn)).replace("\\'", "'")


class Gate(unittest.TestCase):
    def test_required_after_the_christmas_inc_without_removing_a_line(self):
        self.assertLess(FUNCTIONS.index("/inc/landing-xmas.php';"), FUNCTIONS.index("/inc/delayed-third-party.php';"))
        self.assertEqual(FUNCTIONS.count("require_once get_stylesheet_directory() . '/inc/delayed-third-party.php';"), 1)
        base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        if base:
            diff = subprocess.run(["git", "diff", "-U0", base, "--", "site/theme/functions.php"], cwd=REPO, capture_output=True, text=True).stdout
            self.assertEqual([l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")], [])

    def test_christmas_pages_only_never_cart_checkout_or_thank_you(self):
        fn = block(INC, "function molosoc_delayed_third_party_enabled()", "\n}")
        self.assertIn("is_cart()", fn)
        self.assertIn("is_checkout()", fn)
        self.assertIn("is_wc_endpoint_url( 'order-received' )", fn)
        self.assertIn("return false;", fn[: fn.index("$enabled =")])
        self.assertIn("$enabled = function_exists( 'molosoc_is_xmas_landing' ) && molosoc_is_xmas_landing();", fn)
        self.assertIn("apply_filters( 'molosoc_delayed_third_party_enabled', $enabled )", fn)
        self.assertNotIn("hydratacni-navleky-molosoc", INC)  # Landing B not included (one filter line if wanted)
        self.assertNotIn("1065", INC)
        self.assertNotIn("1066", INC)

    def test_only_the_gtag_handle_is_delayed(self):
        handles = block(INC, "function molosoc_delayed_third_party_handles()", "\n}")
        self.assertIn("array( 'google-tag-manager' )", handles)
        self.assertEqual(re.findall(r"'([a-z0-9_-]+)'", handles), ["molosoc_delayed_third_party_handles", "google-tag-manager"])
        code = block(INC, "defined( 'ABSPATH' )", "add_filter( 'script_loader_tag'")
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
        for untouched in ("facebook", "wpconsent", "clarity", "brevo", "sendinblue", "woocommerce-google-analytics-integration"):
            self.assertNotIn(untouched, code.lower(), untouched)


class TagFilter(unittest.TestCase):
    def test_runs_last_and_replaces_the_whole_tag_with_an_inert_placeholder(self):
        self.assertIn("add_filter( 'script_loader_tag', 'molosoc_delayed_third_party_tag', 100, 3 );", INC)
        fn = block(INC, "function molosoc_delayed_third_party_tag( $tag, $handle, $src = '' )", "\n}")
        self.assertIn("in_array( $handle, molosoc_delayed_third_party_handles(), true )", fn)
        self.assertIn("! molosoc_delayed_third_party_enabled()", fn)
        self.assertIn("return $tag;", fn)
        self.assertIn('\'<script type="text/plain" id="%s-js" data-molosoc-delayed-src="%s"></script>\'', fn)
        self.assertIn("esc_url( $src )", fn)
        self.assertIn("static $loader_printed = false;", fn)  # one loader per page
        self.assertIn("'<script id=\"molosoc-delayed-third-party-loader\">' . molosoc_delayed_third_party_loader_js() . '</script>'", fn)

    def test_loader_triggers_interaction_or_load_plus_idle_once(self):
        js = loader_js()
        self.assertIn('evs=["scroll","touchstart","pointerdown","keydown","mousemove"]', js)
        self.assertIn("if(done){return;}done=true;", js)
        self.assertIn('querySelectorAll("script[data-molosoc-delayed-src]")', js)
        self.assertIn('s.async=true;s.src=ps[i].getAttribute("data-molosoc-delayed-src");d.head.appendChild(s);', js)
        self.assertIn('if("requestIdleCallback" in w){w.requestIdleCallback(go,{timeout:2500});}else{w.setTimeout(go,2000);}', js)
        self.assertIn('if(d.readyState==="complete"){idle();}else{w.addEventListener("load",idle);}', js)
        self.assertIn("{passive:true}", js)
        self.assertLess(len(js), 800)
        # The loader never touches dataLayer/gtag/consent: those inline blocks keep running as before.
        for word in ("dataLayer", "gtag(", "consent"):
            self.assertNotIn(word, js, word)


class ThemeVersion(unittest.TestCase):
    def test_bumped(self):
        version = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M)
        self.assertGreaterEqual(tuple(int(v) for v in version.groups()), (0, 2, 108))


if __name__ == "__main__":
    unittest.main()
