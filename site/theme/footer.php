<?php
/**
 * Site-wide footer — rebuilt to match the old Thrive footer's content
 * (legal links, social icons, copyright). Used by every template except
 * front-page.php (self-contained by design, see the note at its top).
 */

defined( 'ABSPATH' ) || exit;

$molosoc_theme_uri = get_stylesheet_directory_uri();
$molosoc_is_cz      = function_exists( 'pll_current_language' ) && pll_current_language() === 'cz';

$molosoc_social_links = array(
	'Facebook'  => 'https://www.facebook.com/molosoc',
	'YouTube'   => 'https://www.youtube.com/@Molosoc',
	'Instagram' => 'https://www.instagram.com/molosoc_/',
	'TikTok'    => 'https://www.tiktok.com/@molosoc',
	'X'         => 'https://x.com/Molosoc_',
);

$molosoc_legal_links = array(
	__( 'Disclaimer', 'molosoc' )     => home_url( '/legal-disclaimer/' ),
	// Privacy policy and Terms of service have no English translation yet
	// (both pages currently hold Czech-only legal text on staging AND on
	// live molosoc.com — a pre-existing gap, not something introduced
	// here). Left unbranched/pointing at the same page for both languages
	// until real English copy exists to pair against.
	__( 'Privacy policy', 'molosoc' ) => home_url( '/privacy-policies/' ),
	__( 'Terms of service', 'molosoc' ) => home_url( '/terms-of-services/' ),
	( $molosoc_is_cz ? 'Zásady dopravy' : __( 'Shipping policy', 'molosoc' ) ) => home_url( $molosoc_is_cz ? '/zasady-dopravy/' : '/shipping-policy/' ),
	( $molosoc_is_cz ? 'Zásady vrácení a refundace' : __( 'Refund & returns', 'molosoc' ) ) => home_url( $molosoc_is_cz ? '/vraceni-a-refundace/' : '/refund-policy/' ),
	__( 'Contact', 'molosoc' )        => home_url( '/contact-kontakt/' ),
);
?>
<footer class="molosoc-site-footer">
	<div class="molosoc-site-footer__inner">
		<div class="molosoc-site-footer__brand">
			<a href="<?php echo esc_url( home_url( '/' ) ); ?>">
				<img src="<?php echo esc_url( $molosoc_theme_uri . '/assets/images/molosoc-logo-white.png' ); ?>" alt="<?php echo esc_attr( get_bloginfo( 'name' ) ); ?>" height="28" loading="lazy" decoding="async">
			</a>

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

		<!-- Visa/Mastercard logos are required in the e-shop footer under
		     Comgate's terms of service; Comgate's own logo is recommended
		     alongside them. Official pre-made banner from
		     help.comgate.cz/docs/en/logos-and-info-on-web, dark-background
		     variant. -->
		<div class="molosoc-site-footer__payments">
			<img src="<?php echo esc_url( $molosoc_theme_uri . '/assets/images/comgate-payment-methods-dark.png' ); ?>" alt="<?php esc_attr_e( 'Accepted payment methods: Comgate, Visa, Mastercard, Google Pay, Apple Pay', 'molosoc' ); ?>" height="24" loading="lazy" decoding="async">
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
