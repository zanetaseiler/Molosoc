<?php
/**
 * Template Name: Pillar 3 — Hardened Skin & Calluses
 *
 * Auto-selected by WordPress for any Page with the slug
 * "hardened-skin-calluses" (the "page-{slug}.php" convention takes
 * priority over a manually-picked template), matching the same convention
 * as page-cracked-heels.php / page-ingrown-toenails.php.
 *
 * Ported from site/theme/preview/hardened-skin-calluses-preview.html — see
 * that file's own header comment for the content/image sourcing. Locked
 * copy source: content/molosoc-site/06-pillar3-hardened-skin-calluses/
 * pillar3-hardened-skin-calluses-copy.md.
 *
 * Like page-cracked-heels.php / page-ingrown-toenails.php, this is a
 * normal template: get_header()/get_footer() (real site chrome, real nav
 * menu). Schema markup + meta description are hooked onto wp_head() in
 * functions.php (molosoc_pillar3_schema()) instead of being printed here,
 * since get_header() already owns the <head>.
 *
 * CSS/JS for this page (pillar1.css, sequential-text-reveal.js,
 * severity-reveal.js, mechanism-drawer.js, GSAP+ScrollTrigger,
 * scroll-refresh.js, model-viewer) are enqueued conditionally in
 * functions.php on is_page('hardened-skin-calluses') — reuses pillar1.css
 * and its JS as-is, same as the other pillar pages, since every class in
 * that file is generic (see that file's own comments).
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. H1 + locked lede over
	     pillar3_01_foot_file.jpg (assets/molosoc-image-assets.csv:
	     "Pillar 3 Hardened Skin / Hero"). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar3_01_foot_file.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Hardened skin & calluses', 'molosoc' ); ?></p>
			<h1><?php esc_html_e( 'Hardened skin and calluses: why they form, and what softens them', 'molosoc' ); ?></h1>
			<p><?php esc_html_e( "Hardened skin builds up gradually as skin's response to repeated pressure and friction — and it softens the same way it formed: gradually, with consistent care.", 'molosoc' ); ?></p>
		</div>
	</section>

	<!-- 2. CALLUSES ON FEET — fixed-image-text-reveal. pillar3_02_pumice.jpg
	     stays fixed/static; the 3 H3 points slide in from the right, one
	     per scroll step. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'The causes', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Calluses on feet', 'molosoc' ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php esc_attr_e( 'Calluses on feet', 'molosoc' ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar3_02_pumice.jpg"
							alt="<?php esc_attr_e( 'Feet soaking with a pumice stone nearby', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Foot callus', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'A foot callus is an area of thickened, hardened skin that forms where pressure and friction repeat in the same spot, most often the ball of the foot or the heel.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Corns and calluses', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Corns are smaller, more concentrated areas of hardened skin, usually on or between toes; calluses cover broader, flatter areas — both form for the same reason, just in different places.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'Why it builds up gradually, not overnight', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Skin thickens in layers over weeks of repeated pressure, which is why it never appears suddenly and why softening it also takes sustained time, not a single treatment.', 'molosoc' ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. FOOT CORN CURE — editorial-feature-reveal.
	     molosoc_ritual_reading_nook-scaled.jpg (Image A) gives way to
	     pillar3_03_texture.jpg (Image B) through a circular mask, then the
	     3 severity cards emerge from center to their tiered positions. -->
	<section class="molosoc-severity-section" aria-label="<?php esc_attr_e( 'Foot corn cure', 'molosoc' ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar3_03_texture.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_ritual_reading_nook-scaled.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php esc_html_e( 'When it gets serious', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'Foot corn cure', 'molosoc' ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php esc_html_e( 'Callus treatment', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Effective callus treatment softens the thickened skin gradually with consistent moisture, rather than removing it all at once.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php esc_html_e( 'When thick skin starts affecting how you walk', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "Once hardened skin gets thick enough, it changes how weight distributes across the foot with each step, which is a sign it's past the point of ignoring.", 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php esc_html_e( 'Why picking or cutting it off yourself is risky', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Cutting or picking at hardened skin can go deeper than intended and leave skin exposed and vulnerable — softening it is a safer route to the same result.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. WHY SOAKING AND FILING ALONE DON'T KEEP IT AWAY —
	     orbit-scroll-drawer. The always-rotating molosoc-3d.glb model
	     fades/blurs as a glass drawer carrying the 3 H3 points slides up
	     over it. Same sanctioned exception to "never spin products" as the
	     Product page's own hero model
	     (docs/molosoc-animation-specification.md) — model-viewer's own
	     auto-rotate, independent of scroll/JS. -->
	<section class="molosoc-mechanism-section" aria-label="<?php esc_attr_e( "Why soaking and filing alone don't keep it away", 'molosoc' ); ?>">
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
				<p class="molosoc-eyebrow"><?php esc_html_e( "Why soaking and filing alone don't keep it away", 'molosoc' ); ?></p>
				<h2><?php esc_html_e( "Why soaking and filing alone don't keep it away", 'molosoc' ); ?></h2>
				<p><?php esc_html_e( 'Soaking feet and filing down hardened skin is the routine most people already know and already do.', 'molosoc' ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php esc_html_e( 'The routine most people already try', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Soaking feet and filing down hardened skin is the routine most people already know and already do.', 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'Why hard skin comes back within weeks', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "Filing removes the surface layer but doesn't stop the same pressure point from thickening again, so the callus returns on its own timeline.", 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'What actually needs to change for softening to last', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Moisture needs to reach the thickened skin consistently, not just after a soak, for softening to actually hold between sessions.', 'molosoc' ); ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- 5. GO DEEPER — static, reuses components.css's .molosoc-topic-grid/
	     .molosoc-topic-card. Spoke articles nested under this pillar; all
	     3 links intentionally share the same target
	     (/hardened-skin-calluses/callus-remover/) with different
	     keyword-targeted headlines — locked as written in
	     pillar3-hardened-skin-calluses-copy.md. Thumbnails: 2 photos from
	     the spa-treatment shoot Pillar 2 partially used
	     (assets/molosoc-image-assets.csv), plus the still-unused
	     toenail-filing lifestyle shot — sourced to give these cards
	     distinct images instead of repeating the page hero. -->
	<section class="molosoc-section molosoc-section--bg-cream molosoc-pillar-go-deeper" aria-label="<?php esc_attr_e( 'Go deeper', 'molosoc' ); ?>">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></h2>
			<div class="molosoc-topic-grid">
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/hardened-skin-calluses/callus-remover/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_04.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Callus remover', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'An honest look at what actually removes hard skin, and why it keeps coming back no matter which method is used.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/hardened-skin-calluses/callus-remover/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_05.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'How to remove thick dead skin from feet home remedy', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'A safe, at-home approach to removing thickened skin without over-thinning it.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/hardened-skin-calluses/callus-remover/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_pedicure_01.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'How to get rid of hard skin on feet permanently', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "Why one-time removal isn't the same as prevention, and what actually slows regrowth.", 'molosoc' ); ?></p>
				</a>
			</div>
		</div>
	</section>

	<!-- FINAL CTA — deep-links to the Product page's "Real results, no
	     filters" H2 (Persona 2), same pattern as the other pillar pages. -->
	<section class="molosoc-section molosoc-pillar-final-cta">
		<div class="molosoc-pillar-final-cta__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-pillar-final-cta__scrim" aria-hidden="true"></div>
		<div class="molosoc-section__inner molosoc-reveal">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'See the real results', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Before/after results, no filters', 'molosoc' ); ?></h2>
			<p><?php esc_html_e( 'Real hardened skin, softened through consistent care — not a one-time fix.', 'molosoc' ); ?></p>
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
