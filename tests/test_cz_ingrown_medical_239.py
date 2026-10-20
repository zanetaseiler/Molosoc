"""Issue #239: ingrown-toenail pillar — healing claim removed, CZ doctor-escalation section, EN isolation."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "site/theme/page-ingrown-toenails.php").read_text(encoding="utf-8")
START = SRC.index("3b. CZ ONLY")
END = SRC.index("4. WHY CUTTING IT YOURSELF")
BLOCK = SRC[START:END]
PRODUCT_CZ = "/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/"
PRODUCT_EN = "/foot-covers/moisture-lock-foot-cover/"


class IngrownMedical(unittest.TestCase):
    def test_misleading_claims_removed(self):
        for bad in ("zahojené díky pravidelné péči", "treated through consistent care"):
            self.assertNotIn(bad, SRC)

    def test_cta_honest_and_unchanged_structure(self):
        cta = SRC[SRC.index("FINAL CTA"):]
        self.assertIn("Zarostlý nehet neléčí", cta)
        self.assertIn("does not treat an ingrown toenail", cta)
        self.assertEqual(cta.count(PRODUCT_CZ), 1)
        self.assertEqual(cta.count(PRODUCT_EN), 1)
        self.assertIn("molosoc-pillar-final-cta__card", cta)

    def test_warning_section_cz_only_and_complete(self):
        self.assertIn("if ( $molosoc_is_cz )", BLOCK)
        self.assertIn("<?php endif; ?>", BLOCK)
        self.assertIn("Kdy nečekat a jít k lékaři", BLOCK)
        for word in ("zarudnutí", "otok", "hnis", "bolest", "horečku", "cukrovku", "prokrvení"):
            self.assertIn(word, BLOCK)
        self.assertIn("nenasazujte na poraněnou nebo zanícenou kůži", BLOCK)
        self.assertNotIn("<a ", BLOCK)

    def test_warning_after_worsening_section_before_next(self):
        self.assertLess(SRC.index("Kdy neodezní — příznaky zhoršení"), START)

    def test_en_isolated_from_cz_warning(self):
        en_only = SRC.replace(BLOCK, "")
        self.assertNotIn("Kdy nečekat a jít k lékaři", en_only)

    def test_scope_preserved(self):
        self.assertEqual(SRC.count("<h1>"), 1)
        self.assertNotIn("schema", BLOCK.lower().replace("no schema", ""))

    def test_php_lint(self):
        try:
            r = subprocess.run(["php", "-l", str(ROOT / "site/theme/page-ingrown-toenails.php")],
                               capture_output=True, text=True)
        except FileNotFoundError:
            self.skipTest("php not installed")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
