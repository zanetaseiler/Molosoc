"""Issue #122: Landing Page B — static checks on the page-580 rebuild.

No PHP runtime is needed: these assert that the template reproduces page
580's structure/copy, that ONLY the operational purchase details changed
(price, shipping, size L, CTA target), and that functions.php wires the
slug exactly once into each gate (assets, sticky CTA, noindex, sitemap)
without touching the live Page A branches.

Issue #153 (mobile PageSpeed, LCP 9.2 s): every photo is served from a
theme-hosted WebP derivative set at its displayed width, the hero is the
prioritised + preloaded LCP image, the unused plugin CSS/JS stack is
dequeued on this page, both Google Fonts stylesheets load non-blocking,
landing-b.js is deferred and "(varianta, koncept)" is stripped from the
document title.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
TEMPLATE = ROOT / "page-hydratacni-navleky-molosoc.php"
FUNCTIONS = ROOT / "functions.php"
CSS = ROOT / "assets/css/landing-b.css"
JS = ROOT / "assets/js/landing-b.js"
WEBP_DIR = ROOT / "assets/images/landing-b"
SLUG = "hydratacni-navleky-molosoc"

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

# Page 580's 13 content photos as the theme-hosted WebP derivative sets the
# <img> tags now use (Issue #153): basename -> widths that must exist as
# assets/images/landing-b/<basename>-<w>.webp. The hero background stays a
# CSS url() to the live upload.
DERIVATIVES = {
    "lpb-hero-baige": [480, 800, 1152],  # hero main (LCP)
    "lpb-sofa-2": [480, 960],  # hero thumb (480 only) + "Co to je"
    "lpb-sizes-wbg": [480],  # hero thumb
    "lpb-product-pack": [480],  # hero thumb (the .png source)
    "lpb-hero-white": [480, 960],  # size M
    "lpb-studio": [480, 960],  # size L
    "lpb-sizes-wbg-1": [480, 960],  # Porovnání
    "lpb-apply-cream": [480, 960],  # Jednoduchý rituál
    "lpb-mami-sofa": [480, 960],  # Z reálu
    "lpb-holding-first-time": [480, 960],  # Z reálu
    "lpb-variation-cream": [480, 960],  # Kompatibilita
    "lpb-product-shot-2": [480, 960],  # Objednávka
    "lpb-opening-package-mami": [400, 800],  # Zakladatelky
}
HERO_BG = "2026/04/hero-bg-v2-nqbEYtifYWW4XirFSK5h8z.webp"

# The lightbox-style <a href> wrappers keep linking to page 580's original
# full-size uploads (the 9 photos page 580 itself wrapped in links).
UPLOAD_LINKS = [
    "2026/04/Molosoc-Photos-Product-Hero-New-Baige.jpg",
    "2026/04/Molosoc-Photos-Product-New-Sofa-2.jpg",
    "2026/04/Molosoc-Photos-Product-Hero-New-White.jpg",
    "2026/04/Molosoc-Photos-Product-New-Studio.jpg",
    "2026/04/Molosoc-Photos-Product-New-Sizes-WBG-1.jpg",
    "2026/04/Molosoc-Photos-Product-New-Apply-Cream-Ok.jpg",
    "2026/04/Molosoc-Photos-Product-New-VariationCream-Ok.jpg",
    "2026/04/Molosoc-Product-Shot-2.jpg",
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

    def test_every_image_is_a_theme_webp_derivative_at_displayed_width(self):
        # Every <img> goes through the srcset helper — no raw <img src=…>
        # upload left anywhere in the rendered markup.
        self.assertEqual(self.body.count("<img "), 14)
        self.assertEqual(
            self.body.count("<img <?php echo molosoc_landing_b_img_attrs("), 14
        )
        self.assertNotIn("<img src=", self.body)
        self.assertNotIn("<img class=", self.body)
        # Each derivative set referenced in the template is complete on disk
        # and nothing is shipped that the template doesn't reference.
        calls = re.findall(
            r"molosoc_landing_b_img_attrs\( '([a-z0-9-]+)', array\( ([0-9, ]+) \)", self.body
        )
        referenced = {}
        for base, widths in calls:
            referenced.setdefault(base, set()).update(int(w) for w in widths.split(","))
        # The hero <img> reads its set from molosoc_landing_b_hero_image().
        hero_fn = self.fn[self.fn.index("function molosoc_landing_b_hero_image()"):]
        hero_fn = hero_fn[: hero_fn.index("\n}\n")]
        base, widths = re.search(r"'base'\s*=> '([a-z0-9-]+)',\s*'widths' => array\( ([0-9, ]+) \)", hero_fn).groups()
        referenced.setdefault(base, set()).update(int(w) for w in widths.split(","))
        self.assertEqual(set(referenced), set(DERIVATIVES))
        for base, widths in DERIVATIVES.items():
            self.assertTrue(referenced[base] <= set(widths), base)
            for w in widths:
                f = WEBP_DIR / f"{base}-{w}.webp"
                self.assertTrue(f.is_file(), f"missing derivative: {f.name}")
                self.assertEqual(f.read_bytes()[:4], b"RIFF", f.name)
                self.assertEqual(f.read_bytes()[8:12], b"WEBP", f.name)
        expected_files = {f"{b}-{w}.webp" for b, ws in DERIVATIVES.items() for w in ws}
        self.assertEqual({p.name for p in WEBP_DIR.iterdir()}, expected_files)
        # The hero set is defined once (functions.php) and used by the <img>.
        self.assertIn(
            "molosoc_landing_b_img_attrs( $lpb_hero['base'], $lpb_hero['widths'], $lpb_hero['sizes'] )",
            self.body,
        )
        self.assertIn("$lpb_hero        = molosoc_landing_b_hero_image();", self.tpl)
        # Lightbox links + hero background still point at the live uploads.
        found = set(re.findall(r"(2026/0\d/[A-Za-z0-9_.-]+)", self.body + self.css))
        for img in UPLOAD_LINKS + [HERO_BG]:
            self.assertIn(img, found, f"upload link missing: {img}")
        self.assertNotIn("staging.molosoc.com", self.tpl + self.css)

    def test_hero_is_the_prioritised_lcp_image_and_the_rest_lazy(self):
        hero = self.body[self.body.index('class="lpb-hero__main"'):self.body.index('class="lpb-hero__thumbs"')]
        self.assertIn('fetchpriority="high"', hero)
        self.assertIn('loading="eager"', hero)
        self.assertNotIn('loading="lazy"', hero)
        self.assertEqual(self.body.count('fetchpriority="high"'), 1)
        lazy_imgs = [l for l in self.body.splitlines() if "<img " in l and 'loading="lazy"' in l]
        self.assertEqual(len(lazy_imgs), 13)
        # functions.php: hero set (sizes = phone full width / desktop media
        # column) + a wp_head preload at priority 1 with the same set.
        fn = self.fn
        hero_fn = fn[fn.index("function molosoc_landing_b_hero_image()"):]
        hero_fn = hero_fn[: hero_fn.index("\n}\n")]
        self.assertIn("'lpb-hero-baige'", hero_fn)
        self.assertIn("array( 480, 800, 1152 )", hero_fn)
        self.assertIn("'(max-width: 900px) 100vw, 700px'", hero_fn)
        head = fn[fn.index("function molosoc_landing_b_head()"):]
        head = head[: head.index("add_action( 'wp_head', 'molosoc_landing_b_head', 1 );")]
        self.assertIn(f"is_page( '{SLUG}' )", head)
        self.assertIn('<link rel="preload" as="image" fetchpriority="high" ', head)
        self.assertIn("'imagesrcset=\"', 'imagesizes=\"'", head)
        self.assertIn('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', head)
        # Both Google Fonts stylesheets non-blocking, with a <noscript> fallback.
        self.assertIn("media=\"print\" onload=\"this.media=\\'all\\'\"", head)
        self.assertIn("<noscript><link rel=\"stylesheet\" href=\"%1$s\"></noscript>", head)
        self.assertIn("molosoc_fonts_url(), molosoc_landing_b_fonts_url()", head)

    def test_unused_plugin_assets_are_dequeued_and_title_cleaned(self):
        fn = self.fn
        gate = fn[fn.index("function molosoc_page_without_plugin_markup()"):]
        gate = gate[: gate.index("}")]
        self.assertIn("is_front_page()", gate)
        self.assertIn(f"is_page( '{SLUG}' )", gate)
        dq = fn[fn.index("function molosoc_dequeue_unused_homepage_assets()"):]
        dq = dq[: dq.index("add_action( 'wp_print_footer_scripts', 'molosoc_dequeue_unused_homepage_assets', 1 );")]
        self.assertIn("if ( ! molosoc_page_without_plugin_markup() ) {", dq)
        for handle in (
            "'woocommerce-general'", "'select2'", "'photoswipe'", "'cr-frontend-css'",
            "'pplcz_map_css'", "'ppl-label-position'", "'jquery-migrate'", "'wc-cart-fragments'",
            "'cr-colcade'", "'pplcz_map_js'", "'pplcz_parcelshop-old-view'",
        ):
            self.assertIn(handle, dq, handle)
        # Order attribution must survive (it records where a purchase started).
        self.assertNotIn("'wc-order-attribution'", dq)
        self.assertNotIn("'sourcebuster-js'", dq)
        self.assertIn("add_action( 'wp_enqueue_scripts', 'molosoc_dequeue_unused_homepage_assets', 100 );", fn)
        # Title: "(varianta, koncept)" stripped on this page only.
        title = fn[fn.index("add_filter( 'document_title_parts', function ( $parts ) {"):]
        title = title[: title.index("} );")]
        self.assertIn(f"is_page( '{SLUG}' )", title)
        self.assertIn("varianta", title)
        self.assertIn("koncept", title)
        self.assertEqual(fn.count("add_filter( 'document_title_parts'"), 1)

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
        branch = fn[fn.index("} elseif ( is_page( '" + SLUG + "' ) ) {"):]
        branch = branch[: branch.index("} elseif (", 10)]
        # Headings use the theme display face (Tenor Sans, global
        # molosoc-fonts handle); only B's own label face is fetched, and on
        # this page both fonts stylesheets are printed non-blocking from
        # wp_head instead of enqueued (Issue #153) — Open Sans was dropped
        # (fallback-only in landing-b.css, never rendered).
        self.assertIn("family=Nunito+Sans", fn)
        self.assertNotIn("DM+Serif+Display", fn)
        self.assertNotIn("Open+Sans", fn)
        self.assertIn("wp_dequeue_style( 'molosoc-fonts' );", branch)
        self.assertNotIn("molosoc-landing-b-fonts", branch)
        self.assertIn("array( 'molosoc-components' ), $theme_version );", branch)
        self.assertIn("wp_script_add_data( 'molosoc-landing-b', 'strategy', 'defer' );", branch)
        # The global enqueue and the non-blocking print share one URL source.
        self.assertIn("wp_enqueue_style( 'molosoc-fonts', molosoc_fonts_url(), array(), null );", fn)
        self.assertEqual(fn.count("fonts.googleapis.com/css2?"), 2)
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
