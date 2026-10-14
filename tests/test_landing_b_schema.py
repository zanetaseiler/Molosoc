"""Issue #155 / #159: meta description + JSON-LD for the CZ landing page
/cz/hydratacni-navleky-molosoc/.

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
// wp_get_document_title() is HTML-escaped by WordPress (Issue #159: the en dash came out as the literal &#8211;).
function wp_get_document_title() { return 'Hydratační návleky na nohy &#8211; MOLOSOC &lt;/script&gt; &amp; co'; }
function esc_attr($s) { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }
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


def homepage_block(fn):
    """The inline JSON-LD of molosoc_homepage_schema() in functions.php, parsed."""
    body = fn[fn.index("function molosoc_homepage_schema()"):]
    body = body[: body.index("add_action( 'wp_head', 'molosoc_homepage_schema' )")]
    return json.loads(blocks(body)[0])


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
        # logo / sameAs are allowed only inside the site nodes mirrored from the homepage.
        start = code.index("function molosoc_landing_b_schema_site_nodes()")
        end = code.index("function molosoc_landing_b_schema_faq(")
        code = code[:start] + code[end:]
        for bad in ("'Product'", "'Offer'", "'AggregateRating'", "'Review'", "gtin", "'logo'", "sameAs",
                    "'BreadcrumbList'", "'image'", "price", "availability", "hasMerchantReturnPolicy"):
            self.assertNotIn(bad, code.replace("$price", ""), bad)

    def test_site_nodes_mirror_the_homepage_graph(self):
        """Organization/WebSite values are copied from molosoc_homepage_schema(), never invented."""
        home = {n["@type"]: n for n in homepage_block(self.fn)["@graph"]}
        nodes = self.src[self.src.index("function molosoc_landing_b_schema_site_nodes()"):]
        nodes = nodes[: nodes.index("function molosoc_landing_b_schema_faq(")]
        org, site = home["Organization"], home["WebSite"]
        for literal in (org["@id"], org["name"], org["url"], org["logo"]["url"], site["@id"], site["url"], site["name"]):
            self.assertIn(f"'{literal}'", nodes, literal)
        same_as = re.findall(r"'(https://[^']+)',\n", nodes[nodes.index("'sameAs'"):nodes.index("'WebSite'")])
        self.assertEqual(same_as, org["sameAs"])
        # The homepage's EN description / inLanguage are not repeated on the Czech page.
        self.assertNotIn("'description'", nodes)
        self.assertNotIn("'inLanguage'", nodes)
        self.assertNotIn(org["description"][:30], self.src)

    def test_meta_description_and_title_decode_are_wired(self):
        self.assertEqual(self.src.count('<meta name="description" content="'), 1)
        self.assertIn("esc_attr( molosoc_landing_b_schema_description() )", self.src)
        self.assertIn("html_entity_decode( wp_get_document_title(), ENT_QUOTES, 'UTF-8' )", self.src)
        self.assertNotIn("\t\twp_get_document_title(),", self.src)
        # Issue #161: the WebPage name follows the fixed <title> that functions.php
        # returns from pre_get_document_title (wp_get_document_title() passes it
        # through verbatim), so it carries no "&#8211;" and no "(varianta, koncept)".
        m = re.search(r"function molosoc_landing_b_document_title\(\) \{\s*return '(.*?)';", self.fn, re.S)
        self.assertEqual(m.group(1), "Hydratační maska na nohy na opakované použití | Molosoc")
        self.assertNotIn("&", m.group(1))
        self.assertEqual(html.unescape(m.group(1)), m.group(1))

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
        return [(x["name"], x["acceptedAnswer"]["text"]) for x in g["@graph"][3]["mainEntity"]]

    def test_template_price_constants_match_schema_call(self):
        self.assertIn("$lpb_price       = '229 Kč';", self.tpl)
        self.assertIn("$lpb_shipping    = 'Doprava od 79 Kč';", self.tpl)
        self.assertIn("molosoc_landing_b_schema_faq( '229 Kč', 'Doprava od 79 Kč' )", self.src)

    def test_description_words_are_on_the_page(self):
        m = re.search(r"function molosoc_landing_b_schema_description\(\) \{\s*return '(.*?)';", self.src, re.S)
        desc = m.group(1)
        # Issue #161 text (Google truncates around 155-160) and only on-page claims.
        self.assertEqual(desc, "Hydratační maska na nohy MOLOSOC na opakované použití. Funguje s krémem, který už máte — bez nepořádku a bez klouzání. 229 Kč.")
        self.assertTrue(110 <= len(desc) <= 158, len(desc))
        page = html.unescape(self.tpl).lower()
        for phrase in ("Hydratační maska na nohy", "na opakované použití", "s krémem, který už máte",
                       "bez nepořádku", "bez klouzání", "229 Kč"):
            self.assertIn(phrase.lower(), desc.lower(), phrase)
            self.assertIn(phrase.lower(), page, phrase)
        # Pillar 1 / category terms stay out of the meta description.
        for term in ("popraskané paty", "suché paty", "návleky na nohy"):
            self.assertNotIn(term, desc.lower(), term)
        self.assertNotRegex(desc, r"(?i)léč|zdrav|vyléč|klinick|dermatolog")
        self.assertNotIn("&", desc)
        self.assertNotIn('"', desc)


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
        self.assertEqual(types, ["Organization", "WebSite", "WebPage", "FAQPage"])
        org, site, page, faq = g["@graph"]
        self.assertEqual(org["@id"], "https://molosoc.com/#organization")
        self.assertEqual(site["@id"], "https://molosoc.com/#website")
        self.assertEqual(site["publisher"], {"@id": org["@id"]})
        home = {n["@type"]: n for n in homepage_block(FUNCTIONS.read_text())["@graph"]}
        self.assertEqual(org["sameAs"], home["Organization"]["sameAs"])
        self.assertEqual(org["logo"], home["Organization"]["logo"])
        # Title entity-decoded (Issue #159): "–" instead of the literal "&#8211;".
        self.assertEqual(page["name"], "Hydratační návleky na nohy – MOLOSOC </script> & co")
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
        self.assertNotIn("&#8211;", out)

    def test_meta_description_printed_once_before_the_graph(self):
        out = run_php(True, "cz")
        metas = re.findall(r'<meta name="description" content="([^"]*)">', out)
        self.assertEqual(len(metas), 1)
        self.assertLess(out.index('<meta name="description"'), out.index('<script type="application/ld+json">'))
        self.assertEqual(html.unescape(metas[0]), json.loads(blocks(out)[0])["@graph"][2]["description"])

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
