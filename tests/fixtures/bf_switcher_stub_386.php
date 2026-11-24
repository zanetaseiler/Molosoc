<?php
// Issue #386: minimal WordPress + Polylang-switcher stubs for the header globe.
// Usage: php bf_switcher_stub_386.php <current-page-slug|-> [bf-draft]
// Prints one line per switcher language, "<lang> <href>", the way Polylang's
// PLL_Switcher builds them: the untranslated fallback (that language's homepage)
// passed through every `pll_the_language_link` callback the theme file registers.
define( 'ABSPATH', '/' );
$page = $argv[1] ?? '-';
$flag = $argv[2] ?? '';
$GLOBALS['molosoc_filters'] = array();

function add_filter( $tag, $cb, $prio = 10, $n = 1 ) { $GLOBALS['molosoc_filters'][ $tag ][ $prio ][] = $cb; }
function add_action() {}
function apply_filters( $t, $v ) { return $v; }
function is_page( $s ) { global $page; return $s === $page; }
function get_page_by_path( $s ) { return (object) array( 'slug' => $s ); }
function get_post_status( $p ) { global $flag; return ( 'bf-draft' === $flag && 0 === strpos( $p->slug, 'black-friday' ) ) ? 'draft' : 'publish'; }
function get_permalink( $p ) { return ( 'black-friday-molosoc' === $p->slug ? 'https://molosoc.com/cz/' : 'https://molosoc.com/' ) . $p->slug . '/'; }
function home_url( $p = '' ) { return 'https://molosoc.com' . $p; }

require __DIR__ . '/../../site/theme/inc/landing-bf.php';

$fallback = array( 'cz' => 'https://molosoc.com/cz/', 'en' => 'https://molosoc.com/' );
$cbs      = $GLOBALS['molosoc_filters']['pll_the_language_link'] ?? array();
ksort( $cbs );
foreach ( $fallback as $lang => $url ) {
	foreach ( $cbs as $list ) {
		foreach ( $list as $cb ) {
			$url = call_user_func( $cb, $url, $lang );
		}
	}
	echo $lang . ' ' . $url . "\n";
}
