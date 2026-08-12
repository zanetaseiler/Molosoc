<?php
/**
 * Template Name: Spoke 2 — Callus Remover
 *
 * Auto-selected by WordPress for any Page with the slug "callus-remover",
 * nested under the "hardened-skin-calluses" parent Page so the permalink
 * resolves to /hardened-skin-calluses/callus-remover/ — site-structure.md
 * §8, Spoke 2.
 *
 * Ported from the approved Spoke 1 template pattern
 * (site/theme/page-treatment.php). Locked copy source: content/molosoc-
 * site/10-spoke2-callus-remover/spoke2-callus-remover-copy.md.
 *
 * Same 3-section spoke shape as Spoke 1 (fixed-image-text-reveal,
 * editorial-feature-reveal, orbit-scroll-drawer), same pillar1.css/JS
 * stack, back-link to parent pillar in place of "Go deeper".
 */

defined( 'ABSPATH' ) || exit;
$molosoc_is_cz = function_exists( 'pll_current_language' ) && pll_current_language() === 'cz';

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom. Same photo Pillar 3's own "Go
	     deeper" card already uses for this spoke (molosoc_spa_treatment_04.jpg). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/molosoc_spa_treatment_04.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Kuří oko' : __( 'Callus remover', 'molosoc' ) ); ?></p>
			<h1><?php echo esc_html( $molosoc_is_cz ? 'Jak odstranit kuří oko' : __( 'Callus remover: what actually works', 'molosoc' ) ); ?></h1>
			<p><?php echo esc_html( $molosoc_is_cz ? 'Neexistuje jeden nástroj ani produkt, který kuří oko odstraní natrvalo — každá metoda, která skutečně funguje, musí následně řešit to samé: tlak, který ho způsobil.' : __( "There's no single tool or product that removes a callus for good — every method that actually works still has to deal with the same thing afterward: the pressure that caused it in the first place.", 'molosoc' ) ); ?></p>
		</div>
	</section>

	<!-- 2. WHAT ACTUALLY REMOVES HARD SKIN — fixed-image-text-reveal.
	     pillar3_02_pumice.jpg (pumice stone) stays fixed; 3 H3 methods
	     slide in from the right. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Poctivý pohled' : __( 'An honest look', 'molosoc' ) ); ?></p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Co kuří oko skutečně odstraní' : __( 'What actually removes hard skin', 'molosoc' ) ); ?></h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Co kuří oko skutečně odstraní' : __( 'What actually removes hard skin', 'molosoc' ) ); ?>">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://staging.molosoc.com/wp-content/uploads/2026/07/pillar3_02_pumice.jpg"
							alt="<?php esc_attr_e( 'Pumice stone used to file thickened skin on a foot', 'molosoc' ); ?>"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Pilování a broušení — co to řeší a co ne' : __( "Filing and pumice stones — what they do and don't fix", 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Pilování fyzicky opotřebovává vrchní vrstvu ztvrdlé kůže, což funguje na povrchové nahromadění, ale nemění tlak, kvůli kterému pod ním znovu tvrdne nová kůže.' : __( 'Filing and pumice stones physically wear down the top layer of thickened skin, which works for surface buildup but doesn\'t change the pressure causing new hardened skin to form underneath.', 'molosoc' ) ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Náplasti s kyselinou salicylovou — jak fungují a kdy jsou rizikové' : __( 'Chemical/acid removers — how they work, and the risk of overdoing it', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Náplasti s kyselinou salicylovou změkčují a chemicky rozrušují ztvrdlou kůži — účinné, ale při přílišném nebo příliš častém používání mohou podráždit i zdravou kůži kolem.' : __( 'Acid-based removers soften and break down thickened skin chemically rather than physically — effective, but overuse can irritate healthy skin around the callus, so they need to be used carefully and not more often than directed.', 'molosoc' ) ); ?></p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Proč odstranění samo o sobě problém nevyřeší natrvalo' : __( "Why removal alone doesn't stop it from coming back", 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Žádná z těchto metod neřeší tlakový bod, který kuří oko způsobil — proto se na stejném místě obvykle znovu vytvoří.' : __( "Every removal method above deals with skin that's already thickened — none of them change the pressure point that caused it, which is why the same spot tends to build back up again.", 'molosoc' ) ); ?></p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. HOW TO REMOVE THICK DEAD SKIN FROM FEET HOME REMEDY —
	     editorial-feature-reveal. pillar3_01_foot_file.jpg (Image A) gives
	     way to pillar3_03_texture.jpg (Image B) through a circular mask,
	     then the 3 cards emerge. -->
	<section class="molosoc-severity-section" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Kuří oko odstranění' : __( 'How to remove thick dead skin from feet home remedy', 'molosoc' ) ); ?>">
		<div class="molosoc-severity-section__stage">
			<div class="molosoc-severity-section__media" aria-hidden="true">
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--b" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar3_03_texture.jpg');"></div>
				<div class="molosoc-severity-section__bg molosoc-severity-section__bg--a" style="background-image: url('https://staging.molosoc.com/wp-content/uploads/2026/07/pillar3_01_foot_file.jpg');"></div>
			</div>
			<div class="molosoc-severity-section__scrim" aria-hidden="true"></div>

			<div class="molosoc-severity-section__heading">
				<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Bezpečné odstranění' : __( 'The home remedy, done safely', 'molosoc' ) ); ?></p>
				<h2><?php echo esc_html( $molosoc_is_cz ? 'Kuří oko odstranění' : __( 'How to remove thick dead skin from feet home remedy', 'molosoc' ) ); ?></h2>
			</div>

			<div class="molosoc-severity-cards">
				<div class="molosoc-severity-card molosoc-severity-card--1">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Namočení kůže před jakýmkoliv zákrokem' : __( 'Soaking first, always', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Namočení změkčí ztvrdlou kůži ještě před pilováním, což zákrok usnadní a sníží riziko, že se odstraní i zdravá kůže pod ní.' : __( 'Soaking softens thickened skin before any filing, making removal both easier and less likely to over-thin healthy skin underneath.', 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--2">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Kdy je bezpečné řešit to doma a kdy ne' : __( 'Safe filing without over-thinning the skin', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Mírné, povrchové kuří oko lze bezpečně řešit doma; cokoliv hlubšího, bolestivého nebo s náznakem infekce patří spíš k lékaři.' : __( "Filing gradually, in short sessions rather than one aggressive pass, keeps removal from going past the hardened layer into skin that isn't ready to be exposed.", 'molosoc' ) ); ?></p>
				</div>
				<div class="molosoc-severity-card molosoc-severity-card--3">
					<h3><?php echo esc_html( $molosoc_is_cz ? 'Co dělat po odstranění, aby se nevrátilo' : __( 'What actually needs to happen after removal for it to last', 'molosoc' ) ); ?></h3>
					<p><?php echo esc_html( $molosoc_is_cz ? 'Čerstvě odkrytá kůže potřebuje po zákroku pravidelnou vlhkost — odstranění bez následné péče jen znovu nastaví stejný cyklus, který kuří oko způsobil.' : __( "Freshly exposed skin needs consistent moisture afterward — removal without follow-up care just resets the same cycle that built the callus in the first place.", 'molosoc' ) ); ?></p>
				</div>
			</div>
		</div>
	</section>

	<!-- 4. HOW TO GET RID OF HARD SKIN ON FEET PERMANENTLY —
	     orbit-scroll-drawer. -->
	<section class="molosoc-mechanism-section" aria-label="<?php echo esc_attr( $molosoc_is_cz ? 'Proč se kuří oko vrací' : __( 'How to get rid of hard skin on feet permanently', 'molosoc' ) ); ?>">
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
				<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Trvale, ne jen teď' : __( 'For good, not just for now', 'molosoc' ) ); ?></p>
			</div>

			<div class="molosoc-mechanism-drawer">
				<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Proč se kuří oko vrací' : __( 'How to get rid of hard skin on feet permanently', 'molosoc' ) ); ?></p>
				<h2><?php echo esc_html( $molosoc_is_cz ? 'Proč se kuří oko vrací' : __( 'How to get rid of hard skin on feet permanently', 'molosoc' ) ); ?></h2>
				<p><?php echo esc_html( $molosoc_is_cz ? 'I po úspěšném odstranění zůstává tlak nebo tření, které kuří oko způsobilo — ať je to obuv, chůze nebo konkrétní místo zátěže — obvykle beze změny.' : __( 'Even after a successful removal, whatever repeated pressure or friction caused the callus — footwear, gait, a specific pressure point — is usually still there.', 'molosoc' ) ); ?></p>
				<div class="molosoc-mechanism-drawer__cards">
					<article>
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Tlakový bod, který ho způsobil, nikam nezmizel' : __( 'The pressure point that caused it is still there', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'I po úspěšném odstranění zůstává tlak nebo tření, které kuří oko způsobilo — ať je to obuv, chůze nebo konkrétní místo zátěže — obvykle beze změny.' : __( 'Even after a successful removal, whatever repeated pressure or friction caused the callus — footwear, gait, a specific pressure point — is usually still there.', 'molosoc' ) ); ?></p>
					</article>
					<article>
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Jednorázové odstranění není totéž co prevence' : __( "Why one-time removal isn't the same as prevention", 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Odstranění řeší to, co už tam je; nezastavuje to, aby stejné místo znovu neztvrdlo pod stejným opakovaným tlakem.' : __( "Removing hardened skin resolves what's already there; it doesn't stop the same spot from thickening again under the same repeated pressure.", 'molosoc' ) ); ?></p>
					</article>
					<article>
						<h3><?php echo esc_html( $molosoc_is_cz ? 'Co skutečně zpomaluje jeho návrat' : __( 'What actually slows the regrowth cycle', 'molosoc' ) ); ?></h3>
						<p><?php echo esc_html( $molosoc_is_cz ? 'Pravidelná vlhkost mezi jednotlivými odstraněními udržuje kůži pod tlakem pružnější, což zpomaluje, jak rychle znovu tvrdne.' : __( 'Consistent moisture between removal sessions keeps skin more flexible under pressure, which slows how quickly it thickens back up.', 'molosoc' ) ); ?></p>
					</article>
				</div>
			</div>
		</div>
	</section>

	<!-- BACK TO PILLAR -->
	<section class="molosoc-section molosoc-section--bg-cream">
		<div class="molosoc-section__inner" style="text-align:center;">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Součást širšího tématu' : __( 'Part of a bigger picture', 'molosoc' ) ); ?></p>
			<h2><a href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/kurici-oko/' ) : home_url( '/hardened-skin-calluses/' ) ); ?>">&larr; <?php echo esc_html( $molosoc_is_cz ? 'Kuří oko a mozoly' : __( 'Back to Hardened Skin & Calluses', 'molosoc' ) ); ?></a></h2>
		</div>
	</section>

	<!-- FINAL CTA — Persona 2. -->
	<section class="molosoc-section molosoc-pillar-final-cta">
		<div class="molosoc-pillar-final-cta__media" aria-hidden="true">
			<img src="https://staging.molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
				alt="" loading="lazy" decoding="async">
		</div>
		<div class="molosoc-pillar-final-cta__scrim" aria-hidden="true"></div>
		<div class="molosoc-section__inner molosoc-reveal">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Podívejte se na skutečné výsledky' : __( 'See the real results', 'molosoc' ) ); ?></p>
			<h2><?php echo esc_html( $molosoc_is_cz ? 'Výsledky před/po, žádné filtry' : __( 'Before/after results, no filters', 'molosoc' ) ); ?></h2>
			<p><?php echo esc_html( $molosoc_is_cz ? 'Časově doložené srovnání před/po ze ztvrdlé kůže, která změkla díky pravidelné péči.' : __( 'Time-stamped before/after results from hardened skin that softened through consistent care.', 'molosoc' ) ); ?></p>
			<a class="molosoc-btn" href="<?php echo esc_url( $molosoc_is_cz ? home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) : home_url( '/foot-covers/moisture-lock-foot-cover/' ) ); ?>"><?php echo esc_html( $molosoc_is_cz ? 'Skutečné výsledky, žádné filtry' : __( 'See real results, no filters', 'molosoc' ) ); ?></a>
		</div>
	</section>

</main>

<?php
get_footer();
