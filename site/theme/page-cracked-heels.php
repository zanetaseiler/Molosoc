<?php
/**
 * Template Name: Pillar 1 — Cracked Heels
 *
 * Auto-selected by WordPress for any Page with the slug "cracked-heels"
 * (the "page-{slug}.php" convention takes priority over a manually-picked
 * template), matching the same convention as page-foot-covers.php.
 *
 * Ported from site/theme/preview/cracked-heels-preview.html — see that
 * file's own header comment for the content/image sourcing, and
 * docs/site-structure.md §7 "Pillar 1 — Cracked Heels" for how this
 * page's headings map to verified keyword data. Locked copy source:
 * content/molosoc-site/04-pillar1-cracked-heels/pillar1-cracked-heels-copy.md.
 *
 * Like page-foot-covers.php, this is a normal template: get_header()/
 * get_footer() (real site chrome, real nav menu). Schema markup + meta
 * description are hooked onto wp_head() in functions.php
 * (molosoc_pillar1_schema()) instead of being printed here, since
 * get_header() already owns the <head>.
 *
 * CSS/JS for this page (pillar1.css, sequential-text-reveal.js,
 * severity-reveal.js, mechanism-drawer.js, GSAP+ScrollTrigger,
 * scroll-refresh.js, model-viewer) are enqueued conditionally in
 * functions.php on is_page('cracked-heels').
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. H1 + locked lede over
	     pillar1_01_heels_floor.jpg (assets/molosoc-image-assets.csv:
	     "Pillar 1 Cracked Heels / Hero"). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar1_01_heels_floor.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Cracked heels', 'molosoc' ); ?></p>
			<h1><?php esc_html_e( "Cracked heels: what's really going on, and what helps", 'molosoc' ); ?></h1>
			<p><?php esc_html_e( 'Cracked heels happen when skin loses the elasticity to stretch under pressure — not from bad luck, and not from "just dry skin." The fix is straightforward once it\'s consistent, not occasional.', 'molosoc' ); ?></p>
		</div>
	</section>

	<!-- 2. WHAT CAUSES CRACKED HEELS — fixed-image-text-reveal.
	     pillar1_02_bed_checking.jpg stays fixed/static; the 3 H3 causes
	     slide in from the right, one per scroll step. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'The causes', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'What causes cracked heels', 'molosoc' ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php esc_attr_e( 'What causes cracked heels', 'molosoc' ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar1_02_bed_checking.jpg"
							alt="<?php esc_attr_e( 'Person checking their heel, seated on the edge of a bed', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( "Dry skin losing its ability to stretch", 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Heel skin cracks when it dries out and loses the elasticity it needs to stretch under pressure.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Pressure and weight-bearing on the heel edge', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "The heel's outer edge carries the most weight with every step — dry, inflexible skin can't take that pressure without splitting.", 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Standing all day, especially in open-back shoes', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Standing for long stretches in open-back shoes speeds up both problems at once: more pressure, more moisture loss.', 'molosoc' ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. WHEN CRACKED HEELS GO FROM DRY TO PAINFUL — editorial-feature-
	     reveal. pillar1_03_sandals.jpg (Image A) gives way to
	     pillar3_03_texture.jpg (Image B) through a circular mask, then the
	     3 severity cards emerge from center to their tiered positions. -->
	<section class="molosoc-severity-section" aria-label="<?php esc_attr_e( 'When cracked heels go from dry to painful', 'molosoc' ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar3_03_texture.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar1_03_sandals.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php esc_html_e( 'When it gets serious', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'When cracked heels go from dry to painful', 'molosoc' ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php esc_html_e( 'Painful deep cracked heels', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "A crack that hurts with every step has gone past surface dryness into a deeper layer of skin.", 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php esc_html_e( 'Severe cracked heels', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "Severe cracked heels widen, deepen, and can bleed — an occasional cream application isn't enough at this stage.", 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php esc_html_e( 'Why "just moisturizing more" stops working at this stage', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "Cream that isn't sealed against skin rubs off before it's absorbed — more product doesn't fix that, more contact time does.", 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. WHY MOISTURIZER ALONE DOESN'T FIX IT — orbit-scroll-drawer. The
	     always-rotating molosoc-3d.glb model fades/blurs as a glass drawer
	     carrying the 3 H3 points slides up over it. Same sanctioned
	     exception to "never spin products" as the Product page's own hero
	     model (docs/molosoc-animation-specification.md) — model-viewer's
	     own auto-rotate, independent of scroll/JS. -->
	<section class="molosoc-mechanism-section" aria-label="<?php esc_attr_e( "Why moisturizer alone doesn't fix it", 'molosoc' ); ?>">
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
				<p class="molosoc-eyebrow"><?php esc_html_e( 'The real fix', 'molosoc' ); ?></p>
			</div>

			<div class="molosoc-mechanism-drawer">
				<p class="molosoc-eyebrow"><?php esc_html_e( "Why moisturizer alone doesn't fix it", 'molosoc' ); ?></p>
				<h2><?php esc_html_e( "Why moisturizer alone doesn't fix it", 'molosoc' ); ?></h2>
				<p><?php esc_html_e( 'Most people already own a foot cream and already apply it — the routine itself was never the problem.', 'molosoc' ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php esc_html_e( 'The routine most people already try', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Most people already own a foot cream and already apply it — the routine itself was never the problem.', 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'Where that routine breaks down', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Cream rubs off onto socks or sheets within minutes, so most of it never gets absorbed.', 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'What actually needs to happen for cream to work', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Cream needs uninterrupted contact with skin to work — not a bigger dose, just enough sealed time to actually absorb.', 'molosoc' ); ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- 5. GO DEEPER — static, reuses components.css's .molosoc-topic-grid/
	     .molosoc-topic-card ("educational content beat"). Spoke articles
	     nested under this pillar (docs/site-structure.md §7/§8) — links
	     resolve once each spoke page is built. -->
	<section class="molosoc-section molosoc-section--bg-cream molosoc-pillar-go-deeper" aria-label="<?php esc_attr_e( 'Go deeper', 'molosoc' ); ?>">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></h2>
			<div class="molosoc-topic-grid">
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/cracked-heels/cracked-heels-cream/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_cracked_heels_05.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Cracked heels cream', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'What actually matters in a cracked-heel cream, and why even a good one fails without the right routine.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/cracked-heels/fix-permanently/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_cracked_heels_03.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'How to fix cracked heels permanently', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Why cracked heels come back after healing once, and what stops the cycle.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/cracked-heels/cracked-heels-treatment/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc-6a6c3e786c068.png"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Cracked heels treatment', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'The full picture beyond cream alone — what real treatment requires, step by step.', 'molosoc' ); ?></p>
				</a>
			</div>
		</div>
	</section>

	<!-- FINAL CTA — deep-links to the Product page's "Real results, no
	     filters" H2 (Persona 2), per docs/site-structure.md §7's own
	     "Deep-links to" note for Pillar 1. -->
	<section class="molosoc-section molosoc-pillar-final-cta">
		<div class="molosoc-pillar-final-cta__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-pillar-final-cta__scrim" aria-hidden="true"></div>
		<div class="molosoc-section__inner molosoc-reveal">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'See the real results', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Before/after results, no filters', 'molosoc' ); ?></h2>
			<p><?php esc_html_e( 'Real cracked heels, healed through consistent care — not a one-time application.', 'molosoc' ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php esc_html_e( 'See real results, no filters', 'molosoc' ); ?></a>
		</div>
	</section>

</main>

<script>
	// motion.js gates .molosoc-hero, not .molosoc-pillar-hero — this page's
	// own hero class — so its breathing-zoom start is triggered here
	// instead, same one-line rAF gate as the static preview.
	requestAnimationFrame( function () {
		var hero = document.getElementById( 'pillarHero' );
		if ( hero ) hero.classList.add( 'is-visible' );
	} );
</script>

<?php get_footer(); ?>
