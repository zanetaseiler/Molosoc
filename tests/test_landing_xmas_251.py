"""Issue #251 (+ #269): Christmas 2026 gift landing (CZ + EN) — static checks (no PHP
runtime or WordPress needed). Pins the approved pricing, the release gate, the
server-side-only price rule, copy bans, asset handling and that the evergreen
pages and the post-purchase gift add-on are untouched."""
import re
import subprocess
import struct
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
INC = (ROOT / "inc/landing-xmas.php").read_text(encoding="utf-8")
PART = (ROOT / "template-parts/landing-xmas.php").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
JS = (ROOT / "assets/js/landing-xmas.js").read_text(encoding="utf-8")


def strip_comments(src):
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


PART_CODE = strip_comments(PART)
JS_CODE = strip_comments(JS)


class Pricing(unittest.TestCase):
    def test_approved_schedule_209_199_199(self):
        self.assertIn("array( 1 => 209, 2 => 199, 3 => 199 )", INC)  # 209 / 408 / 607

    def test_price_comes_from_slot_tag_not_request(self):
        fn = INC[INC.index("function molosoc_xmas_apply_prices"):INC.index("release gate")]
        self.assertIn("molosoc_xmas_slot", fn)
        self.assertNotIn("$_GET", fn)
        self.assertNotIn("$_REQUEST", fn)
        self.assertNotIn("$_POST", fn)
        self.assertIn("set_price( $prices[ $unit ] )", fn)

    def test_bundle_is_repacked_and_base_price_restored(self):
        fn = INC[INC.index("function molosoc_xmas_apply_prices"):INC.index("release gate")]
        self.assertIn("usort( $eligible", fn)
        self.assertIn("_molosoc_xmas_base_price", fn)
        self.assertIn("set_price( $base )", fn)

    def test_add_to_cart_rolls_back_on_failure(self):
        self.assertIn("set_cart_contents( $snapshot )", INC)
        self.assertIn("if ( ! $added )", INC)

    def test_gift_addon_rows_are_skipped(self):
        fn = INC[INC.index("function molosoc_xmas_apply_prices"):INC.index("release gate")]
        self.assertIn("molosoc_gift_slot", fn)

    def test_one_cart_line_per_pair_and_real_variations(self):
        self.assertIn("MOLOSOC_PRODUCT_ID, 1, $v['variation_id']", INC)
        self.assertIn("molosoc_landing_b_buy_links()", INC)

    def test_sizes_are_validated(self):
        self.assertIn("'M' !== $size && 'L' !== $size", INC)
        self.assertIn("count( $sizes ) > 3", INC)

    def test_js_sends_only_sizes(self):
        self.assertIn("molosoc_xmas_sizes=", JS)
        self.assertNotRegex(JS_CODE, r"price|209|199|607|408")


class ReleaseGate(unittest.TestCase):
    def test_noindex_and_sitemap_exclusion_until_published(self):
        self.assertIn("return (bool) apply_filters( 'molosoc_xmas_published', true );", INC)
        self.assertIn("$robots['noindex']  = true;", INC)
        self.assertIn("wp_sitemaps_posts_query_args", INC)

    def test_slugs(self):
        self.assertIn("'vanocni-darek-molosoc'", INC)
        self.assertIn("'christmas-gift-molosoc'", INC)
        self.assertTrue((ROOT / "page-vanocni-darek-molosoc.php").exists())
        self.assertTrue((ROOT / "page-christmas-gift-molosoc.php").exists())

    def test_no_page_creation_or_publish(self):
        for needle in ("wp_insert_post", "wp_update_post", "wp_publish_post"):
            self.assertNotIn(needle, INC + PART)


class Copy(unittest.TestCase):
    def test_headlines(self):
        self.assertIn("Darujte péči, která nekončí Vánocemi.", PART)
        self.assertIn("Give care that doesn\\'t end with Christmas.", PART)
        # Issue #295: the shipping price is read from molosoc_xmas_facts() (69 CZK)
        # and composed in the template, so "Doprava od 69 Kč" is no longer a literal.
        self.assertIn("'ship_from' => 69,", INC)
        self.assertIn("'ship'      => 'Doprava od ' . $lpx_fcz['ship_from'] . ' Kč',", PART)
        self.assertIn("'ship'      => 'Shipping from ' . $lpx_fen['ship_from'] . ' CZK',", PART)
        self.assertNotIn("79 Kč", PART)
        self.assertNotIn("79 CZK", PART)
        self.assertNotIn("=> 79,", INC)

    def test_banned_claims(self):
        low = PART_CODE.lower()
        for banned in ("odpočet", "countdown", "poslední kus", "last chance", "doručíme do vánoc",
                       "delivered by christmas", "zdarma", "free gift", "vyléč", "cure", "léčí"):
            self.assertIsNone(re.search(r"\b" + re.escape(banned), low), banned)

    def test_gift_wrap_is_stated_as_not_included(self):
        self.assertIn("Dárkové balení v ceně není", PART)
        self.assertIn("Gift wrapping is not included", PART)


class Images(unittest.TestCase):
    def test_all_three_drive_ids_registered(self):
        for drive in ("1JHezsiFVICxddNfOX1_7AQfe1Nq36u9k", "12WhUf4aciD21JAoG1_X1cC1-mY8Sto0M", "18RlEVxkbHFW0hH7LRUlLBitualjBxsvm"):
            self.assertIn(drive, INC)

    def test_missing_files_render_nothing(self):
        self.assertIn("if ( ! file_exists( $path ) )", INC)

    def test_imported_webp_files_are_real_and_ordered(self):
        for n in ("01", "02", "03"):
            self.assertIn(f"MOLOSOC_Christmas_Gift_Scene_{n}.webp", INC)
            data = (ROOT / f"assets/images/landing-xmas/MOLOSOC_Christmas_Gift_Scene_{n}.webp").read_bytes()
            self.assertEqual(data[:4], b"RIFF")
            self.assertEqual(data[8:12], b"WEBP")
            self.assertGreater(len(data), 50_000, "must be a real image, not a placeholder")
            self.assertEqual(struct.unpack("<H", data[26:28])[0] & 0x3FFF, 1536)  # VP8 lossy width
        self.assertLess(INC.index("scene-01"), INC.index("scene-02"))
        self.assertLess(INC.index("scene-02"), INC.index("scene-03"))

    def test_both_languages_use_all_three_scenes(self):
        for key in ("scene-01", "scene-02", "scene-03"):
            self.assertIn(f"molosoc_xmas_image( '{key}'", PART)


class SizeAvailability(unittest.TestCase):
    def test_one_sold_out_size_does_not_disable_the_picker(self):
        self.assertNotIn("=== 2", PART_CODE)  # no "both variations required"
        self.assertIn("count( $lpx_avail ) > 0", PART_CODE)

    def test_only_the_unavailable_size_is_disabled(self):
        self.assertIn("! isset( $lpx_avail[ $key ] ) ? ' disabled'", PART_CODE)


class EvergreenUntouched(unittest.TestCase):
    def test_changed_files_are_additive_only(self):
        base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        if not base:
            self.skipTest("no origin/main")
        changed = subprocess.run(["git", "diff", "--name-only", base], cwd=REPO, capture_output=True, text=True).stdout.split()
        protected = re.compile(r"page-hydratacni-navleky-molosoc|page-moisture-lock|landing-b|thank-you-gift|front-page|page-foot-covers")
        # Issue #278 deliberately enables the Landing B feedback summary in its template.
        # Issue #281 adds the numbered feedback list styles to landing-b.css.
        # Issue #288 adds the English Landing B: a new inc file and a lang parameter
        # (default 'cz') on the shared buy helper; the CZ template itself is untouched.
        allowed = {
            "site/theme/page-hydratacni-navleky-molosoc.php",
            "site/theme/assets/css/landing-b.css",
            "site/theme/inc/landing-b-buy.php",
            "site/theme/inc/landing-b-en.php",
            "docs/landing-page-b-en-288.md",
            "tests/test_landing_b_en_288.py",
            # Issue #303 points every Landing A button/link at Landing B (helper in inc/landing-links.php).
            "site/theme/front-page.php",
            "site/theme/page-foot-covers.php",
        }
        self.assertEqual([c for c in changed if protected.search(c) and c not in allowed], [])
        # functions.php and woocommerce-lang.php may only gain lines (Issue #269
        # adds one CZ cart-name filter to woocommerce-lang.php).
        for path in ("site/theme/functions.php", "site/theme/inc/woocommerce-lang.php"):
            diff = subprocess.run(["git", "diff", "-U0", base, "--", path], cwd=REPO, capture_output=True, text=True).stdout
            removed = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
            self.assertEqual(removed, [], path)


class NumberedFeedback284(unittest.TestCase):
    ITEM1 = "Jedna zákaznice nám napsala, že její maminka je s návleky MOLOSOC velmi spokojená a pohodlně je nosí přibližně 30 minut."
    ITEM2 = "Další zákaznice popsala, že má po použití návleků chodidla hebká jako dětskou pokožku."
    ITEM3 = "Jiná zákaznice nám napsala, že si návleky natolik oblíbila, že je nechce odložit."

    def block(self):
        return PART[PART.index("Issue #284"):PART.index("Issue #284") + PART[PART.index("Issue #284"):].index("<?php endif; ?>\n\n\t<section")]

    def test_cz_only_numbered_list_reuses_landing_b_markup(self):
        self.assertIn("if ( 'cz' === $lpx_lang ) :", self.block())
        self.assertIn('<ol class="lpb-testimonial__list">', self.block())
        self.assertIn("<li>" + self.ITEM1 + "</li>", self.block())

    def test_items_1_2_3_all_shown_like_landing_b(self):
        # Issue #305 (Žaneta, 2026-10-30): the numbered list shows all three items, exactly as Landing B does since #281; the old gate is gone.
        b = self.block()
        ol = b[b.index('<ol class="lpb-testimonial__list">'):b.index("</ol>")]
        self.assertEqual(ol.count("<li>"), 3)
        self.assertLess(ol.index(self.ITEM1), ol.index(self.ITEM2))
        self.assertLess(ol.index(self.ITEM2), ol.index(self.ITEM3))
        self.assertNotIn("molosoc_landing_b_feedback_extra_enabled", PART_CODE)  # only the history comment may name it
        self.assertNotIn("molosoc_landing_b_feedback_extra_enabled", FUNCTIONS)
        # Same three sentences as Landing B, byte for byte.
        b_tpl = (ROOT / "page-hydratacni-navleky-molosoc.php").read_text(encoding="utf-8")
        for item in (self.ITEM1, self.ITEM2, self.ITEM3):
            self.assertIn("<li>" + item + "</li>", b_tpl)

    def test_no_quotes_names_or_claims(self):
        b = self.block()
        text = re.sub(r"<[^>]*>", "", b[b.index("<ol"):b.index("</ol>")])
        for bad in ("„", "“", '"', "”", "prdel", "ověřen", "léč", "zlepš", "psoria"):
            self.assertNotIn(bad, text)

    def test_checkout_and_cta_untouched(self):
        self.assertEqual(PART.count("$lpx_picker( "), 2)  # main + order pickers unchanged
        self.assertNotIn("lpx-bundle", self.block())


class SizeSelectorHeight258(unittest.TestCase):
    """Issue #258: M and L size cards must share one height on mobile, even when
    the L label wraps. Pinned statically; the rendered check is a 390px layout."""

    def test_pair_size_cards_stretch_to_equal_height(self):
        css = (ROOT / "assets/css/landing-xmas.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.lpx-pair \.lpb-size\s*\{[^}]*display:\s*flex")
        self.assertRegex(css, r"\.lpx-pair \.lpb-size__label\s*\{[^}]*flex:\s*1 1 auto")


class PreLaunch269(unittest.TestCase):
    """Issue #269: pre-launch fixes on both Christmas pages."""

    def test_no_internal_woocommerce_wording_in_copy(self):
        self.assertNotIn("WooCommerce", PART_CODE)
        self.assertIn("'order_p'   => 'Bezpečná platba přes Comgate.'", PART)
        self.assertIn("'order_p'   => 'Secure payment via Comgate.'", PART)

    def test_order_by_18_december_in_hero_order_section_and_faq(self):
        # Issue #295: the date lives once in molosoc_xmas_facts(); the deadline key
        # and the FAQ answer are composed from it (the info block repeats it too).
        self.assertIn("'order_by'  => $en ? '18 December' : '18. prosince',", INC)
        cz = "Objednejte do %s, doručíme před Vánoci"
        en = "Order by %s for delivery before Christmas"
        self.assertEqual(PART.count(cz + ".', $lpx_fcz['order_by'] )"), 1)  # deadline key
        self.assertIn(cz + ". Platbu a dopravu vybíráte v pokladně; ', $lpx_fcz['ship_from'], $lpx_fcz['order_by'] )", PART)  # FAQ
        self.assertEqual(PART.count(en + ".', $lpx_fen['order_by'] )"), 1)
        self.assertIn(en + ". Shipping and payment methods are chosen at checkout.', $lpx_fen['ship_from'], $lpx_fen['order_by'] )", PART)
        self.assertNotIn("18. prosince", PART_CODE)  # the header comment may still name the date
        self.assertNotIn("18 December", PART_CODE)
        self.assertIn("<p class=\"lpx-deadline\"><?php echo esc_html( $t['deadline'] ); ?></p>", PART)
        self.assertIn("$t['ship'] . '. ' . $t['deadline']", PART)

    def test_no_crossed_out_reference_price(self):
        for gone in ("běžně", "'normally'", "lpx-bundle__was", "<s ", "'regular'", "MOLOSOC_XMAS_REGULAR_PRICE"):
            self.assertNotIn(gone, PART_CODE, gone)
        self.assertNotIn("MOLOSOC_XMAS_REGULAR_PRICE", strip_comments(INC))

    def test_cz_cart_name_covers_store_api_title(self):
        lang = (ROOT / "inc/woocommerce-lang.php").read_text(encoding="utf-8")
        self.assertIn("add_filter( 'woocommerce_product_title', 'molosoc_cz_store_api_product_name', 10, 2 );", lang)
        fn = lang[lang.index("function molosoc_cz_store_api_product_name"):]
        fn = fn[:fn.index("add_filter")]
        self.assertIn("'cz' !== pll_current_language()", fn)
        self.assertIn("molosoc_is_product_364_or_its_variation( $product )", fn)


if __name__ == "__main__":
    unittest.main()
