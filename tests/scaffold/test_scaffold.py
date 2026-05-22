# test/scaffold/test_scaffold.py
from __future__ import annotations

from pathlib import Path

from ai_coder.display import SilentDisplay, i_display_scaffold_result
from ai_coder.scaffold import i_scaffold_create
from ai_coder.setup_config import DEFAULT_DOCKER_IMAGE_NAME

EXPECTED_SCAFFOLD_FILES = (
    ".ai-code/README.md",
    ".ai-code/.env.example",
    ".ai-code/Dockerfile",
    ".ai-code/prompts/implementation.md",
    ".ai-code/prompts/review.md",
    ".ai-code/prompts/merge.md",
    ".ai-code/standards/coding-standards.md",
)


def test_scaffold_create_creates_ai_code_folder_and_files(tmp_path: Path) -> None:
    result = i_scaffold_create(tmp_path)

    scaffold_root = tmp_path / ".ai-code"

    assert scaffold_root.exists()
    assert scaffold_root.is_dir()
    assert (scaffold_root / "prompts").is_dir()
    assert (scaffold_root / "standards").is_dir()

    for relative_file_path in EXPECTED_SCAFFOLD_FILES:
        assert (tmp_path / relative_file_path).is_file()

    assert "AI Code" in (scaffold_root / "README.md").read_text(encoding="utf-8")
    assert "AI Code" in (scaffold_root / ".env.example").read_text(encoding="utf-8")
    assert result.root_path == scaffold_root.resolve()
    assert result.created_count == len(EXPECTED_SCAFFOLD_FILES)
    assert result.skipped_count == 0
    assert result.overwritten_count == 0
    assert {file_result.action for file_result in result.files} == {"created"}


def test_scaffold_create_skips_existing_files_by_default(tmp_path: Path) -> None:
    readme_path = tmp_path / ".ai-code" / "README.md"
    readme_path.parent.mkdir(parents=True)
    readme_path.write_text("custom user content", encoding="utf-8")

    result = i_scaffold_create(tmp_path)

    readme_result = _find_file_result(result.files, ".ai-code/README.md")

    assert readme_path.read_text(encoding="utf-8") == "custom user content"
    assert readme_result.action == "skipped_existing"
    assert result.created_count == len(EXPECTED_SCAFFOLD_FILES) - 1
    assert result.skipped_count == 1
    assert result.overwritten_count == 0


def test_scaffold_create_overwrites_existing_files_when_explicitly_requested(
    tmp_path: Path,
) -> None:
    readme_path = tmp_path / ".ai-code" / "README.md"
    readme_path.parent.mkdir(parents=True)
    readme_path.write_text("old scaffold content", encoding="utf-8")

    result = i_scaffold_create(tmp_path, overwrite_existing=True)

    readme_result = _find_file_result(result.files, ".ai-code/README.md")

    assert "old scaffold content" not in readme_path.read_text(encoding="utf-8")
    assert "AI Code" in readme_path.read_text(encoding="utf-8")
    assert readme_result.action == "overwritten"
    assert result.overwritten_count == 1


def test_scaffold_create_writes_visible_output_to_display(tmp_path: Path) -> None:
    display = SilentDisplay()

    i_scaffold_create(tmp_path, display=display)
    i_scaffold_create(tmp_path, display=display)
    i_scaffold_create(tmp_path, overwrite_existing=True, display=display)

    output = "\n".join(display.messages)

    assert "AI Code scaffold folder:" in output
    assert ".ai-code" in output
    assert "Created: .ai-code/README.md" in output
    assert "Skipped existing: .ai-code/README.md" in output
    assert "Overwritten: .ai-code/README.md" in output
    assert "Scaffold complete:" in output


def test_display_scaffold_result_formats_visible_output(tmp_path: Path) -> None:
    result = i_scaffold_create(tmp_path)
    display = SilentDisplay()

    i_display_scaffold_result(display, result)

    output = "\n".join(display.messages)

    assert "AI Code scaffold folder:" in output
    assert "Created: .ai-code/README.md" in output
    assert "Scaffold complete:" in output


def test_scaffold_create_second_run_skips_all_existing_files_by_default(
    tmp_path: Path,
) -> None:
    i_scaffold_create(tmp_path)

    readme_path = tmp_path / ".ai-code" / "README.md"
    readme_path.write_text("custom README after first scaffold", encoding="utf-8")

    result = i_scaffold_create(tmp_path)

    assert (
        readme_path.read_text(encoding="utf-8") == "custom README after first scaffold"
    )
    assert result.created_count == 0
    assert result.skipped_count == len(EXPECTED_SCAFFOLD_FILES)
    assert result.overwritten_count == 0
    assert {file_result.action for file_result in result.files} == {"skipped_existing"}


def test_scaffold_create_does_not_touch_existing_ai_coder_folder(
    tmp_path: Path,
) -> None:
    legacy_scaffold_path = tmp_path / ".ai_coder"
    legacy_prompt_path = legacy_scaffold_path / "prompt.md"
    legacy_scaffold_path.mkdir(parents=True)
    legacy_prompt_path.write_text("legacy .ai_coder prompt content", encoding="utf-8")

    result = i_scaffold_create(tmp_path)

    assert (tmp_path / ".ai-code").is_dir()
    assert legacy_scaffold_path.is_dir()
    assert (
        legacy_prompt_path.read_text(encoding="utf-8")
        == "legacy .ai_coder prompt content"
    )
    assert all(
        not file_result.relative_path.as_posix().startswith(".ai_coder/")
        for file_result in result.files
    )


def test_scaffold_create_all_generated_files_use_ai_code_name(
    tmp_path: Path,
) -> None:
    result = i_scaffold_create(tmp_path)

    for file_result in result.files:
        assert "AI Code" in file_result.path.read_text(encoding="utf-8")


def test_scaffold_create_generates_prompt_templates_with_safe_placeholders(
    tmp_path: Path,
) -> None:
    i_scaffold_create(tmp_path)

    prompt_paths = (
        tmp_path / ".ai-code" / "prompts" / "implementation.md",
        tmp_path / ".ai-code" / "prompts" / "review.md",
        tmp_path / ".ai-code" / "prompts" / "merge.md",
    )
    prompt_texts = tuple(
        prompt_path.read_text(encoding="utf-8") for prompt_path in prompt_paths
    )
    combined_prompt_text = "\n".join(prompt_texts)

    safe_placeholders = (
        "{{ISSUE_NUMBER}}",
        "{{ISSUE_TITLE}}",
        "{{ISSUE_LABELS}}",
        "{{ISSUE_BODY}}",
        "{{BRANCH_NAME}}",
        "{{WORKTREE_PATH}}",
        "{{REPOSITORY_CONTEXT}}",
        "{{COMPLETE_TOKEN}}",
    )

    for prompt_path, prompt_text in zip(prompt_paths, prompt_texts, strict=True):
        assert prompt_path.is_file()
        assert "AI Code" in prompt_text

    for safe_placeholder in safe_placeholders:
        assert safe_placeholder in combined_prompt_text


def test_scaffold_prompt_templates_describe_distinct_workflow_purposes(
    tmp_path: Path,
) -> None:
    i_scaffold_create(tmp_path)

    implementation_text = (
        tmp_path / ".ai-code" / "prompts" / "implementation.md"
    ).read_text(encoding="utf-8")
    review_text = (tmp_path / ".ai-code" / "prompts" / "review.md").read_text(
        encoding="utf-8"
    )
    merge_text = (tmp_path / ".ai-code" / "prompts" / "merge.md").read_text(
        encoding="utf-8"
    )

    assert "implementation slice" in implementation_text
    assert "code changes" in implementation_text
    assert "review guidance" in review_text
    assert "public seams" in review_text
    assert "merge notes" in merge_text
    assert "human review" in merge_text


def test_scaffold_prompt_templates_do_not_include_real_secrets_or_command_expansion(
    tmp_path: Path,
) -> None:
    i_scaffold_create(tmp_path)

    prompt_paths = (
        tmp_path / ".ai-code" / "prompts" / "implementation.md",
        tmp_path / ".ai-code" / "prompts" / "review.md",
        tmp_path / ".ai-code" / "prompts" / "merge.md",
    )
    combined_prompt_text = "\n".join(
        prompt_path.read_text(encoding="utf-8") for prompt_path in prompt_paths
    )

    forbidden_template_text = (
        "OPENAI_API_KEY=",
        "ANTHROPIC_API_KEY=",
        "GH_TOKEN=",
        "sk-",
        "!`",
    )

    for forbidden_text in forbidden_template_text:
        assert forbidden_text not in combined_prompt_text


def test_scaffold_create_generates_dockerfile_template(tmp_path: Path) -> None:
    i_scaffold_create(tmp_path)

    dockerfile_path = tmp_path / ".ai-code" / "Dockerfile"
    dockerfile_text = dockerfile_path.read_text(encoding="utf-8")

    assert dockerfile_path.is_file()
    assert "AI Code" in dockerfile_text
    assert "RALPH" in dockerfile_text
    assert "/workspace" in dockerfile_text
    assert DEFAULT_DOCKER_IMAGE_NAME in dockerfile_text


def test_scaffold_env_example_documents_docker_runtime_defaults(  #  Changed Code
    tmp_path: Path,
) -> None:  #  Changed Code
    i_scaffold_create(tmp_path)

    env_example_path = tmp_path / ".ai-code" / ".env.example"
    env_example_text = env_example_path.read_text(encoding="utf-8")

    assert env_example_path.is_file()
    assert "AI Code" in env_example_text
    assert "RALPH" in env_example_text
    assert f"RALPH_DOCKER_IMAGE_NAME={DEFAULT_DOCKER_IMAGE_NAME}" in env_example_text
    assert "RALPH_SANDBOX_MODE=docker" in env_example_text
    assert "RALPH_DOCKER_ENV_ALLOWLIST=PYTHONUNBUFFERED" in env_example_text
    assert "RALPH_DOCKER_SECRET_ENV_ALLOWLIST=" in env_example_text
    assert "Do not put real secrets in this example file." in env_example_text


def test_scaffold_templates_do_not_include_real_secrets(tmp_path: Path) -> None:
    i_scaffold_create(tmp_path)

    dockerfile_text = (tmp_path / ".ai-code" / "Dockerfile").read_text(encoding="utf-8")
    env_example_text = (tmp_path / ".ai-code" / ".env.example").read_text(
        encoding="utf-8"
    )
    template_text = f"{dockerfile_text}\n{env_example_text}"

    forbidden_secret_examples = (
        "OPENAI_API_KEY=",
        "ANTHROPIC_API_KEY=",
        "GH_TOKEN=",
        "sk-",
    )

    for forbidden_secret_example in forbidden_secret_examples:
        assert forbidden_secret_example not in template_text


def test_scaffold_create_preserves_existing_dockerfile_by_default(
    tmp_path: Path,
) -> None:
    dockerfile_path = tmp_path / ".ai-code" / "Dockerfile"
    dockerfile_path.parent.mkdir(parents=True)
    dockerfile_path.write_text("custom Dockerfile content", encoding="utf-8")

    result = i_scaffold_create(tmp_path)

    dockerfile_result = _find_file_result(result.files, ".ai-code/Dockerfile")

    assert dockerfile_path.read_text(encoding="utf-8") == "custom Dockerfile content"
    assert dockerfile_result.action == "skipped_existing"


###############################################################################
# Helper function to find a specific file result by relative path
###############################################################################
def _find_file_result(file_results: tuple[object, ...], relative_path: str) -> object:
    for file_result in file_results:
        if file_result.relative_path.as_posix() == relative_path:
            return file_result

    raise AssertionError(f"Missing scaffold file result: {relative_path}")
