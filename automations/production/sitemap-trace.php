<?php
/**
 * Plugin Name: TEMP MOLOSOC sitemap status tracer
 * Description: TEMPORARY, observation-only. Records how the sitemap request's HTTP status is decided, to a private file beside this one. Every callback returns its value unchanged — nothing here alters status, redirects or output. Uploaded and deleted by .github/workflows/prod-sitemap-trace.yml. Must not remain on any server.
 */

// Only ever runs for sitemap requests. Every other request returns here,
// before a single hook is registered.
if ( false === strpos( isset( $_SERVER['REQUEST_URI'] ) ? $_SERVER['REQUEST_URI'] : '', 'wp-sitemap' ) ) {
	return;
}

function molosoc_trace( $line ) {
	file_put_contents( __DIR__ . '/.molosoc-sitemap-trace.log', $line . "\n", FILE_APPEND | LOCK_EX );
}

function molosoc_trace_hooks( $hook ) {
	global $wp_filter;
	if ( ! isset( $wp_filter[ $hook ] ) ) {
		molosoc_trace( "    ($hook: no callbacks registered)" );
		return;
	}
	foreach ( $wp_filter[ $hook ]->callbacks as $prio => $cbs ) {
		molosoc_trace( "    prio $prio: " . implode( ', ', array_keys( $cbs ) ) );
	}
}

molosoc_trace( str_repeat( '=', 70 ) );
molosoc_trace( '1. tracer loaded' );
molosoc_trace( '2. REQUEST_URI = ' . ( isset( $_SERVER['REQUEST_URI'] ) ? $_SERVER['REQUEST_URI'] : '' ) );

add_action( 'muplugins_loaded', function () {
	if ( function_exists( 'wp_get_mu_plugins' ) ) {
		molosoc_trace( 'A. mu-plugins actually loaded: ' . implode( ', ', array_map( 'basename', wp_get_mu_plugins() ) ) );
	}
}, 1 );

// Priority 1: the value before any other pre_handle_404 filter has run.
add_filter( 'pre_handle_404', function ( $preempt, $wp_query ) {
	molosoc_trace( '3. pre_handle_404 FIRED' );
	molosoc_trace( '   incoming preempt        = ' . var_export( $preempt, true ) );
	molosoc_trace( '   sitemap                 = ' . var_export( $wp_query->get( 'sitemap' ), true ) );
	molosoc_trace( '   sitemap-stylesheet      = ' . var_export( $wp_query->get( 'sitemap-stylesheet' ), true ) );
	molosoc_trace( '   sitemap-subtype         = ' . var_export( $wp_query->get( 'sitemap-subtype' ), true ) );
	molosoc_trace( '   registered pre_handle_404 callbacks:' );
	molosoc_trace_hooks( 'pre_handle_404' );
	return $preempt;
}, 1, 2 );

// Priority 9999: the value after every other pre_handle_404 filter has run.
add_filter( 'pre_handle_404', function ( $preempt, $wp_query ) {
	molosoc_trace( '3b. pre_handle_404 FINAL preempt = ' . var_export( $preempt, true ) );
	return $preempt;
}, 9999, 2 );

add_action( 'wp', function () {
	molosoc_trace( '4a. wp                  : is_404=' . var_export( is_404(), true ) . ' status=' . var_export( http_response_code(), true ) );
}, 1 );

add_action( 'template_redirect', function () {
	molosoc_trace( '4b. template_redirect   : is_404=' . var_export( is_404(), true ) . ' status=' . var_export( http_response_code(), true ) );
	molosoc_trace( '5. template_redirect callbacks, in execution order:' );
	molosoc_trace_hooks( 'template_redirect' );
}, -9999 );

add_action( 'shutdown', function () {
	molosoc_trace( '4c. shutdown            : is_404=' . var_export( is_404(), true ) . ' status=' . var_export( http_response_code(), true ) );
}, 9999 );
