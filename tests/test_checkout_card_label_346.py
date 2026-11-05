"""Issue #346: clearer card-payment label on the checkout.

CZ: the Comgate gateway title names card + Apple Pay + Google Pay and "no
surcharge". EN: the Comgate description set in WP admin is Czech and contains
the word "Comgate", so its map entry must win over the bare 'Comgate' entry
(first match wins in molosoc_en_shipping_payment_text()).

The map is read from the PHP source and the first-match loop is replayed in
Python, so the ordering is checked without a php CLI; the same cases also run
under real PHP when it is available.
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEANUP_PHP = ROOT / "site/theme/inc/checkout-cleanup.php"
LANG_PHP = ROOT / "site/theme/inc/woocommerce-lang.php"

CZ_TITLE = "Kartou, Apple Pay nebo Google Pay (bez příplatku)"
CZ_DESC = "Rychlá a bezpečná platba přes platební bránu Comgate. Bez příplatku – objednávku odesíláme hned po zaplacení."
EN_DESC = "Fast, secure payment via the Comgate gateway. No fee – we ship as soon as payment is received."
EN_TITLE = "Card payment (Comgate)"

# (input text, expected EN output)
MAP_CASES = [
    (CZ_DESC, EN_DESC),
    (CZ_DESC.replace(" – ", " - "), EN_DESC),  # stored with a plain hyphen
    ("Comgate", EN_TITLE),  # the stored gateway title
    ("Bezpečná online platba kartou", EN_TITLE),  # the previous description
    ("Bankovní převod", "Bank transfer"),
    ("Dobírka", "Dobírka"),  # no entry: left exactly as built
]


def extract(src, name):
    m = re.search(r"^function %s\s*\(.*?^\}" % re.escape(name), src, re.S | re.M)
    assert m, name
    return m.group(0)


def en_map():
    """The CZ->EN map as an ordered list of (substring, label) pairs."""
    fn = extract(LANG_PHP.read_text(encoding="utf-8"), "molosoc_en_shipping_payment_text")
    return re.findall(r"^\s*'([^']+)'\s*=>\s*'([^']+)',\s*$", fn, re.M)


def translate(text):
    for cz, en in en_map():
        if cz.lower() in text.lower():
            return en
    return text


class EnPaymentTextMapTests(unittest.TestCase):
    def test_map_cases(self):
        for text, expected in MAP_CASES:
            self.assertEqual(translate(text), expected, text)

    def test_description_entries_precede_bare_comgate(self):
        keys = [cz for cz, _ in en_map()]
        bare = keys.index("Comgate")
        described = [i for i, k in enumerate(keys) if k.startswith("Rychlá a bezpečná platba")]
        self.assertEqual(len(described), 2)
        self.assertTrue(all(i < bare for i in described))

    def test_existing_entries_kept(self):
        pairs = dict(en_map())
        self.assertEqual(pairs["Bezpečná online platba kartou"], EN_TITLE)
        self.assertEqual(pairs["Comgate"], EN_TITLE)

    def test_no_czech_left_in_en_output(self):
        out = translate(CZ_DESC)
        for cz_word in ("platba", "příplatku", "objednávku", "Rychlá"):
            self.assertNotIn(cz_word, out)


class CzCardLabelStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fn = extract(CLEANUP_PHP.read_text(encoding="utf-8"), "molosoc_cz_gateway_title")

    def test_new_title_replaces_old(self):
        self.assertIn("return '%s';" % CZ_TITLE, self.fn)
        self.assertNotIn("Platba kartou (Comgate)", self.fn)

    def test_other_methods_untouched(self):
        self.assertIn("return 'Bankovní převod (platba předem)';", self.fn)
        self.assertNotIn("'cod'", self.fn)
        self.assertNotIn("Dobírka", self.fn)

    def test_still_cz_only(self):
        self.assertIn("'cz' !== pll_current_language()", self.fn)


@unittest.skipUnless(shutil.which("php"), "php CLI not available")
class EnPaymentTextPhpTests(unittest.TestCase):
    def run_php(self, lang, calls):
        src = LANG_PHP.read_text(encoding="utf-8")
        funcs = "\n".join(
            extract(src, n)
            for n in ("molosoc_en_shipping_payment_text", "molosoc_en_gateway_title", "molosoc_en_gateway_description")
        )
        code = "<?php\nfunction pll_current_language() { return '%s'; }\n%s\n%s" % (lang, funcs, calls)
        with tempfile.NamedTemporaryFile("w", suffix=".php", delete=False, encoding="utf-8") as f:
            f.write(code)
        out = subprocess.run(["php", f.name], capture_output=True, text=True, check=True)
        Path(f.name).unlink()
        return out.stdout

    def test_map_cases_under_php(self):
        for text, expected in MAP_CASES:
            self.assertEqual(self.run_php("en", "echo molosoc_en_shipping_payment_text(%r);" % text), expected, text)

    def test_en_checkout_title_and_description(self):
        # Issue #348: the EN title is decided by gateway ID, not by the map.
        self.assertEqual(
            self.run_php("en", "echo molosoc_en_gateway_title('Comgate', 'wf-woo-comgate');"),
            "Card, Apple Pay or Google Pay (no fee)",
        )
        self.assertEqual(
            self.run_php("en", "echo molosoc_en_gateway_description(%r, 'wf-woo-comgate');" % CZ_DESC), EN_DESC
        )

    def test_cz_checkout_description_untouched(self):
        self.assertEqual(
            self.run_php("cz", "echo molosoc_en_gateway_description(%r, 'wf-woo-comgate');" % CZ_DESC), CZ_DESC
        )


if __name__ == "__main__":
    unittest.main()
