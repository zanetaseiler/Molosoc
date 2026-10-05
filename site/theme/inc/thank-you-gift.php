<?php
/**
 * Bilingual Thank You / Order Received page — hero heading plus a
 * post-purchase gift add-on section (GitHub Issue #106).
 *
 * The paid order is NEVER modified and the customer is NEVER charged from
 * this page. The Comgate plugin is not vendored in this repository, so no
 * tokenised "one-click" charge can be confirmed safe; the gift CTA instead
 * adds the chosen pairs to the cart and sends the customer through the
 * normal, unchanged checkout as a new, separate order — and says so.
 *
 * Presentation goes through WooCommerce's own hooks only (no
 * checkout/thankyou.php override), so the order overview/details, the
 * Comgate return flow and any analytics plugin's own thank-you hooks keep
 * running exactly as before.
 *
 * Required once from functions.php, after inc/woocommerce-lang.php (this
 * file reuses MOLOSOC_PRODUCT_ID, molosoc_product_url() and
 * molosoc_size_label_for_value() from there).
 */

defined( 'ABSPATH' ) || exit;

// The most pairs one gift checkout can start with.
if ( ! defined( 'MOLOSOC_GIFT_MAX_PAIRS' ) ) {
	define( 'MOLOSOC_GIFT_MAX_PAIRS', 3 );
}

/**
 * The order the current order-received request is for, or null. Mirrors
 * WooCommerce's own thank-you check (order ID from the endpoint query var,
 * order key from ?key=) so nothing here ever renders for an order the
 * visitor doesn't hold the key to. Also null for an order that isn't a
 * successful purchase yet: failed/cancelled, or still pending payment (a
 * gateway return that hasn't been confirmed) — WooCommerce's own default
 * page is left completely untouched for those.
 */
function molosoc_thankyou_order() {
	if ( ! function_exists( 'is_wc_endpoint_url' ) || ! is_wc_endpoint_url( 'order-received' ) ) {
		return null;
	}
	global $wp;
	$order_id = isset( $wp->query_vars['order-received'] ) ? absint( $wp->query_vars['order-received'] ) : 0;
	// phpcs:ignore WordPress.Security.NonceVerification.Recommended -- read-only, same check WooCommerce's own thank-you shortcode does.
	$order_key = isset( $_GET['key'] ) ? wc_clean( wp_unslash( $_GET['key'] ) ) : '';
	if ( ! $order_id || ! is_string( $order_key ) || '' === $order_key ) {
		return null;
	}
	$order = wc_get_order( $order_id );
	if ( ! $order instanceof WC_Order || ! hash_equals( $order->get_order_key(), $order_key ) ) {
		return null;
	}
	if ( ! $order->has_status( array( 'processing', 'completed', 'on-hold' ) ) ) {
		return null;
	}
	return $order;
}

/**
 * 'cz' or 'en' for the Thank You page: the language the order was placed
 * in (_molosoc_lang, stamped at checkout by inc/woocommerce-lang.php),
 * falling back to the request's own language for an order without it.
 */
function molosoc_thankyou_lang( $order ) {
	$lang = ( $order instanceof WC_Order ) ? $order->get_meta( '_molosoc_lang' ) : '';
	if ( 'cz' !== $lang && 'en' !== $lang ) {
		$lang = function_exists( 'pll_current_language' ) ? pll_current_language() : 'en';
	}
	return ( 'cz' === $lang ) ? 'cz' : 'en';
}

/**
 * Hero heading. index.php already prints the page's <h1> from the_title(),
 * which WooCommerce swaps for its endpoint title ("Order received") on
 * this endpoint — replacing that title keeps one H1 and adds no markup.
 */
function molosoc_thankyou_title( $title ) {
	$order = molosoc_thankyou_order();
	if ( ! $order ) {
		return $title;
	}
	return ( 'cz' === molosoc_thankyou_lang( $order ) ) ? 'Děkujeme za vaši objednávku.' : 'Thank you for your order.';
}
add_filter( 'woocommerce_endpoint_order-received_title', 'molosoc_thankyou_title' );

/**
 * WooCommerce's own confirmation line under the heading ("Thank you. Your
 * order has been received.") would repeat the hero word for word, so it
 * keeps only the confirmation half.
 */
function molosoc_thankyou_received_text( $text, $order = null ) {
	if ( ! $order instanceof WC_Order || ! molosoc_thankyou_order() ) {
		return $text;
	}
	return ( 'cz' === molosoc_thankyou_lang( $order ) ) ? 'Vaši objednávku jsme přijali.' : 'Your order has been received.';
}
add_filter( 'woocommerce_thankyou_order_received_text', 'molosoc_thankyou_received_text', 10, 2 );

/**
 * The sizes a gift pair can be ordered in right now, M before L, read from
 * the live variation objects (425 = M, 424 = L — see
 * inc/woocommerce-lang.php's header). A variation that is missing, not
 * purchasable or out of stock is simply not offered. 'price' is the
 * per-pair price as the shop displays it; nothing here is hard-coded.
 */
function molosoc_gift_sizes() {
	$sizes = array();
	foreach ( array( 'M' => 425, 'L' => 424 ) as $key => $variation_id ) {
		$variation = wc_get_product( $variation_id );
		if ( ! $variation instanceof WC_Product_Variation || MOLOSOC_PRODUCT_ID !== (int) $variation->get_parent_id() ) {
			continue;
		}
		if ( ! $variation->is_purchasable() || ! $variation->is_in_stock() ) {
			continue;
		}
		$sizes[ $key ] = array(
			'variation' => $variation,
			'label'     => molosoc_size_label_for_value( $key, $key ),
			'price'     => (float) wc_get_price_to_display( $variation ),
		);
	}
	return $sizes;
}

/**
 * A price as plain text ("229,00 Kč"), formatted by WooCommerce itself.
 */
function molosoc_gift_price_text( $amount ) {
	return trim( html_entity_decode( wp_strip_all_tags( wc_price( $amount ) ), ENT_QUOTES, 'UTF-8' ) );
}

/**
 * Checkout URL for a language, independent of the current request's own
 * language (the CZ twin when it is published, WooCommerce's page otherwise).
 */
function molosoc_gift_checkout_url( $lang ) {
	if ( 'cz' === $lang && function_exists( 'pll_get_post' ) ) {
		$cz_checkout_id = pll_get_post( wc_get_page_id( 'checkout' ), 'cz' );
		if ( $cz_checkout_id && 'publish' === get_post_status( $cz_checkout_id ) ) {
			return get_permalink( $cz_checkout_id );
		}
	}
	return wc_get_checkout_url();
}

/**
 * Gift add-on section, printed after WooCommerce's own order details
 * (woocommerce_order_details_table runs on this hook at priority 10).
 */
function molosoc_thankyou_gift_section( $order_id ) {
	$order = molosoc_thankyou_order();
	if ( ! $order || (int) $order_id !== (int) $order->get_id() ) {
		return;
	}
	$sizes = molosoc_gift_sizes();
	if ( ! $sizes ) {
		return;
	}

	$is_cz = 'cz' === molosoc_thankyou_lang( $order );
	$max   = MOLOSOC_GIFT_MAX_PAIRS;

	// One shared per-pair price when every offered size costs the same —
	// only then can a card state its own total before sizes are chosen.
	$prices     = array_unique( wp_list_pluck( $sizes, 'price' ) );
	$same_price = 1 === count( $prices );

	// Total for every possible M/L mix, formatted server-side by
	// WooCommerce; the script only looks the chosen mix up.
	$price_m = isset( $sizes['M'] ) ? $sizes['M']['price'] : 0;
	$price_l = isset( $sizes['L'] ) ? $sizes['L']['price'] : 0;
	$totals  = array();
	for ( $m = 0; $m <= ( isset( $sizes['M'] ) ? $max : 0 ); $m++ ) {
		for ( $l = 0; $l <= ( isset( $sizes['L'] ) ? $max : 0 ); $l++ ) {
			if ( $m + $l < 1 || $m + $l > $max ) {
				continue;
			}
			$totals[ $m . '-' . $l ] = molosoc_gift_price_text( $m * $price_m + $l * $price_l );
		}
	}

	$pairs_label = function ( $count ) use ( $is_cz ) {
		if ( $is_cz ) {
			return '+ ' . $count . ' ' . ( 1 === $count ? 'pár' : 'páry' );
		}
		return '+ ' . $count . ' ' . ( 1 === $count ? 'pair' : 'pairs' );
	};
	?>
	<section class="molosoc-gift" lang="<?php echo $is_cz ? 'cs' : 'en'; ?>" data-molosoc-gift data-totals="<?php echo esc_attr( wp_json_encode( $totals ) ); ?>">
		<figure class="molosoc-gift__photo">
			<img src="https://molosoc.com/wp-content/uploads/2026/01/Molosoc-Opening-Package-Mami.jpg"
				alt="<?php echo esc_attr( $is_cz ? 'Žaneta s maminkou si společně prohlížejí návlek MOLOSOC' : 'Žaneta and her mom looking at a MOLOSOC foot cover together' ); ?>"
				width="1290" height="1434" loading="lazy" decoding="async">
		</figure>

		<div class="molosoc-gift__body">
			<h2 class="molosoc-gift__title"><?php echo esc_html( $is_cz ? 'Ještě jedny pro někoho, koho máte rádi?' : 'One more for someone you love?' ); ?></h2>
			<p class="molosoc-gift__copy">
				<?php
				echo esc_html(
					$is_cz
						? 'MOLOSOC vznikl mezi mámou a dcerou. Pokud už máte jedny pro sebe, můžete přidat další pro mámu, partnera nebo kamarádku — protože popraskané paty opravdu nemusí být dárek, se kterým člověk žije.'
						: 'MOLOSOC started with a mom and daughter. If you already have yours, add another for your mom, partner or friend — because crusty, cracked feet don\'t have to be something they simply live with.'
				);
				?>
			</p>

			<form class="molosoc-gift__form" method="post" action="<?php echo esc_url( home_url( $is_cz ? '/cz/' : '/' ) ); ?>">
				<input type="hidden" name="molosoc_gift_lang" value="<?php echo $is_cz ? 'cz' : 'en'; ?>">

				<fieldset class="molosoc-gift__choices">
					<legend class="molosoc-visually-hidden"><?php echo esc_html( $is_cz ? 'Kolik párů přidat' : 'How many pairs to add' ); ?></legend>
					<?php for ( $count = 1; $count <= $max; $count++ ) : ?>
						<label class="molosoc-gift-card<?php echo $count > 1 ? ' molosoc-gift-card--multi' : ''; ?>">
							<input type="radio" name="molosoc_gift_pairs" value="<?php echo (int) $count; ?>"<?php checked( 1, $count ); ?>>
							<span class="molosoc-gift-card__face">
								<span class="molosoc-gift-card__count"><?php echo esc_html( $pairs_label( $count ) ); ?></span>
								<?php if ( $same_price ) : ?>
									<span class="molosoc-gift-card__price" translate="no"><?php echo esc_html( molosoc_gift_price_text( $count * reset( $prices ) ) ); ?></span>
								<?php endif; ?>
							</span>
						</label>
					<?php endfor; ?>
				</fieldset>

				<div class="molosoc-gift__sizes">
					<?php for ( $index = 0; $index < $max; $index++ ) : ?>
						<fieldset class="molosoc-gift-size" data-molosoc-gift-pair="<?php echo (int) ( $index + 1 ); ?>"<?php echo $index > 0 ? ' hidden disabled' : ''; ?>>
							<legend class="molosoc-gift-size__legend">
								<?php
								echo esc_html(
									$is_cz
										? sprintf( 'Velikost · %d. pár', $index + 1 )
										: sprintf( 'Size · pair %d', $index + 1 )
								);
								?>
							</legend>
							<?php foreach ( $sizes as $key => $size ) : ?>
								<label class="molosoc-gift-pill">
									<input type="radio" name="molosoc_gift_size[<?php echo (int) $index; ?>]" value="<?php echo esc_attr( $key ); ?>" required<?php checked( 1, count( $sizes ) ); ?>>
									<span class="molosoc-gift-pill__face" translate="no">
										<?php echo esc_html( $size['label'] ); ?>
										<?php if ( ! $same_price ) : ?>
											<span class="molosoc-gift-pill__price"><?php echo esc_html( molosoc_gift_price_text( $size['price'] ) ); ?></span>
										<?php endif; ?>
									</span>
								</label>
							<?php endforeach; ?>
						</fieldset>
					<?php endfor; ?>
				</div>

				<p class="molosoc-gift__total" data-molosoc-gift-total hidden>
					<span><?php echo esc_html( $is_cz ? 'Celkem' : 'Total' ); ?></span>
					<span class="molosoc-gift__total-amount" translate="no" data-molosoc-gift-total-amount></span>
					<span><?php echo esc_html( $is_cz ? '+ doprava' : '+ shipping' ); ?></span>
				</p>

				<button type="submit" class="molosoc-btn molosoc-gift__cta"><?php echo esc_html( $is_cz ? 'Přidat k objednávce' : 'Add to my order' ); ?></button>

				<p class="molosoc-gift__note">
					<?php
					echo esc_html(
						$is_cz
							? 'Dárkové páry vyřídíme jako novou, samostatnou objednávku s vlastní platbou a dopravou. Vaše právě dokončená objednávka zůstává beze změny.'
							: 'Gift pairs are placed as a new, separate order with its own payment and shipping. The order you just completed stays exactly as it is.'
					);
					?>
				</p>
			</form>
		</div>
	</section>
	<?php
}
add_action( 'woocommerce_thankyou', 'molosoc_thankyou_gift_section', 20 );

/**
 * Handle the gift form: add the chosen pairs to the cart through
 * WooCommerce's own add_to_cart() (so its stock, purchasability and
 * validation rules all apply) and continue to the normal checkout in the
 * form's language. Never reads, edits or charges an existing order.
 *
 * Runs on wp_loaded at priority 20, the same point WooCommerce's own
 * add-to-cart form handler uses (session and cart are ready). A missing or
 * unavailable size is never guessed at: the customer is sent to the
 * product page to choose there instead.
 */
function molosoc_gift_add_to_cart_action() {
	// phpcs:disable WordPress.Security.NonceVerification.Missing -- adds catalogue items to the visitor's own cart, exactly what WooCommerce's nonce-less ?add-to-cart= already allows.
	if ( ! isset( $_POST['molosoc_gift_pairs'] ) || ! function_exists( 'WC' ) || ! WC()->cart ) {
		return;
	}

	$lang   = ( isset( $_POST['molosoc_gift_lang'] ) && 'cz' === $_POST['molosoc_gift_lang'] ) ? 'cz' : 'en';
	$pairs  = min( MOLOSOC_GIFT_MAX_PAIRS, max( 1, absint( wp_unslash( $_POST['molosoc_gift_pairs'] ) ) ) );
	$posted = ( isset( $_POST['molosoc_gift_size'] ) && is_array( $_POST['molosoc_gift_size'] ) ) ? wp_unslash( $_POST['molosoc_gift_size'] ) : array();
	// phpcs:enable WordPress.Security.NonceVerification.Missing

	wc_nocache_headers();

	$sizes  = molosoc_gift_sizes();
	$counts = array();
	for ( $index = 0; $index < $pairs; $index++ ) {
		$key = ( isset( $posted[ $index ] ) && is_string( $posted[ $index ] ) ) ? strtoupper( sanitize_text_field( $posted[ $index ] ) ) : '';
		if ( ! isset( $sizes[ $key ] ) ) {
			wp_safe_redirect( molosoc_product_url( $lang ) );
			exit;
		}
		$counts[ $key ] = isset( $counts[ $key ] ) ? $counts[ $key ] + 1 : 1;
	}

	$added = false;
	foreach ( $counts as $key => $quantity ) {
		$variation = $sizes[ $key ]['variation'];
		if ( WC()->cart->add_to_cart( MOLOSOC_PRODUCT_ID, $quantity, $variation->get_id(), $variation->get_variation_attributes() ) ) {
			$added = true;
		}
	}

	wp_safe_redirect( $added ? molosoc_gift_checkout_url( $lang ) : molosoc_product_url( $lang ) );
	exit;
}
add_action( 'wp_loaded', 'molosoc_gift_add_to_cart_action', 20 );
