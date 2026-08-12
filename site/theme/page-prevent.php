<?php
/**
 * Template Name: Spoke 3 — How to Prevent Ingrown Toenails
 *
 * Auto-selected by WordPress for any Page with the slug "prevent", nested
 * under "ingrown-toenails" so the permalink resolves to
 * /ingrown-toenails/prevent/ — site-structure.md §8, Spoke 3.
 *
 * Ported from the approved Spoke 1 template pattern. Locked copy source:
 * content/molosoc-site/11-spoke3-prevent-ingrown-toenails/spoke3-prevent-
 * ingrown-toenails-copy.md.
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. Same photo Pillar 2's own "Go
	     deeper" card already uses for this spoke (molosoc_spa_treatment_03.jpg). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_03.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Ingrown toenails prevention', 'molosoc' ); ?></p>
			<h1><?php esc_html_e( 'How to prevent ingrown toenails', 'molosoc' ); ?></h1>
			<p><?php esc_html_e( "If this isn't the first time, treating the current episode isn't enough — preventing the next one means changing whatever keeps recreating the same pressure point.", 'molosoc' ); ?></p>
		</div>
	</section>

	<!-- 2. WHY DO I KEEP GETTING INGROWN TOENAILS — fixed-image-text-reveal.
	     molosoc_pedicure_01.jpg (filing) stays fixed; 3 H3s slide in. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'The recurring cycle', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Why do I keep getting ingrown toenails?', 'molosoc' ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php esc_attr_e( 'Why do I keep getting ingrown toenails?', 'molosoc' ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_pedicure_01.jpg"
							alt="<?php esc_attr_e( 'Filing a toenail with a foot resting in a basin', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'The nail-cutting habit that causes repeat problems', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Cutting the nail too short or rounding the corners gives the same edge room to dig into skin again every time it regrows.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Footwear that keeps recreating the same pressure point', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Shoes that press against the same spot on the toe recreate the exact pressure that caused the problem the first time, every time they\'re worn.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( "Why one successful treatment doesn't mean it won't happen again", 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "Resolving one episode deals with the symptom in front of you — it doesn't change the trim habit or footwear that caused it, so the same conditions are still in place for next time.", 'molosoc' ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. HOW TO STOP INGROWN TOENAILS — editorial-feature-reveal.
	     pillar2_02_trimming.jpg (Image A) gives way to pillar2_03_elevated.jpg
	     (Image B) through a circular mask, then the 3 cards emerge. -->
	<section class="molosoc-severity-section" aria-label="<?php esc_attr_e( 'How to stop ingrown toenails', 'molosoc' ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar2_03_elevated.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar2_02_trimming.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php esc_html_e( 'The fix that holds', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'How to stop ingrown toenails', 'molosoc' ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php esc_html_e( 'The trim shape that actually prevents regrowth into skin', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Trimming straight across, leaving the corners slightly longer than the center, gives the nail a straighter path to grow along instead of curving into skin.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php esc_html_e( 'Shoe-fit changes that remove the root pressure', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Shoes with enough room at the toe box remove the constant pressure that pushes the nail edge into skin in the first place.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php esc_html_e( 'Softening the surrounding skin as an ongoing habit, not a one-time fix', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Keeping the skin around the nail consistently soft, rather than only after a problem starts, gives the nail room to grow past it instead of into it.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. BUILDING A PREVENTION ROUTINE THAT ACTUALLY STICKS —
	     orbit-scroll-drawer. -->
	<section class="molosoc-mechanism-section" aria-label="<?php esc_attr_e( 'Building a prevention routine that actually sticks', 'molosoc' ); ?>">
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
				<p class="molosoc-eyebrow"><?php esc_html_e( 'Make it stick', 'molosoc' ); ?></p>
			</div>

			<div class="molosoc-mechanism-drawer">
				<p class="molosoc-eyebrow"><?php esc_html_e( 'Building a prevention routine that actually sticks', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'Building a prevention routine that actually sticks', 'molosoc' ); ?></h2>
				<p><?php esc_html_e( 'Prevention habits fall off for the same reason treatment routines do — there\'s no structure keeping them going once the immediate problem has passed.', 'molosoc' ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php esc_html_e( 'Why prevention fails the same way treatment does — no structure', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "Prevention habits fall off for the same reason treatment routines do — there's no structure keeping them going once the immediate problem has passed.", 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'What a five-minute weekly check actually catches', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'A quick weekly look at trim shape, shoe fit, and skin condition catches small issues before they become a repeat episode.', 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'Making it part of an existing routine instead of a new one', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Attaching this check to something already happening regularly — a shower, a nail-trim day — makes it far more likely to actually continue.', 'molosoc' ); ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- BACK TO PILLAR -->
	<section class="molosoc-section molosoc-section--bg-cream">
		<div class="molosoc-section__inner" style="text-align:center;">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Part of a bigger picture', 'molosoc' ); ?></p>
			<h2><a href="<?php echo esc_url( home_url( '/ingrown-toenails/' ) ); ?>">&larr; <?php esc_html_e( 'Back to Ingrown Toenails', 'molosoc' ); ?></a></h2>
		</div>
	</section>

	<!-- FINAL CTA — Persona 2. -->
	<section class="molosoc-section molosoc-pillar-final-cta">
		<div class="molosoc-pillar-final-cta__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-pillar-final-cta__scrim" aria-hidden="true"></div>
		<div class="molosoc-section__inner molosoc-reveal">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'See the real results', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Before/after results, no filters', 'molosoc' ); ?></h2>
			<p><?php esc_html_e( 'Time-stamped before/after results from real, consistent care.', 'molosoc' ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php esc_html_e( 'See real results, no filters', 'molosoc' ); ?></a>
		</div>
	</section>

</main>

<?php
get_footer();
