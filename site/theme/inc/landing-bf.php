<?php
/**
 * Black Friday 2026 Meta landing pages (Issue #378) — CZ + EN.
 *
 * New campaign pages, not replacements: the Christmas pages 1065 / 1066 keep
 * their slugs, copy, photos and code path. The Black Friday pages render the
 * SAME template part (template-parts/landing-xmas.php, $lpx_campaign = 'bf')
 * so the bundle selector (1 / 2 / 3 / 4+ pairs, M/L per pair), its JS, the
 * server-side add-to-cart (molosoc_xmas_add_to_cart()), the slot-tag pricing
 * (209 Kč first pair + 199 Kč each further pair, 3 pairs 607 Kč), checkout,
 * shipping, tax, payments and consent/tracking are byte-for-byte the code the
 * Christmas pages run. Only copy, photos, colours and head tags differ.
 *
 * Templates: page-black-friday-molosoc.php (CZ, /cz/black-friday-molosoc/) and
 * page-black-friday-offer-molosoc.php (EN, /black-friday-offer-molosoc/).
 * Slug collision check (23 Nov 2026): no page, template, redirect or test in
 * this repository uses either slug. The two languages need two different slugs
 * because Polylang Free (this site) cannot give two pages the same slug — the
 * second one would be saved as "black-friday-molosoc-2". The live site could
 * not be checked from the implementation session; WordPress itself refuses a
 * duplicate slug when the draft is created (create-wp-page.yml).
 *
 * How the pages join the Christmas landing family: molosoc_xmas_current_lang()
 * also answers for these two slugs (one line in inc/landing-xmas.php), so every
 * existing gate keyed on molosoc_is_xmas_landing() applies unchanged — Landing B
 * + landing-xmas CSS/JS, the unused-plugin-asset dequeue, the delayed gtag.js
 * (#301), the light header logo, the in-page sticky pill (#299), and the
 * Christmas announcement bar stays OFF here. What must differ is decided by
 * molosoc_bf_current_lang() in this file: title/description, hero preload,
 * Open Graph tags, the sticky pill label, the stock-refusal return page, the
 * release gate and the Black Friday stylesheet.
 *
 * Nothing here creates or publishes a WP page, changes a price, a shipping
 * rate, the checkout, the Meta pixel, Clarity, WPConsent or order attribution.
 */

defined( 'ABSPATH' ) || exit;

/** Page slugs: CZ and EN (see the collision note above). */
function molosoc_bf_slugs() {
	return array( 'cz' => 'black-friday-molosoc', 'en' => 'black-friday-offer-molosoc' );
}

/** 'cz' | 'en' | '' for the current request. */
function molosoc_bf_current_lang() {
	if ( ! function_exists( 'is_page' ) ) {
		return '';
	}
	foreach ( molosoc_bf_slugs() as $lang => $slug ) {
		if ( is_page( $slug ) ) {
			return $lang;
		}
	}
	return '';
}

/** True on either Black Friday page. */
function molosoc_is_bf_landing() {
	return '' !== molosoc_bf_current_lang();
}

/**
 * Release flag: indexable by default, the same as the Christmas pages today
 * (#260). The pages are not public at all until Žaneta publishes the drafts;
 * the filter can switch noindex + sitemap exclusion on without a deploy of
 * the template.
 */
function molosoc_bf_published() {
	return (bool) apply_filters( 'molosoc_bf_published', true );
}

/** URL of the Black Friday page of $lang (falls back to the expected permalink). */
function molosoc_bf_page_url( $lang ) {
	$slugs = molosoc_bf_slugs();
	$slug  = 'en' === $lang ? $slugs['en'] : $slugs['cz'];
	$page  = function_exists( 'get_page_by_path' ) ? get_page_by_path( $slug ) : null;
	if ( $page && 'publish' === get_post_status( $page ) ) {
		return get_permalink( $page );
	}
	return home_url( 'en' === $lang ? '/' . $slug . '/' : '/cz/' . $slug . '/' );
}

/**
 * Header globe / language switcher (Issue #386). The globe is Polylang's
 * switcher item in the primary menu. On a page with no Polylang translation,
 * Polylang builds each link as the other language's HOMEPAGE and then passes it
 * through `pll_the_language_link`. The two Black Friday pages are not linked as
 * a Polylang pair on the live site (#384's link workflow was never run), so EN on
 * /cz/black-friday-molosoc/ went to Home. On the two Black Friday pages only, map
 * the switcher straight to the other language's Black Friday page. This is the
 * same approach as molosoc_product_language_switcher_link() for the product. It
 * works whether or not the pair is ever linked. Every other page, and the top
 * bar (inc/xmas-bar.php, which never uses the switcher), is unchanged.
 */
function molosoc_bf_language_switcher_link( $url, $slug ) {
	if ( ( 'cz' !== $slug && 'en' !== $slug ) || ! molosoc_is_bf_landing() ) {
		return $url;
	}
	return molosoc_bf_page_url( $slug );
}
add_filter( 'pll_the_language_link', 'molosoc_bf_language_switcher_link', 10, 2 );

/* ---------- campaign end (Issue #382) ---------- */

/**
 * Black Friday ends Mon 30 Nov 2026 23:59 Europe/Prague, i.e. the offer is
 * over from Tue 1 Dec 2026 00:00 Prague (= 2026-11-30 23:00 UTC; DateTimeZone
 * applies CET, so no hand-written offset). One source for: the site-wide bar
 * (inc/xmas-bar.php, BF text until then, Christmas text from then), the 302
 * from both Black Friday pages to the Christmas pages, and the client-side
 * guards that make a page cached before the switch behave the same.
 */
function molosoc_bf_end_ts() {
	return ( new DateTimeImmutable( '2026-12-01 00:00:00', new DateTimeZone( 'Europe/Prague' ) ) )->getTimestamp();
}

/** "Now" as a Unix timestamp; `molosoc_bf_now` lets a test or staging fake the date. */
function molosoc_bf_now() {
	return (int) apply_filters( 'molosoc_bf_now', time() );
}

/** True until 30 Nov 2026 23:59:59 Prague. */
function molosoc_bf_active() {
	return molosoc_bf_now() < molosoc_bf_end_ts();
}

/** The end-date wording: 'bar' (top bar) or 'page' (BF page hero + order block). */
function molosoc_bf_until_text( $lang, $where = 'page' ) {
	if ( 'en' === $lang ) {
		return 'bar' === $where ? 'Until Monday 30 Nov' : 'Offer valid until Monday 30 Nov.';
	}
	return 'bar' === $where ? 'Platí do pondělí 30. 11.' : 'Nabídka platí do pondělí 30. 11.';
}

/** Where an expired Black Friday page sends visitors: the Christmas page of the same language. */
function molosoc_bf_expired_url( $lang ) {
	return molosoc_xmas_page_url( 'en' === $lang ? 'en' : 'cz' );
}

/**
 * After the end, both Black Friday pages answer 302 to the Christmas page,
 * keeping the query string (utm_*, fbclid) so old ad links stay attributed.
 * The response is never cached (DONOTCACHEPAGE + nocache headers).
 */
function molosoc_bf_expired_redirect() {
	$lang = molosoc_bf_current_lang();
	if ( ! $lang || molosoc_bf_active() ) {
		return;
	}
	if ( ! defined( 'DONOTCACHEPAGE' ) ) {
		define( 'DONOTCACHEPAGE', true );
	}
	$url = molosoc_bf_expired_url( $lang );
	$qs  = isset( $_SERVER['QUERY_STRING'] ) ? (string) wp_unslash( $_SERVER['QUERY_STRING'] ) : ''; // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
	if ( '' !== $qs ) {
		$url .= ( false === strpos( $url, '?' ) ? '?' : '&' ) . $qs;
	}
	nocache_headers();
	wp_safe_redirect( $url, 302, 'MOLOSOC' );
	exit;
}
add_action( 'template_redirect', 'molosoc_bf_expired_redirect', 1 );

/**
 * The same switch for a copy of the page that WP-Optimize cached before the
 * end (its advanced-cache serves HTML without running PHP): the first thing
 * in <head> compares the visitor's clock with the end time and replaces the
 * location with the Christmas page (query string and hash kept).
 */
function molosoc_bf_expired_guard() {
	$lang = molosoc_bf_current_lang();
	if ( ! $lang ) {
		return;
	}
	printf(
		'<script>(function(){if(Date.now()>=%d){location.replace(%s+location.search+location.hash);}})();</script>' . "\n",
		(int) molosoc_bf_end_ts() * 1000,
		wp_json_encode( molosoc_bf_expired_url( $lang ) )
	);
}
add_action( 'wp_head', 'molosoc_bf_expired_guard', 0 );

/** "209 Kč" / "209 CZK". */
function molosoc_bf_money( $n, $lang ) {
	return 'en' === $lang ? number_format_i18n( $n ) . ' CZK' : number_format_i18n( $n ) . ' Kč';
}

/**
 * Page copy, same keys as the Christmas $copy array in
 * template-parts/landing-xmas.php. Rules (Issue #378): native Czech and
 * English, no Christmas wording, no order-by date (deadline = the offer's
 * end date since Issue #382), no percentage saving, no countdown, no stock pressure, no promotion that is not
 * the real bundle price list. Prices and facts are read from the same
 * functions the checkout uses, so the copy can never quote another price.
 *
 * @param string $lang 'cz' | 'en'.
 * @return array
 */
function molosoc_bf_copy( $lang ) {
	$p     = molosoc_xmas_unit_prices();
	$f     = molosoc_xmas_facts( 'en' === $lang ? 'en' : 'cz' );
	$first = molosoc_bf_money( $p[1], $lang );
	$next  = molosoc_bf_money( $p[2], $lang );
	$three = molosoc_bf_money( molosoc_xmas_bundle_total( 3 ), $lang ); // Issue #388: hero price line.
	if ( 'en' === $lang ) {
		return array(
			'label'      => 'MOLOSOC Black Friday',
			'eyebrow'    => 'Black Friday',
			'h1'         => 'The cream stays on your feet. You can keep moving.', // Issue #388: the first screen continues the ad.
			'sub'        => 'Reusable nitrile MOLOSOC covers – apply cream, slip them on, and after 20–30 minutes your feet feel soft. No slipping, no greasy marks.',
			'price_line' => sprintf( 'Black Friday: first pair %1$s, each extra pair %2$s · 3 pairs %3$s', $first, $next, $three ),
			'clip_pause' => 'Pause video',
			'clip_play'  => 'Play video',
			'ship'       => 'Shipping from ' . $f['ship_from'] . ' CZK',
			'deadline'   => molosoc_bf_until_text( 'en' ), // Issue #382: hero line under the price + the order block lede.
			'cod'        => '',
			'cod_label'  => '',
			'cta'        => 'Add to cart',
			'pairs'      => array( 1 => '1 pair', 2 => '2 pairs', 3 => '3 pairs' ),
			'multi'      => '4 or more pairs',
			'from'       => 'from %s',
			'teaser'     => 'Want more? Choose 4 or more pairs – every extra pair just %s.',
			'multi_h'    => 'Pairs per size',
			'less'       => 'Remove a pair of size %s',
			'more'       => 'Add a pair of size %s',
			'min_err'    => 'Choose at least %d pairs.',
			'pair_n'     => 'Pair %d',
			'size'       => 'Size',
			'size_err'   => 'Please choose a size for every pair.',
			'size_err_n' => 'Please choose a size for pair %d.',
			'size_hint'  => 'Go by your shoe size.',
			'facts'      => array(
				array( 'size', sprintf( 'Size: M = EU %s · L = EU %s (by shoe size)', $f['size_m'], $f['size_l'] ) ),
				array( 'ship', sprintf( 'Shipping from %d CZK', $f['ship_from'] ) ), // Issue #297: COD is CZ/SK only.
			),
			'bundle_h'   => 'Choose your set',
			'pick'       => 'Choose your set',
			'bundle_p'   => 'Pick how many pairs, then size M or L for each. The price is applied at checkout.',
			'sizes'      => array( 'M' => 'M (EU ' . $f['size_m'] . ')', 'L' => 'L (EU ' . $f['size_l'] . ')' ),
			'why_h'      => 'Why MOLOSOC',
			'why'        => array(
				array( 'A simple ritual', 'Apply your cream, put the covers on, sit down for a moment. The cream stays on your feet and you can still move around.' ),
				array( 'Made to be reused', 'Each cover lasts at least 10 uses – just wash it with soap and water after use.' ),
				array( 'Works with the cream you have', 'Use it with any foot cream, balm or oil. Nothing else to buy.' ),
			),
			'how_h'      => 'How it works',
			'steps'      => array( 'Wash and dry your feet', 'Apply cream, balm or oil', 'Put MOLOSOC on and relax for 20–30 minutes' ),
			'story_h'    => 'Made by a mother and her daughter',
			'story'      => 'MOLOSOC started at home, in the bathroom: we put cream on our feet and wondered what to do next. We wanted something that keeps the cream on the foot and still lets you move around. So we made it ourselves.',
			'order_h'    => 'Order your set',
			'order_p'    => 'Secure payment via Comgate.',
			'faq_h'      => 'FAQ',
			'faq'        => array(
				array( 'Which size should I choose?', sprintf( 'M fits shoe sizes EU %s, L fits %s. Go by your shoe size.', $f['size_m'], $f['size_l'] ) ),
				array( 'Can I mix sizes in one set?', 'Yes – you choose M or L for every pair; with 4 or more pairs you set how many pairs of each size.' ),
				array( 'What do shipping and payment cost?', sprintf( 'Shipping from %d CZK. Shipping and payment methods are chosen at checkout.', $f['ship_from'] ) ),
				array( 'How do I care for the covers?', 'Wash with soap and water after use, let them dry and use them again.' ),
			),
		);
	}
	return array(
		'label'      => 'Black Friday MOLOSOC',
		'eyebrow'    => 'Black Friday',
		'h1'         => 'Krém zůstane na noze. Vy se můžete hýbat.', // Issue #388: the first screen continues the ad.
		'sub'        => 'Nitrilové návleky MOLOSOC na opakované použití – namažete, nasadíte a za 20–30 minut máte hebká chodidla. Bez klouzání a bez mastných stop.',
		'price_line' => sprintf( 'Black Friday: první pár %1$s, každý další %2$s · 3 páry %3$s', $first, $next, $three ),
		'clip_pause' => 'Pozastavit video',
		'clip_play'  => 'Přehrát video',
		'ship'       => 'Doprava od ' . $f['ship_from'] . ' Kč',
		'deadline'   => molosoc_bf_until_text( 'cz' ), // Issue #382: hero line under the price + the order block lede.
		'cod'        => molosoc_cod_cz_text(),
		'cod_label'  => 'Dobírka:',
		'cta'        => 'Do košíku',
		'pairs'      => array( 1 => '1 pár', 2 => '2 páry', 3 => '3 páry' ),
		'multi'      => '4 a více párů',
		'from'       => 'od %s',
		'teaser'     => 'Chcete víc? Vyberte 4 a více párů – každý další pár jen za %s.',
		'multi_h'    => 'Počet párů podle velikosti',
		'less'       => 'Ubrat pár velikosti %s',
		'more'       => 'Přidat pár velikosti %s',
		'min_err'    => 'Vyberte alespoň %d páry.',
		'pair_n'     => '%d. pár',
		'size'       => 'Velikost',
		'size_err'   => 'Vyberte velikost pro každý pár.',
		'size_err_n' => 'Vyberte velikost pro %d. pár.',
		'size_hint'  => 'Řiďte se podle velikosti bot.',
		'facts'      => array(
			array( 'size', sprintf( 'Velikost: M = %s · L = %s (podle velikosti bot)', $f['size_m'], $f['size_l'] ) ),
			array( 'ship', sprintf( 'Doprava od %d Kč · můžete platit i dobírkou', $f['ship_from'] ) ),
		),
		'bundle_h'   => 'Vyberte svůj set',
		'pick'       => 'Vybrat set',
		'bundle_p'   => 'Zvolte počet párů a velikost M nebo L pro každý z nich. Cena se započítá v pokladně.',
		'sizes'      => array( 'M' => 'M (' . $f['size_m'] . ')', 'L' => 'L (' . $f['size_l'] . ')' ),
		'why_h'      => 'Proč MOLOSOC',
		'why'        => array(
			array( 'Jednoduchý rituál', 'Namazat, nasadit, chvíli si sednout. Krém zůstane na chodidlech a vy se můžete normálně pohybovat.' ),
			array( 'Na opakované použití', 'Návlek vydrží alespoň 10 použití – po použití ho stačí umýt mýdlem a vodou.' ),
			array( 'S krémem, který už máte', 'Funguje s jakýmkoliv krémem, balzámem nebo olejem na nohy. Nic dalšího není potřeba kupovat.' ),
		),
		'how_h'      => 'Jak to funguje',
		'steps'      => array( 'Umýt a osušit nohy', 'Namazat krémem, balzámem nebo olejem', 'Nasadit MOLOSOC a 20–30 minut si odpočinout' ),
		'story_h'    => 'Vytvořily jsme ho my – máma s dcerou',
		'story'      => 'MOLOSOC vznikl doma, v koupelně: namazaly jsme si nohy krémem a nevěděly, co dál. Hledaly jsme něco, co udrží krém na noze a dovolí nám normálně se pohybovat. Tak jsme to vytvořily samy.',
		'order_h'    => 'Objednejte svůj set',
		'order_p'    => 'Bezpečná platba přes Comgate.',
		'faq_h'      => 'Časté otázky',
		'faq'        => array(
			array( 'Jakou velikost vybrat?', sprintf( 'M sedí na velikost nohy %s, L na %s. Řiďte se podle velikosti bot.', $f['size_m'], $f['size_l'] ) ),
			array( 'Můžu v jednom setu kombinovat velikosti?', 'Ano – u každého páru zvolíte M nebo L zvlášť; u 4 a více párů nastavíte počet párů každé velikosti.' ),
			array( 'Kolik stojí doprava a platba?', sprintf( 'Doprava od %d Kč. Platbu a dopravu vybíráte v pokladně; ', $f['ship_from'] ) . molosoc_cod_cz_text() ),
			array( 'Jak se o návleky starat?', 'Po použití je umyjte mýdlem a vodou, nechte uschnout a použijte znovu.' ),
		),
	);
}

/* ---------- document title, description, Open Graph ---------- */

/** Title + description of $lang (read by molosoc_xmas_meta() on these pages). */
function molosoc_bf_meta( $lang ) {
	$p = molosoc_xmas_unit_prices();
	if ( 'en' === $lang ) {
		return array(
			'title' => 'Black Friday: reusable foot covers | Molosoc',
			'desc'  => sprintf( 'Black Friday at MOLOSOC: reusable nitrile foot covers that turn any foot cream into a simple ritual. First pair %1$s, every extra pair %2$s. Pick 1 to %3$d pairs.', molosoc_bf_money( $p[1], 'en' ), molosoc_bf_money( $p[2], 'en' ), molosoc_xmas_max_pairs() ),
		);
	}
	return array(
		'title' => 'Black Friday: návleky na nohy MOLOSOC | Molosoc',
		'desc'  => sprintf( 'Black Friday u MOLOSOC: opakovaně použitelné nitrilové návleky na nohy. První pár %1$s, každý další %2$s. Vyberte 1 až %3$d párů.', molosoc_bf_money( $p[1], 'cz' ), molosoc_bf_money( $p[2], 'cz' ), molosoc_xmas_max_pairs() ),
	);
}

/**
 * Open Graph + Twitter card tags (link previews in Meta ads / Messenger /
 * WhatsApp). The theme prints no OG tags anywhere else, so there is nothing to
 * duplicate. og:url is the page's own permalink (= WordPress's rel=canonical);
 * og:locale:alternate names the other language. hreflang cs/en comes from
 * Polylang once the two pages are linked as translations, x-default from
 * functions.php.
 */
function molosoc_bf_og_tags() {
	$lang = molosoc_bf_current_lang();
	if ( ! $lang ) {
		return;
	}
	$meta = molosoc_bf_meta( $lang );
	$id   = function_exists( 'get_queried_object_id' ) ? (int) get_queried_object_id() : 0;
	$url  = $id ? get_permalink( $id ) : molosoc_bf_page_url( $lang );
	$img  = molosoc_bf_image_set( 'hero' );
	$tags = array(
		'og:type'             => 'website',
		'og:site_name'        => 'MOLOSOC',
		'og:locale'           => 'en' === $lang ? 'en_US' : 'cs_CZ',
		'og:locale:alternate' => 'en' === $lang ? 'cs_CZ' : 'en_US',
		'og:title'            => $meta['title'],
		'og:description'      => $meta['desc'],
		'og:url'              => $url,
	);
	foreach ( $tags as $prop => $value ) {
		printf( '<meta property="%s" content="%s">' . "\n", esc_attr( $prop ), 'og:url' === $prop ? esc_url( $value ) : esc_attr( $value ) );
	}
	if ( $img ) {
		printf( '<meta property="og:image" content="%s">' . "\n", esc_url( $img['og'] ) );
		printf( '<meta property="og:image:width" content="%d">' . "\n", (int) $img['og_w'] );
		printf( '<meta property="og:image:height" content="%d">' . "\n", (int) $img['og_h'] );
		printf( '<meta property="og:image:alt" content="%s">' . "\n", esc_attr( molosoc_bf_image_alt( 'hero', $lang ) ) );
	}
	echo '<meta name="twitter:card" content="summary_large_image">' . "\n";
}
add_action( 'wp_head', 'molosoc_bf_og_tags', 3 );

/* ---------- release gate (noindex + sitemap only when switched off) ---------- */

add_filter( 'wp_robots', function ( $robots ) {
	if ( molosoc_is_bf_landing() && ! molosoc_bf_published() ) {
		$robots['noindex']  = true;
		$robots['nofollow'] = false;
	}
	return $robots;
} );

add_filter( 'wp_sitemaps_posts_query_args', function ( $args, $post_type ) {
	if ( 'page' === $post_type && ! molosoc_bf_published() ) {
		$ids = array();
		foreach ( molosoc_bf_slugs() as $slug ) {
			$page = get_page_by_path( $slug );
			if ( $page ) {
				$ids[] = (int) $page->ID;
			}
		}
		$args['post__not_in'] = array_merge( isset( $args['post__not_in'] ) ? (array) $args['post__not_in'] : array(), $ids );
	}
	return $args;
}, 10, 2 );

/* ---------- photos ---------- */

/**
 * Hero (Issue #380): Žaneta's Black Friday ad image
 * (assets/images/molosoc_black_friday_ad.webp, 1254 x 1254, uploaded to main)
 * resized — never cropped or retouched — to square WebP at 480 / 800 / 1200 px
 * in assets/images/black-friday/. The artwork itself carries the big
 * "BLACK FRIDAY" lettering, so the page does not repeat it as a second visual
 * headline (landing-bf.css hides the small eyebrow while the ad is shown; it
 * stays in the markup for screen readers and as a fallback). The ad's small
 * print is English; on the CZ page the Czech headline, lede, prices and
 * picker stay in HTML and the ad is the supporting visual (docs/black-friday-380.md).
 *
 * The two figures further down are real MOLOSOC photos already in the theme
 * (assets/images/landing-b/, the Landing B uploads, docs/landing-page-b-580.md).
 * Every photo is shown whole (css object-fit: contain on the hero).
 *
 * @return array key => directory under assets/images/, base file name, widths, intrinsic width/height of the largest file.
 */
function molosoc_bf_images() {
	return array(
		'hero'  => array( 'dir' => 'black-friday', 'base' => 'molosoc-black-friday-ad', 'widths' => array( 480, 800, 1200 ), 'w' => 1200, 'h' => 1200 ),
		'apply' => array( 'dir' => 'landing-b', 'base' => 'lpb-apply-cream', 'widths' => array( 480, 960 ), 'w' => 960, 'h' => 644 ),
		'story' => array( 'dir' => 'landing-b', 'base' => 'lpb-opening-package-mami', 'widths' => array( 400, 800 ), 'w' => 800, 'h' => 890 ),
	);
}

/** Alt text per photo and language. */
function molosoc_bf_image_alt( $key, $lang ) {
	$alts = array(
		'hero'  => array( 'cz' => 'Black Friday MOLOSOC: bílé nitrilové návleky na nohy před balením', 'en' => 'MOLOSOC Black Friday special offer: white nitrile foot covers in front of their pack' ),
		'apply' => array( 'cz' => 'Krém na chodidlo a návleky MOLOSOC', 'en' => 'Foot cream and MOLOSOC foot covers' ),
		'story' => array( 'cz' => 'Máma s dcerou otevírají balení MOLOSOC', 'en' => 'A mother and her daughter opening a MOLOSOC pack' ),
	);
	$lang = 'en' === $lang ? 'en' : 'cz';
	return isset( $alts[ $key ][ $lang ] ) ? $alts[ $key ][ $lang ] : '';
}

/**
 * `sizes` per slot. Hero: square, at most 264 px wide on a phone, 440 px
 * up to 900 px, 500 px in the desktop grid (landing-bf.css). Figures: the
 * section width, capped at 720 / 420 px by landing-bf.css.
 */
function molosoc_bf_image_sizes( $key ) {
	if ( 'hero' === $key ) {
		return '(max-width: 560px) 264px, (max-width: 900px) 440px, 500px';
	}
	return 'story' === $key ? '(max-width: 460px) calc(100vw - 40px), 420px' : '(max-width: 760px) calc(100vw - 40px), 720px';
}

/** src / srcset / sizes / width / height (+ og image) of a photo, or array() when a file is missing. */
function molosoc_bf_image_set( $key ) {
	$all = molosoc_bf_images();
	if ( ! isset( $all[ $key ] ) ) {
		return array();
	}
	$sub    = '/assets/images/' . $all[ $key ]['dir'] . '/';
	$dir    = get_stylesheet_directory() . $sub;
	$uri    = get_stylesheet_directory_uri() . $sub;
	$srcset = array();
	$last   = '';
	foreach ( $all[ $key ]['widths'] as $w ) {
		$file = $all[ $key ]['base'] . '-' . $w . '.webp';
		if ( ! file_exists( $dir . $file ) ) {
			return array();
		}
		$srcset[] = esc_url( $uri . $file ) . ' ' . (int) $w . 'w';
		$last     = $uri . $file;
	}
	return array(
		'src'    => esc_url( $last ),
		'srcset' => implode( ', ', $srcset ),
		'sizes'  => molosoc_bf_image_sizes( $key ),
		'width'  => (int) $all[ $key ]['w'],
		'height' => (int) $all[ $key ]['h'],
		'og'     => $last,
		'og_w'   => (int) $all[ $key ]['w'],
		'og_h'   => (int) $all[ $key ]['h'],
	);
}

/** <img> markup of a photo, or '' when a file is missing. */
function molosoc_bf_image( $key, $lang, $attrs = '' ) {
	$set = molosoc_bf_image_set( $key );
	if ( ! $set ) {
		return '';
	}
	return sprintf(
		'<img class="lpx-bf-img lpx-bf-img--%s" src="%s" srcset="%s" sizes="%s" alt="%s" width="%d" height="%d" decoding="async" %s>',
		esc_attr( $key ),
		$set['src'],
		esc_attr( $set['srcset'] ),
		esc_attr( $set['sizes'] ),
		esc_attr( molosoc_bf_image_alt( $key, $lang ) ),
		$set['width'],
		$set['height'],
		$attrs
	);
}

/** The template's three photos in order: eager high-priority hero, then two lazy figures. */
function molosoc_bf_page_images( $lang ) {
	return array(
		molosoc_bf_image( 'hero', $lang, 'fetchpriority="high" loading="eager"' ),
		molosoc_bf_image( 'apply', $lang, 'loading="lazy"' ),
		molosoc_bf_image( 'story', $lang, 'loading="lazy"' ),
	);
}

/* ---------- hero clip (Issue #388) ---------- */

/**
 * The ad's story in the hero: a 6.3 s silent excerpt of Žaneta's own public
 * video ("Šly jsme to prostě zkusit" / "We Just Went and Tried It") — cream,
 * then MOLOSOC pulled over the foot. It lies over the Black Friday ad image,
 * which stays the LCP element, the clip's poster and the fallback. The frame is
 * the square below the burned-in Czech captions, so one file serves CZ and EN.
 *
 * Nothing is requested before window load: the <video> sits in an inert
 * <template> (measured: a <video> in the initial HTML, even without src, made the
 * hero image finish ~350 ms later on a throttled phone). The script below inserts
 * it and sets src and poster, the poster being the ad file the browser already
 * chose for the <img>, so it is never fetched twice.
 * The clip is skipped for prefers-reduced-motion, data saver and 2G, and the
 * image simply stays if playback is refused. It ignores pointer events, so a tap
 * still follows the photo link to the picker. A pause button appears once it plays.
 *
 * @return string '' when the file is missing.
 */
function molosoc_bf_hero_clip( $t ) {
	$rel = '/assets/video/molosoc-we-tried-it-720.mp4';
	if ( ! file_exists( get_stylesheet_directory() . $rel ) ) {
		return '';
	}
	return sprintf(
		'<template data-bf-clip-tpl><video class="lpx-bf-clip" data-bf-clip data-src="%1$s" width="720" height="720" muted loop playsinline preload="none" disablepictureinpicture disableremoteplayback aria-hidden="true" tabindex="-1"></video></template>'
		. '<button type="button" class="lpx-bf-clip__btn" data-bf-clip-btn data-pause="%2$s" data-play="%3$s" aria-label="%2$s" hidden></button>',
		esc_url( get_stylesheet_directory_uri() . $rel ),
		esc_attr( $t['clip_pause'] ),
		esc_attr( $t['clip_play'] )
	);
}

/** Starts the clip after window load (see molosoc_bf_hero_clip()). Inline: no extra request. */
function molosoc_bf_hero_clip_script() {
	if ( ! molosoc_is_bf_landing() ) {
		return;
	}
	?>
<script>
(function () {
	var tpl = document.querySelector('[data-bf-clip-tpl]');
	if (!tpl || !tpl.content) { return; }
	var v, box = tpl.parentNode, btn = box.querySelector('[data-bf-clip-btn]'), img = box.querySelector('img');
	var c = navigator.connection, rm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
	if (rm || (c && (c.saveData || /2g/.test(c.effectiveType || '')))) { return; }
	var userPaused = false;
	function play() { var p = v.play(); if (p && p.catch) { p.catch(function () {}); } }
	function start() {
		v = tpl.content.firstElementChild.cloneNode(true);
		box.insertBefore(v, btn);
		v.muted = true;
		if (img) { v.poster = img.currentSrc || img.src; }
		v.src = v.getAttribute('data-src');
		v.addEventListener('playing', function () { box.classList.add('is-playing'); btn.hidden = false; }, { once: true });
		if ('IntersectionObserver' in window) {
			new IntersectionObserver(function (e) {
				if (!e[e.length - 1].isIntersecting) { v.pause(); } else if (!userPaused) { play(); }
			}).observe(box);
		} else { play(); }
	}
	btn.addEventListener('click', function () {
		userPaused = !v.paused;
		if (userPaused) { v.pause(); } else { play(); }
		btn.classList.toggle('is-paused', userPaused);
		btn.setAttribute('aria-label', btn.getAttribute(userPaused ? 'data-play' : 'data-pause'));
	});
	function ready() { if (window.requestIdleCallback) { requestIdleCallback(start, { timeout: 2000 }); } else { setTimeout(start, 500); } }
	if (document.readyState === 'complete') { ready(); } else { window.addEventListener('load', ready); }
})();
</script>
	<?php
}
add_action( 'wp_footer', 'molosoc_bf_hero_clip_script', 30 );

/**
 * Hero preload, wp_head priority 1 like molosoc_xmas_head() (which returns
 * early on these pages so the Christmas photo is never fetched here).
 */
function molosoc_bf_head() {
	if ( ! molosoc_is_bf_landing() ) {
		return;
	}
	$set = molosoc_bf_image_set( 'hero' );
	if ( ! $set ) {
		return;
	}
	printf(
		'<link rel="preload" as="image" fetchpriority="high" href="%s" imagesrcset="%s" imagesizes="%s">' . "\n",
		esc_url( $set['src'] ),
		esc_attr( $set['srcset'] ),
		esc_attr( $set['sizes'] )
	);
}
add_action( 'wp_head', 'molosoc_bf_head', 1 );

/* ---------- stylesheet ---------- */

/** The Black Friday colours on top of landing-b.css + landing-xmas.css (enqueued by functions.php for this family). */
function molosoc_bf_enqueue() {
	if ( ! molosoc_is_bf_landing() ) {
		return;
	}
	wp_enqueue_style( 'molosoc-landing-bf', get_stylesheet_directory_uri() . '/assets/css/landing-bf.css', array( 'molosoc-landing-xmas' ), wp_get_theme()->get( 'Version' ) );
}
add_action( 'wp_enqueue_scripts', 'molosoc_bf_enqueue', 20 );

/* ---------- sticky pill label (Issue #299 pattern) ---------- */

/**
 * molosoc_xmas_sticky_cta() (priority 10) already points the pill at the
 * in-page picker on this page family; only its label changes here.
 */
function molosoc_bf_sticky_cta( $data, $lang = '' ) {
	$page_lang = molosoc_bf_current_lang();
	if ( ! $page_lang ) {
		return $data;
	}
	return array(
		'url'   => '#lpx-bundle',
		'label' => molosoc_bf_copy( $page_lang )['pick'],
	);
}
add_filter( 'molosoc_sticky_cta_data', 'molosoc_bf_sticky_cta', 20, 2 );

/* ---------- stock refusal goes back to the page the visitor came from ---------- */

/**
 * The Black Friday picker's checkout URL carries molosoc_lp=bf (template part),
 * so a refused bundle (molosoc_xmas_add_to_cart(), not enough stock) returns
 * to the Black Friday page instead of the Christmas page. Whitelisted value
 * only; the final checkout redirect does not carry it.
 */
function molosoc_bf_return_page_url( $url, $lang ) {
	if ( isset( $_GET['molosoc_lp'] ) && 'bf' === sanitize_key( wp_unslash( $_GET['molosoc_lp'] ) ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		return molosoc_bf_page_url( $lang );
	}
	return $url;
}
add_filter( 'molosoc_xmas_return_page_url', 'molosoc_bf_return_page_url', 10, 2 );
