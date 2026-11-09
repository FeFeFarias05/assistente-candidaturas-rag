"""Lê o material pessoal (PDF, DOCX, PPTX, MD, TXT) em segmentos citáveis."""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

EXTS = {".pdf", ".docx", ".pptx", ".md", ".txt"}
SKIP = {"readme.md"}  # documentação da pasta, não faz parte do material
MAX_XML = 20 * 1024 * 1024  # limite por parte de um .docx/.pptx (proteção contra arquivo malicioso)
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


@dataclass(frozen=True)
class Segment:
    id: str  # "curriculo.pdf#p1" (PDF, por página), "deck.pptx#s3" (slide) ou "projeto.md"
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


def _xml_paragraphs(z: zipfile.ZipFile, part: str, p_tag: str, t_tag: str) -> str:
    if z.getinfo(part).file_size > MAX_XML:
        raise ValueError(f"parte {part} grande demais")
    root = ET.fromstring(z.read(part))
    return "\n".join("".join(t.text or "" for t in p.iter(t_tag)) for p in root.iter(p_tag))


def _pieces(f: Path):
    """Gera (sufixo do id, texto bruto). Sem OCR: PDF escaneado vem sem texto."""
    ext = f.suffix.lower()
    if ext == ".pdf":
        for n, page in enumerate(PdfReader(f).pages, 1):
            yield f"#p{n}", page.extract_text() or ""
    elif ext == ".docx":
        with zipfile.ZipFile(f) as z:
            yield "", _xml_paragraphs(z, "word/document.xml", _W + "p", _W + "t")
    elif ext == ".pptx":
        with zipfile.ZipFile(f) as z:
            slides = sorted((int(m.group(1)), n) for n in z.namelist() if (m := re.fullmatch(r"ppt/slides/slide(\d+)\.xml", n)))
            for num, part in slides:
                yield f"#s{num}", _xml_paragraphs(z, part, _A + "p", _A + "t")
    else:
        yield "", f.read_text(encoding="utf-8")


def load_material(folder: str | Path) -> list[Segment]:
    folder = Path(folder)
    segs, removed = [], 0
    for f in sorted(folder.rglob("*")):
        if f.suffix.lower() not in EXTS or f.name.lower() in SKIP:
            continue
        name = f.relative_to(folder).as_posix()
        try:
            pieces = list(_pieces(f))
        except Exception as e:  # arquivo corrompido ou de outro formato: avisa e segue
            print(f"[material] AVISO: não consegui ler {name} ({type(e).__name__}: {e})", file=sys.stderr)
            continue
        for suffix, raw in pieces:
            t, k = redact(clean(raw))
            removed += k
            if f.suffix.lower() == ".pdf" and len(t) < 30:
                print(f"[material] AVISO: {name} página {suffix[2:]} quase sem texto (PDF escaneado? não há OCR)", file=sys.stderr)
            if t:
                segs.append(Segment(f"{name}{suffix}", t))
    if removed:
        print(f"[material] {removed} linha(s) com dados pessoais (endereço, nascimento, telefone, e-mail) "
              "removida(s) antes de indexar/enviar", file=sys.stderr)
    return segs
