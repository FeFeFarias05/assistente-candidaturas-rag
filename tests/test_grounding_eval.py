import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "eval"))
import grounding_eval as ge  # noqa: E402

BODY = """## Resumo da vaga
A vaga pede Python. [cv.pdf#p1c1]
## Pontos fortes
- Python: usa Python em projetos [cv.pdf#p1c1] [proj.md#c2]
- curto [x.md]
- Sem citação nenhuma sobre Flask na API
## Lacunas
- Kubernetes: sem evidência
## O que destacar no currículo
- Projeto com API em Flask [proj.md#c2]
## Rascunho de mensagem
RASCUNHO, revisar antes de usar.
Olá, trabalho com Python e Flask há um ano. [cv.pdf#p1c1]
Fico à disposição para conversar.
"""


# ---------- extração das afirmações ----------

def test_parse_claims_pega_as_tres_secoes_e_ignora_resumo_e_lacunas():
    claims = ge.parse_claims(BODY)
    textos = [(c["section"], c["text"]) for c in claims]
    assert ("Pontos fortes", "Python: usa Python em projetos") in textos
    assert ("O que destacar no currículo", "Projeto com API em Flask") in textos
    assert ("Rascunho de mensagem", "Olá, trabalho com Python e Flask há um ano.") in textos
    assert not any("Kubernetes" in t or "A vaga pede" in t for _, t in textos)  # Lacunas e Resumo ficam de fora
    assert not any(t.lower().startswith("rascunho") for _, t in textos)  # a marca não é afirmação


def test_parse_claims_guarda_os_ids_citados_e_descarta_itens_minusculos():
    claims = {c["text"]: c for c in ge.parse_claims(BODY)}
    assert claims["Python: usa Python em projetos"]["cited"] == ["cv.pdf#p1c1", "proj.md#c2"]
    assert claims["Sem citação nenhuma sobre Flask na API"]["cited"] == []
    assert "curto" not in claims  # menos de 12 caracteres


def test_evidence_for_junta_os_trechos_citados_sem_repetir_nem_inventar():
    texts = {"a#c1": "texto A", "b#c1": "texto B"}
    ev = ge.evidence_for(["a#c1", "a#c1", "inexistente#c9", "b#c1"], texts)
    assert ev.count("[a#c1]") == 1 and "texto B" in ev and "inexistente" not in ev
    assert ge.evidence_for([], texts) == ""


# ---------- checagem determinística ----------

def test_literal_check():
    techs = ["Python", "C#", "web development"]
    assert ge.literal_check("Domina Python", "Usei Python e Flask", techs) is True
    assert ge.literal_check("Domina C#", "Usei Python e Flask", techs) is False
    assert ge.literal_check("Boa comunicação", "qualquer coisa", techs) is None  # não cita tecnologia
    assert ge.literal_check("web development no estágio", "estágio", techs) is None  # termo de várias palavras é ignorado


# ---------- métricas ----------

def row(mode, label, section="Pontos fortes", cited=("a#c1",)):
    return {"mode": mode, "label": label, "section": section, "cited": list(cited)}


def test_aggregate_calcula_taxas_por_modo_e_secao():
    rows = [row("rag", "SUPPORTED"), row("rag", "SUPPORTED"), row("rag", "PARTIAL"), row("rag", "UNSUPPORTED", cited=()),
            row("full", "SUPPORTED", "Rascunho de mensagem")]
    agg = ge.aggregate(rows)
    r = agg["rag"]["rates"]
    assert agg["rag"]["n"] == 4 and r["SUPPORTED"] == 0.5 and r["PARTIAL"] == 0.25 and r["UNSUPPORTED"] == 0.25 and r["uncited"] == 0.25
    assert agg["full"]["sections"]["Rascunho de mensagem"]["rates"]["SUPPORTED"] == 1.0
    assert agg["full"]["sections"]["Pontos fortes"]["n"] == 0


def test_kappa_perfeito_acaso_e_vazio():
    a = ["SUPPORTED", "PARTIAL", "UNSUPPORTED", "SUPPORTED"]
    assert ge.cohen_kappa(a, a) == 1.0
    assert ge.cohen_kappa(["SUPPORTED"] * 4, ["SUPPORTED"] * 4) == 1.0  # um só rótulo nos dois: sem divisão por zero
    assert ge.cohen_kappa(["SUPPORTED", "UNSUPPORTED"] * 2, ["UNSUPPORTED", "SUPPORTED"] * 2) == -1.0
    assert math.isnan(ge.cohen_kappa([], []))


def test_agreement_conta_aprovacao_a_mais_e_a_menos():
    human = ["SUPPORTED", "PARTIAL", "UNSUPPORTED", "SUPPORTED"]
    judge = ["SUPPORTED", "SUPPORTED", "SUPPORTED", "PARTIAL"]
    r = ge.agreement(human, judge)
    assert r["n"] == 4 and r["acuracia"] == 0.25
    assert r["aprova_a_mais"] == 2 and r["reprova_a_mais"] == 1  # juiz foi mais generoso do que a pessoa


# ---------- juiz ----------

def test_afirmacao_sem_citacao_nao_vai_ao_juiz_e_e_reprovada(monkeypatch):
    chamadas = []
    monkeypatch.setattr(ge.llm, "complete", lambda prompt, system=None, schema=None, model=None:
                        chamadas.append((prompt, model)) or {"verdicts": [{"id": 1, "label": "SUPPORTED", "reason": "ok"}]})
    claims = [{"text": "sem fonte", "evidence": ""}, {"text": "com fonte", "evidence": "[a#c1]\ntexto"}]
    out = ge.judge_report(claims, "gpt-juiz")
    assert out[0] == {"label": "UNSUPPORTED", "reason": "sem citação"} and out[1]["label"] == "SUPPORTED"
    assert len(chamadas) == 1 and chamadas[0][1] == "gpt-juiz" and "sem fonte" not in chamadas[0][0]


def test_veredito_ausente_vira_nao_sustentada(monkeypatch):
    monkeypatch.setattr(ge.llm, "complete", lambda *a, **k: {"verdicts": []})
    out = ge.judge_report([{"text": "x" * 20, "evidence": "[a#c1]\nt"}], None)
    assert out[0]["label"] == "UNSUPPORTED"  # na dúvida, não aprova


def test_sem_nenhuma_afirmacao_citada_nao_chama_o_juiz(monkeypatch):
    monkeypatch.setattr(ge.llm, "complete", lambda *a, **k: pytest.fail("não deveria gastar API"))
    assert ge.judge_report([{"text": "x" * 20, "evidence": ""}], None)[0]["label"] == "UNSUPPORTED"


def test_render_avisa_quando_o_juiz_e_o_proprio_gerador():
    rows = [{**row("rag", "SUPPORTED"), "job": "j", "claim": "c", "reason": "r", "literal_ok": None}]
    assert "o mesmo modelo que escreveu" in ge.render(rows, "m1", "m1", None)
    assert "o mesmo modelo que escreveu" not in ge.render(rows, "m1", "m2", None)
