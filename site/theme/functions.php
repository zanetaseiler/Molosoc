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

		// GSAP + ScrollTrigger (merge transition, topics portal, proof-scale)
		// are TEMPORARILY DISABLED. front-page.php was just re-ported to full
		// markup parity with homepage-preview.html after an earlier port of
		// this same animation stack caused a regression that forced a revert
		// back to a plain static page (see git history: "Revert homepage to
		// last confirmed-stable static state (pre-animation-port)"). Per the
		// current plan, the static markup/images/styling are being confirmed
		// pixel-accurate first; every effect below already has a fully-settled
		// default CSS state with no JS running (--proof-scale defaults to 1,
		// merge tiles sit flush by default, --portal-hole defaults fully
		// open, feature cards default to opacity:1/transform:none — see the
		// comments in homepage.css for each), so leaving these disabled does
		// not change how the page looks at rest. Re-enable one at a time,
		// testing after each, once the static match is confirmed:
		//
		// wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
		// wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
		// wp_enqueue_script( 'molosoc-merge-transition', $theme_uri . '/assets/js/merge-transition.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		// wp_enqueue_script( 'molosoc-proof-scale', $theme_uri . '/assets/js/proof-scale.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		// wp_enqueue_script( 'molosoc-topics-portal', $theme_uri . '/assets/js/topics-portal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
	}
}
add_action( 'wp_enqueue_scripts', 'molosoc_enqueue_assets' );
