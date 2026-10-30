"""Issue #299: on the two Christmas pages the site-wide sticky pill must not leave
the page (order #1073 tapped "Koupit nyní", landed on the regular product page
and paid 229 Kč instead of 209 Kč). Static checks, no PHP/WordPress runtime:
the pill data is overridden through a filter inside the same gated wp_head
closure, the Christmas inc returns #lpx-bundle + its label, landing-xmas.js
smooth-scrolls and hides the pill over the buy box, every other page and
sticky-cta.js are untouched."""
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
INC = (ROOT / "inc/landing-xmas.php").read_text(encoding="utf-8")
PART = (ROOT / "template-parts/landing-xmas.php").read_text(encoding="utf-8")
JS = (ROOT / "assets/js/landing-xmas.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-xmas.css").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")


def strip_comments(src):
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


JS_CODE = strip_comments(JS)
PART_CODE = strip_comments(PART)


def block(src, start, end):
    i = src.index(start)
    return src[i: src.index(end, i)]


class PillData(unittest.TestCase):
    def closure(self):
        return block(FUNCTIONS, "\tif ( molosoc_sticky_cta_hidden() ) {\n\t\treturn;\n\t}", "\n} );")

    def test_override_is_filtered_inside_the_gated_closure_and_defaults_fall_through(self):
        c = self.closure()
        self.assertIn("$molosoc_sticky_cta_override = apply_filters( 'molosoc_sticky_cta_data', array(), $lang );", c)
        self.assertIn("if ( ! empty( $molosoc_sticky_cta_override['url'] ) && ! empty( $molosoc_sticky_cta_override['label'] ) ) {", c)
        self.assertIn("wp_json_encode( $molosoc_sticky_cta_override ) );\n\t\treturn;", c)
        # The default print (product URL + Koupit nyní / Buy now) is still there, after the override.
        self.assertLess(c.index("$molosoc_sticky_cta_override"), c.index("'url'   => molosoc_product_url( $lang ),"))
        self.assertIn("'label' => ( 'cz' === $lang ) ? 'Koupit nyní' : __( 'Buy now', 'molosoc' ),", c)
        self.assertEqual(FUNCTIONS.count("molosoc_sticky_cta_data"), 1)  # applied once, in this closure

    def test_christmas_pages_point_the_pill_at_the_picker(self):
        fn = block(INC, "function molosoc_xmas_sticky_cta( $data, $lang = '' )", "add_filter( 'molosoc_sticky_cta_data'")
        self.assertIn("$page_lang = molosoc_xmas_current_lang();", fn)   # helper, not hard-coded IDs
        self.assertIn("return $data;", fn)                                # every other page: untouched
        self.assertIn("'url'   => '#lpx-bundle',", fn)
        self.assertIn("'label' => 'en' === $page_lang ? 'Choose gift set' : 'Vybrat dárkový set',", fn)
        self.assertIn("add_filter( 'molosoc_sticky_cta_data', 'molosoc_xmas_sticky_cta', 10, 2 );", INC)
        self.assertIn('id="lpx-bundle"', PART)
        self.assertIn('href="#lpx-bundle"', PART)  # the hero button shares the target

    def test_functions_php_only_gained_lines_and_sticky_js_is_untouched(self):
        base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        if not base:
            self.skipTest("no origin/main")
        diff = subprocess.run(["git", "diff", "-U0", base, "--", "site/theme/functions.php"], cwd=REPO, capture_output=True, text=True).stdout
        self.assertEqual([l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")], [])
        changed = subprocess.run(["git", "diff", "--name-only", base, "--", "site/theme/assets/js/sticky-cta.js", "site/theme/assets/css/components.css", "site/theme/assets/css/landing-b.css", "site/theme/assets/css/product.css"], cwd=REPO, capture_output=True, text=True).stdout.split()
        self.assertEqual(changed, [])


class PillBehaviour(unittest.TestCase):
    def test_click_scrolls_in_page_and_keeps_the_url(self):
        fn = block(JS_CODE, "function wirePill()", "if ( ! wirePill() ) {")
        self.assertIn('document.getElementById( "molosoc-sticky-cta" )', fn)
        self.assertIn('document.getElementById( "lpx-bundle" )', fn)
        self.assertIn('indexOf( "#lpx-bundle" ) === -1', fn)      # only the Christmas pill is wired
        self.assertIn("e.preventDefault();", fn)                  # no navigation, no hash change
        self.assertIn('behavior: reduce ? "auto" : "smooth", block: "start"', fn)
        self.assertIn('"(prefers-reduced-motion: reduce)"', fn)
        self.assertIn('window.addEventListener( "load", wirePill );', JS_CODE)

    def test_pill_hides_while_a_buy_box_is_on_screen(self):
        fn = block(JS_CODE, "function wirePill()", "if ( ! wirePill() ) {")
        self.assertIn("new IntersectionObserver(", fn)
        self.assertIn('pill.classList.toggle( "lpx-pill-hidden", any );', fn)
        self.assertIn("groups.forEach( function ( g ) {\n\t\t\t\tio.observe( g );", fn)  # both pickers
        self.assertIn('var groups = Array.prototype.slice.call( document.querySelectorAll( "[data-lpx-buy]" ) );', JS_CODE)
        hidden = re.search(r"\.molosoc-sticky-cta\.lpx-pill-hidden \{([^}]*)\}", CSS).group(1)
        for decl in ("opacity: 0", "visibility: hidden", "pointer-events: none"):
            self.assertIn(decl, hidden, decl)
        self.assertIn("#lpx-bundle { scroll-margin-top: 0.75rem; }", CSS)

    def test_checkout_contract_and_fallback_unchanged(self):
        self.assertIn('"molosoc_xmas=1&molosoc_xmas_sizes=" + encodeURIComponent( sizes.join( "," ) )', JS_CODE)
        self.assertNotRegex(JS_CODE, r"price|209|199|607|408")
        self.assertIn("array( 1 => 209, 2 => 199, 3 => 199 )", INC)
        # The only product-page link left in the template is the no-JS fallback of the checkout button.
        self.assertEqual(PART_CODE.count("$lpx_url()"), 1)
        self.assertIn('href="<?php echo esc_url( $lpx_url() ); ?>" data-lpx-go', PART_CODE)
        self.assertNotIn("molosoc_product_url", PART_CODE.replace("return molosoc_product_url( $lpx_lang );", ""))


class ThemeVersion(unittest.TestCase):
    def test_bumped(self):
        version = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M)
        self.assertGreaterEqual(tuple(int(v) for v in version.groups()), (0, 2, 107))


if __name__ == "__main__":
    unittest.main()
