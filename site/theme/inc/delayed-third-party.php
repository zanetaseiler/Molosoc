<?php
/**
 * Delayed third-party scripts on the Christmas landing (Issue #301).
 *
 * PageSpeed Insights (mobile, slow 4G, 30 Oct 2026) on /cz/vanocni-darek-molosoc/:
 * LCP 3.5 s with the hero already responsive and preloaded (Issue #295); the
 * biggest remaining weight is gtag.js (~304 KB transfer, two ~150 KB files),
 * which competes with the hero for bandwidth on the first screen.
 *
 * The WooCommerce Google Analytics Integration plugin enqueues gtag.js under
 * the handle `google-tag-manager` (async strategy) and prints everything
 * else inline: the Consent Mode default, `gtag('js'|'config'|'set')` and the
 * `dataLayer` bootstrap, plus the events bundle (`window.ga4w`, deferred).
 * All of those only define `gtag()` and push into `dataLayer`, so they keep
 * running exactly as before; only the library download moves.
 *
 * On the two Christmas pages the `script_loader_tag` for that one handle is
 * rewritten to an inert placeholder (`type="text/plain"`, the URL in
 * `data-molosoc-delayed-src`) followed by a tiny inline loader that injects
 * the real `<script async src>` once, on the first of: scroll, touchstart,
 * pointerdown, keydown, mousemove — or `load` + idle (`requestIdleCallback`
 * with a 2.5 s timeout, `setTimeout` 2 s where rIC is missing). When gtag.js
 * arrives it replays the queued `dataLayer`, so page_view, consent state and
 * every ecommerce event are sent as before, just later. Cart, checkout and
 * order-received pages are never touched (explicit guard), so the purchase
 * event path is byte-identical to today.
 *
 * Brevo (`cdn.brevo.com/js/sdk-loader.js`) is printed raw in <head> by its
 * plugin with `async` and an inline `window.Brevo.push(["init", …])` — it
 * is already non-blocking and has no WordPress handle to filter, so it is
 * left alone (Issue #301 point 3). Meta pixel, WPConsent, Clarity: untouched.
 *
 * Landing B is NOT included (the gate below is one `is_page()` away, via the
 * `molosoc_delayed_third_party_enabled` filter, if wanted later).
 */

defined( 'ABSPATH' ) || exit;

/** Script handles whose download is delayed (the GA plugin's gtag.js). */
function molosoc_delayed_third_party_handles() {
	return (array) apply_filters( 'molosoc_delayed_third_party_handles', array( 'google-tag-manager' ) );
}

/**
 * Where the delay applies: the two Christmas pages only, and never on a
 * WooCommerce cart / checkout / order-received page (belt and braces — the
 * Christmas pages are none of those — so the purchase event can never be
 * delayed by a future change to the gate).
 */
function molosoc_delayed_third_party_enabled() {
	if ( is_admin() ) {
		return false;
	}
	if ( ( function_exists( 'is_cart' ) && is_cart() )
		|| ( function_exists( 'is_checkout' ) && is_checkout() )
		|| ( function_exists( 'is_wc_endpoint_url' ) && is_wc_endpoint_url( 'order-received' ) ) ) {
		return false;
	}
	$enabled = function_exists( 'molosoc_is_xmas_landing' ) && molosoc_is_xmas_landing();
	return (bool) apply_filters( 'molosoc_delayed_third_party_enabled', $enabled );
}

/**
 * The inline loader printed right after the placeholder. One function, so
 * the test file and the tag share the same bytes. Plain ES5, ~500 bytes,
 * no dependencies; runs once per page.
 */
function molosoc_delayed_third_party_loader_js() {
	return '(function(){var d=document,w=window,done=false,evs=["scroll","touchstart","pointerdown","keydown","mousemove"];'
		. 'function go(){if(done){return;}done=true;evs.forEach(function(n){w.removeEventListener(n,go,{passive:true});});'
		. 'var ps=d.querySelectorAll("script[data-molosoc-delayed-src]");for(var i=0;i<ps.length;i++){var s=d.createElement("script");s.async=true;s.src=ps[i].getAttribute("data-molosoc-delayed-src");d.head.appendChild(s);}}'
		. 'function idle(){if("requestIdleCallback" in w){w.requestIdleCallback(go,{timeout:2500});}else{w.setTimeout(go,2000);}}'
		. 'evs.forEach(function(n){w.addEventListener(n,go,{passive:true});});'
		. 'if(d.readyState==="complete"){idle();}else{w.addEventListener("load",idle);}})();';
}

/**
 * script_loader_tag at priority 100: after WordPress has built the tag and
 * after WP-Optimize's blanket defer filter, so this sees the final markup
 * and replaces it whole. Only the listed handles, only where enabled.
 *
 * @param string $tag    The <script> tag WordPress is about to print.
 * @param string $handle Script handle.
 * @param string $src    Script URL.
 * @return string The placeholder + loader, or $tag untouched.
 */
function molosoc_delayed_third_party_tag( $tag, $handle, $src = '' ) {
	if ( ! in_array( $handle, molosoc_delayed_third_party_handles(), true ) || ! $src || ! molosoc_delayed_third_party_enabled() ) {
		return $tag;
	}
	static $loader_printed = false;
	$out = sprintf(
		'<script type="text/plain" id="%s-js" data-molosoc-delayed-src="%s"></script>' . "\n",
		esc_attr( $handle ),
		esc_url( $src )
	);
	if ( ! $loader_printed ) {
		$loader_printed = true;
		$out .= '<script id="molosoc-delayed-third-party-loader">' . molosoc_delayed_third_party_loader_js() . '</script>' . "\n";
	}
	return $out;
}
add_filter( 'script_loader_tag', 'molosoc_delayed_third_party_tag', 100, 3 );
