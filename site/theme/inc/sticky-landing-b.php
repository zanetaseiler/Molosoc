<?php
/**
 * Global sticky "Buy now" pill → Landing Page B (Issue #311, 2026-10-30).
 *
 * The pill (assets/js/sticky-cta.js, data printed by the gated wp_head closure
 * in functions.php) used to link to the product page. It now links to Landing
 * Page B of the current language through molosoc_landing_url() (inc/landing-links.php):
 * CZ /cz/hydratacni-navleky-molosoc/; EN /hydrating-foot-covers-molosoc/ only
 * once that page is published, otherwise Landing A (the existing functional page).
 *
 * Hooks the existing molosoc_sticky_cta_data filter AFTER the Christmas filter
 * (priority 10, Issue #299): when that already returned a target (the in-page
 * #lpx-bundle picker) this leaves it alone, so the Christmas pages never
 * navigate away. The gate (molosoc_sticky_cta_hidden()), label, styling and
 * position are unchanged. No redirects.
 *
 * On the destination itself the pill must not link to its own page (a tap would
 * just reload it): Landing B points at its hero size picker (#lpb-buy, printed
 * by molosoc_landing_b_buy_cta()); the EN Landing A fallback keeps the product
 * page, the pill's original destination.
 */

defined( 'ABSPATH' ) || exit;

/**
 * @param array  $data Override so far (empty unless a template set one).
 * @param string $lang Polylang language of the request.
 * @return array
 */
function molosoc_sticky_cta_landing_b( $data, $lang = '' ) {
	if ( ! empty( $data['url'] ) || ! function_exists( 'molosoc_landing_url' ) ) {
		return $data;
	}
	$lang = 'cz' === $lang ? 'cz' : 'en';
	$url  = molosoc_landing_url( $lang );
	if ( is_singular() && untrailingslashit( (string) get_permalink() ) === untrailingslashit( $url ) ) {
		$b = function_exists( 'molosoc_landing_b_slug_for' ) ? get_page_by_path( molosoc_landing_b_slug_for( $lang ), OBJECT, 'page' ) : null;
		if ( $b && is_page( $b->ID ) ) {
			$url = '#lpb-buy';
		} elseif ( function_exists( 'molosoc_product_url' ) ) {
			$url = molosoc_product_url( $lang );
		}
	}
	return array(
		'url'   => $url,
		'label' => ( 'cz' === $lang ) ? 'Koupit nyní' : __( 'Buy now', 'molosoc' ),
	);
}
add_filter( 'molosoc_sticky_cta_data', 'molosoc_sticky_cta_landing_b', 20, 2 );
