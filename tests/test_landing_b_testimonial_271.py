"""Issues #271/#278: the Landing B feedback summary is flag-gated and enabled only for the Landing B template."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
TEMPLATE = (ROOT / "page-hydratacni-navleky-molosoc.php").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-b.css").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
QUOTE = ("Jedna zákaznice nám napsala, že její maminka je s návleky MOLOSOC velmi spokojená "
         "a pohodlně je nosí přibližně 30 minut.")


class TestimonialGate(unittest.TestCase):
    def test_flag_defaults_to_false_and_wraps_the_block(self):
        gate = "apply_filters( 'molosoc_landing_b_testimonial_enabled', false )"
        self.assertIn(gate, TEMPLATE)
        self.assertLess(TEMPLATE.index(gate), TEMPLATE.index('class="lpb-testimonial"'))
        self.assertLess(TEMPLATE.index(QUOTE), TEMPLATE.index("<?php endif; ?>\n\t\t<div class=\"lpb-section__cta\">", TEMPLATE.index(gate)))

    def test_summary_text_is_exact_and_inside_the_real_section(self):
        self.assertEqual(TEMPLATE.count(QUOTE), 1)
        sec = TEMPLATE.index('aria-label="MOLOSOC v reálu"')
        self.assertGreater(TEMPLATE.index(QUOTE), sec)
        self.assertLess(TEMPLATE.index(QUOTE), TEMPLATE.index('aria-label="Jak to vše začalo"'))

    def test_attribution_is_filter_driven_and_nothing_hardcoded(self):
        self.assertIn("molosoc_landing_b_testimonial_attribution", TEMPLATE)
        for banned in ("Lucie", "ověřený nákup", "psoria", "Ověřený"):
            self.assertNotIn(banned, TEMPLATE)

    def test_section_cta_kept_and_css_present(self):
        sec = TEMPLATE[TEMPLATE.index('aria-label="MOLOSOC v reálu"'):TEMPLATE.index('aria-label="Jak to vše začalo"')]
        self.assertIn("molosoc_landing_b_buy_cta();", sec)
        self.assertIn(".lpb-testimonial", CSS)


class Enabled278(unittest.TestCase):
    def test_flag_enabled_only_on_landing_b_page(self):
        self.assertIn("add_filter( 'molosoc_landing_b_testimonial_enabled'", FUNCTIONS)
        self.assertIn("is_page( 'hydratacni-navleky-molosoc' ) ? true : $enabled", FUNCTIONS)

    def test_indirect_speech_not_a_verbatim_quote(self):
        block = TEMPLATE[TEMPLATE.index('class="lpb-testimonial"'):TEMPLATE.index("<?php endif; ?>\n\t\t<div class=\"lpb-section__cta\">")]
        self.assertNotIn("<blockquote", block)
        for quote_mark in ("„", "“", '"', "”"):
            self.assertNotIn(quote_mark, block.split(">", 1)[1].replace('class="lpb-testimonial__title"', ""))
        self.assertNotIn("Zkusila jsem koupit", TEMPLATE)


class AnonymousCard276(unittest.TestCase):
    def test_card_heading_inside_gate_and_css(self):
        gate = TEMPLATE.index("apply_filters( 'molosoc_landing_b_testimonial_enabled', false )")
        self.assertGreater(TEMPLATE.index("Co o nás říkají zákazníci"), gate)
        self.assertIn(".lpb-testimonial__title", CSS)

    def test_no_health_or_name_claims(self):
        block = TEMPLATE[TEMPLATE.index('class="lpb-testimonial"'):TEMPLATE.index("<?php endif; ?>\n\t\t<div class=\"lpb-section__cta\">")]
        for banned in ("psoria", "léč", "zlepš", "ověřen"):
            self.assertNotIn(banned, block)


if __name__ == "__main__":
    unittest.main()
