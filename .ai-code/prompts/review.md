# AI Code review prompt

Use this prompt as review guidance for a completed AI Code implementation slice.

## Issue context

Issue number: {{ISSUE_NUMBER}}
Issue title: {{ISSUE_TITLE}}
Issue labels: {{ISSUE_LABELS}}

## Repository context

{{REPOSITORY_CONTEXT}}

## Working location

Working branch: {{BRANCH_NAME}}
Worktree path: {{WORKTREE_PATH}}

## Review guidance

- Check that the change matches the issue.
- Check that the implementation stayed small and focused.
- Check that public seams are preserved unless the issue required a change.
- Check that tests focus on observable behavior.
- Check that generated files stayed under `.ai-code/`.
- Check that generated files use AI Code wording.
- Check that no real secrets were added.
- Check that no issue text was treated as executable command text.

## Review result

Summarize whether the implementation is ready for human review.
