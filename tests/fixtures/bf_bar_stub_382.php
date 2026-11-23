<?php
// Issue #382: minimal WordPress stubs with a FAKED clock.
// Usage: php bf_bar_stub_382.php <bar|redirect|guard> <cz|en> <unix-now> [bf-draft] [query-string] [page-slug]
//   bar      prints molosoc_xmas_bar() on an ordinary page of <lang>
//   redirect runs the template_redirect hook on the Black Friday page of <lang> (prints "REDIRECT <code> <url>" or nothing)
//   guard    prints the <head> guard script of the Black Friday page of <lang>
define( 'ABSPATH', '/' );
$what  = $argv[1] ?? 'bar';
$lang  = $argv[2] ?? 'cz';
$now   = (int) ( $argv[3] ?? time() );
$flag  = $argv[4] ?? '';
$_SERVER['QUERY_STRING'] = $argv[5] ?? '';
$slug_on = $argv[6] ?? '';

function apply_filters( $t, $v ) { global $now; return 'molosoc_bf_now' === $t ? $now : $v; }
function add_action() {}
function add_filter() {}
function wp_unslash( $v ) { return $v; }
function is_page( $s ) { global $what, $lang, $slug_on; $on = $slug_on ?: ( 'bar' === $what ? '' : ( 'cz' === $lang ? 'black-friday-molosoc' : 'black-friday-offer-molosoc' ) ); return $s === $on; }
function molosoc_xmas_slugs() { return array( 'cz' => 'vanocni-darek-molosoc', 'en' => 'christmas-gift-molosoc' ); }
function molosoc_xmas_page_url( $l ) { return 'en' === $l ? 'https://example.test/christmas-gift-molosoc/' : 'https://example.test/cz/vanocni-darek-molosoc/'; }
function molosoc_xmas_unit_prices() { return array( 1 => 209, 2 => 199, 3 => 199 ); }
function molosoc_is_xmas_landing() { return false; }
function is_checkout() { return false; }
function is_cart() { return false; }
function is_wc_endpoint_url( $e ) { return false; }
function pll_current_language() { global $lang; return $lang; }
function get_page_by_path( $s ) { return (object) array( 'slug' => $s ); }
function get_post_status( $p ) { global $flag; return ( 'bf-draft' === $flag && 0 === strpos( $p->slug, 'black-friday' ) ) ? 'draft' : 'publish'; }
function get_permalink( $p ) { return ( in_array( $p->slug, array( 'vanocni-darek-molosoc', 'black-friday-molosoc' ), true ) ? 'https://example.test/cz/' : 'https://example.test/' ) . $p->slug . '/'; }
function home_url( $p = '' ) { return 'https://example.test' . $p; }
function number_format_i18n( $n ) { return (string) $n; }
function esc_attr( $s ) { return htmlspecialchars( $s, ENT_QUOTES ); }
function esc_url( $s ) { return $s; }
function esc_html( $s ) { return htmlspecialchars( $s, ENT_QUOTES ); }
function wp_json_encode( $v ) { return json_encode( $v ); }
function nocache_headers() {}
function wp_safe_redirect( $url, $code = 302 ) { echo 'REDIRECT ' . $code . ' ' . $url; return true; }

require __DIR__ . '/../../site/theme/inc/landing-bf.php';
require __DIR__ . '/../../site/theme/inc/xmas-bar.php';

if ( 'bar' === $what ) {
	molosoc_xmas_bar();
} elseif ( 'redirect' === $what ) {
	molosoc_bf_expired_redirect();
} else {
	molosoc_bf_expired_guard();
}
