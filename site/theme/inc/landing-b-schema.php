<?php
/**
 * <meta name="description"> + JSON-LD for the CZ landing page
 * /cz/hydratacni-navleky-molosoc/ (Issue #155, fixed/extended in Issue #159).
 *
 * AUDIT (repo, 2026-10-14): the page (template page-hydratacni-navleky-molosoc.php,
 * WP page 1037) printed NO JSON-LD and no meta description. The site has no
 * SEO plugin; every other schema block is a hand-written wp_head function
 * gated on its own slug, so none of them can match this page — including
 * molosoc_homepage_schema(), the only place that defines the site-wide
 * https://molosoc.com/#organization and #website nodes (is_front_page()
 * only). WooCommerce prints its own Product graph only on the product page
 * (/cz/produkt/hydratacni-navlek-na-nohy/), so this page must NOT declare a
 * second Product/Offer: it links to the canonical product page instead and
 * leaves price/stock/seller to WooCommerce there.
 *
 * Emitted on this page only:
 *   - <meta name="description">: molosoc_landing_b_schema_description(), a
 *     constant built only from the visible hero / strip / FAQ copy (the page
 *     had none — Issue #159). The same string is the WebPage description.
 *   - one @graph:
 *     - Organization @id https://molosoc.com/#organization and
 *       WebSite @id https://molosoc.com/#website — the same @ids, name, url,
 *       logo and sameAs that molosoc_homepage_schema() prints on the homepage
 *       (functions.php), repeated here because a graph that only references
 *       them left both dangling on this page (PR #156 finding). Nothing is
 *       invented: tests/test_landing_b_schema.py compares the values against
 *       the homepage block. The homepage's EN Organization description and
 *       the WebSite inLanguage "en" are deliberately not repeated on this
 *       Czech page.
 *     - WebPage @id <canonical>#webpage, inLanguage cs, name = the page's
 *       own <title> (molosoc_landing_b_document_title() in functions.php
 *       since Issue #161), entity-decoded — a WordPress-built title is
 *       HTML-escaped, and before the decode the en dash became the literal
 *       "&#8211;" inside the JSON (Issue #159).
 *       significantLink = the canonical CZ product URL.
 *     - FAQPage @id <canonical>#faq — the six visible <details> Q&As, text
 *       identical to the template (tests compare them).
 * Deliberately NOT emitted: Product/Offer (WooCommerce owns it), BreadcrumbList
 * (the page shows no breadcrumb), ratings/reviews, GTIN, images, shipping /
 * returns, dates, medical claims.
 *
 * Gated on the slug AND, when Polylang is active, the Czech language, so an
 * EN page that happens to reuse the slug never gets cs-language markup.
 */

defined( 'ABSPATH' ) || exit;

/**
 * Meta description / WebPage description of the page (~140 chars), using only
 * wording that is visible on it: eyebrow + H1 ("maska na nohy", "na opakované
 * použití", "s krémem, který už máte"), the page-580 H1 ("bez nepořádku"),
 * the hero subline ("bez klouzání") and the visible price. Issue #161
 * (keyword retarget to "maska na nohy") replaced the Issue #159 text.
 */
function molosoc_landing_b_schema_description() {
	return 'Hydratační maska na nohy MOLOSOC na opakované použití. Funguje s krémem, který už máte — bez nepořádku a bez klouzání. 229 Kč.';
}

/**
 * The site-wide Organization + WebSite nodes, mirroring the values printed
 * by molosoc_homepage_schema() in functions.php (same @ids so the two graphs
 * describe one entity). Keep the two in sync — the test compares them.
 */
function molosoc_landing_b_schema_site_nodes() {
	return array(
		array(
			'@type'  => 'Organization',
			'@id'    => 'https://molosoc.com/#organization',
			'name'   => 'Molosoc',
			'url'    => 'https://molosoc.com/',
			'logo'   => array(
				'@type' => 'ImageObject',
				'url'   => 'https://molosoc.com/wp-content/uploads/2026/06/MOLOSOC-Logo-TM.png',
			),
			'sameAs' => array(
				'https://www.facebook.com/molosoc',
				'https://www.instagram.com/molosoc_/',
				'https://www.tiktok.com/@molosoc',
				'https://www.youtube.com/@Molosoc',
				'https://www.linkedin.com/in/molosoc/',
				'https://x.com/Molosoc_',
			),
		),
		array(
			'@type'     => 'WebSite',
			'@id'       => 'https://molosoc.com/#website',
			'url'       => 'https://molosoc.com/',
			'name'      => 'Molosoc',
			'publisher' => array( '@id' => 'https://molosoc.com/#organization' ),
		),
	);
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
 * @param string $name      Page title (already entity-decoded).
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
	$graph   = molosoc_landing_b_schema_site_nodes();
	$graph[] = array(
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
	);
	$graph[] = array(
		'@type'      => 'FAQPage',
		'@id'        => $canonical . '#faq',
		'url'        => $canonical,
		'inLanguage' => 'cs',
		'isPartOf'   => array( '@id' => $canonical . '#webpage' ),
		'mainEntity' => $questions,
	);
	return array(
		'@context' => 'https://schema.org',
		'@graph'   => $graph,
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
	echo '<meta name="description" content="' . esc_attr( molosoc_landing_b_schema_description() ) . '">' . "\n";
	// Same constants the template renders (page-hydratacni-navleky-molosoc.php).
	// The title is the pre_get_document_title constant from functions.php
	// (Issue #161); the decode stays so a WordPress-built (escaped) title can
	// never put a literal "&#8211;" into the JSON again (Issue #159).
	$graph = molosoc_landing_b_schema_graph(
		$canonical,
		html_entity_decode( wp_get_document_title(), ENT_QUOTES, 'UTF-8' ),
		molosoc_product_url( 'cz' ),
		molosoc_landing_b_schema_faq( '229 Kč', 'Doprava od 69 Kč' )
	);
	echo '<script type="application/ld+json">' . wp_json_encode( $graph, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP ) . "</script>\n"; // phpcs:ignore WordPress.Security.EscapeOutput -- JSON with HEX_TAG/AMP.
}
add_action( 'wp_head', 'molosoc_landing_b_schema' );
