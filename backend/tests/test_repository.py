import pytest

from backend.app.collection.repository import InvalidRepository, parse_repository


@pytest.mark.parametrize(
    "value,expected",
    [
        ("owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo.git", ("owner", "repo")),
        ("https://github.com/owner/repo/issues/5", ("owner", "repo")),
        ("github.com/owner/repo", ("owner", "repo")),
        ("  owner/repo  ", ("owner", "repo")),
    ],
)
def test_parse_repository_accepts_valid_forms(value, expected):
    assert parse_repository(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "owner",
        "owner/repo/extra",
        "owner repo",
        "https://gitlab.com/owner/repo",
        "https://github.com/owner",
        "own er/repo",
    ],
)
def test_parse_repository_rejects_invalid_forms(value):
    with pytest.raises(InvalidRepository):
        parse_repository(value)
