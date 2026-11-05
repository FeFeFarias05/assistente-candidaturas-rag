"""Vaga + material -> relatório de aderência, com validação das citações."""
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

from .llm import complete
from .retrieve import retrieve, term_pattern

ROOT = Path(__file__).resolve().parents[2]
PROMPT = (ROOT / "prompts" / "analyze.md").read_text(encoding="utf-8")
LANGS = {"pt": "português", "en": "inglês (English)"}
CITATION = re.compile(r"\[([^\[\]\n]+?\.(?:pdf|md|txt)(?:#[^\[\]\n]+)?)\]", re.IGNORECASE)


# ---------- prompt ----------

def build_prompt(job: dict, items, lang: str, evidence=None) -> str:
    """`items`: objetos com .id e .text (segmentos inteiros ou trechos recuperados)."""
    material = "\n\n".join(f"[{s.id}]\n{s.text}" for s in items)
    parts = [f"Idioma do rascunho: {LANGS[lang]}",
             f"## DADOS DA VAGA\n{json.dumps(job, ensure_ascii=False, indent=1)}"]
    if evidence is not None:
        lines = []
        for r in evidence:
            req = r.requirement
            ids = " ".join(f"[{h.id}]" for h in r.hits) or "NENHUM trecho relevante encontrado"
            lines.append(f"- {req['text']} ({req['kind']}, {'obrigatório' if req['required'] else 'desejável'}): {ids}")
        parts.append("## TRECHOS ENCONTRADOS POR REQUISITO\n" + "\n".join(lines))
    parts.append(f"## MATERIAL DA CANDIDATA\n{material}")
    return "\n\n".join(parts)


# ---------- validação ----------

def _section(body: str, title: str) -> str:
    m = re.search(rf"^##\s*{re.escape(title)}\s*$(.*?)(?=^##\s|\Z)", body, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else ""


def invalid_citations(body: str, valid_ids: set[str]) -> list[str]:
    return sorted({c for c in CITATION.findall(body) if c not in valid_ids})


def unsupported_techs(body: str, job: dict, texts: dict[str, str]) -> list[str]:
    """Em 'Pontos fortes', tecnologia (de uma palavra) citada num item sem aparecer nos trechos que o item cita.

    ponytail: só tecnologias de uma palavra; termos genéricos ("web development") dariam falso alarme.
    """
    techs = [r["text"] for r in job["requirements"] if r["kind"] == "tech" and " " not in r["text"].strip()]
    out = []
    for item in re.split(r"\n(?=\s*[-*]\s)", _section(body, "Pontos fortes")):
        cited = CITATION.findall(item)
        cited_text = " ".join(texts.get(c, "") for c in cited)
        for t in techs:
            word = term_pattern(t)
            if word.search(CITATION.sub("", item)) and not word.search(cited_text):
                out.append(f"{t}: citada em Pontos fortes sem aparecer no trecho citado")
    return sorted(set(out))


def strengths_saying_no_evidence(body: str) -> list[str]:
    """Item em 'Pontos fortes' que admite 'sem evidência': contradição, deveria estar em Lacunas."""
    items = re.split(r"\n(?=\s*[-*]\s)", _section(body, "Pontos fortes"))
    return [f"Pontos fortes contém item sem evidência: {i.strip()[:60]}" for i in items if "sem evidência" in i.lower()]


def problems(body: str, job: dict, texts: dict[str, str]) -> list[str]:
    return ([f"citação inexistente: [{c}]" for c in invalid_citations(body, set(texts))]
            + unsupported_techs(body, job, texts) + strengths_saying_no_evidence(body))


def generate(job: dict, items, lang: str, evidence=None) -> tuple[str, list[str]]:
    """Gera o relatório, valida e tenta corrigir uma vez. Devolve (texto, avisos que restaram)."""
    texts = {s.id: s.text for s in items}
    prompt = build_prompt(job, items, lang, evidence)
    body = complete(prompt, system=PROMPT)
    found = problems(body, job, texts)
    if found:
        fix = (f"{prompt}\n\n## CORREÇÃO\nSua resposta tem problemas:\n" + "\n".join(f"- {p}" for p in found)
               + f"\n\nReescreva o relatório inteiro, usando SOMENTE estes ids: {sorted(texts)}. "
               "Item de Pontos fortes que o trecho citado não sustenta por completo deve ir para Lacunas "
               "(ou ser removido). Não afirme tecnologia que não está escrita no trecho citado.")
        body = complete(fix, system=PROMPT)
        found = problems(body, job, texts)
    return body, found


# ---------- modos ----------

def analyze_no_rag(job: dict, segments, lang: str | None = None):
    """Linha de base: o material inteiro vai no prompt."""
    return generate(job, segments, lang or job["language"])


def analyze_rag(job: dict, index, lang: str | None = None):
    """RAG: só os trechos recuperados vão no prompt. Devolve (texto, avisos)."""
    if index is None:
        raise RuntimeError("Índice vazio. Rode `jobassist ingest` primeiro.")
    evidence, hits = retrieve(job["requirements"], index)
    if not hits:
        return ("Não encontrei no material nenhum trecho relevante para esta vaga, "
                "então não vou gerar sugestões. Confira se o material foi indexado "
                "(`jobassist ingest`) e se ele cobre o que a vaga pede."), []
    return generate(job, hits, lang or job["language"], evidence)


# ---------- relatório ----------

def slug(text: str | None) -> str:
    ascii_text = unicodedata.normalize("NFKD", text or "vaga").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:40] or "vaga"


def save_report(job: dict, body: str, mode: str, warnings: list[str] = (), folder: Path = ROOT / "reports") -> Path:
    folder.mkdir(exist_ok=True)
    path = folder / f"{date.today()}_{slug(job['company'])}_{slug(job['title'])}.md"
    head = (
        f"# {job['title'] or 'Vaga'} | {job['company'] or 'empresa não informada'}\n"
        f"_Gerado em {date.today()} (modo: {mode}). Rascunho: revise antes de usar._\n\n"
    )
    if warnings:
        head += "> ⚠️ **Avisos de validação (confira antes de usar):**\n" + "".join(f"> - {w}\n" for w in warnings) + "\n"
    path.write_text(head + body + "\n", encoding="utf-8")
    return path
