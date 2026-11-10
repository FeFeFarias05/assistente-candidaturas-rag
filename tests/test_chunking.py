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


# ---------- títulos (achado da avaliação de retrieval) ----------

def _doc_com_paragrafos_longos():
    longo = " ".join(f"palavra{i}" for i in range(140))  # ~1000 caracteres: não cabe num trecho
    return f"# Título do projeto\n\n## Visão geral\n\n{longo}\n\n## O que eu fiz\n\n{longo}"


def test_titulo_nunca_fica_sozinho_num_trecho():
    cs = chunk_segment(Segment("p.md", _doc_com_paragrafos_longos()))
    assert len(cs) > 2
    for c in cs:
        assert not all(l.lstrip().startswith("#") for l in c.text.split("\n")), f"trecho só de título: {c.text!r}"


def test_titulo_nao_termina_um_trecho_e_vai_para_o_proximo():
    cs = chunk_segment(Segment("p.md", _doc_com_paragrafos_longos()))
    for c in cs:
        linhas = c.text.split("\n")
        assert len(linhas) == 1 or not linhas[-1].lstrip().startswith("#"), f"termina em título: {c.text[-40:]!r}"
    assert any(c.text.startswith("## O que eu fiz") for c in cs)  # o título abre o trecho do seu conteúdo


def test_titulo_mais_texto_curto_continua_num_trecho_so():
    cs = chunk_segment(Segment("p.md", "# Título\n\n## Visão geral\n\nTexto curto sobre o projeto."))
    assert len(cs) == 1 and cs[0].text.startswith("# Título") and "Texto curto" in cs[0].text


def test_sem_titulos_o_comportamento_nao_muda():
    texto = "\n".join(f"- item {i}" for i in range(80))
    cs = chunk_segment(Segment("a.md", texto))
    assert cs[0].text.split("\n")[-1] == cs[1].text.split("\n")[0]  # sobreposição como antes
    assert all(f"- item {i}" in "\n".join(c.text for c in cs) for i in range(80))
