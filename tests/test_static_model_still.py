"""Issue #149: the 3D model is a static <img> still, model-viewer is gone.

No PHP runtime needed. Asserts that every template that used to render
molosoc-3d.glb through <model-viewer> now carries the plain
molosoc-hero-still.webp <img> instead, that functions.php no longer
enqueues the unpkg.com module (or warms its origin up), and that the two
CSS files size the still as an image (height from its intrinsic ratio).
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
FUNCTIONS = ROOT / "functions.php"
STILL = "https://molosoc.com/wp-content/uploads/2026/10/molosoc-hero-still.webp"

HERO_TEMPLATE = "page-moisture-lock-foot-cover.php"
JOURNAL_TEMPLATES = [
    "page-cracked-heels.php",
    "page-prevent.php",
    "page-dry-skin-feet.php",
    "page-fix-permanently.php",
    "page-callus-remover.php",
    "page-ingrown-toenails.php",
    "page-hardened-skin-calluses.php",
    "page-na-chodidle.php",
    "page-treatment.php",
    "page-cracked-heels-cream.php",
    "page-cracked-heels-treatment.php",
    "page-foot-cream-that-works.php",
]

IMG_RE = re.compile(r"<img\b[^>]*>", re.S)


def _img_with_class(src, cls):
    tags = [t for t in IMG_RE.findall(src) if f'class="{cls}"' in t]
    return tags


class StaticModelStill(unittest.TestCase):
    def test_no_template_uses_model_viewer(self):
        # A real element opens with an attribute or newline after the tag
        # name; "<model-viewer>" inside an HTML/PHP comment is just history.
        tag = re.compile(r"<model-viewer[\s>][^>]*\bsrc=")
        for path in sorted(ROOT.glob("page-*.php")):
            self.assertIsNone(tag.search(path.read_text(encoding="utf-8")), path.name)

    def test_product_hero_is_the_still(self):
        src = (ROOT / HERO_TEMPLATE).read_text(encoding="utf-8")
        tags = _img_with_class(src, "molosoc-orbit-model")
        self.assertEqual(len(tags), 1)
        tag = tags[0]
        for attr in (
            f'src="{STILL}"', 'alt=""', 'width="1440"', 'height="1440"',
            'fetchpriority="high"', 'decoding="async"',
        ):
            self.assertIn(attr, tag)
        self.assertNotIn("loading=", tag)  # above the fold: never lazy
        self.assertNotIn("molosoc-3d.glb' )", src)

    def test_journal_mechanism_stills(self):
        for name in JOURNAL_TEMPLATES:
            src = (ROOT / name).read_text(encoding="utf-8")
            tags = _img_with_class(src, "molosoc-mechanism-model")
            self.assertEqual(len(tags), 1, name)
            tag = tags[0]
            for attr in (
                f'src="{STILL}"', 'alt=""', 'width="1440"', 'height="1440"',
                'loading="lazy"', 'decoding="async"',
            ):
                self.assertIn(attr, tag, name)
            self.assertNotIn("molosoc-3d.glb' )", src, name)

    def test_functions_php_drops_model_viewer_entirely(self):
        src = FUNCTIONS.read_text(encoding="utf-8")
        self.assertNotIn("wp_enqueue_script( 'molosoc-model-viewer'", src)
        self.assertNotIn("unpkg.com/@google/model-viewer", src)
        self.assertNotIn("'https://unpkg.com'", src)
        self.assertNotIn("molosoc_module_script_tag", src)
        self.assertNotIn("'molosoc-model-viewer' !== $handle", src)

    def test_css_sizes_the_still_as_an_image(self):
        for css, cls in (
            ("assets/css/product.css", "molosoc-orbit-model"),
            ("assets/css/pillar1.css", "molosoc-mechanism-model"),
        ):
            src = (ROOT / css).read_text(encoding="utf-8")
            base = re.search(r"^\." + re.escape(cls) + r" \{(.*?)^\}", src, re.S | re.M)
            self.assertIsNotNone(base, css)
            body = base.group(1)
            for decl in ("display: block;", "object-fit: contain;", "height: auto;", "max-width: 100%;"):
                self.assertIn(decl, body, (css, decl))
            self.assertIsNotNone(re.search(r"^\s*width: min\(", body, re.M), (css, "width kept"))
            self.assertNotIn("--poster-color", src, css)
            self.assertNotIn("--progress-bar-color", src, css)
            # Every rule for the class (base + mobile) must leave height: auto.
            for m in re.finditer(r"\." + re.escape(cls) + r" \{(.*?)\}", src, re.S):
                heights = re.findall(r"^\s*height:\s*([^;]+);", m.group(1), re.M)
                self.assertEqual(heights, ["auto"], (css, m.group(1)[:80]))


if __name__ == "__main__":
    unittest.main()
