<?php
/**
 * Template Name: Spoke 4 — Cracked Heels Cream
 *
 * Auto-selected by WordPress for any Page with the slug
 * "cracked-heels-cream", nested under "cracked-heels" so the permalink
 * resolves to /cracked-heels/cracked-heels-cream/ — site-structure.md
 * §8, Spoke 4.
 *
 * Ported from the approved Spoke 1 template pattern. Locked copy source:
 * content/molosoc-site/12-spoke4-cracked-heels-cream/spoke4-cracked-
 * heels-cream-copy.md.
 *
 * Deliberate exception vs. every other spoke here: this one deep-links to
 * the Product page's "The cream you already own, finally working" H2
 * (Persona 1), not the "Real results, no filters" H2 (Persona 2) — this
 * spoke is about cream effectiveness, matching the Cream Graveyard
 * Owner's mindset, per site-structure.md §8 Spoke 4's own note.
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. Same photo Pillar 1's own "Go
	     deeper" card already uses for this spoke (molosoc_cracked_heels_05.jpg). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc_cracked_heels_05.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Cracked heels cream', 'molosoc' ); ?></p>
			<h1><?php esc_html_e( 'Cracked heels cream: what actually makes one work', 'molosoc' ); ?></h1>
			<p><?php esc_html_e( "A cracked-heel cream doesn't fail because of the formula nearly as often as it fails because of the routine around it — ingredients matter less than whether the cream gets a real chance to absorb.", 'molosoc' ); ?></p>
		</div>
	</section>

	<!-- 2. WHAT TO ACTUALLY LOOK FOR IN A CRACKED HEELS CREAM —
	     fixed-image-text-reveal. molosoc_ritual_ankle_cream_closeup-scaled.jpg
	     (cream massage close-up) stays fixed; 3 H3s slide in. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'What actually matters', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'What to actually look for in a cracked heels cream', 'molosoc' ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php esc_attr_e( 'What to actually look for in a cracked heels cream', 'molosoc' ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc_ritual_ankle_cream_closeup-scaled.jpg"
							alt="<?php esc_attr_e( 'Close-up of hands massaging cream into an ankle and heel', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Urea and other humectants — what they actually do', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Urea and similar humectants draw moisture into skin and help soften thickened areas, which is why they show up often in creams aimed at cracked heels specifically.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Thicker balms vs. lighter lotions — when each makes sense', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Thicker balms sit on skin longer and suit more severe cracking, while lighter lotions absorb faster and work well for everyday maintenance once the worst of it has healed.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( "Why ingredients matter less than how consistently it's used", 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'A well-formulated cream applied inconsistently underperforms a simpler one used every day with enough contact time to actually absorb.', 'molosoc' ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. BEST CREAM FOR CRACKED HEELS — editorial-feature-reveal.
	     homepage_02_cream_massage.jpg (Image A) gives way to
	     molosoc_cream_drawers.jpg (Image B — the cream you already own)
	     through a circular mask, then the 3 cards emerge. -->
	<section class="molosoc-severity-section" aria-label="<?php esc_attr_e( 'Best cream for cracked heels', 'molosoc' ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://molosoc.com/wp-content/uploads/2026/07/molosoc_cream_drawers.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://molosoc.com/wp-content/uploads/2026/07/homepage_02_cream_massage.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php esc_html_e( 'Severity, not brand', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'Best cream for cracked heels', 'molosoc' ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php esc_html_e( 'What "best" really depends on — severity, not brand', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'The "best" cream depends far more on how severe the cracking is than on which brand made it — a mild case and a deep, painful crack call for different levels of intervention, not different logos.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php esc_html_e( "Why the most expensive option isn't always the most effective", 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "Price doesn't reliably predict how well a cream performs on cracked heels — plenty of inexpensive formulas contain the same core humectants as premium ones.", 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php esc_html_e( 'The cream you already own is probably fine', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "If there's already a foot cream in the drawer, it's very likely capable of doing the job — the missing piece is usually consistency and contact time, not a better product.", 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. WHY A GOOD CREAM STILL DOESN'T FIX CRACKED HEELS —
	     orbit-scroll-drawer. -->
	<section class="molosoc-mechanism-section" aria-label="<?php esc_attr_e( "Why a good cream still doesn't fix cracked heels", 'molosoc' ); ?>">
		<div class="molosoc-mechanism-pin">

			<div class="molosoc-mechanism-stage" aria-hidden="true">
				<div class="molosoc-mechanism-glow"></div>
				<model-viewer
					class="molosoc-mechanism-model"
					src="<?php echo esc_url( get_stylesheet_directory_uri() . '/assets/models/molosoc-3d.glb' ); ?>"
					alt=""
					auto-rotate
					rotation-per-second="10deg"
					camera-orbit="0deg 75deg 105%"
					exposure="0.95"
					shadow-intensity="0.7"
					shadow-softness="1"
					environment-image="neutral"
					loading="eager">
				</model-viewer>
			</div>

			<div class="molosoc-mechanism-intro">
				<p class="molosoc-eyebrow"><?php esc_html_e( "It's not the cream", 'molosoc' ); ?></p>
			</div>

			<div class="molosoc-mechanism-drawer">
				<p class="molosoc-eyebrow"><?php esc_html_e( "Why a good cream still doesn't fix cracked heels", 'molosoc' ); ?></p>
				<h2><?php esc_html_e( "Why a good cream still doesn't fix cracked heels", 'molosoc' ); ?></h2>
				<p><?php esc_html_e( "Cream applied and left uncovered rubs off on socks or floors within minutes, long before it's had time to actually absorb into cracked, thickened skin.", 'molosoc' ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php esc_html_e( 'The routine most people already try', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "Most people already own a cream and already apply it somewhat regularly — the routine itself isn't the gap.", 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'Where that routine breaks down', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "Cream applied and left uncovered rubs off on socks or floors within minutes, long before it's had time to actually absorb into cracked, thickened skin.", 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'What actually needs to happen for cream to work', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Cream needs sustained, sealed contact with skin to work — not a stronger formula, just enough uninterrupted time for it to actually absorb.', 'molosoc' ); ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- BACK TO PILLAR -->
	<section class="molosoc-section molosoc-section--bg-cream">
		<div class="molosoc-section__inner" style="text-align:center;">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Part of a bigger picture', 'molosoc' ); ?></p>
			<h2><a href="<?php echo esc_url( home_url( '/cracked-heels/' ) ); ?>">&larr; <?php esc_html_e( 'Back to Cracked Heels', 'molosoc' ); ?></a></h2>
		</div>
	</section>

	<!-- FINAL CTA — deep-links to the Product page's "The cream you
	     already own, finally working" H2 (Persona 1), not the usual
	     "Real results" H2 — deliberate exception per site-structure.md §8. -->
	<section class="molosoc-section molosoc-pillar-final-cta">
		<div class="molosoc-pillar-final-cta__media" aria-hidden="true">
			<img src="https://molosoc.com/wp-content/uploads/2026/07/homepage-cream-collection-cropped.png"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-pillar-final-cta__scrim" aria-hidden="true"></div>
		<div class="molosoc-section__inner molosoc-reveal">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'The cream you already own', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Finally working', 'molosoc' ); ?></h2>
			<p><?php esc_html_e( 'This is exactly what Molosoc is built for — sealing whatever cream you already trust against your skin long enough to actually work.', 'molosoc' ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php esc_html_e( 'See how it works', 'molosoc' ); ?></a>
		</div>
	</section>

</main>

<?php
get_footer();
