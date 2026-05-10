This issue should answer:

What command starts RALPH?
What flags does Release 1 support?
What config fields are required?
How does the fake/test agent behave?
What does a successful commit message look like?
What questions are still open?

# Release 1 Runtime Contract

## Status

Confirmed for Release 1.

## Start command

## Release 1 CLI flags

```text
--issue-number
--repo-path
--max-iterations
--agent
--dry-run
```

Meaning:

```text
--issue-number 1
```

Tells RALPH which GitHub issue to work on.

```text
--repo-path .
```

Tells RALPH where the Git repository is.

```text
--max-iterations 3
```

Limits how many times the agent loop runs.

```text
--agent fake
```

Uses the fake/test agent first.

```text
--dry-run
```

Runs safely without closing issues or pushing real changes.

---

## Minimum `setup_config.py` fields

For Release 1, keep it simple:

```text
project_name
repo_path
github_repo
default_agent
max_iterations
test_command
commit_message_template
dry_run
```

Example values:

```python
project_name = "AI Code"
repo_path = "."
github_repo = "Devilfish281/ai_coder"
default_agent = "fake"
max_iterations = 3
test_command = "poetry run pytest"
commit_message_template = "Fix issue #{issue_number}: {issue_title}"
dry_run = True
```

Example values '.env' file:

```text
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_api_key_here
PROJECT_NAME=AI Code
REPO_PATH=.
GITHUB_REPO=Devilfish281/ai_coder
DEFAULT_AGENT=fake
MAX_ITERATIONS=3
TEST_COMMAND=poetry run pytest
COMMIT_MESSAGE_TEMPLATE=Fix issue #{issue_number}: {issue_title}
DRY_RUN=True
```

## Commit message format

For real GitHub auto-linking later:

```text
Fixes #1: Confirm Release 1 runtime contract
```

GitHub supports keywords like `Fixes #10`, `Closes #10`, and `Resolves #10` to link pull requests to issues and automatically close them after merge.

## Required CLI flags

| Flag               | Required | Purpose                                                            |
| ------------------ | -------: | ------------------------------------------------------------------ |
| `--issue-number`   |      Yes | Selects the GitHub issue RALPH should work on.                     |
| `--repo-path`      |       No | Points to the local Git repository. Defaults to current directory. |
| `--max-iterations` |       No | Limits the number of agent loop attempts.                          |
| `--agent`          |       No | Chooses the agent provider. Defaults to `fake`.                    |
| `--dry-run`        |       No | Runs safely without closing issues or pushing changes.             |

## Minimum setup_config.py fields

| Field                     | Purpose                                  |
| ------------------------- | ---------------------------------------- |
| `project_name`            | Human-readable project name.             |
| `repo_path`               | Local repository path.                   |
| `github_repo`             | GitHub owner/repository name.            |
| `default_agent`           | Default agent provider.                  |
| `max_iterations`          | Agent loop safety limit.                 |
| `test_command`            | Command used to run tests.               |
| `commit_message_template` | Template for successful commit messages. |
| `dry_run`                 | Safety flag for Release 1.               |

## Fake/test agent behavior

The Release 1 fake agent must:

1. Receive the resolved prompt.
2. Log that the prompt was received.
3. Make one safe local test change.
4. Return a completion result.
5. Avoid real AI API calls.
6. Avoid pushing code.
7. Avoid closing GitHub issues.

The fake agent completion signal is:

```text
<promise>COMPLETE</promise>
```

## Successful commit message format

```text
Fix issue #{issue_number}: {issue_title}
```

Example:

```text
Fix issue #001: Confirm Release 1 runtime contract
```

## Pull request closing keyword

The pull request description should include:

```text
Closes #1
```

## Open questions

None for Release 1.

````

---

# Step 8: Run tests

Use your project rule:

```powershell
poetry run pytest
````

If Poetry does not work:

```powershell
pytest
```

Pytest supports running tests from the command line, including running all tests or selecting specific files/directories.

For this issue, tests may not change because this is mostly documentation.

That is okay.

---
