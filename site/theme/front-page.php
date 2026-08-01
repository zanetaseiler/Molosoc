<?php
/**
 * Homepage template — implements the 9-beat storytelling arc from
 * docs/molosoc-design-direction.md, ported from homepage-preview.html (the
 * finished design reference) so the live site actually uses the
 * arc-reveal/merge/proof-scale/topics-portal markup that homepage.css and
 * assets/js/{merge-transition,proof-scale,topics-portal}.js were built
 * against. See docs/homepage-story-mapping.md for the full beat-by-beat
 * mapping.
 *
 * This markup was ported once before (see git history), then reverted back
 * to an older, simpler structure after the animation scripts it depends on
 * caused issues. This is a careful re-port: the static markup/images/
 * styling are restored to full parity with homepage-preview.html first, but
 * merge-transition.js / proof-scale.js / topics-portal.js are deliberately
 * left disabled in functions.php for now (their CSS already defines a
 * fully-settled default state with no JS running, so this section renders
 * pixel-accurate to the preview's resting state either way) — see
 * functions.php for the plan to re-enable each one individually.
 *
 * Not yet ported: the hero-to-section circular transition described in
 * docs/molosoc-animation-specification.md (assets/js/arc-reveal.js) — that
 * file doesn't exist yet anywhere in the repo and needs to be designed/built
 * from scratch, not just wired up like everything else here.
 *
 * Deliberately does NOT call get_header(): that renders the site's own nav
 * chrome, and docs/molosoc-design-direction.md says WooCommerce "must
 * disappear visually" on this page. wp_head() is still called directly so
 * plugins (SEO, analytics, WooCommerce cart fragments elsewhere) keep
 * working.
 *
 * Does render its own minimal nav (2026-07-30) via the same 'primary' menu
 * location header.php uses — WooCommerce chrome stays hidden, but the page
 * is no longer a dead end with no way to click to Foot Covers/Product.
 * Floating over the hero, not boxed like molosoc-site-header.
 *
 * DOES call get_footer() at the bottom, though — the homepage had no
 * footer at all otherwise (no legal links, no copyright), which was never
 * an intentional design decision, just a side effect of skipping both
 * together. Reuses the same footer every other template already uses.
 */

defined( 'ABSPATH' ) || exit;

$molosoc_img = get_stylesheet_directory_uri() . '/assets/images/';
?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class( 'molosoc-front-page' ); ?>>
<?php wp_body_open(); ?>

<a class="molosoc-skip-link" href="#main"><?php esc_html_e( 'Skip to content', 'molosoc' ); ?></a>

<header class="molosoc-home-header">
	<a class="molosoc-home-header__logo" href="<?php echo esc_url( home_url( '/' ) ); ?>">
		<img src="<?php echo esc_url( get_stylesheet_directory_uri() . '/assets/images/molosoc-logo-white.png' ); ?>" alt="<?php echo esc_attr( get_bloginfo( 'name' ) ); ?>" loading="eager" decoding="async">
	</a>
	<button type="button" class="molosoc-nav-toggle" aria-expanded="false" aria-controls="molosoc-home-nav" aria-label="<?php esc_attr_e( 'Menu', 'molosoc' ); ?>">
		<span></span><span></span><span></span>
	</button>
	<?php
	wp_nav_menu( array(
		'theme_location'   => 'primary',
		'container'        => 'nav',
		'container_id'     => 'molosoc-home-nav',
		'container_class'  => 'molosoc-home-header__nav',
		'fallback_cb'      => false,
	) );
	?>
</header>

<main id="main">

	<!-- Beat 1+2 — Hero / emotional opening -->
	<section class="molosoc-hero">
		<div class="molosoc-hero__media">
			<img src="<?php echo esc_url( $molosoc_img . 'homepage-hero-preview-graded.jpg' ); ?>"
				alt="<?php esc_attr_e( 'Bare feet peeking out from under a clean white blanket in a bright, airy bedroom', 'molosoc' ); ?>"
				loading="eager" fetchpriority="high" decoding="async">
		</div>
		<div class="molosoc-hero__scrim"></div>
		<div class="molosoc-hero__content">
			<p class="molosoc-eyebrow" style="color: rgba(255,255,255,0.75);"><?php bloginfo( 'name' ); ?></p>
			<h1><?php esc_html_e( "Foot care you'll actually stick with", 'molosoc' ); ?></h1>
			<p><?php esc_html_e( 'Molosoc is a foot care brand built around one idea: most people already own a cream that works — they just never finish the routine around it. The cream is already in your drawer. Molosoc is the missing piece that helps it finish the job, one short session at a time.', 'molosoc' ); ?></p>
		</div>
		<a class="molosoc-hero__scroll-cue" href="#story-start"><?php esc_html_e( 'Scroll', 'molosoc' ); ?></a>
	</section>

	<!-- Beat 2 — The problem, ported from homepage-preview.html's arc-reveal
	     story sequence (see homepage.css "Beat 2 — Why foot care never
	     sticks" for the section this markup drives). -->
	<section id="story-start" class="molosoc-arc-reveal-section">
		<h2 class="molosoc-arc-reveal__heading molosoc-reveal molosoc-reveal--flat"><?php esc_html_e( 'Why foot care never sticks', 'molosoc' ); ?></h2>

		<div class="molosoc-arc-reveal__rows">
			<div class="molosoc-story molosoc-story--left" style="--story-w: 74%;">
				<div class="molosoc-story__media molosoc-reveal molosoc-reveal--fade-only molosoc-reveal--delay">
					<img src="<?php echo esc_url( $molosoc_img . 'homepage-cream-collection-cropped.jpg' ); ?>"
						alt="<?php esc_attr_e( 'Close-up of hands massaging cream into a heel, bright white bedroom', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
				<div class="molosoc-story__text">
					<h3><?php esc_html_e( 'Feet deserve real care, not just intent', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Buying the cream was never the hard part. Finishing the routine is. Molosoc is for what comes after the good intention.', 'molosoc' ); ?></p>
				</div>
			</div>

			<div class="molosoc-story molosoc-story--right" style="--story-w: 52%;">
				<div class="molosoc-story__media">
					<img src="<?php echo esc_url( $molosoc_img . 'homepage-livingroom-graded.jpg' ); ?>"
						alt="<?php esc_attr_e( 'Bare feet up on a wooden side table in a calm minimalist living room', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
				<div class="molosoc-story__text">
					<h3><?php esc_html_e( 'Care should be simple enough to actually stick', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "Routines survive on less friction, not more willpower. That's the design brief here.", 'molosoc' ); ?></p>
				</div>
			</div>

			<div class="molosoc-story molosoc-story--left" style="--story-w: 68%;">
				<div class="molosoc-story__media">
					<img src="<?php echo esc_url( $molosoc_img . 'homepage-pillar5-drawer-graded.jpg' ); ?>"
						alt="<?php esc_attr_e( 'A half-open bathroom drawer crowded with half-used cream tubes and bottles', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
				<div class="molosoc-story__text">
					<h3><?php esc_html_e( "You don't need new products — you need the right ritual", 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Not another cream. The accessory that makes the one you own actually work.', 'molosoc' ); ?></p>
				</div>
			</div>

			<div class="molosoc-story molosoc-story--right" style="--story-w: 74%;">
				<div class="molosoc-story__media">
					<img src="<?php echo esc_url( $molosoc_img . 'homepage-bedside-rug-cropped.jpg' ); ?>"
						alt="<?php esc_attr_e( 'Bare feet stepping onto a soft cream wool rug beside the bed', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
				<div class="molosoc-story__text">
					<h3><?php esc_html_e( 'Foot care is self-care, not vanity', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Ten quiet minutes, just for you — not for anyone watching.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- Beats 4+5 — "Merge and emerge" scroll-pinned sequence, ported from
	     homepage-preview.html so merge-transition.js has the markup it
	     expects. Static-by-default: with no JS/reduced-motion this renders
	     as one flush photo with all text visible (see homepage.css). -->
	<section class="molosoc-section molosoc-section--photo-bg molosoc-merge-section">
		<div class="molosoc-merge__group">
			<div class="molosoc-merge__tile molosoc-merge__tile--left" style="background-image: url('<?php echo esc_url( $molosoc_img . 'homepage-bathroom-bench-graded.jpg' ); ?>');" role="img" aria-label="<?php esc_attr_e( 'A sunlit minimalist bathroom hallway with sheer curtains, wood beams, and bare feet resting on a linen bench', 'molosoc' ); ?>"></div>
			<div class="molosoc-merge__tile molosoc-merge__tile--right" style="background-image: url('<?php echo esc_url( $molosoc_img . 'homepage-bathroom-bench-graded.jpg' ); ?>');"></div>
		</div>
		<div class="molosoc-section__scrim"></div>
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow molosoc-merge__text"><?php esc_html_e( 'How it helps', 'molosoc' ); ?></p>
			<h2 class="molosoc-merge__text" style="max-width: 30rem; margin-top: var(--space-s);"><?php esc_html_e( 'The cream you own, finally finished', 'molosoc' ); ?></h2>

			<div class="molosoc-pillars">
				<div class="molosoc-pillar molosoc-merge__text">
					<h3><?php esc_html_e( 'Locks in moisture', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Seals cream against skin for the length of the session.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-pillar molosoc-merge__text">
					<h3><?php esc_html_e( 'Reduces mess and slipping', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'No greasy floors, no ruined sheets, no reason to stop early.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-pillar molosoc-merge__text">
					<h3><?php esc_html_e( 'Works with your favorite cream', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Cream-agnostic by design — use whatever you already trust.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-pillar molosoc-merge__text">
					<h3><?php esc_html_e( 'Easy self-care ritual', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Soft, cared-for feet from ten quiet minutes, not a new habit to learn.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- Beat 6 — Social proof, ported to add .molosoc-proof__media--scale so
	     proof-scale.js has the element it looks for. -->
	<section class="molosoc-section molosoc-section--bg-cream molosoc-proof-section">
		<div class="molosoc-section__inner">
			<div class="molosoc-proof">
				<div class="molosoc-proof__intro molosoc-reveal">
					<p class="molosoc-eyebrow"><?php esc_html_e( 'Real results', 'molosoc' ); ?></p>
					<h2><?php esc_html_e( 'Three months in, no filters', 'molosoc' ); ?></h2>
				</div>
				<div class="molosoc-media molosoc-proof__media molosoc-proof__media--scale">
					<img src="<?php echo esc_url( $molosoc_img . 'homepage-results-full.jpg' ); ?>"
						alt="<?php esc_attr_e( 'Real 3-month before/after result, no filters — full unedited comparison', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
			</div>
		</div>
	</section>

	<!-- Beat 7 — Product moment -->
	<section class="molosoc-section molosoc-section--bg-deep">
		<div class="molosoc-section__inner molosoc-product-cta molosoc-reveal">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'How Molosoc helps right now', 'molosoc' ); ?></p>
			<h2 style="margin-top: var(--space-s);"><?php esc_html_e( 'Meet the Foot Cover', 'molosoc' ); ?></h2>
			<p class="molosoc-section__lede" style="margin-left:auto; margin-right:auto;"><?php esc_html_e( 'This is where Molosoc shows up today.', 'molosoc' ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php esc_html_e( 'Meet the Foot Cover', 'molosoc' ); ?></a>
		</div>
	</section>

	<!-- Beat 8 — Foot care, topic by topic: one pinned single-screen sequence,
	     ported from homepage-preview.html so topics-portal.js has the
	     .molosoc-topics__stage / .molosoc-feature-card markup it looks for.
	     Single static photo (no circle-reveal, no second image) — the five
	     feature cards emerge from center over it, see homepage.css /
	     topics-portal.js. -->
	<section class="molosoc-topics" id="topics-section" aria-label="<?php esc_attr_e( 'Foot care, topic by topic', 'molosoc' ); ?>">
		<div class="molosoc-topics__stage">
			<div class="molosoc-topics__media" aria-hidden="true">
				<div class="molosoc-topics__bg molosoc-topics__bg--two" style="background-image: url('<?php echo esc_url( $molosoc_img . 'molosoc_ritual_hallway_walk-scaled.jpg' ); ?>');"></div>
			</div>

			<div class="molosoc-topics__cards">
				<a class="molosoc-feature-card molosoc-feature-card--1" href="<?php echo esc_url( home_url( '/cracked-heels/' ) ); ?>">
					<h3><?php esc_html_e( 'Cracked heels & dry skin', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Cracked heels form when dry skin loses elasticity and splits under pressure — they heal with consistent moisture, not overnight fixes.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-feature-card molosoc-feature-card--2" href="<?php echo esc_url( home_url( '/ingrown-toenails/' ) ); ?>">
					<h3><?php esc_html_e( 'Ingrown toenails', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'An ingrown toenail starts at the nail edge, not the skin around it — tight shoes and short trims are usually the real cause.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-feature-card molosoc-feature-card--3" href="<?php echo esc_url( home_url( '/hardened-skin-calluses/' ) ); ?>">
					<h3><?php esc_html_e( 'Hardened skin & calluses', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Hardened skin builds up gradually from pressure and friction — it softens with consistent care, not a one-time filing session.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-feature-card molosoc-feature-card--4" href="<?php echo esc_url( home_url( '/dry-skin-feet/' ) ); ?>">
					<h3><?php esc_html_e( 'Dry skin on feet', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( "Feet dry out differently than the rest of the body — socks, showers, and season all play a part, and moisturizing alone doesn't always fix it.", 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-feature-card molosoc-feature-card--5" href="<?php echo esc_url( home_url( '/foot-cream-that-works/' ) ); ?>">
					<h3><?php esc_html_e( 'Making the cream you already own actually work', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Most foot creams fail from inconsistent use, not a bad formula — the fix is finishing the routine, not switching products.', 'molosoc' ); ?></p>
				</a>
			</div>
		</div>
	</section>

	<!-- Beat 9 — Final CTA -->
	<section class="molosoc-section molosoc-final-cta">
		<div class="molosoc-final-cta__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/3d_render_01_front_nobg.png" alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-final-cta__scrim"></div>
		<div class="molosoc-section__inner molosoc-reveal" style="text-align:center;">
			<p class="molosoc-eyebrow" style="color: rgba(255,255,255,0.6);"><?php esc_html_e( 'The reusable alternative', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'What is a moisture-lock foot cover?', 'molosoc' ); ?></h2>
			<p><?php esc_html_e( "Not every foot mask works the same way. Here's the one Molosoc believes in.", 'molosoc' ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/foot-covers/' ) ); ?>"><?php esc_html_e( 'See how it works', 'molosoc' ); ?></a>
		</div>
	</section>

</main>

<?php get_footer(); ?>
