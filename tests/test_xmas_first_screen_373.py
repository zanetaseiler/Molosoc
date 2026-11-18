"""Issue #373 — Christmas page: faster on mobile, set choice in the first screen.

Clarity (9-16 Nov 2026, mobile, 132 visits): 39 % left before scrolling 15 %,
only 3 taps on the checkout button, 23 of 54 taps on the cookie banner. On the
live page at 390x844 the bundle cards started at 961 px and the button at
1340 px. The fix is CSS-only for the layout (template order unchanged), the
button reads "Do košíku" / "Add to cart", and inc/landing-xmas.php drops the
WordPress block/global styles + the cart-badge mirror script on the two
Christmas pages and preconnects fonts.gstatic.com. Prices, bundle logic,
checkout, shipping, payment labels and the product page are untouched.
"""
import re
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site" / "theme"
INC = (ROOT / "inc" / "landing-xmas.php").read_text(encoding="utf-8")
PART = (ROOT / "template-parts" / "landing-xmas.php").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "css" / "landing-xmas.css").read_text(encoding="utf-8")
JS = (ROOT / "assets" / "js" / "landing-xmas.js").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def block373():
    """The #373 mobile media query: the `@media (max-width: 560px)` block that
    compacts the hero (between the #287/#314 block and the #295 facts block,
    which older tests pin as the first / last block)."""
    code = strip_comments(CSS)
    start = code.rindex("@media (max-width: 560px) {", 0, code.index(".lpx-hero__title { font-size: 1.75rem"))
    depth, i = 0, start
    while i < len(code):
        if code[i] == "{":
            depth += 1
        elif code[i] == "}":
            depth -= 1
            if depth == 0:
                return code[start : i + 1]
        i += 1
    raise AssertionError("unbalanced media block")


def rule(css, selector):
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert m, selector
    return m.group(1)


class ButtonLabel(unittest.TestCase):
    def test_cz_and_en_labels(self):
        self.assertIn("'cta'       => 'Do košíku',", PART)
        self.assertIn("'cta'       => 'Add to cart',", PART)
        self.assertNotIn("'Pokračovat k pokladně'", PART.replace("(was 'Pokračovat k pokladně')", ""))

    def test_flow_unchanged(self):
        # Same button, same data attribute, same URL contract to the server.
        self.assertIn('data-lpx-go rel="nofollow"><?php echo esc_html( $t[\'cta\'] ); ?></a>', PART)
        self.assertIn('"molosoc_xmas=1&molosoc_xmas_sizes=" + encodeURIComponent( sizes.join( "," ) )', JS)
        self.assertEqual(PART.count("$lpx_picker( "), 2)  # the hero-adjacent picker and the one in "Objednejte dárek"


class MobileFirstScreen(unittest.TestCase):
    def test_hero_is_compacted_not_rebuilt(self):
        # Template order is unchanged: hero, then the picker section directly after it.
        hero = PART.index('<section class="lpx-hero"')
        bundle = PART.index('<section class="lpb-section lpb-section--cream" id="lpx-bundle"')
        self.assertLess(hero, bundle)
        self.assertNotIn("<section", PART[PART.index("</section>", hero) : bundle])
        # The brief's keepers are still printed.
        self.assertIn("<p class=\"lpx-deadline\"><?php echo esc_html( $t['deadline'] ); ?></p>", PART)
        self.assertIn("Darujte péči, která nekončí Vánocemi.", PART)
        self.assertIn('<a class="lpb-btn" href="#lpx-bundle">', PART)  # hidden on phones by CSS only

    def test_mobile_rules(self):
        m = block373()
        # Issue #375: the hero photo is not cropped on phones (no fixed height / cover).
        self.assertNotIn(".lpx-hero__media img", m)
        self.assertIn("font-size: 1.75rem", rule(m, ".lpx-hero__title"))
        self.assertIn("margin: 0", rule(m, ".lpx-deadline"))
        hidden = rule(m, ".lpx-hero .lpb-cod,\n  .lpx-hero > .lpx-hero__inner > .lpx-hero__copy > .lpb-btn")
        self.assertIn("display: none", hidden)
        self.assertIn("padding-top: 0.5rem", rule(m, "#lpx-bundle.lpb-section"))
        self.assertIn("display: none", rule(m, "#lpx-bundle .lpb-section__head .lpb-lede"))
        cards = rule(m, ".lpx-bundles")
        self.assertIn("display: grid", cards)
        self.assertIn("grid-template-columns: 1fr 1fr", cards)
        self.assertIn("grid-column: 1 / -1", rule(m, ".lpx-bundles__teaser"))  # Issue #364 teaser spans both columns

    def test_desktop_untouched_and_picker_rows_kept(self):
        self.assertTrue(block373().startswith("@media (max-width: 560px)"))
        # The size row, hint, error and facts of #287/#295 are not hidden.
        for sel in (".lpx-pair", ".lpx-pair__hint", ".lpx-facts", ".lpb-buy__error", ".lpx-multi"):
            self.assertNotRegex(block373(), re.escape(sel) + r"[^{]*\{[^}]*display: none")

    def test_sticky_pill_and_cookie_rules_untouched(self):
        self.assertIn("'label' => 'en' === $page_lang ? 'Choose gift set' : 'Vybrat dárkový set',", INC)
        self.assertEqual(CSS.count("#wpconsent-container::part(wpconsent-banner) {"), 1)
        self.assertNotIn("wpconsent", block373())


class AssetsThisPageDoesNotUse(unittest.TestCase):
    def test_dequeue_hook_is_gated_and_late(self):
        fn = INC[INC.index("function molosoc_xmas_dequeue_unused_assets()") :]
        fn = fn[: fn.index("add_action(") + 80]
        self.assertIn("if ( ! molosoc_is_xmas_landing() ) {\n\t\treturn;", fn)
        self.assertIn("add_action( 'wp_enqueue_scripts', 'molosoc_xmas_dequeue_unused_assets', 110 );", fn)  # after the theme's 100
        self.assertEqual(
            re.search(r"function molosoc_xmas_unused_style_handles\(\) \{\n\treturn array\( (.*?) \);", INC).group(1),
            "'wp-block-library', 'global-styles', 'classic-theme-styles', 'woocommerce-inline'",
        )
        self.assertEqual(
            re.search(r"function molosoc_xmas_unused_script_handles\(\) \{\n\treturn array\( (.*?) \);", INC).group(1),
            "'molosoc-cart-badge-sync'",
        )

    def test_keepers_are_not_dequeued(self):
        fn = INC[INC.index("assets this page does not use (Issue #373)") :]
        for keep in ("facebook", "clarity", "wpconsent", "google-tag-manager", "order-attribution", "sourcebuster", "landing-xmas", "sticky-cta", "nav-toggle", "molosoc-landing-b"):
            self.assertNotIn(keep, strip_comments(fn).lower(), keep)

    def test_no_fonts_preconnect_the_hero_preload_stays_first(self):
        # Tried and dropped: a fonts.gstatic.com preconnect starts the ~90 KB of
        # Nunito/Tenor files earlier, at Chrome's highest priority, so they
        # compete with the hero image (the LCP element) in the lab runs.
        head = INC[INC.index("function molosoc_xmas_head()") : INC.index("add_action( 'wp_head', 'molosoc_xmas_head', 1 );")]
        self.assertNotIn("preconnect", head)
        self.assertIn('<link rel="preload" as="image" fetchpriority="high"', head)

    def test_body_font_remap_is_page_scoped_css(self):
        self.assertIn(':root { --font-body: var(--font-accent, "Nunito", -apple-system, sans-serif); }', CSS)
        self.assertNotIn("--font-body", FUNCTIONS[FUNCTIONS.index("function molosoc_fonts_url") :][:400])
        self.assertIn("family=Mulish", FUNCTIONS)  # the global font set itself is unchanged


class Guardrails(unittest.TestCase):
    def test_theme_version_bumped(self):
        v = re.search(r"^Version:\s*(\d+)\.(\d+)\.(\d+)", STYLE, re.M)
        self.assertGreaterEqual(tuple(int(x) for x in v.groups()), (0, 2, 123))

    def test_prices_and_checkout_untouched(self):
        self.assertIn("$default = array( 1 => 209 );", INC)
        self.assertNotRegex(strip_comments(JS), r"price|209|199|607|408")
        base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        if not base:
            self.skipTest("no origin/main")
        watched = [
            "site/theme/inc/checkout-cleanup.php", "site/theme/inc/woocommerce-lang.php", "site/theme/assets/css/checkout.css",
            "site/theme/assets/css/landing-b.css", "site/theme/assets/js/landing-b.js", "site/theme/assets/css/components.css",
            "site/theme/assets/js/sticky-cta.js", "site/theme/inc/delayed-third-party.php", "site/theme/inc/wpconsent-lang.php",
            "site/theme/assets/images/landing-xmas",
        ]
        changed = subprocess.run(["git", "diff", "--name-only", base, "--"] + watched, cwd=REPO, capture_output=True, text=True).stdout.split()
        # Issue #375 re-encodes the scaled-down derivatives (-480/-768/-1080) on purpose; the originals stay pinned.
        changed = [c for c in changed if not re.search(r"landing-xmas/MOLOSOC_Christmas_Gift_Scene_0\d-(480|768|1080)\.webp$", c)]
        # The #375 follow-up adds AVIF copies of the hero (new files) and changes the
        # product-page shipping note 69 -> 79 Kč in woocommerce-lang.php (that line only).
        changed = [c for c in changed if not re.search(r"landing-xmas/MOLOSOC_Christmas_Gift_Scene_01(-(480|768|1080))?\.avif$", c)]
        if "site/theme/inc/woocommerce-lang.php" in changed:
            wl = subprocess.run(["git", "diff", "-U0", base, "--", "site/theme/inc/woocommerce-lang.php"], cwd=REPO, capture_output=True, text=True).stdout
            body = [l for l in wl.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
            self.assertEqual(body, [
                "-\t\tesc_html( $is_cz ? 'Doprava od 69 Kč' : 'Shipping from 69 CZK' )",
                "+\t\tesc_html( $is_cz ? 'Doprava od 79 Kč' : 'Shipping from 79 CZK' )",
            ])
            changed.remove("site/theme/inc/woocommerce-lang.php")
        self.assertEqual(changed, [])
        diff = subprocess.run(["git", "diff", "-U0", base, "--", "site/theme/functions.php"], cwd=REPO, capture_output=True, text=True).stdout
        self.assertEqual([l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")], [])


if __name__ == "__main__":
    unittest.main()
