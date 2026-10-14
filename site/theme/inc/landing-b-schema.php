<?php
/**
 * JSON-LD for the CZ landing page /cz/hydratacni-navleky-molosoc/ (Issue #155).
 *
 * AUDIT (repo, 2026-10-14): the page (template page-hydratacni-navleky-molosoc.php,
 * WP page 1037) printed NO JSON-LD. The site has no SEO plugin; every other
 * schema block is a hand-written wp_head function gated on its own slug, so
 * none of them can match this page. WooCommerce prints its own Product graph
 * only on the product page (/cz/produkt/hydratacni-navlek-na-nohy/), so this
 * page must NOT declare a second Product/Offer: it links to the canonical
 * product page instead and leaves price/stock/seller to WooCommerce there.
 *
 * Emitted (one @graph):
 *   - WebPage  @id <canonical>#webpage, inLanguage cs, name = the page's
 *              own <title> (post-"(varianta, koncept)" strip), description
 *              = a constant built only from the visible copy.
 *              isPartOf/about/publisher reuse the site-wide
 *              https://molosoc.com/#website and #organization @ids that the
 *              homepage graph defines (no Organization is redefined here, so
 *              no logo / sameAs / identifiers are invented).
 *              significantLink = the canonical CZ product URL.
 *   - FAQPage  @id <canonical>#faq — the six visible <details> Q&As, text
 *              identical to the template (tests/test_landing_b_schema.py
 *              compares them).
 * Deliberately NOT emitted: Product/Offer (WooCommerce owns it), BreadcrumbList
 * (the page shows no breadcrumb), ratings/reviews, GTIN, logo, social URLs,
 * images, shipping/returns, dates, medical claims.
 *
 * Gated on the slug AND, when Polylang is active, the Czech language, so an
 * EN page that happens to reuse the slug never gets cs-language markup.
 */

defined( 'ABSPATH' ) || exit;

/** Meta-style summary of the page, using only wording that is visible on it. */
function molosoc_landing_b_schema_description() {
	return 'Hydratační návleky na nohy MOLOSOC: bez klouzání, bez čekání, bez mastných stop. 100% nitril, bez latexu, na opakované použití a s jakýmkoliv krémem, který už máte doma.';
}

/**
 * The visible FAQ as [question, answer] pairs — must stay identical to the
 * <details> blocks in page-hydratacni-navleky-molosoc.php.
 *
 * @param string $price    Visible price string, e.g. '229 Kč'.
 * @param string $shipping Visible shipping note, e.g. 'Doprava od 79 Kč'.
 */
function molosoc_landing_b_schema_faq( $price, $shipping ) {
	return array(
		array( 'Z čeho je MOLOSOC vyrobený?', 'MOLOSOC je vyrobený ze 100% nitrilu – bez latexu, bez pudru. Je hypoalergenní a vhodný i pro citlivou pokožku. Představte si to jako rukavice, ale na nohy.' ),
		array( 'Jak se MOLOSOC používá?', 'Jednoduše: 1) Umyjte a osušte nohy. 2) Naneste svůj oblíbený krém, balzám nebo olej. 3) Nasaďte MOLOSOC na každou nohu. 4) Noste 20–30 minut. 5) Sundejte a užijte si jemnější chodidla.' ),
		array( 'Můžu v nich chodit?', 'Ano! MOLOSOC neklouže a umožňuje normální pohyb po bytě. Nemusíte sedět a čekat.' ),
		array( 'Funguje to s jakýmkoliv krémem?', 'Ano. MOLOSOC funguje s jakýmkoliv krémem, balzámem nebo olejem na nohy, který už máte doma. Není potřeba kupovat nic speciálního.' ),
		array( 'Je to jednorázové?', 'Nejsou jednorázové – při domácím použití vydrží opakovaně díky kvalitnímu materiálu. Stačí je po použití umýt mýdlem a vodou, nechat uschnout a použít znovu. (Jednorázové by byly pouze v hygienickém/profesionálním prostředí.)' ),
		array( 'Kolik stojí jedno balení?', 'Jedno balení MOLOSOC (1 pár) stojí ' . $price . '. ' . $shipping . '. Odesíláme do 24 hodin od objednání.' ),
	);
}

/**
 * Pure graph builder (no WordPress calls) so it can be unit-tested with php-cli.
 *
 * @param string $canonical Canonical page URL (get_permalink()).
 * @param string $name      Page title.
 * @param string $product   Canonical CZ product URL.
 * @param array  $faq       [question, answer] pairs.
 * @return array JSON-LD document.
 */
function molosoc_landing_b_schema_graph( $canonical, $name, $product, array $faq ) {
	$questions = array();
	foreach ( $faq as $qa ) {
		$questions[] = array(
			'@type'          => 'Question',
			'name'           => $qa[0],
			'acceptedAnswer' => array(
				'@type' => 'Answer',
				'text'  => $qa[1],
			),
		);
	}
	return array(
		'@context' => 'https://schema.org',
		'@graph'   => array(
			array(
				'@type'           => 'WebPage',
				'@id'             => $canonical . '#webpage',
				'url'             => $canonical,
				'name'            => $name,
				'description'     => molosoc_landing_b_schema_description(),
				'inLanguage'      => 'cs',
				'isPartOf'        => array( '@id' => 'https://molosoc.com/#website' ),
				'about'           => array( '@id' => 'https://molosoc.com/#organization' ),
				'publisher'       => array( '@id' => 'https://molosoc.com/#organization' ),
				'significantLink' => $product,
			),
			array(
				'@type'      => 'FAQPage',
				'@id'        => $canonical . '#faq',
				'url'        => $canonical,
				'inLanguage' => 'cs',
				'isPartOf'   => array( '@id' => $canonical . '#webpage' ),
				'mainEntity' => $questions,
			),
		),
	);
}

function molosoc_landing_b_schema() {
	if ( ! is_page( 'hydratacni-navleky-molosoc' ) ) {
		return;
	}
	if ( function_exists( 'pll_current_language' ) && 'cz' !== pll_current_language() ) {
		return;
	}
	$canonical = get_permalink();
	if ( ! $canonical ) {
		return;
	}
	// Same constants the template renders (page-hydratacni-navleky-molosoc.php).
	$graph = molosoc_landing_b_schema_graph(
		$canonical,
		wp_get_document_title(),
		molosoc_product_url( 'cz' ),
		molosoc_landing_b_schema_faq( '229 Kč', 'Doprava od 79 Kč' )
	);
	echo '<script type="application/ld+json">' . wp_json_encode( $graph, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP ) . "</script>\n"; // phpcs:ignore WordPress.Security.EscapeOutput -- JSON with HEX_TAG/AMP.
}
add_action( 'wp_head', 'molosoc_landing_b_schema' );
