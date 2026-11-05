import json

from jobassist import cli


def test_extract_cli(tmp_path, monkeypatch, capsys):
    vaga = tmp_path / "v.txt"
    vaga.write_text("Dev Python", encoding="utf-8")
    monkeypatch.setattr(cli, "extract_job", lambda t: {"title": t})
    cli.main(["extract", str(vaga)])
    assert json.loads(capsys.readouterr().out) == {"title": "Dev Python"}
