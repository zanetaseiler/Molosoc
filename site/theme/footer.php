<?php
/**
 * Site-wide footer — rebuilt to match the old Thrive footer's content
 * (legal links, social icons, copyright). Used by every template except
 * front-page.php (self-contained by design, see the note at its top).
 */

defined( 'ABSPATH' ) || exit;

$molosoc_social_links = array(
	'Facebook'  => 'https://www.facebook.com/molosoc',
	'YouTube'   => 'https://www.youtube.com/@Molosoc',
	'Instagram' => 'https://www.instagram.com/molosoc_/',
	'TikTok'    => 'https://www.tiktok.com/@molosoc',
	'X'         => 'https://x.com/Molosoc_',
);

$molosoc_legal_links = array(
	__( 'Disclaimer', 'molosoc' )     => home_url( '/legal-disclaimer/' ),
	__( 'Privacy policy', 'molosoc' ) => home_url( '/privacy-policies/' ),
	__( 'Terms of service', 'molosoc' ) => home_url( '/terms-of-services/' ),
	__( 'Contact', 'molosoc' )        => home_url( '/contact-kontakt/' ),
);
?>
<footer class="molosoc-site-footer">
	<div class="molosoc-site-footer__inner">
		<div class="molosoc-site-footer__brand">
			<a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php bloginfo( 'name' ); ?></a>

			<ul class="molosoc-social-links">
				<?php foreach ( $molosoc_social_links as $label => $url ) : ?>
					<li>
						<a href="<?php echo esc_url( $url ); ?>" target="_blank" rel="noopener noreferrer" aria-label="<?php echo esc_attr( $label ); ?>">
							<?php echo esc_html( $label ); ?>
						</a>
					</li>
				<?php endforeach; ?>
			</ul>
		</div>

		<div class="molosoc-site-footer__legal">
			<p class="molosoc-site-footer__copyright">
				<?php
				printf(
					/* translators: %1$s: current year, %2$s: site name */
					esc_html__( 'Copyright © %1$s %2$s. All Rights Reserved.', 'molosoc' ),
					esc_html( gmdate( 'Y' ) ),
					esc_html( get_bloginfo( 'name' ) )
				);
				?>
			</p>

			<ul class="molosoc-legal-links">
				<?php foreach ( $molosoc_legal_links as $label => $url ) : ?>
					<li><a href="<?php echo esc_url( $url ); ?>"><?php echo esc_html( $label ); ?></a></li>
				<?php endforeach; ?>
			</ul>
		</div>
	</div>
</footer>

<?php wp_footer(); ?>
</body>
</html>
