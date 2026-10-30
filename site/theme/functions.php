<?php
/**
 * Molosoc standalone theme — setup, menu registration, and asset enqueue.
 *
 * Per project constraints this pass covers the homepage template and the
 * baseline a classic theme needs to not be broken elsewhere (index/header/
 * footer). Category/product/pillar/spoke templates, and a real footer
 * design, are a later, separate step — see the standing gap list in
 * docs/ (or the chat report that shipped alongside this build).
 */

defined( 'ABSPATH' ) || exit;

// Bilingual WooCommerce purchase flow (CZ /cz/produkt → /cz/kosik →
// /cz/pokladna, EN unchanged) for the one product this store sells — see
// the file's own header comment for the full section map. Split out of
// this already-large file rather than added inline, since it's a
// self-contained, separately reviewable feature (GitHub Issue #53).
require_once get_stylesheet_directory() . '/inc/woocommerce-lang.php';

// Bilingual Thank You page hero + post-purchase gift add-on (GitHub Issue
// #106). Depends on inc/woocommerce-lang.php above.
require_once get_stylesheet_directory() . '/inc/thank-you-gift.php';

// CZ bank-transfer unpaid-order reminder after 24h (Issue #194).
require_once get_stylesheet_directory() . '/inc/bacs-payment-reminder.php';

// Contextual Related-reading internal links (Issue #200).
require_once get_stylesheet_directory() . '/inc/related-links.php';

// Landing Page B JSON-LD (Issue #155). Depends on inc/woocommerce-lang.php above.
require_once get_stylesheet_directory() . '/inc/landing-b-schema.php';
require_once get_stylesheet_directory() . '/inc/landing-b-buy.php';
// English Landing B (Issue #288): slug helper, assets, head, title/meta/JSON-LD, FAQ. Needs landing-b-schema.php above.
require_once get_stylesheet_directory() . '/inc/landing-b-en.php';
require_once get_stylesheet_directory() . '/inc/landing-xmas.php';
// Delayed gtag.js on the Christmas pages (Issue #301). Needs molosoc_is_xmas_landing() from landing-xmas.php above.
require_once get_stylesheet_directory() . '/inc/delayed-third-party.php';

// Checkout cleanup (Issue #267): CZ payment labels, CusRev checkbox text, Comgate logo size.
require_once get_stylesheet_directory() . '/inc/checkout-cleanup.php';

function molosoc_setup() {
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'html5', array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script' ) );
	add_theme_support( 'automatic-feed-links' );

	// WooCommerce theme support — opts into WC's structured template wrappers
	// (gallery, product image zoom/lightbox/slider) instead of its shortcode
	// fallback wrapping. Shop/product/cart still render without this, but
	// less cleanly.
	add_theme_support( 'woocommerce' );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );

	register_nav_menus( array(
		'primary' => __( 'Primary Menu', 'molosoc' ),
	) );
}
add_action( 'after_setup_theme', 'molosoc_setup' );

/**
 * This theme has no sidebar concept anywhere — every page (homepage,
 * category, product, all pillars/spokes) is full-width by design, and
 * the theme ships no sidebar.php of any kind. WooCommerce's own
 * single-product/archive templates still fire the woocommerce_sidebar
 * action regardless (hooked by default to woocommerce_get_sidebar(),
 * which calls get_sidebar('shop')). With no sidebar-shop.php/sidebar.php
 * in the theme to catch that, WordPress core falls through to its own
 * built-in theme-compat fallback sidebar — a raw, completely unstyled
 * search form + full site-wide wp_list_pages() dump — which is exactly
 * the "looks like coding links" block that was appearing below the
 * product description on /product/molosoc-product-moisture-lock-foot-
 * cover/ (and would appear on any native WooCommerce shop/product page).
 * Removing the hook is WooCommerce's own documented way to disable the
 * shop sidebar outright, rather than adding an empty sidebar.php just to
 * intercept it. Hooked on init (not called directly here) since that's
 * safely after WooCommerce registers woocommerce_get_sidebar() on its
 * own init-time hook setup.
 */
function molosoc_remove_woocommerce_sidebar() {
	remove_action( 'woocommerce_sidebar', 'woocommerce_get_sidebar' );
}
add_action( 'init', 'molosoc_remove_woocommerce_sidebar' );

/* ---------- XML-sitemap + robots hygiene (SEO remediation step 3B, 2026-08-16) ----------
 * The site uses WordPress core's wp-sitemap.xml (no SEO plugin), so the
 * cleanup lives in core's filter API. Goal: the sitemap lists only
 * canonical, indexable, 200 URLs. Thrive's tcb_* post types stay fully
 * registered (symbols/lightboxes keep rendering inside pages) — they're
 * only dropped from sitemap output, and their thin public taxonomy
 * archives get a robots noindex. */

// Author archives are empty (no posts exist) — drop the users sitemaps.
add_filter( 'wp_sitemaps_add_provider', function ( $provider, $name ) {
	return 'users' === $name ? false : $provider;
}, 10, 2 );

// Keep Thrive builder internals out of the sitemap: the tcb_symbol
// entries are ?p= query URLs that 302 to the homepage, and lightboxes
// are noindexed fragments — neither belongs in a sitemap.
add_filter( 'wp_sitemaps_post_types', function ( $post_types ) {
	unset( $post_types['tcb_symbol'], $post_types['tcb_lightbox'] );
	return $post_types;
} );

add_filter( 'wp_sitemaps_taxonomies', function ( $taxonomies ) {
	unset( $taxonomies['tcb_symbols_tax'] );
	return $taxonomies;
} );

/**
 * Pages the sitemap must not list: WooCommerce utility pages (already
 * noindexed at render time, which core sitemaps don't know about), the
 * post-purchase thank-you page, and the six retired legacy pages that
 * now 301 via Redirection rules (the pages still exist under the
 * redirect layer, so core would keep listing them).
 */
function molosoc_sitemap_excluded_page_ids() {
	static $ids = null;
	if ( null !== $ids ) {
		return $ids;
	}
	$ids   = array();
	$slugs = array(
		'cart', 'checkout', 'my-account', 'thank-you',
		'kosik', 'pokladna',
		'home-2', 'blog-2', 'blog-legacy-2018',
		'hydratacni-navleky-na-nohy-2', 'doprava-a-platba', 'home-cestina',
		// Landing Page B (hydratacni-navleky-molosoc, page 1037) was listed
		// here while it was an unpublished variant (Issue #122); since
		// Issue #159 it is a normal indexable page, so it is NOT excluded.
	);
	foreach ( $slugs as $slug ) {
		$page = get_page_by_path( $slug );
		if ( $page ) {
			$ids[] = (int) $page->ID;
		}
	}
	return $ids;
}

add_filter( 'wp_sitemaps_posts_query_args', function ( $args, $post_type ) {
	if ( 'page' === $post_type ) {
		$args['post__not_in'] = array_merge(
			isset( $args['post__not_in'] ) ? (array) $args['post__not_in'] : array(),
			molosoc_sitemap_excluded_page_ids()
		);
	}
	return $args;
}, 10, 2 );

// noindex for thin/utility URLs that stay reachable: the post-purchase
// thank-you page, the empty author archives, the empty Uncategorized
// archive and Thrive's symbol-taxonomy archive pages. Landing Page B
// (hydratacni-navleky-molosoc) was noindexed here while it was an
// unpublished variant (Issue #122); it is indexable since Issue #159.
add_filter( 'wp_robots', function ( $robots ) {
	if ( is_author() || is_category( 'uncategorized' ) || is_tax( 'tcb_symbols_tax' ) || is_page( 'thank-you' ) ) {
		$robots['noindex'] = true;
	}
	return $robots;
} );

/**
 * Issue #222: the retired Czech product slug 301s to the equivalent Czech
 * WooCommerce purchase page, not (as WordPress' old-slug redirect did) to the
 * English product. Exact path match on this single source only; runs before
 * wp_old_slug_redirect (template_redirect priority 10). The target is built
 * from home_url(), so staging stays on staging, and it can never equal the
 * source path, so it cannot loop.
 */
function molosoc_cz_product_redirect_target( $request_uri ) {
	$path = (string) wp_parse_url( (string) $request_uri, PHP_URL_PATH );
	if ( '/product/molosoc-hydratacni-navleky-na-nohy' !== untrailingslashit( $path ) ) {
		return '';
	}
	return home_url( '/cz/produkt/hydratacni-navlek-na-nohy/' );
}

add_action( 'template_redirect', function () {
	$target = molosoc_cz_product_redirect_target( $_SERVER['REQUEST_URI'] ?? '' );
	if ( '' !== $target ) {
		wp_redirect( $target, 301, 'Molosoc' );
		exit;
	}
}, 1 );

/**
 * Term IDs of the WooCommerce "foot-care" product category (Issue #203) plus
 * any Polylang translations of it. That archive lists the one product the
 * shop sells, which the Category page (/foot-covers/) and the product page
 * already serve, so it is kept reachable for WooCommerce navigation but
 * out of the index and the sitemap. Only this term is affected — other
 * product taxonomy archives keep core/WooCommerce behaviour.
 */
function molosoc_thin_product_cat_term_ids() {
	static $ids = null;
	if ( null !== $ids ) {
		return $ids;
	}
	$ids  = array();
	$term = taxonomy_exists( 'product_cat' ) ? get_term_by( 'slug', 'foot-care', 'product_cat' ) : false;
	if ( $term && ! is_wp_error( $term ) ) {
		$ids[] = (int) $term->term_id;
		if ( function_exists( 'pll_get_term_translations' ) ) {
			$ids = array_merge( $ids, array_map( 'intval', array_values( (array) pll_get_term_translations( $term->term_id ) ) ) );
		}
		$ids = array_values( array_unique( $ids ) );
	}
	return $ids;
}

// noindex,follow for the thin foot-care category archive. Deliberately no
// canonical tag is added: core only emits rel=canonical for singular posts,
// and a canonical on a page that is noindexed is a mixed signal.
add_filter( 'wp_robots', function ( $robots ) {
	if ( is_tax( 'product_cat' ) && in_array( (int) get_queried_object_id(), molosoc_thin_product_cat_term_ids(), true ) ) {
		$robots['noindex'] = true;
		$robots['follow']  = true;
		unset( $robots['index'] );
	}
	return $robots;
} );

// ...and keep it out of wp-sitemap.xml so sitemap and robots agree.
add_filter( 'wp_sitemaps_taxonomies_query_args', function ( $args, $taxonomy ) {
	if ( 'product_cat' === $taxonomy ) {
		$args['exclude'] = array_merge(
			isset( $args['exclude'] ) ? (array) $args['exclude'] : array(),
			molosoc_thin_product_cat_term_ids()
		);
	}
	return $args;
}, 10, 2 );

// hreflang x-default, pointing unmatched-language searchers at the EN
// version. Free Polylang emits the en/cs alternate pair itself but never
// an x-default, so this fills only that gap: it prints ONLY on pages that
// actually have both a published EN and CZ translation — exactly the
// pages where Polylang already prints the pair — and never rewrites or
// duplicates Polylang's own tags. Language slugs are 'en'/'cz' (locales
// en_US/cs_CZ).
add_action( 'wp_head', function () {
	if ( ! function_exists( 'pll_get_post' ) || ! is_singular() ) {
		return;
	}
	$id = get_queried_object_id();
	if ( ! $id ) {
		return;
	}
	$en = pll_get_post( $id, 'en' );
	$cz = pll_get_post( $id, 'cz' );
	if ( ! $en || ! $cz || 'publish' !== get_post_status( $en ) || 'publish' !== get_post_status( $cz ) ) {
		return;
	}
	printf( '<link rel="alternate" href="%s" hreflang="x-default" />' . "\n", esc_url( get_permalink( $en ) ) );
} );

/**
 * Whether the homepage renders its "card hero" variant (front-page.php):
 * the site's normal boxed header (same logo + menu as every other
 * template, e.g. /cz/navleky-na-nohy/), the hero photo inside one very
 * wide floating elevated card on the cream page background (breathing
 * zoom kept), and NO animation below the hero — no GSAP merge /
 * topics-portal / scroll-refresh, and every .molosoc-reveal pinned at its
 * settled state (homepage.css, body.molosoc-front-page--card).
 *
 * Built for the Czech homepage first (2026-09-21), then approved for the
 * English homepage the same day — so this is now every homepage. Kept as
 * a function (rather than deleting the old floating-header/full-bleed
 * hero code paths) so the two treatments can still be A/B'd or rolled
 * back per language with a one-line change here.
 */
function molosoc_home_card_variant() {
	return true;
}

/**
 * Whether the global sticky "Buy now" CTA (GitHub Issue #73) should be
 * hidden on the current request. Shared between molosoc_enqueue_assets()
 * (which enqueues sticky-cta.js) and the wp_head hook below (which prints
 * the window.molosocStickyCta data that file reads), so the two can never
 * drift apart on which pages get the pill.
 */
function molosoc_sticky_cta_hidden() {
	return ( function_exists( 'is_cart' ) && is_cart() )
		|| ( function_exists( 'is_checkout' ) && is_checkout() )
		|| ( function_exists( 'is_product' ) && is_product() )
		|| is_page( array(
			// The legal pages, EN + CZ (Issue #177): no purchase pill over
			// policy text. The CZ slugs are listed explicitly because they
			// are regular Pages whose translation is not auto-matched (same
			// is_page() convention as the other slug lists in this file).
			'privacy-policies', 'terms-of-services', 'shipping-policy',
			'zasady-ochrany-osobnich-udaju', 'obchodni-podminky', 'zasady-dopravy',
		) );
	// Landing Page B (hydratacni-navleky-molosoc) was excluded here while it
	// shipped its own page-580-style bottom bar (Issue #122); since Issue #163
	// it shows this global pill like every other public page. Landing Page A
	// ('moisture-lock-foot-cover' / 'hydratacni-navlek-na-nohy') was excluded
	// until Issue #177 because of its own .molosoc-sticky-buy bar — but that
	// bar is phone-only, so the page had no sticky CTA at all on desktop. The
	// pill now shows there too; product.css hides it at <=760px, where the
	// bar (same product URL, plus the price) takes over.
}

/**
 * The site-wide Google Fonts stylesheet URL (Tenor Sans display face, Mulish,
 * Nunito). One function so the normal render-blocking enqueue below and the
 * non-blocking Landing Page B print (molosoc_landing_b_head()) can never
 * drift apart on the font set.
 */
function molosoc_fonts_url() {
	return 'https://fonts.googleapis.com/css2?family=Tenor+Sans&family=Mulish:wght@400;500;600;700&family=Nunito:wght@400;600;700&display=swap';
}

/**
 * Landing Page B's own extra face (page 580's label face Nunito Sans).
 * Page 580's Open Sans was dropped in Issue #153: landing-b.css only lists
 * it as a fallback AFTER Nunito, which the global stylesheet always provides,
 * so it was a fetched-but-never-rendered font.
 */
function molosoc_landing_b_fonts_url() {
	return 'https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600&display=swap';
}

/**
 * Is the current page assigned a NEW-article Journal template (Issue #280)?
 * Convention: a template file named page-journal-*.php. Such a page gets the
 * approved article design (pillar1.css, Issues #273/#275) with no edit to
 * the slug list in molosoc_enqueue_assets(), which still covers the existing
 * pillars/spokes. See docs/journal-article-template.md.
 */
function molosoc_has_journal_article_template() {
	return is_page() && 0 === strpos( basename( (string) get_page_template_slug() ), 'page-journal-' );
}

function molosoc_enqueue_assets() {
	$theme_uri     = get_stylesheet_directory_uri();
	$theme_version = wp_get_theme()->get( 'Version' );

	// style.css is deliberately NOT enqueued: it holds only the theme-header
	// comment (WordPress reads that metadata from the file directly), so its
	// minified output is empty — WP-Optimize never writes the bundle file,
	// and every page then shipped a render-blocking <link> that 404ed and
	// 301ed to the homepage (~2s, uncacheable). All real CSS lives in
	// assets/css/ below.

	wp_enqueue_style( 'molosoc-fonts', molosoc_fonts_url(), array(), null );

	wp_enqueue_style( 'molosoc-tokens', $theme_uri . '/assets/css/tokens.css', array(), $theme_version );
	wp_enqueue_style( 'molosoc-base', $theme_uri . '/assets/css/base.css', array( 'molosoc-tokens' ), $theme_version );
	wp_enqueue_style( 'molosoc-components', $theme_uri . '/assets/css/components.css', array( 'molosoc-base' ), $theme_version );

	// Mobile hamburger toggle — every page has exactly one header
	// (.molosoc-site-header everywhere except the homepage, which has its
	// own .molosoc-home-header), so this is unconditional rather than
	// living in one of the per-page branches below.
	wp_enqueue_script( 'molosoc-nav-toggle', $theme_uri . '/assets/js/nav-toggle.js', array(), $theme_version, true );

	// Header cart badge ↔ block cart sync (see the file's header comment).
	// Unconditional like nav-toggle: it self-noops on pages without the
	// wc/store/cart data store, and gating it on is_cart()/is_checkout()
	// would miss any future page embedding a cart/checkout block.
	wp_enqueue_script( 'molosoc-cart-badge-sync', $theme_uri . '/assets/js/cart-badge-sync.js', array(), $theme_version, true );

	// Store API language middleware (see the file's header comment) —
	// cart/checkout only. is_cart()/is_checkout() resolve through the
	// woocommerce_get_cart_page_id / woocommerce_get_checkout_page_id
	// filters added in inc/woocommerce-lang.php, so this also covers the
	// CZ kosik/pokladna twins once they exist — no separate slug check
	// needed here, unlike the page-template branches below.
	if ( function_exists( 'is_cart' ) && function_exists( 'is_checkout' ) && ( is_cart() || is_checkout() ) ) {
		$molosoc_lang_for_js = ( function_exists( 'pll_current_language' ) && pll_current_language() ) ? pll_current_language() : 'en';
		wp_enqueue_script( 'molosoc-store-api-lang', $theme_uri . '/assets/js/store-api-lang.js', array( 'wp-api-fetch' ), $theme_version, true );
		// window.molosocLang, not wp_localize_script's object wrapper, to
		// match the plain 'cz'|'en' global the JS file reads. 'before' so
		// it's defined ahead of the middleware registering itself.
		wp_add_inline_script( 'molosoc-store-api-lang', 'window.molosocLang = ' . wp_json_encode( $molosoc_lang_for_js ) . ';', 'before' );
	}

	// Thank You page hero + gift add-on (inc/thank-you-gift.php) — the
	// order-received endpoint only, so checkout itself loads nothing new.
	if ( function_exists( 'is_wc_endpoint_url' ) && is_wc_endpoint_url( 'order-received' ) ) {
		wp_enqueue_style( 'molosoc-thank-you', $theme_uri . '/assets/css/thank-you.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_script( 'molosoc-thank-you-gift', $theme_uri . '/assets/js/thank-you-gift.js', array(), $theme_version, true );
	}

	// Floating back-to-top button (see the file's header comment for why
	// it jumps instantly instead of smooth-scrolling back through the
	// scroll animations). Unconditional: every page benefits.
	wp_enqueue_script( 'molosoc-back-to-top', $theme_uri . '/assets/js/back-to-top.js', array(), $theme_version, true );

	// Global bilingual sticky "Buy now" CTA — GitHub Issue #73; every public
	// page in both languages since Issue #177. Hidden on Cart/Checkout
	// (is_cart()/is_checkout() already resolve through the CZ kosik/pokladna
	// filters in inc/woocommerce-lang.php, so this covers both languages with
	// no separate slug check), on the single product page itself (it is the
	// pill's destination — the size is chosen there), and on the six legal
	// pages (slugs in molosoc_sticky_cta_hidden()). Landing Page A
	// ('moisture-lock-foot-cover' / 'hydratacni-navlek-na-nohy') keeps its
	// phone-only .molosoc-sticky-buy bar (product.css); the pill shows there
	// at wider widths only, so the two fixed CTAs never overlap.
	//
	// The window.molosocStickyCta data itself is NOT set here via
	// wp_add_inline_script — see the wp_head hook below (molosoc_sticky_cta_hidden())
	// for why.
	if ( ! molosoc_sticky_cta_hidden() ) {
		wp_enqueue_script( 'molosoc-sticky-cta', $theme_uri . '/assets/js/sticky-cta.js', array(), $theme_version, true );
	}

	if ( is_front_page() ) {
		wp_enqueue_style( 'molosoc-homepage', $theme_uri . '/assets/css/homepage.css', array( 'molosoc-components' ), $theme_version );
		// motion.js stays on for BOTH variants: it is what adds .is-visible
		// to .molosoc-hero, which starts the hero photo's breathing zoom.
		wp_enqueue_script( 'molosoc-motion', $theme_uri . '/assets/js/motion.js', array(), $theme_version, true );

		// Card-hero variant (see molosoc_home_card_variant()): nothing below
		// the hero animates, so none of the GSAP/ScrollTrigger stack below
		// is loaded — the merge tiles, proof image and topic cards all
		// render their settled, static state with no JS (homepage.css
		// documents that baseline on each of them).
		if ( ! molosoc_home_card_variant() ) {
			// GSAP + ScrollTrigger are being re-enabled one effect at a time (see
			// git history: "Revert homepage to last confirmed-stable static state
			// (pre-animation-port)" — the full stack caused a regression once
			// before). Merge transition and topics-portal (five-card reveal) are
			// confirmed working; proof-scale stays off until it's confirmed the
			// same way.
			wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
			wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
			wp_enqueue_script( 'molosoc-merge-transition', $theme_uri . '/assets/js/merge-transition.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
			wp_enqueue_script( 'molosoc-topics-portal', $theme_uri . '/assets/js/topics-portal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );

			// Real file content, not wp_add_inline_script — see scroll-refresh.js
			// for why (WPO Minify silently drops inline scripts on a bundled
			// handle). Keeps every ScrollTrigger pin above matched to the real,
			// settled DOM regardless of lazy-loaded images changing page height.
			wp_enqueue_script( 'molosoc-scroll-refresh', $theme_uri . '/assets/js/scroll-refresh.js', array( 'gsap-scrolltrigger', 'molosoc-merge-transition', 'molosoc-topics-portal' ), $theme_version, true );

			// Still disabled — CSS default state (--proof-scale:1) renders this
			// correctly at rest with no JS, so leaving it off doesn't change how
			// it looks:
			// wp_enqueue_script( 'molosoc-proof-scale', $theme_uri . '/assets/js/proof-scale.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		}
	} elseif ( is_page( array( 'foot-covers', 'navleky-na-nohy' ) ) ) {
		// 'navleky-na-nohy' is the Czech translation of 'foot-covers' —
		// is_page() only auto-matches the theme_template by exact English
		// slug, so the Czech page needs to be listed here explicitly or
		// this whole stylesheet/script stack silently never loads on it.
		wp_enqueue_style( 'molosoc-category', $theme_uri . '/assets/css/category.css', array( 'molosoc-components' ), $theme_version );

		// Deliberately NO motion.js / GSAP / ScrollTrigger / scroll-refresh
		// here: everything below the hero on this page is flat, static
		// content (the sequential-text entrances, the "who this is for"
		// mask-reveal + card flight, and the final-CTA .molosoc-reveal fade
		// were all removed). The only animation left is the hero's own
		// pure-CSS ring spin / type-in (category.css), which needs no script.
	} elseif ( is_page( array(
		// Journal article pages — the 5 EN pillars + 6 EN spokes + every
		// Czech translation/CZ-only sibling. Czech slugs are listed
		// explicitly for the same reason as 'navleky-na-nohy' above:
		// is_page() only auto-matches the exact English slug.
		'cracked-heels', 'popraskane-paty',
		'ingrown-toenails', 'zarostly-nehet',
		'hardened-skin-calluses', 'kurici-oko',
		'dry-skin-feet',
		'foot-cream-that-works',
		'treatment',
		'callus-remover', 'jak-odstranit',
		'na-chodidle',
		'sucha-kuze-na-chodidlech',
		'prevent',
		'cracked-heels-cream',
		'cracked-heels-treatment',
		'fix-permanently',
	) ) ) {
		// One shared asset stack for every pillar/spoke template — they all
		// reuse pillar1.css as-is (every class/selector in that file is
		// generic, nothing cracked-heels-specific).
		wp_enqueue_style( 'molosoc-pillar1', $theme_uri . '/assets/css/pillar1.css', array( 'molosoc-components' ), $theme_version );

		// No model-viewer here any more (Issue #149): the "why moisturizer
		// alone doesn't fix it" section's still of the Molosoc model is a
		// plain <img> (molosoc-hero-still.webp) in the templates, so the
		// unpkg.com @google/model-viewer module and the 4.1 MB
		// molosoc-3d.glb are no longer loaded on any Journal page.

		// Deliberately NO motion.js / GSAP / ScrollTrigger /
		// sequential-text-reveal.js / severity-reveal.js /
		// mechanism-drawer.js / scroll-refresh.js here (2026-09-22, per
		// explicit request): on every Journal article the ONLY motion left
		// is the hero photo's pure-CSS breathing zoom (pillar1.css). The
		// "what causes it" text entrance, the "when it gets serious"
		// mask-reveal + card flight, the "why moisturizer alone doesn't fix
		// it" fade/blur/drawer slide, the model's auto-rotate, the final
		// CTA's .molosoc-reveal fade and every hover zoom were all removed —
		// each section renders its settled, static state with no JS.
	} elseif ( molosoc_has_journal_article_template() ) {
		// New CZ/EN Journal articles (Issue #280): same shared stylesheet as the
		// slug-listed branch above, picked up via the page-journal-*.php
		// template-name convention. No JS, same as every Journal article.
		wp_enqueue_style( 'molosoc-pillar1', $theme_uri . '/assets/css/pillar1.css', array( 'molosoc-components' ), $theme_version );
	} elseif ( is_page( array( 'moisture-lock-foot-cover', 'hydratacni-navlek-na-nohy' ) ) ) {
		// 'hydratacni-navlek-na-nohy' is the Czech translation of
		// 'moisture-lock-foot-cover' — see the 'navleky-na-nohy' branch
		// above for why the Czech slug has to be listed explicitly.
		wp_enqueue_style( 'molosoc-product', $theme_uri . '/assets/css/product.css', array( 'molosoc-components' ), $theme_version );

		// Fonts (Issue #190, Landing A first paint): same treatment as
		// Landing B below — the global molosoc-fonts handle is dequeued and
		// molosoc_landing_a_head() prints the one Google Fonts stylesheet as
		// a media="print" + onload swap link, off the critical path. The
		// font set is unchanged (molosoc_fonts_url()); only its blocking
		// behaviour changes.
		wp_dequeue_style( 'molosoc-fonts' );

		// No model-viewer here any more (Issue #149, mobile speed): the
		// hero's still of the Molosoc model is a plain <img>
		// (molosoc-hero-still.webp, ~43 KB) in the template, so neither the
		// unpkg.com @google/model-viewer module nor the 4.1 MB
		// molosoc-3d.glb is loaded on this page. No page-specific JS at all.

		// Deliberately NO GSAP / ScrollTrigger / sequential-text-reveal.js /
		// scroll-refresh.js here (2026-09-21, per explicit request): this
		// page is fully static — the "Make the pedicure last" / "Give it as
		// a gift" scroll-in text entrances were removed along with the
		// hero's model spin, the proof photos' breathing zoom and every
		// hover zoom (see product.css).
	} elseif ( is_page( 'hydratacni-navleky-molosoc' ) ) {
		// Landing Page B (Issue #122): faithful rebuild of Thrive page 580 as
		// an unpublished variant of the CZ landing page — template
		// page-hydratacni-navleky-molosoc.php. Its scoped CSS plus the
		// tabs/sticky-bar enhancement script (deferred: it only wires up
		// click/scroll handlers, nothing render-critical — the strategy is
		// honoured when WP prints the tag itself; WP-Optimize Minify may
		// drop the attribute, which just leaves the footer script where it
		// was). Nothing here touches the live 'hydratacni-navlek-na-nohy'
		// branch below.
		//
		// Fonts (Issue #153, mobile LCP 9.2 s): on this page NEITHER Google
		// Fonts stylesheet is a render-blocking <link>. The global
		// molosoc-fonts handle enqueued above is dequeued again here and
		// both it and page 580's own label face (Nunito Sans — B's headings
		// use the theme display font Tenor Sans, not 580's DM Serif Display,
		// so that request was dropped; family=Nunito+Sans is the only
		// page-specific family) are printed by molosoc_landing_b_head() as
		// media="print" + onload swap links, which the browser downloads
		// off the critical path (display=swap means text renders in the
		// fallback face meanwhile). Raw wp_head output, not an enqueue, so
		// WP-Optimize Minify cannot turn them back into blocking bundles.
		wp_dequeue_style( 'molosoc-fonts' );
		wp_enqueue_style( 'molosoc-landing-b', $theme_uri . '/assets/css/landing-b.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_script( 'molosoc-landing-b', $theme_uri . '/assets/js/landing-b.js', array(), $theme_version, true );
		wp_script_add_data( 'molosoc-landing-b', 'strategy', 'defer' );
	} elseif ( function_exists( 'molosoc_xmas_current_lang' ) && molosoc_xmas_current_lang() ) {
		// Christmas 2026 gift landing (Issue #251, CZ + EN): Landing B's
		// stylesheet as the base plus its own small CSS/JS. B's branch above
		// is slug-gated and unchanged.
		wp_enqueue_style( 'molosoc-landing-b', $theme_uri . '/assets/css/landing-b.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_style( 'molosoc-landing-xmas', $theme_uri . '/assets/css/landing-xmas.css', array( 'molosoc-landing-b' ), $theme_version );
		wp_enqueue_script( 'molosoc-landing-xmas', $theme_uri . '/assets/js/landing-xmas.js', array(), $theme_version, true );
		wp_script_add_data( 'molosoc-landing-xmas', 'strategy', 'defer' );
	} elseif ( is_page( array( 'blog', 'magazin' ) ) ) {
		// Journal index — static photo-tile grid, no motion.js/GSAP needed
		// (see page-blog.php's own header comment for why). 'magazin' is
		// the Czech Journal (/cz/magazin/, rendered by the same
		// page-blog.php via the page-magazin.php shim) — same explicit
		// CZ-slug listing as the product branches above.
		wp_enqueue_style( 'molosoc-blog', $theme_uri . '/assets/css/blog.css', array( 'molosoc-components' ), $theme_version );
	} elseif ( is_product() ) {
		// Native WooCommerce single-product page — trust-badge bars
		// (molosoc_product_trust_bar_top/bottom() below) plus the
		// variation-select/add-to-cart form styling (product-form.css,
		// restyling WooCommerce's own default blue select / purple
		// button to the theme's ink/cream palette); everything else on
		// this page is plain WooCommerce/base.css, no page-specific JS.
		wp_enqueue_style( 'molosoc-product-trust-bars', $theme_uri . '/assets/css/product-trust-bars.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_style( 'molosoc-product-form', $theme_uri . '/assets/css/product-form.css', array( 'molosoc-components' ), $theme_version );
	}
}
add_action( 'wp_enqueue_scripts', 'molosoc_enqueue_assets' );

/**
 * window.molosocStickyCta data for assets/js/sticky-cta.js (molosoc-sticky-cta
 * handle, enqueued above). Printed as raw <script> markup directly on
 * wp_head, NOT via wp_add_inline_script: WP-Optimize Minify combines this
 * handle's file into a bundle with the site's other enqueued scripts on
 * most pages, and silently drops any inline script attached to a bundled
 * handle — the same gotcha documented on assets/js/scroll-refresh.js's own
 * enqueue call above (search "Real file content, not wp_add_inline_script").
 * Raw wp_head output is never attached to any script handle, so it survives
 * that pipeline regardless of what gets bundled/minified together. wp_head
 * always runs before the footer-enqueued sticky-cta.js prints and executes,
 * so window.molosocStickyCta is set by the time that file reads it.
 */
add_action( 'wp_head', function () {
	if ( molosoc_sticky_cta_hidden() ) {
		return;
	}
	$lang = ( function_exists( 'pll_current_language' ) && pll_current_language() ) ? pll_current_language() : 'en';
	// Issue #299: a template may give the pill its own target instead of the
	// product page — the Christmas landing points it at its in-page picker
	// (inc/landing-xmas.php, after order #1073 paid the regular price via this
	// pill). Same gate, same print; every other page falls through unchanged.
	$molosoc_sticky_cta_override = apply_filters( 'molosoc_sticky_cta_data', array(), $lang );
	if ( ! empty( $molosoc_sticky_cta_override['url'] ) && ! empty( $molosoc_sticky_cta_override['label'] ) ) {
		printf( '<script>window.molosocStickyCta = %s;</script>' . "\n", wp_json_encode( $molosoc_sticky_cta_override ) );
		return;
	}
	printf(
		'<script>window.molosocStickyCta = %s;</script>' . "\n",
		wp_json_encode(
			array(
				'url'   => molosoc_product_url( $lang ),
				'label' => ( 'cz' === $lang ) ? 'Koupit nyní' : __( 'Buy now', 'molosoc' ),
			)
		)
	);
} );

/**
 * Early connection hints for the foot-cover landing page (EN
 * 'moisture-lock-foot-cover' / CZ 'hydratacni-navlek-na-nohy') — Issue #99
 * Test 1, "hints only, zero visual change". The page loads the Google
 * Fonts CSS/files, third-party origins on the critical path; preconnect
 * lets the browser open those connections while it parses the head.
 * Output is two <link> tags on this page only — no markup, copy, layout
 * or asset change. (The unpkg.com hint was dropped in Issue #149 together
 * with the model-viewer module it warmed up — the hero's model is a plain
 * same-origin <img> now, so no page loads anything from unpkg.com.)
 *
 * @return array[] Each entry: array( 'href' => string, 'crossorigin' => bool ).
 */
function molosoc_landing_preconnect_hints() {
	if ( ! is_page( array( 'moisture-lock-foot-cover', 'hydratacni-navlek-na-nohy' ) ) ) {
		return array();
	}
	return array(
		array( 'href' => 'https://fonts.googleapis.com', 'crossorigin' => false ),
		array( 'href' => 'https://fonts.gstatic.com', 'crossorigin' => true ),
	);
}
add_action( 'wp_head', function () {
	foreach ( molosoc_landing_preconnect_hints() as $hint ) {
		printf(
			'<link rel="preconnect" href="%s"%s>' . "\n",
			esc_url( $hint['href'] ),
			$hint['crossorigin'] ? ' crossorigin' : ''
		);
	}
}, 1 );

/**
 * Landing Page B (Issue #153) — theme-hosted WebP derivatives of page 580's
 * photos, resized to the widths landing-b.css actually displays them at
 * (assets/images/landing-b/, generated with cwebp -q 78 from the live
 * uploads; see docs/landing-page-b-580.md "Asset inventory"). The template
 * echoes molosoc_landing_b_img_attrs() for every <img>; the hero set is
 * defined once in molosoc_landing_b_hero_image() so the <img> and the
 * <link rel="preload"> below carry byte-identical srcset/sizes.
 *
 * @param string $base   Derivative basename, e.g. 'lpb-hero-baige'.
 * @param int[]  $widths Available widths; files are "<base>-<w>.webp".
 * @param string $sizes  The sizes attribute.
 * @return string Escaped ' src="…" srcset="…" sizes="…"' attributes.
 */
function molosoc_landing_b_img_attrs( $base, array $widths, $sizes ) {
	$dir    = get_stylesheet_directory_uri() . '/assets/images/landing-b/';
	$srcset = array();
	foreach ( $widths as $w ) {
		$srcset[] = esc_url( $dir . $base . '-' . (int) $w . '.webp' ) . ' ' . (int) $w . 'w';
	}
	return sprintf(
		'src="%s" srcset="%s" sizes="%s"',
		esc_url( $dir . $base . '-' . (int) max( $widths ) . '.webp' ),
		esc_attr( implode( ', ', $srcset ) ),
		esc_attr( $sizes )
	);
}

/**
 * The hero (LCP) image set: full column width on phones, the 1.3fr media
 * column (~700px of the 1240px .lpb-hero__inner) on desktop.
 */
function molosoc_landing_b_hero_image() {
	return array(
		'base'   => 'lpb-hero-baige',
		'widths' => array( 480, 800, 1152 ),
		'sizes'  => '(max-width: 900px) 100vw, 700px',
	);
}

/**
 * The .lpb-hero CSS background (Issue #157). PageSpeed reports this
 * section's background image — not the hero <img> — as the LCP element: a
 * CSS url() is only discovered once the stylesheet bundle has downloaded
 * and parsed, so it paints last on the first phone viewport. Theme-hosted
 * WebP derivatives of hero-bg-v2 (a soft watercolour wash under a 50 %
 * white overlay, so 960px is plenty on phones), picked by the 900px
 * breakpoint landing-b.css already uses. The template puts both URLs on
 * the section as custom properties (molosoc_landing_b_hero_background_style())
 * and molosoc_landing_b_head() preloads them, so the preloaded and the
 * painted URL come from this one place.
 *
 * @return array[] 'mobile' / 'desktop' => array( 'url' => …, 'media' => … ).
 */
function molosoc_landing_b_hero_background() {
	$dir = get_stylesheet_directory_uri() . '/assets/images/landing-b/';
	return array(
		'mobile'  => array( 'url' => $dir . 'lpb-hero-bg-960.webp', 'media' => '(max-width: 900px)' ),
		'desktop' => array( 'url' => $dir . 'lpb-hero-bg-1920.webp', 'media' => '(min-width: 900.1px)' ),
	);
}

/**
 * Inline style for <section class="lpb-hero">: the custom properties the
 * .lpb-hero rule in landing-b.css reads (escaped for a style="" attribute).
 */
function molosoc_landing_b_hero_background_style() {
	$bg = molosoc_landing_b_hero_background();
	return esc_attr( sprintf(
		'--lpb-hero-bg-mobile: url(%s); --lpb-hero-bg-desktop: url(%s)',
		esc_url( $bg['mobile']['url'] ),
		esc_url( $bg['desktop']['url'] )
	) );
}

/**
 * Landing Page B <head> output (Issue #153), priority 1 so it lands before
 * the render-blocking stylesheets:
 *   1. preconnect to the Google Fonts origins;
 *   2. the hero image preload with fetchpriority="high" — otherwise the
 *      parser only reaches it in the body after ~10 stylesheets finish;
 *   3. the .lpb-hero background preload (Issue #157: the actual LCP
 *      element), one media-gated link per breakpoint so a phone fetches
 *      only the 960px copy;
 *   4. both Google Fonts stylesheets as non-blocking media="print" links
 *      that swap to media="all" once loaded (+ <noscript> fallback), see
 *      the Landing B branch of molosoc_enqueue_assets().
 * Printed raw (not enqueued) so WP-Optimize Minify leaves it alone.
 */
function molosoc_landing_b_head() {
	if ( ! is_page( 'hydratacni-navleky-molosoc' ) ) {
		return;
	}
	echo '<link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
	echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";

	$hero  = molosoc_landing_b_hero_image();
	$attrs = molosoc_landing_b_img_attrs( $hero['base'], $hero['widths'], $hero['sizes'] );
	// Same escaped values as the <img>, under the preload attribute names.
	$attrs = str_replace( array( 'src="', 'srcset="', 'sizes="' ), array( 'href="', 'imagesrcset="', 'imagesizes="' ), $attrs );
	echo '<link rel="preload" as="image" fetchpriority="high" ' . $attrs . '>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput -- every value is esc_url()/esc_attr()ed in molosoc_landing_b_img_attrs().

	foreach ( molosoc_landing_b_hero_background() as $bg ) {
		printf(
			'<link rel="preload" as="image" fetchpriority="high" href="%s" media="%s">' . "\n",
			esc_url( $bg['url'] ),
			esc_attr( $bg['media'] )
		);
	}

	foreach ( array( molosoc_fonts_url(), molosoc_landing_b_fonts_url() ) as $url ) {
		printf(
			'<link rel="stylesheet" href="%1$s" media="print" onload="this.media=\'all\'">' . "\n" .
			'<noscript><link rel="stylesheet" href="%1$s"></noscript>' . "\n",
			esc_url( $url )
		);
	}
}
add_action( 'wp_head', 'molosoc_landing_b_head', 1 );

/**
 * Landing Page A = the live foot-cover landing page, EN 'moisture-lock-foot-cover'
 * (page 869) / CZ 'hydratacni-navlek-na-nohy' (page 886), template
 * page-moisture-lock-foot-cover.php + product.css. Issue #190 gives it the
 * Landing B speed treatment (no-plugin-markup gate, LCP preload, non-blocking
 * fonts); this helper is the one place those new gates read the pair from.
 * The older gates (preconnect hints, the product.css enqueue branch) keep
 * their own literal pair so their tests stay byte-for-byte meaningful.
 */
function molosoc_is_landing_page_a() {
	return is_page( array( 'moisture-lock-foot-cover', 'hydratacni-navlek-na-nohy' ) );
}

/**
 * The hero still of Landing Page A — the LCP element on phones (Lighthouse
 * mobile, Issue #190: img.molosoc-orbit-model, 1440x1440, ~43 KB). The
 * template hardcodes this same URL on its <img> (tests/test_static_model_still.py
 * pins it there); molosoc_landing_a_head() preloads it so the request starts
 * with the HTML instead of after the head's stylesheets have parsed.
 */
function molosoc_landing_a_hero_still_url() {
	return 'https://molosoc.com/wp-content/uploads/2026/10/molosoc-hero-still.webp';
}

/**
 * Landing Page A <head> output (Issue #190), priority 1 so it lands before
 * the render-blocking stylesheets — the same two moves molosoc_landing_b_head()
 * makes for B, nothing page-visible:
 *   1. the hero still preload with fetchpriority="high" (the <img> already
 *      carries fetchpriority="high", but the parser only reaches it after
 *      the head's stylesheets, which is where Lighthouse's 1.6 s LCP "load
 *      delay" came from);
 *   2. the site Google Fonts stylesheet as a non-blocking media="print"
 *      link that swaps to media="all" once loaded (+ <noscript> fallback);
 *      the Landing A branch of molosoc_enqueue_assets() dequeues the
 *      blocking handle. display=swap is already in the URL, so text renders
 *      in the fallback face until the files arrive — exactly as on B.
 * The preconnect hints for the fonts origins are printed by the
 * molosoc_landing_preconnect_hints() hook above (same priority).
 * Printed raw (not enqueued) so WP-Optimize Minify leaves it alone.
 */
function molosoc_landing_a_head() {
	if ( ! molosoc_is_landing_page_a() ) {
		return;
	}
	printf(
		'<link rel="preload" as="image" fetchpriority="high" href="%s">' . "\n",
		esc_url( molosoc_landing_a_hero_still_url() )
	);
	printf(
		'<link rel="stylesheet" href="%1$s" media="print" onload="this.media=\'all\'">' . "\n" .
		'<noscript><link rel="stylesheet" href="%1$s"></noscript>' . "\n",
		esc_url( molosoc_fonts_url() )
	);
}
add_action( 'wp_head', 'molosoc_landing_a_head', 1 );

/**
 * Microsoft Clarity consent replay (Issue #190, "Clarity starts a new session
 * on every page").
 *
 * Clarity is loaded by the Microsoft Clarity plugin (clarity_add_script_to_header
 * on wp_head, priority 10 — the stub + async tag, no consent handling of its
 * own). The cookie banner is WPConsent, which stores the visitor's decision
 * in the `wpconsent_preferences` cookie ({"essential":true,"statistics":…,
 * "marketing":…}) and, on the click itself, already tells Clarity via
 * window.clarity('consentv2', …) on its `wpconsent_consent_saved` event. It
 * never replays that stored decision on the NEXT page load, so with the
 * project's "require cookie consent" setting Clarity ran cookieless on every
 * page after the first: a fresh user ID and a one-page session each time
 * (landing B → product → cart showed as three sessions).
 *
 * This prints, right after the plugin's stub (priority 11), the stored
 * decision as Clarity's Consent API v2 call — analytics_Storage from the
 * "statistics" category, ad_Storage from "marketing", each 'granted' only
 * when that category was accepted and 'denied' otherwise — and re-sends it on
 * every later `wpconsent_consent_saved` so the page-load path and the click
 * path can never disagree. Visitors without a stored decision get no call at
 * all (Clarity's default is denied/cookieless until the banner is answered,
 * when WPConsent's own handler fires). The call is queued through the same
 * `clarity.q` stub the plugin snippet defines, so it is processed as soon as
 * the tag loads; if the plugin ever prints later than this, the stub is
 * created here with the identical shape and the plugin's `c[a] = c[a] || …`
 * keeps it. Raw wp_head markup, not an enqueue/inline-script, so WP-Optimize
 * Minify cannot bundle or drop it (see the sticky-CTA data print above).
 */
function molosoc_clarity_consent_replay() {
	?>
<script>
(function (w, d) {
	function signal(p) {
		if (!p || typeof p !== 'object') { return; }
		w.clarity = w.clarity || function () { (w.clarity.q = w.clarity.q || []).push(arguments); };
		w.clarity('consentv2', {
			ad_Storage: p.marketing ? 'granted' : 'denied',
			analytics_Storage: p.statistics ? 'granted' : 'denied'
		});
	}
	var parts = ('; ' + d.cookie).split('; wpconsent_preferences=');
	if (parts.length === 2) {
		var raw = parts.pop().split(';').shift(), prefs = null;
		try { prefs = JSON.parse(raw); } catch (e) {
			try { prefs = JSON.parse(decodeURIComponent(raw)); } catch (e2) { prefs = null; }
		}
		signal(prefs);
	}
	w.addEventListener('wpconsent_consent_saved', function (e) { signal(e.detail); });
})(window, document);
</script>
	<?php
}
add_action( 'wp_head', 'molosoc_clarity_consent_replay', 11 );

/**
 * Landing Page B document title. Issue #153 stripped the working label
 * "(varianta, koncept)" of page 1037's WP title from the <title>; Issue #161
 * (keyword retarget to "maska na nohy", KW Everywhere CZ 2026-10-14) replaces
 * the whole <title> for this page with a fixed string, so the post title in
 * wp-admin (label included) is untouched and the separator is the "|" the
 * brief asks for rather than WordPress' en dash. pre_get_document_title is
 * returned by wp_get_document_title() verbatim (no esc_html), which is why
 * this is a plain constant — the Landing B schema include reuses it as the
 * WebPage name. Keep it in sync with the H1 in
 * page-hydratacni-navleky-molosoc.php (tests/test_landing_b_template.py).
 */
function molosoc_landing_b_document_title() {
	return 'Hydratační maska na nohy na opakované použití | Molosoc';
}
add_filter( 'pre_get_document_title', function ( $title ) {
	if ( is_page( 'hydratacni-navleky-molosoc' ) ) {
		return molosoc_landing_b_document_title();
	}
	return $title;
} );

/**
 * Category page ("Reusable Foot Covers") schema markup.
 * A normal template (unlike front-page.php) doesn't build its own <head> —
 * get_header() already calls wp_head(), so this hooks into that instead of
 * being printed directly in the template file.
 * Source: content/molosoc-site/02-category/category-schema.html.
 */
function molosoc_category_schema() {
	if ( ! is_page( 'foot-covers' ) ) {
		return;
	}
	?>
	<meta name="description" content="Skip the single-use sock mask. Molosoc's reusable, moisture-lock foot cover works with any cream you own — less mess, no salon trip, same soft results.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "CollectionPage",
	      "@id": "https://molosoc.com/foot-covers/#webpage",
	      "url": "https://molosoc.com/foot-covers/",
	      "name": "Reusable Foot Covers | Moisture-Lock Foot Cover — Molosoc",
	      "description": "Skip the single-use sock mask. Molosoc's reusable, moisture-lock foot cover works with any cream you own — less mess, no salon trip, same soft results.",
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "about": { "@id": "https://molosoc.com/#organization" },
	      "breadcrumb": { "@id": "https://molosoc.com/foot-covers/#breadcrumb" },
	      "mainEntity": { "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#product" },
	      "inLanguage": "en"
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/foot-covers/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Foot Covers", "item": "https://molosoc.com/foot-covers/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_category_schema' );

/**
 * Homepage schema markup — Organization/WebSite/WebPage, ported from
 * homepage-preview.html's own <head> block. front-page.php builds its own
 * <head> and calls wp_head() directly (see that file's header comment for
 * why it skips get_header()), so this hooks in the same way the category
 * page's schema does rather than being printed inline in the template.
 * Defines the #organization and #website @ids the category (and product)
 * page schema already reference — those were dangling on the live site
 * until this existed.
 * Source: content/molosoc-site/01-homepage/homepage-schema.html.
 */
function molosoc_homepage_schema() {
	if ( ! is_front_page() ) {
		return;
	}
	?>
	<meta name="description" content="Molosoc helps you finish the foot care routine you already started — reusable, cream-agnostic, and built for real bathroom drawers, not perfect ones.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Organization",
	      "@id": "https://molosoc.com/#organization",
	      "name": "Molosoc",
	      "url": "https://molosoc.com/",
	      "description": "Molosoc helps you finish the foot care routine you already started — reusable, cream-agnostic, and built for real bathroom drawers, not perfect ones.",
	      "logo": {
	        "@type": "ImageObject",
	        "url": "https://molosoc.com/wp-content/uploads/2026/06/MOLOSOC-Logo-TM.png"
	      },
	      "sameAs": [
	        "https://www.facebook.com/molosoc",
	        "https://www.instagram.com/molosoc_/",
	        "https://www.tiktok.com/@molosoc",
	        "https://www.youtube.com/@Molosoc",
	        "https://www.linkedin.com/in/molosoc/",
	        "https://x.com/Molosoc_"
	      ]
	    },
	    {
	      "@type": "WebSite",
	      "@id": "https://molosoc.com/#website",
	      "url": "https://molosoc.com/",
	      "name": "Molosoc",
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "inLanguage": "en"
	    },
	    {
	      "@type": "WebPage",
	      "@id": "https://molosoc.com/#webpage",
	      "url": "https://molosoc.com/",
	      "name": "Molosoc® | Foot Care That Actually Sticks",
	      "description": "Molosoc helps you finish the foot care routine you already started — reusable, cream-agnostic, and built for real bathroom drawers, not perfect ones.",
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "about": { "@id": "https://molosoc.com/#organization" },
	      "inLanguage": "en"
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_homepage_schema' );

/**
 * Product page schema markup, ported from product-preview.html's own
 * <head> block. Gated on is_page('moisture-lock-foot-cover') — the live
 * page at /foot-covers/moisture-lock-foot-cover/ turned out to be a
 * regular WP Page (page-id-951, page-template-default), not a WooCommerce
 * 'product' CPT despite the woocommerce-* body classes (WooCommerce is
 * just active site-wide); is_singular('product') never matched it. Same
 * is_page() convention as molosoc_category_schema() above.
 * Two deltas from the preview's source block, both stale content bugs, not
 * design choices: "sku" dropped (was a literal "[INSERT: SKU — not yet
 * assigned]" placeholder — schema.org doesn't require it, and shipping the
 * placeholder text as the real value is worse than omitting the field),
 * and "image" swapped from hero_pair_bedroom.jpg (that file's own comment
 * says it's no longer used on this page, replaced by the molosoc-3d.glb
 * hero) to 3d_render_01_front_nobg.png, the product render actually in use
 * elsewhere on the live site today.
 * Source: content/molosoc-site/03-product/product-schema.html.
 */
function molosoc_product_schema() {
	if ( ! is_page( 'moisture-lock-foot-cover' ) ) {
		return;
	}
	?>
	<meta name="description" content="Real before/after results, not filters. The reusable foot cover that locks in your favorite cream, cuts the mess, and makes your routine actually stick.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Product",
	      "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#product",
	      "name": "Molosoc Foot Cover",
	      "description": "A reusable, moisture-lock foot cover that seals your favorite cream against the skin — cutting the mess and making your foot care routine actually stick. Works with any cream you already own.",
	      "brand": { "@id": "https://molosoc.com/#organization" },
	      "image": "https://molosoc.com/wp-content/uploads/2026/07/3d_render_01_front_nobg.png",
	      "url": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/",
	      "category": "Foot Care",
	      "offers": {
	        "@type": "Offer",
	        "url": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/",
	        "priceCurrency": "CZK",
	        "price": "229",
	        "availability": "https://schema.org/InStock",
	        "itemCondition": "https://schema.org/NewCondition"
	      }
	    },
	    {
	      "@type": "WebPage",
	      "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#webpage",
	      "url": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/",
	      "name": "Molosoc Foot Cover — The Cream You Already Own, Finally Working",
	      "description": "Real before/after results, not filters. The reusable foot cover that locks in your favorite cream, cuts the mess, and makes your routine actually stick.",
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "about": { "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#product" },
	      "breadcrumb": { "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#breadcrumb" },
	      "inLanguage": "en"
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Foot Covers", "item": "https://molosoc.com/foot-covers/" },
	        { "@type": "ListItem", "position": 3, "name": "Molosoc Foot Cover", "item": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_product_schema' );

/**
 * Pillar 1 — Cracked Heels — schema markup, ported from
 * content/molosoc-site/04-pillar1-cracked-heels/pillar1-cracked-heels-
 * schema.html. Same is_page() convention as the category/product schema
 * functions above (a normal template calling get_header(), which already
 * calls wp_head(), rather than front-page.php's self-built <head>).
 * FAQPage answers are kept in sync with this page's own copy (see
 * page-cracked-heels.php) — content/.../pillar1-cracked-heels-copy.md is
 * the locked source for both.
 */
function molosoc_pillar1_schema() {
	if ( ! is_page( 'cracked-heels' ) ) {
		return;
	}
	?>
	<meta name="description" content="Cracked heels aren't just dry skin — here's what's really causing them, what makes them worse, and what actually helps (without the gimmicks).">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/cracked-heels/#article",
	      "headline": "Cracked Heels: Why They Happen and How to Actually Fix Them",
	      "description": "Cracked heels aren't just dry skin — here's what's really causing them, what makes them worse, and what actually helps (without the gimmicks).",
	      "url": "https://molosoc.com/cracked-heels/",
	      "mainEntityOfPage": "https://molosoc.com/cracked-heels/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-30",
	      "dateModified": "2026-07-30",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/cracked-heels/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What causes cracked heels?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Cracked heels form when heel skin dries out and loses the elasticity it needs to stretch under pressure. The heel's outer edge carries the most weight with every step, so dry, inflexible skin in that spot is the first to split. Standing for long stretches, especially in open-back shoes, speeds this up by increasing both pressure and moisture loss."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What are painful deep cracked heels?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Painful deep cracked heels are cracks that hurt with every step because they've gone past surface dryness into a deeper layer of skin. At this stage, occasional moisturizing isn't enough — the skin needs consistent, sealed-in moisture to actually recover."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What are severe cracked heels?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Severe cracked heels are cracks that have widened, deepened, and can bleed. This level requires a daily routine that's actually followed through, not an occasional cream application, to give the skin a real chance to rebuild."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/cracked-heels/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Cracked Heels", "item": "https://molosoc.com/cracked-heels/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_pillar1_schema' );

/**
 * Pillar 2 — Ingrown Toenails — schema markup, ported from
 * content/molosoc-site/05-pillar2-ingrown-toenails/pillar2-ingrown-
 * toenails-schema.html. Same is_page() convention as molosoc_pillar1_schema()
 * above. FAQPage answers are kept in sync with this page's own copy (see
 * page-ingrown-toenails.php) — content/.../pillar2-ingrown-toenails-copy.md
 * is the locked source for both.
 */
function molosoc_pillar2_schema() {
	if ( ! is_page( 'ingrown-toenails' ) ) {
		return;
	}
	?>
	<meta name="description" content="An ingrown toenail can go from mildly annoying to genuinely painful fast. Here's what causes it, what actually helps at home, and when it's more than a nail problem.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/ingrown-toenails/#article",
	      "headline": "Ingrown Toenails: Why They Happen and What Actually Helps",
	      "description": "An ingrown toenail can go from mildly annoying to genuinely painful fast. Here's what causes it, what actually helps at home, and when it's more than a nail problem.",
	      "url": "https://molosoc.com/ingrown-toenails/",
	      "mainEntityOfPage": "https://molosoc.com/ingrown-toenails/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-30",
	      "dateModified": "2026-07-30",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/ingrown-toenails/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What causes ingrown toenails?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Ingrown toenails happen when the nail's edge grows down into the surrounding skin instead of straight across. Tight-fitting shoes press skin against the nail edge, and nails trimmed too short or rounded give that edge room to dig in as it grows back. Without a change to nail shape or footwear, the same pressure point tends to recreate the problem repeatedly."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "Do ingrown toenails go away on their own?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "A mild ingrown toenail can resolve on its own once the pressure causing it — tight shoes, a too-short trim — is removed and the skin has room to heal. Increasing redness, swelling, or pain that doesn't ease up after a few days means it isn't resolving on its own and needs more attention."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "Why does my big toenail hurt?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Pain concentrated at the big toenail is almost always pressure-related, coming from the nail edge, tight footwear, or both at once."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What causes an ingrown big toe?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "The big toe is the most common site for an ingrown nail because it takes the most pressure with every step, making it the spot most likely to develop a nail edge that grows into skin."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/ingrown-toenails/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Ingrown Toenails", "item": "https://molosoc.com/ingrown-toenails/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_pillar2_schema' );

/**
 * Pillar 5 — Cream That Works — schema markup, ported from
 * content/molosoc-site/08-pillar5-cream-that-works/pillar5-cream-that-
 * works-schema.html. Same is_page() convention as molosoc_pillar1_schema()/
 * molosoc_pillar2_schema() above. FAQPage answers are kept in sync with
 * this page's own copy (see page-foot-cream-that-works.php) —
 * content/.../pillar5-cream-that-works-copy.md is the locked source for
 * both.
 */
function molosoc_pillar5_schema() {
	if ( ! is_page( 'foot-cream-that-works' ) ) {
		return;
	}
	?>
	<meta name="description" content="Tried every foot cream with no results? The cream probably isn't the problem — here's why it fails and what actually makes it work.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/foot-cream-that-works/#article",
	      "headline": "Does Foot Cream Actually Work? Why It Fails, and What Fixes It",
	      "description": "Tried every foot cream with no results? The cream probably isn't the problem — here's why it fails and what actually makes it work.",
	      "url": "https://molosoc.com/foot-cream-that-works/",
	      "mainEntityOfPage": "https://molosoc.com/foot-cream-that-works/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/foot-cream-that-works/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "Does foot cream actually work?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Foot cream does work — the reason it often seems like it doesn't is that most of it never gets the chance to fully absorb before it rubs off on socks, sheets, or floors. Given sustained, uninterrupted contact with skin, the same cream tends to perform much better."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "How long does foot cream take to absorb?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Most creams need sustained, uninterrupted contact with skin to fully absorb — often longer than the few minutes most routines actually give them before socks or shoes go back on."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "Should you put socks on after foot cream?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Yes — socks after cream help hold moisture against the skin longer than bare feet do, which is part of why the classic combination of cream plus socks works better than cream applied alone."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "How do you get soft feet overnight?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "The traditional approach is applying a heavier cream and sealing it under socks overnight, which gives skin hours of uninterrupted contact time to absorb. A shorter, focused session with the cream sealed against the skin can achieve much of that same result without needing to commit to wearing anything all night."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/foot-cream-that-works/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Cream That Works", "item": "https://molosoc.com/foot-cream-that-works/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_pillar5_schema' );

/**
 * Pillar 3 — Hardened Skin & Calluses — schema markup, ported from
 * content/molosoc-site/06-pillar3-hardened-skin-calluses/pillar3-hardened-
 * skin-calluses-schema.html. Same is_page() convention as
 * molosoc_pillar1_schema()/molosoc_pillar2_schema() above. FAQPage answers
 * are kept in sync with this page's own copy (see
 * page-hardened-skin-calluses.php) — content/.../pillar3-hardened-skin-
 * calluses-copy.md is the locked source for both.
 */
function molosoc_pillar3_schema() {
	if ( ! is_page( 'hardened-skin-calluses' ) ) {
		return;
	}
	?>
	<meta name="description" content="Thick, hardened skin on your feet doesn't happen overnight — and it doesn't have to stay that way. Here's why calluses form and what actually softens them.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/hardened-skin-calluses/#article",
	      "headline": "Hardened Skin & Calluses on Feet: Why They Form and What Softens Them",
	      "description": "Thick, hardened skin on your feet doesn't happen overnight — and it doesn't have to stay that way. Here's why calluses form and what actually softens them.",
	      "url": "https://molosoc.com/hardened-skin-calluses/",
	      "mainEntityOfPage": "https://molosoc.com/hardened-skin-calluses/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/hardened-skin-calluses/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What is a foot callus?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "A foot callus is an area of thickened, hardened skin that forms where pressure and friction repeat in the same spot, most often the ball of the foot or the heel."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What's the difference between corns and calluses?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Corns are smaller, more concentrated areas of hardened skin, usually on or between toes. Calluses cover broader, flatter areas. Both form for the same reason — repeated pressure and friction — just in different places."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What is the cure for a foot corn?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "There's no single cure that removes a foot corn permanently in one step — effective treatment softens the thickened skin gradually with consistent moisture, rather than removing it all at once."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What is the best callus treatment?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Effective callus treatment focuses on consistent softening rather than one-time removal — moisture needs to reach the thickened skin regularly for the softening to actually last between sessions."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/hardened-skin-calluses/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Hardened Skin & Calluses", "item": "https://molosoc.com/hardened-skin-calluses/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_pillar3_schema' );

/**
 * Pillar 4 — Dry Skin on Feet — schema markup, ported from
 * content/molosoc-site/07-pillar4-dry-skin-feet/pillar4-dry-skin-feet-
 * schema.html. Same is_page() convention as molosoc_pillar1_schema()/
 * molosoc_pillar2_schema() above. FAQPage answers are kept in sync with
 * this page's own copy (see page-dry-skin-feet.php) —
 * content/.../pillar4-dry-skin-feet-copy.md is the locked source for both.
 */
function molosoc_pillar4_schema() {
	if ( ! is_page( 'dry-skin-feet' ) ) {
		return;
	}
	?>
	<meta name="description" content="Still dry after moisturizing? Here's what actually causes dry skin on feet, why cream alone doesn't fix it, and what actually helps it stop.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/dry-skin-feet/#article",
	      "headline": "Dry Skin on Feet: Why It Happens and What Actually Helps",
	      "description": "Still dry after moisturizing? Here's what actually causes dry skin on feet, why cream alone doesn't fix it, and what actually helps it stop.",
	      "url": "https://molosoc.com/dry-skin-feet/",
	      "mainEntityOfPage": "https://molosoc.com/dry-skin-feet/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/dry-skin-feet/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What causes dry skin on feet?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Soles have no oil glands the way most of the rest of the skin does, so they rely entirely on external moisture to stay soft. Enclosed feet also lose moisture to socks, shoes, and air circulation throughout the day, and seasonal triggers like indoor heating, cold air, and hot showers strip moisture faster than usual."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "Why are my feet so dry even when I moisturize?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Cream applied and left uncovered gets absorbed by socks or rubbed off on floors within minutes, long before the skin has had a real chance to take it in. The fix isn't a thicker layer or a pricier formula — it's uninterrupted contact time so the cream can actually absorb instead of transferring elsewhere."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/dry-skin-feet/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Dry Skin on Feet", "item": "https://molosoc.com/dry-skin-feet/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_pillar4_schema' );

/**
 * Spoke 1 — Ingrown Toenails Treatment — schema markup, ported from
 * content/molosoc-site/09-spoke1-ingrown-toenails-treatment/spoke1-
 * ingrown-toenails-treatment-schema.html. Same is_page() convention as
 * molosoc_pillar1_schema()/molosoc_pillar2_schema() above. FAQPage answers
 * are kept in sync with this page's own copy (see page-treatment.php) —
 * content/.../spoke1-ingrown-toenails-treatment-copy.md is the locked
 * source for both.
 */
function molosoc_spoke1_schema() {
	if ( ! is_page( 'treatment' ) ) {
		return;
	}
	?>
	<meta name="description" content="From home softening to when a doctor needs to get involved — here's what actually treats an ingrown toenail, and what makes it worse.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/ingrown-toenails/treatment/#article",
	      "headline": "Ingrown Toenails Treatment: What Actually Works",
	      "description": "From home softening to when a doctor needs to get involved — here's what actually treats an ingrown toenail, and what makes it worse.",
	      "url": "https://molosoc.com/ingrown-toenails/treatment/",
	      "mainEntityOfPage": "https://molosoc.com/ingrown-toenails/treatment/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/ingrown-toenails/treatment/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "How do you treat ingrown toenails?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Treating an ingrown toenail starts with softening the skin around the nail, since firm, dry skin is what the nail edge is pushing against. A warm soak helps soften skin and ease discomfort, but the real improvement comes once the underlying pressure point is relieved, giving the nail room to grow out properly instead of into the skin."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "How do you get rid of ingrown toenails?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Getting rid of an ingrown toenail for good means combining consistent skin softening with a genuine change to whatever's been causing the pressure — footwear, trim habit, or both — rather than only treating the current episode. Trimming the nail straight across, instead of rounding the corners, also helps prevent the same problem from repeating."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/ingrown-toenails/treatment/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Ingrown Toenails", "item": "https://molosoc.com/ingrown-toenails/" },
	        { "@type": "ListItem", "position": 3, "name": "Ingrown Toenails Treatment", "item": "https://molosoc.com/ingrown-toenails/treatment/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_spoke1_schema' );

/**
 * Spoke 2 — Callus Remover — schema markup, ported from content/molosoc-
 * site/10-spoke2-callus-remover/spoke2-callus-remover-schema.html.
 */
function molosoc_spoke2_schema() {
	if ( ! is_page( 'callus-remover' ) ) {
		return;
	}
	?>
	<meta name="description" content="Files, creams, pumice stones — here's an honest look at what actually removes hard skin, and why it keeps coming back no matter which one you use.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/hardened-skin-calluses/callus-remover/#article",
	      "headline": "Callus Remover: What Actually Works (And Why It Doesn't Last)",
	      "description": "Files, creams, pumice stones — here's an honest look at what actually removes hard skin, and why it keeps coming back no matter which one you use.",
	      "url": "https://molosoc.com/hardened-skin-calluses/callus-remover/",
	      "mainEntityOfPage": "https://molosoc.com/hardened-skin-calluses/callus-remover/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/hardened-skin-calluses/callus-remover/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What is the best callus remover?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "There's no single tool or product that removes a callus permanently. Filing and pumice stones physically wear down thickened skin, while acid-based removers soften it chemically — both work on the skin that's already there, but neither changes the pressure point that caused it, which is why hardened skin tends to build back up in the same spot."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "How do you remove thick dead skin from feet at home?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Soak feet first to soften thickened skin, then file gradually in short sessions rather than one aggressive pass, to avoid over-thinning the skin underneath. After removal, consistent moisture is what keeps the results from resetting quickly."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "How do you get rid of hard skin on feet permanently?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Permanent improvement requires more than one-time removal — the pressure point that caused the hardened skin, such as footwear or gait, is usually still there afterward. Consistent moisture between removal sessions keeps skin more flexible under pressure, which slows how quickly it thickens back up."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/hardened-skin-calluses/callus-remover/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Hardened Skin & Calluses", "item": "https://molosoc.com/hardened-skin-calluses/" },
	        { "@type": "ListItem", "position": 3, "name": "Callus Remover", "item": "https://molosoc.com/hardened-skin-calluses/callus-remover/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_spoke2_schema' );

/**
 * Spoke 3 — How to Prevent Ingrown Toenails — schema markup, ported from
 * content/molosoc-site/11-spoke3-prevent-ingrown-toenails/spoke3-prevent-
 * ingrown-toenails-schema.html.
 */
function molosoc_spoke3_schema() {
	if ( ! is_page( 'prevent' ) ) {
		return;
	}
	?>
	<meta name="description" content="If this isn't your first ingrown toenail, the fix isn't just treating this one — it's changing what keeps causing them. Here's what actually prevents it.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/ingrown-toenails/prevent/#article",
	      "headline": "How to Prevent Ingrown Toenails (For Good)",
	      "description": "If this isn't your first ingrown toenail, the fix isn't just treating this one — it's changing what keeps causing them. Here's what actually prevents it.",
	      "url": "https://molosoc.com/ingrown-toenails/prevent/",
	      "mainEntityOfPage": "https://molosoc.com/ingrown-toenails/prevent/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/ingrown-toenails/prevent/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "Why do I keep getting ingrown toenails?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Repeat ingrown toenails usually come from the same nail-cutting habit or footwear recreating the same pressure point every time. Resolving one episode deals with the symptom in front of you — it doesn't change the trim habit or shoe fit that caused it, so the same conditions are still in place for next time."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "How do you stop ingrown toenails?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Trim the nail straight across, leaving the corners slightly longer than the center, so the nail has a straighter path to grow along. Choose shoes with enough room at the toe box to remove the pressure that pushes the nail edge into skin, and keep the surrounding skin consistently soft as an ongoing habit rather than only after a problem starts."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/ingrown-toenails/prevent/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Ingrown Toenails", "item": "https://molosoc.com/ingrown-toenails/" },
	        { "@type": "ListItem", "position": 3, "name": "How to Prevent Ingrown Toenails", "item": "https://molosoc.com/ingrown-toenails/prevent/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_spoke3_schema' );

/**
 * Spoke 4 — Cracked Heels Cream — schema markup, ported from
 * content/molosoc-site/12-spoke4-cracked-heels-cream/spoke4-cracked-
 * heels-cream-schema.html.
 */
function molosoc_spoke4_schema() {
	if ( ! is_page( 'cracked-heels-cream' ) ) {
		return;
	}
	?>
	<meta name="description" content="Not all cracked-heel creams work the same way. Here's what actually matters — the ingredients, the timing, and why even a good cream can fail without the right routine.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/cracked-heels/cracked-heels-cream/#article",
	      "headline": "Cracked Heels Cream: What Actually Makes One Work",
	      "description": "Not all cracked-heel creams work the same way. Here's what actually matters — the ingredients, the timing, and why even a good cream can fail without the right routine.",
	      "url": "https://molosoc.com/cracked-heels/cracked-heels-cream/",
	      "mainEntityOfPage": "https://molosoc.com/cracked-heels/cracked-heels-cream/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/cracked-heels/cracked-heels-cream/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What should you look for in a cracked heels cream?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Look for urea or similar humectants, which draw moisture into skin and help soften thickened areas. Thicker balms suit more severe cracking since they sit on skin longer, while lighter lotions work well for everyday maintenance. Ingredients matter less than how consistently the cream is used with enough contact time to actually absorb."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What is the best cream for cracked heels?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "The best cream for cracked heels depends far more on how severe the cracking is than on brand or price — plenty of inexpensive formulas contain the same core humectants as premium ones. In most cases, a cream already owned is capable of doing the job; the missing piece is usually consistency and contact time, not a better product."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/cracked-heels/cracked-heels-cream/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Cracked Heels", "item": "https://molosoc.com/cracked-heels/" },
	        { "@type": "ListItem", "position": 3, "name": "Cracked Heels Cream", "item": "https://molosoc.com/cracked-heels/cracked-heels-cream/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_spoke4_schema' );

/**
 * Spoke 5 — Cracked Heels Treatment — schema markup, ported from
 * content/molosoc-site/13-spoke5-cracked-heels-treatment/spoke5-cracked-
 * heels-treatment-schema.html.
 */
function molosoc_spoke5_schema() {
	if ( ! is_page( 'cracked-heels-treatment' ) ) {
		return;
	}
	?>
	<meta name="description" content="Cream alone rarely fixes cracked heels. Here's the full picture — exfoliation, moisture, and the one step most routines skip.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/cracked-heels/cracked-heels-treatment/#article",
	      "headline": "Cracked Heels Treatment: What Actually Works, Step by Step",
	      "description": "Cream alone rarely fixes cracked heels. Here's the full picture — exfoliation, moisture, and the one step most routines skip.",
	      "url": "https://molosoc.com/cracked-heels/cracked-heels-treatment/",
	      "mainEntityOfPage": "https://molosoc.com/cracked-heels/cracked-heels-treatment/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/cracked-heels/cracked-heels-treatment/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What is the actual treatment for cracked heels?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Effective cracked heel treatment requires three things together: removing built-up dead skin first, getting moisture into the skin rather than just on the surface, and sealing that moisture in for a real session. Cream applied alone, without removal or sealing, typically underperforms."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What are painful deep cracked heels, and when should you see a podiatrist?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Painful deep cracked heels are cracks that hurt with every step because they've gone past surface dryness into deeper skin. Sharp pain, a crack that doesn't respond to a week or two of consistent care, or any bleeding or signs of infection are reasons to see a podiatrist rather than continuing to self-treat."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/cracked-heels/cracked-heels-treatment/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Cracked Heels", "item": "https://molosoc.com/cracked-heels/" },
	        { "@type": "ListItem", "position": 3, "name": "Cracked Heels Treatment", "item": "https://molosoc.com/cracked-heels/cracked-heels-treatment/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_spoke5_schema' );

/**
 * Spoke 6 — How to Fix Cracked Heels Permanently — schema markup, ported
 * from content/molosoc-site/14-spoke6-fix-cracked-heels-permanently/
 * spoke6-fix-cracked-heels-permanently-schema.html.
 */
function molosoc_spoke6_schema() {
	if ( ! is_page( 'fix-permanently' ) ) {
		return;
	}
	?>
	<meta name="description" content="Cracked heels keep coming back for a reason — treatment fixes them once, but doesn't stop them from returning. Here's what actually makes it stick.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/cracked-heels/fix-permanently/#article",
	      "headline": "How to Fix Cracked Heels Permanently (Not Just Temporarily)",
	      "description": "Cracked heels keep coming back for a reason — treatment fixes them once, but doesn't stop them from returning. Here's what actually makes it stick.",
	      "url": "https://molosoc.com/cracked-heels/fix-permanently/",
	      "mainEntityOfPage": "https://molosoc.com/cracked-heels/fix-permanently/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/cracked-heels/fix-permanently/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "How do you fix cracked heels permanently?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Fixing cracked heels permanently requires consistency, not a stronger product. Treating one crack resolves what's visible but doesn't change the dryness and pressure that caused it, so the same spot stays vulnerable unless care becomes an ongoing habit rather than a one-time fix."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What are severe cracked heels?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Severe cracked heels are cracks that reopen repeatedly or reappear in the same spot every few months, rather than resolving as a one-off. Left unaddressed, each episode tends to be a little worse than the last — but once care becomes consistent rather than reactive, that cycle slows."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/cracked-heels/fix-permanently/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Cracked Heels", "item": "https://molosoc.com/cracked-heels/" },
	        { "@type": "ListItem", "position": 3, "name": "How to Fix Cracked Heels Permanently", "item": "https://molosoc.com/cracked-heels/fix-permanently/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_spoke6_schema' );

/**
 * Czech structured data (SEO remediation step 3C, 2026-08-16).
 *
 * The CZ pages render from the same bilingual templates as their EN
 * twins, but every schema function above is gated on the EN slug, so the
 * Czech pages shipped no JSON-LD at all. One function covers the seven
 * priority CZ URLs, mirroring each EN counterpart's graph shape with
 * Czech text taken from the pages' own rendered copy, canonical CZ
 * URLs/@ids, inLanguage "cs", and the live 229 CZK price on the product
 * landing. The CZ homepage already gets Organization/WebSite from
 * molosoc_homepage_schema() and is untouched.
 */
function molosoc_cz_schema() {
	if ( is_page( 'popraskane-paty' ) ) {
		?>
		<meta name="description" content="Popraskané paty vznikají, když kůže ztratí schopnost se natahovat pod tlakem — nejde o smůlu ani jen o suchou kůži. Co je skutečně způsobuje a co doopravdy pomáhá.">
		<script type="application/ld+json">
		{
		  "@context": "https://schema.org",
		  "@graph": [
		    {
		      "@type": "Article",
		      "@id": "https://molosoc.com/cz/popraskane-paty/#article",
		      "headline": "Popraskané paty: co se skutečně děje a co pomáhá",
		      "description": "Popraskané paty vznikají, když kůže ztratí schopnost se natahovat pod tlakem — nejde o smůlu ani jen o suchou kůži. Náprava je jednoduchá, pokud je pravidelná, ne příležitostná.",
		      "url": "https://molosoc.com/cz/popraskane-paty/",
		      "mainEntityOfPage": "https://molosoc.com/cz/popraskane-paty/",
		      "author": { "@id": "https://molosoc.com/#organization" },
		      "publisher": { "@id": "https://molosoc.com/#organization" },
		      "isPartOf": { "@id": "https://molosoc.com/#website" },
		      "datePublished": "2026-08-13",
		      "dateModified": "2026-08-13",
		      "inLanguage": "cs"
		    },
		    {
		      "@type": "FAQPage",
		      "@id": "https://molosoc.com/cz/popraskane-paty/#faq",
		      "mainEntity": [
		        {
		          "@type": "Question",
		          "name": "Proč vznikají popraskané paty?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Kůže na patě praská, když vyschne a ztratí pružnost potřebnou k natahování pod tlakem. Vnější okraj paty nese při každém kroku nejvíc váhy — suchá, nepružná kůže na tomto místě praská jako první. Dlouhé celodenní stání a boty s otevřenou patou zrychlují oba problémy najednou: víc tlaku, víc ztráty vlhkosti." }
		        },
		        {
		          "@type": "Question",
		          "name": "Co znamená, když popraskané paty bolí?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Prasklina, která bolí při každém kroku, už překonala povrchové sucho a zasahuje hlubší vrstvu kůže. Krém, který není zapečetěný na kůži, se otře dřív, než se vstřebá — víc produktu to nevyřeší, potřeba je delší kontakt a pravidelná, zapečetěná vlhkost." }
		        },
		        {
		          "@type": "Question",
		          "name": "Co jsou vážně popraskané paty?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Vážně popraskané paty se rozšiřují, prohlubují a mohou krvácet — příležitostné mazání krémem v této fázi nestačí. Kůže potřebuje každodenní rutinu, která se skutečně dodržuje, aby měla šanci se obnovit." }
		        }
		      ]
		    },
		    {
		      "@type": "BreadcrumbList",
		      "@id": "https://molosoc.com/cz/popraskane-paty/#breadcrumb",
		      "itemListElement": [
		        { "@type": "ListItem", "position": 1, "name": "Domů", "item": "https://molosoc.com/cz/molosoc-home-cestina/" },
		        { "@type": "ListItem", "position": 2, "name": "Popraskané paty", "item": "https://molosoc.com/cz/popraskane-paty/" }
		      ]
		    }
		  ]
		}
		</script>
		<?php
	} elseif ( is_page( 'zarostly-nehet' ) ) {
		?>
		<meta name="description" content="Zarostlý nehet začíná, když se okraj nehtu prohne nebo roste dolů do kůže vedle sebe. Proč vzniká, kdy odezní sám a co skutečně pomáhá.">
		<script type="application/ld+json">
		{
		  "@context": "https://schema.org",
		  "@graph": [
		    {
		      "@type": "Article",
		      "@id": "https://molosoc.com/cz/zarostly-nehet/#article",
		      "headline": "Zarostlý nehet: co se děje a co skutečně pomáhá",
		      "description": "Zarostlý nehet začíná ve chvíli, kdy se okraj nehtu prohne nebo roste dolů do kůže vedle sebe, místo aby rostl rovně přes ni. Proč vzniká, kdy odezní sám a co skutečně pomáhá.",
		      "url": "https://molosoc.com/cz/zarostly-nehet/",
		      "mainEntityOfPage": "https://molosoc.com/cz/zarostly-nehet/",
		      "author": { "@id": "https://molosoc.com/#organization" },
		      "publisher": { "@id": "https://molosoc.com/#organization" },
		      "isPartOf": { "@id": "https://molosoc.com/#website" },
		      "datePublished": "2026-08-13",
		      "dateModified": "2026-08-13",
		      "inLanguage": "cs"
		    },
		    {
		      "@type": "FAQPage",
		      "@id": "https://molosoc.com/cz/zarostly-nehet/#faq",
		      "mainEntity": [
		        {
		          "@type": "Question",
		          "name": "Proč vzniká zarostlý nehet?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Zarostlý nehet začíná ve chvíli, kdy se okraj nehtu prohne nebo roste dolů do kůže vedle sebe, místo aby rostl rovně přes ni. Těsná obuv tlačí kůži proti okraji nehtu a příliš krátké nebo zaoblené stříhání dává tomuto okraji prostor zarůst při dalším růstu." }
		        },
		        {
		          "@type": "Question",
		          "name": "Zmizí zarostlý nehet sám?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Mírně zarostlý nehet může odeznít sám, jakmile zmizí tlak, který ho způsobil — těsné boty, příliš krátké stříhání — a kůže dostane prostor se zahojit. Zesilující zarudnutí, otok nebo bolest, která po pár dnech neustupuje, znamenají, že už nejde jen o běžný tlak." }
		        },
		        {
		          "@type": "Question",
		          "name": "Proč se zarostlý nehet vrací?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Stejný tvar nehtu a stejné návyky s obuví znovu vytvářejí stejné místo tlaku — bez změny v jednom nebo druhém se problém typicky opakuje." }
		        }
		      ]
		    },
		    {
		      "@type": "BreadcrumbList",
		      "@id": "https://molosoc.com/cz/zarostly-nehet/#breadcrumb",
		      "itemListElement": [
		        { "@type": "ListItem", "position": 1, "name": "Domů", "item": "https://molosoc.com/cz/molosoc-home-cestina/" },
		        { "@type": "ListItem", "position": 2, "name": "Zarostlý nehet", "item": "https://molosoc.com/cz/zarostly-nehet/" }
		      ]
		    }
		  ]
		}
		</script>
		<?php
	} elseif ( is_page( 'kurici-oko' ) ) {
		?>
		<meta name="description" content="Kuří oko vzniká postupně, jako reakce kůže na opakovaný tlak a tření — a stejně postupně se dá i změkčit. Rozdíl mezi kuřím okem a mozolem a co skutečně pomáhá.">
		<script type="application/ld+json">
		{
		  "@context": "https://schema.org",
		  "@graph": [
		    {
		      "@type": "Article",
		      "@id": "https://molosoc.com/cz/kurici-oko/#article",
		      "headline": "Kuří oko a mozoly: proč vznikají a co je změkčí",
		      "description": "Kuří oko vzniká postupně, jako reakce kůže na opakovaný tlak a tření — a stejně postupně, s pravidelnou péčí, se dá i změkčit.",
		      "url": "https://molosoc.com/cz/kurici-oko/",
		      "mainEntityOfPage": "https://molosoc.com/cz/kurici-oko/",
		      "author": { "@id": "https://molosoc.com/#organization" },
		      "publisher": { "@id": "https://molosoc.com/#organization" },
		      "isPartOf": { "@id": "https://molosoc.com/#website" },
		      "datePublished": "2026-08-13",
		      "dateModified": "2026-08-13",
		      "inLanguage": "cs"
		    },
		    {
		      "@type": "FAQPage",
		      "@id": "https://molosoc.com/cz/kurici-oko/#faq",
		      "mainEntity": [
		        {
		          "@type": "Question",
		          "name": "Co je kuří oko a jak vzniká?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Opakovaný tlak a tření na stále stejném místě mění kůži v malý, tvrdý, soustředěný bod — to je kuří oko. Nejčastěji se objevuje na chodidle, mezi prsty nebo na patě — tedy přesně tam, kde se tlak při chůzi soustředí nejvíc. Kůže tloustne postupně, v průběhu týdnů opakovaného tlaku." }
		        },
		        {
		          "@type": "Question",
		          "name": "Jaký je rozdíl mezi kuřím okem a mozolem?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Kuří oko je menší a soustředěné do jednoho bodu, zatímco mozol pokrývá širší, plošší oblast — oba vznikají ze stejného důvodu, jen na jiném místě." }
		        },
		        {
		          "@type": "Question",
		          "name": "Proč namáčení a pilování nestačí?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Odloupnutí řeší jen kůži, která už je ztvrdlá — nemění tlak, který ji způsobil, takže se stejné místo znovu ztvrdne. Jakmile ztvrdlá kůže dosáhne určité tloušťky, začíná měnit rozložení váhy při každém kroku." }
		        }
		      ]
		    },
		    {
		      "@type": "BreadcrumbList",
		      "@id": "https://molosoc.com/cz/kurici-oko/#breadcrumb",
		      "itemListElement": [
		        { "@type": "ListItem", "position": 1, "name": "Domů", "item": "https://molosoc.com/cz/molosoc-home-cestina/" },
		        { "@type": "ListItem", "position": 2, "name": "Kuří oko a mozoly", "item": "https://molosoc.com/cz/kurici-oko/" }
		      ]
		    }
		  ]
		}
		</script>
		<?php
	} elseif ( is_page( 'navleky-na-nohy' ) ) {
		?>
		<meta name="description" content="Většina masek na nohy je na jedno použití — návlek Molosoc vydrží alespoň 10 použití. Funguje s krémem, který už doma máte: návlek zapečetí vlhkost, výběr krému zůstává na vás.">
		<script type="application/ld+json">
		{
		  "@context": "https://schema.org",
		  "@graph": [
		    {
		      "@type": "CollectionPage",
		      "@id": "https://molosoc.com/cz/navleky-na-nohy/#webpage",
		      "url": "https://molosoc.com/cz/navleky-na-nohy/",
		      "name": "Návleky na nohy | Hydratační návlek na nohy — Molosoc",
		      "description": "Většina masek na nohy je na jedno použití — návlek Molosoc vydrží alespoň 10 použití. Funguje s krémem, který už doma máte: návlek zapečetí vlhkost, výběr krému zůstává na vás.",
		      "isPartOf": { "@id": "https://molosoc.com/#website" },
		      "about": { "@id": "https://molosoc.com/#organization" },
		      "inLanguage": "cs"
		    },
		    {
		      "@type": "BreadcrumbList",
		      "@id": "https://molosoc.com/cz/navleky-na-nohy/#breadcrumb",
		      "itemListElement": [
		        { "@type": "ListItem", "position": 1, "name": "Domů", "item": "https://molosoc.com/cz/molosoc-home-cestina/" },
		        { "@type": "ListItem", "position": 2, "name": "Návleky na nohy", "item": "https://molosoc.com/cz/navleky-na-nohy/" }
		      ]
		    }
		  ]
		}
		</script>
		<?php
	} elseif ( is_page( 'hydratacni-navlek-na-nohy' ) ) {
		?>
		<meta name="description" content="Skutečné výsledky, žádné filtry. Návlek na nohy na opakované použití, který zapečetí váš oblíbený krém přímo na kůži — méně nepořádku a rutina, u které konečně vydržíte.">
		<script type="application/ld+json">
		{
		  "@context": "https://schema.org",
		  "@graph": [
		    {
		      "@type": "Product",
		      "@id": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/#product",
		      "name": "Návlek na nohy Molosoc",
		      "description": "Návlek na nohy na opakované použití, který zapečetí váš oblíbený krém přímo na kůži — méně nepořádku a rutina, u které konečně vydržíte. Funguje s jakýmkoli krémem, který už doma máte.",
		      "brand": { "@id": "https://molosoc.com/#organization" },
		      "image": "https://molosoc.com/wp-content/uploads/2026/07/3d_render_01_front_nobg.png",
		      "url": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/",
		      "category": "Péče o nohy",
		      "offers": {
		        "@type": "Offer",
		        "url": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/",
		        "priceCurrency": "CZK",
		        "price": "229",
		        "availability": "https://schema.org/InStock",
		        "itemCondition": "https://schema.org/NewCondition"
		      }
		    },
		    {
		      "@type": "WebPage",
		      "@id": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/#webpage",
		      "url": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/",
		      "name": "Návlek na nohy Molosoc — Krém, který už doma máte, konečně funguje",
		      "description": "Skutečné výsledky, žádné filtry. Návlek na nohy na opakované použití, který zapečetí váš oblíbený krém přímo na kůži — méně nepořádku a rutina, u které konečně vydržíte.",
		      "isPartOf": { "@id": "https://molosoc.com/#website" },
		      "about": { "@id": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/#product" },
		      "breadcrumb": { "@id": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/#breadcrumb" },
		      "inLanguage": "cs"
		    },
		    {
		      "@type": "BreadcrumbList",
		      "@id": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/#breadcrumb",
		      "itemListElement": [
		        { "@type": "ListItem", "position": 1, "name": "Domů", "item": "https://molosoc.com/cz/molosoc-home-cestina/" },
		        { "@type": "ListItem", "position": 2, "name": "Návleky na nohy", "item": "https://molosoc.com/cz/navleky-na-nohy/" },
		        { "@type": "ListItem", "position": 3, "name": "Návlek na nohy Molosoc", "item": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/" }
		      ]
		    }
		  ]
		}
		</script>
		<?php
	} elseif ( is_page( 'jak-odstranit' ) ) {
		?>
		<meta name="description" content="Neexistuje jeden nástroj, který kuří oko odstraní natrvalo — každá metoda, která funguje, musí řešit tlak, který ho způsobil. Co skutečně funguje a proč se kuří oko vrací.">
		<script type="application/ld+json">
		{
		  "@context": "https://schema.org",
		  "@graph": [
		    {
		      "@type": "Article",
		      "@id": "https://molosoc.com/cz/kurici-oko/jak-odstranit/#article",
		      "headline": "Jak odstranit kuří oko: co skutečně funguje",
		      "description": "Neexistuje jeden nástroj ani produkt, který kuří oko odstraní natrvalo — každá metoda, která skutečně funguje, musí následně řešit to samé: tlak, který ho způsobil.",
		      "url": "https://molosoc.com/cz/kurici-oko/jak-odstranit/",
		      "mainEntityOfPage": "https://molosoc.com/cz/kurici-oko/jak-odstranit/",
		      "author": { "@id": "https://molosoc.com/#organization" },
		      "publisher": { "@id": "https://molosoc.com/#organization" },
		      "isPartOf": { "@id": "https://molosoc.com/#website" },
		      "datePublished": "2026-08-13",
		      "dateModified": "2026-08-13",
		      "inLanguage": "cs"
		    },
		    {
		      "@type": "FAQPage",
		      "@id": "https://molosoc.com/cz/kurici-oko/jak-odstranit/#faq",
		      "mainEntity": [
		        {
		          "@type": "Question",
		          "name": "Co kuří oko skutečně odstraní?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Pilování fyzicky opotřebovává vrchní vrstvu ztvrdlé kůže, což funguje na povrchové nahromadění, ale nemění tlak, kvůli kterému pod ním znovu tvrdne nová kůže. Náplasti s kyselinou salicylovou změkčují a chemicky rozrušují ztvrdlou kůži — účinné, ale při přílišném používání mohou podráždit i zdravou kůži kolem." }
		        },
		        {
		          "@type": "Question",
		          "name": "Pomáhá namočení před pilováním?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Namočení změkčí ztvrdlou kůži ještě před pilováním, což zákrok usnadní a sníží riziko, že se odstraní i zdravá kůže pod ní. Mírné, povrchové kuří oko lze bezpečně řešit doma; cokoliv hlubšího, bolestivého nebo s náznakem infekce patří spíš k lékaři." }
		        },
		        {
		          "@type": "Question",
		          "name": "Proč se kuří oko vrací?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Žádná z těchto metod neřeší tlakový bod, který kuří oko způsobil — proto se na stejném místě obvykle znovu vytvoří. Čerstvě odkrytá kůže potřebuje po zákroku pravidelnou vlhkost — odstranění bez následné péče jen znovu nastaví stejný cyklus." }
		        }
		      ]
		    },
		    {
		      "@type": "BreadcrumbList",
		      "@id": "https://molosoc.com/cz/kurici-oko/jak-odstranit/#breadcrumb",
		      "itemListElement": [
		        { "@type": "ListItem", "position": 1, "name": "Domů", "item": "https://molosoc.com/cz/molosoc-home-cestina/" },
		        { "@type": "ListItem", "position": 2, "name": "Kuří oko a mozoly", "item": "https://molosoc.com/cz/kurici-oko/" },
		        { "@type": "ListItem", "position": 3, "name": "Jak odstranit kuří oko", "item": "https://molosoc.com/cz/kurici-oko/jak-odstranit/" }
		      ]
		    }
		  ]
		}
		</script>
		<?php
	} elseif ( is_page( 'na-chodidle' ) ) {
		?>
		<meta name="description" content="Kuří oko pod chodidlem nese tlak při každém kroku — to ho odlišuje od kuřího oka kdekoliv jinde na noze a mění to i to, co na něj skutečně pomáhá.">
		<script type="application/ld+json">
		{
		  "@context": "https://schema.org",
		  "@graph": [
		    {
		      "@type": "Article",
		      "@id": "https://molosoc.com/cz/kurici-oko/na-chodidle/#article",
		      "headline": "Kuří oko na chodidle: proč je jiné a co s ním",
		      "description": "Kuří oko pod chodidlem nese tlak při každém jednotlivém kroku, což ho odlišuje od kuřího oka kdekoliv jinde na noze — a mění to i to, co na něj skutečně pomáhá.",
		      "url": "https://molosoc.com/cz/kurici-oko/na-chodidle/",
		      "mainEntityOfPage": "https://molosoc.com/cz/kurici-oko/na-chodidle/",
		      "author": { "@id": "https://molosoc.com/#organization" },
		      "publisher": { "@id": "https://molosoc.com/#organization" },
		      "isPartOf": { "@id": "https://molosoc.com/#website" },
		      "datePublished": "2026-08-13",
		      "dateModified": "2026-08-13",
		      "inLanguage": "cs"
		    },
		    {
		      "@type": "FAQPage",
		      "@id": "https://molosoc.com/cz/kurici-oko/na-chodidle/#faq",
		      "mainEntity": [
		        {
		          "@type": "Question",
		          "name": "Čím se liší kuří oko na chodidle od kuřího oka na prstu?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Kuří oko na chodidle vzniká hlavně tlakem při chůzi, zatímco na prstech je hlavní příčinou tření o obuv. Opakovaný tlak při každém kroku ho zatlačuje hlouběji do kůže a bývá proto citelně bolestivější než na méně zatížených místech nohy." }
		        },
		        {
		          "@type": "Question",
		          "name": "Co pomáhá, když je kuří oko pod chodidlem?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Obuv s dostatečným prostorem a vložky, které rozloží tlak rovnoměrněji, snižují zátěž přesně v místě, kde kuří oko vzniká. Změkčení okolní kůže by mělo být prvním krokem, ne až tím posledním — dává tlaku menší šanci vytvořit znovu stejně tvrdý bod." }
		        },
		        {
		          "@type": "Question",
		          "name": "Kdy jít s kuřím okem na chodidle k lékaři?",
		          "acceptedAnswer": { "@type": "Answer", "text": "Pokud bolest natolik omezuje chůzi, že mění způsob, jak našlapujete, je čas nechat to posoudit odborníkem. Neobvyklý tvar, barva nebo bolest, která neodpovídá typickému kuřímu oku, mohou znamenat jiný problém, který si zaslouží vyšetření." }
		        }
		      ]
		    },
		    {
		      "@type": "BreadcrumbList",
		      "@id": "https://molosoc.com/cz/kurici-oko/na-chodidle/#breadcrumb",
		      "itemListElement": [
		        { "@type": "ListItem", "position": 1, "name": "Domů", "item": "https://molosoc.com/cz/molosoc-home-cestina/" },
		        { "@type": "ListItem", "position": 2, "name": "Kuří oko a mozoly", "item": "https://molosoc.com/cz/kurici-oko/" },
		        { "@type": "ListItem", "position": 3, "name": "Kuří oko na chodidle", "item": "https://molosoc.com/cz/kurici-oko/na-chodidle/" }
		      ]
		    }
		  ]
		}
		</script>
		<?php
	} elseif ( is_page( 'sucha-kuze-na-chodidlech' ) ) {
		?>
		<meta name="description" content="Suchá kůže na chodidlech: proč chodidla vysychají, jak o ně šetrně pečovat krémem a kdy je vhodné poradit se s lékařem nebo lékárníkem.">
		<script type="application/ld+json">
		{
		  "@context": "https://schema.org",
		  "@graph": [
		    {
		      "@type": "Article",
		      "@id": "https://molosoc.com/cz/sucha-kuze-na-chodidlech/#article",
		      "headline": "Suchá kůže na chodidlech: proč se vrací a jak o ni pečovat",
		      "description": "Suchá kůže na chodidlech: proč chodidla vysychají, jak o ně šetrně pečovat krémem a kdy je vhodné poradit se s lékařem nebo lékárníkem.",
		      "url": "https://molosoc.com/cz/sucha-kuze-na-chodidlech/",
		      "mainEntityOfPage": "https://molosoc.com/cz/sucha-kuze-na-chodidlech/",
		      "author": { "@id": "https://molosoc.com/#organization" },
		      "publisher": { "@id": "https://molosoc.com/#organization" },
		      "isPartOf": { "@id": "https://molosoc.com/#website" },
		      "datePublished": "2026-10-20",
		      "dateModified": "2026-10-20",
		      "inLanguage": "cs"
		    },
		    {
		      "@type": "BreadcrumbList",
		      "@id": "https://molosoc.com/cz/sucha-kuze-na-chodidlech/#breadcrumb",
		      "itemListElement": [
		        { "@type": "ListItem", "position": 1, "name": "Domů", "item": "https://molosoc.com/cz/molosoc-home-cestina/" },
		        { "@type": "ListItem", "position": 2, "name": "Suchá kůže na chodidlech", "item": "https://molosoc.com/cz/sucha-kuze-na-chodidlech/" }
		      ]
		    }
		  ]
		}
		</script>
		<?php
	}
}
add_action( 'wp_head', 'molosoc_cz_schema' );

/**
 * WordPress doesn't allow .glb uploads by default (not in its core mime
 * whitelist) — needed for the 3D product model in the media library.
 */
function molosoc_allow_glb_uploads( $mimes ) {
	$mimes['glb'] = 'model/gltf-binary';
	return $mimes;
}
add_filter( 'upload_mimes', 'molosoc_allow_glb_uploads' );

/**
 * Product-page trust-badge bars — recreates the two bands the OLD theme
 * shows on molosoc.com/product/molosoc-hydratacni-navleky-na-nohy/ (built
 * with Thrive Architect there), since nothing equivalent existed anywhere
 * in this theme. Styling in assets/css/product-trust-bars.css.
 *
 * Hooked on woocommerce_before_main_content at priority 5 — deliberately
 * BEFORE WooCommerce's own breadcrumb (hooked to the same action at
 * priority 20) and before woocommerce_output_content_wrapper() (priority
 * 10) opens #primary.content-area, so this renders as a full-bleed band
 * above the constrained content column, matching production's own
 * layout (its top bar sits above the breadcrumb too, full width).
 */
function molosoc_product_trust_bar_top() {
	if ( ! is_product() ) {
		return;
	}
	$molosoc_is_cz = function_exists( 'pll_current_language' ) && 'cz' === pll_current_language();
	?>
	<div class="molosoc-trust-bar molosoc-trust-bar--top">
		<div class="molosoc-trust-bar__inner">
			<div class="molosoc-trust-bar__item">
				<span class="molosoc-trust-bar__icon" aria-hidden="true">
					<svg viewBox="0 0 24 24"><path d="M1 3h13v13H1z"/><path d="M14 8h4l4 4v4h-8V8z"/><circle cx="6" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>
				</span>
				<div>
					<p class="molosoc-trust-bar__label"><?php echo esc_html( $molosoc_is_cz ? 'Rychlé dodání' : __( 'Fast Shipping', 'molosoc' ) ); ?></p>
					<p class="molosoc-trust-bar__sub"><?php echo esc_html( $molosoc_is_cz ? 'Odesíláme do 24 hodin' : __( 'We ship within 24 hours', 'molosoc' ) ); ?></p>
				</div>
			</div>
			<div class="molosoc-trust-bar__item">
				<span class="molosoc-trust-bar__icon" aria-hidden="true">
					<svg viewBox="0 0 24 24"><path d="M17 2l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
				</span>
				<div>
					<p class="molosoc-trust-bar__label"><?php echo esc_html( $molosoc_is_cz ? 'Snadné vrácení' : __( 'Easy Returns', 'molosoc' ) ); ?></p>
					<p class="molosoc-trust-bar__sub"><?php echo esc_html( $molosoc_is_cz ? 'Bez stresu, bez starostí' : __( 'No stress, no hassle', 'molosoc' ) ); ?></p>
				</div>
			</div>
			<div class="molosoc-trust-bar__item">
				<span class="molosoc-trust-bar__icon" aria-hidden="true">
					<svg viewBox="0 0 24 24"><path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5z"/><path d="M9 12l2 2 4-4"/></svg>
				</span>
				<div>
					<p class="molosoc-trust-bar__label"><?php echo esc_html( $molosoc_is_cz ? 'Bezpečná platba' : __( 'Secure Payment', 'molosoc' ) ); ?></p>
					<p class="molosoc-trust-bar__sub"><?php echo esc_html( $molosoc_is_cz ? '100% ochrana vašich údajů' : __( '100% protection for your data', 'molosoc' ) ); ?></p>
				</div>
			</div>
		</div>
	</div>
	<?php
}
add_action( 'woocommerce_before_main_content', 'molosoc_product_trust_bar_top', 5 );

/**
 * Bottom trust-badge bar — hooked on woocommerce_after_single_product,
 * which fires after woocommerce_output_content_wrapper_end() closes
 * #primary.content-area, so this is also a full-bleed band below the
 * constrained content column, matching production's bottom bar.
 */
function molosoc_product_trust_bar_bottom() {
	if ( ! is_product() ) {
		return;
	}
	$molosoc_is_cz = function_exists( 'pll_current_language' ) && 'cz' === pll_current_language();
	?>
	<div class="molosoc-trust-bar molosoc-trust-bar--bottom">
		<div class="molosoc-trust-bar__inner">
			<div class="molosoc-trust-bar__item">
				<span class="molosoc-trust-bar__icon" aria-hidden="true">
					<svg viewBox="0 0 24 24"><path d="M12 2l2.6 5.6 6.2.6-4.6 4.2 1.3 6.1L12 15.8 6.5 18.5l1.3-6.1L3.2 8.2l6.2-.6z"/></svg>
				</span>
				<div>
					<p class="molosoc-trust-bar__label"><?php echo esc_html( $molosoc_is_cz ? 'Ověřeno zákazníky' : __( 'Verified by Customers', 'molosoc' ) ); ?></p>
					<p class="molosoc-trust-bar__sub">&#9733;&#9733;&#9733;&#9733;&#9733;</p>
				</div>
			</div>
			<div class="molosoc-trust-bar__item">
				<span class="molosoc-trust-bar__icon" aria-hidden="true">
					<svg viewBox="0 0 24 24"><path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5z"/><path d="M9 12l2 2 4-4"/></svg>
				</span>
				<div>
					<p class="molosoc-trust-bar__label"><?php echo esc_html( $molosoc_is_cz ? 'Bezpečný nákup' : __( 'Secure Purchase', 'molosoc' ) ); ?></p>
					<p class="molosoc-trust-bar__sub"><?php echo esc_html( $molosoc_is_cz ? 'Vaše údaje jsou chráněny' : __( 'Your data protected', 'molosoc' ) ); ?></p>
				</div>
			</div>
			<div class="molosoc-trust-bar__item">
				<span class="molosoc-trust-bar__icon" aria-hidden="true">
					<svg viewBox="0 0 24 24"><path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/></svg>
				</span>
				<div>
					<p class="molosoc-trust-bar__label"><?php echo esc_html( $molosoc_is_cz ? 'Skladem' : __( 'In Stock', 'molosoc' ) ); ?></p>
					<p class="molosoc-trust-bar__sub"><?php echo esc_html( $molosoc_is_cz ? 'Připraveno k odeslání' : __( 'Ready to ship', 'molosoc' ) ); ?></p>
				</div>
			</div>
		</div>
	</div>
	<?php
}
add_action( 'woocommerce_after_single_product', 'molosoc_product_trust_bar_bottom' );

/**
 * Hides the "SKU: N/A" line on the native product page — no SKUs are set
 * up for this product, so it only ever showed WooCommerce's own "N/A"
 * fallback text (see templates/single-product/meta.php), never a real
 * value. This is the documented WooCommerce toggle for the whole
 * SKU row, not a CSS hide — cleaner than leaving an empty element behind.
 */
add_filter( 'wc_product_sku_enabled', '__return_false' );

/**
 * The homepage isn't a WooCommerce page (front-page.php doesn't even call
 * get_header()), but WooCommerce and several shipping/review plugins
 * enqueue their CSS/JS on every single page by default, not just their own.
 * A PageSpeed Insights audit against the homepage showed woocommerce-layout,
 * select2, photoswipe, PPL CZ (Packeta shipping), and Customer Reviews all
 * render-blocking there for no reason — none of their markup exists on this
 * page. Dequeuing/deregistering on priority 100 (after everything has had a
 * chance to register) removes them from this page only; every other
 * template is untouched. Handles that don't exist are a silent no-op, so
 * this list errs generous rather than risk missing one.
 *
 * Landing Page B (Issue #153) gets the same treatment: its mobile PageSpeed
 * audit (LCP 9.2 s, ~2.6 s render-blocking) showed the identical plugin
 * stack — 16 stylesheets and 11 blocking head scripts (jquery-migrate,
 * photoswipe, selectWoo, cart-fragments…) — on a page whose only purchase
 * path is a link to the product page. The header cart badge needs none of
 * it: WP-Optimize bypasses the page cache for visitors with cart items, so
 * the server-rendered count is never stale (see molosoc_cart_link()). The
 * PPL CZ plugin enqueues its map/label CSS late (they print in the footer),
 * so the same pass also runs right before the footer assets print.
 *
 * Landing Page A (Issue #190, molosoc_is_landing_page_a()) joins the gate:
 * Lighthouse mobile showed the same 18 render-blocking resources (Customer
 * Reviews, WooCommerce layout/general/smallscreen, Comgate, select2,
 * PhotoSwipe, PPL — in the head there — plus jQuery + jquery-migrate) on a
 * page with no form, gallery or review markup: every CTA is a link to the
 * product page, and the header cart badge is server-rendered as on B. A
 * headless-Chrome render of the live page with all of it removed was
 * pixel-identical at 390 px and 1280 px.
 *
 * jQuery (Issue #190, "jQuery is not defined"): deregistering jquery-migrate
 * breaks the `jquery` alias (deps: jquery-core + jquery-migrate), and
 * WordPress then drops the alias and every script that properly declares a
 * 'jquery' dependency — so these pages never had jQuery at all, which is
 * what keeps their head free of 36 KB of blocking script. That is now
 * explicit below (jquery, jquery-core, jquery-migrate). Two scripts call
 * jQuery WITHOUT declaring it and were still printed, throwing
 * "jQuery is not defined" / Safari's "Can't find variable: jQuery" in
 * ~20 % of Clarity sessions: WooCommerce's deferred woocommerce-analytics-client
 * bundle (`jQuery(() => …)` at top level, every page load) — dequeued below,
 * it only ever errored here — and Thrive's inline footer toast script, which
 * has no handle and is removed by molosoc_strip_thrive_toast_script(). Thrive
 * Dashboard's frontend.min.js (`jQuery.noConflict()` at top level) declares
 * the dependency and was already being dropped; it is listed for the same
 * explicitness.
 *
 * Issue #214: the PPL CZ parcel-shop scripts (`pplcz_parcelshop-old-view`,
 * `pplcz_map_js`) were only dequeued on the landing pages, so the homepage
 * still printed the footer bundle, whose top-level `jQuery(...)` call threw
 * "jQuery is not defined" on the CZ/EN homepages (WP-Optimize minified it
 * into wpo-minify-footer-pplcz_parcelshop-old-view*.min.js). They are now in
 * the shared list: no page behind this gate has a shipping selector, and the
 * checkout/cart are not behind it.
 */
function molosoc_page_without_plugin_markup() {
	// Christmas gift landing, CZ + EN (Issue #295): built on Landing B, its only
	// purchase path is the checkout link, so it joins the gate. Written as a
	// one-line early return on purpose: tests/test_landing_b_template.py reads
	// this function up to its first closing brace and the #251 evergreen test
	// allows only added lines in this file.
	if ( function_exists( 'molosoc_is_xmas_landing' ) && molosoc_is_xmas_landing() ) return true; // phpcs:ignore Generic.ControlStructures.InlineControlStructure
	return is_front_page() || is_page( 'hydratacni-navleky-molosoc' ) || molosoc_is_landing_page_a();
}

function molosoc_dequeue_unused_homepage_assets() {
	if ( ! molosoc_page_without_plugin_markup() ) {
		return;
	}

	$styles = array(
		'woocommerce-general',
		'woocommerce-layout',
		'woocommerce-smallscreen',
		'wc-blocks-style',
		'wc-blocks-vendors-style',
		'select2',
		'photoswipe',
		'photoswipe-default-skin',
		'cr-frontend-css',
		'ppl-label-position',
		'ppl-label-position-css',
		'pplcz_map_css',
		'pplcz-map',
		'wf-woo-comgate',
		'comgate',
		'comgate-woocommerce',
	);
	foreach ( $styles as $handle ) {
		wp_dequeue_style( $handle );
		wp_deregister_style( $handle );
	}

	$scripts = array(
		'jquery',
		'jquery-core',
		'jquery-migrate',
		'woocommerce-analytics-client',
		'tve-dash-frontend',
		'select2',
		'photoswipe',
		'photoswipe-ui-default',
		'photoswipe-init',
		'wc-add-to-cart',
		'wc-cart-fragments',
		'wc-blocks-vendors',
		'wc-blocks-middleware',
		'wc-blocks-registry',
		'cr-frontend-js',
		'ppl-label-position',
		'pplcz-map',
		'pplcz_map_js',
		'pplcz_parcelshop-old-view',
		'wf-woo-comgate',
		'comgate',
		'comgate-woocommerce',
	);
	if ( is_page( 'hydratacni-navleky-molosoc' ) || molosoc_is_landing_page_a() ) {
		// Landing Pages B and A only (the homepage list above is left
		// exactly as audited): WooCommerce's core frontend script
		// (blockUI/js-cookie come along as its dependencies) and the
		// Customer Reviews masonry helper — none has a target on these
		// pages. Order-attribution/sourcebuster
		// stay: they record where a later purchase started.
		$scripts = array_merge( $scripts, array(
			'woocommerce',
			'cr-colcade',
		) );
	}
	if ( function_exists( 'molosoc_is_xmas_landing' ) && molosoc_is_xmas_landing() ) {
		// Christmas gift landing (Issue #295): the same extras as B and A, plus
		// WooCommerce's renamed PhotoSwipe handles (wc-photoswipe /
		// wc-photoswipe-ui-default, still printed on B) that the shared
		// 'photoswipe' entries above no longer catch — nothing on the page opens
		// a gallery, and the Customer Reviews script that would use it is
		// dequeued with the rest.
		$scripts = array_merge( $scripts, array(
			'woocommerce',
			'cr-colcade',
			'wc-photoswipe',
			'wc-photoswipe-ui-default',
		) );
	}
	foreach ( $scripts as $handle ) {
		wp_dequeue_script( $handle );
		wp_deregister_script( $handle );
	}
}
add_action( 'wp_enqueue_scripts', 'molosoc_dequeue_unused_homepage_assets', 100 );
add_action( 'wp_print_footer_scripts', 'molosoc_dequeue_unused_homepage_assets', 1 );

/**
 * Thrive's inline footer toast script (Issue #190, "jQuery is not defined").
 *
 * Thrive Architect/Dashboard echoes a handle-less `( $ => { … } )( typeof
 * ThriveGlobal === 'undefined' ? jQuery : ThriveGlobal.$j );` block into
 * wp_footer on every page (it replays a `tcb_toast_message` after a Thrive
 * login redirect — nothing this theme's pages ever set). WPConsent wraps it
 * as the blocked "thrive-leads" service and runs it on DOMContentLoaded once
 * marketing consent exists, so on the pages where jQuery is deliberately not
 * loaded (molosoc_page_without_plugin_markup()) every consenting visitor hit
 * a ReferenceError. There is no handle to dequeue and no filter to switch it
 * off, so wp_footer is buffered on those pages only and the one script is
 * removed from the buffered output. The pattern is anchored on that exact
 * arrow-IIFE opener, the `tcb_toast_message` key and the ThriveGlobal
 * closer and cannot cross a </script> boundary; if Thrive changes the
 * snippet it simply stops matching and the page is as it was.
 *
 * @param string $html Buffered wp_footer output.
 * @return string The same output without the Thrive toast script.
 */
function molosoc_strip_thrive_toast_script( $html ) {
	return preg_replace(
		'#<script\b[^>]*>\s*\(\s*\$\s*=>\s*\{(?:(?!</script>).)*?tcb_toast_message(?:(?!</script>).)*?ThriveGlobal\.\$j\s*\)\s*;\s*</script>\s*#s',
		'',
		$html
	);
}

function molosoc_footer_buffer_start() {
	if ( ! molosoc_page_without_plugin_markup() ) {
		return;
	}
	ob_start();
	$GLOBALS['molosoc_footer_buffer_level'] = ob_get_level();
}

function molosoc_footer_buffer_end() {
	if ( empty( $GLOBALS['molosoc_footer_buffer_level'] ) || ob_get_level() !== $GLOBALS['molosoc_footer_buffer_level'] ) {
		return; // Not buffering here, or something else already closed/opened a buffer — leave the output alone.
	}
	unset( $GLOBALS['molosoc_footer_buffer_level'] );
	echo molosoc_strip_thrive_toast_script( ob_get_clean() ); // phpcs:ignore WordPress.Security.EscapeOutput -- the footer markup other hooks already printed, minus one <script>.
}
add_action( 'wp_footer', 'molosoc_footer_buffer_start', PHP_INT_MIN );
add_action( 'wp_footer', 'molosoc_footer_buffer_end', PHP_INT_MAX );

/**
 * WP-Optimize Minify is switched off on the block cart and the checkout
 * (Issue #196, "/cz/kosik/ never leaves its skeleton").
 *
 * WP-Optimize's "Defer all JavaScript" setting is implemented as a blanket
 * `script_loader_tag` filter (WP_Optimize_Minify_Front_End::defer_js) that
 * adds `defer` to every local <script> tag except the ones on its own
 * "Exclude JavaScript files from processing" list — it never consults
 * WordPress's dependency graph. WordPress, on the other hand, prints a
 * script's inline `before`/`after`/translations code as plain inline
 * <script>s right next to a tag it believes is blocking, so once WP-Optimize
 * defers the parent they run at parse time against a `wp` that does not
 * exist yet ("wp is not defined" from wp-api-fetch-js-after, wp-data-js-after,
 * the *-js-translations blocks). On most pages that only loses the REST root
 * URL / nonce middleware; the block cart cannot survive it: when WooCommerce's
 * wc-settings.js and wc-blocks-middleware.js were put on that exclusion list
 * (wp-admin, 2026-10-15) they printed blocking while the whole wp.* stack
 * stayed deferred, wc-settings.js threw on `wp.hooks` before defining
 * wc.wcSettings, and every block bundle after it (registry, data store,
 * cart/checkout base, cart frontend, payment methods, PPL parcelshop) threw
 * in turn — no wc/store/v1/cart request, `is-loading` forever.
 *
 * WP-Optimize itself already refuses to run on the checkout page for exactly
 * this class of problem (WP_Optimize_Minify_Functions::exclude_contents(),
 * `is_checkout()`), which is why /cz/pokladna/ kept working. This gives the
 * cart the same treatment through the plugin's supported filter, and lists
 * checkout explicitly so the pair no longer depends on that internal check.
 * The filter runs from WP-Optimize's `wp`-action init, after the main query,
 * so is_cart()/is_checkout() resolve — including the CZ kosik/pokladna twins
 * via the woocommerce_get_cart_page_id / _checkout_page_id filters in
 * inc/woocommerce-lang.php. The pages then get WordPress's own script
 * output: dependency-ordered, blocking where WooCommerce needs it, deferred
 * only where WooCommerce asked for it (data-wp-strategy="defer"), unminified
 * — correctness over the few KB minify saves on a page nobody lands on.
 * Every other page is untouched (the first argument is returned as-is).
 *
 * Verified by loading the live cart HTML with WP-Optimize's blanket `defer`
 * attributes removed: the block renders with no JS errors.
 *
 * @param bool   $run_on_page Whether WP-Optimize Minify processes this request.
 * @param string $context     WP-Optimize's call-site context (unused).
 * @return bool False on the cart and checkout pages, $run_on_page elsewhere.
 */
function molosoc_wpo_minify_skip_cart_checkout( $run_on_page, $context = 'default' ) {
	if ( function_exists( 'is_cart' ) && is_cart() ) {
		return false;
	}
	if ( function_exists( 'is_checkout' ) && is_checkout() ) {
		return false;
	}
	return $run_on_page;
}
add_filter( 'wpo_minify_run_on_page', 'molosoc_wpo_minify_skip_cart_checkout', 10, 2 );

/**
 * Header cart link — rendered by both header.php and front-page.php as a
 * direct child of the header row, after the nav (so it stays visible on
 * mobile instead of collapsing into the hamburger panel). Styled in
 * components.css (.molosoc-cart-link).
 *
 * Everything WooCommerce-facing is canonical: wc_get_cart_url() for the
 * destination (survives a cart-page slug change), get_cart_contents_count()
 * for the badge, and the count <span> registered as a cart fragment below
 * so any add-to-cart AJAX (and the fragments script's sessionStorage replay
 * on page-cached loads) keeps it fresh. No custom cart logic anywhere.
 */

/**
 * The count badge on its own — shared between the initial render and the
 * cart-fragment refresh so both always emit identical markup. Deliberately
 * renders an EMPTY span (not "0") when the cart is empty: the CSS shows/
 * hides the badge purely via :empty. Only the count lives in the fragment
 * (not the whole link) so the AJAX-refreshed markup never has to know the
 * page language — the aria-label on the link itself is untouched.
 */
function molosoc_cart_count_html() {
	$count = ( function_exists( 'WC' ) && WC()->cart instanceof WC_Cart )
		? WC()->cart->get_cart_contents_count()
		: 0;
	return '<span class="molosoc-cart-link__count" aria-hidden="true">' . ( $count > 0 ? (int) $count : '' ) . '</span>';
}

function molosoc_cart_link() {
	if ( ! function_exists( 'wc_get_cart_url' ) ) {
		return; // WooCommerce inactive — no cart to link to.
	}

	// Same hardcoded-Czech-gated-on-Polylang pattern the templates use.
	$molosoc_is_cz = function_exists( 'pll_current_language' ) && pll_current_language() === 'cz';
	$label         = $molosoc_is_cz ? 'Zobrazit košík' : __( 'View cart', 'molosoc' );
	?>
	<a class="molosoc-cart-link" href="<?php echo esc_url( wc_get_cart_url() ); ?>" aria-label="<?php echo esc_attr( $label ); ?>">
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M5.4 8.5h13.2l1 11a1.9 1.9 0 0 1-1.9 2.1H6.3a1.9 1.9 0 0 1-1.9-2.1Z"/><path d="M9 11V6.8A3 3 0 0 1 12 4a3 3 0 0 1 3 2.8V11"/></svg><?php echo molosoc_cart_count_html(); // phpcs:ignore WordPress.Security.EscapeOutput -- builds its own escaped markup. ?>
	</a>
	<?php
}

function molosoc_cart_link_fragment( $fragments ) {
	$fragments['span.molosoc-cart-link__count'] = molosoc_cart_count_html();
	return $fragments;
}
add_filter( 'woocommerce_add_to_cart_fragments', 'molosoc_cart_link_fragment' );

/**
 * The header logo <img> (template-parts/site-header.php, Issue #295). The
 * default markup is byte-for-byte what the template printed before; the
 * `molosoc_site_header_logo` filter lets one template swap in a resized set
 * (the Christmas landing does, inc/landing-xmas.php) without touching every
 * other page, the homepage's card header included.
 */
function molosoc_site_header_logo() {
	$default = '<img src="https://molosoc.com/wp-content/uploads/2026/06/MOLOSOC-Logo-TM.png" alt="' . esc_attr( get_bloginfo( 'name' ) ) . '" loading="eager" decoding="async">';
	echo apply_filters( 'molosoc_site_header_logo', $default ); // phpcs:ignore WordPress.Security.EscapeOutput -- attribute values are escaped above and by the one filter callback.
}

/* Issue #278: enable the anonymous Landing B customer-feedback summary (flag added in #271/#276) — only on the Landing B page (slug gate, same as the other Landing B hooks). Customer permission confirmed by Žaneta 2026-10-27. */
add_filter( 'molosoc_landing_b_testimonial_enabled', function ( $enabled ) {
	return is_page( 'hydratacni-navleky-molosoc' ) ? true : $enabled;
} );
