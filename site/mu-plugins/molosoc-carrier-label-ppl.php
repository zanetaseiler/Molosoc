<?php
/**
 * Plugin Name: MOLOSOC Carrier Label Automation – PPL (OFF by default)
 * Description: PPL path for the hands-off label pipeline (#369): creates exactly ONE PPL shipment per eligible order through the PPL CZ 1.1.3 plugin's own models and batch, fetches its label PDF without the plugin's exit(), and hands it to the shared fixed-recipient mailer. Issue #391.
 * Version: 0.1.0
 *
 * SAFETY CONTRACT
 *
 *   - Inert unless wp-config.php defines MOLOSOC_LABEL_AUTO_PPL_ENABLED === true AND the
 *     #369 automation itself is enabled (MOLOSOC_LABEL_AUTO_ENABLED + cut-off). The
 *     automation file (molosoc-carrier-label-auto.php) owns the queue, gate, cut-off,
 *     eligibility (processing + COD or Comgate-confirmed card), lock, audit, alerts and
 *     the at-most-once mail state machine. This file only adds the PPL steps.
 *   - Exactly one shipment per order. The idempotency key is the order itself: the order
 *     meta MOLOSOC_LP_STATE_META is written as `creating` BEFORE anything is saved in the
 *     PPL plugin or sent to PPL. Any later run that finds `creating` goes to `attention`
 *     (one alert) and never creates again, whatever happened in between (crash, timeout,
 *     exception, PPL error). A create is never retried automatically.
 *   - A shipment that already exists in the PPL plugin for the order (manual click,
 *     batch screen) is ADOPTED, never duplicated: a remote one (sent to PPL) is used for
 *     the label; a local draft (not sent) means someone is working on it by hand, so the
 *     order goes to `attention`. More than one remote shipment → `attention`.
 *   - Shipment data comes from the PPL plugin's own order → ShipmentModel conversion and
 *     its own validator (the same code the admin uses). Nothing is invented. On top of
 *     that, molosoc_lp_check() refuses (`attention`) anything unusual: not CZ, missing
 *     pickup point for SMAR/SBOX, COD amount/currency/variable symbol not matching the
 *     order, unexpected sender address, unknown method, more than one package.
 *   - The shipment is created through the plugin's own batch (BatchData + ShipmentData +
 *     CPLOperation::createPackages), so it shows in the order's PPL box and the plugin's
 *     tables, tracking (ShipmentPhaseCron) and status sync keep working.
 *   - The label is fetched from the same CPL endpoint the plugin uses
 *     (/shipment/batch/{id}/label) with the plugin's own OAuth token, as a return value
 *     instead of the plugin's header()+exit(). Only for a batch that contains this one
 *     shipment; a shared manual batch → `attention` (its labels were printed by hand).
 *   - Live-test limit: with MOLOSOC_LABEL_AUTO_PPL_LIMIT = N (1..20) only the first N
 *     eligible PPL orders (atomic option slots) take this path; every later PPL order stays
 *     manual (`ppl_manual_label_required`, one alert) exactly as before. Used for the
 *     single-order live test (N = 1). An invalid value turns the PPL path off.
 *   - Credentials: only the PPL plugin's stored settings, via its own token helper. No
 *     secret in code, meta, audit or logs. Audit rows carry ids, states and reason codes
 *     only (no customer data).
 *
 * See docs/carrier-label-ppl-391.md.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const MOLOSOC_LP_STATE_META    = '_molosoc_label_ppl_state';    // '' | creating | created | adopted
const MOLOSOC_LP_SHIPMENT_META = '_molosoc_label_ppl_shipment'; // PPL plugin's local ppl_shipment_id
const MOLOSOC_LP_SENDER_ID     = 3;                             // PPL plugin sender address (Issue #391).
const MOLOSOC_LP_PRINT         = '4/PDF';                       // A4, 4 labels per page, first position.
const MOLOSOC_LP_METHODS       = array( 'pplcz_SMAR', 'pplcz_SBOX', 'pplcz_PRIV' );
const MOLOSOC_LP_PARCEL_METHODS = array( 'pplcz_SMAR', 'pplcz_SBOX' );
const MOLOSOC_LP_REMOTE_STATES = array( 'InProgress', 'InProcess', 'Accepted', 'Complete', 'Error' );
const MOLOSOC_LP_PENDING_STATES = array( 'InProgress', 'InProcess', 'Accepted' );
const MOLOSOC_LP_LABEL_TIMEOUT = 30;
const MOLOSOC_LP_SLOT_OPTION   = 'molosoc_lp_slot_';            // + 1..N: order id that took the slot.
const MOLOSOC_LP_LIMIT_MAX     = 20;

/** Pure gate: the PPL path is on only with the constant exactly true. */
function molosoc_lp_gate( $enabled ): bool {
	return true === $enabled;
}

/** Pure: the optional live-test limit is either not defined or an int 1..MOLOSOC_LP_LIMIT_MAX. */
function molosoc_lp_limit_ok( bool $defined, $limit ): bool {
	return ! $defined || ( is_int( $limit ) && $limit >= 1 && $limit <= MOLOSOC_LP_LIMIT_MAX );
}

/**
 * Pure slot claim for the live-test limit. `$get($i)` returns the order id stored in slot
 * `$i` (0 = free), `$add($i, $order_id)` claims a free slot atomically (add_option: one
 * winner). True when this order holds or just won a slot.
 */
function molosoc_lp_claim( int $limit, int $order_id, callable $get, callable $add ): bool {
	for ( $i = 1; $i <= $limit; $i++ ) {
		$v = (int) $get( $i );
		if ( $v === $order_id ) {
			return true;
		}
		if ( $v <= 0 && $add( $i, $order_id ) ) {
			return true;
		}
	}
	return false;
}

/**
 * Pure: the shipment was sent to PPL (has a remote batch, or an import state set by the
 * plugin after createPackages). `None`/''/no batch is a local draft only.
 */
function molosoc_lp_is_remote( array $s ): bool {
	return '' !== trim( (string) ( $s['batch_id'] ?? '' ) )
		|| in_array( (string) ( $s['import_state'] ?? '' ), MOLOSOC_LP_REMOTE_STATES, true );
}

/**
 * Pure refusal check on facts taken from the PPL plugin's own ShipmentModel for the order.
 * Returns '' when the shipment may be created, otherwise a reason code (`attention`).
 * Facts: method_ids (all shipping method ids on the order), errors (validator error
 * count), service_code, has_parcel, parcel_code, country, sender_id, payment_cod,
 * order_total, currency, cod_value, cod_currency, cod_vs, packages.
 */
function molosoc_lp_check( array $f ): string {
	$ppl = array_values(
		array_filter(
			array_map( 'strval', (array) ( $f['method_ids'] ?? array() ) ),
			static function ( $m ) {
				return 0 === strpos( $m, 'pplcz_' );
			}
		)
	);
	if ( 1 !== count( $ppl ) ) {
		return 'ppl_method_ambiguous';
	}
	$method = $ppl[0];
	if ( ! in_array( $method, MOLOSOC_LP_METHODS, true ) ) {
		return 'ppl_method_unknown';
	}
	if ( (int) ( $f['errors'] ?? 1 ) > 0 ) {
		return 'ppl_validation_failed';
	}
	if ( '' === trim( (string) ( $f['service_code'] ?? '' ) ) ) {
		return 'ppl_service_missing';
	}
	if ( 'CZ' !== (string) ( $f['country'] ?? '' ) ) {
		return 'ppl_not_cz';
	}
	if ( 'CZK' !== (string) ( $f['currency'] ?? '' ) ) {
		return 'ppl_currency_unexpected';
	}
	$has_parcel = ! empty( $f['has_parcel'] ) && '' !== trim( (string) ( $f['parcel_code'] ?? '' ) );
	if ( in_array( $method, MOLOSOC_LP_PARCEL_METHODS, true ) && ! $has_parcel ) {
		return 'ppl_parcel_missing';
	}
	if ( ! in_array( $method, MOLOSOC_LP_PARCEL_METHODS, true ) && ! empty( $f['has_parcel'] ) ) {
		return 'ppl_parcel_unexpected';
	}
	if ( MOLOSOC_LP_SENDER_ID !== (int) ( $f['sender_id'] ?? 0 ) ) {
		return 'ppl_sender_mismatch';
	}
	$cod = $f['cod_value'] ?? null;
	if ( ! empty( $f['payment_cod'] ) ) {
		if ( ! is_numeric( $cod ) || (float) $cod <= 0 || abs( (float) $cod - (float) ( $f['order_total'] ?? 0 ) ) > 0.005 ) {
			return 'ppl_cod_mismatch';
		}
		if ( (string) ( $f['cod_currency'] ?? '' ) !== (string) $f['currency'] ) {
			return 'ppl_cod_mismatch';
		}
		if ( 1 !== preg_match( '/^\d{1,10}$/', (string) ( $f['cod_vs'] ?? '' ) ) ) {
			return 'ppl_cod_vs_invalid';
		}
	} elseif ( is_numeric( $cod ) && (float) $cod > 0 ) {
		return 'ppl_cod_unexpected';
	}
	if ( 1 !== (int) ( $f['packages'] ?? 0 ) ) {
		return 'ppl_packages_unexpected';
	}
	return '';
}

/**
 * Pure classification of one shipment as the plugin stores it (normalized array:
 * import_state, import_errors, packages => [ [shipment_number, phase], ... ]).
 * Returns array( 'ready', shipment_number ) | array( 'wait', reason ) | array( 'attention', reason ).
 */
function molosoc_lp_classify( array $s ): array {
	$packages = array_values( (array) ( $s['packages'] ?? array() ) );
	foreach ( $packages as $p ) {
		if ( 'Canceled' === (string) ( $p['phase'] ?? '' ) ) {
			return array( 'attention', 'ppl_shipment_cancelled' );
		}
	}
	$state = (string) ( $s['import_state'] ?? '' );
	if ( 'Complete' === $state ) {
		$num = trim( (string) ( $packages[0]['shipment_number'] ?? '' ) );
		if ( 1 !== preg_match( '/^[0-9A-Za-z]{5,30}$/', $num ) ) {
			return array( 'attention', 'ppl_shipment_number_missing' );
		}
		return array( 'ready', $num );
	}
	if ( 'Error' === $state || '' !== trim( (string) ( $s['import_errors'] ?? '' ) ) ) {
		return array( 'attention', 'ppl_import_error' );
	}
	if ( in_array( $state, MOLOSOC_LP_PENDING_STATES, true ) ) {
		return array( 'wait', 'ppl_import_pending' );
	}
	if ( '' === $state || 'None' === $state ) {
		return array( 'attention', 'ppl_create_failed' ); // The plugin resets a rejected create to None.
	}
	return array( 'attention', 'ppl_import_state_unknown' );
}

/** Pure: find a shipment by the plugin's local id in a normalized list. */
function molosoc_lp_find( array $list, $id ): ?array {
	foreach ( $list as $s ) {
		if ( (int) ( $s['id'] ?? 0 ) > 0 && (int) $s['id'] === (int) $id ) {
			return $s;
		}
	}
	return null;
}

/**
 * Settles one known shipment: refresh it from PPL while the import is still pending
 * (the plugin's own loadingShipmentNumbers), then classify.
 */
function molosoc_lp_settle( array $s, array $io ): array {
	[ $st ] = molosoc_lp_classify( $s );
	$batch  = trim( (string) ( $s['batch_id'] ?? '' ) );
	if ( 'wait' === $st && '' !== $batch ) {
		$io['refresh']( $batch );
		$fresh = molosoc_lp_find( (array) $io['shipments'](), $s['id'] ?? 0 );
		if ( null === $fresh ) {
			return array( 'attention', 'ppl_shipment_missing' );
		}
		$s = $fresh;
	}
	return molosoc_lp_classify( $s );
}

/**
 * The PPL step for one order. Runs under the automation's per-order worker lock.
 * Returns array( 'ready', shipment_number ) | array( 'wait', reason ) | array( 'attention', reason ).
 * Injected I/O:
 *   state() / set_state($s)              MOLOSOC_LP_STATE_META
 *   shipment_id() / set_shipment_id($id) MOLOSOC_LP_SHIPMENT_META
 *   shipments()                          normalized shipments the PPL plugin has for the order
 *   refresh($remote_batch)               plugin's loadingShipmentNumbers for that batch
 *   facts()                              facts for molosoc_lp_check() from the plugin's model
 *   api_ready()                          the plugin can obtain its CPL token
 *   stage()                              plugin draft + batch: array( ok, shipment_id, batch_local_id, reason )
 *   submit($batch_local_id)              plugin createPackages: array( ok, reason )
 *   claim()                              live-test limit slot (true when no limit is set)
 *   audit($row)
 */
function molosoc_lp_prepare( int $order_id, array $io ): array {
	$state = (string) $io['state']();
	if ( 'creating' === $state ) {
		return array( 'attention', 'ppl_create_state_unknown' ); // Never a second create.
	}
	$list   = array_values( (array) $io['shipments']() );
	$remote = array_values( array_filter( $list, 'molosoc_lp_is_remote' ) );

	if ( 'created' === $state || 'adopted' === $state ) {
		$own = molosoc_lp_find( $list, $io['shipment_id']() );
		if ( null === $own ) {
			return array( 'attention', 'ppl_shipment_missing' );
		}
		if ( count( $remote ) > 1 || ( 1 === count( $remote ) && (int) $remote[0]['id'] !== (int) $own['id'] ) ) {
			return array( 'attention', 'ppl_multiple_shipments' );
		}
		return molosoc_lp_settle( $own, $io );
	}
	if ( '' !== $state ) {
		return array( 'attention', 'ppl_state_unknown' );
	}
	if ( ! $io['claim']() ) {
		return array( 'attention', 'ppl_manual_label_required' ); // Live-test limit reached: manual as before.
	}

	if ( count( $remote ) > 1 ) {
		return array( 'attention', 'ppl_multiple_shipments' );
	}
	if ( 1 === count( $remote ) ) {
		// Created by hand (or by the plugin's batch screen): use it, never create another.
		$io['set_shipment_id']( (int) $remote[0]['id'] );
		$io['set_state']( 'adopted' );
		$io['audit']( array( 'order' => $order_id, 'result' => 'ppl_adopted', 'shipment' => (int) $remote[0]['id'] ) );
		return molosoc_lp_settle( $remote[0], $io );
	}
	if ( $list ) {
		return array( 'attention', 'ppl_manual_draft_exists' );
	}

	$why = molosoc_lp_check( (array) $io['facts']() );
	if ( '' !== $why ) {
		return array( 'attention', $why );
	}
	if ( ! $io['api_ready']() ) {
		return array( 'wait', 'ppl_api_unavailable' ); // Nothing written yet: safe to retry.
	}

	// Point of no return: from here on, this order never gets another create.
	$io['set_state']( 'creating' );
	$io['audit']( array( 'order' => $order_id, 'result' => 'ppl_creating' ) );
	try {
		$staged = (array) $io['stage']();
		if ( empty( $staged['ok'] ) || (int) ( $staged['shipment_id'] ?? 0 ) <= 0 || (int) ( $staged['batch_local_id'] ?? 0 ) <= 0 ) {
			$io['audit']( array( 'order' => $order_id, 'result' => 'ppl_create_failed', 'detail' => (string) ( $staged['reason'] ?? 'stage' ) ) );
			return array( 'attention', 'ppl_create_failed' );
		}
		$io['set_shipment_id']( (int) $staged['shipment_id'] );
		$sent = (array) $io['submit']( (int) $staged['batch_local_id'] );
		if ( empty( $sent['ok'] ) ) {
			$io['audit']( array( 'order' => $order_id, 'result' => 'ppl_create_failed', 'shipment' => (int) $staged['shipment_id'], 'detail' => (string) ( $sent['reason'] ?? 'submit' ) ) );
			return array( 'attention', 'ppl_create_failed' );
		}
	} catch ( \Throwable $e ) {
		$io['audit']( array( 'order' => $order_id, 'result' => 'ppl_create_failed', 'class' => get_class( $e ) ) );
		return array( 'attention', 'ppl_create_failed' ); // State stays `creating`: never retried.
	}
	$io['set_state']( 'created' );
	$io['audit']( array( 'order' => $order_id, 'result' => 'ppl_created', 'shipment' => (int) $staged['shipment_id'] ) );
	return array( 'wait', 'ppl_import_pending' );
}

/**
 * Pure: offset/limit of the label pages, only for a remote batch that holds exactly this
 * one shipment (the batch this automation creates). Returns null for a shared batch.
 * `$batch_shipments` are the plugin's shipments with that remote batch id.
 */
function molosoc_lp_label_window( array $own, array $batch_shipments ): ?array {
	if ( 1 !== count( $batch_shipments ) || (int) ( $batch_shipments[0]['id'] ?? 0 ) !== (int) ( $own['id'] ?? -1 ) ) {
		return null;
	}
	$n = count( (array) ( $own['packages'] ?? array() ) );
	return $n > 0 ? array( 0, $n ) : null;
}

/** Pure: CPL remote batch ids are UUIDs. */
function molosoc_lp_batch_id_valid( $id ): bool {
	return is_string( $id ) && 1 === preg_match( '/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/', $id );
}

/** Pure: the label URL, same endpoint and parameters as the plugin (A4, first position). */
function molosoc_lp_label_url( string $base, string $batch, int $offset, int $limit ): string {
	return rtrim( $base, '/' ) . '/shipment/batch/' . rawurlencode( $batch ) . '/label?' . http_build_query(
		array(
			'limit'    => $limit,
			'offset'   => $offset,
			'pageSize' => 'A4',
			'position' => 1,
			'orderBy'  => 'ReferenceId',
		),
		'',
		'&',
		PHP_QUERY_RFC3986
	);
}

/**
 * Provider for the shared state machine (molosoc_ld3_process). FETCH ONLY: it never
 * creates. `$d`: state, own (normalized shipment or null), batch_shipments,
 * fetch(batch, offset, limit) → bytes|false. The ref is the PPL shipment number, so the
 * state machine's `ref_changed` check stops a different shipment from ever being mailed.
 */
function molosoc_lp_provider( string $carrier, string $stored_ref, array $d ): array {
	if ( 'PPL' !== $carrier ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => 'unknown_carrier' );
	}
	if ( ! in_array( (string) ( $d['state'] ?? '' ), array( 'created', 'adopted' ), true ) || ! is_array( $d['own'] ?? null ) ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => 'ppl_shipment_not_ready' );
	}
	[ $st, $val ] = molosoc_lp_classify( $d['own'] );
	if ( 'wait' === $st ) {
		return array( 'ok' => false, 'live' => true, 'reason' => $val );
	}
	if ( 'ready' !== $st ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => $val );
	}
	$batch = trim( (string) ( $d['own']['batch_id'] ?? '' ) );
	if ( ! molosoc_lp_batch_id_valid( $batch ) ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => 'ppl_batch_id_invalid' );
	}
	$win = molosoc_lp_label_window( $d['own'], (array) ( $d['batch_shipments'] ?? array() ) );
	if ( null === $win ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => 'ppl_shared_batch_manual' );
	}
	$pdf = $d['fetch']( $batch, $win[0], $win[1] );
	if ( ! is_string( $pdf ) || '' === $pdf ) {
		return array( 'ok' => false, 'live' => true, 'reason' => 'ppl_label_fetch_failed' );
	}
	return array( 'ok' => true, 'live' => true, 'ref' => $val, 'pdf' => $pdf );
}

/* ---------------------------------------------------------------- WP glue */

/** True when the PPL path may run: constant on and the PPL CZ plugin classes are loaded. */
function molosoc_lp_enabled_now(): bool {
	return molosoc_lp_gate( defined( 'MOLOSOC_LABEL_AUTO_PPL_ENABLED' ) ? MOLOSOC_LABEL_AUTO_PPL_ENABLED : null )
		&& molosoc_lp_plugin_available();
}

function molosoc_lp_plugin_available(): bool {
	return molosoc_lp_limit_ok( defined( 'MOLOSOC_LABEL_AUTO_PPL_LIMIT' ), defined( 'MOLOSOC_LABEL_AUTO_PPL_LIMIT' ) ? MOLOSOC_LABEL_AUTO_PPL_LIMIT : null )
		&& class_exists( '\PPLCZ\Admin\CPLOperation' ) && class_exists( '\PPLCZ\Data\ShipmentData' )
		&& class_exists( '\PPLCZ\Data\BatchData' ) && class_exists( '\PPLCZ\Data\PackageData' )
		&& class_exists( '\PPLCZ\Model\Model\ShipmentModel' ) && class_exists( '\PPLCZ\Admin\Errors' )
		&& function_exists( 'pplcz_denormalize' ) && function_exists( 'pplcz_validate' );
}

/** The plugin's ShipmentData as a plain array (ids, states, package numbers; no customer data). */
function molosoc_lp_normalize( $data ): array {
	$packages = array();
	foreach ( (array) $data->get_package_ids() as $pid ) {
		$p          = new \PPLCZ\Data\PackageData( (int) $pid );
		$packages[] = array(
			'shipment_number' => (string) $p->get_shipment_number(),
			'phase'           => (string) $p->get_phase(),
		);
	}
	return array(
		'id'             => (int) $data->get_id(),
		'batch_id'       => (string) $data->get_batch_id(),
		'batch_local_id' => (int) $data->get_batch_local_id(),
		'import_state'   => (string) $data->get_import_state(),
		'import_errors'  => (string) $data->get_import_errors(),
		'packages'       => $packages,
	);
}

function molosoc_lp_shipments_now( int $order_id ): array {
	return array_map( 'molosoc_lp_normalize', (array) \PPLCZ\Data\ShipmentData::find_shipments_by_wc_order( $order_id ) );
}

/** Builds the plugin's own ShipmentModel for the order and validates it with the plugin's validator. */
function molosoc_lp_model_now( int $order_id ): array {
	$order  = new \WC_Order( $order_id );
	$model  = pplcz_denormalize( $order, \PPLCZ\Model\Model\ShipmentModel::class );
	$errors = pplcz_validate( $model, new \PPLCZ\Admin\Errors(), '' );
	return array( $order, $model, $errors );
}

/** Facts for molosoc_lp_check(): codes and amounts only. */
function molosoc_lp_facts( $order, $model, $errors ): array {
	$methods = array();
	foreach ( (array) $order->get_shipping_methods() as $m ) {
		$methods[] = (string) $m->get_method_id();
	}
	$parcel    = $model->getHasParcel() ? $model->getParcel() : null;
	$recipient = $model->getRecipient();
	$sender    = $model->getSender();
	return array(
		'method_ids'   => $methods,
		'errors'       => is_object( $errors ) && method_exists( $errors, 'has_errors' ) && $errors->has_errors() ? count( $errors->get_error_codes() ) : 0,
		'service_code' => (string) $model->getServiceCode(),
		'has_parcel'   => (bool) $model->getHasParcel(),
		'parcel_code'  => $parcel ? (string) $parcel->getCode() : '',
		'country'      => $recipient ? (string) $recipient->getCountry() : '',
		'sender_id'    => $sender ? (int) $sender->getId() : 0,
		'payment_cod'  => 'cod' === (string) $order->get_payment_method(),
		'order_total'  => (float) $order->get_total( 'edit' ),
		'currency'     => (string) $order->get_currency(),
		'cod_value'    => $model->getCodValue(),
		'cod_currency' => (string) $model->getCodValueCurrency(),
		'cod_vs'       => (string) $model->getCodVariableNumber(),
		'packages'     => count( (array) $model->getPackages() ),
	);
}

/**
 * Plugin draft + one-shipment batch, exactly like the batch screen's "add order" step.
 * Re-checks the facts on the very model that is saved.
 */
function molosoc_lp_stage_now( int $order_id ): array {
	[ $order, $model, $errors ] = molosoc_lp_model_now( $order_id );
	$why = molosoc_lp_check( molosoc_lp_facts( $order, $model, $errors ) );
	if ( '' !== $why ) {
		return array( 'ok' => false, 'reason' => $why );
	}
	if ( \PPLCZ\Data\ShipmentData::find_shipments_by_wc_order( $order_id ) ) {
		return array( 'ok' => false, 'reason' => 'ppl_manual_draft_exists' ); // Appeared meanwhile.
	}
	$data  = pplcz_denormalize( $model, \PPLCZ\Data\ShipmentData::class );
	$batch = new \PPLCZ\Data\BatchData();
	$batch->save();
	$data->set_batch_local_id( $batch->get_id() );
	$data->save();
	\PPLCZ\Data\ShipmentData::reorder_batch_shipments( $batch->get_id(), array( $data->get_id() ) );
	return array( 'ok' => true, 'shipment_id' => (int) $data->get_id(), 'batch_local_id' => (int) $batch->get_id() );
}

/** The plugin's own create call (the batch screen's "Vytisknout zásilky"). */
function molosoc_lp_submit_now( int $batch_local_id ): array {
	( new \PPLCZ\Admin\CPLOperation() )->createPackages( $batch_local_id, MOLOSOC_LP_PRINT );
	return array( 'ok' => true );
}

/** Same label endpoint as CPLOperation::getLabelContents(), returned instead of exit(). */
function molosoc_lp_fetch_now( string $batch, int $offset, int $limit ) {
	$cpl   = new \PPLCZ\Admin\CPLOperation();
	$token = $cpl->getAccessToken( MOLOSOC_LP_LABEL_TIMEOUT );
	if ( ! is_string( $token ) || '' === $token ) {
		return false;
	}
	$res = wp_remote_get(
		molosoc_lp_label_url( \PPLCZ\Admin\CPLOperation::BASE_URL, $batch, $offset, $limit ),
		array(
			'timeout' => MOLOSOC_LP_LABEL_TIMEOUT,
			'headers' => array( 'Authorization' => 'Bearer ' . $token ),
		)
	);
	if ( is_wp_error( $res ) || 200 !== (int) wp_remote_retrieve_response_code( $res ) ) {
		return false;
	}
	$body = wp_remote_retrieve_body( $res );
	return is_string( $body ) && '' !== $body ? $body : false;
}

/** Live I/O for molosoc_lp_prepare(). `$audit` is the automation's audit writer. */
function molosoc_lp_io( int $order_id, callable $audit ): array {
	return array(
		'state'           => static function () use ( $order_id ) {
			return molosoc_ld3_meta_get( $order_id, MOLOSOC_LP_STATE_META );
		},
		'set_state'       => static function ( $s ) use ( $order_id ) {
			molosoc_ld3_meta_set( $order_id, MOLOSOC_LP_STATE_META, (string) $s );
		},
		'shipment_id'     => static function () use ( $order_id ) {
			return (int) molosoc_ld3_meta_get( $order_id, MOLOSOC_LP_SHIPMENT_META );
		},
		'set_shipment_id' => static function ( $id ) use ( $order_id ) {
			molosoc_ld3_meta_set( $order_id, MOLOSOC_LP_SHIPMENT_META, (string) (int) $id );
		},
		'shipments'       => static function () use ( $order_id ) {
			return molosoc_lp_shipments_now( $order_id );
		},
		'refresh'         => static function ( $batch ) {
			if ( molosoc_lp_batch_id_valid( $batch ) ) {
				( new \PPLCZ\Admin\CPLOperation() )->loadingShipmentNumbers( array( $batch ) );
			}
		},
		'facts'           => static function () use ( $order_id ) {
			[ $order, $model, $errors ] = molosoc_lp_model_now( $order_id );
			return molosoc_lp_facts( $order, $model, $errors );
		},
		'api_ready'       => static function () {
			$t = ( new \PPLCZ\Admin\CPLOperation() )->getAccessToken( MOLOSOC_LP_LABEL_TIMEOUT );
			return is_string( $t ) && '' !== $t;
		},
		'stage'           => static function () use ( $order_id ) {
			return molosoc_lp_stage_now( $order_id );
		},
		'submit'          => 'molosoc_lp_submit_now',
		'claim'           => static function () use ( $order_id ) {
			if ( ! defined( 'MOLOSOC_LABEL_AUTO_PPL_LIMIT' ) ) {
				return true;
			}
			return molosoc_lp_claim(
				(int) MOLOSOC_LABEL_AUTO_PPL_LIMIT,
				$order_id,
				static function ( $i ) {
					wp_cache_delete( MOLOSOC_LP_SLOT_OPTION . $i, 'options' );
					wp_cache_delete( 'notoptions', 'options' );
					return (int) get_option( MOLOSOC_LP_SLOT_OPTION . $i, 0 );
				},
				static function ( $i, $id ) {
					return (bool) add_option( MOLOSOC_LP_SLOT_OPTION . $i, (string) (int) $id, '', 'no' );
				}
			);
		},
		'audit'           => $audit,
	);
}

/** Entry point used by the automation worker for a PPL order. */
function molosoc_lp_prepare_now( int $order_id, callable $audit ): array {
	return molosoc_lp_prepare( $order_id, molosoc_lp_io( $order_id, $audit ) );
}

/** Fetch-only provider for the automation's state machine (never creates). */
function molosoc_lp_provider_now( int $order_id, string $carrier, string $ref ): array {
	$own   = molosoc_lp_find( molosoc_lp_shipments_now( $order_id ), (int) molosoc_ld3_meta_get( $order_id, MOLOSOC_LP_SHIPMENT_META ) );
	$batch = is_array( $own ) ? trim( (string) $own['batch_id'] ) : '';
	return molosoc_lp_provider(
		$carrier,
		$ref,
		array(
			'state'           => molosoc_ld3_meta_get( $order_id, MOLOSOC_LP_STATE_META ),
			'own'             => $own,
			'batch_shipments' => molosoc_lp_batch_id_valid( $batch )
				? array_map( 'molosoc_lp_normalize', (array) \PPLCZ\Data\ShipmentData::read_remote_batch_shipments( $batch ) )
				: array(),
			'fetch'           => 'molosoc_lp_fetch_now',
		)
	);
}
