"""Vaga (texto) -> requisitos estruturados."""
import sys
from pathlib import Path

from .llm import complete

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "extract.md").read_text(encoding="utf-8")

_STR_OR_NULL = {"type": ["string", "null"]}

SCHEMA = {
    "type": "object",
    "properties": {
        "title": _STR_OR_NULL,
        "company": _STR_OR_NULL,
        "seniority": _STR_OR_NULL,
        "language": {"type": "string", "enum": ["pt", "en"]},
        "requirements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "kind": {"type": "string", "enum": ["tech", "responsibility", "soft", "other"]},
                    "required": {"type": "boolean"},
                },
                "required": ["text", "kind", "required"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "company", "seniority", "language", "requirements"],
    "additionalProperties": False,
}


def techs_not_in_text(job: dict, text: str) -> list[str]:
    """Tecnologias extraídas que não aparecem literalmente na vaga (sinal de invenção)."""
    low = text.lower()
    return [r["text"] for r in job["requirements"] if r["kind"] == "tech" and r["text"].lower() not in low]


def extract_job(text: str) -> dict:
    job = complete(text, system=PROMPT, schema=SCHEMA)
    missing = techs_not_in_text(job, text)
    if missing:
        print(f"[extract] AVISO: tecnologias que não aparecem literalmente na vaga: {missing}", file=sys.stderr)
    return job
