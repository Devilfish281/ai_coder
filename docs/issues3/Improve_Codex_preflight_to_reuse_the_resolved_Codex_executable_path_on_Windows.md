# Improve Codex preflight to reuse the resolved Codex executable path on Windows

## Add a title

Improve Codex preflight to reuse the resolved Codex executable path on Windows

## Add a description

### Problem

On Windows, `CODEX_COMMAND=codex` can be available on `PATH`, but the Codex preflight readiness command can still fail if the code only checks whether `shutil.which("codex")` returns something and then throws away the resolved path.

Example local proof:

```powershell
where.exe codex
poetry run python -c "import shutil; print(shutil.which('codex'))"
poetry run python -c "import subprocess; print(subprocess.run([r'C:\Users\ME\AppData\Roaming\npm\codex.cmd', '--version'], capture_output=True, text=True).stdout)"
```

Observed successful lookup:

```text
C:\Users\ME\AppData\Roaming\npm\codex.CMD
codex-cli 0.133.0
```

But preflight can still report:

```text
Codex preflight blocked: Codex executable was not found: 'codex'.
Details: [WinError 2] The system cannot find the file specified
```

This happens because the preflight can prove that `codex` exists, but then run the readiness command with the original unresolved command name instead of the resolved `.CMD` wrapper path.

### Why this matters

AI Code targets Windows 11 first. Codex is installed through npm-style command wrappers on Windows, so the stable command may be the resolved `codex.CMD` path rather than the extensionless `codex` name.

RALPH should not block a Codex smoke proof when:

1. `CODEX_COMMAND=codex` is configured.
2. `shutil.which("codex")` resolves to a real executable wrapper.
3. The resolved wrapper succeeds with `--version`.

This keeps the Codex preflight read-only while making it more reliable on Windows.

### Scope

Change only the Codex preflight path-resolution behavior and related tests.

In scope:

- Keep the public interface `i_codex_preflight_check()` unchanged.
- Resolve the configured Codex command once before running the readiness command.
- Reuse the resolved executable path when building the version command.
- Preserve the original configured `codex_command` value in `CodexPreflightResult.codex_command`.
- Store the actual command that was run in `CodexPreflightResult.version_command`.
- Preserve the injected `executable_finder` seam for tests.
- Preserve the injected `command_runner` seam for tests.
- Keep preflight read-only.
- Keep `subprocess.run()` using argument lists.
- Do not use `shell=True`.

Out of scope:

- Do not call the Codex model.
- Do not start RALPH’s real agent loop.
- Do not create worktrees.
- Do not edit project files outside the targeted preflight code and tests.
- Do not create commits from inside preflight.
- Do not create pull requests.
- Do not close GitHub issues.
- Do not add new dependencies.

### Desired behavior

When `CODEX_COMMAND=codex` and the executable finder resolves it to:

```text
C:\Users\ME\AppData\Roaming\npm\codex.CMD
```

the readiness command should be:

```python
[
    "C:\\Users\\ME\\AppData\\Roaming\\npm\\codex.CMD",
    "--version",
]
```

not:

```python
[
    "codex",
    "--version",
]
```

When `CODEX_COMMAND` is already a real path such as:

```text
C:\Users\ME\AppData\Roaming\npm\codex.cmd
```

preflight should use that path directly.

When the command cannot be resolved, preflight should return a blocked result before trying to run `codex --version`.

### Suggested implementation plan

#### Step 1 — Read the current tests

Read:

```text
tests/codex_preflight/test_codex_preflight.py
```

Identify the tests that currently expect:

```python
("codex", "--version")
```

These expectations should change only where the executable finder resolves `codex` to a concrete path.

#### Step 2 — Add a failing Windows-style resolver test

Add or update a test proving this behavior:

1. Config uses `codex_command="codex"`.
2. Fake executable finder returns `r"C:\Users\ME\AppData\Roaming\npm\codex.CMD"`.
3. Fake command runner receives:

```python
[
    r"C:\Users\ME\AppData\Roaming\npm\codex.CMD",
    "--version",
]
```

4. Result is ready.
5. Result keeps `codex_command == "codex"`.
6. Result exposes the resolved command in `version_command`.

#### Step 3 — Add or confirm missing-command behavior

Confirm there is still a test proving:

1. Config uses `codex_command="codex"`.
2. Fake executable finder returns `None`.
3. Command runner is not called.
4. Result is blocked.
5. Message clearly says the Codex executable was not found.

#### Step 4 — Add or confirm explicit-path behavior

Add or confirm a test proving:

1. Config uses a path-like command such as `r"C:\Tools\codex.cmd"`.
2. The path exists in the test setup.
3. Preflight uses that path directly.
4. The readiness command appends only `--version`.

#### Step 5 — Implement the smallest resolver

Add a private helper if needed:

```text
_resolve_codex_executable_command()
```

The helper should:

1. Return the original command when it already looks like a path and exists.
2. Return an empty string when it looks like a path and does not exist.
3. Use the injected executable finder or `shutil.which`.
4. Return the resolved path string from the finder.
5. Return an empty string if nothing is found.

#### Step 6 — Use the resolved command for readiness

Update `i_codex_preflight_check()` so it:

1. Cleans the configured Codex command.
2. Resolves the executable command.
3. Blocks if no executable is resolved.
4. Builds the version command from the resolved executable command.
5. Runs the readiness command through the existing command-runner seam.

#### Step 7 — Preserve result meaning

Keep these result fields clear:

```text
codex_command
version_command
```

Expected meaning:

- `codex_command`: the user-configured command value, such as `codex`.
- `version_command`: the exact command preflight attempted to run, such as `C:\Users\ME\AppData\Roaming\npm\codex.CMD --version`.

#### Step 8 — Keep command safety

Do not use:

```python
shell=True
```

Continue passing command arguments as a list so no shell parsing is needed.

#### Step 9 — Run focused tests

Run:

```powershell
poetry run pytest tests/codex_preflight/test_codex_preflight.py
```

Expected result:

```text
all tests pass
```

#### Step 10 — Run full tests

Run:

```powershell
poetry run pytest
```

Expected result:

```text
all tests pass
```

### Acceptance criteria

- [ ] `CODEX_COMMAND=codex` can resolve to a Windows `.CMD` wrapper path through `shutil.which()` or the injected executable finder.
- [ ] Preflight uses the resolved executable path when building the readiness command.
- [ ] `CodexPreflightResult.codex_command` keeps the original configured value.
- [ ] `CodexPreflightResult.version_command` shows the exact command that was run.
- [ ] Missing Codex executable still returns `blocked`.
- [ ] Missing Codex executable does not call the command runner.
- [ ] Explicit path-like Codex commands still work.
- [ ] The preflight remains read-only.
- [ ] The preflight does not call the Codex model.
- [ ] The implementation does not use `shell=True`.
- [ ] Focused Codex preflight tests pass.
- [ ] Full `poetry run pytest` passes.

### Manual acceptance checklist

After tests pass, confirm:

- [ ] `where.exe codex` shows the npm Codex command folder.
- [ ] `poetry run python -c "import shutil; print(shutil.which('codex'))"` returns a concrete path such as `codex.CMD`.
- [ ] Running the Codex preflight with `CODEX_COMMAND=codex` no longer blocks with `[WinError 2]`.
- [ ] The preflight result has `ready=True`.
- [ ] The preflight result has `blocked=False`.
- [ ] The preflight result includes `version_output` similar to `codex-cli 0.133.0`.
- [ ] The preflight result `version_command` uses the resolved executable path.

### Labels

tracer bullet, polish, Sandcastle
