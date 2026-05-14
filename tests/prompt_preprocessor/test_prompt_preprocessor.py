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
