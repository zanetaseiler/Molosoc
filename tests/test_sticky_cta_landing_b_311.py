"""Issue #311: the global sticky pill leads to Landing Page B of the current
language (molosoc_landing_url(): B when published, else the old destination),
while the Christmas pages keep their in-page picker target (Issue #299).
No PHP runtime needed; asserts the source contract.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
FN = (ROOT / "functions.php").read_text(encoding="utf-8")
NEW = (ROOT / "inc/sticky-landing-b.php").read_text(encoding="utf-8")
XMAS = (ROOT / "inc/landing-xmas.php").read_text(encoding="utf-8")
LINKS = (ROOT / "inc/landing-links.php").read_text(encoding="utf-8")
JS = (ROOT / "assets/js/sticky-cta.js").read_text(encoding="utf-8")


def _closure():
    a = FN.index("\tif ( molosoc_sticky_cta_hidden() ) {\n\t\treturn;\n\t}")
    return FN[a:FN.index("\n} );", a)]


class StickyCtaLandingB(unittest.TestCase):
    def test_filter_returns_landing_b_for_current_language(self):
        self.assertIn("$url  = molosoc_landing_url( $lang );", NEW)
        self.assertIn("'url'   => $url,", NEW)
        self.assertIn("'label' => ( 'cz' === $lang ) ? 'Koupit nyní' : __( 'Buy now', 'molosoc' ),", NEW)
        self.assertIn("add_filter( 'molosoc_sticky_cta_data', 'molosoc_sticky_cta_landing_b', 20, 2 );", NEW)

    def test_required_after_landing_links_and_xmas(self):
        r = FN.index("inc/sticky-landing-b.php")
        self.assertGreater(r, FN.index("inc/landing-links.php"))
        self.assertGreater(r, FN.index("inc/landing-xmas.php"))

    def test_landing_b_slugs_and_unpublished_fallback(self):
        self.assertIn("'hydratacni-navleky-molosoc'", LINKS)
        self.assertIn("'hydrating-foot-covers-molosoc'", LINKS)
        self.assertIn("'publish' === $page->post_status", LINKS)
        self.assertIn("$url  = molosoc_landing_a_url( $lang );", LINKS)

    def test_christmas_target_wins_and_stays_on_page(self):
        # runs after xmas (10) and keeps any target already set
        self.assertIn("! empty( $data['url'] )", NEW)
        self.assertIn("'molosoc_xmas_sticky_cta', 10, 2", XMAS)
        self.assertIn("'#lpx-bundle'", XMAS)
        self.assertNotIn("landing_url", XMAS)

    def test_gate_js_and_product_default_untouched(self):
        gate = FN[FN.index("function molosoc_sticky_cta_hidden()"):]
        gate = gate[:gate.index("\n}")]
        for needle in ("is_cart", "is_checkout", "is_product", "privacy-policies", "obchodni-podminky"):
            self.assertIn(needle, gate)
        self.assertIn("'url'   => molosoc_product_url( $lang ),", FN)  # default stays; filter overrides it
        self.assertNotIn("landing", JS.lower().replace("landing-xmas", ""))

    def test_no_self_link_on_destination_page(self):
        # Codex P2: on Landing B / EN Landing A fallback the URL is the current page
        self.assertIn("untrailingslashit( (string) get_permalink() ) === untrailingslashit( $url )", NEW)
        self.assertIn("$url = '#lpb-buy';", NEW)
        self.assertIn("$url = molosoc_product_url( $lang );", NEW)
        buy = (ROOT / "inc/landing-b-buy.php").read_text(encoding="utf-8")
        self.assertIn("1 === $group ? ' id=\"lpb-buy\"' : ''", buy)

    def test_no_redirects(self):
        self.assertNotIn("wp_redirect", NEW)
        self.assertNotIn("wp_safe_redirect", NEW)


if __name__ == "__main__":
    unittest.main()
