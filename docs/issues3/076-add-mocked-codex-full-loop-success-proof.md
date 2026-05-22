# Add mocked Codex full-loop success proof

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add the main mocked Phase 3 success proof through the RALPH loop.

The fake sandbox should simulate a successful Codex run that makes a visible worktree change and emits `<promise>COMPLETE</promise>`. RALPH should detect completion, run final tests, sync/commit successful changes, and expose phase results.

## Acceptance criteria

- [ ] Test crosses `i_ralph_run()` or the public RALPH seam.
- [ ] setup_config selects CodexProvider.
- [ ] CodexProvider runs through the sandbox seam.
- [ ] Fake Codex output includes `<promise>COMPLETE</promise>`.
- [ ] RALPH detects completion.
- [ ] Baseline pytest ran before the Codex phase.
- [ ] Final pytest ran after the Codex phase.
- [ ] Sync/commit happens only after final pytest passes.
- [ ] `RalphResult` exposes project setup, final test, sync, and cleanup results.
- [ ] Pull request and issue close behavior remains disabled or dry-run.

## Blocked by

- Blocked by `issues/075-prove-codex-command-argument-safety-through-ralph-loop.md`

## User stories addressed

- User story 23
- User story 24
- User story 25
- User story 29
- User story 30

## Assumptions

- The visible worktree change can be simulated safely through a fake sandbox or patched file operation.

## Open questions

None

## Notes

This is the mocked success path. Real Codex and real worktree proof come later.
