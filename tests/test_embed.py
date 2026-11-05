from types import SimpleNamespace

import numpy as np

from jobassist import embed


def test_local_normalizado_e_semantico(monkeypatch):
    monkeypatch.setenv("EMBEDDINGS", "local")
    v = embed.embed(
        ["Consumi a API REST com JavaScript e fetch", "API REST", "receita de bolo de cenoura"]
    )
    assert v.shape[0] == 3 and np.allclose(np.linalg.norm(v, axis=1), 1, atol=1e-4)
    assert v[0] @ v[1] > v[0] @ v[2]  # relacionado > irrelevante


def test_multilingue(monkeypatch):
    monkeypatch.setenv("EMBEDDINGS", "local")
    v = embed.embed(["desenvolvimento web", "web development", "banana madura"])
    assert v[0] @ v[1] > v[0] @ v[2]


def test_openai_usa_llm_e_normaliza(monkeypatch):
    monkeypatch.setattr(embed, "load_config", lambda: SimpleNamespace(embeddings="openai"))
    monkeypatch.setattr(embed.llm, "embeddings_openai", lambda t, m: [[3.0, 4.0]] * len(t))
    assert np.allclose(embed.embed(["a", "b"]), [[0.6, 0.8]] * 2)
    assert embed.provider_id() == f"openai:{embed.OPENAI_MODEL}"


def test_lista_vazia():
    assert embed.embed([]).shape[0] == 0
