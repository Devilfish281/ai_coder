Developer: Developer: To fix the selected GitHub issue.
First write a plan that follows the implementation strategy in this prompt.

Second, follow the plan steps carefully and report test results honestly.

# Context and rules for the RALPH project.

## Important rule

Build this project in small tracer-bullet slices.

A tracer bullet means:

> Build a thin end-to-end version that proves the idea works before adding advanced features.

Do not build every module fully at once.

Start with the smallest useful version of RALPH, then improve it one GitHub issue at a time.

---

# Coding rules

- Build small slices.
- Do not rewrite the whole project.
- Do not change unrelated files.
- Do not add new dependencies unless the issue clearly requires it.
- Do not leave commented-out code.
- Do not add TODO comments.
- Prefer small, readable Python code.
- Prefer explicit names over clever abstractions.
- Keep interfaces small.
- Hide implementation details behind clear module seams.
- Write tests for behavior, not internal implementation.
- Preserve existing public interface functions unless the issue explicitly requires a rename.

---

# Target project

## Project name

```text
ai_coder
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

## Development style

Use clean Python modules under `src/`.

Use tests under `tests/`.

Prefer simple code over clever code.

Do not add unnecessary dependencies.

---

# Project structure

### Important Modules:

- AgentProvider: Python classes for Claude/Codex/OpenCode commands
- Orchestrator: Python loop that runs the agent until complete
- WorktreeManager: Python wrapper around git worktree
- SandboxProvider: Python Docker/Podman/local sandbox runner
- PromptResolver: Python prompt file loader
- PromptPreprocessor: Python placeholder replacement and safe command expansion
- syncIn / syncOut: Python file copy and Git commit sync
- Display: Python terminal output/logging

### The big architecture picture

```
User runs Sandcastle
        |
        v
Read prompt / prompt file
        |
        v
Create Git worktree / branch
        |
        v
Start sandbox provider
(Docker, Podman, Vercel, Daytona, etc.)
        |
        v
Run lifecycle hooks
        |
        v
Start AI agent
(Claude Code, Codex, Pi, OpenCode)
        |
        v
Orchestrator loops:
  - send prompt
  - stream output
  - parse text/tool calls/result
  - check for COMPLETE
  - enforce timeouts
        |
        v
Collect commits
        |
        v
Sync changes back to host repo
        |
        v
Merge or preserve branch/worktree
        |
        v
Clean up safely
```

---

## Project design vocabulary

Use these terms consistently:

### Module

Anything with an interface and an implementation.

### Interface

Everything a caller must know to use the module correctly.

### Implementation

The internal code hidden behind the interface.

### Seam

The place where callers cross into the module through the interface.

### Adapter

A concrete thing that satisfies an interface at a seam.

### Depth

How much useful behavior is hidden behind a small interface.

### Leverage

What callers get from depth.

### Locality

What maintainers get from depth.

## Interface naming rule

Interface functions must follow this naming pattern:

```text
i_ + module_name + verb/action
```

Examples:

```text
i_worktree_create()
i_prompt_resolve()
i_orchestrator_run()
i_github_issue_select()
```

Do not expose many public functions.

Prefer a small interface with useful behavior hidden behind it.

Private helper functions should start with `_`.

---

## Expected behavior source of truth

Expected behavior is defined by the tests.

Read this file before changing behavior:

```text
tests/
```

# Testing rules

Expected behavior is defined by tests.

Before changing behavior, Codex must:

1. Read the related tests.
2. Add or update a focused test when behavior is missing.
3. Write the smallest implementation needed to satisfy the selected issue.
4. Refactor only when the change remains small and directly related.

Codex must not execute project test commands.

Codex must not run:

```powershell
poetry run pytest
```

Codex must not run:

```powershell
pytest
```

Codex must not run final project verification.

RALPH owns all test execution after Codex returns from the orchestrator. Codex should only report the exact verification command that RALPH or the human operator should run.

When testing printed output is required by the selected issue, use pytest output capture such as `capsys` in the test code.

Avoid testing private implementation details directly.

Prefer tests that cross the public interface seam.

# Codex Plan 3: A Plan to Fix the Selected GitHub Issue

## Purpose

This prompt is for Codex after RALPH has already selected exactly one GitHub issue.

Codex should treat the selected GitHub issue as the source of truth for what to fix.

This plan does not assume the issue topic, module, source file, or test file ahead of time.

Codex must first read the selected issue, then discover the smallest relevant area of the `ai_coder` project to change.

The job is to:

1. Understand the selected GitHub issue.
2. Find the smallest relevant project seam.
3. Read the related tests and source code.
4. Add or update a focused test only when behavior is missing.
5. Make the smallest source change needed.
6. Do not run focused tests, full tests, or final project verification.
7. Report that host-side verification is required.
8. Do not commit changes. RALPH owns final testing, commit creation, sync, pull request draft behavior, and issue closing after the orchestrator returns.
9. Output `<promise>COMPLETE</promise>` when the requested code or documentation change is complete and no known source-code blocker remains.

Do not claim tests passed unless the test command was actually run and returned success.
Do not withhold the completion token only because final project verification, commit creation, sync, pull request creation, or issue closing still belongs to RALPH.

---

## Important note about test execution

Codex must not run tests in this prompt.

This rule exists because RALPH owns final verification after the orchestrator returns. It also avoids Windows/Codex subprocess environment failures, such as `[WinError 10106]`, from being mistaken for source-code test failures.

Codex must not run:

```powershell
poetry run pytest
```

Codex must not run:

```powershell
pytest
```

Codex must not run focused tests, full tests, or final project verification.

Codex may read test files and may add or update tests when the selected issue requires a behavior proof.

Codex may run only lightweight non-test inspection commands when command execution is available and safe, such as:

```powershell
git status --short
```

```powershell
git diff
```

At the end, Codex must report:

1. Files changed.
2. Tests run by Codex: no.
3. Reason: RALPH owns final verification.
4. Host-side verification required: yes.
5. Commit: not created; RALPH owns commit creation.

Do not claim tests passed unless RALPH or a human operator later runs them successfully outside this Codex step.

## Issue

Use the GitHub issue that RALPH selected.

Read all selected issue data before deciding what to edit:

1. Issue number
2. Issue title
3. Issue body
4. Issue labels
5. Issue comments, if available
6. Parent PRD reference, if mentioned
7. Acceptance criteria, if present

If the issue is vague, blocked, unsafe, or missing required context, stop and report the blocker.

Do not guess.

---

## Parent PRD

If the selected issue references a parent PRD, read that PRD before editing code.

Known PRD path for this project:

```text
ai_coder/docs/PRD/ai_code_prd_rev_4.md
```

If the PRD file does not exist in the current worktree, continue only with the selected issue and existing tests.

Do not invent requirements that are not in the issue, PRD, tests, or current source code.

---

## Goal

Fix exactly one selected GitHub issue in a small tracer-bullet slice.

Do not redesign RALPH.

Do not rewrite the project.

Do not change unrelated files.

The correct workflow is:

```text
Read issue
  ↓
Find relevant seam
  ↓
Read tests
  ↓
Read source
  ↓
Add or update a focused test only when behavior is missing
  ↓
Make smallest source fix
  ↓
Do not run tests in Codex
  ↓
Report host-side verification is required
  ↓
Do not commit
  ↓
Output completion token when the requested change is complete
```

---

## Project rules

Follow these rules:

- Keep the change small.
- Do not rewrite the whole project.
- Do not add new dependencies unless the issue explicitly requires it.
- Preserve existing public interface names unless the issue explicitly requires a rename.
- Prefer tests that cross a public interface seam.
- Avoid testing private helper functions directly.
- Do not leave commented-out code.
- Do not add TODO comments.
- Do not change unrelated files.
- Do not include `.env` contents or secret files in prompts, logs, commits, or output.
- Do not scan huge folders.
- Prefer configured commands from `setup_config.py` before guessing.
- Do not run `poetry run pytest` from Codex.
- Do not run `pytest` from Codex.
- RALPH owns final test execution after Codex returns.

---

## Current RALPH context

RALPH has already selected one issue and built this prompt.

This prompt is used during the agent execution step:

```python
orchestrator_result = i_orchestrator_run(
    selected_agent_provider,
    prompt,
    max_iterations=max_iterations,
)
```

Codex receives the selected issue inside the prompt.

Codex must use that selected issue to decide what files to inspect and change.

Codex must not create commits. RALPH runs final tests through the test-runner/sandbox seam and decides whether to commit after the orchestrator returns.

---

## File discovery rules

Do not assume which files need to change before reading the issue.

After reading the selected GitHub issue:

1. Identify the feature area named or implied by the issue.
2. Search only relevant project folders.
3. Read matching tests first.
4. Read matching source files second.
5. Choose the smallest file set needed to satisfy the issue.
6. Do not change unrelated modules.
7. Only update `__init__.py` files when a changed or added public interface must be exported.

Do not scan or edit these folders unless the issue explicitly requires it:

```text
.git/
.venv/
.pytest_cache/
__pycache__/
dist/
build/
var/logs/
.ai_coder/ai_coder_worktrees/
```

Do not read, print, copy, or commit secret files, including:

```text
.env
*.env
.env.*
```

---

## Files likely changed

Unknown until the selected GitHub issue is read.

Codex must discover the correct files by following this order:

1. Read the selected GitHub issue title, body, labels, and comments.
2. Identify the module or behavior the issue refers to.
3. Read related tests under `tests/`.
4. Read related source files under `src/ai_coder/`.
5. Make the smallest change needed to satisfy the issue.
6. Do not change unrelated files.

Only change `__init__.py` files when an added or changed public interface must be exported.

---

## Module seam guide

Use this only as a guide after reading the issue.

Do not treat this as a fixed file list.

| Issue topic                          | Likely module seam                                  |
| ------------------------------------ | --------------------------------------------------- |
| Agent command behavior               | `src/ai_coder/agent_provider/`                      |
| Codex readiness or config checks     | `src/ai_coder/codex_preflight/`                     |
| Completion token detection           | `src/ai_coder/completion_detector/`                 |
| Terminal or user messages            | `src/ai_coder/display/`                             |
| GitHub issue reading or selection    | `src/ai_coder/github_issues/`                       |
| CLI startup behavior                 | `src/ai_coder/main/` or `src/ai_coder/__main__.py`  |
| Orchestrator loop behavior           | `src/ai_coder/orchestrator/`                        |
| Prompt loading                       | `src/ai_coder/prompt_resolver/`                     |
| Prompt preprocessing or placeholders | `src/ai_coder/prompt_preprocessor/`                 |
| Repository inspection                | `src/ai_coder/repository_context/`                  |
| Sandbox command execution            | `src/ai_coder/sandbox_provider/`                    |
| Test command execution               | `src/ai_coder/test_runner/`                         |
| Git worktree behavior                | `src/ai_coder/worktree_manager/`                    |
| Syncing files in or out              | `src/ai_coder/sync_in/` or `src/ai_coder/sync_out/` |
| Pull request draft behavior          | `src/ai_coder/pull_request_draft/`                  |
| High-level RALPH workflow            | `src/ai_coder/ralph/`                               |

---

## Implementation strategy

### Step 1: Read the selected issue

Read the issue title, body, labels, and comments.

Determine:

- what behavior is broken or missing,
- what acceptance criteria must be satisfied,
- whether the issue is actionable,
- whether the issue is blocked by missing context or another issue,
- whether the issue asks for a user-visible change, test-only change, refactor, or documentation update.

If the issue is blocked, stop and report the reason.

### Step 2: Read the PRD only if the issue references it

If the issue references a PRD, read the relevant PRD section.

Do not use unrelated PRD sections as requirements.

### Step 3: Locate the smallest relevant seam

Map the issue to the smallest likely public module seam.

Prefer existing public interface functions.

Do not rename public interface functions unless the issue explicitly asks for it.

### Step 4: Read tests first

Find and read the tests that already cover the related behavior.

Use the current project test style.

Expected test locations look like:

```text
tests/<module>/test_<module>.py
```

### Step 5: Add or update one focused failing test

If the issue describes missing or broken behavior, add or update the smallest test that proves it.

The test should cross a public interface seam when practical.

Do not add broad tests that cover unrelated behavior.

### Step 6: Implement the smallest source fix

Change only the source file or files needed to pass the focused test.

Keep the code readable.

Do not add dependencies.

Do not rewrite unrelated modules.

### Step 7: Do not run test commands

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

Codex may read tests and update tests when required by the selected issue, but RALPH owns all test execution after the orchestrator returns.

If the selected issue requires verification reporting, state that tests were not run by Codex and that host-side verification is required.

### Step 8: Leave final verification to RALPH

RALPH owns final verification after the orchestrator returns.

Codex must not attempt the project's final verification command.

Codex must report:

```text
Tests run by Codex: no
Reason: RALPH owns final verification.
Host-side verification required: yes
Commit: not created; RALPH owns commit creation.
```

If Codex accidentally attempts a test command and it fails because of an environment or subprocess problem, report that honestly and do not treat the environment-only failure as proof that the source change is wrong.

### Step 9: Inspect changes

Run, if command execution is available:

```powershell
git status --short
git diff
```

Confirm that only relevant files changed.

Do not include generated caches, logs, `.env` files, or unrelated files in the intended change set.

### Step 10: Do not commit

Do not create a git commit.

RALPH owns final verification, commit creation, sync, pull request draft behavior, and issue closing after the orchestrator returns.

Codex should leave the worktree changed and report:

1. What files changed.
2. What tests were attempted, if any.
3. Whether any test command failed.
4. Whether the requested source or documentation change is complete.

### Step 11: Final output

Output:

```text
<promise>COMPLETE</promise>
```

when the requested source or documentation change is complete and no known source-code blocker remains.

Do not withhold the completion token only because final project verification, commit creation, sync, pull request creation, or issue closing still belongs to RALPH.

If tests were attempted and failed because of an environment or subprocess problem, report the test blocker honestly, then still output the completion token if the requested source or documentation change is complete.

If tests fail because the source change is wrong, fix the source change before outputting the completion token.

---

## Test-command detection note

Codex must not use this prompt to run test commands.

If the selected issue requires discovering the configured verification command for reporting only, prefer configured values from `setup_config.py` before guessing.

Recommended reporting order:

1. If `setup_config.test_command` is non-empty, report that as the host-side verification command.
2. Else if `poetry.lock` and `tests/` exist, report that RALPH should use the Poetry-based project test command.
3. Else if `tests/` exists, report that RALPH should use the project pytest command.
4. Else report that the verification command is unknown.

Do not execute the detected command from Codex.

## Package-manager detection plan

Use this only if the selected issue requires package-manager detection or repository inspection.

Recommended first version:

1. If `poetry.lock` exists, package manager is `poetry`.
2. Else if `pyproject.toml` exists, package manager is `python`.
3. Else package manager is `unknown`.

Do not add TOML parsing unless the tests truly require it.

---

## Code change plan format

Before editing, write a short plan in this shape:

```text
Issue: #<issue_number> - <issue_title>

Relevant tests:
- <test file>: <why it is relevant>

Relevant source:
- <source file>: <why it is relevant>

Planned changes:
1. <small test change>
2. <small source change>
3. <export change only if needed>
```

Do not include guessed files.

Only list files after reading the issue and inspecting the project.

---

## Verification reporting

At the end, report the real verification state in this form:

```text
Tests run by Codex: no
Reason: RALPH owns final verification after the orchestrator returns.
Host-side verification required: yes
Commit: not created; RALPH owns commit creation
Source change complete: yes or no
Files changed:
- <file path>
```

If Codex accidentally attempted a test command and it failed because of an environment or subprocess problem, report the blocker honestly in this form:

```text
Tests run by Codex: attempted accidentally
Blocked command: <command>
Reason: <environment or subprocess blocker>
Host-side verification required: yes
Commit: not created; RALPH owns commit creation
Source change complete: yes or no
```

Do not say tests passed unless RALPH or the human operator later runs them successfully outside this Codex step.

Do not create a commit from Codex.

## Acceptance criteria checklist

Codex must verify:

- [ ] The selected GitHub issue was read.
- [ ] The issue was actionable and not blocked.
- [ ] Any referenced PRD section was read, if available.
- [ ] Relevant tests were read before source changes.
- [ ] Relevant source files were read before source changes.
- [ ] A focused test was added or updated when behavior was missing.
- [ ] The smallest relevant source change was made.
- [ ] No unrelated files were changed.
- [ ] No new dependency was added unless the issue explicitly required it.
- [ ] Existing public interface names were preserved unless the issue explicitly required a rename.
- [ ] No `.env` or secret file content was read, printed, copied, committed, or exposed.
- [ ] No focused tests were run by Codex.
- [ ] No full tests were run by Codex.
- [ ] Host-side verification requirement was reported honestly.
- [ ] No commit was created by Codex.
- [ ] `<promise>COMPLETE</promise>` was output when the requested source or documentation change was complete and no known source-code blocker remained.

---

## Definition of done

Codex is done only when:

1. The selected issue is understood.
2. The requested behavior is implemented.
3. The behavior is covered by a focused test when appropriate.
4. Test execution was not run by Codex, and host-side verification was reported as required.
5. No unrelated files were intentionally changed.
6. No secrets were exposed.
7. No commit was created by Codex.
8. Codex reports whether host-side verification is still required.
9. Codex outputs:

```text
<promise>COMPLETE</promise>
```

RALPH owns final project verification, commit creation, sync, pull request draft behavior, and issue closing after Codex returns.
