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


def set_status(app_id: int, status: str, db_path: Path | None = None) -> None:
    _check_status(status)
    db = _connect(db_path)
    with db:
        n = db.execute("UPDATE applications SET status=? WHERE id=?", (status, app_id)).rowcount
    db.close()
    if not n:
        raise KeyError(f"candidatura {app_id} não encontrada")
