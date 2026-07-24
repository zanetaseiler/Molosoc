# Homepage — storytelling arc mapping

`docs/molosoc-design-direction.md` prescribes a 9-beat homepage story:
1. Emotional opening
2. The problem
3. Why current solutions fail
4. How Molosoc works
5. Benefits
6. Social proof
7. Product
8. Educational content
9. Final CTA

The locked copy in `content/molosoc-site/01-homepage/homepage-copy.md` wasn't
written against this arc — it was written against `docs/wp-build-spec.md`'s
outline. This doc maps one onto the other, built (not invented) — every quoted
line below is taken verbatim from existing content, either `homepage-copy.md`
or `docs/icp.md`'s message hierarchy.

| Beat | Section built | Source |
|---|---|---|
| 1 — Emotional opening | Hero: H1 + intro paragraph | `homepage-copy.md` H1 + body |
| 2 — The problem | "Why foot care never sticks" (4 items) | `homepage-copy.md` H2 |
| 3 — Why current solutions fail | **Not built as its own section** — see below | — |
| 4 — How Molosoc works | "The cream you own, finally finished" pillar grid | `docs/icp.md` §1 message hierarchy |
| 5 — Benefits | Same pillar grid (4 & 5 collapsed into one section) | `docs/icp.md` §1 |
| 6 — Social proof | Before/after photo + caption | `content/molosoc-site/00-STATUS.md` resolved-items list (photo URL) |
| 7 — Product | "Meet the Foot Cover" | `homepage-copy.md` H2 "How Molosoc helps right now" |
| 8 — Educational content | "Foot care, topic by topic" (5 links) | `homepage-copy.md` H2, reordered later in the page than it currently sits |
| 9 — Final CTA | "The reusable alternative" closing section | `homepage-copy.md` H2 |

## Two gaps flagged, not papered over

**Beat 3 (why current solutions fail) was deliberately not built as a homepage
section.** The disposable-vs-reusable argument is written for the **Category
page**, not the homepage — `docs/seo-geo-plan.md` §2 explicitly assigns that
argument to the category layer and warns against letting brand-layer
(homepage) content fight category-layer content. Duplicating it here would
blur that intentional separation. If you want a homepage-level version of this
beat, it needs new copy scoped to the brand layer specifically (a light "this
isn't like a disposable mask" gesture, not the full cost-per-use argument) —
that's a copy decision for you, not one I made unilaterally.

**Beat 6 (social proof) has no written testimonial copy anywhere in the
project** — only the resolved photo asset. The built section uses that real
photo with a short factual caption ("Time-stamped, unedited"), not an invented
quote or testimonial text. If you want an actual customer quote here later,
that's new content to write, not something already sitting in the docs.
