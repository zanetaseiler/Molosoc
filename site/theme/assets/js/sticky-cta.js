/*
  Global bilingual sticky "Buy now" CTA (GitHub Issue #73), injected on
  every public page except Cart/Checkout and the product page itself
  (functions.php only enqueues this handle when none of those apply, and
  supplies window.molosocStickyCta = { url, label } before this runs).

  JS-injected like back-to-top.js and no template markup, so it survives
  regardless of which page template renders — progressive enhancement:
  no JS simply means no pill.
*/
(function () {
	"use strict";

	if ( document.getElementById( "molosoc-sticky-cta" ) ) {
		return; // Never double-inject.
	}

	var data = window.molosocStickyCta;
	if ( ! data || ! data.url || ! data.label ) {
		return;
	}

	var link = document.createElement( "a" );
	link.id = "molosoc-sticky-cta";
	link.className = "molosoc-sticky-cta";
	link.href = data.url;
	link.textContent = data.label;
	document.body.appendChild( link );
})();
