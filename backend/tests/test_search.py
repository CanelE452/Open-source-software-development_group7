import math

import pytest

from backend.app.search import SearchEngine
from backend.app.storage import Comment, Issue, SQLiteRepository


class TopicEmbedder:
    """Explicit two-topic vectors for algorithm tests, not a real semantic model."""

    model_id = "test/topics"
    model_revision = "revision-1"

    def __init__(self):
        self.calls = []

    def encode(self, texts):
        self.calls.append(list(texts))
        return [
            [1.0, 0.0] if any(word in text.casefold() for word in ("database", "sqlite", "locked"))
            else [0.0, 1.0]
            for text in texts
        ]


@pytest.fixture
def repository(tmp_path):
    with SQLiteRepository(tmp_path / "issues.sqlite3") as repository:
        yield repository


def save(repository, issues):
    return repository.save_snapshot(
        "example/project", issues, collected_at="2026-10-29T00:00:00Z",
        collection_scope={"state": "all", "max_issues": 100}, partial_collection=True,
    )


def issue(number, title, body="", comments=()):
    return Issue(number, title, body, f"https://github.com/example/project/issues/{number}", comments=comments)


def test_bm25_ranks_exact_error_and_includes_metadata(repository):
    snapshot = save(repository, [
        issue(2, "Window color issue", "Dark theme"),
        issue(1, "SQLite database locked", "WinError 32 on Windows"),
    ])
    response = SearchEngine(repository).search(
        "EXAMPLE/PROJECT", "database", error="WinError 32", environment="Windows", top_k=1,
    )
    assert [hit.number for hit in response.results] == [1]
    assert response.results[0].score > 0
    assert response.results[0].score_type == "bm25"
    payload = response.to_dict()
    assert payload["repository"] == "example/project"
    assert payload["snapshot"]["snapshot_id"] == snapshot.snapshot_id
    assert payload["snapshot"]["partial_collection"] is True
    assert payload["snapshot"]["collection_scope"] == {"state": "all", "max_issues": 100}
    assert payload["results"][0]["url"].endswith("/1")


def test_bm25_indexes_comments_unicode_and_breaks_ties_by_number(repository):
    comments = (Comment(10, "저장 오류 UNIQUE constraint", "https://github.com/example/project/issues/5#issuecomment-10"),)
    save(repository, [issue(5, "SQLITE", comments=comments), issue(3, "SQLITE")])
    engine = SearchEngine(repository)
    assert [hit.number for hit in engine.search("example/project", "저장 오류").results] == [5]
    # Full width Latin text normalizes to ASCII.
    assert {hit.number for hit in engine.search("example/project", "ＳＱＬＩＴＥ").results} == {3, 5}
    save(repository, [issue(5, "same token"), issue(3, "same token")])
    assert [hit.number for hit in engine.search("example/project", "token").results] == [3, 5]


def test_bm25_returns_no_result_for_unknown_terms_or_punctuation(repository):
    save(repository, [issue(1, "database locked")])
    engine = SearchEngine(repository)
    assert engine.search("example/project", "unrelated").results == []
    assert engine.search("example/project", "?!").results == []


def test_missing_and_empty_snapshots_need_no_model(repository):
    engine = SearchEngine(repository)
    missing = engine.search("example/project", "database", method="semantic")
    assert missing.snapshot is None and missing.results == []
    snapshot = save(repository, [])
    empty = engine.search("example/project", "database", method="hybrid")
    assert empty.snapshot == snapshot and empty.results == []


@pytest.mark.parametrize("kwargs", [
    {"problem": " "}, {"method": "typo"}, {"top_k": 0}, {"top_k": 21}, {"top_k": True},
    {"top_k": 1.5}, {"error": None}, {"environment": 42}, {"method": []},
])
def test_rejects_invalid_search_input(repository, kwargs):
    inputs = {"problem": "database"} | kwargs
    with pytest.raises(ValueError):
        SearchEngine(repository).search("example/project", **inputs)


def test_rejects_snapshot_from_another_repository(repository):
    snapshot = save(repository, [issue(1, "database locked")])
    with pytest.raises(ValueError, match="repository"):
        SearchEngine(repository).search("other/repository", "database", snapshot_id=snapshot.snapshot_id)


def test_selected_old_snapshot_remains_searchable(repository):
    original = save(repository, [issue(1, "old_error")])
    save(repository, [issue(1, "new_error")])
    engine = SearchEngine(repository)
    assert engine.search("example/project", "old_error").results == []
    assert engine.search("example/project", "old_error", snapshot_id=original.snapshot_id).results[0].number == 1


def test_semantic_uses_cosine_scores_and_separate_model_metadata(repository):
    save(repository, [issue(1, "database locked"), issue(2, "theme color")])
    embedder = TopicEmbedder()
    response = SearchEngine(repository, embedder).search("example/project", "sqlite", method="semantic")
    assert [hit.number for hit in response.results] == [1, 2]
    assert response.results[0].score == pytest.approx(1.0)
    assert response.results[1].score == pytest.approx(0.0)
    assert response.results[0].score_type == "cosine"
    assert response.to_dict()["model"] == {"model_id": "test/topics", "model_revision": "revision-1"}


def test_hybrid_combines_ranks_and_semantic_only_candidates(repository):
    save(repository, [issue(1, "database locked"), issue(2, "sqlite"), issue(3, "color")])
    response = SearchEngine(repository, TopicEmbedder()).search("example/project", "sqlite", method="hybrid")
    # BM25 ranks #2 first; semantic ties #1/#2 and deterministically ranks #1 first.
    assert [hit.number for hit in response.results] == [2, 1, 3]
    assert response.results[0].score == pytest.approx(1 / 61 + 1 / 62)
    assert response.results[1].score == pytest.approx(1 / 61)
    assert response.results[0].score_type == "rrf"


def test_semantic_requires_explicit_embedder(repository):
    save(repository, [issue(1, "database")])
    with pytest.raises(ValueError, match="embedder"):
        SearchEngine(repository).search("example/project", "database", method="semantic")


def test_embedding_cache_survives_reopen_and_invalidates_changed_text(tmp_path):
    path = tmp_path / "cache.sqlite3"
    repository = SQLiteRepository(path)
    original = save(repository, [issue(1, "database locked"), issue(2, "theme")])
    embedder = TopicEmbedder()
    SearchEngine(repository, embedder).search("example/project", "sqlite", method="semantic")
    assert sum(len(batch) for batch in embedder.calls) == 3  # two documents + query
    repository.close()

    reopened = SQLiteRepository(path)
    embedder.calls.clear()
    engine = SearchEngine(reopened, embedder)
    engine.search("example/project", "sqlite", method="semantic", snapshot_id=original.snapshot_id)
    assert embedder.calls == [["sqlite"]]
    save(reopened, [issue(1, "database locked"), issue(2, "theme changed")])
    embedder.calls.clear()
    engine.search("example/project", "sqlite", method="semantic")
    assert sum(len(batch) for batch in embedder.calls) == 2

    embedder.model_revision = "revision-2"
    embedder.calls.clear()
    engine.search("example/project", "sqlite", method="semantic")
    assert sum(len(batch) for batch in embedder.calls) == 3
    reopened.close()


def test_comment_edits_invalidate_embedding_cache(repository):
    save(repository, [issue(1, "database", comments=(Comment(1, "locked", "https://example.com/c1"),))])
    embedder = TopicEmbedder()
    engine = SearchEngine(repository, embedder)
    engine.search("example/project", "sqlite", method="semantic")
    save(repository, [issue(1, "database", comments=(Comment(1, "fixed", "https://example.com/c1"),))])
    embedder.calls.clear()
    engine.search("example/project", "sqlite", method="semantic")
    assert sum(len(batch) for batch in embedder.calls) == 2


@pytest.mark.parametrize("vectors", [
    [[math.nan, 1]], [[math.inf, 1]], [[0, 0]], [[]], [[1, 0], [1, 0]], [["bad", 1]],
])
def test_invalid_document_vectors_do_not_poison_cache(repository, vectors):
    save(repository, [issue(1, "database")])

    class InvalidEmbedder(TopicEmbedder):
        def encode(self, texts):
            return vectors

    with pytest.raises(ValueError, match="[Ee]mbedding"):
        SearchEngine(repository, InvalidEmbedder()).search("example/project", "sqlite", method="semantic")
    # A healthy encoder must still encode the document rather than read invalid cache.
    healthy = TopicEmbedder()
    SearchEngine(repository, healthy).search("example/project", "sqlite", method="semantic")
    assert sum(len(batch) for batch in healthy.calls) == 2


def test_rejects_query_document_dimension_mismatch_before_caching(repository):
    save(repository, [issue(1, "database")])

    class MismatchedEmbedder(TopicEmbedder):
        def encode(self, texts):
            return [[1, 0]] if texts != ["sqlite"] else [[1, 0, 0]]

    with pytest.raises(ValueError, match="[Ee]mbedding"):
        SearchEngine(repository, MismatchedEmbedder()).search("example/project", "sqlite", method="semantic")
    healthy = TopicEmbedder()
    SearchEngine(repository, healthy).search("example/project", "sqlite", method="semantic")
    assert sum(len(batch) for batch in healthy.calls) == 2
