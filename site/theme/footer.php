<?php
/**
 * Minimal footer — placeholder chrome only. Rebuilding this to match the
 * old Thrive footer (legal links, social icons, copyright) is tracked as
 * open work; see the report that shipped alongside this build.
 */

defined( 'ABSPATH' ) || exit;
?>
<footer class="molosoc-site-footer">
	<p>&copy; <?php echo esc_html( gmdate( 'Y' ) ); ?> <?php bloginfo( 'name' ); ?></p>
</footer>

<?php wp_footer(); ?>
</body>
</html>
