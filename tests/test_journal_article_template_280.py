"""Issue #280: new Journal articles inherit the approved article design automatically (static checks)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "site/theme"
FUNCS = (THEME / "functions.php").read_text(encoding="utf-8")
DOC = (ROOT / "docs/journal-article-template.md").read_text(encoding="utf-8")
HELPER = re.search(r"function molosoc_is_journal_article\(\).*?\n}\n", FUNCS, re.S).group(0)
ARTICLE_TEMPLATES = [t for t in THEME.glob("page-*.php") if "molosoc-pillar-hero" in t.read_text(encoding="utf-8")]


class JournalEnqueue(unittest.TestCase):
    def test_enqueue_branch_uses_the_helper_and_loads_pillar1_once(self):
        self.assertEqual(FUNCS.count("assets/css/pillar1.css"), 1)
        branch = re.search(r"elseif \( molosoc_is_journal_article\(\) \) \{(.*?)\n\t\} elseif", FUNCS, re.S).group(1)
        self.assertIn("'molosoc-pillar1'", branch)

    def test_every_existing_article_template_is_still_covered(self):
        self.assertEqual(len(ARTICLE_TEMPLATES), 13)
        for tpl in ARTICLE_TEMPLATES:
            slug = tpl.stem[len("page-"):]
            self.assertIn(f"'{slug}'", HELPER, tpl.name)

    def test_czech_siblings_still_listed(self):
        for slug in ("popraskane-paty", "zarostly-nehet", "kurici-oko", "jak-odstranit"):
            self.assertIn(f"'{slug}'", HELPER)

    def test_new_articles_inherit_via_template_naming_convention(self):
        self.assertIn("'page-journal-'", HELPER)
        self.assertIn("get_page_template_slug()", HELPER)
        self.assertIn("molosoc_journal_article_slugs", HELPER)

    def test_non_journal_pages_not_matched(self):
        for slug in ("foot-covers", "moisture-lock-foot-cover", "blog", "magazin", "thank-you"):
            self.assertNotIn(f"'{slug}'", HELPER)

    def test_doc_describes_the_convention(self):
        self.assertIn("page-journal-", DOC)
        self.assertIn("pillar1.css", DOC)


if __name__ == "__main__":
    unittest.main()
