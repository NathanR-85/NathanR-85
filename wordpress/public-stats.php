<?php
/**
 * Plugin Name: Public Stats
 * Description: Nathan's shared public numbers from stats.json in github.com/NathanR-85/NathanR-85.
 *
 * The same file runs on widebluesound.com and nathanrightnour.com (canonical copy:
 * NathanR-85/wordpress/public-stats.php). Pages read the stored copy, so they never wait on
 * GitHub. An hourly cron fetches stats.json; a failed or invalid fetch keeps the last good
 * numbers. When a number changes, the pages that show stats are cleared from the page caches.
 *
 * In PHP: public_stat('plays'). In content: [public_stat key="plays"].
 */

if (!defined('ABSPATH')) {
    exit;
}

const PUBLIC_STATS_URL = 'https://raw.githubusercontent.com/NathanR-85/NathanR-85/main/stats.json';
const PUBLIC_STATS_KEYS = array('plays', 'productions', 'founded', 'studios', 'countries', 'collaborators');

/** Fetch stats.json and store it. Returns true when a valid copy was stored. */
function public_stats_refresh()
{
    $response = wp_remote_get(PUBLIC_STATS_URL . '?t=' . time(), array('timeout' => 10));
    if (is_wp_error($response) || wp_remote_retrieve_response_code($response) !== 200) {
        error_log('Public Stats: could not fetch stats.json');
        return false;
    }
    $data = json_decode(wp_remote_retrieve_body($response), true);
    $stats = array();
    foreach (PUBLIC_STATS_KEYS as $key) {
        if (!is_array($data) || !is_string($data[$key] ?? null) || trim($data[$key]) === '') {
            error_log("Public Stats: stats.json is missing $key; keeping the last good numbers");
            return false;
        }
        $stats[$key] = trim($data[$key]);
    }
    $old = get_option('public_stats');
    if ($old !== $stats) {
        update_option('public_stats', $stats, true);
        if (is_array($old)) {
            public_stats_clear_pages();
        }
    }
    return true;
}

/** One stored number, such as public_stat('plays') => "1,810,000,000+". */
function public_stat($key)
{
    $stats = get_option('public_stats');
    if (!is_array($stats)) {
        public_stats_refresh();
        $stats = (array) get_option('public_stats');
    }
    public_stats_note_page();
    return (string) ($stats[$key] ?? '');
}

/** Remember which pages show stats, so only those are cleared when a number changes. */
function public_stats_note_page()
{
    $id = (int) get_queried_object_id();
    if (!$id) {
        return;
    }
    $pages = (array) get_option('public_stats_pages', array());
    if (!in_array($id, $pages, true)) {
        $pages[] = $id;
        update_option('public_stats_pages', $pages, false);
    }
}

function public_stats_clear_pages()
{
    foreach ((array) get_option('public_stats_pages', array()) as $id) {
        delete_post_meta($id, '_elementor_element_cache');
        if (function_exists('rocket_clean_post')) {
            rocket_clean_post($id); // WP Rocket; its Cloudflare add-on purges the same URL.
        }
        do_action('cache_enabler_clear_page_cache_by_post', $id); // Cache Enabler 1.8+.
        do_action('cache_enabler_clear_page_cache_by_post_id', $id); // Older Cache Enabler (Nexcess bundles 1.7).
    }
}

add_shortcode('public_stat', function ($atts) {
    return esc_html(public_stat(shortcode_atts(array('key' => ''), $atts)['key']));
});

add_action('public_stats_refresh', 'public_stats_refresh');
add_action('init', function () {
    if (!wp_next_scheduled('public_stats_refresh')) {
        wp_schedule_event(time(), 'hourly', 'public_stats_refresh');
    }
});
