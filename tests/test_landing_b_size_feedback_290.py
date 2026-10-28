"""Issue #290: Landing B (CZ) gets the Christmas picker's size feedback (#287 / PR #289).
A blocked "Pokračovat k pokladně" click used to unhide a muted error and focus an
opacity-0 radio, and the "Velikost" legend was sr-only on phones. Static pins; the
behaviour was exercised in headless Chrome against a copy of the buy-group markup."""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
BUY = (ROOT / "inc/landing-b-buy.php").read_text(encoding="utf-8")
JS = (ROOT / "assets/js/landing-b.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-b.css").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")


def strip_comments(src):
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


JS_CODE = strip_comments(JS)
CSS_CODE = strip_comments(CSS)
MOBILE = CSS_CODE[CSS_CODE.index("@media (max-width: 560px)"):]


def rule(css, selector):
    m = re.search(r"(?:^|\n)" + re.escape(selector) + r" \{([^}]*)\}", css)
    assert m, selector
    return m.group(1)


class VisibleLabel(unittest.TestCase):
    def test_legend_has_the_visible_class_and_the_generic_rule_stays(self):
        self.assertIn('<legend class="lpb-buy__legend lpb-buy__size-label"><?php echo esc_html( $copy['legend'] ); ?></legend>', BUY)
        self.assertRegex(MOBILE, r"\.lpb-buy__legend\s*\{[^}]*clip:\s*rect\(0 0 0 0\)")  # Christmas bundle legend relies on it
        label = rule(MOBILE, "  .lpb-buy__sizes .lpb-buy__size-label")
        for decl in ("position: static", "width: 100%", "height: auto", "clip: auto", "overflow: visible"):
            self.assertIn(decl, label, decl)

    def test_size_cards_stay_compact_on_phones(self):
        self.assertRegex(MOBILE, r"\.lpb-size__label\s*\{[^}]*padding:\s*0\.5em 0\.25em")


class MissingSizeFeedback(unittest.TestCase):
    def test_error_is_a_red_live_region(self):
        self.assertIn('<p class="lpb-buy__error" role="alert" aria-live="assertive" aria-atomic="true" hidden><?php echo esc_html( $copy['error'] ); ?></p>', BUY)
        err = rule(CSS_CODE, ".lpb-buy__error")
        self.assertIn("color: #b3261e", err)
        self.assertIn("font-weight: 700", err)

    def test_row_is_outlined_without_a_layout_jump(self):
        self.assertRegex(CSS_CODE, r"\n\.lpb-buy__sizes \{[^}]*border: 2px solid transparent")
        self.assertIn("border-color: #b3261e", rule(CSS_CODE, ".lpb-buy__sizes.is-missing"))
        self.assertIn("color: #ffb4ab", CSS_CODE)  # dark band variant stays legible

    def test_click_marks_scrolls_announces_and_focuses(self):
        fn = JS_CODE[JS_CODE.index("function showError"):JS_CODE.index("groups.forEach( function ( group ) {")]
        self.assertIn('row.classList.toggle( "is-missing", on )', fn)
        self.assertIn('err.textContent = "";', fn)
        self.assertIn('block: "center"', fn)
        self.assertIn('"(prefers-reduced-motion: reduce)"', fn)
        self.assertIn("preventScroll: true", fn)
        click = JS_CODE[JS_CODE.index("var picked = group.querySelector"):JS_CODE.index('var url = picked.getAttribute')]
        self.assertIn("showError( group, true );", click)
        self.assertNotIn("first.focus()", click)  # focus is showError's job, without a second scroll

    def test_a_pick_clears_every_group(self):
        change = JS_CODE[JS_CODE.index('group.addEventListener( "change"'):JS_CODE.index('var button = group.querySelector( "[data-lpb-checkout]" )')]
        self.assertIn("showError( g, false );", change)


class Unchanged(unittest.TestCase):
    def test_checkout_contract_and_no_js_fallback(self):
        self.assertIn("'molosoc_lpb'  => 'en' === $lang ? 'en' : 1,", BUY)
        self.assertIn("add_filter( 'woocommerce_add_to_cart_redirect'", BUY)
        self.assertNotIn("checked", BUY)  # still no preselected size
        self.assertIn('picked.getAttribute( "data-lpb-url" )', JS_CODE)
        self.assertIn("if ( busy )", JS_CODE)
        self.assertNotIn("jQuery", JS_CODE)

    def test_theme_version_bumped(self):
        version = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M)
        self.assertGreaterEqual(tuple(int(v) for v in version.groups()), (0, 2, 104))


if __name__ == "__main__":
    unittest.main()
