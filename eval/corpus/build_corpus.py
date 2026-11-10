"""Gera o corpus FICTÍCIO de avaliação com o LLM e valida cada documento por código.

Uso: python eval/corpus/build_corpus.py [--only 04_assistente_llm.md] [--force]

Os documentos já gerados ficam versionados em eval/corpus/docs/ (o corpus é parte do experimento: não é
regenerado a cada avaliação). Este script só existe para documentar como ele foi feito e permitir refazê-lo.
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))

from jobassist.retrieve import term_pattern  # noqa: E402
from spec import FORBIDDEN, NEGATION_ONLY, PROJECTS  # noqa: E402

DOCS = HERE / "docs"
LANGS = {"pt": "português do Brasil", "en": "inglês"}
HEADINGS = {"pt": "(##) Visão geral, O que eu fiz, Resultados, Desafios e aprendizados",
            "en": "(##) Overview, What I did, Results, Challenges and learnings"}
MIN_CHARS, MAX_CHARS, TRIES = 1500, 3600, 3


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).lower()


def check(project: dict, text: str) -> list[str]:
    """Problemas de um documento. Lista vazia = documento válido."""
    problems = [f"fato ausente (deve aparecer literalmente): {f}" for f in project["facts"] if _norm(f) not in _norm(text)]
    problems += [f"termo proibido: {t}" for t in FORBIDDEN if term_pattern(t).search(text)]
    problems += [f"{t} só pode aparecer em {only}" for t, only in NEGATION_ONLY.items()
                 if project["file"] != only and term_pattern(t).search(text)]
    if not MIN_CHARS <= len(text) <= MAX_CHARS:
        problems.append(f"tamanho {len(text)} fora de {MIN_CHARS}-{MAX_CHARS} caracteres")
    return problems


def prompt_for(project: dict, feedback: list[str]) -> str:
    facts = "\n".join(f"- {f}" for f in project["facts"])
    others = ", ".join(t for t in NEGATION_ONLY if t not in " ".join(project["facts"]))
    text = (
        f"Escreva um documento de projeto pessoal FICTÍCIO, em primeira pessoa, em {LANGS[project['lang']]}. "
        "Quem escreve é Ana, estudante de Engenharia de Software (use o feminino quando precisar).\n\n"
        f"Título: {project['title']}\nContexto: {project['context']}\n\n"
        f"Tamanho: entre 1800 e 2600 caracteres. Markdown simples: um título (#) e as seções {HEADINGS[project['lang']]}, "
        "TODAS escritas no idioma do documento. Texto corrido e listas curtas, sem tabelas.\n\n"
        f"FRASES OBRIGATÓRIAS. Cada uma deve aparecer EXATAMENTE como escrita (mesmas palavras, mesma ordem):\n{facts}\n\n"
        "REGRAS:\n"
        "- Não cite outras linguagens, frameworks, bancos de dados, serviços de nuvem ou ferramentas além das que "
        "aparecem nas frases obrigatórias.\n"
        f"- Nunca mencione nenhum destes termos: {', '.join(FORBIDDEN)}.\n"
        + (f"- Também não mencione: {others}.\n" if others else "")
        + "- Seja concreta (prazos, números, dificuldades reais), sem exagero e sem adjetivos vagos.\n"
        "- Responda só com o documento."
    )
    if feedback:
        text += "\n\nA versão anterior foi recusada. Corrija:\n" + "\n".join(f"- {p}" for p in feedback)
    return text


def build(project: dict) -> str:
    from jobassist.llm import complete  # import tardio: só a geração precisa de API

    feedback: list[str] = []
    for attempt in range(1, TRIES + 1):
        text = complete(prompt_for(project, feedback),
                        system="Você escreve documentos de projeto realistas e fiéis às instruções.").strip()
        feedback = check(project, text)
        if not feedback:
            return text + "\n"
        print(f"  tentativa {attempt}: {len(feedback)} problema(s): {feedback[:3]}", file=sys.stderr)
    raise RuntimeError(f"{project['file']}: não consegui gerar um documento válido: {feedback}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    DOCS.mkdir(exist_ok=True)
    for p in PROJECTS:
        path = DOCS / p["file"]
        if (args.only and p["file"] != args.only) or (path.exists() and not args.force):
            continue
        print(f"gerando {p['file']}", file=sys.stderr)
        path.write_text(build(p), encoding="utf-8")
    from jobassist import llm
    print(f"[custo] {llm.usage_summary()}", file=sys.stderr)


if __name__ == "__main__":
    main()
