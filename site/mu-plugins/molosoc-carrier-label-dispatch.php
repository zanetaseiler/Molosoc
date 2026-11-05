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
 * COMGATE CONFIRMATION FAILS CLOSED
 *
 *   The gateway id is wf_woo_comgate, but that plugin's source could not be
 *   retrieved, so how it records a confirmed payment is unverified. Card
 *   orders are eligible only if the `molosoc_label_dispatch_comgate_confirmed`
 *   filter returns true. By default it returns false: a card order is
 *   recorded as "not eligible: comgate_unverified". Žaneta must name the
 *   real signal (order meta key / transaction id behaviour) before it is
 *   wired in.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const MOLOSOC_LD_RECIPIENT      = 'jarka01@atlas.cz';
const MOLOSOC_LD_AUDIT_META     = '_molosoc_label_dispatch_audit';
const MOLOSOC_LD_STATE_META     = '_molosoc_label_dispatch_state';
const MOLOSOC_LD_LOCK_TTL       = 300;
const MOLOSOC_LD_SIZE_ORDER     = array( 'XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL' );
const MOLOSOC_LD_SIZE_META_KEYS = array( 'pa_size', 'size', 'pa_velikost', 'velikost' );

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
	} elseif ( 'wf_woo_comgate' === $pm ) {
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
		$size = '';
		foreach ( MOLOSOC_LD_SIZE_META_KEYS as $key ) {
			$size = strtoupper( trim( (string) $item->get_meta( $key ) ) );
			if ( '' !== $size ) {
				break;
			}
		}
		if ( '' === $size ) {
			return array_merge( array( 'sizes' => array() ), molosoc_ld_base( $order, $methods ) ); // Unknown size: fail closed.
		}
		$sizes[ $size ] = ( $sizes[ $size ] ?? 0 ) + (int) $item->get_quantity();
	}
	$base          = molosoc_ld_base( $order, $methods );
	$base['sizes'] = $sizes;
	return $base;
}

function molosoc_ld_base( $order, array $methods ): array {
	$pm = (string) $order->get_payment_method();
	return array(
		'status'            => $order->get_status(),
		'payment_method'    => $pm,
		'comgate_confirmed' => 'wf_woo_comgate' === $pm
			? (bool) apply_filters( 'molosoc_label_dispatch_comgate_confirmed', false, $order )
			: false,
		'carrier'           => molosoc_ld_detect_carrier( $methods ),
		'created_ts'        => $order->get_date_created() ? $order->get_date_created()->getTimestamp() : 0,
		'since_ts'          => (int) get_option( 'molosoc_label_dispatch_since', 0 ),
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
				$order = wc_get_order( $order_id );
				if ( $order ) {
					$log   = (array) json_decode( (string) $order->get_meta( MOLOSOC_LD_AUDIT_META ), true );
					$log[] = array_merge( array( 'ts' => gmdate( 'c' ) ), $row );
					$order->update_meta_data( MOLOSOC_LD_AUDIT_META, wp_json_encode( array_slice( $log, -20 ) ) );
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
				return molosoc_ld_adapter_generate_label( $carrier, $order_id );
			},
		)
	);
}

// Registered only when explicitly switched on; there is no live mode.
if ( defined( 'MOLOSOC_LABEL_DISPATCH_DRY_RUN' ) && true === MOLOSOC_LABEL_DISPATCH_DRY_RUN ) {
	add_action( 'woocommerce_order_status_processing', 'molosoc_ld_on_processing', 20, 1 );
}
