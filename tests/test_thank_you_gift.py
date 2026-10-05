"""Issue #106: bilingual Thank You page hero + post-purchase gift add-on."""
import json
import re
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

THEME = Path(__file__).resolve().parents[1] / "site/theme"
GIFT = THEME / "inc/thank-you-gift.php"
FUNCTIONS = THEME / "functions.php"

# Minimal WordPress/WooCommerce stand-ins. $GLOBALS['t'] holds the scenario.
STUBS = r"""<?php
define( 'ABSPATH', '/' );
define( 'MOLOSOC_PRODUCT_ID', 364 );
$GLOBALS['hooks'] = array();
$GLOBALS['added'] = array();
function add_action( $tag, $cb, $prio = 10, $args = 1 ) { $GLOBALS['hooks'][ $tag ] = $cb; }
function add_filter( $tag, $cb, $prio = 10, $args = 1 ) { $GLOBALS['hooks'][ $tag ] = $cb; }
function absint( $v ) { return abs( (int) $v ); }
function wp_unslash( $v ) { return $v; }
function wc_clean( $v ) { return $v; }
function sanitize_text_field( $v ) { return trim( (string) $v ); }
function esc_html( $v ) { return htmlspecialchars( (string) $v, ENT_QUOTES, 'UTF-8' ); }
function esc_attr( $v ) { return htmlspecialchars( (string) $v, ENT_QUOTES, 'UTF-8' ); }
function esc_url( $v ) { return $v; }
function wp_json_encode( $v ) { return json_encode( $v ); }
function wp_strip_all_tags( $v ) { return strip_tags( $v ); }
function wp_list_pluck( $list, $field ) { return array_map( function ( $i ) use ( $field ) { return $i[ $field ]; }, $list ); }
function checked( $a, $b ) { if ( (string) $a === (string) $b ) { echo " checked='checked'"; } }
function home_url( $path = '' ) { return 'https://example.test' . $path; }
function wc_nocache_headers() {}
function wp_safe_redirect( $url ) { echo "\nREDIRECT:" . $url . "\nADDED:" . json_encode( $GLOBALS['added'] ) . "\nCART:" . json_encode( WC()->cart->items ); }
function is_wc_endpoint_url( $e ) { return 'order-received' === $e && ! empty( $GLOBALS['t']['endpoint'] ); }
function pll_current_language() { return $GLOBALS['t']['request_lang']; }
function pll_get_post( $id, $lang ) { return 'cz' === $lang ? 900 : $id; }
function get_post_status( $id ) { return 'publish'; }
function get_permalink( $id ) { return 'https://example.test/cz/pokladna/'; }
function wc_get_page_id( $page ) { return 360; }
function wc_get_checkout_url() { return 'https://example.test/checkout/'; }
function molosoc_product_url( $lang = null ) { return 'https://example.test/product-' . $lang . '/'; }
function molosoc_size_label_for_value( $v, $f ) { return 'M' === $v ? 'M (36–39)' : 'L (39.5–44)'; }
function wc_price( $amount ) { return '<span class="amount">' . number_format( $amount, 0, ',', ' ' ) . '&nbsp;K&#269;</span>'; }
function wc_get_price_to_display( $p ) { return $p->price; }
class WC_Order {
	function get_id() { return 77; }
	function get_order_key() { return 'wc_order_abc'; }
	function get_meta( $k ) { return $GLOBALS['t']['order_lang']; }
	function has_status( $s ) { return in_array( $GLOBALS['t']['status'], (array) $s, true ); }
}
class WC_Product_Variation {
	public $id; public $price; public $stock;
	function __construct( $id, $price, $stock ) { $this->id = $id; $this->price = $price; $this->stock = $stock; }
	function get_id() { return $this->id; }
	function get_parent_id() { return 364; }
	function is_purchasable() { return true; }
	function is_in_stock() { return $this->stock; }
	function get_variation_attributes() { return array( 'attribute_size' => 425 === $this->id ? 'M' : 'L' ); }
}
function wc_get_order( $id ) { return 77 === (int) $id ? new WC_Order() : false; }
function wc_get_product( $id ) {
	$v = $GLOBALS['t']['variations'];
	return isset( $v[ $id ] ) ? new WC_Product_Variation( $id, $v[ $id ][0], $v[ $id ][1] ) : false;
}
class Molosoc_Test_Cart {
	public $items;
	function __construct() { $this->items = $GLOBALS['t']['cart']; }
	function generate_cart_id( $product_id, $variation_id, $attrs ) { return 'line' . $variation_id; }
	function find_product_in_cart( $id ) { return isset( $this->items[ $id ] ) ? $id : ''; }
	function get_cart_item( $key ) { return isset( $this->items[ $key ] ) ? array( 'quantity' => $this->items[ $key ] ) : array(); }
	function set_quantity( $key, $qty ) { $this->items[ $key ] = $qty; }
	function remove_cart_item( $key ) { unset( $this->items[ $key ] ); }
	function add_to_cart( $product_id, $qty, $variation_id, $attrs ) {
		if ( $variation_id === $GLOBALS['t']['fail_variation'] ) { return false; }
		$GLOBALS['added'][] = array( $product_id, $qty, $variation_id, $attrs );
		$key = 'line' . $variation_id;
		$this->items[ $key ] = ( isset( $this->items[ $key ] ) ? $this->items[ $key ] : 0 ) + $qty;
		return $key;
	}
}
class Molosoc_Test_WC { public $cart; function __construct() { $this->cart = new Molosoc_Test_Cart(); } }
function WC() { static $wc; if ( ! $wc ) { $wc = new Molosoc_Test_WC(); } return $wc; }
"""

DEFAULT = {
    "endpoint": True,
    "status": "processing",
    "order_lang": "cz",
    "request_lang": "cz",
    "variations": {"425": [229, True], "424": [229, True]},
    "cart": {},
    "fail_variation": 0,
}


def run_php(scenario, body, get=None, post=None):
    scenario = dict(DEFAULT, **scenario)
    script = (
        STUBS
        + "$GLOBALS['t'] = json_decode( %r, true );\n" % json.dumps(scenario)
        + "$_GET = json_decode( %r, true );\n" % json.dumps(get or {})
        + "$_POST = json_decode( %r, true );\n" % json.dumps(post or {})
        + "$GLOBALS['wp'] = (object) array( 'query_vars' => array( 'order-received' => 77 ) );\n"
        + "require %r;\n" % str(GIFT)
        + textwrap.dedent(body)
    )
    with tempfile.NamedTemporaryFile("w", suffix=".php", encoding="utf-8") as handle:
        handle.write(script)
        handle.flush()
        out = subprocess.run(["php", handle.name], capture_output=True, text=True, check=True)
    return out.stdout


KEY = {"key": "wc_order_abc"}
RENDER = "molosoc_thankyou_gift_section( 77 );"


class StaticContract(unittest.TestCase):
    def setUp(self):
        self.src = GIFT.read_text(encoding="utf-8")

    def test_never_touches_an_existing_order_or_payment(self):
        for forbidden in (
            "add_product(", "update_status(", "payment_complete(", "set_total(",
            "calculate_totals(", "update_meta_data(", "->save(", "wc_create_order(",
            "process_payment(", "empty_cart(",
        ):
            self.assertNotIn(forbidden, self.src)

    def test_no_hard_coded_price_or_discount_wording(self):
        self.assertIsNone(re.search(r"\b(229|199|10)\s*(Kč|CZK|€)|&euro;", self.src))
        for word in ("discount", "sleva", "bundle", "Save ", "Ušetř"):
            self.assertNotIn(word, self.src)

    def test_requested_copy_is_verbatim(self):
        for text in (
            "Děkujeme za vaši objednávku.",
            "Thank you for your order.",
            "Ještě jedny pro někoho, koho máte rádi?",
            "One more for someone you love?",
            "MOLOSOC vznikl mezi mámou a dcerou. Pokud už máte jedny pro sebe, můžete přidat další pro mámu, partnera nebo kamarádku — protože popraskané paty opravdu nemusí být dárek, se kterým člověk žije.",
            "MOLOSOC started with a mom and daughter. If you already have yours, add another for your mom, partner or friend — because crusty, cracked feet don\\'t have to be something they simply live with.",
            "Přidat k objednávce",
            "Add to my order",
            "https://molosoc.com/wp-content/uploads/2026/01/Molosoc-Opening-Package-Mami.jpg",
        ):
            self.assertIn(text, self.src)

    def test_wired_into_theme_on_order_received_only(self):
        functions = FUNCTIONS.read_text(encoding="utf-8")
        self.assertLess(
            functions.index("/inc/woocommerce-lang.php'"),
            functions.index("/inc/thank-you-gift.php'"),
        )
        block = functions[functions.index("is_wc_endpoint_url( 'order-received' ) ) {"):]
        block = block[: block.index("}")]
        self.assertIn("/assets/css/thank-you.css", block)
        self.assertIn("/assets/js/thank-you-gift.js", block)
        self.assertEqual(functions.count("thank-you.css"), 1)
        self.assertEqual(functions.count("thank-you-gift.js"), 1)
        self.assertTrue((THEME / "assets/css/thank-you.css").is_file())
        self.assertTrue((THEME / "assets/js/thank-you-gift.js").is_file())


@unittest.skipUnless(shutil.which("php"), "php not installed")
class Rendering(unittest.TestCase):
    def test_czech_order_gets_czech_section_with_live_totals(self):
        out = run_php({"variations": {"425": [229, True], "424": [249, True]}}, RENDER, get=KEY)
        self.assertIn('lang="cs"', out)
        self.assertIn("Ještě jedny pro někoho, koho máte rádi?", out)
        self.assertIn("Přidat k objednávce", out)
        self.assertIn("samostatnou objednávku", out)
        self.assertIn('action="https://example.test/cz/"', out)
        totals = json.loads(
            re.search(r'data-totals="([^"]+)"', out).group(1).replace("&quot;", '"')
        )
        self.assertEqual(len(totals), 9)
        self.assertEqual(totals["1-0"], "229 Kč")
        self.assertEqual(totals["0-1"], "249 Kč")
        self.assertEqual(totals["2-1"], "707 Kč")
        self.assertNotIn("3-1", totals)
        # Sizes cost different amounts, so no card can state a total up front.
        self.assertNotIn("molosoc-gift-card__price", out)
        self.assertEqual(out.count('name="molosoc_gift_pairs"'), 3)
        self.assertEqual(out.count("M (36–39)"), 3)
        self.assertEqual(out.count("L (39.5–44)"), 3)

    def test_english_order_gets_english_section_even_on_a_czech_request(self):
        out = run_php({"order_lang": "en"}, RENDER, get=KEY)
        self.assertIn('lang="en"', out)
        self.assertIn("One more for someone you love?", out)
        self.assertIn("Add to my order", out)
        self.assertIn("separate order", out)
        self.assertIn('action="https://example.test/"', out)
        self.assertIn("+ 1 pair<", out)
        self.assertIn("+ 3 pairs<", out)
        # Same price for both sizes: each card shows count x live price.
        self.assertEqual(
            re.findall(r'molosoc-gift-card__price" translate="no">([^<]+)<', out),
            ["229&nbsp;Kč".replace("&nbsp;", " "), "458 Kč", "687 Kč"],
        )

    def test_hero_and_confirmation_text_follow_the_order_language(self):
        body = """
        echo call_user_func( $GLOBALS['hooks']['woocommerce_endpoint_order-received_title'], 'Order received' ), '|';
        echo molosoc_thankyou_received_text( 'Thank you. Your order has been received.', new WC_Order() );
        """
        self.assertEqual(run_php({}, body, get=KEY), "Děkujeme za vaši objednávku.|Vaši objednávku jsme přijali.")
        self.assertEqual(
            run_php({"order_lang": "en"}, body, get=KEY),
            "Thank you for your order.|Your order has been received.",
        )
        # No saved order language: fall back to the request's language.
        self.assertTrue(
            run_php({"order_lang": "", "request_lang": "en"}, body, get=KEY).startswith("Thank you for your order.")
        )

    def test_nothing_changes_without_a_successful_order_the_visitor_holds(self):
        body = RENDER + """
        echo call_user_func( $GLOBALS['hooks']['woocommerce_endpoint_order-received_title'], 'Order received' );
        """
        for scenario, get in (
            ({"status": "failed"}, KEY),
            ({"status": "pending"}, KEY),
            ({"status": "cancelled"}, KEY),
            ({}, {"key": "wc_order_wrong"}),
            ({}, {}),
            ({"endpoint": False}, KEY),
        ):
            self.assertEqual(run_php(scenario, body, get=get), "Order received")

    def test_out_of_stock_size_is_not_offered_and_no_stock_hides_the_section(self):
        out = run_php({"variations": {"425": [229, True], "424": [229, False]}}, RENDER, get=KEY)
        self.assertIn("M (36–39)", out)
        self.assertNotIn("L (39.5–44)", out)
        self.assertEqual(run_php({"variations": {"425": [229, False], "424": [229, False]}}, RENDER, get=KEY), "")
        self.assertEqual(run_php({"variations": {}}, RENDER, get=KEY), "")


@unittest.skipUnless(shutil.which("php"), "php not installed")
class AddToCartHandler(unittest.TestCase):
    BODY = "molosoc_gift_add_to_cart_action(); echo 'NOOP';"

    def submit(self, post, scenario=None):
        out = run_php(scenario or {}, self.BODY, post=post)
        if "REDIRECT:" not in out:
            return out, None
        redirect = re.search(r"REDIRECT:(\S+)", out).group(1)
        added = json.loads(re.search(r"ADDED:(.*)", out).group(1))
        return redirect, added

    def test_ignores_requests_that_are_not_the_gift_form(self):
        self.assertEqual(self.submit({}), ("NOOP", None))

    def test_adds_each_size_as_its_own_variation_then_goes_to_czech_checkout(self):
        redirect, added = self.submit(
            {"molosoc_gift_pairs": "3", "molosoc_gift_lang": "cz", "molosoc_gift_size": ["M", "L", "M"]}
        )
        self.assertEqual(redirect, "https://example.test/cz/pokladna/")
        self.assertEqual(
            added,
            [[364, 2, 425, {"attribute_size": "M"}], [364, 1, 424, {"attribute_size": "L"}]],
        )

    def test_english_form_goes_to_the_english_checkout(self):
        redirect, added = self.submit(
            {"molosoc_gift_pairs": "1", "molosoc_gift_lang": "en", "molosoc_gift_size": ["L"]},
            {"request_lang": "en"},
        )
        self.assertEqual(redirect, "https://example.test/checkout/")
        self.assertEqual(added, [[364, 1, 424, {"attribute_size": "L"}]])

    def test_partly_failed_selection_is_rolled_back_and_never_reaches_checkout(self):
        post = {"molosoc_gift_pairs": "3", "molosoc_gift_lang": "cz", "molosoc_gift_size": ["M", "M", "L"]}
        # L can't be added after M already was: M's addition is undone.
        out = run_php({"fail_variation": 424}, self.BODY, post=post)
        self.assertIn("REDIRECT:https://example.test/product-cz/", out)
        self.assertEqual(json.loads(re.search(r"CART:(.*)", out).group(1)), [])
        # A line that was in the cart before keeps its earlier quantity.
        out = run_php({"fail_variation": 424, "cart": {"line425": 1}}, self.BODY, post=post)
        self.assertIn("REDIRECT:https://example.test/product-cz/", out)
        self.assertEqual(json.loads(re.search(r"CART:(.*)", out).group(1)), {"line425": 1})
        # The first size failing leaves the cart untouched too.
        out = run_php({"fail_variation": 425, "cart": {"line424": 2}}, self.BODY, post=post)
        self.assertIn("REDIRECT:https://example.test/product-cz/", out)
        self.assertEqual(json.loads(re.search(r"CART:(.*)", out).group(1)), {"line424": 2})

    def test_never_more_than_three_pairs(self):
        _, added = self.submit(
            {"molosoc_gift_pairs": "50", "molosoc_gift_lang": "en", "molosoc_gift_size": ["M"] * 50}
        )
        self.assertEqual(added, [[364, 3, 425, {"attribute_size": "M"}]])

    def test_only_the_chosen_number_of_pairs_is_added(self):
        _, added = self.submit(
            {"molosoc_gift_pairs": "1", "molosoc_gift_lang": "en", "molosoc_gift_size": ["M", "L", "L"]}
        )
        self.assertEqual(added, [[364, 1, 425, {"attribute_size": "M"}]])

    def test_missing_invalid_or_unavailable_size_adds_nothing(self):
        for post, scenario in (
            ({"molosoc_gift_pairs": "2", "molosoc_gift_lang": "cz", "molosoc_gift_size": ["M"]}, {}),
            ({"molosoc_gift_pairs": "1", "molosoc_gift_lang": "cz", "molosoc_gift_size": ["XL"]}, {}),
            ({"molosoc_gift_pairs": "1", "molosoc_gift_lang": "cz"}, {}),
            ({"molosoc_gift_pairs": "1", "molosoc_gift_lang": "cz", "molosoc_gift_size": "M"}, {}),
            (
                {"molosoc_gift_pairs": "1", "molosoc_gift_lang": "cz", "molosoc_gift_size": ["L"]},
                {"variations": {"425": [229, True], "424": [229, False]}},
            ),
        ):
            redirect, added = self.submit(post, scenario)
            self.assertEqual(redirect, "https://example.test/product-cz/")
            self.assertEqual(added, [])


if __name__ == "__main__":
    unittest.main()
