import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))
from run_eval import has, score_report  # noqa: E402

VAGA = "Requisitos: C#, Docker e Python. Diferencial: Java."

BOM = """## Pontos fortes
- Python: usa Python [cv.pdf#p1c1]
## Lacunas
- C#: sem evidência no material
- Docker: não usou Docker [proj.md#c1]
- Java: sem evidência
"""

RUIM = """## Pontos fortes
- Python [cv.pdf#p1c1]
- C#: domina C# [cv.pdf#p1c1]
- Docker: não usou Docker, mas conhece [proj.md#c1]
## Lacunas
- Java: sem evidência
"""


def test_termo_com_limite_de_palavra():
    assert has("Java", "Java e SQL") and not has("Java", "JavaScript") and has("C#", "sei C# bem")
    assert not has(".NET", "ASP.NET")  # ".NET" colado em "ASP" não conta como palavra própria


def test_relatorio_bom():
    m = score_report(BOM, [], VAGA)
    assert m["iscas"] == ["C#", "Docker", "Java"] and m["iscas_na_lacuna"] == ["C#", "Docker", "Java"]
    assert m["ausentes_como_forte"] == [] and m["fortes"] == 1 and m["lacunas"] == 3


def test_relatorio_ruim_pega_o_ausente_afirmado_como_forte():
    m = score_report(RUIM, ["citação inexistente: [x.md]"], VAGA)
    assert m["ausentes_como_forte"] == ["C#"]  # Docker tem "não": é item de ressalva, não afirmação
    assert m["iscas_na_lacuna"] == ["Java"] and len(m["citacoes_invalidas"]) == 1
