<?php
/**
 * Template Name: Pillar 1 — Cracked Heels
 *
 * Auto-selected by WordPress for any Page with the slug "cracked-heels"
 * (the "page-{slug}.php" convention takes priority over a manually-picked
 * template), matching the same convention as page-foot-covers.php.
 *
 * Ported from site/theme/preview/cracked-heels-preview.html — see that
 * file's own header comment for the content/image sourcing, and
 * docs/site-structure.md §7 "Pillar 1 — Cracked Heels" for how this
 * page's headings map to verified keyword data. Locked copy source:
 * content/molosoc-site/04-pillar1-cracked-heels/pillar1-cracked-heels-copy.md.
 *
 * Like page-foot-covers.php, this is a normal template: get_header()/
 * get_footer() (real site chrome, real nav menu). Schema markup + meta
 * description are hooked onto wp_head() in functions.php
 * (molosoc_pillar1_schema()) instead of being printed here, since
 * get_header() already owns the <head>.
 *
 * CSS for this page (pillar1.css) is enqueued in
 * functions.php's shared Journal-article branch. No motion scripts are
 * loaded: the only motion is the hero photo's pure-CSS breathing zoom;
 * every section below it is static (2026-09-22).
 */

defined( 'ABSPATH' ) || exit;
$molosoc_is_cz = function_exists( 'pll_current_language' ) && pll_current_language() === 'cz';

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. H1 + locked lede over
	     pillar1_01_heels_floor.jpg (assets/molosoc-image-assets.csv:
	     "Pillar 1 Cracked Heels / Hero"). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://molosoc.com/wp-content/uploads/2026/07/pillar1_01_heels_floor.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Popraskané paty' : __( 'Cracked heels', 'molosoc' ) ); ?></p>
			<h1><?php echo esc_html( $molosoc_is_cz ? 'Popraskané paty: co se skutečně děje a co pomáhá' : __( "Cracked heels: what's really going on, and what helps", 'molosoc' ) ); ?></h1>
			<p><?php echo esc_html( $molosoc_is_cz ? 'Popraskané paty vznikají, když kůže ztratí schopnost se natahovat pod tlakem — nejde o smůlu ani jen o "suchou kůži." Náprava je jednoduchá, pokud je pravidelná, ne příležitostná.' : __( 'Cracked heels happen when skin loses the elasticity to stretch under pressure — not from bad luck, and not from "just dry skin." The fix is straightforward once it\'s consistent, not occasional.', 'molosoc' ) ); ?></p>
		</div>
	</section>

	<!-- 2. WHAT CAUSES CRACKED HEELS — static fixed image + text column. The
	     photo and the 3 H3 points sit at rest (the old fixed-image-text-reveal
	     entrance was removed 2026-09-22 — the only motion on this page is the
	     hero breathe). -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Příčiny' : __( 'The causes', 'molosoc' ) ); ?></p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Popraskané paty příčina' : __( 'What causes cracked heels', 'molosoc' ) ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Popraskané paty příčina' : __( 'What causes cracked heels', 'molosoc' ) ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://molosoc.com/wp-content/uploads/2026/07/pillar1_02_bed_checking.jpg"
							alt="<?php esc_attr_e( 'Person checking their heel, seated on the edge of a bed', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Suchá kůže ztrácí schopnost se natahovat' : __( "Dry skin losing its ability to stretch", 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Kůže na patě praská, když vyschne a ztratí pružnost potřebnou k natahování pod tlakem.' : __( 'Heel skin cracks when it dries out and loses the elasticity it needs to stretch under pressure.', 'molosoc' ) ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Tlak a zátěž na okraji paty' : __( 'Pressure and weight-bearing on the heel edge', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Vnější okraj paty nese při každém kroku nejvíc váhy — suchá, nepružná kůže na tomto místě praská jako první.' : __( "The heel's outer edge carries the most weight with every step — dry, inflexible skin can't take that pressure without splitting.", 'molosoc' ) ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Celodenní stání, hlavně v otevřené obuvi' : __( 'Standing all day, especially in open-back shoes', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Dlouhé celodenní stání a boty s otevřenou patou zrychlují oba problémy najednou: víc tlaku, víc ztráty vlhkosti.' : __( 'Standing for long stretches in open-back shoes speeds up both problems at once: more pressure, more moisture loss.', 'molosoc' ) ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. WHEN CRACKED HEELS GO FROM DRY TO PAINFUL — static photo + cards.
	     Image B is the plain background and the 3 cards sit at their final
	     tiered positions (the old editorial-feature-reveal mask + card flight
	     was removed 2026-09-22; Image A stays in the markup, hidden by
	     pillar1.css). -->
	<section class="molosoc-severity-section" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Když suché paty začnou bolet' : __( 'When dry heels start to hurt', 'molosoc' ) ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://molosoc.com/wp-content/uploads/2026/07/pillar3_03_texture.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://molosoc.com/wp-content/uploads/2026/07/pillar1_03_sandals.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Když se to zhorší' : __( 'When it gets serious', 'molosoc' ) ); ?></p>
				<h2><?php echo esc_html( $molosoc_is_cz ? 'Když suché paty začnou bolet' : __( 'When dry heels start to hurt', 'molosoc' ) ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Bolestivé hluboké praskliny na patách' : __( 'Painful deep cracked heels', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Prasklina, která bolí při každém kroku, už překonala povrchové sucho a zasahuje hlubší vrstvu kůže.' : __( "A crack that hurts with every step has gone past surface dryness into a deeper layer of skin.", 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Vážně popraskané paty' : __( 'Severe cracked heels', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Vážně popraskané paty se rozšiřují, prohlubují a mohou krvácet — příležitostné mazání krémem v této fázi nestačí.' : __( "Severe cracked heels widen, deepen, and can bleed — an occasional cream application isn't enough at this stage.", 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Proč "jen víc mazat" v této fázi přestává fungovat' : __( 'Why "just moisturizing more" stops working at this stage', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Krém, který není zapečetěný na kůži, se otře dřív, než se vstřebá — víc produktu to nevyřeší, potřeba je delší kontakt.' : __( "Cream that isn't sealed against skin rubs off before it's absorbed — more product doesn't fix that, more contact time does.", 'molosoc' ) ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. WHY MOISTURIZER ALONE DOESN'T FIX IT — static glass drawer settled
	     over the static still of the Molosoc model (molosoc-hero-still.webp, Issue #149:
	     the model-viewer render of molosoc-3d.glb was dropped for mobile speed) (the old orbit-
	     scroll-drawer fade/blur/slide and the model's auto-rotate were removed
	     2026-09-22). -->
	<section class="molosoc-mechanism-section" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Proč samotné mastění problém nevyřeší' : __( "Why moisturizer alone doesn't fix it", 'molosoc' ) ); ?>">
		<div class="molosoc-mechanism-pin">

			<div class="molosoc-mechanism-stage" aria-hidden="true">
				<div class="molosoc-mechanism-glow"></div>
				<img
					class="molosoc-mechanism-model"
					src="https://molosoc.com/wp-content/uploads/2026/10/molosoc-hero-still.webp"
					alt=""
					width="1440"
					height="1440"
					loading="lazy"
					decoding="async">
			</div>

			<div class="molosoc-mechanism-drawer">
				<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Skutečné řešení' : __( 'The real fix', 'molosoc' ) ); ?></p>
				<h2><?php echo esc_html( $molosoc_is_cz ? 'Proč samotné mastění problém nevyřeší' : __( "Why moisturizer alone doesn't fix it", 'molosoc' ) ); ?></h2>
				<p><?php echo esc_html( $molosoc_is_cz ? 'Většina lidí už mast na paty vlastní a pravidelně ji nanáší — samotná rutina není to, co chybí.' : __( 'Most people already own a foot cream and already apply it — the routine itself was never the problem.', 'molosoc' ) ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Rutina, kterou už většina lidí zkouší' : __( 'The routine most people already try', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Většina lidí už mast na paty vlastní a pravidelně ji nanáší — samotná rutina není to, co chybí.' : __( 'Most people already own a foot cream and already apply it — the routine itself was never the problem.', 'molosoc' ) ); ?></p>
					</article>
					<article>
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Kde se rutina rozpadá' : __( 'Where that routine breaks down', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Mast se otře na ponožky nebo podlahu během pár minut, takže se většina z ní nikdy nestihne vstřebat.' : __( 'Cream rubs off onto socks or sheets within minutes, so most of it never gets absorbed.', 'molosoc' ) ); ?></p>
					</article>
					<article>
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Co je skutečně potřeba, aby mast/krém fungovaly' : __( 'What actually needs to happen for cream to work', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Mast potřebuje nepřerušovaný kontakt s kůží, aby fungovala — ne silnější vrstvu, jen dost času zapečetěného na kůži, aby se skutečně vstřebala.' : __( 'Cream needs uninterrupted contact with skin to work — not a bigger dose, just enough sealed time to actually absorb.', 'molosoc' ) ); ?>
						<?php if ( $molosoc_is_cz ) : ?>
							<a href="<?php echo esc_url( home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) ); ?>">Jak funguje hydratační návlek na nohy na krém, který už máte</a>.
						<?php endif; ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- 4a. CZ ONLY — further causes, practical care and physician guidance
	     (Issue #243). Complements the 3 cause points in section 2 and avoids
	     the generic wash/dry/cream routine owned by
	     /cz/sucha-kuze-na-chodidlech/. No links (related links + CTA below). -->
	<?php if ( $molosoc_is_cz ) : ?>
	<section class="molosoc-section molosoc-pillar-dry-skin molosoc-pillar-causes-care" aria-label="Další příčiny popraskaných pat a co s nimi">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow">Příčiny a péče</p>
			<h2>Další příčiny popraskaných pat</h2>
			<p>Kromě sucha, tlaku a dlouhého stání se na popraskaných patách často podílí i ztluštělá, ztvrdlá kůže na okraji paty, která se při zátěži hůř natahuje, a také obuv bez opory paty, například pantofle nebo sandály. S věkem navíc kůže přirozeně ztrácí pružnost.</p>
			<p>Někdy za praskáním stojí i zdravotní důvod, například kožní onemocnění, plísňová infekce nebo cukrovka. Pokud paty praskají opakovaně i při pravidelné péči, stojí za to to s lékařem nebo lékárníkem probrat.</p>

			<h2>Co na prasklé paty</h2>
			<p>Základem je pravidelná péče o suchou kůži — podrobně ji popisujeme v článku o suché kůži na chodidlech. U popraskaných pat navíc pomáhá:</p>
			<ul>
				<li>nechat okraje prasklin na pokoji — kůži nerozdírejte, neodřezávejte ani neodtrhávejte,</li>
				<li>ztvrdlou kůži případně jen jemně zjemnit po koupeli, bez tlaku a nikdy až do bolesti nebo krve,</li>
				<li>nosit obuv, která patu drží, a doma ponožky místo bosých chodidel na tvrdé podlaze,</li>
				<li>dát kůži čas — praskliny se obvykle nezlepší ze dne na den, rozhoduje pravidelnost.</li>
			</ul>

			<h2>Kdy nečekat a jít k lékaři</h2>
			<p>Praskliny, které jsou hluboké, krvácejí, vypadají zanícené nebo se nehojí, řešte s lékařem. Zvlášť opatrní by měli být lidé s cukrovkou, poruchou prokrvení dolních končetin nebo oslabenou imunitou — u nich se s lékařem poraďte hned, jakmile se na patě objeví prasklina.</p>
		</div>
	</section>
	<?php endif; ?>

	<!-- 4b. CZ ONLY — dry skin on heels/feet + FAQ (Issue #218, R1 of
	     docs/cz-organic-growth-207.md). Plain text on existing section
	     styles; no product link here (the single contextual link lives in
	     section 4, the CTA at the bottom). No FAQ schema: out of scope. -->
	<?php if ( $molosoc_is_cz ) : ?>
	<section class="molosoc-section molosoc-pillar-dry-skin" aria-label="Suchá kůže na patách a chodidlech">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow">Suchá kůže</p>
			<h2>Suchá kůže na patách a chodidlech</h2>
			<p>Kůže na chodidlech nemá mazové žlázy a při chůzi je pod stálým tlakem, proto vysychá snáz než kůže jinde na těle. Suchá kůže na patách bývá matná, drsná nebo se šupinatí a při dalším vysychání se může začít trhat. Pomáhá pravidelná péče: mytí vlažnou vodou, důkladné osušení, krém na nohy nanášený pravidelně a dost času, aby se krém na kůži udržel.</p>
			<p>Pokud suchá kůže přetrvává i přes pravidelnou péči, svědí, zarudne nebo se výrazně zhoršuje, nechte si poradit u lékaře nebo lékárníka — příčinou může být i jiné onemocnění kůže.</p>

			<h2>Časté otázky o popraskaných patách</h2>
			<div class="molosoc-pillar-faq">
				<h3>Jak často natírat paty krémem?</h3>
				<p>Nejlépe pravidelně, tedy alespoň jednou denně, ideálně večer po umytí a osušení nohou. Při velmi suché kůži můžete krém nanést i dvakrát denně. Důležitější než množství je pravidelnost — příležitostné mazání obvykle nestačí.</p>
				<h3>Pomáhá krém na nohy přes noc?</h3>
				<p>Přes noc má krém dlouhý klidný čas, aby se vstřebával, a neotře se hned o podlahu ani obuv. Proto mnoho lidí natírá paty večer a chrání je přes noc, aby se krém neotíral do ložního prádla. Výsledek se liší podle stavu kůže.</p>
				<h3>Kdy s popraskanými patami k lékaři?</h3>
				<p>Pokud jsou praskliny hluboké, krvácejí, bolí při každém kroku, vypadají zanícené (zarudnutí, otok, teplo, hnis) nebo se nehojí, neléčte je sami a objednejte se k lékaři. Text slouží jen jako obecná informace a nenahrazuje vyšetření.</p>
			</div>
		</div>
	</section>
	<?php endif; ?>

	<!-- 5. GO DEEPER — static, reuses components.css's .molosoc-topic-grid/
	     .molosoc-topic-card ("educational content beat"). Spoke articles
	     nested under this pillar (docs/site-structure.md §7/§8) — links
	     resolve once each spoke page is built. -->
	<?php if ( ! $molosoc_is_cz ) : ?>
	<section class="molosoc-section molosoc-section--bg-cream molosoc-pillar-go-deeper" aria-label="<?php esc_attr_e( 'Go deeper', 'molosoc' ); ?>">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow"><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></p>
			<h2><?php esc_html_e( 'Go deeper', 'molosoc' ); ?></h2>
			<div class="molosoc-topic-grid">
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/cracked-heels/cracked-heels-cream/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc_cracked_heels_05.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Cracked heels cream', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'What actually matters in a cracked-heel cream, and why even a good one fails without the right routine.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/cracked-heels/fix-permanently/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc_cracked_heels_03.jpg"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'How to fix cracked heels permanently', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'Why cracked heels come back after healing once, and what stops the cycle.', 'molosoc' ); ?></p>
				</a>
				<a class="molosoc-topic-card" href="<?php echo esc_url( home_url( '/cracked-heels/cracked-heels-treatment/' ) ); ?>">
					<div class="molosoc-topic-card__media molosoc-media">
						<img src="https://molosoc.com/wp-content/uploads/2026/07/molosoc-6a6c3e786c068.png"
							alt="" loading="lazy" decoding="async">
					</div>
					<h3><?php esc_html_e( 'Cracked heels treatment', 'molosoc' ); ?></h3>
					<p><?php esc_html_e( 'The full picture beyond cream alone — what real treatment requires, step by step.', 'molosoc' ); ?></p>
				</a>
			</div>
		</div>
	</section>
	<?php endif; ?>

	<?php molosoc_related_links( 'cracked-heels' ); ?>

	<!-- FINAL CTA — deep-links to the Product page's "Real results, no
	     filters" H2 (Persona 2), per docs/site-structure.md §7's own
	     "Deep-links to" note for Pillar 1. -->
	<section class="molosoc-section molosoc-pillar-final-cta">
		<div class="molosoc-pillar-final-cta__card">
			<div class="molosoc-pillar-final-cta__media">
				<img src="https://molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
					alt="" loading="lazy" decoding="async">
			</div>
			<div class="molosoc-pillar-final-cta__copy">
				<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Podívejte se na skutečné výsledky' : __( 'See the real results', 'molosoc' ) ); ?></p>
				<h2><?php echo esc_html( $molosoc_is_cz ? 'Výsledky před/po, žádné filtry' : __( 'Before/after results, no filters', 'molosoc' ) ); ?></h2>
				<p><?php echo esc_html( $molosoc_is_cz ? 'Skutečné popraskané paty, zahojené díky pravidelné péči — ne jednorázovému nanesení.' : __( 'Real cracked heels, healed through consistent care — not a one-time application.', 'molosoc' ) ); ?></p>
				<a class="molosoc-btn" href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) : home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php echo esc_html( $molosoc_is_cz ? 'Skutečné výsledky, žádné filtry' : __( 'See real results, no filters', 'molosoc' ) ); ?></a>
			</div>
		</div>
	</section>

</main>


<?php get_footer(); ?>
