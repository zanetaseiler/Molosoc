/*
  Issue #373 — Christmas CZ page on a phone, logged out (Playwright, node:test).

  Run (needs Google Chrome on the machine; no browser download). ES modules
  resolve packages from the file's own directory, so run it from a folder that
  has playwright-core installed, e.g. a scratch dir:
    mkdir -p /tmp/e2e && cd /tmp/e2e && npm i playwright-core@1.49
    cp <repo>/tests/e2e/xmas-first-screen-373.spec.mjs . && node --test xmas-first-screen-373.spec.mjs

  Env:
    MOLOSOC_BASE_URL   default https://molosoc.com (any origin that serves the page)
    MOLOSOC_XMAS_PATH  default /cz/vanocni-darek-molosoc/
    MOLOSOC_E2E_CART=1 also runs the live cart flow (3 pairs + size M -> checkout
                       subtotal 607 Kč, #place_order visible, cart emptied after)
                       and the Meta pixel check (PageView asserted; AddToCart reported, see the test).

  Nothing is ordered: the flow stops on the checkout page and removes the three
  cart lines through the Store API with the same guest session.
*/
import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium, devices } from 'playwright-core';

const BASE = (process.env.MOLOSOC_BASE_URL || 'https://molosoc.com').replace(/\/$/, '');
const PATH = process.env.MOLOSOC_XMAS_PATH || '/cz/vanocni-darek-molosoc/';
const VIEWPORT = { width: 390, height: 844 };

async function phone() {
	const browser = await chromium.launch({ channel: 'chrome', headless: true });
	const context = await browser.newContext({ ...devices['iPhone 12'], viewport: VIEWPORT, locale: 'cs-CZ' });
	return { browser, context, page: await context.newPage() };
}

/** Click a WPConsent banner button inside the plugin's shadow root ('accept' | 'cancel'). */
async function consent( page, which ) {
	await page.waitForFunction( () => {
		const c = document.getElementById( 'wpconsent-container' );
		return !! ( c && c.shadowRoot && c.shadowRoot.querySelector( '[part~="wpconsent-button-accept"]' ) );
	}, null, { timeout: 20000 } );
	await page.evaluate( ( which ) => {
		document.getElementById( 'wpconsent-container' ).shadowRoot.querySelector( `[part~="wpconsent-button-${ which }"]` ).click();
	}, which );
	await page.waitForTimeout( 500 );
}

test( 'Issue #375: hero photo shows its full 3:2 frame, sharp at 2x, "Do košíku" ends inside the first screen', async () => {
	const { browser, page } = await phone();
	try {
		await page.goto( BASE + PATH, { waitUntil: 'networkidle' } );
		const m = await page.evaluate( async () => {
			const img = document.querySelector( '.lpx-hero__media img' );
			const r = img.getBoundingClientRect();
			const cta = document.querySelector( '#lpx-bundle [data-lpx-go]' ).getBoundingClientRect();
			// img.naturalWidth is density-corrected for a w-descriptor srcset (CSS px, ~350 here),
			// so measure the chosen file's raw pixels: load currentSrc into a plain Image
			// (no srcset, density 1), and read currentSrc's own w descriptor as a cross-check.
			const raw = new Image();
			raw.src = img.currentSrc;
			await raw.decode();
			const abs = ( u ) => new URL( u, document.baseURI ).href;
			// With the AVIF <source> (#375 follow-up) currentSrc comes from the <source> srcset.
			const sets = [ ...document.querySelectorAll( '.lpx-hero__media source' ), img ].map( ( el ) => el.getAttribute( 'srcset' ) || '' ).join( ',' );
			const cand = sets.split( ',' ).map( ( c ) => c.trim().split( /\s+/ ) ).find( ( [ u ] ) => u && abs( u ) === img.currentSrc );
			const descW = cand && /^\d+w$/.test( cand[ 1 ] || '' ) ? parseInt( cand[ 1 ], 10 ) : null;
			return { avif: /\.avif(\?|$)/.test( img.currentSrc ), shown: r.width / r.height, natural: raw.naturalWidth / raw.naturalHeight, fit: getComputedStyle( img ).objectFit, cssW: r.width, fileW: raw.naturalWidth, descW, src: img.currentSrc, dpr: window.devicePixelRatio, ctaBottom: cta.bottom + window.scrollY, loading: img.loading, prio: img.getAttribute( 'fetchpriority' ) };
		} );
		assert.ok( Math.abs( m.shown - m.natural ) < 0.02, `hero cropped: shown ${ m.shown } vs file ${ m.natural }` );
		assert.notEqual( m.fit, 'cover' );
		assert.ok( m.fileW >= m.cssW * Math.min( m.dpr, 2 ), `hero file ${ m.fileW }px (${ m.src }) for a ${ m.cssW }px slot at ${ m.dpr }x` );
		if ( m.descW !== null ) {
			assert.equal( m.fileW, m.descW, `${ m.src }: raw width vs its srcset w descriptor` );
		}
		assert.ok( m.ctaBottom <= VIEWPORT.height, `"Do košíku" ends at ${ m.ctaBottom }px, viewport ${ VIEWPORT.height }px` );
		assert.equal( m.loading, 'eager' );
		assert.equal( m.prio, 'high' );
		assert.ok( m.avif, `Chrome should pick the AVIF source, got ${ m.src }` );
	} finally {
		await browser.close();
	}
} );

test( 'set selector + "Do košíku" are in the DOM above 1.2x the viewport height', async () => {
	const { browser, page } = await phone();
	try {
		await page.goto( BASE + PATH, { waitUntil: 'networkidle' } );
		const tops = await page.evaluate( () => {
			const top = ( sel ) => { const el = document.querySelector( sel ); return el ? Math.round( el.getBoundingClientRect().top + window.scrollY ) : null; };
			return {
				h1: top( 'h1' ),
				cards: top( '#lpx-bundle .lpx-bundles' ),
				sizes: top( '#lpx-bundle [data-lpx-pair="1"]' ),
				cta: top( '#lpx-bundle [data-lpx-go]' ),
				ctaText: ( document.querySelector( '#lpx-bundle [data-lpx-go]' ) || {} ).textContent?.trim(),
				deadline: ( document.querySelector( '.lpx-deadline' ) || {} ).textContent?.trim(),
				pill: ( document.getElementById( 'molosoc-sticky-cta' ) || {} ).textContent?.trim(),
				prices: [ ...document.querySelectorAll( '#lpx-bundle .lpx-bundle__price' ) ].map( ( e ) => e.textContent.trim() ),
			};
		} );
		const limit = VIEWPORT.height * 1.2;
		assert.equal( tops.ctaText, 'Do košíku' );
		assert.deepEqual( tops.prices.slice( 0, 3 ), [ '209 Kč', '408 Kč', '607 Kč' ] );
		assert.equal( tops.deadline, 'Objednejte do 18. prosince, doručíme před Vánoci.' );
		assert.equal( tops.pill, 'Vybrat dárkový set' );
		for ( const k of [ 'h1', 'cards', 'sizes', 'cta' ] ) {
			assert.ok( tops[ k ] !== null && tops[ k ] <= limit, `${ k } at ${ tops[ k ] }px, limit ${ limit }px` );
		}
		assert.ok( tops.h1 < tops.cards && tops.cards < tops.sizes && tops.sizes < tops.cta, JSON.stringify( tops ) );
	} finally {
		await browser.close();
	}
} );

test( 'cookie banner: compact bottom card, both buttons on one line, headline + set choice above it', async () => {
	const { browser, page } = await phone();
	try {
		await page.goto( BASE + PATH, { waitUntil: 'networkidle' } );
		await page.waitForFunction( () => { const c = document.getElementById( 'wpconsent-container' ); return !! ( c && c.shadowRoot && c.shadowRoot.querySelector( '[part~="wpconsent-banner"]' ) ); }, null, { timeout: 20000 } );
		const m = await page.evaluate( () => {
			const root = document.getElementById( 'wpconsent-container' ).shadowRoot;
			const b = root.querySelector( '[part~="wpconsent-banner"]' ).getBoundingClientRect();
			const btn = ( p ) => root.querySelector( `[part~="wpconsent-button-${ p }"]` ).getBoundingClientRect();
			const a = btn( 'accept' ), c = btn( 'cancel' );
			const h1 = document.querySelector( 'h1' ).getBoundingClientRect();
			const labels = document.querySelectorAll( '#lpx-bundle .lpx-bundle' );
			const cards = labels[ labels.length - 1 ].getBoundingClientRect(); // the last bundle card (the #364 teaser under it may sit behind the banner)
			return { bannerTop: b.top, bannerH: b.height, vh: window.innerHeight, acceptTop: a.top, cancelTop: c.top, h1Bottom: h1.bottom, cardsBottom: cards.bottom };
		} );
		assert.ok( m.bannerH <= m.vh * 0.25, `banner ${ m.bannerH }px of ${ m.vh }px` );
		assert.ok( Math.abs( m.acceptTop - m.cancelTop ) < 2, 'Přijmout vše and Odmítnout on one line' );
		assert.ok( m.h1Bottom < m.bannerTop, 'headline above the banner' );
		assert.ok( m.cardsBottom < m.bannerTop, 'set choice above the banner' );
	} finally {
		await browser.close();
	}
} );

test( '3 pairs + size M -> checkout subtotal 607 Kč, #place_order visible, pixel PageView (AddToCart reported); cart emptied', { skip: process.env.MOLOSOC_E2E_CART !== '1' && 'set MOLOSOC_E2E_CART=1 to run against the live cart' }, async () => {
	const { browser, context, page } = await phone();
	const pixel = [];
	// fbevents.js sends the event as a GET query or as a POST body to facebook.com/tr/: keep both.
	page.on( 'request', ( r ) => { const u = r.url(); if ( /facebook\.com\/tr\b/.test( u ) ) { pixel.push( u + ' ' + ( r.postData() || '' ) ); } } );
	try {
		await page.goto( BASE + PATH, { waitUntil: 'networkidle' } );
		await consent( page, 'accept' );
		await page.waitForTimeout( 2500 );
		assert.ok( pixel.some( ( u ) => /ev=PageView/.test( u ) ), 'Meta PageView after consent: ' + pixel.join( '\n' ) );

		const picker = page.locator( '#lpx-bundle [data-lpx-buy]' );
		await picker.locator( 'input[name^="lpx-pairs-"][value="3"]' ).check( { force: true } );
		await picker.locator( '[data-lpx-pair="1"] input[value="M"]' ).check( { force: true } );
		// Pairs 2 and 3 inherit pair 1's size (Issue #287); the button sends M,M,M.
		const sizes = await picker.evaluate( ( g ) => [ 1, 2, 3 ].map( ( n ) => ( g.querySelector( `[data-lpx-pair="${ n }"] input:checked` ) || {} ).value ) );
		assert.deepEqual( sizes, [ 'M', 'M', 'M' ] );
		await Promise.all( [ page.waitForURL( /\/cz\/pokladna\//, { timeout: 60000 } ), picker.locator( '[data-lpx-go]' ).click() ] );
		await page.waitForLoadState( 'networkidle' );

		const subtotal = ( await page.locator( '.cart-subtotal .woocommerce-Price-amount' ).first().textContent() ).replace( /\s/g, '' );
		assert.ok( subtotal.startsWith( '607' ), 'checkout subtotal: ' + subtotal );
		const lines = await page.locator( '.woocommerce-checkout-review-order-table .cart_item' ).count();
		assert.equal( lines, 3, 'one cart line per pair' );
		await page.locator( '#place_order' ).waitFor( { state: 'visible', timeout: 15000 } );
		await page.waitForTimeout( 2500 );
		// Observed live on 2026-11-16 (before and after this change): the browser
		// sends PageView on the landing page and PageView on the checkout, but no
		// AddToCart — the bundle is added server-side in wp_loaded and the request
		// redirects, so Facebook for WooCommerce's browser event for the add is
		// never printed (its server-side CAPI event cannot be seen from here).
		// Reported, not asserted, until that is decided in its own Issue.
		const addToCart = pixel.some( ( u ) => /ev=AddToCart/.test( u ) );
		console.log( `Meta pixel requests: ${ pixel.length }; PageView: yes; AddToCart: ${ addToCart ? 'yes' : 'NO (pre-existing, see comment)' }` );
	} finally {
		// Empty the guest cart through the Store API (same cookies), then verify.
		try {
			const cart = await context.request.get( BASE + '/wp-json/wc/store/v1/cart' );
			const nonce = cart.headers()[ 'nonce' ];
			for ( const item of ( await cart.json() ).items || [] ) {
				await context.request.delete( BASE + '/wp-json/wc/store/v1/cart/items/' + item.key, { headers: { Nonce: nonce } } );
			}
			const after = await ( await context.request.get( BASE + '/wp-json/wc/store/v1/cart' ) ).json();
			assert.equal( after.items_count, 0, 'cart emptied afterwards' );
		} finally {
			await browser.close();
		}
	}
} );
