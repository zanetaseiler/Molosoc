# Storage layout, schema and exit codes

Companion to `SKILL.md` §4 and §8. Every path is relative to
`gs://{{GCS_BUCKET}}/`.

## Key layout

```
raw/{source}/{YYYY-MM-DD}/…          immutable evidence, exactly as the API returned it
facts/{source}/{YYYY-MM-DD}.json     normalized records — derived, safe to recompute
facts/{source}/{YYYY-MM-DD}.quality.json
state/{name}/{YYYY-MM-DD}.json       collector budget ledger, recommendation ledger

reports/weekly/
├── data/                            ◄── EVERY dated report lives under this prefix
│   └── {YYYY}/{MM}/{YYYY-MM-DD}/
│       ├── report.json              written once, never overwritten
│       ├── report.md
│       └── revisions/{stamp}/…      only if the revision policy was used
├── latest.json                      ◄── mutable pointer
└── index.json                       ◄── mutable pointer
```

`{source}` is `ga4`, `gsc` or `clarity`.

### Why `data/` exists as a separate prefix

A GCS lifecycle rule can match a prefix but **cannot express an exclusion**.
Without this split there is no way to expire dated reports while keeping
`latest.json` and `index.json` alive. The prefix is the mechanism that makes
retention safe — do not flatten it.

## The two mutable objects

`latest.json` and `index.json` are the **only** objects ever overwritten.
Everything else is create-once.

- `latest.json` — the pointer to the most recent report: its date, its keys,
  headline metrics, schema version. The entry point for any consumer.
- `index.json` — one small entry per stored week: date, keys, headline
  metrics. **Not** copies of reports. Bounded at `{{index_max_entries}}`
  (260 ≈ five years). Measure the *marginal* bytes per entry when testing
  growth, never the total.

Both are rebuildable from the `data/` tree. If the pointer write fails, no
data is lost — run the rebuild command.

## Report document schema

```jsonc
{
  "schema_version": "1.0.0",
  "report_kind": "{{CLIENT_SLUG}}.weekly_marketing_analysis",
  "generated_at": "2026-08-16T06:15:00+00:00",
  "as_of_date": "2026-08-13",
  "period":             { "start": "…", "end": "…" },
  "comparison_periods": [ { "start": "…", "end": "…" } ],
  "readiness": "ready | insufficient_data | suppressed",
  "facts":       [ /* measured, causal_claim always false */ ],
  "inferences":  [ /* typed correlation | pattern | hypothesis, with confidence */ ],
  "recommendations": [ /* empty when readiness withheld them */ ],
  "data_quality":  { "hydration": {…}, "conversions": {…}, "tracking_coverage": {…} },
  "data_coverage": { "clarity_ledger": { "days_available": 14 } },
  "views": { "headline": ["fact_id", …] }   // named views reference fact IDs, never copies
}
```

Rules:

- **Views reference fact IDs, never duplicate fact objects.** A copied fact
  becomes a second source of truth the moment one is edited.
- `schema_version` is checked by consumers; an unknown version must be
  refused, not guessed at.
- `report_kind` is namespaced by client slug so two clients cannot collide.
- Every suppressed comparison carries a machine-readable reason
  (`comparison_unavailable_reason`) so renderers can explain rather than
  print a dash.

## Duplicate policy

| Policy | Behaviour |
|---|---|
| `reject` (default) | an already-stored week is left untouched; caller gets exit 3 |
| `revision` | files the re-run under `revisions/{stamp}/` beside the original, never replacing it |

## Exit codes

| Code | Meaning | Workflow response |
|---|---|---|
| 0 | success | continue |
| 1 | generation or storage failure | fail the run |
| 2 | reports stored, pointer/index not updated | fail loudly; data is safe, rebuild pointers |
| 3 | this week already published, left untouched | **warning, continue publishing** |

Code 3 is the storage layer succeeding. Do not couple dashboard publishing to
the report being novel — a re-run should still refresh the page.

Code 2 is deliberately distinct from 1: conflating them reads as data loss
when it is a permission gap.

## Atomicity

- Create-if-absent uses `if_generation_match=0`, which makes both the
  collector and the report publisher idempotent under retry.
- Pointer rewrites are last. A crash mid-run leaves stored reports valid and
  pointers stale — recoverable. The reverse would not be.

## IAM condition

Grant `storage.objects.delete` only under:

```
resource.name == "projects/_/buckets/{{GCS_BUCKET}}/objects/reports/weekly/latest.json" ||
resource.name == "projects/_/buckets/{{GCS_BUCKET}}/objects/reports/weekly/index.json"
```

Generate this string from the bucket name in code rather than pasting it; a
typo silently widens the grant. Requires uniform bucket-level access.
