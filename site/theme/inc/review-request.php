<?php
/**
 * MOLOSOC-hosted post-purchase review request (GitHub Issue #333).
 *
 * One short, branded HTML (plus plain-text alternative) CZ/EN e-mail asking a customer to review the product
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
if ( ! defined( 'MOLOSOC_REVIEW_REQUEST_NOTICE_META' ) ) {
	// Set at checkout only when the collection-time notice was actually shown with the order form.
	define( 'MOLOSOC_REVIEW_REQUEST_NOTICE_META', '_molosoc_review_request_notice' );
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

/** Message language: the language the order was placed in (_molosoc_lang), falling back to the billing/shipping country. */
function molosoc_review_request_is_cz_lang( $order ) {
	$lang = (string) $order->get_meta( '_molosoc_lang' );
	if ( 'cz' === $lang ) {
		return true;
	}
	if ( 'en' === $lang ) {
		return false;
	}
	return molosoc_review_request_is_cz( $order );
}

/** Czech billing/shipping country: drives only the delivery-delay proxy (10d vs 14d), never the language. */
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
	return false !== get_option( molosoc_review_request_suppress_key( $email ), false );
}

/** One option per hashed address, so concurrent opt-outs cannot overwrite each other. */
function molosoc_review_request_suppress_key( $email ) {
	return 'molosoc_rr_optout_' . substr( molosoc_review_request_email_hash( $email ), 0, 40 );
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
		if ( defined( 'MOLOSOC_PRODUCT_ID' ) && MOLOSOC_PRODUCT_ID === (int) $pid && function_exists( 'molosoc_product_url' ) ) {
			// Product 364 is untranslatable in Polylang and its CZ permalink filter needs a CZ request; use the explicit-language helper.
			$out[ $pid ] = array( $item->get_name(), molosoc_product_url( $cz ? 'cz' : 'en' ) . '#reviews' );
			if ( count( $out ) >= 3 ) {
				break;
			}
			continue;
		}
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

/** Verified shop sender for this e-mail only (header-scoped; global WP/Woo sender config is untouched). */
function molosoc_review_request_from() {
	return array(
		'name'  => 'MOLOSOC',
		'email' => (string) apply_filters( 'molosoc_review_request_from_email', 'hello@molosoc.com' ),
	);
}

/** Copy for the e-mail (CZ or EN). */
function molosoc_review_request_copy( $cz, $order_number ) {
	if ( $cz ) {
		return array(
			'subject'  => 'Jak se vám osvědčil váš MOLOSOC?',
			'lang'     => 'cs',
			'hello'    => 'Dobrý den,',
			'intro'    => 'děkujeme za objednávku č. ' . $order_number . '. Pokud už jste produkt vyzkoušeli, budeme rádi za krátké hodnocení. Zabere to chvilku a pomůže to dalším zákaznicím a zákazníkům.',
			'cta'      => 'Napsat hodnocení',
			'note'     => 'Hodnocení se zveřejňují přímo na webu MOLOSOC po kontrole. Nejde o nezávisle ověřenou službu recenzí.',
			'why'      => 'Tuto jednu zprávu posíláme jako zákazníkům, kterým jsme zboží prodali; nic dalšího vám v této věci posílat nebudeme.',
			'optout'   => 'Odhlásit se z těchto zpráv',
			'optout_t' => 'Nechcete-li ji již dostávat, odhlásíte se zde:',
			'bye'      => 'Děkujeme,',
		);
	}
	return array(
		'subject'  => 'How is your MOLOSOC working for you?',
		'lang'     => 'en',
		'hello'    => 'Hello,',
		'intro'    => 'Thank you for your order #' . $order_number . '. If you have tried the product, we would be glad to hear how it went. It takes a minute and helps other customers.',
		'cta'      => 'Write a review',
		'note'     => 'Reviews are published on the MOLOSOC website after moderation. They are not an independently verified review service.',
		'why'      => 'We send this one message to customers we sold the goods to, and nothing else about it.',
		'optout'   => 'Unsubscribe',
		'optout_t' => 'If you do not want to receive it, opt out here:',
		'bye'      => 'Thank you,',
	);
}

/** Branded, responsive, table-based HTML body. Visible text never contains a raw URL or token. */
function molosoc_review_request_html( $c, $products, $optout ) {
	$e   = 'esc_html';
	$out = '<!DOCTYPE html><html lang="' . esc_attr( $c['lang'] ) . '"><head><meta charset="utf-8">'
		. '<meta name="viewport" content="width=device-width,initial-scale=1">'
		. '<title>' . $e( $c['subject'] ) . '</title></head>'
		. '<body style="margin:0;padding:0;background:#f4f1ec;">'
		. '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f1ec;"><tr><td align="center" style="padding:16px;">'
		. '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:8px;font-family:Arial,Helvetica,sans-serif;color:#222222;">'
		. '<tr><td style="padding:24px 24px 8px;font-size:20px;letter-spacing:3px;font-weight:bold;">MOLOSOC</td></tr>'
		. '<tr><td style="padding:8px 24px;font-size:16px;line-height:1.5;">'
		. '<p style="margin:0 0 12px;">' . $e( $c['hello'] ) . '</p>'
		. '<p style="margin:0 0 16px;">' . $e( $c['intro'] ) . '</p></td></tr>';
	foreach ( $products as $p ) {
		$out .= '<tr><td align="center" style="padding:8px 24px;">';
		if ( count( $products ) > 1 ) {
			$out .= '<p style="margin:0 0 8px;font-size:15px;font-weight:bold;">' . $e( $p[0] ) . '</p>';
		}
		$out .= '<a href="' . esc_url( $p[1] ) . '" style="display:inline-block;background:#222222;color:#ffffff;text-decoration:none;font-size:16px;font-weight:bold;padding:14px 28px;border-radius:6px;">' . $e( $c['cta'] ) . '</a>'
			. '</td></tr>';
	}
	$out .= '<tr><td style="padding:16px 24px 8px;font-size:14px;line-height:1.5;color:#444444;">'
		. '<p style="margin:0 0 12px;">' . $e( $c['note'] ) . '</p>'
		. '<p style="margin:0 0 12px;">' . $e( $c['bye'] ) . '<br>MOLOSOC</p></td></tr>'
		. '<tr><td style="padding:8px 24px 24px;font-size:12px;line-height:1.5;color:#777777;border-top:1px solid #eeeeee;">'
		. $e( $c['why'] ) . ' <a href="' . esc_url( $optout ) . '" style="color:#777777;text-decoration:underline;">' . $e( $c['optout'] ) . '</a>'
		. '</td></tr></table></td></tr></table></body></html>';
	return $out;
}

/** Subject + plain-text body + HTML body (CZ or EN). Index 1 stays the plain text. */
function molosoc_review_request_message( $order ) {
	$cz       = molosoc_review_request_is_cz_lang( $order );
	$products = molosoc_review_request_products( $order, $cz );
	if ( ! $products ) {
		return null;
	}
	$optout = molosoc_review_request_optout_url( $order->get_id() );
	$c      = molosoc_review_request_copy( $cz, $order->get_order_number() );
	$lines  = '';
	foreach ( $products as $p ) {
		$lines .= $p[0] . ': ' . $p[1] . "\n";
	}
	$body = $c['hello'] . "\n\n" . $c['intro'] . "\n\n" . $lines . "\n" . $c['note'] . "\n\n"
		. $c['why'] . ' ' . $c['optout_t'] . "\n" . $optout . "\n\n" . $c['bye'] . "\nMOLOSOC";
	return array( $c['subject'], $body, molosoc_review_request_html( $c, $products, $optout ) );
}

/** Per-send multipart/alternative: the plain-text part of the message in flight (set only around one wp_mail call). */
function molosoc_review_request_altbody( $phpmailer ) {
	if ( isset( $GLOBALS['molosoc_review_request_alt'] ) && is_object( $phpmailer ) ) {
		$phpmailer->AltBody = $GLOBALS['molosoc_review_request_alt']; // phpcs:ignore WordPress.NamingConventions.ValidVariableName
	}
}

/** Send the message as branded HTML from MOLOSOC <hello@molosoc.com>, with a plain-text alternative. Scoped to this one call. */
function molosoc_review_request_send_mail( $to, $msg ) {
	$from    = molosoc_review_request_from();
	$headers = array(
		'Content-Type: text/html; charset=UTF-8',
		'From: ' . $from['name'] . ' <' . $from['email'] . '>',
	);
	$GLOBALS['molosoc_review_request_alt'] = $msg[1];
	add_action( 'phpmailer_init', 'molosoc_review_request_altbody' );
	$ok = wp_mail( $to, $msg[0], $msg[2], $headers );
	remove_action( 'phpmailer_init', 'molosoc_review_request_altbody' );
	unset( $GLOBALS['molosoc_review_request_alt'] );
	return $ok;
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
	// Czech Act 480/2004 s.7(3): only customers who saw the collection-time
	// notice and could refuse. Orders placed before the notice existed (or
	// while the feature was off) are never mailed.
	if ( ! $order->get_meta( MOLOSOC_REVIEW_REQUEST_NOTICE_META ) ) {
		return 'no-checkout-notice';
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

	// Atomic per-order claim: an insert-only INSERT IGNORE on the unique
	// option_name, so only one overlapping callback can win. Send only if the
	// claim was acquired.
	$claim_key = 'molosoc_rr_claim_' . (int) $order_id;
	if ( ! molosoc_review_request_insert_once( $claim_key, (string) time() ) ) {
		return;
	}
	$order->update_meta_data( MOLOSOC_REVIEW_REQUEST_SENT_META, (string) time() );
	$order->save();
	if ( molosoc_review_request_send_mail( $to, $msg ) ) {
		$order->add_order_note( 'Odeslána žádost o hodnocení produktu.' );
		return;
	}
	// Mail failed: release both claims so the scheduled retry can try again.
	$order->delete_meta_data( MOLOSOC_REVIEW_REQUEST_SENT_META );
	$order->save();
	delete_option( $claim_key );
	if ( $attempt < MOLOSOC_REVIEW_REQUEST_MAX_RETRIES && function_exists( 'as_schedule_single_action' ) ) {
		as_schedule_single_action( time() + HOUR_IN_SECONDS, MOLOSOC_REVIEW_REQUEST_HOOK, array( (int) $order_id, $attempt + 1 ), 'molosoc', true );
	}
}
add_action( MOLOSOC_REVIEW_REQUEST_HOOK, 'molosoc_review_request_run', 10, 2 );

/**
 * Insert-only option write. WordPress add_option() uses ON DUPLICATE KEY UPDATE,
 * so a competing writer would also "succeed"; INSERT IGNORE rejects the
 * duplicate (0 rows affected) and exactly one caller gets true.
 */
function molosoc_review_request_insert_once( $key, $value ) {
	global $wpdb;
	$rows = $wpdb->query(
		$wpdb->prepare(
			"INSERT IGNORE INTO {$wpdb->options} (option_name, option_value, autoload) VALUES (%s, %s, 'no')",
			$key,
			$value
		)
	);
	if ( 1 === (int) $rows ) {
		wp_cache_delete( $key, 'options' );
		wp_cache_delete( 'notoptions', 'options' );
		return true;
	}
	return false;
}

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
		// Insert-only on a unique key: no read-modify-write race.
		molosoc_review_request_insert_once( molosoc_review_request_suppress_key( $order->get_billing_email() ), (string) time() );
	}
	wp_die( 'Hotovo, žádost o hodnocení již nebudeme posílat. / Done, we will not send you a review request.', 'MOLOSOC', array( 'response' => 200 ) );
}
add_action( 'template_redirect', 'molosoc_review_request_handle_optout', 1 );


/**
 * Checkout collection-time disclosure + easy opt-out (Issue #337, Option B).
 * Shown only when the mode is dry_run/live. It is an opt-OUT: the box is
 * unchecked by default and ticking it means "do not send". Placed after the
 * order notes (outside the AJAX-refreshed payment fragment, so the tick is
 * not lost). The notice is stored on the order, which is what makes the
 * order eligible later.
 */
function molosoc_review_request_checkout_text( $cz ) {
	if ( $cz ) {
		return array(
			'E-maily k objednávce, platbě a doručení dostanete automaticky. Odděleně od nich vám po nákupu pošleme jednu zprávu s prosbou o hodnocení produktu na webu MOLOSOC. Nejde o newsletter, nic dalšího v této věci posílat nebudeme a odhlásit se můžete i přímo v ní. Souhlas s obchodními podmínkami není souhlasem s marketingem a nákupu se toto pole nijak netýká.',
			'Nechci dostat tuto jednu zprávu s prosbou o hodnocení',
			'Informace o zpracování osobních údajů',
		);
	}
	return array(
		'You will receive the e-mails about your order, payment and delivery automatically. Separately, after your purchase we will send you one message asking you to review the product on MOLOSOC. It is not a newsletter, we will send nothing else about it, and you can also opt out in the message itself. Accepting the Terms is not marketing consent, and this option does not affect your purchase.',
		'I do not want to receive this one review-request message',
		'Information on personal data processing',
	);
}

function molosoc_review_request_checkout_field() {
	if ( 'off' === molosoc_review_request_mode() ) {
		return;
	}
	$cz = function_exists( 'pll_current_language' ) && 'cz' === pll_current_language();
	list( $notice, $label, $privacy ) = molosoc_review_request_checkout_text( $cz );
	$privacy_url = home_url( $cz ? '/zasady-ochrany-osobnich-udaju/' : '/privacy-policies/' );
	echo '<div class="molosoc-review-optout" style="margin:1em 0">'
		. '<p>' . esc_html( $notice ) . ' <a href="' . esc_url( $privacy_url ) . '" target="_blank" rel="noopener">' . esc_html( $privacy ) . '</a></p>'
		. '<label><input type="checkbox" name="molosoc_review_request_refuse" value="1"> ' . esc_html( $label ) . '</label>'
		. '<input type="hidden" name="molosoc_review_request_notice_shown" value="1">'
		. '</div>';
}
add_action( 'woocommerce_after_order_notes', 'molosoc_review_request_checkout_field' );

/** Record notice shown / refusal on the new order; a refusal also suppresses the address for any other order. */
function molosoc_review_request_checkout_save( $order, $data = array() ) {
	if ( 'off' === molosoc_review_request_mode() ) {
		return;
	}
	// phpcs:ignore WordPress.Security.NonceVerification -- WooCommerce verifies the checkout nonce before this hook.
	if ( empty( $_POST['molosoc_review_request_notice_shown'] ) ) {
		return; // notice not rendered with this submission: order stays ineligible.
	}
	$order->update_meta_data( MOLOSOC_REVIEW_REQUEST_NOTICE_META, (string) time() );
	// phpcs:ignore WordPress.Security.NonceVerification
	if ( ! empty( $_POST['molosoc_review_request_refuse'] ) ) {
		$order->update_meta_data( MOLOSOC_REVIEW_REQUEST_OPTOUT_META, (string) time() );
		$email = isset( $_POST['billing_email'] ) ? sanitize_email( wp_unslash( $_POST['billing_email'] ) ) : '';
		if ( $email ) {
			molosoc_review_request_insert_once( molosoc_review_request_suppress_key( $email ), (string) time() );
		}
	}
}
add_action( 'woocommerce_checkout_create_order', 'molosoc_review_request_checkout_save', 20, 2 );
