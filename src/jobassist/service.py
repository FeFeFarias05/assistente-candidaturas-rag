"""Casos de uso compartilhados pela CLI e pela interface web."""
import re
import sys
import threading
from pathlib import Path

from . import llm
from .analyze import analyze_no_rag, analyze_rag, save_report
from .config import load_config
from .extract import extract_job
from .ingest import chunk_counts, ingest, load_index
from .material import EXTS, SKIP, load_material

ROOT = Path(__file__).resolve().parents[2]
SAMPLE = (ROOT / "data" / "sample").resolve()
MAX_JOB_CHARS = 50_000
MAX_UPLOAD = 25 * 1024 * 1024
LOCK = threading.Lock()  # uma análise por vez: o consumo (llm) e o índice são compartilhados


class PrivacyError(Exception):
    """Ação que enviaria dados para fora, ou mexeria no material de exemplo, sem confirmação."""


class NoMaterialError(Exception):
    """Não há material indexável na pasta configurada."""


def material_folder() -> Path:
    p = Path(load_config().material_dir)
    return (p if p.is_absolute() else ROOT / p).resolve()


def is_sample(folder: Path | None = None) -> bool:
    return (folder or material_folder()) == SAMPLE


def run_analysis(job_text: str, lang: str | None = None, no_rag: bool = False, send_all: bool = False) -> dict:
    """Extrai a vaga, analisa contra o material e salva o relatório. Levanta PrivacyError, NoMaterialError ou ValueError."""
    job_text = (job_text or "").strip()
    if not job_text:
        raise ValueError("Cole o texto da vaga.")
    if len(job_text) > MAX_JOB_CHARS:
        raise ValueError(f"Texto grande demais ({len(job_text)} caracteres; o limite é {MAX_JOB_CHARS}).")
    if lang not in (None, "", "pt", "en"):
        raise ValueError("Idioma inválido. Use pt ou en.")
    lang = lang or None
    folder = material_folder()
    with LOCK:
        llm.reset_usage()
        if no_rag:
            if not is_sample(folder) and not send_all:
                raise PrivacyError(f"O modo de material inteiro envia TODO o conteúdo de {folder.name} à API")
            segments = load_material(folder)
            if not segments:
                raise NoMaterialError(f"Nenhum material encontrado em {folder.name}.")
            job = extract_job(job_text)
            print(f"[analyze] enviando o material inteiro ({len(segments)} trechos) à API", file=sys.stderr)
            body, warnings = analyze_no_rag(job, segments, lang)
            mode = "sem RAG"
        else:
            ingest(folder)  # incremental: só reindexa o que mudou
            index = load_index()
            if index is None:
                raise NoMaterialError(f"Nenhum material encontrado em {folder.name}. Adicione arquivos na aba Material.")
            job = extract_job(job_text)
            body, warnings = analyze_rag(job, index, lang)
            mode = "RAG"
        path = save_report(job, body, mode, warnings)
        return {"job": job, "report": body, "warnings": warnings, "mode": mode,
                "report_path": str(path), "usage": llm.usage()}


# ---------- material (usado pela interface web) ----------

def _listable(f: Path) -> bool:
    return f.is_file() and f.suffix.lower() in EXTS and f.name.lower() not in SKIP


def material_status() -> dict:
    folder, cfg = material_folder(), load_config()
    counts = chunk_counts()
    files = []
    if folder.is_dir():
        for f in sorted(folder.rglob("*")):
            if _listable(f):
                name = f.relative_to(folder).as_posix()
                files.append({"name": name, "size": f.stat().st_size, "chunks": counts.get(name)})
    try:
        shown = folder.relative_to(ROOT).as_posix()
    except ValueError:
        shown = folder.name
    return {"folder": shown, "is_sample": is_sample(folder), "files": files,
            "model": cfg.model, "api_key_set": bool(cfg.api_key), "embeddings": cfg.embeddings,
            "price_set": cfg.price_in is not None and cfg.price_out is not None}


def _require_private_folder() -> Path:
    folder = material_folder()
    if is_sample(folder):
        raise PrivacyError("O material atual é o de exemplo (fica no Git). "
                           "Aponte MATERIAL_DIR para data/private no .env para usar o seu.")
    return folder


def safe_name(filename: str) -> str:
    name = re.sub(r"[^\w .()\-]", "_", Path(filename or "").name).strip(" .")
    if not name or Path(name).suffix.lower() not in EXTS:
        raise ValueError(f"Formato não aceito: {filename!r}. Use PDF, DOCX, PPTX, MD ou TXT.")
    if name.lower() in SKIP:
        raise ValueError(f"O nome {name!r} é reservado. Renomeie o arquivo.")
    return name


def save_upload(filename: str, data: bytes) -> str:
    folder = _require_private_folder()
    if len(data) > MAX_UPLOAD:
        raise ValueError(f"{filename}: arquivo maior que {MAX_UPLOAD // 1024 // 1024} MB.")
    name = safe_name(filename)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_bytes(data)
    return name


def delete_material(name: str) -> None:
    folder = _require_private_folder()
    target = (folder / name).resolve()
    if folder not in target.parents or not _listable(target):  # impede sair da pasta (../)
        raise KeyError(f"Arquivo não encontrado: {name}")
    target.unlink()


def reindex() -> dict:
    with LOCK:
        return ingest(material_folder())
