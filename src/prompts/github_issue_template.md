# Create new issue

## Add a title

Fix local RALPH loop

## Add a description

### ISSUE_BODY

RALPH should eventually automate this workflow:

1. Start with a Git repository.
2. Read open GitHub issues.
3. Pick one actionable issue.
4. Create a safe working copy using a Git worktree.
5. Start a sandbox or local execution environment.
6. Give an AI coding agent a prompt.
7. Let the agent edit files, run commands, and commit changes.
8. Detect whether the task is complete.
9. Run tests.
10. Sync or merge the finished work back to the host repo.
11. Close the GitHub issue only after tests pass and the fix is committed.
12. Preserve the worktree if there are uncommitted changes or a failure.

### Goal

Have the RALPH follow the workflow above, but with a local GitHub issue file fallback instead of fetching from the GitHub API. This will allow us to test RALPH's core functionality without needing to set up GitHub API access.

### LABELS

### The issue should be labeled with one of these: bug, tracer, polish, refactor, feature

1. **Bug** — a user-facing issue that causes incorrect behavior or an error
2. **Tracer bullet** — a thin end-to-end slice that proves an approach works, even if it's not the final implementation
3. **Polish** — improving existing functionality, such as error messages, UX, or documentation
4. **Refactor** — internal cleanups that don't change user-visible behavior but improve code quality or maintainability
5. **Feature** — a new user-facing capability that adds value to the project

## Polish
