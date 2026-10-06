<?php
/**
 * Bilingual Thank You / Order Received page — hero heading plus a
 * post-purchase gift add-on section (GitHub Issues #106, #108).
 *
 * The paid order is NEVER modified and the customer is NEVER charged from
 * this page. The Comgate plugin is not vendored in this repository, so no
 * tokenised "one-click" charge can be confirmed safe; the gift CTA instead
 * adds the chosen pairs to the cart and sends the customer through the
 * normal, unchanged checkout as a new order that is LINKED to the original
 * one (#108):
 *   - shipping is 0 — one "Ships with order #N" rate replaces the normal
 *     rates while the cart is linked, since the customer already paid
 *     shipping on the original order;
 *   - the checkout address is pre-filled from the original order;
 *   - the new order carries `_molosoc_gift_parent_order`, both orders get
 *     a private order note, and the admin order screen shows the link, so
 *     fulfilment packs the two together.
 * The link lives in the WooCommerce session between the Thank You page
 * and checkout, and is re-validated against the original order every time
 * it is used. The offer only appears while the original order can still be
 * combined: processing/on-hold (never completed = dispatched), placed
 * within MOLOSOC_GIFT_WINDOW_HOURS, and not itself a gift add-on.
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

// How long after the original order was placed the gift add-on (and its
// "ships with your original order" promise) is still offered. JUDGMENT
// CALL: the real dispatch cadence isn't known from this repository; the
// status gate (never a completed order) is the hard rule, this window is
// the safety margin on top of it.
if ( ! defined( 'MOLOSOC_GIFT_WINDOW_HOURS' ) ) {
	define( 'MOLOSOC_GIFT_WINDOW_HOURS', 24 );
}

// Order meta on the gift order pointing at the original order; session key
// carrying the link from the Thank You page to checkout.
if ( ! defined( 'MOLOSOC_GIFT_PARENT_META' ) ) {
	define( 'MOLOSOC_GIFT_PARENT_META', '_molosoc_gift_parent_order' );
}
if ( ! defined( 'MOLOSOC_GIFT_SESSION_KEY' ) ) {
	define( 'MOLOSOC_GIFT_SESSION_KEY', 'molosoc_gift_parent' );
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
 * True while gift pairs can still be packed together with $order: it is
 * paid and not dispatched (processing only: on-hold means payment is still
 * unconfirmed and may yet fail, a completed order has left the building), it
 * was placed within the window,
 * it is not itself a gift add-on (one link only, never a chain), and no
 * add-on has already been confirmed for it (order-backed, so a stale session
 * link in any browser can never grant a second free shipping).
 * Used by the Thank You page to decide whether to show the offer at all,
 * and again by the cart/checkout hooks before they rely on the link.
 */
function molosoc_gift_can_ship_with( $order ) {
	if ( ! $order instanceof WC_Order || ! $order->has_status( 'processing' ) ) {
		return false;
	}
	if ( '' !== (string) $order->get_meta( MOLOSOC_GIFT_PARENT_META ) ) {
		return false;
	}
	$created = $order->get_date_created();
	if ( ! $created ) {
		return false;
	}
	if ( ( time() - $created->getTimestamp() ) > MOLOSOC_GIFT_WINDOW_HOURS * HOUR_IN_SECONDS ) {
		return false;
	}
	return ! molosoc_gift_has_confirmed_addon( $order );
}

/**
 * True once a gift add-on for $order has been confirmed (noted, or sent to
 * manual handling). Read from the add-on orders' own meta, not the session,
 * because the payment confirmation can arrive in a gateway's server-to-server
 * request that has no access to the shopper's browser session.
 */
function molosoc_gift_has_confirmed_addon( $order ) {
	$found = wc_get_orders(
		array(
			'limit'      => 1,
			'return'     => 'ids',
			'status'     => 'any',
			'meta_query' => array(
				array( 'key' => MOLOSOC_GIFT_PARENT_META, 'value' => $order->get_id() ),
				array( 'key' => MOLOSOC_GIFT_PARENT_META . '_noted', 'compare' => 'EXISTS' ),
			),
		)
	);
	return ! empty( $found );
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
 * keeps only the confirmation half. A gift add-on order's own Thank You
 * page adds which order it ships with.
 */
function molosoc_thankyou_received_text( $text, $order = null ) {
	if ( ! $order instanceof WC_Order || ! molosoc_thankyou_order() ) {
		return $text;
	}
	$is_cz  = 'cz' === molosoc_thankyou_lang( $order );
	$text   = $is_cz ? 'Vaši objednávku jsme přijali.' : 'Your order has been received.';
	$parent = molosoc_gift_parent_order( $order );
	// Promised only once payment confirmation linked the orders ('yes'): not while
	// payment is still pending (unset), nor when routed to manual handling.
	if ( $parent && 'yes' === (string) $order->get_meta( MOLOSOC_GIFT_PARENT_META . '_noted' ) ) {
		$text .= ' ' . sprintf(
			$is_cz ? 'Pošleme ji společně s objednávkou č. %s.' : 'It ships together with order #%s.',
			$parent->get_order_number()
		);
	}
	return $text;
}
add_filter( 'woocommerce_thankyou_order_received_text', 'molosoc_thankyou_received_text', 10, 2 );

/**
 * The original order a gift add-on order points at, or null.
 */
function molosoc_gift_parent_order( $order ) {
	if ( ! $order instanceof WC_Order ) {
		return null;
	}
	$parent_id = absint( $order->get_meta( MOLOSOC_GIFT_PARENT_META ) );
	$parent    = $parent_id ? wc_get_order( $parent_id ) : false;
	return $parent instanceof WC_Order ? $parent : null;
}

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
 * Only while the order can still ship together with the gift pairs — the
 * section's whole promise is "no additional shipping", so it is not shown
 * at all once that can't be kept.
 */
function molosoc_thankyou_gift_section( $order_id ) {
	$order = molosoc_thankyou_order();
	if ( ! $order || (int) $order_id !== (int) $order->get_id() || ! molosoc_gift_can_ship_with( $order ) ) {
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
						? 'MOLOSOC vznikl mezi mámou a dcerou. Pokud už máte jedny pro sebe, přidejte další pro maminku, partnera nebo kamarádku — malý dárek, který jim pomůže pečovat o nohy stejně jednoduše.'
						: 'MOLOSOC started with a mom and daughter. If you already have yours, add one for your mom, partner or friend — a small gift that helps them take better care of their feet, too.'
				);
				?>
			</p>

			<form class="molosoc-gift__form" method="post" action="<?php echo esc_url( home_url( $is_cz ? '/cz/' : '/' ) ); ?>">
				<input type="hidden" name="molosoc_gift_lang" value="<?php echo $is_cz ? 'cz' : 'en'; ?>">
				<input type="hidden" name="molosoc_gift_order" value="<?php echo (int) $order->get_id(); ?>">
				<input type="hidden" name="molosoc_gift_key" value="<?php echo esc_attr( $order->get_order_key() ); ?>">

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
				</p>
				<p class="molosoc-gift__shipping">
					<?php echo esc_html( $is_cz ? 'Pošleme s vaší původní objednávkou — bez dalšího poštovného.' : 'Ships with your original order — no additional shipping.' ); ?>
				</p>

				<button type="submit" class="molosoc-btn molosoc-gift__cta"><?php echo esc_html( $is_cz ? 'Přidat dárkové páry' : 'Add gift pairs' ); ?></button>

				<p class="molosoc-gift__note">
					<?php
					echo esc_html(
						$is_cz
							? 'Přibalíme je k objednávce, kterou jste právě vytvořili, takže další dopravu neplatíte. Dárkové páry zaplatíte zvlášť v pokladně.'
							: 'We’ll pack them with the order you just placed, so you won’t pay shipping again. You pay for the gift pairs separately at checkout.'
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
 * validation rules all apply), remember which original order they ship
 * with, pre-fill the checkout address from that order, and continue to the
 * normal checkout in the form's language. Never reads, edits or charges an
 * existing order.
 *
 * Runs on wp_loaded at priority 20, the same point WooCommerce's own
 * add-to-cart form handler uses (session and cart are ready). A missing or
 * unavailable size is never guessed at, and a form whose original order can
 * no longer ship together is not honoured: in both cases the customer is
 * sent to the product page (where nothing about combined shipping is
 * promised) to choose there instead.
 */
function molosoc_gift_add_to_cart_action() {
	// phpcs:disable WordPress.Security.NonceVerification.Missing -- adds catalogue items to the visitor's own cart, exactly what WooCommerce's nonce-less ?add-to-cart= already allows; the original order is only read, and only with its order key.
	if ( ! isset( $_POST['molosoc_gift_pairs'] ) || ! function_exists( 'WC' ) || ! WC()->cart ) {
		return;
	}

	$lang      = ( isset( $_POST['molosoc_gift_lang'] ) && 'cz' === $_POST['molosoc_gift_lang'] ) ? 'cz' : 'en';
	$pairs     = min( MOLOSOC_GIFT_MAX_PAIRS, max( 1, absint( wp_unslash( $_POST['molosoc_gift_pairs'] ) ) ) );
	$posted    = ( isset( $_POST['molosoc_gift_size'] ) && is_array( $_POST['molosoc_gift_size'] ) ) ? wp_unslash( $_POST['molosoc_gift_size'] ) : array();
	$parent_id = isset( $_POST['molosoc_gift_order'] ) ? absint( wp_unslash( $_POST['molosoc_gift_order'] ) ) : 0;
	$order_key = isset( $_POST['molosoc_gift_key'] ) && is_string( $_POST['molosoc_gift_key'] ) ? wc_clean( wp_unslash( $_POST['molosoc_gift_key'] ) ) : '';
	// phpcs:enable WordPress.Security.NonceVerification.Missing

	wc_nocache_headers();

	// The original order must be the one this form was printed for (order
	// key, exactly like the Thank You page itself) and must still be able
	// to ship together with the gift pairs — otherwise the "no additional
	// shipping" promise on that page can't be kept, and nothing is added.
	$parent = $parent_id ? wc_get_order( $parent_id ) : false;
	if ( ! $parent instanceof WC_Order
		|| '' === $order_key
		|| ! hash_equals( $parent->get_order_key(), $order_key )
		|| ! molosoc_gift_can_ship_with( $parent )
	) {
		wp_safe_redirect( molosoc_product_url( $lang ) );
		exit;
	}

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

	// All or nothing: if any size can't be added (e.g. not enough stock for
	// two of the same size), put the cart back exactly as it was before
	// this request and send the customer to the product page, where
	// WooCommerce's own notice explains why — never on to checkout with
	// only part of what they chose.
	$cart    = WC()->cart;
	$restore = array();
	$wanted  = array();
	$failed  = false;
	foreach ( $counts as $key => $quantity ) {
		$variation  = $sizes[ $key ]['variation'];
		$attributes = $variation->get_variation_attributes();
		$existing   = $cart->find_product_in_cart( $cart->generate_cart_id( MOLOSOC_PRODUCT_ID, $variation->get_id(), $attributes ) );
		$line       = $existing ? $cart->get_cart_item( $existing ) : array();
		$before     = isset( $line['quantity'] ) ? (int) $line['quantity'] : 0;
		if ( $before > 0 ) {
			// Never merge into, or shrink, a row the shopper already had.
			$failed = true;
			break;
		}

		$item_key = $cart->add_to_cart( MOLOSOC_PRODUCT_ID, $quantity, $variation->get_id(), $attributes );
		if ( ! $item_key ) {
			$failed = true;
			break;
		}
		$restore[ $item_key ] = $before;
		$wanted[ $item_key ]  = $quantity;
	}

	if ( $failed ) {
		foreach ( $restore as $item_key => $before ) {
			if ( $before > 0 ) {
				$cart->set_quantity( $item_key, $before );
			} else {
				$cart->remove_cart_item( $item_key );
			}
		}
		wp_safe_redirect( molosoc_product_url( $lang ) );
		exit;
	}

	// The free rate must cover exactly the rows chosen on this form. A cart
	// that also holds anything else (another product added in another tab,
	// another size of the gift) is never emptied behind the shopper's back:
	// the add is rolled back like a failed one and they choose on the product
	// page instead. Rows of the chosen sizes are pinned to the submitted
	// quantities, so a pre-loaded row or a repeated submit can never
	// accumulate more than MOLOSOC_GIFT_MAX_PAIRS pairs at shipping 0.
	foreach ( array_keys( $cart->get_cart() ) as $item_key ) {
		if ( ! isset( $wanted[ $item_key ] ) ) {
			$failed = true;
			break;
		}
	}
	if ( $failed ) {
		foreach ( $restore as $item_key => $before ) {
			if ( $before > 0 ) {
				$cart->set_quantity( $item_key, $before );
			} else {
				$cart->remove_cart_item( $item_key );
			}
		}
		wp_safe_redirect( molosoc_product_url( $lang ) );
		exit;
	}
	foreach ( $wanted as $item_key => $quantity ) {
		$cart->set_quantity( $item_key, $quantity );
	}

	molosoc_gift_link_cart_to_order( $parent, $lang, $wanted );

	wp_safe_redirect( molosoc_gift_checkout_url( $lang ) );
	exit;
}
add_action( 'wp_loaded', 'molosoc_gift_add_to_cart_action', 20 );

/**
 * Remember, in the WooCommerce session, which original order this cart's
 * gift pairs ship with, and pre-fill the checkout address from it. The
 * session link stores the order key too, so every later reader re-checks
 * it is still the same, still-combinable order rather than trusting the
 * session blindly. Copying the address is the same data the customer just
 * saw on their own Thank You page; setters that reject a value (e.g. an
 * invalid email) are simply skipped. 'lines' (cart item key => quantity) is
 * the exact set of rows the form added; see molosoc_gift_cart_link().
 */
function molosoc_gift_link_cart_to_order( $parent, $lang, $lines ) {
	if ( ! WC()->session ) {
		return;
	}
	WC()->session->set(
		MOLOSOC_GIFT_SESSION_KEY,
		array(
			'order_id' => $parent->get_id(),
			'key'      => $parent->get_order_key(),
			'lang'     => $lang,
			'lines'    => $lines,
			'time'     => time(),
		)
	);
	$customer = WC()->customer;
	if ( ! $customer ) {
		return;
	}
	foreach ( array( 'billing', 'shipping' ) as $type ) {
		foreach ( (array) $parent->get_address( $type ) as $field => $value ) {
			$setter = 'set_' . $type . '_' . $field;
			// Blank parent fields clear the session's stale value too, so the
			// checkout address is exactly the original order's.
			if ( ! method_exists( $customer, $setter ) ) {
				continue;
			}
			try {
				$customer->$setter( $value );
			} catch ( Exception $e ) {
				continue;
			}
		}
	}
	// WC()->customer is the session-backed customer: save() serialises it into
	// the WooCommerce session only (WC_Customer_Data_Store_Session), without
	// touching the account's stored address. Without it the redirect to checkout
	// would reload the previous address.
	$customer->save();
}

/**
 * The original order the current cart is linked to, re-validated: the
 * session link must name an order whose key still matches and that can
 * still ship together, and the cart must hold exactly the rows and quantities
 * the gift form added (so the free rate never covers anything else, e.g. a
 * pre-loaded or later-increased quantity). Null otherwise.
 * Returns array( 'order' => WC_Order, 'lang' => 'cz'|'en' ).
 */
function molosoc_gift_cart_link() {
	if ( ! function_exists( 'WC' ) || ! WC()->session || ! WC()->cart ) {
		return null;
	}
	$link = WC()->session->get( MOLOSOC_GIFT_SESSION_KEY );
	if ( ! is_array( $link ) || empty( $link['order_id'] ) || empty( $link['key'] ) ) {
		return null;
	}
	$parent = wc_get_order( absint( $link['order_id'] ) );
	if ( ! $parent instanceof WC_Order
		|| ! hash_equals( $parent->get_order_key(), (string) $link['key'] )
		|| ! molosoc_gift_can_ship_with( $parent )
	) {
		return null;
	}
	$lines = ( isset( $link['lines'] ) && is_array( $link['lines'] ) ) ? $link['lines'] : array();
	$items = WC()->cart->get_cart();
	if ( empty( $items ) || empty( $lines ) || count( $items ) !== count( $lines ) || array_sum( $lines ) > MOLOSOC_GIFT_MAX_PAIRS ) {
		return null;
	}
	foreach ( $items as $key => $item ) {
		if ( ! isset( $lines[ $key ], $item['product_id'], $item['quantity'] )
			|| MOLOSOC_PRODUCT_ID !== (int) $item['product_id']
			|| (int) $lines[ $key ] !== (int) $item['quantity']
		) {
			return null;
		}
	}
	return array(
		'order' => $parent,
		'lang'  => ( isset( $link['lang'] ) && 'cz' === $link['lang'] ) ? 'cz' : 'en',
	);
}

/**
 * While the cart is linked to an original order, the only shipping option
 * is a single 0-cost "Ships with order #N" rate — the customer already paid
 * shipping on that order. Replacing (not reducing) the normal rates
 * means no pickup-point or carrier choice is asked for again; fulfilment
 * ships the add-on inside the original parcel. WooCommerce runs this
 * filter for the classic checkout and the Store API (block cart/checkout)
 * alike, after its own rate cache, so it applies on every recalculation.
 */
function molosoc_gift_shipping_rates( $rates, $package ) {
	$link = molosoc_gift_cart_link();
	if ( ! $link ) {
		return $rates;
	}
	$is_cz = ( function_exists( 'pll_current_language' ) && pll_current_language() )
		? ( 'cz' === pll_current_language() )
		: ( 'cz' === $link['lang'] );
	$label = sprintf(
		$is_cz ? 'Pošleme s objednávkou č. %s — bez dalšího poštovného' : 'Ships with order #%s — no additional shipping',
		$link['order']->get_order_number()
	);
	$rate = new WC_Shipping_Rate( 'molosoc_gift_combined', $label, 0, array(), 'molosoc_gift_combined', 0 );
	return array( 'molosoc_gift_combined' => $rate );
}
add_filter( 'woocommerce_package_rates', 'molosoc_gift_shipping_rates', 100, 2 );

/**
 * WooCommerce caches a package's rates under a hash of the package (contents,
 * destination, ...) and only runs woocommerce_package_rates on a cache miss.
 * Whether the gift link is currently valid is not part of that hash, so a
 * cached 0-cost rate could outlive the link (parent expired or dispatched) and
 * cached paid rates could survive linking an otherwise unchanged cart. Put the
 * linked order's ID (0 when there is no valid link) into every package: the
 * hash changes exactly when the link's validity does, forcing a recalculation.
 */
function molosoc_gift_shipping_package_state( $packages ) {
	$link  = molosoc_gift_cart_link();
	$state = $link ? $link['order']->get_id() : 0;
	foreach ( (array) $packages as $i => $package ) {
		$packages[ $i ]['molosoc_gift_parent'] = $state;
	}
	return $packages;
}
add_filter( 'woocommerce_cart_shipping_packages', 'molosoc_gift_shipping_package_state', 100, 1 );

/**
 * Stamp the new order with the original order's ID the moment checkout
 * creates it. Classic checkout fires woocommerce_checkout_create_order
 * (before the order is saved); the block checkout's Store API fires
 * woocommerce_store_api_checkout_update_order_meta instead (WooCommerce
 * saves the order right after). Both hooks pass the new order first.
 */
function molosoc_gift_stamp_new_order( $order ) {
	if ( ! $order instanceof WC_Order ) {
		return;
	}
	$link = molosoc_gift_cart_link();
	if ( ! $link ) {
		return;
	}
	$order->update_meta_data( MOLOSOC_GIFT_PARENT_META, $link['order']->get_id() );
}
add_action( 'woocommerce_checkout_create_order', 'molosoc_gift_stamp_new_order', 10, 1 );
add_action( 'woocommerce_store_api_checkout_update_order_meta', 'molosoc_gift_stamp_new_order', 10, 1 );

/**
 * Once the new order's payment is confirmed: a private order note on BOTH
 * orders so fulfilment sees the link from either side. Deliberately NOT run
 * when the order is merely created (the gateway may still reject it or the
 * shopper abandon the redirect) and NOT on on-hold, which WooCommerce defines
 * as awaiting payment: an offline/delayed method's add-on stays linked by its
 * meta and admin line, and gets its notes when it reaches processing or
 * payment_complete fires. The original order is re-validated at this moment
 * (it may have been dispatched, or the window may have passed, while the
 * add-on was being paid); if it can no longer ship together, only the add-on
 * order gets a note, telling fulfilment to handle it manually, and the
 * original order is left alone. Notes are admin-only (never emailed to the
 * customer) and are the only thing ever written to the original order.
 * Idempotent via a meta flag, since several of these hooks fire for one
 * successful order. The shopper's session link is not touched here (this can
 * run in a gateway callback with another session); molosoc_gift_can_ship_with()
 * stops honouring it once the flag exists.
 */
function molosoc_gift_note_orders( $order ) {
	if ( ! $order instanceof WC_Order ) {
		return;
	}
	$parent = molosoc_gift_parent_order( $order );
	if ( ! $parent || '' !== (string) $order->get_meta( MOLOSOC_GIFT_PARENT_META . '_noted' ) ) {
		return;
	}
	if ( ! molosoc_gift_can_ship_with( $parent ) ) {
		$order->add_order_note(
			sprintf(
				'POZOR: původní objednávka č. %1$s už nejde odeslat společně (odeslána, mimo časové okno nebo už má jiný doplněk) — vyřiďte ručně, poštovné 0 bylo účtováno. / ATTENTION: original order #%1$s can no longer ship together (dispatched, outside the window or already has another add-on) — handle manually, shipping 0 was charged.',
				$parent->get_order_number()
			)
		);
		$order->update_meta_data( MOLOSOC_GIFT_PARENT_META . '_noted', 'manual' );
		$order->save();
		return;
	}
	$pairs = 0;
	foreach ( $order->get_items() as $item ) {
		$pairs += (int) $item->get_quantity();
	}
	$order->add_order_note(
		sprintf(
			'Dárkový doplněk k objednávce č. %1$s — odeslat společně s ní, poštovné 0 (zákazník ho zaplatil v objednávce č. %1$s). / Gift add-on to order #%1$s — ship together with it, shipping 0 (paid on #%1$s).',
			$parent->get_order_number()
		)
	);
	$parent->add_order_note(
		sprintf(
			'Dárkový doplněk: objednávka č. %1$s (%2$d ks) — odeslat společně s touto objednávkou. / Gift add-on: order #%1$s (%2$d pairs) — ship together with this order.',
			$order->get_order_number(),
			$pairs
		)
	);
	$order->update_meta_data( MOLOSOC_GIFT_PARENT_META . '_noted', 'yes' );
	$order->save();
}

function molosoc_gift_note_orders_by_id( $order_id ) {
	molosoc_gift_note_orders( wc_get_order( $order_id ) );
}
add_action( 'woocommerce_payment_complete', 'molosoc_gift_note_orders_by_id', 10, 1 );
add_action( 'woocommerce_order_status_processing', 'molosoc_gift_note_orders_by_id', 10, 1 );

/**
 * Drop the shopper's session link on the add-on order's own Thank You page,
 * a browser request with the shopper's own session, so a later unrelated
 * purchase from the same browser is a normal order.
 */
function molosoc_gift_clear_session_link( $order_id ) {
	$order  = wc_get_order( $order_id );
	$parent = molosoc_gift_parent_order( $order );
	if ( ! $parent || ! function_exists( 'WC' ) || ! WC()->session ) {
		return;
	}
	// Only the link this add-on consumed: a gift checkout already started for
	// another original order (another tab) keeps its own link.
	$link = WC()->session->get( MOLOSOC_GIFT_SESSION_KEY );
	if ( is_array( $link ) && isset( $link['order_id'] ) && absint( $link['order_id'] ) === $parent->get_id() ) {
		WC()->session->set( MOLOSOC_GIFT_SESSION_KEY, null );
	}
}
add_action( 'woocommerce_thankyou', 'molosoc_gift_clear_session_link', 5, 1 );

/**
 * Admin order screen: one line under the order details naming the original
 * order (linked) so the relationship is visible without opening the notes.
 */
function molosoc_gift_admin_order_line( $order ) {
	$parent = molosoc_gift_parent_order( $order );
	if ( ! $parent ) {
		return;
	}
	$manual = 'manual' === (string) $order->get_meta( MOLOSOC_GIFT_PARENT_META . '_noted' );
	printf(
		'<p class="form-field form-field-wide molosoc-gift-admin-link"><strong>%s</strong> <a href="%s">#%s</a> — %s</p>',
		esc_html( 'Dárkový doplněk k objednávce / Gift add-on to order' ),
		esc_url( $parent->get_edit_order_url() ),
		esc_html( $parent->get_order_number() ),
		esc_html( $manual ? 'nelze odeslat společně — vyřiďte ručně, poštovné 0 / cannot ship together — handle manually, shipping 0' : 'odeslat společně, poštovné 0 / ship together, shipping 0' )
	);
}
add_action( 'woocommerce_admin_order_data_after_order_details', 'molosoc_gift_admin_order_line', 10, 1 );
