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
		<?php bloginfo( 'name' ); ?>
	</a>
	<?php
	wp_nav_menu( array(
		'theme_location' => 'primary',
		'container'      => 'nav',
		'container_class' => 'molosoc-site-header__nav',
		'fallback_cb'    => false,
	) );
	?>
</header>
