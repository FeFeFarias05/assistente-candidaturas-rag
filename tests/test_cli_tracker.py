import pytest

from jobassist import cli, tracker

JOB = {"title": "Dev Web", "company": "Acme", "seniority": None, "language": "pt", "requirements": []}


@pytest.fixture(autouse=True)
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(tracker, "DB_PATH", tmp_path / "apps.db")  # nunca toca no banco real


def test_add_list_status_fluxo_completo(capsys):
    cli.main(["add", "Acme", "Dev Web", "--status", "candidatei", "--date", "2026-11-05"])
    cli.main(["list"])
    out = capsys.readouterr().out
    assert "#1" in out and "2026-11-05" in out and "candidatei" in out and "Acme | Dev Web" in out
    cli.main(["status", "1", "entrevista"])
    cli.main(["list", "--status", "entrevista"])
    assert "entrevista" in capsys.readouterr().out.split("agora está")[-1]


def test_list_vazio(capsys):
    cli.main(["list"])
    assert "nenhuma candidatura" in capsys.readouterr().out


def test_status_de_id_inexistente_da_erro_claro(capsys):
    with pytest.raises(SystemExit):
        cli.main(["status", "42", "oferta"])
    assert "42" in capsys.readouterr().err


def test_status_invalido_e_recusado_pelo_argparse():
    with pytest.raises(SystemExit):
        cli.main(["add", "A", "B", "--status", "aprovada"])


def test_register_direto_grava_com_caminho_do_relatorio(tmp_path):
    cli.register(JOB, tmp_path / "r.md", "candidatei")
    row = tracker.list_all()[0]
    assert row["company"] == "Acme" and row["status"] == "candidatei" and row["report_path"].endswith("r.md")


def test_register_sem_terminal_nao_pergunta_nem_grava(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    cli.register(JOB, tmp_path / "r.md", None)
    assert tracker.list_all() == []


def test_register_interativo_sim_e_nao(monkeypatch, tmp_path):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    respostas = iter(["n"])
    monkeypatch.setattr("builtins.input", lambda _: next(respostas))
    cli.register(JOB, tmp_path / "r.md", None)
    assert tracker.list_all() == []
    respostas = iter(["s", ""])  # sim, e Enter = status padrão
    cli.register(JOB, tmp_path / "r.md", None)
    assert tracker.list_all()[0]["status"] == "interessada"


def test_register_com_empresa_e_titulo_nulos(tmp_path):
    cli.register({**JOB, "company": None, "title": None}, tmp_path / "r.md", "interessada")
    row = tracker.list_all()[0]
    assert row["company"] == "empresa não informada" and row["title"] == "vaga sem título"
