<?php
/**
 * Header used by every template except front-page.php (which is
 * intentionally self-contained — see the note at the top of that file).
 */

defined( 'ABSPATH' ) || exit;
?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<a class="molosoc-skip-link" href="#main"><?php esc_html_e( 'Skip to content', 'molosoc' ); ?></a>

<header class="molosoc-site-header">
	<a class="molosoc-site-header__logo" href="<?php echo esc_url( home_url( '/' ) ); ?>">
		<img src="https://staging.molosoc.com/wp-content/uploads/2026/06/MOLOSOC-Logo-TM.png" alt="<?php echo esc_attr( get_bloginfo( 'name' ) ); ?>" loading="eager" decoding="async">
	</a>
	<?php
	// Turned off for now (2026-07-29) — most of the pillar/spoke/product
	// pages a real nav would link to aren't built yet, so this waits until
	// there's an actual decision on what should be in it. Re-enable by
	// uncommenting; the 'primary' menu location and its registration in
	// functions.php are untouched.
	/*
	wp_nav_menu( array(
		'theme_location' => 'primary',
		'container'      => 'nav',
		'container_class' => 'molosoc-site-header__nav',
		'fallback_cb'    => false,
	) );
	*/
	?>
</header>
