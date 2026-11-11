"""Issue #314: Christmas landing (CZ + EN) — Clarity (30-31 Oct 2026, mobile,
Facebook in-app browser) showed dead taps on the hero photo and taps on the
English cookie-banner text on the Czech page. Static checks, no PHP/WordPress
runtime: the hero and story photos are links to the picker scrolled like the
sticky pill (URL unchanged, plain jump under prefers-reduced-motion), the
WPConsent wording is Czech on Polylang CZ front-end requests through the
plugin's own option filter, the Christmas ≤560px banner shows Accept/Reject as
two equal 44px buttons with Preferences as a text link, nothing consent-related
is touched, functions.php only gained lines, theme version bumped. The
rendering itself was measured in headless Chrome at 390x844 (see the PR)."""
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
PART = (ROOT / "template-parts/landing-xmas.php").read_text(encoding="utf-8")
JS = (ROOT / "assets/js/landing-xmas.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-xmas.css").read_text(encoding="utf-8")
INC = (ROOT / "inc/wpconsent-lang.php").read_text(encoding="utf-8")
INC_XMAS = (ROOT / "inc/landing-xmas.php").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")


def strip_comments(src):
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


JS_CODE = strip_comments(JS)
INC_CODE = strip_comments(INC)
CSS_CODE = strip_comments(CSS)
MOBILE = CSS_CODE[CSS_CODE.index("@media (max-width: 560px)"):]
MOBILE = MOBILE[: MOBILE.index("@media", 1)]  # the first ≤560px block only (picker + cookie card)


def rule(css, selector):
    """Declarations of the rule whose whole selector text equals `selector` (whitespace-insensitive)."""
    want = re.sub(r"\s+", " ", selector).strip()
    for m in re.finditer(r"([^{}]*)\{([^}]*)\}", css):
        if re.sub(r"\s+", " ", m.group(1)).strip() == want:
            return m.group(2)
    raise AssertionError(selector)


def section(src, start, end):
    i = src.index(start)
    return src[i: src.index(end, i)]


def merge_base():
    return subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=REPO, capture_output=True, text=True).stdout.strip()


class HeroLink(unittest.TestCase):
    LINK = 'href="#lpx-bundle" aria-label="<?php echo esc_attr( $t[\'pick\'] ); ?>" data-lpx-to-picker>'

    def test_hero_photo_is_a_link_to_the_picker(self):
        self.assertIn('<div class="lpx-hero__media"><a class="lpx-hero__link" ' + self.LINK + "<?php echo $lpx_hero_img;", PART)
        self.assertIn("?></a></div>", PART)

    def test_both_story_photos_link_the_same_way(self):
        self.assertEqual(PART.count('<div class="lpx-figure"><a class="lpx-figure__link" ' + self.LINK), 2)
        self.assertIn("<?php echo $lpx_s2; // phpcs:ignore WordPress.Security.EscapeOutput ?></a></div>", PART)
        self.assertIn("<?php echo $lpx_s3; // phpcs:ignore WordPress.Security.EscapeOutput ?></a></div>", PART)

    def test_accessible_name_is_the_pill_label_in_each_language(self):
        self.assertIn("'pick'      => 'Vybrat dárkový set',", section(PART, "'cz' => array(", "'en' => array("))
        self.assertIn("'pick'      => 'Choose gift set',", section(PART, "'en' => array(", "$t = $copy[ $lpx_lang ];"))
        self.assertIn("'en' === $page_lang ? 'Choose gift set' : 'Vybrat dárkový set'", INC_XMAS)  # same words as the sticky pill

    def test_image_alt_texts_are_kept(self):
        self.assertIn("molosoc_xmas_image( 'scene-01', 'cz' === $lpx_lang ? 'Vánoční dárek MOLOSOC' : 'MOLOSOC Christmas gift', 'fetchpriority=\"high\" loading=\"eager\"' )", PART)
        self.assertIn("'Dárek s návleky MOLOSOC' : 'A gift with MOLOSOC foot covers'", PART)
        self.assertIn("'Vánoční dárek MOLOSOC, detail' : 'MOLOSOC Christmas gift, detail'", PART)

    def test_same_target_as_the_hero_button_and_the_pill(self):
        self.assertIn('<a class="lpb-btn" href="#lpx-bundle">', PART)
        self.assertIn("'url'   => '#lpx-bundle',", INC_XMAS)
        self.assertIn('<section class="lpb-section lpb-section--cream" id="lpx-bundle"', PART)


class HeroScroll(unittest.TestCase):
    def test_photo_links_and_pill_share_one_scroll_handler(self):
        self.assertIn('document.querySelectorAll( "a[data-lpx-to-picker]" )', JS_CODE)
        self.assertIn('link.addEventListener( "click", goToPicker );', JS_CODE)
        self.assertIn('pill.addEventListener( "click", goToPicker );', JS_CODE)
        self.assertEqual(JS_CODE.count('behavior: reduce ? "auto" : "smooth", block: "start"'), 1)

    def test_handler_keeps_the_url_and_respects_reduced_motion(self):
        go = section(JS_CODE, "function goToPicker( e )", "function wirePill()")
        self.assertIn('document.getElementById( "lpx-bundle" )', go)
        self.assertIn("e.preventDefault();", go)
        self.assertNotIn("location.hash", go)
        self.assertNotIn("pushState", go)
        self.assertIn('"(prefers-reduced-motion: reduce)"', go)
        self.assertIn('behavior: reduce ? "auto" : "smooth", block: "start"', go)
        self.assertIn("window.scrollTo( 0, target.getBoundingClientRect().top + window.pageYOffset );", go)  # no scrollIntoView fallback

    def test_without_a_picker_the_plain_anchor_is_left_alone(self):
        go = section(JS_CODE, "function goToPicker( e )", "function wirePill()")
        self.assertLess(go.index("if ( ! target ) {\n\t\t\treturn;"), go.index("e.preventDefault();"))


class HeroStyle(unittest.TestCase):
    def test_pointer_and_focus_ring_are_the_only_visual_change(self):
        base = rule(CSS_CODE, ".lpx-hero__link, .lpx-figure__link")
        self.assertIn("display: block", base)
        self.assertIn("cursor: pointer", base)
        focus = rule(CSS_CODE, ".lpx-hero__link:focus-visible, .lpx-figure__link:focus-visible")
        self.assertIn("outline: 2px solid #000", focus)
        for decl in ("opacity", "transform", "filter", "border", "background"):
            self.assertNotIn(decl, base + focus, decl)

    def test_picker_heading_lands_clear_of_the_top_edge(self):
        self.assertIn("#lpx-bundle { scroll-margin-top: 0.75rem; }", CSS_CODE)

    def test_hero_image_rules_still_apply_through_the_link(self):
        self.assertIn(".lpx-hero__media img { display: block; width: 100%; height: auto; }", CSS_CODE)
        self.assertIn(".lpx-figure img { display: block; width: 100%; height: auto; }", CSS_CODE)


class CookieBannerCzech(unittest.TestCase):
    CZ = {
        "banner_message": "Používáme cookies, abychom vám web zlepšili a změřili, jak funguje naše reklama.",
        "accept_button_text": "Přijmout vše",
        "cancel_button_text": "Odmítnout",
        "preferences_button_text": "Nastavení",
    }

    def test_required_additively_from_functions_php(self):
        line = "require_once get_stylesheet_directory() . '/inc/wpconsent-lang.php';"
        self.assertEqual(FUNCTIONS.count(line), 1)
        self.assertLess(FUNCTIONS.index("/inc/checkout-cleanup.php';"), FUNCTIONS.index(line))
        base = merge_base()
        if base:
            diff = subprocess.run(["git", "diff", "-U0", base, "--", "site/theme/functions.php"], cwd=REPO, capture_output=True, text=True).stdout
            self.assertEqual([l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")], [])

    def test_exactly_the_four_banner_wording_options_with_zanetas_copy(self):
        strings = section(INC, "function molosoc_wpconsent_cz_strings()", "\n}")
        found = dict(re.findall(r"'([a-z_]+)'\s*=> '([^']*)'", strings))
        self.assertEqual(found, self.CZ)
        self.assertIn("add_filter( 'wpconsent_get_option_' . $molosoc_wpconsent_option, 'molosoc_wpconsent_cz_option', 10, 2 );", INC)
        self.assertIn("foreach ( array_keys( molosoc_wpconsent_cz_strings() ) as $molosoc_wpconsent_option )", INC)

    def test_czech_only_on_polylang_cz_front_end_requests(self):
        gate = section(INC, "function molosoc_wpconsent_is_cz_request()", "\n}")
        for guard in ("is_admin()", "wp_doing_ajax()", "wp_doing_cron()", "defined( 'REST_REQUEST' ) && REST_REQUEST"):
            self.assertIn(guard, gate, guard)
        self.assertIn("return function_exists( 'pll_current_language' ) && 'cz' === pll_current_language();", gate)
        cb = section(INC, "function molosoc_wpconsent_cz_option(", "\n}")
        self.assertIn("if ( ! isset( $strings[ $option_name ] ) || ! molosoc_wpconsent_is_cz_request() ) {\n\t\treturn $value;", cb)  # EN pages keep the admin values

    def test_no_consent_logic_is_touched(self):
        for forbidden in ("default_allow", "default_checked", "button_enabled", "enable_consent_banner", "wpconsent_preferences", "setcookie", "update_option", "wpconsent_save_options", "wpconsent_banner_output"):
            self.assertNotIn(forbidden, INC_CODE, forbidden)
        self.assertNotIn("wpconsent", strip_comments(JS).lower())
        self.assertNotIn("wpconsent", PART.lower())


class CookieBannerMobile(unittest.TestCase):
    def test_accept_and_reject_are_two_equal_44px_buttons_side_by_side(self):
        pair = rule(MOBILE, "#wpconsent-container::part(wpconsent-button-accept), #wpconsent-container::part(wpconsent-button-cancel)")
        for decl in ("flex: 1 1 0", "min-width: 0", "height: 44px", "font-size: 0.875rem", "font-weight: 600"):
            self.assertIn(decl, pair, decl)
        self.assertIn("order: 1", rule(MOBILE, "#wpconsent-container::part(wpconsent-button-accept)"))
        self.assertIn("order: 2", rule(MOBILE, "#wpconsent-container::part(wpconsent-button-cancel)"))
        footer = rule(MOBILE, "#wpconsent-container::part(wpconsent-banner-footer)")
        self.assertIn("flex-direction: row", footer)  # the plugin stacks the buttons (column) at <=767px
        self.assertIn("flex-wrap: wrap", footer)

    def test_preferences_is_a_small_text_link_on_its_own_row_below(self):
        prefs = rule(MOBILE, "#wpconsent-container::part(wpconsent-button-preferences)")
        for decl in ("order: 3", "flex: 0 0 100%", "height: auto", "border: 0", "background: transparent", "text-decoration: underline", "font-size: 0.75rem", "min-height: 28px"):
            self.assertIn(decl, prefs, decl)
        self.assertIn("background: transparent", rule(MOBILE, "#wpconsent-container::part(wpconsent-button-preferences):hover"))

    def test_message_does_not_look_tappable_and_stays_small(self):
        body = rule(MOBILE, "#wpconsent-container::part(wpconsent-banner-body)")
        self.assertIn("cursor: default", body)
        self.assertIn("font-size: 0.72rem", body)
        self.assertNotIn("text-decoration", body)

    def test_card_stays_compact(self):
        banner = rule(MOBILE, "#wpconsent-container::part(wpconsent-banner)")
        for decl in ("bottom: 6px", "width: calc(100vw - 12px)", "padding: 8px 10px 4px", "border-radius: 12px"):
            self.assertIn(decl, banner, decl)

    def test_no_consent_button_is_hidden_or_shrunk_below_the_tap_target(self):
        for m in re.finditer(r"([^{}]*wpconsent[^{}]*)\{([^}]*)\}", MOBILE):
            self.assertNotIn("display: none", m.group(2), m.group(1).strip())
            self.assertNotIn("visibility: hidden", m.group(2), m.group(1).strip())
            self.assertNotIn("pointer-events", m.group(2), m.group(1).strip())

    def test_landing_b_pill_and_plugin_facing_files_untouched(self):
        base = merge_base()
        if not base:
            self.skipTest("no origin/main")
        watched = ["site/theme/assets/css/landing-b.css", "site/theme/assets/js/landing-b.js", "site/theme/assets/js/sticky-cta.js", "site/theme/inc/delayed-third-party.php"]
        # Issue #364 deliberately changes inc/landing-xmas.php (4–10 pair bundle); it is no longer watched here.
        changed = subprocess.run(["git", "diff", "--name-only", base, "--"] + watched, cwd=REPO, capture_output=True, text=True).stdout.split()
        self.assertEqual(changed, [])


class ThemeVersion(unittest.TestCase):
    def test_bumped_so_the_minified_bundles_refresh(self):
        v = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M)
        self.assertGreaterEqual(tuple(map(int, v.groups())), (0, 2, 115))


if __name__ == "__main__":
    unittest.main()
