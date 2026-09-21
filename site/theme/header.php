<?php
/**
 * Header used by every template except front-page.php (which is
 * intentionally self-contained — see the note at the top of that file).
 * The <header> markup itself lives in template-parts/site-header.php so
 * front-page.php's "card hero" variant can reuse it verbatim.
 */

defined( 'ABSPATH' ) || exit;
?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>

<a class="molosoc-skip-link" href="#main"><?php esc_html_e( 'Skip to content', 'molosoc' ); ?></a>

<?php get_template_part( 'template-parts/site-header' ); ?>
