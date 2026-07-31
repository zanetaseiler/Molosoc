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
	} elseif ( is_page( 'cracked-heels' ) ) {
		wp_enqueue_style( 'molosoc-pillar1', $theme_uri . '/assets/css/pillar1.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_script( 'molosoc-motion', $theme_uri . '/assets/js/motion.js', array(), $theme_version, true );

		// model-viewer renders the always-rotating molosoc-3d.glb model in
		// the "why moisturizer alone doesn't fix it" section — same web
		// component the Product page's own hero uses (see
		// molosoc_product_schema()'s comment for that page's use of the
		// same model). Needs type="module" (see the script_loader_tag
		// filter below), not a plain classic script.
		wp_enqueue_script( 'molosoc-model-viewer', 'https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js', array(), '3.5.0', true );

		// Two independent GSAP/ScrollTrigger sequences on this page
		// (fixed-image-text-reveal for "what causes it", editorial-
		// feature-reveal for "when it gets serious") plus one plain-
		// scroll-listener sequence with no GSAP dependency (orbit-scroll-
		// drawer for "why moisturizer alone doesn't fix it" — see that
		// file's own header comment for why it skips GSAP). Same real-file
		// scroll-refresh.js convention as the homepage/category branches
		// above (WPO Minify silently drops inline scripts on a bundled
		// handle).
		wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
		wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
		wp_enqueue_script( 'molosoc-sequential-text-reveal', $theme_uri . '/assets/js/sequential-text-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-severity-reveal', $theme_uri . '/assets/js/severity-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-mechanism-drawer', $theme_uri . '/assets/js/mechanism-drawer.js', array(), $theme_version, true );
		wp_enqueue_script( 'molosoc-scroll-refresh', $theme_uri . '/assets/js/scroll-refresh.js', array( 'gsap-scrolltrigger', 'molosoc-sequential-text-reveal', 'molosoc-severity-reveal' ), $theme_version, true );
	} elseif ( is_page( 'ingrown-toenails' ) ) {
		// Identical asset stack to the cracked-heels branch above —
		// page-ingrown-toenails.php reuses pillar1.css and its JS as-is
		// (every class/selector in that file is generic, nothing
		// cracked-heels-specific to duplicate). See that branch's own
		// comments for why each handle is here.
		wp_enqueue_style( 'molosoc-pillar1', $theme_uri . '/assets/css/pillar1.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_script( 'molosoc-motion', $theme_uri . '/assets/js/motion.js', array(), $theme_version, true );
		wp_enqueue_script( 'molosoc-model-viewer', 'https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js', array(), '3.5.0', true );
		wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
		wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
		wp_enqueue_script( 'molosoc-sequential-text-reveal', $theme_uri . '/assets/js/sequential-text-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-severity-reveal', $theme_uri . '/assets/js/severity-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-mechanism-drawer', $theme_uri . '/assets/js/mechanism-drawer.js', array(), $theme_version, true );
		wp_enqueue_script( 'molosoc-scroll-refresh', $theme_uri . '/assets/js/scroll-refresh.js', array( 'gsap-scrolltrigger', 'molosoc-sequential-text-reveal', 'molosoc-severity-reveal' ), $theme_version, true );
	} elseif ( is_page( 'dry-skin-feet' ) ) {
		// Identical asset stack to the cracked-heels/ingrown-toenails
		// branches above — page-dry-skin-feet.php reuses pillar1.css and
		// its JS as-is (every class/selector in that file is generic,
		// nothing cracked-heels-specific to duplicate). See the
		// cracked-heels branch's own comments for why each handle is here.
		wp_enqueue_style( 'molosoc-pillar1', $theme_uri . '/assets/css/pillar1.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_script( 'molosoc-motion', $theme_uri . '/assets/js/motion.js', array(), $theme_version, true );
		wp_enqueue_script( 'molosoc-model-viewer', 'https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js', array(), '3.5.0', true );
		wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
		wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
		wp_enqueue_script( 'molosoc-sequential-text-reveal', $theme_uri . '/assets/js/sequential-text-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-severity-reveal', $theme_uri . '/assets/js/severity-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-mechanism-drawer', $theme_uri . '/assets/js/mechanism-drawer.js', array(), $theme_version, true );
		wp_enqueue_script( 'molosoc-scroll-refresh', $theme_uri . '/assets/js/scroll-refresh.js', array( 'gsap-scrolltrigger', 'molosoc-sequential-text-reveal', 'molosoc-severity-reveal' ), $theme_version, true );
	} elseif ( is_page( 'foot-cream-that-works' ) ) {
		// Identical asset stack to the cracked-heels/ingrown-toenails
		// branches above — page-foot-cream-that-works.php reuses
		// pillar1.css and its JS as-is (every class/selector in that file
		// is generic, nothing cracked-heels-specific to duplicate). See
		// the cracked-heels branch's own comments for why each handle is
		// here.
		wp_enqueue_style( 'molosoc-pillar1', $theme_uri . '/assets/css/pillar1.css', array( 'molosoc-components' ), $theme_version );
		wp_enqueue_script( 'molosoc-motion', $theme_uri . '/assets/js/motion.js', array(), $theme_version, true );
		wp_enqueue_script( 'molosoc-model-viewer', 'https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js', array(), '3.5.0', true );
		wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
		wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
		wp_enqueue_script( 'molosoc-sequential-text-reveal', $theme_uri . '/assets/js/sequential-text-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-severity-reveal', $theme_uri . '/assets/js/severity-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-mechanism-drawer', $theme_uri . '/assets/js/mechanism-drawer.js', array(), $theme_version, true );
		wp_enqueue_script( 'molosoc-scroll-refresh', $theme_uri . '/assets/js/scroll-refresh.js', array( 'gsap-scrolltrigger', 'molosoc-sequential-text-reveal', 'molosoc-severity-reveal' ), $theme_version, true );
	} elseif ( is_page( 'moisture-lock-foot-cover' ) ) {
		wp_enqueue_style( 'molosoc-product', $theme_uri . '/assets/css/product.css', array( 'molosoc-components' ), $theme_version );

		// model-viewer renders the always-rotating molosoc-3d.glb model in
		// the hero — same web component page-cracked-heels.php uses for its
		// "why moisturizer alone doesn't fix it" section. Needs
		// type="module" (see the script_loader_tag filter below), not a
		// plain classic script.
		wp_enqueue_script( 'molosoc-model-viewer', 'https://unpkg.com/@google/model-viewer@3.5.0/dist/model-viewer.min.js', array(), '3.5.0', true );

		// One GSAP/ScrollTrigger sequence, reused twice on this page
		// (sequential-text-reveal for "Make the pedicure last" and "Give it
		// as a gift"). Same real-file scroll-refresh.js convention as the
		// other branches above (WPO Minify silently drops inline scripts on
		// a bundled handle).
		wp_enqueue_script( 'gsap', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js', array(), '3.12.5', true );
		wp_enqueue_script( 'gsap-scrolltrigger', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js', array( 'gsap' ), '3.12.5', true );
		wp_enqueue_script( 'molosoc-sequential-text-reveal', $theme_uri . '/assets/js/sequential-text-reveal.js', array( 'gsap-scrolltrigger' ), $theme_version, true );
		wp_enqueue_script( 'molosoc-scroll-refresh', $theme_uri . '/assets/js/scroll-refresh.js', array( 'gsap-scrolltrigger', 'molosoc-sequential-text-reveal' ), $theme_version, true );
	}
}
add_action( 'wp_enqueue_scripts', 'molosoc_enqueue_assets' );

/**
 * model-viewer is an ES module, not a classic script — wp_enqueue_script()
 * always outputs a plain <script src="...">. Swap in type="module" for
 * just this one handle rather than switching the whole enqueue API.
 */
function molosoc_module_script_tag( $tag, $handle, $src ) {
	if ( 'molosoc-model-viewer' !== $handle ) {
		return $tag;
	}
	return '<script type="module" src="' . esc_url( $src ) . '"></script>';
}
add_filter( 'script_loader_tag', 'molosoc_module_script_tag', 10, 3 );

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
 * <head> block. Gated on is_page('moisture-lock-foot-cover') — the live
 * page at /foot-covers/moisture-lock-foot-cover/ turned out to be a
 * regular WP Page (page-id-951, page-template-default), not a WooCommerce
 * 'product' CPT despite the woocommerce-* body classes (WooCommerce is
 * just active site-wide); is_singular('product') never matched it. Same
 * is_page() convention as molosoc_category_schema() above.
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
	if ( ! is_page( 'moisture-lock-foot-cover' ) ) {
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
 * Pillar 1 — Cracked Heels — schema markup, ported from
 * content/molosoc-site/04-pillar1-cracked-heels/pillar1-cracked-heels-
 * schema.html. Same is_page() convention as the category/product schema
 * functions above (a normal template calling get_header(), which already
 * calls wp_head(), rather than front-page.php's self-built <head>).
 * FAQPage answers are kept in sync with this page's own copy (see
 * page-cracked-heels.php) — content/.../pillar1-cracked-heels-copy.md is
 * the locked source for both.
 */
function molosoc_pillar1_schema() {
	if ( ! is_page( 'cracked-heels' ) ) {
		return;
	}
	?>
	<meta name="description" content="Cracked heels aren't just dry skin — here's what's really causing them, what makes them worse, and what actually helps (without the gimmicks).">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/cracked-heels/#article",
	      "headline": "Cracked Heels: Why They Happen and How to Actually Fix Them",
	      "description": "Cracked heels aren't just dry skin — here's what's really causing them, what makes them worse, and what actually helps (without the gimmicks).",
	      "url": "https://molosoc.com/cracked-heels/",
	      "mainEntityOfPage": "https://molosoc.com/cracked-heels/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-30",
	      "dateModified": "2026-07-30",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/cracked-heels/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What causes cracked heels?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Cracked heels form when heel skin dries out and loses the elasticity it needs to stretch under pressure. The heel's outer edge carries the most weight with every step, so dry, inflexible skin in that spot is the first to split. Standing for long stretches, especially in open-back shoes, speeds this up by increasing both pressure and moisture loss."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What are painful deep cracked heels?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Painful deep cracked heels are cracks that hurt with every step because they've gone past surface dryness into a deeper layer of skin. At this stage, occasional moisturizing isn't enough — the skin needs consistent, sealed-in moisture to actually recover."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What are severe cracked heels?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Severe cracked heels are cracks that have widened, deepened, and can bleed. This level requires a daily routine that's actually followed through, not an occasional cream application, to give the skin a real chance to rebuild."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/cracked-heels/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Cracked Heels", "item": "https://molosoc.com/cracked-heels/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_pillar1_schema' );

/**
 * Pillar 2 — Ingrown Toenails — schema markup, ported from
 * content/molosoc-site/05-pillar2-ingrown-toenails/pillar2-ingrown-
 * toenails-schema.html. Same is_page() convention as molosoc_pillar1_schema()
 * above. FAQPage answers are kept in sync with this page's own copy (see
 * page-ingrown-toenails.php) — content/.../pillar2-ingrown-toenails-copy.md
 * is the locked source for both.
 */
function molosoc_pillar2_schema() {
	if ( ! is_page( 'ingrown-toenails' ) ) {
		return;
	}
	?>
	<meta name="description" content="An ingrown toenail can go from mildly annoying to genuinely painful fast. Here's what causes it, what actually helps at home, and when it's more than a nail problem.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/ingrown-toenails/#article",
	      "headline": "Ingrown Toenails: Why They Happen and What Actually Helps",
	      "description": "An ingrown toenail can go from mildly annoying to genuinely painful fast. Here's what causes it, what actually helps at home, and when it's more than a nail problem.",
	      "url": "https://molosoc.com/ingrown-toenails/",
	      "mainEntityOfPage": "https://molosoc.com/ingrown-toenails/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-30",
	      "dateModified": "2026-07-30",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/ingrown-toenails/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What causes ingrown toenails?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Ingrown toenails happen when the nail's edge grows down into the surrounding skin instead of straight across. Tight-fitting shoes press skin against the nail edge, and nails trimmed too short or rounded give that edge room to dig in as it grows back. Without a change to nail shape or footwear, the same pressure point tends to recreate the problem repeatedly."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "Do ingrown toenails go away on their own?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "A mild ingrown toenail can resolve on its own once the pressure causing it — tight shoes, a too-short trim — is removed and the skin has room to heal. Increasing redness, swelling, or pain that doesn't ease up after a few days means it isn't resolving on its own and needs more attention."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "Why does my big toenail hurt?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Pain concentrated at the big toenail is almost always pressure-related, coming from the nail edge, tight footwear, or both at once."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "What causes an ingrown big toe?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "The big toe is the most common site for an ingrown nail because it takes the most pressure with every step, making it the spot most likely to develop a nail edge that grows into skin."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/ingrown-toenails/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Ingrown Toenails", "item": "https://molosoc.com/ingrown-toenails/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_pillar2_schema' );

/**
 * Pillar 5 — Cream That Works — schema markup, ported from
 * content/molosoc-site/08-pillar5-cream-that-works/pillar5-cream-that-
 * works-schema.html. Same is_page() convention as molosoc_pillar1_schema()/
 * molosoc_pillar2_schema() above. FAQPage answers are kept in sync with
 * this page's own copy (see page-foot-cream-that-works.php) —
 * content/.../pillar5-cream-that-works-copy.md is the locked source for
 * both.
 */
function molosoc_pillar5_schema() {
	if ( ! is_page( 'foot-cream-that-works' ) ) {
		return;
	}
	?>
	<meta name="description" content="Tried every foot cream with no results? The cream probably isn't the problem — here's why it fails and what actually makes it work.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/foot-cream-that-works/#article",
	      "headline": "Does Foot Cream Actually Work? Why It Fails, and What Fixes It",
	      "description": "Tried every foot cream with no results? The cream probably isn't the problem — here's why it fails and what actually makes it work.",
	      "url": "https://molosoc.com/foot-cream-that-works/",
	      "mainEntityOfPage": "https://molosoc.com/foot-cream-that-works/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/foot-cream-that-works/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "Does foot cream actually work?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Foot cream does work — the reason it often seems like it doesn't is that most of it never gets the chance to fully absorb before it rubs off on socks, sheets, or floors. Given sustained, uninterrupted contact with skin, the same cream tends to perform much better."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "How long does foot cream take to absorb?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Most creams need sustained, uninterrupted contact with skin to fully absorb — often longer than the few minutes most routines actually give them before socks or shoes go back on."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "Should you put socks on after foot cream?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Yes — socks after cream help hold moisture against the skin longer than bare feet do, which is part of why the classic combination of cream plus socks works better than cream applied alone."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "How do you get soft feet overnight?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "The traditional approach is applying a heavier cream and sealing it under socks overnight, which gives skin hours of uninterrupted contact time to absorb. A shorter, focused session with the cream sealed against the skin can achieve much of that same result without needing to commit to wearing anything all night."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/foot-cream-that-works/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Cream That Works", "item": "https://molosoc.com/foot-cream-that-works/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_pillar5_schema' );

/**
 * Pillar 4 — Dry Skin on Feet — schema markup, ported from
 * content/molosoc-site/07-pillar4-dry-skin-feet/pillar4-dry-skin-feet-
 * schema.html. Same is_page() convention as molosoc_pillar1_schema()/
 * molosoc_pillar2_schema() above. FAQPage answers are kept in sync with
 * this page's own copy (see page-dry-skin-feet.php) —
 * content/.../pillar4-dry-skin-feet-copy.md is the locked source for both.
 */
function molosoc_pillar4_schema() {
	if ( ! is_page( 'dry-skin-feet' ) ) {
		return;
	}
	?>
	<meta name="description" content="Still dry after moisturizing? Here's what actually causes dry skin on feet, why cream alone doesn't fix it, and what actually helps it stop.">
	<script type="application/ld+json">
	{
	  "@context": "https://schema.org",
	  "@graph": [
	    {
	      "@type": "Article",
	      "@id": "https://molosoc.com/dry-skin-feet/#article",
	      "headline": "Dry Skin on Feet: Why It Happens and What Actually Helps",
	      "description": "Still dry after moisturizing? Here's what actually causes dry skin on feet, why cream alone doesn't fix it, and what actually helps it stop.",
	      "url": "https://molosoc.com/dry-skin-feet/",
	      "mainEntityOfPage": "https://molosoc.com/dry-skin-feet/",
	      "author": { "@id": "https://molosoc.com/#organization" },
	      "publisher": { "@id": "https://molosoc.com/#organization" },
	      "isPartOf": { "@id": "https://molosoc.com/#website" },
	      "datePublished": "2026-07-31",
	      "dateModified": "2026-07-31",
	      "inLanguage": "en"
	    },
	    {
	      "@type": "FAQPage",
	      "@id": "https://molosoc.com/dry-skin-feet/#faq",
	      "mainEntity": [
	        {
	          "@type": "Question",
	          "name": "What causes dry skin on feet?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Soles have no oil glands the way most of the rest of the skin does, so they rely entirely on external moisture to stay soft. Enclosed feet also lose moisture to socks, shoes, and air circulation throughout the day, and seasonal triggers like indoor heating, cold air, and hot showers strip moisture faster than usual."
	          }
	        },
	        {
	          "@type": "Question",
	          "name": "Why are my feet so dry even when I moisturize?",
	          "acceptedAnswer": {
	            "@type": "Answer",
	            "text": "Cream applied and left uncovered gets absorbed by socks or rubbed off on floors within minutes, long before the skin has had a real chance to take it in. The fix isn't a thicker layer or a pricier formula — it's uninterrupted contact time so the cream can actually absorb instead of transferring elsewhere."
	          }
	        }
	      ]
	    },
	    {
	      "@type": "BreadcrumbList",
	      "@id": "https://molosoc.com/dry-skin-feet/#breadcrumb",
	      "itemListElement": [
	        { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://molosoc.com/" },
	        { "@type": "ListItem", "position": 2, "name": "Dry Skin on Feet", "item": "https://molosoc.com/dry-skin-feet/" }
	      ]
	    }
	  ]
	}
	</script>
	<?php
}
add_action( 'wp_head', 'molosoc_pillar4_schema' );

/**
 * WordPress doesn't allow .glb uploads by default (not in its core mime
 * whitelist) — needed for the 3D product model in the media library.
 */
function molosoc_allow_glb_uploads( $mimes ) {
	$mimes['glb'] = 'model/gltf-binary';
	return $mimes;
}
add_filter( 'upload_mimes', 'molosoc_allow_glb_uploads' );
