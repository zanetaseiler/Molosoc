/*
  Issue #378 — Black Friday CZ/EN landing pages on a phone, logged out
  (Playwright, node:test). Same setup as xmas-first-screen-373.spec.mjs:
    mkdir -p /tmp/e2e && cd /tmp/e2e && npm i playwright-core@1.49
    cp <repo>/tests/e2e/black-friday-378.spec.mjs . && node --test black-friday-378.spec.mjs

  Runs only against an origin that serves the pages, i.e. after deploy + the
  drafts being published (Žaneta's approval). Env:
    MOLOSOC_BASE_URL   default https://molosoc.com
    MOLOSOC_BF_CZ_PATH default /cz/black-friday-molosoc/
    MOLOSOC_BF_EN_PATH default /black-friday-offer-molosoc/
    MOLOSOC_E2E_CART=1 also runs the live cart flow on the CZ page (3 pairs +
                       size M -> checkout subtotal 607 Kč, 3 lines, #place_order
                       visible; cart emptied afterwards through the Store API)
                       and reports the Meta pixel events (PageView asserted,
                       AddToCart reported — see the #374 finding below).
    MOLOSOC_SHOT_DIR   where to save the 390x844 first-screen screenshots.
  Nothing is ordered.
*/
import test from 'node:test';
import assert from 'node:assert/strict';
import { chromium, devices } from 'playwright-core';

const BASE = ( process.env.MOLOSOC_BASE_URL || 'https://molosoc.com' ).replace( /\/$/, '' );
const PAGES = {
	cz: { path: process.env.MOLOSOC_BF_CZ_PATH || '/cz/black-friday-molosoc/', cta: 'Do košíku', prices: [ '209 Kč', '408 Kč', '607 Kč' ], pill: 'Vybrat set', locale: 'cs-CZ', checkout: /\/cz\/pokladna\// },
	en: { path: process.env.MOLOSOC_BF_EN_PATH || '/black-friday-offer-molosoc/', cta: 'Add to cart', prices: [ '209 CZK', '408 CZK', '607 CZK' ], pill: 'Choose your set', locale: 'en-GB', checkout: /\/checkout\// },
};
const VIEWPORT = { width: 390, height: 844 };

async function phone( locale ) {
	const browser = await chromium.launch( { channel: 'chrome', headless: true } );
	const context = await browser.newContext( { ...devices[ 'iPhone 12' ], viewport: VIEWPORT, locale } );
	return { browser, context, page: await context.newPage() };
}

for ( const [ lang, p ] of Object.entries( PAGES ) ) {
	test( `${ lang }: product photo whole, set choice + CTA in the first screen, no Christmas copy`, async () => {
		const { browser, page } = await phone( p.locale );
		try {
			await page.goto( BASE + p.path, { waitUntil: 'networkidle' } );
			if ( process.env.MOLOSOC_SHOT_DIR ) {
				await page.screenshot( { path: `${ process.env.MOLOSOC_SHOT_DIR }/bf-${ lang }-390x844.png` } );
			}
			const m = await page.evaluate( () => {
				const img = document.querySelector( '.lpx-hero__media img' );
				const r = img.getBoundingClientRect();
				const top = ( sel ) => { const el = document.querySelector( sel ); return el ? Math.round( el.getBoundingClientRect().top + window.scrollY ) : null; };
				const cta = document.querySelector( '#lpx-bundle [data-lpx-go]' );
				return {
					bf: document.querySelector( 'main.lpx--bf' ) !== null,
					fit: getComputedStyle( img ).objectFit,
					src: img.currentSrc,
					imgW: Math.round( r.width ),
					scrollW: document.documentElement.scrollWidth,
					ratio: r.width / r.height,
					file: img.naturalWidth / img.naturalHeight,
					cards: top( '#lpx-bundle .lpx-bundles' ),
					ctaBottom: Math.round( cta.getBoundingClientRect().bottom + window.scrollY ),
					ctaText: cta.textContent.trim(),
					deadline: document.querySelector( '.lpx-deadline' ) !== null,
					bar: document.getElementById( 'molosoc-xmas-bar' ) !== null,
					pill: ( document.getElementById( 'molosoc-sticky-cta' ) || {} ).textContent?.trim(),
					prices: [ ...document.querySelectorAll( '#lpx-bundle .lpx-bundle__price' ) ].map( ( e ) => e.textContent.trim() ),
					text: document.querySelector( 'main' ).innerText,
					og: ( document.querySelector( 'meta[property="og:url"]' ) || {} ).content,
					canonical: ( document.querySelector( 'link[rel="canonical"]' ) || {} ).href,
				};
			} );
			assert.ok( m.bf );
			assert.equal( m.fit, 'contain' );
			assert.ok( Math.abs( m.ratio - m.file ) < 0.02, 'hero photo not cropped' );
			assert.match( m.src, /black-friday\/molosoc-black-friday-ad-\d+\.webp$/, 'Issue #380: the Black Friday ad is the hero' );
			assert.ok( m.imgW >= 240, `hero ad ${ m.imgW } px wide` );
			assert.ok( m.scrollW <= VIEWPORT.width, `horizontal scroll ${ m.scrollW }` );
			assert.equal( m.ctaText, p.cta );
			assert.deepEqual( m.prices.slice( 0, 3 ), p.prices );
			assert.ok( m.cards < VIEWPORT.height && m.ctaBottom <= VIEWPORT.height, JSON.stringify( m ) );
			assert.equal( m.deadline, false );
			assert.equal( m.bar, false, 'Christmas announcement bar is off here' );
			assert.equal( m.pill, p.pill );
			assert.doesNotMatch( m.text, /Vánoc|vánoč|Christmas|prosince|December|dárek|gift/i );
			assert.ok( m.og && m.canonical && m.og === m.canonical, `og:url ${ m.og } vs canonical ${ m.canonical }` );
		} finally {
			await browser.close();
		}
	} );
}

test( 'cz: 3 pairs + size M -> checkout subtotal 607 Kč, #place_order visible, PageView (AddToCart reported); cart emptied', { skip: process.env.MOLOSOC_E2E_CART !== '1' && 'set MOLOSOC_E2E_CART=1 to run against the live cart' }, async () => {
	const p = PAGES.cz;
	const { browser, context, page } = await phone( p.locale );
	const pixel = [];
	page.on( 'request', ( r ) => { const u = r.url(); if ( /facebook\.com\/tr\b/.test( u ) ) { pixel.push( u + ' ' + ( r.postData() || '' ) ); } } );
	try {
		await page.goto( BASE + p.path, { waitUntil: 'networkidle' } );
		await page.waitForFunction( () => { const c = document.getElementById( 'wpconsent-container' ); return !! ( c && c.shadowRoot && c.shadowRoot.querySelector( '[part~="wpconsent-button-accept"]' ) ); }, null, { timeout: 20000 } );
		await page.evaluate( () => document.getElementById( 'wpconsent-container' ).shadowRoot.querySelector( '[part~="wpconsent-button-accept"]' ).click() );
		await page.waitForTimeout( 3000 );
		assert.ok( pixel.some( ( u ) => /ev=PageView/.test( u ) ), 'Meta PageView after consent: ' + pixel.join( '\n' ) );
		const viewContent = pixel.some( ( u ) => /ev=ViewContent/.test( u ) );

		const picker = page.locator( '#lpx-bundle [data-lpx-buy]' );
		await picker.locator( 'input[name^="lpx-pairs-"][value="3"]' ).check( { force: true } );
		await picker.locator( '[data-lpx-pair="1"] input[value="M"]' ).check( { force: true } );
		await Promise.all( [ page.waitForURL( p.checkout, { timeout: 60000 } ), picker.locator( '[data-lpx-go]' ).click() ] );
		await page.waitForLoadState( 'networkidle' );
		const subtotal = ( await page.locator( '.cart-subtotal .woocommerce-Price-amount' ).first().textContent() ).replace( /\s/g, '' );
		assert.ok( subtotal.startsWith( '607' ), 'checkout subtotal: ' + subtotal );
		assert.equal( await page.locator( '.woocommerce-checkout-review-order-table .cart_item' ).count(), 3 );
		await page.locator( '#place_order' ).waitFor( { state: 'visible', timeout: 15000 } );
		await page.waitForTimeout( 2500 );
		// #374 finding: the bundle is added server-side in wp_loaded and the
		// request redirects, so no browser AddToCart is expected; reported only.
		const addToCart = pixel.some( ( u ) => /ev=AddToCart/.test( u ) );
		console.log( `Meta pixel requests: ${ pixel.length }; PageView: yes; ViewContent: ${ viewContent ? 'yes' : 'no' }; AddToCart (browser): ${ addToCart ? 'yes' : 'NO (pre-existing, #374)' }` );
	} finally {
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
