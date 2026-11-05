<?php
/**
 * Real customer reviews on the sales landings (Issue #335).
 *
 * The landings (Landing B CZ/EN, Christmas CZ/EN) never showed the native
 * WooCommerce reviews: they only link to the product page. This renders the
 * APPROVED native reviews of product 364 and nothing else. No synthesized,
 * hard-coded or placeholder testimonials: with zero approved reviews the
 * helper outputs nothing at all. Reviewer e-mail is never read or printed;
 * only the display name, star rating, date and text are shown.
 */

defined( 'ABSPATH' ) || exit;

/** Approved native reviews of the main product, newest first. */
function molosoc_real_reviews_get( $limit = 6 ) {
	if ( ! defined( 'MOLOSOC_PRODUCT_ID' ) || ! function_exists( 'get_comments' ) ) {
		return array();
	}
	$comments = get_comments(
		array(
			'post_id' => MOLOSOC_PRODUCT_ID,
			'status'  => 'approve',
			'type'    => 'review',
			'parent'  => 0,
			'number'  => max( 1, (int) $limit ),
			'orderby' => 'comment_date_gmt',
			'order'   => 'DESC',
		)
	);
	return is_array( $comments ) ? $comments : array();
}

/** Section markup for $lang ('cz'|'en'); '' when there are no approved reviews. */
function molosoc_real_reviews_html( $lang = 'cz' ) {
	$reviews = molosoc_real_reviews_get( 6 );
	if ( ! $reviews ) {
		return '';
	}
	$cz    = 'cz' === $lang;
	$title = $cz ? 'Recenze zákazníků' : 'Customer reviews';
	$all   = $cz ? 'Všechny recenze' : 'All reviews';
	$url   = function_exists( 'molosoc_product_url' ) ? molosoc_product_url( $cz ? 'cz' : 'en' ) . '#reviews' : '';

	ob_start();
	?>
	<style id="molosoc-real-reviews-css">.lpb-real-reviews__list{margin:0;padding:0;list-style:none;text-align:left}.lpb-real-reviews__list li+li{margin-top:.85rem;padding-top:.85rem;border-top:1px solid rgba(0,0,0,.08)}.lpb-real-reviews__list p{margin:.25rem 0 0}.lpb-real-reviews__stars{display:block;color:#b8860b;letter-spacing:.1em}.lpb-real-reviews__meta{display:block;margin-top:.25rem;font-size:.85rem;opacity:.7}</style>
	<section class="lpb-section" id="molosoc-real-reviews" aria-label="<?php echo esc_attr( $title ); ?>">
		<figure class="lpb-testimonial lpb-real-reviews">
			<p class="lpb-testimonial__title"><?php echo esc_html( $title ); ?></p>
			<ul class="lpb-real-reviews__list">
				<?php foreach ( $reviews as $c ) : ?>
					<?php $rating = (int) get_comment_meta( $c->comment_ID, 'rating', true ); ?>
					<li>
						<?php if ( $rating >= 1 && $rating <= 5 ) : ?>
							<span class="lpb-real-reviews__stars" role="img" aria-label="<?php echo esc_attr( $rating . '/5' ); ?>"><?php echo esc_html( str_repeat( '★', $rating ) . str_repeat( '☆', 5 - $rating ) ); ?></span>
						<?php endif; ?>
						<p><?php echo esc_html( wp_strip_all_tags( $c->comment_content ) ); ?></p>
						<span class="lpb-real-reviews__meta"><?php echo esc_html( $c->comment_author ); ?></span>
					</li>
				<?php endforeach; ?>
			</ul>
			<?php if ( $url ) : ?>
				<p><a href="<?php echo esc_url( $url ); ?>"><?php echo esc_html( $all ); ?></a></p>
			<?php endif; ?>
		</figure>
	</section>
	<?php
	return (string) ob_get_clean();
}
