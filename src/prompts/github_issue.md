# Create new issue

## Add a title

Fix local RALPH loop

## Add a description

### ISSUE_BODY

RALPH should follow and stubout this workflow:

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

Have RALPH follow the workflow above, but with a local GitHub issue file fallback instead of fetching from the GitHub API.

This will allow us to test RALPH's core functionality without needing to set up GitHub API access.

### Test plan

```powershell
poetry run pytest
```

### LABELS

Polish
