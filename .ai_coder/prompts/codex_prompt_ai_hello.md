Developer: Developer: To fix the selected GitHub issue in the `ai_hello` target repository.

First write a plan that follows the implementation strategy in this prompt.

Second, follow the plan steps carefully and report verification status honestly.

# Context and rules for this RALPH run

RALPH is being run by the `ai_coder` program, but the target repository for this run is:

```text
C:\Users\ME\Documents\Python\2026\Projects\ai_hello
```

The selected GitHub issue comes from:

```text
Devilfish281/ai_hello
```

Do not assume the target project is `ai_coder`.

For this run, `ai_coder` is only the automation runner. The code to inspect and change is in the `ai_hello` worktree that RALPH prepared.

# Target project

## Project name

```text
ai_hello
```

## Language

```text
Python
```

## Package manager

```text
Poetry
```

## Test runner

```text
pytest
```

## Operating system target

```text
Windows 11
```

## Expected target project shape

The target repository is expected to be a small Python project like this:

```text
.
├── src/
│   └── ai_hello/
│       ├── __init__.py
│       ├── main.py
│       └── hello_world/
│           ├── __init__.py
│           └── hello_world.py
├── tests/
│   ├── __init__.py
│   └── test_hello_world.py
├── pyproject.toml
└── README.md
```

If the actual worktree differs, inspect the current files and follow the current project structure.

# Important rule

Build a small tracer-bullet change.

A tracer bullet means:

> Build the thinnest useful end-to-end change that proves the workflow works before adding advanced behavior.

Do not redesign the project.

Do not rewrite unrelated modules.

Do not change unrelated files.

# Coding rules

- Keep the change small.
- Do not rewrite the whole project.
- Do not add new dependencies unless the selected issue explicitly requires it.
- Do not change imports unless the selected issue requires it.
- Do not change unrelated behavior.
- Do not leave commented-out code.
- Do not add TODO comments.
- Prefer small, readable Python code.
- Prefer explicit names over clever abstractions.
- Preserve existing public interfaces unless the selected issue explicitly requires a rename.
- Write or update tests only when the selected issue requires a behavior proof or when existing tests must be corrected to match the requested behavior.
- Prefer tests that verify observable behavior.
- Do not read, print, copy, or expose `.env`, `.env.*`, secrets, tokens, or credential files.

# Selected issue source of truth

Use the GitHub issue that RALPH selected.

Read all selected issue data before deciding what to edit:

1. Issue number
2. Issue title
3. Issue body
4. Issue labels
5. Issue comments, if available
6. Acceptance criteria, if present
7. Suggested verification command, if present
8. Done criteria, if present

The selected issue is the source of truth for the exact text, behavior, files, tests, and acceptance criteria.

Do not hard-code a specific issue topic into this prompt.

Do not assume the selected issue asks for a greeting change, print-message change, test-only change, refactor, documentation change, or feature change.

If the selected issue is vague, blocked, unsafe, missing required context, or clearly targets a different repository, stop and report the blocker.

Do not guess.

# Correct workflow

Use this workflow:

```text
Read selected issue
  ↓
Confirm the issue targets ai_hello or can safely be applied to ai_hello
  ↓
Find the smallest relevant ai_hello seam
  ↓
Read related tests first
  ↓
Read related source second
  ↓
Add or update a focused test only when needed
  ↓
Make the smallest source or documentation change needed
  ↓
Do not run tests
  ↓
Report host-side verification is required
  ↓
Do not commit
  ↓
Output completion token when the requested change is complete
```

# File discovery rules

Do not assume the exact file to change before inspecting the worktree.

After reading the selected GitHub issue:

1. Identify the behavior, file, module, or documentation area the issue refers to.
2. Search only relevant target-project folders.
3. Read matching tests first when code behavior is involved.
4. Read matching source files second when code behavior is involved.
5. Read matching documentation files when documentation is involved.
6. Choose the smallest file set needed to satisfy the issue.
7. Do not change unrelated modules.
8. Only update `__init__.py` files when a changed or added public interface must be exported.

Possible target-project paths include:

```text
src/ai_hello/
tests/
README.md
pyproject.toml
```

These paths are guidance only. Inspect the actual target worktree before editing.

Do not scan or edit these folders unless the issue explicitly requires it:

```text
.git/
.venv/
.pytest_cache/
__pycache__/
dist/
build/
var/logs/
.ai_coder/
.ai_coder/ai_coder_worktrees/
```

Do not read, print, copy, or commit secret files, including:

```text
.env
*.env
.env.*
```

# Testing rules

Expected behavior is defined by the selected issue and the target project's tests.

Before changing behavior:

1. Read the related tests.
2. Add or update a focused test when behavior is missing or when the existing test must reflect the selected issue.
3. Write the smallest implementation needed to satisfy the selected issue.
4. Refactor only when the change remains small and directly related.

## Important note about test execution

Codex must not execute project test commands.

Codex must not run:

```powershell
poetry run pytest
```

Codex must not run:

```powershell
pytest
```

Codex must not run focused tests, full tests, or final project verification.

RALPH owns final test execution after Codex returns from the orchestrator.

This rule exists because RALPH must prove the final post-change verification through its own test-runner/sandbox seam.

Codex may read test files and may add or update tests when the selected issue requires a behavior proof.

Codex may run only lightweight non-test inspection commands when command execution is available and safe, such as:

```powershell
git status --short
```

```powershell
git diff
```

Do not claim tests passed unless the test command was actually run by RALPH or a human operator after Codex returned.

# Package manager and verification command

The host-side verification command for this project is expected to be:

```powershell
poetry run pytest
```

Do not run it from Codex.

If the selected issue provides a different suggested verification command, report both:

1. The selected issue's suggested verification command.
2. The expected default host-side verification command.

Do not execute either command from Codex.

# Plan format

Before editing, write a short plan in this exact shape:

```text
Issue: #<issue_number> - <issue_title>

Relevant tests:
- <test file>: <why it is relevant>
- No focused test change needed because <reason>

Relevant source or docs:
- <source or doc file>: <why it is relevant>

Planned changes:
1. <small test change, or "No test change needed because ...">
2. <small source or documentation change>
3. <export change only if needed>
```

Do not include guessed files.

Only list files after reading the issue and inspecting the target project.

# Implementation strategy

## Step 1: Read the selected issue

Read the selected issue title, body, labels, comments, acceptance criteria, suggested verification command, and done criteria.

Determine:

- what behavior is broken or missing,
- what acceptance criteria must be satisfied,
- whether the issue is actionable,
- whether the issue is blocked,
- whether the issue asks for a user-visible change, test-only change, refactor, documentation update, or configuration update.

If the issue is blocked, stop and report the reason.

## Step 2: Confirm this is the ai_hello target repo

Confirm the current worktree contains the target project files.

Look for project evidence such as:

```text
pyproject.toml
src/ai_hello/
tests/
```

If the worktree appears to be `ai_coder` instead of `ai_hello`, stop and report the blocker.

Do not edit `ai_coder` files for this prompt.

## Step 3: Locate the smallest relevant area

Use the selected issue to decide where to inspect.

Search only the likely relevant files and folders.

Do not perform broad, blind replacements.

Do not update every matching word or line unless the selected issue explicitly requires that broad change.

## Step 4: Read tests first when behavior changes

Read the tests that already cover the behavior.

If existing tests need to change to match the selected issue, update the smallest relevant assertion.

If tests already cover the requested behavior, do not add unnecessary tests.

If the selected issue is documentation-only, no test change may be needed.

## Step 5: Read source or documentation second

Read the source file or documentation file that implements the selected issue's requested change.

Change only what the selected issue requires.

Do not change unrelated print messages, imports, public interfaces, configuration, or documentation.

## Step 6: Make the smallest change

Make the smallest source, test, documentation, or configuration change needed to satisfy the selected issue.

Do not add dependencies.

Do not reformat unrelated files.

Do not introduce broad architecture changes.

## Step 7: Do not run tests

Do not run focused tests.

Do not run full tests.

Do not run final project verification.

Do not run:

```powershell
poetry run pytest
```

Do not run:

```powershell
pytest
```

Report that host-side verification is required.

## Step 8: Inspect changes

Run, if command execution is available:

```powershell
git status --short
git diff
```

Confirm that only relevant files changed.

Do not include generated caches, logs, `.env` files, or unrelated files in the intended change set.

## Step 9: Do not commit

Do not create a git commit.

RALPH owns final verification, commit creation, sync, pull request draft behavior, and issue closing after the orchestrator returns.

Codex should leave the worktree changed and report:

1. What files changed.
2. Whether tests were run by Codex.
3. Whether host-side verification is required.
4. Whether a commit was created by Codex.
5. Whether the requested change is complete.

# Verification reporting

At the end, report the real verification state in this form:

```text
Tests run by Codex: no
Reason: RALPH owns final verification after the orchestrator returns.
Host-side verification required: yes
Host-side verification command: poetry run pytest
Commit: not created; RALPH owns commit creation.
Source or documentation change complete: yes or no
Files changed:
- <file path>
```

If the selected issue provides a different suggested verification command, also report:

```text
Issue suggested verification command: <command from selected issue>
```

Do not say tests passed unless RALPH or the human operator later runs them successfully outside this Codex step.

Do not create a commit from Codex.

# Acceptance criteria checklist

Codex must verify:

- [ ] The selected GitHub issue was read.
- [ ] The issue was actionable and not blocked.
- [ ] The worktree was confirmed to be the `ai_hello` target project.
- [ ] Relevant tests were read before source changes when behavior changed.
- [ ] Relevant source or documentation files were read before changes.
- [ ] A focused test was added or updated only when needed.
- [ ] The smallest relevant change was made.
- [ ] The selected issue's acceptance criteria were addressed.
- [ ] No unrelated files were changed.
- [ ] No new dependency was added unless the selected issue explicitly required it.
- [ ] Existing public interface names were preserved unless the selected issue explicitly required a rename.
- [ ] No `.env` or secret file content was read, printed, copied, committed, or exposed.
- [ ] No focused tests were run by Codex.
- [ ] No full tests were run by Codex.
- [ ] Host-side verification requirement was reported honestly.
- [ ] No commit was created by Codex.
- [ ] `<promise>COMPLETE</promise>` was output when the requested change was complete and no known source-code blocker remained.

# Definition of done

Codex is done only when:

1. The selected issue is understood.
2. The target worktree is confirmed to be `ai_hello`.
3. The selected issue's requested change is implemented.
4. The behavior is covered by an existing or updated focused test when appropriate.
5. Test execution was not run by Codex, and host-side verification was reported as required.
6. No unrelated files were intentionally changed.
7. No secrets were exposed.
8. No commit was created by Codex.
9. Codex reports whether host-side verification is still required.
10. Codex outputs:

```text
<promise>COMPLETE</promise>
```

RALPH owns final project verification, commit creation, sync, pull request draft behavior, and issue closing after Codex returns.
