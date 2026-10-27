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
 * BUNDLE PURCHASE. The visitor picks 1, 2 or 3 pairs and M/L per pair. The
 * button opens the checkout URL with `molosoc_xmas=1&molosoc_xmas_sizes=M,L,…`;
 * molosoc_xmas_add_to_cart() (wp_loaded) validates the sizes server-side,
 * resolves the real variations of Woo product 364 (inventory is theirs; no
 * extra SKU) and adds one cart line PER PAIR, each tagged
 * `molosoc_xmas_slot` 1..3, then redirects to the clean checkout URL.
 *
 * PRICING (approved by Žaneta 2026-10-26): pair 1 = 209 Kč, pairs 2 and 3 =
 * 199 Kč each, i.e. 209 / 408 / 607 Kč for 1 / 2 / 3 pairs. The price is
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

/** Release flag: on by default (Issue #260, ZANETA_DECISION 2026-10-26); the filter can still switch it off. */
function molosoc_xmas_published() {
	return (bool) apply_filters( 'molosoc_xmas_published', true );
}

/**
 * Unit price of the 1st, 2nd and 3rd pair of one Christmas bundle (CZK).
 * Approved: 209 + 199 + 199. Anything else from the filter is rejected, so a
 * bad filter can never produce a zero or negative price.
 *
 * @return int[] slot (1-based) => price
 */
function molosoc_xmas_unit_prices() {
	$default = array( 1 => 209, 2 => 199, 3 => 199 );
	$prices  = apply_filters( 'molosoc_xmas_unit_prices', $default );
	if ( ! is_array( $prices ) ) {
		return $default;
	}
	foreach ( array( 1, 2, 3 ) as $slot ) {
		if ( ! isset( $prices[ $slot ] ) || ! is_numeric( $prices[ $slot ] ) || (float) $prices[ $slot ] <= 0 ) {
			return $default;
		}
	}
	return array( 1 => (float) $prices[1], 2 => (float) $prices[2], 3 => (float) $prices[3] );
}

/** Bundle total for $pairs (1..3). */
function molosoc_xmas_bundle_total( $pairs ) {
	$prices = molosoc_xmas_unit_prices();
	$total  = 0;
	for ( $i = 1; $i <= max( 0, min( 3, (int) $pairs ) ); $i++ ) {
		$total += $prices[ $i ];
	}
	return $total;
}

/** Parse "M,L,M" into a list of 1..3 valid size keys, or array() when invalid. */
function molosoc_xmas_parse_sizes( $raw ) {
	$sizes = array_map( 'trim', explode( ',', strtoupper( (string) $raw ) ) );
	if ( count( $sizes ) < 1 || count( $sizes ) > 3 ) {
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
	foreach ( $sizes as $size ) {
		if ( ! $cart || ! isset( $variations[ $size ] ) ) {
			wp_safe_redirect( molosoc_product_url( $lang ) );
			exit;
		}
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
			// All or nothing: put the cart back as it was (e.g. not enough stock for every pair).
			$cart->set_cart_contents( $snapshot );
			$cart->calculate_totals();
			if ( method_exists( $cart, 'set_session' ) ) {
				$cart->set_session();
			}
			wp_safe_redirect( molosoc_product_url( $lang ) );
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
 * re-packs the remaining ones (1 pair 209, 2 pairs 408, 3 pairs 607). Any
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
			'desc'  => 'A small, practical Christmas gift: reusable nitrile foot covers that turn an ordinary foot cream into a simple caring ritual. Pick 1, 2 or 3 pairs.',
		);
	}
	return array(
		'title' => 'Vánoční dárek pro maminku: maska na nohy | Molosoc',
		'desc'  => 'Malý praktický vánoční dárek: opakovaně použitelné nitrilové návleky, které promění obyčejný krém na nohy v pečující rituál. Vyberte 1, 2 nebo 3 páry.',
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
 * Until a file exists, molosoc_xmas_image() prints nothing for it.
 */
function molosoc_xmas_images() {
	return array(
		'scene-01' => array( 'file' => 'MOLOSOC_Christmas_Gift_Scene_01.webp', 'drive' => '1JHezsiFVICxddNfOX1_7AQfe1Nq36u9k' ),
		'scene-02' => array( 'file' => 'MOLOSOC_Christmas_Gift_Scene_02.webp', 'drive' => '12WhUf4aciD21JAoG1_X1cC1-mY8Sto0M' ),
		'scene-03' => array( 'file' => 'MOLOSOC_Christmas_Gift_Scene_03.webp', 'drive' => '18RlEVxkbHFW0hH7LRUlLBitualjBxsvm' ),
	);
}

/** <img> markup for a scene, or '' when the file has not been added yet. */
function molosoc_xmas_image( $key, $alt, $attrs = '' ) {
	$all = molosoc_xmas_images();
	if ( ! isset( $all[ $key ] ) ) {
		return '';
	}
	$path = get_stylesheet_directory() . '/assets/images/landing-xmas/' . $all[ $key ]['file'];
	if ( ! file_exists( $path ) ) {
		return '';
	}
	$size = getimagesize( $path );
	$wh   = $size ? sprintf( ' width="%d" height="%d"', (int) $size[0], (int) $size[1] ) : '';
	return sprintf(
		'<img src="%s" alt="%s"%s decoding="async" %s>',
		esc_url( get_stylesheet_directory_uri() . '/assets/images/landing-xmas/' . $all[ $key ]['file'] ),
		esc_attr( $alt ),
		$wh,
		$attrs
	);
}
