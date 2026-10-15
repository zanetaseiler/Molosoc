<?php
/**
 * CZ bank-transfer unpaid-order reminder after 24 hours (GitHub Issue #194).
 *
 * One warm, transactional e-mail for a Czech order paid by bank transfer
 * (WooCommerce BACS) that still shows no payment 24 hours after it was
 * placed. It is NOT marketing: there is no newsletter/subscription gate and
 * no unsubscribe language, and it never touches the Welcome, Abandoned Cart
 * or Post Purchase flows, the Brevo checkout shim, the gateways, checkout or
 * bank-transfer availability.
 *
 * Mechanics (WooCommerce-native only — Action Scheduler ships with
 * WooCommerce, no external service or credential):
 *   - When a BACS order enters on-hold (what the BACS gateway does at
 *     checkout) or pending, ONE unique Action Scheduler action is scheduled
 *     for date_created + 24h. Re-scheduling the same order is a no-op.
 *   - At run time the order is re-read and the reminder is sent only if it
 *     is still BACS, CZ, genuinely unpaid and still on-hold/pending. Paid,
 *     processing, completed, cancelled, refunded, failed, trash (and any
 *     other status) are suppressed.
 *   - Exactly once: a claim flag is stored on the order BEFORE sending, so
 *     a retry or duplicate run finds it and does nothing. If wp_mail()
 *     reports failure the claim is released so a later run may retry.
 *   - Bank account details are NOT put in the e-mail; the customer already
 *     has them on the order page / order e-mail and may reply for help.
 *
 * Required once from functions.php.
 */

defined( 'ABSPATH' ) || exit;

if ( ! defined( 'MOLOSOC_BACS_REMINDER_HOOK' ) ) {
	define( 'MOLOSOC_BACS_REMINDER_HOOK', 'molosoc_bacs_unpaid_reminder' );
}
// Delay after the order was placed.
if ( ! defined( 'MOLOSOC_BACS_REMINDER_DELAY' ) ) {
	define( 'MOLOSOC_BACS_REMINDER_DELAY', 24 * HOUR_IN_SECONDS );
}
// Order meta set once the reminder is claimed/sent.
if ( ! defined( 'MOLOSOC_BACS_REMINDER_META' ) ) {
	define( 'MOLOSOC_BACS_REMINDER_META', '_molosoc_bacs_reminder_sent' );
}

/**
 * Is this a CZ bank-transfer order? Bank transfer is CZ-only, so the scope is
 * enforced from the order's own country, not from any marketing language.
 */
function molosoc_bacs_reminder_in_scope( $order ) {
	if ( ! $order || 'bacs' !== $order->get_payment_method() ) {
		return false;
	}
	$country = $order->get_billing_country();
	if ( '' === $country ) {
		$country = $order->get_shipping_country();
	}
	return 'CZ' === strtoupper( (string) $country );
}

/**
 * Schedule the single 24h check for an in-scope order.
 */
function molosoc_bacs_reminder_schedule( $order_id ) {
	$order = wc_get_order( $order_id );
	if ( ! molosoc_bacs_reminder_in_scope( $order ) || $order->get_meta( MOLOSOC_BACS_REMINDER_META ) ) {
		return;
	}
	if ( ! function_exists( 'as_schedule_single_action' ) ) {
		return;
	}
	$created = $order->get_date_created();
	$due     = ( $created ? $created->getTimestamp() : time() ) + MOLOSOC_BACS_REMINDER_DELAY;
	// unique = true: a second schedule for the same order is a no-op.
	as_schedule_single_action( $due, MOLOSOC_BACS_REMINDER_HOOK, array( (int) $order_id ), 'molosoc', true );
}
add_action( 'woocommerce_order_status_on-hold', 'molosoc_bacs_reminder_schedule', 20, 1 );
add_action( 'woocommerce_order_status_pending', 'molosoc_bacs_reminder_schedule', 20, 1 );

/**
 * Czech reminder subject and plain-text body.
 */
function molosoc_bacs_reminder_message( $order ) {
	$number = $order->get_order_number();
	$total  = html_entity_decode( wp_strip_all_tags( wc_price( $order->get_total(), array( 'currency' => $order->get_currency() ) ) ), ENT_QUOTES, 'UTF-8' );
	$total  = trim( str_replace( "\xc2\xa0", ' ', $total ) );
	$body   = "Dobrý den,\n\n"
		. "jen krátce připomínáme platbu za objednávku č. {$number} v hodnotě {$total}. Zatím ji u objednávky nevidíme.\n\n"
		. "Pokud jste platbu právě odeslali, tuto zprávu prosím ignorujte — připsání může chvíli trvat.\n\n"
		. "Kdybyste s platbou potřebovali jakkoli pomoci, stačí odpovědět na tento e-mail.\n\n"
		. "Děkujeme,\nMOLOSOC";
	return array( "Připomínka k platbě objednávky č. {$number}", $body );
}

/**
 * Action Scheduler callback. Re-reads the order; sends at most once.
 */
function molosoc_bacs_reminder_run( $order_id ) {
	$order = wc_get_order( $order_id );
	if ( ! molosoc_bacs_reminder_in_scope( $order ) ) {
		return;
	}
	if ( $order->get_meta( MOLOSOC_BACS_REMINDER_META ) ) {
		return; // already sent / claimed
	}
	// Only a genuinely unpaid, still-open order. Everything else (processing,
	// completed, cancelled, refunded, failed, trash, ...) is suppressed.
	if ( ! $order->has_status( array( 'on-hold', 'pending' ) ) || $order->is_paid() || $order->get_date_paid() ) {
		return;
	}
	// Not yet due (early run): put the single check back at the due time.
	$created = $order->get_date_created();
	$due     = ( $created ? $created->getTimestamp() : 0 ) + MOLOSOC_BACS_REMINDER_DELAY;
	if ( time() < $due ) {
		if ( function_exists( 'as_schedule_single_action' ) ) {
			as_schedule_single_action( $due, MOLOSOC_BACS_REMINDER_HOOK, array( (int) $order_id ), 'molosoc', true );
		}
		return;
	}
	$to = $order->get_billing_email();
	if ( ! $to ) {
		return;
	}

	// Claim before sending so a retry / duplicate run cannot send twice.
	$order->update_meta_data( MOLOSOC_BACS_REMINDER_META, (string) time() );
	$order->save();

	list( $subject, $body ) = molosoc_bacs_reminder_message( $order );
	if ( wp_mail( $to, $subject, $body ) ) {
		$order->add_order_note( 'Odeslána připomínka platby bankovním převodem (24 h).' );
	} else {
		$order->delete_meta_data( MOLOSOC_BACS_REMINDER_META );
		$order->save();
	}
}
add_action( MOLOSOC_BACS_REMINDER_HOOK, 'molosoc_bacs_reminder_run', 10, 1 );
