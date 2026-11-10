"""Benchmark de escala da busca vetorial: até quantos trechos a força bruta em NumPy basta?

Uso: python eval/bench_scale.py [--max-n 200000] [--out eval/results_escala.md]

Mede, para N de 1 mil a 200 mil vetores de 384 dimensões (o tamanho do modelo local), em dados SINTÉTICOS com
estrutura de clusters (vetores aleatórios puros não têm vizinhos de verdade e enganam a busca aproximada):
  carga        ler os N embeddings do SQLite com o ingest.load_index() do projeto (acontece a CADA análise hoje)
  exata        produto escalar com todos (NumPy) para 1 consulta e para um lote de 20 (os requisitos de uma vaga)
  hnswlib      índice aproximado HNSW: construção, consulta e recall@10 contra a busca exata
  faiss        IndexFlatIP (exata) e IndexHNSWFlat (aproximada), se instalados
Requer só NumPy; hnswlib e faiss-cpu são opcionais (pip install -r requirements-bench.txt).
"""
import argparse
import sqlite3
import statistics
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from jobassist.ingest import SCHEMA, load_index  # noqa: E402

DIM, K, BATCH, SEED = 384, 10, 20, 11
HARD = False  # ligado por --dificil, só para o texto do relatório
BUDGET_MS = 100  # "interativo": uma análise não deve esperar mais que isso só pela busca

try:
    import hnswlib
except ImportError:  # opcional
    hnswlib = None
try:
    import faiss
except ImportError:  # opcional
    faiss = None


LATENT = 32  # dimensão intrínseca: embeddings reais ocupam poucas direções das 384


def synthetic(n: int, rng: np.random.Generator, hard: bool = False) -> np.ndarray:
    """N vetores normalizados com estrutura de baixa dimensão: ~n/200 grupos num espaço latente de 32
    dimensões, projetado para 384 com um pouco de ruído. (Ruído isotrópico em 384 dimensões deixa todos os
    vizinhos quase equidistantes e faz o recall da busca aproximada parecer pior do que é.)"""
    clusters = max(20, n // 200)
    if hard:  # pior caso: grupos isotrópicos nas 384 dimensões, vizinhos quase empatados (como na 1ª versão)
        x = rng.normal(size=(clusters, DIM))[rng.integers(0, clusters, n)] + 0.35 * rng.normal(size=(n, DIM))
        x = x.astype(np.float32)
        return x / np.linalg.norm(x, axis=1, keepdims=True)
    z = rng.normal(size=(clusters, LATENT))[rng.integers(0, clusters, n)] + 0.6 * rng.normal(size=(n, LATENT))
    x = (z @ rng.normal(size=(LATENT, DIM)) / np.sqrt(LATENT) + 0.05 * rng.normal(size=(n, DIM))).astype(np.float32)
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def queries_from(data: np.ndarray, rng: np.random.Generator, hard: bool = False) -> np.ndarray:
    """Consultas vizinhas de itens que existem (como um requisito que tem evidência no material):
    o item mais 30% de ruído relativo à sua norma."""
    noise = rng.normal(size=(BATCH, DIM)).astype(np.float32)
    if hard:
        q = data[rng.integers(0, len(data), BATCH)] + 0.25 * noise  # ruído de norma ~5 sobre vetores de norma 1
        return (q / np.linalg.norm(q, axis=1, keepdims=True)).astype(np.float32)
    noise /= np.linalg.norm(noise, axis=1, keepdims=True)
    q = data[rng.integers(0, len(data), BATCH)] + 0.3 * noise
    return (q / np.linalg.norm(q, axis=1, keepdims=True)).astype(np.float32)


def topk(scores: np.ndarray, k: int = K) -> np.ndarray:
    part = np.argpartition(-scores, k, axis=1)[:, :k]
    order = np.argsort(-np.take_along_axis(scores, part, axis=1), axis=1)
    return np.take_along_axis(part, order, axis=1)


def timed(fn, reps: int) -> tuple[float, float]:
    """(mediana, p95) em milissegundos."""
    ts = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t0) * 1000)
    ts.sort()
    return statistics.median(ts), ts[min(len(ts) - 1, int(0.95 * len(ts)))]


def recall(found: np.ndarray, truth: np.ndarray) -> float:
    return float(np.mean([len(set(f) & set(t)) / K for f, t in zip(found, truth)]))


def score_ratio(found: np.ndarray, qs: np.ndarray, data: np.ndarray, truth: np.ndarray) -> float:
    """Nota média dos vizinhos devolvidos / nota média dos vizinhos exatos (1,0 = tão bons quanto os exatos).
    Justa quando há quase-empates: devolver o 11º vizinho em vez do 10º quase não perde nada."""
    sims = qs @ data.T
    got = np.take_along_axis(sims, np.clip(found, 0, len(data) - 1), axis=1).mean(axis=1)
    best = np.take_along_axis(sims, truth, axis=1).mean(axis=1)
    return float(np.mean(got / best))


def legacy_load(db_path: Path):
    """O carregador ANTIGO do projeto (laço em Python + vstack), mantido aqui só para o antes/depois."""
    con = sqlite3.connect(db_path)
    rows = con.execute("SELECT id, text, embedding FROM chunks ORDER BY id").fetchall()
    con.close()
    ids, texts, blobs = zip(*rows)
    return list(ids), list(texts), np.vstack([np.frombuffer(b, dtype=np.float32) for b in blobs])


def sqlite_with(data: np.ndarray, path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO chunks VALUES (?,?,?,?,?)",
                    ((f"d{i // 5}.md#c{i % 5}", f"d{i // 5}.md", "x", v.tobytes(), "h") for i, v in enumerate(data)))
    con.commit()
    con.close()


def bench(n: int, rng: np.random.Generator, hard: bool = False) -> dict:
    data = synthetic(n, rng, hard)
    qs = queries_from(data, rng, hard)
    row: dict = {"n": n, "mb": data.nbytes / 1e6}
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "i.db"
        sqlite_with(data, db)
        reps = 3 if n <= 50_000 else 1
        row["carga_antiga_ms"], _ = timed(lambda: legacy_load(db), reps)
        row["carga_ms"], _ = timed(lambda: load_index(db, use_cache=False), reps)  # a frio, carregador atual
        load_index(db)  # aquece o cache
        row["cache_ms"], _ = timed(lambda: load_index(db), 50)
    matrix = data
    sims = qs @ matrix.T
    truth = topk(sims)
    row["sim_top1"] = float(np.take_along_axis(sims, truth[:, :1], axis=1).mean())  # sanidade: vizinhos bem definidos
    row["sim_top10"] = float(np.take_along_axis(sims, truth[:, -1:], axis=1).mean())
    row["exata1_ms"], row["exata1_p95"] = timed(lambda: topk(qs[:1] @ matrix.T), 30)
    row["exata20_ms"], row["exata20_p95"] = timed(lambda: topk(qs @ matrix.T), 15)
    if hnswlib:
        idx = hnswlib.Index(space="ip", dim=DIM)
        t0 = time.perf_counter()
        idx.init_index(max_elements=n, ef_construction=200, M=16)
        idx.add_items(data, num_threads=-1)
        row["hnsw_build_s"] = time.perf_counter() - t0
        idx.set_ef(64)
        row["hnsw20_ms"], _ = timed(lambda: idx.knn_query(qs, k=K), 15)
        found = idx.knn_query(qs, k=K)[0].astype(np.int64)
        row["hnsw_recall"], row["hnsw_ratio"] = recall(found, truth), score_ratio(found, qs, data, truth)
    if faiss:
        flat = faiss.IndexFlatIP(DIM)
        flat.add(data)
        row["faiss_flat20_ms"], _ = timed(lambda: flat.search(qs, K), 15)
        hn = faiss.IndexHNSWFlat(DIM, 32, faiss.METRIC_INNER_PRODUCT)
        hn.hnsw.efConstruction = 200
        t0 = time.perf_counter()
        hn.add(data)
        row["faiss_hnsw_build_s"] = time.perf_counter() - t0
        hn.hnsw.efSearch = 64
        row["faiss_hnsw20_ms"], _ = timed(lambda: hn.search(qs, K), 15)
        found = hn.search(qs, K)[1].astype(np.int64)
        row["faiss_hnsw_recall"], row["faiss_hnsw_ratio"] = recall(found, truth), score_ratio(found, qs, data, truth)
    return row


def fmt(x, nd=1) -> str:
    return "-" if x is None else f"{x:,.{nd}f}".replace(",", " ")


def num(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def render(rows: list[dict]) -> str:
    has_h, has_f = hnswlib is not None, faiss is not None
    L = ["# Benchmark de escala da busca (gerado por `eval/bench_scale.py`)", "",
         f"Dados sintéticos {'DE PIOR CASO (isotrópicos, vizinhos quase empatados)' if HARD else 'com estrutura de baixa dimensão'}, {DIM} dimensões (como o modelo local), top-{K}. Consultas: 1 (isolada) e {BATCH} "
         "(os requisitos de uma vaga). Tempos em milissegundos (mediana). Máquina: a de quem rodou; compare as proporções, não os valores absolutos.", "",
         "## Tempo por análise: carregar o índice + buscar", "",
         "| Trechos (N) | Matriz | Carga antiga | Carga nova, a frio | Carga em cache | Busca exata, 1 consulta | Busca exata, 20 consultas | Total antes | Total agora, a frio | Total agora, em cache |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {num(r['n'])} | {fmt(r['mb'], 0)} MB | {fmt(r['carga_antiga_ms'])} | {fmt(r['carga_ms'])} | {fmt(r['cache_ms'], 3)} | "
                 f"{fmt(r['exata1_ms'], 2)} | {fmt(r['exata20_ms'], 2)} | **{fmt(r['carga_antiga_ms'] + r['exata20_ms'])}** | "
                 f"**{fmt(r['carga_ms'] + r['exata20_ms'])}** | **{fmt(r['cache_ms'] + r['exata20_ms'], 2)}** |")
    if has_h or has_f:
        L += ["", "## Busca aproximada (HNSW) × exata", "",
              "| N | Exata, 20 consultas | " + ("hnswlib: consulta / recall@10 / razão de nota / construção | " if has_h else "")
              + ("FAISS HNSW: consulta / recall@10 / razão de nota / construção | FAISS exata |" if has_f else ""),
              "|---|---|" + ("---|" if has_h else "") + ("---|---|" if has_f else "")]
        for r in rows:
            cells = [num(r["n"]), fmt(r["exata20_ms"], 2)]
            if has_h:
                cells.append(f"{fmt(r['hnsw20_ms'], 2)} / {r['hnsw_recall']:.2f} / {r['hnsw_ratio']:.3f} / {fmt(r['hnsw_build_s'])} s")
            if has_f:
                cells += [f"{fmt(r['faiss_hnsw20_ms'], 2)} / {r['faiss_hnsw_recall']:.2f} / {r['faiss_hnsw_ratio']:.3f} / {fmt(r['faiss_hnsw_build_s'])} s",
                          fmt(r["faiss_flat20_ms"], 2)]
            L.append("| " + " | ".join(cells) + " |")
    def first_over(fn):
        return next((r["n"] for r in rows if fn(r) > BUDGET_MS), None)

    def line(label, n):
        return (f"- {label}: estoura o orçamento a partir de **{num(n)}** trechos." if n
                else f"- {label}: dentro do orçamento até {num(rows[-1]['n'])} trechos.")

    L += [f"Orçamento de referência: {BUDGET_MS} ms só pela busca.",
          line("Antes (laço em Python, relendo o SQLite a cada análise)", first_over(lambda r: r["carga_antiga_ms"] + r["exata20_ms"])),
          line("Agora, a frio (carregador novo, primeira análise ou CLI)", first_over(lambda r: r["carga_ms"] + r["exata20_ms"])),
          line("Agora, em cache (servidor web de pé)", first_over(lambda r: r["cache_ms"] + r["exata20_ms"])), ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-n", type=int, default=200_000)
    ap.add_argument("--dificil", action="store_true", help="dados de pior caso para a busca aproximada (vizinhos quase empatados)")
    ap.add_argument("--out", type=Path, default=HERE / "results_escala.md")
    args = ap.parse_args()
    global HARD
    HARD = args.dificil
    rng = np.random.default_rng(SEED)
    rows = []
    for n in (1_000, 5_000, 20_000, 50_000, 100_000, 200_000):
        if n > args.max_n:
            break
        print(f"N={num(n)} ...", file=sys.stderr)
        rows.append(bench(n, rng, args.dificil))
    text = render(rows)
    args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
