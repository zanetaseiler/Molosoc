<?php
// Issue #378: minimal WordPress stubs that render a landing page template (body) or
// its head output. Usage: php landing_bf_stub_378.php <page-template-file> <slug> [body|head] [molosoc_lp]
define( 'ABSPATH', '/' );
define( 'MOLOSOC_PRODUCT_ID', 364 );
$THEME = __DIR__ . '/../../site/theme'; $TPL = $argv[1]; $SLUG = $argv[2]; $MODE = $argv[3] ?? 'body';
if ( ! empty( $argv[4] ) ) { $_GET['molosoc_lp'] = $argv[4]; }
$GLOBALS['F'] = array(); $GLOBALS['A'] = array();
function add_filter( $h, $cb, $p = 10, $n = 1 ) { $GLOBALS['F'][ $h ][ $p ][] = array( $cb, $n ); return true; }
function add_action( $h, $cb, $p = 10, $n = 1 ) { return add_filter( $h, $cb, $p, $n ); }
function apply_filters( $h, $v, ...$args ) { if ( empty( $GLOBALS['F'][ $h ] ) ) return $v; ksort( $GLOBALS['F'][ $h ] ); foreach ( $GLOBALS['F'][ $h ] as $cbs ) foreach ( $cbs as $c ) { $v = call_user_func_array( $c[0], array_slice( array_merge( array( $v ), $args ), 0, $c[1] ) ); } return $v; }
function do_action( $h, ...$args ) { if ( empty( $GLOBALS['F'][ $h ] ) ) return; ksort( $GLOBALS['F'][ $h ] ); foreach ( $GLOBALS['F'][ $h ] as $cbs ) foreach ( $cbs as $c ) call_user_func_array( $c[0], array_slice( $args, 0, $c[1] ) ); }
function esc_html( $s ) { return htmlspecialchars( (string) $s, ENT_QUOTES, 'UTF-8' ); }
function esc_attr( $s ) { return htmlspecialchars( (string) $s, ENT_QUOTES, 'UTF-8' ); }
function esc_url( $s ) { return htmlspecialchars( (string) $s, ENT_QUOTES, 'UTF-8' ); }
function number_format_i18n( $n ) { return number_format( (float) $n, 0, ',', "\u{00a0}" ); }
function wp_json_encode( $v ) { return json_encode( $v, JSON_UNESCAPED_UNICODE ); }
function get_stylesheet_directory() { return $GLOBALS['THEME']; }
function get_stylesheet_directory_uri() { return 'https://molosoc.com/wp-content/themes/molosoc'; }
function home_url( $p = '/' ) { return 'https://molosoc.com' . $p; }
function is_page( $slug ) { return $slug === $GLOBALS['SLUG']; }
function is_admin() { return false; }
function get_page_by_path( $s ) { return null; }
function get_post_status( $p ) { return 'publish'; }
function get_permalink( $p ) { return 'https://molosoc.com/x/'; }
function get_queried_object_id() { return 0; }
function sanitize_key( $k ) { return strtolower( preg_replace( '/[^a-z0-9_\-]/i', '', $k ) ); }
function wp_unslash( $v ) { return $v; }
function wp_parse_url( $u, $c = -1 ) { return parse_url( $u, $c ); }
function wp_parse_str( $s, &$o ) { parse_str( (string) $s, $o ); }
function add_query_arg( $k, $v = null, $u = null ) { if ( is_array( $k ) ) { $u = $v; $q = $k; } else { $q = array( $k => $v ); } return $u . ( strpos( $u, '?' ) === false ? '?' : '&' ) . http_build_query( $q ); }
function wp_get_theme() { return new class { function get( $k ) { return 'X'; } }; }
function wp_enqueue_style( ...$a ) { $GLOBALS['ENQ'][] = $a[0]; }
function wp_dequeue_style() {} function wp_dequeue_script() {}
function get_bloginfo() { return 'MOLOSOC'; }
function molosoc_product_url( $l ) { return 'en' === $l ? 'https://molosoc.com/product/x/' : 'https://molosoc.com/cz/produkt/x/'; }
function molosoc_cod_cz_text() { return 'Zaplatíte při převzetí zásilky.'; }
function molosoc_real_reviews_html( $l ) { return "<!-- reviews $l -->"; }
function molosoc_landing_b_buy_links() { return array( 'M' => array( 'direct' => 1, 'url' => '/?add-to-cart=364&variation_id=1001&attribute_pa_size=m' ), 'L' => array( 'direct' => 1, 'url' => '/?add-to-cart=364&variation_id=1002&attribute_pa_size=l' ) ); }
function get_header() {}
function get_footer() {}
require $THEME . '/inc/landing-xmas.php';
if ( file_exists( $THEME . '/inc/landing-bf.php' ) ) require $THEME . '/inc/landing-bf.php';
if ( $MODE === 'head' ) {
	echo '<title>' . esc_html( apply_filters( 'pre_get_document_title', 'DEFAULT' ) ) . "</title>\n";
	do_action( 'wp_head' );
	echo 'STICKY ' . json_encode( apply_filters( 'molosoc_sticky_cta_data', array(), 'cz' ), JSON_UNESCAPED_UNICODE ) . "\n";
	do_action( 'wp_enqueue_scripts' ); echo 'ENQ ' . implode( ',', $GLOBALS['ENQ'] ?? array() ) . "\n";
	echo 'RETURN ' . molosoc_xmas_stock_redirect_url( 'cz', 'm', 1 ) . "\n";
	echo 'TOTAL3 ' . molosoc_xmas_bundle_total( 3 ) . "\n";
	exit;
}
require $THEME . '/' . $TPL;
