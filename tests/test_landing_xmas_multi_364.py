"""Issue #364: Christmas landing CZ + EN — "4 a více párů / 4 or more pairs" card
with M/L counters (4..10 pairs). Runs inc/landing-xmas.php under php-cli with
minimal WordPress/WooCommerce stand-ins (no WP install): pricing 209 + 199 x
(n-1) up to 10, the clamped max, parse_sizes 1..10, the aggregate per-variation
stock check that leaves the cart untouched, the all-or-nothing rollback, cart
re-ranking and gift-slot isolation. Static pins cover the template and JS."""
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
INC_PATH = ROOT / "inc/landing-xmas.php"
PART_PATH = ROOT / "template-parts/landing-xmas.php"
INC = INC_PATH.read_text(encoding="utf-8")
PART = PART_PATH.read_text(encoding="utf-8")
JS = (ROOT / "assets/js/landing-xmas.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-xmas.css").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")
DOC = (REPO / "docs/christmas-gift-251.md").read_text(encoding="utf-8")
HAVE_PHP = shutil.which("php") is not None


def strip_comments(src):
    return re.sub(r"/\*.*?\*/", "", src, flags=re.S)


JS_CODE = strip_comments(JS)

# Minimal WordPress + WooCommerce stand-ins. Stock: M variation 101, L variation
# 102 (overridable per test via $GLOBALS['stock'] / $GLOBALS['any_size']).
STUBS = r"""
define( 'ABSPATH', '/' );
define( 'MOLOSOC_PRODUCT_ID', 364 );
$GLOBALS['filters'] = array();
$GLOBALS['stock'] = array( 101 => 50, 102 => 50 );
$GLOBALS['managed'] = true;
$GLOBALS['any_size'] = false;
$GLOBALS['sold_out'] = array();
class Redirect extends Exception {}
function add_action() {}
function add_filter( $tag, $fn = null ) {}
function apply_filters( $tag, $value ) { return isset( $GLOBALS['filters'][ $tag ] ) ? call_user_func( $GLOBALS['filters'][ $tag ], $value ) : $value; }
function is_page() { return false; }
function is_admin() { return false; }
function home_url( $p = '' ) { return 'https://molosoc.test' . $p; }
function get_page_by_path() { return null; }
function wc_get_checkout_url() { return 'https://molosoc.test/checkout/'; }
function molosoc_product_url( $lang ) { return 'https://molosoc.test/product/'; }
function wp_safe_redirect( $url ) { throw new Redirect( $url ); }
function wp_unslash( $v ) { return $v; }
function sanitize_key( $k ) { return preg_replace( '/[^a-z0-9_\-]/', '', strtolower( (string) $k ) ); }
function wp_parse_str( $s, &$out ) { parse_str( $s, $out ); }
function wp_parse_url( $u, $c = -1 ) { return parse_url( $u, $c ); }
function add_query_arg( $args, $url ) { return $url . ( false === strpos( $url, '?' ) ? '?' : '&' ) . http_build_query( $args ); }
function molosoc_landing_b_buy_links() {
	$m = $GLOBALS['any_size'] ? 100 : 101;
	$l = $GLOBALS['any_size'] ? 100 : 102;
	$out = array();
	if ( ! in_array( 'M', $GLOBALS['sold_out'], true ) ) {
		$out['M'] = array( 'direct' => true, 'url' => "https://molosoc.test/checkout/?add-to-cart=364&variation_id=$m&attribute_pa_velikost=m" );
	}
	if ( ! in_array( 'L', $GLOBALS['sold_out'], true ) ) {
		$out['L'] = array( 'direct' => true, 'url' => "https://molosoc.test/checkout/?add-to-cart=364&variation_id=$l&attribute_pa_velikost=l" );
	}
	return $out;
}
class FakeVariation {
	public $id; public $price = 229; public $meta = array();
	function __construct( $id ) { $this->id = $id; }
	function is_purchasable() { return true; }
	function is_in_stock() { return $this->qty() > 0 || ! $GLOBALS['managed']; }
	function managing_stock() { return $GLOBALS['managed']; }
	function backorders_allowed() { return false; }
	function qty() { return isset( $GLOBALS['stock'][ $this->id ] ) ? $GLOBALS['stock'][ $this->id ] : 0; }
	function get_stock_quantity() { return $this->qty(); }
	function get_meta( $k ) { return isset( $this->meta[ $k ] ) ? $this->meta[ $k ] : ''; }
	function update_meta_data( $k, $v ) { $this->meta[ $k ] = $v; }
	function get_price() { return $this->price; }
	function set_price( $p ) { $this->price = $p; }
}
function wc_get_product( $id ) { return new FakeVariation( $id ); }
class FakeCart {
	public $items = array(); public $n = 0; public $fail_at = 0; public $adds = 0;
	function get_cart() { return $this->items; }
	function get_cart_contents() { return $this->items; }
	function set_cart_contents( $c ) { $this->items = $c; }
	function remove_cart_item( $k ) { unset( $this->items[ $k ] ); }
	function calculate_totals() {}
	function set_session() {}
	function add_to_cart( $pid, $qty, $vid, $attrs, $data ) {
		$this->adds++;
		if ( $this->fail_at && $this->adds === $this->fail_at ) { return false; }
		$used = 0;
		foreach ( $this->items as $i ) { if ( $i['variation_id'] === $vid ) { $used += $i['quantity']; } }
		if ( $GLOBALS['managed'] && $used + $qty > ( isset( $GLOBALS['stock'][ $vid ] ) ? $GLOBALS['stock'][ $vid ] : 0 ) ) { return false; }
		$key = 'k' . ( ++$this->n );
		$this->items[ $key ] = array_merge( array( 'product_id' => $pid, 'variation_id' => $vid, 'quantity' => $qty, 'data' => new FakeVariation( $vid ) ), $data );
		return $key;
	}
}
$GLOBALS['cart'] = new FakeCart();
class FakeWC { public $cart; }
function WC() { $w = new FakeWC(); $w->cart = $GLOBALS['cart']; return $w; }
"""


def php(code):
    src = "<?php\n" + STUBS + "\nrequire '" + str(INC_PATH) + "';\n" + code
    return subprocess.run(["php", "-d", "display_errors=stderr", "-r", "?>" + src], capture_output=True, text=True, check=True).stdout


def j(code):
    return json.loads(php(code))


def add(sizes, pre=""):
    """Run molosoc_xmas_add_to_cart() for `sizes`; returns redirect + cart lines."""
    return j(pre + r"""
$_GET = array( 'molosoc_xmas' => '1', 'molosoc_xmas_sizes' => '%s' );
$to = '';
try { molosoc_xmas_add_to_cart(); } catch ( Redirect $r ) { $to = $r->getMessage(); }
$lines = array();
foreach ( $GLOBALS['cart']->items as $k => $i ) {
	$lines[] = array( 'key' => $k, 'vid' => $i['variation_id'], 'qty' => $i['quantity'], 'slot' => isset( $i['molosoc_xmas_slot'] ) ? $i['molosoc_xmas_slot'] : null, 'gift' => isset( $i['molosoc_gift_slot'] ) );
}
echo json_encode( array( 'to' => $to, 'lines' => $lines ) );
""" % sizes)


def totals_after(sizes, pre=""):
    """Add `sizes`, run the price hook and return the cart total and per-line prices."""
    return j(pre + r"""
$_GET = array( 'molosoc_xmas' => '1', 'molosoc_xmas_sizes' => '%s' );
try { molosoc_xmas_add_to_cart(); } catch ( Redirect $r ) {}
molosoc_xmas_apply_prices( $GLOBALS['cart'] );
$p = array();
foreach ( $GLOBALS['cart']->items as $i ) { $p[] = $i['data']->get_price(); }
echo json_encode( array( 'total' => array_sum( $p ), 'prices' => $p ) );
""" % sizes)


TOTALS = {1: 209, 2: 408, 3: 607, 4: 806, 5: 1005, 6: 1204, 7: 1403, 8: 1602, 9: 1801, 10: 2000}


@unittest.skipUnless(HAVE_PHP, "php not installed")
class ServerPricing(unittest.TestCase):
    def test_bundle_totals_1_to_10(self):
        got = j("$o = array(); for ( $n = 1; $n <= 10; $n++ ) { $o[ $n ] = molosoc_xmas_bundle_total( $n ); } echo json_encode( $o );")
        self.assertEqual({int(k): v for k, v in got.items()}, TOTALS)

    def test_unit_prices_209_then_199(self):
        got = j("echo json_encode( molosoc_xmas_unit_prices() );")
        self.assertEqual(got, {"1": 209, **{str(n): 199 for n in range(2, 11)}})

    def test_max_pairs_default_and_clamp(self):
        self.assertEqual(php("echo molosoc_xmas_max_pairs();"), "10")
        for value, want in (("50", "10"), ("1", "3"), ("6", "6"), ("'x'", "3")):
            out = php("$GLOBALS['filters']['molosoc_xmas_max_pairs'] = function () { return %s; }; echo molosoc_xmas_max_pairs();" % value)
            self.assertEqual(out, want, value)

    def test_bad_price_filter_is_rejected(self):
        for bad in ("array( 1 => 209, 2 => 199, 3 => 199 )",  # old 3-slot filter: slots 4..10 missing
                    "array_fill( 1, 10, 0 )", "'nope'", "array_fill( 1, 10, -5 )"):
            got = j("$GLOBALS['filters']['molosoc_xmas_unit_prices'] = function () { return %s; }; echo json_encode( molosoc_xmas_unit_prices() );" % bad)
            self.assertEqual(got["1"], 209, bad)
            self.assertEqual(got["10"], 199, bad)

    def test_parse_sizes(self):
        cases = {
            "M": ["M"], "m, l ,M": ["M", "L", "M"], ",".join("M" * 10): ["M"] * 10,
            ",".join("M" * 11): [], "M,X": [], "": [], "M,,L": [], "XL": [],
        }
        for raw, want in cases.items():
            self.assertEqual(j("echo json_encode( molosoc_xmas_parse_sizes( %s ) );" % json.dumps(raw)), want, raw)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class ServerAddToCart(unittest.TestCase):
    def test_4_5_10_pairs_one_line_per_pair_and_totals(self):
        for sizes, n in (("M,M,M,M", 4), ("M,M,M,L,L", 5), (",".join(["M"] * 6 + ["L"] * 4), 10)):
            out = add(sizes)
            self.assertEqual(out["to"], "https://molosoc.test/checkout/", sizes)
            self.assertEqual([l["slot"] for l in out["lines"]], list(range(1, n + 1)))
            self.assertTrue(all(l["qty"] == 1 for l in out["lines"]))
            self.assertEqual(totals_after(sizes)["total"], TOTALS[n], sizes)

    def test_1_2_3_pairs_unchanged(self):
        for sizes, n in (("M", 1), ("M,L", 2), ("L,L,M", 3)):
            self.assertEqual(totals_after(sizes)["total"], TOTALS[n])

    def test_mixed_sizes_map_to_their_variations(self):
        out = add("M,M,M,L,L")
        self.assertEqual([l["vid"] for l in out["lines"]], [101, 101, 101, 102, 102])

    def test_11_sizes_and_invalid_size_go_to_product_page_untouched(self):
        for sizes in (",".join(["M"] * 11), "M,M,M,XL", "M,S"):
            out = add(sizes)
            self.assertEqual(out["to"], "https://molosoc.test/product/", sizes)
            self.assertEqual(out["lines"], [])

    def test_aggregate_stock_shortfall_keeps_cart_and_explains(self):
        # M has 5 left: 8 x M must be refused BEFORE anything is removed or added.
        pre = r"""$GLOBALS['stock'][101] = 5;
$GLOBALS['cart']->items['old'] = array( 'product_id' => 364, 'variation_id' => 102, 'quantity' => 1, 'molosoc_xmas_slot' => 1, 'data' => new FakeVariation( 102 ) );
$GLOBALS['cart']->items['other'] = array( 'product_id' => 50, 'variation_id' => 0, 'quantity' => 2, 'data' => new FakeVariation( 0 ) );
"""
        out = add(",".join(["M"] * 8 + ["L"] * 2), pre)
        self.assertIn("lpx_stock=m", out["to"])
        self.assertIn("lpx_left=5", out["to"])
        self.assertTrue(out["to"].endswith("#lpx-bundle"))
        self.assertEqual([l["key"] for l in out["lines"]], ["old", "other"])  # original cart preserved
        self.assertEqual(php(pre + "echo $GLOBALS['cart']->adds;"), "0")

    def test_stock_counts_other_lines_of_the_same_variation(self):
        # 6 M in stock, 2 M already in the cart as normal lines -> only 4 left for the bundle.
        pre = r"""$GLOBALS['stock'][101] = 6;
$GLOBALS['cart']->items['normal'] = array( 'product_id' => 364, 'variation_id' => 101, 'quantity' => 2, 'data' => new FakeVariation( 101 ) );
"""
        out = add("M,M,M,M,M", pre)
        self.assertIn("lpx_stock=m", out["to"])
        self.assertIn("lpx_left=4", out["to"])
        self.assertEqual(len(out["lines"]), 1)
        self.assertEqual(add("M,M,M,M", pre)["to"], "https://molosoc.test/checkout/")

    def test_any_size_variation_counts_m_and_l_together(self):
        pre = "$GLOBALS['any_size'] = true; $GLOBALS['stock'][100] = 9;\n"
        out = add(",".join(["M"] * 8 + ["L"] * 2), pre)
        self.assertIn("lpx_stock=any", out["to"])
        self.assertIn("lpx_left=9", out["to"])
        self.assertEqual(out["lines"], [])
        self.assertEqual(add(",".join(["M"] * 7 + ["L"] * 2), pre)["to"], "https://molosoc.test/checkout/")

    def test_sold_out_size(self):
        out = add("M,M,L,L", "$GLOBALS['sold_out'] = array( 'L' );\n")
        self.assertIn("lpx_stock=l", out["to"])
        self.assertIn("lpx_left=0", out["to"])
        self.assertEqual(out["lines"], [])

    def test_unmanaged_stock_is_not_capped(self):
        self.assertEqual(add(",".join(["M"] * 10), "$GLOBALS['managed'] = false;\n")["to"], "https://molosoc.test/checkout/")

    def test_failed_add_rolls_back_everything(self):
        pre = r"""$GLOBALS['cart']->fail_at = 4;
$GLOBALS['cart']->items['old'] = array( 'product_id' => 364, 'variation_id' => 101, 'quantity' => 1, 'molosoc_xmas_slot' => 1, 'data' => new FakeVariation( 101 ) );
"""
        out = add("M,M,M,L,L", pre)
        self.assertIn("lpx_stock=add", out["to"])
        self.assertEqual([l["key"] for l in out["lines"]], ["old"])

    def test_restacking_replaces_earlier_christmas_lines(self):
        pre = r"""$GLOBALS['cart']->items['old'] = array( 'product_id' => 364, 'variation_id' => 101, 'quantity' => 1, 'molosoc_xmas_slot' => 1, 'data' => new FakeVariation( 101 ) );
"""
        out = add("L,L,L,L,L", pre)
        self.assertEqual([l["vid"] for l in out["lines"]], [102] * 5)


@unittest.skipUnless(HAVE_PHP, "php not installed")
class ServerRepricing(unittest.TestCase):
    def test_removal_repacks_ranks_and_gift_rows_untouched(self):
        got = j(r"""
$_GET = array( 'molosoc_xmas' => '1', 'molosoc_xmas_sizes' => 'M,M,M,L,L' );
try { molosoc_xmas_add_to_cart(); } catch ( Redirect $r ) {}
$gift = new FakeVariation( 101 ); $gift->price = 99;
$GLOBALS['cart']->items['gift'] = array( 'product_id' => 364, 'variation_id' => 101, 'quantity' => 1, 'molosoc_gift_slot' => 1, 'molosoc_xmas_slot' => 9, 'data' => $gift );
unset( $GLOBALS['cart']->items['k1'] ); // remove the 209 Kč line
molosoc_xmas_apply_prices( $GLOBALS['cart'] );
$p = array();
foreach ( $GLOBALS['cart']->items as $k => $i ) { $p[ $k ] = $i['data']->get_price(); }
echo json_encode( $p );
""")
        self.assertEqual(got, {"k2": 209, "k3": 199, "k4": 199, "k5": 199, "gift": 99})

    def test_lines_beyond_max_fall_back_to_base_price(self):
        got = j(r"""
$GLOBALS['filters']['molosoc_xmas_max_pairs'] = function () { return 4; };
for ( $s = 1; $s <= 6; $s++ ) {
	$GLOBALS['cart']->items[ 'k' . $s ] = array( 'product_id' => 364, 'variation_id' => 101, 'quantity' => 1, 'molosoc_xmas_slot' => $s, 'data' => new FakeVariation( 101 ) );
}
molosoc_xmas_apply_prices( $GLOBALS['cart'] );
$p = array(); foreach ( $GLOBALS['cart']->items as $i ) { $p[] = $i['data']->get_price(); }
echo json_encode( $p );
""")
        self.assertEqual(got, [209, 199, 199, 199, 229, 229])


@unittest.skipUnless(HAVE_PHP, "php not installed")
class StockMessages(unittest.TestCase):
    def msg(self, lang, size, left):
        return php("echo molosoc_xmas_stock_message( '%s', '%s', %d );" % (lang, size, left))

    def test_czech_plural_and_actionable(self):
        self.assertEqual(self.msg("cz", "M", 5), "Velikosti M máme skladem jen 5 párů. Vyberte prosím méně párů velikosti M a zkuste to znovu.")
        self.assertIn("jen 3 páry", self.msg("cz", "L", 3))
        self.assertIn("jen 1 pár.", self.msg("cz", "L", 1))
        self.assertIn("vyprodaná", self.msg("cz", "M", 0))
        self.assertIn("méně párů", self.msg("cz", "", -1))

    def test_english(self):
        self.assertEqual(self.msg("en", "M", 5), "Only 5 pairs of size M left in stock. Please choose fewer pairs of size M and try again.")
        self.assertIn("sold out", self.msg("en", "L", 0))
        self.assertIn("fewer pairs", self.msg("en", "", -1))

    def test_notice_reads_only_whitelisted_codes(self):
        self.assertEqual(php("$_GET = array( 'lpx_stock' => '<script>', 'lpx_left' => '3' ); echo molosoc_xmas_stock_notice( 'cz' );"), "")
        self.assertIn("jen 10 párů", php("$_GET = array( 'lpx_stock' => 'M', 'lpx_left' => '999' ); echo molosoc_xmas_stock_notice( 'cz' );"))
        self.assertEqual(php("$_GET = array(); echo molosoc_xmas_stock_notice( 'en' );"), "")


class TemplateAndCopy(unittest.TestCase):
    def test_fourth_card_teaser_and_counters(self):
        self.assertIn("'multi'     => '4 a více párů',", PART)
        self.assertIn("'multi'     => '4 or more pairs',", PART)
        self.assertIn("'teaser'    => 'Kupujete pro víc lidí? Vyberte 4 a více párů – každý další pár jen za %s.',", PART)
        self.assertIn("'teaser'    => 'Buying for several people? Choose 4 or more pairs – every extra pair just %s.',", PART)
        self.assertIn("'min_err'   => 'Vyberte alespoň %d páry.',", PART)
        self.assertIn("'min_err'   => 'Choose at least %d pairs.',", PART)
        self.assertIn('value="multi"', PART)
        self.assertIn("data-lpx-multi hidden", PART)
        self.assertIn('data-lpx-max="<?php echo (int) $lpx_max; ?>"', PART)
        self.assertIn("data-lpx-counter=", PART)
        self.assertIn('data-lpx-step="-1"', PART)
        self.assertIn('data-lpx-step="1"', PART)
        self.assertIn("aria-live=\"polite\"", PART)

    def test_1_2_3_cards_and_rows_kept(self):
        self.assertIn("'pairs'     => array( 1 => '1 pár', 2 => '2 páry', 3 => '3 páry' ),", PART)
        self.assertIn("foreach ( array( 1, 2, 3 ) as $n ) :", PART)

    def test_sold_out_size_disables_its_counter(self):
        self.assertIn("$lpx_off = $lpx_buyable && ! isset( $lpx_avail[ $key ] );", PART)
        self.assertIn("<?php echo $lpx_off ? ' disabled' : ''; ?>>−</button>", PART)

    def test_meta_descriptions(self):
        meta = INC[INC.index("function molosoc_xmas_meta"):INC.index("pre_get_document_title")]
        self.assertIn("Vyberte 1 až 10 párů.", meta)
        self.assertIn("Pick 1 to 10 pairs.", meta)
        self.assertNotIn("1, 2 nebo 3 páry", meta)
        self.assertNotIn("1, 2 or 3 pairs", meta)

    def test_tap_targets_44px(self):
        btn = re.search(r"\.lpx-counter__btn \{([^}]*)\}", CSS).group(1)
        self.assertIn("width: 44px", btn)
        self.assertIn("height: 44px", btn)

    def test_theme_version_bumped_and_documented(self):
        version = tuple(int(v) for v in re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M).groups())
        self.assertGreaterEqual(version, (0, 2, 122))
        self.assertIn("Issue #364", DOC)


class Script(unittest.TestCase):
    def test_no_hard_coded_three_and_reads_limits(self):
        self.assertNotIn("n <= 3", JS_CODE)
        self.assertIn('limit( group, "data-lpx-max", 10 )', JS_CODE)
        self.assertIn('limit( group, "data-lpx-min", 4 )', JS_CODE)

    def test_no_prices_in_js(self):
        self.assertNotRegex(JS_CODE, r"price|209|199|607|408|806|1005|2000")

    def test_counters_expand_to_the_same_url_contract(self):
        self.assertIn('sizes.push( box.getAttribute( "data-lpx-counter" ) );', JS_CODE)
        self.assertIn('"molosoc_xmas=1&molosoc_xmas_sizes=" + encodeURIComponent( sizes.join( "," ) )', JS_CODE)

    def test_sync_copies_mode_and_counters(self):
        fn = JS_CODE[JS_CODE.index("function sync"):JS_CODE.index("groups.forEach( function ( group ) {\n\t\trender")]
        self.assertIn("var picked = mode( source );", fn)
        self.assertIn("setQty( counter( g, box.getAttribute( \"data-lpx-counter\" ) ), qtyOf( box ) );", fn)

    def test_busy_lock_and_bfcache_kept(self):
        self.assertIn("if ( busy ) {", JS_CODE)
        self.assertIn("e.persisted", JS_CODE)


if __name__ == "__main__":
    unittest.main()
