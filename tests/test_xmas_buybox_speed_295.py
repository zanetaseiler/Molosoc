"""Issue #295: Christmas landing (CZ + EN) — buyers' questions answered at the buy
box, and a faster first screen on phones. Static checks, no PHP/WordPress runtime.

Part 1: the size ranges, "from" shipping price and order-by date live once in
molosoc_xmas_facts(); the hero line, size buttons, FAQ answers, the 3-line info
block under each checkout button and the size hint under the pair-1 label are
composed from it, and the composed info-block copy equals the Issue's exact copy.

Part 2: 480/768/1080 px WebP derivatives of the three scenes with srcset/sizes
from one helper (the <img> and the head preload carry the same candidates), a
resized header logo on the Christmas pages only (default markup elsewhere), and
the Christmas pages behind the existing no-plugin-markup gate (additive edits in
functions.php only, per the #251 evergreen test)."""
import re
import struct
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
INC = (ROOT / "inc/landing-xmas.php").read_text(encoding="utf-8")
PART = (ROOT / "template-parts/landing-xmas.php").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-xmas.css").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
HEADER = (ROOT / "template-parts/site-header.php").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")


def strip_comments(src):
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


PART_CODE = strip_comments(PART)
CSS_CODE = strip_comments(CSS)


def block(src, start, end):
    i = src.index(start)
    return src[i: src.index(end, i)]


def webp_width(data):
    """Pixel width of a lossy (VP8) or lossless (VP8L) WebP file."""
    assert data[:4] == b"RIFF" and data[8:12] == b"WEBP", "not a WebP file"
    if b"VP8L" in data[:40]:
        i = data.index(b"VP8L")
        return (struct.unpack("<I", data[i + 9:i + 13])[0] & 0x3FFF) + 1
    i = data.index(b"VP8 ")
    return struct.unpack("<H", data[i + 14:i + 16])[0] & 0x3FFF


def facts_block(lang):
    start = PART.index("'facts'     => array(", PART.index("'%s' => array(" % lang))
    return PART[start: PART.index("),\n\t\t'bundle_h'", start)]


FACTS = {
    "cz": {"size_m": "36–39", "size_l": "39,5–44", "ship_from": 69, "order_by": "18. prosince"},
    "en": {"size_m": "36–39", "size_l": "39.5–44", "ship_from": 69, "order_by": "18 December"},
}


class OneSourceOfTruth(unittest.TestCase):
    def test_facts_helper_holds_the_numbers(self):
        fn = block(INC, "function molosoc_xmas_facts( $lang )", "\n}")
        self.assertIn("'size_m'    => '36–39',", fn)
        self.assertIn("'size_l'    => $en ? '39.5–44' : '39,5–44',", fn)
        self.assertIn("'ship_from' => 69,", fn)
        self.assertIn("'order_by'  => $en ? '18 December' : '18. prosince',", fn)
        self.assertIn("$lpx_fcz   = molosoc_xmas_facts( 'cz' );", PART)
        self.assertIn("$lpx_fen   = molosoc_xmas_facts( 'en' );", PART)

    def test_template_has_no_literal_copy_of_a_fact(self):
        for literal in ("36–39", "39.5", "39,5", "69 Kč", "69 CZK", "18. prosince", "18 December"):
            self.assertNotIn(literal, PART_CODE, literal)

    def test_hero_line_size_buttons_and_faq_read_the_facts(self):
        self.assertIn("'ship'      => 'Doprava od ' . $lpx_fcz['ship_from'] . ' Kč',", PART)
        self.assertIn("'ship'      => 'Shipping from ' . $lpx_fen['ship_from'] . ' CZK',", PART)
        self.assertIn("'deadline'  => sprintf( 'Objednejte do %s, doručíme před Vánoci.', $lpx_fcz['order_by'] ),", PART)
        self.assertIn("'deadline'  => sprintf( 'Order by %s for delivery before Christmas.', $lpx_fen['order_by'] ),", PART)
        self.assertIn("'sizes'     => array( 'M' => 'M (' . $lpx_fcz['size_m'] . ')', 'L' => 'L (' . $lpx_fcz['size_l'] . ')' ),", PART)
        self.assertIn("'sizes'     => array( 'M' => 'M (EU ' . $lpx_fen['size_m'] . ')', 'L' => 'L (EU ' . $lpx_fen['size_l'] . ')' ),", PART)
        self.assertIn("sprintf( 'M sedí na velikost nohy %s, L na %s. Pokud si nejste jistí, zeptejte se obdarovaného na velikost bot.', $lpx_fcz['size_m'], $lpx_fcz['size_l'] )", PART)
        self.assertIn("sprintf( 'Doprava od %d Kč. Objednejte do %s, doručíme před Vánoci. Platbu a dopravu vybíráte v pokladně; ', $lpx_fcz['ship_from'], $lpx_fcz['order_by'] ) . molosoc_cod_cz_text()", PART)
        self.assertIn("sprintf( 'M fits shoe sizes EU %s, L fits %s. If unsure, ask the recipient for their shoe size.', $lpx_fen['size_m'], $lpx_fen['size_l'] )", PART)
        self.assertIn("sprintf( 'Shipping from %d CZK. Order by %s for delivery before Christmas. Shipping and payment methods are chosen at checkout.', $lpx_fen['ship_from'], $lpx_fen['order_by'] )", PART)
        # The FAQ itself (four items, <details>) is unchanged.
        self.assertEqual(PART.count("<details><summary>"), 1)
        for q in ("Jakou velikost vybrat?", "Kolik stojí doprava a platba?", "Jak se o návleky starat?", "Je to vhodné jako dárek?"):
            self.assertIn("'%s'" % q, PART)


class InfoBlock(unittest.TestCase):
    EXPECTED = {
        "cz": [
            "Velikost: M = 36–39 · L = 39,5–44 (podle velikosti bot)",
            "Doprava od 69 Kč · můžete platit i dobírkou",
            "Objednejte do 18. prosince, doručíme před Vánoci",
        ],
        "en": [
            "Size: M = EU 36–39 · L = EU 39.5–44 (by shoe size)",
            "Shipping from 69 CZK · cash on delivery available",
            "Order by 18 December for delivery before Christmas",
        ],
    }

    def composed(self, lang):
        pats = re.findall(r"array\( '(\w+)', sprintf\( '([^']*)'((?:, \$lpx_f(?:cz|en)\['\w+'\])+) \) \)", facts_block(lang))
        out = []
        for icon, fmt, args in pats:
            keys = re.findall(r"\['(\w+)'\]", args)
            out.append((icon, fmt % tuple(FACTS[lang][k] for k in keys)))
        return out

    def test_composed_copy_is_the_issue_copy_in_both_languages(self):
        for lang in ("cz", "en"):
            rows = self.composed(lang)
            self.assertEqual([text for _, text in rows], self.EXPECTED[lang], lang)
            self.assertEqual([icon for icon, _ in rows], ["size", "ship", "date"], lang)

    def test_icons_exist_for_every_row(self):
        icons = block(PART, "$lpx_icon = static function ( $name ) {", "\n};")
        for key in ("'size'", "'ship'", "'date'"):
            self.assertIn(key + " => '<", icons)
        self.assertIn('aria-hidden="true" focusable="false"', icons)
        self.assertIn('width="16" height="16"', icons)
        self.assertIn('stroke="currentColor"', icons)

    def test_block_sits_right_after_the_button_in_the_shared_picker(self):
        picker = block(PART, "$lpx_picker = static function ( $id )", "\n};")
        btn = picker.index("data-lpx-go")
        err = picker.index('class="lpb-buy__error lpx-buy__error"')
        facts = picker.index('<ul class="lpx-facts">')
        self.assertLess(btn, err)
        self.assertLess(err, facts)
        self.assertLess(facts, picker.rindex("</div>"))
        self.assertIn("$lpx_icon( $fact[0] )", picker)
        self.assertIn("esc_html( $fact[1] )", picker)
        self.assertIn("$lpx_icon )", picker[: picker.index("?>")])  # captured by the closure
        self.assertEqual(PART.count('<ul class="lpx-facts">'), 1)   # printed by the picker…
        self.assertEqual(PART.count("$lpx_picker( "), 2)           # …which both pickers call

    def test_size_hint_once_under_the_pair_one_label(self):
        self.assertIn("'size_hint' => 'Nevíte? Zeptejte se na velikost bot.',", PART)
        self.assertIn("'size_hint' => 'Not sure? Ask for their shoe size.',", PART)
        self.assertIn("<?php if ( 1 === $n ) : ?>\n\t\t\t\t\t<p class=\"lpx-pair__hint\"><?php echo esc_html( $t['size_hint'] ); ?></p>\n\t\t\t\t<?php endif; ?>", PART)
        self.assertLess(PART.index('lpx-pair__legend">'), PART.index('class="lpx-pair__hint"'))
        self.assertLess(PART.index('class="lpx-pair__hint"'), PART.index('<label class="lpb-size">'))

    def test_compact_muted_readable(self):
        facts = re.search(r"\n\.lpx-facts \{([^}]*)\}", CSS_CODE).group(1)
        self.assertIn("font-size: 0.9rem", facts)
        self.assertIn("color: var(--lpb-body, rgba(64, 53, 42, .84))", facts)  # ~6.9:1 on cream, ~7.6:1 on white
        self.assertIn("list-style: none", facts)
        for heavy in ("border", "background", "box-shadow"):
            self.assertNotIn(heavy, facts, heavy)  # no card
        mobile = CSS_CODE[CSS_CODE.rindex("@media (max-width: 560px)"):]
        self.assertRegex(mobile, r"\.lpx-facts \{[^}]*font-size: 0\.85rem")
        hint = re.search(r"\n\.lpx-pair__hint \{([^}]*)\}", CSS_CODE).group(1)
        self.assertIn("flex: 0 0 100%", hint)  # its own row inside the flex size fieldset
        self.assertIn("font-size: 0.8rem", hint)

    def test_no_new_claims(self):
        low = PART_CODE.lower()
        for banned in ("zdarma", "free shipping", "sleva", "discount", "doručíme do ", "delivered by", "next day", "do 24"):
            self.assertNotIn(banned, low, banned)
        self.assertIn("array( 1 => 209, 2 => 199, 3 => 199 )", INC)  # prices untouched


class ResponsiveImages(unittest.TestCase):
    IMG = ROOT / "assets/images/landing-xmas"

    def test_derivatives_exist_with_the_declared_widths(self):
        self.assertIn("return array( 480, 768, 1080 );", INC)
        for n in ("01", "02", "03"):
            for w in (480, 768, 1080):
                data = (self.IMG / f"MOLOSOC_Christmas_Gift_Scene_{n}-{w}.webp").read_bytes()
                self.assertEqual(webp_width(data), w, (n, w))

    def test_hero_byte_budget_for_phones(self):
        size = {w: len((self.IMG / f"MOLOSOC_Christmas_Gift_Scene_01-{w}.webp").read_bytes()) for w in (480, 768, 1080)}
        # 390 px phone: calc(100vw - 40px) = 350 CSS px → 700 px at 2x (768w), 1050 px at 3x (1080w).
        self.assertLessEqual(size[480], 30_000)
        self.assertLessEqual(size[768], 60_000)
        self.assertLessEqual(size[1080], 75_000)

    def test_originals_are_untouched(self):
        base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        if not base:
            self.skipTest("no origin/main")
        # The 1536 px originals are never re-encoded (landing-xmas.js was pinned here too until Issue #299 changed it on purpose).
        changed = subprocess.run(["git", "diff", "--name-only", base, "--", "site/theme/assets/images/landing-xmas"], cwd=REPO, capture_output=True, text=True).stdout.split()
        self.assertEqual([c for c in changed if re.search(r"Scene_0\d\.webp$", c)], [])

    def test_one_candidate_list_for_the_img_and_the_preload(self):
        self.assertIn("function molosoc_xmas_image_set( $key )", INC)
        self.assertIn("'(max-width: 900px) calc(100vw - 40px), 524px'", INC)
        img = block(INC, "function molosoc_xmas_image( $key, $alt, $attrs = '' )", "\n}")
        self.assertIn("molosoc_xmas_image_set( $key )", img)
        self.assertIn('\'<img src="%s" srcset="%s" sizes="%s" alt="%s"%s decoding="async" %s>\'', img)
        head = block(INC, "function molosoc_xmas_head()", "add_action( 'wp_head', 'molosoc_xmas_head', 1 );")
        self.assertIn("if ( ! molosoc_is_xmas_landing() ) {", head)
        self.assertIn("molosoc_xmas_image_set( 'scene-01' )", head)
        self.assertIn('<link rel="preload" as="image" fetchpriority="high" href="%s" imagesrcset="%s" imagesizes="%s">', head)
        self.assertIn("add_action( 'wp_head', 'molosoc_xmas_head', 1 );", INC)
        self.assertIn("if ( ! file_exists( $path ) )", INC)  # a missing original still prints nothing

    def test_hero_is_eager_and_high_priority_the_other_two_lazy(self):
        self.assertIn("molosoc_xmas_image( 'scene-01', 'cz' === $lpx_lang ? 'Vánoční dárek MOLOSOC' : 'MOLOSOC Christmas gift', 'fetchpriority=\"high\" loading=\"eager\"' )", PART)
        self.assertEqual(PART.count("'loading=\"lazy\"' )"), 2)


class HeaderLogo(unittest.TestCase):
    OLD_TAG = '<img src="https://molosoc.com/wp-content/uploads/2026/06/MOLOSOC-Logo-TM.png" alt="<?php echo esc_attr( get_bloginfo( \'name\' ) ); ?>" loading="eager" decoding="async">'

    def test_default_markup_is_what_the_template_printed_before(self):
        self.assertNotIn(self.OLD_TAG, HEADER)
        self.assertIn("<?php molosoc_site_header_logo();", HEADER)
        fn = block(FUNCTIONS, "function molosoc_site_header_logo()", "\n}")
        self.assertIn("""$default = '<img src="https://molosoc.com/wp-content/uploads/2026/06/MOLOSOC-Logo-TM.png" alt="' . esc_attr( get_bloginfo( 'name' ) ) . '" loading="eager" decoding="async">';""", fn)
        self.assertIn("echo apply_filters( 'molosoc_site_header_logo', $default );", fn)

    def test_christmas_pages_swap_in_the_resized_set(self):
        fn = block(INC, "function molosoc_xmas_header_logo( $html )", "add_filter( 'molosoc_site_header_logo'")
        self.assertIn("if ( ! molosoc_is_xmas_landing() ) {", fn)
        self.assertIn("return $html;", fn)
        self.assertIn('srcset="%2$s 408w, %1$s 612w" sizes="(max-width: 380px) 164px, 205px" width="612" height="90"', fn)
        self.assertIn("add_filter( 'molosoc_site_header_logo', 'molosoc_xmas_header_logo' );", INC)
        for w in (408, 612):
            data = (ROOT / f"assets/images/molosoc-logo-tm-{w}.webp").read_bytes()
            self.assertEqual(webp_width(data), w)
            self.assertLessEqual(len(data), 15_000)


class PluginAssetsGate(unittest.TestCase):
    def test_christmas_pages_join_the_gate_without_removing_a_line(self):
        gate = block(FUNCTIONS, "function molosoc_page_without_plugin_markup()", "\n}")
        self.assertIn("if ( function_exists( 'molosoc_is_xmas_landing' ) && molosoc_is_xmas_landing() ) return true;", gate)
        self.assertIn("return is_front_page() || is_page( 'hydratacni-navleky-molosoc' ) || molosoc_is_landing_page_a();", gate)
        # tests/test_landing_b_template.py reads this gate up to its first closing brace.
        self.assertNotIn("}", gate[: gate.index("return is_front_page()")])
        self.assertIn("function molosoc_is_xmas_landing()", INC)
        self.assertIn("return '' !== molosoc_xmas_current_lang();", INC)

    def test_extra_handles_for_the_christmas_pages_only(self):
        dq = block(FUNCTIONS, "function molosoc_dequeue_unused_homepage_assets()", "add_action( 'wp_print_footer_scripts', 'molosoc_dequeue_unused_homepage_assets', 1 );")
        xmas = block(dq, "if ( function_exists( 'molosoc_is_xmas_landing' ) && molosoc_is_xmas_landing() ) {", "foreach ( $scripts as $handle )")
        for handle in ("'woocommerce'", "'cr-colcade'", "'wc-photoswipe'", "'wc-photoswipe-ui-default'"):
            self.assertIn(handle, xmas, handle)
        shared = dq[: dq.index("if ( is_page( 'hydratacni-navleky-molosoc' ) || molosoc_is_landing_page_a() ) {")]
        for handle in ("'jquery'", "'jquery-migrate'", "'wc-add-to-cart'", "'wc-cart-fragments'", "'select2'", "'cr-frontend-js'", "'woocommerce-analytics-client'", "'tve-dash-frontend'"):
            self.assertIn(handle, shared, handle)
        self.assertNotIn("'wc-photoswipe'", shared)  # homepage / B / A lists untouched
        # What must survive: pixel + signals, consent, Clarity (inline), cart badge sync, order attribution.
        for keep in ("'wc-facebook", "'wpconsent", "'molosoc-cart-badge-sync'", "'wc-order-attribution'", "'sourcebuster", "clarity"):
            self.assertNotIn(keep, dq, keep)

    def test_functions_php_and_header_only_gained_lines(self):
        base = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], cwd=REPO, capture_output=True, text=True).stdout.strip()
        if not base:
            self.skipTest("no origin/main")
        diff = subprocess.run(["git", "diff", "-U0", base, "--", "site/theme/functions.php"], cwd=REPO, capture_output=True, text=True).stdout
        self.assertEqual([l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")], [])


class ThemeVersion(unittest.TestCase):
    def test_bumped_so_the_css_and_bundles_refresh(self):
        version = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M)
        self.assertIsNotNone(version)
        self.assertGreaterEqual(tuple(int(v) for v in version.groups()), (0, 2, 105))


if __name__ == "__main__":
    unittest.main()
