# src/ai_coder/scaffold/scaffold.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


from typing import Protocol

from ai_coder.display import DisplayProtocol, i_display_scaffold_result

SCAFFOLD_FOLDER_NAME = ".ai-code"
ACTION_CREATED = "created"
ACTION_SKIPPED_EXISTING = "skipped_existing"
ACTION_OVERWRITTEN = "overwritten"


@dataclass(frozen=True)
class ScaffoldFileResult:
    path: Path
    relative_path: Path
    action: str
    message: str


@dataclass(frozen=True)
class ScaffoldResult:
    root_path: Path
    files: tuple[ScaffoldFileResult, ...]
    message: str

    @property
    def created_count(self) -> int:
        return _count_file_actions(self.files, ACTION_CREATED)

    @property
    def skipped_count(self) -> int:
        return _count_file_actions(self.files, ACTION_SKIPPED_EXISTING)

    @property
    def overwritten_count(self) -> int:
        return _count_file_actions(self.files, ACTION_OVERWRITTEN)


@dataclass(frozen=True)
class _ScaffoldTemplate:
    relative_path: Path
    content: str


def i_scaffold_create(
    project_root: str | Path,
    overwrite_existing: bool = False,
    display: DisplayProtocol | None = None,
) -> ScaffoldResult:
    project_root_path = Path(project_root).expanduser().resolve()

    if not project_root_path.exists():
        raise FileNotFoundError(f"Project root does not exist: {project_root_path}")

    if not project_root_path.is_dir():
        raise NotADirectoryError(
            f"Project root is not a directory: {project_root_path}"
        )

    scaffold_root = project_root_path / SCAFFOLD_FOLDER_NAME
    scaffold_root.mkdir(parents=True, exist_ok=True)

    file_results: list[ScaffoldFileResult] = []

    for scaffold_template in _default_scaffold_files():
        file_result = _write_scaffold_file(
            project_root_path=project_root_path,
            scaffold_template=scaffold_template,
            overwrite_existing=overwrite_existing,
        )
        file_results.append(file_result)

    file_result_tuple = tuple(file_results)
    result = ScaffoldResult(
        root_path=scaffold_root.resolve(),
        files=file_result_tuple,
        message=_scaffold_complete_message(file_result_tuple),
    )

    if display is not None:
        i_display_scaffold_result(display, result)

    return result


def _write_scaffold_file(
    *,
    project_root_path: Path,
    scaffold_template: _ScaffoldTemplate,
    overwrite_existing: bool,
) -> ScaffoldFileResult:
    target_path = project_root_path / scaffold_template.relative_path
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if target_path.exists() and target_path.is_dir():
        return ScaffoldFileResult(
            path=target_path,
            relative_path=scaffold_template.relative_path,
            action=ACTION_SKIPPED_EXISTING,
            message=f"Skipped existing: {scaffold_template.relative_path.as_posix()}",
        )

    if target_path.exists() and not overwrite_existing:
        return ScaffoldFileResult(
            path=target_path,
            relative_path=scaffold_template.relative_path,
            action=ACTION_SKIPPED_EXISTING,
            message=f"Skipped existing: {scaffold_template.relative_path.as_posix()}",
        )

    action = ACTION_OVERWRITTEN if target_path.exists() else ACTION_CREATED
    target_path.write_text(scaffold_template.content, encoding="utf-8")

    return ScaffoldFileResult(
        path=target_path,
        relative_path=scaffold_template.relative_path,
        action=action,
        message=_file_action_message(action, scaffold_template.relative_path),
    )


def _default_scaffold_files() -> tuple[_ScaffoldTemplate, ...]:
    return (
        _ScaffoldTemplate(
            relative_path=Path(SCAFFOLD_FOLDER_NAME) / "README.md",
            content=_readme_template(),
        ),
        _ScaffoldTemplate(
            relative_path=Path(SCAFFOLD_FOLDER_NAME) / ".env.example",
            content=_env_example_template(),
        ),
        _ScaffoldTemplate(
            relative_path=Path(SCAFFOLD_FOLDER_NAME) / "Dockerfile",
            content=_dockerfile_template(),
        ),
        _ScaffoldTemplate(
            relative_path=Path(SCAFFOLD_FOLDER_NAME) / "prompts" / "implementation.md",
            content=_implementation_prompt_template(),
        ),
        _ScaffoldTemplate(
            relative_path=Path(SCAFFOLD_FOLDER_NAME) / "prompts" / "review.md",
            content=_review_prompt_template(),
        ),
        _ScaffoldTemplate(
            relative_path=Path(SCAFFOLD_FOLDER_NAME) / "prompts" / "merge.md",
            content=_merge_prompt_template(),
        ),
        _ScaffoldTemplate(
            relative_path=Path(SCAFFOLD_FOLDER_NAME)
            / "standards"
            / "coding-standards.md",
            content=_coding_standards_template(),
        ),
    )


def _readme_template() -> str:
    return """# AI Code scaffold

This folder contains project-specific AI Code workflow scaffolding.

RALPH is the coding agent inside AI Code. These files are safe text templates for human review before future automation uses them.

## Files

- `prompts/implementation.md` describes how implementation work should be guided.
- `prompts/review.md` describes how review work should be guided.
- `prompts/merge.md` describes how merge preparation should be guided.
- `standards/coding-standards.md` records local coding expectations.
- `.env.example` documents safe example settings only.

Do not store real secrets in this folder.
"""


def _env_example_template() -> str:
    return """# AI Code example environment values

# Safe starter values for local AI Code scaffold files.
# RALPH is the single-issue coding agent inside AI Code.
# Copy this file to .env only after reviewing each value.
# Do not put real secrets in this example file.

AI_CODE_PROJECT_NAME="AI Code"
AI_CODE_WORKFLOW_NAME="single-issue"
AI_CODE_AGENT_NAME="RALPH"

# Docker sandbox template guidance.
# This image name should match setup_config.py DEFAULT_DOCKER_IMAGE_NAME.
RALPH_SANDBOX_MODE=docker
RALPH_DOCKER_IMAGE_NAME=ai-code-ralph-test-runtime:latest
RALPH_DOCKER_ENV_ALLOWLIST=PYTHONUNBUFFERED

# Keep this empty until a later approved workflow explicitly needs secrets.
# Real secret values belong in your private .env file, not in .env.example.
RALPH_DOCKER_SECRET_ENV_ALLOWLIST=

"""


def _dockerfile_template() -> str:
    return """# AI Code RALPH Docker runtime template

# Expected image tag:
# ai-code-ralph-test-runtime:latest
#
# Manual build command:
# docker build -f .ai-code/Dockerfile -t ai-code-ralph-test-runtime:latest .
#
# This starter image is for the AI Code Docker bind-mount runtime.
# RALPH should run project commands with the repository mounted at /workspace.
# Do not put real secrets in this Dockerfile.

FROM python:3.12-slim

LABEL org.opencontainers.image.title="AI Code RALPH runtime"
LABEL org.opencontainers.image.description="Starter runtime image for AI Code scaffold workflows"
LABEL ai-code.image.tag="ai-code-ralph-test-runtime:latest"

ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

CMD ["python", "--version"]
"""


def _implementation_prompt_template() -> str:
    return """# AI Code implementation prompt

Use this prompt when RALPH is preparing a small implementation slice.

## Guidance

- Read the issue and relevant tests first.
- Keep the change small.
- Preserve public seams unless the issue requires a change.
- Run the configured tests before marking the work complete.
"""


def _review_prompt_template() -> str:
    return """# AI Code review prompt

Use this prompt when RALPH is reviewing a completed implementation slice.

## Guidance

- Check that the change matches the issue.
- Check that generated files use AI Code naming.
- Check that existing user files were not overwritten unexpectedly.
- Check that tests cover observable behavior through public seams.
"""


def _merge_prompt_template() -> str:
    return """# AI Code merge prompt

Use this prompt when RALPH is preparing human-readable merge notes.

## Guidance

- Summarize the issue completed.
- Summarize the files changed.
- Summarize the test command and result.
- Leave final repository actions for human review unless a later approved workflow enables them.
"""


def _coding_standards_template() -> str:
    return """# AI Code coding standards

## Python style

- Prefer small, readable Python modules.
- Use clear public interface seams.
- Keep implementation details private.
- Write tests for behavior, not private implementation details.
- Avoid new dependencies unless the issue clearly requires them.
- Keep generated scaffold content safe and free of real secrets.
"""


def _file_action_message(action: str, relative_path: Path) -> str:
    display_path = relative_path.as_posix()

    if action == ACTION_OVERWRITTEN:
        return f"Overwritten: {display_path}"

    return f"Created: {display_path}"


def _scaffold_complete_message(file_results: tuple[ScaffoldFileResult, ...]) -> str:
    created_count = _count_file_actions(file_results, ACTION_CREATED)
    skipped_count = _count_file_actions(file_results, ACTION_SKIPPED_EXISTING)
    overwritten_count = _count_file_actions(file_results, ACTION_OVERWRITTEN)

    return (
        "Scaffold complete: "
        f"{created_count} created, "
        f"{skipped_count} skipped, "
        f"{overwritten_count} overwritten."
    )


def _count_file_actions(
    file_results: tuple[ScaffoldFileResult, ...],
    action: str,
) -> int:
    return sum(file_result.action == action for file_result in file_results)
