/*
  Landing Page B (page-hydratacni-navleky-molosoc.php) — enqueued by
  functions.php only on that page. One small progressive enhancement:

  1. Story tabs ("Jak MOLOSOC vznikl"): page 580 used Thrive's tabs module.
     Without JS all three panels stay visible stacked (landing-b.css); with
     JS the .is-enhanced class turns them into real tabs with arrow-key
     navigation.

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

	// The page's own sticky bar (#lpb-sticky, hidden/shown around the hero
	// CTA) was removed in Issue #163: the site-wide sticky "Koupit nyní" pill
	// (assets/js/sticky-cta.js) covers this page now.
})();
