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

$molosoc_is_cz = function_exists( 'pll_current_language' ) && pll_current_language() === 'cz';
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
		<picture>
			<source srcset="<?php echo esc_url( $molosoc_img . 'molosoc-logo-white.webp' ); ?>" type="image/webp">
			<img src="<?php echo esc_url( $molosoc_img . 'molosoc-logo-white.png' ); ?>" alt="<?php echo esc_attr( get_bloginfo( 'name' ) ); ?>" loading="eager" decoding="async" width="1567" height="230">
		</picture>
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
			<picture>
				<source type="image/webp"
					srcset="<?php echo esc_url( $molosoc_img . 'homepage-hero-preview-graded-mobile.webp' ); ?> 900w, <?php echo esc_url( $molosoc_img . 'homepage-hero-preview-graded.webp' ); ?> 2200w"
					sizes="100vw">
				<img src="<?php echo esc_url( $molosoc_img . 'homepage-hero-preview-graded.jpg' ); ?>"
					alt="<?php esc_attr_e( 'Bare feet peeking out from under a clean white blanket in a bright, airy bedroom', 'molosoc' ); ?>"
					loading="eager" fetchpriority="high" decoding="async" width="2560" height="1429">
			</picture>
		</div>
		<div class="molosoc-hero__scrim"></div>
		<div class="molosoc-hero__content">
			<p class="molosoc-eyebrow" style="color: rgba(255,255,255,0.75);"><?php bloginfo( 'name' ); ?></p>
			<?php if ( $molosoc_is_cz ) : ?>
				<h1>Péče o nohy, u které vydržíte</h1>
				<p>Molosoc je značka péče o nohy postavená na jedné myšlence: krém, který už máte doma, obvykle funguje — jen se u něj většina lidí nedostane až k pravidelnému používání. Krém už na vás čeká v koupelně. Molosoc je ten chybějící krok, který mu pomůže konečně odvést svou práci.</p>
			<?php else : ?>
				<h1><?php esc_html_e( "Foot care you'll actually stick with", 'molosoc' ); ?></h1>
				<p><?php esc_html_e( 'Molosoc is a foot care brand built around one idea: most people already own a cream that works — they just never finish the routine around it. The cream is already in your drawer. Molosoc is the missing piece that helps it finish the job, one short session at a time.', 'molosoc' ); ?></p>
			<?php endif; ?>
		</div>
		<a class="molosoc-hero__scroll-cue" href="#story-start"><?php esc_html_e( 'Scroll', 'molosoc' ); ?></a>
	</section>

	<!-- Beat 2 — The problem, ported from homepage-preview.html's arc-reveal
	     story sequence (see homepage.css "Beat 2 — Why foot care never
	     sticks" for the section this markup drives). -->
	<section id="story-start" class="molosoc-arc-reveal-section">
		<h2 class="molosoc-arc-reveal__heading molosoc-reveal molosoc-reveal--flat"><?php echo esc_html( $molosoc_is_cz ? 'Proč péče o nohy nikdy nevydrží' : __( 'Why foot care never sticks', 'molosoc' ) ); ?></h2>

		<div class="molosoc-arc-reveal__rows">
			<div class="molosoc-story molosoc-story--left" style="--story-w: 74%;">
				<div class="molosoc-story__media molosoc-reveal molosoc-reveal--fade-only molosoc-reveal--delay">
					<picture>
						<source type="image/webp"
							srcset="<?php echo esc_url( $molosoc_img . 'homepage-cream-collection-cropped-mobile.webp' ); ?> 750w, <?php echo esc_url( $molosoc_img . 'homepage-cream-collection-cropped.webp' ); ?> 1143w"
							sizes="(max-width: 720px) 100vw, 852px">
						<img src="<?php echo esc_url( $molosoc_img . 'homepage-cream-collection-cropped.jpg' ); ?>"
							alt="<?php esc_attr_e( 'Close-up of hands massaging cream into a heel, bright white bedroom', 'molosoc' ); ?>"
							loading="lazy" decoding="async" width="1143" height="1429">
					</picture>
				</div>
				<div class="molosoc-story__text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Nohy si zaslouží skutečnou péči, ne jen dobrý úmysl' : __( 'Feet deserve real care, not just intent', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Koupit krém nikdy nebyl ten těžký krok — většina lidí, kteří ho vlastní, už ví, že na nohou záleží. Chybí až to, co přijde potom.' : __( 'Buying the cream was never the hard part. Finishing the routine is. Molosoc is for what comes after the good intention.', 'molosoc' ) ); ?></p>
				</div>
			</div>

			<div class="molosoc-story molosoc-story--right" style="--story-w: 74%;">
				<div class="molosoc-story__media">
					<picture>
						<source type="image/webp"
							srcset="<?php echo esc_url( $molosoc_img . 'homepage-livingroom-graded-mobile.webp' ); ?> 750w, <?php echo esc_url( $molosoc_img . 'homepage-livingroom-graded.webp' ); ?> 1143w"
							sizes="(max-width: 720px) 100vw, 599px">
						<img src="<?php echo esc_url( $molosoc_img . 'homepage-livingroom-graded.jpg' ); ?>"
							alt="<?php esc_attr_e( 'Bare feet up on a wooden side table in a calm minimalist living room', 'molosoc' ); ?>"
							loading="lazy" decoding="async" width="1143" height="1429" style="object-position: left bottom;">
					</picture>
				</div>
				<div class="molosoc-story__text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Péče by měla být tak jednoduchá, že u ní vydržíte' : __( 'Care should be simple enough to actually stick', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Rutina, která vyžaduje sílu vůle každý večer, nepřežije jediný nabitý týden. Přežívají ty, které mají méně překážek, ne ty, co chtějí víc úsilí.' : __( "Routines survive on less friction, not more willpower. That's the design brief here.", 'molosoc' ) ); ?></p>
				</div>
			</div>

			<div class="molosoc-story molosoc-story--left" style="--story-w: 68%;">
				<div class="molosoc-story__media">
					<picture>
						<source type="image/webp"
							srcset="<?php echo esc_url( $molosoc_img . 'homepage-pillar5-drawer-graded-mobile.webp' ); ?> 750w, <?php echo esc_url( $molosoc_img . 'homepage-pillar5-drawer-graded.webp' ); ?> 1434w"
							sizes="(max-width: 720px) 100vw, 783px">
						<img src="<?php echo esc_url( $molosoc_img . 'homepage-pillar5-drawer-graded.jpg' ); ?>"
							alt="<?php esc_attr_e( 'A half-open bathroom drawer crowded with half-used cream tubes and bottles', 'molosoc' ); ?>"
							loading="lazy" decoding="async" width="1434" height="1792">
					</picture>
				</div>
				<div class="molosoc-story__text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Nepotřebujete nový produkt — potřebujete správný rituál' : __( "You don't need new products — you need the right ritual", 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Není to další krém na plnou poličku. Molosoc nenahrazuje to, co už máte — je to doplněk, díky kterému to konečně funguje.' : __( 'Not another cream. The accessory that makes the one you own actually work.', 'molosoc' ) ); ?></p>
				</div>
			</div>

			<div class="molosoc-story molosoc-story--right" style="--story-w: 74%;">
				<div class="molosoc-story__media">
					<picture>
						<source type="image/webp"
							srcset="<?php echo esc_url( $molosoc_img . 'homepage-bedside-rug-cropped-mobile.webp' ); ?> 750w, <?php echo esc_url( $molosoc_img . 'homepage-bedside-rug-cropped.webp' ); ?> 1143w"
							sizes="(max-width: 720px) 100vw, 852px">
						<img src="<?php echo esc_url( $molosoc_img . 'homepage-bedside-rug-cropped.jpg' ); ?>"
							alt="<?php esc_attr_e( 'Bare feet stepping onto a soft cream wool rug beside the bed', 'molosoc' ); ?>"
							loading="lazy" decoding="async" width="1143" height="1429" style="object-position: bottom;">
					</picture>
				</div>
				<div class="molosoc-story__text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Péče o nohy je péče o sebe, ne marnivost' : __( 'Foot care is self-care, not vanity', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Pečovat o nohy neznamená, jak vypadají pro ostatní. Je to pár tichých minut jen pro vás.' : __( 'Ten quiet minutes, just for you — not for anyone watching.', 'molosoc' ) ); ?></p>
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
			<div class="molosoc-merge__tile molosoc-merge__tile--left" style="background-image: url('<?php echo esc_url( $molosoc_img . 'homepage-bathroom-bench-graded.jpg' ); ?>'); background-image: image-set(url('<?php echo esc_url( $molosoc_img . 'homepage-bathroom-bench-graded.webp' ); ?>') type('image/webp'), url('<?php echo esc_url( $molosoc_img . 'homepage-bathroom-bench-graded.jpg' ); ?>') type('image/jpeg'));" role="img" aria-label="<?php esc_attr_e( 'A sunlit minimalist bathroom hallway with sheer curtains, wood beams, and bare feet resting on a linen bench', 'molosoc' ); ?>"></div>
			<div class="molosoc-merge__tile molosoc-merge__tile--right" style="background-image: url('<?php echo esc_url( $molosoc_img . 'homepage-bathroom-bench-graded.jpg' ); ?>'); background-image: image-set(url('<?php echo esc_url( $molosoc_img . 'homepage-bathroom-bench-graded.webp' ); ?>') type('image/webp'), url('<?php echo esc_url( $molosoc_img . 'homepage-bathroom-bench-graded.jpg' ); ?>') type('image/jpeg'));"></div>
		</div>
		<div class="molosoc-section__scrim"></div>
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow molosoc-merge__text"><?php echo esc_html( $molosoc_is_cz ? 'Jak vám to pomůže' : __( 'How it helps', 'molosoc' ) ); ?></p>
			<h2 class="molosoc-merge__text" style="max-width: 30rem; margin-top: var(--space-s);"><?php echo esc_html( $molosoc_is_cz ? 'Krém, který už máte, konečně funguje' : __( 'The cream you own, finally finished', 'molosoc' ) ); ?></h2>

			<div class="molosoc-pillars">
				<div class="molosoc-pillar molosoc-merge__text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Uzamyká vlhkost' : __( 'Locks in moisture', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Zapečetí krém na kůži po celou dobu použití.' : __( 'Seals cream against skin for the length of the session.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-pillar molosoc-merge__text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Omezuje nepořádek a klouzání' : __( 'Reduces mess and slipping', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Žádné mastné podlahy, zničené povlečení ani důvod přestat předčasně.' : __( 'No greasy floors, no ruined sheets, no reason to stop early.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-pillar molosoc-merge__text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Funguje s vaším oblíbeným krémem' : __( 'Works with your favorite cream', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Funguje s jakýmkoli krémem, záměrně — použijte to, čemu už důvěřujete.' : __( 'Cream-agnostic by design — use whatever you already trust.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-pillar molosoc-merge__text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Jednoduchý rituál péče o sebe' : __( 'Easy self-care ritual', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Jemné, ošetřené nohy za deset tichých minut — žádný nový návyk k učení.' : __( 'Soft, cared-for feet from ten quiet minutes, not a new habit to learn.', 'molosoc' ) ); ?></p>
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
					<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Skutečné výsledky' : __( 'Real results', 'molosoc' ) ); ?></p>
					<h2><?php echo esc_html( $molosoc_is_cz ? 'Tři měsíce, žádné filtry' : __( 'Three months in, no filters', 'molosoc' ) ); ?></h2>
				</div>
				<div class="molosoc-media molosoc-proof__media molosoc-proof__media--scale">
					<picture>
						<source srcset="<?php echo esc_url( $molosoc_img . 'homepage-results-full.webp' ); ?>" type="image/webp">
						<img src="<?php echo esc_url( $molosoc_img . 'homepage-results-full.jpg' ); ?>"
							alt="<?php esc_attr_e( 'Real 3-month before/after result, no filters — full unedited comparison', 'molosoc' ); ?>"
							loading="lazy" decoding="async" width="760" height="1362">
					</picture>
				</div>
			</div>
		</div>
	</section>

	<!-- Beat 7 — Product moment -->
	<section class="molosoc-section molosoc-section--bg-deep">
		<div class="molosoc-section__inner molosoc-product-cta molosoc-reveal">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Jak Molosoc pomáhá právě teď' : __( 'How Molosoc helps right now', 'molosoc' ) ); ?></p>
			<h2 style="margin-top: var(--space-s);"><?php echo esc_html( $molosoc_is_cz ? 'Poznejte návlek na nohy' : __( 'Meet the Foot Cover', 'molosoc' ) ); ?></h2>
			<p class="molosoc-section__lede" style="margin-left:auto; margin-right:auto;"><?php echo esc_html( $molosoc_is_cz ? 'Takhle Molosoc pomáhá už dnes.' : __( 'This is where Molosoc shows up today.', 'molosoc' ) ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) : home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php echo esc_html( $molosoc_is_cz ? 'Poznejte návlek na nohy' : __( 'Meet the Foot Cover', 'molosoc' ) ); ?></a>
		</div>
	</section>

	<!-- Beat 8 — Foot care, topic by topic: one pinned single-screen sequence,
	     ported from homepage-preview.html so topics-portal.js has the
	     .molosoc-topics__stage / .molosoc-feature-card markup it looks for.
	     Single static photo (no circle-reveal, no second image) — the five
	     feature cards emerge from center over it, see homepage.css /
	     topics-portal.js. -->
	<section class="molosoc-topics" id="topics-section" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Péče o nohy, téma po tématu' : __( 'Foot care, topic by topic', 'molosoc' ) ); ?>">
		<div class="molosoc-topics__stage">
			<div class="molosoc-topics__media" aria-hidden="true">
				<div class="molosoc-topics__bg molosoc-topics__bg--two" style="background-image: url('<?php echo esc_url( $molosoc_img . 'molosoc_ritual_hallway_walk-scaled.jpg' ); ?>'); background-image: image-set(url('<?php echo esc_url( $molosoc_img . 'molosoc_ritual_hallway_walk-scaled.webp' ); ?>') type('image/webp'), url('<?php echo esc_url( $molosoc_img . 'molosoc_ritual_hallway_walk-scaled.jpg' ); ?>') type('image/jpeg'));"></div>
			</div>

			<?php if ( $molosoc_is_cz ) : ?>
				<div class="molosoc-topics__cards molosoc-topics__cards--cz">
					<a class="molosoc-feature-card molosoc-feature-card--cz-1" href="<?php echo esc_url( home_url( '/cz/popraskane-paty/' ) ); ?>">
						<h3>Popraskané paty a suchá kůže</h3>
						<p>Popraskané paty nevznikají přes noc — a nezmizí přes noc ani po nasazení jedné masti. Zjistěte, co za nimi skutečně stojí.</p>
					</a>
					<a class="molosoc-feature-card molosoc-feature-card--cz-2" href="<?php echo esc_url( home_url( '/cz/zarostly-nehet/' ) ); ?>">
						<h3>Zarostlý nehet</h3>
						<p>Zarostlý nehet obvykle začíná u okraje nehtu, ne u kůže kolem něj — těsné boty a krátké stříhání jsou nejčastější příčinou.</p>
					</a>
					<a class="molosoc-feature-card molosoc-feature-card--cz-3" href="<?php echo esc_url( home_url( '/cz/kurici-oko/' ) ); ?>">
						<h3>Kuří oko a mozoly</h3>
						<p>Kuří oko vzniká postupně, tlakem a třením na stále stejném místě — a stejně postupně se dá i změkčit.</p>
					</a>
				</div>
			<?php else : ?>
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
			<?php endif; ?>
		</div>
	</section>

	<!-- Beat 9 — Final CTA -->
	<section class="molosoc-section molosoc-final-cta">
		<div class="molosoc-final-cta__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/3d_render_01_front_nobg.png" alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-final-cta__scrim"></div>
		<div class="molosoc-section__inner molosoc-reveal" style="text-align:center;">
			<p class="molosoc-eyebrow" style="color: rgba(255,255,255,0.6);"><?php echo esc_html( $molosoc_is_cz ? 'Alternativa, kterou můžete používat pořád dokola' : __( 'The reusable alternative', 'molosoc' ) ); ?></p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Co je hydratační návlek na nohy?' : __( 'What is a moisture-lock foot cover?', 'molosoc' ) ); ?></h2>
			<p><?php echo esc_html( $molosoc_is_cz ? 'Ne každá maska na nohy funguje stejně. Tady je ta, které Molosoc věří.' : __( "Not every foot mask works the same way. Here's the one Molosoc believes in.", 'molosoc' ) ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/navleky-na-nohy/' ) : home_url( '/foot-covers/' ) ); ?>"><?php echo esc_html( $molosoc_is_cz ? 'Zjistit jak to funguje' : __( 'See how it works', 'molosoc' ) ); ?></a>
		</div>
	</section>

</main>

<?php get_footer(); ?>
