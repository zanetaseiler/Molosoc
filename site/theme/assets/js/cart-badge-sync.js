/**
 * Keeps the header cart badge (.molosoc-cart-link__count) in sync with
 * WooCommerce's block cart/checkout as the shopper edits quantities or
 * removes items IN PLACE on those pages.
 *
 * Why this exists: the badge has two native refresh paths already —
 * server-rendered PHP on every navigation, and the legacy cart-fragments
 * script for classic add-to-cart events — but the block-based /cart/ and
 * /checkout/ update the cart through the wc/store/cart data store and
 * never fire the legacy fragment events, so the badge sat stale next to
 * a visibly changed cart until the next page load.
 *
 * This is a read-only mirror of WooCommerce's own store (wp.data
 * subscribe → getCartData().itemsCount), not cart state of our own. On
 * pages without the block store (most of the site) it does nothing.
 */
( function () {
	function init() {
		if ( ! window.wp || ! wp.data || ! wp.data.select || ! wp.data.subscribe ) {
			return;
		}
		var store;
		try {
			store = wp.data.select( 'wc/store/cart' );
		} catch ( e ) {
			return;
		}
		if ( ! store || ! store.getCartData ) {
			return;
		}

		var last = null;
		wp.data.subscribe( function () {
			var data = wp.data.select( 'wc/store/cart' ).getCartData();
			if ( ! data || typeof data.itemsCount !== 'number' || data.itemsCount === last ) {
				return;
			}
			last = data.itemsCount;
			// Re-query every time: the legacy fragments script replaces the
			// span node wholesale, so a cached reference can go stale.
			var badge = document.querySelector( '.molosoc-cart-link__count' );
			if ( badge ) {
				badge.textContent = last > 0 ? String( last ) : '';
			}
		} );
	}

	// The wc/store/cart store is registered by WooCommerce's footer block
	// scripts; window load runs after all of them, so no polling needed.
	if ( document.readyState === 'complete' ) {
		init();
	} else {
		window.addEventListener( 'load', init );
	}
} )();
