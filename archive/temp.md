# Simple checklist

```text
[ ] git switch main
[ ] git pull origin main
[ ] git switch -c issue-001-release-1-runtime-contract
[ ] create docs/release_1_runtime_contract.md
[ ] update README.md with a link to the contract
[ ] poetry run pytest
[ ] git status
[ ] git diff
[ ] git add README.md docs/release_1_runtime_contract.md
[ ] git commit -m "Fix issue #001: Confirm Release 1 runtime contract"
[ ] git push -u origin issue-001-release-1-runtime-contract
[ ] open PR
[ ] PR body includes Closes #1
[ ] merge after checks pass
```

# Step 9: Check your changed files

```powershell
git status
```

You should see something like:

```text
modified: README.md
new file: docs/release_1_runtime_contract.md
```

Then review the diff:

```powershell
git diff
```

---

# Step 10: Commit the issue 001 work

Use:

```powershell
git add README.md docs/release_1_runtime_contract.md
git commit -m "Fix issue #001: Confirm Release 1 runtime contract"
```

---

# Step 11: Push your branch to GitHub

```powershell
git push -u origin issue-001-release-1-runtime-contract
```

---

# Step 12: Create a pull request

You can do it on GitHub, or with GitHub CLI:

```powershell
gh pr create --base main --head issue-001-release-1-runtime-contract --title "Fix issue #001: Confirm Release 1 runtime contract" --body "Closes #1"
```

Use this PR body:

````markdown
Closes #1

## Summary

This PR confirms the Release 1 runtime contract for AI Code / RALPH.

## Confirmed decisions

- Release 1 start command
- Release 1 CLI flags
- Minimum setup_config.py fields
- Fake/test agent behavior
- Commit message format
- Open questions

## Test command

```powershell
poetry run pytest
```
````

````

---

# Step 13: Merge only after checks pass

Before merging, make sure:

```text
The branch is pushed.
The PR is open.
The tests pass.
The document answers every acceptance criterion.
The PR says Closes #1.
````

After the PR is merged into `main`, GitHub can automatically close the linked issue when the PR uses a closing keyword like `Closes #1`. ([GitHub Docs][4])

---
