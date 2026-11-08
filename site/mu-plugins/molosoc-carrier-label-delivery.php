<?php
/**
 * Plugin Name: MOLOSOC Carrier Label Delivery (Phase 3, disabled by default, mocks only)
 * Description: Staged label-PDF + dispatch-mail stage for the carrier label pipeline. Validates a label PDF, mails it to the dispatcher through an injected mailer, idempotently and fail-closed. No live provider and no live mailer exist in this file. Issue #356.
 * Version: 0.1.0
 *
 * SAFETY CONTRACT
 *
 *   - Inert unless ALL hold: wp_get_environment_type() is `staging` or
 *     `local`; wp-config.php defines MOLOSOC_LABEL_DELIVERY_ENABLED as true;
 *     and the Phase 1 plugin is present. Production can never activate it.
 *   - This file contains NO carrier call, NO network call and NO mail
 *     function (no wp_mail). A "provider" returns label PDF bytes and a
 *     "mailer" delivers them; both are injected through filters. A result
 *     with live=true from either is REFUSED. The only implementations that
 *     ship are in-memory mocks that write to a per-order options outbox (molosoc_ld3_mock_outbox_<order id>).
 *   - Order status is never changed; customers are never e-mailed; historical
 *     orders are never processed (the Phase 1 cut-off option is required).
 *   - The audit holds ids, carrier, subject, PDF sha256/size and outcome only.
 *     The PDF itself and any customer data are never stored.
 *
 * STAGES (each persisted, so a retry resumes and never repeats a stage)
 *
 *   ''            -> nothing done
 *   label_ready   -> a valid PDF was produced; carrier ref + sha256 stored
 *   mailing       -> the mailer is being called (written BEFORE the call)
 *   mailed        -> mailer reported success (terminal)
 *   attention     -> needs a human (terminal until an operator clears it)
 *
 *   If a request dies after `mailing` was written, the mail may or may not
 *   have left. Retry does NOT resend: it moves the order to `attention`
 *   (at-most-once mail beats a duplicate dispatch to the warehouse).
 *   Provider calls on retry receive the stored carrier ref so a real provider
 *   must FETCH the existing label and never create a second shipment.
 *
 * See docs/carrier-label-delivery-356.md for the carrier source findings and
 * the exact blockers before any live provider can exist.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const MOLOSOC_LD3_STATE_META = '_molosoc_label_delivery_state';
const MOLOSOC_LD3_REF_META   = '_molosoc_label_delivery_ref';
const MOLOSOC_LD3_TRY_META   = '_molosoc_label_delivery_tries';
const MOLOSOC_LD3_MAX_TRIES  = 3;
const MOLOSOC_LD3_PDF_MIN    = 200;
const MOLOSOC_LD3_PDF_MAX    = 5242880; // 5 MB.

/** True only on a non-production environment type with the explicit constant. */
function molosoc_ld3_enabled( string $env_type, $constant ): bool {
	return in_array( $env_type, array( 'staging', 'local' ), true ) && true === $constant;
}

/**
 * A label must be one real PDF: %PDF- header, %%EOF near the end, sane size,
 * at least one page object. Returns array( bool ok, string reason ).
 */
function molosoc_ld3_validate_pdf( $bytes ): array {
	if ( ! is_string( $bytes ) || '' === $bytes ) {
		return array( false, 'pdf_empty' );
	}
	$len = strlen( $bytes );
	if ( $len < MOLOSOC_LD3_PDF_MIN ) {
		return array( false, 'pdf_too_small' );
	}
	if ( $len > MOLOSOC_LD3_PDF_MAX ) {
		return array( false, 'pdf_too_large' );
	}
	if ( 0 !== strpos( $bytes, '%PDF-' ) ) {
		return array( false, 'pdf_bad_header' );
	}
	if ( false === strpos( substr( $bytes, -1024 ), '%%EOF' ) ) {
		return array( false, 'pdf_truncated' );
	}
	if ( 0 === preg_match( '#/Type\s*/Page(?![s\w])#', $bytes ) ) {
		return array( false, 'pdf_no_page' );
	}
	return array( true, 'ok' );
}

/** ASCII attachment name, e.g. ppl-1234.pdf / zasilkovna-1234.pdf. */
function molosoc_ld3_filename( string $carrier, int $order_id ): string {
	$slug = 'PPL' === $carrier ? 'ppl' : ( 'Zásilkovna' === $carrier ? 'zasilkovna' : '' );
	return '' === $slug ? '' : $slug . '-' . $order_id . '.pdf';
}

/**
 * Runs the delivery stage for one order with injectable I/O:
 *   snapshot()                 fresh Phase 1 style snapshot (done = delivered)
 *   state() / set_state($s)    persisted stage
 *   ref() / set_ref($r)        persisted carrier reference
 *   tries() / set_tries($n)    persisted failed-attempt counter
 *   lock() / unlock()          per-order lock; lock() false = held
 *   audit($row)                append-only audit
 *   provider($carrier, $ref)   array( ok, live, pdf, ref, reason )
 *   mailer($mail)              array( ok, live, reason ); $mail = to, subject, filename, pdf
 * Eligibility reuses molosoc_ld_decide() (Comgate-confirmed card or COD,
 * processing, after cut-off, known carrier and sizes). Re-checked after the
 * lock. Any exception is audited; terminal states are never re-run.
 * `$io['allow_live']` (bool, default false) is set only by the separately gated
 * live plugin (Issue #358); without it a live=true result is refused as before.
 * A provider result with `permanent=true` goes straight to `attention`.
 */
function molosoc_ld3_process( int $order_id, array $io ): string {
	$state = (string) $io['state']();
	if ( 'mailed' === $state ) {
		$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => 'already_mailed' ) );
		return 'already_mailed';
	}
	if ( 'attention' === $state ) {
		$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => 'needs_attention' ) );
		return 'needs_attention';
	}
	$snap = $io['snapshot']();
	[ $ok, $reason ] = molosoc_ld_decide( $snap );
	if ( ! $ok ) {
		$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => $reason ) );
		return $reason;
	}
	if ( ! $io['lock']() ) {
		$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => 'locked' ) );
		return 'locked';
	}
	try {
		// Re-read everything after taking the lock.
		$state = (string) $io['state']();
		if ( 'mailed' === $state || 'attention' === $state ) {
			$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => 'recheck_' . $state ) );
			return 'recheck_' . $state;
		}
		$snap = $io['snapshot']();
		[ $ok, $reason ] = molosoc_ld_decide( $snap );
		if ( ! $ok ) {
			$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => 'recheck_' . $reason ) );
			return 'recheck_' . $reason;
		}
		if ( 'mailing' === $state ) {
			// Crash window: the mail may already have been sent. Never resend.
			$io['set_state']( 'attention' );
			$io['audit']( array( 'order' => $order_id, 'result' => 'attention', 'reason' => 'mail_state_unknown' ) );
			return 'mail_state_unknown';
		}
		if ( (int) $io['tries']() >= MOLOSOC_LD3_MAX_TRIES ) {
			$io['set_state']( 'attention' );
			$io['audit']( array( 'order' => $order_id, 'result' => 'attention', 'reason' => 'max_tries' ) );
			return 'max_tries';
		}

		$carrier = (string) $snap['carrier'];
		$subject = molosoc_ld_subject( $carrier, (array) $snap['sizes'] );
		$file    = molosoc_ld3_filename( $carrier, $order_id );
		if ( null === $subject || '' === $file ) {
			$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => 'subject_unusable' ) );
			return 'subject_unusable';
		}

		// Stage 1: label PDF. Always asked with the stored ref so a real provider fetches, not creates.
		$allow_live = ! empty( $io['allow_live'] );
		$res        = $io['provider']( $carrier, (string) $io['ref']() );
		if ( ! empty( $res['live'] ) && ! $allow_live ) {
			$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => 'live_provider_refused' ) );
			return 'live_provider_refused';
		}
		if ( empty( $res['ok'] ) && ! empty( $res['permanent'] ) ) {
			$io['set_state']( 'attention' );
			$io['audit']( array( 'order' => $order_id, 'result' => 'attention', 'reason' => 'provider_permanent', 'detail' => (string) ( $res['reason'] ?? '' ) ) );
			return 'provider_permanent';
		}
		if ( empty( $res['ok'] ) ) {
			$io['set_tries']( (int) $io['tries']() + 1 );
			$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => 'provider_failed', 'detail' => (string) ( $res['reason'] ?? '' ) ) );
			return 'provider_failed';
		}
		[ $pdf_ok, $pdf_reason ] = molosoc_ld3_validate_pdf( $res['pdf'] ?? null );
		if ( ! $pdf_ok ) {
			$io['set_tries']( (int) $io['tries']() + 1 );
			$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => $pdf_reason ) );
			return $pdf_reason;
		}
		$ref = (string) ( $res['ref'] ?? '' );
		if ( '' === $ref ) {
			$io['set_tries']( (int) $io['tries']() + 1 );
			$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => 'ref_missing' ) );
			return 'ref_missing';
		}
		$stored = (string) $io['ref']();
		if ( '' !== $stored && $stored !== $ref ) {
			// A different shipment than the one recorded: possible duplicate shipment. Stop.
			$io['set_state']( 'attention' );
			$io['audit']( array( 'order' => $order_id, 'result' => 'attention', 'reason' => 'ref_changed' ) );
			return 'ref_changed';
		}
		$io['set_ref']( $ref );
		$io['set_state']( 'label_ready' );
		$io['audit'](
			array(
				'order'  => $order_id,
				'result' => 'label_ready',
				'ref'    => $ref,
				'sha256' => hash( 'sha256', $res['pdf'] ),
				'bytes'  => strlen( $res['pdf'] ),
			)
		);

		// Stage 2: mail. State is written BEFORE the call (at-most-once).
		$io['set_state']( 'mailing' );
		$mail = array(
			'to'       => MOLOSOC_LD_RECIPIENT,
			'subject'  => $subject,
			'filename' => $file,
			'pdf'      => $res['pdf'],
		);
		$sent = $io['mailer']( $mail );
		if ( ! empty( $sent['live'] ) && ! $allow_live ) {
			$io['set_state']( 'attention' );
			$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => 'live_mailer_refused' ) );
			return 'live_mailer_refused';
		}
		if ( empty( $sent['ok'] ) ) {
			// Mailer reported a definite failure: nothing left, so resuming from label_ready is safe.
			$io['set_state']( 'label_ready' );
			$io['set_tries']( (int) $io['tries']() + 1 );
			$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => 'mailer_failed', 'detail' => (string) ( $sent['reason'] ?? '' ) ) );
			return 'mailer_failed';
		}
		$io['set_state']( 'mailed' );
		$live = $allow_live && ! empty( $sent['live'] );
		$io['audit']( array( 'order' => $order_id, 'result' => $live ? 'mailed' : 'mocked_mailed', 'carrier' => $carrier, 'subject' => $subject, 'to' => MOLOSOC_LD_RECIPIENT, 'live' => $live ) );
		return $live ? 'mailed' : 'mocked_mailed';
	} catch ( \Throwable $e ) {
		// A throw after `mailing` was written leaves that state; the next run goes to attention.
		$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => 'exception', 'class' => get_class( $e ) ) );
		return 'exception';
	} finally {
		$io['unlock']();
	}
}

/* ------------------------------------------------------------ mock plumbing */

/** Smallest valid single-page PDF (mock label). No customer data. */
function molosoc_ld3_mock_pdf( string $carrier, string $ref ): string {
	$text = 'MOCK LABEL ' . $carrier . ' ' . $ref . str_repeat( ' ', 120 );
	return "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
		. "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 283 425]>>endobj\n% " . $text . "\ntrailer<</Root 1 0 R>>\n%%EOF\n";
}

/** Mock provider: deterministic per order+carrier, idempotent, never live. */
function molosoc_ld3_mock_provider( string $carrier, int $order_id, string $stored_ref, bool $packet_submitted ): array {
	if ( 'PPL' !== $carrier && 'Zásilkovna' !== $carrier ) {
		return array( 'ok' => false, 'live' => false, 'reason' => 'unknown_carrier' );
	}
	if ( 'Zásilkovna' === $carrier && ! $packet_submitted ) {
		return array( 'ok' => false, 'live' => false, 'reason' => 'packet_not_submitted' );
	}
	$ref = '' !== $stored_ref ? $stored_ref : 'MOCK-' . strtoupper( substr( sha1( $carrier . ':' . $order_id ), 0, 10 ) );
	return array( 'ok' => true, 'live' => false, 'ref' => $ref, 'pdf' => molosoc_ld3_mock_pdf( $carrier, $ref ) );
}

/**
 * Mock mailer: validates the outgoing message exactly as a real one would be
 * required to, then records metadata (never the PDF) and reports success.
 */
function molosoc_ld3_mock_mailer( array $mail, array $outbox ): array {
	if ( MOLOSOC_LD_RECIPIENT !== ( $mail['to'] ?? '' ) ) {
		return array( array( 'ok' => false, 'live' => false, 'reason' => 'recipient_mismatch' ), $outbox );
	}
	if ( 1 !== preg_match( '/^(PPL|Zásilkovna) \| \d+ (kus|kusy|kusů) \| /u', (string) ( $mail['subject'] ?? '' ) ) ) {
		return array( array( 'ok' => false, 'live' => false, 'reason' => 'subject_mismatch' ), $outbox );
	}
	if ( 1 !== preg_match( '/^(ppl|zasilkovna)-\d+\.pdf$/', (string) ( $mail['filename'] ?? '' ) ) ) {
		return array( array( 'ok' => false, 'live' => false, 'reason' => 'filename_mismatch' ), $outbox );
	}
	[ $ok, $reason ] = molosoc_ld3_validate_pdf( $mail['pdf'] ?? null );
	if ( ! $ok ) {
		return array( array( 'ok' => false, 'live' => false, 'reason' => $reason ), $outbox );
	}
	$outbox[] = array(
		'to'       => $mail['to'],
		'subject'  => $mail['subject'],
		'filename' => $mail['filename'],
		'sha256'   => hash( 'sha256', $mail['pdf'] ),
	);
	return array( array( 'ok' => true, 'live' => false ), $outbox );
}

/* ---------------------------------------------------------------- WP glue */

function molosoc_ld3_snapshot( int $order_id ): array {
	$snap         = molosoc_ld_snapshot( $order_id );
	$snap['done'] = false; // Phase 1's dry-run marker is not a delivery marker; this stage keeps its own state.
	return $snap;
}

function molosoc_ld3_meta_get( int $order_id, string $key ): string {
	$order = wc_get_order( $order_id );
	return $order ? (string) $order->get_meta( $key ) : '';
}

function molosoc_ld3_meta_set( int $order_id, string $key, string $value ): void {
	$order = wc_get_order( $order_id );
	if ( $order ) {
		$order->update_meta_data( $key, $value );
		$order->save_meta_data();
	}
}

/** Runs the stage for one order. Also the operator retry entry point. */
function molosoc_ld3_run( $order_id ): string {
	$order_id = (int) $order_id;
	$lock_key = 'molosoc_ld3_lock_' . $order_id;
	return molosoc_ld3_process(
		$order_id,
		array(
			'snapshot'  => static function () use ( $order_id ) {
				return molosoc_ld3_snapshot( $order_id );
			},
			'state'     => static function () use ( $order_id ) {
				return molosoc_ld3_meta_get( $order_id, MOLOSOC_LD3_STATE_META );
			},
			'set_state' => static function ( $s ) use ( $order_id ) {
				molosoc_ld3_meta_set( $order_id, MOLOSOC_LD3_STATE_META, (string) $s );
			},
			'ref'       => static function () use ( $order_id ) {
				return molosoc_ld3_meta_get( $order_id, MOLOSOC_LD3_REF_META );
			},
			'set_ref'   => static function ( $r ) use ( $order_id ) {
				molosoc_ld3_meta_set( $order_id, MOLOSOC_LD3_REF_META, (string) $r );
			},
			'tries'     => static function () use ( $order_id ) {
				return (int) molosoc_ld3_meta_get( $order_id, MOLOSOC_LD3_TRY_META );
			},
			'set_tries' => static function ( $n ) use ( $order_id ) {
				molosoc_ld3_meta_set( $order_id, MOLOSOC_LD3_TRY_META, (string) (int) $n );
			},
			// add_option is a unique-key insert, so only one request wins. No expiry
			// takeover here: a stuck lock is an operator matter (see operator doc).
			'lock'      => static function () use ( $lock_key ) {
				return (bool) add_option( $lock_key, time(), '', 'no' );
			},
			'unlock'    => static function () use ( $lock_key ) {
				delete_option( $lock_key );
			},
			'audit'     => static function ( array $row ) use ( $order_id ) {
				$order = wc_get_order( $order_id );
				if ( $order ) {
					$order->add_meta_data( MOLOSOC_LD_AUDIT_META, wp_json_encode( array_merge( array( 'ts' => gmdate( 'c' ), 'stage' => 'delivery' ), $row ) ), false );
					$order->save_meta_data();
				}
			},
			'provider'  => static function ( $carrier, $ref ) use ( $order_id ) {
				$custom = apply_filters( 'molosoc_label_delivery_provider', null, $carrier, $order_id, $ref );
				if ( is_array( $custom ) ) {
					return $custom;
				}
				$submitted = ! empty( ( (array) get_option( 'molosoc_ls_mock_submitted', array() ) )[ $order_id ] );
				return molosoc_ld3_mock_provider( (string) $carrier, $order_id, (string) $ref, $submitted );
			},
			'mailer'    => static function ( $mail ) use ( $order_id ) {
				$custom = apply_filters( 'molosoc_label_delivery_mailer', null, $mail );
				if ( is_array( $custom ) ) {
					return $custom;
				}
				// One option per order: the per-order lock serializes writes to it, so
				// concurrent deliveries of different orders never share a read-modify-write.
				$outbox_key = 'molosoc_ld3_mock_outbox_' . $order_id;
				$outbox     = (array) get_option( $outbox_key, array() );
				[ $res, $outbox ] = molosoc_ld3_mock_mailer( $mail, $outbox );
				update_option( $outbox_key, $outbox, false );
				return $res;
			},
		)
	);
}

if ( function_exists( 'wp_get_environment_type' )
	&& molosoc_ld3_enabled( wp_get_environment_type(), defined( 'MOLOSOC_LABEL_DELIVERY_ENABLED' ) ? MOLOSOC_LABEL_DELIVERY_ENABLED : null ) ) {
	// MU plugins load alphabetically, so the dispatch core (molosoc_ld_decide) is not
	// defined yet when this file runs. Defer the dependency check until all have loaded.
	add_action(
		'muplugins_loaded',
		static function () {
			if ( function_exists( 'molosoc_ld_decide' ) ) {
				add_action( 'woocommerce_order_status_processing', 'molosoc_ld3_run', 30, 1 );
			}
		}
	);
}
