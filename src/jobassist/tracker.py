"""Registro de candidaturas (SQLite, separado do índice: o índice é descartável, isto não)."""
import sqlite3
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "applications.db"
STATUSES = ("interessada", "candidatei", "entrevista", "recusada", "oferta")

SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    applied_on TEXT NOT NULL,
    status TEXT NOT NULL,
    report_path TEXT,
    created_at TEXT NOT NULL
)
"""


def _connect(db_path: Path | None) -> sqlite3.Connection:
    db = sqlite3.connect(db_path or DB_PATH)  # resolvido na chamada: facilita testar
    db.row_factory = sqlite3.Row
    db.execute(SCHEMA)
    return db


def _check_status(status: str) -> None:
    if status not in STATUSES:
        raise ValueError(f"status inválido: {status!r}. Use um de: {', '.join(STATUSES)}")


def add(company: str, title: str, status: str = "interessada", applied_on: str | None = None,
        report_path: str | None = None, db_path: Path | None = None) -> int:
    _check_status(status)
    if applied_on:
        date.fromisoformat(applied_on)  # recusa data fora do formato AAAA-MM-DD
    db = _connect(db_path)
    with db:
        cur = db.execute(
            "INSERT INTO applications (company, title, applied_on, status, report_path, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (company, title, applied_on or date.today().isoformat(), status, report_path,
             datetime.now().isoformat(timespec="seconds")),
        )
    db.close()
    return cur.lastrowid


def list_all(status: str | None = None, db_path: Path | None = None) -> list[dict]:
    db = _connect(db_path)
    sql, args = "SELECT * FROM applications", ()
    if status:
        _check_status(status)
        sql, args = sql + " WHERE status=?", (status,)
    rows = [dict(r) for r in db.execute(sql + " ORDER BY id", args)]
    db.close()
    return rows


EDITABLE = ("company", "title", "applied_on", "status", "report_path")


def get(app_id: int, db_path: Path | None = None) -> dict:
    db = _connect(db_path)
    row = db.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
    db.close()
    if row is None:
        raise KeyError(f"candidatura {app_id} não encontrada")
    return dict(row)


def update(app_id: int, db_path: Path | None = None, **fields) -> None:
    """Atualiza só os campos informados (None é ignorado). Nomes de coluna vêm de uma lista fixa."""
    fields = {k: v for k, v in fields.items() if v is not None}
    unknown = set(fields) - set(EDITABLE)
    if unknown:
        raise ValueError(f"campo não editável: {', '.join(sorted(unknown))}")
    if not fields:
        raise ValueError("nada para atualizar")
    if "status" in fields:
        _check_status(fields["status"])
    if "applied_on" in fields:
        try:
            date.fromisoformat(fields["applied_on"])
        except ValueError:
            raise ValueError(f"data inválida: {fields['applied_on']!r}. Use AAAA-MM-DD") from None
    db = _connect(db_path)
    with db:
        n = db.execute(f"UPDATE applications SET {', '.join(f'{k}=?' for k in fields)} WHERE id=?",
                       (*fields.values(), app_id)).rowcount
    db.close()
    if not n:
        raise KeyError(f"candidatura {app_id} não encontrada")


def set_status(app_id: int, status: str, db_path: Path | None = None) -> None:
    update(app_id, db_path, status=status)


def delete(app_id: int, db_path: Path | None = None) -> None:
    db = _connect(db_path)
    with db:
        n = db.execute("DELETE FROM applications WHERE id=?", (app_id,)).rowcount
    db.close()
    if not n:
        raise KeyError(f"candidatura {app_id} não encontrada")
