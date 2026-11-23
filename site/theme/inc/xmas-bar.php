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
 * a "x" button stores one flag in sessionStorage (try/catch, works without it)
 * and the bar stays hidden for the current browsing session only (Issue #324). No JS = the bar simply shows.
 * No plugin, no fixed positioning: the sticky Buy-now pill, the hamburger
 * and the menu are not touched.
 *
 * Filters: `molosoc_xmas_bar_enabled` (bool, default true) switches it off in
 * one line after the season.
 *
 * Black Friday (Issue #382): until Mon 30 Nov 2026 23:59 Europe/Prague
 * (molosoc_bf_active(), inc/landing-bf.php) the same bar — same look, close
 * button and mobile behaviour, no 🎄 — announces the Black Friday price list
 * and links to the Black Friday page of the visitor's language, with its own
 * dismiss key (MOLOSOC_BF_BAR_KEY) so people who closed the Christmas bar see
 * it once. It falls back to the Christmas bar when that Black Friday page is
 * not published (never a link that would bounce). From 1 Dec 00:00 Prague
 * the server renders the Christmas bar again; a page WP-Optimize cached
 * before the switch carries the Christmas text/link too, and the inline
 * script swaps to it by the visitor's clock, so no purge is needed at the
 * switch time. Hidden on the Black Friday pages themselves (they belong to
 * the molosoc_is_xmas_landing() family).
 */

defined( 'ABSPATH' ) || exit;

/** sessionStorage key (versioned so a future campaign can re-show the bar). */
const MOLOSOC_XMAS_BAR_KEY = 'molosocXmasBar317';

/** sessionStorage key of the Black Friday bar (Issue #382): fresh, so a closed Christmas bar does not hide it. */
const MOLOSOC_BF_BAR_KEY = 'molosocBfBar382';

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
	$xmas = array();
	if ( $page && 'publish' === get_post_status( $page ) ) {
		$xmas = 'cz' === $lang
			? array(
				'lang'  => 'cz',
				'url'   => get_permalink( $page ),
				'text'  => '🎄 Tip na vánoční dárek — Objevte vánoční nabídku MOLOSOC',
				'close' => 'Zavřít oznámení',
				'label' => 'Vánoční nabídka',
				'key'   => MOLOSOC_XMAS_BAR_KEY,
			)
			: array(
				'lang'  => 'en',
				'url'   => get_permalink( $page ),
				'text'  => '🎄 Christmas Gift Idea — Discover the MOLOSOC Holiday Offer',
				'close' => 'Close announcement',
				'label' => 'Christmas offer',
				'key'   => MOLOSOC_XMAS_BAR_KEY,
			);
	}

	$bf = molosoc_bf_bar_data( $lang );
	if ( $bf ) {
		$bf['after'] = $xmas; // What the bar becomes at the end time on a cached copy (array() = hide).
		return $bf;
	}
	return $xmas;
}

/**
 * The Black Friday variant for $lang, or array() when it must not show (after
 * the end, Black Friday code not loaded, or that language's page not published).
 */
function molosoc_bf_bar_data( $lang ) {
	if ( ! function_exists( 'molosoc_bf_active' ) || ! molosoc_bf_active() ) {
		return array();
	}
	$page = get_page_by_path( molosoc_bf_slugs()[ $lang ] );
	if ( ! $page || 'publish' !== get_post_status( $page ) ) {
		return array();
	}
	$p = molosoc_xmas_unit_prices();
	if ( 'cz' === $lang ) {
		$text = sprintf( 'Black Friday — první pár %1$s, každý další %2$s. %3$s', molosoc_bf_money( $p[1], 'cz' ), molosoc_bf_money( $p[2], 'cz' ), molosoc_bf_until_text( 'cz', 'bar' ) );
	} else {
		$text = sprintf( 'Black Friday — first pair %1$s, each extra pair %2$s. %3$s', molosoc_bf_money( $p[1], 'en' ), molosoc_bf_money( $p[2], 'en' ), molosoc_bf_until_text( 'en', 'bar' ) );
	}
	return array(
		'lang'  => $lang,
		'url'   => get_permalink( $page ),
		'text'  => $text,
		'close' => 'cz' === $lang ? 'Zavřít oznámení' : 'Close announcement',
		'label' => 'cz' === $lang ? 'Black Friday nabídka' : 'Black Friday offer',
		'key'   => MOLOSOC_BF_BAR_KEY,
		'end'   => (int) molosoc_bf_end_ts() * 1000,
	);
}

/** Prints the bar (called from template-parts/site-header.php). */
function molosoc_xmas_bar() {
	$d = molosoc_xmas_bar_data();
	if ( ! $d ) {
		return;
	}
	$swap = null;
	if ( isset( $d['end'] ) ) {
		$a    = isset( $d['after'] ) ? $d['after'] : array();
		$swap = array(
			'end'   => $d['end'],
			'url'   => $a ? $a['url'] : '',
			'text'  => $a ? $a['text'] : '',
			'label' => $a ? $a['label'] : '',
			'key'   => $a ? $a['key'] : '',
		);
	}
	?>
<div class="molosoc-xmas-bar" id="molosoc-xmas-bar" role="region" aria-label="<?php echo esc_attr( $d['label'] ); ?>" lang="<?php echo esc_attr( 'cz' === $d['lang'] ? 'cs' : 'en' ); ?>">
	<a class="molosoc-xmas-bar__link" href="<?php echo esc_url( $d['url'] ); ?>"><span class="molosoc-xmas-bar__spark" aria-hidden="true">&#10022;</span><span class="molosoc-xmas-bar__text"><?php echo esc_html( $d['text'] ); ?></span><span class="molosoc-xmas-bar__arrow" aria-hidden="true">&rarr;</span></a>
	<button type="button" class="molosoc-xmas-bar__close" aria-label="<?php echo esc_attr( $d['close'] ); ?>"><span aria-hidden="true">&times;</span></button>
</div>
<script>
(function(){var b=document.getElementById("molosoc-xmas-bar");if(!b)return;var k=<?php echo wp_json_encode( $d['key'] ); ?>,s=<?php echo wp_json_encode( $swap ); ?>;
if(s&&Date.now()>=s.end){if(!s.url){b.hidden=true;return;}var a=b.querySelector(".molosoc-xmas-bar__link"),t=b.querySelector(".molosoc-xmas-bar__text");if(a)a.href=s.url;if(t)t.textContent=s.text;b.setAttribute("aria-label",s.label);k=s.key;}
try{if(window.sessionStorage.getItem(k)==="1"){b.hidden=true;return;}}catch(e){}
var c=b.querySelector(".molosoc-xmas-bar__close");if(!c)return;
c.addEventListener("click",function(){b.hidden=true;try{window.sessionStorage.setItem(k,"1");}catch(e){}});})();
</script>
	<?php
}
