import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "backend.app.search", *map(str, arguments)],
        cwd=ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_cli_import_and_bm25_search_without_model(tmp_path):
    fixture = tmp_path / "issues.json"
    fixture.write_text(json.dumps({
        "repository": "Example/Project",
        "collected_at": "2026-10-29T12:00:00Z",
        "collection_scope": {"state": "all", "pages": 1},
        "partial_collection": True,
        "issues": [
            {"number": 2, "title": "윈도우 SQLite database locked", "body": "Concurrent write failure",
             "url": "https://github.com/Example/Project/issues/2",
             "comments": [{"id": 20, "body": "Close the open transaction",
                           "url": "https://github.com/Example/Project/issues/2#issuecomment-20"}]},
            {"number": 3, "title": "CSS spacing", "url": "https://github.com/Example/Project/issues/3"},
        ],
    }), encoding="utf-8")
    db = tmp_path / "nested" / "issues.sqlite3"
    imported = run_cli("--db", db, "import", "--input", fixture)
    assert imported.returncode == 0, imported.stderr
    snapshot = json.loads(imported.stdout)
    assert snapshot["issue_count"] == 2
    assert snapshot["partial_collection"] is True
    response = run_cli("--db", db, "search", "--repository", "Example/Project",
                       "--problem", "SQLite locked", "--snapshot-id", snapshot["snapshot_id"])
    assert response.returncode == 0, response.stderr
    result = json.loads(response.stdout)
    assert [hit["number"] for hit in result["results"]] == [2]
    assert result["snapshot"]["snapshot_id"] == snapshot["snapshot_id"]
    assert result["snapshot"]["collection_scope"]["state"] == "all"


def test_cli_bad_input_is_reported_without_traceback(tmp_path):
    fixture = tmp_path / "bad.json"
    fixture.write_text('{"repository": "owner/repo", "issues": "wrong"}', encoding="utf-8")
    result = run_cli("--db", tmp_path / "db.sqlite3", "import", "--input", fixture)
    assert result.returncode != 0
    assert "error:" in result.stderr.lower()
    assert "Traceback" not in result.stderr


def test_cli_rejects_repository_override_that_mislabels_snapshot(tmp_path):
    fixture = tmp_path / "issues.json"
    fixture.write_text('{"repository": "owner/source", "issues": []}', encoding="utf-8")
    result = run_cli("--db", tmp_path / "db.sqlite3", "import", "--input", fixture,
                     "--repository", "owner/other")
    assert result.returncode != 0
    assert "repository" in result.stderr


def test_cli_empty_database_returns_no_snapshot_or_results(tmp_path):
    result = run_cli("--db", tmp_path / "db.sqlite3", "search",
                     "--repository", "owner/repo", "--problem", "crash")
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    assert response["snapshot"] is None
    assert response["results"] == []


def test_cli_rejects_non_text_source_repository_with_override(tmp_path):
    fixture = tmp_path / "issues.json"
    fixture.write_text('{"repository": 123, "issues": []}', encoding="utf-8")
    result = run_cli("--db", tmp_path / "db.sqlite3", "import", "--input", fixture,
                     "--repository", "owner/repo")
    assert result.returncode != 0
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_custom_model_requires_its_own_revision(tmp_path):
    result = run_cli("--db", tmp_path / "db.sqlite3", "--model-id", "owner/custom-model",
                     "search", "--repository", "owner/repo", "--problem", "crash", "--method", "semantic")
    assert result.returncode != 0
    assert "--model-revision" in result.stderr
