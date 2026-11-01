"""Issue #317: bilingual Christmas announcement bar above the nav. The PHP is
rendered through minimal WordPress stubs (php CLI); the rest are static checks."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
STUB = REPO / "tests/fixtures/xmas_bar_stub_317.php"
HEADER = (ROOT / "template-parts/site-header.php").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/xmas-bar.css").read_text(encoding="utf-8")
INC = (ROOT / "inc/xmas-bar.php").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")


def render(lang, mode=""):
    if not shutil.which("php"):
        raise unittest.SkipTest("no php")
    return subprocess.run(["php", str(STUB), lang, mode], capture_output=True, text=True, check=True).stdout


class Copy(unittest.TestCase):
    def test_czech_text_and_existing_czech_landing(self):
        out = render("cz")
        self.assertIn("🎄 Tip na vánoční dárek — Objevte vánoční nabídku MOLOSOC", out)
        self.assertIn('href="https://example.test/cz/vanocni-darek-molosoc/"', out)
        self.assertIn('aria-label="Zavřít oznámení"', out)
        self.assertNotIn("Christmas Gift Idea", out)

    def test_english_text_and_existing_english_landing(self):
        out = render("en")
        self.assertIn("🎄 Christmas Gift Idea — Discover the MOLOSOC Holiday Offer", out)
        self.assertIn('href="https://example.test/christmas-gift-molosoc/"', out)
        self.assertIn('aria-label="Close announcement"', out)
        self.assertNotIn("vánoční", out)

    def test_urls_come_from_the_existing_slug_helper_not_hard_coded(self):
        self.assertIn("molosoc_xmas_slugs()[ $lang ]", INC)
        code = re.sub(r"/\*.*?\*/", "", INC, flags=re.S)
        self.assertNotIn("vanocni-darek", code)
        self.assertNotIn("christmas-gift-molosoc", code)


class Hidden(unittest.TestCase):
    def test_not_on_christmas_pages_checkout_unpublished_or_switched_off(self):
        for mode in ("landing", "checkout", "draft", "off"):
            for lang in ("cz", "en"):
                self.assertEqual(render(lang, mode).strip(), "", (lang, mode))


class Accessibility(unittest.TestCase):
    def test_markup(self):
        out = render("en")
        self.assertIn('role="region"', out)
        self.assertIn('<button type="button" class="molosoc-xmas-bar__close"', out)
        self.assertIn('aria-hidden="true">&times;', out)

    def test_dismiss_is_storage_safe(self):
        self.assertEqual(INC.count("try{"), 2)
        self.assertIn("sessionStorage", INC)
        self.assertNotIn("localStorage.", INC)
        self.assertIn("b.hidden=true", INC)
        self.assertIn("MOLOSOC_XMAS_BAR_KEY", INC)

    def test_touch_target_focus_and_hidden_rule(self):
        self.assertIn("width: 2.75rem;\n  height: 2.75rem;", CSS[CSS.index(".molosoc-xmas-bar__close {"):])
        self.assertIn(".molosoc-xmas-bar__close:focus-visible", CSS)
        self.assertIn(".molosoc-xmas-bar[hidden] {\n  display: none;", CSS)


class Layout(unittest.TestCase):
    def test_in_flow_not_fixed_so_menu_and_sticky_cta_are_untouched(self):
        css = CSS
        self.assertNotIn("position: fixed", css)
        self.assertNotIn("position: sticky", css)

    def test_rendered_above_the_header_element(self):
        self.assertLess(HEADER.index("molosoc_xmas_bar();"), HEADER.index('<header class="molosoc-site-header">'))
        self.assertIn("inc/xmas-bar.php", FUNCTIONS)
        self.assertIn("'molosoc-xmas-bar', get_stylesheet_directory_uri() . '/assets/css/xmas-bar.css'", INC)

    def test_palette_ivory_champagne_gold(self):
        # Issue #320: restyled from burgundy to warm ivory/champagne + gold.
        for c in ("#fbf5e6", "#f6ebd0", "#d9b66a", "#3d2f22"):
            self.assertIn(c, CSS)
        self.assertNotIn("#6b1d2a", CSS)

    def test_taller_and_whole_bar_clickable(self):
        bar = CSS[CSS.index(".molosoc-xmas-bar {"):]
        self.assertIn("min-height: 3.75rem;", bar)
        self.assertIn(".molosoc-xmas-bar__link::after", CSS)
        self.assertIn("inset: 0;", CSS[CSS.index(".molosoc-xmas-bar__link::after"):])
        close = CSS[CSS.index(".molosoc-xmas-bar__close {"):]
        self.assertIn("z-index: 2;", close)

    def test_prominent_not_underlined_issue_324(self):
        self.assertIn("font-family: var(--font-display);", CSS)
        self.assertIn("font-size: 1.2rem;", CSS)
        self.assertNotIn("text-decoration: underline", CSS)
        self.assertNotIn("text-underline-offset", CSS)
        self.assertIn("molosoc-xmas-bar__spark", INC)

    def test_contrast_at_least_aa(self):
        def lum(h):
            r, g, b = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
        ratio = lambda a, b: (max(lum(a), lum(b)) + 0.05) / (min(lum(a), lum(b)) + 0.05)
        for bg in ("#fbf5e6", "#f6ebd0"):
            self.assertGreaterEqual(ratio("#3d2f22", bg), 7)
            self.assertGreaterEqual(ratio("#7a5c1a", bg), 4.5)  # x button + focus ring


class Version(unittest.TestCase):
    def test_bumped(self):
        v = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M)
        self.assertGreaterEqual(tuple(map(int, v.groups())), (0, 2, 118))


if __name__ == "__main__":
    unittest.main()
