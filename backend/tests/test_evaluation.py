import copy
import io
import json
import unittest
from contextlib import redirect_stderr
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from evaluation.compare import compare_search, main, retrieval_metrics


class RetrievalMetricsTests(unittest.TestCase):
    def test_metrics_use_requested_k_and_first_relevant_rank(self):
        actual = retrieval_metrics([8, 2], {2, 3}, top_k=3)
        self.assertAlmostEqual(actual["precision_at_k"], 1 / 3)
        self.assertEqual(actual["recall_at_k"], 0.5)
        self.assertEqual(actual["reciprocal_rank"], 0.5)

    def test_missing_hits_score_zero_and_duplicates_are_rejected(self):
        self.assertEqual(
            retrieval_metrics([], {2}, top_k=3),
            {"precision_at_k": 0, "recall_at_k": 0, "reciprocal_rank": 0},
        )
        with self.assertRaises(ValueError):
            retrieval_metrics([2, 2], {2}, top_k=3)

    def test_invalid_k_and_unjudged_queries_are_not_silently_scored(self):
        for top_k in [0, 21, True, 1.5]:
            with self.subTest(top_k=top_k), self.assertRaises(ValueError):
                retrieval_metrics([2], {2}, top_k=top_k)
        with self.assertRaises(ValueError):
            retrieval_metrics([2], set(), top_k=3)


@dataclass
class ExampleSnapshot:
    snapshot_id: str = "fixed-snapshot"
    repository: str = "example/fixture"
    collected_at: str = "2026-10-29T00:00:00+00:00"
    collection_scope: dict = None
    partial_collection: bool = False
    content_hash: str = "a" * 64
    issue_count: int = 3

    def __post_init__(self):
        self.collection_scope = {"source": "synthetic-test"}


class FixedEngine:
    def __init__(self):
        self.snapshot = ExampleSnapshot()
        self.repository = SimpleNamespace(
            get_snapshot=lambda _: self.snapshot,
            list_issues=lambda _: [SimpleNamespace(number=n) for n in [1, 2, 3]],
        )
        self.embedder = SimpleNamespace(model_id="test-double", model_revision="test-v1")
        self.configuration = {"fixture": "controlled rankings for metric tests"}
        self.calls = []

    def search(self, repository, problem, **kwargs):
        self.calls.append((repository, problem, kwargs))
        numbers = {"bm25": [3, 2], "semantic": [2, 1], "hybrid": [2, 3]}[
            kwargs["method"]
        ]
        return SimpleNamespace(
            snapshot=self.snapshot,
            results=[SimpleNamespace(number=n, score=1 / n) for n in numbers],
        )


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.engine = FixedEngine()
        self.queries = {
            "version": "authored-test-v1",
            "provenance": "synthetic test fixture",
            "queries": [
                {"id": "database", "problem": "sqlite locked", "relevant_issues": [2]}
            ],
        }

    def test_compares_three_methods_with_same_snapshot_and_query(self):
        report = compare_search(
            self.engine, "example/fixture", "fixed-snapshot", self.queries, top_k=3
        )
        self.assertEqual(len(self.engine.calls), 3)
        self.assertEqual(
            {call[2]["snapshot_id"] for call in self.engine.calls}, {"fixed-snapshot"}
        )
        self.assertEqual({call[1] for call in self.engine.calls}, {"sqlite locked"})
        self.assertEqual(report["query_count"], 1)
        self.assertEqual(report["snapshot"]["content_hash"], "a" * 64)
        self.assertEqual(report["model"]["model_revision"], "test-v1")
        self.assertEqual(len(report["query_set_hash"]), 64)
        self.assertEqual(report["methods"]["bm25"]["mean_reciprocal_rank"], 0.5)
        self.assertEqual(report["methods"]["semantic"]["mean_reciprocal_rank"], 1)
        self.assertEqual(report["methods"]["hybrid"]["recall_at_k"], 1)

    def test_repository_matching_is_case_insensitive(self):
        report = compare_search(
            self.engine, "Example/Fixture", "fixed-snapshot", self.queries
        )
        self.assertEqual(report["repository"], "example/fixture")
        self.assertEqual({call[0] for call in self.engine.calls}, {"example/fixture"})

    def test_rejects_invalid_judgments_before_any_search(self):
        invalid_sets = []
        for relevant in [[], [99], [True], [1, 1]]:
            invalid = copy.deepcopy(self.queries)
            invalid["queries"][0]["relevant_issues"] = relevant
            invalid_sets.append(invalid)
        duplicate = copy.deepcopy(self.queries)
        duplicate["queries"].append(copy.deepcopy(duplicate["queries"][0]))
        invalid_sets.append(duplicate)
        for invalid in invalid_sets:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    compare_search(self.engine, "example/fixture", "fixed-snapshot", invalid)
        self.assertEqual(self.engine.calls, [])

    def test_rejects_repository_mismatch_and_snapshot_drift(self):
        with self.assertRaises(ValueError):
            compare_search(self.engine, "other/repo", "fixed-snapshot", self.queries)
        self.engine.snapshot.snapshot_id = "unexpected-snapshot"
        with self.assertRaises(ValueError):
            compare_search(self.engine, "example/fixture", "fixed-snapshot", self.queries)

    def test_detects_snapshot_change_returned_by_search(self):
        original_search = self.engine.search

        def changed_snapshot(*args, **kwargs):
            response = original_search(*args, **kwargs)
            response.snapshot = copy.copy(response.snapshot)
            response.snapshot.content_hash = "b" * 64
            return response

        self.engine.search = changed_snapshot
        with self.assertRaisesRegex(ValueError, "different snapshot"):
            compare_search(self.engine, "example/fixture", "fixed-snapshot", self.queries)

    def test_custom_model_requires_explicit_revision_before_database_access(self):
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as result:
            main([
                "--db", "missing.sqlite3", "--repository", "example/fixture",
                "--snapshot-id", "fixed-snapshot", "--queries", "unused.json",
                "--output", "unused-output.json", "--model-id", "custom/model",
            ])
        self.assertEqual(result.exception.code, 2)
        self.assertIn("--model-id requires an explicit immutable --model-revision", errors.getvalue())

    def test_authored_fixture_judgments_reference_existing_issues(self):
        root = Path(__file__).resolve().parents[2]
        issues = json.loads((root / "evaluation/datasets/search-smoke.json").read_text("utf-8"))
        judgments = json.loads((root / "evaluation/datasets/smoke-queries.json").read_text("utf-8"))
        numbers = {issue["number"] for issue in issues["issues"]}
        self.assertEqual(len(numbers), 8)
        self.assertEqual(len(judgments["queries"]), 4)
        self.assertEqual(issues["collection_scope"]["source"], "authored-synthetic")
        self.assertIn("synthetic", judgments["provenance"])
        for query in judgments["queries"]:
            self.assertLessEqual(set(query["relevant_issues"]), numbers)


if __name__ == "__main__":
    unittest.main()
