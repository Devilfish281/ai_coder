from ai_coder.repository_context import i_repository_start


def test_repository_start_returns_selected_repo_path(tmp_path) -> None:
    result = i_repository_start(tmp_path)

    assert result.repo_path == tmp_path
    assert result.ready is True
