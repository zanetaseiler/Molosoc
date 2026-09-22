/**
 * Keeps WooCommerce Store API requests (wc/store/* — the block cart/
 * checkout's own data layer) in the current page's language.
 *
 * Why this exists: Polylang derives the language purely from the URL path
 * (/cz/... vs unprefixed), but a Store API request goes out from the
 * browser as its own fetch to /wp-json/wc/store/v1/..., which carries no
 * /cz/ prefix of its own — so without a `lang` query param, Polylang
 * resolves it as English regardless of which page issued it (see the
 * issue's own audit: "REST requests need a `lang` request param or
 * pll_current_language() is `false` in REST"). Cart/checkout also send
 * no-cache, so this can't be solved by keying off the pll_language cookie
 * either — the URL (and, for this one JS-driven exception, this explicit
 * query param) has to carry it.
 *
 * window.molosocLang ('cz'|'en') is set by functions.php via
 * wp_add_inline_script() right before this file, from the same
 * pll_current_language() value PHP already resolved for the page itself —
 * see molosoc_enqueue_assets() for where/why.
 *
 * House JS style (see cart-badge-sync.js): plain IIFE, defensive existence
 * checks, no build step, no jQuery.
 */
( function () {
	function currentLang() {
		return ( window.molosocLang === 'cz' ) ? 'cz' : 'en';
	}

	function appendLang( value ) {
		if ( typeof value !== 'string' || value.indexOf( '/wc/store' ) === -1 ) {
			return value;
		}
		if ( value.indexOf( 'lang=' ) !== -1 ) {
			return value; // Already carries a lang param — don't double it up.
		}
		var separator = value.indexOf( '?' ) === -1 ? '?' : '&';
		return value + separator + 'lang=' + currentLang();
	}

	function init() {
		if ( ! window.wp || ! wp.apiFetch || typeof wp.apiFetch.use !== 'function' ) {
			return;
		}
		wp.apiFetch.use( function ( options, next ) {
			// Store API requests come through apiFetch as either a relative
			// REST `path` (the common case for wc/store/* calls) or, less
			// often, a fully-qualified `url` — cover both defensively.
			if ( options && options.path ) {
				options.path = appendLang( options.path );
			}
			if ( options && options.url ) {
				options.url = appendLang( options.url );
			}
			return next( options );
		} );
	}

	// wp.apiFetch is registered by WooCommerce's own footer block scripts;
	// window load runs after all of them, so no polling needed (same
	// convention as cart-badge-sync.js).
	if ( document.readyState === 'complete' ) {
		init();
	} else {
		window.addEventListener( 'load', init );
	}
} )();
