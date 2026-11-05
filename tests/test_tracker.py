import pytest

from jobassist import tracker


def test_persiste_depois_de_reabrir(tmp_path):
    db = tmp_path / "a.db"
    i = tracker.add("Acme", "Dev Web", db_path=db, applied_on="2026-11-05", report_path="reports/x.md")
    # nova conexão = "reiniciar o programa"
    rows = tracker.list_all(db_path=db)
    assert rows[0]["id"] == i and rows[0]["company"] == "Acme" and rows[0]["status"] == "interessada"
    assert rows[0]["applied_on"] == "2026-11-05" and rows[0]["report_path"] == "reports/x.md"


def test_atualizar_status_persiste(tmp_path):
    db = tmp_path / "a.db"
    i = tracker.add("Acme", "Dev", db_path=db)
    tracker.set_status(i, "entrevista", db_path=db)
    assert tracker.list_all(db_path=db)[0]["status"] == "entrevista"


def test_filtra_por_status(tmp_path):
    db = tmp_path / "a.db"
    tracker.add("A", "x", status="candidatei", db_path=db)
    tracker.add("B", "y", db_path=db)
    assert [r["company"] for r in tracker.list_all("candidatei", db_path=db)] == ["A"]


def test_status_invalido(tmp_path):
    db = tmp_path / "a.db"
    with pytest.raises(ValueError, match="status inválido"):
        tracker.add("A", "x", status="aprovada", db_path=db)
    i = tracker.add("A", "x", db_path=db)
    with pytest.raises(ValueError):
        tracker.set_status(i, "talvez", db_path=db)


def test_id_inexistente(tmp_path):
    with pytest.raises(KeyError):
        tracker.set_status(99, "oferta", db_path=tmp_path / "a.db")


def test_data_padrao_e_hoje(tmp_path):
    from datetime import date
    db = tmp_path / "a.db"
    tracker.add("A", "x", db_path=db)
    assert tracker.list_all(db_path=db)[0]["applied_on"] == date.today().isoformat()
