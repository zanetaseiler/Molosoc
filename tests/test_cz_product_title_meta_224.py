"""Issue #224: CZ product 364 gets the approved Czech <title> and meta description."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "site/theme/inc/woocommerce-lang.php").read_text(encoding="utf-8")
COPY = (ROOT / "i18n/cz/cz-product-copy.md").read_text(encoding="utf-8")


def copy_field(label):
    return re.search(r"\*\*%s:\*\*\s*(.+)" % re.escape(label), COPY).group(1).strip()


class CzProductTitleMeta(unittest.TestCase):
    def test_strings_match_approved_copy(self):
        self.assertIn(copy_field("Title tag"), SRC)
        self.assertIn(copy_field("Meta description"), SRC)

    def test_both_hooks_gated_to_cz_product_364(self):
        for fn in ("molosoc_cz_product_document_title", "molosoc_cz_product_meta_description"):
            body = SRC[SRC.index("function %s(" % fn):]
            body = body[:body.index("\n}\n")]
            self.assertIn("molosoc_is_cz_product_364()", body)
        self.assertIn("add_filter( 'pre_get_document_title', 'molosoc_cz_product_document_title' )", SRC)
        self.assertIn("add_action( 'wp_head', 'molosoc_cz_product_meta_description' )", SRC)

    def test_no_maska_na_nohy_target(self):
        # that phrase belongs to /cz/hydratacni-navleky-molosoc/
        self.assertNotIn("maska na nohy", copy_field("Title tag").lower())


if __name__ == "__main__":
    unittest.main()
