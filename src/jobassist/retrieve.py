"""Busca: uma consulta por requisito da vaga, top-k por cosseno."""
import re
from dataclasses import dataclass

import numpy as np

from .embed import embed

LITERAL_BONUS = 0.5
TOP_K = 3
THRESHOLD = 0.30  # nota mínima de cosseno; calibrada na avaliação (Dia 6)
MAX_TOTAL = 12


def term_pattern(term: str) -> re.Pattern:
    """Termo como palavra inteira, tolerando sufixo de versão (HTML casa com HTML5; Java não casa com JavaScript)."""
    return re.compile(rf"(?<!\w){re.escape(term.strip())}\d*(?!\w)", re.IGNORECASE)


@dataclass
class Hit:
    id: str
    text: str
    score: float


@dataclass
class Retrieval:
    requirement: dict
    hits: list[Hit]  # vazio = "sem evidência no material"


def retrieve(requirements: list[dict], index, top_k: int = TOP_K, threshold: float = THRESHOLD,
             max_total: int = MAX_TOTAL) -> tuple[list[Retrieval], list[Hit]]:
    """Devolve (resultado por requisito, trechos únicos para o prompt).

    ponytail: força bruta (produto escalar com todos os chunks); serve até ~10 mil chunks,
    acima disso trocar por FAISS/sqlite-vec.
    """
    if not requirements or index is None:
        return [Retrieval(r, []) for r in requirements], []
    ids, texts, matrix = index
    queries = embed([r["text"] for r in requirements], "query")
    sims = queries @ matrix.T  # (requisitos x chunks); vetores já normalizados
    # Híbrido: embeddings são fracos com nomes de tecnologia soltos ("JavaScript" = 0,24 num
    # currículo que o cita). Trecho que contém o termo literalmente ganha bônus no ranking.
    for k, r in enumerate(requirements):
        if r["kind"] == "tech":
            word = term_pattern(r["text"])
            sims[k] += LITERAL_BONUS * np.array([bool(word.search(t)) for t in texts])

    per_req = []
    best: dict[int, float] = {}
    for r, row in zip(requirements, sims):
        order = [i for i in np.argsort(-row)[:top_k] if row[i] >= threshold]
        per_req.append((r, order))
        for i in order:
            best[i] = max(best.get(i, 0.0), float(row[i]))

    keep = set(sorted(best, key=best.get, reverse=True)[:max_total])
    hit = lambda i, s: Hit(ids[i], texts[i], round(float(s), 3))
    results = [Retrieval(r, [hit(i, row[i]) for i in order if i in keep])
               for (r, order), row in zip(per_req, sims)]
    unique = sorted(keep, key=lambda i: ids[i])
    return results, [hit(i, best[i]) for i in unique]
