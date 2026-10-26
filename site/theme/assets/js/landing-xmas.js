/*
  Christmas 2026 gift landing (Issue #251): bundle picker -> checkout.
  Shows one size choice per selected pair (1-3), shares the choice between the
  two pickers on the page, and sends the visitor to the checkout URL carrying
  molosoc_xmas=1&molosoc_xmas_sizes=M,L,... The server (inc/landing-xmas.php)
  validates the sizes, adds one cart line per pair and sets the Christmas
  prices; nothing price-related is read from this URL. Without JS the button
  stays the plain product-page link. Vanilla JS: no jQuery on this page.
*/
(function () {
	"use strict";

	var groups = Array.prototype.slice.call( document.querySelectorAll( "[data-lpx-buy]" ) );
	var busy   = false;

	function pairCount( group ) {
		var picked = group.querySelector( 'input[name^="lpx-pairs-"]:checked' );
		return picked ? parseInt( picked.value, 10 ) : 1;
	}

	function sizeOf( group, n ) {
		var picked = group.querySelector( '[data-lpx-pair="' + n + '"] input:checked' );
		return picked ? picked.value : "";
	}

	function render( group ) {
		var count = pairCount( group );
		Array.prototype.forEach.call( group.querySelectorAll( "[data-lpx-pair]" ), function ( fs ) {
			fs.hidden = parseInt( fs.getAttribute( "data-lpx-pair" ), 10 ) > count;
		} );
	}

	function sync( source ) {
		var count = pairCount( source );
		groups.forEach( function ( g ) {
			if ( g === source ) {
				return;
			}
			var radio = g.querySelector( 'input[name^="lpx-pairs-"][value="' + count + '"]' );
			if ( radio ) {
				radio.checked = true;
			}
			for ( var n = 1; n <= 3; n++ ) {
				var size  = sizeOf( source, n );
				var match = size ? g.querySelector( '[data-lpx-pair="' + n + '"] input[value="' + size + '"]' ) : null;
				if ( match ) {
					match.checked = true;
				}
			}
		} );
		groups.forEach( function ( g ) {
			render( g );
			var err = g.querySelector( ".lpb-buy__error" );
			if ( err ) {
				err.hidden = true;
			}
		} );
	}

	groups.forEach( function ( group ) {
		render( group );
		group.addEventListener( "change", function () {
			sync( group );
		} );

		var button = group.querySelector( "[data-lpx-go]" );
		if ( ! button ) {
			return;
		}
		button.addEventListener( "click", function ( e ) {
			if ( group.getAttribute( "data-lpx-enabled" ) !== "1" ) {
				return; // variations unresolved server-side: keep the product-page link.
			}
			e.preventDefault();
			var sizes = [];
			for ( var n = 1; n <= pairCount( group ); n++ ) {
				var size = sizeOf( group, n );
				if ( ! size ) {
					var err = group.querySelector( ".lpb-buy__error" );
					if ( err ) {
						err.hidden = false;
					}
					var first = group.querySelector( '[data-lpx-pair="' + n + '"] input' );
					if ( first ) {
						first.focus();
					}
					return;
				}
				sizes.push( size );
			}
			if ( busy ) {
				return; // already on its way: never add twice.
			}
			busy = true;
			var base = group.getAttribute( "data-lpx-checkout-url" ) || "";
			window.location.href = base + ( base.indexOf( "?" ) === -1 ? "?" : "&" ) + "molosoc_xmas=1&molosoc_xmas_sizes=" + encodeURIComponent( sizes.join( "," ) );
		} );
	} );

	// Back-navigation restores the page from the bfcache with the button locked.
	window.addEventListener( "pageshow", function ( e ) {
		if ( e.persisted ) {
			busy = false;
		}
	} );
})();
