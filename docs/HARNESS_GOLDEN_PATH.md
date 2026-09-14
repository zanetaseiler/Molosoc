# Claude ↔ Santiago/Codex Harness — Golden Path

Zoe is the reference implementation for the reusable autonomous GitHub harness.

## Proven protocol

```text
READY_FOR_CLAUDE_CLOUD
  → Claude Cloud pickup
  → Claude works on the exact Issue/PR
  → READY_FOR_SANTIAGO with exact head SHA
  → SANTIAGO_CODEX_BRIDGE_TOKEN posts @codex review as zanetaseiler
  → Codex reviews the exact current PR head

If Codex has inline findings:
  → codex-feedback-to-claude validates actor + exact head + real findings
  → READY_FOR_CLAUDE_CLOUD is queued
  → Claude is fired directly in the same workflow
  → Claude corrects
  → READY_FOR_SANTIAGO with the new exact head SHA
  → @codex review as zanetaseiler
  → Codex re-reviews

If Codex is clean:
  → codex-clean-verified validates actor + clean wording + reviewed SHA
  → reviewed SHA must match the current PR head
  → VERIFIED label
  → canonical VERIFIED:<full SHA> comment
  → STOP at the human merge gate
```

## Required repository secret

`SANTIAGO_CODEX_BRIDGE_TOKEN`

The shared fine-grained PAT is owned by `zanetaseiler`. It is used only to make the Codex wake-up comment appear as Zaneta's GitHub identity; a `github-actions[bot]` authored `@codex review` cannot invoke Zaneta's connected Codex identity.

The token currently needs repository permissions sufficient for the PR comment operation, including:

- Issues: Read and write
- Pull requests: Read and write

Never place the token value in repository files, comments, logs, or chat.

## Existing Claude configuration

Each harness-enabled repo must also have its working Claude Routine bridge configuration:

- `CLAUDE_ROUTINE_FIRE_URL`
- `CLAUDE_ROUTINE_FIRE_TOKEN`
- `scripts/claude_cloud_bridge.py`
- `.github/workflows/claude-cloud-routine-bridge.yml`

Preserve a repo's stronger existing Claude idempotency implementation instead of replacing it with a simpler copy.

## Required Santiago/Codex workflows

The reusable core is:

- `.github/workflows/santiago-ready-label-trigger.yml`
- `.github/workflows/codex-feedback-to-claude.yml`
- `.github/workflows/codex-clean-verified.yml`

### Santiago wake-up

Accept either:

- the `READY_FOR_SANTIAGO` PR label, or
- a repository-owner-authored `READY_FOR_SANTIAGO` PR comment that names the exact head SHA.

Before waking Codex, resolve the current PR head and reject stale handoffs.

Then use `SANTIAGO_CODEX_BRIDGE_TOKEN` to post exactly:

```text
@codex review
```

### Codex findings → Claude

Listen to native `pull_request_review: submitted` events from `chatgpt-codex-connector[bot]`.

Require:

- the review commit equals the current PR head; and
- the review has one or more real inline findings.

Only then queue/fire Claude for a correction round.

Do not depend on a synthetic `CHANGES_REQUESTED` comment for this transport.

### Clean Codex → VERIFIED

Listen to Codex's clean `issue_comment` result.

Require:

- actor `chatgpt-codex-connector[bot]`;
- body contains `Didn't find any major issues`;
- a parsed `Reviewed commit` / `Commit reviewed` SHA;
- that SHA is a prefix of the current full PR head SHA; and
- no exact-head `VERIFIED:<full SHA>` marker already exists.

Then record `VERIFIED` and stop. Never merge automatically.

## Close/merge label hygiene

Comments preserve history. Labels represent current actionable state only.

Transient labels (`READY_FOR_CLAUDE_CLOUD`, `READY_FOR_SANTIAGO`) and every
retired/forbidden label (`controller:*`, `CHANGES_REQUESTED`,
`SANTIAGO_REVIEWING`, `WORK_IN_PROGRESS`, `SANTIAGO_STALLED`,
`CLAUDE_DISPATCHED`, `CLAUDE_WORKING`, `CLAUDE_STALLED`, historical literal
`NEEDS_ZANETA`) must never survive on a closed Issue/PR. Two idempotent,
removal-only layers keep that true:

- `.github/workflows/harness-label-close-cleanup.yml` — fires on
  `issues: closed` / `pull_request: closed` and removes any transient or
  retired label from that exact item.
- `.github/workflows/harness-label-reconciler.yml` — a 15-minute +
  `workflow_dispatch` fallback that sweeps closed items for the same stray
  labels, for eventual consistency when the event-driven layer missed one.

Both layers, and the shared `.github/scripts/zoe_harness_labels.py`
contract they use:

- only ever remove labels — never add a label, comment, reopen an item,
  requeue Claude, or wake Codex;
- re-check the item's open/closed state immediately before every write, so
  a reopen racing the cleanup is never clobbered;
- treat a label that is already absent as a benign no-op, not a failure;
- never touch `VERIFIED` or any other durable/normal MOLOSOC label.

## Minimal visible states

The reusable core needs only these transport/terminal concepts:

- `READY_FOR_CLAUDE_CLOUD`
- `READY_FOR_SANTIAGO`
- `VERIFIED`

Repositories may retain a separate read-only status/annotation layer, but it must not be required for transport and must not compete with the core loop.

Do not reintroduce transport dependencies on legacy states such as:

- `CHANGES_REQUESTED`
- `SANTIAGO_REVIEWING`
- `WORK_IN_PROGRESS`
- controller-generated proxy labels
- draft/ready-for-review GraphQL transitions

## Important empirical findings

1. `READY_FOR_CLAUDE_CLOUD` reliably wakes the existing Claude Routine bridge.
2. A Zaneta-authored `@codex review` wakes Codex.
3. A `github-actions[bot]` authored `@codex review` does not authenticate as Zaneta and cannot substitute for the PAT bridge.
4. The draft/ready GraphQL transport is unnecessary and failed with `Resource not accessible by integration` in the Zoe harness.
5. `issue_comment` workflows execute the default branch's workflow definition, so fixes to those workflows must be on `main` before they can be empirically tested.
6. The clean terminal workflow needs `pull-requests: write` as well as `issues: write` when it removes PR labels.
7. Codex currently formats the clean reviewed SHA as Markdown like `**Reviewed commit:** `abcdef1234``; parsing must tolerate that exact form.
8. Literal `body=@-` in `gh api -f` calls produces junk `@-` comments. Send the real body value instead.

## Required empirical proof for each repo

Do not declare a repo harness-enabled merely because the files match Zoe.

Run disposable proofs and require:

### A. Santiago clean path

```text
READY_FOR_SANTIAGO
→ @codex review authored by zanetaseiler
→ Codex pickup
→ Codex clean on exact head
→ VERIFIED exact-head marker
```

### B. Correction path

```text
Codex native review with a real inline finding on exact head
→ automatic Claude Routine dispatch
→ Claude correction
→ READY_FOR_SANTIAGO on new exact head
→ @codex review authored by zanetaseiler
→ Codex clean
→ VERIFIED
```

### C. Safety

Confirm:

- no automatic merge;
- stale SHA handoffs are ignored;
- no second Claude session for the same claimed work item;
- no bot-authored substitute for Zaneta's Codex identity;
- no junk `@-` comments;
- disposable proof PRs are closed without merging.
