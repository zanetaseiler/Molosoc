/*
  Landing Page B (page-hydratacni-navleky-landing-b.php) — enqueued by
  functions.php only on that page. Two small progressive enhancements:

  1. Story tabs ("Jak MOLOSOC vznikl"): page 580 used Thrive's tabs module.
     Without JS all three panels stay visible stacked (landing-b.css); with
     JS the .is-enhanced class turns them into real tabs with arrow-key
     navigation.
  2. Sticky CTA bar: hidden while the hero's own "Objednat" button is on
     screen, shown once the visitor scrolls past it — the behaviour of page
     580's pinned header button. Without IntersectionObserver the bar is
     simply always visible.
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

	// 2. Sticky CTA bar
	var bar  = document.getElementById( "lpb-sticky" );
	var hero = document.getElementById( "lpb-hero-cta" );
	if ( bar && hero && "IntersectionObserver" in window ) {
		bar.classList.add( "is-hidden" );
		new IntersectionObserver( function ( entries ) {
			entries.forEach( function ( entry ) {
				// Hidden while the hero CTA is visible or still below the fold.
				var pastHero = ! entry.isIntersecting && entry.boundingClientRect.top < 0;
				bar.classList.toggle( "is-hidden", ! pastHero );
			} );
		}, { threshold: 0 } ).observe( hero );
	}
})();
