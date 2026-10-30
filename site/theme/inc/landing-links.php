<?php
/**
 * Landing page links (Issue #303, 2026-10-30).
 *
 * Žaneta pointed the main-menu "foot cover" item at the new Landing Page B,
 * but the homepage hero button, both category pages (buttons + the three
 * "who is it for" cards) and the CTA of every pillar/spoke page still
 * hard-coded the old Landing Page A URL. From now on every such link goes
 * through molosoc_landing_url(), and any Landing A href that still comes
 * out of a menu item or block/page content is rewritten on output.
 *
 * Landing B exists on production for CZ (page 1037,
 * /cz/hydratacni-navleky-molosoc/). The EN Landing B slug
 * (molosoc_landing_b_en_slug(), /hydrating-foot-covers-molosoc/) is not
 * published yet, so the helper falls back to Landing A for a language whose
 * Landing B page is missing or unpublished — and switches by itself the day
 * that page is published. Nothing else changes: Landing A stays reachable at
 * its URL, the product page, the sticky pill (molosoc_product_url()), the
 * checkout and the JSON-LD product identities are untouched.
 */

defined( 'ABSPATH' ) || exit;

/** Landing Page A URL of a language (the pre-#303 target of every link). */
function molosoc_landing_a_url( $lang ) {
	return home_url( 'cz' === $lang ? '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' : '/foot-covers/moisture-lock-foot-cover/' );
}

/** Landing Page B slug of a language. */
function molosoc_landing_b_slug_for( $lang ) {
	if ( 'cz' === $lang ) {
		return 'hydratacni-navleky-molosoc';
	}
	return function_exists( 'molosoc_landing_b_en_slug' ) ? molosoc_landing_b_en_slug() : 'hydrating-foot-covers-molosoc';
}

/**
 * The landing page every button and link points at: Landing B when that
 * language's Landing B page is published, otherwise Landing A.
 *
 * @param string|null $lang 'cz' | 'en'; null = the current Polylang language.
 * @return string Absolute URL.
 */
function molosoc_landing_url( $lang = null ) {
	static $cache = array();
	if ( null === $lang ) {
		$lang = ( function_exists( 'pll_current_language' ) && 'cz' === pll_current_language() ) ? 'cz' : 'en';
	}
	$lang = 'cz' === $lang ? 'cz' : 'en';
	if ( ! isset( $cache[ $lang ] ) ) {
		$url  = molosoc_landing_a_url( $lang );
		$page = get_page_by_path( molosoc_landing_b_slug_for( $lang ), OBJECT, 'page' );
		if ( $page && 'publish' === $page->post_status ) {
			$url = get_permalink( $page );
		}
		$cache[ $lang ] = $url;
	}
	return apply_filters( 'molosoc_landing_url', $cache[ $lang ], $lang );
}

/**
 * Landing A URL => Landing B URL for every language whose Landing B is live
 * (with and without the trailing slash). Empty when nothing is to be rewritten.
 */
function molosoc_landing_links_map() {
	$map = array();
	foreach ( array( 'cz', 'en' ) as $lang ) {
		$a = molosoc_landing_a_url( $lang );
		$b = molosoc_landing_url( $lang );
		if ( $a !== $b ) {
			$map[ $a ]                      = $b;
			$map[ untrailingslashit( $a ) ] = $b;
		}
	}
	return $map;
}

/** Menu items (WP admin → Menus) that still point at Landing A go to Landing B. */
function molosoc_landing_links_menu( $items ) {
	$map = molosoc_landing_links_map();
	if ( ! $map ) {
		return $items;
	}
	foreach ( $items as $item ) {
		if ( ! empty( $item->url ) && isset( $map[ trailingslashit( $item->url ) ] ) ) {
			$item->url = $map[ trailingslashit( $item->url ) ];
		}
	}
	return $items;
}
add_filter( 'wp_nav_menu_objects', 'molosoc_landing_links_menu' );

/** Block / page / product content that still links to Landing A goes to Landing B. */
function molosoc_landing_links_content( $content ) {
	$map = molosoc_landing_links_map();
	if ( ! $map || ! is_string( $content ) || false === strpos( $content, 'href' ) ) {
		return $content;
	}
	return str_replace( array_keys( $map ), array_values( $map ), $content );
}
add_filter( 'the_content', 'molosoc_landing_links_content', 20 );
