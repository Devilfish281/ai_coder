# Expose sync result on RalphResult

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Expose the sync/commit phase result through the public RALPH result object.

Phase 3 needs this field so the Codex proof can assert that changes were committed only after final tests passed and can inspect the commit hash through the public result object.

## Acceptance criteria

- [ ] `RalphResult` exposes `sync_result` as an optional field.
- [ ] `sync_result` defaults to `None`.
- [ ] Successful runs populate `sync_result`.
- [ ] Successful committed runs expose committed status.
- [ ] Successful committed runs expose the commit hash.
- [ ] Final test failure leaves `sync_result` as `None`.
- [ ] Sync or commit failure returns a populated `sync_result` that explains the failure when the sync phase ran.

## Blocked by

- Blocked by `issues/060-expose-final-test-result-on-ralph-result.md`

## User stories addressed

- User story 23
- User story 29
- User story 30

## Assumptions

- A sync or commit result object already exists or equivalent commit-result data is already produced by the RALPH workflow.

## Open questions

None

## Notes

This does not add new sync behavior. It only makes existing sync/commit results visible.
