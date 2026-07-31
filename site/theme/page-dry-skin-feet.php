<?php
/**
 * Template Name: Pillar 4 — Dry Skin on Feet
 *
 * Auto-selected by WordPress for any Page with the slug "dry-skin-feet"
 * (the "page-{slug}.php" convention takes priority over a manually-picked
 * template), matching the same convention as page-cracked-heels.php /
 * page-ingrown-toenails.php.
 *
 * Ported from site/theme/preview/dry-skin-feet-preview.html — see that
 * file's own header comment for the content/image sourcing and the
 * section-to-animation mapping (this pillar's copy orders its content
 * differently than Pillar 1/2, so the 2nd/3rd sections below use the
 * mechanism/severity animations in a swapped order — see that comment for
 * why). Locked copy source: content/molosoc-site/07-pillar4-dry-skin-feet/
 * pillar4-dry-skin-feet-copy.md.
 *
 * Like page-cracked-heels.php / page-ingrown-toenails.php, this is a
 * normal template: get_header()/get_footer() (real site chrome, real nav
 * menu). Schema markup + meta description are hooked onto wp_head() in
 * functions.php (molosoc_pillar4_schema()) instead of being printed here,
 * since get_header() already owns the <head>.
 *
 * CSS/JS for this page (pillar1.css, sequential-text-reveal.js,
 * severity-reveal.js, mechanism-drawer.js, GSAP+ScrollTrigger,
 * scroll-refresh.js, model-viewer) are enqueued conditionally in
 * functions.php on is_page('dry-skin-feet') — reuses pillar1.css and its
 * JS as-is, same as the other two pillar pages, since every class in that
 * file is generic (see that file's own comments).
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. H1 + locked lede over
	     pillar4_01_wool_socks.jpg (assets/molosoc-image-assets.csv:
	     "Pillar 4 Dry Skin / Hero"). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar4_01_wool_socks.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Dry skin on feet', 'molosoc' ); ?></p>
			<h1><?php esc_html_e( 'Dry skin on feet: why it keeps coming back', 'molosoc' ); ?></h1>
			<p><?php esc_html_e( "Feet dry out differently than the rest of the body, and moisturizing alone often doesn't fix it — not because the cream fails, but because it rarely stays on long enough to actually work.", 'molosoc' ); ?></p>
		</div>
	</section>

	<!-- 2. WHAT CAUSES DRY SKIN ON FEET — fixed-image-text-reveal.
	     pillar4_03_radiator.jpg stays fixed/static; the 3 H3 causes slide
	     in from the right, one per scroll step. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'The causes', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'What causes dry skin on feet', 'molosoc' ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php esc_attr_e( 'What causes dry skin on feet', 'molosoc' ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar4_03_radiator.jpg"
							alt="<?php esc_attr_e( 'Feet resting near a radiator, winter dryness mood', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Why soles dry out differently than the rest of the body', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Soles have no oil glands the way most of the rest of the skin does, so they rely entirely on external moisture to stay soft — which is why they dry out faster and more often.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Socks, shoes, and trapped moisture loss', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Enclosed feet lose moisture to fabric and air circulation throughout the day, often without anyone noticing until the skin already feels rough.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Seasonal triggers (heating, cold air, hot showers)', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Indoor heating, cold outside air, and hot showers all strip moisture from skin faster than usual, which is why dryness tends to spike in the same seasons every year.', 'molosoc' ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. WHY ARE MY FEET SO DRY EVEN WHEN I MOISTURIZE — orbit-scroll-
	     drawer. The always-rotating molosoc-3d.glb model fades/blurs as a
	     glass drawer carrying the 3 H3 points slides up over it. This
	     pillar's copy puts the "routine/mechanism" content in the position
	     Pillar 1/2 use their 4th section for, so it's built with that
	     section's animation here instead (see the preview file's header
	     comment). -->
	<section class="molosoc-mechanism-section" aria-label="<?php esc_attr_e( 'Why are my feet so dry even when I moisturize?', 'molosoc' ); ?>">
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
				<p class="molosoc-eyebrow"><?php esc_html_e( 'Why are my feet so dry even when I moisturize?', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'Why are my feet so dry even when I moisturize?', 'molosoc' ); ?></h2>
				<p><?php esc_html_e( "Most people already apply cream regularly and still end up with dry feet — the routine itself isn't missing.", 'molosoc' ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php esc_html_e( 'The routine most people already try', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "Most people already apply cream regularly and still end up with dry feet — the routine itself isn't missing.", 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'Why cream doesn\'t stay on long enough to actually absorb', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Cream applied and left uncovered gets absorbed by socks or rubbed off on floors within minutes, long before the skin has had a real chance to take it in.', 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'What actually needs to change for it to stick', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Cream needs uninterrupted contact with skin, not a thicker layer or a pricier formula, to actually absorb instead of transferring somewhere else.', 'molosoc' ); ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. SOCKS, TIGHTS, AND THE DRYNESS NOBODY TALKS ABOUT —
	     editorial-feature-reveal. seasonal_03_winter.jpg (Image A) gives
	     way to molosoc_spa_treatment_02.jpg (Image B) through a circular
	     mask, then the 3 cards emerge from center to their tiered
	     positions. -->
	<section class="molosoc-severity-section" aria-label="<?php esc_attr_e( 'Socks, tights, and the dryness nobody talks about', 'molosoc' ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_02.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/seasonal_03_winter.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php esc_html_e( 'What nobody talks about', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'Socks, tights, and the dryness nobody talks about', 'molosoc' ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php esc_html_e( 'Why enclosed feet dry out differently', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Feet inside socks and tights all day are constantly losing moisture to fabric, which is a slower, quieter version of the same drying process as bare, exposed skin.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php esc_html_e( 'Winter habit-building vs. summer exposure', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "Winter hides feet from view, which makes it a low-pressure window to build a consistent moisture habit — without the urgency summer's visibility usually creates.", 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php esc_html_e( 'A private, low-effort ritual for this window', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'A short, private session with a cream already on hand fits easily into a winter routine, with none of the pressure of getting "sandal-ready."', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 5. GO DEEPER — static, reuses components.css's .molosoc-topic-grid/
	     .molosoc-topic-card ("educational content beat"). Spoke articles
	     nested under this pillar; the 3rd card cross-links toward the
	     Cracked Heels pillar comparison, per pillar4-dry-skin-feet-copy.md's
	     own cross-link note. Thumbnails: no dedicated Pillar 4 "Go deeper"
	     photo set exists yet (unlike Pillar 1/2's sourced 3-photo sets), so
	     these reuse thematically-fitting photos already in the library —
	     see assets/molosoc-image-assets.csv for each image's updated
	     multi-use note. -->
	<section class="molosoc-section molosoc-section--bg-cream molosoc-pillar-go-deeper" aria-label="<?php esc_attr_e( 'Go deeper', 'molosoc' ); ?>">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></h2>
			<div class="molosoc-topic-grid">
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/dry-skin-feet/dry-foot-skin-treatment/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_ritual_ankle_cream_closeup-scaled.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Dry foot skin treatment', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'What actually treats dry foot skin, beyond another layer of cream.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/dry-skin-feet/home-remedies/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_ritual_bedside_rug-scaled.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Dry skin feet home remedies', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Simple, at-home approaches that actually hold up over time.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/dry-skin-feet/vs-cracked-heels/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar1_01_heels_floor.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( "Dry feet vs. cracked heels: what's the difference", 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "How to tell which one you're actually dealing with.", 'molosoc' ); ?></p>
				</a>
			</div>
		</div>
	</section>

	<!-- FINAL CTA — deep-links to the Product page's "Real results, no
	     filters" H2 (Persona 2, this pillar's own persona). Reuses the
	     dry/cracked heel-texture proof photo already assigned to Pillar 1's
	     final CTA — it reads as "dry skin" proof at least as directly as it
	     does "cracked heels" proof, so it's the closer visual fit here too
	     (see assets/molosoc-image-assets.csv's updated multi-use note). -->
	<section class="molosoc-section molosoc-pillar-final-cta">
		<div class="molosoc-pillar-final-cta__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-pillar-final-cta__scrim" aria-hidden="true"></div>
		<div class="molosoc-section__inner molosoc-reveal">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'See the real results', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Before/after results, no filters', 'molosoc' ); ?></h2>
			<p><?php esc_html_e( 'If cream that "doesn\'t work anymore" sounds familiar, the real issue is usually the routine, not the formula.', 'molosoc' ); ?></p>
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
