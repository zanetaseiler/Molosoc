"""Issue #287: Christmas landing (CZ + EN) — a buyer of 2-3 pairs who left pair 2+
without a size tapped "Pokračovat k pokladně" four times with no visible reaction
(Clarity, 2026-10-27). Static checks, no PHP/WordPress runtime: visible per-pair
labels on every width, size inheritance for new rows, red live error + outlined,
scrolled-to missing row, an unchanged server contract and a bumped theme version.
The behaviour itself was exercised in headless Chrome against a copy of the
picker markup (see the PR); these pins keep the pieces from drifting apart."""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
PART = (ROOT / "template-parts/landing-xmas.php").read_text(encoding="utf-8")
JS = (ROOT / "assets/js/landing-xmas.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-xmas.css").read_text(encoding="utf-8")
B_CSS = (ROOT / "assets/css/landing-b.css").read_text(encoding="utf-8")
INC = (ROOT / "inc/landing-xmas.php").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")


def strip_comments(src):
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


JS_CODE = strip_comments(JS)
CSS_CODE = strip_comments(CSS)


def block(css, selector):
    """Declarations of the first rule whose selector list contains `selector`."""
    m = re.search(re.escape(selector) + r"[^{]*\{([^}]*)\}", css)
    assert m, selector
    return m.group(1)


class PairLabels(unittest.TestCase):
    def test_copy_numbers_each_pair(self):
        self.assertIn("'pair_n'    => '%d. pár',", PART)
        self.assertIn("'pair_n'    => 'Pair %d',", PART)
        self.assertNotIn("'Pár %d'", PART)

    def test_legend_is_rendered_per_pair_row_with_its_own_class(self):
        self.assertIn('<legend class="lpb-buy__legend lpx-pair__legend">', PART)
        self.assertIn("sprintf( $t['pair_n'], $n )", PART)
        self.assertLess(PART.index('data-lpx-pair="<?php echo (int) $n; ?>"'), PART.index("lpx-pair__legend"))

    def test_landing_b_hides_legends_on_phones_and_xmas_undoes_it(self):
        # The cause of the invisible "pair 1 / pair 2" labels: B's sr-only legend at <=560px.
        mobile = B_CSS[B_CSS.index("@media (max-width: 560px)"):]
        self.assertRegex(mobile, r"\.lpb-buy__legend\s*\{[^}]*clip:\s*rect\(0 0 0 0\)")
        legend = block(CSS_CODE, ".lpx-pair .lpx-pair__legend")
        for decl in ("position: static", "width: 100%", "height: auto", "clip: auto", "overflow: visible"):
            self.assertIn(decl, legend, decl)
        # Loaded after landing-b.css, so the same-or-higher specificity wins.
        self.assertIn("array( 'molosoc-landing-b' ), $theme_version );", (ROOT / "functions.php").read_text(encoding="utf-8"))

    def test_size_cards_stay_compact_at_390(self):
        mobile = CSS_CODE[CSS_CODE.index("@media (max-width: 560px)"):]
        self.assertRegex(mobile, r"\.lpx-pair \.lpb-size__label\s*\{[^}]*padding:\s*0\.5em 0\.25em")
        self.assertRegex(mobile, r"\.lpx-pair \.lpx-pair__legend\s*\{[^}]*font-size:\s*0\.75rem")


class SizeInheritance(unittest.TestCase):
    def test_new_rows_inherit_pair_one_only_when_it_has_a_size(self):
        fn = JS_CODE[JS_CODE.index("function inherit"):JS_CODE.index("function render")]
        self.assertIn("if ( ! size || sizeOf( group, n ) )", fn)   # never overwrite, never from empty
        self.assertIn("radio.disabled", fn)                           # never a sold-out size
        handler = JS_CODE[JS_CODE.index('name.indexOf( "lpx-pairs-" ) === 0'):JS_CODE.index("sync( group );")]
        self.assertIn('getAttribute( "data-lpx-count" )', handler)
        self.assertIn("for ( var n = before + 1; n <= after; n++ )", handler)
        self.assertIn("inherit( group, n, first )", handler)

    def test_pair_one_picked_after_the_count_fills_empty_visible_rows(self):
        # The Clarity order: 2 pairs first, then M for pair 1.
        self.assertIn('row.getAttribute( "data-lpx-pair" ) === "1"', JS_CODE)
        self.assertIn("inherit( group, m, input.value )", JS_CODE)

    def test_render_tracks_the_count_for_the_next_change(self):
        self.assertIn('group.setAttribute( "data-lpx-count", String( count ) );', JS_CODE)


class MissingSizeFeedback(unittest.TestCase):
    def test_error_is_a_red_live_region_with_a_per_pair_message(self):
        self.assertIn('<p class="lpb-buy__error lpx-buy__error" role="alert" aria-live="assertive" aria-atomic="true"', PART)
        self.assertIn("'size_err_n' => 'Vyberte velikost pro %d. pár.',", PART)
        self.assertIn("'size_err_n' => 'Please choose a size for pair %d.',", PART)
        self.assertIn("data-lpx-err-pair=\"<?php echo esc_attr( $t['size_err_n'] ); ?>\"", PART)
        err = block(CSS_CODE, ".lpx-buy .lpb-buy__error")
        self.assertIn("color: #b3261e", err)  # 6.1:1 on #faf7f2, 6.5:1 on #fff
        self.assertIn("font-weight: 700", err)

    def test_click_marks_scrolls_and_announces(self):
        fn = JS_CODE[JS_CODE.index("function showMissing"):JS_CODE.index("function sync")]
        self.assertIn('fs.classList.add( "is-missing" )', fn)
        self.assertIn('tpl.replace( "%d", String( firstMissing ) )', fn)
        self.assertIn('err.textContent = "";', fn)  # re-set so the live region announces again
        self.assertIn('block: "center"', fn)
        self.assertIn('"(prefers-reduced-motion: reduce)"', fn)
        self.assertIn("preventScroll: true", fn)
        self.assertIn("showMissing( group, n );", JS_CODE)

    def test_missing_row_is_outlined_in_red(self):
        row = block(CSS_CODE, ".lpx-pair.is-missing")
        self.assertIn("border-color: #b3261e", row)
        base = re.search(r"\n\.lpx-pair \{([^}]*)\}", CSS_CODE).group(1)
        self.assertIn("border: 2px solid transparent", base)  # no layout jump when the outline appears

    def test_highlight_clears_on_the_next_pick(self):
        fn = JS_CODE[JS_CODE.index("function clearMissing"):JS_CODE.index("function showMissing")]
        self.assertIn('fs.classList.remove( "is-missing" )', fn)
        self.assertIn("err.hidden = true;", fn)
        sync = JS_CODE[JS_CODE.index("function sync"):JS_CODE.index("groups.forEach( function ( group ) {\n\t\trender")]
        self.assertIn("clearMissing( g );", sync)


class ContractUnchanged(unittest.TestCase):
    def test_url_contract_and_server_validation(self):
        self.assertIn('"molosoc_xmas=1&molosoc_xmas_sizes=" + encodeURIComponent( sizes.join( "," ) )', JS_CODE)
        self.assertNotRegex(JS_CODE, r"price|209|199|607|408")
        self.assertIn("array( 1 => 209, 2 => 199, 3 => 199 )", INC)
        self.assertIn("'M' !== $size && 'L' !== $size", INC)

    def test_no_js_fallback_is_the_product_page_link(self):
        self.assertIn('href="<?php echo esc_url( $lpx_url() ); ?>" data-lpx-go', PART)
        self.assertIn('if ( group.getAttribute( "data-lpx-enabled" ) !== "1" )', JS_CODE)

    def test_theme_version_bumped(self):
        version = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M)
        self.assertIsNotNone(version)
        self.assertGreaterEqual(tuple(int(v) for v in version.groups()), (0, 2, 103))


class CookieCard(unittest.TestCase):
    def test_wpconsent_is_compacted_via_parts_only_on_phones(self):
        mobile = CSS_CODE[CSS_CODE.index("@media (max-width: 560px)"):]
        self.assertIn("#wpconsent-container::part(wpconsent-banner)", mobile)
        self.assertIn("#wpconsent-container::part(wpconsent-button-accept)", mobile)
        # Styling only: no selector reaches into the plugin's shadow DOM or JS.
        self.assertNotIn("wpconsent-root", CSS_CODE)
        self.assertNotIn("wpconsent", JS_CODE.lower())


if __name__ == "__main__":
    unittest.main()
