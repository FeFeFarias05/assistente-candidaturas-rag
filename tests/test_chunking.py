from pathlib import Path

from jobassist.chunking import MAX_CHARS, chunk_all, chunk_segment
from jobassist.material import Segment, load_material

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "sample"


def test_texto_curto_vira_um_chunk_com_id_de_md():
    cs = chunk_segment(Segment("p.md", "Um texto curto."))
    assert [(c.id, c.source) for c in cs] == [("p.md#c1", "p.md")]


def test_id_de_pdf_inclui_pagina():
    assert chunk_segment(Segment("cv.pdf#p2", "texto"))[0].id == "cv.pdf#p2c1"


def test_nenhum_chunk_passa_do_limite_mesmo_sem_quebras():
    texto = "palavra " * 400  # uma linha enorme, sem parágrafos
    cs = chunk_segment(Segment("a.txt", texto))
    assert len(cs) > 1 and all(len(c.text) <= MAX_CHARS + 70 for c in cs)


def test_sobreposicao_repete_ultima_linha_curta():
    linhas = [f"item numero {i} " + "x" * 90 for i in range(8)]
    cs = chunk_segment(Segment("a.md", "\n".join(linhas)))
    assert len(cs) > 1
    assert cs[0].text.split("\n")[-1] != cs[1].text.split("\n")[0]  # linhas de 100+ chars: sem overlap
    curtas = [f"- item {i}" for i in range(80)]
    cs = chunk_segment(Segment("a.md", "\n".join(curtas)))
    assert cs[0].text.split("\n")[-1] == cs[1].text.split("\n")[0]


def test_nada_se_perde():
    cs = chunk_segment(Segment("a.md", "\n".join(f"- item {i}" for i in range(80))))
    junto = "\n".join(c.text for c in cs)
    assert all(f"- item {i}" in junto for i in range(80))


def test_sample_ids_unicos_e_curriculo_em_varios_chunks():
    cs = chunk_all(load_material(SAMPLE))
    ids = [c.id for c in cs]
    assert len(ids) == len(set(ids))
    assert sum(c.source == "curriculo.pdf" for c in cs) >= 3
    assert all(len(c.text) <= MAX_CHARS + 70 for c in cs)
