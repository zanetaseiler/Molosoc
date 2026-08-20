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
	array( 'wp', PHP_INT_MAX, 'wp' ),
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
	return isset( $_GET['molosoc_dnc'] ) && '1' === $_GET['molosoc_dnc']; // phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read-only diagnostic flag.
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
	echo "active_plugins:\n";
	foreach ( $plugins as $plugin ) {
		echo '  ' . esc_html( $plugin ) . "\n";
	}
	echo "-->\n";
}, PHP_INT_MIN );
