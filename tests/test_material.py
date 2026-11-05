from pathlib import Path

from jobassist.material import clean, load_material

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample"


def test_clean():
    assert clean("a   \n\n\n\nb  \n") == "a\n\nb"


def test_sample_le_os_tres_formatos_e_ignora_readme():
    ids = [s.id for s in load_material(SAMPLE)]
    assert "curriculo.pdf#p1" in ids
    assert "projeto_dashboard_react.md" in ids
    assert not any("README" in i for i in ids)


def test_pdf_tem_acentos():
    cv = next(s for s in load_material(SAMPLE) if s.id == "curriculo.pdf#p1")
    assert "experiência".upper() in cv.text.upper() and "Júnior" in cv.text


def test_txt_e_ids_unicos(tmp_path):
    (tmp_path / "a.txt").write_text("conteúdo de teste", encoding="utf-8")
    (tmp_path / "x.png").write_bytes(b"x")
    assert [s.id for s in load_material(tmp_path)] == ["a.txt"]
