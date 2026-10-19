"""Issue #122: Landing Page B — static checks on the page-580 rebuild.

No PHP runtime is needed: these assert that the template reproduces page
580's structure/copy, that ONLY the operational purchase details changed
(price, shipping, size L, CTA target), and that functions.php wires the
slug exactly once into the assets gate and out of the sticky-CTA (Issue
#163), noindex and sitemap-exclusion gates (indexable since Issue #159)
without touching the live Page A branches.

Issue #153 (mobile PageSpeed, LCP 9.2 s): every photo is served from a
theme-hosted WebP derivative set at its displayed width, the hero is the
prioritised + preloaded LCP image, the unused plugin CSS/JS stack is
dequeued on this page, both Google Fonts stylesheets load non-blocking,
landing-b.js is deferred and "(varianta, koncept)" is stripped from the
document title.

Issue #157: PageSpeed's actual LCP element is the .lpb-hero CSS background
(hero-bg-v2), discovered only after the CSS bundle. It is now a theme-hosted
WebP pair (960 for ≤900px / 1920 above) whose URLs come from one PHP helper:
the template puts them on the section as custom properties the stylesheet
reads, and wp_head preloads them with media-gated fetchpriority="high" links.
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
# Issue #161 keyword retarget ("maska na nohy", KW Everywhere CZ 2026-10-14).
TITLE = "Hydratační maska na nohy na opakované použití | Molosoc"
H1 = "Maska na nohy, kterou použijete znovu<br>— s krémem, který už máte"

# Section headings of page 580, in its own order (16 Thrive page sections;
# the first two are the sticky header, which the theme header + global pill
# replace).
SECTION_HEADINGS = [
    "Maska na nohy, kterou použijete znovu",  # Issue #161 H1 (page 580: "Namazané nohy.")
    "Počet kusů je omezený",
    "Pro koho MOLOSOC je: suché i popraskané paty",  # Issue #161 (page 580: "Pro koho MOLOSOC je")
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
# assets/images/landing-b/<basename>-<w>.webp. The hero background (Issue
# #157) is a theme-hosted pair too, but a CSS background rather than an <img>.
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
HERO_BG_UPLOAD = "2026/04/hero-bg-v2-nqbEYtifYWW4XirFSK5h8z.webp"
HERO_BG = {"lpb-hero-bg": [960, 1920]}  # ≤900px / above (the CSS breakpoint)

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
        expected_files = {
            f"{b}-{w}.webp" for b, ws in {**DERIVATIVES, **HERO_BG}.items() for w in ws
        }
        self.assertEqual({p.name for p in WEBP_DIR.iterdir()}, expected_files)
        # The hero set is defined once (functions.php) and used by the <img>.
        self.assertIn(
            "molosoc_landing_b_img_attrs( $lpb_hero['base'], $lpb_hero['widths'], $lpb_hero['sizes'] )",
            self.body,
        )
        self.assertIn("$lpb_hero        = molosoc_landing_b_hero_image();", self.tpl)
        # Lightbox links still point at the live uploads; the hero background
        # upload is gone from the CSS (Issue #157, theme-hosted pair instead).
        found = set(re.findall(r"(2026/0\d/[A-Za-z0-9_.-]+)", self.body + self.css))
        for img in UPLOAD_LINKS:
            self.assertIn(img, found, f"upload link missing: {img}")
        self.assertNotIn(HERO_BG_UPLOAD, found)
        self.assertNotIn("hero-bg-v2", self.css_rules)
        self.assertNotIn("staging.molosoc.com", self.tpl + self.css)

    def test_hero_background_is_a_preloaded_theme_webp_pair(self):
        # Issue #157: the LCP element is the section background, not the <img>.
        for base, widths in HERO_BG.items():
            for w in widths:
                f = WEBP_DIR / f"{base}-{w}.webp"
                self.assertTrue(f.is_file(), f"missing derivative: {f.name}")
                self.assertEqual(f.read_bytes()[:4], b"RIFF", f.name)
                self.assertEqual(f.read_bytes()[8:12], b"WEBP", f.name)
        # One PHP source of truth: file + media query per breakpoint, the
        # same 900px cut as landing-b.css.
        fn = self.fn
        helper = fn[fn.index("function molosoc_landing_b_hero_background()"):]
        helper = helper[: helper.index("\n}\n")]
        self.assertIn("'/assets/images/landing-b/'", helper)
        self.assertIn("'url' => $dir . 'lpb-hero-bg-960.webp', 'media' => '(max-width: 900px)'", helper)
        self.assertIn("'url' => $dir . 'lpb-hero-bg-1920.webp', 'media' => '(min-width: 900.1px)'", helper)
        style = fn[fn.index("function molosoc_landing_b_hero_background_style()"):]
        style = style[: style.index("\n}\n")]
        self.assertIn("'--lpb-hero-bg-mobile: url(%s); --lpb-hero-bg-desktop: url(%s)'", style)
        self.assertIn("esc_url( $bg['mobile']['url'] )", style)
        self.assertIn("esc_url( $bg['desktop']['url'] )", style)
        self.assertIn("return esc_attr( sprintf(", style)
        # wp_head: one media-gated high-priority preload per breakpoint,
        # printed right after the hero <img> preload.
        head = fn[fn.index("function molosoc_landing_b_head()"):]
        head = head[: head.index("add_action( 'wp_head', 'molosoc_landing_b_head', 1 );")]
        self.assertIn("foreach ( molosoc_landing_b_hero_background() as $bg ) {", head)
        self.assertIn(
            "'<link rel=\"preload\" as=\"image\" fetchpriority=\"high\" href=\"%s\" media=\"%s\">'", head
        )
        self.assertIn("esc_url( $bg['url'] )", head)
        self.assertIn("esc_attr( $bg['media'] )", head)
        self.assertLess(head.index("'imagesrcset=\"', 'imagesizes=\"'"), head.index("foreach ( molosoc_landing_b_hero_background()"))
        # Template: the section carries the custom properties.
        self.assertIn(
            '<section class="lpb-hero" aria-label="Hydratační návleky na nohy" '
            'style="<?php echo molosoc_landing_b_hero_background_style(); ?>">',
            self.body,
        )
        self.assertEqual(self.body.count("molosoc_landing_b_hero_background_style()"), 1)
        # CSS: the rule reads the custom properties (overlay unchanged) and
        # swaps to the mobile copy at the shared 900px breakpoint.
        css = self.css_rules
        hero = css[css.index(".lpb-hero {"):]
        hero = hero[: hero.index("\n}\n")]
        self.assertIn("--lpb-hero-bg: var(--lpb-hero-bg-desktop, none);", hero)
        self.assertIn(
            "linear-gradient(rgba(252, 252, 252, 0.5), rgba(252, 252, 252, 0.5)),\n"
            "    var(--lpb-hero-bg) center / cover no-repeat;",
            hero,
        )
        mobile = css[css.index("@media (max-width: 900px) {"):]
        mobile = mobile[: mobile.index("@media (max-width: 560px)")]
        self.assertIn(
            ".lpb-hero {\n    --lpb-hero-bg: var(--lpb-hero-bg-mobile, var(--lpb-hero-bg-desktop, none));\n  }",
            mobile,
        )
        self.assertNotIn("url(\"http", css)

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
        # Title (Issue #161): a fixed <title> for this page only, so the WP
        # post title's "(varianta, koncept)" label never reaches the tab.
        self.assertEqual(fn.count("add_filter( 'pre_get_document_title'"), 1)
        self.assertNotIn("add_filter( 'document_title_parts'", fn)
        title = fn[fn.index("add_filter( 'pre_get_document_title'"):]
        title = title[: title.index("} );")]
        self.assertIn(f"is_page( '{SLUG}' )", title)
        self.assertIn("return molosoc_landing_b_document_title();", title)
        self.assertIn(f"return '{TITLE}';", fn)

    def test_keyword_retarget_title_h1_and_pillar_link(self):
        """Issue #161: "maska na nohy" in <title>/H1, Pillar 1 terms only in an H2 + body with a link."""
        self.assertIn(f"<h1 class=\"lpb-hero__title\">{H1}</h1>", self.body)
        self.assertIn('<p class="lpb-eyebrow">Hydratační maska na nohy</p>', self.body)
        # The category page keeps "návleky na nohy" as its main term: not in title/H1.
        self.assertNotIn("návleky na nohy", TITLE.lower())
        self.assertNotIn("návleky na nohy", H1.lower())
        # Pillar 1 owns "popraskané paty" / "suché paty": never in title/H1, one H2 + a body link.
        for term in ("popraskané paty", "suché paty"):
            self.assertNotIn(term, TITLE.lower())
            self.assertNotIn(term, H1.lower())
        h2s = re.findall(r"<h2>(.*?)</h2>", self.body)
        self.assertEqual(sum("popraskané paty" in h.lower() for h in h2s), 1)
        self.assertEqual(self.body.count("home_url( '/cz/popraskane-paty/' )"), 1)
        link = re.search(r'<a href="<\?php echo esc_url\( home_url\( \'/cz/popraskane-paty/\' \) \); \?>">([^<]+)</a>', self.body)
        self.assertEqual(link.group(1), "popraskané paty")
        # Reusable-vs-disposable argument reuses the category page's wording (no new claim).
        cat = (ROOT / "page-foot-covers.php").read_text()
        for phrase in ("na jedno použití", "vydrží alespoň 10 použití", "skončí v koši"):
            self.assertIn(phrase, self.body, phrase)
            self.assertIn(phrase, cat, phrase)
        self.assertIn("maska na nohy na opakované použití", self.body)
        self.assertNotIn("Není to maska.", self.body)
        # URL/slug unchanged (live Meta ads point at it).
        self.assertEqual(TEMPLATE.name, f"page-{SLUG}.php")

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
        # Every CTA goes through the shared buy-CTA helper (Issue #209), whose
        # fallback is the CZ product URL helper.
        self.assertIn("molosoc_product_url( 'cz' )", self.tpl)
        self.assertEqual(self.tpl.count("esc_url( $lpb_product_url )"), 0)
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
        # Issue #163: the global sticky "Koupit nyní" pill shows on B like on
        # every other public page — B is NOT in the hidden gate (the slug may
        # only appear in its comment), and its own bottom bar is gone.
        hidden = fn[fn.index("function molosoc_sticky_cta_hidden()"):]
        hidden = hidden[: hidden.index("\n}")]
        self.assertNotIn(f"'{SLUG}'", hidden)
        # Issue #177: the gate lists the legal pages, not Landing A any more.
        self.assertIn("'zasady-dopravy'", hidden)
        self.assertNotIn("'moisture-lock-foot-cover', 'hydratacni-navlek-na-nohy'", hidden)
        self.assertNotIn("lpb-sticky", self.body)
        self.assertNotIn("id=\"lpb-sticky\"", self.tpl)
        self.assertNotIn("Objednat nyní", self.body)
        self.assertIn("sticky-cta.js", fn)
        # Indexable since Issue #159: neither noindexed nor sitemap-excluded
        # (the slug may only appear in comments there, never as a PHP string).
        robots = fn[fn.index("add_filter( 'wp_robots'"):]
        robots = robots[: robots.index("} );")]
        self.assertIn("is_page( 'thank-you' )", robots)
        self.assertNotIn(f"'{SLUG}'", robots)
        excluded = fn[fn.index("function molosoc_sitemap_excluded_page_ids()"):]
        excluded = excluded[: excluded.index("foreach ( $slugs as $slug )")]
        self.assertNotIn(f"'{SLUG}'", excluded)
        self.assertIn("'hydratacni-navleky-na-nohy-2', 'doprava-a-platba', 'home-cestina',", excluded)
        # Live Page A gates untouched: the landing pair still appears exactly
        # where it did before (preconnect, product.css branch).
        # Issue #177 took the pair out of the sticky-CTA gate: preconnect +
        # product.css branch remain. Issue #190 adds the one helper
        # (molosoc_is_landing_page_a()) its new speed gates read the pair from.
        self.assertEqual(fn.count("array( 'moisture-lock-foot-cover', 'hydratacni-navlek-na-nohy' )"), 3)

    def test_css_and_js_are_scoped_to_the_page(self):
        selectors = re.findall(r"^([^@\s{}][^{]*)\{", self.css_rules, flags=re.M)
        for sel in selectors:
            for part in sel.split(","):
                part = part.strip()
                if not part:
                    continue
                self.assertTrue(part.startswith(".lpb"), f"unscoped selector: {part}")
        # The section-wide default width must stay at single-class specificity
        # (:where) so .lpb-video / .lpb-gallery / .lpb-founders__photo keep
        # their narrower max-widths (live regression: 1080px-wide YouTube embed).
        self.assertIn(".lpb-section > :where(", self.css_rules)
        self.assertIn("data-lpb-tabs", self.js)
        # Issue #163: no page-specific sticky code left in CSS/JS (comments aside).
        self.assertNotIn("lpb-sticky", self.css_rules)
        self.assertNotIn("getElementById( \"lpb-sticky\" )", self.js)
        self.assertNotIn("IntersectionObserver", self.js)


if __name__ == "__main__":
    unittest.main()
