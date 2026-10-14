"""Issue #165: Landing Page A (the CZ/EN product page) hero is compact and
carries the price + Order button in the first screen.

No PHP runtime needed. Asserts the template/CSS contract:

* the price + CTA row (.molosoc-hero-buy) lives inside the hero copy, with
  the same molosoc_product_url() link, .molosoc-btn / .molosoc-price-group
  markup and translate="no" it had in the "cream you already own" block;
* that block no longer carries a buy row of its own (one CTA per screen),
  while the mobile .molosoc-sticky-buy bar is untouched;
* product.css lays the hero out in normal flow (no 92vh box, no absolute
  copy, no translateY nudge, no z-index overlap) with the headline at the
  site's display-l scale instead of the old oversized clamp;
* Landing Page B's files are not part of the change.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
TEMPLATE = ROOT / "page-moisture-lock-foot-cover.php"
CSS = ROOT / "assets/css/product.css"


def _rule(css, selector):
    m = re.search(r"^" + re.escape(selector) + r" \{(.*?)^\}", css, re.S | re.M)
    return m.group(1) if m else None


def _block(src, start_marker, end_marker):
    a = src.index(start_marker)
    b = src.index(end_marker, a)
    return src[a:b]


class LandingAHeroTemplate(unittest.TestCase):
    def setUp(self):
        self.src = TEMPLATE.read_text(encoding="utf-8")

    def test_price_and_cta_sit_in_the_hero_copy(self):
        hero = _block(self.src, 'class="molosoc-orbit-hero-copy"', 'class="molosoc-orbit-drawer"')
        self.assertIn('<div class="molosoc-hero-buy">', hero)
        self.assertIn('<span class="molosoc-price-group" translate="no">', hero)
        self.assertIn("<span class=\"molosoc-hero-buy__price\"><?php echo $molosoc_is_cz ? '229 Kč' : '€10'; ?></span>", hero)
        self.assertIn("'Charged as 229 CZK at checkout.'", hero)  # EN-only note kept
        self.assertIn('<a class="molosoc-btn" href="<?php echo esc_url( molosoc_product_url() ); ?>">', hero)
        self.assertIn("'Objednat nyní' : __( 'Order Now', 'molosoc' )", hero)
        # Reading order inside the copy column: H1 → lede → price/CTA.
        self.assertLess(hero.index("</h1>"), hero.index("</p>"))
        self.assertLess(hero.index("</p>"), hero.index('class="molosoc-hero-buy"'))

    def test_cream_block_has_no_buy_row_anymore(self):
        drawer = _block(self.src, 'class="molosoc-orbit-drawer"', "</section>")
        self.assertNotIn("molosoc-orbit-drawer__buy", drawer)
        self.assertNotIn("molosoc-btn", drawer)
        self.assertNotIn("229", drawer)
        self.assertIn('class="molosoc-orbit-drawer__heading"', drawer)
        self.assertIn('class="molosoc-orbit-drawer__cards"', drawer)
        self.assertEqual(drawer.count("<article>"), 3)

    def test_one_hero_cta_and_the_mobile_sticky_bar_stay(self):
        self.assertEqual(self.src.count('class="molosoc-hero-buy"'), 1)
        self.assertNotIn("molosoc-orbit-drawer__buy", self.src)
        sticky = _block(self.src, '<div class="molosoc-sticky-buy">', "get_footer()")
        self.assertIn('class="molosoc-sticky-buy__price"', sticky)
        self.assertIn('<a class="molosoc-btn" href="<?php echo esc_url( molosoc_product_url() ); ?>">', sticky)
        # Every purchase link on the page is the WooCommerce product URL.
        hrefs = re.findall(r'class="molosoc-btn" href="([^"]+)"', self.src)
        self.assertTrue(hrefs)
        for h in hrefs:
            self.assertEqual(h, "<?php echo esc_url( molosoc_product_url() ); ?>")

    def test_hero_headline_and_still_markup_unchanged(self):
        self.assertIn('<h1 class="molosoc-hero-title">', self.src)
        self.assertIn('<span class="molosoc-hero-title__phrase">Návlek na nohy</span>', self.src)
        self.assertIn("esc_html_e( 'Foot Cover', 'molosoc' )", self.src)
        self.assertIn('class="molosoc-orbit-model"', self.src)


class LandingAHeroCss(unittest.TestCase):
    def setUp(self):
        self.css = CSS.read_text(encoding="utf-8")

    def test_hero_is_in_flow_two_column_grid(self):
        pin = _rule(self.css, ".molosoc-orbit-pin")
        self.assertIsNotNone(pin)
        self.assertIn("display: grid;", pin)
        self.assertIn("grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);", pin)
        self.assertNotIn("min-height", pin)
        stage = _rule(self.css, ".molosoc-orbit-stage")
        self.assertIn("position: relative;", stage)
        self.assertIn("overflow: hidden;", stage)
        self.assertNotIn("position: absolute;", stage)
        self.assertNotIn("z-index", stage)
        copy = _rule(self.css, ".molosoc-orbit-hero-copy")
        self.assertIn("display: flex;", copy)
        self.assertIn("flex-direction: column;", copy)
        self.assertNotIn("position: absolute;", copy)

    def test_old_oversized_hero_is_gone(self):
        for needle in ("92vh", "translateY(190px)", "z-index: 50", "8.5vw", "8.75rem", "pointer-events: none"):
            # Allowed only inside the history comment, never as a declaration.
            decls = [l for l in self.css.splitlines() if needle in l and l.strip().endswith(";")]
            self.assertEqual(decls, [], needle)
        self.assertNotIn(".molosoc-orbit-drawer__buy", self.css)
        self.assertNotIn(".molosoc-orbit-drawer__price", self.css)

    def test_headline_uses_display_l_scale(self):
        phrase = _rule(self.css, ".molosoc-hero-title__phrase")
        # Issue #167: +25% on the Issue #165 size, shared with every section H2.
        self.assertIn("font-size: var(--text-product-heading);", phrase)
        self.assertIn("--text-product-heading: clamp(3.125rem, 4vw + 0.9375rem, 4.6875rem);", self.css)
        self.assertIn("--text-product-heading-mobile: clamp(2.8125rem, 11.875vw, 3.4375rem);", self.css)
        self.assertIn("font-size: var(--text-product-heading);", _rule(self.css, ".molosoc-product-heading h2"))
        drawer = _rule(self.css, ".molosoc-orbit-drawer__heading h2")
        self.assertIn("font-size: var(--text-product-heading);", drawer)
        self.assertIn("text-align: right;", _rule(self.css, ".molosoc-orbit-drawer__heading"))
        self.assertNotIn("white-space: nowrap", phrase)

    def test_second_section_is_right_aligned(self):
        # Issue #169: right, never justify; desktop and the phone breakpoint.
        for sel in (".molosoc-orbit-drawer", ".molosoc-orbit-drawer__heading",
                    ".molosoc-orbit-drawer__cards article"):
            rule = _rule(self.css, sel)
            self.assertIn("text-align: right;", rule, sel)
            self.assertNotIn("justify", rule.replace("justify-content", ""), sel)
        top = _rule(self.css, ".molosoc-orbit-drawer__top")
        self.assertIn("justify-content: flex-end;", top)
        self.assertIn("margin-left: auto;", _rule(self.css, ".molosoc-orbit-drawer__heading h2"))
        self.assertIn("align-items: flex-end;\n    text-align: right;", self.css)
        self.assertNotIn("text-align: justify", self.css.split(".molosoc-orbit-drawer {")[1].split("Tablet portrait")[0])

    def test_still_is_cropped_to_the_product(self):
        model = _rule(self.css, ".molosoc-orbit-model")
        self.assertIn("margin-block: -14%;", model)
        self.assertIn("height: auto;", model)  # test_static_model_still contract
        self.assertIn("object-fit: contain;", model)

    def test_hero_buy_row_styled(self):
        buy = _rule(self.css, ".molosoc-hero-buy")
        self.assertIn("display: flex;", buy)
        price = _rule(self.css, ".molosoc-hero-buy__price")
        self.assertIn("font-family: var(--font-display);", price)
        self.assertIsNotNone(_rule(self.css, ".molosoc-price-group"))
        self.assertIsNotNone(_rule(self.css, ".molosoc-price-note"))

    def test_mobile_stacks_headline_still_lede_cta(self):
        m = re.search(r"@media \(max-width: 860px\) \{(.*?)\n\}\n", self.css, re.S)
        self.assertIsNotNone(m)
        mobile = m.group(1)
        self.assertIn(".molosoc-orbit-hero-copy {\n    display: contents;", mobile)
        order = {}
        for sel, body in re.findall(r"\n  ([^{]+?) \{(.*?)\n  \}", mobile, re.S):
            o = re.search(r"order: (\d+);", body)
            if o:
                order[sel.strip()] = int(o.group(1))
        self.assertEqual(order[".molosoc-hero-title__phrase"], 1)
        self.assertEqual(order[".molosoc-orbit-stage"], 2)
        self.assertEqual(order[".molosoc-orbit-hero-copy p"], 3)
        self.assertEqual(order[".molosoc-hero-buy"], 4)
        self.assertIn("flex-direction: column;", mobile)

    def test_drawer_h2_switches_to_mobile_token_at_the_shared_860_breakpoint(self):
        m = re.search(r"@media \(max-width: 860px\) \{(.*?)\n\}\n", self.css, re.S)
        self.assertIsNotNone(m)
        self.assertIn(
            ".molosoc-product-heading h2,\n  .molosoc-orbit-drawer__heading h2 {\n"
            "    font-size: var(--text-product-heading-mobile);",
            m.group(1),
        )
        m760 = re.search(r"@media \(max-width: 760px\) \{(.*?)\n\}\n", self.css, re.S)
        self.assertNotIn("--text-product-heading-mobile", m760.group(1).split(".molosoc-orbit-drawer__heading h2")[1].split("}")[0])

    def test_hero_buy_row_hands_over_to_the_sticky_bar_on_phones(self):
        m = re.search(r"@media \(max-width: 760px\) \{\n  /\* At phone widths(.*?)\n\}\n", self.css, re.S)
        self.assertIsNotNone(m)
        self.assertIn(".molosoc-hero-buy {\n    display: none;\n  }", m.group(1))

    def test_sticky_mobile_bar_css_untouched(self):
        self.assertIn(".molosoc-sticky-buy {\n  display: none;\n}", self.css)
        self.assertIn("  .molosoc-sticky-buy {\n    display: flex;\n    position: fixed;", self.css)

    def test_landing_page_b_not_touched(self):
        import subprocess
        repo = ROOT.parents[1]
        out = subprocess.run(
            ["git", "diff", "--name-only", "origin/main", "--",
             "site/theme/page-hydratacni-navleky-molosoc.php",
             "site/theme/assets/css/landing-b.css", "site/theme/assets/js/landing-b.js"],
            cwd=repo, capture_output=True, text=True,
        )
        if out.returncode == 0:
            self.assertEqual(out.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
