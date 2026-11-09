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


def _zip(path, files: dict):
    import zipfile
    with zipfile.ZipFile(path, "w") as z:
        for name, xml in files.items():
            z.writestr(name, xml)


def _docx(path, paragraphs):
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    body = "".join(f"<w:p><w:r><w:t>{p}</w:t></w:r></w:p>" for p in paragraphs)
    _zip(path, {"word/document.xml": f'<w:document {ns}><w:body>{body}</w:body></w:document>'})


def _pptx(path, slides: dict[int, list[str]]):
    ns = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
    _zip(path, {f"ppt/slides/slide{n}.xml": f"<p {ns}>" + "".join(f"<a:p><a:r><a:t>{t}</a:t></a:r></a:p>" for t in texts) + "</p>"
                for n, texts in slides.items()})


def test_docx_le_paragrafos_com_acentos(tmp_path):
    _docx(tmp_path / "projeto.docx", ["Gerenciador de tarefas", "Usei Python e Flask na disciplina de Engenharia."])
    segs = load_material(tmp_path)
    assert [s.id for s in segs] == ["projeto.docx"]
    assert "Gerenciador de tarefas\nUsei Python e Flask" in segs[0].text


def test_pptx_um_segmento_por_slide_em_ordem_numerica(tmp_path):
    _pptx(tmp_path / "deck.pptx", {10: ["Resultados do projeto"], 2: ["Stack", "React e TypeScript"], 1: []})
    segs = load_material(tmp_path)
    assert [s.id for s in segs] == ["deck.pptx#s2", "deck.pptx#s10"]  # slide 1 vazio some; 2 vem antes de 10
    assert segs[0].text == "Stack\nReact e TypeScript"


def test_docx_e_pptx_passam_pela_redacao(tmp_path):
    _docx(tmp_path / "cv.docx", ["Sei Python", "Telefone: (51) 98888-7777"])
    assert "98888" not in load_material(tmp_path)[0].text


def test_arquivo_corrompido_avisa_e_nao_derruba(tmp_path, capsys):
    (tmp_path / "quebrado.docx").write_bytes(b"isso nao e um zip")
    (tmp_path / "ok.md").write_text("conteúdo válido para o teste", encoding="utf-8")
    assert [s.id for s in load_material(tmp_path)] == ["ok.md"]
    assert "não consegui ler quebrado.docx" in capsys.readouterr().err


def test_docx_sem_a_parte_principal_avisa(tmp_path, capsys):
    _zip(tmp_path / "vazio.docx", {"outra/coisa.xml": "<x/>"})
    assert load_material(tmp_path) == []
    assert "não consegui ler vazio.docx" in capsys.readouterr().err


def test_chunk_de_slide_tem_id_citavel(tmp_path):
    from jobassist.analyze import CITATION
    from jobassist.chunking import chunk_all
    _pptx(tmp_path / "deck.pptx", {3: ["Projeto com React"]})
    cid = chunk_all(load_material(tmp_path))[0].id
    assert cid == "deck.pptx#s3c1" and CITATION.findall(f"Usou React [{cid}]") == [cid]


def test_txt_e_ids_unicos(tmp_path):
    (tmp_path / "a.txt").write_text("conteúdo de teste", encoding="utf-8")
    (tmp_path / "x.png").write_bytes(b"x")
    assert [s.id for s in load_material(tmp_path)] == ["a.txt"]
