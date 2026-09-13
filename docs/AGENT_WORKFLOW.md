# Agent workflow — minimal Claude ↔ Santiago/Codex handoff

This repository uses the same proven core handoff as Zoe.

## Claude delivery

Before editing a correction PR, Claude reads the PR, current review findings, and current head SHA.

When the implementation or correction is complete, Claude posts:

```text
READY_FOR_SANTIAGO

- exact head commit SHA: `<full SHA>`
- implemented/fixed: <short summary>
- files changed: <paths>
- tests/results: <what was run>
- live/external effects: none, unless explicitly approved otherwise
```

Then Claude stops.

## Santiago/Codex review

`READY_FOR_SANTIAGO` wakes Codex through the authenticated bridge. Reviews are valid only for the current exact PR head.

If Codex has real inline findings on that head, the harness fires Claude for one bounded correction round on the same PR.

If Codex reports no major issues on that head, the harness records:

```text
VERIFIED

- exact head commit SHA: `<full SHA>`
- reviewer: Santiago/Codex
- result: Codex found no major issues on this exact head
- next: human merge gate; no merge performed
```

## Stop conditions

- Claude stops after `READY_FOR_SANTIAGO`.
- A clean Codex result stops at `VERIFIED`.
- `VERIFIED` never authorizes an automatic merge.
- Stale SHA handoffs/reviews are ignored.
- Do not create extra transport states, proxy labels, draft/ready tricks, or synthetic `CHANGES_REQUESTED` transport for this core loop.