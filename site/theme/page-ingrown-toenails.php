<?php
/**
 * Template Name: Pillar 2 — Ingrown Toenails
 *
 * Auto-selected by WordPress for any Page with the slug "ingrown-toenails"
 * (the "page-{slug}.php" convention takes priority over a manually-picked
 * template), matching the same convention as page-cracked-heels.php.
 *
 * Ported from site/theme/preview/ingrown-toenails-preview.html — see that
 * file's own header comment for the content/image sourcing. Locked copy
 * source: content/molosoc-site/05-pillar2-ingrown-toenails/pillar2-
 * ingrown-toenails-copy.md.
 *
 * Like page-cracked-heels.php, this is a normal template: get_header()/
 * get_footer() (real site chrome, real nav menu). Schema markup + meta
 * description are hooked onto wp_head() in functions.php
 * (molosoc_pillar2_schema()) instead of being printed here, since
 * get_header() already owns the <head>.
 *
 * CSS/JS for this page (pillar1.css, sequential-text-reveal.js,
 * severity-reveal.js, mechanism-drawer.js, GSAP+ScrollTrigger,
 * scroll-refresh.js, model-viewer) are enqueued conditionally in
 * functions.php on is_page('ingrown-toenails') — reuses pillar1.css and
 * its JS as-is, same as page-cracked-heels.php, since every class in that
 * file is generic (see that file's own comments).
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. H1 + locked lede over
	     pillar2_01_soaking.jpg (assets/molosoc-image-assets.csv:
	     "Pillar 2 Ingrown Toenails / Hero"). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar2_01_soaking.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Ingrown toenails', 'molosoc' ); ?></p>
			<h1><?php esc_html_e( "Ingrown toenails: what's happening, and what actually helps", 'molosoc' ); ?></h1>
			<p><?php esc_html_e( "An ingrown toenail happens when the nail edge grows into the surrounding skin instead of over it — and it's rarely a one-time event without a reason behind it.", 'molosoc' ); ?></p>
		</div>
	</section>

	<!-- 2. WHAT CAUSES INGROWN TOENAILS — fixed-image-text-reveal.
	     pillar2_02_trimming.jpg stays fixed/static; the 3 H3 causes slide
	     in from the right, one per scroll step. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'The causes', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'What causes ingrown toenails', 'molosoc' ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php esc_attr_e( 'What causes ingrown toenails', 'molosoc' ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar2_02_trimming.jpg"
							alt="<?php esc_attr_e( 'Hands trimming toenails carefully at a bathroom sink', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'How the nail edge starts growing into skin', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "An ingrown toenail starts when the nail's edge curves or grows down into the skin beside it instead of straight across.", 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Tight shoes and cutting nails too short', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Tight-fitting shoes press the skin against the nail edge, and nails trimmed too short or rounded give that edge room to dig in as it grows back.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Why some people get them again and again', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'The same nail shape and the same shoe habits keep recreating the same pressure point — so without a change to either, it tends to repeat.', 'molosoc' ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. DO INGROWN TOENAILS GO AWAY — editorial-feature-reveal.
	     pillar2_03_elevated.jpg (Image A) gives way to
	     molosoc_ingrown_toenail.jpg (Image B) through a circular mask, then
	     the 3 severity cards emerge from center to their tiered positions. -->
	<section class="molosoc-severity-section" aria-label="<?php esc_attr_e( 'Do ingrown toenails go away', 'molosoc' ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_ingrown_toenail.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar2_03_elevated.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php esc_html_e( 'When it gets serious', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'Do ingrown toenails go away', 'molosoc' ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php esc_html_e( 'When it resolves without intervention', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'A mild ingrown toenail can resolve on its own once the pressure causing it — tight shoes, a too-short trim — is removed and the skin has room to heal.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php esc_html_e( "When it doesn't — signs it's getting worse", 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "Increasing redness, swelling, or pain that doesn't ease up after a few days means it isn't resolving on its own.", 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php esc_html_e( 'Why waiting too long makes it harder to treat', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'The longer skin stays irritated and under pressure, the more inflamed and sensitive it gets — which makes it harder for anything applied to it to actually help.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. WHY CUTTING IT YOURSELF OFTEN BACKFIRES — orbit-scroll-drawer.
	     The always-rotating molosoc-3d.glb model fades/blurs as a glass
	     drawer carrying the 3 H3 points slides up over it. -->
	<section class="molosoc-mechanism-section" aria-label="<?php esc_attr_e( 'Why cutting it yourself often backfires', 'molosoc' ); ?>">
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
				<p class="molosoc-eyebrow"><?php esc_html_e( 'Why cutting it yourself often backfires', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'Why cutting it yourself often backfires', 'molosoc' ); ?></h2>
				<p><?php esc_html_e( 'Pain concentrated at the big toenail is almost always pressure-related — from the nail edge, from footwear, or both at once.', 'molosoc' ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php esc_html_e( 'Big toenail hurts', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Pain concentrated at the big toenail is almost always pressure-related — from the nail edge, from footwear, or both at once.', 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'Ingrown big toe', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'The big toe is the most common site for an ingrown nail simply because it takes the most pressure with every step.', 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'What softening the surrounding skin actually changes', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Softer, healthier skin around the nail gives the nail edge room to grow past it instead of into it — which is the actual mechanism behind fewer repeat episodes.', 'molosoc' ); ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- 5. GO DEEPER — static, reuses components.css's .molosoc-topic-grid/
	     .molosoc-topic-card. Spoke articles nested under this pillar; the
	     3rd link intentionally repeats the 1st's target (/treatment/) with
	     a different keyword-targeted headline — locked as written in
	     pillar2-ingrown-toenails-copy.md. Thumbnails: a 5-photo spa-
	     treatment shoot (assets/molosoc-image-assets.csv) sourced
	     specifically to give these cards distinct images instead of
	     repeating the page hero. -->
	<section class="molosoc-section molosoc-section--bg-cream molosoc-pillar-go-deeper" aria-label="<?php esc_attr_e( 'Go deeper', 'molosoc' ); ?>">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></h2>
			<div class="molosoc-topic-grid">
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/ingrown-toenails/treatment/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_02.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'How to treat ingrown toenails', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "What actually helps at home, and when it's time to stop treating it yourself.", 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/ingrown-toenails/prevent/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_03.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'How to prevent ingrown toenails', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Why prevention fails the same way treatment does, and what actually breaks the repeat cycle.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/ingrown-toenails/treatment/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_01.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Ingrown toenails treatment', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'The full at-home approach, step by step.', 'molosoc' ); ?></p>
				</a>
			</div>
		</div>
	</section>

	<!-- FINAL CTA — deep-links to the Product page's "Real results, no
	     filters" H2 (Persona 2 — Ingrown-Nail/Hardened-Skin, this pillar's
	     own persona). -->
	<section class="molosoc-section molosoc-pillar-final-cta">
		<div class="molosoc-pillar-final-cta__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-pillar-final-cta__scrim" aria-hidden="true"></div>
		<div class="molosoc-section__inner molosoc-reveal">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'See the real results', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Before/after results, no filters', 'molosoc' ); ?></h2>
			<p><?php esc_html_e( 'Real ingrown toenails, treated through consistent care — not a one-time fix.', 'molosoc' ); ?></p>
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
