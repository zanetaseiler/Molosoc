<?php
/**
 * Template Name: Pillar 5 — Cream That Works
 *
 * Auto-selected by WordPress for any Page with the slug
 * "foot-cream-that-works" (the "page-{slug}.php" convention takes
 * priority over a manually-picked template), matching the same convention
 * as page-cracked-heels.php / page-ingrown-toenails.php.
 *
 * Ported from site/theme/preview/foot-cream-that-works-preview.html — see
 * that file's own header comment for the content/image sourcing. Locked
 * copy source: content/molosoc-site/08-pillar5-cream-that-works/pillar5-
 * cream-that-works-copy.md.
 *
 * Like page-cracked-heels.php / page-ingrown-toenails.php, this is a
 * normal template: get_header()/get_footer() (real site chrome, real nav
 * menu). Schema markup + meta description are hooked onto wp_head() in
 * functions.php (molosoc_pillar5_schema()) instead of being printed here,
 * since get_header() already owns the <head>.
 *
 * CSS/JS for this page (pillar1.css, sequential-text-reveal.js,
 * severity-reveal.js, mechanism-drawer.js, GSAP+ScrollTrigger,
 * scroll-refresh.js, model-viewer) are enqueued conditionally in
 * functions.php on is_page('foot-cream-that-works') — reuses pillar1.css
 * and its JS as-is, same as page-ingrown-toenails.php, since every class
 * in that file is generic (see that file's own comments).
 *
 * GO DEEPER: unlike Pillar 1/2, this pillar's 3 spoke articles are
 * explicitly "planned — not yet built" in the locked copy doc — no URL
 * slugs decided yet (docs/site-structure.md: Pillars 4 & 5 don't have
 * spoke-level keyword research done). Cards below render without a link
 * wrapper for that reason — swap to <a class="molosoc-topic-card"
 * href="..."> once each spoke page actually exists.
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. H1 + locked lede over
	     pillar5_01_drawer.jpg (assets/molosoc-image-assets.csv:
	     "Pillar 5 Cream That Works / Cream graveyard drawer"). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar5_01_drawer.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Cream that works', 'molosoc' ); ?></p>
			<h1><?php esc_html_e( 'Does foot cream actually work?', 'molosoc' ); ?></h1>
			<p><?php esc_html_e( "Foot cream works — the reason it often seems like it doesn't is that most of it never gets the chance to actually absorb before it rubs off.", 'molosoc' ); ?></p>
		</div>
	</section>

	<!-- 2. WHY CREAMS GET ABANDONED HALFWAY THROUGH — fixed-image-text-reveal.
	     pillar5_02_squeezing.jpg stays fixed/static; the 3 H3 points slide in
	     from the right, one per scroll step. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'The real reason', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Why creams get abandoned halfway through', 'molosoc' ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php esc_attr_e( 'Why creams get abandoned halfway through', 'molosoc' ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar5_02_squeezing.jpg"
							alt="<?php esc_attr_e( 'Hands squeezing the last bit of cream from an almost-empty tube', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( "Real intent, no structure to keep going", 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "Most people buy a foot cream with real intent to use it regularly — the intent isn't the part that runs out first.", 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( 'The mess that makes people stop reaching for it', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Greasy sheets, slippery floors, and socks that won\'t stay on are usually the actual reason someone quietly stops reaching for a cream they still believe in.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php esc_html_e( "It's not that the cream failed", 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "A half-used bottle in the drawer usually isn't evidence the formula didn't work — it's evidence the routine around it didn't hold.", 'molosoc' ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. HOW LONG DOES FOOT CREAM TAKE TO ABSORB — editorial-feature-reveal.
	     pillar5_03_nightstand.jpg (Image A) gives way to molosoc_ritual_
	     ankle_cream_closeup-scaled.jpg (Image B) through a circular mask,
	     then the 3 cards emerge from center to their tiered positions. -->
	<section class="molosoc-severity-section" aria-label="<?php esc_attr_e( 'How long does foot cream take to absorb', 'molosoc' ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_ritual_ankle_cream_closeup-scaled.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar5_03_nightstand.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php esc_html_e( 'The absorption window', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'How long does foot cream take to absorb?', 'molosoc' ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php esc_html_e( 'Why timing matters more than the cream itself', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Most creams need sustained, uninterrupted contact with skin to fully absorb — often longer than the few minutes most routines actually give them before socks or shoes go back on.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php esc_html_e( 'Should you put socks on after foot cream', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Socks after cream help hold moisture against skin longer than bare feet do, which is part of why the classic "cream plus socks" combination works better than cream alone.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php esc_html_e( 'How to get soft feet overnight', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'The traditional approach is a heavier cream sealed under socks overnight, giving skin hours of uninterrupted contact to absorb. A shorter, focused session with the cream sealed against skin can get much of that same result without needing to commit to wearing anything all night.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. THE CREAM GRAVEYARD PROBLEM — orbit-scroll-drawer. The
	     always-rotating molosoc-3d.glb model fades/blurs as a glass drawer
	     carrying the 3 H3 points slides up over it. -->
	<section class="molosoc-mechanism-section" aria-label="<?php esc_attr_e( 'The cream graveyard problem', 'molosoc' ); ?>">
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
				<p class="molosoc-eyebrow"><?php esc_html_e( 'The cream graveyard problem', 'molosoc' ); ?></p>
				<h2><?php esc_html_e( 'The cream graveyard problem', 'molosoc' ); ?></h2>
				<p><?php esc_html_e( 'Each bottle usually got bought with real intent, used a handful of times, then stalled — not from one bad experience, but from the same mess-and-mid-routine drop-off repeating with every new cream.', 'molosoc' ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php esc_html_e( 'Why bathrooms end up with 2-3 half-used bottles', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Each bottle usually got bought with real intent, used a handful of times, then stalled — not from one bad experience, but from the same mess-and-mid-routine drop-off repeating with every new cream.', 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'What that pattern actually says about the routine, not the product', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "Buying a new cream doesn't fix the actual gap, which is structure — the same drop-off tends to happen again with whatever's bought next.", 'molosoc' ); ?></p>
					</article>
					<article>
						<h3><?php esc_html_e( 'Breaking the cycle without buying a new cream', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( "The fix isn't another bottle — it's giving the cream already owned a real, sealed session to actually work, instead of replacing it before it's had the chance.", 'molosoc' ); ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- 5. GO DEEPER — static, reuses components.css's .molosoc-topic-grid/
	     .molosoc-topic-card. Unlike Pillar 1/2, these 3 spoke articles are
	     explicitly "planned — not yet built" in the locked copy (no URL
	     slugs decided yet), so the cards render without a link wrapper —
	     swap to <a class="molosoc-topic-card"> once each spoke page exists.
	     Thumbnails: none of these 3 have a dedicated shoot yet (unlike
	     Pillar 2's 5-photo spa-treatment set), so each pulls a distinct,
	     otherwise-unclaimed generic cream photo instead of repeating this
	     page's own hero/section images. Checked against
	     assets/molosoc-image-assets.csv first — molosoc_ritual_bedside_rug
	     and molosoc_ritual_ankle_cream_closeup were already assigned to
	     Pillar 4's Go Deeper thumbnails as of 2026-07-31, so those two were
	     deliberately skipped here. -->
	<section class="molosoc-section molosoc-section--bg-cream molosoc-pillar-go-deeper" aria-label="<?php esc_attr_e( 'Go deeper', 'molosoc' ); ?>">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></h2>
			<div class="molosoc-topic-grid">
				<div class="molosoc-topic-card">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/hero_collection_02_cream-scaled.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Softening foot cream', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'What actually makes a softening cream effective, beyond the ingredient list.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-topic-card">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_ritual_vanity_cream-scaled.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'How to moisturize feet overnight', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'A closer look at the overnight technique, and what it actually takes to do it well.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-topic-card">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_05.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Overnight foot cream', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'What to look for if going the overnight route.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- FINAL CTA — deep-links to the Product page. This pillar's own copy
	     closes with "The cream you already own, finally working" instead
	     of Pillar 1/2's generic "See the real results" — kept exactly as
	     locked, eyebrow/H2 sharing the same text (same pattern
	     page-moisture-lock-foot-cover.php's own molosoc-product-heading
	     already uses). -->
	<section class="molosoc-section molosoc-pillar-final-cta">
		<div class="molosoc-pillar-final-cta__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/homepage-results-full.jpg"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-pillar-final-cta__scrim" aria-hidden="true"></div>
		<div class="molosoc-section__inner molosoc-reveal">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'The cream you already own, finally working', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'The cream you already own, finally working', 'molosoc' ); ?></h2>
			<p><?php esc_html_e( 'This is exactly what Molosoc is built for — sealing the cream you already trust against your skin, in one focused session, instead of another bottle in the drawer.', 'molosoc' ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php esc_html_e( 'See how it works', 'molosoc' ); ?></a>
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
