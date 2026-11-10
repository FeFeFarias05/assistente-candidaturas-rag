"""Integridade do corpus fictício e do gabarito: se isto falha, as métricas de avaliação não valem."""
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "eval" / "corpus"))
import retrieval_eval as ev  # noqa: E402
from build_corpus import DOCS, check  # noqa: E402
from jobassist.retrieve import term_pattern  # noqa: E402
from spec import FORBIDDEN, NEGATION_ONLY, PROJECTS, QUERIES  # noqa: E402

PROJECT = {"file": "x.md", "facts": ["Usei Flask na API"]}
OK = "Usei Flask na API. " + "Texto de enchimento sem nada proibido. " * 50


# ---------- validador de documentos ----------

def test_check_aceita_documento_valido():
    assert check(PROJECT, OK) == []


def test_check_pega_fato_ausente_termo_proibido_e_tamanho():
    assert any("fato ausente" in p for p in check(PROJECT, "Texto " * 400))
    assert any("termo proibido: Kubernetes" in p for p in check(PROJECT, OK + " Usei Kubernetes."))
    assert any("tamanho" in p for p in check(PROJECT, "Usei Flask na API"))


def test_check_negacao_so_no_documento_indicado():
    assert any("Docker só pode aparecer" in p for p in check(PROJECT, OK + " Não usei Docker."))
    assert check({"file": NEGATION_ONLY["Docker"], "facts": PROJECT["facts"]}, OK + " Não usei Docker.") == []


def test_check_nao_confunde_javascript_com_java():
    assert check(PROJECT, OK + " Escrevi JavaScript.") == []


# ---------- o corpus gerado ----------

def test_todos_os_documentos_existem_e_sao_validos():
    assert len(PROJECTS) == 25
    for p in PROJECTS:
        f = DOCS / p["file"]
        assert f.exists(), f"falta {p['file']}: rode eval/corpus/build_corpus.py"
        assert check(p, f.read_text(encoding="utf-8")) == [], p["file"]


@pytest.fixture(scope="module")
def chunks():
    return ev.load_chunks()


def test_tamanho_do_corpus(chunks):
    assert len({c.source for c in chunks}) == 25
    assert len(chunks) >= 120  # com 13 trechos o Recall@K não separa estratégia nenhuma


def test_nenhum_termo_ausente_existe_no_corpus(chunks):
    for q in QUERIES:
        if q.category == "absent":
            for term in q.evidence:
                assert not any(term_pattern(term).search(c.text) for c in chunks), f"{term} existe no corpus, mas deveria estar ausente"


def test_cada_consulta_com_evidencia_tem_resposta_no_corpus(chunks):
    for q in QUERIES:
        if q.category != "absent":
            assert ev.relevant_set(chunks, q), f"sem trecho relevante para: {q.text}"


def test_gabarito_tem_as_tres_categorias_e_consultas_unicas():
    cats = Counter(q.category for q in QUERIES)
    assert cats["present"] >= 55 and cats["negated"] == 4 and cats["absent"] >= 40
    assert len({q.text for q in QUERIES}) == len(QUERIES)
    assert {q.kind for q in QUERIES} <= {"tech", "responsibility", "soft", "other"}


def test_termos_de_negacao_so_existem_nos_documentos_certos(chunks):
    for term, only in NEGATION_ONLY.items():
        onde = {c.source for c in chunks if term_pattern(term).search(c.text)}
        assert onde == {only}, f"{term} apareceu em {onde}"


def test_forbidden_nao_inclui_o_que_e_do_perfil():
    for presente in ("Python", "React", "JavaScript", "TypeScript", "SQL", "PostgreSQL"):
        assert presente not in FORBIDDEN
