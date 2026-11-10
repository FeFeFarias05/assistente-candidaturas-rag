"""Avaliação de fundamentação (groundedness): cada afirmação do relatório é sustentada pelo trecho que ela cita?

Uso:
  python eval/grounding_eval.py --judge-model gpt-5.5   # gera os relatórios (RAG e material inteiro) e julga
  python eval/grounding_eval.py --sample 30             # escreve uma amostra para VOCÊ rotular à mão
  python eval/grounding_eval.py --agreement eval/out/grounding_amostra.csv   # compara os seus rótulos com os do juiz

Corpus: eval/corpus/docs (fictício). Vagas: eval/jobs_corpus. Os dois modos usam o MESMO prompt e o mesmo modelo.
O juiz deveria ser um modelo diferente do que escreveu os relatórios (um modelo tende a aprovar o próprio texto).
Rótulos: SUPPORTED (a evidência diz isso por completo), PARTIAL (só em parte, ou em nível menor), UNSUPPORTED.
"""
import argparse
import csv
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from jobassist import llm  # noqa: E402
from jobassist.analyze import CITATION, _section, analyze_no_rag, analyze_rag  # noqa: E402
from jobassist.extract import extract_job  # noqa: E402
from jobassist.ingest import ingest, load_index  # noqa: E402
from jobassist.material import load_material  # noqa: E402
from jobassist.retrieve import term_pattern  # noqa: E402

CORPUS = HERE / "corpus" / "docs"
JOBS = HERE / "jobs_corpus"
OUT = HERE / "out" / "grounding"
LABELS = ("SUPPORTED", "PARTIAL", "UNSUPPORTED")
SECTIONS = ("Pontos fortes", "O que destacar no currículo", "Rascunho de mensagem")
EVIDENCE_CHARS = 3000

JUDGE_SYSTEM = (
    "Você é um verificador rigoroso de fundamentação. Para cada AFIRMAÇÃO sobre uma candidata, você recebe a EVIDÊNCIA: "
    "os trechos do material dela que a afirmação cita. Classifique usando SOMENTE a evidência:\n"
    "- SUPPORTED: a evidência diz isso por completo e diretamente.\n"
    "- PARTIAL: a evidência sustenta só parte da afirmação, ou um nível/escopo menor que o afirmado.\n"
    "- UNSUPPORTED: a evidência não diz isso, contradiz, ou a afirmação vai além do que o texto permite.\n"
    "Não use conhecimento externo e não seja generoso: inferência não é suporte. Responda uma reason curta (até 20 palavras)."
)
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {"verdicts": {"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "integer"}, "label": {"type": "string", "enum": list(LABELS)}, "reason": {"type": "string"}},
        "required": ["id", "label", "reason"], "additionalProperties": False}}},
    "required": ["verdicts"], "additionalProperties": False,
}


# ---------- extração das afirmações (puro) ----------

def parse_claims(body: str) -> list[dict]:
    """Afirmações com citação: itens de Pontos fortes e de O que destacar, e linhas do rascunho."""
    claims = []
    for title in SECTIONS:
        for line in _section(body, title).split("\n"):
            line = line.strip()
            if title != "Rascunho de mensagem":
                if not re.match(r"^[-*]\s+", line):
                    continue
                line = re.sub(r"^[-*]\s+", "", line)
            elif not line or line.lower().startswith("rascunho"):
                continue
            text = CITATION.sub("", line).strip()
            if len(text) >= 12:
                claims.append({"section": title, "text": text, "cited": CITATION.findall(line)})
    return claims


def evidence_for(cited: list[str], texts: dict[str, str]) -> str:
    return "\n\n".join(f"[{c}]\n{texts[c][:EVIDENCE_CHARS]}" for c in dict.fromkeys(cited) if c in texts)


def literal_check(claim: str, evidence: str, techs: list[str]) -> bool | None:
    """Checagem determinística: tecnologia (uma palavra) citada na afirmação aparece na evidência?
    None se a afirmação não cita nenhuma tecnologia da vaga."""
    mentioned = [t for t in techs if " " not in t.strip() and term_pattern(t).search(claim)]
    if not mentioned:
        return None
    return all(term_pattern(t).search(evidence) for t in mentioned)


# ---------- métricas (puras) ----------

def aggregate(rows: list[dict]) -> dict:
    """Por modo: contagem e taxa de cada rótulo, e o mesmo por seção."""
    out: dict = {}
    for mode in sorted({r["mode"] for r in rows}):
        sel = [r for r in rows if r["mode"] == mode]
        out[mode] = {"n": len(sel), "rates": _rates(sel), "sections": {
            s: {"n": len([r for r in sel if r["section"] == s]), "rates": _rates([r for r in sel if r["section"] == s])}
            for s in SECTIONS}}
    return out


def _rates(sel: list[dict]) -> dict:
    """Taxas sobre as afirmações CITADAS. Sem citação é uma categoria à parte: no rascunho, a maioria é cortesia
    ("Fico à disposição para conversar"), e tratá-la como afirmação falsa distorceria a comparação."""
    cited = [r for r in sel if r["label"] != "UNCITED"]
    n = len(cited) or 1
    c = Counter(r["label"] for r in cited)
    return {lab: c[lab] / n for lab in LABELS} | {"uncited": (len(sel) - len(cited)) / (len(sel) or 1), "n_cited": len(cited)}


def normalize(rows: list[dict]) -> list[dict]:
    """Linha sem citação nunca foi ao juiz: vira UNCITED (também em resultados guardados por versões antigas)."""
    return [dict(r, label="UNCITED", reason="sem citação") if not r["cited"] else r for r in rows]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confiança de 95% para uma proporção k/n (Wilson: melhor que a normal em amostras pequenas)."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / d
    meia = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return centro - meia, centro + meia


def diff_ci(a: list[bool], b: list[bool], reps: int = 2000, seed: int = 7) -> tuple[float, float, float]:
    """Diferença de proporções (a menos b) com IC 95% por bootstrap; as amostras são independentes."""
    import numpy as np
    rng = np.random.default_rng(seed)
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    d = x[rng.integers(0, len(x), (reps, len(x)))].mean(axis=1) - y[rng.integers(0, len(y), (reps, len(y)))].mean(axis=1)
    return float(x.mean() - y.mean()), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def cohen_kappa(a: list[str], b: list[str]) -> float:
    """Concordância entre dois avaliadores além do acaso (1 = perfeita, 0 = acaso)."""
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] / n * cb[l] / n for l in set(a) | set(b))
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def agreement(human: list[str], judge: list[str]) -> dict:
    n = len(human)
    return {"n": n, "acuracia": sum(h == j for h, j in zip(human, judge)) / n if n else float("nan"),
            "kappa": cohen_kappa(human, judge),
            "aprova_a_mais": sum(j == "SUPPORTED" and h != "SUPPORTED" for h, j in zip(human, judge)),
            "reprova_a_mais": sum(h == "SUPPORTED" and j != "SUPPORTED" for h, j in zip(human, judge)),
            "confusao": Counter(zip(human, judge))}


# ---------- geração e julgamento ----------

def load_jobs() -> dict[str, str]:
    return {f.stem: f.read_text(encoding="utf-8") for f in sorted(JOBS.glob("*.txt"))}


def cached_job(name: str, text: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    cache_file = OUT / "jobs.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    if cache.get(name, {}).get("text") != text:
        cache[name] = {"text": text, "job": extract_job(text)}
        cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache[name]["job"]


def generate(force: bool) -> None:
    db = OUT / "index.db"
    OUT.mkdir(parents=True, exist_ok=True)
    ingest(CORPUS, db_path=db, rebuild=force)
    index, segments = load_index(db), load_material(CORPUS)
    for name, text in load_jobs().items():
        job = cached_job(name, text)
        for mode in ("rag", "full"):
            target = OUT / mode / f"{name}.json"
            if target.exists() and not force:
                continue
            print(f"gerando {name} ({mode})", file=sys.stderr)
            body, warnings = analyze_rag(job, index) if mode == "rag" else analyze_no_rag(job, segments)
            texts = dict(zip(index[0], index[1])) if mode == "rag" else {s.id: s.text for s in segments}
            target.parent.mkdir(exist_ok=True)
            target.write_text(json.dumps({"job": job, "body": body, "warnings": warnings, "texts": texts},
                                         ensure_ascii=False), encoding="utf-8")


def judge_report(claims: list[dict], model: str | None) -> list[dict]:
    """Uma chamada por relatório. Afirmação sem citação não vai ao juiz: fica como UNCITED (sem o que julgar)."""
    todo = [(i, c) for i, c in enumerate(claims) if c["evidence"]]
    verdicts: dict[int, dict] = {}
    if todo:
        prompt = "\n\n".join(f"### AFIRMAÇÃO {i}\n{c['text']}\n\n### EVIDÊNCIA {i}\n{c['evidence']}" for i, c in todo)
        res = llm.complete(prompt, system=JUDGE_SYSTEM, schema=JUDGE_SCHEMA, model=model)
        verdicts = {v["id"]: v for v in res["verdicts"]}
    out = []
    for i, c in enumerate(claims):
        v = verdicts.get(i) if c["evidence"] else {"label": "UNCITED", "reason": "sem citação"}
        out.append(v or {"label": "UNSUPPORTED", "reason": "o juiz não devolveu veredito"})
    return out


def judge_all(model: str | None) -> list[dict]:
    rows = []
    for mode in ("rag", "full"):
        for f in sorted((OUT / mode).glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            techs = [r["text"] for r in data["job"]["requirements"] if r["kind"] == "tech"]
            claims = parse_claims(data["body"])
            for c in claims:
                c["evidence"] = evidence_for(c["cited"], data["texts"])
            print(f"julgando {f.stem} ({mode}): {len(claims)} afirmações", file=sys.stderr)
            for c, v in zip(claims, judge_report(claims, model)):
                rows.append({"job": f.stem, "mode": mode, "section": c["section"], "claim": c["text"], "cited": c["cited"],
                             "evidence": c["evidence"], "label": v["label"], "reason": v["reason"],
                             "literal_ok": literal_check(c["text"], c["evidence"], techs)})
    (OUT / "rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


# ---------- relatório ----------

def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def render(rows: list[dict], gen_model: str, judge_model: str, usage: str | None) -> str:
    rows = normalize(rows)
    agg = aggregate(rows)
    names = {"rag": "RAG (só os trechos recuperados)", "full": "Material inteiro (sem busca)"}

    def cell(rates, label, n):
        k = round(rates[label] * n)
        lo, hi = wilson(k, n)
        return f"{pct(rates[label])} ({pct(lo)} a {pct(hi)})"

    L = ["# Avaliação de fundamentação (gerada por `eval/grounding_eval.py`)", "",
         f"Relatórios gerados com `{gen_model}`; afirmações julgadas por `{judge_model}`"
         + (" (**o mesmo modelo que escreveu: o juiz tende a aprovar o próprio texto**)" if gen_model == judge_model else "") + ". "
         "Corpus fictício de 25 documentos; 6 vagas. Uma afirmação é um item de Pontos fortes, de O que destacar, ou uma linha do rascunho. "
         "As taxas valem para as afirmações **com citação**; as sem citação aparecem à parte.", "",
         "## Resultado", "", "| Modo | Citadas | Sustentada (IC 95%) | Parcial | Não sustentada | Linhas sem citação |", "|---|---|---|---|---|---|"]
    for mode, a in agg.items():
        r, n = a["rates"], a["rates"]["n_cited"]
        L.append(f"| {names[mode]} | {n} de {a['n']} | {cell(r, 'SUPPORTED', n)} | {cell(r, 'PARTIAL', n)} | {cell(r, 'UNSUPPORTED', n)} | {pct(r['uncited'])} |")
    flags = {m: [r["label"] == "SUPPORTED" for r in rows if r["mode"] == m and r["label"] != "UNCITED"] for m in agg}
    if "rag" in flags and "full" in flags and flags["rag"] and flags["full"]:
        d, lo, hi = diff_ci(flags["rag"], flags["full"])
        L += ["", f"Diferença na taxa sustentada, RAG menos material inteiro: **{100 * d:+.0f} pp** (IC 95%: {100 * lo:+.0f} a {100 * hi:+.0f}). "
              + ("O intervalo inclui zero: inconclusivo." if lo <= 0 <= hi else "O intervalo exclui zero.")]
    L += ["", "## Por seção", "", "| Modo | Seção | Citadas | Sustentada | Parcial | Não sustentada | Sem citação |", "|---|---|---|---|---|---|---|"]
    for mode, a in agg.items():
        for sec, v in a["sections"].items():
            if v["n"]:
                r = v["rates"]
                L.append(f"| {mode} | {sec} | {r['n_cited']} de {v['n']} | {pct(r['SUPPORTED'])} | {pct(r['PARTIAL'])} | {pct(r['UNSUPPORTED'])} | {pct(r['uncited'])} |")
    checked = [r for r in rows if r["literal_ok"] is not None and r["label"] != "UNCITED"]
    if checked:
        agree = sum((r["label"] != "UNSUPPORTED") == r["literal_ok"] for r in checked)
        L += ["", "## Checagem cruzada com a regra determinística", "",
              f"Em {len(checked)} afirmações que citam uma tecnologia da vaga, o juiz concordou com a regra "
              f"\"o termo aparece na evidência\" em {pct(agree / len(checked))} dos casos "
              f"(juiz aprovou sem o termo na evidência: {sum(r['label'] != 'UNSUPPORTED' and not r['literal_ok'] for r in checked)}; "
              f"juiz reprovou com o termo presente: {sum(r['label'] == 'UNSUPPORTED' and r['literal_ok'] for r in checked)})."]
    bad = [r for r in rows if r["label"] == "UNSUPPORTED"][:10]
    L += ["", "## Afirmações não sustentadas", ""]
    L += [f"- ({r['mode']}, {r['job']}) {r['claim'][:150]}: _{r['reason']}_" for r in bad] or ["Nenhuma afirmação com citação foi considerada não sustentada."]
    parc = [r for r in rows if r["label"] == "PARTIAL"][:6]
    if parc:
        L += ["", "## Exemplos de afirmações parciais", ""] + [f"- ({r['mode']}, {r['job']}) {r['claim'][:140]}: _{r['reason']}_" for r in parc]
    if usage:
        L += ["", f"Consumo da API nesta execução: {usage}."]
    return "\n".join(L) + "\n"


# ---------- amostra para rotulagem manual ----------

def write_sample(rows: list[dict], n: int) -> None:
    rng = random.Random(7)
    rows = [r for r in normalize(rows) if r["label"] != "UNCITED"]  # sem citação não há o que rotular
    half = [r for r in rows if r["mode"] == "rag"], [r for r in rows if r["mode"] == "full"]
    pick = [r for group in half for r in rng.sample(group, min(n // 2, len(group)))]
    rng.shuffle(pick)
    with open(OUT.parent / "grounding_amostra.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "afirmacao", "evidencia", "seu_rotulo (SUPPORTED, PARTIAL ou UNSUPPORTED)"])
        for i, r in enumerate(pick, 1):
            w.writerow([i, r["claim"], r["evidence"][:1500].replace("\n", " "), ""])
    (OUT.parent / "grounding_amostra_juiz.json").write_text(json.dumps({str(i): r["label"] for i, r in enumerate(pick, 1)}), encoding="utf-8")
    print(f"amostra de {len(pick)} afirmações em {OUT.parent / 'grounding_amostra.csv'} (os rótulos do juiz ficam separados)")


def compare_with_human(path: Path) -> None:
    judge = json.loads((path.parent / "grounding_amostra_juiz.json").read_text(encoding="utf-8"))
    pairs = []
    with open(path, encoding="utf-8") as f:
        for row in csv.reader(f):
            if row[0].isdigit() and row[-1].strip().upper() in LABELS:
                pairs.append((row[-1].strip().upper(), judge[row[0]]))
    if not pairs:
        sys.exit("nenhum rótulo válido na planilha: preencha a última coluna com SUPPORTED, PARTIAL ou UNSUPPORTED")
    res = agreement([h for h, _ in pairs], [j for _, j in pairs])
    print(f"afirmações rotuladas: {res['n']} | acurácia do juiz: {pct(res['acuracia'])} | kappa: {res['kappa']:.2f}")
    print(f"juiz aprovou a mais: {res['aprova_a_mais']} | juiz reprovou a mais: {res['reprova_a_mais']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-model", help="modelo do juiz (use um diferente do gerador)")
    ap.add_argument("--force", action="store_true", help="refaz os relatórios")
    ap.add_argument("--render-only", action="store_true", help="refaz results_grounding.md a partir de rows.json, sem chamar a API")
    ap.add_argument("--sample", type=int, help="escreve uma amostra de N afirmações para rotular à mão")
    ap.add_argument("--agreement", type=Path, help="planilha da amostra com a sua última coluna preenchida")
    args = ap.parse_args()
    if args.agreement:
        return compare_with_human(args.agreement)
    if args.sample:
        return write_sample(json.loads((OUT / "rows.json").read_text(encoding="utf-8")), args.sample)
    from jobassist.config import load_config
    if args.render_only:
        rows = json.loads((OUT / "rows.json").read_text(encoding="utf-8"))
        text = render(rows, load_config().model, args.judge_model or "gpt-5.5", None)
        (HERE / "results_grounding.md").write_text(text, encoding="utf-8")
        return print(text)
    llm.reset_usage()
    generate(args.force)
    judge_model = args.judge_model or load_config().model
    rows = judge_all(args.judge_model)
    text = render(rows, load_config().model, judge_model, llm.usage_summary())
    (HERE / "results_grounding.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
