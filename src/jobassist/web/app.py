"""Interface web local. Escuta só em 127.0.0.1: o servidor lê o seu material e usa a sua chave da API."""
import functools
import webbrowser
from pathlib import Path

import openai
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from .. import service, tracker

STATIC = Path(__file__).parent / "static"
REPORTS = (service.ROOT / "reports").resolve()
ALLOWED_HOSTS = {"127.0.0.1", "localhost"}
CSP = ("default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; "
       "script-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'self'; "
       "frame-ancestors 'none'")


def err(message: str, code: int):
    return jsonify({"error": message}), code


def _report_file(path_str: str | None) -> Path | None:
    """Só devolve arquivos dentro de reports/ (o caminho vem do banco ou do cliente)."""
    if not path_str:
        return None
    p = Path(path_str).resolve()
    return p if p.is_file() and REPORTS in p.parents else None


def _app_json(row: dict) -> dict:
    row = dict(row)
    row["has_report"] = _report_file(row.pop("report_path", None)) is not None
    return row


def _text(data: dict, key: str, required: bool = True, limit: int = 200) -> str | None:
    value = data.get(key)
    if value is None:
        if required:
            raise ValueError(f"Campo obrigatório: {key}.")
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > limit:  # em branco nunca vale
        raise ValueError(f"Valor inválido em {key}.")
    return value.strip()


def _json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Envie um JSON válido.")
    return data


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(STATIC), static_url_path="/static")
    app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    @app.before_request
    def guard():
        if request.host.rsplit(":", 1)[0].strip("[]") not in ALLOWED_HOSTS:
            return err("Host não permitido.", 403)
        # Sem este cabeçalho, uma página qualquer aberta no navegador poderia enviar arquivos ou
        # disparar análises (CSRF). Navegadores não enviam cabeçalho próprio entre origens sem preflight.
        if request.method not in ("GET", "HEAD") and request.headers.get("X-JobAssist") != "1":
            return err("Requisição recusada: falta o cabeçalho X-JobAssist.", 403)

    @app.after_request
    def headers(resp):
        resp.headers["Content-Security-Policy"] = CSP
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/"):
            resp.headers["Cache-Control"] = "no-store"
        return resp

    @app.errorhandler(413)
    def too_large(_):
        return err("Envio grande demais (limite de 60 MB por vez).", 413)

    @app.errorhandler(404)
    def not_found(_):
        return err("Não encontrado.", 404)

    @app.errorhandler(405)
    def not_allowed(_):
        return err("Método não permitido.", 405)

    def api(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            try:
                return fn(*a, **k)
            except service.PrivacyError as e:
                return err(str(e), 403)
            except service.NoMaterialError as e:
                return err(str(e), 409)
            except KeyError as e:
                return err(str(e.args[0]), 404)
            except ValueError as e:
                return err(str(e), 400)
            except openai.OpenAIError as e:
                return err(f"Falha na API da OpenAI ({type(e).__name__}). Confira a chave, o crédito e o modelo no .env.", 502)
            except RuntimeError as e:  # ex.: chave ou modelo ausentes no .env
                return err(str(e), 400)
            except HTTPException:
                raise  # 413 e afins têm tratamento próprio
            except Exception:
                app.logger.exception("erro inesperado")
                return err("Erro interno. Veja o terminal onde o servidor está rodando.", 500)
        return wrapper

    @app.get("/")
    def index():
        return send_from_directory(STATIC, "index.html")

    @app.get("/api/status")
    @api
    def status():
        return jsonify({**service.material_status(), "statuses": list(tracker.STATUSES)})

    @app.post("/api/analyze")
    @api
    def analyze():
        data = _json_body()
        result = service.run_analysis(data.get("vaga", ""), data.get("lang"), data.get("mode") == "full",
                                      data.get("confirm_send_all") is True)
        result["report_file"] = Path(result.pop("report_path")).name
        return jsonify(result)

    @app.get("/api/applications")
    @api
    def applications():
        return jsonify([_app_json(r) for r in tracker.list_all(request.args.get("status") or None)])

    @app.post("/api/applications")
    @api
    def add_application():
        data = _json_body()
        report = None
        if data.get("report"):
            f = _report_file(str(REPORTS / Path(str(data["report"])).name))
            report = str(f) if f else None
        def opt(key):  # campo opcional deixado em branco no formulário = valor padrão
            return None if data.get(key) in (None, "") else _text(data, key, False)

        n = tracker.add(_text(data, "company"), _text(data, "title"), opt("status") or "interessada",
                        opt("applied_on"), report)
        return jsonify(_app_json(tracker.get(n))), 201

    @app.patch("/api/applications/<int:app_id>")
    @api
    def edit_application(app_id: int):
        data = _json_body()
        tracker.update(app_id, company=_text(data, "company", False), title=_text(data, "title", False),
                       applied_on=_text(data, "applied_on", False), status=_text(data, "status", False))
        return jsonify(_app_json(tracker.get(app_id)))

    @app.delete("/api/applications/<int:app_id>")
    @api
    def delete_application(app_id: int):
        tracker.delete(app_id)
        return jsonify({"ok": True})

    @app.get("/api/applications/<int:app_id>/report")
    @api
    def application_report(app_id: int):
        f = _report_file(tracker.get(app_id)["report_path"])
        if f is None:
            raise KeyError("Esta candidatura não tem relatório (ou o arquivo não existe mais).")
        return jsonify({"report": f.read_text(encoding="utf-8")})

    @app.post("/api/material")
    @api
    def upload_material():
        saved, errors = [], []
        files = request.files.getlist("files")
        if not files:
            raise ValueError("Escolha pelo menos um arquivo.")
        for f in files:
            try:
                saved.append(service.save_upload(f.filename, f.read()))
            except ValueError as e:  # formato ou tamanho: segue com os outros
                errors.append({"name": f.filename, "error": str(e)})
        index = service.reindex() if saved else None
        return jsonify({"saved": saved, "errors": errors, "index": index})

    @app.delete("/api/material/<path:name>")
    @api
    def delete_material(name: str):
        service.delete_material(name)
        return jsonify({"ok": True, "index": service.reindex()})

    @app.post("/api/ingest")
    @api
    def reindex():
        return jsonify(service.reindex())

    return app


def serve(port: int = 8765, open_browser: bool = False) -> None:
    url = f"http://127.0.0.1:{port}"
    print(f"[web] {url}  (só nesta máquina; Ctrl+C para parar)")
    if open_browser:
        webbrowser.open(url)
    create_app().run(host="127.0.0.1", port=port, threaded=True, debug=False)
