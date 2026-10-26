"""Issue #251: Christmas 2026 gift landing (CZ + EN) — static checks (no PHP
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
        self.assertIn("Doprava od 69 Kč", PART)
        self.assertIn("Shipping from 69 CZK", PART)
        self.assertNotIn("79 Kč", PART)
        self.assertNotIn("79 CZK", PART)

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
        protected = re.compile(r"page-hydratacni-navleky-molosoc|page-moisture-lock|landing-b|thank-you-gift|front-page|page-foot-covers|inc/woocommerce-lang")
        self.assertEqual([c for c in changed if protected.search(c)], [])
        diff = subprocess.run(["git", "diff", "-U0", base, "--", "site/theme/functions.php"], cwd=REPO, capture_output=True, text=True).stdout
        removed = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
        self.assertEqual(removed, [])


class SizeSelectorHeight258(unittest.TestCase):
    """Issue #258: M and L size cards must share one height on mobile, even when
    the L label wraps. Pinned statically; the rendered check is a 390px layout."""

    def test_pair_size_cards_stretch_to_equal_height(self):
        css = (ROOT / "assets/css/landing-xmas.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.lpx-pair \.lpb-size\s*\{[^}]*display:\s*flex")
        self.assertRegex(css, r"\.lpx-pair \.lpb-size__label\s*\{[^}]*flex:\s*1 1 auto")


if __name__ == "__main__":
    unittest.main()
