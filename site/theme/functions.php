<?php
/**
 * Molosoc standalone theme — setup, menu registration, and asset enqueue.
 *
 * Per project constraints this pass covers the homepage template and the
 * baseline a classic theme needs to not be broken elsewhere (index/header/
 * footer). Category/product/pillar/spoke templates, and a real footer
 * design, are a later, separate step — see the standing gap list in
 * docs/ (or the chat report that shipped alongside this build).
 */

defined( 'ABSPATH' ) || exit;

function molosoc_setup() {
	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'html5', array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script' ) );
	add_theme_support( 'automatic-feed-links' );

	// WooCommerce theme support — opts into WC's structured template wrappers
	// (gallery, product image zoom/lightbox/slider) instead of its shortcode
	// fallback wrapping. Shop/product/cart still render without this, but
	// less cleanly.
	add_theme_support( 'woocommerce' );
	add_theme_support( 'wc-product-gallery-zoom' );
	add_theme_support( 'wc-product-gallery-lightbox' );
	add_theme_support( 'wc-product-gallery-slider' );

	register_nav_menus( array(
		'primary' => __( 'Primary Menu', 'molosoc' ),
	) );
}
add_action( 'after_setup_theme', 'molosoc_setup' );

function molosoc_enqueue_assets() {
	$theme_uri     = get_stylesheet_directory_uri();
	$theme_version = wp_get_theme()->get( 'Version' );

	wp_enqueue_style( 'molosoc-style', get_stylesheet_uri(), array(), $theme_version );

	wp_enqueue_style(
		'molosoc-fonts',
		'https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Mulish:wght@400;600;700&family=Nunito:wght@400;600;700&display=swap',
		array(),
		null
	);

	wp_enqueue_style( 'molosoc-tokens', $theme_uri . '/assets/css/tokens.css', array(), $theme_version );
	wp_enqueue_style( 'molosoc-base', $theme_uri . '/assets/css/base.css', array( 'molosoc-tokens' ), $theme_version );
	wp_enqueue_style( 'molosoc-components', $theme_uri . '/assets/css/components.css', array( 'molosoc-base' ), $theme_version );

	if ( is_front_page() ) {
		wp_enqueue_style( 'molosoc-homepage', $theme_uri . '/assets/css/homepage.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_script( 'molosoc-motion', $theme_uri . '/assets/js/motion.js', array(), $theme_version, true );

		// GSAP + ScrollTrigger are being re-enabled one effect at a time (see
		// git history: "Revert homepage to last confirmed-stable static state
		// (pre-animation-port)" — the full stack caused a regression once
		// before). Merge transition and topics-portal (five-card reveal) are
		// confirmed working; proof-scale stays off until it's confirmed the
		// same way.
		wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
		wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
		wp_enqueue_script( 'molosoc-merge-transition', $theme_uri . '/assets/js/merge-transition.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-topics-portal', $theme_uri . '/assets/js/topics-portal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );

		// Real file content, not wp_add_inline_script — see scroll-refresh.js
		// for why (WPO Minify silently drops inline scripts on a bundled
		// handle). Keeps every ScrollTrigger pin above matched to the real,
		// settled DOM regardless of lazy-loaded images changing page height.
		wp_enqueue_script( 'molosoc-scroll-refresh', $theme_uri . '/assets/js/scroll-refresh.js', array( 'gsap-scrolltrigger', 'molosoc-merge-transition', 'molosoc-topics-portal' ), $theme_version, true );

		// Still disabled — CSS default state (--proof-scale:1) renders this
		// correctly at rest with no JS, so leaving it off doesn't change how
		// it looks:
		// wp_enqueue_script( 'molosoc-proof-scale', $theme_uri . '/assets/js/proof-scale.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
	} elseif ( is_page( 'foot-covers' ) ) {
		wp_enqueue_style( 'molosoc-category', $theme_uri . '/assets/css/category.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_script( 'molosoc-motion', $theme_uri . '/assets/js/motion.js', array(), $theme_version, true );

		// Three independent pinned sequences on this page (two
		// sequential-text-reveal sections + the "who this is for" editorial
		// feature reveal) — same GSAP/ScrollTrigger stack as the homepage,
		// same reasoning for real-file scroll-refresh.js over inline script
		// (see the homepage branch above).
		wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
		wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
		wp_enqueue_script( 'molosoc-sequential-text-reveal', $theme_uri . '/assets/js/sequential-text-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-who-reveal', $theme_uri . '/assets/js/who-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-scroll-refresh', $theme_uri . '/assets/js/scroll-refresh.js', array( 'gsap-scrolltrigger', 'molosoc-sequential-text-reveal', 'molosoc-who-reveal' ), $theme_version, true );
	}
}
add_action( 'wp_enqueue_scripts', 'molosoc_enqueue_assets' );

/**
 * Category page ("Reusable Foot Covers") schema markup.
 * A normal template (unlike front-page.php) doesn't build its own <head> —
 * get_header() already calls wp_head(), so this hooks into that instead of
 * being printed directly in the template file.
 * Source: content/molosoc-site/02-category/category-schema.html.
 */
function molosoc_category_schema() {
	if ( ! is_page( 'foot-covers' ) ) {
		return;
	}
	?>
	<meta name="description" content="Skip the single-use sock mask. Molosoc's reusable, moisture-lock foot cover works with any cream you own — less mess, no salon trip, same soft results.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "CollectionPage",
	      "@id": "https://molosoc.com/foot-covers/#webpage",
	      "url": "https://molosoc.com/foot-covers/",
	      "name": "Reusable Foot Covers | Moisture-Lock Foot Cover — Molosoc",
	      "description": "Skip the single-use sock mask. Molosoc's reusable, moisture-lock foot cover works with any cream you own — less mess, no salon trip, same soft results.",
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "about": { "@id": "https://molosoc.com/#organization" },
	      "breadcrumb": { "@id": "https://molosoc.com/foot-covers/#breadcrumb" },
	      "mainEntity": { "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#product" },
	      "inLanguage": "en"
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/foot-covers/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Foot Covers", "item": "https://molosoc.com/foot-covers/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_category_schema' );

/**
 * Homepage schema markup — Organization/WebSite/WebPage, ported from
 * homepage-preview.html's own <head> block. front-page.php builds its own
 * <head> and calls wp_head() directly (see that file's header comment for
 * why it skips get_header()), so this hooks in the same way the category
 * page's schema does rather than being printed inline in the template.
 * Defines the #organization and #website @ids the category (and product)
 * page schema already reference — those were dangling on the live site
 * until this existed.
 * Source: content/molosoc-site/01-homepage/homepage-schema.html.
 */
function molosoc_homepage_schema() {
	if ( ! is_front_page() ) {
		return;
	}
	?>
	<meta name="description" content="Molosoc helps you finish the foot care routine you already started — reusable, cream-agnostic, and built for real bathroom drawers, not perfect ones.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Organization",
	      "@id": "https://molosoc.com/#organization",
	      "name": "Molosoc",
	      "url": "https://molosoc.com/",
	      "description": "Molosoc helps you finish the foot care routine you already started — reusable, cream-agnostic, and built for real bathroom drawers, not perfect ones.",
	      "logo": {
	        "@type": "ImageObject",
	        "url": "https://molosoc.com/wp-content/uploads/2026/06/MOLOSOC-Logo-TM.png"
	      },
	      "sameAs": [
	        "https://www.facebook.com/molosoc",
	        "https://www.instagram.com/molosoc_/",
	        "https://www.tiktok.com/@molosoc",
	        "https://www.youtube.com/@Molosoc",
	        "https://www.linkedin.com/in/molosoc/",
	        "https://x.com/Molosoc_"
	      ]
	    },
	    {
	      "@type": "WebSite",
	      "@id": "https://molosoc.com/#website",
	      "url": "https://molosoc.com/",
	      "name": "Molosoc",
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "inLanguage": "en"
	    },
	    {
	      "@type": "WebPage",
	      "@id": "https://molosoc.com/#webpage",
	      "url": "https://molosoc.com/",
	      "name": "Molosoc® | Foot Care That Actually Sticks",
	      "description": "Molosoc helps you finish the foot care routine you already started — reusable, cream-agnostic, and built for real bathroom drawers, not perfect ones.",
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "about": { "@id": "https://molosoc.com/#organization" },
	      "inLanguage": "en"
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_homepage_schema' );

/**
 * Product page schema markup, ported from product-preview.html's own
 * <head> block. Gated on is_singular('product') (core WP conditional,
 * works whether or not WooCommerce's own is_product() is available) since
 * the live product page at /foot-covers/moisture-lock-foot-cover/ is a
 * WooCommerce single-product template, not yet product.php in this theme.
 * Two deltas from the preview's source block, both stale content bugs, not
 * design choices: "sku" dropped (was a literal "[INSERT: SKU — not yet
 * assigned]" placeholder — schema.org doesn't require it, and shipping the
 * placeholder text as the real value is worse than omitting the field),
 * and "image" swapped from hero_pair_bedroom.jpg (that file's own comment
 * says it's no longer used on this page, replaced by the molosoc-3d.glb
 * hero) to 3d_render_01_front_nobg.png, the product render actually in use
 * elsewhere on the live site today.
 * Source: content/molosoc-site/03-product/product-schema.html.
 */
function molosoc_product_schema() {
	if ( ! is_singular( 'product' ) ) {
		return;
	}
	?>
	<meta name="description" content="Real before/after results, not filters. The reusable foot cover that locks in your favorite cream, cuts the mess, and makes your routine actually stick.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Product",
	      "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#product",
	      "name": "Molosoc Foot Cover",
	      "description": "A reusable, moisture-lock foot cover that seals your favorite cream against the skin — cutting the mess and making your foot care routine actually stick. Works with any cream you already own.",
	      "brand": { "@id": "https://molosoc.com/#organization" },
	      "image": "https://staging.molosoc.com/wp-content/uploads/2026/07/3d_render_01_front_nobg.png",
	      "url": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/",
	      "category": "Foot Care",
	      "offers": {
	        "@type": "Offer",
	        "url": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/",
	        "priceCurrency": "USD",
	        "price": "13.00",
	        "availability": "https://schema.org/InStock",
	        "itemCondition": "https://schema.org/NewCondition"
	      }
	    },
	    {
	      "@type": "WebPage",
	      "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#webpage",
	      "url": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/",
	      "name": "Molosoc Foot Cover — The Cream You Already Own, Finally Working",
	      "description": "Real before/after results, not filters. The reusable foot cover that locks in your favorite cream, cuts the mess, and makes your routine actually stick.",
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "about": { "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#product" },
	      "breadcrumb": { "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#breadcrumb" },
	      "inLanguage": "en"
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Foot Covers", "item": "https://molosoc.com/foot-covers/" },
	        { "@type": "ListItem", "position": 3, "name": "Molosoc Foot Cover", "item": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_product_schema' );

/**
 * WordPress doesn't allow .glb uploads by default (not in its core mime
 * whitelist) — needed for the 3D product model in the media library.
 */
function molosoc_allow_glb_uploads( $mimes ) {
	$mimes['glb'] = 'model/gltf-binary';
	return $mimes;
}
add_filter( 'upload_mimes', 'molosoc_allow_glb_uploads' );
