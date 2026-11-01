"""Issue #320: the Foot Covers hero product must not be veiled by its scrim."""
import re
import unittest
from pathlib import Path

CSS = (Path(__file__).resolve().parents[1] / "site/theme/assets/css/category.css").read_text(encoding="utf-8")


def alphas(block):
    return [float(a) for a in re.findall(r"rgba\(255, 255, 255, ([\d.]+)\)", block)]


class HeroScrim(unittest.TestCase):
    def test_desktop_scrim_clear_before_photo_half(self):
        i = CSS.index(".molosoc-category-hero__scrim {")
        blk = CSS[i:CSS.index("}", i)]
        self.assertIn("rgba(255, 255, 255, 0) 50%", blk)  # photo starts at 50%

    def test_mobile_scrim_light_and_fades_out(self):
        i = CSS.index("@media (max-width: 860px)")
        m = CSS[i:]
        j = m.index(".molosoc-category-hero__scrim {")
        blk = m[j:m.index("}", j)]
        a = alphas(blk)
        self.assertLess(max(a), 0.55)
        self.assertEqual(a[-1], 0)

    def test_photo_background_and_blend_untouched(self):
        self.assertIn("mix-blend-mode: multiply;", CSS)
        self.assertIn("rgba(252, 252, 252, 0.5)", CSS)


if __name__ == "__main__":
    unittest.main()
