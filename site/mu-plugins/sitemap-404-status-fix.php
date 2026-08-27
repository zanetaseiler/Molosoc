<?php
/**
 * Plugin Name: MOLOSOC Sitemap 404 Status Fix
 * Description: WP::handle_404() has no sitemap awareness, so a core sitemap route is marked is_404() before template_redirect. WordPress then renders valid sitemap XML under a 404 status, and any 404-triggered plugin (404 to Start) fires on it. This short-circuits that status handling for sitemap routes only. Genuinely unavailable sitemaps still 404, because WP_Sitemaps::render_sitemaps() sets that itself later.
 */
add_filter( 'pre_handle_404', function ( $preempt, $wp_query ) {
    if (
        $wp_query->get( 'sitemap' ) ||
        $wp_query->get( 'sitemap-stylesheet' )
    ) {
        return true;
    }
    return $preempt;
}, 10, 2 );
