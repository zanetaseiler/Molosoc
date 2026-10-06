"""Issues #106/#108/#110: bilingual Thank You page hero + post-purchase gift add-on
that ships together with the original order, with offer pricing by the original
order's pair count."""
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
function get_woocommerce_currency() { return $GLOBALS['t']['currency']; }
class Molosoc_Test_Date { public $ts; function __construct( $ts ) { $this->ts = $ts; } function getTimestamp() { return $this->ts; } }
class WC_Order_Item {
	public $pid; public $qty; public $meta = array();
	function __construct( $pid, $q ) { $this->pid = $pid; $this->qty = $q; }
	function get_product_id() { return $this->pid; }
	function get_quantity() { return $this->qty; }
	function add_meta_data( $k, $v, $unique = false ) { $this->meta[ $k ] = $v; }
}
class WC_Order {
	public $id; public $meta = array(); public $saved = 0;
	function __construct( $id ) { $this->id = $id; $this->meta = isset( $GLOBALS['t']['meta'][ $id ] ) ? $GLOBALS['t']['meta'][ $id ] : array(); }
	function get_id() { return $this->id; }
	function get_order_number() { return (string) $this->id; }
	function get_order_key() { return 'wc_order_key' . $this->id; }
	function get_meta( $k ) { if ( '_molosoc_lang' === $k ) { return $GLOBALS['t']['order_lang']; } return isset( $this->meta[ $k ] ) ? $this->meta[ $k ] : ''; }
	function update_meta_data( $k, $v ) { $this->meta[ $k ] = $v; }
	function delete_meta_data( $k ) { unset( $this->meta[ $k ] ); }
	function save() { $this->saved++; $GLOBALS['t']['meta'][ $this->id ] = $this->meta; }
	function has_status( $s ) { return in_array( $GLOBALS['t']['status'][ $this->id ], (array) $s, true ); }
	function get_date_created() { return new Molosoc_Test_Date( time() - $GLOBALS['t']['age'][ $this->id ] ); }
	function get_address( $type ) { return 'billing' === $type ? array( 'first_name' => 'Jana', 'email' => $GLOBALS['t']['email'], 'phone' => '' ) : array( 'first_name' => 'Jana', 'city' => 'Praha' ); }
	function get_items() {
		$out = array();
		foreach ( $GLOBALS['t']['items'][ $this->id ] as $row ) { $out[] = new WC_Order_Item( $row[0], $row[1] ); }
		return $out;
	}
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
class Molosoc_Test_Product {
	public $price = 229;
	function set_price( $p ) { $this->price = $p; }
	function get_regular_price() { return '229'; }
}
class Molosoc_Test_Cart {
	public $items; public $products = array();
	function __construct() {
		$this->items = $GLOBALS['t']['cart'];
		foreach ( $this->items as $key => $qty ) { $this->products[ $key ] = new Molosoc_Test_Product(); }
	}
	function generate_cart_id( $product_id, $variation_id, $attrs, $data = array() ) { return 'line' . $variation_id . ( $data ? 's' . $data['molosoc_gift_slot'] : '' ); }
	function find_product_in_cart( $id ) { return isset( $this->items[ $id ] ) ? $id : ''; }
	function get_cart_item( $key ) { return isset( $this->items[ $key ] ) ? array( 'quantity' => $this->items[ $key ] ) : array(); }
	function set_quantity( $key, $qty ) { $this->items[ $key ] = $qty; }
	function remove_cart_item( $key ) { unset( $this->items[ $key ] ); }
	function get_cart() {
		$out = array();
		foreach ( $this->items as $key => $qty ) {
			$row = array( 'product_id' => 'lineX' === $key ? 999 : 364, 'quantity' => $qty, 'data' => $this->products[ $key ] );
			if ( preg_match( '/s(\\d)$/', $key, $m ) ) { $row['molosoc_gift_slot'] = (int) $m[1]; }
			$out[ $key ] = $row;
		}
		return $out;
	}
	function add_to_cart( $product_id, $qty, $variation_id, $attrs, $data = array() ) {
		if ( $variation_id === $GLOBALS['t']['fail_variation'] ) { return false; }
		$GLOBALS['added'][] = array( $product_id, $qty, $variation_id, $attrs, $data );
		$key = $this->generate_cart_id( $product_id, $variation_id, $attrs, $data );
		$this->products[ $key ] = new Molosoc_Test_Product();
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
    "currency": "CZK",
    "items": {"77": [[364, 1]], "88": [[364, 2], [364, 1]]},
    "fail_variation": 0,
    "session": {},
    "email": "jana@example.test",
}

# Original order 77 holds one pair; the linked cart holds pair #2 (M) and #3 (L).
LINK = {"order_id": 77, "key": "wc_order_key77", "lang": "cz", "time": 0,
        "lines": {"line425s2": 1, "line424s3": 1}, "slots": {"line425s2": 2, "line424s3": 3}}
LINKED_CART = {"line425s2": 1, "line424s3": 1}


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

    def test_normal_price_is_never_hard_coded_or_overridden(self):
        # 229 comes from the live product; only the two offer prices are defined here,
        # and they are applied to cart rows, never to the product or a coupon.
        self.assertIsNone(re.search(r"\b(229|199|209|10)\s*(Kč|CZK|€)|&euro;|\b229\b", self.src))
        self.assertIn("define( 'MOLOSOC_GIFT_PRICE_PAIR_2', 209 )", self.src)
        self.assertIn("define( 'MOLOSOC_GIFT_PRICE_PAIR_3', 199 )", self.src)
        for forbidden in ("WC_Coupon", "add_discount", "apply_coupon", "woocommerce_product_get_price",
                          "woocommerce_get_price", "set_regular_price", "set_sale_price"):
            self.assertNotIn(forbidden, self.src)
        for word in ("bundle", "Save ", "Ušetř"):
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
    def test_original_one_pair_offers_up_to_two_more_at_209_and_199(self):
        # Original order of 1 pair; the base variation prices (229 / 249) are
        # irrelevant to the offer and must not leak into it.
        out = run_php({"variations": {"425": [229, True], "424": [249, True]}}, RENDER, get=KEY)
        self.assertIn('lang="cs"', out)
        self.assertIn("Ještě jedny pro někoho, koho máte rádi?", out)
        self.assertIn("Přidat dárkové páry", out)
        self.assertIn("bez dalšího poštovného", out)
        self.assertIn('action="https://example.test/cz/"', out)
        self.assertIn('name="molosoc_gift_order" value="77"', out)
        self.assertIn('name="molosoc_gift_key" value="wc_order_key77"', out)
        self.assertIn("Přidejte další za 209\xa0Kč — nebo dva za 408\xa0Kč celkem.", out)
        self.assertIn("Druhý přidaný pár stojí 199\xa0Kč.", out)
        totals = json.loads(
            re.search(r'data-totals="([^"]+)"', out).group(1).replace("&quot;", '"')
        )
        self.assertEqual(totals, {"1-0": "209\xa0Kč", "0-1": "209\xa0Kč", "2-0": "408\xa0Kč", "1-1": "408\xa0Kč", "0-2": "408\xa0Kč"})
        self.assertEqual(out.count('name="molosoc_gift_pairs"'), 2)  # no irrelevant third card
        self.assertEqual(re.findall(r'molosoc-gift-card__price" translate="no">([^<]+)<', out), ["209\xa0Kč", "408\xa0Kč"])
        self.assertEqual(out.count("M (36–39)"), 2)  # one size selector per possible pair
        self.assertEqual(out.count("L (39.5–44)"), 2)
        self.assertNotIn("229", out)
        self.assertNotIn("+ 3", out)

    def test_original_two_pairs_offers_exactly_one_more_at_199(self):
        out = run_php({"items": {"77": [[364, 1], [364, 1]]}}, RENDER, get=KEY)
        self.assertIn("Přidejte třetí pár za 199\xa0Kč.", out)
        self.assertNotIn("molosoc-gift-card", out)  # no choice of count
        self.assertEqual(out.count('name="molosoc_gift_pairs"'), 1)
        self.assertIn('type="hidden" name="molosoc_gift_pairs" value="1"', out)
        self.assertEqual(out.count("M (36–39)"), 1)
        totals = json.loads(re.search(r'data-totals="([^"]+)"', out).group(1).replace("&quot;", '"'))
        self.assertEqual(totals, {"1-0": "199\xa0Kč", "0-1": "199\xa0Kč"})
        self.assertNotIn("209", out)
        # The same for a single line item of quantity 2, and across variation lines.
        self.assertIn("Přidejte třetí pár", run_php({"items": {"77": [[364, 2]]}}, RENDER, get=KEY))

    def test_original_three_or_more_pairs_renders_no_upsell_at_all(self):
        body = RENDER + "echo '|', call_user_func( $GLOBALS['hooks']['woocommerce_endpoint_order-received_title'], 'Order received' );"
        for items in ([[364, 3]], [[364, 1], [364, 2]], [[364, 5]], [[364, 1], [364, 1], [364, 1]]):
            out = run_php({"items": {"77": items}}, body, get=KEY)
            self.assertNotIn("molosoc-gift", out, items)
            self.assertTrue(out.startswith("|Děkujeme za vaši objednávku."), items)  # normal Thank You page
        # Other products in the order do not count towards the pair total.
        out = run_php({"items": {"77": [[364, 1], [555, 5]]}}, RENDER, get=KEY)
        self.assertIn("Přidejte další za 209", out)
        # An order without a MOLOSOC pair has nothing to extend.
        self.assertEqual(run_php({"items": {"77": [[555, 1]]}}, RENDER, get=KEY), "")

    def test_english_order_gets_english_section_even_on_a_czech_request(self):
        out = run_php({"order_lang": "en"}, RENDER, get=KEY)
        self.assertIn('lang="en"', out)
        self.assertIn("One more for someone you love?", out)
        self.assertIn("Add gift pairs", out)
        self.assertIn("no additional shipping", out)
        self.assertIn('action="https://example.test/"', out)
        self.assertIn("+ 1 pair<", out)
        self.assertIn("+ 2 pairs<", out)
        self.assertIn("Add another for 209\xa0CZK — or two for 408\xa0CZK total.", out)
        self.assertIn("The second additional pair is 199\xa0CZK.", out)
        out = run_php({"order_lang": "en", "items": {"77": [[364, 2]]}}, RENDER, get=KEY)
        self.assertIn("Add a third pair for 199\xa0CZK.", out)

    def test_no_offer_when_the_shop_currency_is_not_czk(self):
        self.assertEqual(run_php({"currency": "EUR"}, RENDER, get=KEY), "")

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
        linked = {"meta": {"77": {"_molosoc_gift_parent_order": 88, "_molosoc_gift_parent_order_noted": "yes"}}}
        self.assertEqual(run_php(linked, body, get=KEY), "Vaši objednávku jsme přijali. Pošleme ji společně s objednávkou č. 88.")
        self.assertEqual(
            run_php(dict(linked, order_lang="en"), body, get=KEY),
            "Your order has been received. It ships together with order #88.",
        )

    def test_gift_order_with_payment_still_pending_makes_no_ship_together_promise(self):
        body = "echo molosoc_thankyou_received_text( 'x', wc_get_order( 77 ) );"
        pending = {"meta": {"77": {"_molosoc_gift_parent_order": 88}}}
        self.assertEqual(run_php(pending, body, get=KEY), "Vaši objednávku jsme přijali.")

    def test_manually_routed_gift_order_makes_no_ship_together_promise(self):
        body = "echo molosoc_thankyou_received_text( 'x', wc_get_order( 77 ) );"
        manual = {"meta": {"77": {"_molosoc_gift_parent_order": 88, "_molosoc_gift_parent_order_noted": "manual"}}}
        self.assertEqual(run_php(manual, body, get=KEY), "Vaši objednávku jsme přijali.")

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
        # on-hold = payment unconfirmed: the original may still fail, so no offer.
        self.assertNotIn("molosoc-gift", run_php({"status": {"77": "on-hold"}}, RENDER, get=KEY))

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
            dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        )
        self.assertEqual(redirect, "https://example.test/cz/pokladna/")
        # One quantity-1 row per pair, each tagged with its overall pair number.
        self.assertEqual(
            added,
            [[364, 1, 425, {"attribute_size": "M"}, {"molosoc_gift_slot": 2}],
             [364, 1, 424, {"attribute_size": "L"}, {"molosoc_gift_slot": 3}]],
        )
        link = section(out, "SESSION")["molosoc_gift_parent"]
        self.assertEqual((link["order_id"], link["key"], link["lang"]), (77, "wc_order_key77", "cz"))
        self.assertEqual(link["lines"], {"line425s2": 1, "line424s3": 1})
        self.assertEqual(link["slots"], {"line425s2": 2, "line424s3": 3})
        customer = section(out, "CUSTOMER")
        self.assertEqual(customer["billing_first_name"], "Jana")
        self.assertEqual(customer["billing_email"], "jana@example.test")
        self.assertEqual(customer["shipping_city"], "Praha")
        self.assertEqual(customer["billing_phone"], "")  # blank parent fields clear stale session values
        self.assertEqual(customer["saved"], 1)  # session-backed customer saved so checkout sees the address

    def test_preloaded_rows_are_rejected_and_untouched(self):
        # A row the shopper already had (the same pair, or any ordinary pair) is
        # never merged into or shrunk: the add is rolled back and nothing is linked.
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        for cart in ({"line425s2": 1}, {"line425": 3}, {"line424": 1}, {"line999": 2}, {"line999": 2, "line425": 3}):
            redirect, _, out = self.submit(post, {"cart": cart})
            self.assertEqual(redirect, "https://example.test/product-cz/", cart)
            self.assertEqual(section(out, "CART"), cart)
            self.assertEqual(section(out, "SESSION"), {})

    def test_english_form_goes_to_the_english_checkout(self):
        redirect, added, _ = self.submit(
            dict(FORM, molosoc_gift_lang="en", molosoc_gift_size=["L"]), {"request_lang": "en"}
        )
        self.assertEqual(redirect, "https://example.test/checkout/")
        self.assertEqual(added, [[364, 1, 424, {"attribute_size": "L"}, {"molosoc_gift_slot": 2}]])

    def test_original_two_pairs_may_add_only_the_third_pair(self):
        two = {"items": {"77": [[364, 2]]}}
        _, added, out = self.submit(dict(FORM, molosoc_gift_size=["L"]), two)
        self.assertEqual(added, [[364, 1, 424, {"attribute_size": "L"}, {"molosoc_gift_slot": 3}]])
        self.assertEqual(section(out, "SESSION")["molosoc_gift_parent"]["slots"], {"line424s3": 3})
        # Asking for two is rejected, not trimmed to one.
        redirect, added, out = self.submit(dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"]), two)
        self.assertEqual(redirect, "https://example.test/product-cz/")
        self.assertEqual((added, section(out, "CART"), section(out, "SESSION")), ({}, {}, {}))

    def test_original_three_or_more_pairs_gets_no_gift_cart_at_all(self):
        for items in ([[364, 3]], [[364, 1], [364, 2]], [[364, 4]]):
            redirect, added, out = self.submit(FORM, {"items": {"77": items}})
            self.assertEqual(redirect, "https://example.test/product-cz/", items)
            self.assertEqual((added, section(out, "CART"), section(out, "SESSION")), ({}, {}, {}))

    def test_form_for_an_order_that_cannot_ship_together_adds_nothing(self):
        for post, scenario in (
            (dict(FORM, molosoc_gift_key="wc_order_wrong"), {}),
            (dict(FORM, molosoc_gift_order="12"), {}),
            ({k: v for k, v in FORM.items() if k not in ("molosoc_gift_order", "molosoc_gift_key")}, {}),
            (FORM, {"status": {"77": "completed"}}),
            (FORM, {"status": {"77": "pending"}}),
            (FORM, {"status": {"77": "on-hold"}}),
            (FORM, {"age": {"77": 30 * 3600}}),
            (FORM, {"meta": {"77": {"_molosoc_gift_parent_order": 88}}}),
        ):
            redirect, added, out = self.submit(post, scenario)
            self.assertEqual(redirect, "https://example.test/product-cz/", (post, scenario))
            self.assertEqual(added, {})
            self.assertEqual(section(out, "SESSION"), {})

    def test_more_pairs_than_allowed_is_rejected_never_trimmed_to_a_discounted_fourth_pair(self):
        for pairs in ("3", "4", "50", "0", "abc"):
            redirect, added, out = self.submit(dict(FORM, molosoc_gift_pairs=pairs, molosoc_gift_size=["M"] * 50))
            self.assertEqual(redirect, "https://example.test/product-cz/", pairs)
            self.assertEqual((added, section(out, "CART"), section(out, "SESSION")), ({}, {}, {}), pairs)
        redirect, _, _ = self.submit(dict(FORM, molosoc_gift_pairs=["2"], molosoc_gift_size=["M", "M"]))
        self.assertEqual(redirect, "https://example.test/product-cz/")

    def test_only_the_chosen_number_of_pairs_is_added(self):
        _, added, _ = self.submit(dict(FORM, molosoc_gift_size=["M", "L", "L"]))
        self.assertEqual(added, [[364, 1, 425, {"attribute_size": "M"}, {"molosoc_gift_slot": 2}]])

    def test_partly_failed_selection_is_rolled_back_and_never_reaches_checkout(self):
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        # L can't be added after M already was: M's addition is undone.
        _, _, out = self.submit(post, {"fail_variation": 424})
        self.assertIn("REDIRECT:https://example.test/product-cz/", out)
        self.assertEqual(section(out, "CART"), {})
        self.assertEqual(section(out, "SESSION"), {})
        # Rows that were in the cart before keep their quantity.
        _, _, out = self.submit(post, {"fail_variation": 424, "cart": {"line425": 1}})
        self.assertEqual(section(out, "CART"), {"line425": 1})
        # The first size failing leaves the cart untouched too.
        _, _, out = self.submit(post, {"fail_variation": 425, "cart": {"line424": 2}})
        self.assertEqual(section(out, "CART"), {"line424": 2})

    def test_missing_invalid_or_unavailable_size_adds_nothing(self):
        for post, scenario in (
            (dict(FORM, molosoc_gift_pairs="2"), {}),
            (dict(FORM, molosoc_gift_size=["XL"]), {}),
            ({k: v for k, v in FORM.items() if k != "molosoc_gift_size"}, {}),
            (dict(FORM, molosoc_gift_size="M"), {}),
            (dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "XL"]), {}),
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
        out = run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART}, self.RATES)
        self.assertEqual(
            json.loads(out),
            {"molosoc_gift_combined": ["molosoc_gift_combined", "Pošleme s objednávkou č. 77 — bez dalšího poštovného", 0, [], "molosoc_gift_combined", 0]},
        )
        out = run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART, "request_lang": "en"}, self.RATES)
        self.assertEqual(json.loads(out)["molosoc_gift_combined"][1], "Ships with order #77 — no additional shipping")

    def test_normal_rates_stay_whenever_the_link_is_not_valid(self):
        normal = {"flat_rate:1": "normal", "zasilkovna": "pickup"}
        S = {"molosoc_gift_parent": LINK}
        for scenario in (
            {"cart": {"line425": 1}},                                                 # no link at all
            {"session": {"molosoc_gift_parent": dict(LINK, key="stale")}, "cart": LINKED_CART},
            {"session": S, "cart": {}},                                               # empty cart
            {"session": S, "cart": dict(LINKED_CART, lineX=1)},                       # another product
            {"session": S, "cart": {"line425s2": 2, "line424s3": 1}},                 # quantity changed
            {"session": S, "cart": {"line425s2": 1, "line424s3": 1, "line425": 1}},   # extra ordinary pair
            {"session": S, "cart": {"line425s2": 1, "line424s3": 1, "line425s3": 1}}, # a third gift row
            {"session": S, "cart": {"line425s2": 1}},                                 # a row removed
            {"session": {"molosoc_gift_parent": {k: v for k, v in LINK.items() if k != "lines"}}, "cart": LINKED_CART},
            {"session": {"molosoc_gift_parent": {k: v for k, v in LINK.items() if k != "slots"}}, "cart": LINKED_CART},
            {"session": S, "cart": LINKED_CART, "status": {"77": "completed"}},
            {"session": S, "cart": LINKED_CART, "age": {"77": 48 * 3600}},
            {"session": S, "cart": LINKED_CART, "items": {"77": [[364, 3]]}},         # original now 3 pairs
            {"session": S, "cart": LINKED_CART, "items": {"77": [[364, 2]]}},         # original now 2: one allowed
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
        out = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART}, body))
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

    def test_stale_stamp_is_removed_when_the_link_stops_being_valid(self):
        body = """
        $new = wc_get_order( 88 );
        molosoc_gift_stamp_new_order( $new );
        $first = isset( $new->meta['_molosoc_gift_parent_order'] );
        $GLOBALS['session']['molosoc_gift_parent'] = null; // link gone: draft updated again
        molosoc_gift_stamp_new_order( $new );
        echo json_encode( array( 'first' => $first, 'after' => isset( $new->meta['_molosoc_gift_parent_order'] ) ) );
        """
        out = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART}, body))
        self.assertTrue(out["first"])
        self.assertFalse(out["after"])

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
        scenario = {"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART,
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
        # A link for a different original order (another tab) is not this add-on's to drop.
        other = dict(LINK, order_id=55)
        out = run_php({"session": {"molosoc_gift_parent": other}, "meta": {"88": {"_molosoc_gift_parent_order": 77}}}, body)
        self.assertEqual(json.loads(out)["molosoc_gift_parent"]["order_id"], 55)

    def test_shipping_cache_key_follows_the_link_state(self):
        body = """
        echo json_encode( molosoc_gift_shipping_package_state( array( array( 'contents' => array() ), array( 'contents' => array() ) ) ) );
        """
        linked = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART}, body))
        self.assertEqual([p["molosoc_gift_parent"] for p in linked], [77, 77])
        for scenario in (
            {"cart": {"line425": 2}},                                                     # no link
            {"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART, "status": {"77": "completed"}},
            {"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART, "age": {"77": 48 * 3600}},
        ):
            unlinked = json.loads(run_php(scenario, body))
            self.assertEqual([p["molosoc_gift_parent"] for p in unlinked], [0, 0], scenario)

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

    def test_admin_line_does_not_say_ship_together_for_manual_orders(self):
        body = "molosoc_gift_admin_order_line( wc_get_order( 88 ) );"
        out = run_php({"meta": {"88": {"_molosoc_gift_parent_order": 77, "_molosoc_gift_parent_order_noted": "manual"}}}, body)
        self.assertIn("handle manually", out)
        self.assertNotIn("ship together,", out)


@unittest.skipUnless(shutil.which("php"), "php not installed")
class OfferPricing(unittest.TestCase):
    """The 209 / 199 prices (#110) exist only on a valid, linked gift cart."""

    PRICES = """
    molosoc_gift_apply_prices( WC()->cart );
    $out = array();
    foreach ( WC()->cart->get_cart() as $key => $item ) { $out[ $key ] = $item['data']->price; }
    echo json_encode( $out );
    """

    def prices(self, cart, link=None, **extra):
        scenario = dict({"session": {"molosoc_gift_parent": link or LINK}, "cart": cart}, **extra)
        return json.loads(run_php(scenario, self.PRICES))

    def link(self, slots, **extra):
        return dict(LINK, lines={k: 1 for k in slots}, slots=slots, **extra)

    def test_original_one_pair_plus_one_addon_is_209(self):
        slots = {"line425s2": 2}
        self.assertEqual(self.prices({"line425s2": 1}, self.link(slots)), {"line425s2": 209})

    def test_original_one_pair_plus_two_addons_is_209_plus_199_for_408(self):
        prices = self.prices(LINKED_CART)  # pair #2 in M, pair #3 in L
        self.assertEqual(prices, {"line425s2": 209, "line424s3": 199})
        self.assertEqual(sum(prices.values()), 408)

    def test_mixed_and_same_sizes_price_by_pair_number_not_by_size(self):
        for first, second in (("425", "425"), ("424", "424"), ("424", "425"), ("425", "424")):
            slots = {"line%ss2" % first: 2, "line%ss3" % second: 3}
            prices = self.prices({k: 1 for k in slots}, self.link(slots))
            self.assertEqual(prices, {"line%ss2" % first: 209, "line%ss3" % second: 199}, (first, second))
        # Different base variation prices change nothing.
        out = run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART,
                       "variations": {"425": [229, True], "424": [249, True]}}, self.PRICES)
        self.assertEqual(json.loads(out), {"line425s2": 209, "line424s3": 199})

    def test_original_two_pairs_plus_one_addon_is_199(self):
        link = self.link({"line424s3": 3})
        self.assertEqual(self.prices({"line424s3": 1}, link, items={"77": [[364, 1], [364, 1]]}), {"line424s3": 199})
        self.assertEqual(self.prices({"line424s3": 1}, link, items={"77": [[364, 2]]}), {"line424s3": 199})

    def test_no_offer_price_for_original_three_or_more_pairs(self):
        for items in ([[364, 3]], [[364, 4]], [[364, 1], [364, 2]]):
            self.assertEqual(self.prices(LINKED_CART, items={"77": items}), {"line425s2": 229, "line424s3": 229}, items)

    def test_a_fourth_pair_or_forged_slots_never_get_the_offer_price(self):
        forged = (
            {"line425s2": 2, "line424s3": 3, "line425s4": 4},   # a fourth pair overall
            {"line425s3": 3, "line424s3": 3},                    # same slot twice (cannot collide in a real cart, still rejected)
            {"line425s3": 3, "line424s4": 4},                    # skips pair #2
            {"line425s1": 1},                                    # slot 1 = the original pair
        )
        for slots in forged:
            cart = {k: 1 for k in slots}
            normal = {k: 229 for k in slots}
            self.assertEqual(self.prices(cart, self.link(slots)), normal, slots)
        # Original order of two pairs: slot 2 is not on offer, and two add-ons are one too many.
        two = {"items": {"77": [[364, 2]]}}
        self.assertEqual(self.prices({"line425s2": 1}, self.link({"line425s2": 2}), **two), {"line425s2": 229})
        self.assertEqual(self.prices(LINKED_CART, **two), {"line425s2": 229, "line424s3": 229})
        # A row whose own slot tag disagrees with the link, or whose quantity grew.
        self.assertEqual(self.prices({"line425s2": 1, "line424s3": 1}, dict(LINK, slots={"line425s2": 2, "line424s3": 2})),
                         {"line425s2": 229, "line424s3": 229})
        self.assertEqual(self.prices({"line425s2": 2, "line424s3": 1}), {"line425s2": 229, "line424s3": 229})

    def test_expired_or_ineligible_parent_gets_no_price_and_no_free_shipping(self):
        rates = LinkedCheckout.RATES
        normal = {"flat_rate:1": "normal", "zasilkovna": "pickup"}
        for extra in (
            {"status": {"77": "completed"}},
            {"status": {"77": "on-hold"}},
            {"age": {"77": 24 * 3600 + 1}},
            {"meta": {"77": {"_molosoc_gift_parent_order": 88}}},
            {"meta": {"88": {"_molosoc_gift_parent_order": 77, "_molosoc_gift_parent_order_noted": "yes"}}},
            {"currency": "EUR"},
        ):
            self.assertEqual(self.prices(LINKED_CART, **extra), {"line425s2": 229, "line424s3": 229}, extra)
            scenario = dict({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART}, **extra)
            self.assertEqual(json.loads(run_php(scenario, rates)), normal, extra)
        # Wrong order key in the session: same.
        self.assertEqual(self.prices(LINKED_CART, dict(LINK, key="forged")), {"line425s2": 229, "line424s3": 229})

    def test_normal_cart_and_product_stay_229(self):
        # No session link, or an ordinary product row: never touched.
        for cart in ({"line425": 1}, {"line425": 3, "line424": 1}, {"line425s2": 1}):
            out = run_php({"cart": cart}, self.PRICES)
            self.assertEqual(json.loads(out), {k: 229 for k in cart}, cart)
        # An ordinary row beside a valid gift cart is a different cart: nothing is discounted.
        mixed = {"line425": 1, "line425s2": 1, "line424s3": 1}
        self.assertEqual(self.prices(mixed), {k: 229 for k in mixed})
        # The offer prices never go through the product or a coupon.
        src = GIFT.read_text(encoding="utf-8")
        self.assertIn("'woocommerce_before_calculate_totals'", src)
        self.assertNotIn("add_filter( 'woocommerce_product", src)

    def test_order_keeps_the_pricing_audit_trail(self):
        body = """
        $new = wc_get_order( 88 );
        molosoc_gift_stamp_new_order( $new );
        $item = new WC_Order_Item( 364, 1 );
        $cart = WC()->cart->get_cart();
        molosoc_gift_stamp_order_line( $item, 'line424s3', $cart['line424s3'], $new );
        $plain = new WC_Order_Item( 364, 1 );
        molosoc_gift_stamp_order_line( $plain, 'line999', array( 'data' => new Molosoc_Test_Product() ), $new );
        molosoc_gift_note_orders_by_id( 88 );
        echo json_encode( array( 'meta' => $new->meta, 'item' => $item->meta, 'plain' => $plain->meta, 'notes' => $GLOBALS['notes'] ) );
        """
        out = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART}, body))
        self.assertEqual(out["meta"]["_molosoc_gift_parent_order"], 77)
        self.assertEqual(out["meta"]["_molosoc_gift_parent_order_original_qty"], 1)
        self.assertEqual(json.loads(out["meta"]["_molosoc_gift_parent_order_pricing"]), {"2": 209, "3": 199})
        self.assertEqual(out["item"], {"_molosoc_gift_pair_number": 3, "_molosoc_gift_unit_price": "199", "_molosoc_gift_list_price": "229"})
        self.assertIn(out["plain"], ([], {}))  # rows the link did not price carry no offer record
        self.assertIn("pair #2 = 209, #3 = 199", out["notes"][0][1])  # private note on the add-on order
        self.assertNotIn("209", out["notes"][1][1])                    # the original order only gets its link note

    def test_parent_order_and_linkage_still_work_with_the_offer(self):
        rates = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART}, LinkedCheckout.RATES))
        self.assertEqual(list(rates), ["molosoc_gift_combined"])
        self.assertEqual(rates["molosoc_gift_combined"][2], 0)
        body = "$o = wc_get_order( 88 ); molosoc_gift_note_orders_by_id( 88 ); echo json_encode( array( $o->meta, $GLOBALS['notes'], wc_get_order( 77 )->saved ) );"
        meta, notes, parent_saved = json.loads(run_php({"meta": {"88": {"_molosoc_gift_parent_order": 77}}}, body))
        self.assertEqual(meta["_molosoc_gift_parent_order_noted"], "yes")
        self.assertEqual([n[0] for n in notes], [88, 77])
        self.assertEqual(parent_saved, 0)  # the paid original order is only annotated, never saved

    def test_manual_handling_note_flags_that_offer_prices_were_charged(self):
        body = "molosoc_gift_note_orders_by_id( 88 ); echo json_encode( $GLOBALS['notes'] );"
        notes = json.loads(run_php({"status": {"77": "completed"}, "meta": {"88": {"_molosoc_gift_parent_order": 77}}}, body))
        self.assertIn("offer prices were charged", notes[0][1])


if __name__ == "__main__":
    unittest.main()
