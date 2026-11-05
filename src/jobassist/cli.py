import argparse
import json
import sys
from pathlib import Path

from .analyze import analyze_no_rag, analyze_rag, save_report
from .config import load_config
from .extract import extract_job
from .ingest import ingest, load_index
from .material import load_material

SAMPLE = Path("data/sample")


def read_job(path: str | None) -> str:
    return Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jobassist", description="Assistente de candidaturas")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract", help="extrai os requisitos de uma vaga")
    e.add_argument("vaga", nargs="?", help="arquivo .txt (omita para colar no stdin)")
    a = sub.add_parser("analyze", help="analisa a aderência do seu perfil à vaga")
    a.add_argument("vaga", nargs="?", help="arquivo .txt (omita para colar no stdin)")
    a.add_argument("--no-rag", action="store_true", help="envia o material inteiro no prompt (linha de base)")
    a.add_argument("--lang", choices=["pt", "en"], help="idioma do rascunho (padrão: o da vaga)")
    a.add_argument("--yes-send-all", action="store_true", help="confirma enviar TODO o material à API")
    i = sub.add_parser("ingest", help="indexa o material (embeddings) para a busca")
    i.add_argument("--rebuild", action="store_true", help="refaz o índice do zero (ex.: ao trocar de provedor)")
    return p


def main(argv=None):
    p = build_parser()
    args = p.parse_args(argv)

    if args.cmd == "ingest":
        folder = load_config().material_dir
        stats = ingest(folder, rebuild=args.rebuild)
        print(f"[ingest] {folder}: {stats['novos']} arquivo(s) indexado(s), "
              f"{stats['inalterados']} inalterado(s), {stats['removidos']} removido(s)")
        return

    if args.cmd == "extract":
        print(json.dumps(extract_job(read_job(args.vaga)), ensure_ascii=False, indent=2))
        return

    folder = Path(load_config().material_dir)
    if args.no_rag:
        if folder.resolve() != SAMPLE.resolve() and not args.yes_send_all:
            p.error(f"--no-rag envia TODO o conteúdo de {folder} à API. Use o material fictício ou confirme com --yes-send-all")
        segments = load_material(folder)
        if not segments:
            p.error(f"nenhum material encontrado em {folder}")
        job = extract_job(read_job(args.vaga))
        print(f"[analyze] enviando o material inteiro ({len(segments)} trechos) à API", file=sys.stderr)
        body, warnings = analyze_no_rag(job, segments, args.lang)
        mode = "sem RAG"
    else:
        ingest(folder)  # incremental: só reindexa o que mudou
        job = extract_job(read_job(args.vaga))
        body, warnings = analyze_rag(job, load_index(), args.lang)
        mode = "RAG"
    path = save_report(job, body, mode, warnings)
    print(body)
    for w in warnings:
        print(f"[analyze] AVISO: {w}", file=sys.stderr)
    print(f"\n[analyze] relatório salvo em {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
