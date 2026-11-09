import json

from jobassist import cli


def test_extract_cli(tmp_path, monkeypatch, capsys):
    vaga = tmp_path / "v.txt"
    vaga.write_text("Dev Python", encoding="utf-8")
    monkeypatch.setattr(cli, "extract_job", lambda t: {"title": t})
    cli.main(["extract", str(vaga)])
    assert json.loads(capsys.readouterr().out) == {"title": "Dev Python"}


def test_cli_mostra_consumo_so_quando_houve_chamada(monkeypatch, capsys):
    monkeypatch.setattr(cli.llm, "usage_summary", lambda: "2 chamada(s) à API, 10 tokens de entrada e 5 de saída")
    monkeypatch.setattr(cli, "extract_job", lambda t: {"title": t})
    cli.main(["extract", "/dev/null"])
    assert "[custo] 2 chamada(s)" in capsys.readouterr().err
