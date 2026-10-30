"""Issue #303: every button and link that used to go to Landing Page A goes to
Landing Page B (like the main menu) through one helper, molosoc_landing_url(),
which falls back to Landing A for a language whose Landing B page is not
published (EN today). Static checks, no PHP/WordPress runtime."""
import glob
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
INC = (ROOT / "inc/landing-links.php").read_text(encoding="utf-8")
FUNCTIONS = (ROOT / "functions.php").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")
A_CZ = "/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/"
A_EN = "/foot-covers/moisture-lock-foot-cover/"


def block(src, start, end):
    i = src.index(start)
    return src[i: src.index(end, i)]


class Helper(unittest.TestCase):
    def test_required_after_the_en_landing_b_inc(self):
        self.assertLess(FUNCTIONS.index("/inc/landing-b-en.php';"), FUNCTIONS.index("/inc/landing-links.php';"))
        self.assertEqual(FUNCTIONS.count("require_once get_stylesheet_directory() . '/inc/landing-links.php';"), 1)

    def test_landing_b_when_published_else_landing_a(self):
        fn = block(INC, "function molosoc_landing_url( $lang = null )", "\n}")
        self.assertIn("$url  = molosoc_landing_a_url( $lang );", fn)
        self.assertIn("get_page_by_path( molosoc_landing_b_slug_for( $lang ), OBJECT, 'page' )", fn)
        self.assertIn("if ( $page && 'publish' === $page->post_status ) {", fn)
        self.assertIn("$url = get_permalink( $page );", fn)
        self.assertIn("apply_filters( 'molosoc_landing_url', $cache[ $lang ], $lang )", fn)
        self.assertIn("'hydratacni-navleky-molosoc'", block(INC, "function molosoc_landing_b_slug_for( $lang )", "\n}"))
        self.assertIn("molosoc_landing_b_en_slug()", block(INC, "function molosoc_landing_b_slug_for( $lang )", "\n}"))
        a = block(INC, "function molosoc_landing_a_url( $lang )", "\n}")
        self.assertIn(A_CZ, a)
        self.assertIn(A_EN, a)

    def test_menu_and_content_rewrites_are_hooked(self):
        self.assertIn("add_filter( 'wp_nav_menu_objects', 'molosoc_landing_links_menu' );", INC)
        self.assertIn("add_filter( 'the_content', 'molosoc_landing_links_content', 20 );", INC)
        m = block(INC, "function molosoc_landing_links_map()", "\n}")
        self.assertIn("if ( $a !== $b ) {", m)  # nothing rewritten for a language still on Landing A
        self.assertIn("untrailingslashit( $a )", m)
        c = block(INC, "function molosoc_landing_links_content( $content )", "\n}")
        self.assertIn("str_replace( array_keys( $map ), array_values( $map ), $content )", c)
        self.assertIn("if ( ! $map ||", c)

    def test_product_url_and_sticky_pill_untouched(self):
        code = re.sub(r"/\*.*?\*/", "", INC, flags=re.S)
        for needle in ("molosoc_product_url", "MOLOSOC_PRODUCT_URL", "molosocStickyCta", "wp_redirect", "wp_safe_redirect"):
            self.assertNotIn(needle, code, needle)


class Templates(unittest.TestCase):
    def test_no_template_hard_codes_a_landing_a_href_any_more(self):
        left = []
        for f in glob.glob(str(ROOT / "**/*.php"), recursive=True):
            if f.endswith("inc/landing-links.php"):
                continue
            src = Path(f).read_text(encoding="utf-8")
            for m in re.finditer(r"home_url\( '(%s|%s)' \)" % (re.escape(A_CZ), re.escape(A_EN)), src):
                left.append((Path(f).name, m.group(1)))
            for m in re.finditer(r"href=\"https://molosoc\.com(%s|%s)\"" % (re.escape(A_CZ), re.escape(A_EN)), src):
                left.append((Path(f).name, m.group(1)))
        self.assertEqual(left, [])

    def test_every_former_landing_a_link_uses_the_helper(self):
        uses = {}
        for f in glob.glob(str(ROOT / "*.php")):
            n = Path(f).read_text(encoding="utf-8").count("molosoc_landing_url(")
            if n:
                uses[Path(f).name] = n
        self.assertEqual(sum(uses.values()), 21)
        self.assertEqual(uses.get("front-page.php"), 1)       # homepage hero button
        self.assertEqual(uses.get("page-cracked-heels.php"), 2) # in-text link + CTA
        self.assertEqual(uses.get("page-sucha-kuze-na-chodidlech.php"), 2)
        self.assertEqual(uses.get("page-foot-covers.php"), 5) # 2 buttons + 3 "who is it for" cards
        for f in ("page-cracked-heels.php", "page-treatment.php", "page-prevent.php", "page-na-chodidle.php", "page-sucha-kuze-na-chodidlech.php", "page-ingrown-toenails.php", "page-callus-remover.php", "page-hardened-skin-calluses.php", "page-fix-permanently.php", "page-dry-skin-feet.php", "page-foot-cream-that-works.php", "page-cracked-heels-cream.php", "page-cracked-heels-treatment.php"):
            self.assertIn(f, uses, f)
        self.assertIn("molosoc_landing_url( $molosoc_is_cz ? 'cz' : 'en' )", (ROOT / "front-page.php").read_text(encoding="utf-8"))

    def test_landing_a_itself_and_its_gates_still_exist(self):
        self.assertTrue((ROOT / "page-moisture-lock-foot-cover.php").exists())
        self.assertIn("function molosoc_is_landing_page_a()", FUNCTIONS)
        self.assertIn("is_page( array( 'moisture-lock-foot-cover', 'hydratacni-navlek-na-nohy' ) )", FUNCTIONS)


class ThemeVersion(unittest.TestCase):
    def test_bumped(self):
        version = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M)
        self.assertGreaterEqual(tuple(int(v) for v in version.groups()), (0, 2, 110))


if __name__ == "__main__":
    unittest.main()
