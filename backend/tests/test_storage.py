import math
import sqlite3

import pytest

from backend.app.storage import Comment, Issue, SQLiteRepository


def test_snapshot_round_trip_survives_reopen_and_preserves_collection_metadata(tmp_path):
    path = tmp_path / "nested" / "issues.sqlite3"
    issue = Issue(
        number=42,
        title="Unicode 한글 and 'SQL'",
        body="Traceback: disk full",
        url="https://github.com/example/project/issues/42",
        state="closed",
        comments=(Comment(10, "Fixed in 2.0", "https://github.com/example/project/issues/42#issuecomment-10"),),
        updated_at="2026-10-29T10:30:00Z",
    )
    repository = SQLiteRepository(path)
    snapshot = repository.save_snapshot(
        "example/project",
        [issue],
        collected_at="2026-10-29T12:00:00+02:00",
        collection_scope={"state": "all", "pages": 1},
        partial_collection=True,
    )
    repository.close()

    with SQLiteRepository(path) as reopened:
        assert reopened.get_snapshot(snapshot.snapshot_id) == snapshot
        assert reopened.get_issue(snapshot.snapshot_id, 42) == issue
        assert reopened.list_issues(snapshot.snapshot_id) == [issue]
        assert reopened.get_issue(snapshot.snapshot_id, 999) is None
        assert reopened.latest_snapshot("example/project") == snapshot
        assert reopened.latest_snapshot("other/project") is None

    assert snapshot.collected_at == "2026-10-29T10:00:00+00:00"
    assert snapshot.collection_scope == {"state": "all", "pages": 1}
    assert snapshot.partial_collection is True
    assert snapshot.issue_count == 1
    assert len(snapshot.content_hash) == 64


def test_new_snapshot_does_not_overwrite_old_issue_or_other_repository(tmp_path):
    with SQLiteRepository(tmp_path / "issues.db") as repository:
        old = repository.save_snapshot("a/repo", [Issue(1, "Old")], collected_at="2026-01-01T00:00:00Z")
        new = repository.save_snapshot("a/repo", [Issue(1, "New")], collected_at="2026-01-02T00:00:00Z")
        other = repository.save_snapshot("b/repo", [Issue(1, "Other")])

        assert old.snapshot_id != new.snapshot_id
        assert repository.get_issue(old.snapshot_id, 1).title == "Old"
        assert repository.get_issue(new.snapshot_id, 1).title == "New"
        assert repository.get_issue(other.snapshot_id, 1).title == "Other"
        assert repository.latest_snapshot("a/repo") == new


def test_empty_snapshot_is_valid_but_unknown_snapshot_is_not(tmp_path):
    with SQLiteRepository(tmp_path / "issues.db") as repository:
        snapshot = repository.save_snapshot("a/repo", [])
        assert snapshot.issue_count == 0
        assert repository.list_issues(snapshot.snapshot_id) == []
        assert repository.get_issue(snapshot.snapshot_id, 1) is None
        with pytest.raises(KeyError):
            repository.get_snapshot("missing")
        with pytest.raises(KeyError):
            repository.list_issues("missing")
        with pytest.raises(KeyError):
            repository.get_issue("missing", 1)


def test_duplicate_issue_numbers_and_reused_ids_leave_original_snapshot_intact(tmp_path):
    path = tmp_path / "issues.db"
    with SQLiteRepository(path) as repository:
        original = repository.save_snapshot("a/repo", [Issue(1, "Original")], snapshot_id="original")
        with pytest.raises(ValueError, match="duplicate"):
            repository.save_snapshot("a/repo", [Issue(2, "One"), Issue(2, "Two")], snapshot_id="bad")
        with pytest.raises(ValueError, match="snapshot"):
            repository.save_snapshot("a/repo", [Issue(1, "Replacement")], snapshot_id="original")

        assert repository.get_snapshot("original") == original
        assert repository.get_issue("original", 1).title == "Original"
        with pytest.raises(KeyError):
            repository.get_snapshot("bad")
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0] == 1


def test_failing_input_iterator_leaves_no_partial_snapshot(tmp_path):
    def failing_source():
        yield Issue(1, "First")
        raise RuntimeError("collector stopped")

    with SQLiteRepository(tmp_path / "issues.db") as repository:
        with pytest.raises(RuntimeError, match="collector stopped"):
            repository.save_snapshot("a/repo", failing_source(), snapshot_id="interrupted")
        assert repository.latest_snapshot("a/repo") is None


def test_content_hash_is_deterministic_and_changes_with_content_or_scope(tmp_path):
    with SQLiteRepository(tmp_path / "issues.db") as repository:
        first = repository.save_snapshot("a/repo", [Issue(2, "Second"), Issue(1, "First")])
        same = repository.save_snapshot("a/repo", [Issue(1, "First"), Issue(2, "Second")])
        changed = repository.save_snapshot("a/repo", [Issue(1, "Changed"), Issue(2, "Second")])
        partial = repository.save_snapshot("a/repo", [Issue(1, "First"), Issue(2, "Second")], partial_collection=True)
        scoped = repository.save_snapshot("a/repo", [Issue(1, "First"), Issue(2, "Second")], collection_scope={"state": "open"})
        assert first.content_hash == same.content_hash
        assert first.snapshot_id != same.snapshot_id
        assert len({first.content_hash, changed.content_hash, partial.content_hash, scoped.content_hash}) == 4
        assert [issue.number for issue in repository.list_issues(first.snapshot_id)] == [1, 2]


def test_embeddings_persist_and_are_separated_by_model_revision_and_text(tmp_path):
    path = tmp_path / "issues.db"
    with SQLiteRepository(path) as repository:
        assert repository.get_embedding("model", "rev-1", "text-a") is None
        repository.put_embedding("model", "rev-1", "text-a", [0.25, -0.5])
    with SQLiteRepository(path) as repository:
        assert repository.get_embedding("model", "rev-1", "text-a") == [0.25, -0.5]
        assert repository.get_embedding("model", "rev-2", "text-a") is None
        assert repository.get_embedding("other", "rev-1", "text-a") is None
        assert repository.get_embedding("model", "rev-1", "text-b") is None
        repository.put_embedding("model", "rev-2", "text-a", [1.0, 0.0])
        assert repository.get_embedding("model", "rev-1", "text-a") == [0.25, -0.5]
        assert repository.get_embedding("model", "rev-2", "text-a") == [1.0, 0.0]


@pytest.mark.parametrize("vector", [[], [math.nan], [math.inf], ["not-a-number"], [True]])
def test_invalid_embedding_is_rejected(tmp_path, vector):
    with SQLiteRepository(tmp_path / "issues.db") as repository:
        with pytest.raises(ValueError):
            repository.put_embedding("model", "revision", "text", vector)
        assert repository.get_embedding("model", "revision", "text") is None


@pytest.mark.parametrize("repository_name", ["", "repo", "owner/repo/extra", "https://github.com/o/r", "o/r?bad", "o /r"])
def test_invalid_repository_name_is_rejected(tmp_path, repository_name):
    with SQLiteRepository(tmp_path / "issues.db") as repository:
        with pytest.raises(ValueError, match="repository"):
            repository.save_snapshot(repository_name, [])


@pytest.mark.parametrize("number,title", [(0, "Title"), (-1, "Title"), (True, "Title"), (1, ""), (1, "   ")])
def test_invalid_issue_is_rejected(number, title):
    with pytest.raises(ValueError):
        Issue(number, title)


def test_naive_collection_timestamp_is_rejected(tmp_path):
    with SQLiteRepository(tmp_path / "issues.db") as repository:
        with pytest.raises(ValueError, match="timezone"):
            repository.save_snapshot("a/repo", [], collected_at="2026-10-29T12:00:00")


def test_in_memory_repository_keeps_data_for_its_lifetime():
    with SQLiteRepository(":memory:") as repository:
        snapshot = repository.save_snapshot("a/repo", [Issue(1, "Memory")])
        assert repository.get_issue(snapshot.snapshot_id, 1).title == "Memory"


def test_mutating_metadata_input_or_return_value_does_not_change_persisted_snapshot(tmp_path):
    scope = {"pages": [1], "filters": {"state": "all"}}
    with SQLiteRepository(tmp_path / "issues.db") as repository:
        snapshot = repository.save_snapshot("Owner/Repo", [], collection_scope=scope)
        scope["pages"].append(2)
        snapshot.collection_scope["filters"]["state"] = "closed"

        saved = repository.get_snapshot(snapshot.snapshot_id)
        assert saved.collection_scope == {"pages": [1], "filters": {"state": "all"}}
        assert saved.repository == "owner/repo"
        assert repository.latest_snapshot("OWNER/REPO") == saved


def test_sql_failure_rolls_back_snapshot_and_issues_as_one_transaction(tmp_path):
    path = tmp_path / "issues.db"
    with SQLiteRepository(path) as repository:
        original = repository.save_snapshot("a/repo", [Issue(1, "Original")])
        with sqlite3.connect(path) as connection:
            connection.execute(
                """CREATE TRIGGER reject_issue BEFORE INSERT ON issues
                WHEN NEW.title = 'Rejected'
                BEGIN SELECT RAISE(ABORT, 'write failed'); END"""
            )
        with pytest.raises(sqlite3.IntegrityError, match="write failed"):
            repository.save_snapshot("a/repo", [Issue(1, "Accepted"), Issue(2, "Rejected")], snapshot_id="failed")

        assert repository.latest_snapshot("a/repo") == original
        with pytest.raises(KeyError):
            repository.get_snapshot("failed")
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM issues").fetchone()[0] == 1


def test_repository_can_be_used_from_a_worker_thread(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    with SQLiteRepository(tmp_path / "issues.db") as repository:
        snapshot = repository.save_snapshot("a/repo", [Issue(1, "Threaded")])
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _: repository.get_issue(snapshot.snapshot_id, 1), range(4)))
        assert results == [Issue(1, "Threaded")] * 4
