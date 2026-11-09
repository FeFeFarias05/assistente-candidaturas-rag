import pytest

from jobassist import service

JOB = {"title": "Dev", "company": "Acme", "seniority": None, "language": "pt", "requirements": []}


@pytest.fixture
def private(tmp_path, monkeypatch):
    """Pasta de material 'real' (não é a de exemplo) e relatórios/índice isolados."""
    mat = tmp_path / "material"
    mat.mkdir()
    monkeypatch.setenv("MATERIAL_DIR", str(mat))
    monkeypatch.setattr(service, "save_report", lambda job, body, mode, warnings: tmp_path / "r.md")
    monkeypatch.setattr(service, "ingest", lambda folder, **k: {"novos": 0, "inalterados": 0, "removidos": 0})
    monkeypatch.setattr(service, "chunk_counts", lambda: {})
    return mat


# ---------- run_analysis ----------

@pytest.mark.parametrize("text,lang", [("", None), ("   \n", None), ("x" * (service.MAX_JOB_CHARS + 1), None), ("vaga", "fr")])
def test_entradas_invalidas(private, text, lang):
    with pytest.raises(ValueError):
        service.run_analysis(text, lang)


def test_material_inteiro_fora_do_exemplo_exige_confirmacao(private):
    (private / "cv.md").write_text("Sei Python e Flask muito bem.", encoding="utf-8")
    with pytest.raises(service.PrivacyError, match="TODO o conteúdo"):
        service.run_analysis("vaga", no_rag=True)


def test_material_inteiro_confirmado_roda(private, monkeypatch):
    (private / "cv.md").write_text("Sei Python e Flask muito bem.", encoding="utf-8")
    monkeypatch.setattr(service, "extract_job", lambda t: JOB)
    monkeypatch.setattr(service, "analyze_no_rag", lambda job, segs, lang: ("## Resumo da vaga\nok", ["aviso"]))
    out = service.run_analysis("vaga", no_rag=True, send_all=True)
    assert out["mode"] == "sem RAG" and out["warnings"] == ["aviso"] and out["job"] == JOB
    assert out["report_path"].endswith("r.md") and "calls" in out["usage"]


def test_modo_inteiro_sem_arquivos(private):
    with pytest.raises(service.NoMaterialError):
        service.run_analysis("vaga", no_rag=True, send_all=True)


def test_rag_sem_indice_da_erro_claro_sem_chamar_o_llm(private, monkeypatch):
    monkeypatch.setattr(service, "load_index", lambda: None)
    monkeypatch.setattr(service, "extract_job", lambda t: pytest.fail("não deveria gastar API sem material"))
    with pytest.raises(service.NoMaterialError, match="aba Material"):
        service.run_analysis("vaga")


def test_rag_normaliza_idioma_vazio(private, monkeypatch):
    seen = {}
    monkeypatch.setattr(service, "load_index", lambda: object())
    monkeypatch.setattr(service, "extract_job", lambda t: JOB)
    monkeypatch.setattr(service, "analyze_rag", lambda job, idx, lang: seen.update(lang=lang) or ("corpo", []))
    out = service.run_analysis("vaga", lang="")
    assert seen["lang"] is None and out["mode"] == "RAG"


# ---------- material ----------

def test_status_lista_so_formatos_aceitos(private, monkeypatch):
    (private / "cv.pdf").write_bytes(b"x")
    (private / "notas.md").write_text("n", encoding="utf-8")
    (private / "README.md").write_text("não é material", encoding="utf-8")
    (private / "foto.png").write_bytes(b"x")
    monkeypatch.setattr(service, "chunk_counts", lambda: {"notas.md": 3})
    s = service.material_status()
    assert [f["name"] for f in s["files"]] == ["cv.pdf", "notas.md"]
    assert s["files"][1]["chunks"] == 3 and s["files"][0]["chunks"] is None
    assert s["is_sample"] is False and isinstance(s["api_key_set"], bool)


def test_status_do_material_de_exemplo(monkeypatch):
    monkeypatch.setenv("MATERIAL_DIR", "data/sample")
    s = service.material_status()
    assert s["is_sample"] is True and s["folder"] == "data/sample" and len(s["files"]) >= 4


def test_upload_e_delete(private):
    name = service.save_upload("Meu Currículo (2026).pdf", b"%PDF")
    assert name == "Meu Currículo (2026).pdf"  # acentos e espaços são mantidos
    assert (private / name).read_bytes() == b"%PDF"
    service.delete_material(name)
    assert list(private.iterdir()) == []


def test_upload_troca_caracteres_perigosos(private):
    assert service.save_upload("rel<>|atório?.md", b"x") == "rel___atório_.md"


def test_upload_nao_escapa_da_pasta(private):
    name = service.save_upload("../../fora.md", b"conteudo")
    assert name == "fora.md" and (private / "fora.md").exists()
    assert not (private.parent.parent / "fora.md").exists()


@pytest.mark.parametrize("nome", ["virus.exe", "sem_extensao", "", "README.md", ".md"])
def test_upload_recusa_formato_ou_nome_reservado(private, nome):
    with pytest.raises(ValueError):
        service.save_upload(nome, b"x")


def test_upload_grande_demais(private, monkeypatch):
    monkeypatch.setattr(service, "MAX_UPLOAD", 10)
    with pytest.raises(ValueError, match="maior que"):
        service.save_upload("a.md", b"x" * 11)


def test_delete_nao_sai_da_pasta_nem_apaga_o_que_nao_e_material(private):
    (private.parent / "segredo.md").write_text("fora da pasta", encoding="utf-8")
    (private / "foto.png").write_bytes(b"x")
    for alvo in ("../segredo.md", "foto.png", "nao_existe.md", "../../etc/passwd"):
        with pytest.raises(KeyError):
            service.delete_material(alvo)
    assert (private.parent / "segredo.md").exists() and (private / "foto.png").exists()


def test_exemplo_nunca_recebe_nem_perde_arquivos(monkeypatch):
    monkeypatch.setenv("MATERIAL_DIR", "data/sample")
    with pytest.raises(service.PrivacyError, match="MATERIAL_DIR"):
        service.save_upload("x.md", b"x")
    with pytest.raises(service.PrivacyError):
        service.delete_material("curriculo.pdf")
    assert (service.SAMPLE / "curriculo.pdf").exists()


def test_pasta_relativa_vale_a_partir_da_raiz_do_projeto(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)  # rodar de outro diretório não muda o material
    monkeypatch.setenv("MATERIAL_DIR", "data/sample")
    assert service.material_folder() == service.SAMPLE


def test_reindex_chama_o_ingest(private, monkeypatch):
    monkeypatch.setattr(service, "ingest", lambda folder: {"novos": 1, "inalterados": 0, "removidos": 0, "pasta": folder})
    assert service.reindex()["pasta"] == private.resolve()
