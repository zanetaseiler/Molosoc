"""Issues #106/#108: bilingual Thank You page hero + post-purchase gift add-on
that ships together with the original order."""
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
# Order 77 is the original order; order 88 is a gift add-on order that
# points at it (via meta) when the scenario says so.
STUBS = r"""<?php
define( 'ABSPATH', '/' );
define( 'MOLOSOC_PRODUCT_ID', 364 );
define( 'HOUR_IN_SECONDS', 3600 );
$GLOBALS['hooks'] = array();
$GLOBALS['added'] = array();
$GLOBALS['notes'] = array();
$GLOBALS['session'] = $GLOBALS['t']['session'];
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
function wp_safe_redirect( $url ) { echo "\nREDIRECT:" . $url . "\nADDED:" . json_encode( $GLOBALS['added'] ) . "\nCART:" . json_encode( WC()->cart->items ) . "\nSESSION:" . json_encode( $GLOBALS['session'] ) . "\nCUSTOMER:" . json_encode( WC()->customer->props ); }
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
class Molosoc_Test_Date { public $ts; function __construct( $ts ) { $this->ts = $ts; } function getTimestamp() { return $this->ts; } }
class WC_Order_Item { public $qty; function __construct( $q ) { $this->qty = $q; } function get_quantity() { return $this->qty; } }
class WC_Order {
	public $id; public $meta = array(); public $saved = 0;
	function __construct( $id ) { $this->id = $id; $this->meta = isset( $GLOBALS['t']['meta'][ $id ] ) ? $GLOBALS['t']['meta'][ $id ] : array(); }
	function get_id() { return $this->id; }
	function get_order_number() { return (string) $this->id; }
	function get_order_key() { return 'wc_order_key' . $this->id; }
	function get_meta( $k ) { if ( '_molosoc_lang' === $k ) { return $GLOBALS['t']['order_lang']; } return isset( $this->meta[ $k ] ) ? $this->meta[ $k ] : ''; }
	function update_meta_data( $k, $v ) { $this->meta[ $k ] = $v; }
	function save() { $this->saved++; $GLOBALS['t']['meta'][ $this->id ] = $this->meta; }
	function has_status( $s ) { return in_array( $GLOBALS['t']['status'][ $this->id ], (array) $s, true ); }
	function get_date_created() { return new Molosoc_Test_Date( time() - $GLOBALS['t']['age'][ $this->id ] ); }
	function get_address( $type ) { return 'billing' === $type ? array( 'first_name' => 'Jana', 'email' => $GLOBALS['t']['email'], 'phone' => '' ) : array( 'first_name' => 'Jana', 'city' => 'Praha' ); }
	function get_items() { return array( new WC_Order_Item( 2 ), new WC_Order_Item( 1 ) ); }
	function add_order_note( $n ) { $GLOBALS['notes'][] = array( $this->id, $n ); }
	function get_edit_order_url() { return 'https://example.test/wp-admin/order/' . $this->id; }
}
$GLOBALS['orders'] = array();
function wc_get_order( $id ) {
	if ( ! in_array( (int) $id, array( 77, 88 ), true ) ) { return false; }
	if ( ! isset( $GLOBALS['orders'][ $id ] ) ) { $GLOBALS['orders'][ $id ] = new WC_Order( (int) $id ); }
	return $GLOBALS['orders'][ $id ];
}
function wc_get_orders( $args ) {
	$parent = null; $need_noted = false;
	foreach ( $args['meta_query'] as $q ) {
		if ( '_molosoc_gift_parent_order' === $q['key'] ) { $parent = (int) $q['value']; }
		if ( '_molosoc_gift_parent_order_noted' === $q['key'] ) { $need_noted = true; }
	}
	$ids = array();
	foreach ( $GLOBALS['t']['meta'] as $id => $meta ) {
		if ( isset( $meta['_molosoc_gift_parent_order'] ) && (int) $meta['_molosoc_gift_parent_order'] === $parent && ( ! $need_noted || isset( $meta['_molosoc_gift_parent_order_noted'] ) ) ) { $ids[] = (int) $id; }
	}
	return $ids;
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
function wc_get_product( $id ) {
	$v = $GLOBALS['t']['variations'];
	return isset( $v[ $id ] ) ? new WC_Product_Variation( $id, $v[ $id ][0], $v[ $id ][1] ) : false;
}
class WC_Shipping_Rate {
	public $args;
	function __construct( ...$args ) { $this->args = $args; }
}
class Molosoc_Test_Cart {
	public $items;
	function __construct() { $this->items = $GLOBALS['t']['cart']; }
	function generate_cart_id( $product_id, $variation_id, $attrs ) { return 'line' . $variation_id; }
	function find_product_in_cart( $id ) { return isset( $this->items[ $id ] ) ? $id : ''; }
	function get_cart_item( $key ) { return isset( $this->items[ $key ] ) ? array( 'quantity' => $this->items[ $key ] ) : array(); }
	function set_quantity( $key, $qty ) { $this->items[ $key ] = $qty; }
	function remove_cart_item( $key ) { unset( $this->items[ $key ] ); }
	function get_cart() {
		$out = array();
		foreach ( $this->items as $key => $qty ) { $out[ $key ] = array( 'product_id' => 'lineX' === $key ? 999 : 364, 'quantity' => $qty ); }
		return $out;
	}
	function add_to_cart( $product_id, $qty, $variation_id, $attrs ) {
		if ( $variation_id === $GLOBALS['t']['fail_variation'] ) { return false; }
		$GLOBALS['added'][] = array( $product_id, $qty, $variation_id, $attrs );
		$key = 'line' . $variation_id;
		$this->items[ $key ] = ( isset( $this->items[ $key ] ) ? $this->items[ $key ] : 0 ) + $qty;
		return $key;
	}
}
class Molosoc_Test_Session {
	function get( $k ) { return isset( $GLOBALS['session'][ $k ] ) ? $GLOBALS['session'][ $k ] : null; }
	function set( $k, $v ) { if ( null === $v ) { unset( $GLOBALS['session'][ $k ] ); } else { $GLOBALS['session'][ $k ] = $v; } }
}
class Molosoc_Test_Customer {
	// Real WC_Customer has one concrete setter per address field; the file
	// checks method_exists() before calling, so these must be real methods.
	public $props = array(); public $saved = 0;
	function set_billing_first_name( $v ) { $this->props['billing_first_name'] = $v; }
	function set_billing_email( $v ) { if ( 'bad' === $v ) { throw new Exception( 'invalid' ); } $this->props['billing_email'] = $v; }
	function set_billing_phone( $v ) { $this->props['billing_phone'] = $v; }
	function set_shipping_first_name( $v ) { $this->props['shipping_first_name'] = $v; }
	function set_shipping_city( $v ) { $this->props['shipping_city'] = $v; }
	function save() { $this->saved++; $this->props['saved'] = $this->saved; }
}
class Molosoc_Test_WC {
	public $cart; public $session; public $customer;
	function __construct() { $this->cart = new Molosoc_Test_Cart(); $this->session = new Molosoc_Test_Session(); $this->customer = new Molosoc_Test_Customer(); }
}
function WC() { static $wc; if ( ! $wc ) { $wc = new Molosoc_Test_WC(); } return $wc; }
"""

DEFAULT = {
    "endpoint": True,
    "status": {"77": "processing", "88": "processing"},
    "age": {"77": 600, "88": 60},
    "meta": {"77": {}, "88": {}},
    "order_lang": "cz",
    "request_lang": "cz",
    "variations": {"425": [229, True], "424": [229, True]},
    "cart": {},
    "fail_variation": 0,
    "session": {},
    "email": "jana@example.test",
}

LINK = {"order_id": 77, "key": "wc_order_key77", "lang": "cz", "time": 0, "lines": {"line425": 2}}


def scenario_with(scenario):
    merged = dict(DEFAULT)
    for key, value in scenario.items():
        if isinstance(value, dict) and isinstance(DEFAULT.get(key), dict) and key not in ("variations", "cart", "session"):
            merged[key] = dict(DEFAULT[key], **value)
        else:
            merged[key] = value
    return merged


def run_php(scenario, body, get=None, post=None):
    scenario = scenario_with(scenario)
    script = (
        STUBS.replace("<?php\n", "<?php\n$GLOBALS['t'] = json_decode( %r, true );\n" % json.dumps(scenario), 1)
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


KEY = {"key": "wc_order_key77"}
RENDER = "molosoc_thankyou_gift_section( 77 );"
FORM = {"molosoc_gift_pairs": "1", "molosoc_gift_lang": "cz", "molosoc_gift_size": ["M"],
        "molosoc_gift_order": "77", "molosoc_gift_key": "wc_order_key77"}


def section(out, name):
    value = json.loads(re.search(name + r":(.*)", out).group(1))
    return {} if value == [] else value  # an empty PHP array encodes as []


class StaticContract(unittest.TestCase):
    def setUp(self):
        self.src = GIFT.read_text(encoding="utf-8")

    def test_the_original_order_is_only_ever_read_or_annotated(self):
        # $parent is the original order everywhere in the file: the only
        # method that writes anything to it is add_order_note().
        calls = set(re.findall(r"\$parent->(\w+)\(", self.src))
        self.assertTrue(calls)
        self.assertLessEqual(
            calls,
            {"get_id", "get_order_key", "get_order_number", "get_address", "get_edit_order_url", "add_order_note"},
            calls,
        )
        for forbidden in ("add_product(", "update_status(", "payment_complete(", "set_total(",
                          "calculate_totals(", "wc_create_order(", "process_payment(", "empty_cart("):
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
            "MOLOSOC vznikl mezi mámou a dcerou. Pokud už máte jedny pro sebe, přidejte další pro maminku, partnera nebo kamarádku — malý dárek, který jim pomůže pečovat o nohy stejně jednoduše.",
            "MOLOSOC started with a mom and daughter. If you already have yours, add one for your mom, partner or friend — a small gift that helps them take better care of their feet, too.",
            "Ships with your original order — no additional shipping.",
            "Pošleme s vaší původní objednávkou — bez dalšího poštovného.",
            "Add gift pairs",
            "Přidat dárkové páry",
            "We’ll pack them with the order you just placed, so you won’t pay shipping again.",
            "Přibalíme je k objednávce, kterou jste právě vytvořili, takže další dopravu neplatíte.",
            "https://molosoc.com/wp-content/uploads/2026/01/Molosoc-Opening-Package-Mami.jpg",
        ):
            self.assertIn(text, self.src)
        for gone in ("crusty", "Add to my order", "Přidat k objednávce", "+ shipping", "+ doprava",
                     "own payment and shipping", "vlastní platbou a dopravou"):
            self.assertNotIn(gone, self.src)

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
        self.assertIn("Přidat dárkové páry", out)
        self.assertIn("bez dalšího poštovného", out)
        self.assertIn('action="https://example.test/cz/"', out)
        self.assertIn('name="molosoc_gift_order" value="77"', out)
        self.assertIn('name="molosoc_gift_key" value="wc_order_key77"', out)
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
        self.assertIn("Add gift pairs", out)
        self.assertIn("no additional shipping", out)
        self.assertIn('action="https://example.test/"', out)
        self.assertIn("+ 1 pair<", out)
        self.assertIn("+ 3 pairs<", out)
        # Same price for both sizes: each card shows count x live price.
        self.assertEqual(
            re.findall(r'molosoc-gift-card__price" translate="no">([^<]+)<', out),
            ["229 Kč", "458 Kč", "687 Kč"],
        )

    def test_hero_and_confirmation_text_follow_the_order_language(self):
        body = """
        echo call_user_func( $GLOBALS['hooks']['woocommerce_endpoint_order-received_title'], 'Order received' ), '|';
        echo molosoc_thankyou_received_text( 'Thank you. Your order has been received.', wc_get_order( 77 ) );
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

    def test_gift_order_thank_you_names_the_order_it_ships_with(self):
        body = "echo molosoc_thankyou_received_text( 'x', wc_get_order( 77 ) );"
        linked = {"meta": {"77": {"_molosoc_gift_parent_order": 88}}}
        self.assertEqual(run_php(linked, body, get=KEY), "Vaši objednávku jsme přijali. Pošleme ji společně s objednávkou č. 88.")
        self.assertEqual(
            run_php(dict(linked, order_lang="en"), body, get=KEY),
            "Your order has been received. It ships together with order #88.",
        )

    def test_nothing_changes_without_a_successful_order_the_visitor_holds(self):
        body = RENDER + """
        echo call_user_func( $GLOBALS['hooks']['woocommerce_endpoint_order-received_title'], 'Order received' );
        """
        for scenario, get in (
            ({"status": {"77": "failed"}}, KEY),
            ({"status": {"77": "pending"}}, KEY),
            ({"status": {"77": "cancelled"}}, KEY),
            ({}, {"key": "wc_order_wrong"}),
            ({}, {}),
            ({"endpoint": False}, KEY),
        ):
            self.assertEqual(run_php(scenario, body, get=get), "Order received")

    def test_offer_hidden_once_the_order_can_no_longer_ship_together(self):
        body = RENDER + "echo '|', call_user_func( $GLOBALS['hooks']['woocommerce_endpoint_order-received_title'], 'Order received' );"
        for scenario in (
            {"status": {"77": "completed"}},            # already dispatched
            {"age": {"77": 24 * 3600 + 1}},             # outside the window
            {"meta": {"77": {"_molosoc_gift_parent_order": 88}}},  # itself a gift add-on
        ):
            out = run_php(scenario, body, get=KEY)
            self.assertNotIn("molosoc-gift", out, scenario)
            self.assertTrue(out.endswith("|Děkujeme za vaši objednávku."), scenario)  # hero still shows
        self.assertIn("molosoc-gift", run_php({"age": {"77": 24 * 3600 - 60}}, RENDER, get=KEY))
        self.assertIn("molosoc-gift", run_php({"status": {"77": "on-hold"}}, RENDER, get=KEY))

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
            return out, None, None
        redirect = re.search(r"REDIRECT:(\S+)", out).group(1)
        return redirect, section(out, "ADDED"), out

    def test_ignores_requests_that_are_not_the_gift_form(self):
        self.assertEqual(self.submit({})[0], "NOOP")

    def test_adds_each_size_links_the_cart_and_prefills_checkout(self):
        redirect, added, out = self.submit(
            dict(FORM, molosoc_gift_pairs="3", molosoc_gift_size=["M", "L", "M"])
        )
        self.assertEqual(redirect, "https://example.test/cz/pokladna/")
        self.assertEqual(
            added,
            [[364, 2, 425, {"attribute_size": "M"}], [364, 1, 424, {"attribute_size": "L"}]],
        )
        link = section(out, "SESSION")["molosoc_gift_parent"]
        self.assertEqual((link["order_id"], link["key"], link["lang"]), (77, "wc_order_key77", "cz"))
        customer = section(out, "CUSTOMER")
        self.assertEqual(customer["billing_first_name"], "Jana")
        self.assertEqual(customer["billing_email"], "jana@example.test")
        self.assertEqual(customer["shipping_city"], "Praha")
        self.assertNotIn("billing_phone", customer)  # empty values are not copied
        self.assertEqual(customer["saved"], 1)

    def test_preloaded_or_repeated_rows_never_ride_the_free_rate(self):
        # A pre-loaded quantity of the same size and an unrelated line are
        # reset to exactly what this form submitted, and the link records it.
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        _, _, out = self.submit(post, {"cart": {"line425": 3, "line999": 2}})
        self.assertEqual(section(out, "CART"), {"line425": 1, "line424": 1})
        link = section(out, "SESSION")["molosoc_gift_parent"]
        self.assertEqual(link["lines"], {"line425": 1, "line424": 1})

    def test_english_form_goes_to_the_english_checkout(self):
        redirect, added, _ = self.submit(
            dict(FORM, molosoc_gift_lang="en", molosoc_gift_size=["L"]), {"request_lang": "en"}
        )
        self.assertEqual(redirect, "https://example.test/checkout/")
        self.assertEqual(added, [[364, 1, 424, {"attribute_size": "L"}]])

    def test_form_for_an_order_that_cannot_ship_together_adds_nothing(self):
        for post, scenario in (
            (dict(FORM, molosoc_gift_key="wc_order_wrong"), {}),
            (dict(FORM, molosoc_gift_order="12"), {}),
            ({k: v for k, v in FORM.items() if k not in ("molosoc_gift_order", "molosoc_gift_key")}, {}),
            (FORM, {"status": {"77": "completed"}}),
            (FORM, {"status": {"77": "pending"}}),
            (FORM, {"age": {"77": 30 * 3600}}),
            (FORM, {"meta": {"77": {"_molosoc_gift_parent_order": 88}}}),
        ):
            redirect, added, out = self.submit(post, scenario)
            self.assertEqual(redirect, "https://example.test/product-cz/", (post, scenario))
            self.assertEqual(added, {})
            self.assertEqual(section(out, "SESSION"), {})

    def test_partly_failed_selection_is_rolled_back_and_never_reaches_checkout(self):
        post = dict(FORM, molosoc_gift_pairs="3", molosoc_gift_size=["M", "M", "L"])
        # L can't be added after M already was: M's addition is undone.
        _, _, out = self.submit(post, {"fail_variation": 424})
        self.assertIn("REDIRECT:https://example.test/product-cz/", out)
        self.assertEqual(section(out, "CART"), {})
        self.assertEqual(section(out, "SESSION"), {})
        # A line that was in the cart before keeps its earlier quantity.
        _, _, out = self.submit(post, {"fail_variation": 424, "cart": {"line425": 1}})
        self.assertEqual(section(out, "CART"), {"line425": 1})
        # The first size failing leaves the cart untouched too.
        _, _, out = self.submit(post, {"fail_variation": 425, "cart": {"line424": 2}})
        self.assertEqual(section(out, "CART"), {"line424": 2})

    def test_never_more_than_three_pairs(self):
        _, added, _ = self.submit(dict(FORM, molosoc_gift_pairs="50", molosoc_gift_size=["M"] * 50))
        self.assertEqual(added, [[364, 3, 425, {"attribute_size": "M"}]])

    def test_only_the_chosen_number_of_pairs_is_added(self):
        _, added, _ = self.submit(dict(FORM, molosoc_gift_size=["M", "L", "L"]))
        self.assertEqual(added, [[364, 1, 425, {"attribute_size": "M"}]])

    def test_missing_invalid_or_unavailable_size_adds_nothing(self):
        for post, scenario in (
            (dict(FORM, molosoc_gift_pairs="2"), {}),
            (dict(FORM, molosoc_gift_size=["XL"]), {}),
            ({k: v for k, v in FORM.items() if k != "molosoc_gift_size"}, {}),
            (dict(FORM, molosoc_gift_size="M"), {}),
            (dict(FORM, molosoc_gift_size=["L"]), {"variations": {"425": [229, True], "424": [229, False]}}),
        ):
            redirect, added, _ = self.submit(post, scenario)
            self.assertEqual(redirect, "https://example.test/product-cz/")
            self.assertEqual(added, {})

    def test_an_address_value_the_customer_object_rejects_is_skipped(self):
        _, _, out = self.submit(FORM, {"email": "bad"})
        customer = section(out, "CUSTOMER")
        self.assertNotIn("billing_email", customer)
        self.assertEqual(customer["billing_first_name"], "Jana")
        self.assertEqual(customer["shipping_city"], "Praha")


@unittest.skipUnless(shutil.which("php"), "php not installed")
class LinkedCheckout(unittest.TestCase):
    RATES = """
    $rates = array( 'flat_rate:1' => 'normal', 'zasilkovna' => 'pickup' );
    $out = molosoc_gift_shipping_rates( $rates, array() );
    echo json_encode( array_map( function ( $r ) { return $r instanceof WC_Shipping_Rate ? $r->args : $r; }, $out ) );
    """

    def test_linked_cart_gets_one_free_ships_with_rate(self):
        out = run_php({"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 2}}, self.RATES)
        self.assertEqual(
            json.loads(out),
            {"molosoc_gift_combined": ["molosoc_gift_combined", "Pošleme s objednávkou č. 77 — bez dalšího poštovného", 0, [], "molosoc_gift_combined", 0]},
        )
        out = run_php({"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 2}, "request_lang": "en"}, self.RATES)
        self.assertEqual(json.loads(out)["molosoc_gift_combined"][1], "Ships with order #77 — no additional shipping")

    def test_normal_rates_stay_whenever_the_link_is_not_valid(self):
        normal = {"flat_rate:1": "normal", "zasilkovna": "pickup"}
        for scenario in (
            {"cart": {"line425": 1}},                                                 # no link at all
            {"session": {"molosoc_gift_parent": dict(LINK, key="stale")}, "cart": {"line425": 1}},
            {"session": {"molosoc_gift_parent": LINK}, "cart": {}},                   # empty cart
            {"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 1, "lineX": 1}},  # another product
            {"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 1}},       # quantity changed
            {"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 5}},       # more than was added
            {"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 2, "line424": 1}},  # extra pre-loaded row
            {"session": {"molosoc_gift_parent": {k: v for k, v in LINK.items() if k != "lines"}}, "cart": {"line425": 2}},
            {"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 2}, "status": {"77": "completed"}},
            {"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 2}, "age": {"77": 48 * 3600}},
        ):
            self.assertEqual(json.loads(run_php(scenario, self.RATES)), normal, scenario)

    def test_new_order_is_stamped_and_noted_on_both_sides_once_paid(self):
        body = """
        $new = wc_get_order( 88 );
        molosoc_gift_stamp_new_order( $new );
        $created = array( 'notes' => count( $GLOBALS['notes'] ), 'session' => $GLOBALS['session'] );
        molosoc_gift_note_orders_by_id( 88 );
        molosoc_gift_note_orders_by_id( 88 ); // several payment hooks fire for one order: note once
        echo json_encode( array( 'created' => $created, 'meta' => $new->meta, 'saved' => $new->saved, 'notes' => $GLOBALS['notes'], 'session' => $GLOBALS['session'], 'parent_saved' => wc_get_order( 77 )->saved ) );
        """
        out = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 2}}, body))
        # Nothing is noted and the link survives until payment is confirmed.
        self.assertEqual(out["created"]["notes"], 0)
        self.assertEqual(out["created"]["session"]["molosoc_gift_parent"]["order_id"], 77)
        self.assertEqual(out["meta"]["_molosoc_gift_parent_order"], 77)
        self.assertEqual(out["meta"]["_molosoc_gift_parent_order_noted"], "yes")
        self.assertEqual(out["saved"], 1)
        self.assertEqual(out["parent_saved"], 0)
        self.assertEqual([n[0] for n in out["notes"]], [88, 77])
        self.assertIn("Gift add-on to order #77", out["notes"][0][1])
        self.assertIn("shipping 0", out["notes"][0][1])
        self.assertIn("Gift add-on: order #88 (3 pairs)", out["notes"][1][1])
        # The gateway callback may not hold the shopper's session: untouched here.
        self.assertEqual(out["session"]["molosoc_gift_parent"]["order_id"], 77)

    def test_notes_wait_for_confirmed_payment(self):
        body = """
        echo json_encode( array_keys( $GLOBALS['hooks'] ) );
        """
        hooks = json.loads(run_php({}, body))
        for tag in ("woocommerce_payment_complete", "woocommerce_order_status_processing"):
            self.assertIn(tag, hooks)
        # on-hold means awaiting payment: it must never trigger the notes.
        for tag in ("woocommerce_order_status_on-hold", "woocommerce_checkout_order_created", "woocommerce_store_api_checkout_order_processed"):
            self.assertNotIn(tag, hooks)

    def test_payment_after_the_original_order_became_ineligible_goes_to_manual_handling(self):
        body = """
        $new = wc_get_order( 88 );
        molosoc_gift_note_orders_by_id( 88 );
        molosoc_gift_note_orders_by_id( 88 );
        echo json_encode( array( 'meta' => $new->meta, 'notes' => $GLOBALS['notes'] ) );
        """
        for scenario in ({"status": {"77": "completed"}}, {"age": {"77": 48 * 3600}}):
            scenario = dict(scenario, meta={"88": {"_molosoc_gift_parent_order": 77}})
            out = json.loads(run_php(scenario, body))
            self.assertEqual(out["meta"]["_molosoc_gift_parent_order_noted"], "manual", scenario)
            self.assertEqual([n[0] for n in out["notes"]], [88], scenario)  # nothing written to the original
            self.assertIn("handle manually", out["notes"][0][1])

    def test_a_confirmed_addon_makes_any_stale_session_link_worthless(self):
        # The link in the browser session survives (a gateway callback cannot
        # clear it), but the order-backed flag stops it granting free shipping again.
        scenario = {"session": {"molosoc_gift_parent": LINK}, "cart": {"line425": 2},
                    "meta": {"88": {"_molosoc_gift_parent_order": 77, "_molosoc_gift_parent_order_noted": "yes"}}}
        normal = {"flat_rate:1": "normal", "zasilkovna": "pickup"}
        self.assertEqual(json.loads(run_php(scenario, self.RATES)), normal)
        self.assertNotIn("molosoc-gift", run_php(scenario, RENDER, get=KEY))
        # An add-on that was only created (not yet confirmed) does not block a retry.
        scenario["meta"] = {"88": {"_molosoc_gift_parent_order": 77}}
        self.assertIn("molosoc_gift_combined", json.loads(run_php(scenario, self.RATES)))

    def test_gift_orders_own_thank_you_page_drops_the_session_link(self):
        body = "molosoc_gift_clear_session_link( 88 ); echo json_encode( $GLOBALS['session'] );"
        out = run_php({"session": {"molosoc_gift_parent": LINK}, "meta": {"88": {"_molosoc_gift_parent_order": 77}}}, body)
        self.assertIn(json.loads(out), ({}, []))
        out = run_php({"session": {"molosoc_gift_parent": LINK}}, body)  # an ordinary order: untouched
        self.assertIn("molosoc_gift_parent", json.loads(out))

    def test_unlinked_checkout_is_untouched(self):
        body = """
        $new = wc_get_order( 88 );
        molosoc_gift_stamp_new_order( $new );
        molosoc_gift_note_orders( $new );
        echo json_encode( array( $new->meta, $GLOBALS['notes'], $new->saved ) );
        """
        self.assertEqual(json.loads(run_php({"cart": {"line425": 1}}, body)), [[], [], 0])

    def test_admin_order_screen_links_to_the_original_order(self):
        body = "molosoc_gift_admin_order_line( wc_get_order( 88 ) );"
        out = run_php({"meta": {"88": {"_molosoc_gift_parent_order": 77}}}, body)
        self.assertIn('href="https://example.test/wp-admin/order/77">#77</a>', out)
        self.assertIn("ship together, shipping 0", out)
        self.assertEqual(run_php({}, body), "")


if __name__ == "__main__":
    unittest.main()
