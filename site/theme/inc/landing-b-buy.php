<?php
/**
 * Landing Page B — direct size selection to checkout (Issue #209).
 *
 * Every purchase CTA on B used to be a plain link to the product page, so a
 * mobile visitor needed a second page just to pick a size and press the real
 * button (Clarity: 1 of 38 visitors reached it). The product is variable
 * (M 36–39 / L 39.5–44), so there is no single "add to cart" URL: this file
 * resolves one per size, each pointing at the CZ checkout with WooCommerce's
 * own add-to-cart query string (?add-to-cart=364&variation_id=…&attribute_…=…
 * &quantity=1&molosoc_lpb=1). The visitor picks a size (no default — the
 * choice is explicit), landing-b.js sends them to the URL of that size, and
 * WooCommerce's standard form handler (wp_loaded) adds the variation. A single
 * `woocommerce_add_to_cart_redirect` filter, active only for requests that
 * carry molosoc_lpb, then redirects to the clean checkout URL, so a reload or
 * back-navigation can never re-add the item. Cart, checkout, payment,
 * shipping, price and variation mapping are WooCommerce's own: the
 * variation's price is what checkout charges.
 *
 * Anything that cannot be resolved (product missing, not variable, a size
 * with no purchasable variation) has no checkout URL: the CTA keeps its
 * href to the CZ product page for that case, never a dead link.
 */

defined( 'ABSPATH' ) || exit;

/**
 * Czech checkout page URL regardless of the language the (REST-created)
 * landing page itself carries — same reasoning as molosoc_product_url( 'cz' )
 * in the template.
 */
function molosoc_landing_b_checkout_url( $lang = 'cz' ) {
	if ( 'en' === $lang ) {
		// English Landing B (Issue #288): the EN checkout page, resolved from
		// whatever language WooCommerce's stored page id resolves to.
		if ( ! function_exists( 'wc_get_checkout_url' ) ) {
			return home_url( '/checkout/' );
		}
		if ( function_exists( 'wc_get_page_id' ) && function_exists( 'pll_get_post' ) ) {
			$checkout_id = wc_get_page_id( 'checkout' );
			$en_id       = $checkout_id > 0 ? pll_get_post( $checkout_id, 'en' ) : 0;
			if ( $en_id && 'publish' === get_post_status( $en_id ) ) {
				return get_permalink( $en_id );
			}
		}
		return wc_get_checkout_url();
	}
	if ( ! function_exists( 'wc_get_checkout_url' ) ) {
		return home_url( '/cz/pokladna/' );
	}
	if ( function_exists( 'wc_get_page_id' ) && function_exists( 'pll_get_post' ) ) {
		$checkout_id = wc_get_page_id( 'checkout' );
		$cz_id       = $checkout_id > 0 ? pll_get_post( $checkout_id, 'cz' ) : 0;
		if ( $cz_id && 'publish' === get_post_status( $cz_id ) ) {
			return get_permalink( $cz_id );
		}
	}
	return wc_get_checkout_url();
}

/**
 * After WooCommerce adds the item for a Landing B request (molosoc_lpb), go
 * to the clean checkout URL. Every other add-to-cart is untouched: the
 * filter only returns a URL for requests carrying the marker.
 */
add_filter( 'woocommerce_add_to_cart_redirect', 'molosoc_landing_b_checkout_redirect' );
function molosoc_landing_b_checkout_redirect( $url ) {
	if ( isset( $_REQUEST['molosoc_lpb'] ) && function_exists( 'wc_get_checkout_url' ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		// molosoc_lpb=1 is the CZ page; molosoc_lpb=en the English one (Issue #288).
		$lang = 'en' === sanitize_key( wp_unslash( $_REQUEST['molosoc_lpb'] ) ) ? 'en' : 'cz'; // phpcs:ignore WordPress.Security.NonceVerification
		return molosoc_landing_b_checkout_url( $lang );
	}
	return $url;
}

/**
 * Add-to-cart-and-checkout URL per size key ('M' / 'L') for product 364, plus the
 * size labels the buttons print.
 *
 * @return array[] size key => array( 'url' => string, 'label' => string, 'direct' => bool ).
 */
function molosoc_landing_b_buy_links( $lang = 'cz' ) {
	$fallback = molosoc_product_url( 'en' === $lang ? 'en' : 'cz' );
	$links    = array(
		'M' => array( 'url' => $fallback, 'label' => 'M (36–39)', 'direct' => false ),
		'L' => array( 'url' => $fallback, 'label' => 'L (39.5–44)', 'direct' => false ),
	);

	if ( ! function_exists( 'wc_get_product' ) ) {
		return $links;
	}
	$product = wc_get_product( MOLOSOC_PRODUCT_ID );
	if ( ! $product || ! $product->is_type( 'variable' ) ) {
		return $links;
	}

	$checkout_url = molosoc_landing_b_checkout_url( $lang );
	$wanted   = array( 'M' => 0, 'L' => 1 ); // molosoc_size_value_rank() ranks.

	foreach ( $product->get_children() as $variation_id ) {
		$variation = wc_get_product( $variation_id );
		if ( ! $variation || ! $variation->is_purchasable() || ! $variation->is_in_stock() ) {
			continue;
		}
		$attributes = (array) $variation->get_variation_attributes();
		foreach ( $wanted as $key => $rank ) {
			if ( $links[ $key ]['direct'] ) {
				continue;
			}
			$matches = false;
			$filled  = $attributes;
			foreach ( $attributes as $name => $value ) {
				if ( '' === (string) $value ) {
					continue;
				}
				if ( molosoc_size_value_rank( $value ) === $rank ) {
					$matches = true;
				}
			}
			if ( ! $matches ) {
				// A variation whose size is "Any" has no value of its own:
				// fill it with the parent's option for this size (the same
				// fix the thank-you gift add-on uses) so WooCommerce accepts it.
				if ( array_filter( $attributes, 'strlen' ) ) {
					continue;
				}
				$filled = molosoc_gift_variation_attributes( $variation, $key );
				if ( ! array_filter( $filled, 'strlen' ) ) {
					continue;
				}
			}
			$links[ $key ]['url']    = add_query_arg(
				array_merge(
					array(
						'add-to-cart'  => MOLOSOC_PRODUCT_ID,
						'variation_id' => $variation_id,
						'quantity'     => 1,
						'molosoc_lpb'  => 'en' === $lang ? 'en' : 1,
					),
					array_map( 'strval', $filled )
				),
				$checkout_url
			);
			$links[ $key ]['direct'] = true;
		}
	}
	return $links;
}

/**
 * The purchase CTA group printed in the hero and after every main section:
 * a size choice (no default) and one "Pokračovat k pokladně" button. All
 * groups share one choice (landing-b.js), so the same size is bought from any
 * of them. Without JS, or for a size with no checkout URL, the button is the
 * plain product-page link. Issue #290 (same fix as the Christmas picker, #287):
 * the "Velikost" legend stays visible on phones (.lpb-buy__size-label) and the
 * error is a live region that landing-b.js pairs with a red outline on the row.
 *
 * @param string $variant '' (default, black button) or 'dark' (outlined, for the black band).
 * @param string $lang    'cz' (default) or 'en' — the English Landing B (Issue #288) uses
 *                        English labels and the EN product / checkout URLs; the markup,
 *                        classes and data attributes (so landing-b.js) are identical.
 */
function molosoc_landing_b_buy_cta( $variant = '', $lang = 'cz' ) {
	static $links = array();
	static $group = 0;
	$lang = 'en' === $lang ? 'en' : 'cz';
	if ( ! isset( $links[ $lang ] ) ) {
		$links[ $lang ] = molosoc_landing_b_buy_links( $lang );
	}
	$copy = 'en' === $lang
		? array( 'legend' => 'Size', 'button' => 'Continue to checkout', 'error' => 'Please choose a size.' )
		: array( 'legend' => 'Velikost', 'button' => 'Pokračovat k pokladně', 'error' => 'Vyberte velikost.' );
	++$group;
	$class = 'lpb-buy' . ( 'dark' === $variant ? ' lpb-buy--dark' : '' );
	?>
	<div class="<?php echo esc_attr( $class ); ?>" data-lpb-buy<?php echo 1 === $group ? ' id="lpb-buy"' : ''; ?>>
		<fieldset class="lpb-buy__sizes">
			<legend class="lpb-buy__legend lpb-buy__size-label"><?php echo esc_html( $copy['legend'] ); ?></legend>
			<?php foreach ( $links[ $lang ] as $key => $link ) : ?>
				<label class="lpb-size">
					<input type="radio" name="lpb-size-<?php echo (int) $group; ?>" value="<?php echo esc_attr( $key ); ?>"<?php echo $link['direct'] ? ' data-lpb-url="' . esc_url( $link['url'] ) . '"' : ''; ?>>
					<span class="lpb-size__label"><?php echo esc_html( $link['label'] ); ?></span>
				</label>
			<?php endforeach; ?>
		</fieldset>
		<a class="lpb-btn lpb-buy__btn<?php echo 'dark' === $variant ? ' lpb-btn--ghost' : ''; ?>" href="<?php echo esc_url( molosoc_product_url( $lang ) ); ?>" data-lpb-checkout rel="nofollow"><?php echo esc_html( $copy['button'] ); ?></a>
		<p class="lpb-buy__error" role="alert" aria-live="assertive" aria-atomic="true" hidden><?php echo esc_html( $copy['error'] ); ?></p>
	</div>
	<?php
}
