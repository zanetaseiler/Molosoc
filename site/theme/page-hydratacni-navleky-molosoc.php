<?php
/**
 * Template Name: Landing Page B — Hydratační návleky (rebuild of WP page 580)
 *
 * Auto-selected by WordPress for the Page with the slug
 * "hydratacni-navleky-molosoc" (page-{slug}.php convention — the page was
 * created as "hydratacni-navleky-landing-b" and renamed in WordPress on
 * 2026-10-13; this file and every is_page() gate in functions.php follow
 * the slug, so a future rename needs the same repo change; same as
 * page-moisture-lock-foot-cover.php / page-cracked-heels.php). The Page
 * itself is created as a DRAFT via .github/workflows/create-wp-page.yml
 * (slug hydratacni-navleky-landing-b at the time) — this file never publishes
 * anything and never touches the live CZ landing Page A (886,
 * /cz/navleky-na-nohy/hydratacni-navlek-na-nohy/) or the source page 580.
 *
 * SOURCE (GitHub Issue #122, owner confirmation 2026-10-13): WordPress page
 * 580 "Hydratacni Navleky Landing Page Old", a Thrive Architect landing
 * page (meta tve_landing_page = tcb2-clickjournalist-sales-page, Thrive
 * footer symbol 103, 16 page sections). Its structure, section order,
 * copy, images and the YouTube embed are reproduced here 1:1 from the
 * page's public rendered HTML + REST record; see
 * docs/landing-page-b-580.md for the section map, the asset inventory
 * and the flagged-outdated-messaging list.
 *
 * ONLY the operational purchase details were adapted to the live shop
 * (Issue scope: "adapt ONLY operational purchase details"):
 *   - price 199 Kč            -> 229 Kč (Woo product 364, Store API)
 *   - "Doprava od 69 Kč"/"49 Kč" -> "Doprava od 79 Kč" (inc/woocommerce-lang.php)
 *   - size L "40–44"          -> "39.5–44" (Woo attribute, matches page 580's
 *                                own size card)
 *   - CTA href /product/molosoc-hydratacni-ponozky/ (dead slug) ->
 *     molosoc_product_url( 'cz' ) = /cz/produkt/hydratacni-navlek-na-nohy/
 * Everything else — including the presale-era "Počet kusů je omezený"
 * strip — is kept verbatim and FLAGGED (search "FLAG:" below) for the
 * owner to decide on; nothing was invented.
 *
 * Czech-only copy by design (page 580 was Czech-only); the product URL is
 * forced to the CZ shop URL because a REST-created draft lands in the
 * default (EN) Polylang language until the owner sets it to Cz.
 *
 * IMAGES (Issue #153, mobile PageSpeed: LCP 9.2 s / score 60): every <img>
 * below is served from the theme's own WebP derivatives in
 * assets/images/landing-b/ (cwebp -q 78 renditions of the page-580 uploads,
 * resized to the widths landing-b.css displays them at) via
 * molosoc_landing_b_img_attrs() in functions.php (src/srcset/sizes). The
 * hero photo is the LCP element: fetchpriority="high", eager, and preloaded
 * from wp_head (molosoc_landing_b_head()) with the identical srcset — both
 * read molosoc_landing_b_hero_image(). Every lightbox-style <a href> still
 * points at the original full-size upload, exactly as page 580 did.
 * Issue #157: PageSpeed's real LCP element is the .lpb-hero CSS background
 * (hero-bg-v2), so it is now a theme-hosted WebP pair too (960 ≤900px /
 * 1920 above) whose URLs the section carries as custom properties from
 * molosoc_landing_b_hero_background_style() and wp_head preloads.
 *
 * CSS/JS (assets/css/landing-b.css, assets/js/landing-b.js, Google Fonts
 * Nunito Sans as on page 580 — loaded non-blocking, see functions.php) are
 * enqueued conditionally in functions.php on is_page('hydratacni-navleky-molosoc').
 * The global sticky "Koupit nyní" pill (Issue #73, sticky-cta.js) shows on
 * this page like everywhere else since Issue #163 — the page-580-style
 * bottom bar (.lpb-sticky) it carried until then was removed with that
 * Issue so the two never overlap. The slug was also noindexed +
 * sitemap-excluded while B was an unpublished variant of A
 * (Issue #122); since Issue #159 the page is indexable and listed in the
 * core sitemap, and inc/landing-b-schema.php prints its meta description
 * and JSON-LD.
 */

defined( 'ABSPATH' ) || exit;

$lpb_product_url = molosoc_product_url( 'cz' );
$lpb_price       = '229 Kč';
$lpb_shipping    = 'Doprava od 79 Kč';
$lpb_uploads     = 'https://molosoc.com/wp-content/uploads';
$lpb_hero        = molosoc_landing_b_hero_image(); // LCP image set, shared with the wp_head preload.

get_header();
?>

<main id="main" class="lpb">

	<!-- ============ 2. Hero (page 580 section 2: 2 columns over hero-bg-v2 webp + 50% white overlay; the bg URLs are custom properties from functions.php, preloaded in wp_head — Issue #157) ============ -->
	<section class="lpb-hero" aria-label="Hydratační návleky na nohy" style="<?php echo molosoc_landing_b_hero_background_style(); ?>">
		<div class="lpb-hero__inner">
			<div class="lpb-hero__media">
				<a class="lpb-hero__main" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-Hero-New-Baige.jpg' ); ?>">
					<img <?php echo molosoc_landing_b_img_attrs( $lpb_hero['base'], $lpb_hero['widths'], $lpb_hero['sizes'] ); ?> width="1152" height="860" alt="Bílé nitrilové návleky MOLOSOC na béžové látce vedle levandule a kelímku krému" fetchpriority="high" loading="eager" decoding="async">
				</a>
				<div class="lpb-hero__thumbs">
					<a href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Sofa-2.jpg' ); ?>"><img <?php echo molosoc_landing_b_img_attrs( 'lpb-sofa-2', array( 480 ), '(max-width: 900px) 33vw, 230px' ); ?> width="1152" height="860" alt="Nohy v návlecích MOLOSOC položené na pohovce" loading="lazy" decoding="async"></a>
					<img <?php echo molosoc_landing_b_img_attrs( 'lpb-sizes-wbg', array( 480 ), '(max-width: 900px) 33vw, 230px' ); ?> width="1152" height="860" alt="Dva páry návleků MOLOSOC, velikosti M a L" loading="lazy" decoding="async">
					<img <?php echo molosoc_landing_b_img_attrs( 'lpb-product-pack', array( 480 ), '(max-width: 900px) 33vw, 230px' ); ?> width="1152" height="860" alt="Balení MOLOSOC s návlekem" loading="lazy" decoding="async">
				</div>
			</div>
			<div class="lpb-hero__copy">
				<?php /* Issue #161 keyword retarget ("maska na nohy"): eyebrow + H1 replaced; page 580 read "Hydratační návleky na nohy" / "Namazané nohy. Bez nepořádku." */ ?>
				<p class="lpb-eyebrow">Hydratační maska na nohy</p>
				<h1 class="lpb-hero__title">Maska na nohy, kterou použijete znovu<br>— s krémem, který už máte</h1>
				<p class="lpb-hero__sub">Bez klouzání. Bez čekání. Bez mastných stop.</p>
				<p class="lpb-hero__lede">Vzniklo doma. Z běžného života. Pro ženy jako jsme my.</p>
				<?php /* FLAG: page 580 carried an EMPTY line-through <span> before the price — a leftover of a crossed-out presale price. Reproduced as nothing (no fake "was" price invented). */ ?>
				<p class="lpb-price" translate="no"><span class="lpb-price__amount"><?php echo esc_html( $lpb_price ); ?></span></p>
				<p class="lpb-price__meta">Za 1 pár · <?php echo esc_html( $lpb_shipping ); ?></p>
				<a class="lpb-btn lpb-hero__cta" id="lpb-hero-cta" href="<?php echo esc_url( $lpb_product_url ); ?>">Objednat za <?php echo esc_html( $lpb_price ); ?></a>
			</div>
		</div>
	</section>

	<!-- ============ 3. Black strip + feature strip (page 580 section 3) ============ -->
	<?php /* FLAG: presale-era scarcity line kept verbatim from page 580 ("Počet kusů je omezený"). Not an operational purchase detail, so it was NOT changed — owner decides whether B keeps it. */ ?>
	<section class="lpb-strip" aria-label="Počet kusů je omezený">
		<p class="lpb-strip__scarcity">Počet kusů je omezený</p>
		<p class="lpb-strip__features"><span>100% nitril</span><span>Bez latexu</span><span>Hypoalergenní</span></p>
	</section>

	<!-- ============ 4. Pro koho (page 580 section 4: 3 icon cards) ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="Pro koho MOLOSOC je">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Pro koho je</p>
			<?php /* Issue #161: H2 reworked from page 580's "Pro koho MOLOSOC je" to carry the Pillar 1 terms; the lede links to /cz/popraskane-paty/, which owns "popraskané paty" / "suché paty". */ ?>
			<h2>Pro koho MOLOSOC je: suché i popraskané paty</h2>
			<p class="lpb-lede">Popraskané paty mají své příčiny – co je způsobuje a co opravdu pomáhá, čtěte v průvodci <a href="<?php echo esc_url( home_url( '/cz/popraskane-paty/' ) ); ?>">popraskané paty</a>. MOLOSOC je nástroj, který nechá váš krém pracovat.</p>
		</div>
		<div class="lpb-cards lpb-cards--3">
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12,6.7L13.45,10.55L17.3,12L13.45,13.45L12,17.3L10.55,13.45L6.7,12L10.55,10.55L12,6.7M12,1L9,9L1,12L9,15L12,23L15,15L23,12L15,9L12,1Z"/></svg>
				<h3>Péče bez čekání</h3>
				<p>Vzniklo doma. Z běžného života. Pro ženy jako jsme my.</p>
			</div>
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21,11C21,16.55 17.16,21.74 12,23C6.84,21.74 3,16.55 3,11V5L12,1L21,5V11M12,21C15.75,20 19,15.54 19,11.22V6.3L12,3.18L5,6.3V11.22C5,15.54 8.25,20 12,21M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9"/></svg>
				<h3>Bez nepořádku</h3>
				<p>Pro ty, kterým vadí klouzání po bytě a mastné stopy.</p>
			</div>
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 512 512" aria-hidden="true"><path d="M464 256A208 208 0 1 1 48 256a208 208 0 1 1 416 0zM0 256a256 256 0 1 0 512 0A256 256 0 1 0 0 256zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"/></svg>
				<h3>20–30 minut</h3>
				<p>Pro chvíle péče – ne na celý den, jen na krátký rituál.</p>
			</div>
		</div>
	</section>

	<!-- ============ 5. Co to je (page 580 section 5: image left, copy right) ============ -->
	<section class="lpb-section lpb-split" aria-label="Co to je">
		<a class="lpb-split__media" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Sofa-2.jpg' ); ?>">
			<img <?php echo molosoc_landing_b_img_attrs( 'lpb-sofa-2', array( 480, 960 ), '(max-width: 900px) 100vw, 50vw' ); ?> width="1152" height="860" alt="Nohy v návlecích MOLOSOC položené na pohovce" loading="lazy" decoding="async">
		</a>
		<div class="lpb-split__copy">
			<p class="lpb-eyebrow">Co to je</p>
			<h2>Nejsou to ponožky.</h2>
			<p class="lpb-strong">MOLOSOC jsou nitrilové návleky na nohy – představte si je jako rukavice, ale na chodidla. Strečový, hladký materiál, který:</p>
			<ul class="lpb-list">
				<li>zamkne krém na noze – nevsakuje ho do látky</li>
				<li>neklouže při chůzi po bytě</li>
				<li>umožňuje normální pohyb</li>
				<li>zpříjemní péči o suché paty a chodidla</li>
			</ul>
			<p class="lpb-caps">100% nitril · Bez latexu · Bez pudru · Hypoalergenní</p>
		</div>
	</section>

	<!-- ============ 6. Velikosti (page 580 section 6: 3 image cards) ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="Velikosti">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Velikosti</p>
			<h2>Dvě velikosti. Jeden účel.</h2>
		</div>
		<div class="lpb-cards lpb-cards--3 lpb-cards--photo">
			<div class="lpb-card">
				<a href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-Hero-New-White.jpg' ); ?>"><img <?php echo molosoc_landing_b_img_attrs( 'lpb-hero-white', array( 480, 960 ), '230px' ); ?> width="1152" height="860" alt="Návlek MOLOSOC velikost M" loading="lazy" decoding="async"></a>
				<h3>Velikost M</h3>
				<p>Velikost nohy 36–39</p>
			</div>
			<div class="lpb-card">
				<a href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Studio.jpg' ); ?>"><img <?php echo molosoc_landing_b_img_attrs( 'lpb-studio', array( 480, 960 ), '230px' ); ?> width="1920" height="1434" alt="Návlek MOLOSOC velikost L" loading="lazy" decoding="async"></a>
				<h3>Velikost L</h3>
				<p>Velikost nohy 39.5–44</p>
			</div>
			<div class="lpb-card">
				<a href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Sizes-WBG-1.jpg' ); ?>"><img <?php echo molosoc_landing_b_img_attrs( 'lpb-sizes-wbg-1', array( 480, 960 ), '230px' ); ?> width="1152" height="860" alt="Porovnání velikostí M a L" loading="lazy" decoding="async"></a>
				<h3>Porovnání</h3>
				<p>M nahoře, L dole</p>
			</div>
		</div>
	</section>

	<!-- ============ 7. Jak to funguje (page 580 section 7: image + 5 numbered steps) ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="Jak to funguje">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Jak to funguje</p>
			<h2>Jednoduchý rituál</h2>
		</div>
		<div class="lpb-split lpb-split--inner">
			<a class="lpb-split__media" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Apply-Cream-Ok.jpg' ); ?>">
				<img <?php echo molosoc_landing_b_img_attrs( 'lpb-apply-cream', array( 480, 960 ), '(max-width: 900px) 100vw, 50vw' ); ?> width="1920" height="1288" alt="Nanášení krému na chodidlo, vedle leží návleky MOLOSOC" loading="lazy" decoding="async">
			</a>
			<ol class="lpb-steps">
				<li><span class="lpb-steps__num">01</span>Umyjte a osušte si nohy</li>
				<li><span class="lpb-steps__num">02</span>Naneste krém, balzám nebo olej</li>
				<li><span class="lpb-steps__num">03</span>Nasaďte MOLOSOC na každou nohu</li>
				<li><span class="lpb-steps__num">04</span>Noste 20–30 minut</li>
				<li><span class="lpb-steps__num">05</span>Sundejte a užijte si jemnější chodidla</li>
			</ol>
		</div>
	</section>

	<!-- ============ 8. Příběh (page 580 section 8: Thrive tabs, 3 tabs) ============ -->
	<section class="lpb-section" aria-label="Příběh">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Příběh</p>
			<h2>Jak MOLOSOC vznikl</h2>
		</div>
		<?php /* FLAG: the third tab title on page 580 is broken by a stray line break ("A pak se stal nápad sku / tečností."); rendered here as the obviously intended "A pak se stal nápad skutečností." — the only copy change outside operational details. */ ?>
		<div class="lpb-tabs" data-lpb-tabs>
			<div class="lpb-tabs__list" role="tablist" aria-label="Jak MOLOSOC vznikl">
				<button class="lpb-tabs__tab is-active" type="button" role="tab" id="lpb-tab-1" aria-controls="lpb-panel-1" aria-selected="true">MOLOSOC vznikl doma.</button>
				<button class="lpb-tabs__tab" type="button" role="tab" id="lpb-tab-2" aria-controls="lpb-panel-2" aria-selected="false" tabindex="-1">Chtěly jsme jinou možnost.</button>
				<button class="lpb-tabs__tab" type="button" role="tab" id="lpb-tab-3" aria-controls="lpb-panel-3" aria-selected="false" tabindex="-1">A pak se stal nápad skutečností.</button>
			</div>
			<div class="lpb-tabs__panel is-active" role="tabpanel" id="lpb-panel-1" aria-labelledby="lpb-tab-1">
				<p>Všechno to začalo jednoduše – doma, v koupelně. Namazaly jsme si nohy krémem a pak jsme nevěděly, co dál. Čekat? Klouzat po bytě? Zašpinit povlečení? Znáte to.</p>
			</div>
			<div class="lpb-tabs__panel" role="tabpanel" id="lpb-panel-2" aria-labelledby="lpb-tab-2" hidden>
				<p>Hledaly jsme něco, co udrží krém na noze, nevsákne ho do látky a dovolí nám normálně se pohybovat. Nic takového neexistovalo. Tak jsme to vytvořily samy.</p>
			</div>
			<div class="lpb-tabs__panel" role="tabpanel" id="lpb-panel-3" aria-labelledby="lpb-tab-3" hidden>
				<p>Po měsících testování, výběru materiálu a ladění detailů vznikl MOLOSOC – nitrilový návlek na nohy, který zamkne vlhkost a nechá krém pracovat. Jednoduše. Bez nepořádku.</p>
			</div>
		</div>
	</section>

	<!-- ============ 9. Z reálu (page 580 section 9: 2 captioned photos) ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="MOLOSOC v reálu">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Z reálu</p>
			<h2>MOLOSOC v reálu</h2>
			<p class="lpb-lede">Žádné studiové fotky. Takhle to vypadá u nás doma.</p>
		</div>
		<div class="lpb-gallery">
			<figure>
				<img <?php echo molosoc_landing_b_img_attrs( 'lpb-mami-sofa', array( 480, 960 ), '(max-width: 900px) 100vw, 430px' ); ?> width="1920" height="1434" alt="Nohy v návlecích MOLOSOC na oranžové pohovce" loading="lazy" decoding="async">
				<figcaption>Namazat, nasadit, sednout si – a krém pracuje za vás.</figcaption>
			</figure>
			<figure>
				<img <?php echo molosoc_landing_b_img_attrs( 'lpb-holding-first-time', array( 480, 960 ), '(max-width: 900px) 100vw, 430px' ); ?> width="1920" height="1434" alt="Máma drží poprvé hotový návlek MOLOSOC" loading="lazy" decoding="async">
				<figcaption>MOLOSOC jsme vytvořily my – máma s dcerou. Tady ho držíme poprvé.</figcaption>
			</figure>
		</div>
	</section>

	<!-- ============ 10. Podívejte se (page 580 section 10: YouTube embed dXVivzbZBfc, vertical) ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="Jak to vše začalo">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Podívejte se</p>
			<h2>Jak to vše začalo.</h2>
			<p class="lpb-lede">Takhle vypadal moment, kdy jsme poprvé začaly vytvářet MOLOSOC.</p>
		</div>
		<div class="lpb-video">
			<iframe src="https://www.youtube-nocookie.com/embed/dXVivzbZBfc?rel=0&amp;modestbranding=1" title="Takhle nějak to vypadalo… když vznikal první MOLOSOC." width="315" height="560" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>
		</div>
	</section>

	<!-- ============ 11. Kompatibilita (page 580 section 11: copy left, image right, 4 chips) ============ -->
	<section class="lpb-section lpb-split lpb-split--reverse" aria-label="Kompatibilita">
		<div class="lpb-split__copy">
			<p class="lpb-eyebrow">Kompatibilita</p>
			<h2>Funguje s vaším oblíbeným krémem.</h2>
			<?php /* Issue #161: page 580 read "MOLOSOC není krém. Není to maska." — reworded so the page does not contradict its own H1; the one-use vs. reusable comparison repeats the category page's argument (page-foot-covers.php), no new claim. */ ?>
			<p class="lpb-strong">MOLOSOC není krém ani předplněná jednorázová maska. Je to maska na nohy na opakované použití – nástroj, který zlepší účinek krému, který už máte doma.</p>
			<p>Většina masek na nohy v obchodě je na jedno použití: má vlastní formuli, použijete ji jednou a obojí skončí v koši. Návlek MOLOSOC vydrží alespoň 10 použití – stačí ho po použití umýt a výběr krému zůstává na vás.</p>
			<p>Naneste svůj oblíbený krém, balzám nebo olej na chodidla. Nasaďte MOLOSOC. Nitrilový materiál zamkne vlhkost a nechá aktivní složky proniknout hlouběji do pokožky.</p>
			<ul class="lpb-chips">
				<li>Krém na paty</li>
				<li>Hydratační balzám</li>
				<li>Olej na nohy</li>
				<li>Urea mast</li>
			</ul>
		</div>
		<a class="lpb-split__media" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-VariationCream-Ok.jpg' ); ?>">
			<img <?php echo molosoc_landing_b_img_attrs( 'lpb-variation-cream', array( 480, 960 ), '(max-width: 900px) 100vw, 50vw' ); ?> width="1152" height="860" alt="Návlek MOLOSOC mezi kelímky krému, balzámu a oleje" loading="lazy" decoding="async">
		</a>
	</section>

	<!-- ============ 12. Proč MOLOSOC (page 580 section 12: black band, 3 icon cards, price + CTA) ============ -->
	<section class="lpb-section lpb-section--dark" aria-label="Proč MOLOSOC">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Proč MOLOSOC</p>
			<h2>Konec klouzání. Konec čekání.</h2>
		</div>
		<div class="lpb-cards lpb-cards--3 lpb-cards--dark">
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 18.5C18.83 18.5 19.5 17.83 19.5 17C19.5 16.17 18.83 15.5 18 15.5C17.17 15.5 16.5 16.17 16.5 17C16.5 17.83 17.17 18.5 18 18.5M19.5 9.5H17V12H21.46L19.5 9.5M6 18.5C6.83 18.5 7.5 17.83 7.5 17C7.5 16.17 6.83 15.5 6 15.5C5.17 15.5 4.5 16.17 4.5 17C4.5 17.83 5.17 18.5 6 18.5M20 8L23 12V17H21C21 18.66 19.66 20 18 20C16.34 20 15 18.66 15 17H9C9 18.66 7.66 20 6 20C4.34 20 3 18.66 3 17H1V6C1 4.89 1.89 4 3 4H17V8H20M3 6V15H3.76C4.31 14.39 5.11 14 6 14C6.89 14 7.69 14.39 8.24 15H15V6H3Z"/></svg>
				<h3>Odesíláme do 24 hodin</h3>
			</div>
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 512 512" aria-hidden="true"><path d="M225.8 468.2l-2.5-2.3L48.1 303.2C17.4 274.7 0 234.7 0 192.8v-3.3c0-70.4 50-130.8 119.2-144C158.6 37.9 198.9 47 231 69.6c9 6.4 17.4 13.8 25 22.3 4.2-4.8 8.7-9.2 13.5-13.3 3.7-3.2 7.5-6.2 11.5-9C313.1 47 353.4 37.9 392.8 45.4 462 58.6 512 119.1 512 189.5v3.3c0 41.9-17.4 81.9-48.1 110.4L288.7 465.9l-2.5 2.3c-8.2 7.6-19 11.9-30.2 11.9s-22-4.2-30.2-11.9zM239.1 145c-.4-.3-.7-.7-1-1.1l-17.8-20c-23.1-25.9-58-37.7-92-31.2C81.6 101.5 48 142.1 48 189.5v3.3c0 28.5 11.9 55.8 32.8 75.2L256 430.7 431.2 268c20.9-19.4 32.8-46.7 32.8-75.2v-3.3c0-47.3-33.6-88-80.1-96.9-34-6.5-69 5.4-92 31.2l-17.8 20c-.3.4-.7.7-1 1.1-4.5 4.5-10.6 7-16.9 7s-12.4-2.5-16.9-7z"/></svg>
				<h3>Vytvořeno s láskou</h3>
			</div>
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M19,19H5V5H15V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V11H19M7.91,10.08L6.5,11.5L11,16L21,6L19.59,4.58L11,13.17L7.91,10.08Z"/></svg>
				<h3>Bezpečná platba</h3>
			</div>
		</div>
		<p class="lpb-price lpb-price--dark" translate="no"><span class="lpb-price__amount"><?php echo esc_html( $lpb_price ); ?></span></p>
		<p class="lpb-price__meta">Za 1 pár · <?php echo esc_html( $lpb_shipping ); ?> · Bezpečná platba přes Comgate</p>
		<a class="lpb-btn lpb-btn--ghost" href="<?php echo esc_url( $lpb_product_url ); ?>">Objednat MOLOSOC za <?php echo esc_html( $lpb_price ); ?></a>
	</section>

	<!-- ============ 13. FAQ (page 580 section 13: 6 Thrive toggles -> native <details>) ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="FAQ">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">FAQ</p>
			<h2>Máte otázky?</h2>
		</div>
		<div class="lpb-faq">
			<details>
				<summary>Z čeho je MOLOSOC vyrobený?</summary>
				<p>MOLOSOC je vyrobený ze 100% nitrilu – bez latexu, bez pudru. Je hypoalergenní a vhodný i pro citlivou pokožku. Představte si to jako rukavice, ale na nohy.</p>
			</details>
			<details>
				<summary>Jak se MOLOSOC používá?</summary>
				<p>Jednoduše: 1) Umyjte a osušte nohy. 2) Naneste svůj oblíbený krém, balzám nebo olej. 3) Nasaďte MOLOSOC na každou nohu. 4) Noste 20–30 minut. 5) Sundejte a užijte si jemnější chodidla.</p>
			</details>
			<details>
				<summary>Můžu v nich chodit?</summary>
				<p>Ano! MOLOSOC neklouže a umožňuje normální pohyb po bytě. Nemusíte sedět a čekat.</p>
			</details>
			<details>
				<summary>Funguje to s jakýmkoliv krémem?</summary>
				<p>Ano. MOLOSOC funguje s jakýmkoliv krémem, balzámem nebo olejem na nohy, který už máte doma. Není potřeba kupovat nic speciálního.</p>
			</details>
			<details>
				<summary>Je to jednorázové?</summary>
				<p>Nejsou jednorázové – při domácím použití vydrží opakovaně díky kvalitnímu materiálu. Stačí je po použití umýt mýdlem a vodou, nechat uschnout a použít znovu. (Jednorázové by byly pouze v hygienickém/profesionálním prostředí.)</p>
			</details>
			<details>
				<summary>Kolik stojí jedno balení?</summary>
				<?php /* Operational: page 580 said "199 Kč. Doprava od 49 Kč." — the only place it quoted 49 Kč. */ ?>
				<p>Jedno balení MOLOSOC (1 pár) stojí <?php echo esc_html( $lpb_price ); ?>. <?php echo esc_html( $lpb_shipping ); ?>. Odesíláme do 24 hodin od objednání.</p>
			</details>
		</div>
	</section>

	<!-- ============ 14. Objednávka (page 580 section 14: product card with 3 mini badges) ============ -->
	<section class="lpb-section" aria-label="Objednávka">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Objednávka</p>
			<h2>Objednejte MOLOSOC</h2>
			<p class="lpb-lede">1 balení = 1 pár nitrilových návleků na nohy. <?php echo esc_html( $lpb_shipping ); ?>.</p>
		</div>
		<div class="lpb-order">
			<a class="lpb-order__media" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Product-Shot-2.jpg' ); ?>">
				<img <?php echo molosoc_landing_b_img_attrs( 'lpb-product-shot-2', array( 480, 960 ), '(max-width: 900px) 100vw, 400px' ); ?> width="2048" height="2048" alt="Balení MOLOSOC – 1 pár hydratačních návleků na nohy" loading="lazy" decoding="async">
			</a>
			<div class="lpb-order__copy">
				<p class="lpb-eyebrow">MOLOSOC · 1 pár</p>
				<h3 class="lpb-order__title">Hydratační návleky na nohy</h3>
				<p class="lpb-order__spec">100% nitril · Bez latexu · Hypoalergenní · Velikost M (36–39) nebo L (39.5–44)</p>
				<p class="lpb-price" translate="no"><span class="lpb-price__amount"><?php echo esc_html( $lpb_price ); ?></span></p>
				<p class="lpb-price__meta"><?php echo esc_html( $lpb_shipping ); ?> · Odesíláme do 24 hodin</p>
				<a class="lpb-btn" href="<?php echo esc_url( $lpb_product_url ); ?>">Objednat za <?php echo esc_html( $lpb_price ); ?></a>
				<ul class="lpb-badges">
					<li><svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 18.5C18.83 18.5 19.5 17.83 19.5 17C19.5 16.17 18.83 15.5 18 15.5C17.17 15.5 16.5 16.17 16.5 17C16.5 17.83 17.17 18.5 18 18.5M19.5 9.5H17V12H21.46L19.5 9.5M6 18.5C6.83 18.5 7.5 17.83 7.5 17C7.5 16.17 6.83 15.5 6 15.5C5.17 15.5 4.5 16.17 4.5 17C4.5 17.83 5.17 18.5 6 18.5M20 8L23 12V17H21C21 18.66 19.66 20 18 20C16.34 20 15 18.66 15 17H9C9 18.66 7.66 20 6 20C4.34 20 3 18.66 3 17H1V6C1 4.89 1.89 4 3 4H17V8H20M3 6V15H3.76C4.31 14.39 5.11 14 6 14C6.89 14 7.69 14.39 8.24 15H15V6H3Z"/></svg><span>Bezpečná platba</span></li>
					<li><svg class="lpb-icon" viewBox="0 0 512 512" aria-hidden="true"><path d="M225.8 468.2l-2.5-2.3L48.1 303.2C17.4 274.7 0 234.7 0 192.8v-3.3c0-70.4 50-130.8 119.2-144C158.6 37.9 198.9 47 231 69.6c9 6.4 17.4 13.8 25 22.3 4.2-4.8 8.7-9.2 13.5-13.3 3.7-3.2 7.5-6.2 11.5-9C313.1 47 353.4 37.9 392.8 45.4 462 58.6 512 119.1 512 189.5v3.3c0 41.9-17.4 81.9-48.1 110.4L288.7 465.9l-2.5 2.3c-8.2 7.6-19 11.9-30.2 11.9s-22-4.2-30.2-11.9zM239.1 145c-.4-.3-.7-.7-1-1.1l-17.8-20c-23.1-25.9-58-37.7-92-31.2C81.6 101.5 48 142.1 48 189.5v3.3c0 28.5 11.9 55.8 32.8 75.2L256 430.7 431.2 268c20.9-19.4 32.8-46.7 32.8-75.2v-3.3c0-47.3-33.6-88-80.1-96.9-34-6.5-69 5.4-92 31.2l-17.8 20c-.3.4-.7.7-1 1.1-4.5 4.5-10.6 7-16.9 7s-12.4-2.5-16.9-7z"/></svg><span>Doručení do 24h</span></li>
					<li><svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M19,19H5V5H15V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V11H19M7.91,10.08L6.5,11.5L11,16L21,6L19.59,4.58L11,13.17L7.91,10.08Z"/></svg><span>Vyrobeno s láskou</span></li>
				</ul>
			</div>
		</div>
	</section>

	<!-- ============ 15. Zakladatelky (page 580 section 15) ============ -->
	<section class="lpb-section lpb-section--cream lpb-founders" aria-label="Zakladatelky">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Zakladatelky</p>
			<h2>MOLOSOC jsme vytvořily my – máma s dcerou.</h2>
			<p class="lpb-quote"><em>“Protože víme, jaké to je – namazat se a pak nevědět, co dál.”</em></p>
		</div>
		<img <?php echo molosoc_landing_b_img_attrs( 'lpb-opening-package-mami', array( 400, 800 ), '(max-width: 400px) 100vw, 400px' ); ?> class="lpb-founders__photo" width="1290" height="1434" alt="Máma a dcera spolu otevírají balíček MOLOSOC" loading="lazy" decoding="async">
	</section>

</main>

<?php
/*
 * Sticky CTA: page 580 pinned its header "Objednat nyní" button (Thrive
 * data-tve-scroll); B rebuilt that as its own .lpb-sticky bottom bar until
 * Issue #163 replaced it with the site-wide sticky "Koupit nyní" pill that
 * every other public page shows (functions.php enqueues sticky-cta.js and
 * prints window.molosocStickyCta here like anywhere else) — same button,
 * every device, no page-specific markup.
 */
get_footer();
