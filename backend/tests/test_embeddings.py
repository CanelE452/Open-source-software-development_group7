import builtins
import sys
from types import SimpleNamespace

import pytest


def adapter_class():
    from backend.app.search.embeddings import SentenceTransformerEmbedder

    return SentenceTransformerEmbedder


def test_adapter_loads_only_on_first_nonempty_encode(monkeypatch, tmp_path):
    events = []

    class FakeModel:
        def __init__(self, model_id, **kwargs):
            events.append((model_id, kwargs))

        def encode(self, texts, **kwargs):
            events.append((texts, kwargs))
            return SimpleNamespace(tolist=lambda: [[0.25, 0.75] for _ in texts])

    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=FakeModel))
    cls = adapter_class()
    adapter = cls(cache_folder=tmp_path, local_files_only=True)
    assert events == []
    assert adapter.encode([]) == []
    assert events == []

    assert adapter.encode(["database locked"]) == [[0.25, 0.75]]
    assert events[0] == (
        adapter.model_id,
        {
            "revision": adapter.model_revision,
            "cache_folder": str(tmp_path),
            "device": "cpu",
            "trust_remote_code": False,
            "local_files_only": True,
        },
    )
    assert events[1] == (
        ["database locked"],
        {"normalize_embeddings": True, "convert_to_numpy": True, "show_progress_bar": False},
    )
    adapter.encode(["another query"])
    assert len(events) == 3


def test_adapter_missing_dependency_has_install_instruction(monkeypatch):
    original_import = builtins.__import__

    def missing_package(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise ImportError("missing sentence_transformers")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_package)
    adapter = adapter_class()()
    with pytest.raises(RuntimeError, match="requirements-search.txt"):
        adapter.encode(["query"])


@pytest.mark.parametrize("revision", ["main", "latest", "", "a" * 39, "z" * 40])
def test_adapter_requires_immutable_model_revision(revision):
    with pytest.raises(ValueError, match="revision"):
        adapter_class()(model_revision=revision)


def test_adapter_accepts_explicit_model_and_revision(monkeypatch, tmp_path):
    seen = {}

    def fake_model(model_id, **kwargs):
        seen.update(model_id=model_id, **kwargs)
        return SimpleNamespace(encode=lambda texts, **_: SimpleNamespace(tolist=lambda: [[1, 0]]))

    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=fake_model))
    adapter = adapter_class()("example/model", "a" * 40, cache_folder=tmp_path)
    assert adapter.encode(["query"]) == [[1.0, 0.0]]
    assert seen["model_id"] == "example/model"
    assert seen["revision"] == "a" * 40
    assert seen["cache_folder"] == str(tmp_path)


@pytest.mark.parametrize("model_id", ["", "  "])
def test_adapter_rejects_blank_model_identifier(model_id):
    with pytest.raises(ValueError, match="model_id"):
        adapter_class()(model_id=model_id)


def test_adapter_does_not_hide_model_loading_failure(monkeypatch):
    def unavailable_model(*args, **kwargs):
        raise OSError("model cache unavailable")

    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=unavailable_model))
    with pytest.raises(OSError, match="cache unavailable"):
        adapter_class()().encode(["query"])
