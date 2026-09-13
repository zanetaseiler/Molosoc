# CLAUDE.md

This is Claude Code's entry point for this repository's shared Claude ↔ Santiago/Codex harness.

## Load the proven harness first

Read `docs/HARNESS_GOLDEN_PATH.md` before doing anything else. Zoe is the reference implementation and this repository must follow the same proven handoff behavior.

Before every new or resumed Issue/PR task:

1. Refresh the base branch and inspect the current exact PR head.
2. Read the Issue/PR and every current review/comment relevant to the active task.
3. If this is a Codex correction round, read the current exact-head Codex inline findings and fix only those findings within the existing task scope.
4. Make the required repository-only edits and tests on the existing task branch/PR.
5. When implementation or correction is complete, post `READY_FOR_SANTIAGO` with the new exact head commit SHA and a concise implementation/test summary.
6. STOP. Do not continue into review, merge, deployment, publishing, production mutation, credential changes, or another task.

GitHub is the persistent source of truth. Do not rely on chat/session memory over the current Issue/PR state.

## Consequential actions

Never merge a PR, deploy, publish, send, spend, mutate production/client data, change OAuth/platform state, or create/replace/expose credentials without Žaneta's separate explicit approval.
