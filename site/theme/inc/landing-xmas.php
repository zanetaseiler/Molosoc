<?php
/**
 * Christmas 2026 gift landing page (Issue #251) — CZ + EN, based on Landing B.
 *
 * Templates: page-vanocni-darek-molosoc.php (CZ, /cz/vanocni-darek-molosoc/)
 * and page-christmas-gift-molosoc.php (EN, /christmas-gift-molosoc/), both
 * rendering template-parts/landing-xmas.php. Landing A, B, the product pages,
 * checkout and the homepage are not touched.
 *
 * RELEASE GATE. The pages are noindex + out of the sitemap only while the
 * filter `molosoc_xmas_published` returns false. It now defaults to true
 * (Issue #260, approved by Žaneta), so the two pages are indexable and in the
 * sitemap once the WP pages are published. This file never creates or
 * publishes a WP page; draft pages stay non-public.
 *
 * BUNDLE PURCHASE. The visitor picks 1, 2 or 3 pairs and M/L per pair, or
 * (Issue #364) the "4 a více párů / 4 or more pairs" card with M/L counters
 * (4..molosoc_xmas_max_pairs() = 10 pairs). Both end in the same URL: the
 * button opens the checkout URL with `molosoc_xmas=1&molosoc_xmas_sizes=M,L,…`
 * (one size per pair); molosoc_xmas_add_to_cart() (wp_loaded) validates the
 * sizes server-side, resolves the real variations of Woo product 364
 * (inventory is theirs; no extra SKU), checks that each variation has stock
 * for every pair asked of it, and adds one cart line PER PAIR, each tagged
 * `molosoc_xmas_slot` 1..n, then redirects to the clean checkout URL. Not
 * enough stock: the cart stays as it was and the visitor goes back to the
 * landing page with a localized message (molosoc_xmas_stock_message()).
 *
 * PRICING (approved by Žaneta 2026-10-26, extended 2026-11-11 in Issue #364):
 * pair 1 = 209 Kč, every further pair = 199 Kč, i.e. 209 / 408 / 607 / 806 /
 * 1005 / … / 2000 Kč for 1 / 2 / 3 / 4 / 5 / … / 10 pairs. The price is
 * derived on the server from the slot tag only (never from the request), set
 * on the cart line's product object in woocommerce_before_calculate_totals, so
 * WooCommerce taxes, shipping and payment run on it unchanged. Rows without
 * the tag (every other add-to-cart, the evergreen pages) keep the normal 229 Kč
 * Woo price, and the post-purchase gift add-on rows (`molosoc_gift_slot`) are
 * never read or modified here.
 */

defined( 'ABSPATH' ) || exit;

/** Page slugs: CZ and EN. */
function molosoc_xmas_slugs() {
	return array( 'cz' => 'vanocni-darek-molosoc', 'en' => 'christmas-gift-molosoc' );
}

/** 'cz' | 'en' | '' for the current request. */
function molosoc_xmas_current_lang() {
	foreach ( molosoc_xmas_slugs() as $lang => $slug ) {
		if ( is_page( $slug ) ) {
			return $lang;
		}
	}
	return '';
}

/** True on either Christmas page (the no-plugin-markup gate in functions.php reads this, Issue #295). */
function molosoc_is_xmas_landing() {
	return '' !== molosoc_xmas_current_lang();
}

/**
 * The facts quoted on the page (Issue #295): one source for the hero line, the
 * size buttons, the FAQ answers, the info block under each checkout button and
 * the size hint under the pair-1 label, so a change here changes every place
 * at once. Numbers only; the sentences around them live in
 * template-parts/landing-xmas.php. The shipping price is the cheapest method
 * offered at checkout ("from"); nothing here changes a price, a shipping rate
 * or the checkout.
 *
 * @param string $lang 'cz' | 'en'.
 * @return array size_m / size_l (shoe-size ranges), ship_from (int, CZK), order_by (date as text).
 */
function molosoc_xmas_facts( $lang ) {
	$en = 'en' === $lang;
	return array(
		'size_m'    => '36–39',
		'size_l'    => $en ? '39.5–44' : '39,5–44',
		'ship_from' => 69,
		'order_by'  => $en ? '18 December' : '18. prosince',
	);
}

/** Release flag: on by default (Issue #260, ZANETA_DECISION 2026-10-26); the filter can still switch it off. */
function molosoc_xmas_published() {
	return (bool) apply_filters( 'molosoc_xmas_published', true );
}

/**
 * Most pairs one Christmas bundle may hold (Issue #364): 10 by default. The
 * filter is clamped to 3..10, so the 1/2/3 cards always work and a bad filter
 * can never open the bundle wider than the approved price list.
 */
function molosoc_xmas_max_pairs() {
	$max = (int) apply_filters( 'molosoc_xmas_max_pairs', 10 );
	return max( 3, min( 10, $max ) );
}

/** Fewest pairs of the "4 a více párů / 4 or more pairs" card (Issue #364). */
function molosoc_xmas_multi_min() {
	return 4;
}

/**
 * Unit price of each pair of one Christmas bundle (CZK), slot 1..max.
 * Approved: 209 for pair 1, 199 for every further pair (Issue #364). The
 * filter must return a positive number for EVERY slot 1..max; anything else
 * is rejected, so a bad filter can never produce a zero or negative price.
 *
 * @return float[]|int[] slot (1-based) => price
 */
function molosoc_xmas_unit_prices() {
	$max     = molosoc_xmas_max_pairs();
	$default = array( 1 => 209 );
	for ( $slot = 2; $slot <= $max; $slot++ ) {
		$default[ $slot ] = 199;
	}
	$prices = apply_filters( 'molosoc_xmas_unit_prices', $default );
	if ( ! is_array( $prices ) ) {
		return $default;
	}
	$out = array();
	for ( $slot = 1; $slot <= $max; $slot++ ) {
		if ( ! isset( $prices[ $slot ] ) || ! is_numeric( $prices[ $slot ] ) || (float) $prices[ $slot ] <= 0 ) {
			return $default;
		}
		$out[ $slot ] = (float) $prices[ $slot ];
	}
	return $out;
}

/** Bundle total for $pairs (1..max). */
function molosoc_xmas_bundle_total( $pairs ) {
	$prices = molosoc_xmas_unit_prices();
	$total  = 0;
	for ( $i = 1; $i <= max( 0, min( molosoc_xmas_max_pairs(), (int) $pairs ) ); $i++ ) {
		$total += $prices[ $i ];
	}
	return $total;
}

/** Parse "M,L,M" into a list of 1..max valid size keys, or array() when invalid. */
function molosoc_xmas_parse_sizes( $raw ) {
	$sizes = array_map( 'trim', explode( ',', strtoupper( (string) $raw ) ) );
	if ( count( $sizes ) < 1 || count( $sizes ) > molosoc_xmas_max_pairs() ) {
		return array();
	}
	foreach ( $sizes as $size ) {
		if ( 'M' !== $size && 'L' !== $size ) {
			return array();
		}
	}
	return $sizes;
}

/** Checkout URL of the requested language (falls back to Woo's). */
function molosoc_xmas_checkout_url( $lang ) {
	if ( ! function_exists( 'wc_get_checkout_url' ) ) {
		return home_url( 'cz' === $lang ? '/cz/pokladna/' : '/checkout/' );
	}
	if ( function_exists( 'wc_get_page_id' ) && function_exists( 'pll_get_post' ) ) {
		$checkout_id = wc_get_page_id( 'checkout' );
		$id          = $checkout_id > 0 ? pll_get_post( $checkout_id, $lang ) : 0;
		if ( $id && 'publish' === get_post_status( $id ) ) {
			return get_permalink( $id );
		}
	}
	return wc_get_checkout_url();
}

/**
 * variation_id + attributes per size key, read from Landing B's resolver
 * (read-only reuse: it already handles "Any size" variations and stock).
 *
 * @return array size key => array( 'variation_id' => int, 'attributes' => array )
 */
function molosoc_xmas_variations() {
	$out = array();
	if ( ! function_exists( 'molosoc_landing_b_buy_links' ) ) {
		return $out;
	}
	foreach ( molosoc_landing_b_buy_links() as $key => $link ) {
		if ( empty( $link['direct'] ) ) {
			continue;
		}
		$query = array();
		wp_parse_str( (string) wp_parse_url( $link['url'], PHP_URL_QUERY ), $query );
		if ( empty( $query['variation_id'] ) ) {
			continue;
		}
		$attributes = array();
		foreach ( $query as $name => $value ) {
			if ( 0 === strpos( $name, 'attribute_' ) ) {
				$attributes[ $name ] = (string) $value;
			}
		}
		$out[ $key ] = array( 'variation_id' => (int) $query['variation_id'], 'attributes' => $attributes );
	}
	return $out;
}

/** URL of the Christmas landing page of $lang (falls back to the home page). */
function molosoc_xmas_page_url( $lang ) {
	$slugs = molosoc_xmas_slugs();
	$slug  = 'en' === $lang ? $slugs['en'] : $slugs['cz'];
	$page  = function_exists( 'get_page_by_path' ) ? get_page_by_path( $slug ) : null;
	if ( $page && 'publish' === get_post_status( $page ) ) {
		return get_permalink( $page );
	}
	return home_url( 'en' === $lang ? '/' . $slug . '/' : '/cz/' . $slug . '/' );
}

/**
 * Stock problems of a requested size list (Issue #364), checked BEFORE the
 * cart is touched. Pairs are counted per variation (an "Any size" variation
 * may serve both M and L, so M=8 + L=2 asks 10 of it), and units of that
 * variation already in the cart on other lines (not the Christmas lines,
 * which the add replaces) are counted too, as WooCommerce itself does.
 *
 * @param string[] $sizes      Parsed size list.
 * @param array    $variations molosoc_xmas_variations() output.
 * @param object   $cart       WC_Cart (or a stand-in with get_cart()).
 * @return array array() when fine, else array( 'size' => 'M'|'L'|'', 'left' => int ).
 */
function molosoc_xmas_stock_problem( array $sizes, array $variations, $cart ) {
	$wanted = array(); // variation_id => pairs asked
	$by_vid = array(); // variation_id => first size key using it
	foreach ( $sizes as $size ) {
		if ( ! isset( $variations[ $size ] ) ) {
			return array( 'size' => $size, 'left' => 0 ); // sold out: no purchasable variation for this size.
		}
		$vid            = (int) $variations[ $size ]['variation_id'];
		$wanted[ $vid ] = ( isset( $wanted[ $vid ] ) ? $wanted[ $vid ] : 0 ) + 1;
		if ( ! isset( $by_vid[ $vid ] ) ) {
			$by_vid[ $vid ] = $size;
		}
	}
	$in_cart = array();
	if ( is_object( $cart ) && method_exists( $cart, 'get_cart' ) ) {
		foreach ( $cart->get_cart() as $item ) {
			if ( isset( $item['molosoc_xmas_slot'] ) ) {
				continue;
			}
			$vid = isset( $item['variation_id'] ) ? (int) $item['variation_id'] : 0;
			if ( $vid && isset( $wanted[ $vid ] ) ) {
				$in_cart[ $vid ] = ( isset( $in_cart[ $vid ] ) ? $in_cart[ $vid ] : 0 ) + (int) $item['quantity'];
			}
		}
	}
	foreach ( $wanted as $vid => $pairs ) {
		$variation = function_exists( 'wc_get_product' ) ? wc_get_product( $vid ) : null;
		$shared    = 0;
		foreach ( $variations as $v ) {
			$shared += (int) $v['variation_id'] === $vid ? 1 : 0;
		}
		$size = $shared > 1 ? '' : $by_vid[ $vid ]; // one variation for both sizes: name no size.
		if ( ! $variation || ! $variation->is_purchasable() || ! $variation->is_in_stock() ) {
			return array( 'size' => $size, 'left' => 0 );
		}
		if ( $variation->managing_stock() && ! $variation->backorders_allowed() ) {
			$left = max( 0, (int) $variation->get_stock_quantity() - ( isset( $in_cart[ $vid ] ) ? $in_cart[ $vid ] : 0 ) );
			if ( $pairs > $left ) {
				return array( 'size' => $size, 'left' => $left );
			}
		}
	}
	return array();
}

/**
 * Localized stock message shown on the landing page after a refused bundle.
 * $size '' = a variation shared by both sizes (or unknown): no size named.
 * $left < 0 = WooCommerce refused the add for a reason not caught above.
 */
function molosoc_xmas_stock_message( $lang, $size, $left ) {
	$size = 'M' === $size || 'L' === $size ? $size : '';
	$left = (int) $left;
	if ( 'en' === $lang ) {
		if ( $left < 0 ) {
			return 'We could not add that many pairs right now. Please choose fewer pairs and try again.';
		}
		if ( 0 === $left ) {
			return $size ? sprintf( 'Size %s is sold out right now. Please choose the other size.', $size ) : 'This item is sold out right now.';
		}
		$pairs = 1 === $left ? '1 pair' : $left . ' pairs';
		return $size
			? sprintf( 'Only %1$s of size %2$s left in stock. Please choose fewer pairs of size %2$s and try again.', $pairs, $size )
			: sprintf( 'Only %s left in stock. Please choose fewer pairs and try again.', $pairs );
	}
	if ( $left < 0 ) {
		return 'Tolik párů teď nemůžeme přidat do košíku. Vyberte prosím méně párů a zkuste to znovu.';
	}
	if ( 0 === $left ) {
		return $size ? sprintf( 'Velikost %s je momentálně vyprodaná. Vyberte prosím druhou velikost.', $size ) : 'Zboží je momentálně vyprodané.';
	}
	$pairs = 1 === $left ? '1 pár' : ( $left <= 4 ? $left . ' páry' : $left . ' párů' );
	return $size
		? sprintf( 'Velikosti %1$s máme skladem jen %2$s. Vyberte prosím méně párů velikosti %1$s a zkuste to znovu.', $size, $pairs )
		: sprintf( 'Skladem máme jen %s. Vyberte prosím méně párů a zkuste to znovu.', $pairs );
}

/**
 * The stock message for the current landing request, from the redirect's
 * query args (lpx_stock = M|L|any|add, lpx_left = 0..max), or '' when none.
 * Only these whitelisted values are read; the text itself is built here.
 */
function molosoc_xmas_stock_notice( $lang ) {
	if ( ! isset( $_GET['lpx_stock'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		return '';
	}
	$code = strtolower( sanitize_key( wp_unslash( $_GET['lpx_stock'] ) ) ); // phpcs:ignore WordPress.Security.NonceVerification
	$left = isset( $_GET['lpx_left'] ) ? (int) $_GET['lpx_left'] : 0; // phpcs:ignore WordPress.Security.NonceVerification
	$left = max( 0, min( molosoc_xmas_max_pairs(), $left ) );
	if ( 'add' === $code ) {
		return molosoc_xmas_stock_message( $lang, '', -1 );
	}
	if ( 'm' === $code || 'l' === $code ) {
		return molosoc_xmas_stock_message( $lang, strtoupper( $code ), $left );
	}
	if ( 'any' === $code ) {
		return molosoc_xmas_stock_message( $lang, '', $left );
	}
	return '';
}

/** Back to the landing page's picker with a stock code (never touches the cart). */
function molosoc_xmas_stock_redirect_url( $lang, $code, $left = 0 ) {
	return add_query_arg(
		array( 'lpx_stock' => $code, 'lpx_left' => max( 0, (int) $left ) ),
		molosoc_xmas_page_url( $lang )
	) . '#lpx-bundle';
}

/** Purchase URL for a size list; '' when nothing valid. */
function molosoc_xmas_buy_url( array $sizes, $lang ) {
	if ( ! $sizes ) {
		return '';
	}
	return add_query_arg(
		array( 'molosoc_xmas' => 1, 'molosoc_xmas_sizes' => implode( ',', $sizes ) ),
		molosoc_xmas_checkout_url( $lang )
	);
}

/**
 * Add the bundle (wp_loaded, after WooCommerce's own handler at 20). Replaces
 * an earlier Christmas selection in the cart instead of stacking onto it.
 */
add_action( 'wp_loaded', 'molosoc_xmas_add_to_cart', 30 );
function molosoc_xmas_add_to_cart() {
	if ( empty( $_GET['molosoc_xmas'] ) || ! isset( $_GET['molosoc_xmas_sizes'] ) || ! function_exists( 'WC' ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		return;
	}
	$sizes = molosoc_xmas_parse_sizes( wp_unslash( $_GET['molosoc_xmas_sizes'] ) ); // phpcs:ignore WordPress.Security.NonceVerification
	$lang  = ( function_exists( 'pll_current_language' ) && 'en' === pll_current_language() ) ? 'en' : 'cz';
	if ( ! $sizes ) {
		wp_safe_redirect( molosoc_product_url( $lang ) );
		exit;
	}
	if ( null === WC()->cart && function_exists( 'wc_load_cart' ) ) {
		wc_load_cart();
	}
	$cart       = WC()->cart;
	$variations = molosoc_xmas_variations();
	if ( ! $cart || ! $variations ) {
		wp_safe_redirect( molosoc_product_url( $lang ) );
		exit;
	}
	// Issue #364: every pair asked of each variation must be in stock before
	// anything is removed or added; otherwise the cart stays untouched.
	$problem = molosoc_xmas_stock_problem( $sizes, $variations, $cart );
	if ( $problem ) {
		wp_safe_redirect( molosoc_xmas_stock_redirect_url( $lang, '' === $problem['size'] ? 'any' : strtolower( $problem['size'] ), $problem['left'] ) );
		exit;
	}
	$snapshot = $cart->get_cart_contents();
	foreach ( $cart->get_cart() as $key => $item ) {
		if ( isset( $item['molosoc_xmas_slot'] ) ) {
			$cart->remove_cart_item( $key );
		}
	}
	foreach ( $sizes as $i => $size ) {
		$v = $variations[ $size ];
		// One line per pair: a unique slot tag keeps lines apart and fixes the price.
		$added = $cart->add_to_cart( MOLOSOC_PRODUCT_ID, 1, $v['variation_id'], $v['attributes'], array( 'molosoc_xmas_slot' => $i + 1 ) );
		if ( ! $added ) {
			// All or nothing: put the cart back as it was (e.g. stock held by another order).
			$cart->set_cart_contents( $snapshot );
			$cart->calculate_totals();
			if ( method_exists( $cart, 'set_session' ) ) {
				$cart->set_session();
			}
			wp_safe_redirect( molosoc_xmas_stock_redirect_url( $lang, 'add' ) );
			exit;
		}
	}
	wp_safe_redirect( molosoc_xmas_checkout_url( $lang ) );
	exit;
}

/**
 * Reprice tagged lines. Priority 20 (the gift add-on runs at 100 and only
 * touches its own rows). Eligible lines (tagged, product 364, quantity 1) are
 * ranked by slot tag and priced by rank, so removing a line from the bundle
 * re-packs the remaining ones (1 pair 209, 2 pairs 408, 3 pairs 607, … 10
 * pairs 2000). Any
 * other tagged line goes back to its remembered normal Woo price.
 */
add_action( 'woocommerce_before_calculate_totals', 'molosoc_xmas_apply_prices', 20, 1 );
function molosoc_xmas_apply_prices( $cart ) {
	if ( ! is_object( $cart ) || ! method_exists( $cart, 'get_cart' ) || ( is_admin() && ! defined( 'DOING_AJAX' ) ) ) {
		return;
	}
	$prices   = molosoc_xmas_unit_prices();
	$eligible = array();
	foreach ( $cart->get_cart() as $key => $item ) {
		if ( isset( $item['molosoc_gift_slot'] ) || ! isset( $item['molosoc_xmas_slot'], $item['data'] ) || ! is_object( $item['data'] ) ) {
			continue;
		}
		$base = $item['data']->get_meta( '_molosoc_xmas_base_price', true, 'edit' );
		if ( '' === (string) $base ) {
			$base = $item['data']->get_price( 'edit' );
			$item['data']->update_meta_data( '_molosoc_xmas_base_price', $base );
		}
		$slot = (int) $item['molosoc_xmas_slot'];
		if ( isset( $prices[ $slot ] ) && 1 === (int) $item['quantity'] && MOLOSOC_PRODUCT_ID === (int) $item['product_id'] ) {
			$eligible[] = array( 'slot' => $slot, 'item' => $item );
		} else {
			$item['data']->set_price( $base );
		}
	}
	usort( $eligible, function ( $a, $b ) {
		return $a['slot'] <=> $b['slot'];
	} );
	foreach ( $eligible as $rank => $row ) {
		$unit = $rank + 1;
		if ( isset( $prices[ $unit ] ) ) {
			$row['item']['data']->set_price( $prices[ $unit ] );
		} else {
			$row['item']['data']->set_price( $row['item']['data']->get_meta( '_molosoc_xmas_base_price', true, 'edit' ) );
		}
	}
}

/* ---------- release gate: noindex + sitemap exclusion until published ---------- */

add_filter( 'wp_robots', function ( $robots ) {
	if ( molosoc_xmas_current_lang() && ! molosoc_xmas_published() ) {
		$robots['noindex']  = true;
		$robots['nofollow'] = false;
	}
	return $robots;
} );

add_filter( 'wp_sitemaps_posts_query_args', function ( $args, $post_type ) {
	if ( 'page' === $post_type && ! molosoc_xmas_published() ) {
		$ids = array();
		foreach ( molosoc_xmas_slugs() as $slug ) {
			$page = get_page_by_path( $slug );
			if ( $page ) {
				$ids[] = (int) $page->ID;
			}
		}
		$args['post__not_in'] = array_merge( isset( $args['post__not_in'] ) ? (array) $args['post__not_in'] : array(), $ids );
	}
	return $args;
}, 10, 2 );

/* ---------- document title + description ---------- */

function molosoc_xmas_meta( $lang ) {
	if ( 'en' === $lang ) {
		return array(
			'title' => 'Christmas gift for her: reusable foot mask | Molosoc',
			'desc'  => 'A small, practical Christmas gift: reusable nitrile foot covers that turn an ordinary foot cream into a simple caring ritual. Pick 1 to 10 pairs.',
		);
	}
	return array(
		'title' => 'Vánoční dárek pro maminku: maska na nohy | Molosoc',
		'desc'  => 'Malý praktický vánoční dárek: opakovaně použitelné nitrilové návleky, které promění obyčejný krém na nohy v pečující rituál. Vyberte 1 až 10 párů.',
	);
}

add_filter( 'pre_get_document_title', function ( $title ) {
	$lang = molosoc_xmas_current_lang();
	return $lang ? molosoc_xmas_meta( $lang )['title'] : $title;
} );

add_action( 'wp_head', function () {
	$lang = molosoc_xmas_current_lang();
	if ( $lang ) {
		printf( '<meta name="description" content="%s">' . "\n", esc_attr( molosoc_xmas_meta( $lang )['desc'] ) );
	}
}, 2 );

/* ---------- images ---------- */

/**
 * The three owner-edited Christmas photos (Drive IDs in Issue #251), imported
 * as 1536x1024 WebP files into assets/images/landing-xmas/ (Issue #255).
 * Issue #295 adds 480/768/1080 px derivatives next to each one
 * ("<file minus .webp>-<w>.webp"; cwebp -m 6 -sharp_yuv at q 75/70/60) so a
 * phone no longer downloads the 1536 px file for a ~350 px slot; the 1536 px
 * original stays the largest srcset candidate. Until the original exists,
 * molosoc_xmas_image() prints nothing for it; a missing derivative is simply
 * left out of the srcset.
 */
function molosoc_xmas_images() {
	return array(
		'scene-01' => array( 'file' => 'MOLOSOC_Christmas_Gift_Scene_01.webp', 'drive' => '1JHezsiFVICxddNfOX1_7AQfe1Nq36u9k' ),
		'scene-02' => array( 'file' => 'MOLOSOC_Christmas_Gift_Scene_02.webp', 'drive' => '12WhUf4aciD21JAoG1_X1cC1-mY8Sto0M' ),
		'scene-03' => array( 'file' => 'MOLOSOC_Christmas_Gift_Scene_03.webp', 'drive' => '18RlEVxkbHFW0hH7LRUlLBitualjBxsvm' ),
	);
}

/** Derivative widths generated for every scene (the original is 1536 px). */
function molosoc_xmas_image_widths() {
	return array( 480, 768, 1080 );
}

/**
 * The `sizes` attribute per slot. Hero: one column up to 900 px (.lpx-hero has
 * 20 px padding each side), the left half of the 1080 px grid above that
 * ((1080 - 32 gap) / 2). The two lazy figures run the section width, max 1080.
 */
function molosoc_xmas_image_sizes( $key ) {
	return 'scene-01' === $key
		? '(max-width: 900px) calc(100vw - 40px), 524px'
		: '(max-width: 1120px) calc(100vw - 40px), 1080px';
}

/**
 * src / srcset / sizes / width / height of a scene, or array() when the
 * original file is missing. One place, so the <img> (molosoc_xmas_image())
 * and the head preload (molosoc_xmas_head()) carry byte-identical candidates
 * and the browser fetches exactly one file.
 */
function molosoc_xmas_image_set( $key ) {
	$all = molosoc_xmas_images();
	if ( ! isset( $all[ $key ] ) ) {
		return array();
	}
	$dir  = get_stylesheet_directory() . '/assets/images/landing-xmas/';
	$uri  = get_stylesheet_directory_uri() . '/assets/images/landing-xmas/';
	$file = $all[ $key ]['file'];
	$path = $dir . $file;
	if ( ! file_exists( $path ) ) {
		return array();
	}
	$size   = getimagesize( $path );
	$base   = preg_replace( '/\.webp$/', '', $file );
	$srcset = array();
	foreach ( molosoc_xmas_image_widths() as $w ) {
		if ( file_exists( $dir . $base . '-' . $w . '.webp' ) ) {
			$srcset[] = esc_url( $uri . $base . '-' . $w . '.webp' ) . ' ' . (int) $w . 'w';
		}
	}
	$srcset[] = esc_url( $uri . $file ) . ' ' . ( $size ? (int) $size[0] : 1536 ) . 'w';
	return array(
		'src'    => esc_url( $uri . $file ),
		'srcset' => implode( ', ', $srcset ),
		'sizes'  => molosoc_xmas_image_sizes( $key ),
		'width'  => $size ? (int) $size[0] : 0,
		'height' => $size ? (int) $size[1] : 0,
	);
}

/** <img> markup for a scene, or '' when the file has not been added yet. */
function molosoc_xmas_image( $key, $alt, $attrs = '' ) {
	$set = molosoc_xmas_image_set( $key );
	if ( ! $set ) {
		return '';
	}
	$wh = $set['width'] ? sprintf( ' width="%d" height="%d"', $set['width'], $set['height'] ) : '';
	return sprintf(
		'<img src="%s" srcset="%s" sizes="%s" alt="%s"%s decoding="async" %s>',
		$set['src'],
		esc_attr( $set['srcset'] ),
		esc_attr( $set['sizes'] ),
		esc_attr( $alt ),
		$wh,
		$attrs
	);
}

/* ---------- <head>: hero preload (Issue #295) ---------- */

/**
 * Printed raw at wp_head priority 1 — before the render-blocking stylesheets
 * and outside WP-Optimize Minify's reach, the same pattern as
 * molosoc_landing_b_head(): the hero candidates as a preload, so the request
 * starts with the HTML instead of after the CSS bundle has parsed. The browser
 * picks the same candidate as for the <img> because srcset/sizes are
 * byte-identical (both come from molosoc_xmas_image_set()).
 */
function molosoc_xmas_head() {
	if ( ! molosoc_is_xmas_landing() ) {
		return;
	}
	$set = molosoc_xmas_image_set( 'scene-01' );
	if ( ! $set ) {
		return;
	}
	printf(
		'<link rel="preload" as="image" fetchpriority="high" href="%s" imagesrcset="%s" imagesizes="%s">' . "\n",
		esc_url( $set['src'] ),
		esc_attr( $set['srcset'] ),
		esc_attr( $set['sizes'] )
	);
}
add_action( 'wp_head', 'molosoc_xmas_head', 1 );

/* ---------- sticky pill (Issue #299) ---------- */

/**
 * The site-wide "Koupit nyní" pill (functions.php wp_head hook → sticky-cta.js)
 * links to the regular product page, where the Christmas price does not
 * apply: order #1073 (30 Oct 2026) came from the Christmas ad, tapped the pill
 * and paid 229 Kč instead of 209 Kč. On the two Christmas pages the pill is
 * an in-page link to the picker (#lpx-bundle, the hero button's target) with
 * its own label; landing-xmas.js smooth-scrolls it, keeps the URL and hides
 * the pill while a buy box is on screen. Every other page keeps
 * molosoc_product_url() and "Koupit nyní" / "Buy now".
 *
 * @param array  $data Override so far (empty by default).
 * @param string $lang Polylang language of the request (unused: the page's own language decides).
 * @return array url + label on the Christmas pages, $data elsewhere.
 */
function molosoc_xmas_sticky_cta( $data, $lang = '' ) {
	$page_lang = molosoc_xmas_current_lang();
	if ( ! $page_lang ) {
		return $data;
	}
	return array(
		'url'   => '#lpx-bundle',
		'label' => 'en' === $page_lang ? 'Choose gift set' : 'Vybrat dárkový set',
	);
}
add_filter( 'molosoc_sticky_cta_data', 'molosoc_xmas_sticky_cta', 10, 2 );

/* ---------- header logo (Issue #295) ---------- */

/**
 * On the two Christmas pages only, the header logo comes from two theme-hosted
 * lossless WebP derivatives (408 and 612 px wide, ~4 and ~6.5 KB) of the
 * 1567x230 upload; the display size is 205x30 px (164x24 below 381 px,
 * components.css), so 612 px covers 3x screens. Every other page keeps the
 * default markup of molosoc_site_header_logo() untouched, and so does this
 * page when a derivative is missing.
 */
function molosoc_xmas_header_logo( $html ) {
	if ( ! molosoc_is_xmas_landing() ) {
		return $html;
	}
	$dir = get_stylesheet_directory() . '/assets/images/';
	if ( ! file_exists( $dir . 'molosoc-logo-tm-408.webp' ) || ! file_exists( $dir . 'molosoc-logo-tm-612.webp' ) ) {
		return $html;
	}
	$uri = get_stylesheet_directory_uri() . '/assets/images/';
	return sprintf(
		'<img src="%1$s" srcset="%2$s 408w, %1$s 612w" sizes="(max-width: 380px) 164px, 205px" width="612" height="90" alt="%3$s" loading="eager" decoding="async">',
		esc_url( $uri . 'molosoc-logo-tm-612.webp' ),
		esc_url( $uri . 'molosoc-logo-tm-408.webp' ),
		esc_attr( get_bloginfo( 'name' ) )
	);
}
add_filter( 'molosoc_site_header_logo', 'molosoc_xmas_header_logo' );
