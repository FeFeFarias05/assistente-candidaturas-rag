"""Avaliação: roda vagas de teste nos dois modos (RAG e sem RAG) e confere invenções e iscas.

Uso: python eval/run_eval.py [--jobs PASTA ...] [--out eval/results.md]
Usa SEMPRE o material fictício (data/sample). Chama a API de verdade: não faz parte do pytest.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from jobassist.analyze import _section, analyze_no_rag, analyze_rag  # noqa: E402
from jobassist.extract import extract_job  # noqa: E402
from jobassist.ingest import ingest, load_index  # noqa: E402
from jobassist.material import load_material  # noqa: E402
from jobassist.retrieve import retrieve  # noqa: E402

SAMPLE = ROOT / "data" / "sample"
OUT = ROOT / "eval" / "out"
# Termos que o perfil fictício NÃO tem como experiência (ver data/sample/README.md).
# Docker e Redux aparecem no material só como "não usei": devem ir para Lacunas.
ABSENT = ["C#", ".NET", "ASP.NET", "SQL Server", "Azure", "AWS", "jQuery", "Docker", "Kubernetes",
          "Terraform", "Redux", "Jest", "Power BI", "Excel", "Linux", "CI/CD", "GraphQL", "Java"]


def has(term: str, text: str) -> bool:
    return bool(re.search(rf"(?<![\w.]){re.escape(term)}(?![\w])", text, re.IGNORECASE))


def score_report(body: str, warnings: list[str], job_text: str) -> dict:
    """Métricas automáticas de um relatório. Função pura (testável)."""
    items = re.split(r"\n(?=\s*[-*]\s)", _section(body, "Pontos fortes"))
    lacunas = _section(body, "Lacunas")

    def afirma(item: str) -> bool:  # item que apresenta algo como ponto forte
        low = item.lower()
        return "sem evidência" not in low and not re.search(r"\bnão\b", low)

    expected = [t for t in ABSENT if has(t, job_text)]
    return {
        "fortes": sum(1 for i in items if i.strip()),
        "lacunas": len(re.findall(r"^\s*[-*]\s", lacunas, re.MULTILINE)),
        "iscas": expected,
        "iscas_na_lacuna": [t for t in expected if has(t, lacunas)],
        "ausentes_como_forte": [t for t in ABSENT if any(has(t, i) and afirma(i) for i in items)],
        "citacoes_invalidas": [w for w in warnings if w.startswith("citação inexistente")],
        "avisos": warnings,
    }


def load_jobs(dirs: list[Path]) -> dict[str, str]:
    return {f.stem: f.read_text(encoding="utf-8") for d in dirs for f in sorted(d.glob("*.txt"))}


def cached_extract(name: str, text: str) -> dict:
    """A extração é cacheada: reexecutar a avaliação não repete essas chamadas."""
    OUT.mkdir(parents=True, exist_ok=True)
    cache_file = OUT / "jobs_cache.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    key = hashlib.sha256(text.encode()).hexdigest()[:16]
    if cache.get(name, {}).get("key") != key:
        cache[name] = {"key": key, "job": extract_job(text)}
        cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache[name]["job"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", nargs="+", type=Path, default=[ROOT / "eval" / "jobs"])
    ap.add_argument("--out", type=Path, default=ROOT / "eval" / "results.md")
    args = ap.parse_args()

    jobs = load_jobs(args.jobs)
    ingest(SAMPLE)
    index, segments = load_index(), load_material(SAMPLE)
    rows, relevance = [], []
    for name, text in jobs.items():
        print(f"== {name}", file=sys.stderr)
        job = cached_extract(name, text)
        evidence, _ = retrieve(job["requirements"], index)
        relevance.append((name, evidence))
        for mode, run in (("sem RAG", lambda: analyze_no_rag(job, segments)), ("RAG", lambda: analyze_rag(job, index))):
            body, warnings = run()
            (OUT / mode.replace(" ", "_")).mkdir(exist_ok=True)
            (OUT / mode.replace(" ", "_") / f"{name}.md").write_text(body, encoding="utf-8")
            rows.append((name, mode, score_report(body, warnings, text)))
    write_results(args.out, rows, relevance)
    print(f"resultados em {args.out}", file=sys.stderr)


def write_results(path: Path, rows, relevance) -> None:
    L = ["# Resultados da avaliação (gerado por `eval/run_eval.py`)", "",
         "Material: `data/sample` (fictício). Cada vaga roda nos dois modos com o mesmo prompt.", "",
         "## Por vaga", "",
         "| Vaga | Modo | Fortes | Lacunas | Iscas na vaga | Iscas em Lacunas | Ausentes afirmados como forte | Citações inválidas | Avisos |",
         "|---|---|---|---|---|---|---|---|---|"]
    for name, mode, m in rows:
        L.append(f"| {name} | {mode} | {m['fortes']} | {m['lacunas']} | {', '.join(m['iscas']) or '-'} | "
                 f"{', '.join(m['iscas_na_lacuna']) or '-'} | {', '.join(m['ausentes_como_forte']) or '-'} | "
                 f"{len(m['citacoes_invalidas'])} | {len(m['avisos'])} |")
    L += ["", "## Resumo por modo", "", "| Modo | Iscas detectadas | Ausentes afirmados como forte | Citações inválidas | Relatórios com avisos |",
          "|---|---|---|---|---|"]
    for mode in ("sem RAG", "RAG"):
        ms = [m for _, md, m in rows if md == mode]
        iscas, achadas = sum(len(m["iscas"]) for m in ms), sum(len(m["iscas_na_lacuna"]) for m in ms)
        L.append(f"| {mode} | {achadas}/{iscas} | {sum(len(m['ausentes_como_forte']) for m in ms)} | "
                 f"{sum(len(m['citacoes_invalidas']) for m in ms)} | {sum(1 for m in ms if m['avisos'])}/{len(ms)} |")
    L += ["", "## Avisos de validação", ""]
    for name, mode, m in rows:
        for w in m["avisos"]:
            L.append(f"- {name} ({mode}): {w}")
    OUT.mkdir(parents=True, exist_ok=True)
    rel = ["# Trechos recuperados por requisito (para avaliar relevância)", ""]
    for name, evidence in relevance:
        rel += [f"## {name}", ""]
        for r in evidence:
            hits = "; ".join(f"{h.id} ({h.score})" for h in r.hits) or "NENHUM"
            top = r.hits[0].text.replace("\n", " ")[:90] if r.hits else ""
            rel.append(f"- **{r.requirement['text'][:60]}** → {hits}" + (f"\n  > {top}" if top else ""))
        rel.append("")
    (OUT / "relevance.md").write_text("\n".join(rel), encoding="utf-8")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
