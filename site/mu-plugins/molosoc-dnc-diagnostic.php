<?php
/**
 * Plugin Name: Molosoc DONOTCACHEPAGE Diagnostic (temporary)
 * Description: Reports at which load stage the DONOTCACHEPAGE constant gets defined, to find which plugin blocks WP-Optimize page caching on the EN front page (867). Output only appears with ?molosoc_dnc=1. Remove after diagnosis.
 * Version: 1.0.0
 *
 * TEMPORARY DIAGNOSTIC — REMOVE once the definer is identified.
 *
 * The EN front page is never page-cached ("wpo-cache-message:
 * DONOTCACHEPAGE constant forbade it") while every other page caches
 * fine, so each visit re-renders it in PHP (1-4s TTFB). This probe
 * checks defined('DONOTCACHEPAGE') at a ladder of load stages and
 * reports the first stage where it turned up, plus the active-plugin
 * list, as an X-Molosoc-DNC header (state as of send_headers) and an
 * HTML comment appended at shutdown (final verdict). Both outputs are
 * gated on ?molosoc_dnc=1 so normal traffic is untouched; WP-Optimize
 * doesn't cache query-string URLs, so probing can't pollute the cache.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$GLOBALS['molosoc_dnc_first'] = defined( 'DONOTCACHEPAGE' ) ? 'before-mu-plugins (wp-config/advanced-cache)' : '';

function molosoc_dnc_probe( $label ) {
	if ( '' === $GLOBALS['molosoc_dnc_first'] && defined( 'DONOTCACHEPAGE' ) ) {
		$GLOBALS['molosoc_dnc_first'] = $label;
	}
}

foreach ( array(
	array( 'muplugins_loaded', PHP_INT_MAX, 'muplugins_loaded' ),
	array( 'plugins_loaded', PHP_INT_MIN, 'plugins_loaded:first' ),
	array( 'plugins_loaded', PHP_INT_MAX, 'plugins_loaded:last' ),
	array( 'setup_theme', PHP_INT_MIN, 'setup_theme' ),
	array( 'after_setup_theme', PHP_INT_MAX, 'after_setup_theme:last' ),
	array( 'init', PHP_INT_MIN, 'init:first' ),
	array( 'init', PHP_INT_MAX, 'init:last' ),
	array( 'wp_loaded', PHP_INT_MAX, 'wp_loaded' ),
	array( 'wp', PHP_INT_MIN, 'wp:first' ),
	array( 'wp', 9, 'wp:pri<10' ),
	array( 'wp', 10, 'wp:pri10-start (mu-plugin registers first within 10)' ),
	array( 'wp', 11, 'wp:after-pri10' ),
	array( 'wp', PHP_INT_MAX, 'wp:last' ),
	array( 'template_redirect', PHP_INT_MIN, 'template_redirect:first' ),
	array( 'template_redirect', PHP_INT_MAX, 'template_redirect:last' ),
	array( 'wp_head', PHP_INT_MIN, 'wp_head:first' ),
	array( 'wp_head', PHP_INT_MAX, 'wp_head:last' ),
	array( 'wp_footer', PHP_INT_MIN, 'wp_footer:first' ),
	array( 'wp_footer', PHP_INT_MAX, 'wp_footer:last' ),
) as $molosoc_dnc_hook ) {
	add_action(
		$molosoc_dnc_hook[0],
		function () use ( $molosoc_dnc_hook ) {
			molosoc_dnc_probe( $molosoc_dnc_hook[2] );
		},
		$molosoc_dnc_hook[1]
	);
}

function molosoc_dnc_enabled() {
	// GET param, or an X-Molosoc-Dnc request header for probing WITHOUT a
	// query string (a GET param itself changes caching-related behavior,
	// so header-triggered runs see the same conditions as real traffic).
	return ( isset( $_GET['molosoc_dnc'] ) && '1' === $_GET['molosoc_dnc'] ) // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read-only diagnostic flag.
		|| ( isset( $_SERVER['HTTP_X_MOLOSOC_DNC'] ) && '1' === $_SERVER['HTTP_X_MOLOSOC_DNC'] );
}

// Header carries the state as of send_headers (pre-template); the
// shutdown comment below is the authoritative final verdict.
add_action( 'send_headers', function () {
	if ( ! molosoc_dnc_enabled() ) {
		return;
	}
	molosoc_dnc_probe( 'send_headers' );
	$first = $GLOBALS['molosoc_dnc_first'];
	header( 'X-Molosoc-DNC: ' . ( '' !== $first ? 'defined-by:' . $first : 'not-defined-yet' ) );
}, PHP_INT_MAX );

add_action( 'shutdown', function () {
	if ( ! molosoc_dnc_enabled() ) {
		return;
	}
	molosoc_dnc_probe( 'shutdown' );
	$first   = $GLOBALS['molosoc_dnc_first'];
	$plugins = (array) get_option( 'active_plugins', array() );
	echo "\n<!-- molosoc-dnc\n";
	echo 'DONOTCACHEPAGE: ' . ( defined( 'DONOTCACHEPAGE' ) ? 'DEFINED, first seen at [' . esc_html( $first ) . ']' : 'never defined' ) . "\n";
	echo 'front_page: ' . ( function_exists( 'is_front_page' ) && is_front_page() ? 'yes' : 'no' ) . "\n";
	echo 'queried_object_id: ' . (int) get_queried_object_id() . "\n";
	if ( function_exists( 'wc_get_page_id' ) ) {
		foreach ( array( 'cart', 'checkout', 'myaccount', 'shop', 'terms' ) as $wc_page ) {
			echo 'wc_page_id[' . $wc_page . ']: ' . (int) wc_get_page_id( $wc_page ) . "\n";
		}
		echo 'is_cart/is_checkout/is_account_page: '
			. ( is_cart() ? 'y' : 'n' ) . '/'
			. ( is_checkout() ? 'y' : 'n' ) . '/'
			. ( is_account_page() ? 'y' : 'n' ) . "\n";
	}
	global $wp_filter;
	if ( isset( $wp_filter['wp'] ) ) {
		echo "wp-hook callbacks (priorities 5-15):\n";
		foreach ( $wp_filter['wp']->callbacks as $pri => $cbs ) {
			if ( $pri < 5 || $pri > 15 ) {
				continue;
			}
			foreach ( $cbs as $cb ) {
				$f = $cb['function'];
				if ( is_array( $f ) ) {
					$name = ( is_object( $f[0] ) ? get_class( $f[0] ) : (string) $f[0] ) . '::' . $f[1];
				} elseif ( is_string( $f ) ) {
					$name = $f;
				} elseif ( $f instanceof Closure ) {
					$r    = new ReflectionFunction( $f );
					$name = 'closure@' . basename( (string) $r->getFileName() ) . ':' . $r->getStartLine();
				} else {
					$name = 'object:' . get_class( $f );
				}
				echo '  wp@' . (int) $pri . ': ' . esc_html( $name ) . "\n";
			}
		}
	}
	echo "active_plugins:\n";
	foreach ( $plugins as $plugin ) {
		echo '  ' . esc_html( $plugin ) . "\n";
	}
	echo "-->\n";
}, PHP_INT_MIN );
