"""Issue #335: landings show real approved native reviews only, nothing synthesized."""
import unittest
from pathlib import Path

T = Path(__file__).resolve().parents[1] / "site/theme"
H = (T / "inc/real-reviews.php").read_text(encoding="utf-8")


class RealReviews(unittest.TestCase):
    def test_queries_only_approved_native_reviews_of_product(self):
        for needle in ("'status'  => 'approve'", "'type'    => 'review'", "MOLOSOC_PRODUCT_ID"):
            self.assertIn(needle, H)

    def test_empty_when_no_reviews_and_no_hardcoded_text(self):
        self.assertIn("if ( ! $reviews ) {\n\t\treturn '';", H)
        self.assertNotIn("comment_author_email", H)
        self.assertNotIn("“", H)

    def test_wired_into_all_landings_and_loaded(self):
        self.assertIn("inc/real-reviews.php", (T / "functions.php").read_text(encoding="utf-8"))
        for f in ("page-hydratacni-navleky-molosoc.php", "page-hydrating-foot-covers-molosoc.php", "template-parts/landing-xmas.php"):
            self.assertIn("molosoc_real_reviews_html(", (T / f).read_text(encoding="utf-8"), f)

    def test_styles_inline_so_guarded_css_files_stay_untouched(self):
        self.assertIn('<style id="molosoc-real-reviews-css">', H)

    def test_checkout_place_order_untouched(self):
        self.assertNotIn("place-order", H)


if __name__ == "__main__":
    unittest.main()
