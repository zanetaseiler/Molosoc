<?php
/**
 * Plugin Name: MOLOSOC Sitemap Polylang Redirect Fix
 * Description: Prevents Polylang browser-language redirects from intercepting WordPress core sitemap requests.
 */
add_filter( 'pll_redirect_home', function ( $redirect ) {
    $request_uri = $_SERVER['REQUEST_URI'] ?? '';
    if ( false !== strpos( $request_uri, 'wp-sitemap' ) ) {
        return false;
    }
    return $redirect;
} );
