<?php
/**
 * Contextual "Related reading" internal links (Issue #200).
 *
 * GSC showed the CZ foot-care pillars and spokes almost never linked to one
 * another or to the Czech Magazín (/cz/magazin/), and the EN cracked-heels /
 * ingrown-toenail spokes only linked back to their pillar. This renders one
 * small, plain-anchor link list per page from a single map, so the link graph
 * lives in one reviewable place. No URL, slug or permalink is changed; every
 * target already exists and is linked from the pillar/spoke templates today.
 */

defined( 'ABSPATH' ) || exit;

/**
 * Link map: page key => list of [ path, EN label, CZ label ].
 * Keys are used by molosoc_related_links( $key ) in the templates.
 */
function molosoc_related_links_map() {
	return array(
		'cracked-heels'           => array(
			array( '/ingrown-toenails/', 'Ingrown toenails: causes and care', 'Zarostlý nehet: příčiny a péče' ),
			array( '/hardened-skin-calluses/', 'Hardened skin and calluses', 'Kuří oko a mozoly' ),
			array( '/dry-skin-feet/', null, 'Suchá kůže na chodidlech' ),
			array( '/blog/', 'More foot-care guides in the Journal', 'Další průvodci péčí o nohy v Magazínu' ),
		),
		'sucha-kuze'              => array(
			array( '/cracked-heels/', 'Cracked heels: what helps', 'Popraskané paty: co pomáhá' ),
			array( '/hardened-skin-calluses/', 'Hardened skin and calluses', 'Kuří oko a mozoly' ),
			array( '/blog/', 'More foot-care guides in the Journal', 'Další průvodci péčí o nohy v Magazínu' ),
		),
		'ingrown-toenails'        => array(
			array( '/cracked-heels/', 'Cracked heels: what helps', 'Popraskané paty: co pomáhá' ),
			array( '/hardened-skin-calluses/', 'Hardened skin and calluses', 'Kuří oko a mozoly' ),
			array( '/blog/', 'More foot-care guides in the Journal', 'Další průvodci péčí o nohy v Magazínu' ),
		),
		'hardened-skin-calluses'  => array(
			array( '/cracked-heels/', 'Cracked heels: what helps', 'Popraskané paty: co pomáhá' ),
			array( '/ingrown-toenails/', 'Ingrown toenails: causes and care', 'Zarostlý nehet: příčiny a péče' ),
			array( '/blog/', 'More foot-care guides in the Journal', 'Další průvodci péčí o nohy v Magazínu' ),
		),
		'callus-remover'         => array(
			array( '/cracked-heels/', 'Cracked heels: what helps', 'Popraskané paty: co pomáhá' ),
			array( '/blog/', 'More foot-care guides in the Journal', 'Další průvodci péčí o nohy v Magazínu' ),
		),
		'fix-permanently'         => array(
			array( '/cracked-heels/cracked-heels-treatment/', 'Cracked heels treatment', 'Ošetření popraskaných pat' ),
			array( '/cracked-heels/cracked-heels-cream/', 'What to look for in a cracked heels cream', 'Na co se zaměřit u krému na popraskané paty' ),
		),
		'cracked-heels-treatment' => array(
			array( '/cracked-heels/fix-permanently/', 'How to fix cracked heels permanently', 'Jak popraskané paty vyřešit trvale' ),
			array( '/cracked-heels/cracked-heels-cream/', 'What to look for in a cracked heels cream', 'Na co se zaměřit u krému na popraskané paty' ),
		),
		'cracked-heels-cream'     => array(
			array( '/cracked-heels/cracked-heels-treatment/', 'Cracked heels treatment', 'Ošetření popraskaných pat' ),
			array( '/cracked-heels/fix-permanently/', 'How to fix cracked heels permanently', 'Jak popraskané paty vyřešit trvale' ),
		),
		'ingrown-treatment'       => array(
			array( '/ingrown-toenails/prevent/', 'How to prevent ingrown toenails', 'Jak předcházet zarostlému nehtu' ),
		),
		'ingrown-prevent'         => array(
			array( '/ingrown-toenails/treatment/', 'Ingrown toenail treatment', 'Ošetření zarostlého nehtu' ),
		),
	);
}

/**
 * Print the Related reading section for a page key. Prints nothing for an
 * unknown key. Language: Czech when Polylang reports 'cz', else English.
 * Czech links to /cz/ equivalents where the CZ page exists (see $cz_paths);
 * paths with no CZ twin are skipped in Czech rather than cross-linking to EN.
 * A row whose EN label is null is Czech-only (e.g. Issue #229): skipped in EN.
 */
function molosoc_related_links( $key ) {
	$map = molosoc_related_links_map();
	if ( ! isset( $map[ $key ] ) ) {
		return;
	}
	$is_cz   = function_exists( 'pll_current_language' ) && pll_current_language() === 'cz';
	$cz_path = array(
		'/cracked-heels/'         => '/cz/popraskane-paty/',
		'/ingrown-toenails/'      => '/cz/zarostly-nehet/',
		'/hardened-skin-calluses/' => '/cz/kurici-oko/',
		'/blog/'                  => '/cz/magazin/',
		'/dry-skin-feet/'         => '/cz/sucha-kuze-na-chodidlech/',
	);
	$items = array();
	foreach ( $map[ $key ] as $row ) {
		list( $path, $en, $cz ) = $row;
		if ( ! $is_cz && null === $en ) {
			continue; // CZ-only row (no EN label): the EN page keeps its own links.
		}
		if ( $is_cz ) {
			if ( ! isset( $cz_path[ $path ] ) ) {
				continue;
			}
			$items[] = array( $cz_path[ $path ], $cz );
		} else {
			$items[] = array( $path, $en );
		}
	}
	if ( ! $items ) {
		return;
	}
	?>
	<!-- RELATED READING (Issue #200) -->
	<section class="molosoc-section molosoc-section--bg-cream molosoc-related-links">
		<div class="molosoc-section__inner" style="text-align:center;">
			<p class="molosoc-eyebrow"><?php echo esc_html( $is_cz ? 'Související čtení' : 'Related reading' ); ?></p>
			<ul style="list-style:none;margin:0;padding:0;">
				<?php foreach ( $items as $item ) : ?>
					<li><a href="<?php echo esc_url( home_url( $item[0] ) ); ?>"><?php echo esc_html( $item[1] ); ?></a></li>
				<?php endforeach; ?>
			</ul>
		</div>
	</section>
	<?php
}
