"""Issue #209: Landing B mobile purchase path — static checks (no PHP runtime
or WordPress needed).

Every purchase CTA on B is the shared size choice + "Pokračovat k pokladně"
button from inc/landing-b-buy.php (hero + after each main section), the hero shows the
Kč price and the COD line built only from approved wording, the 390px CSS
keeps the size choice and buy button clear of the WPConsent card, and nothing here adds
jQuery/JS to B (jQuery is deliberately absent there, Issue #190).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
TEMPLATE = (ROOT / "page-hydratacni-navleky-molosoc.php").read_text(encoding="utf-8")
BUY = (ROOT / "inc/landing-b-buy.php").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-b.css").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
JS = (ROOT / "assets/js/landing-b.js").read_text(encoding="utf-8")


class LandingBBuyPath(unittest.TestCase):
    def test_helper_is_loaded(self):
        self.assertIn("/inc/landing-b-buy.php';", FUNCTIONS)

    def test_hero_has_price_cod_line_and_buy_group_in_order(self):
        hero = TEMPLATE[TEMPLATE.index('<section class="lpb-hero"'):TEMPLATE.index("</section>")]
        price = hero.index("lpb-price__amount")
        cod = hero.index('class="lpb-cod"')
        buy = hero.index("molosoc_landing_b_buy_cta()")
        self.assertLess(price, cod)
        self.assertLess(cod, buy)
        # COD wording is the approved Issue #198 string, not new copy.
        self.assertIn("molosoc_cod_cz_text()", hero)
        self.assertIn("<strong>Dobírka:</strong>", hero)

    def test_cta_is_in_hero_every_second_section_and_final_purchase(self):
        # Issue #216: hero + every second main section + final purchase section.
        with_cta = ("Co to je", "Jak to funguje", "MOLOSOC v reálu", "Kompatibilita", "Objednávka")
        without = ("Pro koho MOLOSOC je", "Velikosti", "Příběh", "Jak to vše začalo", "Proč MOLOSOC", "FAQ")
        for label in with_cta + without:
            m = re.search(r'<section[^>]*aria-label="%s".*?</section>' % re.escape(label), TEMPLATE, re.S)
            self.assertIsNotNone(m, label)
            has = "molosoc_landing_b_buy_cta(" in m.group(0)
            self.assertEqual(has, label in with_cta, label)
        self.assertEqual(TEMPLATE.count("molosoc_landing_b_buy_cta("), 6)  # hero + 5 sections

    def test_sticky_pill_halo_is_styled_for_landing_b(self):
        css = (ROOT / "assets/css/landing-b.css").read_text(encoding="utf-8")
        i = css.index("Issue #216")
        block = css[i:]
        self.assertIn(".molosoc-sticky-cta {", block)
        self.assertIn("rgba(250, 245, 232", block)
        self.assertNotIn("animation", block)

    def test_no_cta_links_to_the_product_page_directly(self):
        self.assertNotIn("esc_url( $lpb_product_url )", TEMPLATE)

    def test_links_are_woocommerce_add_to_cart_urls_to_the_cz_checkout(self):
        for needle in ("'add-to-cart'  => MOLOSOC_PRODUCT_ID", "'variation_id' => $variation_id",
                       "'quantity'     => 1", "'molosoc_lpb'  => 1", "get_variation_attributes()",
                       "molosoc_landing_b_checkout_url()", "pll_get_post( $checkout_id, 'cz' )"):
            self.assertIn(needle, BUY, needle)
        # Never worse than before: unresolved sizes keep the CZ product-page link.
        self.assertIn("molosoc_product_url( 'cz' )", BUY)
        # Only purchasable, in-stock variations are linked.
        self.assertIn("is_purchasable()", BUY)
        self.assertIn("is_in_stock()", BUY)

    def test_size_choice_is_explicit_and_cta_is_pokracovat_k_pokladne(self):
        self.assertIn("Pokračovat k pokladně", BUY)
        self.assertIn('type="radio"', BUY)
        self.assertNotIn("checked", BUY)  # no preselected size
        self.assertIn("M (36–39)", BUY)
        self.assertIn("L (39.5–44)", BUY)
        # JS refuses to continue without a size and never sends two requests.
        self.assertIn('input[type="radio"]:checked', JS)
        self.assertIn("if ( busy )", JS)
        self.assertIn("pageshow", JS)

    def test_only_one_scoped_redirect_filter_and_no_cart_or_price_logic(self):
        self.assertEqual(BUY.count("add_filter("), 1)
        self.assertIn("add_filter( 'woocommerce_add_to_cart_redirect'", BUY)
        self.assertIn("isset( $_REQUEST['molosoc_lpb'] )", BUY)
        for forbidden in ("add_action", "WC()->cart", "set_price", "woocommerce_cart_redirect_after_add"):
            self.assertNotIn(forbidden, BUY, forbidden)
        code = re.sub(r"/\*.*?\*/", "", BUY, flags=re.S)  # the header comment names jQuery on purpose
        js_code = re.sub(r"/\*.*?\*/", "", JS, flags=re.S)
        self.assertNotIn("jQuery", code + js_code)
        self.assertNotIn("wp_enqueue_script", BUY)

    def test_price_is_still_the_checkout_price(self):
        self.assertIn("$lpb_price       = '229 Kč';", TEMPLATE)

    def test_mobile_css_keeps_buy_buttons_in_the_first_screen_and_compacts_the_banner(self):
        m = re.search(r"@media \(max-width: 560px\) \{(.*?)\n\}\n", CSS, re.S)
        self.assertIsNotNone(m)
        mob = m.group(1)
        self.assertIn(".lpb-hero__thumbs,\n  .lpb-hero__sub,\n  .lpb-hero__lede {\n    display: none;", mob)
        self.assertIn("height: 170px;", mob)
        # Banner compaction is only the card's size/spacing: never display/visibility of consent UI.
        banner = mob[mob.index("#wpconsent-container::part(wpconsent-banner) {"):]
        self.assertNotIn("display: none", banner)
        self.assertNotIn("visibility", banner)
        self.assertIn("bottom: 8px;", banner)


if __name__ == "__main__":
    unittest.main()
