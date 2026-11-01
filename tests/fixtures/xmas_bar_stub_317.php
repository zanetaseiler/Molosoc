<?php
// Minimal WordPress stubs: renders molosoc_xmas_bar() for a scenario. Usage: php stub.php <cz|en> [landing|checkout|draft|off]
define( 'ABSPATH', '/' );
$lang = $argv[1] ?? 'en'; $mode = $argv[2] ?? '';
function apply_filters( $t, $v ) { global $mode; return ( 'off' === $mode && 'molosoc_xmas_bar_enabled' === $t ) ? false : $v; }
function add_action() {}
function molosoc_xmas_slugs() { return array( 'cz' => 'vanocni-darek-molosoc', 'en' => 'christmas-gift-molosoc' ); }
function molosoc_is_xmas_landing() { global $mode; return 'landing' === $mode; }
function is_checkout() { global $mode; return 'checkout' === $mode; }
function is_cart() { return false; }
function is_wc_endpoint_url( $e ) { return false; }
function pll_current_language() { global $lang; return $lang; }
function get_page_by_path( $s ) { return (object) array( 'slug' => $s ); }
function get_post_status( $p ) { global $mode; return 'draft' === $mode ? 'draft' : 'publish'; }
function get_permalink( $p ) { return ( 'vanocni-darek-molosoc' === $p->slug ? 'https://example.test/cz/' : 'https://example.test/' ) . $p->slug . '/'; }
function esc_attr( $s ) { return htmlspecialchars( $s, ENT_QUOTES ); }
function esc_url( $s ) { return $s; }
function esc_html( $s ) { return htmlspecialchars( $s, ENT_QUOTES ); }
function wp_json_encode( $v ) { return json_encode( $v ); }
require __DIR__ . '/../../site/theme/inc/xmas-bar.php';
molosoc_xmas_bar();
