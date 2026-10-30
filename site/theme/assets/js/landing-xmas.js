/*
  Christmas 2026 gift landing (Issue #251): bundle picker -> checkout.
  Shows one size choice per selected pair (1-3), shares the choice between the
  two pickers on the page, and sends the visitor to the checkout URL carrying
  molosoc_xmas=1&molosoc_xmas_sizes=M,L,... The server (inc/landing-xmas.php)
  validates the sizes, adds one cart line per pair and sets the Christmas
  prices; nothing price-related is read from this URL. Without JS the button
  stays the plain product-page link. Vanilla JS: no jQuery on this page.

  Issue #287 (Clarity 2026-10-27: "2 pairs, size for pair 1 only, 4 dead
  clicks on the button"): newly revealed pair rows inherit pair 1's size
  (never when pair 1 has none), and a blocked click now marks every pair row
  without a size (.is-missing), smooth-scrolls the first one to the middle of
  the screen (clear of the cookie card), names the pair in the red error and
  re-announces it through the aria-live region. The marks clear on the next
  size pick. The URL contract and the no-JS fallback are unchanged.

  Issue #299 (order #1073 paid the regular 229 Kč after tapping the site-wide
  "Koupit nyní" pill, which links to the product page): on these pages
  functions.php/inc prints the pill as an in-page link to #lpx-bundle with
  the label "Vybrat dárkový set" / "Choose gift set". Below, its click
  smooth-scrolls to the picker (plain jump under prefers-reduced-motion) and
  the URL stays as it is, and an IntersectionObserver hides the pill while
  either buy box is on screen so it never covers the button or the facts.
  sticky-cta.js itself is untouched; without it there is no pill to wire.
*/
(function () {
	"use strict";

	var groups = Array.prototype.slice.call( document.querySelectorAll( "[data-lpx-buy]" ) );
	var busy   = false;

	function pairCount( group ) {
		var picked = group.querySelector( 'input[name^="lpx-pairs-"]:checked' );
		return picked ? parseInt( picked.value, 10 ) : 1;
	}

	function pairRow( group, n ) {
		return group.querySelector( '[data-lpx-pair="' + n + '"]' );
	}

	function sizeOf( group, n ) {
		var picked = group.querySelector( '[data-lpx-pair="' + n + '"] input:checked' );
		return picked ? picked.value : "";
	}

	/* Pre-select size `size` for pair `n` when that row has no size yet and the
	   variation is purchasable. Returns true when something was selected. */
	function inherit( group, n, size ) {
		if ( ! size || sizeOf( group, n ) ) {
			return false;
		}
		var radio = group.querySelector( '[data-lpx-pair="' + n + '"] input[value="' + size + '"]' );
		if ( ! radio || radio.disabled ) {
			return false;
		}
		radio.checked = true;
		return true;
	}

	function render( group ) {
		var count = pairCount( group );
		Array.prototype.forEach.call( group.querySelectorAll( "[data-lpx-pair]" ), function ( fs ) {
			fs.hidden = parseInt( fs.getAttribute( "data-lpx-pair" ), 10 ) > count;
		} );
		group.setAttribute( "data-lpx-count", String( count ) );
	}

	function clearMissing( group ) {
		Array.prototype.forEach.call( group.querySelectorAll( "[data-lpx-pair].is-missing" ), function ( fs ) {
			fs.classList.remove( "is-missing" );
		} );
		var err = group.querySelector( ".lpb-buy__error" );
		if ( err ) {
			err.hidden = true;
		}
	}

	/* Blocked click: mark every visible pair row without a size, scroll the
	   first one into the middle of the viewport, name it in the error and make
	   the live region re-announce (same text set again does not announce). */
	function showMissing( group, firstMissing ) {
		var count = pairCount( group );
		for ( var n = 1; n <= count; n++ ) {
			var fs = pairRow( group, n );
			if ( fs && ! sizeOf( group, n ) ) {
				fs.classList.add( "is-missing" );
			}
		}
		var err = group.querySelector( ".lpb-buy__error" );
		if ( err ) {
			var tpl  = group.getAttribute( "data-lpx-err-pair" ) || "";
			var text = tpl.indexOf( "%d" ) !== -1 ? tpl.replace( "%d", String( firstMissing ) ) : ( err.getAttribute( "data-lpx-err" ) || err.textContent );
			err.hidden = false;
			err.textContent = "";
			err.textContent = text;
		}
		var row = pairRow( group, firstMissing );
		if ( row ) {
			var reduce = window.matchMedia && window.matchMedia( "(prefers-reduced-motion: reduce)" ).matches;
			if ( row.scrollIntoView ) {
				row.scrollIntoView( { behavior: reduce ? "auto" : "smooth", block: "center" } );
			}
			var first = row.querySelector( "input:not([disabled])" );
			if ( first ) {
				try {
					first.focus( { preventScroll: true } );
				} catch ( e ) {
					first.focus();
				}
			}
		}
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
			clearMissing( g );
		} );
	}

	groups.forEach( function ( group ) {
		render( group );
		group.addEventListener( "change", function ( e ) {
			var input = e.target;
			var name  = input && input.name ? input.name : "";
			if ( name.indexOf( "lpx-pairs-" ) === 0 ) {
				// More pairs: the new rows start with pair 1's size (if any).
				var before = parseInt( group.getAttribute( "data-lpx-count" ), 10 ) || 1;
				var after  = pairCount( group );
				var first  = sizeOf( group, 1 );
				for ( var n = before + 1; n <= after; n++ ) {
					inherit( group, n, first );
				}
			} else if ( name.indexOf( "lpx-size-" ) === 0 ) {
				// Pair 1 picked after the count (the Clarity order): rows already
				// on screen that still have no size take the same size.
				var row = input.closest ? input.closest( "[data-lpx-pair]" ) : null;
				if ( row && row.getAttribute( "data-lpx-pair" ) === "1" ) {
					for ( var m = 2; m <= pairCount( group ); m++ ) {
						inherit( group, m, input.value );
					}
				}
			}
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
					showMissing( group, n );
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

	/* Issue #299: the sticky pill on these pages is an in-page link to the picker. */
	function wirePill() {
		var pill   = document.getElementById( "molosoc-sticky-cta" );
		var target = document.getElementById( "lpx-bundle" );
		if ( ! pill || ! target || pill.getAttribute( "data-lpx-pill" ) ) {
			return !! pill;
		}
		if ( ( pill.getAttribute( "href" ) || "" ).indexOf( "#lpx-bundle" ) === -1 ) {
			return true; // not the Christmas pill (should not happen here): leave it alone.
		}
		pill.setAttribute( "data-lpx-pill", "1" );
		pill.addEventListener( "click", function ( e ) {
			e.preventDefault(); // stay on this URL, no hash change
			var reduce = window.matchMedia && window.matchMedia( "(prefers-reduced-motion: reduce)" ).matches;
			if ( target.scrollIntoView ) {
				target.scrollIntoView( { behavior: reduce ? "auto" : "smooth", block: "start" } );
			} else {
				window.scrollTo( 0, target.getBoundingClientRect().top + window.pageYOffset );
			}
		} );
		if ( "IntersectionObserver" in window && groups.length ) {
			var onScreen = [];
			var io = new IntersectionObserver( function ( entries ) {
				entries.forEach( function ( entry ) {
					onScreen[ groups.indexOf( entry.target ) ] = entry.isIntersecting;
				} );
				var any = onScreen.some( function ( v ) {
					return v;
				} );
				pill.classList.toggle( "lpx-pill-hidden", any );
				pill.setAttribute( "aria-hidden", any ? "true" : "false" );
			}, { threshold: 0 } );
			groups.forEach( function ( g ) {
				io.observe( g );
			} );
		}
		return true;
	}
	if ( ! wirePill() ) {
		// sticky-cta.js prints after this file when every footer script is deferred: wire once the page has loaded.
		window.addEventListener( "load", wirePill );
	}

	// Back-navigation restores the page from the bfcache with the button locked.
	window.addEventListener( "pageshow", function ( e ) {
		if ( e.persisted ) {
			busy = false;
		}
	} );
})();
