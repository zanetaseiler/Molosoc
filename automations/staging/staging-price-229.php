<?php
/**
 * Plugin Name: Molosoc staging price sync (temporary, one-shot)
 * Description: Sets Woo product 364 (variations 424/425) to 229 CZK on STAGING, matching production. Uploaded to staging's mu-plugins over FTPS, triggered once, then deleted from the server by .github/workflows/staging-set-product-price.yml. Lives under automations/staging/ (NOT site/mu-plugins/, which auto-deploys to PRODUCTION on push).
 */

add_action( 'init', function () {
	if ( ! isset( $_GET['molosoc_price_sync'] ) || 'molosoc-staging-229' !== $_GET['molosoc_price_sync'] ) {
		return;
	}
	// Hard host gate: this must never run anywhere but staging, even if the
	// file is ever copied to the wrong server.
	if ( 0 !== strpos( $_SERVER['HTTP_HOST'] ?? '', 'staging.' ) ) {
		return;
	}
	if ( ! function_exists( 'wc_get_product' ) ) {
		wp_send_json( array( 'ok' => false, 'error' => 'WooCommerce not loaded' ), 500 );
	}

	$out = array();
	foreach ( array( 424, 425 ) as $vid ) {
		$v = wc_get_product( $vid );
		if ( $v ) {
			$v->set_regular_price( '229' );
			$v->set_price( '229' );
			$v->save();
			$out[ $vid ] = $v->get_price();
		}
	}
	$parent = wc_get_product( 364 );
	if ( $parent && class_exists( 'WC_Product_Variable' ) ) {
		WC_Product_Variable::sync( $parent );
		wc_delete_product_transients( 364 );
		$out[364] = wc_get_product( 364 )->get_price();
	}
	wp_send_json( array( 'ok' => true, 'prices' => $out ) );
} );
