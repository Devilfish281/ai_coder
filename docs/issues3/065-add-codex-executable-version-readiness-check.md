# Add Codex executable version readiness check

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_4.md`

## Type

AFK

## Human decision needed

None.

## What to build

Extend Codex preflight to check command availability and basic CLI readiness.

This slice should verify the configured Codex command is available and can report a version or equivalent readiness signal. Missing CLI setup should be blocked, not failed, because RALPH did not actually run the agent loop.

## Acceptance criteria

- [ ] Preflight checks the configured Codex command name or path.
- [ ] Preflight checks executable availability.
- [ ] Preflight can run a read-only version/readiness command such as `codex --version`.
- [ ] Missing Codex executable returns blocked.
- [ ] Version/readiness command failure returns blocked with diagnostics.
- [ ] Preflight still does not call the model or modify the worktree.

## Blocked by

- Blocked by `issues/064-add-codex-preflight-provider-and-sandbox-checks.md`

## User stories addressed

- User story 23
- User story 27

## Assumptions

- A command-running seam or subprocess wrapper can be patched in tests.

## Open questions

- What exact blocked message should be shown when Codex authentication is missing?

## Notes

Authentication may not be fully provable without a model call. Keep the check lightweight and conservative.
