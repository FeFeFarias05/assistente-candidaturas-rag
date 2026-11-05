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
    return sorted({f"{t}: citada em Pontos fortes sem aparecer no trecho citado"
                   for item in _strength_items(body) for t in _unsupported_in(item, job, texts)})


def _strength_items(body: str) -> list[str]:
    return [i for i in re.split(r"\n(?=\s*[-*]\s)", _section(body, "Pontos fortes")) if i.strip()]


def _unsupported_in(item: str, job: dict, texts: dict[str, str]) -> list[str]:
    techs = [r["text"] for r in job["requirements"] if r["kind"] == "tech" and " " not in r["text"].strip()]
    cited_text = " ".join(texts.get(c, "") for c in CITATION.findall(item))
    return [t for t in techs if term_pattern(t).search(CITATION.sub("", item)) and not term_pattern(t).search(cited_text)]


def strengths_saying_no_evidence(body: str) -> list[str]:
    """Item em 'Pontos fortes' que admite 'sem evidência': contradição, deveria estar em Lacunas."""
    return [f"Pontos fortes contém item sem evidência: {i.strip()[:60]}"
            for i in _strength_items(body) if "sem evidência" in i.lower()]


def demote(body: str, job: dict, texts: dict[str, str]) -> tuple[str, list[str]]:
    """Garantia final: item de Pontos fortes com tecnologia sem suporte no trecho citado, ou que admite
    'sem evidência', sai de lá e vai para Lacunas. Devolve (texto novo, notas para o relatório)."""
    bad = [i for i in _strength_items(body) if _unsupported_in(i, job, texts) or "sem evidência" in i.lower()]
    if not bad:
        return body, []
    titles = [i.strip().lstrip("-* ").split(":")[0].strip() for i in bad]
    for i in bad:
        body = body.replace(i, "", 1)
    existing = _section(body, "Lacunas").casefold()  # não duplica lacuna que o modelo já escreveu
    moved = "".join(f"- {t}: sem suporte no trecho citado (item movido de Pontos fortes pela validação)\n"
                    for t in titles if t.casefold() not in existing)
    if not moved:
        return body, [f"a validação removeu de Pontos fortes (já estavam em Lacunas): {', '.join(titles)}"]
    if re.search(r"^##\s*Lacunas\s*$", body, re.MULTILINE):
        body = re.sub(r"(^##\s*Lacunas\s*$\n)", lambda m: m.group(1) + moved, body, count=1, flags=re.MULTILINE)
    else:
        body += f"\n\n## Lacunas\n{moved}"
    return body, [f"a validação moveu de Pontos fortes para Lacunas: {', '.join(titles)}"]


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
    body, notes = demote(body, job, texts)  # o que o modelo não corrigiu, o código tira de Pontos fortes
    return body, problems(body, job, texts) + notes


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
