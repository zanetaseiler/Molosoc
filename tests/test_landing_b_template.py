"""Issue #122: Landing Page B — static checks on the page-580 rebuild.

No PHP runtime is needed: these assert that the template reproduces page
580's structure/copy, that ONLY the operational purchase details changed
(price, shipping, size L, CTA target), and that functions.php wires the
slug exactly once into each gate (assets, sticky CTA, noindex, sitemap)
without touching the live Page A branches.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
TEMPLATE = ROOT / "page-hydratacni-navleky-landing-b.php"
FUNCTIONS = ROOT / "functions.php"
CSS = ROOT / "assets/css/landing-b.css"
JS = ROOT / "assets/js/landing-b.js"
SLUG = "hydratacni-navleky-landing-b"

# Section headings of page 580, in its own order (16 Thrive page sections;
# the first two are the sticky header, which the theme header + sticky bar
# replace).
SECTION_HEADINGS = [
    "Namazané nohy.",
    "Počet kusů je omezený",
    "Pro koho MOLOSOC je",
    "Nejsou to ponožky.",
    "Dvě velikosti. Jeden účel.",
    "Jednoduchý rituál",
    "Jak MOLOSOC vznikl",
    "MOLOSOC v reálu",
    "Jak to vše začalo.",
    "Funguje s vaším oblíbeným krémem.",
    "Konec klouzání. Konec čekání.",
    "Máte otázky?",
    "Objednejte MOLOSOC",
    "MOLOSOC jsme vytvořily my – máma s dcerou.",
]

# Every image page 580 renders inside its content (17 distinct files) plus
# the hero background.
IMAGES = [
    "2026/04/hero-bg-v2-nqbEYtifYWW4XirFSK5h8z.webp",
    "2026/04/Molosoc-Photos-Product-Hero-New-Baige.jpg",
    "2026/04/Molosoc-Photos-Product-New-Sofa-2.jpg",
    "2026/04/Molosoc-Photos-Product-New-Sizes-WBG.jpg",
    "2026/04/Molosoc-Photos-Product-New-Product.png",
    "2026/04/Molosoc-Photos-Product-Hero-New-White.jpg",
    "2026/04/Molosoc-Photos-Product-New-Studio.jpg",
    "2026/04/Molosoc-Photos-Product-New-Sizes-WBG-1.jpg",
    "2026/04/Molosoc-Photos-Product-New-Apply-Cream-Ok.jpg",
    "2026/04/Molosoc-Photos-Product-Mami-Sofa.jpg",
    "2026/04/Molosoc-Photos-Product-Holdind-It-First-Time-WBG.jpg",
    "2026/04/Molosoc-Photos-Product-New-VariationCream-Ok.jpg",
    "2026/04/Molosoc-Product-Shot-2.jpg",
    "2026/01/Molosoc-Opening-Package-Mami.jpg",
]

FAQ = [
    "Z čeho je MOLOSOC vyrobený?",
    "Jak se MOLOSOC používá?",
    "Můžu v nich chodit?",
    "Funguje to s jakýmkoliv krémem?",
    "Je to jednorázové?",
    "Kolik stojí jedno balení?",
]


class LandingBTemplate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tpl = TEMPLATE.read_text(encoding="utf-8")
        cls.fn = FUNCTIONS.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")
        cls.js = JS.read_text(encoding="utf-8")
        # Rendered markup only: PHP docblock / inline comments stripped, so a
        # comment that *mentions* "199 Kč" or "<details>" can't satisfy or
        # fail a content check.
        cls.body = re.sub(r"/\*.*?\*/|<!--.*?-->", "", cls.tpl, flags=re.S)
        cls.css_rules = re.sub(r"/\*.*?\*/", "", cls.css, flags=re.S)

    def test_files_exist_and_follow_page_slug_convention(self):
        self.assertTrue(TEMPLATE.is_file())
        self.assertEqual(TEMPLATE.name, f"page-{SLUG}.php")
        self.assertIn("get_header();", self.tpl)
        self.assertIn("get_footer();", self.tpl)

    def test_sections_present_in_page_580_order(self):
        positions = []
        for heading in SECTION_HEADINGS:
            idx = self.body.find(">" + heading + "<")
            self.assertGreater(idx, -1, f"missing heading: {heading}")
            positions.append(idx)
        self.assertEqual(positions, sorted(positions), "sections out of page-580 order")

    def test_every_page_580_image_is_used_from_the_live_uploads(self):
        found = set(re.findall(r"(2026/0\d/[A-Za-z0-9_.-]+)", self.body + self.css))
        for img in IMAGES:
            self.assertIn(img, found, f"image missing: {img}")
        self.assertNotIn("staging.molosoc.com", self.tpl + self.css)

    def test_video_embed_and_faq(self):
        self.assertIn("youtube-nocookie.com/embed/dXVivzbZBfc", self.tpl)
        for q in FAQ:
            self.assertIn(f"<summary>{q}</summary>", self.tpl)
        self.assertEqual(self.body.count("<details>"), 6)

    def test_story_tabs_have_three_panels(self):
        self.assertEqual(self.tpl.count('role="tab"'), 3)
        self.assertEqual(self.tpl.count('role="tabpanel"'), 3)
        self.assertIn("A pak se stal nápad skutečností.", self.tpl)

    def test_only_operational_purchase_details_were_adapted(self):
        # Stale presale-era values must not survive anywhere in the markup.
        for stale in ("199 Kč", "69 Kč", "49 Kč", "40–44", "molosoc-hydratacni-ponozky"):
            self.assertNotIn(stale, self.body, f"stale value present: {stale}")
        self.assertIn("$lpb_price       = '229 Kč';", self.tpl)
        self.assertIn("$lpb_shipping    = 'Doprava od 79 Kč';", self.tpl)
        self.assertIn("39.5–44", self.tpl)
        # Every CTA goes through the shared CZ product URL helper.
        self.assertIn("molosoc_product_url( 'cz' )", self.tpl)
        self.assertEqual(self.tpl.count("esc_url( $lpb_product_url )"), 4)
        self.assertNotIn("/product/", self.body)
        # Presale scarcity line is kept verbatim but flagged for the owner.
        self.assertIn("Počet kusů je omezený", self.body)
        self.assertIn("FLAG:", self.tpl)

    def test_functions_php_wiring_is_exactly_once_per_gate(self):
        fn = self.fn
        self.assertEqual(fn.count("} elseif ( is_page( '" + SLUG + "' ) ) {"), 1)
        self.assertIn("/assets/css/landing-b.css", fn)
        self.assertIn("/assets/js/landing-b.js", fn)
        # Headings use the theme display face (Tenor Sans, global
        # molosoc-fonts handle); only B's own body/label faces are fetched.
        self.assertIn("family=Nunito+Sans", fn)
        self.assertNotIn("DM+Serif+Display", fn)
        # Sticky "Koupit nyní" pill hidden on B (own sticky bar).
        hidden = fn[fn.index("function molosoc_sticky_cta_hidden()"):]
        hidden = hidden[: hidden.index("}")]
        self.assertIn(f"is_page( '{SLUG}' )", hidden)
        # noindex + sitemap exclusion.
        self.assertIn(f"is_page( array( 'thank-you', '{SLUG}' ) )", fn)
        excluded = fn[fn.index("function molosoc_sitemap_excluded_page_ids()"):]
        excluded = excluded[: excluded.index("foreach ( $slugs as $slug )")]
        self.assertIn(f"'{SLUG}',", excluded)
        # Live Page A gates untouched: the landing pair still appears exactly
        # where it did before (preconnect, product.css branch, sticky hide).
        self.assertEqual(fn.count("array( 'moisture-lock-foot-cover', 'hydratacni-navlek-na-nohy' )"), 3)

    def test_css_and_js_are_scoped_to_the_page(self):
        selectors = re.findall(r"^([^@\s{}][^{]*)\{", self.css_rules, flags=re.M)
        for sel in selectors:
            for part in sel.split(","):
                part = part.strip()
                if not part:
                    continue
                self.assertTrue(
                    part.startswith(".lpb") or part.startswith("body:has(.lpb-sticky)"),
                    f"unscoped selector: {part}",
                )
        # The section-wide default width must stay at single-class specificity
        # (:where) so .lpb-video / .lpb-gallery / .lpb-founders__photo keep
        # their narrower max-widths (live regression: 1080px-wide YouTube embed).
        self.assertIn(".lpb-section > :where(", self.css_rules)
        self.assertIn("data-lpb-tabs", self.js)
        self.assertIn("lpb-sticky", self.js)


if __name__ == "__main__":
    unittest.main()
