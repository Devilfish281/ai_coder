# Plan: 003-load-defaults-and-env-values-into-setup-config-py

## Issue

`003-load-defaults-and-env-values-into-setup-config-py`

## Parent PRD

`ai_code_prd_rev_3.md`

## Blocked by

`issues/002-define-setup-config-py-runtime-model.md`

Do not start coding this issue until issue 002 is complete, merged, or intentionally unblocked.

---

## Goal

Add the first configuration-loading path for AI Code / RALPH:

1. Load safe defaults first.
2. Let `.env` values override those defaults.
3. Build the final `setup_config.py` runtime object.
4. Validate the final values before CLI overrides are applied.
5. Prove the behavior with tests.

This issue should stay small. It should not redesign the whole configuration system.

---

## Current state

`setup_config.py` already has:

- default constants such as `DEFAULT_PROJECT_NAME`, `DEFAULT_GITHUB_REPO`, `DEFAULT_AGENT_NAME`, `DEFAULT_TEST_COMMAND`, and `DEFAULT_COMMIT_MESSAGE_TEMPLATE`;
- `load_dotenv_once()`;
- `get_env()`;
- `env_bool()`;
- `env_int()`;
- `resolve_github_issue_path()`;
- `validate_initialization()`;
- singleton-style access through `c_setup_config.get_instance()`.

The main missing piece is clear test coverage proving:

- default-only loading works;
- `.env` or environment values override defaults;
- missing optional values fall back safely;
- invalid values fail with clear errors.

---

## Desired runtime loading order

The Release 1 loading order should be:

```text
default constants
        ↓
.env values loaded into environment
        ↓
setup_config.py fields read environment or defaults
        ↓
validate_initialization()
        ↓
main.py applies CLI overrides later
        ↓
validate_initialization() can run again after CLI overrides
```

For this issue, focus on the first validation point:

```text
defaults + .env → setup_config.py → validation
```

CLI override behavior belongs mostly to issue 002 and `main.py`.

---

## Files likely changed

Expected files:

```text
src/ai_coder/setup_config.py
src/ai_coder/my_utils/env_loader.py
tests/setup_config/test_setup_config.py
src/issues/003-load-defaults-and-env-values-into-setup-config-py.md
```

Possible files:

```text
.ai_coder/.env.example
README.md
```

Do not change unrelated runtime modules unless a failing test proves it is needed.

---

## Implementation strategy

### Step 1: Add the issue markdown file

Create this file:

```text
src/issues/003-load-defaults-and-env-values-into-setup-config-py.md
```

Paste the original issue text into it.

Keep the acceptance criteria unchecked until the work is done.

---

### Step 2: Add tests first

Open:

```text
tests/setup_config/test_setup_config.py
```

Add tests for default-only loading and environment override loading.

Use `monkeypatch` to control environment variables.

Important test setup pattern:

```python
c_setup_config._instance = None
```

Use that before calling:

```python
config = c_setup_config.get_instance()
```

This makes sure each test gets a fresh config object.

---

## Test plan

### Test 1: default-only loading works

Add a test named:

```python
test_setup_config_loads_safe_defaults_when_env_values_are_missing
```

Purpose:

Prove that missing optional values fall back to safe defaults.

Test idea:

- remove optional env vars with `monkeypatch.delenv(...)`;
- set only required filesystem paths needed for validation, if needed;
- create a temporary prompt file;
- instantiate a fresh config;
- assert default values are used.

Expected default values:

```text
project_name = "AI Code"
github_repo = "Devilfish281/ai_coder"
default_agent = "mock"
dry_run = True
test_command = "poetry run pytest"
commit_message_template = "RALPH: issue #{issue_number} - {issue_title}"
max_iterations = 3
sandbox_mode = "local"
```

---

### Test 2: env values override defaults

Add a test named:

```python
test_setup_config_env_values_override_defaults
```

Purpose:

Prove `.env`-style environment values override default constants.

Test env values:

```text
PROJECT_NAME=Custom AI Code
GITHUB_REPO=Devilfish281/custom_ai_coder
RALPH_AGENT=mock
DRY_RUN=false
TEST_COMMAND=pytest
COMMIT_MESSAGE_TEMPLATE=RALPH: custom issue #{issue_number}
MAX_ITERATIONS=5
RALPH_SANDBOX_MODE=local
```

Expected result:

`config` should contain the override values, not the default values.

---

### Test 3: validation accepts valid loaded config

Add a test named:

```python
test_setup_config_validate_initialization_accepts_valid_loaded_values
```

Purpose:

Prove the loaded config can pass validation.

Test setup:

- create a temporary repo path;
- create a temporary prompt file;
- set `REPO_PATH` to the temporary repo path;
- set `PROMPT_PATH` to the temporary prompt file;
- set valid optional env values;
- instantiate fresh config;
- call `config.validate_initialization()`.

Expected result:

No exception is raised.

---

### Test 4: missing optional values use safe defaults

Add a test named:

```python
test_setup_config_missing_optional_values_use_safe_defaults
```

Purpose:

Prove optional values do not cause a crash when missing.

Optional values to remove:

```text
PROJECT_NAME
GITHUB_REPO
RALPH_AGENT
DRY_RUN
TEST_COMMAND
COMMIT_MESSAGE_TEMPLATE
MAX_ITERATIONS
RALPH_SANDBOX_MODE
```

Expected result:

The config uses safe defaults.

---

### Test 5: invalid env integer gives clear error

Add a test named:

```python
test_setup_config_invalid_env_int_has_clear_error
```

Test setup:

```text
MAX_ITERATIONS=not-a-number
```

Expected error:

```text
MAX_ITERATIONS must be an integer.
```

This may require improving `env_int()`.

---

### Test 6: invalid sandbox mode fails validation

Add a test named:

```python
test_setup_config_invalid_sandbox_mode_fails_validation
```

Test setup:

```text
RALPH_SANDBOX_MODE=cloud
```

Expected error:

```text
RALPH_SANDBOX_MODE must be 'local' or 'docker'.
```

---

### Test 7: invalid agent fails validation

Add a test named:

```python
test_setup_config_invalid_agent_fails_validation
```

Test setup:

```text
RALPH_AGENT=codex
```

Expected error:

```text
RALPH_AGENT must be 'mock' for Release 1.
```

---

## Code changes

### Change 1: Keep `load_dotenv_once()` as the loading seam

Keep this module:

```text
src/ai_coder/my_utils/env_loader.py
```

Current function:

```python
def load_dotenv_once(*, override: bool = False) -> bool:
```

Keep the default behavior:

```python
override=False
```

Reason:

Real environment variables should usually win over `.env` values.

For tests, prefer `monkeypatch.setenv()` instead of forcing dotenv reloads from real files.

---

### Change 2: Improve `env_int()`

In:

```text
src/ai_coder/setup_config.py
```

Change:

```python
@staticmethod
def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return int(raw.strip().strip("'\""))
```

To:

```python
@staticmethod
def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default

    cleaned_value = raw.strip().strip("'\"")

    try:
        return int(cleaned_value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer.") from error
```

Why:

This turns a raw Python `ValueError` into a clear user-facing config error.

---

### Change 3: Make `env_bool()` stricter only if tests require it

Current behavior:

```python
return raw.strip().lower() in {"1", "true", "yes", "y", "on"}
```

This means any unknown value becomes `False`.

For this issue, keep it unless you want stricter validation.

Optional future behavior:

```text
true values: 1, true, yes, y, on
false values: 0, false, no, n, off
invalid values: clear ValueError
```

Do not add this stricter behavior unless you add tests for it.

---

### Change 4: Make defaults explicit in `to_dict()`

Make sure `to_dict()` includes these loaded runtime values:

```text
project_name
repo_path
github_repo
default_agent
dry_run
test_command
commit_message_template
issue_number
issue_title
issue_body
github_issue_path
label
max_iterations
prompt_path
sandbox_mode
testing_flag
openai_model
```

If `sandbox_mode` is missing from `to_dict()`, add it.

---

### Change 5: Keep validation in `validate_initialization()`

Validation should continue checking:

```text
PROJECT_NAME cannot be empty.
REPO_PATH must exist.
GITHUB_REPO cannot be empty.
RALPH_AGENT must be 'mock' for Release 1.
TEST_COMMAND cannot be empty.
COMMIT_MESSAGE_TEMPLATE cannot be empty.
MAX_ITERATIONS must be at least 1.
OPENAI_MODEL cannot be empty.
PROMPT_PATH must exist.
RALPH_SANDBOX_MODE must be 'local' or 'docker'.
```

Do not require Docker files unless `require_docker=True`.

Do not require OpenAI API key unless `require_llm=True`.

---

## Recommended test helper

To avoid repeating setup in every test, add a small private helper in:

```text
tests/setup_config/test_setup_config.py
```

Example:

```python
def _fresh_config(monkeypatch, tmp_path):
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("prompt", encoding="utf-8")

    monkeypatch.setenv("REPO_PATH", str(tmp_path))
    monkeypatch.setenv("PROMPT_PATH", str(prompt_file))

    c_setup_config._instance = None
    return c_setup_config.get_instance()
```

Keep it private because it is only for tests.

---

## Commands to run

Run setup config tests first:

```powershell
poetry run pytest tests/setup_config/test_setup_config.py
```

Then run main tests:

```powershell
poetry run pytest tests/main/test_main.py
```

Then run all tests:

```powershell
poetry run pytest
```

Expected result:

```text
all tests passed
```

---

## Acceptance criteria checklist

When finished, update this issue file:

```text
src/issues/003-load-defaults-and-env-values-into-setup-config-py.md
```

Change:

```markdown
- [ ] Defaults are loaded into setup_config.py.
- [ ] .env values can override defaults.
- [ ] Validation runs after default and .env loading.
- [ ] Missing optional values fall back to safe defaults.
- [ ] Tests cover default-only loading and .env override loading.
```

To:

```markdown
- [x] Defaults are loaded into setup_config.py.
- [x] .env values can override defaults.
- [x] Validation runs after default and .env loading.
- [x] Missing optional values fall back to safe defaults.
- [x] Tests cover default-only loading and .env override loading.
```

Only check these boxes after tests pass.

---

## Git workflow

Create a branch:

```powershell
git switch main
git pull
git switch -c issue-003-load-defaults-and-env-values-into-setup-config-py
```

After coding:

```powershell
poetry run pytest
git status
git add src/ai_coder/setup_config.py
git add src/ai_coder/my_utils/env_loader.py
git add tests/setup_config/test_setup_config.py
git add src/issues/003-load-defaults-and-env-values-into-setup-config-py.md
git commit -m "RALPH: issue #3 - load defaults and env values into setup_config"
git push -u origin issue-003-load-defaults-and-env-values-into-setup-config-py
```

Only add files that actually changed.

---

## Pull request

PR title:

```text
Load defaults and env values into setup_config.py
```

PR body:

````markdown
Closes #3

## Summary

Loads Release 1 defaults and `.env` values into `setup_config.py`, then validates the resulting runtime configuration.

## Changes

- Confirmed default values load into `setup_config.py`.
- Confirmed environment values override defaults.
- Improved invalid integer config errors.
- Added tests for default-only loading and env override loading.

## Verification

```powershell
poetry run pytest
```
````

```

---

## Definition of done

This issue is complete when:

- `setup_config.py` loads defaults safely;
- environment values override defaults;
- validation runs successfully after loading;
- invalid loaded values produce clear errors;
- tests prove default-only and env override behavior;
- `poetry run pytest` passes;
- one `RALPH:` commit is pushed;
- the PR includes `Closes #3`.
```
