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
	// Re-enabled (2026-07-30) — Home and Foot Covers are real pages now, so
	// there's something for a nav to link to. Assign the actual menu items
	// (Foot Covers, Product once it's ported, etc.) under Appearance > Menus
	// in wp-admin to the "Primary Menu" location; nothing renders here until
	// that menu exists (fallback_cb is intentionally false, not a hardcoded
	// link list).
	wp_nav_menu( array(
		'theme_location' => 'primary',
		'container'      => 'nav',
		'container_class' => 'molosoc-site-header__nav',
		'fallback_cb'    => false,
	) );
	?>
</header>
