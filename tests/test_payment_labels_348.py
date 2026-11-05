"""Issue #348: payment labels in harmony (CZ + EN + order record).

- EN checkout: card title "Card, Apple Pay or Google Pay (no fee)", COD title
  "Cash on delivery", COD fee line "Cash on delivery fee".
- Order record: a new Comgate order stores a short payment name in the
  order's language instead of the long checkout label.
- CZ checkout texts, other gateways and the fee amount are not touched.

Static checks and a Python replay of the text map run everywhere; the PHP
functions are also executed with small WordPress/WooCommerce stand-ins when a
php CLI is available.
"""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANG_PHP = ROOT / "site/theme/inc/woocommerce-lang.php"
CLEANUP_PHP = ROOT / "site/theme/inc/checkout-cleanup.php"

EN_CARD = "Card, Apple Pay or Google Pay (no fee)"
CZ_CARD = "Kartou, Apple Pay nebo Google Pay (bez příplatku)"
EN_SHORT = "Card / Apple Pay / Google Pay"
CZ_SHORT = "Platba kartou / Apple Pay / Google Pay"
EN_FEE = "Cash on delivery fee"

FUNCS = (
    "molosoc_en_shipping_payment_text",
    "molosoc_en_gateway_title",
    "molosoc_en_gateway_description",
    "molosoc_en_cod_fee_name",
    "molosoc_en_cod_fee_rename",
    "molosoc_order_short_payment_title",
)

PHP_STUBS = """
class Molosoc_Test_Order {
	public $method; public $title; public $meta;
	function __construct( $method, $title, $lang ) { $this->method = $method; $this->title = $title; $this->meta = $lang; }
	function get_payment_method() { return $this->method; }
	function set_payment_method_title( $t ) { $this->title = $t; }
	function get_meta( $key ) { return '_molosoc_lang' === $key ? $this->meta : ''; }
}
class Molosoc_Test_Cart {
	public $fees = array();
	function __construct( $names ) { foreach ( $names as $n ) { $f = new stdClass(); $f->name = $n; $f->amount = 29; $this->fees[] = $f; } }
	function get_fees() { return $this->fees; }
}
"""


def extract(src, name):
    m = re.search(r"^function %s\s*\(.*?^\}" % re.escape(name), src, re.S | re.M)
    assert m, name
    return m.group(0)


def lang_src():
    return LANG_PHP.read_text(encoding="utf-8")


def en_map():
    fn = extract(lang_src(), "molosoc_en_shipping_payment_text")
    return re.findall(r"^\s*'([^']+)'\s*=>\s*'([^']+)',\s*$", fn, re.M)


def translate(text):
    for cz, en in en_map():
        if cz.lower() in text.lower():
            return en
    return text


class EnTitleStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fn = extract(lang_src(), "molosoc_en_gateway_title")

    def test_en_only_guard_kept(self):
        self.assertIn("'en' !== pll_current_language()", self.fn)

    def test_card_title_by_comgate_substring(self):
        self.assertIn("false !== strpos( $id, 'comgate' )", self.fn)
        self.assertIn("return '%s';" % EN_CARD, self.fn)
        self.assertNotIn("'comgate' === strtolower", self.fn)

    def test_cod_and_bacs_titles(self):
        self.assertRegex(self.fn, r"if \( 'cod' === \$id \) \{\s*return 'Cash on delivery';")
        self.assertRegex(self.fn, r"if \( 'bacs' === \$id \) \{\s*return 'Bank transfer';")

    def test_unknown_gateway_still_uses_map(self):
        self.assertIn("return molosoc_en_shipping_payment_text( $title );", self.fn)

    def test_hook_registered_once(self):
        self.assertEqual(
            lang_src().count("add_filter( 'woocommerce_gateway_title', 'molosoc_en_gateway_title', 10, 2 );"), 1
        )


class EnMapTests(unittest.TestCase):
    def test_czech_cod_description_entry(self):
        self.assertEqual(translate("Zaplatíte při převzetí zásilky."), "Pay when you collect the parcel.")

    def test_cod_title_is_not_a_map_entry(self):
        # The EN title comes from the gateway-ID branch; the shared substring
        # map (also used for shipping labels) carries no title literal.
        self.assertNotIn("Dobírka", dict(en_map()))
        self.assertEqual(translate("Dobírka"), "Dobírka")

    def test_stored_english_cod_description_untouched(self):
        self.assertEqual(translate("Pay with cash upon delivery."), "Pay with cash upon delivery.")

    def test_earlier_entries_unchanged(self):
        pairs = dict(en_map())
        self.assertEqual(pairs["Comgate"], "Card payment (Comgate)")
        self.assertEqual(pairs["Bezpečná online platba kartou"], "Card payment (Comgate)")
        self.assertEqual(pairs["Bankovní převod"], "Bank transfer")
        self.assertEqual(translate("PPL výdejní místo"), "PPL pickup point")

    def test_map_does_not_touch_the_fee_name(self):
        # The fee line has its own function; the shared map must not shorten it.
        self.assertEqual(translate("Příplatek za dobírku"), "Příplatek za dobírku")


class FeeStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.name_fn = extract(lang_src(), "molosoc_en_cod_fee_name")
        cls.rename_fn = extract(lang_src(), "molosoc_en_cod_fee_rename")

    def test_known_names_map_to_english(self):
        self.assertIn("strcasecmp( $trimmed, 'COD fee' )", self.name_fn)
        self.assertIn("'Příplatek za dobírku' === $trimmed", self.name_fn)
        self.assertIn("return '%s';" % EN_FEE, self.name_fn)
        self.assertIn("return $name;", self.name_fn)

    def test_rename_is_en_only_and_name_only(self):
        self.assertIn("'en' !== pll_current_language()", self.rename_fn)
        for bad in ("add_fee", "remove", "->amount", "->total", "->tax", "set_fees"):
            self.assertNotIn(bad, self.rename_fn)

    def test_runs_after_every_plugin_fee(self):
        self.assertIn(
            "add_action( 'woocommerce_cart_calculate_fees', 'molosoc_en_cod_fee_rename', PHP_INT_MAX, 1 );",
            lang_src(),
        )


class ShortTitleStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fn = extract(lang_src(), "molosoc_order_short_payment_title")

    def test_comgate_only(self):
        self.assertIn("strpos( strtolower( (string) $order->get_payment_method() ), 'comgate' )", self.fn)

    def test_both_names(self):
        self.assertIn("'cz' === $lang ? '%s' : '%s'" % (CZ_SHORT, EN_SHORT), self.fn)

    def test_no_selling_line_on_the_record(self):
        for bad in ("příplatku", "no fee", "Comgate)"):
            self.assertNotIn(bad, self.fn)

    def test_runs_after_language_stamp(self):
        src = lang_src()
        self.assertIn("add_action( 'woocommerce_checkout_create_order', 'molosoc_save_order_lang', 10, 2 );", src)
        self.assertIn(
            "add_action( 'woocommerce_checkout_create_order', 'molosoc_order_short_payment_title', 20, 2 );", src
        )

    def test_only_the_new_order_is_written(self):
        for bad in ("wc_get_orders", "wc_get_order(", "update_option", "->save("):
            self.assertNotIn(bad, self.fn)


class CzCheckoutUntouchedTests(unittest.TestCase):
    def test_cz_card_label_and_other_methods(self):
        fn = extract(CLEANUP_PHP.read_text(encoding="utf-8"), "molosoc_cz_gateway_title")
        self.assertIn("return '%s';" % CZ_CARD, fn)
        self.assertIn("return 'Bankovní převod (platba předem)';", fn)
        self.assertNotIn("Dobírka", fn)

    def test_cz_cod_description_source_unchanged(self):
        self.assertIn("return 'Zaplatíte při převzetí zásilky.';", extract(lang_src(), "molosoc_cod_cz_text"))


@unittest.skipUnless(shutil.which("php"), "php CLI not available")
class PhpBehaviourTests(unittest.TestCase):
    def run_php(self, lang, calls):
        src = lang_src()
        funcs = "\n".join(extract(src, n) for n in FUNCS)
        code = "<?php\n"
        if lang is not None:
            code += "function pll_current_language() { return %s; }\n" % ("false" if lang == "" else "'%s'" % lang)
        code += PHP_STUBS + funcs + "\n" + calls
        with tempfile.NamedTemporaryFile("w", suffix=".php", delete=False, encoding="utf-8") as f:
            f.write(code)
        out = subprocess.run(["php", f.name], capture_output=True, text=True, check=True)
        Path(f.name).unlink()
        return out.stdout

    def title(self, lang, gid, title):
        return self.run_php(lang, "echo molosoc_en_gateway_title(%r, %r);" % (title, gid))

    def test_en_titles(self):
        self.assertEqual(self.title("en", "wf-woo-comgate", "Comgate"), EN_CARD)
        self.assertEqual(self.title("en", "comgate", "Comgate"), EN_CARD)
        self.assertEqual(self.title("en", "cod", "Dobírka"), "Cash on delivery")
        self.assertEqual(self.title("en", "bacs", "Bankovní převod"), "Bank transfer")
        self.assertEqual(self.title("en", "other", "X"), "X")

    def test_titles_untouched_outside_en(self):
        for lang in ("cz", "", None):
            self.assertEqual(self.title(lang, "wf-woo-comgate", "Comgate"), "Comgate")
            self.assertEqual(self.title(lang, "cod", "Dobírka"), "Dobírka")

    def test_en_cod_description(self):
        call = "echo molosoc_en_gateway_description(%r, 'cod');"
        self.assertEqual(self.run_php("en", call % "Pay with cash upon delivery."), "Pay with cash upon delivery.")
        self.assertEqual(self.run_php("en", call % "Zaplatíte při převzetí zásilky."), "Pay when you collect the parcel.")
        self.assertEqual(self.run_php("cz", call % "Zaplatíte při převzetí zásilky."), "Zaplatíte při převzetí zásilky.")

    def fees(self, lang, names):
        calls = (
            "$c = new Molosoc_Test_Cart(%s); molosoc_en_cod_fee_rename($c);"
            "echo json_encode(array_map(function($f){return array($f->name,$f->amount);}, $c->get_fees()));"
            % ("array(%s)" % ", ".join(repr(n) for n in names))
        )
        return json.loads(self.run_php(lang, calls))

    def test_fee_renamed_on_en_only(self):
        names = ["COD fee", "Příplatek za dobírku", "Gift wrap"]
        self.assertEqual(self.fees("en", names), [[EN_FEE, 29], [EN_FEE, 29], ["Gift wrap", 29]])
        for lang in ("cz", "", None):
            self.assertEqual(self.fees(lang, names), [[n, 29] for n in names])

    def test_fee_rename_survives_odd_input(self):
        self.assertEqual(self.run_php("en", "molosoc_en_cod_fee_rename(null); molosoc_en_cod_fee_rename(); echo 'ok';"), "ok")

    def stored(self, method, title, order_lang, request_lang="en"):
        calls = (
            "$o = new Molosoc_Test_Order(%r, %r, %r); molosoc_order_short_payment_title($o, array()); echo $o->title;"
            % (method, title, order_lang)
        )
        return self.run_php(request_lang, calls)

    def test_short_title_for_comgate_orders(self):
        self.assertEqual(self.stored("wf-woo-comgate", CZ_CARD, "cz"), CZ_SHORT)
        self.assertEqual(self.stored("wf-woo-comgate", EN_CARD, "en"), EN_SHORT)

    def test_short_title_follows_the_order_language_stamp(self):
        # The stamp wins over whatever language the request resolves to.
        self.assertEqual(self.stored("wf-woo-comgate", CZ_CARD, "cz", request_lang="en"), CZ_SHORT)
        # No stamp: fall back to the request language, then to English.
        self.assertEqual(self.stored("wf-woo-comgate", CZ_CARD, "", request_lang="cz"), CZ_SHORT)
        self.assertEqual(self.stored("wf-woo-comgate", EN_CARD, "", request_lang=""), EN_SHORT)
        self.assertEqual(self.stored("wf-woo-comgate", EN_CARD, "", request_lang=None), EN_SHORT)

    def test_other_gateways_keep_their_stored_title(self):
        self.assertEqual(self.stored("cod", "Dobírka", "cz"), "Dobírka")
        self.assertEqual(self.stored("cod", "Cash on delivery", "en"), "Cash on delivery")
        self.assertEqual(self.stored("bacs", "Bankovní převod (platba předem)", "cz"), "Bankovní převod (platba předem)")


if __name__ == "__main__":
    unittest.main()
