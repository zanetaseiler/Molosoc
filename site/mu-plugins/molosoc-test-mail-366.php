<?php
/**
 * Plugin Name: MOLOSOC One-time TEST Mail (Issue #366, OFF by default)
 * Description: Admin-only, single-use test of wp_mail() -> WP Mail SMTP -> Brevo with a fixed Czech message and a generated TEST PDF. Not a shipping label, no order effects.
 * Version: 0.1.0
 *
 * SAFETY CONTRACT
 *
 *   - Inert unless wp-config.php defines MOLOSOC_TEST_MAIL_366_ENABLED === true
 *     (exactly the boolean true). Without it no hook, menu or handler is registered.
 *     Merging/deploying this file changes nothing by itself.
 *   - Only a logged-in user with `manage_options` can trigger it, by a POST to
 *     admin-post.php that must carry a valid nonce.
 *   - Recipient (To jarka01@atlas.cz, Cc hello@molosoc.com), subject, body and
 *     attachment are fixed constants or generated here. No request field is
 *     ever read into the message. There is nothing to configure.
 *   - Durable one-time lock: the option `molosoc_test_mail_366_lock` is claimed with
 *     an atomic `INSERT IGNORE` on the unique option_name BEFORE wp_mail() runs
 *     (add_option() is not used: its ON DUPLICATE KEY UPDATE can let a race through).
 *     It is never released, not even if wp_mail() fails, so at most ONE send attempt
 *     is ever possible.
 *   - Uses only wp_mail(); the existing WP Mail SMTP -> Brevo configuration decides
 *     the transport and the forced sender (hello@molosoc.com). No From header, no
 *     SMTP/Brevo settings, no API keys are read or changed here.
 *   - Touches no order, packet, shipping, checkout or payment data. It does not load
 *     or call WooCommerce and is independent of the carrier label pipeline.
 *   - The attachment is a generated, clearly marked TEST PDF written to a private
 *     temporary directory that is always removed.
 *
 * Removal: see docs/test-mail-366.md.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const MOLOSOC_TM366_TO       = 'jarka01@atlas.cz';
const MOLOSOC_TM366_CC       = 'hello@molosoc.com';
const MOLOSOC_TM366_SUBJECT  = 'MOLOSOC – TEST doručování přepravních štítků (není skutečná objednávka)';
const MOLOSOC_TM366_BODY     = "Ahoj mami,\n\nposíláme pouze zkušební e-mail, abychom ověřili, že správně funguje automatické zasílání přepravních štítků z MOLOSOC.\n\nV příloze je testovací PDF, nejde o skutečnou objednávku ani o štítek k odeslání zásilky.\n\nNemusíš nic tisknout ani odesílat.\n\nDěkujeme!";
const MOLOSOC_TM366_FILENAME = 'MOLOSOC-TEST-neni-stitek.pdf';
const MOLOSOC_TM366_LOCK     = 'molosoc_test_mail_366_lock';
const MOLOSOC_TM366_ACTION   = 'molosoc_test_mail_366';
const MOLOSOC_TM366_CAP      = 'manage_options';

/** Exactly true, nothing else. */
function molosoc_tm366_enabled( $flag ): bool {
	return true === $flag;
}

/** The fixed message. Pure; no argument can influence it. */
function molosoc_tm366_message(): array {
	return array(
		'to'       => MOLOSOC_TM366_TO,
		'subject'  => MOLOSOC_TM366_SUBJECT,
		'body'     => MOLOSOC_TM366_BODY,
		'headers'  => array( 'Content-Type: text/plain; charset=UTF-8', 'Cc: ' . MOLOSOC_TM366_CC ),
		'filename' => MOLOSOC_TM366_FILENAME,
	);
}

/**
 * Deterministic one-page PDF that says, in large type, that it is a TEST and not a
 * shipping label. ASCII only (standard Helvetica), correct xref offsets.
 */
function molosoc_tm366_pdf(): string {
	$lines = array(
		array( 36, 'TEST - NENI SKUTECNY STITEK' ),
		array( 20, 'TEST ONLY - NOT A SHIPPING LABEL' ),
		array( 14, 'MOLOSOC - zkusebni e-mail (Issue #366)' ),
		array( 14, 'Netisknout, neodesilat. Do not print, do not ship.' ),
	);
	$stream = "BT\n";
	$y      = 760;
	foreach ( $lines as $l ) {
		$stream .= '/F1 ' . $l[0] . ' Tf 1 0 0 1 50 ' . $y . " Tm (" . $l[1] . ") Tj\n";
		$y      -= $l[0] + 24;
	}
	$stream .= "ET\n";
	$objs = array(
		'<< /Type /Catalog /Pages 2 0 R >>',
		'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
		'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>',
		'<< /Length ' . strlen( $stream ) . " >>\nstream\n" . $stream . 'endstream',
		'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
	);
	$pdf  = "%PDF-1.4\n";
	$offs = array();
	foreach ( $objs as $i => $o ) {
		$offs[] = strlen( $pdf );
		$pdf   .= ( $i + 1 ) . " 0 obj\n" . $o . "\nendobj\n";
	}
	$xref = strlen( $pdf );
	$pdf .= 'xref' . "\n0 " . ( count( $objs ) + 1 ) . "\n0000000000 65535 f \n";
	foreach ( $offs as $off ) {
		$pdf .= sprintf( "%010d 00000 n \n", $off );
	}
	$pdf .= 'trailer' . "\n<< /Size " . ( count( $objs ) + 1 ) . " /Root 1 0 R >>\nstartxref\n" . $xref . "\n%%EOF\n";
	return $pdf;
}

/**
 * Core, with all I/O injected so it is testable without WordPress or a network.
 * `$io`:
 *   enabled          bool    MOLOSOC_TEST_MAIL_366_ENABLED === true
 *   can              bool    current user has MOLOSOC_TM366_CAP
 *   nonce_ok         bool    valid admin nonce for MOLOSOC_TM366_ACTION
 *   claim()          bool    atomically create the lock; false if it already exists
 *   tmp(name, bytes) string  path of a written private temp file ('' = failed)
 *   rm(path)                 remove that temp file (and its private dir)
 *   send(to, subj, body, headers, attachments) bool   wp_mail
 *   record(array)            store the result in the (already claimed) lock
 * Returns a short reason code.
 */
function molosoc_tm366_execute( array $io ): string {
	if ( true !== ( $io['enabled'] ?? null ) ) {
		return 'disabled';
	}
	if ( true !== ( $io['can'] ?? null ) ) {
		return 'forbidden';
	}
	if ( true !== ( $io['nonce_ok'] ?? null ) ) {
		return 'bad_nonce';
	}
	// Claim the durable lock BEFORE any send. Never released: at most one attempt, ever.
	if ( true !== (bool) $io['claim']() ) {
		return 'already_used';
	}
	$m    = molosoc_tm366_message();
	$path = (string) $io['tmp']( $m['filename'], molosoc_tm366_pdf() );
	if ( '' === $path ) {
		$io['record']( array( 'result' => 'tempfile_failed' ) );
		return 'tempfile_failed';
	}
	try {
		$sent = (bool) $io['send']( $m['to'], $m['subject'], $m['body'], $m['headers'], array( $path ) );
	} finally {
		$io['rm']( $path );
	}
	$io['record']( array( 'result' => $sent ? 'sent' : 'wp_mail_false' ) );
	return $sent ? 'sent' : 'wp_mail_false';
}

/** Writes the PDF as <private temp dir>/<fixed filename> so the attachment keeps its name. */
function molosoc_tm366_tmp( string $name, string $bytes ): string {
	$dir = trailingslashit( get_temp_dir() ) . 'molosoc-tm366-' . wp_generate_password( 16, false, false );
	if ( ! wp_mkdir_p( $dir ) ) {
		return '';
	}
	$path = $dir . '/' . $name;
	if ( strlen( $bytes ) !== (int) file_put_contents( $path, $bytes ) ) {
		molosoc_tm366_rm( $path );
		return '';
	}
	return $path;
}

function molosoc_tm366_rm( string $path ): void {
	if ( '' === $path ) {
		return;
	}
	if ( is_file( $path ) ) {
		unlink( $path );
	}
	$dir = dirname( $path );
	if ( 0 === strpos( basename( $dir ), 'molosoc-tm366-' ) && is_dir( $dir ) ) {
		rmdir( $dir );
	}
}

/** Atomic, durable claim. True only for the single request whose INSERT created the row. */
function molosoc_tm366_claim( int $user ): bool {
	global $wpdb;
	$value = maybe_serialize( array( 'result' => 'claimed', 'user' => $user, 'ts' => time() ) );
	$rows  = $wpdb->query(
		$wpdb->prepare( "INSERT IGNORE INTO {$wpdb->options} (option_name, option_value, autoload) VALUES (%s, %s, 'no')", MOLOSOC_TM366_LOCK, $value )
	);
	wp_cache_delete( 'notoptions', 'options' );
	wp_cache_delete( MOLOSOC_TM366_LOCK, 'options' );
	return 1 === (int) $rows;
}

/** Lock status for the admin screen: null when never used. */
function molosoc_tm366_lock_state() {
	$v = get_option( MOLOSOC_TM366_LOCK, null );
	return is_array( $v ) ? $v : ( null === $v ? null : array( 'result' => 'claimed' ) );
}

function molosoc_tm366_handle(): void {
	$nonce_ok = isset( $_POST['_wpnonce'] ) && false !== wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['_wpnonce'] ) ), MOLOSOC_TM366_ACTION );
	$user     = get_current_user_id();
	$reason   = molosoc_tm366_execute(
		array(
			'enabled'  => molosoc_tm366_enabled( defined( 'MOLOSOC_TEST_MAIL_366_ENABLED' ) ? MOLOSOC_TEST_MAIL_366_ENABLED : null ),
			'can'      => current_user_can( MOLOSOC_TM366_CAP ),
			'nonce_ok' => $nonce_ok,
			'claim'    => function () use ( $user ) {
				return molosoc_tm366_claim( $user );
			},
			'tmp'      => 'molosoc_tm366_tmp',
			'rm'       => 'molosoc_tm366_rm',
			'send'     => 'wp_mail',
			'record'   => function ( array $r ) use ( $user ) {
				update_option( MOLOSOC_TM366_LOCK, $r + array( 'user' => $user, 'ts' => time() ), 'no' );
			},
		)
	);
	if ( in_array( $reason, array( 'forbidden', 'bad_nonce', 'disabled' ), true ) ) {
		wp_die( esc_html( 'MOLOSOC test mail: ' . $reason ), 403 );
	}
	wp_safe_redirect( add_query_arg( array( 'page' => MOLOSOC_TM366_ACTION, 'tm366' => $reason ), admin_url( 'tools.php' ) ) );
	exit;
}

function molosoc_tm366_page(): void {
	if ( ! current_user_can( MOLOSOC_TM366_CAP ) ) {
		return;
	}
	$m     = molosoc_tm366_message();
	$state = molosoc_tm366_lock_state();
	echo '<div class="wrap"><h1>MOLOSOC – jednorázový TEST e-mail (#366)</h1>';
	if ( isset( $_GET['tm366'] ) ) {
		echo '<div class="notice notice-info"><p>Výsledek: <code>' . esc_html( sanitize_key( wp_unslash( $_GET['tm366'] ) ) ) . '</code></p></div>';
	}
	echo '<p><strong>To:</strong> ' . esc_html( $m['to'] ) . '<br><strong>Cc:</strong> ' . esc_html( MOLOSOC_TM366_CC ) .
		'<br><strong>Předmět:</strong> ' . esc_html( $m['subject'] ) . '<br><strong>Příloha:</strong> ' . esc_html( $m['filename'] ) . '</p>';
	echo '<pre style="white-space:pre-wrap;max-width:640px">' . esc_html( $m['body'] ) . '</pre>';
	if ( null !== $state ) {
		echo '<p><strong>Již použito – další odeslání není možné.</strong> Stav: <code>' . esc_html( (string) ( $state['result'] ?? '' ) ) . '</code>' .
			( isset( $state['ts'] ) ? ' (' . esc_html( gmdate( 'Y-m-d H:i:s', (int) $state['ts'] ) ) . ' UTC)' : '' ) . '</p></div>';
		return;
	}
	echo '<form method="post" action="' . esc_url( admin_url( 'admin-post.php' ) ) . '">';
	echo '<input type="hidden" name="action" value="' . esc_attr( MOLOSOC_TM366_ACTION ) . '">';
	wp_nonce_field( MOLOSOC_TM366_ACTION );
	echo '<p><button type="submit" class="button button-primary" onclick="return confirm(\'Odeslat JEDINÝ testovací e-mail? Lze jen jednou.\');">Odeslat jediný TEST e-mail</button></p></form></div>';
}

if ( molosoc_tm366_enabled( defined( 'MOLOSOC_TEST_MAIL_366_ENABLED' ) ? MOLOSOC_TEST_MAIL_366_ENABLED : null ) ) {
	add_action( 'admin_post_' . MOLOSOC_TM366_ACTION, 'molosoc_tm366_handle' );
	add_action(
		'admin_menu',
		function () {
			add_management_page( 'MOLOSOC TEST e-mail', 'MOLOSOC TEST e-mail', MOLOSOC_TM366_CAP, MOLOSOC_TM366_ACTION, 'molosoc_tm366_page' );
		}
	);
}
