# Main modules to build

## 1. `AgentProvider`

Purpose:

`AgentProvider` defines which AI coding agent RALPH runs.

Examples of future providers:

```text
claude
codex
opencode
local_mock
```

For the first tracer bullet, implement only a simple mock provider.

The mock provider should:

- accept a prompt,
- return deterministic output,
- be easy to test,
- not call a real external AI service.

Later providers can call real command-line tools.

---

## 2. `Orchestrator`

Purpose:

`Orchestrator` is the main loop.

It repeatedly runs an agent until one of these things happens:

- the agent outputs `<promise>COMPLETE</promise>`,
- the maximum iteration count is reached,
- the agent returns an error,
- an idle timeout is reached.

For the first tracer bullet, implement:

- max iteration limit,
- completion detection,
- clear result object,
- tests for complete and max-iteration behavior.

Do not implement streaming, idle timeout, or advanced display until a later issue requires it.

---

## 3. `WorktreeManager`

Purpose:

`WorktreeManager` wraps Git worktree commands.

It should eventually support:

- creating a worktree,
- generating a temporary branch name,
- sanitizing branch names,
- checking for uncommitted changes,
- removing clean worktrees,
- preserving dirty worktrees,
- pruning stale worktrees.

For the first tracer bullet, implement only:

- branch-name generation,
- name sanitizing,
- optional command construction that can be tested without running Git.

Do not run real Git commands in unit tests unless the issue explicitly asks for integration tests.

---

## 4. `SandboxProvider`

Purpose:

`SandboxProvider` defines where the agent runs.

Future sandbox types:

```text
local
docker
podman
test
```

For the first tracer bullet, implement only a local/test sandbox adapter.

The first sandbox adapter should:

- run commands in a chosen working directory,
- return stdout, stderr, and exit code,
- be easy to replace later.

---

## 5. `PromptResolver`

Purpose:

`PromptResolver` loads prompts.

It should eventually support:

- inline prompts,
- prompt files,
- default built-in prompts.

For the first tracer bullet, implement:

- inline prompt support,
- loading a prompt from a file path,
- helpful error when the file does not exist.

---

## 6. `PromptPreprocessor`

Purpose:

`PromptPreprocessor` prepares prompt text before it is sent to the agent.

It should eventually support:

- placeholder replacement like `{{ISSUE_NUMBER}}`,
- safe shell command expansion like `` !`git log --oneline -5` ``,
- built-in prompt arguments,
- protection against accidental command execution from user-provided values.

Important security rule:

Only shell commands written directly in the raw trusted prompt template may be executed.

Never execute shell commands that appear only after placeholder substitution.

For the first tracer bullet, implement only safe placeholder replacement.

Do not implement shell command expansion until a later issue requires it.

---

## 7. `github_issues.py`

Purpose:

This module reads and updates GitHub issues.

## GitHub issue priority order

When RALPH is working through issues, it should pick issues in this order:

1. Bug fixes — broken behavior affecting users
2. Tracer bullets — thin end-to-end slices that prove an approach works
3. Polish — improving existing functionality, error messages, UX, or docs
4. Refactors — internal cleanups with no user-visible change

Pick the highest-priority open issue that is not blocked by another open issue.

Work on one issue per iteration.

Do not attempt multiple issues in a single run.

---

It should eventually wrap these commands:

```powershell
gh issue list
gh issue close
gh issue comment
```

For the first tracer bullet, implement:

- a small data model for a GitHub issue,
- issue-priority selection logic,
- tests using fake issue data.

Do not require the GitHub CLI in unit tests.

---

## 8. `sync_in.py` and `sync_out.py`

Purpose:

These modules eventually move files and commits in and out of isolated sandboxes.

For the first tracer bullet, create the files but keep behavior minimal.

Do not implement full file syncing unless the issue requires it.

---

## 9. `display.py`

Purpose:

`Display` controls what the user sees.

Future display adapters:

```text
ConsoleDisplay
SilentDisplay
FileDisplay
```

For the first tracer bullet, implement:

- `SilentDisplay` for tests,
- simple console messages if needed.

---

## 10. `ralph.py`

Purpose:

This is the high-level RALPH workflow.

RALPH should eventually:

1. list open GitHub issues,
2. select one issue,
3. prepare a branch/worktree,
4. prepare a prompt,
5. run the orchestrator,
6. run tests,
7. commit changes,
8. close or comment on the issue.

For the first tracer bullet, implement a minimal version that:

- accepts fake issue data,
- selects one issue,
- builds a prompt,
- runs the mock agent through the orchestrator,
- returns a clear result.

## RALPH runtime behavior

When the project is ready for real GitHub issue execution, RALPH should follow this runtime workflow.

## 1. Explore

Read the issue carefully.

If the issue references a parent PRD, read the parent PRD.

Read relevant source files and tests before writing code.

## 2. Plan

Decide what to change and why.

Keep the change as small as possible.

Do not rewrite the whole project.

## 3. Execute

Use:

```text
Red → Green → Repeat → Refactor
```

Write or update a failing pytest test first when behavior is missing.

Then write the smallest implementation needed to pass the test.

## 4. Verify

Run:

```powershell
poetry run pytest
```

If Poetry is unavailable, run:

```powershell
pytest
```

Do not commit if tests fail.

## 5. Commit

If files changed and tests pass, make exactly one git commit.

The commit message must start with:

```text
RALPH:
```

The commit message should include:

- issue number,
- task completed,
- PRD reference if any,
- key decisions made,
- files changed,
- blockers for the next iteration if any.

## 6. Close or comment

Only close the issue if:

- the fix is committed,
- tests pass,
- the issue is fully completed.

Close with:

```powershell
gh issue close <ID> --comment "Completed by Sandcastle/RALPH. Summary: <short summary>. Verification: pytest passed."
```

If blocked, do not close the issue.

Comment with:

```powershell
gh issue comment <ID> --body "Blocked by Sandcastle/RALPH. Reason: <reason>"
```

---

---
