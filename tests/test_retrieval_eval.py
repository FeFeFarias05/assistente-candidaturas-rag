import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "eval" / "corpus"))
import retrieval_eval as ev  # noqa: E402
from spec import Q  # noqa: E402


def chunk(text, cid="a.md#c1"):
    return SimpleNamespace(id=cid, text=text, source=cid.split("#")[0])


# ---------- AUC ----------

def test_auc_perfeito_empate_e_vazio():
    assert ev.auc([0.9, 0.8], [0.1, 0.2]) == 1.0
    assert ev.auc([0.5], [0.5]) == 0.5
    assert ev.auc([0.1], [0.9]) == 0.0
    assert math.isnan(ev.auc([], [0.1]))


# ---------- métricas por consulta ----------

def test_metricas_com_ranking_conhecido():
    queries = [Q("x", "tech", "present", "a"), Q("y", "other", "present", "b")]
    rels = [{2}, {0, 5}]
    rankings = [[(0, .9), (1, .8), (2, .7)], [(5, .9), (9, .8), (0, .7)]]
    rows = ev.per_query(rankings, queries, rels)
    assert rows["hit@1"] == [0.0, 1.0] and rows["hit@3"] == [1.0, 1.0]
    assert rows["mrr"] == [pytest.approx(1 / 3), 1.0]
    assert rows["p@3"] == [pytest.approx(1 / 3), pytest.approx(2 / 3)]
    assert rows["r@3"] == [1.0, 1.0]  # 1 de 1 relevante; 2 de 2 relevantes
    assert rows["kind"] == ["tech", "outro"]


def test_consulta_sem_evidencia_nao_entra_nas_metricas_de_acerto():
    queries = [Q("x", "tech", "present", "a"), Q("C#", "tech", "absent", "C#")]
    rows = ev.per_query([[(0, .9)], [(0, .9)]], queries, [{0}, set()])
    assert rows["hit@1"] == [1.0]


def test_summarize_separa_evidencia_de_ausencia():
    queries = [Q("a", "tech", "present", "a"), Q("b", "tech", "present", "b"), Q("c", "tech", "absent", "c"), Q("d", "tech", "absent", "d")]
    rankings = [[(0, .9)], [(1, .8)], [(2, .2)], [(3, .1)]]
    m = ev.summarize(rankings, queries, [{0}, {1}, set(), set()])
    assert m["auc"] == 1.0 and m["abstencao_90"] == 1.0 and m["hit@1"] == 1.0
    assert (m["n_com_evidencia"], m["n_sem_evidencia"]) == (2, 2)


def test_bootstrap_e_deterministico_e_contem_a_media():
    vals = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0]
    lo, hi = ev.bootstrap_ci(vals)
    assert (lo, hi) == ev.bootstrap_ci(vals) and lo <= sum(vals) / len(vals) <= hi


# ---------- gabarito por texto ----------

def test_relevancia_por_texto_respeita_limite_de_palavra():
    chunks = [chunk("Usei SQLite e SQLAlchemy"), chunk("Escrevi consultas em SQL", "b.md#c1"), chunk("JavaScript apenas", "c.md#c1")]
    assert ev.relevant_set(chunks, Q("SQL", "tech", "present", "SQL")) == {1}  # SQLite/SQLAlchemy não valem
    assert ev.relevant_set(chunks, Q("Java", "tech", "present", "Java")) == set()  # dentro de JavaScript não vale
    assert ev.relevant_set(chunks, Q("C#", "tech", "absent", "C#")) == set()  # ausente: nunca há relevantes


def test_tamanho_do_trecho_e_restaurado():
    from jobassist import chunking
    antes = (chunking.MAX_CHARS, chunking.OVERLAP)
    with ev.chunk_size(200):
        assert chunking.MAX_CHARS == 200
    assert (chunking.MAX_CHARS, chunking.OVERLAP) == antes


# ---------- BM25 e RRF ----------

def test_bm25_acha_o_trecho_com_o_termo_e_nao_inventa_para_o_ausente():
    chunks = [chunk("Escrevi testes com pytest"), chunk("Usei Flask na API", "b.md#c1"), chunk("Trabalhei em equipe", "c.md#c1")]
    ranking = ev.rank_bm25([Q("pytest", "tech", "present", "pytest"), Q("Kubernetes", "tech", "absent", "Kubernetes")], chunks)
    assert ranking[0][0][0] == 0
    assert all(score == 0.0 for _, score in ranking[1])  # nenhuma palavra em comum: nota zero


def test_bm25_ignora_acentos_e_stopwords():
    assert ev.tokens("Avaliação da Execução") == ["avaliacao", "execucao"]


def test_rrf_favorece_o_que_aparece_bem_nas_duas_listas():
    a = [[(1, 0.9), (2, 0.8), (3, 0.7)]]
    b = [[(3, 5.0), (1, 4.0), (9, 3.0)]]
    fused = ev.rank_rrf(a, b)[0]
    assert [i for i, _ in fused][:2] == [1, 3]  # 1 e 3 estão nas duas
