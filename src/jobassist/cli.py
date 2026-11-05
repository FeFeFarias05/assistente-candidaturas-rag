import argparse
import json
import sys
from pathlib import Path

from . import tracker
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
    a.add_argument("--register", nargs="?", const="interessada", choices=tracker.STATUSES, metavar="STATUS",
                   help="registra a candidatura sem perguntar (padrão do status: interessada)")
    ad = sub.add_parser("add", help="registra uma candidatura manualmente")
    ad.add_argument("company")
    ad.add_argument("title")
    ad.add_argument("--status", default="interessada", choices=tracker.STATUSES)
    ad.add_argument("--date", help="data da candidatura (AAAA-MM-DD; padrão: hoje)")
    ls = sub.add_parser("list", help="lista as candidaturas")
    ls.add_argument("--status", choices=tracker.STATUSES)
    st = sub.add_parser("status", help="atualiza o status de uma candidatura")
    st.add_argument("id", type=int)
    st.add_argument("novo", choices=tracker.STATUSES)
    i = sub.add_parser("ingest", help="indexa o material (embeddings) para a busca")
    i.add_argument("--rebuild", action="store_true", help="refaz o índice do zero (ex.: ao trocar de provedor)")
    return p


def main(argv=None):
    p = build_parser()
    args = p.parse_args(argv)

    if args.cmd == "add":
        n = tracker.add(args.company, args.title, args.status, args.date)
        print(f"[tracker] candidatura #{n} registrada ({args.status})")
        return
    if args.cmd == "list":
        rows = tracker.list_all(args.status)
        for r in rows:
            print(f"#{r['id']:<3} {r['applied_on']}  {r['status']:<11}  {r['company']} | {r['title']}")
        if not rows:
            print("nenhuma candidatura registrada")
        return
    if args.cmd == "status":
        try:
            tracker.set_status(args.id, args.novo)
        except KeyError as e:
            p.error(str(e.args[0]))
        print(f"[tracker] #{args.id} agora está: {args.novo}")
        return

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
    register(job, path, args.register)


def register(job: dict, report: Path, status: str | None) -> None:
    """Registra a candidatura: direto com --register, ou perguntando se houver terminal interativo."""
    if status is None:
        if not sys.stdin.isatty():
            return
        if input("Registrar esta candidatura? [s/N] ").strip().lower() not in ("s", "sim", "y"):
            return
        status = input(f"Status [{'/'.join(tracker.STATUSES)}] (Enter = interessada): ").strip() or "interessada"
        if status not in tracker.STATUSES:
            print(f"[tracker] status inválido ({status}); não registrei.", file=sys.stderr)
            return
    n = tracker.add(job["company"] or "empresa não informada", job["title"] or "vaga sem título",
                    status, report_path=str(report))
    print(f"[tracker] candidatura #{n} registrada ({status})", file=sys.stderr)


if __name__ == "__main__":
    main()
