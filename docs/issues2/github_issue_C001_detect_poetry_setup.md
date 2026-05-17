## ISSUE_BODY

RALPH should add a new setup verification step after the sandbox starts and before prompt-safe repository context is discovered.

Current desired flow:

```text
Step 4: Create a safe working copy using a Git worktree.
Step 5: Start a sandbox or local execution environment.
Step 5a: Detect Poetry, run poetry install, run poetry run pytest.
Step 5b: Discover prompt-safe repository context.
Step 6: Give an AI coding agent a prompt.
```

This catches a fresh-worktree problem early: the worktree exists, but its Poetry environment may not have pytest or other project dependencies installed yet.

## Goal

Add a small Step 5a setup seam that detects Poetry, runs `poetry install`, runs baseline `poetry run pytest`, stops before agent execution if setup fails, preserves the worktree on setup failure, and continues to Step 5b only when setup passes.

## Why this belongs after Step 5

`poetry install` and `poetry run pytest` should run through `sandbox_result.handle.i_sandboxhandle_run()`.

That means RALPH needs the sandbox handle first.

So this should happen after:

```python
logger.info("Step 5: Start a sandbox or local execution environment.")
```

and after `sandbox_result.started` is confirmed.

## Important design decision

Do not remove the existing final Step 9 test run.

This issue creates two different test moments:

1. Step 5a baseline test — runs before the agent edits code.
2. Step 9 final test — runs after the agent finishes, before commit.

## Expected behavior

1. RALPH starts the sandbox.
2. RALPH checks whether the worktree has `pyproject.toml`.
3. If `pyproject.toml` exists, RALPH treats it as a Poetry project candidate.
4. RALPH runs `poetry install` through the sandbox seam.
5. If `poetry install` fails, RALPH stops before agent execution and preserves the worktree.
6. If `poetry install` succeeds, RALPH runs baseline `poetry run pytest` through the sandbox seam.
7. If baseline pytest fails, RALPH stops before agent execution and preserves the worktree.
8. If baseline pytest passes, RALPH continues to Step 5b.
9. Step 5b discovers prompt-safe repository context.
10. RALPH continues to prompt building, agent execution, final tests, commit, and cleanup.

## Recommended status behavior

### `poetry install` fails

Return:

```text
status = "blocked"
completed = False
```

### Baseline `poetry run pytest` fails before agent changes

Return:

```text
status = "blocked"
completed = False
```

### Project is not Poetry

Skip Step 5a Poetry setup and continue.

## Files to change

### Add a project setup module

Create:

```text
src/ai_coder/project_setup/
├── __init__.py
└── project_setup.py
```

Recommended public seam:

```text
i_project_setup_run()
```

Recommended result class:

```text
ProjectSetupResult
```

### Add tests

Create:

```text
tests/project_setup/
├── __init__.py
└── test_project_setup.py
```

Update:

```text
tests/ralph/test_ralph.py
```

## Recommended result object

```text
ProjectSetupResult
- poetry_project: bool
- install_ran: bool
- install_passed: bool
- baseline_tests_ran: bool
- baseline_tests_passed: bool
- blocked: bool
- install_command: tuple[str, ...]
- install_stdout: str
- install_stderr: str
- install_exit_code: int
- baseline_test_command: tuple[str, ...]
- baseline_test_stdout: str
- baseline_test_stderr: str
- baseline_test_exit_code: int
- message: str
```

## Tests to add first

Use Red → Green → Repeat → Refactor.

1. Non-Poetry project skips setup.
2. Poetry project runs `poetry install`.
3. Successful install runs baseline `poetry run pytest`.
4. Failed install blocks before pytest.
5. Failed baseline pytest blocks before agent.
6. RALPH calls Step 5a after sandbox startup.
7. RALPH stops before Step 5b when setup is blocked.
8. RALPH continues to Step 5b when setup passes.

## Acceptance criteria

- [ ] `ralph.py` logs `Step 5: Start a sandbox or local execution environment.`
- [ ] `ralph.py` logs `Step 5a: Detect Poetry, run poetry install, run poetry run pytest.`
- [ ] `ralph.py` logs `Step 5b: Discover prompt-safe repository context.`
- [ ] Step 5a runs only after sandbox startup succeeds.
- [ ] Step 5a runs before prompt-safe repository context discovery.
- [ ] Poetry detection checks for `pyproject.toml` in the worktree.
- [ ] Poetry projects run `poetry install` through the sandbox seam.
- [ ] `poetry run pytest` runs through the sandbox seam after successful install.
- [ ] A failed `poetry install` blocks the run before agent execution.
- [ ] A failed baseline `poetry run pytest` blocks the run before agent execution.
- [ ] Blocked setup preserves the worktree.
- [ ] Blocked setup shows the preserved worktree path.
- [ ] Non-Poetry projects skip Step 5a setup without failing.
- [ ] Existing final Step 9 tests still run after agent completion.
- [ ] RALPH does not commit when Step 5a blocks.
- [ ] RALPH does not close the GitHub issue when Step 5a blocks.
- [ ] Unit tests use fake sandbox handles and do not call real Poetry.

## Manual acceptance checklist

- [ ] Fresh worktree is created.
- [ ] Sandbox starts successfully.
- [ ] Step 5a appears in logs after Step 5.
- [ ] `poetry install` runs before the agent prompt is built.
- [ ] Baseline `poetry run pytest` runs before the agent prompt is built.
- [ ] Step 5b appears after Step 5a succeeds.
- [ ] If install fails, RALPH stops and preserves the worktree.
- [ ] If baseline tests fail, RALPH stops and preserves the worktree.
- [ ] If setup passes, the normal RALPH workflow continues.
- [ ] Final Step 9 tests still run before commit.
- [ ] `poetry run pytest` passes for the full test suite.

## Test command

```powershell
poetry run pytest
```

If Poetry is unavailable:

```powershell
pytest
```

Do not use:

```powershell
python -m pytest --capture=tee-sys
```

## Recommended commit message after implementation

```text
RALPH: issue #<issue-number> - add Poetry setup baseline before prompt context

- Detect Poetry projects after sandbox startup
- Run poetry install through the sandbox seam
- Run baseline poetry run pytest before agent edits
- Preserve worktree when setup or baseline tests fail
- Keep final pytest verification before commit
```
