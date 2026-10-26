<?php
/**
 * Checkout cleanup (GitHub Issue #267) — CZ payment-method labels, Czech
 * text for the CusRev review-invitation checkbox, smaller Comgate logo.
 * Kept in its own file so inc/woocommerce-lang.php stays untouched.
 *
 * Display only: no gateway is disabled or reordered, no fee/price/option is
 * changed, no plugin file is edited, and CusRev consent/reminders are not
 * touched. Relies on Polylang's pll_current_language() ('cz'|'en').
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * CZ display titles for the three checkout payment methods, so each reads
 * as its own distinct option. Display text only: no gateway is enabled,
 * disabled or reordered, and no fee, price or stored setting is touched
 * or written. COD ("Dobírka") already reads correctly and is left as is.
 *
 * Gate: explicit 'cz' only, same as every CZ hook above — a falsy or
 * unresolved language (wp-admin, REST, cron) and 'en' return the title
 * untouched, so molosoc_en_gateway_title() keeps sole ownership of 'en'.
 * JUDGMENT CALL: the live Comgate gateway ID is not verifiable from this
 * repo, so it is matched on the substring 'comgate' (the plugin is
 * `wf-woo-comgate`); an unmatched gateway keeps the title it was built with.
 */
function molosoc_cz_gateway_title( $title, $gateway_id = '' ) {
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return $title;
	}
	$id = strtolower( (string) $gateway_id );
	if ( false !== strpos( $id, 'comgate' ) ) {
		return 'Platba kartou (Comgate)';
	}
	if ( 'bacs' === $id ) {
		return 'Bankovní převod (platba předem)';
	}
	return $title;
}
add_filter( 'woocommerce_gateway_title', 'molosoc_cz_gateway_title', 10, 2 );

/**
 * Czech text for the "Customer Reviews for WooCommerce" (CusRev) checkout
 * opt-in checkbox. The plugin's own English source string is matched on its
 * first sentence through the core `gettext` filter, in ANY text domain (the
 * live domain could not be verified from this repo), and ONLY on the Czech
 * checkout. The English checkout keeps the plugin's English text untouched.
 *
 * This changes wording only. Whether the box is checked, whether it is
 * shown, and whether CusRev sends invitations are plugin behaviour and are
 * deliberately not touched: consent still depends on the shopper ticking it
 * (it renders unchecked), and review reminders stay on.
 *
 * Limitation: if the text was customised in the plugin's own settings
 * (stored option, not a translatable string) this filter cannot see it.
 */
function molosoc_cz_cusrev_checkbox_text( $translation, $text, $domain = '' ) {
	if ( 0 !== strpos( (string) $text, 'Would you like to be invited to review your order' ) ) {
		return $translation;
	}
	if ( ! function_exists( 'is_checkout' ) || ! is_checkout() ) {
		return $translation;
	}
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return $translation;
	}
	return 'Chcete být pozváni k hodnocení objednávky? Zaškrtnutím obdržíte zprávu od CusRev (nezávislé služby recenzí) s formulářem hodnocení.';
}
add_filter( 'gettext', 'molosoc_cz_cusrev_checkbox_text', 10, 3 );

/**
 * Checkout-only stylesheet: shrinks the Comgate logo (the plugin ships a
 * very large PNG) to ~112px, responsive. Enqueued from here, and only on
 * is_checkout(), so no other page loads it; plugin files are not edited.
 */
function molosoc_enqueue_checkout_css() {
	if ( ! function_exists( 'is_checkout' ) || ! is_checkout() ) {
		return;
	}
	wp_enqueue_style(
		'molosoc-checkout',
		get_stylesheet_directory_uri() . '/assets/css/checkout.css',
		array( 'molosoc-components' ),
		wp_get_theme()->get( 'Version' )
	);
}
add_action( 'wp_enqueue_scripts', 'molosoc_enqueue_checkout_css', 20 );
