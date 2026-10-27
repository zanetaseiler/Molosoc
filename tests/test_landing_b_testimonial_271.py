"""Issues #271/#278: the Landing B feedback summary is flag-gated and enabled only for the Landing B template."""
import re
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

    def test_gate_is_slug_based_not_assigned_template(self):
        # is_page_template() is false for automatic page-{slug}.php selection (Codex P2, PR #279).
        start = FUNCTIONS.index("add_filter( 'molosoc_landing_b_testimonial_enabled'")
        hook = FUNCTIONS[start:FUNCTIONS.index("} );", start)]
        self.assertNotIn("is_page_template", hook)
        self.assertIn("is_page( 'hydratacni-navleky-molosoc' )", hook)

    def test_indirect_speech_not_a_verbatim_quote(self):
        block = TEMPLATE[TEMPLATE.index('class="lpb-testimonial"'):TEMPLATE.index("<?php endif; ?>\n\t\t<div class=\"lpb-section__cta\">")]
        self.assertNotIn("<blockquote", block)
        text = re.sub(r"<[^>]*>", "", block.split(">", 1)[1])
        for quote_mark in ("„", "“", '"', "”"):
            self.assertNotIn(quote_mark, text)
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


class NumberedFeedback281(unittest.TestCase):
    ITEM2 = "Další zákaznice popsala, že má po použití návleků chodidla hebká jako dětskou pokožku."
    ITEM3 = "Jiná zákaznice nám napsala, že si návleky natolik oblíbila, že je nechce odložit."

    def test_numbered_list_with_item1_always_shown(self):
        self.assertIn('<ol class="lpb-testimonial__list">', TEMPLATE)
        gate = TEMPLATE.index("molosoc_landing_b_feedback_extra_enabled', false")
        self.assertLess(TEMPLATE.index("<li>" + QUOTE), TEMPLATE.index("<?php if ( $lpb_extra_feedback )"))
        self.assertLess(TEMPLATE.index("<ol class"), gate + 1000)

    def test_items_2_and_3_are_disabled_by_default_and_unenabled_in_theme(self):
        flag = "apply_filters( 'molosoc_landing_b_feedback_extra_enabled', false )"
        self.assertIn(flag, TEMPLATE)
        cond = TEMPLATE.index("<?php if ( $lpb_extra_feedback )")
        end = TEMPLATE.index("<?php endif; ?>", cond)
        self.assertLess(cond, TEMPLATE.index(self.ITEM2))
        self.assertLess(TEMPLATE.index(self.ITEM3), end)
        self.assertNotIn("molosoc_landing_b_feedback_extra_enabled", FUNCTIONS)

    def test_no_quotes_names_or_claims_in_list(self):
        ol = TEMPLATE[TEMPLATE.index("<ol class"):TEMPLATE.index("</ol>")]
        text = re.sub(r"<[^>]*>", "", ol)
        for bad in ("„", "“", '"', "”", "prdel", "ověřen", "léč", "zlepš", "psoria"):
            self.assertNotIn(bad, text)

    def test_css_numbers_the_list(self):
        self.assertIn(".lpb-testimonial__list", CSS)
        self.assertIn("counter(lpb-feedback)", CSS)


if __name__ == "__main__":
    unittest.main()
