import io

import openai
import pytest

from jobassist import service, tracker
from jobassist.web import app as webapp

H = {"X-JobAssist": "1"}  # cabeçalho que o front-end envia em toda requisição que altera algo


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    reports = tmp_path / "reports"
    reports.mkdir()
    mat = tmp_path / "material"
    mat.mkdir()
    monkeypatch.setattr(tracker, "DB_PATH", tmp_path / "apps.db")
    monkeypatch.setattr(webapp, "REPORTS", reports.resolve())
    monkeypatch.setenv("MATERIAL_DIR", str(mat))
    monkeypatch.setattr(service, "ingest", lambda folder, **k: {"novos": 1, "inalterados": 0, "removidos": 0})
    monkeypatch.setattr(service, "chunk_counts", lambda: {})
    app = webapp.create_app()
    return type("Ctx", (), {"client": app.test_client(), "app": app, "reports": reports, "mat": mat})


# ---------- proteções ----------

def test_host_estranho_e_recusado(ctx):
    assert ctx.client.get("/api/status", headers={"Host": "evil.example.com"}).status_code == 403
    assert ctx.client.get("/api/status", headers={"Host": "127.0.0.1:8765"}).status_code == 200
    assert ctx.client.get("/api/status", headers={"Host": "localhost:9"}).status_code == 200


def test_requisicao_que_altera_sem_cabecalho_e_recusada(ctx):
    r = ctx.client.post("/api/applications", json={"company": "A", "title": "x"})
    assert r.status_code == 403 and "X-JobAssist" in r.get_json()["error"]
    assert ctx.client.delete("/api/applications/1").status_code == 403
    assert ctx.client.post("/api/material", data={}).status_code == 403
    assert tracker.list_all() == []


def test_cabecalhos_de_seguranca(ctx):
    r = ctx.client.get("/api/status")
    assert "script-src 'self'" in r.headers["Content-Security-Policy"] and "frame-ancestors 'none'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["Cache-Control"] == "no-store"


def test_rotas_inexistentes_e_metodos_errados_devolvem_json(ctx):
    assert ctx.client.get("/api/nada").get_json() == {"error": "Não encontrado."}
    assert ctx.client.put("/api/status", headers=H).status_code == 405


# ---------- status ----------

def test_status(ctx):
    (ctx.mat / "cv.md").write_text("x", encoding="utf-8")
    s = ctx.client.get("/api/status").get_json()
    assert s["statuses"] == list(tracker.STATUSES) and s["is_sample"] is False
    assert [f["name"] for f in s["files"]] == ["cv.md"] and "api_key_set" in s
    assert "OPENAI_API_KEY" not in str(s)  # nunca devolve a chave, só se existe


# ---------- análise ----------

RESULT = {"job": {"title": "Dev", "company": "Acme"}, "report": "## Resumo da vaga\nok", "warnings": [],
          "mode": "RAG", "report_path": "/algum/lugar/reports/2026_acme.md", "usage": {"calls": 2, "cost_usd": None}}


def test_analyze_repassa_opcoes_e_nao_expoe_caminho_absoluto(ctx, monkeypatch):
    seen = {}
    monkeypatch.setattr(service, "run_analysis", lambda t, lang, no_rag, send_all: seen.update(
        t=t, lang=lang, no_rag=no_rag, send_all=send_all) or dict(RESULT))
    r = ctx.client.post("/api/analyze", headers=H, json={"vaga": "texto", "lang": "en", "mode": "full", "confirm_send_all": True})
    body = r.get_json()
    assert r.status_code == 200 and seen == {"t": "texto", "lang": "en", "no_rag": True, "send_all": True}
    assert body["report_file"] == "2026_acme.md" and "report_path" not in body and "/algum/lugar" not in str(body)


def test_confirmacao_so_vale_se_for_exatamente_true(ctx, monkeypatch):
    seen = {}
    monkeypatch.setattr(service, "run_analysis", lambda t, lang, no_rag, send_all: seen.update(s=send_all) or dict(RESULT))
    ctx.client.post("/api/analyze", headers=H, json={"vaga": "x", "mode": "full", "confirm_send_all": "false"})
    assert seen["s"] is False  # a string "false" não vale como confirmação


@pytest.mark.parametrize("exc,code", [
    (service.PrivacyError("envia tudo"), 403),
    (service.NoMaterialError("sem material"), 409),
    (ValueError("Cole o texto da vaga."), 400),
    (RuntimeError("OPENAI_API_KEY ausente"), 400),
    (openai.OpenAIError("detalhe interno com sk-segredo"), 502),
])
def test_analyze_mapeia_erros(ctx, monkeypatch, exc, code):
    def boom(*a):
        raise exc
    monkeypatch.setattr(service, "run_analysis", boom)
    r = ctx.client.post("/api/analyze", headers=H, json={"vaga": "x"})
    assert r.status_code == code and r.get_json()["error"]
    assert "sk-segredo" not in r.get_data(as_text=True)  # detalhes da API não vazam


def test_erro_inesperado_nao_vaza_detalhes(ctx, monkeypatch):
    def boom(*a):
        raise ZeroDivisionError("detalhe interno /Users/alguem/arquivo.py")
    monkeypatch.setattr(service, "run_analysis", boom)
    r = ctx.client.post("/api/analyze", headers=H, json={"vaga": "x"})
    assert r.status_code == 500 and "Users" not in r.get_data(as_text=True)


@pytest.mark.parametrize("payload", ["não é json", "[1, 2]", "null"])
def test_analyze_exige_json_objeto(ctx, payload):
    r = ctx.client.post("/api/analyze", headers={**H, "Content-Type": "application/json"}, data=payload)
    assert r.status_code == 400


# ---------- candidaturas ----------

def test_crud_de_candidaturas(ctx):
    r = ctx.client.post("/api/applications", headers=H, json={"company": " Acme ", "title": "Dev Web", "status": "candidatei", "applied_on": "2026-05-06"})
    assert r.status_code == 201
    a = r.get_json()
    assert (a["company"], a["status"], a["has_report"]) == ("Acme", "candidatei", False) and "report_path" not in a
    r = ctx.client.patch(f"/api/applications/{a['id']}", headers=H, json={"status": "entrevista", "title": "Dev Sênior"})
    assert (r.get_json()["status"], r.get_json()["title"], r.get_json()["company"]) == ("entrevista", "Dev Sênior", "Acme")
    assert [x["id"] for x in ctx.client.get("/api/applications?status=entrevista").get_json()] == [a["id"]]
    assert ctx.client.get("/api/applications?status=recusada").get_json() == []
    assert ctx.client.delete(f"/api/applications/{a['id']}", headers=H).get_json() == {"ok": True}
    assert tracker.list_all() == []


@pytest.mark.parametrize("payload", [
    {"company": "", "title": "x"}, {"company": "A"}, {"company": 5, "title": "x"},
    {"company": "A", "title": "x" * 201}, {"company": "A", "title": "x", "status": "aprovada"},
    {"company": "A", "title": "x", "applied_on": "ontem"},
])
def test_candidatura_invalida_e_recusada(ctx, payload):
    assert ctx.client.post("/api/applications", headers=H, json=payload).status_code == 400
    assert tracker.list_all() == []


def test_editar_ou_apagar_id_inexistente_e_404_e_patch_vazio_e_400(ctx):
    assert ctx.client.patch("/api/applications/99", headers=H, json={"title": "x"}).status_code == 404
    assert ctx.client.delete("/api/applications/99", headers=H).status_code == 404
    i = tracker.add("A", "x")
    assert ctx.client.patch(f"/api/applications/{i}", headers=H, json={}).status_code == 400
    assert ctx.client.patch(f"/api/applications/{i}", headers=H, json={"company": ""}).status_code == 400


def test_campos_opcionais_em_branco_no_formulario_usam_o_padrao(ctx):
    r = ctx.client.post("/api/applications", headers=H, json={"company": "A", "title": "x", "status": "", "applied_on": ""})
    a = r.get_json()
    assert r.status_code == 201 and a["status"] == "interessada" and a["applied_on"]


def test_relatorio_da_candidatura(ctx):
    (ctx.reports / "r1.md").write_text("# Dev | Acme\n## Resumo da vaga\ntexto", encoding="utf-8")
    r = ctx.client.post("/api/applications", headers=H, json={"company": "Acme", "title": "Dev", "report": "r1.md"})
    a = r.get_json()
    assert a["has_report"] is True
    assert "texto" in ctx.client.get(f"/api/applications/{a['id']}/report").get_json()["report"]


def test_relatorio_so_dentro_de_reports(ctx, tmp_path):
    (tmp_path / "segredo.md").write_text("fora de reports", encoding="utf-8")
    # cliente tenta apontar para fora: só o nome do arquivo conta, e ele não existe em reports/
    r = ctx.client.post("/api/applications", headers=H, json={"company": "A", "title": "x", "report": "../segredo.md"})
    assert r.get_json()["has_report"] is False
    # banco com caminho fora de reports/ (ex.: editado à mão): a leitura é recusada
    i = tracker.add("B", "y", report_path=str(tmp_path / "segredo.md"))
    r = ctx.client.get(f"/api/applications/{i}/report")
    assert r.status_code == 404 and "fora de reports" not in r.get_data(as_text=True)
    assert ctx.client.get("/api/applications/999/report").status_code == 404


# ---------- material ----------

def _file(name, content=b"conteudo"):
    return (io.BytesIO(content), name)


def test_upload_aceita_bons_recusa_ruins_e_reindexa(ctx):
    r = ctx.client.post("/api/material", headers=H, content_type="multipart/form-data",
                        data={"files": [_file("notas.md"), _file("virus.exe"), _file("../../fuga.txt")]})
    body = r.get_json()
    assert r.status_code == 200 and sorted(body["saved"]) == ["fuga.txt", "notas.md"]
    assert [e["name"] for e in body["errors"]] == ["virus.exe"] and body["index"]["novos"] == 1
    assert sorted(f.name for f in ctx.mat.iterdir()) == ["fuga.txt", "notas.md"]


def test_upload_sem_arquivo_ou_so_com_ruins(ctx):
    assert ctx.client.post("/api/material", headers=H, data={}).status_code == 400
    r = ctx.client.post("/api/material", headers=H, content_type="multipart/form-data", data={"files": [_file("x.exe")]})
    assert r.get_json()["saved"] == [] and r.get_json()["index"] is None


def test_upload_na_pasta_de_exemplo_e_proibido(ctx, monkeypatch):
    monkeypatch.setenv("MATERIAL_DIR", "data/sample")
    r = ctx.client.post("/api/material", headers=H, content_type="multipart/form-data", data={"files": [_file("x.md")]})
    assert r.status_code == 403 and not (service.SAMPLE / "x.md").exists()
    assert ctx.client.delete("/api/material/curriculo.pdf", headers=H).status_code == 403
    assert (service.SAMPLE / "curriculo.pdf").exists()


def test_apagar_material_e_traversal(ctx, tmp_path):
    (ctx.mat / "a.md").write_text("x", encoding="utf-8")
    (tmp_path / "fora.md").write_text("não mexer", encoding="utf-8")
    assert ctx.client.delete("/api/material/a.md", headers=H).get_json()["ok"] is True
    assert not (ctx.mat / "a.md").exists()
    for alvo in ("..%2Ffora.md", "../fora.md", "nao_existe.md"):
        assert ctx.client.delete(f"/api/material/{alvo}", headers=H).status_code == 404
    assert (tmp_path / "fora.md").exists()


def test_envio_grande_demais_da_413_em_json(ctx):
    ctx.app.config["MAX_CONTENT_LENGTH"] = 100
    r = ctx.client.post("/api/material", headers=H, content_type="multipart/form-data",
                        data={"files": [_file("a.md", b"x" * 5000)]})
    assert r.status_code == 413 and "grande demais" in r.get_json()["error"]


def test_reindexar(ctx):
    assert ctx.client.post("/api/ingest", headers=H).get_json()["novos"] == 1
