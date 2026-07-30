/**
 * Orbit scroll drawer — drives the product page's hero fade/blur + drawer
 * slide from a single scroll-progress number, per
 * .claude/skills/orbit-scroll-drawer/SKILL.md §5. The molosoc-3d.glb
 * <model-viewer> itself keeps rotating on its own (auto-rotate attribute,
 * independent of this script) — this file never touches the model's
 * rotation, only the stage's opacity/blur and the drawer's position.
 *
 * The drawer travels the full 100vh→0 range (per explicit correction): it
 * physically slides in from below the pinned viewport as a distinct block,
 * rather than resting in place the whole time and just fading/nudging
 * into visibility like an overlay.
 *
 * HOLD_FRACTION adds a "just look at the object" beat at the very start of
 * the pin, per explicit correction: the drawer was entering immediately on
 * the first scroll tick, before there was any real chance to actually see
 * the floating model. For the first HOLD_FRACTION of scroll progress
 * through the section, nothing moves — full-opacity model, drawer still
 * completely off-screen. Only after that does the fade/blur/slide sequence
 * play out, remapped to fill the remaining scroll distance. Raised further
 * (and the section's total scroll height raised alongside it, see
 * product.css) per a second round of explicit correction — the first pass
 * still didn't feel like "much more space" once the drawer actually
 * started moving.
 */
(function () {
	var prefersReduced = window.matchMedia( '(prefers-reduced-motion: reduce)' ).matches;
	if ( prefersReduced ) return; // CSS already renders the settled end-state

	if ( window.innerWidth <= 760 ) return; // mobile: plain static stack, no scroll-driven effect

	var section = document.getElementById( 'orbit-section' );
	var stage = document.getElementById( 'orbitStage' );
	var drawer = document.getElementById( 'orbitDrawer' );
	var heroCopy = document.getElementById( 'orbitHeroCopy' );
	if ( ! section || ! stage || ! drawer || ! heroCopy ) return;

	var HOLD_FRACTION = 0.55;

	function clamp01( n ) {
		return Math.max( 0, Math.min( 1, n ) );
	}

	function getProgress() {
		var rect = section.getBoundingClientRect();
		var total = section.offsetHeight - window.innerHeight;
		if ( total <= 0 ) return 1;
		return clamp01( -rect.top / total );
	}

	var ticking = false;
	function update() {
		ticking = false;
		var raw = getProgress();
		// p stays 0 through the hold beat, then ramps 0→1 across the rest.
		var p = clamp01( ( raw - HOLD_FRACTION ) / ( 1 - HOLD_FRACTION ) );

		// Orbit fades toward ~60% opacity and barely blurs, but is never
		// fully invisible or paused — it keeps spinning behind the glass
		// drawer the whole time (skill §3). Floor raised and max blur
		// lowered further per explicit correction ("I want to see the
		// animation through it") — the rotation itself needs to stay
		// perceptible, not just a recognizable-but-frozen-looking shape.
		stage.style.setProperty( '--orbit-opacity', ( 1 - p * 0.4 ).toFixed( 3 ) );
		stage.style.setProperty( '--orbit-blur', ( p * 3 ).toFixed( 2 ) + 'px' );

		// Hero copy recedes as the drawer takes over.
		heroCopy.style.setProperty( '--hero-copy-opacity', ( 1 - p * 1.4 ).toFixed( 3 ) );

		// Drawer physically travels up from fully below the pinned viewport
		// (100vh) to its resting place (0) — a genuine slide-in, not an
		// overlay that's already in position and just fades/nudges into
		// view. At p=0 (top of the section) it sits completely off-screen.
		drawer.style.setProperty( '--drawer-offset', ( ( 1 - p ) * 100 ).toFixed( 2 ) + 'vh' );
	}

	function onScroll() {
		if ( ! ticking ) {
			requestAnimationFrame( update );
			ticking = true;
		}
	}

	window.addEventListener( 'scroll', onScroll, { passive: true } );
	update();
})();
