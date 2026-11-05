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


def load_material(folder: str | Path) -> list[Segment]:
    folder = Path(folder)
    segs = []
    for f in sorted(folder.rglob("*")):
        if f.suffix.lower() not in EXTS or f.name.lower() in SKIP:
            continue
        name = f.relative_to(folder).as_posix()
        if f.suffix.lower() == ".pdf":
            for n, page in enumerate(PdfReader(f).pages, 1):
                t = clean(page.extract_text() or "")
                if len(t) < 30:
                    print(f"[material] AVISO: {name} página {n} quase sem texto (PDF escaneado?)", file=sys.stderr)
                if t:
                    segs.append(Segment(f"{name}#p{n}", t))
        else:
            t = clean(f.read_text(encoding="utf-8"))
            if t:
                segs.append(Segment(name, t))
    return segs
