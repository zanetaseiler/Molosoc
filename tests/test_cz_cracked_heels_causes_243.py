"""Issue #243: CZ cracked-heels causes / care / physician section, CZ-only."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "site/theme/page-cracked-heels.php").read_text(encoding="utf-8")
START = SRC.index("4a. CZ ONLY")
BLOCK = SRC[START:SRC.index("4b. CZ ONLY")]
FAQ = SRC[SRC.index("4b. CZ ONLY"):SRC.index("5. GO DEEPER")]


class CzCrackedHeelsCauses(unittest.TestCase):
    def test_cz_only_and_headings(self):
        self.assertIn("if ( $molosoc_is_cz )", BLOCK)
        for h in ("Další příčiny popraskaných pat", "Co na prasklé paty", "Kdy nečekat a jít k lékaři"):
            self.assertIn(h, BLOCK)
        self.assertNotIn("<a ", BLOCK)
        self.assertNotIn("<h3>", BLOCK)  # no extra FAQ-style headings

    def test_no_cure_claims_or_scope_drift(self):
        low = BLOCK.lower()
        for bad in ("zim", "ingrown", "zarostl", "kuří oko", "vyléč", "zahoj", "zaručen", "léčb"):
            self.assertNotIn(bad, low)

    def test_no_duplication_with_existing_copy(self):
        body = re.sub(r"<[^>]+>", " ", BLOCK)
        for existing in ("Jak často natírat paty krémem?", "Pomáhá krém na nohy přes noc?",
                         "Kdy s popraskanými patami k lékaři?", "mytí vlažnou vodou"):
            self.assertNotIn(existing, body)
        self.assertEqual(SRC.count("Kdy s popraskanými patami k lékaři?"), 1)

    def test_en_and_existing_structure_preserved(self):
        self.assertEqual(SRC.count("<h1>"), 1)
        self.assertIn("Popraskané paty: co se skutečně děje a co pomáhá", SRC)
        self.assertEqual(SRC.count("molosoc_landing_url("), 2)  # Issue #303: in-text link (cz) + bilingual CTA
        self.assertEqual(len(re.findall(r"<h3>", FAQ)), 3)
        self.assertIn("molosoc_related_links( 'cracked-heels' );", SRC)
        # the block sits between the mechanism section and the 4b FAQ section
        self.assertLess(SRC.index("molosoc-mechanism-section"), START)

    def test_list_style_scoped(self):
        css = (ROOT / "site/theme/assets/css/pillar1.css").read_text(encoding="utf-8")
        self.assertIn(".molosoc-pillar-causes-care ul", css)


if __name__ == "__main__":
    unittest.main()
