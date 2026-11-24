"""Issue #386: the header globe (Polylang's language switcher in the primary menu)
on the Black Friday pages links to the other language's Black Friday page, not
Home. Rendering goes through tests/fixtures/bf_switcher_stub_386.php (php CLI,
skipped without it), which reproduces Polylang's untranslated-page fallback
(the other language's homepage) and runs the theme's `pll_the_language_link`
callbacks over it."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
STUB = REPO / "tests/fixtures/bf_switcher_stub_386.php"
BF = (ROOT / "inc/landing-bf.php").read_text(encoding="utf-8")
HEADER = (ROOT / "template-parts/site-header.php").read_text(encoding="utf-8")

CZ_BF = "https://molosoc.com/cz/black-friday-molosoc/"
EN_BF = "https://molosoc.com/black-friday-offer-molosoc/"


def switcher(page, flag=""):
    if not shutil.which("php"):
        raise unittest.SkipTest("no php")
    args = ["php", str(STUB), page] + ([flag] if flag else [])
    out = subprocess.run(args, capture_output=True, text=True, check=True, cwd=REPO).stdout
    return dict(line.split(" ", 1) for line in out.strip().splitlines())


class HeaderGlobe(unittest.TestCase):
    def test_cz_bf_page_en_goes_to_en_bf_page(self):
        links = switcher("black-friday-molosoc")
        self.assertEqual(links["en"], EN_BF)
        self.assertEqual(links["cz"], CZ_BF)

    def test_en_bf_page_cz_goes_to_cz_bf_page(self):
        links = switcher("black-friday-offer-molosoc")
        self.assertEqual(links["cz"], CZ_BF)
        self.assertEqual(links["en"], EN_BF)

    def test_other_pages_keep_polylangs_link(self):
        for page in ("-", "vanocni-darek-molosoc", "christmas-gift-molosoc", "navleky-na-nohy"):
            self.assertEqual(switcher(page), {"cz": "https://molosoc.com/cz/", "en": "https://molosoc.com/"}, page)

    def test_unpublished_target_falls_back_to_its_expected_permalink(self):
        # molosoc_bf_page_url(): an unpublished page still gives the expected URL, never Home.
        self.assertEqual(switcher("black-friday-molosoc", "bf-draft")["en"], EN_BF)


class Wiring(unittest.TestCase):
    def test_filter_registered_on_polylangs_switcher_link(self):
        self.assertIn(
            "add_filter( 'pll_the_language_link', 'molosoc_bf_language_switcher_link', 10, 2 );", BF
        )

    def test_header_globe_is_the_primary_menu_switcher(self):
        # The globe comes from wp_nav_menu('primary'); the top bar is separate and untouched.
        self.assertIn("'theme_location'  => 'primary'", HEADER)
        self.assertIn("molosoc_xmas_bar();", HEADER)

    def test_filter_only_acts_on_bf_pages(self):
        body = re.search(r"function molosoc_bf_language_switcher_link\(.*?\n}\n", BF, re.S).group(0)
        self.assertIn("molosoc_is_bf_landing()", body)
        self.assertIn("return molosoc_bf_page_url( $slug );", body)


if __name__ == "__main__":
    unittest.main()
