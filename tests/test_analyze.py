import pytest

from jobassist import analyze, cli
from jobassist.material import Segment

JOB = {"title": "Dev Web", "company": "Acme S/A", "seniority": None, "language": "pt", "requirements": []}
SEGS = [Segment("cv.pdf#p1", "Python e Flask"), Segment("proj.md", "Projeto X")]


def test_prompt_tem_ids_e_idioma():
    p = analyze.build_prompt(JOB, SEGS, "en")
    assert "[cv.pdf#p1]\nPython e Flask" in p and "[proj.md]" in p and "inglês" in p


def test_lang_padrao_vem_da_vaga(monkeypatch):
    seen = {}
    monkeypatch.setattr(analyze, "complete", lambda prompt, system=None: seen.update(p=prompt) or "ok")
    assert analyze.analyze_no_rag(JOB, SEGS) == "ok" and "português" in seen["p"]


def test_save_report(tmp_path):
    path = analyze.save_report(JOB, "corpo", "sem RAG", tmp_path)
    assert "acme-s-a_dev-web" in path.name and "corpo" in path.read_text(encoding="utf-8")


def test_slug_vazio():
    assert analyze.slug(None) == "vaga" and analyze.slug("!!!") == "vaga"


def test_trava_de_privacidade(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("segredo pessoal", encoding="utf-8")
    monkeypatch.setenv("MATERIAL_DIR", str(tmp_path))
    vaga = tmp_path / "v.txt"
    vaga.write_text("vaga", encoding="utf-8")
    with pytest.raises(SystemExit):
        cli.main(["analyze", str(vaga), "--no-rag"])
