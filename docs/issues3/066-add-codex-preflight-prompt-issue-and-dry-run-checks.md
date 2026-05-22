# Add Codex preflight prompt, issue, and dry-run checks

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Extend Codex preflight to verify that the smoke proof has safe inputs before the model call.

This slice checks that the prompt file or prompt text is available, issue data is available or live issue reading is configured, and GitHub automation remains dry-run or disabled during Phase 3.

## Acceptance criteria

- [ ] Preflight verifies the Codex smoke prompt or configured prompt input exists.
- [ ] Preflight verifies provided issue data or live issue-reading input is available.
- [ ] Preflight verifies PR creation is disabled or dry-run.
- [ ] Preflight verifies issue closing is disabled or dry-run.
- [ ] Missing prompt input returns blocked.
- [ ] Missing issue input returns blocked.
- [ ] Unsafe PR or close configuration returns blocked.

## Blocked by

- Blocked by `issues/065-add-codex-executable-version-readiness-check.md`

## User stories addressed

- User story 23
- User story 27
- User story 28

## Assumptions

- The Phase 3 smoke proof may use provided issue data or live issue reading with the configured tracer label.

## Open questions

None

## Notes

This issue should not create the prompt file itself. That comes later in the smoke prompt/checklist issue.
