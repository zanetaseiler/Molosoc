<?php
/**
 * Admin settings screen for the MOLOSOC post-purchase review request (Issue #353).
 *
 * Lets an administrator set the three existing options of inc/review-request.php
 * without raw wp_options access:
 *   molosoc_review_request_mode             off | dry_run | live
 *   molosoc_review_request_test_emails      comma-separated allowlist
 *   molosoc_review_request_legal_confirmed  '1' | ''
 *
 * NOT a new engine. Registers a page only; writes nothing on load, activation
 * or deploy. Options change only when an administrator submits the form
 * (nonce + manage_options). Go-live additionally needs an explicit
 * acknowledgement when the allowlist is empty.
 *
 * Required once from functions.php, after inc/review-request.php.
 */

defined( 'ABSPATH' ) || exit;

if ( ! defined( 'MOLOSOC_REVIEW_REQUEST_ADMIN_SLUG' ) ) {
	define( 'MOLOSOC_REVIEW_REQUEST_ADMIN_SLUG', 'molosoc-review-request' );
}

/** Pure sanitiser: keep only valid, de-duplicated e-mail addresses. */
function molosoc_review_request_admin_clean_emails( $raw ) {
	$out = array();
	foreach ( preg_split( '/[\s,;]+/', (string) $raw ) as $e ) {
		$e = trim( $e );
		if ( '' !== $e && is_email( $e ) && ! in_array( strtolower( $e ), array_map( 'strtolower', $out ), true ) ) {
			$out[] = $e;
		}
	}
	return implode( ', ', $out );
}

/**
 * Validate a submission. Returns array( values|null, error string ).
 * Pure function so it can be tested without WordPress.
 */
function molosoc_review_request_admin_validate( $post ) {
	$mode = isset( $post['mode'] ) ? (string) $post['mode'] : 'off';
	if ( ! in_array( $mode, array( 'off', 'dry_run', 'live' ), true ) ) {
		return array( null, 'Invalid mode.' );
	}
	$emails = molosoc_review_request_admin_clean_emails( isset( $post['test_emails'] ) ? $post['test_emails'] : '' );
	$legal  = ! empty( $post['legal_confirmed'] ) ? '1' : '';
	if ( 'live' === $mode ) {
		if ( '1' !== $legal ) {
			return array( null, 'Live mode needs the legal-confirmed box ticked (otherwise it would only behave as a dry run).' );
		}
		if ( '' === $emails && empty( $post['ack_all_orders'] ) ) {
			return array( null, 'The test allowlist is empty: live mode would e-mail ALL eligible orders. Tick the acknowledgement or add an allowlist address.' );
		}
	}
	return array( array( 'mode' => $mode, 'emails' => $emails, 'legal' => $legal ), '' );
}

function molosoc_review_request_admin_menu() {
	add_submenu_page(
		'woocommerce',
		'Review request',
		'Review request',
		'manage_options',
		MOLOSOC_REVIEW_REQUEST_ADMIN_SLUG,
		'molosoc_review_request_admin_render'
	);
}
add_action( 'admin_menu', 'molosoc_review_request_admin_menu' );

function molosoc_review_request_admin_save() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( 'Not allowed.' );
	}
	check_admin_referer( 'molosoc_review_request_save' );
	list( $v, $err ) = molosoc_review_request_admin_validate( wp_unslash( $_POST ) );
	$url = admin_url( 'admin.php?page=' . MOLOSOC_REVIEW_REQUEST_ADMIN_SLUG );
	if ( null === $v ) {
		wp_safe_redirect( add_query_arg( 'mrr_error', rawurlencode( $err ), $url ) );
		exit;
	}
	update_option( 'molosoc_review_request_mode', $v['mode'] );
	update_option( 'molosoc_review_request_test_emails', $v['emails'] );
	update_option( 'molosoc_review_request_legal_confirmed', $v['legal'] );
	wp_safe_redirect( add_query_arg( 'mrr_saved', '1', $url ) );
	exit;
}
add_action( 'admin_post_molosoc_review_request_save', 'molosoc_review_request_admin_save' );

function molosoc_review_request_admin_render() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	$mode   = molosoc_review_request_mode();
	$emails = (string) get_option( 'molosoc_review_request_test_emails', '' );
	$legal  = '1' === (string) get_option( 'molosoc_review_request_legal_confirmed', '' );
	$sends  = molosoc_review_request_is_live();
	$scope  = '' !== trim( $emails ) ? 'ONLY the allowlist addresses' : 'ALL eligible orders (allowlist is empty)';

	echo '<div class="wrap"><h1>Review request e-mail</h1>';
	if ( isset( $_GET['mrr_saved'] ) ) {
		echo '<div class="notice notice-success"><p>Saved.</p></div>';
	}
	if ( isset( $_GET['mrr_error'] ) ) {
		echo '<div class="notice notice-error"><p>' . esc_html( wp_unslash( $_GET['mrr_error'] ) ) . '</p></div>';
	}

	echo '<div class="notice notice-warning inline"><p><strong>Legal copy / approval required.</strong> '
		. 'Do not go live until the approved CZ/EN review-request and opt-out wording is published in the Terms/Privacy pages. '
		. 'Accepting the Terms is not marketing permission; the checkout notice with a refusal box is what permits this e-mail.</p>'
		. '<p><strong>CusRev:</strong> turn off its review invitations/reminders in its own settings before any send (do not deactivate the plugin) to avoid duplicate requests.</p></div>';

	echo '<h2>Current status</h2><table class="widefat striped" style="max-width:720px"><tbody>';
	printf( '<tr><th>Mode</th><td><code>%s</code></td></tr>', esc_html( $mode ) );
	printf( '<tr><th>Legal confirmed</th><td>%s</td></tr>', $legal ? 'yes' : 'no' );
	printf( '<tr><th>Real e-mails are sent</th><td><strong>%s</strong></td></tr>', $sends ? 'YES' : 'no (off or dry run)' );
	printf( '<tr><th>Recipients when sending</th><td>%s</td></tr>', esc_html( $scope ) );
	echo '<tr><th>Always enforced</th><td>Only orders that saw the checkout notice; per-order opt-out; suppressed addresses; no refunded orders; one e-mail per order; no retroactive sends.</td></tr>';
	echo '</tbody></table>';

	echo '<h2>Settings</h2><form method="post" action="' . esc_url( admin_url( 'admin-post.php' ) ) . '">';
	echo '<input type="hidden" name="action" value="molosoc_review_request_save">';
	wp_nonce_field( 'molosoc_review_request_save' );
	echo '<table class="form-table"><tbody><tr><th>Mode</th><td>';
	foreach ( array( 'off' => 'Off (nothing scheduled or sent)', 'dry_run' => 'Dry run (private order notes only, never e-mails)', 'live' => 'Live (sends; needs legal confirmation)' ) as $k => $label ) {
		printf( '<label style="display:block"><input type="radio" name="mode" value="%s"%s> %s</label>', esc_attr( $k ), checked( $mode, $k, false ), esc_html( $label ) );
	}
	echo '</td></tr><tr><th>Test allowlist</th><td>';
	printf( '<textarea name="test_emails" rows="3" cols="50">%s</textarea>', esc_textarea( $emails ) );
	echo '<p class="description">Comma-separated. While filled, ONLY these addresses are ever e-mailed, in any mode. '
		. '<strong>Clearing it enables all eligible orders.</strong></p></td></tr>';
	echo '<tr><th>Legal confirmed</th><td><label><input type="checkbox" name="legal_confirmed" value="1"' . checked( $legal, true, false )
		. '> Approved CZ/EN legal copy is published and the checkout notice is live.</label></td></tr>';
	echo '<tr><th>Empty allowlist</th><td><label><input type="checkbox" name="ack_all_orders" value="1"> '
		. 'I understand live mode with an empty allowlist e-mails ALL eligible orders.</label></td></tr>';
	echo '</tbody></table>';
	submit_button( 'Save settings' );
	echo '</form></div>';
}
