<?php
/**
 * Fallback template — required for WordPress to consider this theme valid,
 * and the final rung of the template hierarchy for anything without a more
 * specific template (single posts, generic pages, archives, search, 404).
 * Deliberately plain; per-type templates (page.php, single.php, archive.php,
 * WooCommerce overrides) are open work — see the report that shipped
 * alongside this build.
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="main" class="molosoc-main">
	<?php if ( have_posts() ) : ?>
		<?php while ( have_posts() ) : the_post(); ?>
			<article <?php post_class(); ?>>
				<h1><?php the_title(); ?></h1>
				<div class="molosoc-entry-content">
					<?php the_content(); ?>
				</div>
			</article>
		<?php endwhile; ?>
	<?php else : ?>
		<p><?php esc_html_e( 'Nothing found.', 'molosoc' ); ?></p>
	<?php endif; ?>
</main>

<?php get_footer(); ?>
