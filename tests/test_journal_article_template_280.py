"""Issue #280: new Journal articles inherit the approved article design automatically (static checks)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "site/theme"
FUNCS = (THEME / "functions.php").read_text(encoding="utf-8")
DOC = (ROOT / "docs/journal-article-template.md").read_text(encoding="utf-8")
HELPER = re.search(r"function molosoc_has_journal_article_template\(\).*?\n}\n", FUNCS, re.S).group(0)
SLUG_BRANCH = re.search(r"elseif \( is_page\( array\(\n\t\t// Journal article pages.*?\) \) \) \{", FUNCS, re.S).group(0)
ARTICLE_TEMPLATES = [t for t in THEME.glob("page-*.php") if "molosoc-pillar-hero" in t.read_text(encoding="utf-8")]


class JournalEnqueue(unittest.TestCase):
    def test_both_branches_load_the_one_shared_stylesheet(self):
        self.assertEqual(FUNCS.count("assets/css/pillar1.css"), 2)
        branch = re.search(r"elseif \( molosoc_has_journal_article_template\(\) \) \{(.*?)\n\t\} elseif", FUNCS, re.S).group(1)
        self.assertIn("'molosoc-pillar1'", branch)
        self.assertNotIn("wp_enqueue_script", branch)

    def test_every_existing_article_template_is_still_covered(self):
        self.assertEqual(len(ARTICLE_TEMPLATES), 13)
        for tpl in ARTICLE_TEMPLATES:
            slug = tpl.stem[len("page-"):]
            self.assertIn(f"'{slug}'", SLUG_BRANCH, tpl.name)

    def test_czech_siblings_still_listed(self):
        for slug in ("popraskane-paty", "zarostly-nehet", "kurici-oko", "jak-odstranit"):
            self.assertIn(f"'{slug}'", SLUG_BRANCH)

    def test_new_articles_inherit_via_template_naming_convention(self):
        self.assertIn("'page-journal-'", HELPER)
        self.assertIn("get_page_template_slug()", HELPER)

    def test_non_journal_pages_not_matched(self):
        for slug in ("foot-covers", "moisture-lock-foot-cover", "blog", "magazin", "thank-you"):
            self.assertNotIn(f"'{slug}'", SLUG_BRANCH)

    def test_doc_describes_the_convention(self):
        self.assertIn("page-journal-", DOC)
        self.assertIn("pillar1.css", DOC)


if __name__ == "__main__":
    unittest.main()
