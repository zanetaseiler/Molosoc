<?php
/**
 * Template Name: Blog / Journal index
 *
 * Auto-selected by WordPress for the Page with slug "blog". Editorial
 * index of every content page on the site EXCEPT the three structural
 * pages (Homepage, Category, Product — see docs/site-structure.md §1-4):
 * the 5 TOFU pillars (§7) and their 6 spoke articles (§8), 11 tiles total.
 *
 * Deliberately static — no GSAP/ScrollTrigger, no motion.js. This is an
 * index page, not a story beat; big photo tiles + a short heading is the
 * whole design, per the brief ("elegant, minimalistic, editorial").
 *
 * Also serves the Czech "Magazín" page (/cz/magazin/, template assigned
 * explicitly since its slug isn't "blog"): same design, but only the 5
 * guides that exist in Czech (3 pillars + the two kuří-oko spokes) —
 * the other 6 EN guides have no CZ translation yet, and tiles must not
 * silently switch language. Same $molosoc_is_cz pattern as
 * page-foot-covers.php.
 */

defined( 'ABSPATH' ) || exit;

get_header();

$molosoc_img = 'https://molosoc.com/wp-content/uploads/2026/07/';
$molosoc_is_cz = function_exists( 'pll_current_language' ) && pll_current_language() === 'cz';

// Eyebrow = parent topic, heading = the short, specific angle. Pillars
// carry "Guide" as their eyebrow (they ARE the topic); spokes carry the
// parent pillar's name so the index reads as a real taxonomy at a glance.
if ( $molosoc_is_cz ) {
	$molosoc_blog_tiles = array(
		array(
			'href'    => home_url( '/cz/popraskane-paty/' ),
			'image'   => $molosoc_img . 'pillar1_01_heels_floor.jpg',
			'eyebrow' => 'Průvodce',
			'heading' => 'Popraskané paty',
			'alt'     => 'Bosé paty na koupelnové podlaze',
			'featured' => true,
		),
		array(
			'href'    => home_url( '/cz/zarostly-nehet/' ),
			'image'   => $molosoc_img . 'pillar2_01_soaking.jpg',
			'eyebrow' => 'Průvodce',
			'heading' => 'Zarostlý nehet',
			'alt'     => 'Nohy máčené v teplé lázni',
		),
		array(
			'href'    => home_url( '/cz/kurici-oko/' ),
			'image'   => $molosoc_img . 'pillar3_01_foot_file.jpg',
			'eyebrow' => 'Průvodce',
			'heading' => 'Kuří oko a mozoly',
			'alt'     => 'Pilník na nohy položený vedle bosé nohy',
		),
		array(
			'href'    => home_url( '/cz/kurici-oko/jak-odstranit/' ),
			'image'   => $molosoc_img . 'molosoc_spa_treatment_04.jpg',
			'eyebrow' => 'Kuří oko',
			'heading' => 'Jak ho odstranit',
			'alt'     => 'Probíhající domácí lázeňská péče o nohy',
		),
		array(
			'href'    => home_url( '/cz/kurici-oko/na-chodidle/' ),
			'image'   => $molosoc_img . 'molosoc_spa_treatment_03.jpg',
			'eyebrow' => 'Kuří oko',
			'heading' => 'Na chodidle',
			'alt'     => 'Probíhající domácí lázeňská péče o nohy',
		),
	);
} else {
	$molosoc_blog_tiles = array(
	array(
		'href'    => home_url( '/cracked-heels/' ),
		'image'   => $molosoc_img . 'pillar1_01_heels_floor.jpg',
		'eyebrow' => __( 'Guide', 'molosoc' ),
		'heading' => __( 'Cracked Heels', 'molosoc' ),
		'alt'     => __( 'Bare heels resting on a bathroom floor', 'molosoc' ),
		'featured' => true,
	),
	array(
		'href'    => home_url( '/ingrown-toenails/' ),
		'image'   => $molosoc_img . 'pillar2_01_soaking.jpg',
		'eyebrow' => __( 'Guide', 'molosoc' ),
		'heading' => __( 'Ingrown Toenails', 'molosoc' ),
		'alt'     => __( 'Feet soaking in a warm basin', 'molosoc' ),
	),
	array(
		'href'    => home_url( '/hardened-skin-calluses/' ),
		'image'   => $molosoc_img . 'pillar3_01_foot_file.jpg',
		'eyebrow' => __( 'Guide', 'molosoc' ),
		'heading' => __( 'Hardened Skin', 'molosoc' ),
		'alt'     => __( 'A foot file resting beside a bare foot', 'molosoc' ),
	),
	array(
		'href'    => home_url( '/dry-skin-feet/' ),
		'image'   => $molosoc_img . 'pillar4_01_wool_socks.jpg',
		'eyebrow' => __( 'Guide', 'molosoc' ),
		'heading' => __( 'Dry Skin', 'molosoc' ),
		'alt'     => __( 'A pair of soft wool socks', 'molosoc' ),
	),
	array(
		'href'    => home_url( '/foot-cream-that-works/' ),
		'image'   => $molosoc_img . 'pillar5_01_drawer.jpg',
		'eyebrow' => __( 'Guide', 'molosoc' ),
		'heading' => __( 'Cream That Works', 'molosoc' ),
		'alt'     => __( 'A bathroom drawer crowded with half-used cream tubes', 'molosoc' ),
	),
	array(
		'href'    => home_url( '/ingrown-toenails/treatment/' ),
		'image'   => $molosoc_img . 'molosoc_spa_treatment_02.jpg',
		'eyebrow' => __( 'Ingrown Toenails', 'molosoc' ),
		'heading' => __( 'Treatment', 'molosoc' ),
		'alt'     => __( 'An at-home spa foot treatment in progress', 'molosoc' ),
	),
	array(
		'href'    => home_url( '/hardened-skin-calluses/callus-remover/' ),
		'image'   => $molosoc_img . 'molosoc_spa_treatment_04.jpg',
		'eyebrow' => __( 'Hardened Skin', 'molosoc' ),
		'heading' => __( 'Callus Remover', 'molosoc' ),
		'alt'     => __( 'An at-home spa foot treatment in progress', 'molosoc' ),
	),
	array(
		'href'    => home_url( '/ingrown-toenails/prevent/' ),
		'image'   => $molosoc_img . 'molosoc_spa_treatment_03.jpg',
		'eyebrow' => __( 'Ingrown Toenails', 'molosoc' ),
		'heading' => __( 'Prevention', 'molosoc' ),
		'alt'     => __( 'An at-home spa foot treatment in progress', 'molosoc' ),
	),
	array(
		'href'    => home_url( '/cracked-heels/cracked-heels-cream/' ),
		'image'   => $molosoc_img . 'molosoc_cracked_heels_05.jpg',
		'eyebrow' => __( 'Cracked Heels', 'molosoc' ),
		'heading' => __( 'The Right Cream', 'molosoc' ),
		'alt'     => __( 'Cream being massaged into a heel', 'molosoc' ),
	),
	array(
		'href'    => home_url( '/cracked-heels/cracked-heels-treatment/' ),
		'image'   => $molosoc_img . 'molosoc-6a6c3e786c068.png',
		'eyebrow' => __( 'Cracked Heels', 'molosoc' ),
		'heading' => __( 'Treatment', 'molosoc' ),
		'alt'     => __( 'A step-by-step cracked heels treatment routine', 'molosoc' ),
	),
	array(
		'href'    => home_url( '/cracked-heels/fix-permanently/' ),
		'image'   => $molosoc_img . 'molosoc_cracked_heels_03.jpg',
		'eyebrow' => __( 'Cracked Heels', 'molosoc' ),
		'heading' => __( 'Fixed For Good', 'molosoc' ),
		'alt'     => __( 'Smooth, healed heels after a consistent routine', 'molosoc' ),
	),
	);
}
?>

<main id="main">

	<!-- Intro — plain type, no photo. Deliberately quieter than every other
	     template's photo hero: the tile grid below is the visual moment. -->
	<section class="molosoc-section molosoc-section--bg-cream molosoc-blog-intro">
		<div class="molosoc-section__inner">
			<p class="molosoc-eyebrow"><?php echo esc_html( $molosoc_is_cz ? 'Péče o nohy, do hloubky' : __( 'Foot care, explored', 'molosoc' ) ); ?></p>
			<h1><?php echo esc_html( $molosoc_is_cz ? 'Magazín' : __( 'The Journal', 'molosoc' ) ); ?></h1>
			<p class="molosoc-section__lede">
				<?php echo esc_html( $molosoc_is_cz ? 'Pět upřímných průvodců o popraskaných patách, zarostlém nehtu a kuřích okách — a o rutinách, které skutečně pomáhají. Bez vaty, bez strašení.' : __( 'Eleven honest guides on cracked heels, ingrown toenails, calluses, and the routines that actually help — no filler, no fear-mongering.', 'molosoc' ) ); ?>
			</p>
		</div>
	</section>

	<!-- Tile grid — big editorial photo tiles, caption overlaid, short
	     heading only (no body copy) per the brief. First tile spans 2
	     columns as the featured entry point. -->
	<section class="molosoc-section molosoc-section--bg-cream molosoc-blog-grid-section">
		<div class="molosoc-section__inner">
			<div class="molosoc-blog-grid">
				<?php foreach ( $molosoc_blog_tiles as $molosoc_tile ) : ?>
					<a class="molosoc-blog-tile<?php echo ! empty( $molosoc_tile['featured'] ) ? ' molosoc-blog-tile--featured' : ''; ?>" href="<?php echo esc_url( $molosoc_tile['href'] ); ?>">
						<img src="<?php echo esc_url( $molosoc_tile['image'] ); ?>" alt="<?php echo esc_attr( $molosoc_tile['alt'] ); ?>" loading="lazy" decoding="async">
						<span class="molosoc-blog-tile__scrim" aria-hidden="true"></span>
						<span class="molosoc-blog-tile__text">
							<span class="molosoc-blog-tile__eyebrow"><?php echo esc_html( $molosoc_tile['eyebrow'] ); ?></span>
							<span class="molosoc-blog-tile__heading"><?php echo esc_html( $molosoc_tile['heading'] ); ?></span>
						</span>
					</a>
				<?php endforeach; ?>
			</div>
		</div>
	</section>

</main>

<?php get_footer(); ?>
