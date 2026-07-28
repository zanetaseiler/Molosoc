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

function molosoc_enqueue_assets() {
	$theme_uri     = get_stylesheet_directory_uri();
	$theme_version = wp_get_theme()->get( 'Version' );

	wp_enqueue_style( 'molosoc-style', get_stylesheet_uri(), array(), $theme_version );

	wp_enqueue_style(
		'molosoc-fonts',
		'https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Mulish:wght@400;600;700&family=Nunito:wght@400;600;700&display=swap',
		array(),
		null
	);

	wp_enqueue_style( 'molosoc-tokens', $theme_uri . '/assets/css/tokens.css', array(), $theme_version );
	wp_enqueue_style( 'molosoc-base', $theme_uri . '/assets/css/base.css', array( 'molosoc-tokens' ), $theme_version );
	wp_enqueue_style( 'molosoc-components', $theme_uri . '/assets/css/components.css', array( 'molosoc-base' ), $theme_version );

	if ( is_front_page() ) {
		wp_enqueue_style( 'molosoc-homepage', $theme_uri . '/assets/css/homepage.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_script( 'molosoc-motion', $theme_uri . '/assets/js/motion.js', array(), $theme_version, true );

		// GSAP + ScrollTrigger, scoped to the front page — see front-page.php
		// for the sections that use these (merge transition, topics portal,
		// proof-scale). CDN-hosted; each dependent script no-ops gracefully
		// if this fails to load (see docs/molosoc-animation-specification.md).
		wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
		wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
		wp_enqueue_script( 'molosoc-merge-transition', $theme_uri . '/assets/js/merge-transition.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-proof-scale', $theme_uri . '/assets/js/proof-scale.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-topics-portal', $theme_uri . '/assets/js/topics-portal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );

		// window.load alone isn't enough: it only waits for eagerly-loading
		// resources. Most images on this page use loading="lazy" (deliberate,
		// for performance) — a lazy image that hasn't scrolled near the
		// viewport yet is never part of window.load's pending set, so it
		// finishes loading LATER, growing page height and leaving every
		// ScrollTrigger pin's cached start/end stale relative to the real,
		// final layout. That's what produced the "plays once correctly, then
		// the same section appears to repeat/jump further down, flickers on
		// scroll-up" symptom: the pin was engaging against pre-lazy-load
		// geometry.
		//
		// Fix: refresh on window.load (covers fonts + eager images), refresh
		// again once every image still incomplete at that point has actually
		// finished (covers lazy images triggered after load), AND refresh on
		// every individual image's own load event as a standing safety net
		// (covers anything loading later still — slow network, a font swap
		// nudging layout, etc.).
		wp_add_inline_script(
			'molosoc-topics-portal',
			'function molosocRefreshScrollTrigger() { if (window.ScrollTrigger) ScrollTrigger.refresh(); }
			window.addEventListener("load", function () {
				molosocRefreshScrollTrigger();

				var pending = [];
				document.querySelectorAll("img").forEach(function (img) {
					if (!img.complete) {
						pending.push(new Promise(function (resolve) {
							img.addEventListener("load", resolve, { once: true });
							img.addEventListener("error", resolve, { once: true });
						}));
					}
					// Safety net — fires on every future image load, including
					// ones not yet in the DOM/pending set at window.load time.
					img.addEventListener("load", molosocRefreshScrollTrigger);
				});

				if (pending.length) {
					Promise.all(pending).then(molosocRefreshScrollTrigger);
				}
			});'
		);
	}
}
add_action( 'wp_enqueue_scripts', 'molosoc_enqueue_assets' );
