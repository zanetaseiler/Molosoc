/*
  Landing Page B (page-hydratacni-navleky-molosoc.php) — enqueued by
  functions.php only on that page. Small progressive enhancements:

  1. Story tabs ("Jak MOLOSOC vznikl"): page 580 used Thrive's tabs module.
     Without JS all three panels stay visible stacked (landing-b.css); with
     JS the .is-enhanced class turns them into real tabs with arrow-key
     navigation.

  2. Size choice + "Pokračovat k pokladně" (Issue #209): every purchase CTA
     group (hero + after each section, inc/landing-b-buy.php) has an M / L
     radio pair and one button. The choice is shared by all groups, is never
     preselected, and the button refuses to go on until a size is picked.
     (Issue #290: with a red outlined, scrolled-to row and a live error.)
     Then the button opens the WooCommerce add-to-cart URL of that size
     (quantity 1), which adds the variation once and redirects to a clean
     checkout URL. Vanilla JS: jQuery is deliberately absent on this page.
     Without JS the button stays the plain product-page link.

  The page's own sticky CTA bar (shown once the hero button scrolled away,
  as page 580's pinned header button did) was removed in Issue #163 — the
  site-wide sticky "Koupit nyní" pill (assets/js/sticky-cta.js) is used
  here like on every other page.
*/
(function () {
	"use strict";

	// 1. Tabs
	document.querySelectorAll( "[data-lpb-tabs]" ).forEach( function ( root ) {
		var tabs   = Array.prototype.slice.call( root.querySelectorAll( '[role="tab"]' ) );
		var panels = Array.prototype.slice.call( root.querySelectorAll( '[role="tabpanel"]' ) );
		if ( ! tabs.length || tabs.length !== panels.length ) {
			return;
		}
		root.classList.add( "is-enhanced" );

		function activate( index ) {
			tabs.forEach( function ( tab, i ) {
				var on = i === index;
				tab.classList.toggle( "is-active", on );
				tab.setAttribute( "aria-selected", on ? "true" : "false" );
				tab.tabIndex = on ? 0 : -1;
				panels[ i ].hidden = ! on;
				panels[ i ].classList.toggle( "is-active", on );
			} );
		}

		tabs.forEach( function ( tab, i ) {
			tab.addEventListener( "click", function () {
				activate( i );
			} );
			tab.addEventListener( "keydown", function ( e ) {
				var next = null;
				if ( e.key === "ArrowRight" || e.key === "ArrowDown" ) {
					next = ( i + 1 ) % tabs.length;
				} else if ( e.key === "ArrowLeft" || e.key === "ArrowUp" ) {
					next = ( i - 1 + tabs.length ) % tabs.length;
				} else if ( e.key === "Home" ) {
					next = 0;
				} else if ( e.key === "End" ) {
					next = tabs.length - 1;
				}
				if ( next !== null ) {
					e.preventDefault();
					activate( next );
					tabs[ next ].focus();
				}
			} );
		} );
	} );

	// 2. Size choice -> checkout
	var groups = Array.prototype.slice.call( document.querySelectorAll( "[data-lpb-buy]" ) );
	var busy   = false;

	function setBusy( on ) {
		busy = on;
		groups.forEach( function ( g ) {
			var btn = g.querySelector( "[data-lpb-checkout]" );
			if ( btn ) {
				btn.classList.toggle( "is-busy", on );
				btn.setAttribute( "aria-disabled", on ? "true" : "false" );
			}
		} );
	}

	/* Issue #290 (same as the Christmas picker, #287): a blocked click used to
	   only unhide the error and focus an opacity-0 radio, which shows nothing on
	   a phone. Now the size row is outlined (.is-missing), scrolled to the middle
	   of the screen (clear of the cookie card), the live region re-announces the
	   error and focus moves without a second scroll. A size pick clears it. */
	function showError( group, on ) {
		var err = group.querySelector( ".lpb-buy__error" );
		var row = group.querySelector( ".lpb-buy__sizes" );
		if ( row ) {
			row.classList.toggle( "is-missing", on );
		}
		if ( err ) {
			err.hidden = ! on;
			if ( on ) {
				var text = err.textContent;
				err.textContent = "";
				err.textContent = text; // same text set again would not announce
			}
		}
		if ( ! on || ! row ) {
			return;
		}
		var reduce = window.matchMedia && window.matchMedia( "(prefers-reduced-motion: reduce)" ).matches;
		if ( row.scrollIntoView ) {
			row.scrollIntoView( { behavior: reduce ? "auto" : "smooth", block: "center" } );
		}
		var first = row.querySelector( 'input[type="radio"]' );
		if ( first ) {
			try {
				first.focus( { preventScroll: true } );
			} catch ( e ) {
				first.focus();
			}
		}
	}

	groups.forEach( function ( group ) {
		group.addEventListener( "change", function ( e ) {
			if ( ! e.target || e.target.type !== "radio" ) {
				return;
			}
			groups.forEach( function ( g ) {
				Array.prototype.forEach.call( g.querySelectorAll( 'input[type="radio"]' ), function ( r ) {
					r.checked = r.value === e.target.value;
				} );
				showError( g, false );
			} );
		} );

		var button = group.querySelector( "[data-lpb-checkout]" );
		if ( ! button ) {
			return;
		}
		button.addEventListener( "click", function ( e ) {
			var picked = group.querySelector( 'input[type="radio"]:checked' );
			if ( ! picked ) {
				e.preventDefault();
				showError( group, true );
				return;
			}
			var url = picked.getAttribute( "data-lpb-url" );
			if ( ! url ) {
				return; // size without a checkout URL: keep the product-page link.
			}
			e.preventDefault();
			if ( busy ) {
				return; // already on its way: never add twice.
			}
			setBusy( true );
			window.location.href = url;
		} );
	} );

	// Back-navigation restores the page from the bfcache with the button locked.
	window.addEventListener( "pageshow", function ( e ) {
		if ( e.persisted ) {
			setBusy( false );
		}
	} );

	// The page's own sticky bar (#lpb-sticky, hidden/shown around the hero
	// CTA) was removed in Issue #163: the site-wide sticky "Koupit nyní" pill
	// (assets/js/sticky-cta.js) covers this page now.
})();
