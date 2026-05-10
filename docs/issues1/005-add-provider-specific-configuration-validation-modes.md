# Add provider-specific configuration validation modes

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Add validation behavior that only checks Docker settings when Docker mode is selected and only checks Codex settings when CodexProvider is selected.

## Acceptance criteria

- [ ] Docker settings are validated only when Docker sandbox mode is selected.
- [ ] Codex settings are validated only when CodexProvider is selected.
- [ ] Local Release 1 mode does not require Docker or Codex configuration.
- [ ] Errors clearly explain which selected mode requires the missing setting.
- [ ] Tests cover local, Docker, and Codex validation paths.

## Blocked by

- Blocked by `issues/004-add-cli-parsing-and-validated-config-override-flow.md`

## User stories addressed

- User story 7
- User story 8
- User story 12

## Assumptions

- None

## Open questions

- None

## Notes

- This prevents local tracer-bullet runs from failing because future-mode settings are missing.
