<?php
/**
 * Molosoc child theme — asset enqueue only.
 *
 * Deliberately minimal: no WooCommerce hooks, no template overrides beyond
 * front-page.php yet. Per project constraints this pass covers the homepage
 * only — category/product/pillar/spoke templates are a later, separate step.
 */

defined( 'ABSPATH' ) || exit;

function molosoc_enqueue_assets() {
	$theme_uri     = get_stylesheet_directory_uri();
	$theme_version = wp_get_theme()->get( 'Version' );

	// Parent (Thrive) stylesheet stays loaded so anything not yet rebuilt
	// (cart/checkout/account, still on the parent theme) keeps working.
	wp_enqueue_style(
		'molosoc-parent-style',
		get_template_directory_uri() . '/style.css',
		array(),
		$theme_version
	);

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
	}
}
add_action( 'wp_enqueue_scripts', 'molosoc_enqueue_assets' );
