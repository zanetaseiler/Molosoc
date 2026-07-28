<?php
/**
 * Homepage template — implements the 9-beat storytelling arc from
 * docs/molosoc-design-direction.md, mapped against the locked copy in
 * content/molosoc-site/01-homepage/homepage-copy.md.
 *
 * See docs/homepage-story-mapping.md for the full beat-by-beat mapping,
 * including the two beats (3 "why current solutions fail", and the
 * disposable-vs-reusable argument) intentionally NOT duplicated here —
 * that argument belongs to the Category page per docs/seo-geo-plan.md's
 * layered architecture.
 *
 * Images: staging URLs match assets/molosoc-image-assets.csv exactly
 * (page/section = "Homepage / Hero" and "Homepage / Brand pillars").
 * Do not swap these for other CSV rows mapped to other pages.
 *
 * Deliberately does NOT call get_header()/get_footer(): those render the
 * parent Thrive theme's own nav/store chrome, which is exactly what
 * docs/molosoc-design-direction.md says must "disappear visually" on this
 * page. wp_head()/wp_footer() are still called directly below so plugins
 * (SEO, analytics, WooCommerce cart fragments elsewhere) keep working —
 * only the parent theme's visual header/footer markup is skipped.
 */

defined( 'ABSPATH' ) || exit;
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
	<img src="https://staging.molosoc.com/wp-content/uploads/2026/06/MOLOSOC-Logo-TM.png" alt="<?php bloginfo( 'name' ); ?>" loading="eager" decoding="async">
</header>

<main id="main">

	<section class="molosoc-hero">
		<div class="molosoc-hero__media">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/homepage_01_bathroom_bench-scaled.jpg"
				alt="<?php esc_attr_e( 'Bare feet resting on a linen bench in a sunlit minimalist bathroom hallway', 'molosoc' ); ?>"
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

	<section id="story-start" class="molosoc-section molosoc-section--bg-cream">
		<div class="molosoc-section__inner">
			<h2 class="molosoc-eyebrow molosoc-reveal"><?php esc_html_e( 'Why foot care never sticks', 'molosoc' ); ?></h2>

			<div class="molosoc-problem__list">
				<div class="molosoc-problem__item molosoc-reveal">
					<div>
						<h3><?php esc_html_e( 'Feet deserve real care, not just intent', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Buying the cream was never the hard part. Finishing the routine is. Molosoc is for what comes after the good intention.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-media molosoc-problem__media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/homepage_02_cream_massage.jpg"
							alt="<?php esc_attr_e( 'Close-up of hands massaging cream into a heel', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>

				<div class="molosoc-problem__item molosoc-reveal">
					<div>
						<h3><?php esc_html_e( 'Care should be simple enough to actually stick', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Routines survive on less friction, not more willpower. That\'s the design brief here.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-media molosoc-problem__media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/homepage_03_livingroom_footrest-scaled.jpg"
							alt="<?php esc_attr_e( 'Bare feet up on a wooden side table in a calm minimalist living room', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>

				<div class="molosoc-problem__item molosoc-reveal" style="grid-template-columns: 1fr; max-width: 34rem;">
					<div>
						<h3><?php esc_html_e( "You don't need new products — you need the right ritual", 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Not another cream. The accessory that makes the one you own actually work.', 'molosoc' ); ?></p>
					</div>
				</div>

				<div class="molosoc-problem__item molosoc-reveal">
					<div>
						<h3><?php esc_html_e( 'Foot care is self-care, not vanity', 'molosoc' ); ?></h3>
						<p><?php esc_html_e( 'Ten quiet minutes, just for you — not for anyone watching.', 'molosoc' ); ?></p>
					</div>
					<div class="molosoc-media molosoc-problem__media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/homepage_04_bedroom_blanket-scaled.jpg"
							alt="<?php esc_attr_e( 'Bare feet peeking out from under a cream blanket in a serene bedroom', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
			</div>
		</div>
	</section>

	<section class="molosoc-section molosoc-section--bg-deep">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow molosoc-reveal"><?php esc_html_e( 'How it helps', 'molosoc' ); ?></p>
			<h2 class="molosoc-reveal" style="max-width: 30rem; margin-top: var(--space-s);"><?php esc_html_e( 'The cream you own, finally finished', 'molosoc' ); ?></h2>

			<div class="molosoc-pillars molosoc-reveal">
				<div class="molosoc-pillar">
					<h3><?php esc_html_e( 'Locks in moisture', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Seals cream against skin for the length of the session.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-pillar">
					<h3><?php esc_html_e( 'Reduces mess and slipping', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'No greasy floors, no ruined sheets, no reason to stop early.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-pillar">
					<h3><?php esc_html_e( 'Works with your favorite cream', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Cream-agnostic by design — use whatever you already trust.', 'molosoc' ); ?></p>
				</div>
				<div class="molosoc-pillar">
					<h3><?php esc_html_e( 'Easy self-care ritual', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Soft, cared-for feet from ten quiet minutes, not a new habit to learn.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<section class="molosoc-section molosoc-section--bg-cream molosoc-proof-section">
		<div class="molosoc-section__inner">
			<div class="molosoc-proof">
				<div class="molosoc-media molosoc-reveal">
					<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/Molosoc-Real-3-months-results.jpg"
						alt="<?php esc_attr_e( 'Real 3-month before/after result, no filters', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
				<div class="molosoc-reveal">
					<p class="molosoc-eyebrow"><?php esc_html_e( 'Real results', 'molosoc' ); ?></p>
					<h2 style="margin-top: var(--space-s);"><?php esc_html_e( 'Three months in, no filters', 'molosoc' ); ?></h2>
					<p class="molosoc-proof__caption"><?php esc_html_e( 'Time-stamped, unedited — the kind of proof this brand leads with.', 'molosoc' ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<section class="molosoc-section molosoc-section--bg-deep">
		<div class="molosoc-section__inner molosoc-product-cta molosoc-reveal">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'How Molosoc helps right now', 'molosoc' ); ?></p>
			<h2 style="margin-top: var(--space-s);"><?php esc_html_e( 'Meet the Foot Cover', 'molosoc' ); ?></h2>
			<p class="molosoc-section__lede" style="margin-left:auto; margin-right:auto;"><?php esc_html_e( 'This is where Molosoc shows up today.', 'molosoc' ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php esc_html_e( 'Meet the Foot Cover', 'molosoc' ); ?></a>
		</div>
	</section>

	<section class="molosoc-section molosoc-section--bg-cream">
		<div class="molosoc-section__inner">
			<h2 class="molosoc-eyebrow molosoc-reveal"><?php esc_html_e( 'Foot care, topic by topic', 'molosoc' ); ?></h2>

			<div class="molosoc-topic-grid molosoc-reveal">
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/cracked-heels/' ) ); ?>">
					<h3><?php esc_html_e( 'Cracked heels & dry skin', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Cracked heels form when dry skin loses elasticity and splits under pressure — they heal with consistent moisture, not overnight fixes.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/ingrown-toenails/' ) ); ?>">
					<h3><?php esc_html_e( 'Ingrown toenails', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'An ingrown toenail starts at the nail edge, not the skin around it — tight shoes and short trims are usually the real cause.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/hardened-skin-calluses/' ) ); ?>">
					<h3><?php esc_html_e( 'Hardened skin & calluses', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Hardened skin builds up gradually from pressure and friction — it softens with consistent care, not a one-time filing session.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/dry-skin-feet/' ) ); ?>">
					<h3><?php esc_html_e( 'Dry skin on feet', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Feet dry out differently than the rest of the body — socks, showers, and season all play a part.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/foot-cream-that-works/' ) ); ?>">
					<h3><?php esc_html_e( 'Making the cream you already own work', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Most foot creams fail from inconsistent use, not a bad formula — the fix is finishing the routine.', 'molosoc' ); ?></p>
				</a>
			</div>
		</div>
	</section>

	<section class="molosoc-section molosoc-final-cta">
		<div class="molosoc-section__inner molosoc-reveal" style="text-align:center;">
			<p class="molosoc-eyebrow" style="color: rgba(255,255,255,0.6);"><?php esc_html_e( 'The reusable alternative', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'What is a moisture-lock foot cover?', 'molosoc' ); ?></h2>
			<p><?php esc_html_e( "Not every foot mask works the same way. Here's the one Molosoc believes in.", 'molosoc' ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/foot-covers/' ) ); ?>"><?php esc_html_e( 'See how it works', 'molosoc' ); ?></a>
		</div>
	</section>

</main>

<?php wp_footer(); ?>
</body>
</html>
