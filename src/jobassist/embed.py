"""Embeddings: local (padrão, o material não sai da máquina) ou OpenAI."""
from functools import lru_cache
from pathlib import Path

import numpy as np

from . import llm
from .config import load_config

LOCAL_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_MODEL = "text-embedding-3-small"
CACHE = Path(__file__).resolve().parents[2] / ".cache" / "fastembed"


def provider_id() -> str:
    """Grava-se no índice: vetores de provedores diferentes não se misturam."""
    return f"openai:{OPENAI_MODEL}" if load_config().embeddings == "openai" else f"local:{LOCAL_MODEL}"


@lru_cache(maxsize=1)
def _local():
    from fastembed import TextEmbedding  # import tardio: só carrega se for usado

    return TextEmbedding(LOCAL_MODEL, cache_dir=str(CACHE))


def embed(texts: list[str], kind: str = "passage") -> np.ndarray:
    """Vetores float32 normalizados (cosseno = produto escalar).

    `kind` ("passage" | "query") é ignorado pelo MiniLM; fica na assinatura para
    modelos que exigem prefixo (ex.: e5), caso o modelo seja trocado.
    """
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)
    if load_config().embeddings == "openai":
        vecs = np.array(llm.embeddings_openai(texts, OPENAI_MODEL), dtype=np.float32)
    else:
        vecs = np.array(list(_local().embed(texts)), dtype=np.float32)
    return vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
