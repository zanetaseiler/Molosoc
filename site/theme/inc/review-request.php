<?php
/**
 * MOLOSOC-hosted post-purchase review request (GitHub Issue #333).
 *
 * One short, plain-text CZ/EN e-mail asking a customer to review the product
 * they bought, linking to the review form on the MOLOSOC product page
 * (native WooCommerce reviews, moderated, "verified owner" label is Woo's
 * own). Reviews are hosted on MOLOSOC and are NOT independently verified;
 * the e-mail says so. No newsletter coupling, no marketing content.
 *
 * SAFE BY DEFAULT. Nothing is scheduled and nothing is sent unless the owner
 * sets the mode. Modes (option `molosoc_review_request_mode`):
 *   off      (default) - nothing scheduled, nothing sent.
 *   dry_run            - orders are scheduled and evaluated; a private order
 *                        note records what WOULD be sent. wp_mail() is never
 *                        called and no "sent" claim is set.
 *   live               - sends, but ONLY if the owner has also set option
 *                        `molosoc_review_request_legal_confirmed` to '1'
 *                        (the Czech/EU legal-basis and checkout-notice
 *                        confirmation required by the Issue #333 decision).
 *                        Without it live behaves as dry_run.
 * Optional test allowlist: option `molosoc_review_request_test_emails`
 * (comma-separated). When set, ONLY those addresses are ever mailed, in any
 * mode.
 *
 * Trigger: WooCommerce status `completed` + a delay (CZ 10 days, abroad 14,
 * filterable). `completed` is only a PROXY: it means the shop marked the
 * order completed, NOT that a carrier delivered it. No carrier-delivered
 * signal is used or claimed.
 *
 * Idempotent: one unique Action Scheduler action per order; a claim meta is
 * written BEFORE sending; a failed wp_mail() releases it for a bounded
 * retry; a repeat run finds the claim and does nothing.
 *
 * Suppression (checked at run time): per-order opt-out meta; hashed e-mail
 * suppression list (set by the opt-out link in every e-mail); the filter
 * `molosoc_review_request_suppressed` (hook an existing marketing-unsubscribe
 * list here); non-completed/refunded orders; orders with no e-mail.
 *
 * Required once from functions.php.
 */

defined( 'ABSPATH' ) || exit;

if ( ! defined( 'MOLOSOC_REVIEW_REQUEST_HOOK' ) ) {
	define( 'MOLOSOC_REVIEW_REQUEST_HOOK', 'molosoc_review_request_send' );
}
if ( ! defined( 'MOLOSOC_REVIEW_REQUEST_SENT_META' ) ) {
	define( 'MOLOSOC_REVIEW_REQUEST_SENT_META', '_molosoc_review_request_sent' );
}
if ( ! defined( 'MOLOSOC_REVIEW_REQUEST_DRY_META' ) ) {
	define( 'MOLOSOC_REVIEW_REQUEST_DRY_META', '_molosoc_review_request_dry_run' );
}
if ( ! defined( 'MOLOSOC_REVIEW_REQUEST_OPTOUT_META' ) ) {
	define( 'MOLOSOC_REVIEW_REQUEST_OPTOUT_META', '_molosoc_review_request_optout' );
}
if ( ! defined( 'MOLOSOC_REVIEW_REQUEST_MAX_RETRIES' ) ) {
	define( 'MOLOSOC_REVIEW_REQUEST_MAX_RETRIES', 3 );
}

/** Current mode: off | dry_run | live (anything else is off). */
function molosoc_review_request_mode() {
	$mode = get_option( 'molosoc_review_request_mode', 'off' );
	return in_array( $mode, array( 'dry_run', 'live' ), true ) ? $mode : 'off';
}

/** True only when a real send is allowed. */
function molosoc_review_request_is_live() {
	return 'live' === molosoc_review_request_mode()
		&& '1' === (string) get_option( 'molosoc_review_request_legal_confirmed', '' );
}

/** CZ order (Czech billing/shipping country) gets the Czech e-mail. */
function molosoc_review_request_is_cz( $order ) {
	$country = $order->get_billing_country();
	if ( '' === $country ) {
		$country = $order->get_shipping_country();
	}
	return 'CZ' === strtoupper( (string) $country );
}

/** Delay in seconds after `completed`. */
function molosoc_review_request_delay( $order ) {
	$days = molosoc_review_request_is_cz( $order ) ? 10 : 14;
	$days = (int) apply_filters( 'molosoc_review_request_delay_days', $days, $order );
	return max( 1, $days ) * DAY_IN_SECONDS;
}

/** Hash used for the e-mail suppression list (no plain addresses stored). */
function molosoc_review_request_email_hash( $email ) {
	return hash_hmac( 'sha256', strtolower( trim( (string) $email ) ), wp_salt( 'auth' ) );
}

function molosoc_review_request_email_suppressed( $email ) {
	$list = get_option( 'molosoc_review_request_suppressed', array() );
	return is_array( $list ) && in_array( molosoc_review_request_email_hash( $email ), $list, true );
}

/** Signed opt-out URL for an order (no login, no nonce; HMAC of order id). */
function molosoc_review_request_optout_url( $order_id ) {
	$token = hash_hmac( 'sha256', 'review-optout|' . (int) $order_id, wp_salt( 'auth' ) );
	return add_query_arg(
		array(
			'molosoc_review_optout' => (int) $order_id,
			't'                     => $token,
		),
		home_url( '/' )
	);
}

/** Schedule the single request when an order becomes completed. */
function molosoc_review_request_schedule( $order_id ) {
	if ( 'off' === molosoc_review_request_mode() ) {
		return;
	}
	$order = wc_get_order( $order_id );
	if ( ! $order || $order->get_meta( MOLOSOC_REVIEW_REQUEST_SENT_META ) || ! function_exists( 'as_schedule_single_action' ) ) {
		return;
	}
	// unique = true: completing the same order twice schedules once.
	as_schedule_single_action( time() + molosoc_review_request_delay( $order ), MOLOSOC_REVIEW_REQUEST_HOOK, array( (int) $order_id ), 'molosoc', true );
}
add_action( 'woocommerce_order_status_completed', 'molosoc_review_request_schedule', 20, 1 );

/** Up to 3 purchased products: array of [name, review link in the order language]. */
function molosoc_review_request_products( $order, $cz ) {
	$out = array();
	foreach ( $order->get_items() as $item ) {
		$pid = $item->get_product_id();
		if ( ! $pid ) {
			continue;
		}
		$target = $pid;
		if ( function_exists( 'pll_get_post' ) ) {
			$tr = pll_get_post( $pid, $cz ? 'cz' : 'en' );
			if ( $tr ) {
				$target = $tr;
			}
		}
		$link = get_permalink( $target );
		if ( $link && ! isset( $out[ $pid ] ) ) {
			$out[ $pid ] = array( $item->get_name(), $link . '#reviews' );
		}
		if ( count( $out ) >= 3 ) {
			break;
		}
	}
	return array_values( $out );
}

/** Subject + plain-text body (CZ or EN). */
function molosoc_review_request_message( $order ) {
	$cz       = molosoc_review_request_is_cz( $order );
	$products = molosoc_review_request_products( $order, $cz );
	if ( ! $products ) {
		return null;
	}
	$optout = molosoc_review_request_optout_url( $order->get_id() );
	$lines  = '';
	foreach ( $products as $p ) {
		$lines .= $p[0] . ': ' . $p[1] . "\n";
	}
	if ( $cz ) {
		$subject = 'Jak se vám osvědčil váš MOLOSOC?';
		$body    = "Dobrý den,\n\n"
			. "děkujeme za objednávku č. {$order->get_order_number()}. Pokud už jste produkt vyzkoušeli, budeme rádi za krátké hodnocení. Zabere to chvilku a pomůže to dalším zákaznicím a zákazníkům.\n\n"
			. $lines . "\n"
			. "Hodnocení se zveřejňují přímo na webu MOLOSOC po kontrole. Nejde o nezávisle ověřenou službu recenzí.\n\n"
			. "Tuto jednu zprávu posíláme jako zákazníkům, kterým jsme zboží prodali; nic dalšího vám v této věci posílat nebudeme. Nechcete-li ji již dostávat, odhlásíte se zde:\n{$optout}\n\n"
			. "Děkujeme,\nMOLOSOC";
	} else {
		$subject = 'How is your MOLOSOC working for you?';
		$body    = "Hello,\n\n"
			. "Thank you for your order #{$order->get_order_number()}. If you have tried the product, we would be glad to hear how it went. It takes a minute and helps other customers.\n\n"
			. $lines . "\n"
			. "Reviews are published on the MOLOSOC website after moderation. They are not an independently verified review service.\n\n"
			. "We send this one message to customers we sold the goods to, and nothing else about it. If you do not want to receive it, opt out here:\n{$optout}\n\n"
			. "Thank you,\nMOLOSOC";
	}
	return array( $subject, $body );
}

/** Reason the order must not be mailed, or '' if eligible. */
function molosoc_review_request_blocked_reason( $order ) {
	if ( ! $order->has_status( 'completed' ) ) {
		return 'status-not-completed';
	}
	if ( $order->get_meta( MOLOSOC_REVIEW_REQUEST_SENT_META ) ) {
		return 'already-sent';
	}
	if ( $order->get_meta( MOLOSOC_REVIEW_REQUEST_OPTOUT_META ) ) {
		return 'order-opted-out';
	}
	$total    = (float) $order->get_total();
	$refunded = (float) $order->get_total_refunded();
	if ( $total > 0 && $refunded >= $total ) {
		return 'fully-refunded';
	}
	$to = $order->get_billing_email();
	if ( ! $to || ! is_email( $to ) ) {
		return 'no-valid-email';
	}
	if ( molosoc_review_request_email_suppressed( $to ) ) {
		return 'email-suppressed';
	}
	if ( apply_filters( 'molosoc_review_request_suppressed', false, $order, $to ) ) {
		return 'filter-suppressed';
	}
	$allow = trim( (string) get_option( 'molosoc_review_request_test_emails', '' ) );
	if ( '' !== $allow ) {
		$list = array_map( 'strtolower', array_map( 'trim', explode( ',', $allow ) ) );
		if ( ! in_array( strtolower( $to ), $list, true ) ) {
			return 'not-on-test-allowlist';
		}
	}
	return '';
}

/** Action Scheduler callback. At most one real send per order. */
function molosoc_review_request_run( $order_id, $attempt = 0 ) {
	$attempt = (int) $attempt;
	$mode    = molosoc_review_request_mode();
	if ( 'off' === $mode ) {
		return;
	}
	$order = wc_get_order( $order_id );
	if ( ! $order || '' !== molosoc_review_request_blocked_reason( $order ) ) {
		return;
	}
	$msg = molosoc_review_request_message( $order );
	if ( ! $msg ) {
		return;
	}
	$to = $order->get_billing_email();

	if ( ! molosoc_review_request_is_live() ) {
		// Dry run: record once, never mail, never set the sent claim.
		if ( ! $order->get_meta( MOLOSOC_REVIEW_REQUEST_DRY_META ) ) {
			$order->update_meta_data( MOLOSOC_REVIEW_REQUEST_DRY_META, (string) time() );
			$order->save();
			$order->add_order_note( 'DRY RUN: žádost o hodnocení by byla odeslána (nic neodesláno).' );
		}
		return;
	}

	// Claim before sending so a retry / duplicate run cannot send twice.
	$order->update_meta_data( MOLOSOC_REVIEW_REQUEST_SENT_META, (string) time() );
	$order->save();
	if ( wp_mail( $to, $msg[0], $msg[1] ) ) {
		$order->add_order_note( 'Odeslána žádost o hodnocení produktu.' );
		return;
	}
	$order->delete_meta_data( MOLOSOC_REVIEW_REQUEST_SENT_META );
	$order->save();
	if ( $attempt < MOLOSOC_REVIEW_REQUEST_MAX_RETRIES && function_exists( 'as_schedule_single_action' ) ) {
		as_schedule_single_action( time() + HOUR_IN_SECONDS, MOLOSOC_REVIEW_REQUEST_HOOK, array( (int) $order_id, $attempt + 1 ), 'molosoc', true );
	}
}
add_action( MOLOSOC_REVIEW_REQUEST_HOOK, 'molosoc_review_request_run', 10, 2 );

/** Opt-out link handler: validates the HMAC, suppresses the address. */
function molosoc_review_request_handle_optout() {
	if ( ! isset( $_GET['molosoc_review_optout'], $_GET['t'] ) ) {
		return;
	}
	$order_id = (int) $_GET['molosoc_review_optout'];
	$token    = (string) $_GET['t'];
	$expected = hash_hmac( 'sha256', 'review-optout|' . $order_id, wp_salt( 'auth' ) );
	if ( ! hash_equals( $expected, $token ) ) {
		wp_die( 'Neplatný odkaz / Invalid link.', '', array( 'response' => 403 ) );
	}
	$order = wc_get_order( $order_id );
	if ( $order ) {
		$order->update_meta_data( MOLOSOC_REVIEW_REQUEST_OPTOUT_META, (string) time() );
		$order->save();
		$list = get_option( 'molosoc_review_request_suppressed', array() );
		$list = is_array( $list ) ? $list : array();
		$hash = molosoc_review_request_email_hash( $order->get_billing_email() );
		if ( ! in_array( $hash, $list, true ) ) {
			$list[] = $hash;
			update_option( 'molosoc_review_request_suppressed', $list, false );
		}
	}
	wp_die( 'Hotovo, žádost o hodnocení již nebudeme posílat. / Done, we will not send you a review request.', 'MOLOSOC', array( 'response' => 200 ) );
}
add_action( 'template_redirect', 'molosoc_review_request_handle_optout', 1 );
