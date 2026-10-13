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
$GLOBALS['log'] = array();
$GLOBALS['trace'] = array();
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
$GLOBALS['notices'] = array();
function wc_add_notice( $m, $t = 'success' ) { $GLOBALS['notices'][] = $m; }
function wp_safe_redirect( $url ) { echo "\nREDIRECT:" . $url . "\nADDED:" . json_encode( $GLOBALS['added'] ) . "\nCART:" . json_encode( WC()->cart->items ) . "\nSESSION:" . json_encode( $GLOBALS['session'] ) . "\nCOOKIE:" . json_encode( ! empty( $GLOBALS['cookie'] ) ) . "\nLOG:" . json_encode( $GLOBALS['log'] ) . "\nTRACE:" . json_encode( $GLOBALS['trace'] ) . "\nNOTICES:" . json_encode( $GLOBALS['notices'], JSON_UNESCAPED_UNICODE ) . "\nCUSTOMER:" . json_encode( WC()->customer->props ); }
function is_wc_endpoint_url( $e ) { return 'order-received' === $e && ! empty( $GLOBALS['t']['endpoint'] ); }
function pll_current_language() { return $GLOBALS['t']['request_lang']; }
function pll_get_post( $id, $lang ) { return 'cz' === $lang ? 900 : 360; }
function get_post_status( $id ) { return 'publish'; }
function get_permalink( $id ) { return 900 === $id ? 'https://example.test/cz/pokladna/' : 'https://example.test/checkout/'; }
function wc_get_endpoint_url( $endpoint, $value, $base ) { return $base . $endpoint . '/' . $value . '/'; }
function add_query_arg( $k, $v, $url ) { return $url . '?' . $k . '=' . $v; }
function wc_get_logger() { return new class { function warning( $m, $c = array() ) { $GLOBALS['log'][] = $m; } function info( $m, $c = array() ) { $GLOBALS['trace'][] = $m; } }; }
function molosoc_size_value_rank( $v ) { return in_array( strtolower( $v ), array( 'm' ), true ) ? 0 : ( in_array( strtolower( $v ), array( 'l' ), true ) ? 1 : 2 ); }
function wc_get_page_id( $page ) { return 360; }
function wc_get_checkout_url() { return 'https://example.test/checkout/'; }
function molosoc_product_url( $lang = null ) { return 'https://example.test/product-' . $lang . '/'; }
function molosoc_size_label_for_value( $v, $f ) { return 'M' === $v ? 'M (36–39)' : 'L (39.5–44)'; }
function wc_price( $amount ) { return '<span class="amount">' . number_format( $amount, 0, ',', ' ' ) . '&nbsp;K&#269;</span>'; }
function wc_get_price_to_display( $p ) { return $p->price; }
function get_woocommerce_currency() { return $GLOBALS['t']['currency']; }
class Molosoc_Test_Date { public $ts; function __construct( $ts ) { $this->ts = $ts; } function getTimestamp() { return $this->ts; } }
class WC_Order_Item {
	public $pid; public $qty; public $vid; public $meta = array();
	function __construct( $pid, $q, $vid = 0 ) { $this->pid = $pid; $this->qty = $q; $this->vid = $vid; }
	function get_product_id() { return $this->pid; }
	function get_variation_id() { return $this->vid; }
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
		foreach ( $GLOBALS['t']['items'][ $this->id ] as $row ) { $out[] = new WC_Order_Item( $row[0], $row[1], isset( $row[2] ) ? $row[2] : 0 ); }
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
	public $pmeta = array();
	function get_price( $c = 'view' ) { return $this->price; }
	function get_meta( $k, $single = true, $c = 'view' ) { return isset( $this->pmeta[ $k ] ) ? $this->pmeta[ $k ] : ''; }
	function update_meta_data( $k, $v ) { $this->pmeta[ $k ] = $v; }
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
	public $removed = array();
	function remove_cart_item( $key ) { if ( isset( $this->items[ $key ] ) ) { $this->removed[ $key ] = $this->items[ $key ]; } unset( $this->items[ $key ] ); }
	function get_removed_cart_contents() { return $this->removed; }
	function set_removed_cart_contents( $removed ) { $this->removed = array(); foreach ( $removed as $key => $row ) { $this->removed[ $key ] = is_array( $row ) ? $row['quantity'] : $row; } }
	function restore_cart_item( $key ) { if ( isset( $this->removed[ $key ] ) ) { $this->items[ $key ] = $this->removed[ $key ]; unset( $this->removed[ $key ] ); } }
	function get_cart() {
		$out = array();
		foreach ( $this->items as $key => $qty ) {
			$row = array( 'product_id' => in_array( $key, array( 'lineX', 'line999' ), true ) ? 999 : 364, 'variation_id' => (int) substr( $key, 4 ), 'quantity' => $qty, 'data' => $this->products[ $key ] );
			if ( preg_match( '/s(\\d)$/', $key, $m ) ) { $row['molosoc_gift_slot'] = (int) $m[1]; }
			$out[ $key ] = $row;
		}
		return $out;
	}
	function add_to_cart( $product_id, $qty, $variation_id, $attrs, $data = array() ) {
		if ( $variation_id === $GLOBALS['t']['fail_variation'] ) { return false; }
		// Like WooCommerce, the stock check counts what the cart already holds.
		$key = $this->generate_cart_id( $product_id, $variation_id, $attrs, $data );
		$stock = $GLOBALS['t']['stock'];
		if ( isset( $stock[ $variation_id ] ) && ( isset( $this->items[ $key ] ) ? $this->items[ $key ] : 0 ) + $qty > $stock[ $variation_id ] ) { return false; }
		$GLOBALS['added'][] = array( $product_id, $qty, $variation_id, $attrs, $data );
		$key = $this->generate_cart_id( $product_id, $variation_id, $attrs, $data );
		$this->products[ $key ] = new Molosoc_Test_Product();
		$this->items[ $key ] = ( isset( $this->items[ $key ] ) ? $this->items[ $key ] : 0 ) + $qty;
		return $key;
	}
}
class Molosoc_Test_Session {
	function set_customer_session_cookie( $set ) { $GLOBALS['cookie'] = $set; }
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
    "items": {"77": [[364, 1, 425]], "88": [[364, 2], [364, 1]]},
    "fail_variation": 0,
    "stock": {},
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
# Session record written when order 77 was placed (see molosoc_gift_remember_paid_rows).
def paid_record(rows, **over):
    record = {"order_id": 77, "rows": {k: {"variation": int(k[4:]), "quantity": q} for k, q in rows.items()}, "tainted": False}
    return {"molosoc_gift_paid_rows": dict(record, **over)}
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
            {"get_id", "get_order_key", "get_order_number", "get_address", "get_edit_order_url", "add_order_note", "get_items"},
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


class SpacingContract(unittest.TestCase):
    def test_offer_and_quantity_cards_have_breathing_room(self):
        css = (THEME / "assets/css/thank-you.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.molosoc-gift__form \{\s*margin-top: var\(--space-m\)")
        self.assertRegex(css, r"\.molosoc-gift__choices \{\s*display: grid;\s*gap: var\(--space-xs\)")
        self.assertRegex(css, r"\.molosoc-gift__offer-note \{\s*display: block;\s*margin-top")


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

    def test_section_follows_the_request_language_so_the_switcher_switches_the_page(self):
        # An English order viewed through the Czech URL (after the language
        # switch) renders Czech, and the form posts to the Czech checkout flow.
        out = run_php({"order_lang": "en", "request_lang": "cz"}, RENDER, get=KEY)
        self.assertIn('lang="cs"', out)
        self.assertIn('name="molosoc_gift_lang" value="cz"', out)
        self.assertIn('action="https://example.test/cz/"', out)

    def test_english_request_gets_english_section(self):
        out = run_php({"order_lang": "en", "request_lang": "en"}, RENDER, get=KEY)
        self.assertIn('lang="en"', out)
        self.assertIn("One more for someone you love?", out)
        self.assertIn("Add gift pairs", out)
        self.assertIn("no additional shipping", out)
        self.assertIn('action="https://example.test/"', out)
        self.assertIn("+ 1 pair<", out)
        self.assertIn("+ 2 pairs<", out)
        self.assertIn("Add another for 209\xa0CZK — or two for 408\xa0CZK total.", out)
        self.assertIn("The second additional pair is 199\xa0CZK.", out)
        out = run_php({"order_lang": "en", "request_lang": "en", "items": {"77": [[364, 2]]}}, RENDER, get=KEY)
        self.assertIn("Add a third pair for 199\xa0CZK.", out)

    def test_no_offer_when_the_shop_currency_is_not_czk(self):
        self.assertEqual(run_php({"currency": "EUR"}, RENDER, get=KEY), "")

    def test_hero_and_confirmation_text_follow_the_request_then_the_order_language(self):
        body = """
        echo call_user_func( $GLOBALS['hooks']['woocommerce_endpoint_order-received_title'], 'Order received' ), '|';
        echo molosoc_thankyou_received_text( 'Thank you. Your order has been received.', wc_get_order( 77 ) );
        """
        self.assertEqual(run_php({}, body, get=KEY), "Děkujeme za vaši objednávku.|Vaši objednávku jsme přijali.")
        self.assertEqual(
            run_php({"order_lang": "en", "request_lang": "en"}, body, get=KEY),
            "Thank you for your order.|Your order has been received.",
        )
        # A request with no language of its own falls back to the order's.
        self.assertTrue(
            run_php({"order_lang": "en", "request_lang": ""}, body, get=KEY).startswith("Thank you for your order.")
        )

    def test_gift_order_thank_you_names_the_order_it_ships_with(self):
        body = "echo molosoc_thankyou_received_text( 'x', wc_get_order( 77 ) );"
        linked = {"meta": {"77": {"_molosoc_gift_parent_order": 88, "_molosoc_gift_parent_order_noted": "yes"}}}
        self.assertEqual(run_php(linked, body, get=KEY), "Vaši objednávku jsme přijali. Pošleme ji společně s objednávkou č. 88.")
        self.assertEqual(
            run_php(dict(linked, order_lang="en", request_lang="en"), body, get=KEY),
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

    def test_valid_submission_goes_to_checkout_never_the_product_page(self):
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        for lang, url in (("cz", "https://example.test/cz/pokladna/"), ("en", "https://example.test/checkout/")):
            redirect, _, _ = self.submit(dict(post, molosoc_gift_lang=lang), {"request_lang": lang})
            self.assertEqual(redirect, url)
            self.assertNotIn("product", redirect)

    @staticmethod
    def owned(cart, **over):
        link = {"order_id": 77, "key": "wc_order_key77", "lang": "cz", "lines": {k: 1 for k in cart}, "slots": {k: int(k[-1]) if "s" in k[4:] else 2 for k in cart}, "time": 1}
        return {"molosoc_gift_parent": dict(link, **over)}

    def test_rows_left_from_an_earlier_submit_do_not_block_checkout(self):
        # Our own gift rows from an earlier submit are dropped; the new cart is
        # exactly the chosen pairs.
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        for cart in ({"line425s2": 1}, {"line424s3": 1}, {"line425s2": 1, "line424s3": 1}):
            redirect, _, out = self.submit(post, {"cart": cart, "session": self.owned(cart)})
            self.assertEqual(redirect, "https://example.test/cz/pokladna/", cart)
            self.assertEqual(section(out, "CART"), {"line425s2": 1, "line424s3": 1}, cart)
            self.assertIn("molosoc_gift_parent", section(out, "SESSION"))

    def test_the_pair_just_bought_is_set_aside_not_charged_and_not_a_product_page_fallback(self):
        # Issue #145, production: the add-on checkout carried the already-paid
        # original pair(s). Original order 77 holds ONE paid pair (variation 425,
        # M). A cart row that is exactly that paid line is set aside on evidence;
        # the add-on cart holds the gift rows only.
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        redirect, _, out = self.submit(post, {"cart": {"line425": 1}, "session": paid_record({"line425": 1})})
        self.assertEqual(redirect, "https://example.test/cz/pokladna/")
        self.assertEqual(section(out, "CART"), {"line425s2": 1, "line424s3": 1})
        self.assertEqual(section(out, "COOKIE"), True)
        link = section(out, "SESSION")["molosoc_gift_parent"]
        self.assertEqual(set(link["lines"]), set(section(out, "CART")))
        # Two paid pairs (one line of quantity 2, or two lines): same.
        two = {"items": {"77": [[364, 2, 425]]}}
        for cart in ({"line425": 2}, {"line425": 1}):
            redirect, _, out = self.submit(dict(FORM, molosoc_gift_size=["L"]), dict(two, cart=cart, session=paid_record(cart)))
            self.assertEqual(redirect, "https://example.test/cz/pokladna/", cart)
            self.assertEqual(section(out, "CART"), {"line424s3": 1}, cart)
        two = {"items": {"77": [[364, 1, 425], [364, 1, 424]]}}
        redirect, _, out = self.submit(dict(FORM, molosoc_gift_size=["L"]), dict(two, cart={"line425": 1, "line424": 1}, session=paid_record({"line425": 1, "line424": 1})))
        self.assertEqual(redirect, "https://example.test/cz/pokladna/")
        self.assertEqual(section(out, "CART"), {"line424s3": 1})

    def test_any_other_cart_row_is_parked_never_a_product_page_fallback_and_never_deleted(self):
        # Issue #147, production: after #146 any row the session could not vouch for
        # sent a VALID +1/+2 submission to the product page. Whatever else the cart
        # holds is parked in the session (never deleted, never charged); the add-on
        # cart is exactly the gift rows and the shopper still reaches checkout.
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        for cart, session in (
            ({"line999": 2}, {}),                       # another product
            ({"line999": 1, "line425": 1}, {}),         # paid pair plus another product
            ({"line424": 1}, {}),                       # other variation than the paid one
            ({"line425": 3}, {}),                       # more than the paid quantity
            ({"line425": 1, "line424": 1}, {}),         # extra variation beside the paid pair
            ({"line425": 1}, {}),                       # the paid pair, order placed before the record existed
            ({"line424s2": 1}, {}),                     # gift-shaped row, no link
            ({"line424s2": 1}, self.owned({"line424s2": 1}, order_id=88)),
            ({"line424s2": 1}, self.owned({"line424s2": 1}, key="wc_order_other")),
            ({"line424s2": 1}, self.owned({"line424s2": 1}, slots={"line424s2": 3})),
        ):
            redirect, added, out = self.submit(post, {"cart": cart, "session": session})
            self.assertEqual(redirect, "https://example.test/cz/pokladna/", (cart, session))
            self.assertEqual(section(out, "CART"), {"line425s2": 1, "line424s3": 1}, (cart, session))
            parked = section(out, "SESSION")["molosoc_gift_parked_rows"]
            self.assertEqual({k: r["quantity"] for k, r in parked["rows"].items()}, cart, (cart, session))
            self.assertFalse(section(out, "NOTICES"), (cart, session))
            self.assertFalse(section(out, "LOG"), (cart, session))  # no fallback reason logged
            self.assertNotIn("wc_order_key77", out.split("TRACE:")[1])

    def test_a_pair_that_only_matches_the_order_is_parked_and_comes_back_unless_proven_paid(self):
        # Codex P1 on #146: a pair added after ordering looks exactly like the paid
        # one and must never vanish. It is parked, and returns after the add-on
        # unless the untainted record of THIS order names that very row.
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        cart = {"line425": 1}
        back = "molosoc_gift_unpark_rows(); echo json_encode( WC()->cart->items );"
        for session, comes_back in (
            ({}, True),                                                  # no record: other session / older order
            (paid_record({"line425": 1}, tainted=True), True),           # a product was added/raised after ordering
            (paid_record({"line425": 1}, order_id=88), True),            # record belongs to another order
            (paid_record({"line424": 1}), True),                         # record names a different row
            (paid_record({"line425": 1}), False),                        # proven: the pair that was paid for
        ):
            _, _, out = self.submit(post, {"cart": cart, "session": session})
            self.assertEqual(section(out, "CART"), {"line425s2": 1, "line424s3": 1}, session)
            after = run_php({"cart": {}, "session": section(out, "SESSION")}, back)
            self.assertEqual(json.loads(after) if after != "[]" else {}, {"line425": 1} if comes_back else {}, session)

    def test_the_paid_pair_is_never_in_the_addon_checkout_and_only_gift_pairs_are_charged(self):
        # Issue #147 jointly: successful checkout redirect (EN and CZ), +1 charges
        # 209, +2 charges 408 (209 + 199), shipping 0, the original order is not
        # charged again, and the shopper's own rows are kept. Run for the pair just
        # bought with and without the session record (order placed before #146).
        check = """
        $cart = WC()->cart;
        molosoc_gift_apply_prices( $cart );
        $total = 0; $keys = array();
        foreach ( $cart->get_cart() as $key => $item ) { $total += $item['data']->price * $item['quantity']; $keys[] = $key; }
        $rates = molosoc_gift_shipping_rates( array( 'flat' => 1 ), array() );
        echo json_encode( array( $total, $keys, array_keys( $rates ), $rates['molosoc_gift_combined']->args[2], molosoc_gift_cart_link() ? 'linked' : 'unlinked' ) );
        """
        for lang, url in (("cz", "https://example.test/cz/pokladna/"), ("en", "https://example.test/checkout/")):
            for sizes, expected in ((["M"], 209), (["M", "L"], 408)):
                for held in ({"line425": 1}, {"line425": 1, "line999": 2}):
                    for session in ({}, paid_record({"line425": 1})):
                        post = dict(FORM, molosoc_gift_lang=lang, molosoc_gift_pairs=str(len(sizes)), molosoc_gift_size=sizes)
                        redirect, _, out = self.submit(post, {"cart": held, "session": session, "request_lang": lang})
                        label = (lang, sizes, held, session)
                        self.assertEqual(redirect, url, label)
                        cart = section(out, "CART")
                        self.assertEqual(len(cart), len(sizes), label)
                        self.assertTrue(all("s" in k[4:] for k in cart), label)
                        total, keys, rates, cost, linked = json.loads(run_php({"request_lang": lang, "cart": cart, "session": section(out, "SESSION")}, check))
                        self.assertEqual((total, cost, rates, linked), (expected, 0, ["molosoc_gift_combined"], "linked"), label)
                        parked = section(out, "SESSION")["molosoc_gift_parked_rows"]["rows"]
                        self.assertEqual({k: r["quantity"] for k, r in parked.items()}, held, label)

    def test_parked_rows_return_once_the_addon_checkout_is_no_longer_the_cart(self):
        parked = {"molosoc_gift_parked_rows": {"order_id": 77, "rows": {"line999": {"product_id": 999, "variation_id": 999, "variation": [], "quantity": 2, "extra": []}}}}
        # Still the valid gift cart: nothing moves.
        body = "molosoc_gift_maybe_unpark_rows(); echo json_encode( WC()->cart->items );"
        cart = dict(LINKED_CART)
        page = {"endpoint": False}  # the default scenario is an order-received request
        out = run_php(dict(page, cart=cart, session=dict(parked, molosoc_gift_parent=LINK)), body)
        self.assertEqual(json.loads(out), cart)
        # The shopper added something (link voided): parked rows come back, once.
        out = run_php(dict(page, cart=dict(cart, line424=1), session=dict(parked, molosoc_gift_parent=LINK)), body + "molosoc_gift_maybe_unpark_rows(); echo json_encode( WC()->session->get( 'molosoc_gift_parked_rows' ) );")
        items, gone = out[:out.index("}") + 1], out[out.index("}") + 1:]
        self.assertEqual(json.loads(items), dict(cart, line424=1, line999=2))
        self.assertEqual(gone, "null")
        # On an order-received page WooCommerce empties the cart: not here.
        body = "$GLOBALS['t']['endpoint'] = true; molosoc_gift_maybe_unpark_rows(); echo json_encode( WC()->cart->items );"
        self.assertEqual(json.loads(run_php({"cart": {}, "session": parked}, body)), [])
        # The add-on order's own Thank You page restores them; an ordinary order does not.
        body = "molosoc_gift_unpark_after_addon( %d ); echo json_encode( WC()->cart->items );"
        addon = {"meta": {"88": {"_molosoc_gift_parent_order": 77}}}
        self.assertEqual(json.loads(run_php(dict(addon, cart={}, session=parked), body % 88)), {"line999": 2})
        self.assertEqual(json.loads(run_php({"cart": {}, "session": parked}, body % 77)), [])

    def test_the_addon_checkout_does_not_overwrite_the_paid_row_record(self):
        # Codex P1 on #148: the add-on order runs the same hook with a gift-only cart.
        body = """
        WC()->cart->items = array( 'line425s2' => 1 );
        molosoc_gift_remember_paid_rows( 88 );
        echo json_encode( WC()->session->get( 'molosoc_gift_paid_rows' ) );
        """
        self.assertEqual(json.loads(run_php({"session": paid_record({"line425": 1})}, body)), paid_record({"line425": 1})["molosoc_gift_paid_rows"])
        # So the original paid pair is still not restored on the add-on Thank You page.
        parked = {"molosoc_gift_parked_rows": {"order_id": 77, "rows": {"line425": {"product_id": 364, "variation_id": 425, "variation": [], "quantity": 1, "extra": []}}}}
        addon = {"meta": {"88": {"_molosoc_gift_parent_order": 77}}}
        out = run_php(dict(addon, cart={}, session=dict(parked, **paid_record({"line425": 1}))), "molosoc_gift_unpark_after_addon( 88 ); echo json_encode( WC()->cart->items );")
        self.assertEqual(json.loads(out), [])

    def test_a_parked_row_woocommerce_refuses_is_kept_for_a_later_retry(self):
        # Codex P2 on #148: out of stock / validation filter must not lose the row.
        parked = {"molosoc_gift_parked_rows": {"order_id": 77, "rows": {"line999": {"product_id": 999, "variation_id": 999, "variation": [], "quantity": 2, "extra": []}}}}
        body = "molosoc_gift_unpark_rows(); echo json_encode( WC()->cart->items ), '|', json_encode( WC()->session->get( 'molosoc_gift_parked_rows' ) );"
        items, kept = run_php({"cart": {}, "session": parked, "fail_variation": 999}, body).split("|")
        self.assertEqual(json.loads(items), [])
        self.assertEqual(json.loads(kept), parked["molosoc_gift_parked_rows"])
        items, kept = run_php({"cart": {}, "session": parked}, body).split("|")
        self.assertEqual(json.loads(items), {"line999": 2})
        self.assertEqual(kept, "null")

    def test_a_new_flow_judges_an_earlier_orders_park_by_its_own_proof_instead_of_merging(self):
        # Codex P2 on #148: order 99's park (paid pair line425 + another row) must not
        # be relabelled as order 77's: 99's proof drops line425, the rest is re-parked.
        earlier = {"molosoc_gift_parked_rows": {"order_id": 99, "rows": {
            "line425": {"product_id": 364, "variation_id": 425, "variation": [], "quantity": 1, "extra": []},
            "line999": {"product_id": 999, "variation_id": 999, "variation": [], "quantity": 2, "extra": []}}}}
        session = dict(earlier, **paid_record({"line425": 1}, order_id=99))
        redirect, _, out = self.submit(dict(FORM), {"cart": {}, "session": session})
        self.assertEqual(redirect, "https://example.test/cz/pokladna/")
        parked = section(out, "SESSION")["molosoc_gift_parked_rows"]
        self.assertEqual(parked["order_id"], 77)
        self.assertEqual({k: r["quantity"] for k, r in parked["rows"].items()}, {"line999": 2})

    def test_another_addons_thank_you_page_leaves_a_newer_flows_parked_rows(self):
        # Codex P2 on #148: parked for order 99, but the Thank You page is the add-on of order 77.
        parked = {"molosoc_gift_parked_rows": {"order_id": 99, "rows": {"line999": {"product_id": 999, "variation_id": 999, "variation": [], "quantity": 2, "extra": []}}}}
        addon = {"meta": {"88": {"_molosoc_gift_parent_order": 77}}}
        body = "molosoc_gift_unpark_after_addon( 88 ); echo json_encode( WC()->cart->items ), '|', json_encode( WC()->session->get( 'molosoc_gift_parked_rows' ) );"
        items, kept = run_php(dict(addon, cart={}, session=parked), body).split("|")
        self.assertEqual(json.loads(items), [])
        self.assertEqual(json.loads(kept), parked["molosoc_gift_parked_rows"])

    def test_order_creation_records_the_rows_and_a_later_add_voids_the_record(self):
        body = """
        WC()->cart->items = array( 'line425' => 1, 'line999' => 2, 'line425s2' => 1 );
        molosoc_gift_remember_paid_rows( 77 );
        echo json_encode( WC()->session->get( 'molosoc_gift_paid_rows' ) ), '|';
        molosoc_gift_void_paid_rows_on_add( 'k', 364, 1, 424, array(), array( 'molosoc_gift_slot' => 2 ) );
        molosoc_gift_void_paid_rows_on_add( 'k', 999, 1, 0, array(), array() );
        molosoc_gift_void_paid_rows_on_quantity( 'line425', 1, 1 );
        echo json_encode( WC()->session->get( 'molosoc_gift_paid_rows' )['tainted'] ), '|';
        molosoc_gift_void_paid_rows_on_add( 'k', 364, 1, 425, array(), array() );
        echo json_encode( WC()->session->get( 'molosoc_gift_paid_rows' )['tainted'] );
        """
        recorded, after_noise, after_add = run_php({}, body).split("|")
        self.assertEqual(json.loads(recorded), {"order_id": 77, "rows": {"line425": {"variation": 425, "quantity": 1}}, "tainted": False})
        self.assertEqual(after_noise, "false")  # gift row, other product, unchanged quantity
        self.assertEqual(after_add, "true")
        body = "WC()->cart->items = array( 'line425' => 1 ); molosoc_gift_void_paid_rows_on_quantity( 'line425', 2, 1 ); echo json_encode( WC()->session->get( 'molosoc_gift_paid_rows' )['tainted'] );"
        self.assertEqual(run_php({"session": paid_record({"line425": 1})}, body), "true")

    def test_a_failed_submit_with_a_paid_row_and_an_own_stale_row_restores_both(self):
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        cart = {"line425": 1, "line425s2": 1}
        session = dict(self.owned({"line425s2": 1}), **paid_record({"line425": 1}))
        _, _, out = self.submit(post, {"cart": cart, "session": session, "fail_variation": 424})
        self.assertIn("REDIRECT:https://example.test/product-cz/", out)
        self.assertEqual(section(out, "CART"), cart)
        self.assertEqual(section(out, "SESSION"), session)

    def test_repeated_submission_ends_with_exactly_one_set_of_gift_rows(self):
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        redirect, _, out = self.submit(post, {"cart": {"line425": 1}, "session": paid_record({"line425": 1})})
        cart, session = section(out, "CART"), section(out, "SESSION")
        self.assertEqual(cart, {"line425s2": 1, "line424s3": 1})
        # Second submit (same session), also with the paid pair back in the cart.
        for again in (cart, dict(cart, line425=1)):
            redirect, _, out = self.submit(post, {"cart": again, "session": session})
            self.assertEqual(redirect, "https://example.test/cz/pokladna/")
            self.assertEqual(section(out, "CART"), {"line425s2": 1, "line424s3": 1})

    def test_a_gift_shaped_row_the_session_cannot_vouch_for_is_parked_not_merged(self):
        # A row with a gift marker whose quantity no longer matches the link is the
        # shopper's own: it is parked (returns as an ordinary row), so it can never
        # merge into a chosen gift row and inflate the add-on.
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        cart = {"line425s2": 2}
        redirect, _, out = self.submit(post, {"cart": cart, "session": self.owned(cart, lines={"line425s2": 1})})
        self.assertEqual(redirect, "https://example.test/cz/pokladna/")
        self.assertEqual(section(out, "CART"), {"line425s2": 1, "line424s3": 1})
        parked = section(out, "SESSION")["molosoc_gift_parked_rows"]["rows"]
        self.assertEqual({k: r["quantity"] for k, r in parked.items()}, cart)

    def test_an_invalid_submission_leaves_a_non_empty_cart_untouched(self):
        # The fallback still never changes the cart: validation happens before
        # any row is set aside.
        cart = {"line425": 2}
        for post in (dict(FORM, molosoc_gift_key="wc_order_wrong"), dict(FORM, molosoc_gift_size=["XL"]), dict(FORM, molosoc_gift_pairs="3")):
            redirect, added, out = self.submit(post, {"cart": cart})
            self.assertEqual(redirect, "https://example.test/product-cz/", post)
            self.assertEqual((added, section(out, "CART"), section(out, "SESSION")), ({}, cart, {}), post)

    def test_every_fallback_is_logged_without_the_order_key(self):
        _, _, out = self.submit(dict(FORM, molosoc_gift_size=["XL"]))
        log = section(out, "LOG")
        self.assertTrue(log and "size not available" in log[0])
        self.assertNotIn("wc_order_key77", out.split("LOG:")[1])

    def test_a_failed_replacement_add_restores_the_rows_it_would_have_dropped(self):
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        for cart in ({"line425s2": 1}, {"line425s2": 1, "line424s3": 1}):
            session = self.owned(cart)
            _, _, out = self.submit(post, {"cart": cart, "session": session, "fail_variation": 424})
            self.assertIn("REDIRECT:https://example.test/product-cz/", out, cart)
            self.assertEqual(section(out, "CART"), cart, cart)
            self.assertEqual(section(out, "SESSION"), session, cart)

    def test_a_failed_add_restores_a_stale_row_that_shares_a_key_with_its_replacement(self):
        # The stale slot-2 row has quantity 2; the replacement has the same key
        # (same size and pair number). A later pair fails: the original row, with
        # its original quantity, must come back, not the replacement.
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        _, _, out = self.submit(post, {"cart": {"line425s2": 2}, "session": self.owned({"line425s2": 2}), "fail_variation": 424})
        self.assertIn("REDIRECT:https://example.test/product-cz/", out)
        self.assertEqual(section(out, "CART"), {"line425s2": 2})

    def test_replacing_a_stale_row_is_not_refused_by_the_stock_check(self):
        # Only one unit left of M: the earlier submit's row is replaced, not
        # counted against the new add. Two of the same size need two in stock.
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"])
        redirect, _, out = self.submit(post, {"cart": {"line425s2": 1}, "session": self.owned({"line425s2": 1}), "stock": {"425": 1}})
        self.assertEqual(redirect, "https://example.test/cz/pokladna/")
        self.assertEqual(section(out, "CART"), {"line425s2": 1, "line424s3": 1})
        # A failed stock-checked add still leaves the cart as it was.
        _, _, out = self.submit(post, {"cart": {"line425s2": 1}, "session": self.owned({"line425s2": 1}), "stock": {"424": 0}})
        self.assertIn("REDIRECT:https://example.test/product-cz/", out)
        self.assertEqual(section(out, "CART"), {"line425s2": 1})

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
        # Another product's row is never touched (and nothing is added at all).
        _, _, out = self.submit(post, {"fail_variation": 424, "cart": {"line999": 1}})
        self.assertEqual(section(out, "CART"), {"line999": 1})
        self.assertEqual(section(out, "SESSION"), {})  # nothing parked on a failed submit
        # The paid pair is put back when a later pair fails.
        _, _, out = self.submit(post, {"fail_variation": 424, "cart": {"line425": 1}, "session": paid_record({"line425": 1})})
        self.assertIn("REDIRECT:https://example.test/product-cz/", out)
        self.assertEqual(section(out, "CART"), {"line425": 1})

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
class LanguageSwitchAndFlow(unittest.TestCase):
    """Issue #125 retest: the Thank You language switch must not open an empty
    checkout, and the whole flow (form -> cart -> checkout -> priced cart)
    is driven through the real handler and pricing hooks."""

    SWITCH = "echo molosoc_thankyou_language_switcher_link( 'https://example.test/pokladna/', '%s' );"

    def test_switch_keeps_the_order_received_context_in_both_directions(self):
        self.assertEqual(
            run_php({"request_lang": "en"}, self.SWITCH % "cz", get=KEY),
            "https://example.test/cz/pokladna/order-received/77/?key=wc_order_key77",
        )
        self.assertEqual(
            run_php({"request_lang": "cz"}, self.SWITCH % "en", get=KEY),
            "https://example.test/checkout/order-received/77/?key=wc_order_key77",
        )

    def test_switch_keeps_order_context_while_the_gateway_return_is_still_pending(self):
        # Status gate applies to the gift offer, not to the switcher link.
        self.assertEqual(
            run_php({"request_lang": "en", "status": {"77": "pending"}}, self.SWITCH % "cz", get=KEY),
            "https://example.test/cz/pokladna/order-received/77/?key=wc_order_key77",
        )
        self.assertEqual(
            run_php({"request_lang": "en", "status": {"77": "pending"}}, "echo json_encode( molosoc_thankyou_order() );", get=KEY).strip(),
            "null",
        )

    def test_switch_is_untouched_off_the_thank_you_page_or_without_the_key(self):
        self.assertEqual(run_php({"endpoint": False}, self.SWITCH % "cz", get=KEY), "https://example.test/pokladna/")
        self.assertEqual(run_php({}, self.SWITCH % "cz", get={"key": "wc_order_wrong"}), "https://example.test/pokladna/")
        self.assertEqual(run_php({}, self.SWITCH % "cz", get={}), "https://example.test/pokladna/")

    def test_switch_never_leaks_the_key_into_another_orders_url(self):
        out = run_php({"request_lang": "en"}, self.SWITCH % "cz", get=KEY)
        self.assertNotIn("wc_order_key88", out)

    def test_form_to_checkout_to_priced_cart_end_to_end(self):
        # Post-purchase cart still holds the pair just bought. Submit +2 (M, L),
        # then run the checkout-side hooks on the resulting cart/session.
        body = """
        $GLOBALS['t']['cart_after'] = null;
        molosoc_gift_add_to_cart_action();
        """
        post = dict(FORM, molosoc_gift_pairs="2", molosoc_gift_size=["M", "L"], molosoc_gift_lang="en")
        out = run_php({"request_lang": "en", "cart": {}}, body, post=post)
        self.assertIn("REDIRECT:https://example.test/checkout/\n", out)
        self.assertEqual(section(out, "CART"), {"line425s2": 1, "line424s3": 1})
        # Same session, next request: the cart is linked, priced 209 / 199 and
        # ships free; the page never went through the product URL.
        session = section(out, "SESSION")
        check = """
        $cart = WC()->cart;
        molosoc_gift_apply_prices( $cart );
        $prices = array();
        foreach ( $cart->get_cart() as $key => $item ) { $prices[ $key ] = $item['data']->price; }
        echo json_encode( $prices ), '|';
        $rates = molosoc_gift_shipping_rates( array( 'flat' => 1, 'pickup' => 2 ), array() );
        echo json_encode( array_keys( $rates ) ), '|', $rates['molosoc_gift_combined']->args[2];
        """
        out = run_php({"request_lang": "en", "cart": {"line425s2": 1, "line424s3": 1}, "session": session}, check)
        prices, rates, cost = out.split("|")
        self.assertEqual(json.loads(prices), {"line425s2": 209, "line424s3": 199})
        self.assertEqual(json.loads(rates), ["molosoc_gift_combined"])
        self.assertEqual(float(cost), 0)

    def test_price_bypass_attempts_get_no_offer_price(self):
        # A forged session link for another key, or a cart with a different row
        # set, prices nothing at the offer price and keeps normal shipping.
        check = """
        $cart = WC()->cart;
        molosoc_gift_apply_prices( $cart );
        $prices = array();
        foreach ( $cart->get_cart() as $key => $item ) { $prices[ $key ] = $item['data']->price; }
        echo json_encode( $prices );
        """
        forged = {"molosoc_gift_parent": dict(LINK, key="wc_order_forged")}
        out = run_php({"cart": LINKED_CART, "session": forged}, check)
        self.assertEqual(json.loads(out), {"line425s2": 229, "line424s3": 229})
        # A row the link does not name — even gift-shaped, even a third pair —
        # voids the offer for the whole cart (#145): nothing is discounted.
        extra = {"line425s2": 1, "line424s3": 1, "line425s3": 1}
        out = run_php({"cart": extra, "session": {"molosoc_gift_parent": LINK}}, check)
        self.assertEqual(set(json.loads(out).values()), {229})
        # A gift row removed or changed after the form: no row is discounted.
        for cart in ({"line425s2": 1, "line999": 1}, {"line425s2": 2, "line424s3": 1}):
            out = run_php({"cart": cart, "session": {"molosoc_gift_parent": LINK}}, check)
            self.assertEqual(set(json.loads(out).values()), {229}, cart)


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
        # (the order-processed hooks only record the paid cart rows in the session)
        for tag in ("woocommerce_order_status_on-hold", "woocommerce_checkout_order_created"):
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

    MIXED = {"line999": 2, "line425": 1, "line425s2": 1, "line424s3": 1}  # other product + the pair just bought + 2 gift rows

    PACKAGES = """
    $contents = array();
    foreach ( WC()->cart->get_cart() as $key => $item ) { $contents[ $key ] = array( 'quantity' => $item['quantity'], 'line_total' => 229 * $item['quantity'] ); }
    $packages = molosoc_gift_shipping_package_state( array( array( 'contents' => $contents, 'destination' => array( 'country' => 'CZ' ) ) ) );
    $rates = array( 'flat_rate:1' => 'normal', 'zasilkovna' => 'pickup' );
    $res = array();
    foreach ( $packages as $package ) {
        $out = molosoc_gift_shipping_rates( $rates, $package );
        $res[] = array(
            'keys'  => array_keys( $package['contents'] ),
            'cost'  => $package['contents_cost'],
            'state' => $package['molosoc_gift_parent'],
            'rates' => array_map( function ( $r ) { return $r instanceof WC_Shipping_Rate ? $r->args : $r; }, $out ),
        );
    }
    echo json_encode( $res );
    """

    def test_gift_only_cart_ships_free_in_one_package(self):
        pure = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART}, self.PACKAGES))
        self.assertEqual(len(pure), 1)
        self.assertEqual(list(pure[0]["rates"]), ["molosoc_gift_combined"])
        self.assertEqual(pure[0]["state"], 77)
        for lang, label in (("cz", "Pošleme s objednávkou č. 77 — bez dalšího poštovného"), ("en", "Ships with order #77 — no additional shipping")):
            out = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART, "request_lang": lang}, self.PACKAGES))
            self.assertEqual(out[0]["rates"]["molosoc_gift_combined"][1], label, lang)
            self.assertEqual(out[0]["rates"]["molosoc_gift_combined"][2], 0, lang)

    def test_any_extra_row_in_the_addon_checkout_voids_the_offer_entirely(self):
        # Issue #145: if the paid pair (or anything else) is in the cart beside
        # the gift rows, isolation isn't guaranteed: no offer price, no free
        # shipping, no stamp — an honest normal cart, never a misleading total.
        normal = {"flat_rate:1": "normal", "zasilkovna": "pickup"}
        for extra in ({"line425": 1}, {"line999": 2}, {"line424": 1, "line999": 1}):
            cart = dict(LINKED_CART, **extra)
            session = {"molosoc_gift_parent": LINK}
            self.assertEqual(json.loads(run_php({"session": session, "cart": cart}, OfferPricing.PRICES)), {k: 229 for k in cart}, extra)
            out = json.loads(run_php({"session": session, "cart": cart}, self.PACKAGES))
            self.assertEqual(len(out), 1, extra)
            self.assertEqual((out[0]["rates"], out[0]["state"]), (normal, 0), extra)
            self.assertEqual(json.loads(run_php({"session": session, "cart": cart}, self.RATES)), normal, extra)

    def test_order_with_an_extra_row_is_not_stamped_as_a_gift_add_on(self):
        body = """
        $new = wc_get_order( 88 );
        molosoc_gift_stamp_new_order( $new );
        echo json_encode( $new->meta );
        """
        meta = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": self.MIXED}, body))
        self.assertNotIn("_molosoc_gift_parent_order", meta)

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
def self_link(slots):
    return dict(LINK, lines={k: 1 for k in slots}, slots=slots)


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
        # The offer prices never go through the product or a coupon.
        src = GIFT.read_text(encoding="utf-8")
        self.assertIn("'woocommerce_before_calculate_totals'", src)
        self.assertNotIn("add_filter( 'woocommerce_product", src)

    def test_prices_are_restored_when_the_link_stops_holding_between_passes(self):
        body = """
        molosoc_gift_apply_prices( WC()->cart );
        $first = array();
        foreach ( WC()->cart->get_cart() as $k => $i ) { $first[ $k ] = $i['data']->price; }
        $GLOBALS['t']['status']['77'] = 'completed';
        molosoc_gift_apply_prices( WC()->cart );
        $second = array();
        foreach ( WC()->cart->get_cart() as $k => $i ) { $second[ $k ] = $i['data']->price; }
        echo json_encode( array( $first, $second ) );
        """
        first, second = json.loads(run_php({"session": {"molosoc_gift_parent": LINK}, "cart": LINKED_CART}, body))
        self.assertEqual(first, {"line425s2": 209, "line424s3": 199})
        self.assertEqual(second, {"line425s2": 229, "line424s3": 229})

    def test_audit_pricing_lists_only_pairs_actually_purchased(self):
        body = """
        $new = wc_get_order( 88 );
        molosoc_gift_stamp_new_order( $new );
        echo json_encode( $new->meta );
        """
        meta = json.loads(run_php({"session": {"molosoc_gift_parent": self_link({"line425s2": 2})}, "cart": {"line425s2": 1}}, body))
        self.assertEqual(json.loads(meta["_molosoc_gift_parent_order_pricing"]), {"2": 209})

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
