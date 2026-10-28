<?php
/**
 * Template Name: Landing Page B — Hydrating foot covers (EN) (Issue #288)
 *
 * Auto-selected by WordPress for the Page with the slug
 * "hydrating-foot-covers-molosoc" (page-{slug}.php convention) — the PROPOSED
 * English slug; see inc/landing-b-en.php and docs/landing-page-b-en-288.md.
 * The page itself is provisioned (draft -> Polylang link to CZ B 1037 ->
 * publish) only by the explicitly dispatched, dry-run-by-default workflow
 * .github/workflows/provision-en-lp-b.yml; this file never publishes or
 * touches anything.
 *
 * EN equivalent of page-hydratacni-navleky-molosoc.php: the same sections in
 * the same order, the same markup/classes (so landing-b.css and landing-b.js
 * apply unchanged), the same theme-hosted WebP derivatives, the same size
 * choice -> add-to-cart -> checkout flow (molosoc_landing_b_buy_cta( '', 'en' )
 * with the EN product and EN checkout URLs). Only the copy is localized:
 *   - price: the EN product page's own wording, €10 "charged as 229 CZK"
 *     (molosoc_cz_product_price_html()); shipping: "Shipping from 69 CZK" as on
 *     the EN product page (molosoc_product_364_shipping_note()).
 * Deliberately NOT carried over from the CZ page (no EN wording has been
 * approved for them — owner decision, see the doc): the presale "limited
 * quantity" strip line, the Cash-on-delivery line (CZ-only gateway text), and
 * the anonymous CZ customer-feedback block. The YouTube Short is the same
 * Czech-language video.
 */

defined( 'ABSPATH' ) || exit;

$lpb_price    = '€10';
$lpb_charged  = 'charged as 229 CZK';
$lpb_shipping = 'Shipping from 69 CZK';
$lpb_uploads  = 'https://molosoc.com/wp-content/uploads';
$lpb_hero     = molosoc_landing_b_hero_image(); // LCP image set, shared with the wp_head preload.
$lpb_faq      = molosoc_landing_b_en_faq( $lpb_price, $lpb_shipping );

get_header();
?>

<main id="main" class="lpb" data-lpb-en-landing="288">

	<!-- ============ Hero ============ -->
	<section class="lpb-hero" aria-label="Hydrating foot covers" style="<?php echo molosoc_landing_b_hero_background_style(); ?>">
		<div class="lpb-hero__inner">
			<div class="lpb-hero__media">
				<a class="lpb-hero__main" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-Hero-New-Baige.jpg' ); ?>">
					<img <?php echo molosoc_landing_b_img_attrs( $lpb_hero['base'], $lpb_hero['widths'], $lpb_hero['sizes'] ); ?> width="1152" height="860" alt="White nitrile MOLOSOC foot covers on beige fabric next to lavender and a jar of cream" fetchpriority="high" loading="eager" decoding="async">
				</a>
				<div class="lpb-hero__thumbs">
					<a href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Sofa-2.jpg' ); ?>"><img <?php echo molosoc_landing_b_img_attrs( 'lpb-sofa-2', array( 480 ), '(max-width: 900px) 33vw, 230px' ); ?> width="1152" height="860" alt="Feet in MOLOSOC foot covers resting on a sofa" loading="lazy" decoding="async"></a>
					<img <?php echo molosoc_landing_b_img_attrs( 'lpb-sizes-wbg', array( 480 ), '(max-width: 900px) 33vw, 230px' ); ?> width="1152" height="860" alt="Two pairs of MOLOSOC foot covers, sizes M and L" loading="lazy" decoding="async">
					<img <?php echo molosoc_landing_b_img_attrs( 'lpb-product-pack', array( 480 ), '(max-width: 900px) 33vw, 230px' ); ?> width="1152" height="860" alt="MOLOSOC pack with a foot cover" loading="lazy" decoding="async">
				</div>
			</div>
			<div class="lpb-hero__copy">
				<p class="lpb-eyebrow">Hydrating foot mask</p>
				<h1 class="lpb-hero__title">A foot mask you can use again<br>— with the cream you already have</h1>
				<p class="lpb-hero__sub">No slipping. No waiting. No greasy marks.</p>
				<p class="lpb-hero__lede">Born at home. From real life. For women like us.</p>
				<p class="lpb-price" translate="no"><span class="lpb-price__amount"><?php echo esc_html( $lpb_price ); ?></span></p>
				<p class="lpb-price__meta" translate="no">Per 1 pair · <?php echo esc_html( $lpb_charged ); ?> · <?php echo esc_html( $lpb_shipping ); ?></p>
				<?php molosoc_landing_b_buy_cta( '', 'en' ); ?>
				<p class="lpb-hero__nudge">Don't wait until your heels are dry again. Give them care today.</p>
			</div>
		</div>
	</section>

	<!-- ============ Feature strip ============ -->
	<section class="lpb-strip" aria-label="Materials">
		<p class="lpb-strip__features"><span>100% nitrile</span><span>Latex-free</span><span>Hypoallergenic</span></p>
	</section>

	<!-- ============ Who it is for ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="Who MOLOSOC is for">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Who it's for</p>
			<h2>Who MOLOSOC is for: dry and cracked heels</h2>
			<p class="lpb-lede">Cracked heels have their causes — what triggers them and what really helps is in our guide to <a href="<?php echo esc_url( home_url( '/cracked-heels/' ) ); ?>">cracked heels</a>. MOLOSOC is the tool that lets your cream do its work.</p>
		</div>
		<div class="lpb-cards lpb-cards--3">
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12,6.7L13.45,10.55L17.3,12L13.45,13.45L12,17.3L10.55,13.45L6.7,12L10.55,10.55L12,6.7M12,1L9,9L1,12L9,15L12,23L15,15L23,12L15,9L12,1Z"/></svg>
				<h3>Care without waiting</h3>
				<p>Born at home. From real life. For women like us.</p>
			</div>
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21,11C21,16.55 17.16,21.74 12,23C6.84,21.74 3,16.55 3,11V5L12,1L21,5V11M12,21C15.75,20 19,15.54 19,11.22V6.3L12,3.18L5,6.3V11.22C5,15.54 8.25,20 12,21M10,17L6,13L7.41,11.59L10,14.17L16.59,7.58L18,9"/></svg>
				<h3>No mess</h3>
				<p>For anyone who hates slipping around the flat and greasy marks.</p>
			</div>
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 512 512" aria-hidden="true"><path d="M464 256A208 208 0 1 1 48 256a208 208 0 1 1 416 0zM0 256a256 256 0 1 0 512 0A256 256 0 1 0 0 256zM232 120l0 136c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2 280 120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"/></svg>
				<h3>20–30 minutes</h3>
				<p>For a moment of care — not all day, just a short ritual.</p>
			</div>
		</div>
	</section>

	<!-- ============ What it is ============ -->
	<section class="lpb-section lpb-split" aria-label="What it is">
		<a class="lpb-split__media" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Sofa-2.jpg' ); ?>">
			<img <?php echo molosoc_landing_b_img_attrs( 'lpb-sofa-2', array( 480, 960 ), '(max-width: 900px) 100vw, 50vw' ); ?> width="1152" height="860" alt="Feet in MOLOSOC foot covers resting on a sofa" loading="lazy" decoding="async">
		</a>
		<div class="lpb-split__copy">
			<p class="lpb-eyebrow">What it is</p>
			<h2>They're not socks.</h2>
			<p class="lpb-strong">MOLOSOC are nitrile foot covers — think of them as gloves, but for your feet. A stretchy, smooth material that:</p>
			<ul class="lpb-list">
				<li>locks the cream on your skin — it doesn't soak into fabric</li>
				<li>doesn't slip when you walk around the home</li>
				<li>lets you move normally</li>
				<li>makes caring for dry heels and feet a pleasure</li>
			</ul>
			<p class="lpb-caps">100% nitrile · Latex-free · Powder-free · Hypoallergenic</p>
		</div>
		<div class="lpb-section__cta"><?php molosoc_landing_b_buy_cta( '', 'en' ); ?></div>
	</section>

	<!-- ============ Sizes ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="Sizes">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Sizes</p>
			<h2>Two sizes. One purpose.</h2>
		</div>
		<div class="lpb-cards lpb-cards--3 lpb-cards--photo">
			<div class="lpb-card">
				<a href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-Hero-New-White.jpg' ); ?>"><img <?php echo molosoc_landing_b_img_attrs( 'lpb-hero-white', array( 480, 960 ), '230px' ); ?> width="1152" height="860" alt="MOLOSOC foot cover, size M" loading="lazy" decoding="async"></a>
				<h3>Size M</h3>
				<p>Foot size EU 36–39</p>
			</div>
			<div class="lpb-card">
				<a href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Studio.jpg' ); ?>"><img <?php echo molosoc_landing_b_img_attrs( 'lpb-studio', array( 480, 960 ), '230px' ); ?> width="1920" height="1434" alt="MOLOSOC foot cover, size L" loading="lazy" decoding="async"></a>
				<h3>Size L</h3>
				<p>Foot size EU 39.5–44</p>
			</div>
			<div class="lpb-card">
				<a href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Sizes-WBG-1.jpg' ); ?>"><img <?php echo molosoc_landing_b_img_attrs( 'lpb-sizes-wbg-1', array( 480, 960 ), '230px' ); ?> width="1152" height="860" alt="Size comparison, M and L" loading="lazy" decoding="async"></a>
				<h3>Comparison</h3>
				<p>M on top, L below</p>
			</div>
		</div>
	</section>

	<!-- ============ How it works ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="How it works">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">How it works</p>
			<h2>A simple ritual</h2>
		</div>
		<div class="lpb-split lpb-split--inner">
			<a class="lpb-split__media" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-Apply-Cream-Ok.jpg' ); ?>">
				<img <?php echo molosoc_landing_b_img_attrs( 'lpb-apply-cream', array( 480, 960 ), '(max-width: 900px) 100vw, 50vw' ); ?> width="1920" height="1288" alt="Applying cream to a foot, MOLOSOC foot covers lying next to it" loading="lazy" decoding="async">
			</a>
			<ol class="lpb-steps">
				<li><span class="lpb-steps__num">01</span>Wash and dry your feet</li>
				<li><span class="lpb-steps__num">02</span>Apply cream, balm or oil</li>
				<li><span class="lpb-steps__num">03</span>Put MOLOSOC on each foot</li>
				<li><span class="lpb-steps__num">04</span>Wear for 20–30 minutes</li>
				<li><span class="lpb-steps__num">05</span>Take them off and enjoy softer feet</li>
			</ol>
		</div>
		<div class="lpb-section__cta"><?php molosoc_landing_b_buy_cta( '', 'en' ); ?></div>
	</section>

	<!-- ============ Story ============ -->
	<section class="lpb-section" aria-label="Our story">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Our story</p>
			<h2>How MOLOSOC began</h2>
		</div>
		<div class="lpb-tabs" data-lpb-tabs>
			<div class="lpb-tabs__list" role="tablist" aria-label="How MOLOSOC began">
				<button class="lpb-tabs__tab is-active" type="button" role="tab" id="lpb-tab-1" aria-controls="lpb-panel-1" aria-selected="true">MOLOSOC began at home.</button>
				<button class="lpb-tabs__tab" type="button" role="tab" id="lpb-tab-2" aria-controls="lpb-panel-2" aria-selected="false" tabindex="-1">We wanted another option.</button>
				<button class="lpb-tabs__tab" type="button" role="tab" id="lpb-tab-3" aria-controls="lpb-panel-3" aria-selected="false" tabindex="-1">And then the idea became real.</button>
			</div>
			<div class="lpb-tabs__panel is-active" role="tabpanel" id="lpb-panel-1" aria-labelledby="lpb-tab-1">
				<p>It all started simply — at home, in the bathroom. We rubbed cream into our feet and then didn't know what to do next. Wait? Slip around the flat? Stain the bedding? You know the feeling.</p>
			</div>
			<div class="lpb-tabs__panel" role="tabpanel" id="lpb-panel-2" aria-labelledby="lpb-tab-2" hidden>
				<p>We looked for something that would keep the cream on the skin, not soak it into fabric, and let us move around normally. Nothing like that existed. So we made it ourselves.</p>
			</div>
			<div class="lpb-tabs__panel" role="tabpanel" id="lpb-panel-3" aria-labelledby="lpb-tab-3" hidden>
				<p>After months of testing, choosing the material and fine-tuning the details, MOLOSOC was born — a nitrile foot cover that locks in moisture and lets your cream work. Simple. No mess.</p>
			</div>
		</div>
	</section>

	<!-- ============ In real life ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="MOLOSOC in real life">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">In real life</p>
			<h2>MOLOSOC in real life</h2>
			<p class="lpb-lede">No studio photos. This is how it looks at our home.</p>
		</div>
		<div class="lpb-gallery">
			<figure>
				<img <?php echo molosoc_landing_b_img_attrs( 'lpb-mami-sofa', array( 480, 960 ), '(max-width: 900px) 100vw, 430px' ); ?> width="1920" height="1434" alt="Feet in MOLOSOC foot covers on an orange sofa" loading="lazy" decoding="async">
				<figcaption>Apply, put them on, sit down — and the cream works for you.</figcaption>
			</figure>
			<figure>
				<img <?php echo molosoc_landing_b_img_attrs( 'lpb-holding-first-time', array( 480, 960 ), '(max-width: 900px) 100vw, 430px' ); ?> width="1920" height="1434" alt="Mum holding the finished MOLOSOC foot cover for the first time" loading="lazy" decoding="async">
				<figcaption>We made MOLOSOC ourselves — mother and daughter. Here we hold it for the first time.</figcaption>
			</figure>
		</div>
		<div class="lpb-section__cta"><?php molosoc_landing_b_buy_cta( '', 'en' ); ?></div>
	</section>

	<!-- ============ Video ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="How it all began">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Watch</p>
			<h2>How it all began.</h2>
			<p class="lpb-lede">This is the moment we first started making MOLOSOC (video in Czech).</p>
		</div>
		<div class="lpb-video">
			<iframe src="https://www.youtube-nocookie.com/embed/dXVivzbZBfc?rel=0&amp;modestbranding=1" title="This is roughly how it looked… when the first MOLOSOC was made." width="315" height="560" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>
		</div>
	</section>

	<!-- ============ Compatibility ============ -->
	<section class="lpb-section lpb-split lpb-split--reverse" aria-label="Compatibility">
		<div class="lpb-split__copy">
			<p class="lpb-eyebrow">Compatibility</p>
			<h2>Works with your favourite cream.</h2>
			<p class="lpb-strong">MOLOSOC is not a cream or a pre-soaked single-use mask. It is a reusable foot mask — a tool that boosts the effect of the cream you already have at home.</p>
			<p>Most foot masks in the shop are single-use: they come with their own formula, you use them once and both end up in the bin. A MOLOSOC foot cover lasts at least 10 uses — just wash it after use — and the choice of cream stays yours.</p>
			<p>Apply your favourite cream, balm or oil to your feet. Put MOLOSOC on. The nitrile material locks in moisture and lets the active ingredients reach deeper into the skin.</p>
			<ul class="lpb-chips">
				<li>Heel cream</li>
				<li>Hydrating balm</li>
				<li>Foot oil</li>
				<li>Urea ointment</li>
			</ul>
		</div>
		<a class="lpb-split__media" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Photos-Product-New-VariationCream-Ok.jpg' ); ?>">
			<img <?php echo molosoc_landing_b_img_attrs( 'lpb-variation-cream', array( 480, 960 ), '(max-width: 900px) 100vw, 50vw' ); ?> width="1152" height="860" alt="MOLOSOC foot cover between jars of cream, balm and oil" loading="lazy" decoding="async">
		</a>
		<div class="lpb-section__cta"><?php molosoc_landing_b_buy_cta( '', 'en' ); ?></div>
	</section>

	<!-- ============ Why MOLOSOC ============ -->
	<section class="lpb-section lpb-section--dark" aria-label="Why MOLOSOC">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Why MOLOSOC</p>
			<h2>No more slipping. No more waiting.</h2>
		</div>
		<div class="lpb-cards lpb-cards--3 lpb-cards--dark">
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 18.5C18.83 18.5 19.5 17.83 19.5 17C19.5 16.17 18.83 15.5 18 15.5C17.17 15.5 16.5 16.17 16.5 17C16.5 17.83 17.17 18.5 18 18.5M19.5 9.5H17V12H21.46L19.5 9.5M6 18.5C6.83 18.5 7.5 17.83 7.5 17C7.5 16.17 6.83 15.5 6 15.5C5.17 15.5 4.5 16.17 4.5 17C4.5 17.83 5.17 18.5 6 18.5M20 8L23 12V17H21C21 18.66 19.66 20 18 20C16.34 20 15 18.66 15 17H9C9 18.66 7.66 20 6 20C4.34 20 3 18.66 3 17H1V6C1 4.89 1.89 4 3 4H17V8H20M3 6V15H3.76C4.31 14.39 5.11 14 6 14C6.89 14 7.69 14.39 8.24 15H15V6H3Z"/></svg>
				<h3>Shipped within 24 hours</h3>
			</div>
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 512 512" aria-hidden="true"><path d="M225.8 468.2l-2.5-2.3L48.1 303.2C17.4 274.7 0 234.7 0 192.8v-3.3c0-70.4 50-130.8 119.2-144C158.6 37.9 198.9 47 231 69.6c9 6.4 17.4 13.8 25 22.3 4.2-4.8 8.7-9.2 13.5-13.3 3.7-3.2 7.5-6.2 11.5-9C313.1 47 353.4 37.9 392.8 45.4 462 58.6 512 119.1 512 189.5v3.3c0 41.9-17.4 81.9-48.1 110.4L288.7 465.9l-2.5 2.3c-8.2 7.6-19 11.9-30.2 11.9s-22-4.2-30.2-11.9zM239.1 145c-.4-.3-.7-.7-1-1.1l-17.8-20c-23.1-25.9-58-37.7-92-31.2C81.6 101.5 48 142.1 48 189.5v3.3c0 28.5 11.9 55.8 32.8 75.2L256 430.7 431.2 268c20.9-19.4 32.8-46.7 32.8-75.2v-3.3c0-47.3-33.6-88-80.1-96.9-34-6.5-69 5.4-92 31.2l-17.8 20c-.3.4-.7.7-1 1.1-4.5 4.5-10.6 7-16.9 7s-12.4-2.5-16.9-7z"/></svg>
				<h3>Made with love</h3>
			</div>
			<div class="lpb-card">
				<svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M19,19H5V5H15V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V11H19M7.91,10.08L6.5,11.5L11,16L21,6L19.59,4.58L11,13.17L7.91,10.08Z"/></svg>
				<h3>Secure payment</h3>
			</div>
		</div>
		<p class="lpb-price lpb-price--dark" translate="no"><span class="lpb-price__amount"><?php echo esc_html( $lpb_price ); ?></span></p>
		<p class="lpb-price__meta" translate="no">Per 1 pair · <?php echo esc_html( $lpb_charged ); ?> · <?php echo esc_html( $lpb_shipping ); ?></p>
	</section>

	<!-- ============ FAQ (single source: molosoc_landing_b_en_faq(), also the JSON-LD) ============ -->
	<section class="lpb-section lpb-section--cream" aria-label="FAQ">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">FAQ</p>
			<h2>Any questions?</h2>
		</div>
		<div class="lpb-faq">
			<?php foreach ( $lpb_faq as $lpb_qa ) : ?>
			<details>
				<summary><?php echo esc_html( $lpb_qa[0] ); ?></summary>
				<p><?php echo esc_html( $lpb_qa[1] ); ?></p>
			</details>
			<?php endforeach; ?>
		</div>
	</section>

	<!-- ============ Order ============ -->
	<section class="lpb-section" aria-label="Order">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Order</p>
			<h2>Order MOLOSOC</h2>
			<p class="lpb-lede">1 pack = 1 pair of nitrile foot covers. <?php echo esc_html( $lpb_shipping ); ?>.</p>
		</div>
		<div class="lpb-order">
			<a class="lpb-order__media" href="<?php echo esc_url( $lpb_uploads . '/2026/04/Molosoc-Product-Shot-2.jpg' ); ?>">
				<img <?php echo molosoc_landing_b_img_attrs( 'lpb-product-shot-2', array( 480, 960 ), '(max-width: 900px) 100vw, 400px' ); ?> width="2048" height="2048" alt="MOLOSOC pack — 1 pair of hydrating foot covers" loading="lazy" decoding="async">
			</a>
			<div class="lpb-order__copy">
				<p class="lpb-eyebrow">MOLOSOC · 1 pair</p>
				<h3 class="lpb-order__title">Hydrating foot covers</h3>
				<p class="lpb-order__spec">100% nitrile · Latex-free · Hypoallergenic · Size M (EU 36–39) or L (EU 39.5–44)</p>
				<p class="lpb-price" translate="no"><span class="lpb-price__amount"><?php echo esc_html( $lpb_price ); ?></span></p>
				<p class="lpb-price__meta" translate="no"><?php echo esc_html( $lpb_charged ); ?> · <?php echo esc_html( $lpb_shipping ); ?> · Shipped within 24 hours</p>
				<?php molosoc_landing_b_buy_cta( '', 'en' ); ?>
				<ul class="lpb-badges">
					<li><svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M18 18.5C18.83 18.5 19.5 17.83 19.5 17C19.5 16.17 18.83 15.5 18 15.5C17.17 15.5 16.5 16.17 16.5 17C16.5 17.83 17.17 18.5 18 18.5M19.5 9.5H17V12H21.46L19.5 9.5M6 18.5C6.83 18.5 7.5 17.83 7.5 17C7.5 16.17 6.83 15.5 6 15.5C5.17 15.5 4.5 16.17 4.5 17C4.5 17.83 5.17 18.5 6 18.5M20 8L23 12V17H21C21 18.66 19.66 20 18 20C16.34 20 15 18.66 15 17H9C9 18.66 7.66 20 6 20C4.34 20 3 18.66 3 17H1V6C1 4.89 1.89 4 3 4H17V8H20M3 6V15H3.76C4.31 14.39 5.11 14 6 14C6.89 14 7.69 14.39 8.24 15H15V6H3Z"/></svg><span>Secure payment</span></li>
					<li><svg class="lpb-icon" viewBox="0 0 512 512" aria-hidden="true"><path d="M225.8 468.2l-2.5-2.3L48.1 303.2C17.4 274.7 0 234.7 0 192.8v-3.3c0-70.4 50-130.8 119.2-144C158.6 37.9 198.9 47 231 69.6c9 6.4 17.4 13.8 25 22.3 4.2-4.8 8.7-9.2 13.5-13.3 3.7-3.2 7.5-6.2 11.5-9C313.1 47 353.4 37.9 392.8 45.4 462 58.6 512 119.1 512 189.5v3.3c0 41.9-17.4 81.9-48.1 110.4L288.7 465.9l-2.5 2.3c-8.2 7.6-19 11.9-30.2 11.9s-22-4.2-30.2-11.9zM239.1 145c-.4-.3-.7-.7-1-1.1l-17.8-20c-23.1-25.9-58-37.7-92-31.2C81.6 101.5 48 142.1 48 189.5v3.3c0 28.5 11.9 55.8 32.8 75.2L256 430.7 431.2 268c20.9-19.4 32.8-46.7 32.8-75.2v-3.3c0-47.3-33.6-88-80.1-96.9-34-6.5-69 5.4-92 31.2l-17.8 20c-.3.4-.7.7-1 1.1-4.5 4.5-10.6 7-16.9 7s-12.4-2.5-16.9-7z"/></svg><span>Delivery within 24h</span></li>
					<li><svg class="lpb-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M19,19H5V5H15V3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V11H19M7.91,10.08L6.5,11.5L11,16L21,6L19.59,4.58L11,13.17L7.91,10.08Z"/></svg><span>Made with love</span></li>
				</ul>
			</div>
		</div>
	</section>

	<!-- ============ Founders ============ -->
	<section class="lpb-section lpb-section--cream lpb-founders" aria-label="Founders">
		<div class="lpb-section__head">
			<p class="lpb-eyebrow">Founders</p>
			<h2>We made MOLOSOC ourselves — mother and daughter.</h2>
			<p class="lpb-quote"><em>“Because we know what it's like — to apply cream and then not know what to do next.”</em></p>
		</div>
		<img <?php echo molosoc_landing_b_img_attrs( 'lpb-opening-package-mami', array( 400, 800 ), '(max-width: 400px) 100vw, 400px' ); ?> class="lpb-founders__photo" width="1290" height="1434" alt="Mother and daughter opening a MOLOSOC package together" loading="lazy" decoding="async">
	</section>

</main>

<?php
get_footer();
