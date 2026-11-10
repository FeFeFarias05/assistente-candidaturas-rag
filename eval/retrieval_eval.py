"""Avaliação de retrieval no corpus fictício (eval/corpus): só busca, sem chamar o LLM.

Uso: python eval/retrieval_eval.py [--openai] [--out eval/results_retrieval.md]

Relevância é por TEXTO: um trecho é relevante para uma consulta se contém alguma frase de evidência do gabarito
(eval/corpus/spec.py). Estratégias comparadas:
  dense       só similaridade semântica (embeddings locais), sem o bônus de termo literal
  bm25        só palavras-chave (BM25 implementado aqui, sem dependências)
  sistema     o que o jobassist faz hoje: semântica + bônus de termo literal/idioma
  rrf         fusão por posição (Reciprocal Rank Fusion) de dense + bm25
  dense_openai (opcional, --openai) embeddings da OpenAI em vez dos locais
"""
import argparse
import contextlib
import math
import os
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "corpus"))
sys.path.insert(0, str(HERE.parent / "src"))

from jobassist import chunking, retrieve as rt  # noqa: E402
from jobassist.embed import embed  # noqa: E402
from jobassist.material import load_material  # noqa: E402
from jobassist.retrieve import term_pattern  # noqa: E402
from spec import QUERIES  # noqa: E402

CORPUS = HERE / "corpus" / "docs"
KS = (1, 3, 5)
TOP = 10
SEED = 7


# ---------- corpus e gabarito ----------

@contextlib.contextmanager
def chunk_size(max_chars: int | None, overlap: int | None = None):
    old = chunking.MAX_CHARS, chunking.OVERLAP
    if max_chars:
        chunking.MAX_CHARS = max_chars
        chunking.OVERLAP = overlap if overlap is not None else max(20, round(max_chars * 0.13))
    try:
        yield
    finally:
        chunking.MAX_CHARS, chunking.OVERLAP = old


def load_chunks(max_chars: int | None = None) -> list:
    with chunk_size(max_chars):
        return chunking.chunk_all(load_material(CORPUS))


def relevant_set(chunks: list, query) -> set[int]:
    """Índices dos trechos que provam a consulta (present/negated). Vazio para absent."""
    if query.category == "absent":
        return set()
    pats = [term_pattern(e) for e in query.evidence]
    return {i for i, c in enumerate(chunks) if any(p.search(c.text) for p in pats)}


# ---------- estratégias: cada uma devolve, por consulta, [(índice do trecho, nota)] em ordem ----------

def _rank_all(scores: np.ndarray) -> list[list[tuple[int, float]]]:
    out = []
    for row in scores:
        order = np.argsort(-row, kind="stable")[:TOP]
        out.append([(int(i), float(row[i])) for i in order])
    return out


def rank_system(queries, chunks, vecs, dense_only: bool = False):
    """Usa o próprio retrieve() do projeto, sem limiar (limiar = -10) para ver o ranking completo."""
    index = ([c.id for c in chunks], [c.text for c in chunks], vecs)
    pos = {c.id: i for i, c in enumerate(chunks)}
    saved = rt.LITERAL_BONUS, rt.LANGUAGES
    if dense_only:
        rt.LITERAL_BONUS, rt.LANGUAGES = 0.0, []
    try:
        results, _ = rt.retrieve([q.as_requirement() for q in queries], index, top_k=TOP, threshold=-10.0, max_total=10**9)
    finally:
        rt.LITERAL_BONUS, rt.LANGUAGES = saved
    return [[(pos[h.id], h.score) for h in r.hits] for r in results]


STOP = set("de da do das dos e em com para a o as os um uma que the of and in with for to an on".split())


def tokens(text: str) -> list[str]:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return [t for t in re.findall(r"\w+", plain) if t not in STOP]


def rank_bm25(queries, chunks, k1: float = 1.5, b: float = 0.75):
    docs = [tokens(c.text) for c in chunks]
    n, avg = len(docs), sum(map(len, docs)) / len(docs)
    df = Counter(t for d in docs for t in set(d))
    tfs = [Counter(d) for d in docs]
    scores = np.zeros((len(queries), n))
    for qi, q in enumerate(queries):
        for t in set(tokens(q.text)):
            if t not in df:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            for di, tf in enumerate(tfs):
                f = tf.get(t, 0)
                if f:
                    scores[qi, di] += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * len(docs[di]) / avg))
    return _rank_all(scores)


def rank_rrf(first, second, k: int = 60):
    fused = []
    for a, b in zip(first, second):
        score: dict[int, float] = {}
        for ranking in (a, b):
            for rank, (idx, _) in enumerate(ranking, 1):
                score[idx] = score.get(idx, 0.0) + 1.0 / (k + rank)
        fused.append(sorted(score.items(), key=lambda kv: -kv[1])[:TOP])
    return fused


# ---------- métricas (puras) ----------

def auc(pos: list[float], neg: list[float]) -> float:
    """Probabilidade de a nota do melhor trecho de uma consulta COM evidência superar a de uma SEM."""
    if not pos or not neg:
        return float("nan")
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def per_query(rankings, queries, rels) -> dict:
    """Valores por consulta com evidência (present/negated), prontos para média e bootstrap."""
    rows = {f"hit@{k}": [] for k in KS} | {f"p@{k}": [] for k in KS} | {f"r@{k}": [] for k in KS} | {"mrr": [], "kind": []}
    for ranking, q, rel in zip(rankings, queries, rels):
        if q.category == "absent":
            continue
        order = [i for i, _ in ranking]
        for k in KS:
            hits = len(set(order[:k]) & rel)
            rows[f"hit@{k}"].append(1.0 if hits else 0.0)
            rows[f"p@{k}"].append(hits / k)
            rows[f"r@{k}"].append(hits / len(rel) if rel else 0.0)
        first = next((r for r, i in enumerate(order, 1) if i in rel), None)
        rows["mrr"].append(1.0 / first if first else 0.0)
        rows["kind"].append("tech" if q.kind == "tech" else "outro")
    return rows


def bootstrap_ci(values: list[float], reps: int = 2000, seed: int = SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    arr = np.asarray(values)
    means = arr[rng.integers(0, len(arr), (reps, len(arr)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def summarize(rankings, queries, rels) -> dict:
    rows = per_query(rankings, queries, rels)
    top1 = lambda sel: [r[0][1] if r else 0.0 for r, q in zip(rankings, queries) if sel(q)]
    pos, neg = top1(lambda q: q.category != "absent"), top1(lambda q: q.category == "absent")
    t90 = float(np.percentile(pos, 10))  # limiar que mantém 90% das consultas com evidência
    out = {m: float(np.mean(v)) for m, v in rows.items() if m != "kind"}
    out["hit@3_ci"] = bootstrap_ci(rows["hit@3"])
    out["mrr_ci"] = bootstrap_ci(rows["mrr"])
    out["auc"] = auc(pos, neg)
    out["abstencao_90"] = float(np.mean([s < t90 for s in neg])) if neg else float("nan")
    for kind in ("tech", "outro"):
        vals = [h for h, kd in zip(rows["hit@3"], rows["kind"]) if kd == kind]
        out[f"hit@3_{kind}"] = float(np.mean(vals)) if vals else float("nan")
    out["n_com_evidencia"], out["n_sem_evidencia"] = len(pos), len(neg)
    return out


# ---------- execução ----------

def run_all(include_openai: bool = False) -> dict:
    chunks = load_chunks()
    texts = [c.text for c in chunks]
    rels = [relevant_set(chunks, q) for q in QUERIES]
    vecs = embed(texts, "passage")
    dense = rank_system(QUERIES, chunks, vecs, dense_only=True)
    bm25 = rank_bm25(QUERIES, chunks)
    strategies = {"dense": dense, "bm25": bm25, "sistema": rank_system(QUERIES, chunks, vecs), "rrf": rank_rrf(dense, bm25)}
    if include_openai:
        os.environ["EMBEDDINGS"] = "openai"
        try:
            strategies["dense_openai"] = rank_system(QUERIES, chunks, embed(texts, "passage"), dense_only=True)
        finally:
            os.environ["EMBEDDINGS"] = "local"
    result = {"n_chunks": len(chunks), "n_docs": len({c.source for c in chunks}), "n_queries": len(QUERIES),
              "estrategias": {name: summarize(r, QUERIES, rels) for name, r in strategies.items()}, "tamanho": {}}
    for size in (250, 450, 700):
        sized = load_chunks(size)
        with chunk_size(size):
            svecs = embed([c.text for c in sized], "passage")
            srels = [relevant_set(sized, q) for q in QUERIES]
            for name, dense_only in (("dense", True), ("sistema", False)):
                result["tamanho"][(size, name)] = dict(summarize(rank_system(QUERIES, sized, svecs, dense_only), QUERIES, srels),
                                                       n_chunks=len(sized))
    return result


def pct(x: float) -> str:
    return "-" if x != x else f"{100 * x:.0f}%"


def ci(pair: tuple[float, float]) -> str:
    return f"{100 * pair[0]:.0f}–{100 * pair[1]:.0f}%"


def render(res: dict) -> str:
    s = res["estrategias"]
    any_ = next(iter(s.values()))
    L = ["# Avaliação de retrieval (gerada por `eval/retrieval_eval.py`)", "",
         f"Corpus fictício: {res['n_docs']} documentos, {res['n_chunks']} trechos. Consultas: {res['n_queries']} "
         f"({any_['n_com_evidencia']} com evidência no corpus, {any_['n_sem_evidencia']} sem). Só busca, sem LLM.", "",
         "## Estratégias", "",
         "| Estratégia | Hit@1 | Hit@3 (IC 95%) | Hit@5 | Precisão@3 | Recall@3 | MRR (IC 95%) | AUC | Abstenção a 90% |",
         "|---|---|---|---|---|---|---|---|---|"]
    for name, m in s.items():
        L.append(f"| {name} | {pct(m['hit@1'])} | {pct(m['hit@3'])} ({ci(m['hit@3_ci'])}) | {pct(m['hit@5'])} | "
                 f"{pct(m['p@3'])} | {pct(m['r@3'])} | {m['mrr']:.2f} ({m['mrr_ci'][0]:.2f}–{m['mrr_ci'][1]:.2f}) | "
                 f"{m['auc']:.2f} | {pct(m['abstencao_90'])} |")
    L += ["", "## Hit@3 por tipo de requisito", "", "| Estratégia | Tecnologias | Responsabilidades e outros |", "|---|---|---|"]
    L += [f"| {n} | {pct(m['hit@3_tech'])} | {pct(m['hit@3_outro'])} |" for n, m in s.items()]
    L += ["", "## Tamanho do trecho (caracteres)", "",
          "| Tamanho | Estratégia | Trechos | Hit@3 | Precisão@3 | MRR | AUC |", "|---|---|---|---|---|---|---|"]
    for (size, name), m in res["tamanho"].items():
        L.append(f"| {size} | {name} | {m['n_chunks']} | {pct(m['hit@3'])} | {pct(m['p@3'])} | {m['mrr']:.2f} | {m['auc']:.2f} |")
    L += ["", "Como ler:",
          "- **Hit@K**: em quantas consultas com evidência existe ao menos um trecho relevante entre os K primeiros.",
          "- **Precisão@K / Recall@K**: fração dos K primeiros que é relevante / fração dos relevantes que foi recuperada. "
          "O Recall@K fica baixo por definição quando há muitos trechos relevantes (ex.: \"Git\" aparece em vários).",
          "- **MRR**: média de 1/posição do primeiro trecho relevante.",
          "- **AUC**: chance de a nota do melhor trecho de uma consulta COM evidência superar a de uma consulta SEM. "
          "0,5 = não separa; 1,0 = separa perfeitamente. Mede se dá para escolher um limiar de \"sem evidência\".",
          "- **Abstenção a 90%**: com o limiar que mantém 90% das consultas com evidência, quantas das sem evidência ficam de fora.",
          "- IC 95%: bootstrap sobre as consultas (2000 reamostragens). Diferenças dentro do intervalo não são conclusivas.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--openai", action="store_true", help="inclui embeddings da OpenAI (gasta API, centavos)")
    ap.add_argument("--out", type=Path, default=HERE / "results_retrieval.md")
    args = ap.parse_args()
    res = run_all(args.openai)
    args.out.write_text(render(res), encoding="utf-8")
    print(render(res))
    from jobassist import llm
    if llm.usage_summary():
        print(f"[custo] {llm.usage_summary()}", file=sys.stderr)


if __name__ == "__main__":
    main()
