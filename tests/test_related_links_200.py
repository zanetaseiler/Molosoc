"""Issue #200: contextual Related-reading links (static checks, no PHP runtime)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "site/theme"
HELPER = (THEME / "inc/related-links.php").read_text(encoding="utf-8")

TEMPLATES = {
    "page-cracked-heels.php": "cracked-heels",
    "page-ingrown-toenails.php": "ingrown-toenails",
    "page-hardened-skin-calluses.php": "hardened-skin-calluses",
    "page-fix-permanently.php": "fix-permanently",
    "page-cracked-heels-treatment.php": "cracked-heels-treatment",
    "page-treatment.php": "ingrown-treatment",
    "page-prevent.php": "ingrown-prevent",
    "page-callus-remover.php": "callus-remover",
    "page-na-chodidle.php": "callus-remover",
}


class RelatedLinks(unittest.TestCase):
    def test_required_from_functions(self):
        src = (THEME / "functions.php").read_text(encoding="utf-8")
        self.assertIn("/inc/related-links.php", src)

    def test_templates_call_helper_with_known_key(self):
        keys = set(re.findall(r"^\t\t'([a-z-]+)'\s+=> array\(", HELPER, re.M))
        for name, key in TEMPLATES.items():
            src = (THEME / name).read_text(encoding="utf-8")
            self.assertIn(f"molosoc_related_links( '{key}' );", src, name)
            self.assertIn(key, keys, name)

    def test_cz_targets_are_existing_cz_pages(self):
        cz = re.findall(r"=> '(/cz/[^']+)'", HELPER)
        self.assertEqual(
            sorted(cz),
            ["/cz/kurici-oko/", "/cz/magazin/", "/cz/popraskane-paty/", "/cz/zarostly-nehet/"],
        )

    def test_en_targets_are_known_urls(self):
        known = {
            "/cracked-heels/", "/ingrown-toenails/", "/hardened-skin-calluses/", "/blog/",
            "/cracked-heels/cracked-heels-treatment/", "/cracked-heels/cracked-heels-cream/",
            "/cracked-heels/fix-permanently/", "/ingrown-toenails/treatment/",
            "/ingrown-toenails/prevent/",
        }
        for path in re.findall(r"array\( '(/[^']+)', '", HELPER):
            self.assertIn(path, known)


if __name__ == "__main__":
    unittest.main()
