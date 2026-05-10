# Add repository context discovery

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Build a small, useful repository context summary for agent prompts, including package manager, likely test command, and useful project signals.

## Acceptance criteria

- [ ] Repository context detects useful project facts such as package manager and likely test command.
- [ ] Configured commands from setup_config.py are preferred over guessed commands.
- [ ] Repository context stays small and prompt-safe.
- [ ] Repository context discovery is behind a clear responsibility.
- [ ] Tests cover configured and inferred context behavior.

## Blocked by

- Blocked by `issues/006-add-repository-root-and-branch-discovery.md`

## User stories addressed

- User story 21

## Assumptions

- None

## Open questions

- None

## Notes

- None
