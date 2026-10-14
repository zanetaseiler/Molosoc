"""Issue #155: JSON-LD for the CZ landing page /cz/hydratacni-navleky-molosoc/.

Static checks plus php-cli runs of inc/landing-b-schema.php against a tiny
WordPress stub (skipped when php is not installed).
"""
import html
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
SCHEMA = ROOT / "inc/landing-b-schema.php"
TEMPLATE = ROOT / "page-hydratacni-navleky-molosoc.php"
FUNCTIONS = ROOT / "functions.php"
CANON = "https://molosoc.com/cz/hydratacni-navleky-molosoc/"
PRODUCT = "https://molosoc.com/cz/produkt/hydratacni-navlek-na-nohy/"

# $slug_match / $lang / $permalink drive the stubbed conditionals.
STUB = r"""<?php
define('ABSPATH', '/');
define('JSON_HEX_TAG_X', 1);
$slug_match = (bool) (int) $argv[1];
$lang = $argv[2];            // 'cz', 'en' or '' (Polylang inactive)
$permalink = $argv[3];
function add_action($h, $cb) {}
function is_page($s) { global $slug_match; return $slug_match && $s === 'hydratacni-navleky-molosoc'; }
function get_permalink() { global $permalink; return $permalink; }
function wp_get_document_title() { return 'Hydratační návleky na nohy </script> & MOLOSOC'; }
function molosoc_product_url($l) { return 'https://molosoc.com/cz/produkt/hydratacni-navlek-na-nohy/'; }
function wp_json_encode($d, $f = 0) { return json_encode($d, $f); }
if ($lang !== '') { function pll_current_language() { global $lang; return $lang; } }
require $argv[4];
molosoc_landing_b_schema();
"""


def run_php(slug_match, lang, permalink=CANON):
    with tempfile.TemporaryDirectory() as d:
        stub = Path(d) / "stub.php"
        stub.write_text(STUB)
        out = subprocess.run(
            ["php", str(stub), str(int(slug_match)), lang, permalink, str(SCHEMA)],
            capture_output=True, text=True, check=True,
        ).stdout
    return out


def blocks(out):
    return re.findall(r'<script type="application/ld\+json">(.*?)</script>', out, re.S)


class LandingBSchemaStatic(unittest.TestCase):
    def setUp(self):
        self.src = SCHEMA.read_text()
        self.fn = FUNCTIONS.read_text()
        self.tpl = TEMPLATE.read_text()

    def test_wired_once_from_functions_after_woocommerce_lang(self):
        self.assertEqual(self.fn.count("inc/landing-b-schema.php"), 1)
        self.assertLess(self.fn.index("inc/woocommerce-lang.php"), self.fn.index("inc/landing-b-schema.php"))

    def test_hooked_once_on_wp_head_and_slug_gated(self):
        self.assertEqual(self.src.count("add_action( 'wp_head', 'molosoc_landing_b_schema' )"), 1)
        self.assertIn("is_page( 'hydratacni-navleky-molosoc' )", self.src)
        self.assertIn("pll_current_language() )", self.src)

    def test_no_forbidden_markup(self):
        code = re.sub(r"/\*.*?\*/", "", self.src, flags=re.S)
        for bad in ("'Product'", "'Offer'", "'AggregateRating'", "'Review'", "gtin", "'logo'", "sameAs",
                    "'BreadcrumbList'", "'image'", "price", "availability", "hasMerchantReturnPolicy"):
            self.assertNotIn(bad, code.replace("$price", ""), bad)

    def test_faq_matches_visible_template_exactly(self):
        details = re.findall(r"<details>\s*<summary>(.*?)</summary>\s*(?:<\?php.*?\?>\s*)?<p>(.*?)</p>", self.tpl, re.S)
        self.assertEqual(len(details), 6)
        visible = []
        for q, a in details:
            a = re.sub(r"<\?php echo esc_html\( \$lpb_price \); \?>", "{PRICE}", a)
            a = re.sub(r"<\?php echo esc_html\( \$lpb_shipping \); \?>", "{SHIP}", a)
            visible.append((html.unescape(q), html.unescape(a)))
        faq = [(q, a.replace("229 Kč", "{PRICE}").replace("Doprava od 79 Kč", "{SHIP}"))
               for q, a in self._php_faq()]
        self.assertEqual(visible, faq)

    def _php_faq(self):
        if not shutil.which("php"):
            self.skipTest("php not installed")
        g = json.loads(blocks(run_php(True, "cz"))[0])
        return [(x["name"], x["acceptedAnswer"]["text"]) for x in g["@graph"][1]["mainEntity"]]

    def test_template_price_constants_match_schema_call(self):
        self.assertIn("$lpb_price       = '229 Kč';", self.tpl)
        self.assertIn("$lpb_shipping    = 'Doprava od 79 Kč';", self.tpl)
        self.assertIn("molosoc_landing_b_schema_faq( '229 Kč', 'Doprava od 79 Kč' )", self.src)

    def test_description_words_are_on_the_page(self):
        m = re.search(r"function molosoc_landing_b_schema_description\(\) \{\s*return '(.*?)';", self.src, re.S)
        desc = m.group(1)
        for phrase in ("Bez klouzání", "Bez čekání", "Bez mastných stop", "100% nitril", "Bez latexu"):
            self.assertIn(phrase.lower(), self.tpl.lower(), phrase)
        self.assertNotRegex(desc, r"(?i)léč|zdrav|vyléč|klinick|dermatolog")


@unittest.skipUnless(shutil.which("php"), "php not installed")
class LandingBSchemaRendered(unittest.TestCase):
    def graph(self):
        out = run_php(True, "cz")
        b = blocks(out)
        self.assertEqual(len(b), 1)
        return json.loads(b[0])  # syntax check

    def test_cz_landing_graph(self):
        g = self.graph()
        self.assertEqual(g["@context"], "https://schema.org")
        types = [n["@type"] for n in g["@graph"]]
        self.assertEqual(types, ["WebPage", "FAQPage"])
        page, faq = g["@graph"]
        self.assertEqual(page["@id"], CANON + "#webpage")
        self.assertEqual(page["url"], CANON)
        self.assertEqual(page["inLanguage"], "cs")
        self.assertEqual(page["significantLink"], PRODUCT)
        self.assertEqual(page["isPartOf"], {"@id": "https://molosoc.com/#website"})
        self.assertEqual(page["publisher"], {"@id": "https://molosoc.com/#organization"})
        self.assertEqual(faq["@id"], CANON + "#faq")
        self.assertEqual(len(faq["mainEntity"]), 6)

    def test_no_duplicate_ids_or_product(self):
        g = self.graph()
        ids = [n["@id"] for n in g["@graph"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn("Product", json.dumps(g))
        self.assertNotIn("Offer", json.dumps(g))
        # the product page's @id must not be (re)declared here
        self.assertFalse(any(i.startswith(PRODUCT) for i in ids))

    def test_script_breakout_is_escaped(self):
        out = run_php(True, "cz")
        self.assertEqual(out.count("</script>"), 1)
        self.assertIn("\\u003C/script\\u003E", out)

    def test_canonical_follows_permalink(self):
        out = run_php(True, "cz", "https://molosoc.com/cz/jiny-slug/")
        self.assertIn("https://molosoc.com/cz/jiny-slug/#webpage", out)
        self.assertNotIn(CANON, out)

    def test_nothing_on_other_pages_or_english(self):
        self.assertEqual(run_php(False, "cz").strip(), "")   # unrelated page / product / EN counterpart slugs
        self.assertEqual(run_php(True, "en").strip(), "")    # EN page reusing the slug
        self.assertNotEqual(run_php(True, "").strip(), "")   # Polylang inactive: still the CZ-only page


if __name__ == "__main__":
    unittest.main()
