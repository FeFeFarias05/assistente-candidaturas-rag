"""Segmentos -> chunks pequenos e citáveis."""
from dataclasses import dataclass

from .material import Segment

# O modelo de embeddings local lê ~128 tokens: chunks curtos evitam truncar.
MAX_CHARS = 450
OVERLAP = 60


@dataclass(frozen=True)
class Chunk:
    id: str  # "curriculo.pdf#p1c3" ou "projeto.md#c2"
    source: str  # arquivo
    text: str


def _units(text: str) -> list[str]:
    """Parágrafos; os longos viram linhas; as linhas longas viram palavras."""
    out = []
    for para in text.split("\n\n"):
        for line in ([para] if len(para) <= MAX_CHARS else para.split("\n")):
            if len(line) <= MAX_CHARS:
                out.append(line.strip())
                continue
            cur = ""
            for w in line.split():
                if cur and len(cur) + 1 + len(w) > MAX_CHARS:
                    out.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            out.append(cur)
    return [u for u in out if u]


def chunk_segment(seg: Segment) -> list[Chunk]:
    source = seg.id.split("#")[0]
    base = seg.id if "#" in seg.id else seg.id + "#"
    pieces, cur = [], ""
    for u in _units(seg.text):
        if cur and len(cur) + 1 + len(u) > MAX_CHARS:
            pieces.append(cur)
            # sobreposição: repete a última unidade se for curta
            last = cur.split("\n")[-1]
            cur = last if len(last) <= OVERLAP else ""
        cur = f"{cur}\n{u}".strip("\n")
    if cur:
        pieces.append(cur)
    return [Chunk(f"{base}c{n}", source, p) for n, p in enumerate(pieces, 1)]


def chunk_all(segments: list[Segment]) -> list[Chunk]:
    return [c for s in segments for c in chunk_segment(s)]
