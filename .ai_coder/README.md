# AI Code Template Scaffold Scope

## Confirmed first scaffold folder name

Use this future scaffold folder name:

```text
.ai-code/
```

Do not use this name for the future scaffold folder:

```text
.ai_coder/
```

Reason:

The PRD locks `.ai-code/` as the future scaffold folder for AI Code template scaffolding. The existing `.ai_coder/` folder may remain as an early runtime/project folder, but it is not the confirmed future workflow template scaffold name.

## Confirmed first scaffold file list

The first useful `.ai-code/` workflow template scaffolding slice should be small, readable, and safe.

Confirmed first scaffold files for a later generator:

```text
.ai-code/
├── README.md
├── .env.example
├── prompts/
│   └── implementation.md
├── github_issue_example.md
└── coding_standards.md
```

## Purpose of each first scaffold file

### `.ai-code/README.md`

Purpose:

- Explain what the `.ai-code/` folder is for.
- Explain that it contains workflow helper files for AI Code.
- Explain that generated files are project-local templates.
- Explain that real secrets should not be committed.
- Explain that scaffold files are templates, not proof that automation has already run.

### `.ai-code/.env.example`

Purpose:

- Show safe placeholder configuration names.
- Avoid real secrets.
- Keep early scaffold configuration simple.
- Support later setup/config documentation without changing runtime behavior yet.
- Help users understand which values may eventually feed into `setup_config.py`.

### `.ai-code/prompts/implementation.md`

Purpose:

- Provide the first reusable implementation prompt template.
- Use AI Code and RALPH wording.
- Keep issue title, issue body, labels, and external values as inert text.
- Keep the template focused on one GitHub issue at a time.
- Reinforce small tracer-bullet implementation behavior.

### `.ai-code/github_issue_example.md`

Purpose:

- Provide a safe example issue file for local testing and demos.
- Show issue number, title, body, and labels in a simple format.
- Help future users understand fake or provided issue input.
- Avoid using live GitHub access as a requirement for the first scaffold slice.

### `.ai-code/coding_standards.md`

Purpose:

- Capture AI Code’s small-slice coding rules.
- Remind future generated prompts to avoid unrelated rewrites.
- Keep project rules separate from the implementation prompt.
- Make the generated scaffold easier for a human developer to inspect.

## Current first-slice scaffold items

These items are confirmed for the first future scaffold generator:

```text
.ai-code/README.md
.ai-code/.env.example
.ai-code/prompts/implementation.md
.ai-code/github_issue_example.md
.ai-code/coding_standards.md
```

These files are enough to prove the first scaffold shape without creating a full automation system.

## Future scaffold items

These items are intentionally future work:

```text
.ai-code/
├── Dockerfile
├── config.example.toml
├── runner.py
├── prompts/
│   ├── review.md
│   └── merge.md
├── workflows/
│   └── issue_to_pr.md
└── sandbox/
    └── docker_bind_mount.md
```

## Why future items are not first

### `.ai-code/Dockerfile`

Docker scaffold files should wait until Docker bind-mount behavior is stable.

### `.ai-code/config.example.toml`

A config example should wait until the CLI and `setup_config.py` runtime model are stable enough to document accurately.

### `.ai-code/runner.py`

A generated runner should wait until the CLI entry point and runtime configuration flow are stable.

### `.ai-code/prompts/review.md`

A review prompt should wait until the basic implementation workflow is proven.

### `.ai-code/prompts/merge.md`

A merge prompt should wait until safe commit, PR, and close workflows are implemented.

### `.ai-code/workflows/issue_to_pr.md`

Workflow files should wait until PR draft behavior and issue close behavior are safer and more complete.

### `.ai-code/sandbox/docker_bind_mount.md`

Sandbox-specific scaffold documentation should wait until Docker bind-mount behavior is implemented and tested.
