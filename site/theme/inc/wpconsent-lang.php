<?php
/**
 * WPConsent banner wording in the page language (Issue #314).
 *
 * The cookie banner is the WPConsent Lite plugin. Its message and button
 * labels are single admin-entered options (WPConsent → Settings → Banner →
 * Content) with no per-language values: per-language banner texts
 * ("Automatic Translations") are a WPConsent Pro feature, and the plugin does
 * not read Polylang. Clarity (30–31 Oct 2026) showed Czech visitors on
 * /cz/vanocni-darek-molosoc/ tapping around an English banner ("We use
 * cookies…", "Preferences", "Reject", "Accept All") before consenting or
 * leaving, while the plugin's own .po strings around it ("Souhlas se soubory
 * cookie", "Běží na") were already Czech.
 *
 * WPConsent_Settings::get_option() passes every option through the plugin's
 * own `wpconsent_get_option_{$option_name}` filter (in every release since
 * 1.0.4; the hook its Pro features use to override a base value), so this
 * file answers it with the Czech strings on Polylang 'cz' front-end requests
 * and leaves every other request — EN pages, wp-admin and its banner preview,
 * AJAX, REST, cron — with the admin values. Only four wording options are
 * touched; the consent logic, the categories and their defaults (nothing
 * pre-ticked), Reject's availability, the `wpconsent_preferences` cookie, the
 * `wpconsent_consent_saved` event, Meta pixel blocking and the Clarity replay
 * (functions.php) are the plugin's own and unchanged. The preferences modal
 * keeps its admin wording (its category names are WordPress terms).
 */

defined( 'ABSPATH' ) || exit;

/**
 * The Czech banner strings, keyed by WPConsent option name (Žaneta's copy, Issue #314).
 *
 * @return array<string,string>
 */
function molosoc_wpconsent_cz_strings() {
	return array(
		'banner_message'          => 'Používáme cookies, abychom vám web zlepšili a změřili, jak funguje naše reklama.',
		'accept_button_text'      => 'Přijmout vše',
		'cancel_button_text'      => 'Odmítnout',
		'preferences_button_text' => 'Nastavení',
	);
}

/**
 * True when the current request renders a Czech front-end page (Polylang 'cz').
 *
 * @return bool
 */
function molosoc_wpconsent_is_cz_request() {
	if ( is_admin() || wp_doing_ajax() || wp_doing_cron() || ( defined( 'REST_REQUEST' ) && REST_REQUEST ) ) {
		return false;
	}
	return function_exists( 'pll_current_language' ) && 'cz' === pll_current_language();
}

/**
 * wpconsent_get_option_{name}: the Czech string on CZ pages, the admin value everywhere else.
 *
 * @param mixed  $value       The option value as saved in wp-admin (or the plugin default).
 * @param string $option_name WPConsent option name.
 * @return mixed
 */
function molosoc_wpconsent_cz_option( $value, $option_name = '' ) {
	$strings = molosoc_wpconsent_cz_strings();
	if ( ! isset( $strings[ $option_name ] ) || ! molosoc_wpconsent_is_cz_request() ) {
		return $value;
	}
	return $strings[ $option_name ];
}

foreach ( array_keys( molosoc_wpconsent_cz_strings() ) as $molosoc_wpconsent_option ) {
	add_filter( 'wpconsent_get_option_' . $molosoc_wpconsent_option, 'molosoc_wpconsent_cz_option', 10, 2 );
}
unset( $molosoc_wpconsent_option );
