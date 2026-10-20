"""Issue #220: the live size slugs `m-medium` / `l-large` must be recognised by
molosoc_size_value_rank(), which drives the Landing B direct-checkout URLs, so
both size choices resolve a variation (resolved from WooCommerce data, never a
hardcoded ID) and neither is preselected. Runs the real PHP function via the
`php` CLI (skipped if unavailable)."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
LANG = (ROOT / "inc/woocommerce-lang.php").read_text(encoding="utf-8")
BUY = (ROOT / "inc/landing-b-buy.php").read_text(encoding="utf-8")


def rank(value):
    fn = re.search(r"function molosoc_size_value_rank\(.*?\n}\n", LANG, re.S).group(0)
    code = "<?php\n%s\necho molosoc_size_value_rank(%s);" % (fn, "'" + value.replace("'", "\\'") + "'")
    return int(subprocess.run(["php", "-r", code[6:]], capture_output=True, text=True, check=True).stdout)


@unittest.skipUnless(shutil.which("php"), "php CLI not available")
class LiveSizeSlugs(unittest.TestCase):
    def test_live_slugs_rank_m_and_l(self):
        self.assertEqual(rank("m-medium"), 0)
        self.assertEqual(rank("l-large"), 1)
        self.assertEqual(rank(" L-Large "), 1)

    def test_previous_spellings_and_unknowns_unchanged(self):
        for v, r in (("m", 0), ("medium", 0), ("36-39", 0), ("l", 1), ("large", 1), ("39.5-44", 1),
                     ("xl", 2), ("", 2), ("m-large", 2)):
            self.assertEqual(rank(v), r, v)


class NoDefaultNoHardcodedId(unittest.TestCase):
    def test_no_preselected_size_and_no_hardcoded_variation_id(self):
        self.assertNotIn("checked", BUY)
        self.assertNotRegex(BUY, r"\b42[45]\b")
        self.assertIn("$variation_id", BUY)
        self.assertIn("'quantity'     => 1", BUY)


if __name__ == "__main__":
    unittest.main()
