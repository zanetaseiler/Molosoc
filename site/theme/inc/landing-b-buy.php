<?php
/**
 * Landing Page B — direct add-to-cart links (Issue #209).
 *
 * Every purchase CTA on B used to be a plain link to the product page, so a
 * mobile visitor needed a second page just to pick a size and press the real
 * button (Clarity: 1 of 38 visitors reached it). The product is variable
 * (M 36–39 / L 39.5–44), so there is no single "add to cart" URL: this file
 * resolves one per size, each pointing at the CZ cart with WooCommerce's own
 * add-to-cart query string (?add-to-cart=364&variation_id=…&attribute_…=…).
 * WooCommerce's standard form handler (wp_loaded) adds the item and the
 * visitor lands on the cart with the product in it — no JavaScript, no AJAX,
 * no jQuery/cart-fragments on B (they are deliberately dequeued there, see
 * molosoc_dequeue_unused_homepage_assets()), and no cart/checkout/price
 * logic of ours: the variation's own price is what the cart and checkout
 * charge.
 *
 * Anything that cannot be resolved (product missing, not variable, a size
 * with no purchasable variation) falls back to the CZ product-page URL for
 * that size — exactly what the CTAs linked to before, never a dead link.
 */

defined( 'ABSPATH' ) || exit;

/**
 * Czech cart page URL regardless of the language the (REST-created) landing
 * page itself carries — same reasoning as molosoc_product_url( 'cz' ) in the
 * template.
 */
function molosoc_landing_b_cart_url() {
	if ( ! function_exists( 'wc_get_cart_url' ) ) {
		return home_url( '/cz/kosik/' );
	}
	if ( function_exists( 'wc_get_page_id' ) && function_exists( 'pll_get_post' ) ) {
		$cart_id = wc_get_page_id( 'cart' );
		$cz_id   = $cart_id > 0 ? pll_get_post( $cart_id, 'cz' ) : 0;
		if ( $cz_id && 'publish' === get_post_status( $cz_id ) ) {
			return get_permalink( $cz_id );
		}
	}
	return wc_get_cart_url();
}

/**
 * Add-to-cart URL per size key ('M' / 'L') for product 364, plus the
 * size labels the buttons print.
 *
 * @return array[] size key => array( 'url' => string, 'label' => string, 'direct' => bool ).
 */
function molosoc_landing_b_buy_links() {
	$fallback = molosoc_product_url( 'cz' );
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

	$cart_url = molosoc_landing_b_cart_url();
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
					),
					array_map( 'strval', $filled )
				),
				$cart_url
			);
			$links[ $key ]['direct'] = true;
		}
	}
	return $links;
}

/**
 * The purchase CTA group printed in the hero and after every main section:
 * one button per size, same price on both (the product is one price).
 *
 * @param string $variant '' (default, black buttons) or 'dark' (outlined, for the black band).
 */
function molosoc_landing_b_buy_cta( $variant = '' ) {
	static $links = null;
	if ( null === $links ) {
		$links = molosoc_landing_b_buy_links();
	}
	$class = 'lpb-buy' . ( 'dark' === $variant ? ' lpb-buy--dark' : '' );
	?>
	<div class="<?php echo esc_attr( $class ); ?>" role="group" aria-label="Objednat MOLOSOC">
		<?php foreach ( $links as $key => $link ) : ?>
			<a class="lpb-btn lpb-buy__btn<?php echo 'dark' === $variant ? ' lpb-btn--ghost' : ''; ?>" href="<?php echo esc_url( $link['url'] ); ?>" data-lpb-size="<?php echo esc_attr( $key ); ?>" rel="nofollow">
				<span class="lpb-buy__action">Objednat</span>
				<span class="lpb-buy__size"><?php echo esc_html( $link['label'] ); ?></span>
			</a>
		<?php endforeach; ?>
	</div>
	<?php
}
