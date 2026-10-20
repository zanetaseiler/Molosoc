<?php
/**
 * Plugin Name: Molosoc staging noindex (durable)
 * Description: Keeps staging.molosoc.com out of search indexes with an `X-Robots-Tag: noindex, nofollow` response header plus a robots meta tag. Deliberately does NOT disallow crawling in robots.txt - Google must be able to fetch a page to see its noindex. Hard host gate: inert on every host except staging.molosoc.com. Lives under automations/staging/ (NOT site/mu-plugins/, which auto-deploys to PRODUCTION on push); shipped to staging only by .github/workflows/deploy-mu-plugins-staging.yml.
 */

function molosoc_staging_noindex_is_staging_host() {
	$host = strtolower( (string) ( $_SERVER['HTTP_HOST'] ?? '' ) );
	$host = preg_replace( '/:\d+$/', '', $host );
	return 'staging.molosoc.com' === $host;
}

add_action( 'send_headers', function () {
	if ( ! molosoc_staging_noindex_is_staging_host() ) {
		return;
	}
	header( 'X-Robots-Tag: noindex, nofollow', true );
} );

add_filter( 'wp_robots', function ( $robots ) {
	if ( ! molosoc_staging_noindex_is_staging_host() ) {
		return $robots;
	}
	$robots['noindex']  = true;
	$robots['nofollow'] = true;
	unset( $robots['index'], $robots['follow'] );
	return $robots;
}, 999 );
