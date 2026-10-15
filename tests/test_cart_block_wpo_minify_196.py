"""Issue #196: the block cart (/cz/kosik/, /cart/) stayed in its skeleton state.

WP-Optimize Minify's "defer all JavaScript" adds `defer` to every local script
tag except those on its exclusion list, without consulting WordPress's
dependency graph. With wc-settings.js / wc-blocks-middleware.js excluded
(blocking) while every wp.* library stayed deferred, wc-settings.js threw
before defining wc.wcSettings and every WooCommerce block bundle after it
failed. WP-Optimize already skips the checkout page itself; the theme now opts
the cart (and, explicitly, the checkout) out through the plugin's supported
`wpo_minify_run_on_page` filter.

No PHP runtime is needed; these are static checks on functions.php.
"""
import re
import unittest
from pathlib import Path

FUNCTIONS = Path(__file__).resolve().parents[1] / "site/theme/functions.php"
FUNCTION_NAME = "molosoc_wpo_minify_skip_cart_checkout"


def function_body(src, name):
    match = re.search(r"function %s\s*\((.*?)\)\s*\{(.*?)\n\}" % re.escape(name), src, re.S)
    assert match, "%s() not found" % name
    return match.group(1), match.group(2)


class CartBlockWpoMinifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = FUNCTIONS.read_text(encoding="utf-8")

    def test_filter_is_registered_with_both_arguments(self):
        # WP-Optimize calls apply_filters('wpo_minify_run_on_page', $bool, $context);
        # the callback must be registered for 2 args at the default priority
        # so other plugins' later opinions still apply on non-cart pages.
        self.assertRegex(
            self.src,
            r"add_filter\(\s*'wpo_minify_run_on_page',\s*'%s',\s*10,\s*2\s*\);" % FUNCTION_NAME,
        )
        self.assertEqual(self.src.count("add_filter( 'wpo_minify_run_on_page'"), 1)

    def test_gate_skips_cart_and_checkout_and_passes_everything_else_through(self):
        params, body = function_body(self.src, FUNCTION_NAME)
        self.assertRegex(params, r"^\s*\$run_on_page,\s*\$context = 'default'\s*$")
        # Both WooCommerce conditionals, each guarded (the theme must not fatal
        # if WooCommerce is deactivated), each returning false.
        for tag in ("is_cart", "is_checkout"):
            self.assertRegex(
                body,
                r"if \( function_exists\( '%s' \) && %s\(\) \) \{\s*return false;\s*\}" % (tag, tag),
                "%s() must short-circuit to false" % tag,
            )
        # Non-cart pages keep WP-Optimize's own verdict untouched.
        self.assertRegex(body, r"return \$run_on_page;\s*$")
        self.assertNotIn("return true", body)

    def test_no_slug_based_gate(self):
        # The CZ twins (kosik/pokladna) must resolve through is_cart()/is_checkout()
        # (inc/woocommerce-lang.php filters), never through a hardcoded slug list
        # that would silently miss a renamed or EN page.
        _, body = function_body(self.src, FUNCTION_NAME)
        self.assertNotIn("is_page(", body)
        self.assertNotIn("kosik", body)

    def test_theme_does_not_touch_script_loader_tag(self):
        # The fix is the plugin-level opt-out, not a competing script_loader_tag
        # rewrite that would have to replicate WordPress's dependency logic.
        self.assertNotIn("add_filter( 'script_loader_tag'", self.src)
        self.assertNotIn("wpo_minify_defer_or_async", self.src)


if __name__ == "__main__":
    unittest.main()
