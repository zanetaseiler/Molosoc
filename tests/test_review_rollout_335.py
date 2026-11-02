"""Issue #335: CusRev checkbox hiding is opt-in and checkout-only."""
import unittest
from pathlib import Path

SRC = (Path(__file__).resolve().parents[1] / "site/theme/inc/checkout-cleanup.php").read_text()


class HideCusrev(unittest.TestCase):
    def test_default_off_and_checkout_only(self):
        fn = SRC.split("function molosoc_hide_cusrev_checkbox_css", 1)[1].split("add_action", 1)[0]
        self.assertIn("'molosoc_hide_cusrev_checkbox', '0'", fn)
        self.assertIn("is_checkout()", fn)
        self.assertLess(fn.index("'1' !=="), fn.index("echo"))

    def test_hooked(self):
        self.assertIn("add_action( 'wp_head', 'molosoc_hide_cusrev_checkbox_css'", SRC)


if __name__ == "__main__":
    unittest.main()
