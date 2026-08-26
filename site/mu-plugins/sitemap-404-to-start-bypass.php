<?php
/**
 * Plugin Name: MOLOSOC Sitemap 404-to-Start Bypass
 * Description: WordPress marks core sitemap routes as is_404() (WP::handle_404 has no sitemap awareness). 404 to Start 1.6.1 reads that flag on template_redirect and calls wp_redirect() without exiting, so /wp-sitemap.xml answers 301 to the homepage while WordPress still renders the sitemap XML. This removes that one callback, on sitemap routes only.
 */
add_action( 'template_redirect', function () {
    if ( get_query_var( 'sitemap' ) || get_query_var( 'sitemap-stylesheet' ) ) {
        remove_action( 'template_redirect', 'f042start_output_header' );
    }
}, 1 );
