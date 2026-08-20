<?php
/**
 * Plugin Name: Brevo Checkout Capture Shim (temporary)
 * Description: Restores checkout email capture (identify + cart_updated) lost to a Brevo for WooCommerce 4.0.54–4.0.58 regression. Remove once Brevo fixes the upstream plugin.
 * Version: 1.0.0
 *
 * TEMPORARY REGRESSION SHIM — REMOVE once Brevo ships an upstream fix.
 *
 * Brevo for WooCommerce 4.0.54 inverted the checkout gate in
 * brevo_hook_javascript_footer() (src/managers/admin-manager.php) from
 * `if (!$is_checkout) return;` to `if ($is_checkout) return;` and added the
 * same early-return to install_ma_and_chat_script(). Checkout is the only
 * page where a guest types an email, so from 4.0.54 on guests are never
 * identified and cart_updated is never sent — abandoned-cart tracking is
 * silently dead on classic-checkout stores (Brevo ticket filed 2026-08-20).
 *
 * This shim re-emits ONLY the missing email-capture snippet on the classic
 * checkout page. It POSTs to the Brevo plugin's own still-registered
 * `the_ajax_hook` AJAX action, which performs the identify + cart_updated
 * sends server-side — no Brevo API calls or keys live here.
 *
 * Self-limits:
 *   - runs only on checkout, excluding the order-received endpoint;
 *   - runs only while the installed Brevo plugin version is 4.0.54–4.0.58
 *     (when Brevo updates, re-test checkout capture: extend the ceiling if
 *     still broken, delete this file via the deploy-mu-plugins workflow's
 *     `remove` action once fixed);
 *   - duplicate-safe: skips when the tracking_email cookie already holds
 *     the same address (the plugin's own rule), so even if a fixed plugin
 *     re-adds its script, whichever listener fires first wins and the
 *     other no-ops.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_action( 'wp_footer', 'molosoc_brevo_checkout_capture_shim', 20 );

function molosoc_brevo_checkout_capture_shim() {
	if ( ! defined( 'SENDINBLUE_WC_PLUGIN_VERSION' ) ) {
		return; // Brevo for WooCommerce not active.
	}
	if (
		version_compare( SENDINBLUE_WC_PLUGIN_VERSION, '4.0.54', '<' ) ||
		version_compare( SENDINBLUE_WC_PLUGIN_VERSION, '4.0.58', '>' )
	) {
		return; // Outside the verified-broken range.
	}
	if ( ! function_exists( 'is_checkout' ) || ! is_checkout() ) {
		return;
	}
	if ( function_exists( 'is_wc_endpoint_url' ) && is_wc_endpoint_url( 'order-received' ) ) {
		return;
	}
	?>
	<script type="text/javascript" id="molosoc-brevo-checkout-capture-shim">
	(function () {
		var AJAX_URL = <?php echo wp_json_encode( admin_url( 'admin-ajax.php' ) ); ?>;
		// Same validation pattern the Brevo plugin uses in its own capture script.
		var EMAIL_RE = /^[#&*\/=?^{!}~'_a-z0-9-\+]+([#&*\/=?^{!}~'_a-z0-9-\+]+)*(\.[#&*\/=?^{!}~'_a-z0-9-\+]+)*[.]?@[_a-z0-9-]+(\.[_a-z0-9-]+)*(\.[a-z0-9]{2,63})$/i;
		function cookieValue(name) {
			var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
			return match ? match[2] : '';
		}
		document.body.addEventListener('blur', function (event) {
			var el = event.target;
			if (!el || el.id !== 'billing_email') {
				return;
			}
			var email = (el.value || '').trim();
			if (!EMAIL_RE.test(email)) {
				return;
			}
			var encoded = encodeURIComponent(email);
			if (cookieValue('tracking_email') === encoded) {
				return; // Already captured — prevents duplicate events.
			}
			document.cookie = 'tracking_email=' + encoded + '; path=/';
			var xhr = new XMLHttpRequest();
			xhr.open('POST', AJAX_URL, true);
			xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
			xhr.send('action=the_ajax_hook&tracking_email=' + encoded + '&subscription_location=order-checkout');
		}, true);
	})();
	</script>
	<?php
}
