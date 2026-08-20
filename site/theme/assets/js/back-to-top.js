/*
  Floating "back to top" button, injected on every page (enqueued
  unconditionally in functions.php next to nav-toggle.js).

  Why a JS-injected floating button and not a footer link: the long
  scroll-animated pages (homepage, pillars, product) are exactly where
  getting back up matters, and a fixed button is reachable mid-page too.
  Progressive enhancement — no JS simply means no button.

  The jump is deliberately INSTANT (behavior: "auto"; base.css also pins
  html { scroll-behavior: auto }): a smooth scroll would replay every
  pinned/scroll-linked animation on the way up, which is the exact
  annoyance this button exists to skip.
*/
(function () {
	"use strict";

	if ( document.getElementById( "molosoc-back-to-top" ) ) {
		return; // Never double-inject (e.g. a script accidentally loaded twice).
	}

	var isCz = ( document.documentElement.lang || "" ).toLowerCase().indexOf( "cs" ) === 0;

	var btn = document.createElement( "button" );
	btn.type = "button";
	btn.id = "molosoc-back-to-top";
	btn.className = "molosoc-back-to-top";
	btn.setAttribute( "aria-label", isCz ? "Zpět nahoru" : "Back to top" );
	btn.innerHTML =
		'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>';
	document.body.appendChild( btn );

	// Appears once the visitor is ~1.5 viewports down — far enough that
	// "top" is genuinely out of reach, early enough to be useful.
	var ticking = false;
	function update() {
		ticking = false;
		btn.classList.toggle( "is-visible", window.scrollY > window.innerHeight * 1.5 );
	}
	window.addEventListener( "scroll", function () {
		if ( ! ticking ) {
			ticking = true;
			window.requestAnimationFrame( update );
		}
	}, { passive: true } );
	update();

	btn.addEventListener( "click", function () {
		window.scrollTo( { top: 0, left: 0, behavior: "auto" } );
		// Hide immediately rather than waiting for the scroll listener's
		// rAF tick — throttled/occluded tabs can delay that frame.
		btn.classList.remove( "is-visible" );
		// Hand keyboard focus back to the top of the page so tabbing
		// continues from the header, not from the (now hidden) button.
		var target = document.querySelector( ".molosoc-skip-link" ) || document.body;
		if ( target.focus ) {
			try {
				target.focus( { preventScroll: true } );
			} catch ( e ) {
				/* older engines: focus without options is fine */
				target.focus();
			}
		}
	} );
})();
