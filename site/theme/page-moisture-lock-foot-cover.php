<?php
/**
 * Template Name: Product — Moisture-Lock Foot Cover
 *
 * Auto-selected by WordPress for any Page with the slug
 * "moisture-lock-foot-cover" (the "page-{slug}.php" convention takes
 * priority over a manually-picked template), matching the same convention
 * as page-foot-covers.php / page-cracked-heels.php.
 *
 * Ported from site/theme/preview/product-preview.html — see that file's
 * own header comment for the content/image sourcing decisions (orbit
 * scroll-drawer reverted to a static block, editorial image treatment,
 * proof-block/how-block background media, etc.). Locked copy source:
 * content/molosoc-site/03-product/product-copy.md.
 *
 * Like page-foot-covers.php / page-cracked-heels.php, this is a normal
 * template: get_header()/get_footer() (real site chrome, real nav menu).
 * Schema markup + meta description are hooked onto wp_head() in
 * functions.php (molosoc_product_schema()) instead of being printed here,
 * since get_header() already owns the <head> — that hook already existed
 * (gated on is_page('moisture-lock-foot-cover')) before this template
 * file did, which is why the live page was rendering the WP Page's own
 * placeholder content instead of this design: the Page existed, the
 * schema hook existed, but this template file — the thing that actually
 * replaces the_content() with the real page — never did.
 *
 * CSS/JS for this page (product.css + model-viewer only) are enqueued
 * conditionally in functions.php on is_page('moisture-lock-foot-cover').
 *
 * FULLY STATIC PAGE (2026-09-21, per explicit request): no animation of
 * any kind. The hero's molosoc-3d.glb model renders as a still — its
 * auto-rotate was removed — and no GSAP/ScrollTrigger, scroll-refresh,
 * scroll-reveal, breathing-zoom or hover-zoom motion runs anywhere on
 * the page.
 */

defined( 'ABSPATH' ) || exit;
$molosoc_is_cz = function_exists( 'pll_current_language' ) && pll_current_language() === 'cz';

get_header();
?>

<main id="main">

	<!-- Hero: H1 + lede over a STATIC render of the molosoc-3d.glb model
	     (model-viewer with no auto-rotate and no camera-controls — the
	     continuous spin this hero used to run was removed 2026-09-21 per
	     explicit request; see docs/molosoc-animation-specification.md).
	     The "cream you already own" H2's 3 H3 points sit directly below
	     as static feature cards,
	     in normal document flow — a firm static block under the hero, not
	     a glass drawer sliding in over it (that scroll-pin mechanic was
	     built, then explicitly reverted; see product.css's file-header
	     comment). No JS runs on this section at all. -->
	<section class="molosoc-orbit-section">
		<div class="molosoc-orbit-pin">

			<div class="molosoc-orbit-stage" aria-hidden="true">
				<div class="molosoc-orbit-glow"></div>
				<model-viewer
					class="molosoc-orbit-model"
					src="<?php echo esc_url( get_stylesheet_directory_uri() . '/assets/models/molosoc-3d.glb' ); ?>"
					alt=""
					camera-orbit="0deg 75deg 105%"
					exposure="0.95"
					shadow-intensity="0.7"
					shadow-softness="1"
					environment-image="neutral"
					loading="eager">
				</model-viewer>
			</div>

			<div class="molosoc-orbit-hero-copy">
				<?php
				// Editorial two-part headline (2026-09-21): the H1's text is
				// unchanged ("Návlek na nohy Molosoc" / "Molosoc Foot Cover") —
				// the two spans only let product.css set the product phrase
				// oversized and the brand word as its own tracked-out element,
				// placed around the 3D model. Span order follows each
				// language's word order; CSS grid areas do the placement.
				?>
				<h1 class="molosoc-hero-title">
					<?php if ( $molosoc_is_cz ) : ?>
						<span class="molosoc-hero-title__phrase">Návlek na nohy</span>
						<span class="molosoc-hero-title__brand">Molosoc</span>
					<?php else : ?>
						<span class="molosoc-hero-title__brand"><?php esc_html_e( 'Molosoc', 'molosoc' ); ?></span>
						<span class="molosoc-hero-title__phrase"><?php esc_html_e( 'Foot Cover', 'molosoc' ); ?></span>
					<?php endif; ?>
				</h1>
				<p><?php echo esc_html( $molosoc_is_cz ? 'Skutečné výsledky před/po, žádné filtry. Opakovaně použitelný návlek, který udrží váš oblíbený krém na místě a usnadní pravidelnou péči.' : __( 'Real before/after results, no filters. A reusable foot cover that keeps your favorite cream in place and makes regular care easier.', 'molosoc' ) ); ?></p>
			</div>

		</div>

		<!-- Sibling of .molosoc-orbit-pin, not nested inside it — see
		     product-preview.html's own comment on this block for why. -->
		<div class="molosoc-orbit-drawer">
			<div class="molosoc-orbit-drawer__top">
				<div class="molosoc-orbit-drawer__heading">
					<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Váš krém konečně dostane čas' : __( 'Your cream, finally working', 'molosoc' ) ); ?></p>
					<h2><?php echo esc_html( $molosoc_is_cz ? 'Váš krém konečně dostane čas' : __( 'Your cream, finally working', 'molosoc' ) ); ?></h2>
				</div>
				<div class="molosoc-orbit-drawer__buy">
					<?php // translate="no" on every price group/note: browser auto-translate
					      // (e.g. Chrome for Czech visitors on the EN page) garbles the
					      // currency code — "229 CZK" was observed rendered as "229 CZH".
					      // Prices and ISO codes must survive machine translation verbatim. ?>
					<span class="molosoc-price-group" translate="no">
						<span class="molosoc-orbit-drawer__price"><?php echo $molosoc_is_cz ? '229 Kč' : '€10'; ?></span>
						<?php if ( ! $molosoc_is_cz ) : ?>
							<span class="molosoc-price-note"><?php esc_html_e( 'Charged as 229 CZK at checkout.', 'molosoc' ); ?></span>
						<?php endif; ?>
					</span>
					<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/product/moisture-lock-foot-cover/' ) ); ?>"><?php echo esc_html( $molosoc_is_cz ? 'Objednat nyní' : __( 'Order Now', 'molosoc' ) ); ?></a>
				</div>
			</div>
			<div class="molosoc-orbit-drawer__cards">
				<article>
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Proč krémy často skončí v šuplíku' : __( 'Why creams end up in the drawer', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Ne vždy je problém v krému. Často je to rutina kolem něj — mastné ponožky, povlečení a péče, ke které se člověk přestane vracet.' : __( 'The problem isn\'t always the cream. Often it\'s the routine around it — greasy socks, bedsheets, and care you stop coming back to.', 'molosoc' ) ); ?></p>
				</article>
				<article>
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Méně nepořádku, jednodušší rutina' : __( 'Less mess, a simpler routine', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Návlek drží krém na chodidle a omezuje jeho otírání. Vy si jen uděláte chvíli na péči a necháte ho pracovat.' : __( 'The cover keeps the cream on your foot and stops it rubbing off. You just take a moment for the care and let it work.', 'molosoc' ) ); ?></p>
				</article>
				<article>
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Použijte krém, který už máte' : __( 'Use the cream you already have', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Molosoc není další kosmetická formule. Funguje s krémem nebo balzámem, kterému už důvěřujete.' : __( 'Molosoc isn\'t another skincare formula. It works with the cream or balm you already trust.', 'molosoc' ) ); ?></p>
				</article>
			</div>
		</div>
	</section>

	<!-- H2: Real results, no filters (Persona 2 — Ingrown-Nail/Hardened-
	     Skin Sufferer). molosoc-product-proof-block wraps the heading +
	     card grid together so a 3D render image can sit as a background
	     behind the whole block, with a white transparent scrim over it for
	     legibility — same absolute-media + __scrim layering convention as
	     category.css's .molosoc-category-hero. -->
	<div class="molosoc-product-proof-block">
		<div class="molosoc-product-proof-block__media" aria-hidden="true">
			<img src="https://molosoc.com/wp-content/uploads/2026/07/3d_turntable_04_topdown.png"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-product-proof-block__scrim"></div>
		<div class="molosoc-product-proof-block__content">
			<div class="molosoc-product-heading">
				<div class="molosoc-product-heading__inner molosoc-product-heading__inner--center">
					<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Skutečné výsledky, žádné filtry' : __( 'Real results, no filters', 'molosoc' ) ); ?></p>
					<h2><?php echo esc_html( $molosoc_is_cz ? 'Skutečné výsledky, žádné filtry' : __( 'Real results, no filters', 'molosoc' ) ); ?></h2>
				</div>
			</div>
			<section aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Skutečné výsledky, žádné filtry' : __( 'Real results, no filters', 'molosoc' ) ); ?>">
				<div class="molosoc-product-proof">
					<article class="molosoc-product-proof__card">
						<h3><?php echo esc_html( $molosoc_is_cz ? '3 měsíce mezi fotografiemi' : __( '3 months between photos', 'molosoc' ) ); ?></h3>
						<div class="molosoc-media molosoc-product-proof__media">
							<img src="https://molosoc.com/wp-content/uploads/2026/07/homepage-results-full.jpg"
								alt="<?php esc_attr_e( 'Real 3-month before/after result, no filters — full unedited comparison', 'molosoc' ); ?>"
								loading="lazy" decoding="async">
						</div>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Stejné nohy, fotografované s odstupem tří měsíců. Bez retuše a studiového osvětlení — jen pravidelná péče s krémem a návlekem.' : __( 'The same feet, photographed three months apart. No retouching, no studio lighting — just regular care with cream and a cover.', 'molosoc' ) ); ?></p>
					</article>
					<article class="molosoc-product-proof__card">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Popraskané paty v čase' : __( 'Cracked heels over time', 'molosoc' ) ); ?></h3>
						<div class="molosoc-media molosoc-product-proof__media">
							<img src="https://molosoc.com/wp-content/uploads/2026/07/Mom-Feet-cracked-heals-before-using-Molosoc.jpg"
								alt="<?php esc_attr_e( "Mom's cracked heels before using Molosoc", 'molosoc' ); ?>"
								loading="lazy" decoding="async">
						</div>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Pravidelná péče může udělat velký rozdíl. Tady vidíte skutečný výsledek při opakovaném používání — bez změny na „zázračný“ krém.' : __( 'Regular care can make a big difference. This is a real result from repeated use — without switching to a "miracle" cream.', 'molosoc' ) ); ?></p>
					</article>
					<article class="molosoc-product-proof__card">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Skutečná reakce' : __( 'A real reaction', 'molosoc' ) ); ?></h3>
						<div class="molosoc-media molosoc-product-proof__media">
							<img src="https://molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
								alt="<?php esc_attr_e( 'Nail comparison showing visible improvement, no filters', 'molosoc' ); ?>"
								loading="lazy" decoding="async">
						</div>
						<p>
							<?php echo esc_html( $molosoc_is_cz ? 'Žádný scénář ani nacvičená reakce. Jen moment, kdy si člověk všimne změny na vlastních nohou.' : __( 'No script, no rehearsed reaction. Just the moment someone notices the change in their own feet.', 'molosoc' ) ); ?>
							<a href="https://youtube.com/shorts/ajdjJg0OuYg?si=cXDSn79awbO0JLDy" target="_blank" rel="noopener noreferrer"><?php echo esc_html( $molosoc_is_cz ? 'Podívejte se na reakci →' : __( 'Watch the reaction →', 'molosoc' ) ); ?></a>
						</p>
					</article>
				</div>
			</section>
		</div>
	</div>

	<!-- H2: Make the pedicure last (Persona 3 — After-Pedicure Maintainer).
	     Photo pair and the three points below are all static — the
	     scroll-in text entrance (sequential-text-reveal.js) this section
	     used to run was removed 2026-09-21. -->
	<div class="molosoc-product-heading">
		<div class="molosoc-product-heading__inner molosoc-product-heading__inner--center">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Ať vám pocit po pedikúře vydrží déle' : __( 'Make the pedicure last', 'molosoc' ) ); ?></p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Ať vám pocit po pedikúře vydrží déle' : __( 'Make the pedicure last', 'molosoc' ) ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Ať vám pocit po pedikúře vydrží déle' : __( 'Make the pedicure last', 'molosoc' ) ); ?>">
		<div class="molosoc-argument molosoc-argument--reverse">
			<div class="molosoc-argument__media molosoc-argument__media--duo molosoc-argument__media--editorial">
				<div class="molosoc-media molosoc-media--primary molosoc-media--static">
					<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc_pedicure_01.jpg"
						alt="<?php esc_attr_e( 'Woman in cream loungewear giving herself an at-home pedicure, foot resting in a ceramic basin, minimalist bright hallway', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
				<div class="molosoc-media molosoc-media--secondary molosoc-media--static">
					<img src="https://molosoc.com/wp-content/uploads/2026/07/persona3_01_painted_nails.jpg"
						alt="<?php esc_attr_e( 'Freshly painted toenails resting on a spa towel', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
			</div>
			<div class="molosoc-argument__text">
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Péče nekončí odchodem ze salonu' : __( 'Care doesn\'t end when you leave the salon', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Po pedikúře se pokožka postupně začne znovu vysušovat. Pravidelná domácí péče pomáhá udržovat chodidla mezi návštěvami.' : __( 'After a pedicure, the skin gradually starts drying out again. Regular care at home helps keep your feet in shape between visits.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Přibližně 23 Kč za použití' : __( 'About €1 per use', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Molosoc stojí 229 Kč a vydrží alespoň 10 použití. To je méně než 23 Kč za jedno použití.' : __( 'Molosoc costs €10 and lasts at least 10 uses. That works out to about €1 per use.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Domácí péče bez další rezervace' : __( 'Home care without another booking', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Vlastní krém, návlek a chvíle pro sebe. Bez cesty do salonu a bez dalšího termínu.' : __( 'Your own cream, a cover, and a moment for yourself. No trip to the salon, no next appointment.', 'molosoc' ) ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- H2: Give it as a gift (Persona 4 — Gift Buyer). Photo pair and the
	     three points below are all static, same as above. -->
	<div class="molosoc-product-heading">
		<div class="molosoc-product-heading__inner molosoc-product-heading__inner--center">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Darujte ho dál' : __( 'Give it as a gift', 'molosoc' ) ); ?></p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Darujte ho dál' : __( 'Give it as a gift', 'molosoc' ) ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Darujte ho dál' : __( 'Give it as a gift', 'molosoc' ) ); ?>">
		<div class="molosoc-argument">
			<div class="molosoc-argument__media molosoc-argument__media--duo molosoc-argument__media--editorial">
				<div class="molosoc-media molosoc-media--primary molosoc-media--static">
					<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc_pack_gift.jpg"
						alt="<?php esc_attr_e( 'An open gift box with a pair of Molosoc foot covers, lavender oil, and dried lavender sprigs styled around it', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
				<div class="molosoc-media molosoc-media--secondary molosoc-media--static">
					<img src="https://molosoc.com/wp-content/uploads/2026/07/persona4_02_giving_gift.jpg"
						alt="<?php esc_attr_e( 'Two pairs of hands — one giving a wrapped gift to another', 'molosoc' ); ?>"
						loading="lazy" decoding="async">
				</div>
			</div>
			<div class="molosoc-argument__text">
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Pro někoho, kdo je pořád na nohou' : __( 'For someone always on her feet', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Jednoduchý dárek pro někoho, kdo na péči o sebe často nemá čas.' : __( 'A simple gift for someone who rarely has time to care for themselves.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Výsledek, který je vidět' : __( 'A result you can see', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Fotografie před a po ukazují princip lépe než dlouhé vysvětlování.' : __( 'Before-and-after photos show the idea better than a long explanation.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Jednoduché použití' : __( 'Simple to use', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Nanést vlastní krém, nasadit návlek a nechat působit. Žádná další kosmetika není potřeba.' : __( 'Apply your own cream, put on the cover, and let it work. No extra products needed.', 'molosoc' ) ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- Brand story — a compact mother-and-daughter note (2026-09-22):
	     one candid photo beside three short lines of copy, generous
	     whitespace, no card/background/CTA. Deliberately small; not an
	     About section. -->
	<section class="molosoc-product-story" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Náš příběh' : __( 'Our story', 'molosoc' ) ); ?>">
		<div class="molosoc-product-story__inner">
			<div class="molosoc-product-story__media">
				<img src="https://molosoc.com/wp-content/uploads/2026/01/Molosoc-Opening-Package-Mami.jpg"
					alt="<?php echo esc_attr( $molosoc_is_cz ? 'Máma a dcera spolu otevírají balíček Molosoc u stolu doma' : __( 'A mother and daughter opening a Molosoc package together at the table at home', 'molosoc' ) ); ?>"
					loading="lazy" decoding="async" width="1290" height="1434">
			</div>
			<div class="molosoc-product-story__text">
				<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Náš příběh' : __( 'Our story', 'molosoc' ) ); ?></p>
				<h2><?php echo esc_html( $molosoc_is_cz ? 'Vzniklo mezi mámou a dcerou' : __( 'Created by a mother and daughter', 'molosoc' ) ); ?></h2>
				<p><?php echo esc_html( $molosoc_is_cz ? 'Molosoc jsme vytvořily spolu — z jednoduché potřeby udělat každodenní péči o nohy snadnější a udržitelnou jako rutinu.' : __( 'We created Molosoc together — from a simple need to make everyday foot care easier and turn it into a routine you can actually keep.', 'molosoc' ) ); ?></p>
			</div>
		</div>
	</section>

	<!-- H2: How it works. molosoc-product-how-block wraps the
	     heading+content together so a 3D render image can sit as a
	     background behind the whole block — same pattern as
	     molosoc-product-proof-block above, just a heavier 75% white scrim
	     per the preview's own build notes. Closes with the page's purchase
	     action. -->
	<div class="molosoc-product-how-block">
		<div class="molosoc-product-how-block__media" aria-hidden="true">
			<img src="https://molosoc.com/wp-content/uploads/2026/07/3d_turntable_01_front.png"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-product-how-block__scrim"></div>
		<div class="molosoc-product-how-block__content">
			<div class="molosoc-product-heading">
				<div class="molosoc-product-heading__inner molosoc-product-heading__inner--center">
					<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Jak to funguje' : __( 'How it works', 'molosoc' ) ); ?></p>
					<h2><?php echo esc_html( $molosoc_is_cz ? 'Jak to funguje' : __( 'How it works', 'molosoc' ) ); ?></h2>
				</div>
			</div>
			<section aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Jak to funguje' : __( 'How it works', 'molosoc' ) ); ?>">
				<div class="molosoc-argument molosoc-argument--reverse">
					<div class="molosoc-argument__media molosoc-argument__media--duo">
						<div class="molosoc-media molosoc-media--primary">
							<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc_pack_env3.jpg"
								alt="<?php esc_attr_e( 'Molosoc foot covers and packaging styled on a sunlit windowsill with a plant and a glass of water', 'molosoc' ); ?>"
								loading="lazy" decoding="async">
						</div>
						<div class="molosoc-media molosoc-media--secondary molosoc-media--contain">
							<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc_product_only.jpg"
								alt="<?php esc_attr_e( 'The Molosoc foot cover shown alone with a minimal, plain background', 'molosoc' ); ?>"
								loading="lazy" decoding="async">
						</div>
					</div>
					<div class="molosoc-argument__text">
						<div class="molosoc-argument__item">
							<h3><?php echo esc_html( $molosoc_is_cz ? 'Co najdete v balení' : __( "What's in the box", 'molosoc' ) ); ?></h3>
							<p><?php echo esc_html( $molosoc_is_cz ? 'Opakovaně použitelný návlek na nohy připravený k použití s vaším vlastním krémem.' : __( 'A reusable foot cover, ready to use with your own cream.', 'molosoc' ) ); ?></p>
						</div>
						<div class="molosoc-argument__item">
							<h3><?php echo esc_html( $molosoc_is_cz ? 'Jak ho použít' : __( 'How to use it', 'molosoc' ) ); ?></h3>
							<p><?php echo esc_html( $molosoc_is_cz ? 'Naneste krém, nasaďte návlek a nechte působit 30–60 minut. Potom návlek opláchněte a nechte uschnout.' : __( 'Apply your cream, put on the cover, and leave it on for 30–60 minutes. Then rinse the cover and let it dry.', 'molosoc' ) ); ?></p>
						</div>
						<div class="molosoc-argument__item">
							<h3><?php echo esc_html( $molosoc_is_cz ? 'Použijte znovu' : __( 'Use it again', 'molosoc' ) ); ?></h3>
							<p><?php echo esc_html( $molosoc_is_cz ? 'Jeden návlek vydrží alespoň 10 použití a při správné péči může vydržet déle.' : __( 'One cover lasts at least 10 uses, and with proper care it can last longer.', 'molosoc' ) ); ?></p>
						</div>
					</div>
				</div>
				<div class="molosoc-product-buy">
					<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/product/moisture-lock-foot-cover/' ) ); ?>"><?php echo esc_html( $molosoc_is_cz ? 'Objednat nyní — 229 Kč' : __( 'Order Now — €10', 'molosoc' ) ); ?></a>
					<?php if ( ! $molosoc_is_cz ) : ?>
						<p class="molosoc-price-note" translate="no"><?php esc_html_e( 'Charged as 229 CZK at checkout.', 'molosoc' ); ?></p>
					<?php endif; ?>
				</div>
			</section>
		</div>
	</div>

</main>

<!-- Sticky mobile buy bar — see product.css for why this exists only at
     mobile widths. -->
<div class="molosoc-sticky-buy">
	<span class="molosoc-price-group" translate="no">
		<span class="molosoc-sticky-buy__price"><?php echo $molosoc_is_cz ? '229 Kč' : '€10'; ?></span>
		<?php if ( ! $molosoc_is_cz ) : ?>
			<span class="molosoc-price-note"><?php esc_html_e( 'Charged as 229 CZK at checkout.', 'molosoc' ); ?></span>
		<?php endif; ?>
	</span>
	<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/product/moisture-lock-foot-cover/' ) ); ?>"><?php echo esc_html( $molosoc_is_cz ? 'Objednat nyní' : __( 'Order Now', 'molosoc' ) ); ?></a>
</div>

<?php get_footer(); ?>
