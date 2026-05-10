# Run pytest through sandbox seam

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Run pytest through the sandbox seam before any successful commit is created.

## Acceptance criteria

- [ ] pytest runs through i_sandboxhandle_run().
- [ ] Configured test commands are preferred over guesses.
- [ ] Test stdout, stderr, and exit code are visible.
- [ ] Test failure prevents success.
- [ ] Tests cover passing pytest, failing pytest, and missing test command behavior.

## Blocked by

- Blocked by `issues/022-add-ralph-result-status-contract.md`

## User stories addressed

- User story 16
- User story 19

## Assumptions

- None

## Open questions

- None

## Notes

- None
