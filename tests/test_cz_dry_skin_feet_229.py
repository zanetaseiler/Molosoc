"""Issue #229: CZ dry-skin-on-feet informational page (static checks, no PHP runtime)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "site/theme"
TPL_FULL = (THEME / "page-sucha-kuze-na-chodidlech.php").read_text(encoding="utf-8")
TPL = TPL_FULL.split("*/", 1)[1]  # markup only; the docblock explains the keyword scope
FUNCTIONS = (THEME / "functions.php").read_text(encoding="utf-8")
RELATED = (THEME / "inc/related-links.php").read_text(encoding="utf-8")
PRODUCT = "/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/"
SLUG = "sucha-kuze-na-chodidlech"
CREATE_PAGE = (ROOT / "automations/content-sync/create_wp_page.py").read_text(encoding="utf-8")
CREATE_WF = (ROOT / ".github/workflows/create-wp-page.yml").read_text(encoding="utf-8")


class CzDrySkinFeetPage(unittest.TestCase):
    def test_one_h1_and_primary_keyword(self):
        self.assertEqual(TPL.count("<h1>"), 1)
        self.assertIn("Suchá kůže na chodidlech", TPL.split("<h1>")[1].split("</h1>")[0])

    def test_no_competing_keywords_or_claims(self):
        low = TPL.lower()
        for bad in ("maska na nohy", "masku na nohy", "vyléč", "zahoj", "zaručen", "zarostl", "kuří oko"):
            self.assertNotIn(bad, low)

    def test_links_only_to_existing_cz_pages(self):
        paths = set(re.findall(r"home_url\( '(/[^']+)' \)", TPL))
        self.assertEqual(paths, {PRODUCT, "/cz/popraskane-paty/"})
        self.assertNotIn("hreflang", TPL)
        self.assertNotRegex(TPL, r"href=[^>]*#")

    def test_product_link_contextual_plus_cta_only(self):
        self.assertEqual(TPL.count(PRODUCT), 2)

    def test_medical_escalation_present(self):
        self.assertIn("Kdy se poradit s lékařem", TPL)

    def test_related_links_wired_and_cz_only_row(self):
        self.assertIn("molosoc_related_links( 'sucha-kuze' );", TPL)
        self.assertIn("'sucha-kuze'", RELATED)
        self.assertIn("array( '/dry-skin-feet/', null, 'Suchá kůže na chodidlech' )", RELATED)
        self.assertIn("'/dry-skin-feet/'         => '/cz/sucha-kuze-na-chodidlech/'", RELATED)
        self.assertIn("null === $en", RELATED)

    def test_assets_and_schema_registered(self):
        self.assertIn(f"'{SLUG}',", FUNCTIONS)
        m = re.search(r"is_page\( '%s' \)(.*?)add_action\( 'wp_head', 'molosoc_cz_schema' \)" % SLUG, FUNCTIONS, re.S)
        self.assertIsNotNone(m)
        self.assertIn(f"https://molosoc.com/cz/{SLUG}/", m.group(1))
        self.assertIn('"inLanguage": "cs"', m.group(1))

    def test_no_hardcoded_hreflang_or_en_pairing(self):
        self.assertNotRegex(FUNCTIONS, rf"hreflang[^\n]*{SLUG}|{SLUG}[^\n]*hreflang")

class CzProvisioning(unittest.TestCase):
    def test_cz_only_link_gated_on_published_czech_page(self):
        self.assertIn("function molosoc_cz_page_is_live", RELATED)
        self.assertIn("pll_get_post_language", RELATED)
        self.assertIn("null === $en && ! molosoc_cz_page_is_live", RELATED)

    def test_create_page_supports_czech_language_and_checks_permalink(self):
        self.assertIn("--lang", CREATE_PAGE)
        self.assertIn('payload["lang"]', CREATE_PAGE)
        self.assertIn("permalink_in_language", CREATE_PAGE)
        self.assertIn("ACTION REQUIRED", CREATE_PAGE)
        self.assertIn("lang:", CREATE_WF)
        self.assertIn("--lang", CREATE_WF)


if __name__ == "__main__":
    unittest.main()
