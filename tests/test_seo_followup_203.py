"""Issue #203: thin foot-care category noindex, CZ-only spoke hreflang, CZ Magazín topics.

Static checks (no PHP runtime needed beyond `php -l`, run separately).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "site/theme"
FUNCTIONS = (THEME / "functions.php").read_text(encoding="utf-8")
BLOG = (THEME / "page-blog.php").read_text(encoding="utf-8")


class FootCareCategory(unittest.TestCase):
    def test_noindex_scoped_to_foot_care_term_only(self):
        self.assertIn("get_term_by( 'slug', 'foot-care', 'product_cat' )", FUNCTIONS)
        self.assertIn("in_array( (int) get_queried_object_id(), molosoc_thin_product_cat_term_ids(), true )", FUNCTIONS)
        # never a blanket product_cat noindex
        self.assertNotRegex(FUNCTIONS, r"if \( is_tax\( 'product_cat' \) \) \{\s*\$robots\['noindex'\]")

    def test_sitemap_excludes_same_term_ids(self):
        m = re.search(r"wp_sitemaps_taxonomies_query_args.*?\}, 10, 2 \);", FUNCTIONS, re.S)
        self.assertIsNotNone(m)
        self.assertIn("molosoc_thin_product_cat_term_ids()", m.group(0))
        self.assertIn("'product_cat' === $taxonomy", m.group(0))

    def test_no_canonical_added_for_noindexed_category(self):
        m = re.search(r"function molosoc_thin_product_cat_term_ids.*?wp_sitemaps_taxonomies_query_args", FUNCTIONS, re.S)
        self.assertNotIn('rel="canonical"', m.group(0))


class CzOnlySpokeHreflang(unittest.TestCase):
    def test_no_fabricated_hreflang_for_na_chodidle(self):
        # na-chodidle has no EN twin (seo/cz-pages/spoke-na-chodidle.md:
        # translation_of_en_slug: null) so nothing may hardcode alternates.
        self.assertNotRegex(FUNCTIONS, r"hreflang[^\n]*na-chodidle|na-chodidle[^\n]*hreflang")
        md = (ROOT / "seo/cz-pages/spoke-na-chodidle.md").read_text(encoding="utf-8")
        self.assertIn("translation_of_en_slug: null", md)


class CzMagazinTopics(unittest.TestCase):
    def test_topics_section_is_cz_only_and_links_existing_cz_pages(self):
        m = re.search(r"<\?php if \( \$molosoc_is_cz \) : \?>(.*?)<\?php endif; \?>", BLOG, re.S)
        self.assertIsNotNone(m)
        paths = re.findall(r"home_url\( '(/[^']+)' \)", m.group(1))
        self.assertEqual(
            sorted(set(paths)),
            ["/cz/kurici-oko/", "/cz/kurici-oko/jak-odstranit/", "/cz/kurici-oko/na-chodidle/",
             "/cz/popraskane-paty/", "/cz/sucha-kuze-na-chodidlech/", "/cz/zarostly-nehet/"],
        )

    def test_intro_counts_four_topics_including_dry_feet(self):
        m = re.search(r"<\?php if \( \$molosoc_is_cz \) : \?>(.*?)<\?php endif; \?>", BLOG, re.S)
        block = m.group(1)
        self.assertIn("do čtyř témat", block)
        self.assertNotIn("do tří témat", block)
        self.assertEqual(block.count("<h3>"), 4)


if __name__ == "__main__":
    unittest.main()
