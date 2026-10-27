"""Issue #273: editorial layout for the lower blog-article sections."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "site/theme"
CSS = (THEME / "assets/css/pillar1.css").read_text(encoding="utf-8")
BACKBAND_TPLS = (
    "page-callus-remover", "page-cracked-heels-cream", "page-cracked-heels-treatment",
    "page-fix-permanently", "page-na-chodidle", "page-prevent", "page-treatment",
)


def rule(selector):
    m = re.search(r"(?m)^" + re.escape(selector) + r" \{(.*?)\}", CSS, re.S)
    assert m, selector
    return m.group(1)


class ArticleTypography(unittest.TestCase):
    def test_prose_column_and_sizes(self):
        self.assertIn("max-width: 50rem", rule(".molosoc-pillar-dry-skin .molosoc-section__inner"))  # 800px
        self.assertIn("clamp(1.75rem, 1.2vw + 1.45rem, 2.125rem)", rule(".molosoc-pillar-dry-skin h2"))  # 28-34px
        self.assertIn("clamp(1.3125rem, 0.6vw + 1.15rem, 1.5rem)", rule(".molosoc-pillar-dry-skin h3"))  # 21-24px
        p = rule(".molosoc-pillar-dry-skin p:not(.molosoc-eyebrow)")
        self.assertIn("clamp(1rem, 0.3vw + 0.95rem, 1.125rem)", p)  # 16-18px
        self.assertIn("max-width: none", p)

    def test_faq_questions_separated(self):
        self.assertIn("border-top", rule(".molosoc-pillar-dry-skin h3"))
        self.assertIn("border-top: 0", rule(".molosoc-pillar-dry-skin h2 + h3"))


class LowerBands(unittest.TestCase):
    def test_backband_markup_uses_class_not_inline_style(self):
        for name in BACKBAND_TPLS:
            src = (THEME / f"{name}.php").read_text(encoding="utf-8")
            self.assertIn("molosoc-section--bg-cream molosoc-pillar-backband", src, name)
            self.assertNotIn('class="molosoc-section__inner" style="text-align:center;"', src, name)

    def test_related_links_inline_styles_removed(self):
        src = (THEME / "inc/related-links.php").read_text(encoding="utf-8")
        self.assertNotIn("style=", src)
        self.assertIn("molosoc-related-links", src)
        self.assertIn("text-align: center;", CSS.split(".molosoc-related-links .molosoc-section__inner {")[1].split("}")[0])

    def test_scoped_to_lower_sections_only(self):
        # upper visual sections untouched: no new rules on hero/severity/mechanism/topic selectors
        for sel in (".molosoc-pillar-hero", ".molosoc-severity-card", ".molosoc-mechanism-drawer"):
            self.assertNotIn("Issue #273", rule(sel))


if __name__ == "__main__":
    unittest.main()
