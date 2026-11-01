<?php
/**
 * Christmas announcement bar above the global navigation (Issue #317).
 *
 * A slim, non-sticky, in-flow strip rendered by template-parts/site-header.php
 * right before <header class="molosoc-site-header">, so it sits above the logo +
 * menu on every normal template and on the homepage (which also uses that part).
 * It links to the existing Christmas landing pages whose slugs live in
 * molosoc_xmas_slugs() (inc/landing-xmas.php); nothing is invented:
 *   CZ  /cz/vanocni-darek-molosoc/   EN  /christmas-gift-molosoc/
 *
 * Hidden on: the two Christmas pages themselves (already there), cart,
 * checkout and the order-received page (the on-page purchase flow stays
 * undisturbed), and while a Christmas page is not published. Dismissible:
 * a "x" button stores one flag in localStorage (try/catch, works without it)
 * and the bar stays hidden for that visitor. No JS = the bar simply shows.
 * No plugin, no fixed positioning: the sticky Buy-now pill, the hamburger
 * and the menu are not touched.
 *
 * Filters: `molosoc_xmas_bar_enabled` (bool, default true) switches it off in
 * one line after the season.
 */

defined( 'ABSPATH' ) || exit;

/** localStorage key (versioned so a future campaign can re-show the bar). */
const MOLOSOC_XMAS_BAR_KEY = 'molosocXmasBar317';

/** Stylesheet: its own small file, loaded wherever the bar can show (same gate as the markup). */
add_action( 'wp_enqueue_scripts', 'molosoc_xmas_bar_enqueue', 20 );
function molosoc_xmas_bar_enqueue() {
	if ( ! molosoc_xmas_bar_data() ) {
		return;
	}
	wp_enqueue_style( 'molosoc-xmas-bar', get_stylesheet_directory_uri() . '/assets/css/xmas-bar.css', array( 'molosoc-components' ), wp_get_theme()->get( 'Version' ) );
}

/**
 * Localised bar data for the current request, or array() when the bar must not show.
 *
 * @return array{lang:string,url:string,text:string,close:string}|array
 */
function molosoc_xmas_bar_data() {
	if ( ! apply_filters( 'molosoc_xmas_bar_enabled', true ) || ! function_exists( 'molosoc_xmas_slugs' ) ) {
		return array();
	}
	if ( function_exists( 'molosoc_is_xmas_landing' ) && molosoc_is_xmas_landing() ) {
		return array();
	}
	if ( ( function_exists( 'is_cart' ) && is_cart() )
		|| ( function_exists( 'is_checkout' ) && is_checkout() ) // includes order-received
		|| ( function_exists( 'is_wc_endpoint_url' ) && is_wc_endpoint_url( 'order-received' ) ) ) {
		return array();
	}

	$lang = ( function_exists( 'pll_current_language' ) && 'cz' === pll_current_language() ) ? 'cz' : 'en';
	$slug = molosoc_xmas_slugs()[ $lang ];
	$page = get_page_by_path( $slug );
	if ( ! $page || 'publish' !== get_post_status( $page ) ) {
		return array();
	}

	if ( 'cz' === $lang ) {
		return array(
			'lang'  => 'cz',
			'url'   => get_permalink( $page ),
			'text'  => '🎄 Tip na vánoční dárek — Objevte vánoční nabídku MOLOSOC',
			'close' => 'Zavřít oznámení',
		);
	}
	return array(
		'lang'  => 'en',
		'url'   => get_permalink( $page ),
		'text'  => '🎄 Christmas Gift Idea — Discover the MOLOSOC Holiday Offer',
		'close' => 'Close announcement',
	);
}

/** Prints the bar (called from template-parts/site-header.php). */
function molosoc_xmas_bar() {
	$d = molosoc_xmas_bar_data();
	if ( ! $d ) {
		return;
	}
	$key = MOLOSOC_XMAS_BAR_KEY;
	?>
<div class="molosoc-xmas-bar" id="molosoc-xmas-bar" role="region" aria-label="<?php echo esc_attr( 'cz' === $d['lang'] ? 'Vánoční nabídka' : 'Christmas offer' ); ?>" lang="<?php echo esc_attr( 'cz' === $d['lang'] ? 'cs' : 'en' ); ?>">
	<a class="molosoc-xmas-bar__link" href="<?php echo esc_url( $d['url'] ); ?>"><?php echo esc_html( $d['text'] ); ?></a>
	<button type="button" class="molosoc-xmas-bar__close" aria-label="<?php echo esc_attr( $d['close'] ); ?>"><span aria-hidden="true">&times;</span></button>
</div>
<script>
(function(){var b=document.getElementById("molosoc-xmas-bar");if(!b)return;var k=<?php echo wp_json_encode( $key ); ?>;
try{if(window.localStorage.getItem(k)==="1"){b.hidden=true;return;}}catch(e){}
var c=b.querySelector(".molosoc-xmas-bar__close");if(!c)return;
c.addEventListener("click",function(){b.hidden=true;try{window.localStorage.setItem(k,"1");}catch(e){}});})();
</script>
	<?php
}
