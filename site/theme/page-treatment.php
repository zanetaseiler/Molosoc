<?php
/**
 * Template Name: Spoke 1 — Ingrown Toenails Treatment
 *
 * Auto-selected by WordPress for any Page with the slug "treatment" (the
 * "page-{slug}.php" convention), nested under the "ingrown-toenails"
 * parent Page so the permalink resolves to
 * /ingrown-toenails/treatment/ — matching site-structure.md §8, Spoke 1.
 *
 * Ported from site/theme/preview/ingrown-toenails-treatment-preview.html
 * — approved as the spoke template pattern before this port. Locked copy
 * source: content/molosoc-site/09-spoke1-ingrown-toenails-treatment/
 * spoke1-ingrown-toenails-treatment-copy.md.
 *
 * Spokes have exactly 3 H2s (no "Go deeper" — that's pillar-only), so this
 * reuses 3 of the pillar template's 4 content sections one-for-one:
 * fixed-image-text-reveal, editorial-feature-reveal, orbit-scroll-drawer.
 * Same pillar1.css/JS stack as every pillar template — nothing new to
 * enqueue. In place of "Go deeper" this has a link back up to the parent
 * pillar before the final CTA.
 *
 * Normal template: get_header()/get_footer() (real site chrome, real nav
 * menu). Schema markup + meta description are hooked onto wp_head() in
 * functions.php (molosoc_spoke1_schema()) instead of being printed here,
 * since get_header() already owns the <head>.
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. Same photo Pillar 2's own "Go
	     deeper" card already uses for this spoke (molosoc-image-assets.csv /
	     media-library.csv: molosoc_spa_treatment_02.jpg), continuing that
	     visual thread rather than picking a new photo. -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_02.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Ingrown toenails treatment', 'molosoc' ); ?></p>
			<h1><?php esc_html_e( 'Ingrown toenails treatment: what actually works', 'molosoc' ); ?></h1>
			<p><?php esc_html_e( 'Most ingrown toenails respond well to consistent at-home care — softening the skin, relieving pressure, and giving the nail room to grow out properly.', 'molosoc' ); ?></p>
		</div>
	</section>

	<!-- 2. HOW TO TREAT INGROWN TOENAILS — fixed-image-text-reveal.
	     molosoc_ingrown_toenail.jpg stays fixed/static; the 3 H3 steps
	     slide in from the right, one per scroll step. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Step by step', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'How to treat ingrown toenails', 'molosoc' ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php esc_attr_e( 'How to treat ingrown toenails', 'molosoc' ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_ingrown_toenail.jpg"
							alt="<?php esc_attr_e( 'Foot soaking in a warm basin beside nail clippers and cotton pads', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Softening the skin before anything else', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Softening the skin around the nail is the first real step, since firm, dry skin is what the nail edge is fighting against as it grows.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Why warm soaks are step one, not a cure', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "A warm soak softens skin and eases discomfort in the moment, but it doesn't change the underlying pressure — it's preparation for the steps that actually help, not a fix on its own.", 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'What changes once the pressure is relieved', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Once the surrounding skin is softer and the pressure point is addressed, the nail has room to grow past the skin instead of into it, which is when actual improvement starts.', 'molosoc' ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. HOW TO GET RID OF INGROWN TOENAILS — editorial-feature-reveal.
	     molosoc_pedicure_01.jpg (Image A, filing) gives way to
	     pillar2_02_trimming.jpg (Image B, trimming) through a circular
	     mask, then the 3 cards emerge from center to their tiered
	     positions. -->
	<section class="molosoc-severity-section" aria-label="<?php esc_attr_e( 'How to get rid of ingrown toenails', 'molosoc' ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar2_02_trimming.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_pedicure_01.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php esc_html_e( 'For good, not just for now', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'How to get rid of ingrown toenails', 'molosoc' ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php esc_html_e( 'The at-home approach that actually holds up over time', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "An approach that holds up combines consistent softening with a genuine change to whatever's been causing the pressure — shoes, trim, or both — rather than treating a single episode in isolation.", 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php esc_html_e( 'Why "getting rid of it" once isn\'t the same as it not coming back', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Resolving the current episode addresses the symptom; preventing the next one requires the underlying cause — nail shape, footwear, trim habit — to actually change.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php esc_html_e( 'Nail-trimming technique that prevents the repeat cycle', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Trimming straight across, rather than rounding the corners, gives the nail edge a straighter path to grow along instead of curving back into the skin.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. WHEN HOME TREATMENT ISN'T ENOUGH — orbit-scroll-drawer. The
	     always-rotating molosoc-3d.glb model fades/blurs as a glass drawer
	     carrying the 3 H3 points slides up over it. -->
	<section class="molosoc-mechanism-section" aria-label="<?php esc_attr_e( "When home treatment isn't enough", 'molosoc' ); ?>">
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
				<p class="molosoc-eyebrow"><?php esc_html_e( 'When to get help', 'molosoc' ); ?></p>
			</div>

			<div class="molosoc-mechanism-drawer">
				<p class="molosoc-eyebrow"><?php esc_html_e( "When home treatment isn't enough", 'molosoc' ); ?></p>
				<h2><?php esc_html_e( "When home treatment isn't enough", 'molosoc' ); ?></h2>
				<p><?php esc_html_e( 'Increasing redness, warmth, swelling, or discharge around the nail are signs that go beyond what home care alone typically resolves.', 'molosoc' ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php esc_html_e( 'Signs of infection to take seriously', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Increasing redness, warmth, swelling, or discharge around the nail are signs that go beyond what home care alone typically resolves.', 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'When to see a podiatrist instead of continuing at home', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "If symptoms are worsening after several days of consistent home care, or if there's any sign of infection, it's time to see a podiatrist rather than continuing to self-treat.", 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'Why waiting too long makes treatment harder later', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'The longer irritated skin stays under pressure, the more inflamed and harder to treat it becomes — which is why early, consistent care matters more than an aggressive fix later.', 'molosoc' ); ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- BACK TO PILLAR — spokes don't have a "Go deeper" section of their
	     own (they're the leaf page); this replaces it with a link back up
	     to the parent pillar, per site-structure.md §8. No new CSS —
	     reuses molosoc-section/molosoc-eyebrow exactly as elsewhere on
	     this page. -->
	<section class="molosoc-section molosoc-section--bg-cream">
		<div class="molosoc-section__inner" style="text-align:center;">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Part of a bigger picture', 'molosoc' ); ?></p>
			<h2><a href="<?php echo esc_url( home_url( '/ingrown-toenails/' ) ); ?>">&larr; <?php esc_html_e( 'Back to Ingrown Toenails', 'molosoc' ); ?></a></h2>
		</div>
	</section>

	<!-- FINAL CTA — deep-links to the Product page's "Real results, no
	     filters" H2 (Persona 2 — same persona this spoke's parent pillar
	     targets). -->
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
