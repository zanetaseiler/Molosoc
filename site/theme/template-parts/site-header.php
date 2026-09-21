<?php
/**
 * The site's standard boxed header: logo + hamburger + primary menu + cart.
 *
 * Rendered by header.php on every normal template, and ALSO by
 * front-page.php for its "card hero" homepage variant (see
 * molosoc_home_card_variant() in functions.php), which wants the exact
 * same logo/menu as e.g. /cz/navleky-na-nohy/ instead of the white
 * floating .molosoc-home-header. One copy, so the two never drift.
 */

defined( 'ABSPATH' ) || exit;
?>
<header class="molosoc-site-header">
	<a class="molosoc-site-header__logo" href="<?php echo esc_url( home_url( '/' ) ); ?>">
		<img src="https://molosoc.com/wp-content/uploads/2026/06/MOLOSOC-Logo-TM.png" alt="<?php echo esc_attr( get_bloginfo( 'name' ) ); ?>" loading="eager" decoding="async">
	</a>
	<button type="button" class="molosoc-nav-toggle" aria-expanded="false" aria-controls="molosoc-site-nav" aria-label="<?php esc_attr_e( 'Menu', 'molosoc' ); ?>">
		<span></span><span></span><span></span>
	</button>
	<?php
	// Re-enabled (2026-07-30) — Home and Foot Covers are real pages now, so
	// there's something for a nav to link to. Assign the actual menu items
	// (Foot Covers, Product once it's ported, etc.) under Appearance > Menus
	// in wp-admin to the "Primary Menu" location; nothing renders here until
	// that menu exists (fallback_cb is intentionally false, not a hardcoded
	// link list).
	wp_nav_menu( array(
		'theme_location'  => 'primary',
		'container'       => 'nav',
		'container_id'    => 'molosoc-site-nav',
		'container_class' => 'molosoc-site-header__nav',
		'fallback_cb'     => false,
	) );

	molosoc_cart_link();
	?>
</header>
