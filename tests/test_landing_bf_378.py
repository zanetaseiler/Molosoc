"""Issue #378: Black Friday CZ/EN landing pages. Rendering checks go through
minimal WordPress stubs (tests/fixtures/landing_bf_stub_378.php, php CLI; skipped
without php); the rest are static. Pins: same picker / server path / prices as the
Christmas pages, no Christmas copy or order-by date on the Black Friday pages, no
invented saving/promotion, the real product photo shown whole, localized head tags,
stock refusal returns to the Black Friday page, and the Christmas pages unchanged."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
STUB = REPO / "tests/fixtures/landing_bf_stub_378.php"
BF = (ROOT / "inc/landing-bf.php").read_text(encoding="utf-8")
INC = (ROOT / "inc/landing-xmas.php").read_text(encoding="utf-8")
PART = (ROOT / "template-parts/landing-xmas.php").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-bf.css").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")

PAGES = {
    "cz": ("page-black-friday-molosoc.php", "black-friday-molosoc"),
    "en": ("page-black-friday-offer-molosoc.php", "black-friday-offer-molosoc"),
}
XMAS = {
    "cz": ("page-vanocni-darek-molosoc.php", "vanocni-darek-molosoc"),
    "en": ("page-christmas-gift-molosoc.php", "christmas-gift-molosoc"),
}
CHRISTMAS_WORDS = re.compile(r"vánoc|vánoč|christmas|prosince|december|dárek|dárkov|gift|santa|🎄", re.I)


def render(tpl, slug, mode="body", lp=""):
    if not shutil.which("php"):
        raise unittest.SkipTest("no php")
    args = ["php", str(STUB), tpl, slug, mode] + ([lp] if lp else [])
    return subprocess.run(args, capture_output=True, text=True, check=True, cwd=REPO).stdout


def main_text(html):
    return re.sub(r"<[^>]+>", " ", html)


class Templates(unittest.TestCase):
    def test_page_templates_use_the_shared_template_part(self):
        for lang, (tpl, _slug) in PAGES.items():
            src = (ROOT / tpl).read_text(encoding="utf-8")
            self.assertIn(f"$lpx_lang     = '{lang}';", src)
            self.assertIn("$lpx_campaign = 'bf';", src)
            self.assertIn("/template-parts/landing-xmas.php", src)

    def test_slugs_differ_per_language_and_are_new(self):
        self.assertIn("'cz' => 'black-friday-molosoc', 'en' => 'black-friday-offer-molosoc'", BF)
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", INC + PART, flags=re.S)
        for slug in ("black-friday-molosoc", "black-friday-offer-molosoc"):
            self.assertNotIn(slug, code)  # the Christmas files never hard-code the BF slugs

    def test_loaded_and_joins_the_landing_family(self):
        self.assertIn("require_once get_stylesheet_directory() . '/inc/landing-bf.php';", FUNCTIONS)
        self.assertIn("return function_exists( 'molosoc_bf_current_lang' ) ? molosoc_bf_current_lang() : '';", INC)

    def test_no_page_creation_or_publish(self):
        for needle in ("wp_insert_post", "wp_update_post", "wp_publish_post"):
            self.assertNotIn(needle, BF)

    def test_bf_css_is_scoped(self):
        rules = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
        for sel in re.findall(r"([^{}]+)\{", rules):
            sel = sel.strip()
            if sel.startswith("@media"):
                continue
            for part in sel.split(","):
                self.assertTrue(part.strip().startswith(".lpx--bf"), part)


class Copy(unittest.TestCase):
    def test_no_christmas_date_or_invented_promotion(self):
        for lang, (tpl, slug) in PAGES.items():
            html = render(tpl, slug)
            text = main_text(html)
            self.assertIsNone(CHRISTMAS_WORDS.search(text), lang)
            self.assertNotIn("lpx-deadline", html)
            self.assertNotIn("%", text)  # no percentage saving
            for word in ("sleva", "ušetř", "save ", "discount", "skladem jen", "only ", "posledn", "last chance", "do půlnoci", "ends"):
                self.assertNotIn(word, text.lower(), (lang, word))

    def test_deadline_key_is_empty_on_bf(self):
        self.assertEqual(BF.count("'deadline'   => '',"), 2)

    def test_prices_come_from_the_checkout_price_list(self):
        fn = BF[BF.index("function molosoc_bf_copy"):BF.index("function molosoc_bf_meta")]
        self.assertIn("molosoc_xmas_unit_prices()", fn)
        self.assertNotRegex(fn, r"\b(209|199|607|408)\b")

    def test_main_picker_shows_the_same_bundle_prices(self):
        cz = render(*PAGES["cz"])
        en = render(*PAGES["en"])
        for amount in ("209 Kč", "408 Kč", "607 Kč", "od 806 Kč"):
            self.assertIn(">%s<" % amount, cz)
        self.assertIn(">607 CZK<", en)
        self.assertIn(">Do košíku<", cz)
        self.assertIn(">Add to cart<", en)


class Purchase(unittest.TestCase):
    def test_same_picker_markup_as_christmas_apart_from_copy(self):
        bf, xmas = render(*PAGES["cz"]), render(*XMAS["cz"])
        for needle in ('value="multi"', "data-lpx-go", 'data-lpx-max="10"', 'data-lpx-min="4"', "data-lpx-counter=\"M\"", "data-lpx-counter=\"L\""):
            self.assertEqual(bf.count(needle), xmas.count(needle), needle)
        self.assertEqual(bf.count("data-lpx-buy "), 2)

    def test_checkout_url_carries_only_the_return_marker(self):
        self.assertIn('data-lpx-checkout-url="https://molosoc.com/cz/pokladna/?molosoc_lp=bf"', render(*PAGES["cz"]))
        self.assertIn('data-lpx-checkout-url="https://molosoc.com/checkout/?molosoc_lp=bf"', render(*PAGES["en"]))
        self.assertNotIn("molosoc_lp", render(*XMAS["cz"]))

    def test_three_pairs_total_607(self):
        self.assertIn("TOTAL3 607\n", render(*PAGES["cz"], mode="head"))

    def test_stock_refusal_returns_to_the_page_it_came_from(self):
        tpl, slug = PAGES["cz"]
        self.assertIn("RETURN https://molosoc.com/cz/black-friday-molosoc/?lpx_stock=m", render(tpl, slug, "head", "bf"))
        self.assertIn("RETURN https://molosoc.com/cz/vanocni-darek-molosoc/?lpx_stock=m", render(tpl, slug, "head"))
        self.assertIn("RETURN https://molosoc.com/cz/vanocni-darek-molosoc/?lpx_stock=m", render(tpl, slug, "head", "other"))

    def test_server_path_and_pricing_untouched(self):
        self.assertIn("$default = array( 1 => 209 );", INC)
        self.assertIn("MOLOSOC_PRODUCT_ID, 1, $v['variation_id']", INC)
        self.assertNotIn("molosoc_xmas_add_to_cart", BF.replace("molosoc_xmas_add_to_cart()", ""))


class Head(unittest.TestCase):
    def test_localized_title_description_og(self):
        for lang, (tpl, slug) in PAGES.items():
            head = render(tpl, slug, "head")
            self.assertIn("<title>Black Friday", head)
            self.assertIn('<meta name="description" content="Black Friday', head)
            self.assertIn('<meta property="og:locale" content="%s">' % ("cs_CZ" if lang == "cz" else "en_US"), head)
            url = "https://molosoc.com/cz/black-friday-molosoc/" if lang == "cz" else "https://molosoc.com/black-friday-offer-molosoc/"
            self.assertIn('<meta property="og:url" content="%s">' % url, head)
            self.assertIn('<meta property="og:image" content="https://molosoc.com/wp-content/themes/molosoc/assets/images/landing-b/lpb-product-shot-2-960.webp">', head)
            self.assertIsNone(CHRISTMAS_WORDS.search(head), lang)

    def test_preloads_the_product_photo_not_the_christmas_scene(self):
        head = render(*PAGES["cz"], mode="head")
        self.assertIn('rel="preload" as="image" fetchpriority="high" href="https://molosoc.com/wp-content/themes/molosoc/assets/images/landing-b/lpb-product-shot-2-960.webp"', head)
        self.assertNotIn("Christmas_Gift_Scene", head)

    def test_sticky_pill_label_and_bf_stylesheet(self):
        self.assertIn('STICKY {"url":"#lpx-bundle","label":"Vybrat set"}', render(*PAGES["cz"], mode="head"))
        self.assertIn('STICKY {"url":"#lpx-bundle","label":"Choose your set"}', render(*PAGES["en"], mode="head"))
        self.assertIn("ENQ molosoc-landing-bf", render(*PAGES["cz"], mode="head"))


class Photo(unittest.TestCase):
    def test_real_product_photo_shown_whole(self):
        html = render(*PAGES["cz"])
        hero = html[html.index('class="lpx-hero__media"'):html.index("lpx-hero__copy")]
        self.assertIn("lpb-product-shot-2-960.webp 960w", hero)
        self.assertIn('fetchpriority="high" loading="eager"', hero)
        self.assertIn('width="960" height="960"', hero)
        self.assertIn("object-fit: contain;", CSS)
        self.assertIn("aspect-ratio: 1 / 1;", CSS)
        for base in ("lpb-product-shot-2-480", "lpb-product-shot-2-960", "lpb-apply-cream-960", "lpb-opening-package-mami-800"):
            self.assertTrue((ROOT / "assets/images/landing-b" / f"{base}.webp").exists(), base)

    def test_no_christmas_photo_on_bf(self):
        for tpl, slug in PAGES.values():
            self.assertNotIn("landing-xmas/", render(tpl, slug))


class ChristmasUnchanged(unittest.TestCase):
    def test_christmas_pages_keep_copy_photos_head_and_no_bf_class(self):
        for lang, (tpl, slug) in XMAS.items():
            html = render(tpl, slug)
            head = render(tpl, slug, "head")
            self.assertIn('class="lpb lpx"', html)
            self.assertNotIn("lpx--bf", html)
            self.assertIn('<p class="lpx-deadline">', html)
            self.assertIn("MOLOSOC_Christmas_Gift_Scene_01", html)
            self.assertNotIn("og:", head)
            self.assertNotIn("molosoc-landing-bf", head)
            self.assertIn("Christmas_Gift_Scene_01", head)  # its own preload
            self.assertIn('"label":"%s"' % ("Vybrat dárkový set" if lang == "cz" else "Choose gift set"), head)


if __name__ == "__main__":
    unittest.main()
