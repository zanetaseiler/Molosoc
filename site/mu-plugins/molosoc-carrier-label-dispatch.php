<?php
/**
 * Plugin Name: MOLOSOC Carrier Label Dispatch (Phase 1, dry-run only)
 * Description: Decides, for each WooCommerce order that reaches `processing`, whether a PPL / Zásilkovna label would be generated and e-mailed to the dispatcher, and records that decision. Phase 1 NEVER creates a label and NEVER sends mail. Issue #345.
 * Version: 0.1.0
 *
 * SAFETY CONTRACT (Phase 1)
 *
 *   - Inert unless wp-config.php defines MOLOSOC_LABEL_DISPATCH_DRY_RUN as
 *     true. Merging/deploying this file therefore changes nothing on its own.
 *   - There is no live mode in this file. The carrier adapters below are
 *     stubs that return a "would generate" result; they call no carrier
 *     code and no network. No mail-sending call exists in this file.
 *   - Order status is never changed; customers are never e-mailed.
 *   - The audit record holds order id, carrier, subject and outcome only:
 *     no names, addresses, e-mails, phone numbers or credentials.
 *
 * WHY THE ADAPTERS ARE STUBS (researched against upstream tags, Issue #345)
 *
 *   PPL CZ 1.1.3 (PPL-CZ/PPL-WooCommerce, tag 1.1.3): labels are created by
 *   CPLOperation::createPackages() (live CPL API call) and fetched by
 *   CPLOperation::getLabelContents(). Neither is a public hook or filter;
 *   both need BatchData/ShipmentData built from plugin internals.
 *   Packeta 2.3.2 (Zasilkovna/WooCommerce, tag v2.3.2): a label PDF exists
 *   only after the packet was submitted to the Packeta API
 *   (Client::packetsLabelsPdf / packetsCarrierLabelsPdf), a live action.
 *   A live adapter for either means calling non-public plugin internals and
 *   needs a staging test with credentials. That is a later phase and needs
 *   Žaneta's approval.
 *
 * COMGATE PAID DETECTION (ZANETA_DECISION 2026-11-08, Issue #352)
 *
 *   WisdomFactory Comgate plugin 1.1.40 (gateway id `wf-woo-comgate`; the
 *   legacy spelling `wf_woo_comgate` is also accepted) calls
 *   $order->payment_complete($transId) only on a Comgate PAID callback.
 *   A card order is therefore paid only if ALL of: status exactly
 *   `processing`; payment method is the Comgate gateway; a non-empty
 *   $order->get_transaction_id(); $order->is_paid(); and the transaction id
 *   is not merely the placeholder in `wf_gateway_tmp_transaction_id` (that
 *   meta is set even for unpaid orders and is NEVER used as a signal).
 *   `date_paid` or `processing` alone are unsafe (order #775 was cancelled
 *   after processing). No configurable meta key exists any more.
 *
 *   Issue #369 (ZANETA_DECISION 2026-11-11): live data showed all 34 paid
 *   Comgate orders keep `_transaction_id` EQUAL to
 *   `wf_gateway_tmp_transaction_id`, and unpaid ones have an empty
 *   `_transaction_id`. The documented rule is therefore `paid_status`:
 *   processing + Comgate gateway + non-empty transaction id + is_paid().
 *   The placeholder comparison (`strict`) now runs only when wp-config sets
 *   MOLOSOC_LABEL_COMGATE_TMPID_RULE to exactly 'strict'.
 *
 * CUT-OFF (Issue #369)
 *
 *   Orders created before the cut-off are never processed. The cut-off is the
 *   wp-config constant MOLOSOC_LABEL_DISPATCH_SINCE when defined (a Unix
 *   timestamp or an ISO 8601 date-time with offset, not before
 *   MOLOSOC_LD_SINCE_FLOOR), otherwise the `molosoc_label_dispatch_since`
 *   option. A defined but invalid constant fails closed (no fallback).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const MOLOSOC_LD_RECIPIENT      = 'jarka01@atlas.cz';
const MOLOSOC_LD_CC             = 'hello@molosoc.com'; // Issue #361: one copy of every dispatch mail, same message.
const MOLOSOC_LD_AUDIT_META     = '_molosoc_label_dispatch_audit';
const MOLOSOC_LD_STATE_META     = '_molosoc_label_dispatch_state';
const MOLOSOC_LD_LOCK_TTL       = 300;
const MOLOSOC_LD_SIZE_ORDER     = array( 'XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL' );
const MOLOSOC_LD_SIZE_META_KEYS = array( 'pa_size', 'pa_velikost' ); // new orders / older orders.
const MOLOSOC_LD_VARIATION_SIZES = array( 424 => 'L', 425 => 'M' );   // product 364 variations.
const MOLOSOC_LD_COMGATE_IDS     = array( 'wf-woo-comgate', 'wf_woo_comgate' );
// Issue #369: earliest cut-off a wp-config constant may set (2026-11-11T00:00:00Z, the decision date).
const MOLOSOC_LD_SINCE_FLOOR     = 1794355200;

/** Czech "kus" form for a count: 1 kus, 2-4 kusy, 5+ kusů (0 -> kusů). */
function molosoc_ld_piece_word( int $n ): string {
	if ( 1 === $n ) {
		return 'kus';
	}
	return ( $n >= 2 && $n <= 4 ) ? 'kusy' : 'kusů';
}

/** Orders sizes S<M<L..., unknown sizes after the known ones, alphabetically. */
/**
 * Maps a raw size attribute value (incl. live slugs such as `m-medium` /
 * `l-large`, Issue #220) to its canonical label; unknown values are only
 * uppercased so they still fail closed downstream.
 */
function molosoc_ld_normalize_size( string $raw ): string {
	$v = strtolower( trim( $raw ) );
	if ( '' === $v ) {
		return '';
	}
	$aliases = array(
		'm-medium' => 'M',
		'medium'   => 'M',
		'l-large'  => 'L',
		'large'    => 'L',
	);
	return $aliases[ $v ] ?? strtoupper( $v );
}

function molosoc_ld_sort_sizes( array $sizes ): array {
	uksort(
		$sizes,
		static function ( $a, $b ) {
			$ia = array_search( $a, MOLOSOC_LD_SIZE_ORDER, true );
			$ib = array_search( $b, MOLOSOC_LD_SIZE_ORDER, true );
			if ( false === $ia && false === $ib ) {
				return strcmp( (string) $a, (string) $b );
			}
			if ( false === $ia ) {
				return 1;
			}
			if ( false === $ib ) {
				return -1;
			}
			return $ia <=> $ib;
		}
	);
	return $sizes;
}

/**
 * Subject: "{PPL|Zásilkovna} | {n} kus/kusy/kusů | {qty}x {size}, ...".
 * $sizes maps size => quantity. Returns null if the input is unusable
 * (unknown carrier, no sizes, non-positive quantity), never a guess.
 */
function molosoc_ld_subject( string $carrier, array $sizes ): ?string {
	if ( ! in_array( $carrier, array( 'PPL', 'Zásilkovna' ), true ) || ! $sizes ) {
		return null;
	}
	$total = 0;
	$parts = array();
	foreach ( molosoc_ld_sort_sizes( $sizes ) as $size => $qty ) {
		$size = trim( (string) $size );
		if ( '' === $size || ! is_int( $qty ) || $qty < 1 ) {
			return null;
		}
		$total  += $qty;
		$parts[] = $qty . 'x ' . $size;
	}
	return sprintf( '%s | %d %s | %s', $carrier, $total, molosoc_ld_piece_word( $total ), implode( ', ', $parts ) );
}

/**
 * Carrier from the order's shipping method ids. Exactly one carrier must
 * match; none or both returns null (fail closed).
 */
function molosoc_ld_detect_carrier( array $method_ids ): ?string {
	$found = array();
	foreach ( $method_ids as $id ) {
		$id = (string) $id;
		if ( 0 === strpos( $id, 'pplcz_' ) ) {
			$found['PPL'] = true;
		} elseif ( 'packetery_shipping_method' === $id || 0 === strpos( $id, 'packeta_method_' ) ) {
			$found['Zásilkovna'] = true;
		}
	}
	return 1 === count( $found ) ? (string) key( $found ) : null;
}

/**
 * Authoritative Comgate "paid" decision from plain facts: status,
 * payment_method, transaction_id, tmp_transaction_id, is_paid (bool).
 * Fail closed on any missing/mismatching fact.
 */
function molosoc_ld_comgate_paid( array $f ): bool {
	if ( 'processing' !== ( $f['status'] ?? '' ) ) {
		return false;
	}
	if ( ! in_array( (string) ( $f['payment_method'] ?? '' ), MOLOSOC_LD_COMGATE_IDS, true ) ) {
		return false;
	}
	$tx = trim( (string) ( $f['transaction_id'] ?? '' ) );
	if ( '' === $tx ) {
		return false;
	}
	$tmp = trim( (string) ( $f['tmp_transaction_id'] ?? '' ) );
	// Default `paid_status` (Issue #369, verified on live Comgate 1.1.40 data): the plugin keeps
	// the transaction id equal to the temporary id after payment, so that equality says nothing.
	// Only an explicit `strict` rule still treats an equal id as an unpaid placeholder.
	// Everything else (processing, Comgate gateway, non-empty id, is_paid) always applies.
	if ( 'strict' === ( $f['tmp_rule'] ?? 'paid_status' ) && '' !== $tmp && hash_equals( $tmp, $tx ) ) {
		return false; // Placeholder id of an unpaid order (strict rule only).
	}
	return true === ( $f['is_paid'] ?? false );
}

/** Issue #369: Comgate rule from the wp-config value. Only exactly 'strict' opts back into the placeholder check. */
function molosoc_ld_comgate_tmp_rule( $configured ): string {
	return 'strict' === $configured ? 'strict' : 'paid_status';
}

/**
 * Issue #369: cut-off timestamp. A defined constant (`$const_defined`) wins over the option and
 * must be a positive int / digit string Unix timestamp or an ISO 8601 date-time with an explicit
 * offset (e.g. `2026-11-12T00:00:00+01:00`), not before MOLOSOC_LD_SINCE_FLOOR. Anything else
 * returns 0, which molosoc_ld_decide() treats as `before_cutoff_no_retroactive` (fail closed).
 * Without the constant, the `molosoc_label_dispatch_since` option value is used as before.
 */
function molosoc_ld_since_ts( bool $const_defined, $const, $option ): int {
	if ( ! $const_defined ) {
		return max( 0, (int) $option );
	}
	$ts = 0;
	if ( is_int( $const ) ) {
		$ts = $const;
	} elseif ( is_string( $const ) && 1 === preg_match( '/^\d{1,12}$/', $const ) ) {
		$ts = (int) $const;
	} elseif ( is_string( $const ) && 1 === preg_match( '/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$/', $const ) ) {
		$dt = DateTimeImmutable::createFromFormat( '!Y-m-d\TH:i:sP', $const );
		$err = DateTimeImmutable::getLastErrors(); // false on PHP >= 8.2 when clean.
		$ok  = $dt instanceof DateTimeImmutable && ( false === $err || 0 === $err['warning_count'] + $err['error_count'] );
		$ts = $ok ? $dt->getTimestamp() : 0;
	}
	return $ts >= MOLOSOC_LD_SINCE_FLOOR ? $ts : 0;
}

/**
 * Size of one order line: canonical size from item meta (pa_size, then older
 * pa_velikost) with the variation id as authoritative fallback. Returns ''
 * (fail closed) for unknown values or when meta and variation disagree.
 */
function molosoc_ld_item_size( array $meta_values, int $variation_id ): string {
	$from_meta = '';
	foreach ( MOLOSOC_LD_SIZE_META_KEYS as $key ) {
		$n = molosoc_ld_normalize_size( (string) ( $meta_values[ $key ] ?? '' ) );
		if ( '' !== $n ) {
			$from_meta = $n;
			break;
		}
	}
	$from_var = MOLOSOC_LD_VARIATION_SIZES[ $variation_id ] ?? '';
	if ( '' !== $from_meta ) {
		if ( ! in_array( $from_meta, MOLOSOC_LD_SIZE_ORDER, true ) ) {
			return '';
		}
		if ( '' !== $from_var && $from_var !== $from_meta ) {
			return '';
		}
		return $from_meta;
	}
	return $from_var;
}

/**
 * Pure eligibility decision from a plain snapshot:
 *   status, payment_method, comgate_confirmed (bool), carrier (?string),
 *   created_ts, since_ts (cut-off: orders created before it are skipped),
 *   done (already generated+mailed), sizes (size => qty).
 * Returns array( bool eligible, string reason ).
 */
function molosoc_ld_decide( array $o ): array {
	if ( 'processing' !== ( $o['status'] ?? '' ) ) {
		return array( false, 'status_not_processing' );
	}
	if ( empty( $o['since_ts'] ) || (int) ( $o['created_ts'] ?? 0 ) < (int) $o['since_ts'] ) {
		return array( false, 'before_cutoff_no_retroactive' );
	}
	$pm = (string) ( $o['payment_method'] ?? '' );
	if ( 'cod' === $pm ) {
		$paid_ok = true;
	} elseif ( in_array( $pm, MOLOSOC_LD_COMGATE_IDS, true ) ) {
		if ( empty( $o['comgate_confirmed'] ) ) {
			return array( false, 'comgate_unverified' );
		}
		$paid_ok = true;
	} else {
		return array( false, 'payment_method_excluded' ); // bacs, unknown, empty.
	}
	if ( ! $paid_ok ) {
		return array( false, 'payment_unverified' );
	}
	if ( empty( $o['carrier'] ) ) {
		return array( false, 'carrier_unknown' );
	}
	if ( null === molosoc_ld_subject( (string) $o['carrier'], (array) ( $o['sizes'] ?? array() ) ) ) {
		return array( false, 'sizes_unusable' );
	}
	if ( ! empty( $o['done'] ) ) {
		return array( false, 'already_processed' );
	}
	return array( true, 'eligible' );
}

/**
 * Stub carrier adapter. Phase 1: never calls the carrier. A future live
 * adapter must implement the same signature and is NOT part of this phase.
 */
function molosoc_ld_adapter_generate_label( string $carrier, int $order_id ): array {
	return array(
		'ok'      => true,
		'live'    => false,
		'carrier' => $carrier,
		'note'    => 'dry-run stub: no label generated',
	);
}

/**
 * Runs one order through the pipeline given injectable I/O:
 *   $io['snapshot']()           fresh order snapshot (re-read each call)
 *   $io['lock']() / unlock()    per-order lock; lock() false = already held
 *   $io['audit']($row)          append audit row
 *   $io['mark_done']()          persist idempotency marker
 *   $io['adapter']($carrier)    label adapter (stub in Phase 1)
 * Eligibility is checked, the lock taken, then eligibility RE-CHECKED from a
 * fresh snapshot before acting. Any exception releases the lock and is
 * audited; a failed run leaves no done-marker, so a retry is safe.
 * Nothing is mailed: the would-be mail is only described in the audit row.
 */
function molosoc_ld_process( int $order_id, array $io ): string {
	[ $ok, $reason ] = molosoc_ld_decide( $io['snapshot']() );
	if ( ! $ok ) {
		$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => $reason ) );
		return $reason;
	}
	if ( ! $io['lock']() ) {
		$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => 'locked' ) );
		return 'locked';
	}
	try {
		$snap = $io['snapshot']();
		[ $ok, $reason ] = molosoc_ld_decide( $snap );
		if ( ! $ok ) {
			$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => 'recheck_' . $reason ) );
			return 'recheck_' . $reason;
		}
		$res = $io['adapter']( (string) $snap['carrier'] );
		if ( ! empty( $res['live'] ) ) {
			// Phase 2: no live adapter may run through this pipeline.
			$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => 'live_adapter_refused' ) );
			return 'live_adapter_refused';
		}
		if ( empty( $res['ok'] ) ) {
			$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => 'adapter_failed' ) );
			return 'adapter_failed';
		}
		$io['audit'](
			array(
				'order'   => $order_id,
				'result'  => 'dry_run_would_send',
				'carrier' => $snap['carrier'],
				'subject' => molosoc_ld_subject( (string) $snap['carrier'], (array) $snap['sizes'] ),
				'to'      => MOLOSOC_LD_RECIPIENT,
				'live'    => false,
				'mock_ref' => isset( $res['mock_ref'] ) ? (string) $res['mock_ref'] : null,
			)
		);
		$io['mark_done']();
		return 'dry_run_would_send';
	} catch ( \Throwable $e ) {
		$io['audit']( array( 'order' => $order_id, 'result' => 'error', 'reason' => 'exception', 'class' => get_class( $e ) ) );
		return 'exception';
	} finally {
		$io['unlock']();
	}
}

/* ---------------------------------------------------------------- WP glue */

/** Builds the plain snapshot from a live WC_Order (re-read from the DB). */
function molosoc_ld_snapshot( int $order_id ): array {
	$order = wc_get_order( $order_id );
	if ( ! $order ) {
		return array( 'status' => 'missing' );
	}
	$methods = array();
	foreach ( $order->get_shipping_methods() as $item ) {
		$methods[] = $item->get_method_id();
	}
	$sizes = array();
	foreach ( $order->get_items() as $item ) {
		$meta = array();
		foreach ( MOLOSOC_LD_SIZE_META_KEYS as $key ) {
			$meta[ $key ] = (string) $item->get_meta( $key );
		}
		// Zero-price gift lines are physical pairs and count; quantities are summed.
		$size = molosoc_ld_item_size( $meta, (int) $item->get_variation_id() );
		if ( '' === $size ) {
			return array_merge( array( 'sizes' => array() ), molosoc_ld_base( $order, $methods ) ); // Unknown size: fail closed.
		}
		$sizes[ $size ] = ( $sizes[ $size ] ?? 0 ) + (int) $item->get_quantity();
	}
	$base          = molosoc_ld_base( $order, $methods );
	$base['sizes'] = $sizes;
	return $base;
}

/** Reads the Comgate paid facts from a live order. */
function molosoc_ld_comgate_from_order( $order ): bool {
	return molosoc_ld_comgate_paid(
		array(
			'status'             => (string) $order->get_status(),
			'payment_method'     => (string) $order->get_payment_method(),
			'transaction_id'     => (string) $order->get_transaction_id(),
			'tmp_transaction_id' => (string) $order->get_meta( 'wf_gateway_tmp_transaction_id' ),
			'is_paid'            => (bool) $order->is_paid(),
			'tmp_rule'           => molosoc_ld_comgate_tmp_rule( defined( 'MOLOSOC_LABEL_COMGATE_TMPID_RULE' ) ? MOLOSOC_LABEL_COMGATE_TMPID_RULE : null ),
		)
	);
}

function molosoc_ld_base( $order, array $methods ): array {
	$pm = (string) $order->get_payment_method();
	return array(
		'status'            => $order->get_status(),
		'payment_method'    => $pm,
		'comgate_confirmed' => in_array( $pm, MOLOSOC_LD_COMGATE_IDS, true )
			? (bool) apply_filters( 'molosoc_label_dispatch_comgate_confirmed', molosoc_ld_comgate_from_order( $order ), $order )
			: false,
		'carrier'           => molosoc_ld_detect_carrier( $methods ),
		'created_ts'        => $order->get_date_created() ? $order->get_date_created()->getTimestamp() : 0,
		'since_ts'          => molosoc_ld_since_ts(
			defined( 'MOLOSOC_LABEL_DISPATCH_SINCE' ),
			defined( 'MOLOSOC_LABEL_DISPATCH_SINCE' ) ? MOLOSOC_LABEL_DISPATCH_SINCE : null,
			defined( 'MOLOSOC_LABEL_DISPATCH_SINCE' ) ? 0 : get_option( 'molosoc_label_dispatch_since', 0 )
		),
		'done'              => (bool) $order->get_meta( MOLOSOC_LD_STATE_META ),
	);
}

function molosoc_ld_on_processing( $order_id ): void {
	$order_id = (int) $order_id;
	$lock_key = 'molosoc_ld_lock_' . $order_id;
	molosoc_ld_process(
		$order_id,
		array(
			'snapshot'  => static function () use ( $order_id ) {
				return molosoc_ld_snapshot( $order_id );
			},
			// add_option is a unique-key insert, so only one request wins.
			'lock'      => static function () use ( $lock_key ) {
				if ( add_option( $lock_key, time(), '', 'no' ) ) {
					return true;
				}
				global $wpdb;
				wp_cache_delete( $lock_key, 'options' );
				wp_cache_delete( 'notoptions', 'options' );
				wp_cache_delete( 'alloptions', 'options' );
				$observed = get_option( $lock_key, false );
				if ( false === $observed || time() - (int) $observed <= MOLOSOC_LD_LOCK_TTL ) {
					return false;
				}
				// Atomic compare-and-swap on the observed value: a contender that
				// lost the race matches 0 rows and can never remove a fresh lock.
				$swapped = $wpdb->update(
					$wpdb->options,
					array( 'option_value' => (string) time() ),
					array(
						'option_name'  => $lock_key,
						'option_value' => (string) $observed,
					)
				);
				wp_cache_delete( $lock_key, 'options' );
				wp_cache_delete( 'alloptions', 'options' );
				return 1 === (int) $swapped;
			},
			'unlock'    => static function () use ( $lock_key ) {
				delete_option( $lock_key );
			},
			'audit'     => static function ( array $row ) use ( $order_id ) {
				// Append-only: every audit row is its own meta row (an INSERT), never a
				// read-modify-write of a shared blob, so overlapping callbacks - including
				// ones that lost the lock - cannot overwrite each other's rows.
				$order = wc_get_order( $order_id );
				if ( $order ) {
					$order->add_meta_data( MOLOSOC_LD_AUDIT_META, wp_json_encode( array_merge( array( 'ts' => gmdate( 'c' ) ), $row ) ), false );
					$order->save_meta_data();
				}
			},
			'mark_done' => static function () use ( $order_id ) {
				$order = wc_get_order( $order_id );
				if ( $order ) {
					$order->update_meta_data( MOLOSOC_LD_STATE_META, 'dry_run_done' );
					$order->save_meta_data();
				}
			},
			'adapter'   => static function ( $carrier ) use ( $order_id ) {
				$custom = apply_filters( 'molosoc_label_dispatch_adapter', null, $carrier, $order_id );
				return is_array( $custom ) ? $custom : molosoc_ld_adapter_generate_label( $carrier, $order_id );
			},
		)
	);
}

// Registered only when explicitly switched on; there is no live mode.
if ( defined( 'MOLOSOC_LABEL_DISPATCH_DRY_RUN' ) && true === MOLOSOC_LABEL_DISPATCH_DRY_RUN ) {
	add_action( 'woocommerce_order_status_processing', 'molosoc_ld_on_processing', 20, 1 );
}
