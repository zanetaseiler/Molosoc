# AGENTS.md — Claude ↔ Santiago development protocol

GitHub Issues, pull requests, commits, reviews, and comments are the authoritative record for this repository's agent handoffs.

## Operating model

Žaneta defines or approves the goal and material boundaries → Claude implements or corrects one bounded piece of work → Santiago/Codex reviews the exact PR head → Claude fixes only recorded findings → Santiago/Codex re-reviews → a clean exact-head result becomes `VERIFIED` → Žaneta decides whether to merge.

## Core transport states

- `READY_FOR_CLAUDE_CLOUD` — queue Claude Cloud.
- `READY_FOR_SANTIAGO` — Claude finished the current implementation/correction phase and hands off the exact PR head.
- `VERIFIED` — Santiago/Codex found no major issues on the exact current PR head. This is a stop state, not merge authorization.

## Claude correction behavior

When Claude is started for an existing PR because Codex found a review issue:

1. Read the PR, all current review comments, and the current exact head.
2. Make only the corrections required by those findings.
3. Push the correction to the same PR branch.
4. Post `READY_FOR_SANTIAGO` naming the new exact head commit SHA and summarizing the fix/tests.
5. Stop.

Do not open a replacement PR for the same correction round.

## Human gate

Never merge automatically. A clean `VERIFIED` result still waits for Žaneta's explicit merge approval.

Do not deploy, publish, spend, mutate production data, change OAuth/platform state, or create/replace credentials without explicit human approval.

## Exact-head rule

Every Claude delivery and Santiago/Codex verification must apply to the exact current PR head SHA. Stale handoffs or reviews must be ignored.

Read `docs/AGENT_WORKFLOW.md` for the required comment formats.