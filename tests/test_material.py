from pathlib import Path

from jobassist.material import clean, load_material, redact

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


def test_redact_remove_dados_pessoais_e_mantem_o_resto():
    texto = "\n".join([
        "Fernanda Exemplo",
        "Endereço: Rua X, 10 – Porto Alegre",
        "Data de Nascimento: 01/02/2000 | 25 anos",
        "Email: fulana@exemplo.com",
        "Contato fulana@exemplo.com para detalhes",
        "Telefone: (51) 99999-0000",
        "Cel (51) 99999-0000",
        "CPF 123.456.789-09",
        "Linkedin: www.linkedin.com/in/fulana",
        "GitHub: https://github.com/fulana",
        "Graduanda 2023-2026 na PUCRS",
        "Reduzi o tempo de 4,2s para 2,1s",
    ])
    out, n = redact(texto)
    assert n == 7
    for sensivel in ("Rua X", "01/02/2000", "@exemplo.com", "99999", "123.456"):
        assert sensivel not in out
    for manter in ("Fernanda Exemplo", "linkedin.com/in/fulana", "github.com/fulana", "2023-2026", "4,2s"):
        assert manter in out


def test_load_material_aplica_redacao(tmp_path, capsys):
    (tmp_path / "cv.md").write_text("Sei Python.\nTelefone: (51) 98888-7777\nSei Flask.", encoding="utf-8")
    segs = load_material(tmp_path)
    assert "98888" not in segs[0].text and "Python" in segs[0].text and "Flask" in segs[0].text
    assert "1 linha(s) com dados pessoais" in capsys.readouterr().err


def test_txt_e_ids_unicos(tmp_path):
    (tmp_path / "a.txt").write_text("conteúdo de teste", encoding="utf-8")
    (tmp_path / "x.png").write_bytes(b"x")
    assert [s.id for s in load_material(tmp_path)] == ["a.txt"]
