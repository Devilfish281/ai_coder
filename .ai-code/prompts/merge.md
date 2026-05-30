# AI Code merge prompt

Use this prompt when preparing human-readable merge notes for AI Code.

## Issue context

Issue number: {{ISSUE_NUMBER}}
Issue title: {{ISSUE_TITLE}}

## Working location

Working branch: {{BRANCH_NAME}}
Worktree path: {{WORKTREE_PATH}}

## Merge notes

- Summarize the issue completed.
- Summarize the files changed.
- Summarize the test command and result.
- Confirm whether the completion signal was present: {{COMPLETE_TOKEN}}.
- Leave pull request creation for human review unless a later approved workflow enables it.
- Leave GitHub issue closing for human review unless a later approved workflow enables it.

## Safety reminder

Do not automatically merge, open a pull request, or close an issue from this prompt.
