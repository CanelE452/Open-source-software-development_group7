"""Optional, lazy local embedding model adapter."""

import re
from pathlib import Path
from typing import Protocol


DEFAULT_MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_MODEL_REVISION = "e8f8c211226b894fcb81acc59f3b34ba3efd5f42"


class Embedder(Protocol):
    model_id: str
    model_revision: str

    def encode(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        model_revision: str = DEFAULT_MODEL_REVISION,
        *,
        cache_folder: str | Path = "data/models",
        local_files_only: bool = False,
    ):
        if not model_id.strip():
            raise ValueError("model_id must not be blank")
        if not re.fullmatch(r"[0-9a-fA-F]{40}", model_revision):
            raise ValueError("model_revision must be an immutable 40-character commit SHA")
        self.model_id = model_id
        self.model_revision = model_revision.lower()
        self.cache_folder = str(cache_folder)
        self.local_files_only = local_files_only
        self._model = None

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "Semantic search requires optional dependencies: "
                    "python -m pip install -r backend/requirements-search.txt"
                ) from exc
            self._model = SentenceTransformer(
                self.model_id,
                revision=self.model_revision,
                cache_folder=self.cache_folder,
                device="cpu",
                trust_remote_code=False,
                local_files_only=self.local_files_only,
            )
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [[float(value) for value in vector] for vector in vectors.tolist()]
