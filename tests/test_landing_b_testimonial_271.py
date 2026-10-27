"""Issue #271: the Landing B testimonial is consent-gated and off by default."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
TEMPLATE = (ROOT / "page-hydratacni-navleky-molosoc.php").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-b.css").read_text(encoding="utf-8")
QUOTE = ("Zkusila jsem koupit vaše návleky a maminka je s nimi nesmírně spokojená. "
         "Vydrží je mít 30 minut na nohách úplně v pohodě.")


class TestimonialGate(unittest.TestCase):
    def test_flag_defaults_to_false_and_wraps_the_block(self):
        gate = "apply_filters( 'molosoc_landing_b_testimonial_enabled', false )"
        self.assertIn(gate, TEMPLATE)
        self.assertLess(TEMPLATE.index(gate), TEMPLATE.index('class="lpb-testimonial"'))
        self.assertLess(TEMPLATE.index(QUOTE), TEMPLATE.index("<?php endif; ?>\n\t\t<div class=\"lpb-section__cta\">", TEMPLATE.index(gate)))

    def test_quote_is_exact_and_inside_the_real_section(self):
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


if __name__ == "__main__":
    unittest.main()
