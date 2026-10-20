"""Issue #227: CZ-only 'Pro koho je (a pro koho není)' guidance on the product template."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TPL = ROOT / "site/theme/page-moisture-lock-foot-cover.php"
SRC = TPL.read_text(encoding="utf-8")
HEADING = "Pro koho je (a pro koho není)"


class CzProductSuitability(unittest.TestCase):
    def test_php_lint(self):
        r = subprocess.run(["php", "-l", str(TPL)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_block_is_cz_only_and_in_how_section(self):
        self.assertEqual(SRC.count(HEADING), 1)
        pos = SRC.index(HEADING)
        opener = SRC.rindex("<?php if ( $molosoc_is_cz ) : ?>", 0, pos)
        closer = SRC.index("<?php endif; ?>", pos)
        self.assertNotIn("<?php endif; ?>", SRC[opener:pos])
        self.assertNotIn("__(", SRC[opener:closer])  # no EN string leaks into the block
        self.assertGreater(pos, SRC.index("Co najdete v balení"))
        self.assertLess(pos, SRC.index("molosoc-product-buy"))

    def test_no_duplicate_instructions_or_forbidden_claims(self):
        pos = SRC.index(HEADING)
        block = SRC[pos:SRC.index("<?php endif; ?>", pos)].lower()
        for bad in ("30–60", "opláchn", "nechte působit", "vodotěs", "voděodoln",
                    "certifik", "přes noc", "klinick", "léč", "záruk"):
            self.assertNotIn(bad, block)
        self.assertEqual(SRC.count("nechte působit 30–60 minut"), 1)

    def test_en_template_and_purchase_flow_unchanged(self):
        self.assertIn("Charged as 229 CZK at checkout.", SRC)
        self.assertEqual(len(re.findall(r"molosoc_product_url\(\)", SRC)), 3)
        for en in ("How to use it", "Use it again", "How it works"):
            self.assertIn("__( '%s'" % en, SRC)


if __name__ == "__main__":
    unittest.main()
