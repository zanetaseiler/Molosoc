<?php
/**
 * Plugin Name: MOLOSOC Carrier Label Automation (OFF by default, all eligible new orders)
 * Description: Hands-off carrier label pipeline for every eligible NEW order: queue, wait for the Packeta packet, fetch its existing label PDF, mail it to the dispatcher via wp_mail, retry, alert on failure. PPL stays manual (alert only). Includes a read-only status page. Issue #369.
 * Version: 0.1.0
 *
 * SAFETY CONTRACT
 *
 *   - Inert unless wp-config.php defines MOLOSOC_LABEL_AUTO_ENABLED === true AND a valid
 *     MOLOSOC_LABEL_DISPATCH_SINCE cut-off constant (the DB option is NOT accepted here).
 *     Refuses to run while the single-order live path (MOLOSOC_LABEL_LIVE_ENABLED) or the
 *     mock delivery stage (MOLOSOC_LABEL_DELIVERY_ENABLED) is on. The gate is re-checked on
 *     every queued run, so removing the constant stops all pending work at once.
 *   - No retroactive sends: only orders created at or after the cut-off, status exactly
 *     `processing`, COD or Comgate-confirmed card (molosoc_ld_decide()); bank transfer never.
 *   - NEVER creates a packet/shipment and never changes order status. Packeta packets are
 *     created by Packeta itself (its own auto-submission, or a manual export). This file only
 *     READS Packeta's `{prefix}packetery_order` row and FETCHES the existing label.
 *   - Packeta internal pickup-point carriers only. A numeric Packeta carrier id (external
 *     courier, needs a courier label), a cancelled/handed-over packet or a malformed packet id
 *     goes to `attention`, nothing is mailed.
 *   - PPL CZ 1.1.3 has no headless label path (see docs): PPL orders go to `attention` with
 *     one alert, nothing is fetched or mailed.
 *   - Label mail: the existing fixed-recipient mailer (MOLOSOC_LD_RECIPIENT, Cc MOLOSOC_LD_CC)
 *     and the Phase 3 state machine: at-most-once mail, stored packet ref (`ref_changed` stops
 *     a duplicate), tries limit. Customers are never mailed.
 *   - Alerts: at most one per order, plain text, to MOLOSOC_LD_CC only, ids and reason codes
 *     only (no customer data). The alert marker is written BEFORE the send (at-most-once).
 *   - Status page (Tools -> MOLOSOC štítky – automat): read-only, `manage_woocommerce`. No
 *     PDF fetch, no mail, no writes. Available with MOLOSOC_LABEL_AUTO_PREVIEW === true (for
 *     verification before go-live) or while automation is enabled.
 *
 * See docs/carrier-label-automation-369.md.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const MOLOSOC_LA_HOOK           = 'molosoc_la_process';
const MOLOSOC_LA_SWEEP_HOOK     = 'molosoc_la_sweep';
const MOLOSOC_LA_GROUP          = 'molosoc-carrier-label';
const MOLOSOC_LA_FIRST_DELAY    = 180;    // Let Packeta's own auto-submission run first.
const MOLOSOC_LA_WAIT_INTERVAL  = 900;    // Re-check for a packet every 15 min ...
const MOLOSOC_LA_WAIT_MAX       = 259200; // ... for up to 72 h after the order was first seen.
const MOLOSOC_LA_RETRY_DELAY    = 600;    // Retry after a transient fetch/mail failure.
const MOLOSOC_LA_SWEEP_INTERVAL = 900;
const MOLOSOC_LA_SWEEP_LIMIT    = 100;    // Orders queued per sweep run (also the page size) ...
const MOLOSOC_LA_SWEEP_MAX_PAGES = 20;     // ... and pages scanned per run, so handled orders never hide newer ones.
const MOLOSOC_LA_LOCK_TTL       = 900;    // A lock older than this is stale (request died).
const MOLOSOC_LA_SEEN_META      = '_molosoc_label_auto_seen';
const MOLOSOC_LA_ALERT_META     = '_molosoc_label_auto_alert';
const MOLOSOC_LA_DONE_META      = '_molosoc_label_auto_done'; // Set when a run ends with no follow-up queued.
const MOLOSOC_LA_PAGE           = 'molosoc-label-auto';
const MOLOSOC_LA_CAP            = 'manage_woocommerce';
const MOLOSOC_LA_LOG_SOURCE     = 'molosoc-carrier-label';
// Packeta packet statuses for which the label is still the one to print (not yet handed over).
const MOLOSOC_LA_PACKET_STATUS_OK = array( '', 'received data' );

/**
 * Pure gate. Returns array( bool allowed, string reason ).
 * `$enabled` must be exactly true; the cut-off must come from a defined, valid constant.
 */
function molosoc_la_gate( $enabled, bool $live_enabled, bool $mock_enabled, bool $since_defined, $since ): array {
	if ( true !== $enabled ) {
		return array( false, 'auto_disabled' );
	}
	if ( $live_enabled ) {
		return array( false, 'single_order_live_also_enabled' );
	}
	if ( $mock_enabled ) {
		return array( false, 'mock_delivery_also_enabled' );
	}
	if ( ! $since_defined ) {
		return array( false, 'cutoff_constant_required' );
	}
	if ( molosoc_ld_since_ts( true, $since, null ) <= 0 ) {
		return array( false, 'cutoff_invalid' );
	}
	return array( true, 'allowed' );
}

/**
 * Pure check of Packeta's own order row (packet_id, carrier_id, packet_status).
 * Returns '' when the existing label may be fetched, 'wait' when no packet exists yet,
 * otherwise a permanent reason (fail closed).
 */
function molosoc_la_packeta_check( $row ): string {
	if ( ! is_array( $row ) ) {
		return 'wait'; // No Packeta row yet.
	}
	$carrier_id = trim( (string) ( $row['carrier_id'] ?? '' ) );
	if ( '' === $carrier_id ) {
		return 'packeta_carrier_unknown';
	}
	if ( is_numeric( $carrier_id ) ) {
		return 'packeta_external_carrier_manual'; // External courier: needs a courier label.
	}
	$packet = trim( (string) ( $row['packet_id'] ?? '' ) );
	if ( '' === $packet ) {
		return 'wait';
	}
	if ( ! molosoc_ll_packet_id_valid( $packet ) ) {
		return 'packet_id_malformed';
	}
	$status = strtolower( trim( (string) ( $row['packet_status'] ?? '' ) ) );
	if ( 'cancelled' === $status ) {
		return 'packet_cancelled';
	}
	if ( ! in_array( $status, MOLOSOC_LA_PACKET_STATUS_OK, true ) ) {
		return 'packet_already_moving';
	}
	return '';
}

/**
 * Pure plan for one order. Returns array( action, reason ), action one of:
 *   done | attention_existing | check (mailing) | skip | wait | attention | send
 * `$snap` is the delivery snapshot, `$state` the stored delivery state, `$row` Packeta's
 * row (Zásilkovna only), `$configured` whether a Packeta API password is available.
 */
function molosoc_la_plan( array $snap, string $state, $row, bool $configured ): array {
	if ( 'mailed' === $state ) {
		return array( 'done', 'already_mailed' );
	}
	if ( 'attention' === $state ) {
		return array( 'attention_existing', 'needs_attention' );
	}
	if ( 'mailing' === $state ) {
		return array( 'check', 'mailing_in_progress_or_unknown' );
	}
	[ $ok, $reason ] = molosoc_ld_decide( $snap );
	if ( ! $ok ) {
		return array( 'skip', $reason );
	}
	$carrier = (string) ( $snap['carrier'] ?? '' );
	if ( 'PPL' === $carrier ) {
		return array( 'attention', 'ppl_manual_label_required' );
	}
	if ( 'Zásilkovna' !== $carrier ) {
		return array( 'attention', 'unknown_carrier' );
	}
	if ( ! $configured ) {
		return array( 'attention', 'packeta_unconfigured' );
	}
	$chk = molosoc_la_packeta_check( $row );
	if ( 'wait' === $chk ) {
		return array( 'wait', 'packet_not_submitted' );
	}
	if ( '' !== $chk ) {
		return array( 'attention', $chk );
	}
	return array( 'send', 'ready' );
}

/**
 * Provider for the automatic path: re-reads Packeta's row at fetch time, re-checks it, then
 * uses the shared fetch-only Packeta provider. `$d` = row, api_password, fetch.
 */
function molosoc_la_provider( string $carrier, string $stored_ref, array $d ): array {
	if ( 'Zásilkovna' !== $carrier ) {
		return molosoc_ll_provider( $carrier, $stored_ref, array() );
	}
	$chk = molosoc_la_packeta_check( $d['row'] ?? null );
	if ( 'wait' === $chk ) {
		return array( 'ok' => false, 'live' => true, 'reason' => 'packet_not_submitted' );
	}
	if ( '' !== $chk ) {
		return array( 'ok' => false, 'live' => true, 'permanent' => true, 'reason' => $chk );
	}
	return molosoc_ll_provider(
		$carrier,
		$stored_ref,
		array(
			'packet_id'    => trim( (string) $d['row']['packet_id'] ),
			'api_password' => (string) ( $d['api_password'] ?? '' ),
			'fetch'        => $d['fetch'],
		)
	);
}

/** Short Czech hint per reason for the alert mail. */
function molosoc_la_hint( string $reason ): string {
	$hints = array(
		'ppl_manual_label_required'       => 'PPL: štítek vytvořte ručně v pluginu PPL a pošlete ho ručně.',
		'packet_not_submitted'            => 'Zásilka v Packetě zatím neexistuje.',
		'packet_wait_timeout'             => 'Zásilka nebyla do 72 hodin podána do Packety. Podejte ji a štítek pošlete ručně.',
		'packeta_external_carrier_manual' => 'Packeta s externím dopravcem: štítek dopravce vytiskněte ručně v pluginu Packeta.',
		'packeta_carrier_unknown'         => 'Packeta nezná dopravce objednávky. Zkontrolujte objednávku v pluginu Packeta.',
		'packet_cancelled'                => 'Zásilka je v Packetě zrušená. Nic nebylo odesláno.',
		'packet_already_moving'           => 'Zásilka už je v přepravě. Nic nebylo odesláno.',
		'packet_id_malformed'             => 'Neplatné číslo zásilky v Packetě.',
		'packeta_unconfigured'            => 'Chybí API heslo Packety (nastavení pluginu Packeta).',
		'mail_state_unknown'              => 'E-mail možná odešel. Nejdřív zkontrolujte schránku a log Brevo, nic znovu neposílejte.',
		'ref_changed'                     => 'Číslo zásilky se změnilo. Zkontrolujte v Packetě, zda nevznikla duplicitní zásilka.',
		'max_tries'                       => 'Stažení štítku nebo odeslání e-mailu opakovaně selhalo.',
		'exception'                       => 'Automat opakovaně narazil na chybu (výjimku). Štítek nebyl odeslán, zkontrolujte log molosoc-carrier-label-auto.',
		'unknown_carrier'                 => 'Neznámý dopravce.',
	);
	return $hints[ $reason ] ?? 'Zkontrolujte audit objednávky.';
}

/**
 * Pure alert message. Fixed recipient (MOLOSOC_LD_CC), ids and reason codes only.
 * An unexpected reason string is replaced by `unknown` (it never reaches a header raw).
 */
function molosoc_la_alert_message( int $order_id, string $reason ): array {
	if ( 1 !== preg_match( '/^[a-z0-9_]{1,64}$/', $reason ) ) {
		$reason = 'unknown';
	}
	return array(
		'to'      => MOLOSOC_LD_CC,
		'subject' => sprintf( 'MOLOSOC štítek: objednávka #%d vyžaduje ruční kontrolu (%s)', $order_id, $reason ),
		'body'    => implode(
			"\n",
			array(
				sprintf( 'Objednávka: #%d', $order_id ),
				sprintf( 'Důvod: %s', $reason ),
				molosoc_la_hint( $reason ),
				'',
				'Štítek NEBYL automaticky odeslán. Automat tuto objednávku dál nezpracuje.',
				'Stav: WooCommerce -> Nástroje -> MOLOSOC štítky – automat.',
			)
		),
	);
}

/**
 * Sends the alert at most once per order. `$get()` returns the stored marker, `$set($r)`
 * stores it (BEFORE sending), `$send(to, subject, body, headers)` is wp_mail.
 */
function molosoc_la_alert( int $order_id, string $reason, callable $get, callable $set, callable $send ): string {
	if ( '' !== (string) $get() ) {
		return 'alert_already_sent';
	}
	$m = molosoc_la_alert_message( $order_id, $reason );
	$set( $reason );
	if ( MOLOSOC_LD_CC !== $m['to'] ) {
		return 'alert_recipient_mismatch';
	}
	$ok = (bool) $send( $m['to'], $m['subject'], $m['body'], array( 'Content-Type: text/plain; charset=UTF-8' ) );
	return $ok ? 'alert_sent' : 'alert_failed';
}

/**
 * Settles an uncertain `mailing` state under the shared delivery lock, BEFORE any
 * eligibility check (Codex #372): if the order is still `mailing` once the lock is held, the
 * mail may or may not have left, so it goes to `attention` (`mail_state_unknown`) and is
 * never resent, whatever the order's WooCommerce status is now. Uses the Phase 3 I/O keys
 * lock(), unlock(), state(), set_state($s), audit($row). Returns `locked`,
 * `mail_state_unknown`, or `recheck_<state>` when another run already moved the order on.
 */
function molosoc_la_resolve_mailing( int $order_id, array $io ): string {
	if ( ! $io['lock']() ) {
		return 'locked';
	}
	try {
		$state = (string) $io['state']();
		if ( 'mailing' !== $state ) {
			return 'recheck_' . ( '' === $state ? 'none' : $state );
		}
		$io['set_state']( 'attention' );
		$io['audit']( array( 'order' => $order_id, 'result' => 'attention', 'reason' => 'mail_state_unknown' ) );
		return 'mail_state_unknown';
	} finally {
		$io['unlock']();
	}
}

/**
 * One queued run for one order. Returns array( string result, int retry_delay ) where a
 * delay > 0 means "run again later". Injected I/O:
 *   now(), state(), seen() / set_seen($ts), snapshot(), packeta_row(), configured(),
 *   deliver() -> array( result, detail )   (molosoc_ld3_process with the live provider/mailer)
 *   resolve_mailing() -> string            (molosoc_la_resolve_mailing under the delivery lock)
 *   tries(), attention($reason)            (sets state `attention` + audit row)
 *   alert($reason), audit($row)
 */
function molosoc_la_step( int $order_id, array $io ): array {
	$state = (string) $io['state']();
	if ( 'mailed' === $state ) {
		return array( 'already_mailed', 0 );
	}
	if ( 'attention' === $state ) {
		return array( 'needs_attention', 0 );
	}
	$now  = (int) $io['now']();
	$seen = (int) $io['seen']();
	if ( $seen <= 0 ) {
		$seen = $now;
		$io['set_seen']( $now );
	}

	if ( 'mailing' === $state ) {
		// Codex #372: settle the uncertain mail state under the delivery lock BEFORE any
		// eligibility check, so an order whose status has since changed (completed,
		// cancelled) still reaches `attention` + one alert. Never resends.
		$resolved = (string) $io['resolve_mailing']();
		if ( 'mail_state_unknown' === $resolved ) {
			$io['alert']( 'mail_state_unknown' );
			return array( 'mail_state_unknown', 0 );
		}
		if ( 'locked' === $resolved ) {
			return array( 'locked', MOLOSOC_LA_RETRY_DELAY ); // Stale locks are taken over after the TTL.
		}
		// Another run changed the state while we waited for the lock: re-read and go on.
		$state = (string) $io['state']();
		if ( 'mailed' === $state ) {
			return array( 'already_mailed', 0 );
		}
		if ( 'attention' === $state ) {
			return array( 'needs_attention', 0 );
		}
		if ( 'mailing' === $state ) {
			return array( 'locked', MOLOSOC_LA_RETRY_DELAY ); // Defensive: never deliver from `mailing`.
		}
	}

	$snap   = $io['snapshot']();
	$is_zas = 'Zásilkovna' === ( $snap['carrier'] ?? '' );
	[ $action, $reason ] = molosoc_la_plan(
		$snap,
		$state,
		$is_zas ? $io['packeta_row']() : null,
		$is_zas ? (bool) $io['configured']() : false
	);

	if ( 'skip' === $action ) {
		$io['audit']( array( 'order' => $order_id, 'result' => 'skipped', 'reason' => $reason ) );
		return array( $reason, 0 );
	}
	if ( 'wait' === $action ) {
		if ( $now - $seen >= MOLOSOC_LA_WAIT_MAX ) {
			$io['attention']( 'packet_wait_timeout' );
			$io['alert']( 'packet_wait_timeout' );
			return array( 'packet_wait_timeout', 0 );
		}
		if ( $now === $seen ) {
			$io['audit']( array( 'order' => $order_id, 'result' => 'waiting', 'reason' => $reason ) ); // Once, not every 15 min.
		}
		return array( 'waiting_for_packet', MOLOSOC_LA_WAIT_INTERVAL );
	}
	if ( 'attention' === $action ) {
		$io['attention']( $reason );
		$io['alert']( $reason );
		return array( $reason, 0 );
	}
	if ( 'send' !== $action ) {
		return array( $reason, 0 );
	}

	[ $result, $detail ] = $io['deliver']();
	$result = (string) $result;
	if ( 'exception' === $result ) {
		// The state machine caught a throw and returned it as a result (Codex #372).
		$after = (string) $io['state']();
		if ( 'mailing' === $after ) {
			// The throw came after `mailing` was written: the mail may have gone. Never resend.
			$io['attention']( 'mail_state_unknown' );
			$io['alert']( 'mail_state_unknown' );
			return array( 'mail_state_unknown', 0 );
		}
		if ( 'attention' !== $after && molosoc_la_exception_retry( $seen, $now ) ) {
			return array( 'exception', MOLOSOC_LA_RETRY_DELAY ); // Bounded by the wait window from first sight.
		}
		if ( 'attention' !== $after ) {
			$io['attention']( 'exception' );
		}
		$io['alert']( 'exception' );
		return array( 'exception', 0 );
	}
	$tries  = (int) $io['tries']();
	if ( molosoc_ll_exhausted( $result, $tries ) ) {
		$io['attention']( 'max_tries' );
		$io['alert']( 'max_tries' );
		return array( 'max_tries', 0 );
	}
	if ( 'locked' === $result || molosoc_ll_should_retry( $result, $tries ) ) {
		return array( $result, MOLOSOC_LA_RETRY_DELAY );
	}
	if ( 'attention' === (string) $io['state']() ) {
		$io['alert']( '' !== (string) $detail ? (string) $detail : $result );
	}
	return array( $result, 0 );
}

/**
 * Pure stale-lock decision: a lock stamped `$observed` may be taken over only when it is
 * older than MOLOSOC_LA_LOCK_TTL (the request holding it died).
 */
function molosoc_la_lock_stale( $observed, int $now ): bool {
	return false !== $observed && null !== $observed && $now - (int) $observed > MOLOSOC_LA_LOCK_TTL;
}

/**
 * Pure recovery decision for the sweep (Codex #372): a previously seen order whose run chain
 * was lost (e.g. the request died after `set_seen()`, mid-mail or while waiting) is queued
 * again so the state machine can resume it or turn an uncertain `mailing` into `attention`
 * with one alert (never a resend). Only when automation never finished it (no done marker),
 * it is not `mailed`/`attention`, no run is pending, no live worker holds its lock, and it was
 * first seen longer ago than the lock TTL (so a first run in flight is not raced).
 */
function molosoc_la_recoverable( string $state, int $seen, string $done, bool $pending, bool $locked, int $now ): bool {
	return $seen > 0
		&& '' === $done
		&& ! in_array( $state, array( 'mailed', 'attention' ), true )
		&& ! $pending
		&& ! $locked
		&& $now - $seen > MOLOSOC_LA_LOCK_TTL;
}

/** Pure: retry after an exception only inside the wait window counted from first sight. */
function molosoc_la_exception_retry( int $seen, int $now ): bool {
	return $seen > 0 && $now - $seen < MOLOSOC_LA_WAIT_MAX;
}

/* ---------------------------------------------------------------- WP glue */

function molosoc_la_gate_now(): array {
	return molosoc_la_gate(
		defined( 'MOLOSOC_LABEL_AUTO_ENABLED' ) ? MOLOSOC_LABEL_AUTO_ENABLED : null,
		defined( 'MOLOSOC_LABEL_LIVE_ENABLED' ) && true === MOLOSOC_LABEL_LIVE_ENABLED,
		defined( 'MOLOSOC_LABEL_DELIVERY_ENABLED' ) && true === MOLOSOC_LABEL_DELIVERY_ENABLED,
		defined( 'MOLOSOC_LABEL_DISPATCH_SINCE' ),
		defined( 'MOLOSOC_LABEL_DISPATCH_SINCE' ) ? MOLOSOC_LABEL_DISPATCH_SINCE : null
	);
}

/**
 * Read-only lookup of Packeta 2.3.2's own row for the order: packet_id, carrier_id,
 * packet_status from `{prefix}packetery_order`. Null when the table or row is missing.
 */
function molosoc_la_packeta_row( int $order_id ): ?array {
	global $wpdb;
	if ( $order_id <= 0 || ! isset( $wpdb ) || ! is_object( $wpdb ) ) {
		return null;
	}
	$table = $wpdb->prefix . 'packetery_order';
	if ( $table !== $wpdb->get_var( $wpdb->prepare( 'SHOW TABLES LIKE %s', $wpdb->esc_like( $table ) ) ) ) {
		return null;
	}
	$row = $wpdb->get_row(
		$wpdb->prepare( 'SELECT `packet_id`, `carrier_id`, `packet_status` FROM `' . $table . '` WHERE `id` = %d LIMIT 1', $order_id ),
		defined( 'ARRAY_A' ) ? ARRAY_A : 'ARRAY_A'
	);
	return is_array( $row ) ? $row : null;
}

/**
 * Option-based lock: add_option is a unique-key insert, so only one request wins. A stale
 * lock (older than MOLOSOC_LA_LOCK_TTL) is taken over with a compare-and-swap on the
 * observed value, so two contenders can never both win.
 */
function molosoc_la_lock( string $key ): bool {
	if ( add_option( $key, time(), '', 'no' ) ) {
		return true;
	}
	global $wpdb;
	wp_cache_delete( $key, 'options' );
	wp_cache_delete( 'notoptions', 'options' );
	wp_cache_delete( 'alloptions', 'options' );
	$observed = get_option( $key, false );
	if ( ! molosoc_la_lock_stale( $observed, time() ) ) {
		return false;
	}
	$swapped = $wpdb->update(
		$wpdb->options,
		array( 'option_value' => (string) time() ),
		array(
			'option_name'  => $key,
			'option_value' => (string) $observed,
		)
	);
	wp_cache_delete( $key, 'options' );
	wp_cache_delete( 'alloptions', 'options' );
	return 1 === (int) $swapped;
}

/** True while a live (not stale) worker lock exists. Read-only. */
function molosoc_la_lock_held( string $key ): bool {
	$observed = get_option( $key, false );
	return false !== $observed && ! molosoc_la_lock_stale( $observed, time() );
}

function molosoc_la_log( string $level, string $msg ): void {
	if ( function_exists( 'wc_get_logger' ) ) {
		wc_get_logger()->log( $level, $msg, array( 'source' => MOLOSOC_LA_LOG_SOURCE ) );
	}
}

/** True when a pending (not running) queued run exists for the order. */
function molosoc_la_pending( int $order_id ): bool {
	if ( function_exists( 'as_get_scheduled_actions' ) ) {
		return (bool) as_get_scheduled_actions(
			array(
				'hook'     => MOLOSOC_LA_HOOK,
				'args'     => array( $order_id ),
				'group'    => MOLOSOC_LA_GROUP,
				'status'   => 'pending',
				'per_page' => 1,
			),
			'ids'
		);
	}
	return (bool) wp_next_scheduled( MOLOSOC_LA_HOOK, array( $order_id ) );
}

/** Queues one run (Action Scheduler when available, WP-Cron otherwise); never duplicates a pending one. */
function molosoc_la_schedule( int $order_id, int $delay ): void {
	if ( $order_id <= 0 || molosoc_la_pending( $order_id ) ) {
		return;
	}
	if ( function_exists( 'as_schedule_single_action' ) ) {
		as_schedule_single_action( time() + max( 0, $delay ), MOLOSOC_LA_HOOK, array( $order_id ), MOLOSOC_LA_GROUP );
	} elseif ( function_exists( 'wp_schedule_single_event' ) ) {
		wp_schedule_single_event( time() + max( 0, $delay ), MOLOSOC_LA_HOOK, array( $order_id ) );
	}
}

/** `woocommerce_order_status_processing`: queue only, never process inline. */
function molosoc_la_on_processing( $order_id ): void {
	[ $ok ] = molosoc_la_gate_now();
	if ( $ok ) {
		molosoc_la_schedule( (int) $order_id, MOLOSOC_LA_FIRST_DELAY );
	}
}

/** Queued worker. Also the operator entry point: `wp eval 'echo molosoc_la_worker( N );'`. */
function molosoc_la_worker( $order_id ): string {
	$order_id = (int) $order_id;
	[ $ok, $reason ] = molosoc_la_gate_now();
	if ( ! $ok || $order_id <= 0 ) {
		return $ok ? 'invalid_order' : $reason; // Disabled: pending runs do nothing.
	}
	$outer = 'molosoc_la_lock_' . $order_id;
	if ( ! molosoc_la_lock( $outer ) ) {
		molosoc_la_schedule( $order_id, MOLOSOC_LA_RETRY_DELAY );
		return 'locked';
	}
	try {
		$meta_get = static function ( string $key ) use ( $order_id ): string {
			return molosoc_ld3_meta_get( $order_id, $key );
		};
		$audit    = static function ( array $row ) use ( $order_id ) {
			$order = wc_get_order( $order_id );
			if ( $order ) {
				$order->add_meta_data( MOLOSOC_LD_AUDIT_META, wp_json_encode( array_merge( array( 'ts' => gmdate( 'c' ), 'stage' => 'auto' ), $row ) ), false );
				$order->save_meta_data();
			}
		};
		$detail   = '';
		[ $result, $delay ] = molosoc_la_step(
			$order_id,
			array(
				'now'         => 'time',
				'state'       => static function () use ( $meta_get ) {
					return $meta_get( MOLOSOC_LD3_STATE_META );
				},
				'seen'        => static function () use ( $meta_get ) {
					return (int) $meta_get( MOLOSOC_LA_SEEN_META );
				},
				'set_seen'    => static function ( $ts ) use ( $order_id ) {
					molosoc_ld3_meta_set( $order_id, MOLOSOC_LA_SEEN_META, (string) (int) $ts );
				},
				'snapshot'    => static function () use ( $order_id ) {
					return molosoc_ld3_snapshot( $order_id );
				},
				'packeta_row' => static function () use ( $order_id ) {
					return molosoc_la_packeta_row( $order_id );
				},
				'configured'  => static function () {
					return '' !== molosoc_ll_packeta_password_now();
				},
				'resolve_mailing' => static function () use ( $order_id ) {
					// Same inner lock key as the state machine, so the two never race.
					$inner = 'molosoc_ll_lock_' . $order_id;
					return molosoc_la_resolve_mailing(
						$order_id,
						molosoc_ll_io(
							$order_id,
							'auto',
							$inner,
							static function () use ( $inner ) {
								return molosoc_la_lock( $inner );
							},
							static function () {
								return array( 'ok' => false, 'live' => false, 'reason' => 'not_used' ); // Never fetches.
							}
						)
					);
				},
				'deliver'     => static function () use ( $order_id, &$detail ) {
					// Same inner lock key as the single-order live path, with stale takeover.
					$inner = 'molosoc_ll_lock_' . $order_id;
					$res   = molosoc_ld3_process(
						$order_id,
						molosoc_ll_io(
							$order_id,
							'auto',
							$inner,
							static function () use ( $inner ) {
								return molosoc_la_lock( $inner );
							},
							static function ( $carrier, $ref ) use ( $order_id, &$detail ) {
								$r = molosoc_la_provider(
									(string) $carrier,
									(string) $ref,
									array(
										'row'          => molosoc_la_packeta_row( $order_id ),
										'api_password' => molosoc_ll_packeta_password_now(),
										'fetch'        => 'molosoc_ll_packeta_fetch',
									)
								);
								$detail = (string) ( $r['reason'] ?? '' );
								return $r;
							}
						)
					);
					return array( $res, 'provider_permanent' === $res ? $detail : '' );
				},
				'tries'       => static function () use ( $meta_get ) {
					return (int) $meta_get( MOLOSOC_LD3_TRY_META );
				},
				'attention'   => static function ( $why ) use ( $order_id, $audit ) {
					molosoc_ld3_meta_set( $order_id, MOLOSOC_LD3_STATE_META, 'attention' );
					$audit( array( 'order' => $order_id, 'result' => 'attention', 'reason' => (string) $why ) );
				},
				'alert'       => static function ( $why ) use ( $order_id, $meta_get, $audit ) {
					$r = molosoc_la_alert(
						$order_id,
						(string) $why,
						static function () use ( $meta_get ) {
							return $meta_get( MOLOSOC_LA_ALERT_META );
						},
						static function ( $v ) use ( $order_id ) {
							molosoc_ld3_meta_set( $order_id, MOLOSOC_LA_ALERT_META, (string) $v );
						},
						'wp_mail'
					);
					$audit( array( 'order' => $order_id, 'result' => $r, 'reason' => (string) $why ) );
					molosoc_la_log( 'alert_sent' === $r ? 'warning' : 'error', sprintf( 'order %d: %s (%s)', $order_id, $r, (string) $why ) );
				},
				'audit'       => $audit,
			)
		);
	} catch ( \Throwable $e ) {
		molosoc_la_log( 'error', sprintf( 'order %d: exception %s', $order_id, get_class( $e ) ) );
		$result = 'exception';
		// Retry, but never beyond the wait window: a persistent error must not loop forever.
		$seen  = (int) molosoc_ld3_meta_get( $order_id, MOLOSOC_LA_SEEN_META );
		$delay = molosoc_la_exception_retry( $seen, time() ) ? MOLOSOC_LA_RETRY_DELAY : 0;
	} finally {
		delete_option( $outer );
	}
	molosoc_la_log( 'info', sprintf( 'order %d: %s', $order_id, $result ) );
	if ( $delay > 0 ) {
		molosoc_la_schedule( $order_id, $delay );
	} else {
		// No follow-up: the sweep's recovery pass must not pick this order up again.
		molosoc_ld3_meta_set( $order_id, MOLOSOC_LA_DONE_META, (string) time() );
	}
	return $result;
}

/**
 * Pure sweep loop. `$page($n)` returns the ids of page `$n` (page size MOLOSOC_LA_SWEEP_LIMIT),
 * `$eligible($id)` says whether the order still needs queueing, `$queue($id)` queues it.
 * Pages past already-handled orders, so they can never hide a newer missed order (Codex #372),
 * while queueing at most MOLOSOC_LA_SWEEP_LIMIT orders and reading at most
 * MOLOSOC_LA_SWEEP_MAX_PAGES pages per run.
 */
function molosoc_la_sweep_collect( callable $page, callable $eligible, callable $queue, int $limit = MOLOSOC_LA_SWEEP_LIMIT ): int {
	$n = 0;
	if ( $limit <= 0 ) {
		return 0;
	}
	for ( $p = 1; $p <= MOLOSOC_LA_SWEEP_MAX_PAGES; $p++ ) {
		$ids = array_values( (array) $page( $p ) );
		foreach ( $ids as $id ) {
			$id = (int) $id;
			if ( $id > 0 && $eligible( $id ) ) {
				$queue( $id );
				if ( ++$n >= $limit ) {
					return $n;
				}
			}
		}
		if ( count( $ids ) < MOLOSOC_LA_SWEEP_LIMIT ) {
			break;
		}
	}
	return $n;
}

/**
 * Safety net, two passes sharing one budget of MOLOSOC_LA_SWEEP_LIMIT queued orders:
 *   1. recent `processing` orders created after the cut-off that this automation has never
 *      seen (e.g. a lost queue entry); the query skips orders carrying the seen marker;
 *   2. recovery (Codex #372): orders created after the cut-off that were seen but never
 *      finished (no done marker) and lost their pending run, see molosoc_la_recoverable().
 * Reads only, apart from queueing; the pure loop above pages past already-handled orders.
 */
function molosoc_la_sweep(): int {
	[ $ok ] = molosoc_la_gate_now();
	if ( ! $ok || ! function_exists( 'wc_get_orders' ) ) {
		return 0;
	}
	$since = molosoc_ld_since_ts( true, MOLOSOC_LABEL_DISPATCH_SINCE, null );
	$query = static function ( array $extra, array $meta_query ) use ( $since ): callable {
		return static function ( int $p ) use ( $since, $extra, $meta_query ) {
			return wc_get_orders(
				array_merge(
					array(
						'date_created' => '>=' . $since,
						'meta_query'   => $meta_query, // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_query
						'limit'        => MOLOSOC_LA_SWEEP_LIMIT,
						'paged'        => $p,
						'orderby'      => 'date',
						'order'        => 'ASC',
						'return'       => 'ids',
					),
					$extra
				)
			);
		};
	};
	$queue = static function ( int $id ) {
		molosoc_la_schedule( $id, 0 );
	};
	$n = molosoc_la_sweep_collect(
		$query(
			array( 'status' => array( 'processing' ) ),
			array(
				array(
					'key'     => MOLOSOC_LA_SEEN_META,
					'compare' => 'NOT EXISTS',
				),
			)
		),
		static function ( int $id ): bool {
			return '' === molosoc_ld3_meta_get( $id, MOLOSOC_LA_SEEN_META )
				&& '' === molosoc_ld3_meta_get( $id, MOLOSOC_LD3_STATE_META )
				&& ! molosoc_la_pending( $id );
		},
		$queue
	);
	// Any status: a run lost mid-mail must still reach `attention` + alert after a status change.
	return $n + molosoc_la_sweep_collect(
		$query(
			array( 'status' => 'any' ),
			array(
				'relation' => 'AND',
				array(
					'key'     => MOLOSOC_LA_SEEN_META,
					'compare' => 'EXISTS',
				),
				array(
					'key'     => MOLOSOC_LA_DONE_META,
					'compare' => 'NOT EXISTS',
				),
			)
		),
		static function ( int $id ): bool {
			return molosoc_la_recoverable(
				molosoc_ld3_meta_get( $id, MOLOSOC_LD3_STATE_META ),
				(int) molosoc_ld3_meta_get( $id, MOLOSOC_LA_SEEN_META ),
				molosoc_ld3_meta_get( $id, MOLOSOC_LA_DONE_META ),
				molosoc_la_pending( $id ),
				molosoc_la_lock_held( 'molosoc_la_lock_' . $id ),
				time()
			);
		},
		$queue,
		MOLOSOC_LA_SWEEP_LIMIT - $n
	);
}

function molosoc_la_ensure_sweep(): void {
	if ( function_exists( 'as_has_scheduled_action' ) && function_exists( 'as_schedule_recurring_action' ) ) {
		if ( ! as_has_scheduled_action( MOLOSOC_LA_SWEEP_HOOK, array(), MOLOSOC_LA_GROUP ) ) {
			as_schedule_recurring_action( time() + 60, MOLOSOC_LA_SWEEP_INTERVAL, MOLOSOC_LA_SWEEP_HOOK, array(), MOLOSOC_LA_GROUP );
		}
	} elseif ( function_exists( 'wp_next_scheduled' ) && ! wp_next_scheduled( MOLOSOC_LA_SWEEP_HOOK ) ) {
		wp_schedule_event( time() + 60, 'hourly', MOLOSOC_LA_SWEEP_HOOK );
	}
}

/* ------------------------------------------------------ read-only status page */

function molosoc_la_page_enabled(): bool {
	return ( defined( 'MOLOSOC_LABEL_AUTO_PREVIEW' ) && true === MOLOSOC_LABEL_AUTO_PREVIEW )
		|| ( defined( 'MOLOSOC_LABEL_AUTO_ENABLED' ) && true === MOLOSOC_LABEL_AUTO_ENABLED );
}

/**
 * Pure summary of Packeta's own auto-submission setting (option `packetery_auto_submission`):
 * whether it is allowed and which event it uses for COD and Comgate. Strings only.
 */
function molosoc_la_packeta_autosubmit_summary( $opt ): array {
	$opt    = is_array( $opt ) ? $opt : array();
	$events = is_array( $opt['payment_method_events'] ?? null ) ? $opt['payment_method_events'] : array();
	$pick   = static function ( array $ids ) use ( $events ): string {
		foreach ( $ids as $id ) {
			if ( isset( $events[ $id ] ) && is_string( $events[ $id ] ) && '' !== $events[ $id ] ) {
				return $events[ $id ];
			}
		}
		return '-';
	};
	return array(
		'allow'   => ! empty( $opt['allow'] ) ? 'ano' : 'ne',
		'cod'     => $pick( array( 'cod' ) ),
		'comgate' => $pick( array( 'wf-woo-comgate', 'wf_woo_comgate' ) ),
	);
}

function molosoc_la_render_page(): void {
	if ( ! current_user_can( MOLOSOC_LA_CAP ) ) {
		wp_die( esc_html__( 'Nedostatečná oprávnění.' ) );
	}
	[ $ok, $gate ] = molosoc_la_gate_now();
	$since_def     = defined( 'MOLOSOC_LABEL_DISPATCH_SINCE' );
	$since         = $since_def ? molosoc_ld_since_ts( true, MOLOSOC_LABEL_DISPATCH_SINCE, null ) : 0;
	$configured    = '' !== molosoc_ll_packeta_password_now();
	$as            = molosoc_la_packeta_autosubmit_summary( get_option( 'packetery_auto_submission', null ) );
	$query         = array(
		'status'  => array( 'processing', 'completed', 'on-hold' ),
		'limit'   => 30,
		'orderby' => 'date',
		'order'   => 'DESC',
		'return'  => 'ids',
	);
	if ( $since > 0 ) {
		$query['date_created'] = '>=' . $since;
	}
	$ids = function_exists( 'wc_get_orders' ) ? (array) wc_get_orders( $query ) : array();

	echo '<div class="wrap"><h1>MOLOSOC štítky – automat (jen pro čtení)</h1>';
	echo '<p>Tato stránka nic neposílá, nestahuje štítky a nic nezapisuje.</p><table class="widefat striped" style="max-width:720px"><tbody>';
	$cfg = array(
		'Automat (MOLOSOC_LABEL_AUTO_ENABLED)' => $ok ? 'ZAPNUTO' : 'vypnuto (' . $gate . ')',
		'Cut-off (MOLOSOC_LABEL_DISPATCH_SINCE)' => $since > 0 ? gmdate( 'c', $since ) : ( $since_def ? 'neplatné' : 'nenastaveno' ),
		'API heslo Packety'                    => $configured ? 'k dispozici' : 'CHYBÍ',
		'Packeta auto-podání povoleno'         => $as['allow'],
		'Packeta auto-podání: dobírka'         => $as['cod'],
		'Packeta auto-podání: Comgate'         => $as['comgate'],
		'Příjemce / kopie'                     => MOLOSOC_LD_RECIPIENT . ' / ' . MOLOSOC_LD_CC,
		'Upozornění chyb'                      => MOLOSOC_LD_CC,
	);
	foreach ( $cfg as $k => $v ) {
		echo '<tr><th>' . esc_html( $k ) . '</th><td><code>' . esc_html( (string) $v ) . '</code></td></tr>';
	}
	echo '</tbody></table><h2>Objednávky' . ( $since > 0 ? ' od cut-off' : ' (cut-off chybí: posledních 30)' ) . '</h2>';
	echo '<table class="widefat striped"><thead><tr><th>Objednávka</th><th>Stav</th><th>Platba</th><th>Dopravce</th><th>Packeta dopravce</th><th>Zásilka</th><th>Stav zásilky</th><th>Stav štítku</th><th>Automat udělá</th><th>Upozornění</th></tr></thead><tbody>';
	foreach ( $ids as $id ) {
		$id    = (int) $id;
		$snap  = molosoc_ld3_snapshot( $id );
		$state = molosoc_ld3_meta_get( $id, MOLOSOC_LD3_STATE_META );
		$row   = 'Zásilkovna' === ( $snap['carrier'] ?? '' ) ? molosoc_la_packeta_row( $id ) : null;
		[ $action, $why ] = molosoc_la_plan( $snap, $state, $row, $configured );
		$cid   = is_array( $row ) ? trim( (string) ( $row['carrier_id'] ?? '' ) ) : '';
		$pid   = is_array( $row ) ? trim( (string) ( $row['packet_id'] ?? '' ) ) : '';
		$alert = molosoc_ld3_meta_get( $id, MOLOSOC_LA_ALERT_META );
		$alert = '' === $alert ? '-' : $alert;
		$cells = array(
			'#' . $id,
			(string) ( $snap['status'] ?? '' ),
			(string) ( $snap['payment_method'] ?? '' ),
			(string) ( $snap['carrier'] ?? '-' ),
			'' === $cid ? '-' : ( is_numeric( $cid ) ? 'externí (' . $cid . ')' : 'interní (' . $cid . ')' ),
			molosoc_ll_packet_id_valid( $pid ) ? $pid : ( '' === $pid ? '-' : 'neplatné' ),
			is_array( $row ) ? (string) ( $row['packet_status'] ?? '' ) : '-',
			'' === $state ? '-' : $state,
			$action . ': ' . $why,
			$alert,
		);
		echo '<tr>';
		foreach ( $cells as $c ) {
			echo '<td>' . esc_html( $c ) . '</td>';
		}
		echo '</tr>';
	}
	echo '</tbody></table></div>';
}

/* ------------------------------------------------------------------- hooks */

if ( molosoc_la_page_enabled() ) { // True only with MOLOSOC_LABEL_AUTO_PREVIEW or MOLOSOC_LABEL_AUTO_ENABLED.
	add_action(
		'muplugins_loaded',
		static function () {
			// MU plugins load alphabetically; the pipeline core lives in later files.
			foreach ( array( 'molosoc_ld_decide', 'molosoc_ld3_process', 'molosoc_ll_io', 'molosoc_ll_provider' ) as $fn ) {
				if ( ! function_exists( $fn ) ) {
					return;
				}
			}
			add_action(
				'admin_menu',
				static function () {
					add_management_page( 'MOLOSOC štítky – automat', 'MOLOSOC štítky – automat', MOLOSOC_LA_CAP, MOLOSOC_LA_PAGE, 'molosoc_la_render_page' );
				}
			);
			[ $ok ] = molosoc_la_gate_now();
			if ( ! $ok ) {
				return;
			}
			add_action( 'woocommerce_order_status_processing', 'molosoc_la_on_processing', 50, 1 );
			add_action( MOLOSOC_LA_HOOK, 'molosoc_la_worker', 10, 1 );
			add_action( MOLOSOC_LA_SWEEP_HOOK, 'molosoc_la_sweep', 10, 0 );
			add_action( 'init', 'molosoc_la_ensure_sweep', 20, 0 );
		}
	);
}
