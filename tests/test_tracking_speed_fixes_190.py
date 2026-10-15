"""Issue #190: three technical fixes from the Oct 14 Meta Ads + Clarity review.

No PHP runtime is needed; these are static checks on functions.php plus a
behavioural check of the Thrive-toast regex against the snippet captured from
the live site.

1. Clarity consent replay — the stored WPConsent decision is sent to Clarity's
   Consent API v2 on every page load (wp_head priority 11, right after the
   Microsoft Clarity plugin's priority-10 stub) and again on the banner's
   `wpconsent_consent_saved` event; each storage flag is 'granted' only for
   its own accepted category, otherwise 'denied'; no call without a stored
   decision.
2. Landing Page A first paint — the page joins the no-plugin-markup gate (so
   the Customer Reviews / WooCommerce / Comgate / select2 / PhotoSwipe / PPL
   stacks and jQuery are dequeued there like on B), its hero still is
   preloaded with fetchpriority="high", and the Google Fonts stylesheet is
   printed non-blocking. Nothing in the template changes.
3. "jQuery is not defined" — on the gated pages jQuery is dequeued explicitly
   (it was already absent through the broken `jquery` alias), the two scripts
   that call jQuery without declaring it are handled: WooCommerce's
   woocommerce-analytics-client bundle is dequeued and Thrive's handle-less
   inline toast script is stripped from the buffered wp_footer output.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
FUNCTIONS = ROOT / "functions.php"
TEMPLATE_A = ROOT / "page-moisture-lock-foot-cover.php"
STILL = "https://molosoc.com/wp-content/uploads/2026/10/molosoc-hero-still.webp"
A_PAIR = "array( 'moisture-lock-foot-cover', 'hydratacni-navlek-na-nohy' )"

# Captured verbatim from the live CZ Landing A footer on 2026-10-14 (the
# WPConsent-wrapped form; the raw form Thrive prints has a plain <script> tag).
THRIVE_TOAST = """<script type='text/plain' data-wpconsent-name="thrive-leads" data-wpconsent-category="marketing">( $ => {
\t/**
\t * Displays toast message from storage, it is used when the user is redirected after login
\t */
\tif ( window.sessionStorage ) {
\t\t$( window ).on( 'tcb_after_dom_ready', () => {
\t\t\tconst message = sessionStorage.getItem( 'tcb_toast_message' );

\t\t\tif ( message ) {
\t\t\t\ttcbToast( sessionStorage.getItem( 'tcb_toast_message' ), false );
\t\t\t\tsessionStorage.removeItem( 'tcb_toast_message' );
\t\t\t}
\t\t} );
\t}

\tfunction tcbToast( message, error, callback ) {
\t\tif ( typeof message !== 'string' ) {
\t\t\tmessage = message.message || message.error || message.success;
\t\t}
\t\tif ( ! error ) {
\t\t\terror = false;
\t\t}
\t\tTCB_Front.notificationElement.toggle( message, error ? 'error' : 'success', callback );
\t}
} )( typeof ThriveGlobal === 'undefined' ? jQuery : ThriveGlobal.$j );
</script>"""


def _block(src, start, end_marker, offset=0):
    a = src.index(start, offset)
    b = src.index(end_marker, a + len(start))
    return src[a:b]


def _php_regex_to_python(php_literal):
    """'#…#s' PHP single-quoted PCRE literal -> compiled Python pattern."""
    assert php_literal.startswith("'#") and php_literal.endswith("#s'"), php_literal
    body = php_literal[2:-3].replace("\\'", "'")
    return re.compile(body, re.S)


class TrackingSpeedFixesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fn = FUNCTIONS.read_text(encoding="utf-8")
        cls.tpl = TEMPLATE_A.read_text(encoding="utf-8")

    # --- 1. Clarity consent replay -------------------------------------
    def test_clarity_consent_replay_runs_after_the_plugin_stub_on_every_page(self):
        fn = self.fn
        self.assertEqual(fn.count("function molosoc_clarity_consent_replay()"), 1)
        self.assertIn("add_action( 'wp_head', 'molosoc_clarity_consent_replay', 11 );", fn)
        body = _block(fn, "function molosoc_clarity_consent_replay()", "add_action( 'wp_head', 'molosoc_clarity_consent_replay', 11 );")
        # Unconditional: every front-end page, no slug or template gate.
        self.assertNotIn("is_page(", body)
        self.assertNotIn("is_front_page(", body)
        # Raw <script> on wp_head (WP-Optimize-safe), never an enqueue.
        self.assertIn("<script>", body)
        self.assertNotIn("wp_add_inline_script", body)
        self.assertNotIn("wp_enqueue_script", body)

    def test_clarity_consent_values_follow_the_stored_wpconsent_decision(self):
        body = _block(self.fn, "function molosoc_clarity_consent_replay()", "add_action( 'wp_head', 'molosoc_clarity_consent_replay', 11 );")
        self.assertIn("wpconsent_preferences", body)
        self.assertIn("w.clarity('consentv2', {", body)
        self.assertIn("ad_Storage: p.marketing ? 'granted' : 'denied'", body)
        self.assertIn("analytics_Storage: p.statistics ? 'granted' : 'denied'", body)
        # 'granted' only ever appears inside those two per-category ternaries.
        self.assertEqual(body.count("'granted'"), 2)
        # No stored decision -> no call (signal() bails on a non-object).
        self.assertIn("if (!p || typeof p !== 'object') { return; }", body)
        self.assertIn("if (parts.length === 2) {", body)
        # The click path is re-sent on WPConsent's own event, same signal().
        self.assertIn("w.addEventListener('wpconsent_consent_saved', function (e) { signal(e.detail); });", body)
        # Same stub shape as Clarity's own snippet, so a call before the tag
        # loads is queued, never lost.
        self.assertIn("w.clarity = w.clarity || function () { (w.clarity.q = w.clarity.q || []).push(arguments); };", body)

    # --- 2. Landing Page A first paint ---------------------------------
    def test_landing_a_joins_the_no_plugin_markup_gate(self):
        fn = self.fn
        self.assertEqual(fn.count("function molosoc_is_landing_page_a()"), 1)
        helper = _block(fn, "function molosoc_is_landing_page_a()", "\n}")
        self.assertIn(f"return is_page( {A_PAIR} );", helper)
        gate = _block(fn, "function molosoc_page_without_plugin_markup()", "\n}")
        self.assertIn("is_front_page()", gate)
        self.assertIn("is_page( 'hydratacni-navleky-molosoc' )", gate)
        self.assertIn("molosoc_is_landing_page_a()", gate)
        # The B-only extended script list (WooCommerce core frontend, Customer
        # Reviews masonry, PPL map) now covers A as well.
        dq = _block(fn, "function molosoc_dequeue_unused_homepage_assets()", "add_action( 'wp_print_footer_scripts', 'molosoc_dequeue_unused_homepage_assets', 1 );")
        self.assertIn("if ( is_page( 'hydratacni-navleky-molosoc' ) || molosoc_is_landing_page_a() ) {", dq)
        for handle in ("'woocommerce'", "'cr-colcade'", "'pplcz_map_js'", "'pplcz_parcelshop-old-view'"):
            self.assertIn(handle, dq, handle)
        # Order attribution still survives everywhere.
        self.assertNotIn("'wc-order-attribution'", dq)
        self.assertNotIn("'sourcebuster-js'", dq)

    def test_landing_a_head_preloads_the_hero_still_and_unblocks_fonts(self):
        fn = self.fn
        self.assertEqual(fn.count("function molosoc_landing_a_head()"), 1)
        self.assertIn("add_action( 'wp_head', 'molosoc_landing_a_head', 1 );", fn)
        head = _block(fn, "function molosoc_landing_a_head()", "add_action( 'wp_head', 'molosoc_landing_a_head', 1 );")
        self.assertIn("if ( ! molosoc_is_landing_page_a() ) {", head)
        self.assertIn('<link rel="preload" as="image" fetchpriority="high" href="%s">', head)
        self.assertIn("esc_url( molosoc_landing_a_hero_still_url() )", head)
        self.assertIn("""'<link rel="stylesheet" href="%1$s" media="print" onload="this.media=\\'all\\'">'""", head)
        self.assertIn("""'<noscript><link rel="stylesheet" href="%1$s"></noscript>'""", head)
        self.assertIn("esc_url( molosoc_fonts_url() )", head)
        # One font URL source for the whole theme (the Landing B test pins the
        # literal count at 2: molosoc_fonts_url() + molosoc_landing_b_fonts_url()).
        self.assertNotIn("fonts.googleapis.com", head)
        # The preloaded URL is byte-identical to the template's <img src>.
        self.assertIn(f"return '{STILL}';", _block(fn, "function molosoc_landing_a_hero_still_url()", "\n}"))
        self.assertIn(f'src="{STILL}"', self.tpl)
        # The blocking handle is dequeued in A's enqueue branch only.
        branch = _block(fn, "} elseif ( is_page( " + A_PAIR + " ) ) {", "} elseif (", 0)
        self.assertIn("wp_dequeue_style( 'molosoc-fonts' );", branch)
        self.assertEqual(fn.count("wp_dequeue_style( 'molosoc-fonts' );"), 2)  # A + B

    def test_landing_a_template_is_untouched_by_this_issue(self):
        # Technical-only constraint (Meta A/B test until Oct 18): the hero
        # <img> keeps its exact attributes and no preload/font markup moved
        # into the template.
        tag = re.search(r"<img\s+class=\"molosoc-orbit-model\".*?>", self.tpl, re.S).group(0)
        for attr in (f'src="{STILL}"', 'alt=""', 'width="1440"', 'height="1440"', 'fetchpriority="high"', 'decoding="async"'):
            self.assertIn(attr, tag)
        self.assertNotIn("rel=\"preload\"", self.tpl)
        self.assertNotIn("fonts.googleapis.com", self.tpl)

    # --- 3. "jQuery is not defined" -------------------------------------
    def test_jquery_and_its_undeclared_callers_are_handled_on_the_gated_pages(self):
        dq = _block(self.fn, "function molosoc_dequeue_unused_homepage_assets()", "add_action( 'wp_print_footer_scripts', 'molosoc_dequeue_unused_homepage_assets', 1 );")
        scripts = _block(dq, "$scripts = array(", ");")
        for handle in ("'jquery'", "'jquery-core'", "'jquery-migrate'", "'woocommerce-analytics-client'", "'tve-dash-frontend'"):
            self.assertIn(handle, scripts, handle)
        # Dequeue AND deregister, as for every other handle in the list.
        self.assertIn("wp_dequeue_script( $handle );", dq)
        self.assertIn("wp_deregister_script( $handle );", dq)

    def test_thrive_toast_script_is_stripped_from_wp_footer_on_the_gated_pages_only(self):
        fn = self.fn
        self.assertIn("add_action( 'wp_footer', 'molosoc_footer_buffer_start', PHP_INT_MIN );", fn)
        self.assertIn("add_action( 'wp_footer', 'molosoc_footer_buffer_end', PHP_INT_MAX );", fn)
        start = _block(fn, "function molosoc_footer_buffer_start()", "\n}")
        self.assertIn("if ( ! molosoc_page_without_plugin_markup() ) {", start)
        self.assertIn("ob_start();", start)
        end = _block(fn, "function molosoc_footer_buffer_end()", "\n}")
        self.assertIn("ob_get_level() !== $GLOBALS['molosoc_footer_buffer_level']", end)
        self.assertIn("echo molosoc_strip_thrive_toast_script( ob_get_clean() );", end)

    def test_thrive_toast_regex_matches_the_live_snippet_and_nothing_else(self):
        strip = _block(self.fn, "function molosoc_strip_thrive_toast_script( $html )", "\n}")
        literal = re.search(r"'#.*?#s'", strip, re.S).group(0)
        pattern = _php_regex_to_python(literal)

        raw_tag = THRIVE_TOAST.replace(
            """<script type='text/plain' data-wpconsent-name="thrive-leads" data-wpconsent-category="marketing">""",
            "<script>",
        )
        keep = (
            '<script type="speculationrules">{"prefetch":[]}</script>\n'
            '<input id=\'ws_ma_event_type\' type=\'hidden\' />'
            '<script>window.molosocX = ( $ => { return $; } )( 1 );</script>\n'
            "<script>( $ => { $('tcb_toast_message'); } )( jQuery );</script>\n"  # no ThriveGlobal closer
            '<script id="wpo_min-footer-6-js" src="https://example.test/wpconsent.min.js"></script>'
        )
        for variant in (THRIVE_TOAST, raw_tag):
            html = keep.replace("</script>\n<input", "</script>\n" + variant + "\n<input", 1)
            self.assertIn("tcb_after_dom_ready", html)
            out = pattern.sub("", html)
            self.assertNotIn("tcb_after_dom_ready", out)
            self.assertNotIn("ThriveGlobal", out)
            # Every other node survives byte for byte.
            self.assertEqual(out, keep)
        # Never crosses a </script> boundary: a toast opener without its own
        # closer must not swallow the following scripts.
        orphan = "<script>( $ => { tcb_toast_message; } )( jQuery );</script>\n<script>ThriveGlobal.$j );</script>"
        self.assertEqual(pattern.sub("", orphan), orphan)
        # Idempotent on an already clean footer.
        self.assertEqual(pattern.sub("", keep), keep)

    def test_landing_b_gate_tripwire_count_includes_the_new_helper(self):
        # test_landing_b_template.py pins the literal pair count; the helper
        # added here is the third copy (preconnect hints, product.css branch,
        # molosoc_is_landing_page_a()).
        self.assertEqual(self.fn.count(A_PAIR), 3)


if __name__ == "__main__":
    unittest.main()
