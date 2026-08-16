<?php
/**
 * Template Name: Category — Reusable Foot Covers
 *
 * Auto-selected by WordPress for any Page with the slug "foot-covers" (the
 * "page-{slug}.php" convention takes priority over a manually-picked
 * template), and also selectable by name from the Page editor if the slug
 * ever changes. Ported from site/theme/preview/category-preview.html —
 * see that file's own header comment and docs/wp-build-spec.md's
 * "CATEGORY PAGE" section for the content/structure source, and
 * docs/homepage-story-mapping.md-style docs/skills/
 * Fixed-Image-Sequential-Text-Reveal.md for the three scroll-gated
 * sections' mechanics.
 *
 * Unlike front-page.php, this is a normal template: it calls
 * get_header()/get_footer() (real site chrome, real nav menu — see
 * header.php/footer.php) rather than building its own <head>/<body>.
 * Schema markup + meta description are hooked onto wp_head() in
 * functions.php (molosoc_category_schema()) instead of being printed here,
 * since get_header() already owns the <head>.
 *
 * CSS/JS for this page (category.css, sequential-text-reveal.js,
 * who-reveal.js, GSAP+ScrollTrigger, scroll-refresh.js) are enqueued
 * conditionally in functions.php on is_page('foot-covers').
 */

defined( 'ABSPATH' ) || exit;

$molosoc_img = get_stylesheet_directory_uri() . '/assets/images/';
$molosoc_is_cz = function_exists( 'pll_current_language' ) && pll_current_language() === 'cz';

get_header();
?>

<main id="main">

	<!-- Hero — H1 + locked lede from category-copy.md, product cutout per
	     assets/molosoc-image-assets.csv ("FLEXIBLE ASSET... hero banners").
	     Motion decoration (rings/labels/baseline, type-in headline reveal)
	     adapted from nexu-io/open-design's "motion-frames" template,
	     re-themed to this site's own tokens/copy — see category.css for
	     the full note. -->
	<section class="molosoc-category-hero">
		<div class="molosoc-category-hero__media" aria-hidden="true">
			<img src="https://molosoc.com/wp-content/uploads/2026/07/3d_turntable_01_mirror.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-category-hero__scrim" aria-hidden="true"></div>

		<div class="molosoc-hero-motion" aria-hidden="true">
			<div class="molosoc-hero-motion__rings">
				<div class="molosoc-hero-motion__ring"></div>
				<div class="molosoc-hero-motion__ring molosoc-hero-motion__ring--2"></div>
				<div class="molosoc-hero-motion__ring molosoc-hero-motion__ring--3"></div>
				<div class="molosoc-hero-motion__labels">
					<span class="molosoc-hero-motion__label--1"><?php echo esc_html( $molosoc_is_cz ? 'Uzamyká vlhkost' : __( 'Moisture-lock', 'molosoc' ) ); ?></span>
					<span class="molosoc-hero-motion__label--2"><?php echo esc_html( $molosoc_is_cz ? 'Opakované použití' : __( 'Reusable', 'molosoc' ) ); ?></span>
					<span class="molosoc-hero-motion__label--3"><?php echo esc_html( $molosoc_is_cz ? 'S jakýmkoli krémem' : __( 'Cream-agnostic', 'molosoc' ) ); ?></span>
					<span class="molosoc-hero-motion__label--4"><?php echo esc_html( $molosoc_is_cz ? 'Méně nepořádku' : __( 'Less mess', 'molosoc' ) ); ?></span>
				</div>
			</div>
		</div>
		<div class="molosoc-hero-motion__baseline" aria-hidden="true"></div>

		<div class="molosoc-category-hero__text">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Alternativa na opakované použití' : __( 'The reusable alternative', 'molosoc' ) ); ?></p>
			<h1><?php echo esc_html( $molosoc_is_cz ? 'Návleky na nohy, které zadrží vlhkost — ne jen jednou' : __( 'Reusable foot covers that lock moisture in — not just once', 'molosoc' ) ); ?></h1>
			<p class="molosoc-section__lede"><?php echo esc_html( $molosoc_is_cz ? 'Většina masek na nohy v obchodě je na jedno použití. Návlek od Molosoc je na stovky.' : __( "Most foot masks on the shelf are built for one wear. Molosoc's cover is built for hundreds.", 'molosoc' ) ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) : home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php echo esc_html( $molosoc_is_cz ? 'Poznejte návlek na nohy' : __( 'Meet the Foot Cover', 'molosoc' ) ); ?></a>
		</div>
	</section>

	<!-- H2: Disposable sock masks vs. reusable foot covers — photo stays
	     fixed/static in place; each of the three points slides in from the
	     right, one per scroll step, starting with the first scroll into
	     the section. See assets/js/sequential-text-reveal.js and
	     docs/skills/Fixed-Image-Sequential-Text-Reveal.md. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Alternativa' : __( 'The alternative', 'molosoc' ) ); ?></p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Jednorázové ponožkové masky vs. návleky na opakované použití' : __( 'Disposable sock masks vs. reusable foot covers', 'molosoc' ) ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Jednorázové ponožkové masky vs. návleky na opakované použití' : __( 'Disposable sock masks vs. reusable foot covers', 'molosoc' ) ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media molosoc-media--static">
						<img src="https://molosoc.com/wp-content/uploads/2026/07/Disposable-Foot-masks-versus-reusable-Molosoc.png"
							alt="<?php echo esc_attr( $molosoc_is_cz ? 'Srovnání jednorázové masky na nohy vedle sebe s opakovaně použitelným návlekem Molosoc' : __( 'Side-by-side comparison of a disposable single-use foot mask versus the reusable Molosoc foot cover', 'molosoc' ) ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Co je skutečně uvnitř jednorázové ponožkové masky' : __( "What's actually inside a single-use sock mask", 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Předplněná ponožková maska přichází s vlastní, pevně danou formulí — použijete ji jednou a maska i formule společně skončí v koši. Pro jeden večer pohodlné, ale cena se s každým dalším použitím opakuje od nuly.' : __( 'A pre-filled sock mask comes pre-loaded with its own formula — you use it once, and both the formula and the sock go in the bin together. Convenient for a single night, but the formula is fixed and the cost resets every time.', 'molosoc' ) ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Proč opakované použití mění celou matematiku' : __( 'Why reusable changes the math', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Návlek na opakované použití odděluje dvě věci, které jednorázová maska spojuje: samotný návlek a krém uvnitř. Vypláchněte ho, naplňte tím, co už doma máte, a použijte znovu — cena jednoho použití klesá, místo aby se s každým večerem opakovala.' : __( "A reusable cover separates the two things a disposable mask bundles together: the cover itself, and the cream inside it. Wash it, refill it with whatever you're already using, and use it again — the cost of a single session drops instead of repeating every time.", 'molosoc' ) ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Jeden návlek, jakýkoli krém — ne uzamčený v předplněné formuli' : __( 'One cover, any cream — not locked to a pre-filled formula', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Jednorázová maska vás uzamkne do formule, se kterou přišla. Molosoc ne — funguje s krémem, který už máte v koupelně, ať je to levnější balzám nebo něco dražšího. Návlek zajistí uzamčení vlhkosti, výběr krému zůstává na vás.' : __( "A disposable mask locks you into whatever formula it shipped with. Molosoc doesn't — it works with the cream already in your drawer, whether that's a drugstore balm or something you paid more for. The cover does the locking-in; the cream is entirely your choice.", 'molosoc' ) ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- H2: What "moisture-lock" actually means — photo stays fixed/static
	     in place; each of the three points slides in from the left, one
	     per scroll step, starting with the first scroll into the section.
	     See assets/js/sequential-text-reveal.js and
	     docs/skills/Fixed-Image-Sequential-Text-Reveal.md. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Mechanismus' : __( 'The mechanism', 'molosoc' ) ); ?></p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Co skutečně znamená "hydratační"' : __( 'What "moisture-lock" actually means', 'molosoc' ) ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="left" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Co skutečně znamená "hydratační"' : __( 'What "moisture-lock" actually means', 'molosoc' ) ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument molosoc-argument--reverse">
				<div class="molosoc-argument__media">
					<div class="molosoc-media molosoc-media--static molosoc-media--justify-right">
						<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc_disposable_mask_editorial.jpg"
							alt="<?php esc_attr_e( 'A foot inside a clear single-use plastic sock mask, cream visibly pooled inside, stepping onto a wool rug in front of a wooden stool with a folded towel', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Jak těsnění zadrží vlhkost na kůži' : __( 'How the seal traps moisture against skin', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Krém nanesený a ponechaný na vzduchu ztrácí účinek už během pár minut — většina z něj skončí na ponožkách nebo prostěradle dřív, než se stihne vstřebat. Návlek zapečetí krém přímo na kůži po dobu použití, takže se ho vstřebá výrazně víc.' : __( "Cream applied and left open to air starts losing its effect within minutes — most of it ends up on socks or sheets before it's absorbed. A moisture-lock cover seals the cream directly against skin for the length of the session, so more of it actually goes in instead of rubbing off.", 'molosoc' ) ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Proč nepořádek a klouzání obvykle zabijí rutinu' : __( 'Why mess and slipping usually kill the routine', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Nejčastější důvod, proč rutina s krémem na nohy skončí, není samotný krém — je to nepořádek. Mastné povlečení, kluzká podlaha a ponožka, která nedrží, jsou obvykle ten skutečný důvod, proč lidé potichu přestanou krém používat.' : __( "The most common reason a foot cream routine stops isn't the cream — it's the mess. Slippery floors, greasy sheets, and a sock that won't stay put make people quietly stop reaching for it. A sealed cover removes that friction, which is usually the actual reason routines don't survive past the first week.", 'molosoc' ) ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Funguje s jakýmkoli krémem, záměrně' : __( 'Cream-agnostic, by design', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Molosoc není navržen na jednu konkrétní formuli — je navržen tak, aby fungoval s tím, čemu už důvěřujete. Je to záměr: cílem není prodat nový krém, ale konečně nechat fungovat ten, který už máte.' : __( "Molosoc isn't formulated to work with one specific cream — it's designed to work with whichever one you already trust. That's a deliberate choice: the goal isn't to sell a new formula, it's to make the one you already own finally do its job.", 'molosoc' ) ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- H2: Reusable vs. disposable: the real cost — headline shows first;
	     each of the three cost points rises in from the bottom, one per
	     scroll step, starting with the first scroll into the section. See
	     assets/js/sequential-text-reveal.js and
	     docs/skills/Fixed-Image-Sequential-Text-Reveal.md (no fixed image
	     in this instance — the pattern works with or without one). -->
	<div class="molosoc-sequential-heading molosoc-sequential-heading--clear">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Skutečná cena' : __( 'The real cost', 'molosoc' ) ); ?></p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Opakované použití vs. jednorázové: skutečná cena' : __( 'Reusable vs. disposable: the real cost', 'molosoc' ) ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage molosoc-sequential-stage--clear" data-slide-direction="up" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Opakované použití vs. jednorázové: skutečná cena' : __( 'Reusable vs. disposable: the real cost', 'molosoc' ) ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-pillars molosoc-cost-grid">
				<div class="molosoc-pillar molosoc-sequential-entrance--text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Cena za použití během měsíce' : __( 'Cost per use over a month', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Návlek Molosoc stojí 229 Kč a vydrží alespoň 10 použití — při pravidelném používání dvakrát týdně tak jedno balení pokryje celý měsíc za méně než 23 Kč na použití. Jednorázová maska se musí kupovat znovu při každém dalším použití.' : __( 'Using a twice-weekly routine as an example: a Molosoc cover costs €10 and holds up for at least 10 uses — so across a month of regular use (roughly 8 sessions), that €10 covers the entire month, working out to under €1.50 per session. A disposable sock mask, priced $6–10, is a new purchase every single time — the same 8 sessions cost $48–80 in disposables alone.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-pillar molosoc-sequential-entrance--text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Cena za použití během roku' : __( 'Cost per use over a year', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Při stejném tempu (přibližně 96 použití za rok) vychází Molosoc, vyměňovaný každých 10 použití, na přibližně 1 900 Kč ročně. Jednorázové masky se musí dokupovat znovu s každým balením — u stejného počtu použití je celková částka výrazně vyšší.' : __( "Stretched across a year at the same twice-weekly pace (roughly 96 sessions), a Molosoc cover — replaced every 10 uses at €10 each — comes to around €100 for the year. The same 96 sessions in disposable masks, at $6–10 each, adds up to $576–960. The gap isn't a marketing number — it's the same €10 cover, reused instead of rebought.", 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-pillar molosoc-sequential-entrance--text">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Za co už neplatíte (opakované návštěvy salonu)' : __( "What you're not paying for anymore (salon touch-ups)", 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Výsledek z pedikúry vyprchá během dní až dvou týdnů. Udržet ho doma s návlekem na opakované použití stojí zlomek toho, co jedna další návštěva salonu — úspora není jen v návleku oproti masce, ale hlavně v cestách do salonu, které už nemusíte podnikat.' : __( "A salon pedicure fades within days to a couple of weeks. Maintaining that result at home with a €10 reusable cover costs a fraction of what a single repeat salon visit runs — the saving isn't just the cover versus the mask, it's the trips you stop needing to book.", 'molosoc' ) ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- H2: Who this is for — links to Product page. Editorial feature
	     reveal (see assets/js/who-reveal.js): Image A gives way to Image B
	     in the same crop via a plain circular mask, then the three persona
	     cards emerge from center to their own tiered positions. -->
	<section class="molosoc-who-section" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Pro koho je to určené' : __( 'Who this is for', 'molosoc' ) ); ?>">
		<div class="molosoc-who-section__stage">
			<div class="molosoc-who-section__media" aria-hidden="true">
				<div class="molosoc-who-section__bg molosoc-who-section__bg--b" style="background-image: url('https://molosoc.com/wp-content/uploads/2026/07/molosoc_pedicure_relaxing.jpg');"></div>
				<div class="molosoc-who-section__bg molosoc-who-section__bg--a" style="background-image: url('https://molosoc.com/wp-content/uploads/2026/07/hero_collection_03_relaxing-scaled.jpg');"></div>
			</div>
			<div class="molosoc-who-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-who-section__heading">
				<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Pro koho je to určené' : __( 'Who this is for', 'molosoc' ) ); ?></p>
				<h2><?php echo esc_html( $molosoc_is_cz ? 'Pro koho je to určené' : __( 'Who this is for', 'molosoc' ) ); ?></h2>
			</div>

			<div class="molosoc-who-cards">
				<a class="molosoc-who-card molosoc-who-card--1" href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) : home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Už máte oblíbený krém' : __( 'Already have a cream you love', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Pokud už máte krém, kterému věříte, tohle je způsob, jak ho konečně nechat fungovat tak, jak měl od začátku.' : __( "If there's already a cream in your routine that you trust, this is how you make it actually work the way it was supposed to.", 'molosoc' ) ); ?></p>
				</a>
				<a class="molosoc-who-card molosoc-who-card--2" href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) : home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Právě jste byli na pedikúře a chcete, aby vydržela' : __( 'Just had a pedicure and want it to last', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Čerstvá pedikúra začíná vyprchávat téměř okamžitě. Návlek na opakované použití je způsob, jak si výsledek prodloužit bez další rezervace v salonu.' : __( 'A fresh pedicure starts fading almost immediately. A reusable cover is how you stretch that result without booking another appointment.', 'molosoc' ) ); ?></p>
				</a>
				<a class="molosoc-who-card molosoc-who-card--3" href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) : home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Kupujete to pro někoho jiného' : __( 'Buying this for someone else', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Pro někoho, kdo je pořád na nohou, nebo se k péči o sebe nikdy pořádně nedostane — tohle je nejjednodušší způsob, jak jí dát rutinu, u které skutečně vydrží.' : __( "For someone who's always on her feet, or who never quite gets around to taking care of her own — this is the easiest way to give her a routine that actually sticks.", 'molosoc' ) ); ?></p>
				</a>
			</div>
		</div>
	</section>

	<!-- Final CTA -->
	<section class="molosoc-section molosoc-category-final-cta">
		<div class="molosoc-category-final-cta__media" aria-hidden="true">
			<img src="https://molosoc.com/wp-content/uploads/2026/07/3d_render_01_front_nobg.png"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-category-final-cta__scrim" aria-hidden="true"></div>
		<div class="molosoc-section__inner molosoc-reveal">
			<p class="molosoc-eyebrow" style="color: rgba(255,255,255,0.6);">Molosoc</p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Poznejte návlek na vlastní kůži' : __( 'See the reusable cover for yourself', 'molosoc' ) ); ?></h2>
			<p><?php echo esc_html( $molosoc_is_cz ? 'Skutečné výsledky před/po, celý mechanismus a co přesně najdete v balení.' : __( "Real before/after results, the full mechanism, and what's actually in the box.", 'molosoc' ) ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) : home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php echo esc_html( $molosoc_is_cz ? 'Poznejte návlek na nohy' : __( 'Meet the Foot Cover', 'molosoc' ) ); ?></a>
		</div>
	</section>

</main>

<?php get_footer(); ?>
