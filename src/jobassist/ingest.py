"""Material -> chunks -> embeddings -> index.db (incremental por hash do arquivo)."""
import hashlib
import sqlite3
from pathlib import Path

import numpy as np

from .chunking import chunk_all
from .embed import embed, provider_id
from .material import load_material

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "index.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY, source TEXT, text TEXT, embedding BLOB, file_hash TEXT
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    return db


def _check_provider(db: sqlite3.Connection, rebuild: bool) -> None:
    row = db.execute("SELECT value FROM meta WHERE key='provider'").fetchone()
    current = provider_id()
    if row and row[0] != current:
        if not rebuild:
            raise RuntimeError(
                f"O índice foi criado com {row[0]}, mas o provedor atual é {current}. "
                "Vetores de modelos diferentes não se misturam: rode `jobassist ingest --rebuild`."
            )
        db.execute("DELETE FROM chunks")
    db.execute("INSERT OR REPLACE INTO meta VALUES ('provider', ?)", (current,))


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ingest(folder: str | Path, db_path: Path = INDEX_PATH, rebuild: bool = False) -> dict:
    """Indexa só o que mudou. Devolve {'novos': n, 'inalterados': n, 'removidos': n} (em arquivos)."""
    folder = Path(folder)
    by_source: dict[str, list] = {}
    for c in chunk_all(load_material(folder)):
        by_source.setdefault(c.source, []).append(c)
    hashes = {s: file_hash(folder / s) for s in by_source}

    db = _connect(db_path)
    with db:
        _check_provider(db, rebuild)
        old = dict(db.execute("SELECT source, file_hash FROM chunks GROUP BY source"))
        gone = [s for s in old if s not in by_source]
        todo = [s for s in by_source if old.get(s) != hashes[s]]
        for s in gone + todo:
            db.execute("DELETE FROM chunks WHERE source=?", (s,))
        chunks = [c for s in todo for c in by_source[s]]
        if chunks:
            vecs = embed([c.text for c in chunks], "passage")
            db.executemany(
                "INSERT INTO chunks VALUES (?,?,?,?,?)",
                [(c.id, c.source, c.text, v.tobytes(), hashes[c.source]) for c, v in zip(chunks, vecs)],
            )
    db.close()
    return {"novos": len(todo), "inalterados": len(by_source) - len(todo), "removidos": len(gone)}


def chunk_counts(db_path: Path = INDEX_PATH) -> dict[str, int]:
    """Quantos trechos cada arquivo tem no índice (vazio se o índice não existe)."""
    if not Path(db_path).exists():
        return {}
    db = sqlite3.connect(db_path)
    try:
        return dict(db.execute("SELECT source, COUNT(*) FROM chunks GROUP BY source"))
    except sqlite3.OperationalError:  # arquivo existe mas ainda sem a tabela
        return {}
    finally:
        db.close()


def load_index(db_path: Path = INDEX_PATH):
    """Devolve (ids, textos, matriz de vetores) ou None se o índice não existe/está vazio."""
    if not Path(db_path).exists():
        return None
    db = sqlite3.connect(db_path)
    rows = db.execute("SELECT id, text, embedding FROM chunks ORDER BY id").fetchall()
    db.close()
    if not rows:
        return None
    ids, texts, blobs = zip(*rows)
    return list(ids), list(texts), np.vstack([np.frombuffer(b, dtype=np.float32) for b in blobs])
