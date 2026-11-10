from dataclasses import dataclass
from urllib.parse import urlsplit


def _positive_integer(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


def _text(value: str, name: str, *, required: bool = False) -> None:
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f"{name} must be {'nonempty ' if required else ''}text")


def _url(value: str) -> None:
    _text(value, "url")
    if value:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("url must be an HTTP(S) source URL")


@dataclass(frozen=True)
class Comment:
    id: int
    body: str
    url: str
    author: str | None = None
    created_at: str | None = None

    def __post_init__(self):
        _positive_integer(self.id, "comment id")
        _text(self.body, "comment body")
        _url(self.url)
        if self.author is not None:
            _text(self.author, "comment author")
        if self.created_at is not None:
            _text(self.created_at, "comment created_at")


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str = ""
    url: str = ""
    state: str = "open"
    comments: tuple[Comment, ...] = ()
    updated_at: str | None = None

    def __post_init__(self):
        _positive_integer(self.number, "issue number")
        _text(self.title, "issue title", required=True)
        _text(self.body, "issue body")
        _url(self.url)
        if self.state not in {"open", "closed"}:
            raise ValueError("issue state must be open or closed")
        if self.updated_at is not None:
            _text(self.updated_at, "issue updated_at")
        comments = tuple(self.comments)
        if any(not isinstance(comment, Comment) for comment in comments):
            raise ValueError("comments must contain Comment objects")
        if len({comment.id for comment in comments}) != len(comments):
            raise ValueError("duplicate comment id")
        object.__setattr__(self, "comments", comments)


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    repository: str
    collected_at: str
    collection_scope: dict
    partial_collection: bool
    content_hash: str
    issue_count: int
