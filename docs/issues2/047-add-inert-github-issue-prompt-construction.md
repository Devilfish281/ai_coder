# Add inert GitHub issue prompt construction

> File status: Draft local markdown issue. Not created automatically.

## Parent PRD

`ai_code_prd_rev_3.md`

## Type

AFK

## Human decision needed

None.

## What to build

Use GitHub issue number, title, body, and labels to build the agent prompt while treating all issue data as inert text.

## Acceptance criteria

- [ ] Issue number/title/body/labels can be inserted into the prompt.
- [ ] Shell-command syntax in issue data is not executed.
- [ ] Large issue bodies are handled safely.
- [ ] Raw prompt bodies are not logged by default.
- [ ] Tests cover special characters and long issue bodies.

## Blocked by

- Blocked by `issues/045-add-github-issue-reading-adapter.md`
- Blocked by `issues/046-add-github-issue-filtering-and-skip-reasons.md`
- Blocked by `issues/018-add-sandbox-aware-prompt-preprocessing.md`

## User stories addressed

- User story 11

## Assumptions

- None

## Open questions

- None

## Notes

- None
