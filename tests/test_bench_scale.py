import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import bench_scale as bs  # noqa: E402


def test_dados_sinteticos_sao_normalizados_e_reprodutiveis():
    a = bs.synthetic(500, np.random.default_rng(1))
    b = bs.synthetic(500, np.random.default_rng(1))
    assert a.shape == (500, bs.DIM) and np.allclose(np.linalg.norm(a, axis=1), 1, atol=1e-4) and np.array_equal(a, b)


def test_vizinhos_sao_bem_definidos_nos_dados_sinteticos():
    """O defeito que invalidou a 1ª versão: com ruído isotrópico todos os vizinhos eram quase empatados."""
    rng = np.random.default_rng(5)
    data = bs.synthetic(2000, rng)
    sims = bs.queries_from(data, rng) @ data.T
    top = -np.sort(-sims, axis=1)
    assert top[:, 0].mean() > 0.8  # a consulta está perto de um item que existe
    assert (top[:, 0] - top[:, 9]).mean() > 0.02  # e o 1º vizinho é visivelmente melhor que o 10º


def test_razao_de_nota_e_um_para_resultado_exato_e_menor_para_pior():
    rng = np.random.default_rng(2)
    data = bs.synthetic(500, rng)
    qs = bs.queries_from(data, rng)
    truth = bs.topk(qs @ data.T)
    assert bs.score_ratio(truth, qs, data, truth) == pytest.approx(1.0)
    pior = bs.topk(-(qs @ data.T))  # os 10 MAIS distantes
    assert bs.score_ratio(pior, qs, data, truth) < 0.5


def test_topk_devolve_os_melhores_em_ordem():
    scores = np.array([[0.1, 0.9, 0.5, 0.7, 0.3, 0.2, 0.05, 0.4, 0.6, 0.8, 0.0]])
    assert list(bs.topk(scores)[0][:3]) == [1, 9, 3]


def test_recall_conta_a_fracao_encontrada():
    truth = np.array([list(range(10))])
    assert bs.recall(np.array([list(range(10))]), truth) == 1.0
    assert bs.recall(np.array([list(range(5)) + [90, 91, 92, 93, 94]]), truth) == 0.5


def test_bench_pequeno_roda_e_a_busca_exata_e_consistente():
    row = bs.bench(1000, np.random.default_rng(3))
    assert row["n"] == 1000 and row["carga_ms"] > 0 and row["exata20_ms"] > 0
    assert row["cache_ms"] < row["carga_ms"]  # o cache existe para isso
    for chave in ("hnsw_recall", "faiss_hnsw_recall"):  # só existem se a biblioteca opcional estiver instalada
        if chave in row:
            assert 0.5 <= row[chave] <= 1.0


def test_render_formata_numeros_sem_estragar_o_texto():
    row = {"n": 20000, "mb": 30.7, "carga_antiga_ms": 120.0, "carga_ms": 40.0, "cache_ms": 0.01, "exata1_ms": 0.4, "exata1_p95": 0.5, "exata20_ms": 3.0, "exata20_p95": 3.5, "sim_top1": 0.95, "sim_top10": 0.9}
    if bs.hnswlib:
        row |= {"hnsw20_ms": 0.5, "hnsw_recall": 0.98, "hnsw_ratio": 0.999, "hnsw_build_s": 1.2}
    if bs.faiss:
        row |= {"faiss_flat20_ms": 3.0, "faiss_hnsw20_ms": 0.6, "faiss_hnsw_recall": 0.97, "faiss_hnsw_ratio": 0.998, "faiss_hnsw_build_s": 2.0}
    text = bs.render([row])
    assert "20 000" in text and "Dados sintéticos com estrutura de baixa dimensão, 384 dimensões" in text  # vírgulas do texto intactas
    assert "Antes (laço em Python, relendo o SQLite a cada análise): estoura o orçamento a partir de **20 000**" in text
    assert "Agora, em cache (servidor web de pé): dentro do orçamento até 20 000" in text  # cache: só a busca de 3 ms


def test_modo_dificil_gera_vizinhos_quase_empatados_e_o_facil_nao():
    """O difícil é o pior caso de propósito: o 1º vizinho mal se distingue do 10º, e por isso o recall exato engana."""
    rng = np.random.default_rng(5)
    gaps = {}
    for hard in (False, True):
        data = bs.synthetic(2000, rng, hard)
        assert np.allclose(np.linalg.norm(data, axis=1), 1, atol=1e-4)
        top = -np.sort(-(bs.queries_from(data, rng, hard) @ data.T), axis=1)
        gaps[hard] = (top[:, 0] - top[:, 9]).mean()
    assert gaps[False] > 0.1 and gaps[True] < 0.05  # medido: 0,19 contra 0,02
    row = bs.bench(500, np.random.default_rng(1), hard=True)
    assert row["n"] == 500 and row["exata20_ms"] > 0
