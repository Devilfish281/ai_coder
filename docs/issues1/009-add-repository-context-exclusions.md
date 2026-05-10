# Add repository context exclusions

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Exclude unsafe, huge, generated, or secret-bearing paths from repository context discovery by default.

## Acceptance criteria

- [ ] Repository context excludes .git, .venv, venv, __pycache__, pytest/mypy/ruff caches, node_modules, dist, build, .env, generated logs, and large binary files.
- [ ] Secret files are not included in prompts by default.
- [ ] Generated logs and reports are excluded unless explicitly requested.
- [ ] Tests cover excluded directory and file patterns.
- [ ] The exclusion logic is easy to extend.

## Blocked by

- Blocked by `issues/008-add-repository-context-discovery.md`

## User stories addressed

- User story 20
- User story 21

## Assumptions

- None

## Open questions

- None

## Notes

- None
