# Creating the next Journal article (CZ/EN) — Issue #280

The approved article design (Issues #273 / PR #275) lives in one place:
`site/theme/assets/css/pillar1.css` (hero → upper sections → §4b article-body
system: 800px measure, responsive type/spacing, FAQ rows, related reading,
back-to-pillar band, §6 final CTA). It is **not duplicated** per article.

## What is automatic

`molosoc_enqueue_assets()` (`site/theme/functions.php`) loads `pillar1.css` for
the existing pillars/spokes (EN + CZ, matched by slug) **and**, via
`molosoc_has_journal_article_template()`, for any page whose assigned template
file is named `page-journal-*.php`. The enqueue branch is non-global: no other page type is
affected, and no JS is enqueued.

## Steps for a new article (EN or CZ)

1. Copy an existing template with the same shape (a spoke such as
   `page-prevent.php`, or a pillar) to `site/theme/page-journal-<slug>.php`.
   Update `Template Name:` and replace the article-specific hero photo, copy
   and links. Keep the class names/markup of the lower sections (prose blocks,
   FAQ pairs, `molosoc_related_links()`, `.molosoc-pillar-back` band, final
   CTA) so they pick up the shared §4b/§6 styling.
2. In WP admin assign that template to the new Page (Page Attributes →
   Template). Because the file name starts with `page-journal-`, the shared
   stylesheet loads automatically — no edit to `functions.php` or CSS.
3. Keep one `<h1>`, ordered H2/H3, and add the article's SEO title/meta and
   JSON-LD (see the `molosoc_pillar*_schema()` / CZ meta functions in
   `functions.php`; these remain per-article by design).
4. Add the article to the relevant "related reading"/pillar "Go deeper" links.
5. Bump the `Version:` in `site/theme/style.css` if CSS changed (not needed
   for a new template alone).

## Limitations

- Per-article schema and CZ title/meta are still registered per slug; the
  template convention only covers styling/assets.
- Existing templates keep their slug-based matching; nothing was renamed.
