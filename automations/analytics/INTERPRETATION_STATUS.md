# Interpretation graph — status

**Ready to activate when an approved model runtime is available.**

_Last reviewed: 2026-08-17. Branch: `claude/molosoc-interpretation-graph`._

The interpretation layer is complete, tested and deliberately dormant. It is
not merged, not wired to any model provider, and not scheduled. Nothing in the
production analytics, reporting or dashboard system depends on it.

## Why it is parked

The wiring was built against the Anthropic API and then held, because a
separately billed AI vendor was not wanted. The intended substitute —
GitHub Models, authenticated by the Actions token with no new secret — was
investigated and found to be gone: it stopped accepting new customers on
2026-06-16 and was fully retired on 2026-07-30, taking the catalog, the
inference API and BYOK with it. This account was created 2026-07-15 and was
never eligible for it.

The surviving GitHub-native path (Copilot SDK) is metered under usage-based
AI Credits and offers no schema-enforced structured output, so it would both
reintroduce metered billing and remove the first line of defence behind the
anti-fabrication contracts. Nothing else on offer avoided a second vendor.

So the layer waits. This is a decision to hold, not an unfinished build.

## What exists

| File | Role |
| --- | --- |
| `interpretation_contracts.py` | The four anti-fabrication invariants, and the JSON schemas that mirror them |
| `interpretation_graph.py` | Orchestration: slices, budgets, selective verification, run manifest |
| `interpretation_prompts.py` | The four bounded specialist prompts, the verifier, the synthesis |
| `interpretation_caller.py` | The live model caller — **the only vendor-specific file** |
| `marketing_intelligence.py` | The Analytics → Marketing Strategy handoff document |
| `intelligence_store.py` | Where that document is persisted, derived from the report's own key |
| `run_interpretation.py` | CLI entry point |
| `client_config.py` | Client slug parameterization (MOLOSOC is the configured client) |
| `test_interpretation.py`, `test_interpretation_wiring.py` | 63 offline tests, all passing |

Caps, unchanged and not to be relaxed on activation: 4 specialist calls,
6 verifier calls, 1 synthesis call, 1 retry per node against a separate
allowance. The readiness gate, completeness guards and human-approval
boundary are carried across the handoff intact.

## Deliberately absent

- `ANTHROPIC_API_KEY` is **not** set, in this repository or anywhere else.
- `INTERPRETATION_ENABLED` is **not** set; the code defaults to on, so the
  kill switch must be set to `false` if the workflow ever reaches `main`
  before a runtime is approved.
- No second AI provider has been introduced.
- No live model call has ever been made from this branch, to any vendor.

## Independence from production — verified 2026-08-17

- `main` contains **no** interpretation artifact of any kind.
- The branch is a pure addition: 13 files, 3310 insertions, 0 deletions. Only
  two files that already exist on `main` are touched — the weekly workflow
  and `requirements.txt`.
- No module outside the interpretation layer imports any part of it. The
  dependency runs one way only.
- A clean checkout of `main` runs the full offline suite unchanged:
  552 passed, 10 failed — the same ten sandbox-only failures caused by a
  missing `_cffi_backend`, which pass in CI where dependencies install.
- The weekly production run (`cron: 15 6 * * 3`) generates the report,
  persists it to GCS, uploads the 90-day artifact and publishes the dashboard
  without reference to anything here.

## To activate

1. Choose and approve a model runtime.
2. Replace `interpretation_caller.py`. Nothing else needs to move: the graph,
   contracts, prompts, handoff and store are all vendor-agnostic. Expect the
   env-var names in `run_interpretation.py`, the dependency line in
   `requirements.txt`, and the auth block of the workflow step to follow.
3. Re-run the offline suite before any live call.
4. Set `INTERPRETATION_ENABLED=false`, merge, and dispatch once to confirm the
   step is correctly skipped. Only then flip it to `true`.

The graph runs last in the workflow under `continue-on-error: true`, after the
report is already persisted, uploaded and published. It cannot reach back and
affect any of that — and until step 4 it does not run at all.
