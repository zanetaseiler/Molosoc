"""Issue #267: checkout cleanup — CZ payment labels, Czech CusRev checkbox
text, smaller Comgate logo. The PHP functions are extracted from the theme and
executed under the php CLI with tiny WordPress stand-ins (no network, no live
site); the CSS is checked statically."""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG_PHP = ROOT / "site/theme/inc/checkout-cleanup.php"
FUNCTIONS = ROOT / "site/theme/functions.php"
CSS = ROOT / "site/theme/assets/css/checkout.css"

CZ_BOX = "Chcete být pozváni k hodnocení objednávky? Zaškrtnutím obdržíte zprávu od CusRev (nezávislé služby recenzí) s formulářem hodnocení."
EN_BOX = "Would you like to be invited to review your order? Check here to receive a message from CusRev (an independent reviews service) with a review form."


def extract(src, name):
    m = re.search(r"^function %s\s*\(.*?^\}" % re.escape(name), src, re.S | re.M)
    assert m, name
    return m.group(0)


def run_php(lang, checkout, calls):
    src = LANG_PHP.read_text(encoding="utf-8")
    funcs = "\n".join(
        extract(src, n) for n in ("molosoc_cz_gateway_title", "molosoc_cz_cusrev_checkbox_text")
    )
    stubs = "<?php\n"
    if lang is not None:
        stubs += "function pll_current_language() { return %s; }\n" % ("false" if lang == "" else "'%s'" % lang)
    stubs += "function is_checkout() { return %s; }\n" % ("true" if checkout else "false")
    code = stubs + funcs + "\n" + calls
    with tempfile.NamedTemporaryFile("w", suffix=".php", delete=False, encoding="utf-8") as f:
        f.write(code)
    out = subprocess.run(["php", f.name], capture_output=True, text=True, check=True)
    Path(f.name).unlink()
    return out.stdout


@unittest.skipUnless(shutil.which("php"), "php CLI not available")
class CheckoutCleanupPhpTests(unittest.TestCase):
    def title(self, lang, gid, title="orig"):
        return run_php(lang, True, "echo molosoc_cz_gateway_title(%r, %r);" % (title, gid))

    def box(self, lang, checkout=True, text=EN_BOX, domain="customer-reviews-woocommerce"):
        return run_php(lang, checkout, "echo molosoc_cz_cusrev_checkbox_text(%r, %r, %r);" % (text, text, domain))

    def test_cz_titles_distinct(self):
        self.assertEqual(self.title("cz", "comgate"), "Platba kartou (Comgate)")
        self.assertEqual(self.title("cz", "wf_woo_comgate"), "Platba kartou (Comgate)")
        self.assertEqual(self.title("cz", "bacs"), "Bankovní převod (platba předem)")

    def test_cod_and_unknown_untouched(self):
        self.assertEqual(self.title("cz", "cod", "Dobírka"), "Dobírka")
        self.assertEqual(self.title("cz", "other", "X"), "X")

    def test_not_applied_outside_cz(self):
        for lang in ("en", "", None):
            self.assertEqual(self.title(lang, "comgate", "T"), "T")
            self.assertEqual(self.title(lang, "bacs", "T"), "T")

    def test_checkbox_czech_on_cz_checkout(self):
        self.assertEqual(self.box("cz"), CZ_BOX)
        self.assertEqual(self.box("cz", domain="some-other-domain"), CZ_BOX)

    def test_checkbox_english_kept_on_en_and_unresolved(self):
        for lang in ("en", "", None):
            self.assertEqual(self.box(lang), EN_BOX)

    def test_checkbox_not_touched_off_checkout(self):
        self.assertEqual(self.box("cz", checkout=False), EN_BOX)

    def test_other_strings_untouched(self):
        self.assertEqual(self.box("cz", text="Quantity"), "Quantity")


class CheckoutCleanupStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = LANG_PHP.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")

    def test_hooks_registered(self):
        self.assertIn("add_filter( 'woocommerce_gateway_title', 'molosoc_cz_gateway_title', 10, 2 );", self.src)
        self.assertIn("add_filter( 'gettext', 'molosoc_cz_cusrev_checkbox_text', 10, 3 );", self.src)

    def test_no_consent_or_gateway_mutation(self):
        body = self.src
        for bad in ("update_option", "delete_option", "unset(", "ivole", "_checked", "checked="):
            self.assertNotIn(bad, body)

    def test_required_from_functions_php(self):
        self.assertIn("/inc/checkout-cleanup.php'", FUNCTIONS.read_text(encoding="utf-8"))

    def test_css_logo_size_and_mobile(self):
        self.assertIn('img[src*="comgate"]', self.css)
        self.assertRegex(self.css, r"width:\s*112px")
        self.assertRegex(self.css, r"@media \(max-width: 480px\)")
        self.assertRegex(self.css, r"max-width:\s*100%")
        self.assertRegex(self.css, r"height:\s*auto")

    def test_css_enqueued_only_on_checkout(self):
        fn = extract(self.src, "molosoc_enqueue_checkout_css")
        self.assertIn("is_checkout()", fn)
        self.assertIn("assets/css/checkout.css", fn)


if __name__ == "__main__":
    unittest.main()
