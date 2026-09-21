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
				<h1><?php echo esc_html( $molosoc_is_cz ? 'Návlek na nohy Molosoc' : __( 'Molosoc Foot Cover', 'molosoc' ) ); ?></h1>
				<p><?php echo esc_html( $molosoc_is_cz ? 'Skutečné výsledky před/po, žádné filtry. Opakovaně použitelný návlek, který udrží váš oblíbený krém na místě a usnadní pravidelnou péči.' : __( 'Real before/after results, not filters. The reusable foot cover that locks in your favorite cream, cuts the mess, and makes your routine actually stick.', 'molosoc' ) ); ?></p>
			</div>

		</div>

		<!-- Sibling of .molosoc-orbit-pin, not nested inside it — see
		     product-preview.html's own comment on this block for why. -->
		<div class="molosoc-orbit-drawer">
			<div class="molosoc-orbit-drawer__top">
				<div class="molosoc-orbit-drawer__heading">
					<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Krém, který už doma máte, konečně dostane čas' : __( 'The cream you already own, finally working', 'molosoc' ) ); ?></p>
					<h2><?php echo esc_html( $molosoc_is_cz ? 'Krém, který už doma máte, konečně dostane čas' : __( 'The cream you already own, finally working', 'molosoc' ) ); ?></h2>
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
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Proč krémy často skončí v šuplíku' : __( 'Why creams get abandoned halfway through', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Ne vždy je problém v krému. Často je to rutina kolem něj — mastné ponožky, povlečení a péče, ke které se člověk přestane vracet.' : __( "Almost nobody stops using a foot cream because it didn't work. They stop because there was no structure to keep going — no reason the fifth night was any different from the first, except the mess.", 'molosoc' ) ); ?></p>
				</article>
				<article>
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Méně nepořádku, jednodušší rutina' : __( 'What changes when the mess disappears', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Návlek drží krém na chodidle a omezuje jeho otírání. Vy si jen uděláte chvíli na péči a necháte ho pracovat.' : __( "Take away the greasy sheets and the sock that won't stay put, and the only thing left is a short session where the cream actually gets to do its job. That's the entire difference between a cream that gets abandoned and one that gets finished.", 'molosoc' ) ); ?></p>
				</article>
				<article>
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Použijte krém, který už máte' : __( 'Works with the cream in your drawer right now', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Molosoc není další kosmetická formule. Funguje s krémem nebo balzámem, kterému už důvěřujete.' : __( "Molosoc isn't a new formula to buy into. It's built to work with whatever's already in your bathroom — the balm you liked enough to buy, the one that's been sitting half-used. This is what finally lets it work.", 'molosoc' ) ); ?></p>
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
						<h3><?php echo esc_html( $molosoc_is_cz ? '3 měsíce mezi fotografiemi' : __( '3-month before/after', 'molosoc' ) ); ?></h3>
						<div class="molosoc-media molosoc-product-proof__media">
							<img src="https://molosoc.com/wp-content/uploads/2026/07/homepage-results-full.jpg"
								alt="<?php esc_attr_e( 'Real 3-month before/after result, no filters — full unedited comparison', 'molosoc' ); ?>"
								loading="lazy" decoding="async">
						</div>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Stejné nohy, fotografované s odstupem tří měsíců. Bez retuše a studiového osvětlení — jen pravidelná péče s krémem a návlekem.' : __( 'No retouching, no staged lighting — the same feet, photographed the same way, three months apart. Skin that was blackened and hardened around the nails healed visibly over that time, using nothing more than a cream already owned and a cover that kept it working every session.', 'molosoc' ) ); ?></p>
					</article>
					<article class="molosoc-product-proof__card">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Popraskané paty v čase' : __( 'What actually happens to cracked heels over time', 'molosoc' ) ); ?></h3>
						<div class="molosoc-media molosoc-product-proof__media">
							<img src="https://molosoc.com/wp-content/uploads/2026/07/Mom-Feet-cracked-heals-before-using-Molosoc.jpg"
								alt="<?php esc_attr_e( "Mom's cracked heels before using Molosoc", 'molosoc' ); ?>"
								loading="lazy" decoding="async">
						</div>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Pravidelná péče může udělat velký rozdíl. Tady vidíte skutečný výsledek při opakovaném používání — bez změny na „zázračný“ krém.' : __( 'Cracked heels don\'t heal because a "better" cream shows up — they heal because the same cream gets a real chance to work, session after session, instead of rubbing off before it\'s absorbed. In one case, heels that were badly cracked improved by roughly 90% through regular use — not from a different product, but from a routine that finally held.', 'molosoc' ) ); ?></p>
					</article>
					<article class="molosoc-product-proof__card">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Skutečná reakce' : __( 'Mom surprised with results', 'molosoc' ) ); ?></h3>
						<div class="molosoc-media molosoc-product-proof__media">
							<img src="https://molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
								alt="<?php esc_attr_e( 'Nail comparison showing visible improvement, no filters', 'molosoc' ); ?>"
								loading="lazy" decoding="async">
						</div>
						<p>
							<?php echo esc_html( $molosoc_is_cz ? 'Žádný scénář ani nacvičená reakce. Jen moment, kdy si člověk všimne změny na vlastních nohou.' : __( 'The real moment a mom sees and reacts to her own results after a home pedicure session — caught as it happens, not staged for it. No script, no rehearsed delivery.', 'molosoc' ) ); ?>
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
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Péče nekončí odchodem ze salonu' : __( 'Why salon results fade in ~10 days', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Po pedikúře se pokožka postupně začne znovu vysušovat. Pravidelná domácí péče pomáhá udržovat chodidla mezi návštěvami.' : __( "A fresh pedicure looks its best for about a week to ten days before dryness starts creeping back in. That's not a flaw in the salon treatment — it's just what happens once the intensive care stops.", 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Přibližně 23 Kč za použití' : __( 'Cost per use vs. another salon visit', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Molosoc stojí 229 Kč a vydrží alespoň 10 použití. To je méně než 23 Kč za jedno použití.' : __( 'A Molosoc cover costs €10 and holds up for at least 10 sessions — working out to about €1 per use. A single repeat salon visit to maintain that softness typically runs $15–30, depending on the level of pedicure. Maintaining the result at home costs a fraction of going back.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Domácí péče bez další rezervace' : __( 'Home spa, without the salon price', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Vlastní krém, návlek a chvíle pro sebe. Bez cesty do salonu a bez dalšího termínu.' : __( 'Ten to fifteen minutes with your own cream and a cover gets you most of what a touch-up appointment does, without the drive, the booking, or the bill.', 'molosoc' ) ); ?></p>
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
					<p><?php echo esc_html( $molosoc_is_cz ? 'Jednoduchý dárek pro někoho, kdo na péči o sebe často nemá čas.' : __( "For the person who's on her feet all day and never quite gets around to taking care of her own — this is the easiest way to actually give her something she'll use.", 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Výsledek, který je vidět' : __( 'One before/after photo says it all', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Fotografie před a po ukazují princip lépe než dlouhé vysvětlování.' : __( 'No explanation needed. Cracked, hardened skin on one side; soft, cared-for skin on the other. That\'s the entire pitch.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-argument__item">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Jednoduché použití' : __( 'How to gift it (simple, low-effort framing)', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Nanést vlastní krém, nasadit návlek a nechat působit. Žádná další kosmetika není potřeba.' : __( 'No assembly, no learning curve — open the box, use the cream you already have, done in one short session. The easiest self-care gift to actually hand someone and have them use.', 'molosoc' ) ); ?></p>
				</div>
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
							<p><?php echo esc_html( $molosoc_is_cz ? 'Opakovaně použitelný návlek na nohy připravený k použití s vaším vlastním krémem.' : __( 'One reusable moisture-lock foot cover, ready to use with any cream you already own — no separate formula included, no separate purchase required to get started.', 'molosoc' ) ); ?></p>
						</div>
						<div class="molosoc-argument__item">
							<h3><?php echo esc_html( $molosoc_is_cz ? 'Jak ho použít' : __( 'How to use it with any cream', 'molosoc' ) ); ?></h3>
							<p><?php echo esc_html( $molosoc_is_cz ? 'Naneste krém, nasaďte návlek a nechte působit 30–60 minut. Potom návlek opláchněte a nechte uschnout.' : __( 'Apply your cream as usual, then slip the cover on and leave it sealed for 30 to 60 minutes. That\'s the entire routine — no extra steps, no waiting overnight.', 'molosoc' ) ); ?></p>
						</div>
						<div class="molosoc-argument__item">
							<h3><?php echo esc_html( $molosoc_is_cz ? 'Použijte znovu' : __( 'Reusable — how many uses to expect', 'molosoc' ) ); ?></h3>
							<p><?php echo esc_html( $molosoc_is_cz ? 'Jeden návlek vydrží alespoň 10 použití a při správné péči může vydržet déle.' : __( 'Built to hold up for at least 10 uses before it starts to stretch, and often lasts well beyond that with normal care. Rinse it out after each session and let it dry before the next one.', 'molosoc' ) ); ?></p>
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
