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

## Harness handoff rules (same in every repo)

These come from `docs/HARNESS_TEMPLATE.md` ("Rules for each role"), which is
identical in every repository that runs the Claude <-> Santiago/Codex loop.

1. Before any edit, post `CONTEXT_RECEIPT` as its own comment (on the PR once
   one exists).
2. After the last `git push`, post a **separate** comment on the **PR** whose
   first line is exactly `READY_FOR_SANTIAGO` and which contains
   `- exact head commit SHA: <sha>`, with `<sha>` copied from
   `git rev-parse HEAD`, never typed.
3. Push nothing after that comment, and never post `@codex review` yourself.
   A correction round repeats steps 1-2.
4. If a `HANDOFF_IGNORED` or `HARNESS_STALLED` comment appears, do exactly
   what it says.
5. **Never end a session without one of these two comments on GitHub:**
   `READY_FOR_SANTIAGO` on the PR (work done) or `NEEDS_ZANETA` (you are
   blocked or need a decision -- put the question there). Nobody reads the
   session chat: a question or summary left only in chat stops the work
   silently. Žaneta answers `NEEDS_ZANETA` with a `ZANETA_DECISION` comment,
   which restarts Claude automatically.
6. Never merge a PR yourself. A `VERIFIED` PR is merged by the harness
   (`MERGED` comment, Žaneta's standing decision of 2026-09-25); that merge
   is not an instruction to start more work.
