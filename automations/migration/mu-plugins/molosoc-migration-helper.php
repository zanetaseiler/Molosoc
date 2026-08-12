<?php
/**
 * Plugin Name: Molosoc Migration Helper (temporary)
 * Description: Admin-only REST endpoints wrapping Polylang's PHP API so the
 * staging->production migration can assign per-post language, link EN/CZ
 * translation pairs, and set per-language nav menu locations — capabilities
 * the free Polylang edition does not expose over REST. Remove this file once
 * the migration is verified complete.
 */

defined('ABSPATH') || exit;

add_action('rest_api_init', function () {
    $perm = function () {
        return current_user_can('manage_options');
    };

    register_rest_route('molosoc-migrate/v1', '/set-language', [
        'methods'             => 'POST',
        'permission_callback' => $perm,
        'callback'            => function (WP_REST_Request $req) {
            if (!function_exists('pll_set_post_language')) {
                return new WP_Error('no_polylang', 'Polylang not active', ['status' => 500]);
            }
            $post_id = (int) $req['post_id'];
            $lang    = sanitize_key($req['lang']);
            if (!get_post($post_id)) {
                return new WP_Error('no_post', "Post $post_id not found", ['status' => 404]);
            }
            pll_set_post_language($post_id, $lang);
            return [
                'post_id'  => $post_id,
                'language' => pll_get_post_language($post_id),
            ];
        },
    ]);

    register_rest_route('molosoc-migrate/v1', '/link-translations', [
        'methods'             => 'POST',
        'permission_callback' => $perm,
        'callback'            => function (WP_REST_Request $req) {
            if (!function_exists('pll_save_post_translations')) {
                return new WP_Error('no_polylang', 'Polylang not active', ['status' => 500]);
            }
            $translations = $req['translations']; // e.g. {"en": 123, "cz": 456}
            if (!is_array($translations) || count($translations) < 2) {
                return new WP_Error('bad_request', 'translations must map >=2 langs to post IDs', ['status' => 400]);
            }
            $clean = [];
            foreach ($translations as $lang => $id) {
                $clean[sanitize_key($lang)] = (int) $id;
                if (!get_post((int) $id)) {
                    return new WP_Error('no_post', "Post $id not found", ['status' => 404]);
                }
            }
            pll_save_post_translations($clean);
            $first = reset($clean);
            return [
                'requested' => $clean,
                'saved'     => pll_get_post_translations($first),
            ];
        },
    ]);

    register_rest_route('molosoc-migrate/v1', '/status/(?P<id>\d+)', [
        'methods'             => 'GET',
        'permission_callback' => $perm,
        'callback'            => function (WP_REST_Request $req) {
            $id = (int) $req['id'];
            return [
                'post_id'      => $id,
                'language'     => function_exists('pll_get_post_language') ? pll_get_post_language($id) : null,
                'translations' => function_exists('pll_get_post_translations') ? pll_get_post_translations($id) : null,
            ];
        },
    ]);

    register_rest_route('molosoc-migrate/v1', '/set-nav-menus', [
        'methods'             => 'POST',
        'permission_callback' => $perm,
        'callback'            => function (WP_REST_Request $req) {
            $theme       = sanitize_key($req['theme']);       // e.g. "molosoc"
            $location    = sanitize_key($req['location']);    // e.g. "primary"
            $assignments = $req['assignments'];               // e.g. {"en": 12, "cz": 13}
            if (!$theme || !$location || !is_array($assignments)) {
                return new WP_Error('bad_request', 'theme, location, assignments required', ['status' => 400]);
            }
            $options = get_option('polylang');
            if (!is_array($options)) {
                return new WP_Error('no_polylang', 'Polylang options not found', ['status' => 500]);
            }
            if (!isset($options['nav_menus']) || !is_array($options['nav_menus'])) {
                $options['nav_menus'] = [];
            }
            if (!isset($options['nav_menus'][$theme]) || !is_array($options['nav_menus'][$theme])) {
                $options['nav_menus'][$theme] = [];
            }
            $clean = [];
            foreach ($assignments as $lang => $menu_id) {
                $clean[sanitize_key($lang)] = (int) $menu_id;
            }
            $options['nav_menus'][$theme][$location] = $clean;
            update_option('polylang', $options);
            $saved = get_option('polylang');
            return ['saved_nav_menus' => $saved['nav_menus']];
        },
    ]);
});
