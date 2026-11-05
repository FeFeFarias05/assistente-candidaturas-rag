import numpy as np
import pytest

from jobassist import analyze, cli
from jobassist.material import Segment

JOB = {"title": "Dev Web", "company": "Acme S/A", "seniority": None, "language": "pt",
       "requirements": [{"text": "Python", "kind": "tech", "required": True},
                        {"text": "C#", "kind": "tech", "required": True},
                        {"text": "web development", "kind": "tech", "required": True}]}
SEGS = [Segment("cv.pdf#p1", "Python e Flask"), Segment("proj.md", "Projeto X")]

BOM = """## Resumo da vaga
x
## Pontos fortes
- Python: usa Python e Flask [cv.pdf#p1]
## Lacunas
- C#: sem evidência no material
"""


def fake_llm(monkeypatch, *replies):
    seen = []
    it = iter(replies)
    monkeypatch.setattr(analyze, "complete", lambda prompt, system=None: seen.append(prompt) or next(it))
    return seen


# ---------- prompt ----------

def test_prompt_tem_ids_e_idioma():
    p = analyze.build_prompt(JOB, SEGS, "en")
    assert "[cv.pdf#p1]\nPython e Flask" in p and "[proj.md]" in p and "inglês" in p
    assert "TRECHOS ENCONTRADOS" not in p


def test_prompt_com_evidencia_marca_requisito_sem_trecho():
    from jobassist.retrieve import Hit, Retrieval
    ev = [Retrieval(JOB["requirements"][0], [Hit("cv.pdf#p1", "x", 0.9)]), Retrieval(JOB["requirements"][1], [])]
    p = analyze.build_prompt(JOB, SEGS, "pt", ev)
    assert "Python (tech, obrigatório): [cv.pdf#p1]" in p
    assert "C# (tech, obrigatório): NENHUM trecho relevante encontrado" in p


# ---------- validação (CA3, CA5) ----------

def test_citacao_inventada_e_detectada():
    body = "- Python [cv.pdf#p1] e Java [inventado.pdf#p9] e [outro.md]"
    assert analyze.invalid_citations(body, {"cv.pdf#p1", "outro.md"}) == ["inventado.pdf#p9"]


def test_colchetes_comuns_nao_sao_citacao():
    assert analyze.invalid_citations("veja [1] e [nota]", set()) == []


def test_tech_nos_pontos_fortes_sem_suporte_no_trecho_citado():
    texts = {"cv.pdf#p1": "Python e Flask", "proj.md": "Projeto X"}
    body = "## Pontos fortes\n- C#: domina C# [cv.pdf#p1]\n- Python [cv.pdf#p1]\n## Lacunas\n- nada"
    assert analyze.unsupported_techs(body, JOB, texts) == ["C#: citada em Pontos fortes sem aparecer no trecho citado"]


def test_tech_em_lacunas_nao_e_problema_e_termo_generico_e_ignorado():
    texts = {"cv.pdf#p1": "Python e Flask"}
    body = "## Pontos fortes\n- web development: estágio [cv.pdf#p1]\n## Lacunas\n- C#: sem evidência no material"
    assert analyze.unsupported_techs(body, JOB, texts) == []


def test_ponto_forte_que_admite_falta_de_evidencia():
    body = "## Pontos fortes\n- Python [cv.pdf#p1]\n- Gestão: sem evidência no material [cv.pdf#p1]\n## Lacunas\n- x"
    assert len(analyze.strengths_saying_no_evidence(body)) == 1
    assert analyze.strengths_saying_no_evidence(BOM) == []


def test_ponto_forte_sem_citacao_e_apontado():
    body = "## Pontos fortes\n- Python: sabe muito\n## Lacunas\n- x"
    assert analyze.unsupported_techs(body, JOB, {"cv.pdf#p1": "Python"})


# ---------- geração com retry ----------

def test_gera_sem_avisos(monkeypatch):
    fake_llm(monkeypatch, BOM)
    body, warnings = analyze.analyze_no_rag(JOB, SEGS)
    assert body == BOM and warnings == []


def test_retry_corrige_citacao_inventada(monkeypatch):
    ruim = BOM.replace("[cv.pdf#p1]", "[fantasma.pdf#p1]")
    seen = fake_llm(monkeypatch, ruim, BOM)
    body, warnings = analyze.analyze_no_rag(JOB, SEGS)
    assert body == BOM and warnings == [] and len(seen) == 2
    assert "fantasma.pdf#p1" in seen[1] and "CORREÇÃO" in seen[1]


def test_se_persistir_vira_aviso(monkeypatch):
    ruim = BOM.replace("[cv.pdf#p1]", "[fantasma.pdf#p1]")
    fake_llm(monkeypatch, ruim, ruim)
    _, warnings = analyze.analyze_no_rag(JOB, SEGS)
    assert "citação inexistente: [fantasma.pdf#p1]" in warnings


def test_lang_padrao_vem_da_vaga(monkeypatch):
    seen = fake_llm(monkeypatch, BOM)
    analyze.analyze_no_rag(JOB, SEGS)
    assert "português" in seen[0]


# ---------- RAG ----------

def test_rag_sem_nenhum_trecho_nao_chama_o_llm(monkeypatch):
    monkeypatch.setattr(analyze, "complete", lambda *a, **k: pytest.fail("não deveria chamar o LLM"))
    index = (["a#c1"], ["bolo"], np.eye(1, dtype=np.float32))
    monkeypatch.setattr("jobassist.retrieve.embed", lambda t, k="passage": np.zeros((len(t), 1), dtype=np.float32) + 0.01)
    body, warnings = analyze.analyze_rag(JOB, index)
    assert "não vou gerar sugestões" in body and warnings == []


def test_rag_sem_indice(monkeypatch):
    with pytest.raises(RuntimeError, match="ingest"):
        analyze.analyze_rag(JOB, None)


def test_rag_manda_so_os_trechos_recuperados(monkeypatch):
    seen = fake_llm(monkeypatch, BOM.replace("cv.pdf#p1", "cv.pdf#p1c1"))
    index = (["cv.pdf#p1c1", "x.md#c1"], ["Python e Flask", "bolo de cenoura"], np.eye(2, dtype=np.float32))
    monkeypatch.setattr("jobassist.retrieve.embed", lambda t, k="passage": np.tile(np.array([[0.9, 0.0]], dtype=np.float32), (len(t), 1)))
    body, warnings = analyze.analyze_rag(JOB, index)
    assert "[cv.pdf#p1c1]\nPython e Flask" in seen[0] and "bolo de cenoura" not in seen[0]
    assert warnings == []


# ---------- relatório ----------

def test_save_report_com_avisos(tmp_path):
    path = analyze.save_report(JOB, "corpo", "RAG", ["citação inexistente: [x.md]"], tmp_path)
    txt = path.read_text(encoding="utf-8")
    assert "acme-s-a_dev-web" in path.name and "corpo" in txt and "Avisos de validação" in txt


def test_save_report_sem_avisos_nao_mostra_bloco(tmp_path):
    assert "Avisos" not in analyze.save_report(JOB, "c", "RAG", [], tmp_path).read_text(encoding="utf-8")


def test_slug_vazio():
    assert analyze.slug(None) == "vaga" and analyze.slug("!!!") == "vaga"


def test_trava_de_privacidade(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("segredo pessoal", encoding="utf-8")
    monkeypatch.setenv("MATERIAL_DIR", str(tmp_path))
    vaga = tmp_path / "v.txt"
    vaga.write_text("vaga", encoding="utf-8")
    with pytest.raises(SystemExit):
        cli.main(["analyze", str(vaga), "--no-rag"])
