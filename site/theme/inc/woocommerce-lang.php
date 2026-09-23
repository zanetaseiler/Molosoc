<?php
/**
 * Bilingual WooCommerce purchase flow — CZ /cz/produkt → /cz/kosik →
 * /cz/pokladna, EN /product → /cart → /checkout — for ONE WooCommerce
 * product (ID 364, variations 424=L, 425=M), one inventory, one order
 * system. Implements zanetaseiler/Molosoc GitHub Issue #53.
 *
 * NO new plugin, NO Polylang-for-WooCommerce/WPML, NO duplicated product.
 * The `product` post type stays deliberately untranslatable in Polylang —
 * this file exists precisely because it is untranslatable: every hook here
 * is the theme's own language-context plumbing standing in for what a
 * translated post type would otherwise get from Polylang for free (a
 * second post, a translation group, `pll_get_post()`). Everywhere that
 * pattern doesn't apply, this file hardcodes the product ID (364) and the
 * two known URLs instead.
 *
 * Required once from functions.php. All functions are prefixed
 * `molosoc_` per the theme's existing convention.
 *
 * Section map (mirrors the issue's own numbering):
 *   1. Cart/checkout Czech twins — woocommerce_get_cart_page_id /
 *      woocommerce_get_checkout_page_id filters. The two CZ pages
 *      themselves (slugs kosik/pokladna) are NOT created by this file —
 *      see automations/content-sync/create_cart_checkout_cz_pages.py and
 *      .github/workflows/create-cart-checkout-cz-pages.yml, neither of
 *      which this PR runs (production write, needs separate approval).
 *   2. Czech product URL for the same product — rewrite rule, permalink
 *      filter, redirect guard, language-switcher link, hreflang/canonical.
 *   3. Requests that leave the URL context — wc-ajax endpoint prefixing,
 *      Store API `lang` query param via a small JS apiFetch middleware.
 *   4. Order language — `_molosoc_lang` order meta, CZ order-received URL,
 *      locale-switched customer emails for async (e.g. payment-gateway
 *      callback) request contexts.
 *   5. Presentation — Czech copy, size-selector labels/order, product-page
 *      price display, EN shipping/payment labels, billing_phone label.
 *      Every hook here is gated to product ID 364 specifically (or, for
 *      cart/order line items, to the line item that references product
 *      364) — never a blanket filter across the whole shop.
 */

defined( 'ABSPATH' ) || exit;

// The one product this whole file exists for. Used throughout instead of a
// magic number so every gate reads the same way.
if ( ! defined( 'MOLOSOC_PRODUCT_ID' ) ) {
	define( 'MOLOSOC_PRODUCT_ID', 364 );
}

// The two canonical product URLs. Hardcoded (not derived from get_permalink())
// because the CZ one doesn't exist as a WordPress-native permalink at all —
// it only exists via the rewrite rule registered below — and the EN one is
// the product's real, unfiltered permalink, which we don't want a filter
// loop to be even a theoretical risk for.
if ( ! defined( 'MOLOSOC_PRODUCT_URL_EN' ) ) {
	define( 'MOLOSOC_PRODUCT_URL_EN', home_url( '/product/moisture-lock-foot-cover/' ) );
}
if ( ! defined( 'MOLOSOC_PRODUCT_URL_CZ' ) ) {
	define( 'MOLOSOC_PRODUCT_URL_CZ', home_url( '/cz/produkt/hydratacni-navlek-na-nohy/' ) );
}

/**
 * Language-appropriate product URL. $lang defaults to the current Polylang
 * language; pass 'en'/'cz' explicitly to get either URL regardless of the
 * current request (used by the hreflang/canonical emitter below, which
 * always needs both).
 *
 * The 3 landing-page CTAs in page-moisture-lock-foot-cover.php call this
 * instead of hardcoding home_url('/product/moisture-lock-foot-cover/') —
 * that page is reachable in both languages (it's a translated Polylang
 * Page, unlike the product itself) and its "Order Now" buttons need to
 * land Czech visitors on the CZ product URL, not the EN one.
 */
function molosoc_product_url( $lang = null ) {
	if ( null === $lang ) {
		$lang = function_exists( 'pll_current_language' ) ? pll_current_language() : 'en';
	}
	return ( 'cz' === $lang ) ? MOLOSOC_PRODUCT_URL_CZ : MOLOSOC_PRODUCT_URL_EN;
}

/**
 * Shared gate used by every "product 364, current-request Czech" filter in
 * section 5: true only when Polylang resolves the current request to 'cz'
 * AND the post in question is product 364. Centralized so every Czech-copy
 * filter below reads identically and can never silently drift into a
 * blanket-across-the-shop condition.
 *
 * $post_id_or_null: pass the post ID a filter already received (e.g. the
 * `the_title` filter's second arg) when the hook gives one; some hooks
 * (woocommerce_short_description, the_content) don't pass an ID at all, so
 * this falls back to the current queried object on a product singular.
 */
function molosoc_is_cz_product_364( $post_id_or_null = null ) {
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return false;
	}
	if ( null !== $post_id_or_null && 0 !== (int) $post_id_or_null ) {
		return MOLOSOC_PRODUCT_ID === (int) $post_id_or_null;
	}
	return function_exists( 'is_product' ) && is_product() && MOLOSOC_PRODUCT_ID === (int) get_queried_object_id();
}

/* =====================================================================
 * 1. Cart/checkout Czech twins
 * =================================================================== */

/**
 * Resolve WooCommerce's cart/checkout page to its Czech Polylang
 * translation when one exists and is published — otherwise fall back to
 * WooCommerce's own configured page unchanged. WooCommerce's own option
 * values (woocommerce_cart_page_id / woocommerce_checkout_page_id) are
 * NEVER written to here; wc_get_page_id() already applies exactly these
 * two filter names to its stored option value, so this only changes what
 * gets returned at read time, for this request's language.
 *
 * Once the CZ twins (slugs kosik/pokladna, Polylang-linked to 359/360)
 * exist, wc_get_cart_url()/wc_get_checkout_url() — and therefore
 * is_cart()/is_checkout(), the header cart link (functions.php
 * molosoc_cart_link(), ~line 2079), and WooCommerce's own checkout
 * redirects — all resolve to the Czech pages automatically. Nothing about
 * those call sites needs to change.
 *
 * The CZ pages themselves are a production content change and are NOT
 * created by this PR — see
 * automations/content-sync/create_cart_checkout_cz_pages.py and
 * .github/workflows/create-cart-checkout-cz-pages.yml.
 */
function molosoc_cz_cart_checkout_page_id( $page_id ) {
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return $page_id;
	}
	if ( ! function_exists( 'pll_get_post' ) ) {
		return $page_id;
	}
	$cz_page_id = pll_get_post( $page_id, 'cz' );
	if ( $cz_page_id && 'publish' === get_post_status( $cz_page_id ) ) {
		return $cz_page_id;
	}
	return $page_id; // No published CZ twin yet — keep WooCommerce's own page.
}
add_filter( 'woocommerce_get_cart_page_id', 'molosoc_cz_cart_checkout_page_id' );
add_filter( 'woocommerce_get_checkout_page_id', 'molosoc_cz_cart_checkout_page_id' );

/* =====================================================================
 * 2. Czech product URL for the same (untranslated) product
 * =================================================================== */

/**
 * Rewrite CZ product URL -> the real product query. This is the only way
 * /cz/produkt/hydratacni-navlek-na-nohy/ resolves to product 364 at all,
 * since the `product` post type is deliberately NOT Polylang-translated
 * (keep it that way — see the file header). 'top' priority so this rule is
 * matched before WordPress's own generated product rewrite rules, which
 * would otherwise try (and fail) to parse "cz/produkt/..." as a language
 * archive or 404.
 *
 * flush_rewrite_rules() is expensive (rebuilds and re-saves the full
 * rewrite rule set) and must never run on every request — gated behind a
 * version-numbered option, the same "bump a version to force a one-time
 * action" idiom this theme already uses for cache-busting
 * ($theme_version / style.css's Version: header). Bump
 * MOLOSOC_REWRITE_VERSION (and the option check below) if this rule ever
 * needs to change.
 */
function molosoc_register_cz_product_rewrite() {
	add_rewrite_rule(
		'^cz/produkt/hydratacni-navlek-na-nohy/?$',
		'index.php?product=moisture-lock-foot-cover&lang=cz',
		'top'
	);

	if ( get_option( 'molosoc_rewrite_version' ) !== '1' ) {
		flush_rewrite_rules();
		update_option( 'molosoc_rewrite_version', '1' );
	}
}
add_action( 'init', 'molosoc_register_cz_product_rewrite', 20 );

/**
 * Make get_permalink( 364 ) (and therefore every WooCommerce/theme call
 * that builds the product's own link — breadcrumbs, related-product cards,
 * the add-to-cart redirect, etc.) return the CZ URL when the current
 * request is Czech. Only ever touches product 364; every other product
 * link (there are none on this store today, but future-proofing costs
 * nothing) is untouched.
 */
function molosoc_cz_product_permalink( $post_link, $post ) {
	if ( ! $post || 'product' !== $post->post_type || MOLOSOC_PRODUCT_ID !== (int) $post->ID ) {
		return $post_link;
	}
	if ( function_exists( 'pll_current_language' ) && 'cz' === pll_current_language() ) {
		return MOLOSOC_PRODUCT_URL_CZ;
	}
	return $post_link;
}
add_filter( 'post_type_link', 'molosoc_cz_product_permalink', 10, 2 );

/**
 * Stop WordPress core's own redirect_canonical() from 301ing the CZ
 * product URL away. redirect_canonical() runs on template_redirect and
 * compares the requested URL against what it thinks the canonical one is;
 * without the permalink filter above it would have redirected
 * /cz/produkt/... to /product/... (today's actual live behavior per the
 * issue's audit), and even WITH that filter in place it's cheaper and more
 * certain to explicitly short-circuit it for this one exact request than
 * to trust every core code path agrees with our filtered permalink.
 * Returning false from this filter is core's own documented way to skip
 * the redirect for a specific request.
 */
function molosoc_cz_product_no_canonical_redirect( $redirect_url, $requested_url ) {
	if ( function_exists( 'pll_current_language' )
		&& 'cz' === pll_current_language()
		&& function_exists( 'is_product' )
		&& is_product()
		&& MOLOSOC_PRODUCT_ID === (int) get_queried_object_id()
	) {
		return false;
	}
	return $redirect_url;
}
add_filter( 'redirect_canonical', 'molosoc_cz_product_no_canonical_redirect', 10, 2 );

/**
 * Suppress WordPress core's own <link rel="canonical"> for product 364
 * (rel_canonical(), hooked on wp_head, reads get_canonical_url()) so the
 * single canonical tag on this page is the one printed by
 * molosoc_product_canonical_hreflang() below — avoids two canonical tags
 * disagreeing (or duplicating) on the same page. Every other post/page is
 * untouched.
 */
function molosoc_suppress_core_product_canonical( $canonical_url, $post ) {
	if ( $post && 'product' === $post->post_type && MOLOSOC_PRODUCT_ID === (int) $post->ID ) {
		return '';
	}
	return $canonical_url;
}
add_filter( 'get_canonical_url', 'molosoc_suppress_core_product_canonical', 10, 2 );

/**
 * Self-canonical + en/cs hreflang pair for exactly the two product URLs.
 * Mirrors the existing x-default hreflang block's style (functions.php
 * ~132-153) — same wp_head-action, same printf-a-<link>-tag shape — but
 * keyed on the hardcoded product ID/URLs instead of pll_get_post(), since
 * product 364 is one untranslated post reachable at two URLs by rewrite,
 * not two Polylang-linked posts. Fires ONLY on the product-364 singular
 * (either URL/language), never elsewhere.
 */
function molosoc_product_canonical_hreflang() {
	if ( ! function_exists( 'is_product' ) || ! is_product() ) {
		return;
	}
	if ( MOLOSOC_PRODUCT_ID !== (int) get_queried_object_id() ) {
		return;
	}
	$current_lang = function_exists( 'pll_current_language' ) ? pll_current_language() : 'en';
	$self_url     = ( 'cz' === $current_lang ) ? MOLOSOC_PRODUCT_URL_CZ : MOLOSOC_PRODUCT_URL_EN;

	printf( '<link rel="canonical" href="%s" />' . "\n", esc_url( $self_url ) );
	printf( '<link rel="alternate" href="%s" hreflang="en" />' . "\n", esc_url( MOLOSOC_PRODUCT_URL_EN ) );
	printf( '<link rel="alternate" href="%s" hreflang="cs" />' . "\n", esc_url( MOLOSOC_PRODUCT_URL_CZ ) );
}
add_action( 'wp_head', 'molosoc_product_canonical_hreflang' );

/**
 * Polylang's language switcher (pll_the_language_link filter) falls back
 * to the homepage for any post type it doesn't translate — which includes
 * `product`, deliberately. On the product-364 singular specifically, map
 * the switcher link straight to the other language's product URL instead
 * of that homepage fallback.
 *
 * Polylang passes the already-assembled target URL as the first argument
 * and the target language's slug as the second — not a switcher data
 * array — so this reads/returns a plain URL string, not an array.
 */
function molosoc_product_language_switcher_link( $url, $slug ) {
	if ( ! function_exists( 'is_product' ) || ! is_product() || MOLOSOC_PRODUCT_ID !== (int) get_queried_object_id() ) {
		return $url;
	}
	if ( 'cz' === $slug ) {
		return MOLOSOC_PRODUCT_URL_CZ;
	}
	if ( 'en' === $slug ) {
		return MOLOSOC_PRODUCT_URL_EN;
	}
	return $url;
}
add_filter( 'pll_the_language_link', 'molosoc_product_language_switcher_link', 10, 2 );

/* =====================================================================
 * 3. Requests that leave the URL context (classic-checkout AJAX, Store API)
 * =================================================================== */

/**
 * Classic checkout (page 360, [woocommerce_checkout] shortcode) refreshes
 * order review / re-validates via admin-ajax-style wc-ajax requests, whose
 * default URL is always built off the *unprefixed* site root
 * (home_url('/', 'relative') + ?wc-ajax=...) regardless of which page the
 * shopper is actually on — so on the CZ checkout that request would
 * normally come back English. Prefix it with /cz/ when the current
 * request is Czech, matching WooCommerce's own default construction
 * (WC_AJAX::get_endpoint()) with a /cz/ base substituted in.
 *
 * Implemented defensively against the filter's exact call shape: WC passes
 * the already-built $url plus the raw $request as a second arg. If $url
 * doesn't carry a wc-ajax query var for some reason (a future WC version
 * changing the construction), fall back to reading $request directly
 * rather than guessing.
 */
function molosoc_cz_ajax_endpoint( $url, $request = '' ) {
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return $url;
	}

	$endpoint = $request;
	if ( '' === $endpoint || null === $endpoint ) {
		$parsed = wp_parse_url( (string) $url );
		$query  = array();
		if ( ! empty( $parsed['query'] ) ) {
			parse_str( $parsed['query'], $query );
		}
		$endpoint = isset( $query['wc-ajax'] ) ? $query['wc-ajax'] : '';
	}

	return home_url( '/cz/?wc-ajax=' . $endpoint );
}
add_filter( 'woocommerce_ajax_get_endpoint', 'molosoc_cz_ajax_endpoint', 10, 2 );

/**
 * Pass the current language to the JS middleware below via a plain global
 * (window.molosocLang) rather than wp_localize_script's forced object
 * wrapper, so the enqueue site (functions.php) can set exactly the
 * 'cz'|'en' string the issue calls for. See functions.php's enqueue
 * function for where this is set with wp_add_inline_script() and where
 * store-api-lang.js itself is conditionally enqueued (cart/checkout only).
 */

/* =====================================================================
 * 4. Order language
 * =================================================================== */

/**
 * Stamp the order with the language it was placed in, at the moment
 * checkout creates it — this is the one point in the whole flow that is
 * guaranteed to run inside the real shopper request (with the real /cz/
 * or unprefixed URL, so pll_current_language() is reliable), before any
 * async gateway callback or admin context might read the order later with
 * no language of its own. Everything else in this section (order-received
 * URL, customer-email locale) reads this meta back instead of re-deriving
 * language from whatever request happens to be running at send time.
 */
function molosoc_save_order_lang( $order, $data ) {
	$lang = ( function_exists( 'pll_current_language' ) && pll_current_language() ) ? pll_current_language() : 'en';
	$order->update_meta_data( '_molosoc_lang', $lang );
}
add_action( 'woocommerce_checkout_create_order', 'molosoc_save_order_lang', 10, 2 );

/**
 * Send a CZ order's "thank you" redirect to the Czech checkout twin's own
 * order-received endpoint instead of the EN one — reconstructed the same
 * way WC_Order::get_checkout_order_received_url() itself builds the URL
 * (wc_get_endpoint_url() off the checkout permalink, plus the order key
 * query arg), just with the CZ checkout page's permalink as the base. If
 * the CZ checkout twin doesn't exist/isn't published yet, falls back to
 * WooCommerce's own URL unchanged — never a broken link.
 */
function molosoc_cz_order_received_url( $url, $order ) {
	if ( ! $order instanceof WC_Order ) {
		return $url;
	}
	if ( 'cz' !== $order->get_meta( '_molosoc_lang' ) ) {
		return $url;
	}
	if ( ! function_exists( 'pll_get_post' ) || ! function_exists( 'wc_get_page_id' ) || ! function_exists( 'wc_get_endpoint_url' ) ) {
		return $url;
	}

	$cz_checkout_id = pll_get_post( wc_get_page_id( 'checkout' ), 'cz' );
	if ( ! $cz_checkout_id || 'publish' !== get_post_status( $cz_checkout_id ) ) {
		return $url; // CZ twin not published yet — keep WooCommerce's own URL.
	}

	$cz_checkout_url  = get_permalink( $cz_checkout_id );
	$cz_received_url  = wc_get_endpoint_url( 'order-received', $order->get_id(), $cz_checkout_url );
	return add_query_arg( 'key', $order->get_order_key(), $cz_received_url );
}
add_filter( 'woocommerce_get_checkout_order_received_url', 'molosoc_cz_order_received_url', 10, 2 );

/**
 * Read-only WooCommerce REST API field exposing an order's actual
 * get_checkout_order_received_url() — i.e. WooCommerce's own real computed
 * redirect target, built through molosoc_cz_order_received_url() above —
 * so scripts/test_bilingual_purchase_flow.py's credential-gated
 * real-order-received check can assert on what WooCommerce itself would
 * redirect/link a shopper to, instead of a URL the test script assembles
 * by hand and could get "right" by coincidence even if that filter
 * regressed. Gated to manage_woocommerce, the same capability already
 * required to create/read orders over this REST API at all, so this adds
 * no new exposure.
 */
function molosoc_register_order_received_url_rest_field() {
	register_rest_field(
		'shop_order',
		'order_received_url',
		array(
			'get_callback' => function ( $order_data ) {
				if ( ! current_user_can( 'manage_woocommerce' ) ) {
					return null;
				}
				$order = wc_get_order( $order_data['id'] );
				return $order ? $order->get_checkout_order_received_url() : null;
			},
			'schema'       => array(
				'description' => __( "The order's actual checkout order-received URL, after language routing.", 'molosoc' ),
				'type'        => 'string',
				'context'     => array( 'view', 'edit' ),
			),
		)
	);
}
add_action( 'rest_api_init', 'molosoc_register_order_received_url_rest_field' );

/**
 * Customer order emails triggered from a request with no /cz/ URL context
 * at all — a payment gateway's async return/callback (e.g. Comgate's
 * server-to-server notification) running as its own HTTP request, or a
 * cron/admin-triggered status change — have no language for
 * pll_current_language() to resolve; it comes back false there regardless
 * of which language the shopper actually checked out in. For a 'cz' order,
 * switch the site's active locale to cs_CZ for just the moment the
 * customer email is composed, so WooCommerce's own translated email
 * strings render in Czech, then restore whatever locale was active before.
 *
 * This does NOT change which emails get sent, how many, or to whom — only
 * the locale (and therefore string translations / date-number formatting)
 * used while WooCommerce composes and sends the customer-facing ones.
 *
 * Several of WooCommerce's own admin emails ("New order", "Cancelled
 * order", "Failed order") are, for a number of order-status transitions,
 * bound to the exact same `woocommerce_order_status_{from}_to_{to}_notification`
 * action as the matching customer email (e.g. both "New order" and
 * "Customer processing order" fire on
 * `..._pending_to_processing_notification`) — a blanket switch/restore
 * around that whole shared action would therefore also compose the admin
 * email in cs_CZ, which is never wanted (admin emails aren't customer-
 * facing and don't get this locale treatment). Exactly which hook names
 * collide is WooCommerce-email-class-internal, not reliably enumerable
 * from this sandbox, and has differed across WC versions before, so
 * rather than hardcode a hook/email allowlist, find wherever WooCommerce
 * itself already bound each `customer_*` email class's own `trigger`
 * callback and rewrap exactly that binding in place — any other callback
 * sharing the same hook (an admin email's own trigger, in particular) is
 * left completely untouched.
 */
function molosoc_order_from_notification_arg( $arg ) {
	// Most WooCommerce notification hooks pass a plain order ID; the
	// customer-note notification instead passes an args array containing
	// an 'order_id' key (WC_Email_Customer_Note::trigger()).
	if ( is_array( $arg ) && isset( $arg['order_id'] ) ) {
		$arg = $arg['order_id'];
	}
	return wc_get_order( $arg );
}
function molosoc_switch_locale_for_cz_order_email( $order_id ) {
	$order = molosoc_order_from_notification_arg( $order_id );
	if ( $order && 'cz' === $order->get_meta( '_molosoc_lang' ) ) {
		switch_to_locale( 'cs_CZ' );
	}
}
function molosoc_restore_locale_after_cz_order_email( $order_id ) {
	$order = molosoc_order_from_notification_arg( $order_id );
	if ( $order && 'cz' === $order->get_meta( '_molosoc_lang' ) ) {
		restore_current_locale();
	}
}
function molosoc_switch_locale_for_cz_resend_email( $order, $email_type ) {
	if ( 'customer_invoice' === $email_type && $order instanceof WC_Order && 'cz' === $order->get_meta( '_molosoc_lang' ) ) {
		switch_to_locale( 'cs_CZ' );
	}
}
function molosoc_restore_locale_after_cz_resend_email( $order, $email_type ) {
	if ( 'customer_invoice' === $email_type && $order instanceof WC_Order && 'cz' === $order->get_meta( '_molosoc_lang' ) ) {
		restore_current_locale();
	}
}

/**
 * Resolve the order a WooCommerce email `trigger()` call is for, from
 * whatever argument shape that specific hook happened to pass (see
 * molosoc_order_from_notification_arg()'s own doc comment for the
 * customer-note args-array case; some hooks pass the order object
 * directly as the second argument instead of relying on a re-fetch).
 */
function molosoc_cz_order_from_trigger_args( $args ) {
	$first = isset( $args[0] ) ? $args[0] : null;
	if ( isset( $args[1] ) && $args[1] instanceof WC_Order ) {
		return $args[1];
	}
	return molosoc_order_from_notification_arg( $first );
}

/**
 * Find every already-registered `customer_*` WooCommerce email's own
 * `trigger` callback, wherever WordPress core's own $wp_filter records it
 * was bound, and replace it in place with a locale-aware wrapper that
 * switches to cs_CZ only for that specific email/order before calling the
 * original trigger(), then restores the prior locale. Deliberately never
 * touches admin-facing email classes (id not prefixed `customer_`), so a
 * hook shared with an admin email's own trigger is left exactly as
 * WooCommerce itself registered it.
 */
function molosoc_wrap_customer_email_triggers_with_cz_locale() {
	if ( ! function_exists( 'WC' ) || ! WC()->mailer() ) {
		return;
	}
	global $wp_filter;
	if ( empty( $wp_filter ) || ! is_array( $wp_filter ) ) {
		return;
	}
	// Not every `customer_*` email id is order-related: the account-
	// lifecycle emails below call trigger() with a user id, not an order
	// id. wc_get_order() on that id can coincidentally resolve to an
	// unrelated order that happens to share the same numeric id (user ids
	// and order/post ids are independent namespaces), which would then
	// wrongly localize a new-account or password-reset email that has
	// nothing to do with that order. Only wrap the known order-related
	// customer_* email classes.
	$molosoc_order_customer_email_ids = array(
		'customer_processing_order',
		'customer_on_hold_order',
		'customer_completed_order',
		'customer_refunded_order',
		'customer_invoice',
		'customer_note',
	);
	foreach ( WC()->mailer()->get_emails() as $molosoc_email ) {
		if ( ! ( $molosoc_email instanceof WC_Email ) || ! in_array( (string) $molosoc_email->id, $molosoc_order_customer_email_ids, true ) ) {
			continue; // Never rewrap a non-order (e.g. account) email class.
		}
		foreach ( $wp_filter as $molosoc_hook_name => $molosoc_hook_obj ) {
			if ( ! ( $molosoc_hook_obj instanceof WP_Hook ) ) {
				continue;
			}
			foreach ( $molosoc_hook_obj->callbacks as $molosoc_priority => $molosoc_callbacks ) {
				foreach ( $molosoc_callbacks as $molosoc_cb ) {
					$molosoc_fn = isset( $molosoc_cb['function'] ) ? $molosoc_cb['function'] : null;
					if ( ! is_array( $molosoc_fn ) || ! isset( $molosoc_fn[0], $molosoc_fn[1] ) || $molosoc_fn[0] !== $molosoc_email || 'trigger' !== $molosoc_fn[1] ) {
						continue;
					}
					remove_action( $molosoc_hook_name, array( $molosoc_email, 'trigger' ), $molosoc_priority );
					add_action(
						$molosoc_hook_name,
						function ( ...$molosoc_args ) use ( $molosoc_email ) {
							$molosoc_order = molosoc_cz_order_from_trigger_args( $molosoc_args );
							$molosoc_is_cz = $molosoc_order && 'cz' === $molosoc_order->get_meta( '_molosoc_lang' );
							if ( $molosoc_is_cz ) {
								switch_to_locale( 'cs_CZ' );
							}
							call_user_func_array( array( $molosoc_email, 'trigger' ), $molosoc_args );
							if ( $molosoc_is_cz ) {
								restore_current_locale();
							}
						},
						$molosoc_priority,
						$molosoc_cb['accepted_args']
					);
				}
			}
		}
	}
}
// 'wp_loaded' (after 'init' has fully completed) rather than 'init'
// itself, so WC_Emails::init_transactional_emails() — hooked on 'init' —
// has definitely already instantiated every email class and registered
// its own trigger callbacks by the time this looks for them.
add_action( 'wp_loaded', 'molosoc_wrap_customer_email_triggers_with_cz_locale', 20 );

// Customer-facing emails that aren't tied to a status transition at all:
// partial/full refund notifications and the "customer note added" email.
// None of these have an admin-email equivalent sharing the same hook, so
// the blanket switch/restore pair above is safe to use directly.
$molosoc_extra_customer_email_hooks = array(
	'woocommerce_order_partially_refunded_notification',
	'woocommerce_order_fully_refunded_notification',
	'woocommerce_new_customer_note_notification',
);
foreach ( $molosoc_extra_customer_email_hooks as $molosoc_extra_hook ) {
	add_action( $molosoc_extra_hook, 'molosoc_switch_locale_for_cz_order_email', 5, 1 );
	add_action( $molosoc_extra_hook, 'molosoc_restore_locale_after_cz_order_email', 20, 1 );
}
unset( $molosoc_extra_customer_email_hooks, $molosoc_extra_hook );

// Admin "Resend order details" order action does not go through any
// status-transition notification hook at all — WC_Meta_Box_Order_Actions
// calls WC()->mailer()->customer_invoice( $order ), which triggers
// WC_Email_Customer_Invoice directly via a plain method call, not a
// shared action dispatch, so no admin-email collision is possible here
// either. WooCommerce wraps that direct call in
// 'woocommerce_before_resend_order_emails' / '..._after_resend_order_email'
// (note the mismatched singular/plural hook names in WooCommerce core
// itself), passing the email type ('customer_invoice', not 'invoice') as
// the second argument, so that's the only hook pair that actually fires
// around this send.
add_action( 'woocommerce_before_resend_order_emails', 'molosoc_switch_locale_for_cz_resend_email', 5, 2 );
add_action( 'woocommerce_after_resend_order_email', 'molosoc_restore_locale_after_cz_resend_email', 20, 2 );

/* =====================================================================
 * 5. Presentation (data untouched — every hook below is gated to product
 *    364, or to the cart/order line item referencing it, and never a
 *    blanket filter across the shop)
 * =================================================================== */

/**
 * Czech title for product 364. Sourced from
 * i18n/cz/cz-product-copy.md's H1 (verbatim) — same string
 * page-moisture-lock-foot-cover.php's own CZ H1 spans already render.
 */
function molosoc_cz_product_title( $title, $post_id = 0 ) {
	if ( ! molosoc_is_cz_product_364( $post_id ) ) {
		return $title;
	}
	return 'Návlek na nohy Molosoc';
}
add_filter( 'the_title', 'molosoc_cz_product_title', 10, 2 );

/**
 * Czech short description (WooCommerce's own excerpt-based
 * woocommerce_short_description filter, single-product template hero
 * lede). This filter's signature carries no post ID — molosoc_is_cz_
 * product_364() falls back to is_product() + get_queried_object_id() for
 * exactly this case (see its own doc comment). Copy is the same CZ lede
 * page-moisture-lock-foot-cover.php's hero paragraph and
 * cz-product-copy.md's meta description both already use verbatim.
 */
function molosoc_cz_product_short_description( $excerpt ) {
	if ( ! molosoc_is_cz_product_364() ) {
		return $excerpt;
	}
	return '<p>Skutečné výsledky před/po, žádné filtry. Opakovaně použitelný návlek, který udrží váš oblíbený krém na místě a usnadní pravidelnou péči.</p>';
}
add_filter( 'woocommerce_short_description', 'molosoc_cz_product_short_description' );

/**
 * Czech full description (the_content, WooCommerce's Description tab).
 * Sourced from i18n/cz/cz-product-copy.md's first H2/H3 block (Persona 1 —
 * "Majitel(ka) hřbitova krémů" / cream-graveyard owner), verbatim. Hooked
 * at priority 20 (after wpautop's default 10) and returns fully-formed
 * HTML directly, so wpautop never gets a second pass at it. Gated to the
 * main query's product-364 loop iteration specifically (in_the_loop() +
 * is_main_query()) so it can never leak into a related-products widget or
 * any other secondary loop that happens to touch this post.
 */
function molosoc_cz_product_content( $content ) {
	if ( ! molosoc_is_cz_product_364() || ! in_the_loop() || ! is_main_query() ) {
		return $content;
	}
	return '<h2>Krém, který už doma máte, konečně funguje</h2>'
		. '<p>Skoro nikdo nepřestává používat krém na nohy proto, že nefungoval. Přestává proto, že chyběla struktura, díky které by u něj vydržel — pátý večer nebyl ničím jiný než první, kromě nepořádku.</p>'
		. '<p>Odstraňte mastné povlečení a ponožku, která nedrží, a zbyde jen krátká chvíle, kdy krém skutečně dostane šanci fungovat. To je celý rozdíl mezi krémem, který skončí v šuplíku, a tím, který se doopravdy dotáhne.</p>'
		. '<p>Molosoc není nová formule, do které máte investovat. Je postavený tak, aby fungoval s tím, co už máte v koupelně — s balzámem, který jste si oblíbili natolik, že jste si ho koupili, i tím napůl vypitým. Tohle mu konečně dá šanci fungovat.</p>';
}
add_filter( 'the_content', 'molosoc_cz_product_content', 20 );

/**
 * "Velikost" (Size) attribute label, product 364 only. Matches on the
 * label text rather than a hardcoded attribute/taxonomy name, since this
 * repo has no live access to confirm whether the size attribute is a
 * global taxonomy (pa_size or similar) or a custom product attribute —
 * JUDGMENT CALL: confirm the exact attribute name against the live
 * product before merge if this doesn't relabel the size dropdown/cart
 * lines on staging.
 */
function molosoc_cz_attribute_label( $label, $name, $product = null ) {
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return $label;
	}
	if ( $product instanceof WC_Product && ! molosoc_is_product_364_or_its_variation( $product ) ) {
		return $label;
	}
	if ( false !== stripos( $label, 'size' ) || false !== stripos( (string) $name, 'size' ) ) {
		return 'Velikost';
	}
	return $label;
}
add_filter( 'woocommerce_attribute_label', 'molosoc_cz_attribute_label', 10, 3 );

/**
 * Shared M/L size-value classifier used by both the dropdown-args filter
 * (ordering) and the option-name filter (the rendered label text) below,
 * so the two can never disagree with each other. Matches on known slug/
 * value spellings for the two real variations (424=L, 425=M) —
 * JUDGMENT CALL: this repo has no live access to the product's actual
 * attribute term slugs/values, so the hint lists are a best-effort covering
 * the plausible spellings (a plain 'm'/'l' term slug, a 'medium'/'large'
 * term name, or the raw "36-39"/"39.5-44" range used as the attribute
 * value directly). Confirm against the live product before merge; an
 * unrecognized value is left exactly as WooCommerce rendered it rather
 * than guessed at.
 */
function molosoc_size_value_rank( $value ) {
	$v = strtolower( trim( (string) $value ) );
	$m_hints = array( 'm', 'medium', '36', '36-39', '36–39' );
	$l_hints = array( 'l', 'large', '39.5', '39.5-44', '39,5', '39.5–44' );
	if ( in_array( $v, $m_hints, true ) ) {
		return 0;
	}
	if ( in_array( $v, $l_hints, true ) ) {
		return 1;
	}
	return 2; // Unrecognized — sort last, don't guess.
}
function molosoc_size_label_for_value( $value, $fallback ) {
	$rank = molosoc_size_value_rank( $value );
	if ( 0 === $rank ) {
		return 'M (36–39)';
	}
	if ( 1 === $rank ) {
		return 'L (39.5–44)';
	}
	return $fallback;
}

/**
 * Size dropdown: CZ/EN placeholder text, plus force M-before-L ordering
 * regardless of whatever order the underlying attribute terms/values are
 * stored in.
 */
function molosoc_size_dropdown_args( $args ) {
	if ( ! isset( $args['product'] ) || ! $args['product'] instanceof WC_Product || MOLOSOC_PRODUCT_ID !== (int) $args['product']->get_id() ) {
		return $args;
	}
	$is_cz = function_exists( 'pll_current_language' ) && 'cz' === pll_current_language();
	// 'show_option_none' is WooCommerce's own arg key for the dropdown's
	// placeholder <option> (falls back to "Choose an option" when blank).
	$args['show_option_none'] = $is_cz ? 'Vyberte velikost' : 'Choose your size';

	if ( ! empty( $args['options'] ) && is_array( $args['options'] ) ) {
		$options = $args['options'];
		usort(
			$options,
			function ( $a, $b ) {
				return molosoc_size_value_rank( $a ) <=> molosoc_size_value_rank( $b );
			}
		);
		$args['options'] = $options;
	}
	return $args;
}
add_filter( 'woocommerce_dropdown_variation_attribute_options_args', 'molosoc_size_dropdown_args' );

/**
 * The rendered option text itself — same "M (36–39)" / "L (39.5–44)"
 * strings in BOTH languages (only the "Velikost"/"Size" label above
 * differs by language; the size values themselves are numbers + a letter,
 * not translated prose). This filter covers the size dropdown, where
 * WooCommerce passes the PARENT product (364), and — since it's also
 * exactly what both the classic cart's wc_get_formatted_cart_item_data()
 * and the Store API's CartItemSchema::format_variation_data() call for a
 * custom (non-taxonomy) attribute — the classic AND block Cart/Checkout
 * "Size" line for this custom attribute too, where the product passed is
 * the cart's WC_Product_Variation (424/425) rather than the parent; that's
 * why the guard below accepts either. It does NOT cover a taxonomy
 * attribute's cart/order line (neither call site invokes this hook for
 * that case) — see the explicit woocommerce_get_item_data /
 * woocommerce_order_item_display_meta_value mappings below for that path.
 * Gated to product 364 (parent or variation) in both languages (the
 * values/order are the same either way); left as WooCommerce's own text
 * for every other product.
 */
function molosoc_size_option_label( $term_name, $term = null, $attribute = null, $product = null ) {
	if ( ! molosoc_is_product_364_or_its_variation( $product ) ) {
		return $term_name;
	}
	$value = ( is_object( $term ) && isset( $term->slug ) ) ? $term->slug : $term_name;
	return molosoc_size_label_for_value( $value, $term_name );
}
add_filter( 'woocommerce_variation_option_name', 'molosoc_size_option_label', 10, 4 );

/**
 * Cart/checkout "Size: ..." line — wc_get_formatted_cart_item_data()
 * resolves the item-data array (taxonomy term names already looked up,
 * custom-attribute values passed through woocommerce_variation_option_name
 * above with the variation rather than the parent) before applying this
 * filter, so fixing it up here — keyed off the cart item's own product
 * object via molosoc_is_product_364_or_its_variation() — covers both
 * attribute types uniformly regardless of what happened upstream.
 */
function molosoc_size_cart_item_data( $item_data, $cart_item ) {
	$product = isset( $cart_item['data'] ) ? $cart_item['data'] : null;
	if ( ! molosoc_is_product_364_or_its_variation( $product ) || ! is_array( $item_data ) ) {
		return $item_data;
	}
	$is_cz = function_exists( 'pll_current_language' ) && 'cz' === pll_current_language();
	foreach ( $item_data as $index => $data ) {
		// The display KEY ("Size") is untouched by woocommerce_variation_
		// option_name (which only ever supplies the value) — relabel it
		// here too so cart/checkout rows don't show a Czech value under
		// an English "Size" heading.
		$key = isset( $data['key'] ) ? $data['key'] : ( isset( $data['name'] ) ? $data['name'] : '' );
		if ( $is_cz && false !== stripos( (string) $key, 'size' ) ) {
			if ( isset( $data['key'] ) ) {
				$item_data[ $index ]['key'] = 'Velikost';
			}
			if ( isset( $data['name'] ) ) {
				$item_data[ $index ]['name'] = 'Velikost';
			}
		}
		$raw = isset( $data['value'] ) ? $data['value'] : ( isset( $data['display'] ) ? $data['display'] : '' );
		if ( 2 === molosoc_size_value_rank( $raw ) ) {
			continue; // Not a recognized size value — leave untouched.
		}
		$label = molosoc_size_label_for_value( $raw, $raw );
		if ( isset( $data['value'] ) ) {
			$item_data[ $index ]['value'] = $label;
		}
		if ( isset( $data['display'] ) ) {
			$item_data[ $index ]['display'] = $label;
		}
	}
	return $item_data;
}
add_filter( 'woocommerce_get_item_data', 'molosoc_size_cart_item_data', 10, 2 );

/**
 * Order details / order emails / admin order screen "Size: ..." meta
 * line — WC_Order_Item::get_formatted_meta_data() runs each already-
 * resolved meta value through this filter (not woocommerce_variation_
 * option_name), for both taxonomy and custom attributes alike.
 */
function molosoc_size_order_item_meta_value( $display_value, $meta, $item ) {
	if ( ! is_a( $item, 'WC_Order_Item_Product' ) || ! molosoc_is_product_364_or_its_variation( $item->get_product() ) ) {
		return $display_value;
	}
	$raw = wp_strip_all_tags( (string) $display_value );
	if ( 2 === molosoc_size_value_rank( $raw ) ) {
		return $display_value; // Not a recognized size value — leave untouched.
	}
	return molosoc_size_label_for_value( $raw, $display_value );
}
add_filter( 'woocommerce_order_item_display_meta_value', 'molosoc_size_order_item_meta_value', 10, 3 );

/**
 * Order details / order emails / admin order screen "Size" meta LABEL —
 * the key, not the value already handled above. Gated on the ORDER's own
 * saved _molosoc_lang meta rather than pll_current_language(), because
 * async/admin contexts (see molosoc_switch_locale_for_cz_order_email
 * above) switch only the WordPress locale — Polylang's own request-
 * language resolution is never established there, so pll_current_
 * language() would wrongly read as non-cz for exactly the emails this is
 * meant to cover. Same gating molosoc_cz_order_item_name() already uses.
 */
function molosoc_size_order_item_meta_key( $display_key, $meta, $item ) {
	if ( ! is_a( $item, 'WC_Order_Item_Product' ) || ! molosoc_is_product_364_or_its_variation( $item->get_product() ) ) {
		return $display_key;
	}
	$order = $item->get_order();
	if ( ! $order instanceof WC_Order || 'cz' !== $order->get_meta( '_molosoc_lang' ) ) {
		return $display_key;
	}
	if ( false === stripos( (string) $display_key, 'size' ) ) {
		return $display_key;
	}
	return 'Velikost';
}
add_filter( 'woocommerce_order_item_display_meta_key', 'molosoc_size_order_item_meta_key', 10, 3 );

/**
 * Czech product-name override in the cart line, product 364 only. Cart
 * item "name" HTML is normally the linked product title
 * (get_the_title()); replace just that title substring (whatever markup
 * wraps it — the edit/quantity link — is left intact) rather than
 * reconstructing the whole HTML string.
 */
function molosoc_cz_cart_item_name( $name, $cart_item, $cart_item_key ) {
	$product_id = isset( $cart_item['product_id'] ) ? (int) $cart_item['product_id'] : 0;
	if ( ! molosoc_is_cz_product_364( $product_id ) ) {
		return $name;
	}
	$product = isset( $cart_item['data'] ) ? $cart_item['data'] : null;
	$en_title = ( $product instanceof WC_Product ) ? $product->get_name() : '';
	if ( '' !== $en_title && false !== strpos( $name, $en_title ) ) {
		return str_replace( $en_title, 'Návlek na nohy Molosoc', $name );
	}
	return $name;
}
add_filter( 'woocommerce_cart_item_name', 'molosoc_cz_cart_item_name', 10, 3 );

/**
 * Same swap for the Store API (block Cart/Checkout — /cz/kosik/ and
 * /cz/pokladna/'s Cart/Checkout blocks copy page 359/360's blocks
 * verbatim, so they read cart line names straight off the
 * wc/store/v1/cart REST response's own get_name() call, never through
 * woocommerce_cart_item_name or the_title). This product is variable and
 * always added to cart as variation 424/425, so `$cart_item['data']` the
 * Store API schema reads is a WC_Product_Variation. WC_Product_Variation
 * doesn't override get_name() with its own formatting — it inherits
 * WC_Product::get_name(), which is a plain get_prop( 'name' ) call, so the
 * filter WC_Data applies is built from the variation class's own hook
 * prefix: woocommerce_product_variation_get_name, not
 * woocommerce_product_variation_name (that hook name was this file's own
 * earlier, incorrect guess — corrected here after Codex re-flagged it,
 * confirming get_prop()'s `$this->get_hook_prefix() . $prop` pattern is
 * what actually fires for this getter).
 * Gated the same way as the rest of section 3: pll_current_language()
 * reads 'cz' for this request because store-api-lang.js's apiFetch
 * middleware appends ?lang=cz to the wc/store/* request itself. Also kept
 * on woocommerce_product_variation_name and woocommerce_product_get_name
 * as a defensive superset in case a differently-versioned WooCommerce core
 * or another code path resolves get_name() through either of those instead
 * — a filter for a hook that never fires is simply never triggered.
 */
function molosoc_cz_store_api_product_name( $name, $product ) {
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return $name;
	}
	if ( ! molosoc_is_product_364_or_its_variation( $product ) ) {
		return $name;
	}
	return 'Návlek na nohy Molosoc';
}
add_filter( 'woocommerce_product_variation_get_name', 'molosoc_cz_store_api_product_name', 10, 2 );
add_filter( 'woocommerce_product_variation_name', 'molosoc_cz_store_api_product_name', 10, 2 );
add_filter( 'woocommerce_product_get_name', 'molosoc_cz_store_api_product_name', 10, 2 );

/**
 * Same swap for order line items (emails, order-received page, My
 * Account > Orders, admin order screen) — gated on the ORDER's own saved
 * _molosoc_lang meta (section 4) rather than the current request's
 * language, since an order can be viewed/emailed from a request with no
 * language of its own (admin screen, async gateway callback).
 */
function molosoc_cz_order_item_name( $item_name, $item ) {
	if ( ! is_a( $item, 'WC_Order_Item_Product' ) ) {
		return $item_name;
	}
	if ( MOLOSOC_PRODUCT_ID !== (int) $item->get_product_id() ) {
		return $item_name;
	}
	$order = $item->get_order();
	if ( ! $order instanceof WC_Order || 'cz' !== $order->get_meta( '_molosoc_lang' ) ) {
		return $item_name;
	}
	$en_name = $item->get_name();
	if ( '' !== $en_name && false !== strpos( $item_name, $en_name ) ) {
		return str_replace( $en_name, 'Návlek na nohy Molosoc', $item_name );
	}
	return $item_name;
}
add_filter( 'woocommerce_order_item_name', 'molosoc_cz_order_item_name', 10, 2 );

/**
 * True for product 364 itself or either of its variations (424=L, 425=M).
 * WooCommerce resolves woocommerce_get_price_html separately per selected
 * variation on the single-product page, so the display-only override below
 * has to follow the parent relationship — an ID-only check against 364
 * would miss the price shown as soon as a shopper picks a size.
 */
function molosoc_is_product_364_or_its_variation( $product ) {
	if ( ! $product instanceof WC_Product ) {
		return false;
	}
	if ( MOLOSOC_PRODUCT_ID === (int) $product->get_id() ) {
		return true;
	}
	return $product instanceof WC_Product_Variation && MOLOSOC_PRODUCT_ID === (int) $product->get_parent_id();
}

/**
 * Single-product-page display price only, product 364 (and its variations)
 * only. EN shows the EUR headline price plus the CZK-charge clarifier
 * (translate="no" — same idiom page-moisture-lock-foot-cover.php already
 * uses on every price group/note, so Chrome's auto-translate on the EN page
 * can't garble the currency code the way it garbled "229 CZK" into "229
 * CZH" before). CZ shows the plain CZK price. Deliberately does NOT hook
 * woocommerce_cart_item_price / woocommerce_cart_item_subtotal / any
 * totals filter — cart, checkout, and the actual amount charged all stay
 * exactly 229,00 Kč / 229 CZK, untouched.
 */
function molosoc_cz_product_price_html( $price_html, $product ) {
	if ( ! function_exists( 'is_product' ) || ! is_product() ) {
		return $price_html;
	}
	if ( ! molosoc_is_product_364_or_its_variation( $product ) ) {
		return $price_html;
	}
	$is_cz = function_exists( 'pll_current_language' ) && 'cz' === pll_current_language();
	if ( $is_cz ) {
		return '<span class="price" translate="no">229 Kč</span>';
	}
	return '<span class="price" translate="no">&euro;10 &middot; charged as 229 CZK. Your bank converts at its rate.</span>';
}
add_filter( 'woocommerce_get_price_html', 'molosoc_cz_product_price_html', 10, 2 );

/**
 * Shared CZ->EN text map for shipping-rate labels and payment-gateway
 * titles/descriptions — the known Czech admin strings from the issue's
 * audit, matched defensively by substring since punctuation/whitespace in
 * the live strings isn't guaranteed to match exactly.
 *
 * JUDGMENT CALL: no live shipping-zone/gateway method IDs were available
 * to this session (no server/plugin access) — matching is done on the
 * known label substrings only, best-effort, per the issue's own
 * instruction. Confirm the exact method/gateway IDs against the live site
 * before merge; an unmatched label is left exactly as WooCommerce/the
 * gateway plugin built it, never guessed at.
 */
function molosoc_en_shipping_payment_text( $text ) {
	$map = array(
		'PPL výdejní místo'           => 'PPL pickup point',
		'PPL doručení na adresu'      => 'PPL home delivery',
		'Zásilkovna – Z-BOX'          => 'Zásilkovna Z-BOX',
		'Zásilkovna - Z-BOX'          => 'Zásilkovna Z-BOX',
		'Zásilkovna – výdejní místa'  => 'Zásilkovna pickup point',
		'Zásilkovna - výdejní místa'  => 'Zásilkovna pickup point',
		'Evropa 1 - Smart Europe'     => 'Europe 1 – Smart Europe',
		'Evropa 1 – Smart Europe'     => 'Europe 1 – Smart Europe',
		'Bezpečná online platba kartou' => 'Card payment (Comgate)',
		'Comgate'                     => 'Card payment (Comgate)',
		'Bankovní převod'             => 'Bank transfer',
	);
	foreach ( $map as $cz_substring => $en_label ) {
		if ( false !== stripos( (string) $text, $cz_substring ) ) {
			return $en_label;
		}
	}
	return $text; // No known match — leave exactly as built, never guessed at.
}

/**
 * EN shipping-rate labels. Applied ONLY when pll_current_language()
 * explicitly returns 'en' — never when it's falsy/unresolved (a REST or
 * async context with no language of its own keeps the original Czech
 * strings unchanged, per the issue's explicit instruction), and never for
 * 'cz' (nothing to relabel there — the Czech strings are the live config).
 */
function molosoc_en_shipping_rate_label( $label, $method ) {
	if ( ! function_exists( 'pll_current_language' ) || 'en' !== pll_current_language() ) {
		return $label;
	}
	return molosoc_en_shipping_payment_text( $label );
}
add_filter( 'woocommerce_shipping_rate_label', 'molosoc_en_shipping_rate_label', 10, 2 );

/**
 * EN payment-gateway title/description — same falsy-language guard as
 * shipping above.
 */
function molosoc_en_gateway_title( $title, $gateway_id = '' ) {
	if ( ! function_exists( 'pll_current_language' ) || 'en' !== pll_current_language() ) {
		return $title;
	}
	if ( 'comgate' === strtolower( (string) $gateway_id ) ) {
		return 'Card payment (Comgate)';
	}
	if ( 'bacs' === strtolower( (string) $gateway_id ) ) {
		return 'Bank transfer';
	}
	return molosoc_en_shipping_payment_text( $title );
}
add_filter( 'woocommerce_gateway_title', 'molosoc_en_gateway_title', 10, 2 );

function molosoc_en_gateway_description( $description, $gateway_id = '' ) {
	if ( ! function_exists( 'pll_current_language' ) || 'en' !== pll_current_language() ) {
		return $description;
	}
	return molosoc_en_shipping_payment_text( $description );
}
add_filter( 'woocommerce_gateway_description', 'molosoc_en_gateway_description', 10, 2 );

/**
 * Checkout billing_phone field label, per language. Only overridden when
 * the current language explicitly resolves to 'en' or 'cz' — an
 * unresolved language context leaves WooCommerce's own default label
 * (Telefon) exactly as configured.
 */
function molosoc_checkout_phone_label( $fields ) {
	if ( ! isset( $fields['billing']['billing_phone'] ) ) {
		return $fields;
	}
	if ( ! function_exists( 'pll_current_language' ) ) {
		return $fields;
	}
	$lang = pll_current_language();
	if ( 'en' === $lang ) {
		$fields['billing']['billing_phone']['label'] = 'Phone';
	} elseif ( 'cz' === $lang ) {
		$fields['billing']['billing_phone']['label'] = 'Telefon';
	}
	return $fields;
}
add_filter( 'woocommerce_checkout_fields', 'molosoc_checkout_phone_label' );

/* =====================================================================
 * 6. Add-to-cart UI/notices + remaining theme-controlled core strings
 *    on the CZ product page (Issue #67). Same gate as section 5: every
 *    hook here is scoped to product 364 (or its variation) AND the
 *    current request resolving to 'cz' — never a blanket filter across
 *    the shop, and the EN product page is untouched.
 * =================================================================== */

/**
 * "Add to cart" button text on the single-product page itself. This is
 * the single-product-specific filter (WC_Product::single_add_to_cart_text())
 * — deliberately not woocommerce_product_add_to_cart_text, which is the
 * shop/archive loop's own variant and isn't rendered on this page.
 */
function molosoc_cz_single_add_to_cart_text( $text, $product ) {
	if ( ! molosoc_is_product_364_or_its_variation( $product ) ) {
		return $text;
	}
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return $text;
	}
	return 'Přidat do košíku';
}
add_filter( 'woocommerce_product_single_add_to_cart_text', 'molosoc_cz_single_add_to_cart_text', 10, 2 );

/**
 * The "'X' has been added to your cart. View cart" notice WooCommerce
 * prints back on the product page itself after a non-AJAX add-to-cart
 * (this product is variable, added via a form submit back to this same
 * URL) — official documented filter over the fully-assembled HTML,
 * rather than guessing at WooCommerce's internal _n()/sprintf() string
 * shape. $products is the [product_id => qty] array the notice covers;
 * only rewritten when product 364 is in it.
 *
 * For the normal variable-product form submission, WooCommerce builds
 * this message from WC_Form_Handler::add_to_cart_action() on
 * `wp_loaded`, before the main query has run — so is_product() (and
 * therefore molosoc_is_cz_product_364()) is never true yet on this
 * exact path. Gate directly on the Czech request language and the
 * supplied $products IDs instead of the singular-page conditional.
 */
function molosoc_cz_add_to_cart_message( $message, $products ) {
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return $message;
	}
	if ( ! is_array( $products ) || ! array_key_exists( MOLOSOC_PRODUCT_ID, $products ) ) {
		return $message;
	}
	return sprintf(
		'%s <a href="%s" class="button wc-forward" tabindex="1">%s</a>',
		esc_html__( 'Návlek na nohy Molosoc byl přidán do košíku.', 'molosoc' ),
		esc_url( wc_get_cart_url() ),
		esc_html__( 'Zobrazit košík', 'molosoc' )
	);
}
add_filter( 'wc_add_to_cart_message_html', 'molosoc_cz_add_to_cart_message', 10, 2 );

/**
 * Stock-availability text near the add-to-cart form ("In stock" /
 * "Out of stock" / "On backorder") — official filter over the
 * availability array, same best-effort substring approach as the EN
 * shipping/gateway label map above (no live stock-status string variant
 * was available to confirm from this sandbox, e.g. whether a quantity
 * is appended).
 */
function molosoc_cz_stock_availability( $availability, $product ) {
	if ( ! molosoc_is_product_364_or_its_variation( $product ) ) {
		return $availability;
	}
	if ( ! function_exists( 'pll_current_language' ) || 'cz' !== pll_current_language() ) {
		return $availability;
	}
	if ( empty( $availability['availability'] ) ) {
		return $availability;
	}
	$map = array(
		'Out of stock'   => 'Vyprodáno',
		'On backorder'   => 'Dostupné na objednávku',
		'In stock'       => 'Skladem',
	);
	foreach ( $map as $en => $cz ) {
		if ( false !== stripos( $availability['availability'], $en ) ) {
			$availability['availability'] = str_ireplace( $en, $cz, $availability['availability'] );
			break;
		}
	}
	return $availability;
}
add_filter( 'woocommerce_get_availability', 'molosoc_cz_stock_availability', 10, 2 );

/**
 * Description / Additional information / Reviews tab titles. Priority
 * 100 so this runs after WooCommerce core registers the default tabs
 * (its own callbacks are on the default priority 10) — modifying titles
 * in place rather than replacing the tabs array. The Reviews tab title
 * carries a live "(%d)" count from WooCommerce core; only the word
 * itself is replaced so the count keeps rendering correctly.
 */
function molosoc_cz_product_tabs( $tabs ) {
	if ( ! molosoc_is_cz_product_364() ) {
		return $tabs;
	}
	if ( isset( $tabs['description']['title'] ) ) {
		$tabs['description']['title'] = 'Popis';
	}
	if ( isset( $tabs['additional_information']['title'] ) ) {
		$tabs['additional_information']['title'] = 'Další informace';
	}
	if ( isset( $tabs['reviews']['title'] ) ) {
		$tabs['reviews']['title'] = preg_replace( '/^Reviews\b/i', 'Recenze', $tabs['reviews']['title'] );
	}
	return $tabs;
}
add_filter( 'woocommerce_product_tabs', 'molosoc_cz_product_tabs', 100 );

/**
 * Remaining core WooCommerce strings on this page with no equally
 * precise dedicated filter (the quantity input's screen-reader label and
 * the "Related products" section heading — the category/tag lines are
 * handled separately below, via `ngettext`, since WooCommerce renders
 * them through `_n()`). Scoped to the 'woocommerce' text domain AND
 * molosoc_is_cz_product_364() (is_product() + this exact post), so it
 * can never translate an unrelated page's identical WooCommerce string.
 *
 * The quantity label has two source forms depending on whether a
 * product name is available to the template: the plain 'Quantity'
 * string, or the formatted '%s quantity' string with the product name
 * substituted in afterward via sprintf() — both are mapped here, and the
 * '%s' placeholder is preserved so the substitution still works.
 */
function molosoc_cz_woocommerce_gettext( $translation, $text, $domain ) {
	if ( 'woocommerce' !== $domain || ! molosoc_is_cz_product_364() ) {
		return $translation;
	}
	$map = array(
		'Quantity'          => 'Množství',
		'%s quantity'       => 'Množství: %s',
		'Related products'  => 'Podobné produkty',
	);
	return isset( $map[ $text ] ) ? $map[ $text ] : $translation;
}
add_filter( 'gettext', 'molosoc_cz_woocommerce_gettext', 10, 3 );

/**
 * Category:/Categories: and Tag:/Tags: labels in single-product/meta.php.
 * WooCommerce obtains these through _n( $single, $plural, $count,
 * 'woocommerce' ), which WordPress routes through the `ngettext` filter,
 * not `gettext` — so they need their own handler, matched on the exact
 * singular/plural source pair rather than an already-translated string.
 * Same product/language gate as the map above. JUDGMENT CALL: whether
 * this product actually has visible categories/tags assigned wasn't
 * confirmable from this sandbox; this is a no-op if they're not shown.
 */
function molosoc_cz_woocommerce_ngettext( $translation, $single, $plural, $number, $domain ) {
	if ( 'woocommerce' !== $domain || ! molosoc_is_cz_product_364() ) {
		return $translation;
	}
	$map = array(
		'Category:|Categories:' => array( 'Kategorie:', 'Kategorie:' ),
		'Tag:|Tags:'            => array( 'Štítek:', 'Štítky:' ),
	);
	$key = $single . '|' . $plural;
	if ( ! isset( $map[ $key ] ) ) {
		return $translation;
	}
	return 1 === (int) $number ? $map[ $key ][0] : $map[ $key ][1];
}
add_filter( 'ngettext', 'molosoc_cz_woocommerce_ngettext', 10, 5 );

/* =====================================================================
 * 7. Product-page polish before the sticky CTA (Issue #69). Both language
 *    variants of the SAME product-364 page get the identical cleanup:
 *      - the Description tab (WooCommerce's own the_content tab) is
 *        removed — it duplicates the marketing/landing-page copy and
 *        isn't needed here. Additional information and Reviews are left
 *        exactly as WooCommerce builds them; no review data is touched.
 *      - WooCommerce's own per-variation description text (rendered
 *        client-side once a size is picked) is replaced with one concise
 *        shipping line, shown immediately under the size selector.
 *    Every hook is gated to product 364 (or its variation) specifically —
 *    never a blanket filter across the shop — and touches presentation
 *    only, never price, inventory, variations, or orders.
 * =================================================================== */

/**
 * True only for the product-364 singular, in either language. Unlike
 * molosoc_is_cz_product_364() above, this is NOT language-gated — both
 * the CZ and EN cleanup in this section apply identically.
 */
function molosoc_is_product_364_page() {
	return function_exists( 'is_product' ) && is_product() && MOLOSOC_PRODUCT_ID === (int) get_queried_object_id();
}

/**
 * Remove the Description tab for product 364. Hooked before
 * molosoc_cz_product_tabs() (priority 100) so that function's now-moot
 * 'description' title tweak simply no-ops via its own isset() guard.
 */
function molosoc_product_364_remove_description_tab( $tabs ) {
	if ( ! molosoc_is_product_364_page() ) {
		return $tabs;
	}
	unset( $tabs['description'] );
	return $tabs;
}
add_filter( 'woocommerce_product_tabs', 'molosoc_product_364_remove_description_tab', 90 );

/**
 * Blank WooCommerce's own per-variation "Description" text for product
 * 364's variations (424/425) — the "unnecessary variation text" the issue
 * asks to remove from the size area. This only clears the text WooCommerce
 * would otherwise inject client-side once a size is selected; the CSS rule
 * in product-form.css hides the (now-empty) wrapper outright as a
 * belt-and-suspenders measure.
 */
function molosoc_product_364_blank_variation_description( $data, $product, $variation ) {
	if ( ! molosoc_is_product_364_or_its_variation( $variation ) ) {
		return $data;
	}
	$data['variation_description'] = '';
	return $data;
}
add_filter( 'woocommerce_available_variation', 'molosoc_product_364_blank_variation_description', 10, 3 );

/**
 * Concise shipping line in the variation/size area, in place of the
 * per-variation text blanked above. Hooked on
 * woocommerce_after_variations_table (fires right after the size dropdown
 * table itself, before single_variation_wrap's price/quantity/add-to-cart
 * controls, in both languages' identical markup), so it's visible
 * immediately on page load — not only after a size is picked — and stays
 * in the selector area rather than below the purchase controls.
 * translate="no" matches this file's existing price/currency idiom so
 * browser auto-translate can't garble "CZK".
 */
function molosoc_product_364_shipping_note() {
	global $product;
	if ( ! $product instanceof WC_Product || ! molosoc_is_product_364_or_its_variation( $product ) ) {
		return;
	}
	$is_cz = function_exists( 'pll_current_language' ) && 'cz' === pll_current_language();
	printf(
		'<p class="molosoc-product-shipping-note" translate="no">%s</p>',
		esc_html( $is_cz ? 'Doprava od 79 Kč' : 'Shipping from 79 CZK' )
	);
}
add_action( 'woocommerce_after_variations_table', 'molosoc_product_364_shipping_note' );
