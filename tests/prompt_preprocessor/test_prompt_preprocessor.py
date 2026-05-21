# tests/prompt_preprocessor/test_prompt_preprocessor.py
from ai_coder.prompt_preprocessor import i_prompt_preprocess


def test_prompt_preprocess_replaces_placeholders() -> None:
    raw_prompt = "Issue #{{ISSUE_NUMBER}}: {{ISSUE_TITLE}}"

    result = i_prompt_preprocess(
        raw_prompt,
        {
            "ISSUE_NUMBER": 7,
            "ISSUE_TITLE": "Build local RALPH loop",
        },
    )

    assert result == "Issue #7: Build local RALPH loop"


def test_prompt_preprocess_does_not_execute_shell_text_from_values() -> None:
    raw_prompt = "Body: {{ISSUE_BODY}}"

    result = i_prompt_preprocess(raw_prompt, {"ISSUE_BODY": "!`echo unsafe`"})

    assert result == "Body: !`echo unsafe`"


def test_prompt_preprocess_replaces_all_safe_placeholders() -> None:
    raw_prompt = (
        "Issue: {{ISSUE_NUMBER}}\n"
        "Title: {{ISSUE_TITLE}}\n"
        "Body: {{ISSUE_BODY}}\n"
        "Labels: {{ISSUE_LABELS}}\n"
        "Branch: {{BRANCH_NAME}}\n"
        "Worktree: {{WORKTREE_PATH}}"
    )

    result = i_prompt_preprocess(
        raw_prompt,
        {
            "ISSUE_NUMBER": 18,
            "ISSUE_TITLE": "Add sandbox-aware prompt preprocessing",
            "ISSUE_BODY": "Preprocess after sandbox startup.",
            "ISSUE_LABELS": "tracer bullet, Sandcastle",
            "BRANCH_NAME": "ralph-issue-18-add-sandbox-aware-prompt-preprocessing",
            "WORKTREE_PATH": r"C:\repo\.ai_coder\worktrees\issue-18",
        },
    )

    assert "Issue: 18" in result
    assert "Title: Add sandbox-aware prompt preprocessing" in result
    assert "Body: Preprocess after sandbox startup." in result
    assert "Labels: tracer bullet, Sandcastle" in result
    assert "Branch: ralph-issue-18-add-sandbox-aware-prompt-preprocessing" in result
    assert r"Worktree: C:\repo\.ai_coder\worktrees\issue-18" in result


def test_prompt_preprocess_leaves_unknown_placeholders_unchanged() -> None:
    raw_prompt = "Known: {{ISSUE_NUMBER}}\nUnknown: {{NOT_DEFINED}}"

    result = i_prompt_preprocess(raw_prompt, {"ISSUE_NUMBER": 18})

    assert result == "Known: 18\nUnknown: {{NOT_DEFINED}}"


def test_prompt_preprocess_converts_none_values_to_empty_text() -> None:
    raw_prompt = "Branch: {{BRANCH_NAME}}"

    result = i_prompt_preprocess(raw_prompt, {"BRANCH_NAME": None})

    assert result == "Branch: "
    assert "None" not in result


def test_prompt_preprocess_keeps_missing_placeholder_predictable() -> None:
    raw_prompt = "Branch: {{BRANCH_NAME}}\nWorktree: {{WORKTREE_PATH}}"

    result = i_prompt_preprocess(raw_prompt, {"BRANCH_NAME": "ralph-issue-18"})

    assert result == "Branch: ralph-issue-18\nWorktree: {{WORKTREE_PATH}}"


# 019 tests for security and special character handling
def test_prompt_preprocess_treats_issue_title_shell_syntax_as_text() -> None:
    raw_prompt = "Title: {{ISSUE_TITLE}}"
    issue_title = (
        'Fix literal !`echo title` $(Write-Output "title") '
        '&& echo done | findstr "done"'
    )

    result = i_prompt_preprocess(
        raw_prompt,
        {
            "ISSUE_TITLE": issue_title,
        },
    )

    assert result == f"Title: {issue_title}"


def test_prompt_preprocess_treats_issue_body_shell_syntax_as_text_without_side_effects(
    tmp_path,
) -> None:
    sentinel_file = tmp_path / "prompt_preprocess_should_not_create_this.txt"
    raw_prompt = "Body:\n{{ISSUE_BODY}}"
    issue_body = (
        "Keep this body literal: "
        f"!`python -c \"from pathlib import Path; Path({str(sentinel_file)!r}).write_text('created')\"` "
        "&& echo body | more"
    )

    result = i_prompt_preprocess(
        raw_prompt,
        {
            "ISSUE_BODY": issue_body,
        },
    )

    assert result == f"Body:\n{issue_body}"
    assert sentinel_file.exists() is False


def test_prompt_preprocess_treats_issue_labels_special_characters_as_text() -> None:
    raw_prompt = "Labels: {{ISSUE_LABELS}}"
    issue_labels = (
        r"label:needs-review, windows path C:\Temp\A&B, pipe | label, "
        r'quote "label", percent %PATH%, caret ^'
    )

    result = i_prompt_preprocess(
        raw_prompt,
        {
            "ISSUE_LABELS": issue_labels,
        },
    )

    assert result == f"Labels: {issue_labels}"


def test_prompt_preprocess_preserves_long_untrusted_issue_body() -> None:
    raw_prompt = "Body:\n{{ISSUE_BODY}}"
    repeated_line = (
        "This is literal issue text with !`echo chunk`, "
        '$(Write-Output "chunk"), &&, |, ^, and %USERNAME%.\n'
    )
    long_issue_body = repeated_line * 60
    expected_result = f"Body:\n{long_issue_body}"

    result = i_prompt_preprocess(
        raw_prompt,
        {
            "ISSUE_BODY": long_issue_body,
        },
    )

    assert result == expected_result
    assert len(result) == len(expected_result)
    assert result.count("!`echo chunk`") == 60
    assert '$(Write-Output "chunk")' in result


def test_prompt_preprocess_preserves_windows_special_characters_as_text() -> None:
    raw_prompt = "Windows text: {{ISSUE_BODY}}"
    windows_text = (
        r"C:\Temp\RALPH Folder\file name (draft)^2 "
        r'& echo literal | findstr "literal" %USERNAME%'
    )

    result = i_prompt_preprocess(
        raw_prompt,
        {
            "ISSUE_BODY": windows_text,
        },
    )

    assert result == f"Windows text: {windows_text}"


def test_prompt_preprocess_does_not_reprocess_placeholders_from_values() -> None:
    raw_prompt = (
        "Title: {{ISSUE_TITLE}}\n"
        "Body: {{ISSUE_BODY}}\n"
        "Labels: {{ISSUE_LABELS}}\n"
        "Done: {{COMPLETE_TOKEN}}"
    )

    result = i_prompt_preprocess(
        raw_prompt,
        {
            "ISSUE_TITLE": "Fix literal {{ISSUE_BODY}}",
            "ISSUE_BODY": "Body contains literal {{COMPLETE_TOKEN}}",
            "ISSUE_LABELS": "label {{WORKTREE_PATH}}",
            "COMPLETE_TOKEN": "<promise>COMPLETE</promise>",
            "WORKTREE_PATH": r"C:\repo\.ai_coder\worktrees\issue-47",
        },
    )

    assert "Title: Fix literal {{ISSUE_BODY}}" in result
    assert "Body: Body contains literal {{COMPLETE_TOKEN}}" in result
    assert "Labels: label {{WORKTREE_PATH}}" in result
    assert "Done: <promise>COMPLETE</promise>" in result
    assert r"C:\repo\.ai_coder\worktrees\issue-47" not in result
