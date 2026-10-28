<?php
/**
 * English Landing Page B (Issue #288) — the EN counterpart of the CZ Landing B
 * (/cz/hydratacni-navleky-molosoc/, WP page 1037).
 *
 * PROPOSED slug: hydrating-foot-covers-molosoc  ->  https://molosoc.com/hydrating-foot-covers-molosoc/
 * (NOT live until the page is provisioned — see docs/landing-page-b-en-288.md).
 * Derived from the existing URL architecture: English pages sit at the site
 * root, Czech ones under /cz/ (e.g. /foot-covers/, /cracked-heels/,
 * /christmas-gift-molosoc/ vs /cz/...); the CZ slug is hydratacni-navleky-
 * molosoc ("hydrating foot covers" + brand), and the Christmas pair
 * (vanocni-darek-molosoc <-> christmas-gift-molosoc) already uses the same
 * "literal translation of the CZ slug" convention. The template is
 * page-hydrating-foot-covers-molosoc.php (page-{slug}.php convention).
 *
 * This file only holds what is specific to the EN page. It is purely additive:
 * the CZ Landing B gates in functions.php are slug-gated to the CZ page and are
 * not edited, so the EN page gets its own small hooks here instead:
 *   - the slug / "is this the EN Landing B request" helper;
 *   - the stylesheet + script enqueue and the head output (hero image and
 *     background preloads, non-blocking fonts) — the same helpers and the same
 *     treatment as the CZ page (molosoc_landing_b_head() / the Landing B branch of
 *     molosoc_enqueue_assets()). Not replicated: the CZ-only "unused plugin
 *     CSS/JS" dequeue pass (molosoc_page_without_plugin_markup()); the EN page
 *     simply keeps WooCommerce's default assets, which is harmless and can be
 *     added later by extending that one gate;
 *   - document title, <meta name="description"> and JSON-LD (WebPage + FAQPage,
 *     inLanguage en) — the CZ equivalents in inc/landing-b-schema.php are
 *     slug-gated to the CZ page and are not changed;
 *   - the visible FAQ, single source for the template and the JSON-LD.
 *
 * It changes nothing for the CZ page, adds no redirect, no canonical or
 * robots change (the page is a normal indexable page, like CZ B), and no
 * Product/Offer markup (WooCommerce owns it on the product page).
 */

defined( 'ABSPATH' ) || exit;

/** Proposed EN slug (page-{slug}.php convention). */
function molosoc_landing_b_en_slug() {
	return 'hydrating-foot-covers-molosoc';
}

/** True on the EN Landing B request. */
function molosoc_landing_b_en_active() {
	return is_page( molosoc_landing_b_en_slug() );
}

/**
 * Assets: landing-b.css / landing-b.js, exactly as the CZ Landing B branch of
 * molosoc_enqueue_assets() (priority 10) registers them; runs after it so the
 * blocking Google Fonts handle can be dequeued again (fonts are printed
 * non-blocking by molosoc_landing_b_en_head() below).
 */
add_action( 'wp_enqueue_scripts', function () {
	if ( ! molosoc_landing_b_en_active() ) {
		return;
	}
	$theme_uri     = get_stylesheet_directory_uri();
	$theme_version = wp_get_theme()->get( 'Version' );
	wp_dequeue_style( 'molosoc-fonts' );
	wp_enqueue_style( 'molosoc-landing-b', $theme_uri . '/assets/css/landing-b.css', array( 'molosoc-components' ), $theme_version );
	wp_enqueue_script( 'molosoc-landing-b', $theme_uri . '/assets/js/landing-b.js', array(), $theme_version, true );
	wp_script_add_data( 'molosoc-landing-b', 'strategy', 'defer' );
}, 11 );

/**
 * wp_head: the same preloads and non-blocking fonts molosoc_landing_b_head()
 * prints for the CZ page (hero <img> preload, the two hero background
 * breakpoints, both Google Fonts stylesheets as media="print" + onload swap).
 */
function molosoc_landing_b_en_head() {
	if ( ! molosoc_landing_b_en_active() ) {
		return;
	}
	echo '<link rel="preconnect" href="https://fonts.googleapis.com">' . "\n";
	echo '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n";

	$hero  = molosoc_landing_b_hero_image();
	$attrs = molosoc_landing_b_img_attrs( $hero['base'], $hero['widths'], $hero['sizes'] );
	$attrs = str_replace( array( 'src="', 'srcset="', 'sizes="' ), array( 'href="', 'imagesrcset="', 'imagesizes="' ), $attrs );
	echo '<link rel="preload" as="image" fetchpriority="high" ' . $attrs . '>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput -- every value is esc_url()/esc_attr()ed in molosoc_landing_b_img_attrs().

	foreach ( molosoc_landing_b_hero_background() as $bg ) {
		printf(
			'<link rel="preload" as="image" fetchpriority="high" href="%s" media="%s">' . "\n",
			esc_url( $bg['url'] ),
			esc_attr( $bg['media'] )
		);
	}

	foreach ( array( molosoc_fonts_url(), molosoc_landing_b_fonts_url() ) as $url ) {
		printf(
			'<link rel="stylesheet" href="%1$s" media="print" onload="this.media=\'all\'">' . "\n" .
			'<noscript><link rel="stylesheet" href="%1$s"></noscript>' . "\n",
			esc_url( $url )
		);
	}
}
add_action( 'wp_head', 'molosoc_landing_b_en_head', 1 );

/** Document title (also the JSON-LD WebPage name). */
function molosoc_landing_b_en_document_title() {
	return 'Reusable Hydrating Foot Mask | Molosoc';
}

add_filter( 'pre_get_document_title', function ( $title ) {
	return molosoc_landing_b_en_active() ? molosoc_landing_b_en_document_title() : $title;
} );

/** Meta description / WebPage description — built only from wording visible on the page. */
function molosoc_landing_b_en_schema_description() {
	return 'Reusable hydrating foot mask from MOLOSOC. Works with the cream you already have — no mess, no slipping. €10, charged as 229 CZK.';
}

/**
 * The visible FAQ as [question, answer] pairs; the template prints exactly these.
 *
 * @param string $price    Visible price, e.g. '€10'.
 * @param string $shipping Visible shipping note, e.g. 'Shipping from 69 CZK'.
 */
function molosoc_landing_b_en_faq( $price, $shipping ) {
	return array(
		array( 'What is MOLOSOC made of?', 'MOLOSOC is made of 100% nitrile — latex-free and powder-free. It is hypoallergenic and suitable for sensitive skin too. Think of it as gloves, but for your feet.' ),
		array( 'How do I use MOLOSOC?', 'Simple: 1) Wash and dry your feet. 2) Apply your favourite cream, balm or oil. 3) Put MOLOSOC on each foot. 4) Wear for 20–30 minutes. 5) Take them off and enjoy softer feet.' ),
		array( 'Can I walk in them?', 'Yes! MOLOSOC does not slip and lets you move normally around your home. No need to sit still and wait.' ),
		array( 'Does it work with any cream?', 'Yes. MOLOSOC works with any foot cream, balm or oil you already have at home. There is nothing special to buy.' ),
		array( 'Is it disposable?', 'No — for home use it lasts through repeated uses thanks to the quality material. Simply wash it with soap and water after use, let it dry and use it again. (Only in a hygiene or professional setting would it be single-use.)' ),
		array( 'How much does one pack cost?', 'One MOLOSOC pack (1 pair) costs ' . $price . ' (charged as 229 CZK). ' . $shipping . '. We ship within 24 hours of your order.' ),
	);
}

/**
 * Pure graph builder (no WordPress calls), mirrors molosoc_landing_b_schema_graph().
 *
 * @param string $canonical Canonical page URL (get_permalink()).
 * @param string $name      Page title.
 * @param string $product   Canonical EN product URL.
 * @param array  $faq       [question, answer] pairs.
 * @return array JSON-LD document.
 */
function molosoc_landing_b_en_schema_graph( $canonical, $name, $product, array $faq ) {
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
	// Same Organization + WebSite nodes (and @ids) as the homepage and CZ B.
	$graph   = molosoc_landing_b_schema_site_nodes();
	$graph[] = array(
		'@type'           => 'WebPage',
		'@id'             => $canonical . '#webpage',
		'url'             => $canonical,
		'name'            => $name,
		'description'     => molosoc_landing_b_en_schema_description(),
		'inLanguage'      => 'en',
		'isPartOf'        => array( '@id' => 'https://molosoc.com/#website' ),
		'about'           => array( '@id' => 'https://molosoc.com/#organization' ),
		'publisher'       => array( '@id' => 'https://molosoc.com/#organization' ),
		'significantLink' => $product,
	);
	$graph[] = array(
		'@type'      => 'FAQPage',
		'@id'        => $canonical . '#faq',
		'url'        => $canonical,
		'inLanguage' => 'en',
		'isPartOf'   => array( '@id' => $canonical . '#webpage' ),
		'mainEntity' => $questions,
	);
	return array(
		'@context' => 'https://schema.org',
		'@graph'   => $graph,
	);
}

function molosoc_landing_b_en_schema() {
	if ( ! molosoc_landing_b_en_active() ) {
		return;
	}
	if ( function_exists( 'pll_current_language' ) && 'cz' === pll_current_language() ) {
		return;
	}
	$canonical = get_permalink();
	if ( ! $canonical ) {
		return;
	}
	echo '<meta name="description" content="' . esc_attr( molosoc_landing_b_en_schema_description() ) . '">' . "\n";
	$graph = molosoc_landing_b_en_schema_graph(
		$canonical,
		html_entity_decode( wp_get_document_title(), ENT_QUOTES, 'UTF-8' ),
		molosoc_product_url( 'en' ),
		molosoc_landing_b_en_faq( '€10', 'Shipping from 69 CZK' )
	);
	echo '<script type="application/ld+json">' . wp_json_encode( $graph, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP ) . "</script>\n"; // phpcs:ignore WordPress.Security.EscapeOutput -- JSON with HEX_TAG/AMP.
}
add_action( 'wp_head', 'molosoc_landing_b_en_schema' );
