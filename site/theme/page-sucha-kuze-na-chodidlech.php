<?php
/**
 * Template Name: CZ — Suchá kůže na chodidlech
 *
 * Auto-selected by WordPress for the Page with slug "sucha-kuze-na-chodidlech"
 * (top-level Czech page, /cz/sucha-kuze-na-chodidlech/), same page-{slug}.php
 * convention as page-na-chodidle.php. Issue #229 / R7 of
 * docs/cz-organic-growth-207.md.
 *
 * Czech-first informational page: the CZ site had no page for dry skin on the
 * feet (the EN /dry-skin-feet/ pillar has no Czech twin). Copy is adapted
 * from the approved EN pillar 4 (content/molosoc-site/07-pillar4-dry-skin-feet/)
 * but is NOT a 1:1 translation, so it is deliberately not paired with the EN
 * page in Polylang and gets no hreflang/x-default (functions.php prints
 * x-default only for truly paired pages). Popraskané paty stay owned by
 * /cz/popraskane-paty/ and the commercial "maska na nohy" intent by
 * /cz/hydratacni-navleky-molosoc/; this page links to the former and does not
 * target the latter. Schema + meta description: molosoc_cz_schema().
 *
 * Czech-only, so no $molosoc_is_cz branching. Reuses pillar1.css (enqueued
 * via the shared Journal-article slug list in functions.php).
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main">

	<!-- 1. HERO — hero-breathing-zoom (pure CSS, pillar1.css). -->
	<section class="molosoc-pillar-hero" id="pillarHero">
		<div class="molosoc-pillar-hero__media" aria-hidden="true">
			<img src="https://molosoc.com/wp-content/uploads/2026/07/pillar4_01_wool_socks.jpg"
				alt="" loading="eager" decoding="async">
		</div>
		<div class="molosoc-pillar-hero__scrim" aria-hidden="true"></div>
		<div class="molosoc-pillar-hero__text">
			<p class="molosoc-eyebrow">Suchá kůže</p>
			<h1>Suchá kůže na chodidlech: proč se vrací a jak o ni pečovat</h1>
			<p>Chodidla vysychají jinak než zbytek těla. Pomáhá šetrná pravidelná péče a krém, který se na kůži opravdu stihne vstřebat.</p>
		</div>
	</section>

	<!-- 2. PROČ CHODIDLA VYSYCHAJÍ — static image + text column. -->
	<div class="molosoc-sequential-heading">
		<div class="molosoc-sequential-heading__inner">
			<p class="molosoc-eyebrow">Příčiny</p>
			<h2>Proč chodidla vysychají</h2>
		</div>
	</div>
	<section class="molosoc-sequential-stage" data-slide-direction="right" aria-label="Proč chodidla vysychají">
		<div class="molosoc-sequential-stage__inner">
			<div class="molosoc-argument">
				<div class="molosoc-argument__media">
					<div class="molosoc-media">
						<img src="https://molosoc.com/wp-content/uploads/2026/07/pillar4_03_radiator.jpg"
							alt="Nohy odpočívající u topení"
							loading="lazy" decoding="async">
					</div>
				</div>
				<div class="molosoc-argument__text">
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3>Chodidla nemají mazové žlázy</h3>
						<p>Kůže na chodidlech nemá mazové žlázy jako většina kůže jinde na těle, a vlhkost si proto drží hůř. Vysychá snáz a častěji.</p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3>Ponožky, boty a ztráta vlhkosti</h3>
						<p>Nohy zavřené v obuvi a ponožkách ztrácejí vlhkost do látky i vzduchu celý den. Člověk si toho často všimne až ve chvíli, kdy je kůže už drsná.</p>
					</div>
					<div class="molosoc-argument__item molosoc-sequential-entrance--text">
						<h3>Horká voda, mytí a suchý vzduch</h3>
						<p>Dlouhé horké koupele, agresivní mycí prostředky a suchý vzduch ve vytápěných místnostech odebírají kůži vlhkost rychleji než obvykle.</p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- 3. JAK POZNAT SUCHOU KŮŽI A JAK O NI PEČOVAT — plain text on existing
	     section styles (.molosoc-pillar-dry-skin spacing lives in pillar1.css).
	     The single contextual product-info link is in the cream-routine
	     paragraph below; the final CTA is the only other one. -->
	<section class="molosoc-section molosoc-pillar-dry-skin" aria-label="Šetrná péče o suchá chodidla">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow">Péče</p>
			<h2>Jak poznat suchou kůži na chodidlech</h2>
			<p>Suchá kůže na chodidlech bývá matná, drsná na dotek, může se šupinatit a někdy se napíná nebo svědí. Obvykle je nejvíc znát na patách a po stranách chodidla.</p>

			<h2>Šetrná péče krok za krokem</h2>
			<h3>Mytí a osušení</h3>
			<p>Nohy myjte vlažnou vodou a jemným mycím prostředkem a nenamáčejte je zbytečně dlouho. Pak je důkladně osušte, hlavně mezi prsty, a krém nanášejte hned, dokud je kůže mírně vlhká.</p>
			<h3>Krém na nohy</h3>
			<p>Používejte krém, který vám vyhovuje, a mažte pravidelně, nejlépe každý den, ideálně večer. Důležitější než množství krému je pravidelnost. Pokud tuhle rutinu držíte, ale krém se vám přesto otírá do ponožek nebo do ložního prádla dřív, než se vstřebá, pomůže ho na kůži udržet. K tomu slouží například <a href="<?php echo esc_url( home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) ); ?>">opakovaně použitelný hydratační návlek na nohy</a>, který se nosí přes krém, který už doma máte. Je to pomůcka pro pohodlnější rutinu, ne léčba.</p>
			<h3>Co kůži spíš nepomáhá</h3>
			<p>Tvrdou suchou kůži nedrhněte ani neodřezávejte. Příliš horká voda, silné mýdlo a agresivní pilníky suchost obvykle ještě zhorší. Pokud se vám na patách tvoří praskliny, přečtěte si
				<a href="<?php echo esc_url( home_url( '/cz/popraskane-paty/' ) ); ?>">průvodce popraskanými patami</a>.</p>

			<h2>Kdy se poradit s lékařem nebo lékárníkem</h2>
			<p>Pokud suchá kůže přetrvává i přes pravidelnou péči, výrazně se zhoršuje, svědí, zarudne, mokvá, nebo se objeví praskliny, které krvácejí či vypadají zanícené, nechte si poradit u lékaře nebo lékárníka. Příčinou může být i jiné kožní onemocnění, třeba mykóza nebo ekzém, a to si žádá vyšetření. Pozornost zvlášť věnujte kůži na nohou při cukrovce nebo poruše prokrvení. Tato stránka slouží jen jako obecná informace a nenahrazuje vyšetření.</p>

			<h2>Časté otázky o suché kůži na chodidlech</h2>
			<div class="molosoc-pillar-faq">
				<h3>Proč mám suchá chodidla, i když je mažu?</h3>
				<p>Často je důvodem, že se krém otře do ponožek nebo o podlahu dřív, než se vstřebá, nebo že se mazání vynechává. Pomáhá pravidelnost a dostatek času, aby krém zůstal na kůži.</p>
				<h3>Jak často mazat suchá chodidla?</h3>
				<p>Alespoň jednou denně, nejlépe večer po umytí a osušení nohou. Při velmi suché kůži můžete krém nanést i ráno.</p>
				<h3>Je suchá kůže na chodidlech stejná věc jako popraskané paty?</h3>
				<p>Ne tak úplně. Suchost je výchozí stav, popraskané paty jsou pokročilejší stav, kdy suchá a nepružná kůže pod tlakem praská. Podrobnosti najdete na stránce
					<a href="<?php echo esc_url( home_url( '/cz/popraskane-paty/' ) ); ?>">Popraskané paty</a>.</p>
			</div>
		</div>
	</section>

	<?php molosoc_related_links( 'sucha-kuze' ); ?>

	<!-- FINAL CTA — gentle link to the product-info page. -->
	<section class="molosoc-section molosoc-pillar-final-cta molosoc-pillar-final-cta--halo">
		<div class="molosoc-pillar-final-cta__card">
			<div class="molosoc-pillar-final-cta__media">
				<img src="https://molosoc.com/wp-content/uploads/2026/05/Compare-Molosoc-Nails.jpg"
					alt="" loading="lazy" decoding="async">
			</div>
			<div class="molosoc-pillar-final-cta__copy">
				<p class="molosoc-eyebrow">Podívejte se na skutečné výsledky</p>
				<h2>Výsledky před/po, žádné filtry</h2>
				<p>Podívejte se, jak může krém, který už doma máte, zůstat na kůži déle, když ho přikryje návlek.</p>
				<a class="molosoc-btn" href="<?php echo esc_url( home_url( '/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/' ) ); ?>">Skutečné výsledky, žádné filtry</a>
			</div>
		</div>
	</section>

</main>


<?php get_footer(); ?>
