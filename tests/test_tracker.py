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


def test_get_e_update_parcial(tmp_path):
    db = tmp_path / "a.db"
    i = tracker.add("Acme", "Dev", db_path=db, applied_on="2026-01-02")
    tracker.update(i, db_path=db, company="Acme S/A", status="candidatei", title=None)  # None é ignorado
    a = tracker.get(i, db_path=db)
    assert (a["company"], a["title"], a["status"], a["applied_on"]) == ("Acme S/A", "Dev", "candidatei", "2026-01-02")


def test_update_recusa_campo_status_data_e_vazio(tmp_path):
    db = tmp_path / "a.db"
    i = tracker.add("A", "x", db_path=db)
    with pytest.raises(ValueError, match="não editável"):
        tracker.update(i, db_path=db, id=5)
    with pytest.raises(ValueError, match="status inválido"):
        tracker.update(i, db_path=db, status="talvez")
    with pytest.raises(ValueError, match="data inválida"):
        tracker.update(i, db_path=db, applied_on="05/11/2026")
    with pytest.raises(ValueError, match="nada para atualizar"):
        tracker.update(i, db_path=db)
    assert tracker.get(i, db_path=db)["status"] == "interessada"  # nada foi alterado


def test_update_nome_de_coluna_malicioso_nao_chega_ao_sql(tmp_path):
    db = tmp_path / "a.db"
    i = tracker.add("A", "x", db_path=db)
    with pytest.raises(ValueError):
        tracker.update(i, db_path=db, **{"status=?, company": "x"})
    assert tracker.get(i, db_path=db)["company"] == "A"


def test_delete(tmp_path):
    db = tmp_path / "a.db"
    a, b = tracker.add("A", "x", db_path=db), tracker.add("B", "y", db_path=db)
    tracker.delete(a, db_path=db)
    assert [r["id"] for r in tracker.list_all(db_path=db)] == [b]
    with pytest.raises(KeyError):
        tracker.delete(a, db_path=db)
    with pytest.raises(KeyError):
        tracker.get(a, db_path=db)


def test_add_recusa_data_fora_do_formato(tmp_path):
    with pytest.raises(ValueError):
        tracker.add("A", "x", applied_on="amanhã", db_path=tmp_path / "a.db")


def test_data_padrao_e_hoje(tmp_path):
    from datetime import date
    db = tmp_path / "a.db"
    tracker.add("A", "x", db_path=db)
    assert tracker.list_all(db_path=db)[0]["applied_on"] == date.today().isoformat()
