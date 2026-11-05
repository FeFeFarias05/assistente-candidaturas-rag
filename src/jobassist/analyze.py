"""Vaga + material -> relatório de aderência."""
import json
import re
from datetime import date
from pathlib import Path

from .llm import complete
from .material import Segment

ROOT = Path(__file__).resolve().parents[2]
PROMPT = (ROOT / "prompts" / "analyze.md").read_text(encoding="utf-8")
LANGS = {"pt": "português", "en": "inglês (English)"}


def build_prompt(job: dict, segments: list[Segment], lang: str) -> str:
    material = "\n\n".join(f"[{s.id}]\n{s.text}" for s in segments)
    return (
        f"Idioma do rascunho: {LANGS[lang]}\n\n"
        f"## DADOS DA VAGA\n{json.dumps(job, ensure_ascii=False, indent=1)}\n\n"
        f"## MATERIAL DA CANDIDATA\n{material}"
    )


def analyze_no_rag(job: dict, segments: list[Segment], lang: str | None = None) -> str:
    """Linha de base: o material inteiro vai no prompt."""
    return complete(build_prompt(job, segments, lang or job["language"]), system=PROMPT)


def slug(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "vaga").lower()).strip("-")[:40] or "vaga"


def save_report(job: dict, body: str, mode: str, folder: Path = ROOT / "reports") -> Path:
    folder.mkdir(exist_ok=True)
    path = folder / f"{date.today()}_{slug(job['company'])}_{slug(job['title'])}.md"
    head = (
        f"# {job['title'] or 'Vaga'} | {job['company'] or 'empresa não informada'}\n"
        f"_Gerado em {date.today()} (modo: {mode}). Rascunho: revise antes de usar._\n\n"
    )
    path.write_text(head + body + "\n", encoding="utf-8")
    return path
