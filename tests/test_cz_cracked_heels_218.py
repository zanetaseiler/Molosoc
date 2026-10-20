"""Issue #218: CZ cracked-heels pillar section, FAQ and single contextual link."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "site/theme/page-cracked-heels.php").read_text(encoding="utf-8")
PRODUCT = "/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/"


class CzCrackedHeels(unittest.TestCase):
    def test_contextual_link_in_mechanism_section_only_once(self):
        start = SRC.index("molosoc-mechanism-section")
        end = SRC.index("4b. CZ ONLY")
        self.assertEqual(SRC[start:end].count(PRODUCT), 1)
        # one contextual link + the existing bottom CTA, nothing else
        self.assertEqual(SRC.count(PRODUCT), 2)

    def test_no_fragment_links(self):
        self.assertNotRegex(SRC, r"href=[^>]*#")

    def test_new_section_and_faq_present_cz_only(self):
        block = SRC[SRC.index("4b. CZ ONLY"):SRC.index("5. GO DEEPER")]
        self.assertIn("if ( $molosoc_is_cz )", block)
        for h in ("Suchá kůže na patách a chodidlech", "Jak často natírat paty krémem?",
                  "Pomáhá krém na nohy přes noc?", "Kdy s popraskanými patami k lékaři?"):
            self.assertIn(h, block)
        self.assertNotIn("<a ", block)
        self.assertEqual(len(re.findall(r"<h3>", block)), 3)

    def test_preserved_parts_and_scope(self):
        self.assertIn("molosoc_related_links( 'cracked-heels' );", SRC)
        self.assertIn("molosoc-pillar-final-cta", SRC)
        self.assertEqual(SRC.count("<h1>"), 1)
        for bad in ("zim", "ingrown", "zarostl", "kuří oko", "vyléč", "zahoj"):
            block = SRC[SRC.index("4b. CZ ONLY"):SRC.index("5. GO DEEPER")]
            self.assertNotIn(bad, block.lower())

    def test_dry_skin_block_has_scoped_spacing(self):
        css = (ROOT / "site/theme/assets/css/pillar1.css").read_text(encoding="utf-8")
        for sel in (".molosoc-pillar-dry-skin h2", ".molosoc-pillar-dry-skin h3",
                    ".molosoc-pillar-dry-skin p:not(.molosoc-eyebrow) + p"):
            self.assertIn(sel, css)


if __name__ == "__main__":
    unittest.main()
