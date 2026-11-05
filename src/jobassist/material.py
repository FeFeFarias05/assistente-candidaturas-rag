"""Lê o material pessoal (PDF, MD, TXT) em segmentos citáveis."""
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

EXTS = {".pdf", ".md", ".txt"}
SKIP = {"readme.md"}  # documentação da pasta, não faz parte do material


@dataclass(frozen=True)
class Segment:
    id: str  # "curriculo.pdf#p1" (PDF, por página) ou "projeto.md"
    text: str


def clean(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# Dados pessoais que a análise não precisa e que não devem ir para a API.
# Linkedin/GitHub ficam (são perfis públicos e úteis).
PII_LINE = re.compile(
    r"(?i)\b(endere[cç]o|data de nascimento|nascimento|telefone|celular|whatsapp|cpf|rg|e-?mail)\b\s*[:\-–]"
    r"|[\w.+-]+@[\w-]+\.[\w.-]+"  # e-mail em qualquer lugar da linha
    r"|\d{3}\.\d{3}\.\d{3}-\d{2}"  # CPF
    r"|(\+55\s?)?\(\d{2}\)\s?9?\d{4}[-\s]?\d{4}"  # telefone com DDD entre parênteses
    r"|\+55\s?\d{2}\s?9?\d{4}[-\s]?\d{4}"
)


def redact(text: str) -> tuple[str, int]:
    """Remove linhas com dados pessoais. Devolve (texto, nº de linhas removidas).

    ponytail: heurística por linha (rótulos e padrões comuns no Brasil); dados pessoais em
    texto corrido não são pegos. Para dados sensíveis, mantenha-os fora da pasta de material.
    """
    kept = [l for l in text.split("\n") if not PII_LINE.search(l)]
    return "\n".join(kept), len(text.split("\n")) - len(kept)


def load_material(folder: str | Path) -> list[Segment]:
    folder = Path(folder)
    segs, removed = [], 0
    for f in sorted(folder.rglob("*")):
        if f.suffix.lower() not in EXTS or f.name.lower() in SKIP:
            continue
        name = f.relative_to(folder).as_posix()
        if f.suffix.lower() == ".pdf":
            for n, page in enumerate(PdfReader(f).pages, 1):
                t, k = redact(clean(page.extract_text() or ""))
                removed += k
                if len(t) < 30:
                    print(f"[material] AVISO: {name} página {n} quase sem texto (PDF escaneado?)", file=sys.stderr)
                if t:
                    segs.append(Segment(f"{name}#p{n}", t))
        else:
            t, k = redact(clean(f.read_text(encoding="utf-8")))
            removed += k
            if t:
                segs.append(Segment(name, t))
    if removed:
        print(f"[material] {removed} linha(s) com dados pessoais (endereço, nascimento, telefone, e-mail) "
              "removida(s) antes de indexar/enviar", file=sys.stderr)
    return segs
