"""Compare all retrieval methods using one immutable snapshot and query set."""

import argparse
import hashlib
import json
import platform
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

from backend.app.storage import normalize_repository


METHODS = ("bm25", "semantic", "hybrid")


def _validate_top_k(top_k):
    if type(top_k) is not int or not 1 <= top_k <= 20:
        raise ValueError("top_k must be an integer from 1 to 20")


def _positive_numbers(numbers, name):
    if not isinstance(numbers, (list, tuple, set)):
        raise ValueError(f"{name} must contain issue numbers")
    if any(type(number) is not int or number < 1 for number in numbers):
        raise ValueError(f"{name} must contain positive integer issue numbers")
    if len(set(numbers)) != len(numbers):
        raise ValueError(f"{name} must not contain duplicate issue numbers")
    return set(numbers)


def retrieval_metrics(ranked_numbers, relevant_numbers, *, top_k):
    """Compute binary P@K, Recall@K and reciprocal rank within K.

    P@K uses the requested K; relevance judgments must be nonempty.
    """
    _validate_top_k(top_k)
    if not isinstance(ranked_numbers, (list, tuple)):
        raise ValueError("ranked_numbers must be an ordered list or tuple")
    _positive_numbers(ranked_numbers, "ranked_numbers")
    relevant = _positive_numbers(relevant_numbers, "relevant_numbers")
    if not relevant:
        raise ValueError("relevant_numbers must contain at least one judgment")
    ranked = ranked_numbers[:top_k]
    hits = len(set(ranked) & relevant)
    reciprocal_rank = next(
        (1 / rank for rank, number in enumerate(ranked, start=1) if number in relevant),
        0.0,
    )
    return {
        "precision_at_k": hits / top_k,
        "recall_at_k": hits / len(relevant),
        "reciprocal_rank": reciprocal_rank,
    }


def _digest(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_queries(query_set, issue_numbers):
    if not isinstance(query_set, dict):
        raise ValueError("query set must be a JSON object")
    version = query_set.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("query set must have a nonempty version")
    queries = query_set.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError("query set must contain at least one query")
    seen = set()
    for query in queries:
        if not isinstance(query, dict):
            raise ValueError("each query must be an object")
        query_id = query.get("id")
        if not isinstance(query_id, str) or not query_id.strip() or query_id in seen:
            raise ValueError("query ids must be nonempty and unique")
        seen.add(query_id)
        problem = query.get("problem")
        if not isinstance(problem, str) or not problem.strip():
            raise ValueError(f"query {query_id}: problem must be a nonempty string")
        for field in ("error", "environment"):
            if not isinstance(query.get(field, ""), str):
                raise ValueError(f"query {query_id}: {field} must be a string")
        relevant = _positive_numbers(query.get("relevant_issues"), "relevant_issues")
        if not relevant:
            raise ValueError(f"query {query_id}: relevance judgments cannot be empty")
        missing = relevant - issue_numbers
        if missing:
            raise ValueError(f"query {query_id}: judged issues absent from snapshot: {sorted(missing)}")
    return queries


def compare_search(engine, repository, snapshot_id, queries, top_k=3):
    """Evaluate an injected SearchEngine without changing the source snapshot."""
    _validate_top_k(top_k)
    repository = normalize_repository(repository)
    snapshot = engine.repository.get_snapshot(snapshot_id)
    if snapshot.repository != repository or snapshot.snapshot_id != snapshot_id:
        raise ValueError("repository and snapshot_id must identify the same snapshot")
    issue_numbers = {issue.number for issue in engine.repository.list_issues(snapshot_id)}
    query_list = _validate_queries(queries, issue_numbers)
    if engine.embedder is None:
        raise ValueError("all-method comparison requires a semantic embedder")

    report = {
        "report_version": "retrieval-comparison-v1",
        "created_at": datetime.now(UTC).isoformat(),
        "repository": repository,
        "snapshot": asdict(snapshot),
        "query_set_version": queries["version"],
        "query_set_provenance": queries.get("provenance", "not provided"),
        "query_set_hash": _digest(queries),
        "query_count": len(query_list),
        "top_k": top_k,
        "model": {
            "model_id": engine.embedder.model_id,
            "model_revision": engine.embedder.model_revision,
        },
        "search_configuration": engine.configuration,
        "runtime": {"python": platform.python_version()},
        "methods": {},
    }
    for package in ("sentence-transformers", "transformers", "torch"):
        try:
            report["runtime"][package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            pass

    for method in METHODS:
        query_results = []
        for query in query_list:
            response = engine.search(
                repository,
                query["problem"],
                error=query.get("error", ""),
                environment=query.get("environment", ""),
                method=method,
                top_k=top_k,
                snapshot_id=snapshot_id,
            )
            returned = response.snapshot
            if returned is None or (
                returned.snapshot_id != snapshot_id
                or returned.content_hash != snapshot.content_hash
                or returned.repository != repository
            ):
                raise ValueError("search returned a different snapshot during comparison")
            numbers = [hit.number for hit in response.results]
            if set(numbers) - issue_numbers:
                raise ValueError("search returned an issue absent from the evaluated snapshot")
            scores = retrieval_metrics(numbers, query["relevant_issues"], top_k=top_k)
            query_results.append(
                {
                    "id": query["id"],
                    "query_hash": _digest(query),
                    "problem": query["problem"],
                    "error": query.get("error", ""),
                    "environment": query.get("environment", ""),
                    "relevant_issues": sorted(query["relevant_issues"]),
                    "ranked_issues": numbers,
                    "scores": [hit.score for hit in response.results],
                    **scores,
                }
            )
        count = len(query_results)
        report["methods"][method] = {
            "precision_at_k": sum(row["precision_at_k"] for row in query_results) / count,
            "recall_at_k": sum(row["recall_at_k"] for row in query_results) / count,
            "mean_reciprocal_rank": sum(row["reciprocal_rank"] for row in query_results) / count,
            "queries": query_results,
        }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-id")
    parser.add_argument("--model-revision")
    parser.add_argument("--model-cache", type=Path, default=Path("data/models"))
    args = parser.parse_args(argv)

    try:
        if args.model_id and not args.model_revision:
            raise ValueError("--model-id requires an explicit immutable --model-revision")
        if not args.db.is_file():
            raise ValueError("database does not exist; import a snapshot first")
        if args.output.exists():
            raise ValueError("output already exists; choose a new filename to preserve past runs")
        query_set = json.loads(args.queries.read_text(encoding="utf-8-sig"))
        from backend.app.search import SearchEngine
        from backend.app.search.embeddings import SentenceTransformerEmbedder
        from backend.app.storage import SQLiteRepository

        model_options = {"cache_folder": args.model_cache}
        if args.model_id:
            model_options["model_id"] = args.model_id
        if args.model_revision:
            model_options["model_revision"] = args.model_revision
        embedder = SentenceTransformerEmbedder(**model_options)
        with SQLiteRepository(args.db) as storage:
            report = compare_search(
                SearchEngine(storage, embedder),
                args.repository,
                args.snapshot_id,
                query_set,
                top_k=args.top_k,
            )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n")
    except (OSError, ValueError, KeyError, ImportError, RuntimeError, sqlite3.DatabaseError) as exc:
        parser.error(str(exc))
    print(f"Comparison saved: {args.output}")
    for method, result in report["methods"].items():
        print(
            f"{method}: P@{args.top_k}={result['precision_at_k']:.4f} "
            f"Recall@{args.top_k}={result['recall_at_k']:.4f} "
            f"MRR@{args.top_k}={result['mean_reciprocal_rank']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
