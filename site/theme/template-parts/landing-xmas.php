<?php
/**
 * Christmas 2026 gift landing (Issue #251) — shared CZ/EN body.
 *
 * Expects $lpx_lang ('cz'|'en') from page-vanocni-darek-molosoc.php /
 * page-christmas-gift-molosoc.php. Structure and classes follow Landing B
 * (landing-b.css is a dependency of landing-xmas.css); copy lives in the
 * $t array below, one entry per language. No countdown, no scarcity, no
 * delivery-date promise, no free-gift-wrap claim, no medical claim.
 */

defined( 'ABSPATH' ) || exit;

$lpx_lang  = ( isset( $lpx_lang ) && 'en' === $lpx_lang ) ? 'en' : 'cz';
$lpx_prices = molosoc_xmas_unit_prices();
$lpx_fmt   = static function ( $n ) use ( $lpx_lang ) {
	return 'en' === $lpx_lang ? number_format_i18n( $n ) . ' CZK' : number_format_i18n( $n ) . ' Kč';
};
$lpx_url   = static function () use ( $lpx_lang ) {
	return molosoc_product_url( $lpx_lang );
};

$copy = array(
	'cz' => array(
		'label'     => 'Vánoční dárek MOLOSOC',
		'eyebrow'   => 'Vánoce 2026',
		'h1'        => 'Darujte péči, která nekončí Vánocemi.',
		'sub'       => 'Malý dárek pro maminku, partnera nebo někoho, na kom vám záleží. MOLOSOC pomáhá proměnit obyčejný krém na nohy v jednoduchý pečující rituál.',
		'ship'      => 'Doprava od 79 Kč',
		'cod'       => molosoc_cod_cz_text(),
		'cod_label' => 'Dobírka:',
		'cta'       => 'Pokračovat k pokladně',
		'pairs'     => array( 1 => '1 pár', 2 => '2 páry', 3 => '3 páry' ),
		'normally'  => 'běžně',
		'pair_n'    => 'Pár %d',
		'size'      => 'Velikost',
		'size_err'  => 'Vyberte velikost pro každý pár.',
		'bundle_h'  => 'Vyberte dárkový set',
		'bundle_p'  => 'Zvolte počet párů a velikost M nebo L pro každý z nich. Cena se započítá v pokladně.',
		'sizes'     => array( 'M' => 'M (36–39)', 'L' => 'L (39.5–44)' ),
		'why_h'     => 'Proč je to dobrý dárek',
		'why'       => array(
			array( 'Praktický a promyšlený', 'Nitrilové návleky na nohy s sebou nesou jednoduchý rituál: namazat, nasadit, chvíli si sednout.' ),
			array( 'Použijí ho znovu', 'Návlek vydrží alespoň 10 použití – po použití ho stačí umýt mýdlem a vodou.' ),
			array( 'Hodí se ke krému, který už mají', 'Funguje s jakýmkoliv krémem, balzámem nebo olejem na nohy. Nic dalšího není potřeba kupovat.' ),
		),
		'how_h'     => 'Jak to funguje',
		'steps'     => array( 'Umýt a osušit nohy', 'Namazat krémem, balzámem nebo olejem', 'Nasadit MOLOSOC a 20–30 minut si odpočinout' ),
		'story_h'   => 'Vytvořily jsme ho my – máma s dcerou',
		'story'     => 'MOLOSOC vznikl doma, v koupelně: namazaly jsme si nohy krémem a nevěděly, co dál. Hledaly jsme něco, co udrží krém na noze a dovolí nám normálně se pohybovat. Tak jsme to vytvořily samy. Teď ho můžete dát dál.',
		'order_h'   => 'Objednejte dárek',
		'order_p'   => 'Normální WooCommerce objednávka: výběr dopravy a platby proběhne v pokladně. Bezpečná platba přes Comgate.',
		'faq_h'     => 'Časté otázky',
		'faq'       => array(
			array( 'Jakou velikost vybrat?', 'M sedí na velikost nohy 36–39, L na 39.5–44. Pokud si nejste jistí, zeptejte se obdarovaného na velikost bot.' ),
			array( 'Kolik stojí doprava a platba?', 'Doprava od 79 Kč. Platbu a dopravu vybíráte v pokladně; ' . molosoc_cod_cz_text() ),
			array( 'Jak se o návleky starat?', 'Po použití je umyjte mýdlem a vodou, nechte uschnout a použijte znovu.' ),
			array( 'Je to vhodné jako dárek?', 'Ano – je to malý praktický dárek k domácí péči o nohy. Dárkové balení v ceně není; objednávka přijde v běžném balení.' ),
		),
	),
	'en' => array(
		'label'     => 'MOLOSOC Christmas gift',
		'eyebrow'   => 'Christmas 2026',
		'h1'        => 'Give care that doesn\'t end with Christmas.',
		'sub'       => 'A small gift for your mum, partner or someone you care about. MOLOSOC turns an ordinary foot cream into a simple caring ritual.',
		'ship'      => 'Shipping from 79 CZK',
		'cod'       => '',
		'cod_label' => '',
		'cta'       => 'Continue to checkout',
		'pairs'     => array( 1 => '1 pair', 2 => '2 pairs', 3 => '3 pairs' ),
		'normally'  => 'normally',
		'pair_n'    => 'Pair %d',
		'size'      => 'Size',
		'size_err'  => 'Please choose a size for every pair.',
		'bundle_h'  => 'Choose your gift set',
		'bundle_p'  => 'Pick how many pairs, then size M or L for each. The price is applied at checkout.',
		'sizes'     => array( 'M' => 'M (EU 36–39)', 'L' => 'L (EU 39.5–44)' ),
		'why_h'     => 'Why it makes a thoughtful gift',
		'why'       => array(
			array( 'Practical and considered', 'Nitrile foot covers come with a simple ritual: apply, put on, sit down for a moment.' ),
			array( 'They will use it again', 'Each cover lasts at least 10 uses – just wash it with soap and water after use.' ),
			array( 'Pairs with the foot cream they already have', 'Works with any foot cream, balm or oil. Nothing else to buy.' ),
		),
		'how_h'     => 'How it works',
		'steps'     => array( 'Wash and dry the feet', 'Apply cream, balm or oil', 'Put MOLOSOC on and relax for 20–30 minutes' ),
		'story_h'   => 'Made by a mother and her daughter',
		'story'     => 'MOLOSOC started at home, in the bathroom: we put cream on our feet and wondered what to do next. We wanted something that keeps the cream on the foot and still lets you move around. So we made it ourselves. Now you can pass it on.',
		'order_h'   => 'Order the gift',
		'order_p'   => 'A normal WooCommerce order: shipping and payment are chosen at checkout. Secure payment via Comgate.',
		'faq_h'     => 'FAQ',
		'faq'       => array(
			array( 'Which size should I choose?', 'M fits shoe sizes EU 36–39, L fits 39.5–44. If unsure, ask the recipient for their shoe size.' ),
			array( 'What do shipping and payment cost?', 'Shipping from 79 CZK. Shipping and payment methods are chosen at checkout.' ),
			array( 'How do I care for the covers?', 'Wash with soap and water after use, let them dry and use them again.' ),
			array( 'Is it suitable as a gift?', 'Yes – a small, practical gift for at-home foot care. Gift wrapping is not included; the order ships in standard packaging.' ),
		),
	),
);
$t = $copy[ $lpx_lang ];

$lpx_sizes = $t['sizes'];
$lpx_base  = array();
foreach ( array( 1, 2, 3 ) as $n ) {
	$lpx_base[ $n ] = array(
		'total'   => molosoc_xmas_bundle_total( $n ),
		'regular' => MOLOSOC_XMAS_REGULAR_PRICE * $n,
		'url'     => '', // filled from the size picks by landing-xmas.js
	);
}
$lpx_checkout = molosoc_xmas_checkout_url( $lpx_lang );
$lpx_buyable  = count( molosoc_xmas_variations() ) === 2;

/** Bundle picker: a fieldset of 1/2/3 pairs, then a size fieldset per pair. */
$lpx_picker = static function ( $id ) use ( $t, $lpx_sizes, $lpx_base, $lpx_fmt, $lpx_url, $lpx_checkout, $lpx_buyable ) {
	?>
	<div class="lpb-buy lpx-buy" data-lpx-buy data-lpx-checkout-url="<?php echo esc_url( $lpx_checkout ); ?>" data-lpx-enabled="<?php echo $lpx_buyable ? '1' : '0'; ?>">
		<fieldset class="lpx-bundles">
			<legend class="lpb-buy__legend"><?php echo esc_html( $t['bundle_h'] ); ?></legend>
			<?php foreach ( $lpx_base as $n => $b ) : ?>
				<label class="lpx-bundle">
					<input type="radio" name="lpx-pairs-<?php echo esc_attr( $id ); ?>" value="<?php echo (int) $n; ?>"<?php echo 1 === $n ? ' checked' : ''; ?>>
					<span class="lpx-bundle__body">
						<span class="lpx-bundle__name"><?php echo esc_html( $t['pairs'][ $n ] ); ?></span>
						<span class="lpx-bundle__price" translate="no"><?php echo esc_html( $lpx_fmt( $b['total'] ) ); ?></span>
						<?php if ( $b['total'] < $b['regular'] ) : ?>
							<s class="lpx-bundle__was" translate="no"><?php echo esc_html( $t['normally'] . ' ' . $lpx_fmt( $b['regular'] ) ); ?></s>
						<?php endif; ?>
					</span>
				</label>
			<?php endforeach; ?>
		</fieldset>
		<?php foreach ( array( 1, 2, 3 ) as $n ) : ?>
			<fieldset class="lpb-buy__sizes lpx-pair" data-lpx-pair="<?php echo (int) $n; ?>"<?php echo $n > 1 ? ' hidden' : ''; ?>>
				<legend class="lpb-buy__legend"><?php echo esc_html( sprintf( $t['pair_n'], $n ) . ' · ' . $t['size'] ); ?></legend>
				<?php foreach ( $lpx_sizes as $key => $label ) : ?>
					<label class="lpb-size">
						<input type="radio" name="lpx-size-<?php echo esc_attr( $id ); ?>-<?php echo (int) $n; ?>" value="<?php echo esc_attr( $key ); ?>">
						<span class="lpb-size__label"><?php echo esc_html( $label ); ?></span>
					</label>
				<?php endforeach; ?>
			</fieldset>
		<?php endforeach; ?>
		<a class="lpb-btn lpb-buy__btn" href="<?php echo esc_url( $lpx_url() ); ?>" data-lpx-go rel="nofollow"><?php echo esc_html( $t['cta'] ); ?></a>
		<p class="lpb-buy__error" role="alert" hidden><?php echo esc_html( $t['size_err'] ); ?></p>
	</div>
	<?php
};

$lpx_hero_img = molosoc_xmas_image( 'scene-01', 'cz' === $lpx_lang ? 'Vánoční dárek MOLOSOC' : 'MOLOSOC Christmas gift', 'fetchpriority="high" loading="eager"' );
$lpx_s2       = molosoc_xmas_image( 'scene-02', 'cz' === $lpx_lang ? 'Dárek s návleky MOLOSOC' : 'A gift with MOLOSOC foot covers', 'loading="lazy"' );
$lpx_s3       = molosoc_xmas_image( 'scene-03', 'cz' === $lpx_lang ? 'Vánoční dárek MOLOSOC, detail' : 'MOLOSOC Christmas gift, detail', 'loading="lazy"' );

get_header();
?>

<main id="main" class="lpb lpx" lang="<?php echo 'cz' === $lpx_lang ? 'cs' : 'en'; ?>">

	<section class="lpx-hero" aria-label="<?php echo esc_attr( $t['label'] ); ?>">
		<div class="lpx-hero__inner">
			<?php if ( $lpx_hero_img ) : ?>
				<div class="lpx-hero__media"><?php echo $lpx_hero_img; // phpcs:ignore WordPress.Security.EscapeOutput -- escaped in molosoc_xmas_image(). ?></div>
			<?php endif; ?>
			<div class="lpx-hero__copy">
				<p class="lpb-eyebrow"><?php echo esc_html( $t['eyebrow'] ); ?></p>
				<h1 class="lpx-hero__title"><?php echo esc_html( $t['h1'] ); ?></h1>
				<p class="lpb-hero__lede"><?php echo esc_html( $t['sub'] ); ?></p>
				<p class="lpb-price__meta"><?php echo esc_html( $lpx_fmt( $lpx_prices[1] ) . ' · ' . $t['ship'] ); ?></p>
				<?php if ( $t['cod'] ) : ?>
					<p class="lpb-cod"><strong><?php echo esc_html( $t['cod_label'] ); ?></strong> <?php echo esc_html( $t['cod'] ); ?></p>
				<?php endif; ?>
				<a class="lpb-btn" href="#lpx-bundle"><?php echo esc_html( $t['bundle_h'] ); ?></a>
			</div>
		</div>
	</section>

	<section class="lpb-section lpb-section--cream" id="lpx-bundle" aria-label="<?php echo esc_attr( $t['bundle_h'] ); ?>">
		<div class="lpb-section__head">
			<h2><?php echo esc_html( $t['bundle_h'] ); ?></h2>
			<p class="lpb-lede"><?php echo esc_html( $t['bundle_p'] ); ?></p>
		</div>
		<div class="lpb-section__cta"><?php $lpx_picker( 'main' ); ?></div>
	</section>

	<section class="lpb-section" aria-label="<?php echo esc_attr( $t['why_h'] ); ?>">
		<div class="lpb-section__head"><h2><?php echo esc_html( $t['why_h'] ); ?></h2></div>
		<div class="lpb-cards lpb-cards--3">
			<?php foreach ( $t['why'] as $card ) : ?>
				<div class="lpb-card"><h3><?php echo esc_html( $card[0] ); ?></h3><p><?php echo esc_html( $card[1] ); ?></p></div>
			<?php endforeach; ?>
		</div>
		<?php if ( $lpx_s2 ) : ?><div class="lpx-figure"><?php echo $lpx_s2; // phpcs:ignore WordPress.Security.EscapeOutput ?></div><?php endif; ?>
	</section>

	<section class="lpb-section lpb-section--cream" aria-label="<?php echo esc_attr( $t['how_h'] ); ?>">
		<div class="lpb-section__head"><h2><?php echo esc_html( $t['how_h'] ); ?></h2></div>
		<ol class="lpb-steps">
			<?php foreach ( $t['steps'] as $i => $step ) : ?>
				<li><span class="lpb-steps__num"><?php echo esc_html( sprintf( '%02d', $i + 1 ) ); ?></span><?php echo esc_html( $step ); ?></li>
			<?php endforeach; ?>
		</ol>
	</section>

	<section class="lpb-section" aria-label="<?php echo esc_attr( $t['story_h'] ); ?>">
		<div class="lpb-section__head">
			<h2><?php echo esc_html( $t['story_h'] ); ?></h2>
			<p class="lpb-lede"><?php echo esc_html( $t['story'] ); ?></p>
		</div>
		<?php if ( $lpx_s3 ) : ?><div class="lpx-figure"><?php echo $lpx_s3; // phpcs:ignore WordPress.Security.EscapeOutput ?></div><?php endif; ?>
	</section>

	<section class="lpb-section lpb-section--cream" aria-label="<?php echo esc_attr( $t['order_h'] ); ?>">
		<div class="lpb-section__head">
			<h2><?php echo esc_html( $t['order_h'] ); ?></h2>
			<p class="lpb-lede"><?php echo esc_html( $t['order_p'] . ' ' . $t['ship'] . '.' ); ?></p>
		</div>
		<div class="lpb-section__cta"><?php $lpx_picker( 'order' ); ?></div>
	</section>

	<section class="lpb-section" aria-label="FAQ">
		<div class="lpb-section__head"><h2><?php echo esc_html( $t['faq_h'] ); ?></h2></div>
		<div class="lpb-faq">
			<?php foreach ( $t['faq'] as $qa ) : ?>
				<details><summary><?php echo esc_html( $qa[0] ); ?></summary><p><?php echo esc_html( $qa[1] ); ?></p></details>
			<?php endforeach; ?>
		</div>
	</section>

</main>

<?php
get_footer();
