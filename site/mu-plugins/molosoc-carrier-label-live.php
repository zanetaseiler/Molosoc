<?php
/**
 * Plugin Name: MOLOSOC Carrier Label Live Activation (OFF by default, single-order allowlist)
 * Description: Production-capable provider + wp_mail mailer for the carrier label pipeline, behind an explicit opt-in and an allowlist of exactly ONE order id. Issue #358.
 * Version: 0.1.0
 *
 * SAFETY CONTRACT
 *
 *   - Inert unless wp-config.php defines BOTH
 *       MOLOSOC_LABEL_LIVE_ENABLED   === true
 *       MOLOSOC_LABEL_LIVE_ORDER_IDS === array( <exactly one positive int> )
 *     Merging/deploying this file changes nothing by itself.
 *   - Only the allowlisted order is ever touched; every other order is ignored
 *     before any lookup. Historic bulk processing is impossible (one id, plus the
 *     Phase 1 cut-off and `processing` status checks inside molosoc_ld_decide()).
 *   - Refuses to run while the mock delivery plugin is also enabled.
 *   - Reuses the Phase 1/3 state machine: eligibility (processing + Comgate-confirmed
 *     card or COD, never bank transfer), at-most-once mail, stored carrier ref,
 *     tries limit, append-only audit (ids, subject, sha256, size only).
 *   - This file NEVER creates a shipment/packet and never changes order status.
 *     Packeta packets are created by the Packeta plugin's own auto-submission
 *     (which skips already exported orders). This file only FETCHES the label.
 *   - Mail goes to MOLOSOC_LD_RECIPIENT only, with the PDF attached from a
 *     temporary file that is always removed.
 *
 * UNVERIFIED PLUGIN FACTS (not guessed; supplied by the operator)
 *
 *   - Packeta (Issue #369, checked on production): Packeta 2.3.2 keeps the packet
 *     id in its own table `{prefix}packetery_order.packet_id` (keyed by order id),
 *     not in order meta. It is read there with one prepared, read-only SELECT.
 *     The API password is MOLOSOC_LL_PACKETA_API_PASSWORD when defined, otherwise
 *     the `api_password` Packeta already stores in its own `packetery` option, so
 *     no secret has to be copied anywhere. It is never logged, audited or shown.
 *     Without a password the provider fails closed (`packeta_unconfigured`).
 *     The label call uses Packeta's own documented API (SOAP `packetLabelPdf`),
 *     not plugin internals, and is verified only by the controlled one-order test.
 *   - PPL: no headless path exists in PPL CZ 1.1.3; labels stay manual. The
 *     provider returns a permanent failure (state `attention`), nothing is mailed.
 *
 * See docs/carrier-label-activation-358.md.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const MOLOSOC_LL_RETRY_HOOK  = 'molosoc_ll_retry';
const MOLOSOC_LL_RETRY_DELAY = 300;
// Issue #363: fixed sender used only when MOLOSOC_LL_MAIL_FROM_EXPLICIT === true (OFF by default).
const MOLOSOC_LL_FROM_EMAIL = 'hello@molosoc.com';
const MOLOSOC_LL_FROM_NAME  = 'MOLOSOC';

/**
 * Pure header builder. Default (`$explicit_from` not exactly true) is byte-identical to
 * the pre-#363 headers: no From header, so WordPress / the active mail plugin (e.g.
 * Brevo) decides the sender. Opt-in adds one fixed `From:` built only from constants.
 * Note: a `wp_mail_from` filter (SMTP/Brevo plugins) can still override it; verify with
 * the operator checks in docs/carrier-label-brevo-readiness-363.md.
 */
function molosoc_ll_headers( $explicit_from ): array {
	$h = array( 'Content-Type: text/plain; charset=UTF-8', 'Cc: ' . MOLOSOC_LD_CC );
	if ( true === $explicit_from ) {
		$h[] = 'From: ' . MOLOSOC_LL_FROM_NAME . ' <' . MOLOSOC_LL_FROM_EMAIL . '>';
	}
	return $h;
}

/** Packeta packet id shape (digits, optional `Z` barcode prefix). Non-strings are invalid. */
function molosoc_ll_packet_id_valid( $id ): bool {
	return is_string( $id ) && 1 === preg_match( '/^Z?\d{5,20}$/', $id );
}

/**
 * Issue #369: a provider success is accepted only for the approved packet. Any other
 * packet id is a permanent failure (`attention`), so a re-exported or duplicate packet
 * is never mailed. Failures pass through unchanged.
 */
function molosoc_ll_require_approved( array $res, string $approved ): array {
	if ( empty( $res['ok'] ) ) {
		return $res;
	}
	if ( ! molosoc_ll_packet_id_valid( $approved ) || ! hash_equals( $approved, (string) ( $res['ref'] ?? '' ) ) ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => 'packet_not_approved' );
	}
	return $res;
}

/**
 * Pure gate. Returns array( bool allowed, string reason ).
 * `$enabled` must be exactly true; `$ids` must be an array of exactly one positive int;
 * `$approved_packet` (Issue #369) must be the well-formed Packeta packet id approved
 * after the read-only preview.
 */
function molosoc_ll_gate( $enabled, $ids, bool $mock_enabled, int $order_id, $approved_packet = null ): array {
	if ( true !== $enabled ) {
		return array( false, 'live_disabled' );
	}
	if ( ! is_array( $ids ) || 1 !== count( $ids ) ) {
		return array( false, 'allowlist_must_be_exactly_one_order' );
	}
	$only = reset( $ids );
	if ( ! is_int( $only ) || $only <= 0 ) {
		return array( false, 'allowlist_invalid_id' );
	}
	// Issue #369: the live send is pinned to the one packet Žaneta approved after the read-only preview.
	if ( ! molosoc_ll_packet_id_valid( $approved_packet ) ) {
		return array( false, 'approved_packet_missing' );
	}
	if ( $mock_enabled ) {
		return array( false, 'mock_delivery_also_enabled' );
	}
	if ( $order_id !== $only ) {
		return array( false, 'order_not_allowlisted' );
	}
	return array( true, 'allowed' );
}

/**
 * Real mailer. `$send( to, subject, body, headers, attachments )` is wp_mail; `$tmp(
 * filename, bytes )` returns a temp file path or '' and `$rm( path )` removes it.
 * Success means wp_mail accepted the message for sending (it cannot confirm delivery).
 */
function molosoc_ll_mail( array $mail, callable $send, callable $tmp, callable $rm, $explicit_from = false ): array {
	if ( MOLOSOC_LD_RECIPIENT !== ( $mail['to'] ?? '' ) ) {
		return array( 'ok' => false, 'live' => true, 'reason' => 'recipient_mismatch' );
	}
	// Only the fixed constant may ever reach a header: exact match, no user data, no CR/LF.
	if ( MOLOSOC_LD_CC !== ( $mail['cc'] ?? '' ) ) {
		return array( 'ok' => false, 'live' => true, 'reason' => 'cc_mismatch' );
	}
	if ( 1 !== preg_match( '/^(PPL|Zásilkovna) \| \d+ (kus|kusy|kusů) \| /u', (string) ( $mail['subject'] ?? '' ) ) ) {
		return array( 'ok' => false, 'live' => true, 'reason' => 'subject_mismatch' );
	}
	if ( 1 !== preg_match( '/^(ppl|zasilkovna)-\d+\.pdf$/', (string) ( $mail['filename'] ?? '' ) ) ) {
		return array( 'ok' => false, 'live' => true, 'reason' => 'filename_mismatch' );
	}
	[ $ok, $reason ] = molosoc_ld3_validate_pdf( $mail['pdf'] ?? null );
	if ( ! $ok ) {
		return array( 'ok' => false, 'live' => true, 'reason' => $reason );
	}
	$path = (string) $tmp( $mail['filename'], $mail['pdf'] );
	if ( '' === $path ) {
		return array( 'ok' => false, 'live' => true, 'reason' => 'tempfile_failed' );
	}
	try {
		$sent = (bool) $send(
			$mail['to'],
			$mail['subject'],
			'Štítek k odeslání v příloze.',
			molosoc_ll_headers( $explicit_from ),
			array( $path )
		);
	} finally {
		$rm( $path );
	}
	return $sent ? array( 'ok' => true, 'live' => true ) : array( 'ok' => false, 'live' => true, 'reason' => 'wp_mail_false' );
}

/**
 * Issue #369: Packeta API password. The wp-config constant wins when it is a non-empty
 * string; otherwise the password Packeta stores in its own `packetery` option is used.
 * Returns '' (fail closed) when neither is a usable single-line string. Never log it.
 */
function molosoc_ll_packeta_password( $constant, $packetery_option ): string {
	foreach ( array( $constant, is_array( $packetery_option ) ? ( $packetery_option['api_password'] ?? null ) : null ) as $pw ) {
		if ( is_string( $pw ) && '' !== trim( $pw ) && 1 !== preg_match( '/[\x00-\x1F\x7F]/', $pw ) ) {
			return trim( $pw );
		}
	}
	return '';
}

/**
 * Issue #369: read-only lookup of the packet id Packeta 2.3.2 stored for this order in
 * `{prefix}packetery_order` (column `packet_id`, row `id` = order id). Returns '' when the
 * table or row is missing or the value is NULL; the caller validates the shape.
 */
function molosoc_ll_packeta_packet_id( int $order_id ): string {
	global $wpdb;
	if ( $order_id <= 0 || ! isset( $wpdb ) || ! is_object( $wpdb ) ) {
		return '';
	}
	$table = $wpdb->prefix . 'packetery_order';
	if ( $table !== $wpdb->get_var( $wpdb->prepare( 'SHOW TABLES LIKE %s', $wpdb->esc_like( $table ) ) ) ) {
		return '';
	}
	$val = $wpdb->get_var( $wpdb->prepare( 'SELECT `packet_id` FROM `' . $table . '` WHERE `id` = %d LIMIT 1', $order_id ) );
	return is_string( $val ) ? trim( $val ) : '';
}

/**
 * Provider. `$d` holds injected I/O:
 *   packet_id         Packeta packet id of this order from Packeta's own table ('' = not submitted yet)
 *   api_password      Packeta API password, constant or Packeta's stored setting ('' = unconfigured)
 *   fetch( id, pw )   returns PDF bytes (string) or false on failure
 * It never creates a packet. A stored ref that differs from the current packet id is
 * returned as-is so the state machine flags `ref_changed` (possible duplicate).
 */
function molosoc_ll_provider( string $carrier, string $stored_ref, array $d ): array {
	if ( 'PPL' === $carrier ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => 'ppl_manual_label_required' );
	}
	if ( 'Zásilkovna' !== $carrier ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => 'unknown_carrier' );
	}
	if ( '' === (string) ( $d['api_password'] ?? '' ) ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => 'packeta_unconfigured' );
	}
	$packet = trim( (string) ( $d['packet_id'] ?? '' ) );
	if ( '' === $packet ) {
		return array( 'ok' => false, 'live' => true, 'reason' => 'packet_not_submitted' ); // Retryable: native submission may not have run yet.
	}
	if ( ! molosoc_ll_packet_id_valid( $packet ) ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => 'packet_id_malformed' );
	}
	$pdf = $d['fetch']( $packet, (string) $d['api_password'] );
	if ( ! is_string( $pdf ) || '' === $pdf ) {
		return array( 'ok' => false, 'live' => true, 'reason' => 'packeta_fetch_failed' );
	}
	return array( 'ok' => true, 'live' => true, 'ref' => $packet, 'pdf' => $pdf );
}

/** Outcomes that count as a failed, retryable attempt. */
function molosoc_ll_is_retryable_result( string $result ): bool {
	return in_array( $result, array( 'provider_failed', 'mailer_failed', 'pdf_empty', 'pdf_truncated', 'pdf_bad_header', 'pdf_no_page', 'pdf_too_small', 'pdf_too_large' ), true );
}

/** Retry decision: schedule one more attempt only for retryable outcomes under the tries limit. */
function molosoc_ll_should_retry( string $result, int $tries ): bool {
	return molosoc_ll_is_retryable_result( $result ) && $tries < MOLOSOC_LD3_MAX_TRIES;
}

/** True when a retryable failure just used up the last allowed attempt: the order must go to `attention` now. */
function molosoc_ll_exhausted( string $result, int $tries ): bool {
	return molosoc_ll_is_retryable_result( $result ) && $tries >= MOLOSOC_LD3_MAX_TRIES;
}

/* ---------------------------------------------------------------- WP glue */

function molosoc_ll_gate_now( int $order_id ): array {
	return molosoc_ll_gate(
		defined( 'MOLOSOC_LABEL_LIVE_ENABLED' ) ? MOLOSOC_LABEL_LIVE_ENABLED : null,
		defined( 'MOLOSOC_LABEL_LIVE_ORDER_IDS' ) ? MOLOSOC_LABEL_LIVE_ORDER_IDS : null,
		defined( 'MOLOSOC_LABEL_DELIVERY_ENABLED' ) && true === MOLOSOC_LABEL_DELIVERY_ENABLED,
		$order_id,
		defined( 'MOLOSOC_LABEL_LIVE_APPROVED_PACKET' ) ? MOLOSOC_LABEL_LIVE_APPROVED_PACKET : null
	);
}

/** Packeta SOAP `packetLabelPdf`. Unverified until the controlled test; see docs. */
function molosoc_ll_packeta_fetch( string $packet, string $password ) {
	if ( ! class_exists( 'SoapClient' ) ) {
		return false;
	}
	try {
		$client = new SoapClient( 'https://www.zasilkovna.cz/api/soap.wsdl', array( 'connection_timeout' => 15, 'exceptions' => true ) );
		$res    = $client->packetLabelPdf( $password, $packet, 'A6 on A6', 0 );
	} catch ( \Throwable $e ) {
		return false;
	}
	if ( is_string( $res ) && 0 === strpos( $res, '%PDF-' ) ) {
		return $res;
	}
	$dec = is_string( $res ) ? base64_decode( $res, true ) : false;
	return ( is_string( $dec ) && 0 === strpos( $dec, '%PDF-' ) ) ? $dec : false;
}

/** Packeta API password from wp-config or Packeta's own stored setting (Issue #369). */
function molosoc_ll_packeta_password_now(): string {
	return molosoc_ll_packeta_password(
		defined( 'MOLOSOC_LL_PACKETA_API_PASSWORD' ) ? MOLOSOC_LL_PACKETA_API_PASSWORD : null,
		get_option( 'packetery', null )
	);
}

/** Real provider for one order (fetch only, never creates a packet). */
function molosoc_ll_provider_now( int $order_id, string $carrier, string $ref ): array {
	if ( 'Zásilkovna' !== $carrier ) {
		return molosoc_ll_provider( $carrier, $ref, array() ); // PPL/unknown: no DB or password read.
	}
	return molosoc_ll_provider(
		$carrier,
		$ref,
		array(
			'packet_id'    => molosoc_ll_packeta_packet_id( $order_id ),
			'api_password' => molosoc_ll_packeta_password_now(),
			'fetch'        => 'molosoc_ll_packeta_fetch',
		)
	);
}

/** Entry point for the hook and for operator retries. Only the allowlisted order proceeds. */
function molosoc_ll_run( $order_id ): string {
	$order_id = (int) $order_id;
	[ $ok, $reason ] = molosoc_ll_gate_now( $order_id );
	if ( ! $ok ) {
		return $reason; // Silent: no order lookup, no audit for non-allowlisted orders.
	}
	$lock_key = 'molosoc_ll_lock_' . $order_id;
	$result   = molosoc_ld3_process(
		$order_id,
		array(
			'allow_live' => true,
			'snapshot'   => static function () use ( $order_id ) {
				return molosoc_ld3_snapshot( $order_id );
			},
			'state'      => static function () use ( $order_id ) {
				return molosoc_ld3_meta_get( $order_id, MOLOSOC_LD3_STATE_META );
			},
			'set_state'  => static function ( $s ) use ( $order_id ) {
				molosoc_ld3_meta_set( $order_id, MOLOSOC_LD3_STATE_META, (string) $s );
			},
			'ref'        => static function () use ( $order_id ) {
				return molosoc_ld3_meta_get( $order_id, MOLOSOC_LD3_REF_META );
			},
			'set_ref'    => static function ( $r ) use ( $order_id ) {
				molosoc_ld3_meta_set( $order_id, MOLOSOC_LD3_REF_META, (string) $r );
			},
			'tries'      => static function () use ( $order_id ) {
				return (int) molosoc_ld3_meta_get( $order_id, MOLOSOC_LD3_TRY_META );
			},
			'set_tries'  => static function ( $n ) use ( $order_id ) {
				molosoc_ld3_meta_set( $order_id, MOLOSOC_LD3_TRY_META, (string) (int) $n );
			},
			'lock'       => static function () use ( $lock_key ) {
				return (bool) add_option( $lock_key, time(), '', 'no' );
			},
			'unlock'     => static function () use ( $lock_key ) {
				delete_option( $lock_key );
			},
			'audit'      => static function ( array $row ) use ( $order_id ) {
				$order = wc_get_order( $order_id );
				if ( $order ) {
					$order->add_meta_data( MOLOSOC_LD_AUDIT_META, wp_json_encode( array_merge( array( 'ts' => gmdate( 'c' ), 'stage' => 'live' ), $row ) ), false );
					$order->save_meta_data();
				}
			},
			'provider'   => static function ( $carrier, $ref ) use ( $order_id ) {
				return molosoc_ll_require_approved(
					molosoc_ll_provider_now( $order_id, (string) $carrier, (string) $ref ),
					(string) MOLOSOC_LABEL_LIVE_APPROVED_PACKET // Defined: checked by the gate.
				);
			},
			'mailer'     => static function ( $mail ) {
				return molosoc_ll_mail(
					$mail,
					'wp_mail',
					static function ( $name, $bytes ) {
						// No wp-admin helper (wp_tempnam) needed: works on frontend/cron requests.
						// A private unique directory keeps the validated `<carrier>-<id>.pdf` name.
						$dir = rtrim( sys_get_temp_dir(), '/\\' ) . '/molosoc-label-' . bin2hex( random_bytes( 8 ) );
						if ( ! mkdir( $dir, 0700 ) ) {
							return '';
						}
						$path = $dir . '/' . basename( (string) $name );
						if ( false === file_put_contents( $path, $bytes ) ) {
							@unlink( $path );
							@rmdir( $dir );
							return '';
						}
						return $path;
					},
					static function ( $path ) {
						if ( is_string( $path ) && '' !== $path ) {
							if ( file_exists( $path ) ) {
								unlink( $path );
							}
							@rmdir( dirname( $path ) );
						}
					},
					defined( 'MOLOSOC_LL_MAIL_FROM_EXPLICIT' ) && true === MOLOSOC_LL_MAIL_FROM_EXPLICIT
				);
			},
		)
	);
	$tries = (int) molosoc_ld3_meta_get( $order_id, MOLOSOC_LD3_TRY_META );
	if ( molosoc_ll_exhausted( $result, $tries ) ) {
		// Last allowed attempt failed: persist the terminal state now instead of waiting for a run that never comes.
		molosoc_ld3_meta_set( $order_id, MOLOSOC_LD3_STATE_META, 'attention' );
		$order = wc_get_order( $order_id );
		if ( $order ) {
			$order->add_meta_data( MOLOSOC_LD_AUDIT_META, wp_json_encode( array( 'ts' => gmdate( 'c' ), 'stage' => 'live', 'order' => $order_id, 'result' => 'attention', 'reason' => 'max_tries' ) ), false );
			$order->save_meta_data();
		}
		return 'max_tries';
	}
	if ( molosoc_ll_should_retry( $result, $tries ) && function_exists( 'wp_schedule_single_event' )
		&& ! wp_next_scheduled( MOLOSOC_LL_RETRY_HOOK, array( $order_id ) ) ) {
		wp_schedule_single_event( time() + MOLOSOC_LL_RETRY_DELAY, MOLOSOC_LL_RETRY_HOOK, array( $order_id ) );
	}
	return $result;
}

if ( defined( 'MOLOSOC_LABEL_LIVE_ENABLED' ) && true === MOLOSOC_LABEL_LIVE_ENABLED ) {
	add_action(
		'muplugins_loaded',
		static function () {
			if ( function_exists( 'molosoc_ld_decide' ) && function_exists( 'molosoc_ld3_process' ) ) {
				add_action( 'woocommerce_order_status_processing', 'molosoc_ll_run', 40, 1 );
				add_action( MOLOSOC_LL_RETRY_HOOK, 'molosoc_ll_run', 10, 1 );
			}
		}
	);
}
