<?php
/**
 * Plugin Name: MOLOSOC CZ Home Redirect
 * Description: 302s first-time visitors whose browser prefers Czech or Slovak from the bare site home (/) to Polylang's Czech home, keeping the query string. Only the bare home is touched; it is kept out of the WP-Optimize page cache so the decision always runs in PHP. Issue #293.
 * Version: 1.0.0
 *
 * Why a mu-plugin and not Polylang's "Detect browser language"
 * (Languages > Settings > URL modifications):
 *
 *   - WP-Optimize's advanced-cache serves a cached `/` before mu-plugins,
 *     plugins or the theme run (cache/file-based-page-cache.php calls
 *     wpo_serve_cache() at include time) and wpo_can_serve_from_cache()
 *     never looks at Accept-Language. Any PHP-side redirect therefore only
 *     works if `/` is never written to the page cache.
 *   - Polylang's own setting knows that: PLL_Cache_Compat::do_not_cache_site_home
 *     defines DONOTCACHEPAGE on the default-language front page whenever
 *     browser detection is on. That is why it was switched OFF on
 *     2026-08-20 (every `/` hit became a 1-4 s PHP render) and replaced by
 *     the client-side script in front-page.php. The customer behind
 *     Issue #293 still landed on the English home, so the redirect moves
 *     back to the server with the same cache trade-off, but limited to
 *     exactly the bare `/` request.
 *   - Polylang's detection also redirects every `pll_language=cz` cookie
 *     holder, has no bot exclusion and does not map Slovak to Czech; all
 *     three are requirements of Issue #293.
 *
 * Behaviour (bare `/` only, GET or HEAD; everything else is untouched):
 *
 *   1. DONOTCACHEPAGE is defined so WP-Optimize never caches `/`
 *      (with or without a query string: `/?utm_source=x` is served from
 *      the `/` cache file otherwise).
 *   2. `Vary: Accept-Language` is added to the response, redirect or not.
 *   3. The visitor is 302-redirected to pll_home_url( 'cz' ) plus the
 *      original query string when ALL of these hold:
 *        - no `pll_language` cookie (Polylang sets it on every page view,
 *          so one visit to any page in either language ends the
 *          redirects: a manual choice is never overridden);
 *        - no same-site referer (the EN link in the language switcher and
 *          every other in-site navigation always reaches the English home,
 *          same test Polylang uses in get_home_language());
 *        - the user agent is not a known bot/crawler/link-previewer;
 *        - the highest-q language in Accept-Language is `cs` or `sk`.
 *   4. The redirect target comes from Polylang at runtime; nothing is
 *      hard-coded. If Polylang or its `cz` language is missing the plugin
 *      does nothing.
 *
 * Hooked on plugins_loaded (priority 20, after Polylang's own init at 1)
 * so a redirected visitor never pays for the theme, the main query or the
 * template. The EN front page keeps its client-side script, which still
 * sends returning `pll_language=cz` visitors to the Czech home.
 *
 * Removal: delete this file from site/mu-plugins/ (deploy-mu-plugins.yml
 * syncs deletions) and drop its `need` line from that workflow.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( ! defined( 'MOLOSOC_CZ_HOME_POLYLANG_SLUG' ) ) {
	define( 'MOLOSOC_CZ_HOME_POLYLANG_SLUG', 'cz' );
}

/**
 * Primary language subtags that should land on the Czech home.
 *
 * @return string[]
 */
function molosoc_cz_home_languages() {
	return array( 'cs', 'sk' );
}

/**
 * True when the request path is exactly the site home ("/" for a root
 * install), ignoring the query string. Pure: no WordPress dependencies.
 *
 * @param string $request_uri $_SERVER['REQUEST_URI'].
 * @param string $home_path   Path component of home_url( '/' ).
 * @return bool
 */
function molosoc_cz_home_is_bare_home_path( $request_uri, $home_path = '/' ) {
	$path = parse_url( (string) $request_uri, PHP_URL_PATH ); // phpcs:ignore WordPress.WP.AlternativeFunctions.parse_url_parse_url -- pure helper, testable without WordPress.
	if ( ! is_string( $path ) || '' === $path ) {
		return false;
	}
	$home_path = (string) $home_path;
	if ( '' === $home_path ) {
		$home_path = '/';
	}
	return rtrim( $path, '/' ) === rtrim( $home_path, '/' );
}

/**
 * Primary subtag (e.g. "cs") of the highest-quality entry in an
 * Accept-Language header, or "" when the header has no usable entry.
 * Ties keep the first entry, q=0 entries and wildcards are ignored.
 *
 * @param string $accept_language Raw Accept-Language header value.
 * @return string
 */
function molosoc_cz_home_preferred_language( $accept_language ) {
	$best   = '';
	$best_q = -1.0;

	foreach ( explode( ',', (string) $accept_language ) as $entry ) {
		$params = explode( ';', $entry );
		$tag    = strtolower( trim( (string) array_shift( $params ) ) );

		if ( '' === $tag || ! preg_match( '/^[a-z]{1,8}(?:-[a-z0-9]{1,8})*$/', $tag ) ) {
			continue; // Empty, "*" or malformed.
		}

		$q = 1.0;
		foreach ( $params as $param ) {
			$param = trim( $param );
			if ( 0 === stripos( $param, 'q=' ) ) {
				$value = trim( substr( $param, 2 ) );
				$q     = is_numeric( $value ) ? (float) $value : 0.0;
			}
		}

		if ( $q <= 0 ) {
			continue;
		}
		if ( $q > $best_q ) {
			$best_q = $q;
			$best   = $tag;
		}
	}

	if ( '' === $best ) {
		return '';
	}
	$parts = explode( '-', $best );
	return $parts[0];
}

/**
 * Known crawlers, link previewers and audit tools. They must keep getting
 * the English home so hreflang/canonical discovery is unchanged. An empty
 * user agent is treated as non-human as well.
 *
 * @param string $user_agent Raw User-Agent header value.
 * @return bool
 */
function molosoc_cz_home_is_bot( $user_agent ) {
	$user_agent = trim( (string) $user_agent );
	if ( '' === $user_agent ) {
		return true;
	}
	$pattern = '~bot|crawl|spider|slurp|facebookexternalhit|facebot|twitterbot|linkedinbot|pinterest|whatsapp|telegrambot|skypeuripreview|embedly|quora link preview|outbrain|vkshare|w3c_validator|validator\.nu|lighthouse|pagespeed|gtmetrix|ia_archiver|mediapartners-google|wp-optimize~i';
	return 1 === preg_match( $pattern, $user_agent );
}

/**
 * The whole redirect decision, with every input passed in so it can be
 * unit-tested without WordPress.
 *
 * @param string $accept_language       Raw Accept-Language header value.
 * @param string $user_agent            Raw User-Agent header value.
 * @param bool   $has_language_cookie   Whether the Polylang cookie is set (any value).
 * @param bool   $has_same_site_referer Whether the request came from a page on this site.
 * @param string $method                HTTP request method.
 * @return bool
 */
function molosoc_cz_home_should_redirect( $accept_language, $user_agent, $has_language_cookie, $has_same_site_referer, $method ) {
	if ( ! in_array( strtoupper( (string) $method ), array( 'GET', 'HEAD' ), true ) ) {
		return false;
	}
	if ( $has_language_cookie || $has_same_site_referer ) {
		return false;
	}
	if ( molosoc_cz_home_is_bot( $user_agent ) ) {
		return false;
	}
	return in_array( molosoc_cz_home_preferred_language( $accept_language ), molosoc_cz_home_languages(), true );
}

/**
 * Appends the original query string (utm_*, fbclid, gclid, ...) to the
 * Czech home URL.
 *
 * @param string $cz_home_url  Polylang's Czech home URL.
 * @param string $query_string $_SERVER['QUERY_STRING'].
 * @return string
 */
function molosoc_cz_home_redirect_target( $cz_home_url, $query_string ) {
	$target = (string) $cz_home_url;
	$query  = ltrim( (string) $query_string, '?' );
	if ( '' === $target || '' === $query ) {
		return $target;
	}
	return $target . ( false === strpos( $target, '?' ) ? '?' : '&' ) . $query;
}

/**
 * Polylang's Czech home URL, or "" when it cannot be resolved (Polylang
 * missing, no `cz` language, or the URL collapses to the site home).
 *
 * @return string
 */
function molosoc_cz_home_url() {
	if ( ! function_exists( 'pll_home_url' ) || ! function_exists( 'pll_languages_list' ) ) {
		return '';
	}
	if ( ! in_array( MOLOSOC_CZ_HOME_POLYLANG_SLUG, (array) pll_languages_list(), true ) ) {
		return '';
	}
	$url = (string) pll_home_url( MOLOSOC_CZ_HOME_POLYLANG_SLUG );
	if ( '' === $url || untrailingslashit( $url ) === untrailingslashit( home_url( '/' ) ) ) {
		return '';
	}
	return $url;
}

/**
 * Runs on every front-end request; acts only on the bare site home.
 */
function molosoc_cz_home_maybe_redirect() {
	if ( is_admin() || wp_doing_ajax() || wp_doing_cron() || ( defined( 'REST_REQUEST' ) && REST_REQUEST ) || ( defined( 'WP_CLI' ) && WP_CLI ) ) {
		return;
	}

	$request_uri = isset( $_SERVER['REQUEST_URI'] ) ? (string) wp_unslash( $_SERVER['REQUEST_URI'] ) : ''; // phpcs:ignore WordPress.Security.ValidatedSanitizedInput.InputNotSanitized -- only parsed for its path, never output.
	$home_path   = (string) wp_parse_url( home_url( '/' ), PHP_URL_PATH );
	if ( ! molosoc_cz_home_is_bare_home_path( $request_uri, $home_path ) ) {
		return;
	}

	// The bare home must always reach PHP: WP-Optimize would otherwise
	// serve one visitor's cached English home to everyone.
	if ( ! defined( 'DONOTCACHEPAGE' ) ) {
		define( 'DONOTCACHEPAGE', true );
	}
	if ( ! headers_sent() ) {
		header( 'Vary: Accept-Language', false );
	}

	$cookie_name         = defined( 'PLL_COOKIE' ) ? PLL_COOKIE : 'pll_language';
	$has_language_cookie = ! empty( $cookie_name ) && isset( $_COOKIE[ $cookie_name ] );

	$should_redirect = molosoc_cz_home_should_redirect(
		isset( $_SERVER['HTTP_ACCEPT_LANGUAGE'] ) ? (string) wp_unslash( $_SERVER['HTTP_ACCEPT_LANGUAGE'] ) : '', // phpcs:ignore WordPress.Security.ValidatedSanitizedInput.InputNotSanitized -- compared only, never output.
		isset( $_SERVER['HTTP_USER_AGENT'] ) ? (string) wp_unslash( $_SERVER['HTTP_USER_AGENT'] ) : '', // phpcs:ignore WordPress.Security.ValidatedSanitizedInput.InputNotSanitized -- compared only, never output.
		$has_language_cookie,
		(bool) wp_get_referer(),
		isset( $_SERVER['REQUEST_METHOD'] ) ? (string) $_SERVER['REQUEST_METHOD'] : ''
	);
	if ( ! $should_redirect ) {
		return;
	}

	$cz_home = molosoc_cz_home_url();
	if ( '' === $cz_home ) {
		return;
	}

	$target = molosoc_cz_home_redirect_target(
		$cz_home,
		isset( $_SERVER['QUERY_STRING'] ) ? (string) wp_unslash( $_SERVER['QUERY_STRING'] ) : '' // phpcs:ignore WordPress.Security.ValidatedSanitizedInput.InputNotSanitized -- wp_safe_redirect sanitizes the final URL.
	);

	nocache_headers();
	wp_safe_redirect( $target, 302, 'MOLOSOC CZ Home Redirect' );
	exit;
}
add_action( 'plugins_loaded', 'molosoc_cz_home_maybe_redirect', 20 );
