<?php
/**
 * Christmas 2026 gift landing (Issue #251) — shared CZ/EN body.
 *
 * Expects $lpx_lang ('cz'|'en') from page-vanocni-darek-molosoc.php /
 * page-christmas-gift-molosoc.php. Structure and classes follow Landing B
 * (landing-b.css is a dependency of landing-xmas.css); copy lives in the
 * $t array below, one entry per language. No countdown, no scarcity, no
 * free-gift-wrap claim, no medical claim. One order-by line (18 December,
 * Issue #269 decision) and no crossed-out reference price (Issue #269).
 * Issue #287: every size row carries a visible "1. pár / Pair 1" label on
 * every width, and the size error is a red live region (landing-xmas.js
 * also outlines + scrolls to the first pair row without a size).
 * Issue #295: the size ranges, "from" shipping price and order-by date come
 * from molosoc_xmas_facts() (inc/landing-xmas.php); the hero line, the size
 * buttons, the FAQ, the 3-line info block under each checkout button and the
 * size hint under the pair-1 label all read the same values.
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
$lpx_fcz   = molosoc_xmas_facts( 'cz' );
$lpx_fen   = molosoc_xmas_facts( 'en' );

$copy = array(
	'cz' => array(
		'label'     => 'Vánoční dárek MOLOSOC',
		'eyebrow'   => 'Vánoce 2026',
		'h1'        => 'Darujte péči, která nekončí Vánocemi.',
		'sub'       => 'Malý dárek pro maminku, partnera nebo někoho, na kom vám záleží. MOLOSOC pomáhá proměnit obyčejný krém na nohy v jednoduchý pečující rituál.',
		'ship'      => 'Doprava od ' . $lpx_fcz['ship_from'] . ' Kč',
		'deadline'  => sprintf( 'Objednejte do %s, doručíme před Vánoci.', $lpx_fcz['order_by'] ),
		'cod'       => molosoc_cod_cz_text(),
		'cod_label' => 'Dobírka:',
		'cta'       => 'Pokračovat k pokladně',
		'pairs'     => array( 1 => '1 pár', 2 => '2 páry', 3 => '3 páry' ),
		'pair_n'    => '%d. pár',
		'size'      => 'Velikost',
		'size_err'  => 'Vyberte velikost pro každý pár.',
		'size_err_n' => 'Vyberte velikost pro %d. pár.',
		'size_hint' => 'Řiďte se podle velikosti bot.', // Žaneta, Issue #307
		'facts'     => array(
			array( 'size', sprintf( 'Velikost: M = %s · L = %s (podle velikosti bot)', $lpx_fcz['size_m'], $lpx_fcz['size_l'] ) ),
			array( 'ship', sprintf( 'Doprava od %d Kč · můžete platit i dobírkou', $lpx_fcz['ship_from'] ) ),
			array( 'date', sprintf( 'Objednejte do %s, doručíme před Vánoci', $lpx_fcz['order_by'] ) ),
		),
		'bundle_h'  => 'Vyberte dárkový set',
		'bundle_p'  => 'Zvolte počet párů a velikost M nebo L pro každý z nich. Cena se započítá v pokladně.',
		'sizes'     => array( 'M' => 'M (' . $lpx_fcz['size_m'] . ')', 'L' => 'L (' . $lpx_fcz['size_l'] . ')' ),
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
		'order_p'   => 'Bezpečná platba přes Comgate.',
		'faq_h'     => 'Časté otázky',
		'faq'       => array(
			array( 'Jakou velikost vybrat?', sprintf( 'M sedí na velikost nohy %s, L na %s. Pokud si nejste jistí, zeptejte se obdarovaného na velikost bot.', $lpx_fcz['size_m'], $lpx_fcz['size_l'] ) ),
			array( 'Kolik stojí doprava a platba?', sprintf( 'Doprava od %d Kč. Objednejte do %s, doručíme před Vánoci. Platbu a dopravu vybíráte v pokladně; ', $lpx_fcz['ship_from'], $lpx_fcz['order_by'] ) . molosoc_cod_cz_text() ),
			array( 'Jak se o návleky starat?', 'Po použití je umyjte mýdlem a vodou, nechte uschnout a použijte znovu.' ),
			array( 'Je to vhodné jako dárek?', 'Ano – je to malý praktický dárek k domácí péči o nohy. Dárkové balení v ceně není; objednávka přijde v běžném balení.' ),
		),
	),
	'en' => array(
		'label'     => 'MOLOSOC Christmas gift',
		'eyebrow'   => 'Christmas 2026',
		'h1'        => 'Give care that doesn\'t end with Christmas.',
		'sub'       => 'A small gift for your mum, partner or someone you care about. MOLOSOC turns an ordinary foot cream into a simple caring ritual.',
		'ship'      => 'Shipping from ' . $lpx_fen['ship_from'] . ' CZK',
		'deadline'  => sprintf( 'Order by %s for delivery before Christmas.', $lpx_fen['order_by'] ),
		'cod'       => '',
		'cod_label' => '',
		'cta'       => 'Continue to checkout',
		'pairs'     => array( 1 => '1 pair', 2 => '2 pairs', 3 => '3 pairs' ),
		'pair_n'    => 'Pair %d',
		'size'      => 'Size',
		'size_err'  => 'Please choose a size for every pair.',
		'size_err_n' => 'Please choose a size for pair %d.',
		'size_hint' => 'Not sure? Ask for their shoe size.',
		'facts'     => array(
			array( 'size', sprintf( 'Size: M = EU %s · L = EU %s (by shoe size)', $lpx_fen['size_m'], $lpx_fen['size_l'] ) ),
			array( 'ship', sprintf( 'Shipping from %d CZK', $lpx_fen['ship_from'] ) ), // Issue #297: COD is offered in CZ/SK only, so the EN page does not mention it.
			array( 'date', sprintf( 'Order by %s for delivery before Christmas', $lpx_fen['order_by'] ) ),
		),
		'bundle_h'  => 'Choose your gift set',
		'bundle_p'  => 'Pick how many pairs, then size M or L for each. The price is applied at checkout.',
		'sizes'     => array( 'M' => 'M (EU ' . $lpx_fen['size_m'] . ')', 'L' => 'L (EU ' . $lpx_fen['size_l'] . ')' ),
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
		'order_p'   => 'Secure payment via Comgate.',
		'faq_h'     => 'FAQ',
		'faq'       => array(
			array( 'Which size should I choose?', sprintf( 'M fits shoe sizes EU %s, L fits %s. If unsure, ask the recipient for their shoe size.', $lpx_fen['size_m'], $lpx_fen['size_l'] ) ),
			array( 'What do shipping and payment cost?', sprintf( 'Shipping from %d CZK. Order by %s for delivery before Christmas. Shipping and payment methods are chosen at checkout.', $lpx_fen['ship_from'], $lpx_fen['order_by'] ) ),
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
		'url'     => '', // filled from the size picks by landing-xmas.js
	);
}
$lpx_checkout = molosoc_xmas_checkout_url( $lpx_lang );
$lpx_avail    = molosoc_xmas_variations(); // sizes with a purchasable variation right now.
$lpx_buyable  = count( $lpx_avail ) > 0;

/** Issue #295: the three 16 px line icons of the info block (stroke = text colour). */
$lpx_icon = static function ( $name ) {
	$paths = array(
		'size' => '<path d="M3 15.5 15.5 3l5.5 5.5L8.5 21z"/><path d="m7 12 2 2M10 9l2 2M13 6l2 2"/>',
		'ship' => '<path d="M3 6h11v10H3z"/><path d="M14 10h4l3 3v3h-7z"/><circle cx="7" cy="18" r="1.6"/><circle cx="17" cy="18" r="1.6"/>',
		'date' => '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
	);
	if ( ! isset( $paths[ $name ] ) ) {
		return '';
	}
	return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">' . $paths[ $name ] . '</svg>';
};

/** Bundle picker: a fieldset of 1/2/3 pairs, then a size fieldset per pair, the button, then the 3 facts (Issue #295). */
$lpx_picker = static function ( $id ) use ( $t, $lpx_sizes, $lpx_base, $lpx_fmt, $lpx_url, $lpx_checkout, $lpx_buyable, $lpx_avail, $lpx_icon ) {
	?>
	<div class="lpb-buy lpx-buy" data-lpx-buy data-lpx-checkout-url="<?php echo esc_url( $lpx_checkout ); ?>" data-lpx-enabled="<?php echo $lpx_buyable ? '1' : '0'; ?>" data-lpx-err-pair="<?php echo esc_attr( $t['size_err_n'] ); ?>">
		<fieldset class="lpx-bundles">
			<legend class="lpb-buy__legend"><?php echo esc_html( $t['bundle_h'] ); ?></legend>
			<?php foreach ( $lpx_base as $n => $b ) : ?>
				<label class="lpx-bundle">
					<input type="radio" name="lpx-pairs-<?php echo esc_attr( $id ); ?>" value="<?php echo (int) $n; ?>"<?php echo 1 === $n ? ' checked' : ''; ?>>
					<span class="lpx-bundle__body">
						<span class="lpx-bundle__name"><?php echo esc_html( $t['pairs'][ $n ] ); ?></span>
						<span class="lpx-bundle__price" translate="no"><?php echo esc_html( $lpx_fmt( $b['total'] ) ); ?></span>
					</span>
				</label>
			<?php endforeach; ?>
		</fieldset>
		<?php foreach ( array( 1, 2, 3 ) as $n ) : ?>
			<fieldset class="lpb-buy__sizes lpx-pair" data-lpx-pair="<?php echo (int) $n; ?>"<?php echo $n > 1 ? ' hidden' : ''; ?>>
				<legend class="lpb-buy__legend lpx-pair__legend"><span class="lpx-pair__num"><?php echo esc_html( sprintf( $t['pair_n'], $n ) ); ?></span> <span class="lpx-pair__size"><?php echo esc_html( '· ' . $t['size'] ); ?></span></legend>
				<?php if ( 1 === $n ) : ?>
					<p class="lpx-pair__hint"><?php echo esc_html( $t['size_hint'] ); ?></p>
				<?php endif; ?>
				<?php foreach ( $lpx_sizes as $key => $label ) : ?>
					<label class="lpb-size">
						<input type="radio" name="lpx-size-<?php echo esc_attr( $id ); ?>-<?php echo (int) $n; ?>" value="<?php echo esc_attr( $key ); ?>"<?php echo $lpx_buyable && ! isset( $lpx_avail[ $key ] ) ? ' disabled' : ''; ?>>
						<span class="lpb-size__label"><?php echo esc_html( $label ); ?></span>
					</label>
				<?php endforeach; ?>
			</fieldset>
		<?php endforeach; ?>
		<a class="lpb-btn lpb-buy__btn" href="<?php echo esc_url( $lpx_url() ); ?>" data-lpx-go rel="nofollow"><?php echo esc_html( $t['cta'] ); ?></a>
		<p class="lpb-buy__error lpx-buy__error" role="alert" aria-live="assertive" aria-atomic="true" data-lpx-err="<?php echo esc_attr( $t['size_err'] ); ?>" hidden><?php echo esc_html( $t['size_err'] ); ?></p>
		<ul class="lpx-facts">
			<?php foreach ( $t['facts'] as $fact ) : ?>
				<li><?php echo $lpx_icon( $fact[0] ); // phpcs:ignore WordPress.Security.EscapeOutput -- static inline SVG built above. ?><span><?php echo esc_html( $fact[1] ); ?></span></li>
			<?php endforeach; ?>
		</ul>
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
				<p class="lpx-deadline"><?php echo esc_html( $t['deadline'] ); ?></p>
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

	<?php
	/* Issue #284: the numbered 1-2-3 anonymous customer feedback from Landing B (#281), CZ page only (the summaries are Czech editorial indirect speech, not translated). Issue #305: all three items are shown, exactly as on Landing B — Žaneta confirmed anonymous republication permission and the wording of items 2 and 3 (ZANETA_DECISION 2026-10-27 on Landing B, re-confirmed in chat 2026-10-30); the former `molosoc_landing_b_feedback_extra_enabled` gate is gone. No quotation marks, names, verified-buyer or medical claims. */
	if ( 'cz' === $lpx_lang ) :
		?>
	<section class="lpb-section" aria-label="Co o nás říkají zákazníci">
		<figure class="lpb-testimonial">
			<p class="lpb-testimonial__title">Co o nás říkají zákazníci</p>
			<ol class="lpb-testimonial__list">
				<li>Jedna zákaznice nám napsala, že její maminka je s návleky MOLOSOC velmi spokojená a pohodlně je nosí přibližně 30 minut.</li>
				<li>Další zákaznice popsala, že má po použití návleků chodidla hebká jako dětskou pokožku.</li>
				<li>Jiná zákaznice nám napsala, že si návleky natolik oblíbila, že je nechce odložit.</li>
			</ol>
		</figure>
	</section>
	<?php endif; ?>

	<section class="lpb-section lpb-section--cream" aria-label="<?php echo esc_attr( $t['order_h'] ); ?>">
		<div class="lpb-section__head">
			<h2><?php echo esc_html( $t['order_h'] ); ?></h2>
			<p class="lpb-lede"><?php echo esc_html( $t['order_p'] . ' ' . $t['ship'] . '. ' . $t['deadline'] ); ?></p>
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
