<?php
/**
 * Plugin Name: MOLOSOC Carrier Label Read-only Preview (OFF by default, single-order allowlist)
 * Description: Admin-only, read-only check of the ONE allowlisted order before any live label mail: eligibility, carrier, subject, recipient, Packeta packet id, and the label PDF itself, shown to the admin only. Sends nothing and writes nothing. Issue #369.
 * Version: 0.1.0
 *
 * SAFETY CONTRACT
 *
 *   - Inert unless wp-config.php defines
 *       MOLOSOC_LABEL_LIVE_PREVIEW   === true
 *       MOLOSOC_LABEL_LIVE_ORDER_IDS === array( <exactly one positive int> )
 *     and MOLOSOC_LABEL_LIVE_ENABLED is NOT true (preview is the step BEFORE live)
 *     and the mock delivery stage is not enabled.
 *   - Admin only: `manage_woocommerce` capability; the label fetch is a nonce-checked POST.
 *   - Read-only: no mail is sent, no order status/meta/option write, no audit row, no cron,
 *     no packet creation. The label PDF is fetched with Packeta's `packetLabelPdf` for the
 *     packet that ALREADY exists on the order and is streamed only to the admin's browser
 *     (`Cache-Control: no-store`); it is never stored on the server.
 *   - The packet id shown here is what Žaneta approves; the live send is then pinned to it
 *     via MOLOSOC_LABEL_LIVE_APPROVED_PACKET (molosoc-carrier-label-live.php).
 *
 * See docs/carrier-label-live-order-369.md.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const MOLOSOC_LP_PAGE   = 'molosoc-label-preview';
const MOLOSOC_LP_ACTION = 'molosoc_label_preview_pdf';
const MOLOSOC_LP_CAP    = 'manage_woocommerce';

/**
 * Pure gate. Returns array( bool ok, string reason, int order_id ).
 * `$preview` must be exactly true, live must be off, mock off, allowlist exactly one positive int.
 */
function molosoc_lp_gate( $preview, $live_enabled, $ids, bool $mock_enabled ): array {
	if ( true !== $preview ) {
		return array( false, 'preview_disabled', 0 );
	}
	if ( true === $live_enabled ) {
		return array( false, 'live_enabled_preview_refused', 0 );
	}
	if ( $mock_enabled ) {
		return array( false, 'mock_delivery_also_enabled', 0 );
	}
	if ( ! is_array( $ids ) || 1 !== count( $ids ) ) {
		return array( false, 'allowlist_must_be_exactly_one_order', 0 );
	}
	$only = reset( $ids );
	if ( ! is_int( $only ) || $only <= 0 ) {
		return array( false, 'allowlist_invalid_id', 0 );
	}
	return array( true, 'allowed', $only );
}

/**
 * Pure read-only report for the allowlisted order. `$snap` is the delivery-stage snapshot,
 * `$state` the stored delivery state, `$packet_id` the value of the operator packet meta,
 * `$configured` whether the packet meta key and API password are both defined.
 * Contains no customer data (ids, carrier, subject, fixed addresses only).
 */
function molosoc_lp_report( int $order_id, array $snap, string $state, string $packet_id, bool $configured ): array {
	[ $eligible, $reason ] = molosoc_ld_decide( $snap );
	$carrier  = (string) ( $snap['carrier'] ?? '' );
	$subject  = '' === $carrier ? null : molosoc_ld_subject( $carrier, (array) ( $snap['sizes'] ?? array() ) );
	$packet   = trim( $packet_id );
	$blockers = array();
	if ( ! $eligible ) {
		$blockers[] = $reason;
	}
	if ( 'Zásilkovna' !== $carrier ) {
		$blockers[] = 'PPL' === $carrier ? 'ppl_manual_label_required' : 'carrier_not_zasilkovna';
	}
	if ( in_array( $state, array( 'mailed', 'attention', 'mailing' ), true ) ) {
		$blockers[] = 'delivery_state_' . $state;
	}
	if ( ! $configured ) {
		$blockers[] = 'packeta_unconfigured';
	} elseif ( '' === $packet ) {
		$blockers[] = 'packet_not_submitted';
	} elseif ( ! molosoc_ll_packet_id_valid( $packet ) ) {
		$blockers[] = 'packet_id_malformed';
	}
	return array(
		'order'     => $order_id,
		'decision'  => $reason,
		'carrier'   => $carrier,
		'subject'   => $subject,
		'filename'  => molosoc_ld3_filename( $carrier, $order_id ),
		'to'        => MOLOSOC_LD_RECIPIENT,
		'cc'        => MOLOSOC_LD_CC,
		'state'     => $state,
		'packet_id' => molosoc_ll_packet_id_valid( $packet ) ? $packet : '',
		'blockers'  => $blockers,
		'ready'     => array() === $blockers,
	);
}

/**
 * Pure label check for the preview download: provider result → array( ok, reason, pdf, sha256, bytes ).
 * Uses the same PDF validation as the live mailer.
 */
function molosoc_lp_label( array $res ): array {
	if ( empty( $res['ok'] ) ) {
		return array( 'ok' => false, 'reason' => (string) ( $res['reason'] ?? 'provider_failed' ) );
	}
	[ $ok, $reason ] = molosoc_ld3_validate_pdf( $res['pdf'] ?? null );
	if ( ! $ok ) {
		return array( 'ok' => false, 'reason' => $reason );
	}
	return array( 'ok' => true, 'reason' => 'ok', 'pdf' => $res['pdf'], 'sha256' => hash( 'sha256', $res['pdf'] ), 'bytes' => strlen( $res['pdf'] ) );
}

/* ---------------------------------------------------------------- WP glue */

function molosoc_lp_gate_now(): array {
	return molosoc_lp_gate(
		defined( 'MOLOSOC_LABEL_LIVE_PREVIEW' ) ? MOLOSOC_LABEL_LIVE_PREVIEW : null,
		defined( 'MOLOSOC_LABEL_LIVE_ENABLED' ) ? MOLOSOC_LABEL_LIVE_ENABLED : null,
		defined( 'MOLOSOC_LABEL_LIVE_ORDER_IDS' ) ? MOLOSOC_LABEL_LIVE_ORDER_IDS : null,
		defined( 'MOLOSOC_LABEL_DELIVERY_ENABLED' ) && true === MOLOSOC_LABEL_DELIVERY_ENABLED
	);
}

function molosoc_lp_deps_loaded(): bool {
	return function_exists( 'molosoc_ld_decide' ) && function_exists( 'molosoc_ld3_snapshot' ) && function_exists( 'molosoc_ll_provider_now' );
}

function molosoc_lp_report_now( int $order_id ): array {
	$key = defined( 'MOLOSOC_LL_PACKETA_PACKET_META' ) ? (string) MOLOSOC_LL_PACKETA_PACKET_META : '';
	$pw  = defined( 'MOLOSOC_LL_PACKETA_API_PASSWORD' ) ? (string) MOLOSOC_LL_PACKETA_API_PASSWORD : '';
	return molosoc_lp_report(
		$order_id,
		molosoc_ld3_snapshot( $order_id ),
		molosoc_ld3_meta_get( $order_id, MOLOSOC_LD3_STATE_META ),
		'' === $key ? '' : molosoc_ld3_meta_get( $order_id, $key ),
		'' !== $key && '' !== $pw
	);
}

function molosoc_lp_render_page(): void {
	if ( ! current_user_can( MOLOSOC_LP_CAP ) ) {
		wp_die( 'forbidden', 403 );
	}
	[ $ok, $reason, $order_id ] = molosoc_lp_gate_now();
	echo '<div class="wrap"><h1>MOLOSOC – náhled štítku (jen čtení, nic se neodešle)</h1>';
	if ( ! $ok || ! molosoc_lp_deps_loaded() ) {
		echo '<p>Nedostupné: <code>' . esc_html( $ok ? 'pipeline_not_loaded' : $reason ) . '</code></p></div>';
		return;
	}
	$r    = molosoc_lp_report_now( $order_id );
	$rows = array(
		'Objednávka'            => (string) $r['order'],
		'Rozhodnutí'            => (string) $r['decision'],
		'Dopravce'              => (string) $r['carrier'],
		'Předmět'               => (string) $r['subject'],
		'Příloha'               => (string) $r['filename'],
		'Komu'                  => (string) $r['to'],
		'Kopie'                 => (string) $r['cc'],
		'Stav doručení'         => '' === $r['state'] ? '(žádný)' : (string) $r['state'],
		'Packeta packet id'     => '' === $r['packet_id'] ? '(chybí)' : (string) $r['packet_id'],
		'Překážky'              => array() === $r['blockers'] ? '(žádné)' : implode( ', ', $r['blockers'] ),
	);
	echo '<table class="widefat striped" style="max-width:720px"><tbody>';
	foreach ( $rows as $k => $v ) {
		echo '<tr><th>' . esc_html( $k ) . '</th><td><code>' . esc_html( $v ) . '</code></td></tr>';
	}
	echo '</tbody></table>';
	if ( '' !== $r['packet_id'] ) {
		echo '<form method="post" action="' . esc_url( admin_url( 'admin-post.php' ) ) . '" target="_blank" style="margin-top:1em">';
		echo '<input type="hidden" name="action" value="' . esc_attr( MOLOSOC_LP_ACTION ) . '">';
		wp_nonce_field( MOLOSOC_LP_ACTION );
		echo '<button class="button">Zobrazit PDF štítku (jen náhled, nic se neodešle)</button></form>';
	}
	echo '</div>';
}

function molosoc_lp_handle_pdf(): void {
	if ( ! current_user_can( MOLOSOC_LP_CAP ) ) {
		wp_die( 'forbidden', 403 );
	}
	check_admin_referer( MOLOSOC_LP_ACTION );
	[ $ok, $reason, $order_id ] = molosoc_lp_gate_now();
	if ( ! $ok || ! molosoc_lp_deps_loaded() ) {
		wp_die( esc_html( $ok ? 'pipeline_not_loaded' : $reason ), 409 );
	}
	$r = molosoc_lp_report_now( $order_id );
	if ( 'Zásilkovna' !== $r['carrier'] || '' === $r['packet_id'] ) {
		wp_die( esc_html( 'no_packeta_packet' ), 409 );
	}
	$label = molosoc_lp_label( molosoc_ll_provider_now( $order_id, 'Zásilkovna', '' ) );
	if ( ! $label['ok'] ) {
		wp_die( esc_html( 'label_fetch_failed: ' . $label['reason'] ), 502 );
	}
	nocache_headers();
	header( 'Cache-Control: no-store, private' );
	header( 'Content-Type: application/pdf' );
	header( 'Content-Disposition: inline; filename="preview-' . $r['filename'] . '"' );
	header( 'X-Molosoc-Label-Sha256: ' . $label['sha256'] );
	header( 'X-Molosoc-Packet-Id: ' . $r['packet_id'] );
	echo $label['pdf']; // phpcs:ignore WordPress.Security.EscapeOutput -- binary PDF to an authenticated admin.
	exit;
}

if ( defined( 'MOLOSOC_LABEL_LIVE_PREVIEW' ) && true === MOLOSOC_LABEL_LIVE_PREVIEW ) {
	add_action(
		'admin_menu',
		static function () {
			add_management_page( 'MOLOSOC náhled štítku', 'MOLOSOC náhled štítku', MOLOSOC_LP_CAP, MOLOSOC_LP_PAGE, 'molosoc_lp_render_page' );
		}
	);
	add_action( 'admin_post_' . MOLOSOC_LP_ACTION, 'molosoc_lp_handle_pdf' );
}
