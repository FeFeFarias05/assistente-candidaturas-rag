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


def test_edit_show_com_relatorio_e_delete(tmp_path, capsys, monkeypatch):
    rel = tmp_path / "r.md"
    rel.write_text("## Resumo da vaga\nconteúdo do relatório", encoding="utf-8")
    tracker.add("Acme", "Dev", report_path=str(rel))
    cli.main(["edit", "1", "--company", "Acme S/A", "--status", "entrevista", "--date", "2026-03-04"])
    cli.main(["show", "1"])
    out = capsys.readouterr().out
    assert "Acme S/A | Dev" in out and "entrevista" in out and "2026-03-04" in out and "conteúdo do relatório" in out
    cli.main(["delete", "1", "--yes"])
    assert tracker.list_all() == []


def test_show_sem_relatorio_avisa(capsys):
    tracker.add("Acme", "Dev")
    cli.main(["show", "1"])
    assert "sem relatório associado" in capsys.readouterr().out


def test_delete_sem_terminal_exige_yes(monkeypatch, capsys):
    tracker.add("Acme", "Dev")
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    with pytest.raises(SystemExit):
        cli.main(["delete", "1"])
    assert "--yes" in capsys.readouterr().err and len(tracker.list_all()) == 1


def test_delete_interativo_respeita_o_nao(monkeypatch, capsys):
    tracker.add("Acme", "Dev")
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: "n")
    cli.main(["delete", "1"])
    assert "nada foi apagado" in capsys.readouterr().out and len(tracker.list_all()) == 1


@pytest.mark.parametrize("args", [["show", "9"], ["edit", "9", "--title", "x"], ["delete", "9", "--yes"]])
def test_id_inexistente_da_erro_claro_nos_tres_comandos(args, capsys):
    with pytest.raises(SystemExit):
        cli.main(args)
    assert "9 não encontrada" in capsys.readouterr().err


def test_edit_sem_campos_e_data_invalida(capsys):
    tracker.add("Acme", "Dev")
    with pytest.raises(SystemExit):
        cli.main(["edit", "1"])
    assert "nada para atualizar" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        cli.main(["edit", "1", "--date", "ontem"])
    with pytest.raises(SystemExit):
        cli.main(["add", "A", "B", "--date", "ontem"])


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
