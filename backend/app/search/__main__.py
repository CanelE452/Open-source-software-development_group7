"""CLI for importing snapshots and searching SQLite."""

import argparse
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path


def import_snapshot(repository, path: Path, repository_name: str | None = None):
    from backend.app.storage import Comment, Issue

    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict) or not isinstance(payload.get("issues"), list):
        raise ValueError("input must be an object containing an issues array")
    source = payload.get("repository")
    if source is not None and not isinstance(source, str):
        raise ValueError("input repository must be text")
    if repository_name and source and repository_name.lower() != source.lower():
        raise ValueError("--repository must match the input repository")
    name = repository_name or source
    if not isinstance(name, str):
        raise ValueError("repository is required in the input or --repository")
    issues = []
    for item in payload["issues"]:
        if not isinstance(item, dict):
            raise ValueError("each issue must be an object")
        fields = dict(item)
        comments = fields.pop("comments", [])
        if not isinstance(comments, list) or any(not isinstance(c, dict) for c in comments):
            raise ValueError("issue comments must be an array of objects")
        issues.append(Issue(**fields, comments=tuple(Comment(**c) for c in comments)))
    return repository.save_snapshot(
        name,
        issues,
        collected_at=payload.get("collected_at"),
        collection_scope=payload.get("collection_scope"),
        partial_collection=payload.get("partial_collection", False),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Import collected Issues and search SQLite snapshots")
    parser.add_argument("--db", type=Path, default=Path("data/database/issues.sqlite3"))
    parser.add_argument("--model-id", help="Optional sentence-transformers model identifier")
    parser.add_argument("--model-revision", help="Immutable model revision; required with custom model ID")
    parser.add_argument("--model-cache", type=Path, default=Path("data/models"))
    commands = parser.add_subparsers(dest="command", required=True)
    importer = commands.add_parser("import", help="Store a collected JSON snapshot (no GitHub requests)")
    importer.add_argument("--input", type=Path, required=True)
    importer.add_argument("--repository")
    search = commands.add_parser("search", help="Search an existing snapshot")
    search.add_argument("--repository", required=True)
    search.add_argument("--problem", required=True)
    search.add_argument("--error", default="")
    search.add_argument("--environment", default="")
    search.add_argument("--method", choices=("bm25", "semantic", "hybrid"), default="bm25")
    search.add_argument("--top-k", type=int, default=5)
    search.add_argument("--snapshot-id")
    args = parser.parse_args(argv)
    if args.model_id and not args.model_revision:
        parser.error("--model-revision is required with --model-id")
    try:
        from backend.app.search import SearchEngine
        from backend.app.storage import SQLiteRepository

        with SQLiteRepository(args.db) as repository:
            if args.command == "import":
                output = asdict(import_snapshot(repository, args.input, args.repository))
            else:
                embedder = None
                if args.method != "bm25":
                    from backend.app.search.embeddings import SentenceTransformerEmbedder

                    model_options = {"cache_folder": str(args.model_cache)}
                    if args.model_id:
                        model_options["model_id"] = args.model_id
                    if args.model_revision:
                        model_options["model_revision"] = args.model_revision
                    embedder = SentenceTransformerEmbedder(**model_options)
                output = SearchEngine(repository, embedder=embedder).search(
                    args.repository, args.problem, error=args.error,
                    environment=args.environment, method=args.method,
                    top_k=args.top_k, snapshot_id=args.snapshot_id,
                ).to_dict()
        print(json.dumps(output, ensure_ascii=True, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, ImportError, sqlite3.DatabaseError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
