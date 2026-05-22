# test/scaffold/test_scaffold.py
from __future__ import annotations

from pathlib import Path

from ai_coder.display import SilentDisplay, i_display_scaffold_result
from ai_coder.scaffold import i_scaffold_create

EXPECTED_SCAFFOLD_FILES = (
    ".ai-code/README.md",
    ".ai-code/.env.example",
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


def _find_file_result(file_results: tuple[object, ...], relative_path: str) -> object:
    for file_result in file_results:
        if file_result.relative_path.as_posix() == relative_path:
            return file_result

    raise AssertionError(f"Missing scaffold file result: {relative_path}")
