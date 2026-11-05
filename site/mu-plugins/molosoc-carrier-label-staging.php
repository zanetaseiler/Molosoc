<?php
/**
 * Plugin Name: MOLOSOC Carrier Label Staging Harness (Phase 2, mocks only)
 * Description: Staging-only mock carrier adapters for the Phase 1 label-dispatch pipeline. Never calls PPL, Packeta or Comgate, never creates a real label, never sends mail. Issue #352.
 * Version: 0.1.0
 *
 * SAFETY CONTRACT
 *
 *   - Inert unless BOTH hold: wp_get_environment_type() is `staging` or
 *     `local` AND wp-config.php defines MOLOSOC_LABEL_DISPATCH_STAGING as
 *     true. Production (`production`, the WP default) can never activate it.
 *   - The Phase 1 plugin must also be switched on (MOLOSOC_LABEL_DISPATCH_DRY_RUN).
 *   - The adapters here return {live:false, mock_ref:"MOCK-..."}; the Phase 1
 *     pipeline refuses any adapter result with live=true.
 *   - No network, no carrier class, no mail function is referenced in this file.
 *
 * The mock contracts mirror the real paths found in the upstream sources
 * (see docs/carrier-label-staging-352.md): PPL needs a created shipment batch
 * before a PDF exists; Packeta needs a packet submitted to its API first.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** True only on a non-production environment type with the explicit constant. */
function molosoc_ls_enabled( string $env_type, $constant ): bool {
	return in_array( $env_type, array( 'staging', 'local' ), true ) && true === $constant;
}

/**
 * Deterministic mock label adapter. $facts: order_id, carrier, submitted (bool,
 * Packeta: packet already submitted), store (array of order_id => ref, used to
 * make retries idempotent). Returns array( result, store ).
 */
function molosoc_ls_mock_adapter( string $carrier, array $facts ): array {
	$store    = (array) ( $facts['store'] ?? array() );
	$order_id = (int) ( $facts['order_id'] ?? 0 );
	$key      = $carrier . ':' . $order_id;
	if ( 'PPL' !== $carrier && 'Zásilkovna' !== $carrier ) {
		return array( array( 'ok' => false, 'live' => false, 'reason' => 'unknown_carrier' ), $store );
	}
	if ( 'Zásilkovna' === $carrier && empty( $facts['submitted'] ) ) {
		// Real Packeta: no PDF until the packet exists at the API.
		return array( array( 'ok' => false, 'live' => false, 'reason' => 'packet_not_submitted' ), $store );
	}
	if ( ! isset( $store[ $key ] ) ) {
		$store[ $key ] = 'MOCK-' . strtoupper( substr( sha1( $key ), 0, 10 ) );
	}
	return array(
		array(
			'ok'       => true,
			'live'     => false,
			'carrier'  => $carrier,
			'mock_ref' => $store[ $key ],
			'note'     => 'staging mock: no real label',
		),
		$store,
	);
}

/**
 * Explicit per-order mock state: has a sandbox packet been "submitted" for this
 * order? Stored in option molosoc_ls_mock_submitted (order_id => true). Defaults
 * to false, so a fresh Packeta order fails with packet_not_submitted.
 */
function molosoc_ls_packet_submitted( int $order_id ): bool {
	$submitted = (array) get_option( 'molosoc_ls_mock_submitted', array() );
	return ! empty( $submitted[ $order_id ] );
}

/** Mark a mock packet as submitted for an order (staging simulation only, no API call). */
function molosoc_ls_mock_submit_packet( int $order_id ): void {
	$submitted              = (array) get_option( 'molosoc_ls_mock_submitted', array() );
	$submitted[ $order_id ] = true;
	update_option( 'molosoc_ls_mock_submitted', $submitted, false );
}

/** The callback registered on molosoc_label_dispatch_adapter. */
function molosoc_ls_adapter_filter( $unused, $carrier, $order_id ) {
	$store = (array) get_option( 'molosoc_ls_mock_store', array() );
	[ $res, $store ] = molosoc_ls_mock_adapter(
		(string) $carrier,
		array(
			'order_id'  => (int) $order_id,
			'submitted' => molosoc_ls_packet_submitted( (int) $order_id ),
			'store'     => $store,
		)
	);
	update_option( 'molosoc_ls_mock_store', $store, false );
	return $res;
}

if ( function_exists( 'wp_get_environment_type' )
	&& molosoc_ls_enabled( wp_get_environment_type(), defined( 'MOLOSOC_LABEL_DISPATCH_STAGING' ) ? MOLOSOC_LABEL_DISPATCH_STAGING : null ) ) {
	add_filter( 'molosoc_label_dispatch_adapter', 'molosoc_ls_adapter_filter', 10, 3 );
}
