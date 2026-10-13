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
 * Post-purchase pricing (#110): the offer depends on how many pairs the
 * ORIGINAL order held (product 364, all variations summed). One pair: up to
 * two more, the first for MOLOSOC_GIFT_PRICE_PAIR_2 and the second for
 * MOLOSOC_GIFT_PRICE_PAIR_3. Two pairs: exactly one more, at the pair-3
 * price. Three or more: no offer at all. These prices exist only inside
 * the linked cart: each gift pair is its own cart row carrying its overall
 * pair number, and the price comes from that number via the server-side
 * schedule — never from anything the browser submits — and only while
 * molosoc_gift_cart_link() re-validates the original order, its key, its
 * window/status and the exact rows. The product's own price is never
 * changed, so every other cart/product URL stays at the normal price, and
 * a link that stops being valid simply falls back to it.
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

// The most additional pairs any gift checkout can ever hold (an original
// order of one pair may add two). The real limit per order is
// molosoc_gift_offer()['max'].
if ( ! defined( 'MOLOSOC_GIFT_MAX_PAIRS' ) ) {
	define( 'MOLOSOC_GIFT_MAX_PAIRS', 2 );
}

// Unit price (CZK) of the 2nd and the 3rd pair overall, valid only inside the
// authenticated gift flow (#110). The pair number is the position counting
// the original order's pairs.
if ( ! defined( 'MOLOSOC_GIFT_PRICE_PAIR_2' ) ) {
	define( 'MOLOSOC_GIFT_PRICE_PAIR_2', 209 );
}
if ( ! defined( 'MOLOSOC_GIFT_PRICE_PAIR_3' ) ) {
	define( 'MOLOSOC_GIFT_PRICE_PAIR_3', 199 );
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
if ( ! defined( 'MOLOSOC_GIFT_PAID_SESSION_KEY' ) ) {
	define( 'MOLOSOC_GIFT_PAID_SESSION_KEY', 'molosoc_gift_paid_rows' );
}
if ( ! defined( 'MOLOSOC_GIFT_PARKED_SESSION_KEY' ) ) {
	define( 'MOLOSOC_GIFT_PARKED_SESSION_KEY', 'molosoc_gift_parked_rows' );
}
if ( ! defined( 'MOLOSOC_GIFT_SESSION_KEY' ) ) {
	define( 'MOLOSOC_GIFT_SESSION_KEY', 'molosoc_gift_parent' );
}

/**
 * The order the current order-received request is for, authenticated by the
 * order key from ?key= (same check WooCommerce's own thank-you shortcode
 * does), in ANY status, or null. Used where only the order's identity matters
 * (language switcher links), including a pending gateway return.
 */
function molosoc_thankyou_keyed_order() {
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
	return $order;
}

/**
 * The keyed order (see molosoc_thankyou_keyed_order()) only when it is a
 * successful purchase: null for failed/cancelled, or still pending payment (a
 * gateway return that hasn't been confirmed) — WooCommerce's own default
 * page is left completely untouched for those. Gates everything that renders
 * or acts on the gift offer.
 */
function molosoc_thankyou_order() {
	$order = molosoc_thankyou_keyed_order();
	if ( ! $order || ! $order->has_status( array( 'processing', 'completed', 'on-hold' ) ) ) {
		return null;
	}
	return $order;
}

/**
 * 'cz' or 'en' for the Thank You page: the language of the request (so the
 * language switcher on this page really switches the page, Issue #125),
 * falling back to the language the order was placed in (_molosoc_lang,
 * stamped at checkout by inc/woocommerce-lang.php) when the request has none.
 */
function molosoc_thankyou_lang( $order ) {
	$lang = function_exists( 'pll_current_language' ) ? pll_current_language() : '';
	if ( 'cz' !== $lang && 'en' !== $lang ) {
		$lang = ( $order instanceof WC_Order ) ? $order->get_meta( '_molosoc_lang' ) : '';
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
 * Pairs of the MOLOSOC product (all variations) held by an order.
 */
function molosoc_gift_original_qty( $order ) {
	$qty = 0;
	if ( ! $order instanceof WC_Order ) {
		return $qty;
	}
	foreach ( $order->get_items() as $item ) {
		if ( MOLOSOC_PRODUCT_ID === (int) $item->get_product_id() ) {
			$qty += (int) $item->get_quantity();
		}
	}
	return $qty;
}

/**
 * Unit price of the pair at overall position $slot (2 or 3), or null.
 */
function molosoc_gift_slot_price( $slot ) {
	$schedule = array(
		2 => (float) MOLOSOC_GIFT_PRICE_PAIR_2,
		3 => (float) MOLOSOC_GIFT_PRICE_PAIR_3,
	);
	return isset( $schedule[ $slot ] ) ? $schedule[ $slot ] : null;
}

/**
 * The gift offer $order is entitled to right now, or null for none: the order
 * must still be able to ship together (status, window, no add-on yet) and
 * hold one or two pairs. 'slots' are the overall pair numbers on offer
 * (original + 1 .. 3), 'prices' maps each to its server-side unit price and
 * 'max' is how many pairs may be added. Everything that grants a price asks
 * this, never the browser.
 */
function molosoc_gift_offer( $order ) {
	if ( ! molosoc_gift_can_ship_with( $order ) ) {
		return null;
	}
	// The schedule is in CZK; never apply it to another currency.
	if ( function_exists( 'get_woocommerce_currency' ) && 'CZK' !== get_woocommerce_currency() ) {
		return null;
	}
	$original = molosoc_gift_original_qty( $order );
	if ( $original < 1 || $original > 2 ) {
		return null;
	}
	$prices = array();
	for ( $slot = $original + 1; $slot <= 3; $slot++ ) {
		$prices[ $slot ] = molosoc_gift_slot_price( $slot );
	}
	return array(
		'original' => $original,
		'slots'    => array_keys( $prices ),
		'prices'   => $prices,
		'max'      => count( $prices ),
	);
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
		$mixed = molosoc_gift_has_other_lines( $order );
		$text .= ' ' . sprintf(
			$mixed
				? ( $is_cz ? 'Dárkové páry pošleme společně s objednávkou č. %s, ostatní položky zvlášť.' : 'The gift pairs ship together with order #%s; the other items ship separately.' )
				: ( $is_cz ? 'Pošleme ji společně s objednávkou č. %s.' : 'It ships together with order #%s.' ),
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
 * A price as plain text ("1 234,00 Kč"), formatted by WooCommerce itself.
 */
function molosoc_gift_price_text( $amount ) {
	return trim( html_entity_decode( wp_strip_all_tags( wc_price( $amount ) ), ENT_QUOTES, 'UTF-8' ) );
}

/**
 * Checkout page ID for a language, independent of the current request's own
 * language: WooCommerce's configured page is translated through Polylang
 * (the stored ID may itself be the Czech twin when the request is Czech).
 */
function molosoc_gift_checkout_page_id( $lang ) {
	$page_id = function_exists( 'wc_get_page_id' ) ? (int) wc_get_page_id( 'checkout' ) : 0;
	if ( $page_id > 0 && function_exists( 'pll_get_post' ) ) {
		$translated = (int) pll_get_post( $page_id, 'cz' === $lang ? 'cz' : 'en' );
		if ( $translated && 'publish' === get_post_status( $translated ) ) {
			return $translated;
		}
	}
	return 0;
}

/**
 * Checkout URL for a language, independent of the current request's own
 * language (the translated twin when it is published, WooCommerce's page
 * otherwise).
 */
function molosoc_gift_checkout_url( $lang ) {
	$page_id = molosoc_gift_checkout_page_id( $lang );
	return $page_id ? get_permalink( $page_id ) : wc_get_checkout_url();
}

/**
 * Order-received URL of $order in $lang, or '' when the language's checkout
 * page is not a published twin. Built the way WooCommerce builds its own
 * (endpoint on the checkout permalink plus ?key=), so the order key stays
 * the only thing that opens it.
 */
function molosoc_gift_order_received_url( $order, $lang ) {
	$page_id = molosoc_gift_checkout_page_id( $lang );
	if ( ! $page_id || ! $order instanceof WC_Order || ! function_exists( 'wc_get_endpoint_url' ) ) {
		return '';
	}
	return add_query_arg( 'key', $order->get_order_key(), wc_get_endpoint_url( 'order-received', $order->get_id(), get_permalink( $page_id ) ) );
}

/**
 * Polylang's language switcher links to the translated checkout PAGE, which
 * drops the order-received endpoint and the order key: the shopper landed on
 * an empty checkout (Issue #125). On a valid Thank You page the switcher goes
 * to the same order in the other language instead; when that language has no
 * published checkout twin it stays on this order's page rather than opening a
 * cart-less checkout.
 */
function molosoc_thankyou_language_switcher_link( $url, $slug ) {
	$order = molosoc_thankyou_keyed_order();
	if ( ! $order || ( 'cz' !== $slug && 'en' !== $slug ) ) {
		return $url;
	}
	$target = molosoc_gift_order_received_url( $order, $slug );
	if ( '' !== $target ) {
		return $target;
	}
	$current = molosoc_gift_order_received_url( $order, function_exists( 'pll_current_language' ) && 'cz' === pll_current_language() ? 'cz' : 'en' );
	return '' !== $current ? $current : $url;
}
add_filter( 'pll_the_language_link', 'molosoc_thankyou_language_switcher_link', 20, 2 );

/**
 * Variation attributes for add_to_cart(). A variation whose size is "Any"
 * reports an empty value, which WooCommerce refuses ("choose product
 * options"); fill it from the parent's option matching the chosen size.
 */
function molosoc_gift_variation_attributes( $variation, $size_key ) {
	$attributes = (array) $variation->get_variation_attributes();
	$product    = null;
	foreach ( $attributes as $name => $value ) {
		if ( '' !== (string) $value ) {
			continue;
		}
		if ( null === $product ) {
			$product = wc_get_product( MOLOSOC_PRODUCT_ID );
		}
		$options = ( $product && method_exists( $product, 'get_variation_attributes' ) ) ? (array) $product->get_variation_attributes() : array();
		$options = isset( $options[ preg_replace( '/^attribute_/', '', $name ) ] ) ? (array) $options[ preg_replace( '/^attribute_/', '', $name ) ] : array();
		foreach ( $options as $option ) {
			if ( molosoc_size_value_rank( $option ) === ( 'M' === $size_key ? 0 : 1 ) ) {
				$attributes[ $name ] = $option;
				break;
			}
		}
	}
	return $attributes;
}

/**
 * Diagnostic line in WooCommerce's log (source molosoc-gift) for every way the
 * gift form can fall back to the product page, so a production report can be
 * traced to its reason. Never logs the order key.
 */
function molosoc_gift_log( $reason, $context = array() ) {
	if ( function_exists( 'wc_get_logger' ) ) {
		wc_get_logger()->warning( 'gift form fallback: ' . $reason . ' ' . wp_json_encode( $context ), array( 'source' => 'molosoc-gift' ) );
	}
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
	if ( ! $order || (int) $order_id !== (int) $order->get_id() ) {
		return;
	}
	// No offer (nothing rendered) for an original order of three or more
	// pairs, or one that can no longer ship together.
	$offer = molosoc_gift_offer( $order );
	if ( ! $offer ) {
		return;
	}
	$sizes = molosoc_gift_sizes();
	if ( ! $sizes ) {
		return;
	}

	$is_cz = 'cz' === molosoc_thankyou_lang( $order );
	$max   = $offer['max'];

	// Cumulative price of the first N additional pairs; the same for every
	// M/L mix, because the offer price does not depend on the size.
	$cumulative = array( 0 => 0.0 );
	foreach ( array_values( $offer['prices'] ) as $index => $price ) {
		$cumulative[ $index + 1 ] = $cumulative[ $index ] + $price;
	}
	$first_price  = reset( $offer['prices'] );
	$second_price = ( $max > 1 ) ? next( $offer['prices'] ) : null;

	// Total for every possible M/L mix, formatted by WooCommerce; the script
	// only looks the chosen mix up.
	$totals = array();
	for ( $m = 0; $m <= ( isset( $sizes['M'] ) ? $max : 0 ); $m++ ) {
		for ( $l = 0; $l <= ( isset( $sizes['L'] ) ? $max : 0 ); $l++ ) {
			if ( $m + $l < 1 || $m + $l > $max ) {
				continue;
			}
			$totals[ $m . '-' . $l ] = molosoc_gift_price_text( $cumulative[ $m + $l ] );
		}
	}

	$money = function ( $amount ) use ( $is_cz ) {
		$text = ( floor( $amount ) === (float) $amount ) ? (string) (int) $amount : number_format( $amount, 2, ',', '' );
		return $text . "\xC2\xA0" . ( $is_cz ? 'Kč' : 'CZK' );
	};
	if ( 1 === $max ) {
		$offer_line = $is_cz
			? sprintf( 'Přidejte třetí pár za %s.', $money( $first_price ) )
			: sprintf( 'Add a third pair for %s.', $money( $first_price ) );
		$offer_note = '';
	} else {
		$offer_line = $is_cz
			? sprintf( 'Přidejte další za %1$s — nebo dva za %2$s celkem.', $money( $first_price ), $money( $cumulative[2] ) )
			: sprintf( 'Add another for %1$s — or two for %2$s total.', $money( $first_price ), $money( $cumulative[2] ) );
		$offer_note = $is_cz
			? sprintf( 'Druhý přidaný pár stojí %s.', $money( $second_price ) )
			: sprintf( 'The second additional pair is %s.', $money( $second_price ) );
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
			<p class="molosoc-gift__offer" translate="no"><strong><?php echo esc_html( $offer_line ); ?></strong>
				<?php if ( '' !== $offer_note ) : ?>
					<span class="molosoc-gift__offer-note"><?php echo esc_html( $offer_note ); ?></span>
				<?php endif; ?>
			</p>

			<form class="molosoc-gift__form" method="post" action="<?php echo esc_url( home_url( $is_cz ? '/cz/' : '/' ) ); ?>">
				<input type="hidden" name="molosoc_gift_lang" value="<?php echo $is_cz ? 'cz' : 'en'; ?>">
				<input type="hidden" name="molosoc_gift_order" value="<?php echo (int) $order->get_id(); ?>">
				<input type="hidden" name="molosoc_gift_key" value="<?php echo esc_attr( $order->get_order_key() ); ?>">

				<?php if ( $max > 1 ) : ?>
					<fieldset class="molosoc-gift__choices molosoc-gift__choices--<?php echo (int) $max; ?>">
						<legend class="molosoc-visually-hidden"><?php echo esc_html( $is_cz ? 'Kolik párů přidat' : 'How many pairs to add' ); ?></legend>
						<?php for ( $count = 1; $count <= $max; $count++ ) : ?>
							<label class="molosoc-gift-card<?php echo $count > 1 ? ' molosoc-gift-card--multi' : ''; ?>">
								<input type="radio" name="molosoc_gift_pairs" value="<?php echo (int) $count; ?>"<?php checked( 1, $count ); ?>>
								<span class="molosoc-gift-card__face">
									<span class="molosoc-gift-card__count"><?php echo esc_html( $pairs_label( $count ) ); ?></span>
									<span class="molosoc-gift-card__price" translate="no"><?php echo esc_html( molosoc_gift_price_text( $cumulative[ $count ] ) ); ?></span>
								</span>
							</label>
						<?php endfor; ?>
					</fieldset>
				<?php else : ?>
					<input type="hidden" name="molosoc_gift_pairs" value="1">
				<?php endif; ?>

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
									<span class="molosoc-gift-pill__face" translate="no"><?php echo esc_html( $size['label'] ); ?></span>
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
 * Issue #145 provenance: remember, in the shopper's own WooCommerce session,
 * which cart rows the checkout that created this order consumed (cart item
 * key => variation and quantity). Product, variation and quantity alone never
 * prove a later cart row is that already-paid pair, so molosoc_gift_unpark_rows()
 * leaves a parked row out of the cart afterwards only when this record names it
 * (Issue #147: the record no longer gates the gift checkout itself; an order
 * placed before it existed, or in another browser, has none). Classic checkout
 * passes the order id, the Store API the order object; the cart still holds its
 * rows at this point.
 */
function molosoc_gift_remember_paid_rows( $order ) {
	$order_id = ( $order instanceof WC_Order ) ? $order->get_id() : absint( $order );
	if ( $order_id < 1 || ! function_exists( 'WC' ) || ! WC()->session || ! WC()->cart ) {
		return;
	}
	$rows = array();
	$gift = false;
	foreach ( WC()->cart->get_cart() as $item_key => $item ) {
		if ( isset( $item['molosoc_gift_slot'] ) ) {
			$gift = true;
			continue;
		}
		if ( ! isset( $item['product_id'] ) || MOLOSOC_PRODUCT_ID !== (int) $item['product_id'] ) {
			continue;
		}
		$rows[ $item_key ] = array(
			'variation' => isset( $item['variation_id'] ) ? (int) $item['variation_id'] : 0,
			'quantity'  => isset( $item['quantity'] ) ? (int) $item['quantity'] : 0,
		);
	}
	if ( $gift && ! $rows ) {
		// The gift add-on checkout consumed no paid pair: it must not overwrite the
		// record of the original order that the parked rows are judged by.
		return;
	}
	WC()->session->set(
		MOLOSOC_GIFT_PAID_SESSION_KEY,
		array(
			'order_id' => $order_id,
			'rows'     => $rows,
			'tainted'  => false,
		)
	);
}
add_action( 'woocommerce_checkout_order_processed', 'molosoc_gift_remember_paid_rows', 10, 1 );
add_action( 'woocommerce_store_api_checkout_order_processed', 'molosoc_gift_remember_paid_rows', 10, 1 );

/**
 * After the order, any product row the shopper adds or raises is theirs: the
 * record can no longer vouch that an identical-looking row is the paid pair
 * (a re-added pair has the very same cart item key), so it is voided. Gift
 * rows (the ones this flow adds) do not count.
 */
function molosoc_gift_void_paid_rows() {
	if ( ! function_exists( 'WC' ) || ! WC()->session ) {
		return;
	}
	$record = WC()->session->get( MOLOSOC_GIFT_PAID_SESSION_KEY );
	if ( is_array( $record ) && empty( $record['tainted'] ) ) {
		$record['tainted'] = true;
		WC()->session->set( MOLOSOC_GIFT_PAID_SESSION_KEY, $record );
	}
}

function molosoc_gift_void_paid_rows_on_add( $cart_id = '', $product_id = 0, $quantity = 1, $variation_id = 0, $variation = array(), $cart_item_data = array() ) {
	if ( is_array( $cart_item_data ) && isset( $cart_item_data['molosoc_gift_slot'] ) ) {
		return;
	}
	if ( MOLOSOC_PRODUCT_ID === (int) $product_id ) {
		molosoc_gift_void_paid_rows();
	}
}
add_action( 'woocommerce_add_to_cart', 'molosoc_gift_void_paid_rows_on_add', 10, 6 );

function molosoc_gift_void_paid_rows_on_quantity( $item_key = '', $quantity = 0, $old_quantity = 0 ) {
	if ( (int) $quantity > (int) $old_quantity ) {
		molosoc_gift_void_paid_rows();
	}
}
add_action( 'woocommerce_after_cart_item_quantity_update', 'molosoc_gift_void_paid_rows_on_quantity', 10, 3 );

/**
 * Diagnostic line (info level, source molosoc-gift) for a gift submission that
 * was accepted, so a production report can be traced through the whole flow, not
 * only through its fallbacks. Never logs the order key.
 */
function molosoc_gift_trace( $message, $context = array() ) {
	if ( function_exists( 'wc_get_logger' ) ) {
		wc_get_logger()->info( 'gift form: ' . $message . ' ' . wp_json_encode( $context ), array( 'source' => 'molosoc-gift' ) );
	}
}

/**
 * Cart rows as "key => variation x quantity" for the diagnostic log.
 */
function molosoc_gift_row_summary( $rows ) {
	$out = array();
	foreach ( (array) $rows as $item_key => $item ) {
		$out[ $item_key ] = ( isset( $item['product_id'] ) ? (int) $item['product_id'] : 0 ) . '/' . ( isset( $item['variation_id'] ) ? (int) $item['variation_id'] : 0 ) . 'x' . ( isset( $item['quantity'] ) ? (int) $item['quantity'] : 0 ) . ( isset( $item['molosoc_gift_slot'] ) ? ' gift' : '' );
	}
	return $out;
}

/**
 * Whether the session can vouch for the rows of $order's checkout: 'none' (no
 * record: an order placed before it existed, or in another browser), 'tainted',
 * 'other-order' or 'valid'. Diagnostics only.
 */
function molosoc_gift_paid_record_state( $order ) {
	$record = ( function_exists( 'WC' ) && WC()->session ) ? WC()->session->get( MOLOSOC_GIFT_PAID_SESSION_KEY ) : null;
	if ( ! is_array( $record ) ) {
		return 'none';
	}
	if ( ! $order instanceof WC_Order || ! isset( $record['order_id'] ) || (int) $record['order_id'] !== $order->get_id() ) {
		return 'other-order';
	}
	return empty( $record['tainted'] ) ? 'valid' : 'tainted';
}

/**
 * Keep the cart rows set aside for the add-on checkout in the shopper's own
 * session (Issue #147), in a form that survives serialisation: product,
 * variation, attributes, quantity and any other plain cart item data, minus
 * WooCommerce's computed fields and the gift marker (a parked gift-shaped row
 * returns as an ordinary row at the normal price). Rows parked by an earlier
 * submit for the same order that is still pending are kept and merged (another
 * order's park is unparked first, in the submit handler).
 */
function molosoc_gift_park_rows( $parent, $rows ) {
	if ( ! $rows || ! function_exists( 'WC' ) || ! WC()->session ) {
		return;
	}
	$park = WC()->session->get( MOLOSOC_GIFT_PARKED_SESSION_KEY );
	$kept = ( is_array( $park ) && isset( $park['rows'] ) && is_array( $park['rows'] ) ) ? $park['rows'] : array();
	foreach ( $rows as $item_key => $item ) {
		$quantity = isset( $item['quantity'] ) ? (int) $item['quantity'] : 0;
		if ( $quantity < 1 || ! isset( $item['product_id'] ) ) {
			continue;
		}
		$extra = array();
		foreach ( $item as $field => $value ) {
			if ( in_array( $field, array( 'key', 'product_id', 'variation_id', 'variation', 'quantity', 'data', 'data_hash', 'molosoc_gift_slot', 'line_tax_data', 'line_subtotal', 'line_subtotal_tax', 'line_total', 'line_tax' ), true ) ) {
				continue;
			}
			if ( is_scalar( $value ) || is_array( $value ) ) {
				$extra[ $field ] = $value;
			}
		}
		if ( isset( $kept[ $item_key ] ) ) {
			$kept[ $item_key ]['quantity'] = (int) $kept[ $item_key ]['quantity'] + $quantity;
			continue;
		}
		$kept[ $item_key ] = array(
			'product_id'   => (int) $item['product_id'],
			'variation_id' => isset( $item['variation_id'] ) ? (int) $item['variation_id'] : 0,
			'variation'    => ( isset( $item['variation'] ) && is_array( $item['variation'] ) ) ? $item['variation'] : array(),
			'quantity'     => $quantity,
			'extra'        => $extra,
		);
	}
	WC()->session->set(
		MOLOSOC_GIFT_PARKED_SESSION_KEY,
		array(
			'order_id' => $parent->get_id(),
			'rows'     => $kept,
		)
	);
}

/**
 * Put the parked rows back into the cart and forget them. A row (or the part of
 * its quantity) that the session PROVES is the pair the original order already
 * paid for (molosoc_gift_remember_paid_rows(), untainted, same order) is not put
 * back: it is bought, WooCommerce itself would have emptied it from the cart, and
 * restoring it would invite a second payment. Everything else returns, so a row
 * the session cannot vouch for is never lost. Returns how many rows came back.
 */
function molosoc_gift_unpark_rows() {
	if ( ! function_exists( 'WC' ) || ! WC()->session || ! WC()->cart ) {
		return 0;
	}
	$park = WC()->session->get( MOLOSOC_GIFT_PARKED_SESSION_KEY );
	if ( null === $park ) {
		return 0;
	}
	// Forget first: nothing below may run twice for the same rows.
	WC()->session->set( MOLOSOC_GIFT_PARKED_SESSION_KEY, null );
	if ( ! is_array( $park ) || empty( $park['rows'] ) || ! is_array( $park['rows'] ) ) {
		return 0;
	}
	$record = WC()->session->get( MOLOSOC_GIFT_PAID_SESSION_KEY );
	$proven = ( is_array( $record ) && empty( $record['tainted'] ) && isset( $record['order_id'], $record['rows'], $park['order_id'] )
		&& (int) $record['order_id'] === (int) $park['order_id'] && is_array( $record['rows'] ) )
		? $record['rows']
		: array();
	$todo = array();
	foreach ( $park['rows'] as $item_key => $row ) {
		$quantity = isset( $row['quantity'] ) ? (int) $row['quantity'] : 0;
		if ( isset( $proven[ $item_key ]['variation'], $proven[ $item_key ]['quantity'] )
			&& (int) $proven[ $item_key ]['variation'] === ( isset( $row['variation_id'] ) ? (int) $row['variation_id'] : 0 )
		) {
			$quantity -= (int) $proven[ $item_key ]['quantity'];
		}
		if ( $quantity > 0 && isset( $row['product_id'] ) ) {
			$todo[ $item_key ] = array( $row, $quantity );
		}
	}
	$restored = 0;
	$failed   = array();
	foreach ( $todo as $item_key => $pair ) {
		list( $row, $quantity ) = $pair;
		$added = WC()->cart->add_to_cart(
			(int) $row['product_id'],
			$quantity,
			isset( $row['variation_id'] ) ? (int) $row['variation_id'] : 0,
			( isset( $row['variation'] ) && is_array( $row['variation'] ) ) ? $row['variation'] : array(),
			( isset( $row['extra'] ) && is_array( $row['extra'] ) ) ? $row['extra'] : array()
		);
		if ( $added ) {
			$restored++;
		} else {
			// Keep only the unpaid remainder, so a retry never depends on proof that may change.
			$row['quantity']     = $quantity;
			$failed[ $item_key ] = $row;
			molosoc_gift_log( 'parked cart row could not be put back', array( 'row' => $item_key ) );
		}
	}
	if ( $failed ) {
		// Keep what WooCommerce refused (out of stock, validation filter) so a later request retries it.
		WC()->session->set(
			MOLOSOC_GIFT_PARKED_SESSION_KEY,
			array(
				'order_id' => isset( $park['order_id'] ) ? $park['order_id'] : 0,
				'rows'     => $failed,
			)
		);
	}
	molosoc_gift_trace( 'parked rows restored', array( 'parked' => count( $park['rows'] ), 'restored' => $restored ) );
	return $restored;
}

/**
 * Rows parked for an add-on checkout come back as soon as that checkout is no
 * longer the shopper's cart: on any page view where the cart is no longer
 * exactly the valid gift cart (the shopper added something, emptied it, the offer
 * lapsed). Not on an order-received page: WooCommerce empties the cart there, and
 * the add-on order's own Thank You page restores them afterwards.
 */
function molosoc_gift_maybe_unpark_rows() {
	if ( ! function_exists( 'WC' ) || ! WC()->session || null === WC()->session->get( MOLOSOC_GIFT_PARKED_SESSION_KEY ) ) {
		return;
	}
	if ( function_exists( 'is_wc_endpoint_url' ) && is_wc_endpoint_url( 'order-received' ) ) {
		return;
	}
	if ( molosoc_gift_cart_link() ) {
		return;
	}
	molosoc_gift_unpark_rows();
}
add_action( 'template_redirect', 'molosoc_gift_maybe_unpark_rows', 20 );

/**
 * The add-on order's own Thank You page (after WooCommerce emptied the cart and
 * the session link was dropped at priority 5): give the shopper back what was
 * parked for the checkout.
 */
function molosoc_gift_unpark_after_addon( $order_id ) {
	$parent = molosoc_gift_parent_order( wc_get_order( $order_id ) );
	if ( ! $parent || ! function_exists( 'WC' ) || ! WC()->session ) {
		return;
	}
	// Only the rows parked for this add-on: a newer gift checkout (another tab) keeps its own.
	$park = WC()->session->get( MOLOSOC_GIFT_PARKED_SESSION_KEY );
	if ( is_array( $park ) && isset( $park['order_id'] ) && absint( $park['order_id'] ) !== $parent->get_id() ) {
		return;
	}
	molosoc_gift_unpark_rows();
}
add_action( 'woocommerce_thankyou', 'molosoc_gift_unpark_after_addon', 6, 1 );

/**
 * Put rows this request set aside back into the cart exactly as they were
 * (key => cart item as WooCommerce held it). A replacement can share a set-aside
 * row's key; removing it overwrote WooCommerce's removed-items snapshot of that
 * row, so the original data is written back to the list before restoring.
 */
function molosoc_gift_restore_rows( $cart, $rows ) {
	$removed = $cart->get_removed_cart_contents();
	foreach ( $rows as $item_key => $item ) {
		$removed[ $item_key ] = $item;
	}
	$cart->set_removed_cart_contents( $removed );
	foreach ( array_keys( $rows ) as $item_key ) {
		$cart->restore_cart_item( $item_key );
	}
}

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
 * promised) to choose there instead. A VALID submission never is, whatever
 * the cart held before (Issues #125, #147: other rows are parked, not judged);
 * every fallback is logged (molosoc-gift).
 */
function molosoc_gift_add_to_cart_action() {
	// phpcs:disable WordPress.Security.NonceVerification.Missing -- adds catalogue items to the visitor's own cart, exactly what WooCommerce's nonce-less ?add-to-cart= already allows; the original order is only read, and only with its order key.
	if ( ! isset( $_POST['molosoc_gift_pairs'] ) || ! function_exists( 'WC' ) || ! WC()->cart ) {
		return;
	}

	$lang      = ( isset( $_POST['molosoc_gift_lang'] ) && 'cz' === $_POST['molosoc_gift_lang'] ) ? 'cz' : 'en';
	$pairs     = is_string( $_POST['molosoc_gift_pairs'] ) ? absint( wp_unslash( $_POST['molosoc_gift_pairs'] ) ) : 0;
	$posted    = ( isset( $_POST['molosoc_gift_size'] ) && is_array( $_POST['molosoc_gift_size'] ) ) ? wp_unslash( $_POST['molosoc_gift_size'] ) : array();
	$parent_id = isset( $_POST['molosoc_gift_order'] ) ? absint( wp_unslash( $_POST['molosoc_gift_order'] ) ) : 0;
	$order_key = isset( $_POST['molosoc_gift_key'] ) && is_string( $_POST['molosoc_gift_key'] ) ? wc_clean( wp_unslash( $_POST['molosoc_gift_key'] ) ) : '';
	// phpcs:enable WordPress.Security.NonceVerification.Missing

	wc_nocache_headers();

	// The original order must be the one this form was printed for (order
	// key, exactly like the Thank You page itself) and must still be entitled
	// to an offer — otherwise the "no additional shipping" promise and the
	// prices on that page can't be kept, and nothing is added.
	$parent = $parent_id ? wc_get_order( $parent_id ) : false;
	$offer  = ( $parent instanceof WC_Order && '' !== $order_key && hash_equals( $parent->get_order_key(), $order_key ) )
		? molosoc_gift_offer( $parent )
		: null;
	// More pairs than the original order allows is rejected outright, never
	// trimmed: a tampered form must not end up with a discounted extra pair.
	if ( ! $offer || $pairs < 1 || $pairs > $offer['max'] ) {
		molosoc_gift_log( 'invalid offer or pair count', array( 'order' => $parent_id, 'offer' => (bool) $offer, 'pairs' => $pairs ) );
		wp_safe_redirect( molosoc_product_url( $lang ) );
		exit;
	}

	$sizes = molosoc_gift_sizes();
	$picks = array();
	for ( $index = 0; $index < $pairs; $index++ ) {
		$key = ( isset( $posted[ $index ] ) && is_string( $posted[ $index ] ) ) ? strtoupper( sanitize_text_field( $posted[ $index ] ) ) : '';
		if ( ! isset( $sizes[ $key ] ) ) {
			molosoc_gift_log( 'size not available', array( 'order' => $parent_id, 'index' => $index ) );
			wp_safe_redirect( molosoc_product_url( $lang ) );
			exit;
		}
		$picks[ $offer['slots'][ $index ] ] = $key;
	}

	// All or nothing: if any pair can't be added (e.g. not enough stock for
	// two of the same size), put the cart back exactly as it was before
	// this request and send the customer to the product page, where
	// WooCommerce's own notice explains why — never on to checkout with
	// only part of what they chose. Every pair is its own quantity-1 row
	// carrying its overall pair number, which is what its price is read from.
	$cart = WC()->cart;

	// A shopper who has just paid for an order can still hold rows in the cart
	// (a gateway return, a cached Thank You page, a second try from the same
	// page, a second tab): the pair(s) just bought, rows an earlier submit of
	// this form added, or anything else. None of that may send a valid
	// submission to the product page (Issue #125): the order, its key, the
	// offer and the sizes are already validated above. Rows this form itself
	// added earlier are replaced (taken out first because WooCommerce's stock
	// check counts what the cart already holds, and kept in the removed-items
	// list so a failed add puts them back exactly as they were); an invalid
	// submission never changes the cart.
	// Only gift rows this order's own earlier submit added are set aside: the
	// session link names THIS order (id and key) and lists the row's key with
	// the same pair number and the quantity recorded then — a gift row another
	// order's Thank You tab created, a bare marker, or a row the shopper has
	// since changed proves nothing. Every other row (the pair just bought,
	// another product, a pair added in another tab) is the shopper's own: it
	// is never removed, and no cart row is judged "theirs" from what the page
	// happened to show. It simply stays beside the gift rows.
	$link    = ( WC()->session ) ? WC()->session->get( MOLOSOC_GIFT_SESSION_KEY ) : null;
	$link_ok  = is_array( $link )
		&& isset( $link['order_id'], $link['key'] )
		&& (int) $link['order_id'] === $parent->get_id()
		&& hash_equals( $parent->get_order_key(), (string) $link['key'] )
		&& isset( $link['lines'], $link['slots'] )
		&& is_array( $link['lines'] )
		&& is_array( $link['slots'] );
	$stale = array();
	foreach ( $cart->get_cart() as $item_key => $item ) {
		if ( ! isset( $item['product_id'], $item['variation_id'], $item['molosoc_gift_slot'] ) || MOLOSOC_PRODUCT_ID !== (int) $item['product_id'] ) {
			continue;
		}
		if ( $link_ok && isset( $link['lines'][ $item_key ], $link['slots'][ $item_key ] )
			&& (int) $link['slots'][ $item_key ] === (int) $item['molosoc_gift_slot']
			&& (int) $link['lines'][ $item_key ] === ( isset( $item['quantity'] ) ? (int) $item['quantity'] : 0 )
		) {
			$stale[ $item_key ] = $item;
		}
	}
	foreach ( array_keys( $stale ) as $item_key ) {
		$cart->remove_cart_item( $item_key );
	}

	// Issues #145/#147: the add-on checkout charges ONLY the gift pairs, so no
	// other row may ride along. Whatever else the cart holds (the pair just bought
	// that WooCommerce has not cleared, another product, a gift row no session link
	// vouches for) is PARKED, not judged: taken out of the cart for the duration of
	// the add-on checkout, kept in the session and put back afterwards
	// (molosoc_gift_unpark_rows()). A valid submission therefore never depends on
	// proof about those rows (#146 sent it to the product page whenever the session
	// had none, e.g. for an order placed before the record existed), nothing is
	// charged twice and nothing the shopper put in the cart is deleted.
	// Rows still parked for an EARLIER pending add-on (another order) are judged
	// against that order's own paid-row proof now, before they could be merged into
	// this flow's park and lose that scope: what that proof covers stays out, the
	// rest returns to the cart and is parked again below under this order.
	$earlier = WC()->session ? WC()->session->get( MOLOSOC_GIFT_PARKED_SESSION_KEY ) : null;
	if ( is_array( $earlier ) && isset( $earlier['order_id'] ) && absint( $earlier['order_id'] ) !== $parent_id ) {
		molosoc_gift_unpark_rows();
	}
	$parked = $cart->get_cart();
	foreach ( array_keys( $parked ) as $item_key ) {
		$cart->remove_cart_item( $item_key );
	}
	molosoc_gift_trace( 'submit accepted', array( 'order' => $parent_id, 'pairs' => $pairs, 'stale' => array_keys( $stale ), 'parked' => molosoc_gift_row_summary( $parked ), 'paid_record' => molosoc_gift_paid_record_state( $parent ) ) );

	$wanted = array();
	$slots  = array();
	$failed = false;
	foreach ( $picks as $slot => $key ) {
		$variation  = $sizes[ $key ]['variation'];
		$attributes = molosoc_gift_variation_attributes( $variation, $key );
		$item_key   = $cart->add_to_cart( MOLOSOC_PRODUCT_ID, 1, $variation->get_id(), $attributes, array( 'molosoc_gift_slot' => $slot ) );
		if ( ! $item_key ) {
			molosoc_gift_log( 'add_to_cart refused', array( 'variation' => $variation->get_id(), 'slot' => $slot, 'attributes' => $attributes ) );
			$failed = true;
			break;
		}
		$wanted[ $item_key ] = 1;
		$slots[ $item_key ]  = $slot;
	}

	// The cart is now exactly the chosen rows unless one merged into a row
	// already there (quantity above 1): that cannot be honoured.
	if ( ! $failed ) {
		foreach ( $wanted as $item_key => $unused ) {
			$row = $cart->get_cart_item( $item_key );
			if ( ! $row || 1 !== (int) $row['quantity'] ) {
				molosoc_gift_log( 'chosen row merged with a cart row', array( 'order' => $parent_id, 'row' => $item_key ) );
				$failed = true;
				break;
			}
		}
	}
	if ( $failed ) {
		foreach ( array_keys( $wanted ) as $item_key ) {
			$cart->remove_cart_item( $item_key );
		}
		molosoc_gift_restore_rows( $cart, $stale + $parked );
		wp_safe_redirect( molosoc_product_url( $lang ) );
		exit;
	}

	// The add-on cart is now exactly the gift rows: keep the parked rows, and drop
	// them from WooCommerce's undo list so they cannot come back twice.
	molosoc_gift_park_rows( $parent, $parked );
	if ( $parked ) {
		$removed = $cart->get_removed_cart_contents();
		foreach ( array_keys( $parked ) as $item_key ) {
			unset( $removed[ $item_key ] );
		}
		$cart->set_removed_cart_contents( $removed );
	}
	molosoc_gift_link_cart_to_order( $parent, $lang, $wanted, $slots );

	// The cart and the link live in the WooCommerce session: make sure the
	// shopper's browser holds the session cookie that finds them again on the
	// checkout request (a shopper returning from a payment gateway may have
	// none yet), or the checkout would open empty.
	if ( WC()->session && method_exists( WC()->session, 'set_customer_session_cookie' ) ) {
		WC()->session->set_customer_session_cookie( true );
	}

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
 * the exact set of rows the form added and 'slots' (cart item key => overall
 * pair number) the position each was added for; see molosoc_gift_cart_link().
 */
function molosoc_gift_link_cart_to_order( $parent, $lang, $lines, $slots ) {
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
			'slots'    => $slots,
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
 * still be offered the add-on (molosoc_gift_offer()), and the cart must still
 * hold every row the gift form added, one per pair with its pair number and
 * quantity 1 (so neither the free rate nor the offer prices ever cover a
 * pre-loaded, later-increased, removed-in-part or fourth pair), and NOTHING else
 * (#145: the already-paid pair or any other row would be charged in the add-on
 * checkout). Null otherwise.
 * Returns array( 'order' => WC_Order, 'lang' => 'cz'|'en', 'prices' => cart
 * item key => unit price, 'offer' => molosoc_gift_offer()).
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
	if ( ! $parent instanceof WC_Order || ! hash_equals( $parent->get_order_key(), (string) $link['key'] ) ) {
		return null;
	}
	// Still entitled to an offer (status, window, no add-on yet, one or two
	// original pairs) and within what that offer allows.
	$offer = molosoc_gift_offer( $parent );
	if ( ! $offer ) {
		return null;
	}
	$lines = ( isset( $link['lines'] ) && is_array( $link['lines'] ) ) ? $link['lines'] : array();
	$slots = ( isset( $link['slots'] ) && is_array( $link['slots'] ) ) ? $link['slots'] : array();
	$items = WC()->cart->get_cart();
	if ( empty( $items ) || empty( $lines ) || count( $slots ) !== count( $lines ) || array_sum( $lines ) > $offer['max'] ) {
		return null;
	}
	// The pairs must be exactly the next ones in line (original + 1, +2, ...),
	// each once, so a fourth pair — or a repeated slot — can never be priced.
	$taken = array_map( 'intval', array_values( $slots ) );
	sort( $taken );
	if ( $taken !== array_slice( $offer['slots'], 0, count( $taken ) ) ) {
		return null;
	}
	$prices    = array();
	$purchased = array();
	foreach ( $lines as $key => $unused ) {
		$item = isset( $items[ $key ] ) ? $items[ $key ] : null;
		if ( ! $item || ! isset( $slots[ $key ], $item['product_id'], $item['quantity'], $item['molosoc_gift_slot'] )
			|| MOLOSOC_PRODUCT_ID !== (int) $item['product_id']
			|| 1 !== (int) $lines[ $key ]
			|| 1 !== (int) $item['quantity']
			|| (int) $slots[ $key ] !== (int) $item['molosoc_gift_slot']
		) {
			return null;
		}
		$prices[ $key ]                    = $offer['prices'][ (int) $slots[ $key ] ];
		$purchased[ (int) $slots[ $key ] ] = $prices[ $key ];
	}
	// Issue #145: the add-on checkout may hold the gift rows and nothing else.
	// Any other row (the already-paid pair back in the cart, anything else)
	// means isolation is no longer guaranteed, so the link does not hold: no
	// offer price, no free shipping, no stamp — the customer sees an honest,
	// normal cart rather than a misleading discounted total.
	if ( array_diff( array_keys( $items ), array_keys( $lines ) ) ) {
		return null;
	}
	ksort( $purchased );
	return array(
		'order'  => $parent,
		'lang'   => ( isset( $link['lang'] ) && 'cz' === $link['lang'] ) ? 'cz' : 'en',
		'prices' => $prices, // cart item key => unit price, from the server-side schedule
		'pairs'  => $purchased, // overall pair number => unit price, only pairs actually in the cart
		'offer'  => $offer,
	);
}

/**
 * The offer prices. While molosoc_gift_cart_link() holds, each gift row is
 * priced from its overall pair number; the product itself is never touched,
 * so without a valid link (or on any other cart) every row stays at the
 * normal price. Runs at the end of the totals pass so nothing else can
 * overwrite it, for the classic and the Store API cart alike.
 */
function molosoc_gift_apply_prices( $cart ) {
	if ( ! is_object( $cart ) ) {
		return;
	}
	$link = molosoc_gift_cart_link();
	foreach ( $cart->get_cart() as $key => $item ) {
		if ( ! isset( $item['molosoc_gift_slot'], $item['data'] ) || ! is_object( $item['data'] ) ) {
			continue;
		}
		// The cart's product objects outlive a totals pass: remember the price
		// they had before the first offer price and put it back on every pass
		// whose link no longer holds.
		$base = $item['data']->get_meta( '_molosoc_gift_base_price', true, 'edit' );
		if ( '' === (string) $base ) {
			$base = $item['data']->get_price( 'edit' );
			$item['data']->update_meta_data( '_molosoc_gift_base_price', $base );
		}
		$item['data']->set_price( ( $link && isset( $link['prices'][ $key ] ) ) ? $link['prices'][ $key ] : $base );
	}
}
add_action( 'woocommerce_before_calculate_totals', 'molosoc_gift_apply_prices', 100, 1 );

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
		// A draft order (block checkout) is updated repeatedly: a stamp from an
		// earlier, valid state must not outlive the link, or a normal paid-shipping
		// order would later be treated as a gift add-on.
		foreach ( array( '', '_original_qty', '_pricing', '_other_lines' ) as $suffix ) {
			if ( '' !== (string) $order->get_meta( MOLOSOC_GIFT_PARENT_META . $suffix ) ) {
				$order->delete_meta_data( MOLOSOC_GIFT_PARENT_META . $suffix );
			}
		}
		return;
	}
	$order->update_meta_data( MOLOSOC_GIFT_PARENT_META, $link['order']->get_id() );
	// Audit trail for the offer prices: how many pairs the original order held
	// and the unit price granted to each overall pair number.
	$order->update_meta_data( MOLOSOC_GIFT_PARENT_META . '_original_qty', $link['offer']['original'] );
	$order->update_meta_data( MOLOSOC_GIFT_PARENT_META . '_pricing', wp_json_encode( $link['pairs'] ) );
	// The link only holds for a gift-only cart (#145); older orders may carry the
	// retired marker.
	$order->delete_meta_data( MOLOSOC_GIFT_PARENT_META . '_other_lines' );
}
add_action( 'woocommerce_checkout_create_order', 'molosoc_gift_stamp_new_order', 10, 1 );
add_action( 'woocommerce_store_api_checkout_update_order_meta', 'molosoc_gift_stamp_new_order', 10, 1 );

/**
 * Record on each gift order line which overall pair it is, the unit price it
 * was sold at and the normal price it would otherwise have had, so the
 * offer price stays auditable from the order alone. Only for rows the valid
 * link priced; classic checkout and the Store API both create their lines
 * through this action.
 */
function molosoc_gift_stamp_order_line( $item, $cart_item_key, $values, $order = null ) {
	$link = molosoc_gift_cart_link();
	if ( ! $link || ! isset( $link['prices'][ $cart_item_key ] ) || ! is_object( $item ) ) {
		return;
	}
	$item->add_meta_data( '_molosoc_gift_pair_number', (int) $values['molosoc_gift_slot'], true );
	$item->add_meta_data( '_molosoc_gift_unit_price', (string) $link['prices'][ $cart_item_key ], true );
	if ( isset( $values['data'] ) && is_object( $values['data'] ) ) {
		$item->add_meta_data( '_molosoc_gift_list_price', (string) $values['data']->get_regular_price(), true );
	}
}
add_action( 'woocommerce_checkout_create_order_line_item', 'molosoc_gift_stamp_order_line', 10, 4 );

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
				'POZOR: původní objednávka č. %1$s už nejde odeslat společně (odeslána, mimo časové okno nebo už má jiný doplněk) — vyřiďte ručně, poštovné 0 a zvýhodněné ceny byly účtovány. / ATTENTION: original order #%1$s can no longer ship together (dispatched, outside the window or already has another add-on) — handle manually, shipping 0 and the offer prices were charged.',
				$parent->get_order_number()
			)
		);
		$order->update_meta_data( MOLOSOC_GIFT_PARENT_META . '_noted', 'manual' );
		$order->save();
		return;
	}
	// Only the lines the offer priced (stamped at checkout) ship with the
	// original order; with none stamped (older orders) every line counts.
	$pairs  = 0;
	$stamped = 0;
	foreach ( $order->get_items() as $item ) {
		$stamped += ( is_object( $item ) && method_exists( $item, 'get_meta' ) && '' !== (string) $item->get_meta( '_molosoc_gift_pair_number' ) ) ? (int) $item->get_quantity() : 0;
		$pairs   += (int) $item->get_quantity();
	}
	if ( $stamped ) {
		$pairs = $stamped;
	}
	$order->add_order_note(
		( molosoc_gift_has_other_lines( $order )
			? sprintf(
				'Dárkový doplněk k objednávce č. %1$s — POUZE dárkové páry (%2$d ks) odeslat společně s ní, poštovné 0 (zaplaceno v objednávce č. %1$s); ostatní položky této objednávky se posílají zvlášť s běžným poštovným. / Gift add-on to order #%1$s — ONLY the gift pairs (%2$d) ship together with it, shipping 0 (paid on #%1$s); the other lines of this order ship separately with normal shipping.',
				$parent->get_order_number(),
				$pairs
			)
			: sprintf(
				'Dárkový doplněk k objednávce č. %1$s — odeslat společně s ní, poštovné 0 (zákazník ho zaplatil v objednávce č. %1$s). / Gift add-on to order #%1$s — ship together with it, shipping 0 (paid on #%1$s).',
				$parent->get_order_number()
			)
		) . molosoc_gift_pricing_note( $order )
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

/**
 * True when the add-on order also holds lines that are not gift pairs (stamped
 * at checkout): those ship separately, with normal shipping.
 */
function molosoc_gift_has_other_lines( $order ) {
	return (int) $order->get_meta( MOLOSOC_GIFT_PARENT_META . '_other_lines' ) > 0;
}

/**
 * " Offer prices: ..." suffix for the add-on order's private note, from the
 * meta stamped at checkout; empty when the order carries none.
 */
function molosoc_gift_pricing_note( $order ) {
	$pricing = json_decode( (string) $order->get_meta( MOLOSOC_GIFT_PARENT_META . '_pricing' ), true );
	if ( ! is_array( $pricing ) || ! $pricing ) {
		return '';
	}
	$parts = array();
	foreach ( $pricing as $slot => $price ) {
		$parts[] = sprintf( '#%d = %s', (int) $slot, $price );
	}
	return sprintf(
		' Cena párů podle původní objednávky (%1$d ks): pár %2$s. / Pair prices by original order (%1$d pairs): pair %2$s.',
		(int) $order->get_meta( MOLOSOC_GIFT_PARENT_META . '_original_qty' ),
		implode( ', ', $parts )
	);
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
	$mixed  = molosoc_gift_has_other_lines( $order );
	printf(
		'<p class="form-field form-field-wide molosoc-gift-admin-link"><strong>%s</strong> <a href="%s">#%s</a> — %s</p>',
		esc_html( 'Dárkový doplněk k objednávce / Gift add-on to order' ),
		esc_url( $parent->get_edit_order_url() ),
		esc_html( $parent->get_order_number() ),
		esc_html( $manual ? 'nelze odeslat společně — vyřiďte ručně, poštovné 0 / cannot ship together — handle manually, shipping 0' : ( $mixed ? 'společně odeslat jen dárkové páry (poštovné 0), ostatní položky zvlášť / ship only the gift pairs together (shipping 0), other lines separately' : 'odeslat společně, poštovné 0 / ship together, shipping 0' ) )
	);
}
add_action( 'woocommerce_admin_order_data_after_order_details', 'molosoc_gift_admin_order_line', 10, 1 );
