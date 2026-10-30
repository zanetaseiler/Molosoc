"""Issue #177: the global sticky "Buy now" pill (Issue #73) is on every
public CZ/EN page except Cart/Checkout, the product (size) page it links
to, and the six legal pages; Landing Page A shows it at wider widths only,
where its own phone-only .molosoc-sticky-buy bar is hidden.

No PHP runtime needed. Asserts the functions.php / product.css contract:

* molosoc_sticky_cta_hidden() lists exactly the six legal slugs (EN + CZ)
  and no longer the Landing A pair, and still hides Cart/Checkout/product;
* the enqueue and the wp_head data print both go through that one gate;
* the pill links to molosoc_product_url() (the WooCommerce product page
  where the size is chosen) with the CZ/EN label;
* product.css hides .molosoc-sticky-cta at <=760px on the Landing A
  template only, and leaves the .molosoc-sticky-buy bar as it was;
* sticky-cta.js itself is unchanged (JS-injected, no template markup).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
FUNCTIONS = ROOT / "functions.php"
PRODUCT_CSS = ROOT / "assets/css/product.css"
COMPONENTS_CSS = ROOT / "assets/css/components.css"
STICKY_JS = ROOT / "assets/js/sticky-cta.js"

LEGAL_SLUGS = (
    "privacy-policies", "terms-of-services", "shipping-policy",
    "zasady-ochrany-osobnich-udaju", "obchodni-podminky", "zasady-dopravy",
)
LANDING_A_SLUGS = ("moisture-lock-foot-cover", "hydratacni-navlek-na-nohy")


def _function(src, name):
    a = src.index(f"function {name}()")
    b = src.index("\n}", a)
    return src[a:b]


def _strip_php_comments(src):
    return re.sub(r"^\s*//.*$", "", src, flags=re.M)


class StickyCtaGate(unittest.TestCase):
    def setUp(self):
        self.fn = FUNCTIONS.read_text(encoding="utf-8")
        self.gate = _function(self.fn, "molosoc_sticky_cta_hidden")
        self.gate_code = _strip_php_comments(self.gate)

    def test_legal_pages_are_hidden_in_both_languages(self):
        is_page = re.search(r"is_page\( array\((.*?)\) \)", self.gate_code, re.S)
        self.assertIsNotNone(is_page)
        slugs = re.findall(r"'([a-z0-9-]+)'", is_page.group(1))
        self.assertEqual(sorted(slugs), sorted(LEGAL_SLUGS))

    def test_landing_a_is_no_longer_in_the_gate(self):
        for slug in LANDING_A_SLUGS:
            self.assertNotIn(f"'{slug}'", self.gate_code)

    def test_cart_checkout_and_product_page_stay_hidden(self):
        self.assertIn("is_cart()", self.gate_code)
        self.assertIn("is_checkout()", self.gate_code)
        self.assertIn("is_product()", self.gate_code)

    def test_enqueue_and_data_print_share_the_gate(self):
        self.assertIn("if ( ! molosoc_sticky_cta_hidden() ) {\n\t\twp_enqueue_script( 'molosoc-sticky-cta'", self.fn)
        self.assertIn("\tif ( molosoc_sticky_cta_hidden() ) {\n\t\treturn;\n\t}", self.fn)
        # Exactly one enqueue of the handle; the data print lives in one gated
        # closure (Issue #299 added the filtered override print before the
        # default one, both after the gate's early return).
        self.assertEqual(self.fn.count("wp_enqueue_script( 'molosoc-sticky-cta'"), 1)
        self.assertEqual(self.fn.count("window.molosocStickyCta = %s;"), 2)
        closure = self.fn[self.fn.index("\tif ( molosoc_sticky_cta_hidden() ) {\n\t\treturn;\n\t}"):]
        closure = closure[: closure.index("\n} );")]
        self.assertEqual(closure.count("window.molosocStickyCta = %s;"), 2)
        self.assertIn("apply_filters( 'molosoc_sticky_cta_data', array(), $lang )", closure)

    def test_pill_links_to_the_size_page_with_the_language_label(self):
        self.assertIn("'url'   => molosoc_product_url( $lang ),", self.fn)
        self.assertIn("'label' => ( 'cz' === $lang ) ? 'Koupit nyní' : __( 'Buy now', 'molosoc' ),", self.fn)


class StickyCtaLandingA(unittest.TestCase):
    def setUp(self):
        self.css = PRODUCT_CSS.read_text(encoding="utf-8")

    def test_global_pill_hidden_at_phone_widths_on_landing_a_stylesheet(self):
        rule = (
            "@media (max-width: 760px) {\n"
            "  .molosoc-sticky-cta {\n"
            "    display: none;\n"
            "  }\n"
            "}\n"
        )
        self.assertEqual(self.css.count(rule), 1)
        # Bare selector (product.css loads only on the Landing A slugs); must not
        # depend on a page-template-* body class, and must stay inside the media query.
        self.assertNotIn("page-template-page-moisture-lock-foot-cover", self.css)
        self.assertNotRegex(self.css, r"(?m)^\.molosoc-sticky-cta\s*\{")

    def test_phone_bar_stays_as_it_was(self):
        self.assertIn(".molosoc-sticky-buy {\n  display: none;\n}", self.css)
        self.assertIn("  .molosoc-sticky-buy {\n    display: flex;\n    position: fixed;", self.css)
        # Same breakpoint as the pill hide, so exactly one of the two is visible.
        self.assertEqual(self.css.count("@media (max-width: 760px)"), self.css.count("@media (max-width: 760px) {"))

    def test_components_css_still_owns_the_pill_rule(self):
        components = COMPONENTS_CSS.read_text(encoding="utf-8")
        self.assertIn("\n.molosoc-sticky-cta {\n  position: fixed;", components)


class StickyCtaScript(unittest.TestCase):
    def test_js_is_injected_from_window_data_only(self):
        js = STICKY_JS.read_text(encoding="utf-8")
        self.assertIn("var data = window.molosocStickyCta;", js)
        self.assertIn('link.id = "molosoc-sticky-cta";', js)
        self.assertIn("link.href = data.url;", js)
        self.assertIn("document.body.appendChild( link );", js)


if __name__ == "__main__":
    unittest.main()
