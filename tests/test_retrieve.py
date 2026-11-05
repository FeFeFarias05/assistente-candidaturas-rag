import numpy as np

from jobassist import retrieve as rt

IDS = ["a#c1", "b#c1", "c#c1"]
TEXTS = ["python", "react", "bolo"]
MATRIX = np.eye(3, dtype=np.float32)  # cada chunk é um eixo
INDEX = (IDS, TEXTS, MATRIX)


def fake_embed(vecs):
    return lambda texts, kind="passage": np.array([vecs[t] for t in texts], dtype=np.float32)


def req(t):
    return {"text": t, "kind": "tech", "required": True}


def test_acha_o_trecho_certo_e_deixa_requisito_sem_evidencia(monkeypatch):
    monkeypatch.setattr(rt, "embed", fake_embed({"Python": [1, 0, 0], "Kubernetes": [0.1, 0.1, 0.1]}))
    res, unique = rt.retrieve([req("Python"), req("Kubernetes")], INDEX)
    assert [h.id for h in res[0].hits] == ["a#c1"]
    assert res[1].hits == []  # abaixo do limiar: sem evidência
    assert [h.id for h in unique] == ["a#c1"]


def test_sem_duplicatas_e_top_k(monkeypatch):
    v = {"x": [1, 0.9, 0.8], "y": [1, 0, 0]}
    monkeypatch.setattr(rt, "embed", fake_embed(v))
    res, unique = rt.retrieve([req("x"), req("y")], INDEX, top_k=2, threshold=0.5)
    assert len(res[0].hits) == 2 and [h.id for h in res[1].hits] == ["a#c1"]
    assert [h.id for h in unique] == ["a#c1", "b#c1"]  # a#c1 aparece uma vez só


def test_limite_total_mantem_os_melhores(monkeypatch):
    monkeypatch.setattr(rt, "embed", fake_embed({"x": [1, 0.9, 0.8]}))
    res, unique = rt.retrieve([req("x")], INDEX, top_k=3, threshold=0.5, max_total=2)
    assert [h.id for h in unique] == ["a#c1", "b#c1"]
    assert [h.id for h in res[0].hits] == ["a#c1", "b#c1"]


def test_tecnologia_citada_literalmente_entra_mesmo_com_nota_baixa(monkeypatch):
    texts = ["Usei Python e Flask", "outro texto", "C# nunca usei"]
    index = (IDS, texts, MATRIX)
    # nota semântica baixa (0.1), abaixo do limiar de 0.30
    monkeypatch.setattr(rt, "embed", fake_embed({"python": [0.1, 0.1, 0.1], "Ruby": [0.1, 0.1, 0.1]}))
    res, _ = rt.retrieve([req("python"), req("Ruby")], index)
    assert [h.id for h in res[0].hits] == ["a#c1"]  # achou pelo termo literal
    assert res[1].hits == []  # ausente: continua sem evidência


def test_termo_literal_respeita_limite_de_palavra(monkeypatch):
    index = (IDS, ["JavaScript e Java", "x", "y"], MATRIX)
    monkeypatch.setattr(rt, "embed", fake_embed({"Java": [0.0, 0.0, 0.0], "C#": [0.0, 0.0, 0.0]}))
    assert rt.retrieve([req("Java")], index)[0][0].hits  # "Java" aparece como palavra
    index = (IDS, ["JavaScript apenas", "x", "y"], MATRIX)
    assert rt.retrieve([req("Java")], index)[0][0].hits == []  # só dentro de "JavaScript": não vale
    index = (IDS, ["Sei C# bem", "x", "y"], MATRIX)
    assert rt.retrieve([req("C#")], index)[0][0].hits  # símbolo especial não quebra o regex


def test_idioma_casa_entre_ingles_e_portugues(monkeypatch):
    index = (IDS, ["Idiomas: Português (nativo), Inglês (B2)", "bolo", "outro"], MATRIX)
    monkeypatch.setattr(rt, "embed", fake_embed({"Advanced level of English": [0.1, 0.1, 0.1],
                                                  "Fluent Spanish": [0.1, 0.1, 0.1]}))
    soft = lambda t: {"text": t, "kind": "soft", "required": False}
    res, _ = rt.retrieve([soft("Advanced level of English"), soft("Fluent Spanish")], index)
    assert [h.id for h in res[0].hits] == ["a#c1"]  # "English" achou "Inglês"
    assert res[1].hits == []  # espanhol não está no material


def test_versao_nos_dois_lados():
    p = rt.term_pattern
    assert p("HTML5").search("Skills: HTML, CSS") and p("HTML").search("usa HTML5")
    assert p("CSS3").search("CSS e Bootstrap") and p("Python3").search("Python")
    assert not p("Java").search("JavaScript") and not p("S3").search("S")  # S3 mantém o número
    assert p("S3").search("AWS S3") and p("C#").search("sei C# bem")


def test_indice_vazio_ou_sem_requisitos():
    res, unique = rt.retrieve([req("x")], None)
    assert res[0].hits == [] and unique == []
    assert rt.retrieve([], INDEX) == ([], [])
