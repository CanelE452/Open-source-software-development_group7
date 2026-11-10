"""Snapshot-scoped lexical, semantic, and reciprocal-rank search."""

import hashlib
import math
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass

from backend.app.search.embeddings import Embedder
from backend.app.storage import Issue, Snapshot, SQLiteRepository, normalize_repository


BM25_K1 = 1.5
BM25_B = 0.75
RRF_K = 60
TEXT_VERSION = "issue-text-v1"


def _normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).split())


def issue_text(issue: Issue) -> str:
    parts = [issue.title, issue.body]
    parts.extend(comment.body for comment in sorted(issue.comments, key=lambda item: item.id))
    return "\n".join(part for part in map(_normalize, parts) if part)


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", _normalize(text).casefold())


def _text_hash(text: str) -> str:
    return hashlib.sha256(f"{TEXT_VERSION}\0{text}".encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SearchHit:
    number: int
    title: str
    url: str
    score: float
    score_type: str


@dataclass(frozen=True)
class SearchResponse:
    repository: str
    snapshot: Snapshot | None
    method: str
    results: list[SearchHit]
    model: dict[str, str] | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class _BM25Index:
    def __init__(self, issues: list[Issue]):
        self.issues = issues
        self.frequencies = [Counter(_tokens(issue_text(issue))) for issue in issues]
        self.lengths = [sum(frequency.values()) for frequency in self.frequencies]
        self.average_length = sum(self.lengths) / len(issues) if issues else 0.0
        self.document_frequency = Counter(
            token for frequency in self.frequencies for token in frequency
        )

    def rank(self, query: str) -> list[tuple[int, float]]:
        query_tokens = set(_tokens(query))
        if not query_tokens or not self.average_length:
            return []
        count = len(self.issues)
        scores = []
        for issue, frequencies, length in zip(self.issues, self.frequencies, self.lengths):
            score = 0.0
            length_penalty = BM25_K1 * (1 - BM25_B + BM25_B * length / self.average_length)
            for token in sorted(query_tokens):
                frequency = frequencies.get(token, 0)
                if not frequency:
                    continue
                document_frequency = self.document_frequency[token]
                inverse_frequency = math.log(1 + (count - document_frequency + 0.5) / (document_frequency + 0.5))
                score += inverse_frequency * frequency * (BM25_K1 + 1) / (frequency + length_penalty)
            if score > 0:
                scores.append((issue.number, score))
        return sorted(scores, key=lambda item: (-item[1], item[0]))


def _unit_vectors(vectors, expected_count: int, dimension: int | None = None) -> list[list[float]]:
    if not isinstance(vectors, (list, tuple)) or len(vectors) != expected_count:
        raise ValueError("Embedding encoder returned an unexpected vector count")
    normalized = []
    for vector in vectors:
        try:
            values = [float(value) for value in vector]
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Embedding vector must contain finite numbers") from exc
        if not values or any(not math.isfinite(value) for value in values):
            raise ValueError("Embedding vector must contain finite numbers and not be empty")
        if dimension is None:
            dimension = len(values)
        if len(values) != dimension:
            raise ValueError("Embedding dimensions do not match")
        norm = math.hypot(*values)
        if norm == 0 or not math.isfinite(norm):
            raise ValueError("Embedding vector must have a nonzero finite norm")
        normalized.append([value / norm for value in values])
    return normalized


class SearchEngine:
    def __init__(self, repository: SQLiteRepository, embedder: Embedder | None = None):
        self.repository = repository
        self.embedder = embedder
        self._indexes: dict[str, _BM25Index] = {}

    @property
    def configuration(self) -> dict:
        return {
            "bm25": {"k1": BM25_K1, "b": BM25_B},
            "hybrid": {"rrf_k": RRF_K},
            "preprocessing_version": TEXT_VERSION,
        }

    def search(
        self,
        repository: str,
        problem: str,
        *,
        error: str = "",
        environment: str = "",
        method: str = "bm25",
        top_k: int = 5,
        snapshot_id: str | None = None,
    ) -> SearchResponse:
        repository = normalize_repository(repository)
        if not isinstance(problem, str) or not problem.strip():
            raise ValueError("problem must contain text")
        if not isinstance(error, str) or not isinstance(environment, str):
            raise ValueError("error and environment must be text")
        if not isinstance(method, str) or method not in {"bm25", "semantic", "hybrid"}:
            raise ValueError("method must be bm25, semantic, or hybrid")
        if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 20:
            raise ValueError("top_k must be an integer from 1 to 20")
        snapshot = (
            self.repository.get_snapshot(snapshot_id)
            if snapshot_id is not None else self.repository.latest_snapshot(repository)
        )
        if snapshot is not None and snapshot.repository != repository:
            raise ValueError("snapshot belongs to another repository")
        model = None
        if method != "bm25" and self.embedder is not None:
            model = {"model_id": self.embedder.model_id, "model_revision": self.embedder.model_revision}
        if snapshot is None:
            return SearchResponse(repository, None, method, [], model)
        issues = self.repository.list_issues(snapshot.snapshot_id)
        if not issues:
            return SearchResponse(repository, snapshot, method, [], model)
        query = "\n".join(part for part in map(_normalize, [problem, error, environment]) if part)
        lexical = []
        semantic = []
        if method in {"bm25", "hybrid"}:
            if snapshot.snapshot_id not in self._indexes:
                self._indexes[snapshot.snapshot_id] = _BM25Index(issues)
            lexical = self._indexes[snapshot.snapshot_id].rank(query)
        if method in {"semantic", "hybrid"}:
            semantic = self._semantic(issues, query)
        if method == "bm25":
            ranked, score_type = lexical, "bm25"
        elif method == "semantic":
            ranked, score_type = semantic, "cosine"
        else:
            combined = Counter()
            for ranking in (lexical, semantic):
                for position, (number, _) in enumerate(ranking, start=1):
                    combined[number] += 1 / (RRF_K + position)
            ranked = sorted(combined.items(), key=lambda item: (-item[1], item[0]))
            score_type = "rrf"
        by_number = {issue.number: issue for issue in issues}
        hits = [
            SearchHit(number, by_number[number].title, by_number[number].url, score, score_type)
            for number, score in ranked[:top_k]
        ]
        return SearchResponse(repository, snapshot, method, hits, model)

    def _semantic(self, issues: list[Issue], query: str) -> list[tuple[int, float]]:
        if self.embedder is None:
            raise ValueError("Semantic and hybrid search require an embedder")
        model_id, model_revision = self.embedder.model_id, self.embedder.model_revision
        if not isinstance(model_id, str) or not model_id.strip() or not isinstance(model_revision, str) or not model_revision.strip():
            raise ValueError("Embedding model_id and model_revision must contain text")
        texts = [issue_text(issue) for issue in issues]
        hashes = [_text_hash(text) for text in texts]
        by_hash = dict(zip(hashes, texts))
        vectors = {
            text_hash: self.repository.get_embedding(model_id, model_revision, text_hash)
            for text_hash in by_hash
        }
        missing = [text_hash for text_hash, vector in vectors.items() if vector is None]
        generated = self.embedder.encode([by_hash[text_hash] for text_hash in missing]) if missing else []
        fresh_vectors = _unit_vectors(generated, len(missing))
        vectors.update(zip(missing, fresh_vectors))
        ordered_vectors = _unit_vectors([vectors[text_hash] for text_hash in hashes], len(hashes))
        query_vector = _unit_vectors(self.embedder.encode([query]), 1, len(ordered_vectors[0]))[0]
        # Persist only after the complete document/query batch passes validation.
        for text_hash, vector in zip(missing, fresh_vectors):
            self.repository.put_embedding(model_id, model_revision, text_hash, vector)
        scores = [
            (issue.number, max(-1.0, min(1.0, math.fsum(left * right for left, right in zip(vector, query_vector)))))
            for issue, vector in zip(issues, ordered_vectors)
        ]
        return sorted(scores, key=lambda item: (-item[1], item[0]))
