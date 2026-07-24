# GA4 / Meta Pixel — Event Naming Spec

One source of truth for event names. GTM fires these; GA4 and Meta Pixel both listen to the
same dataLayer pushes; Klaviyo flows (Phase 4) trigger off the same names. Don't invent a
second naming scheme anywhere downstream.

WooCommerce pushes most of these to the dataLayer automatically once the GA4/Woo integration
plugin (or a small mu-plugin) is active — this doc is the checklist to confirm each one fires.

| Event name (GA4) | Fires when | Meta Pixel equivalent | Klaviyo flow trigger |
|---|---|---|---|
| `view_item` | Product page viewed | `ViewContent` | — |
| `add_to_cart` | Item added to cart | `AddToCart` | Browse/cart abandonment |
| `begin_checkout` | Checkout page reached | `InitiateCheckout` | Checkout abandonment |
| `purchase` | Order completed | `Purchase` | Post-purchase flow, welcome-to-list suppression |
| `sign_up` | Newsletter/account signup | `CompleteRegistration` | Welcome flow |

## Verification checklist (Phase 2 exit condition)
- [ ] Open GTM Preview mode, walk through: product page → add to cart → checkout → dummy purchase
- [ ] Confirm each event above appears in the GTM debug console with correct name
- [ ] Confirm GA4 DebugView shows the same events in real time
- [ ] Confirm Meta Events Manager "Test Events" tab shows the same events
- [ ] Confirm Microsoft Clarity is recording sessions (separate — page-view only, no event mapping needed)
