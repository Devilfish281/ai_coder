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
