"""Issue #273: shared editorial layout for the lower Journal article sections (static checks, no PHP runtime)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "site/theme"
CSS = (THEME / "assets/css/pillar1.css").read_text(encoding="utf-8")
HELPER = (THEME / "inc/related-links.php").read_text(encoding="utf-8")

SPOKES_WITH_BACK_BAND = (
    "page-callus-remover.php", "page-cracked-heels-cream.php", "page-cracked-heels-treatment.php",
    "page-fix-permanently.php", "page-na-chodidle.php", "page-prevent.php", "page-treatment.php",
)
FAQ_TEMPLATES = {
    "page-cracked-heels.php": "Časté otázky o popraskaných patách",
    "page-sucha-kuze-na-chodidlech.php": "Časté otázky o suché kůži na chodidlech",
}


def clamp_px(name):
    """(min px, max px) of a `--name: clamp(<min>rem, …, <max>rem)` token."""
    m = re.search(rf"--{name}: clamp\(([\d.]+)rem, [^,]+, ([\d.]+)rem\);", CSS)
    assert m, name
    return float(m.group(1)) * 16, float(m.group(2)) * 16


class ArticleTypeScale(unittest.TestCase):
    """Body 16–18px, H2 28–34px, H3 21–24px, ~760–850px measure (Issue #273)."""

    def test_tokens_are_scoped_to_main_and_within_brief(self):
        self.assertIn("\nmain {\n  /* 800px", CSS)
        self.assertEqual(clamp_px("article-text"), (17.0, 18.0))
        self.assertEqual(clamp_px("article-h2"), (28.0, 34.0))
        self.assertEqual(clamp_px("article-h3"), (21.0, 24.0))
        measure = float(re.search(r"--article-measure: ([\d.]+)rem;", CSS).group(1)) * 16
        self.assertTrue(760 <= measure <= 850, measure)

    def test_prose_block_uses_the_tokens(self):
        rules = {
            ".molosoc-pillar-dry-skin .molosoc-section__inner": "max-width: var(--article-measure);",
            ".molosoc-pillar-dry-skin h2": "font-size: var(--article-h2);",
            ".molosoc-pillar-dry-skin h3": "font-size: var(--article-h3);",
            ".molosoc-pillar-dry-skin p:not(.molosoc-eyebrow)": "font-size: var(--article-text);",
            ".molosoc-pillar-back h2": "font-size: var(--article-h2);",
        }
        for sel, decl in rules.items():
            block = CSS.split(sel + " {", 1)[1].split("}", 1)[0]
            self.assertIn(decl, block, sel)
        # the paragraph no longer inherits base.css's 36rem cap inside the column
        p_block = CSS.split(".molosoc-pillar-dry-skin p:not(.molosoc-eyebrow) {", 1)[1].split("}", 1)[0]
        self.assertIn("max-width: none;", p_block)

    def test_one_vertical_rhythm_for_every_lower_section(self):
        for sel in (".molosoc-pillar-dry-skin", ".molosoc-pillar-back", ".molosoc-related-links"):
            block = CSS.split("\n" + sel + " {", 1)[1].split("}", 1)[0]
            self.assertIn("padding: var(--article-section-y) var(--section-padding-x);", block, sel)
        self.assertIn(".molosoc-pillar-go-deeper {\n  padding-bottom: var(--article-section-y);", CSS)
        self.assertIn(".molosoc-pillar-final-cta {\n  padding-top: clamp(", CSS)

    def test_legacy_selectors_still_present(self):
        # Issues #218/#239/#243 tests and anything else referencing them keep resolving.
        for sel in (".molosoc-pillar-dry-skin h2:not(:first-of-type)", ".molosoc-pillar-see-doctor ul",
                    ".molosoc-pillar-causes-care ul", ".molosoc-pillar-final-cta--halo .molosoc-btn {"):
            self.assertIn(sel, CSS, sel)

    def test_upper_sections_untouched(self):
        # Nothing above the mechanism card gets an article-* token.
        upper = CSS.split("/* 4b. ARTICLE BODY", 1)[0]
        self.assertNotIn("--article-", upper)
        for sel in (".molosoc-pillar-hero {", ".molosoc-argument {", ".molosoc-severity-card {", ".molosoc-mechanism-drawer {"):
            self.assertIn(sel, upper, sel)


class FaqMarkup(unittest.TestCase):
    def test_faq_pairs_are_wrapped_and_hierarchy_unchanged(self):
        for name, h2 in FAQ_TEMPLATES.items():
            src = (THEME / name).read_text(encoding="utf-8")
            after_h2 = src.split(f"<h2>{h2}</h2>", 1)[1]
            self.assertTrue(after_h2.lstrip().startswith('<div class="molosoc-pillar-faq">'), name)
            faq = after_h2.split('<div class="molosoc-pillar-faq">', 1)[1].split("\t\t\t</div>", 1)[0]
            self.assertEqual(len(re.findall(r"<h3>", faq)), 3, name)
            self.assertEqual(len(re.findall(r"<p>", faq)), 3, name)
            self.assertNotIn("<h2>", faq, name)
            self.assertNotIn("<details", faq, name)  # plain h3/p pairs, no accordion
        self.assertIn(".molosoc-pillar-faq {", CSS)
        self.assertIn(".molosoc-pillar-dry-skin .molosoc-pillar-faq h3 {", CSS)
        self.assertIn(".molosoc-pillar-dry-skin .molosoc-pillar-faq p {", CSS)


class BackBandAndRelatedLinks(unittest.TestCase):
    def test_spokes_back_band_has_class_and_no_inline_style(self):
        for name in SPOKES_WITH_BACK_BAND:
            src = (THEME / name).read_text(encoding="utf-8")
            self.assertIn('class="molosoc-section molosoc-section--bg-cream molosoc-pillar-back"', src, name)
            self.assertNotIn('style="text-align:center;"', src, name)
            self.assertRegex(src, r'molosoc-pillar-back">\s*<div class="molosoc-section__inner">\s*<p class="molosoc-eyebrow">', name)

    def test_related_links_helper_uses_classes(self):
        self.assertIn('<ul class="molosoc-related-links__list">', HELPER)
        self.assertNotIn("style=", HELPER)
        self.assertIn(".molosoc-related-links__list a {", CSS)

    def test_no_journal_template_keeps_the_old_centred_inline_style(self):
        for tpl in THEME.glob("page-*.php"):
            src = tpl.read_text(encoding="utf-8")
            if "molosoc_related_links(" in src:
                self.assertNotIn('style="text-align:center;"', src, tpl.name)


class ThemeVersion(unittest.TestCase):
    def test_style_version_bumped_for_the_css_deploy(self):
        style = (THEME / "style.css").read_text(encoding="utf-8")
        ver = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", style, re.M)
        self.assertIsNotNone(ver)
        self.assertGreaterEqual(tuple(int(x) for x in ver.groups()), (0, 2, 101))


if __name__ == "__main__":
    unittest.main()
