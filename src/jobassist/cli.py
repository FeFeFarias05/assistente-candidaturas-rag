import argparse
import json
import sys
from pathlib import Path

from . import llm, service, tracker
from .extract import extract_job
from .ingest import ingest


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
    sh = sub.add_parser("show", help="mostra uma candidatura e o relatório dela")
    sh.add_argument("id", type=int)
    ed = sub.add_parser("edit", help="edita os dados de uma candidatura")
    ed.add_argument("id", type=int)
    ed.add_argument("--company")
    ed.add_argument("--title")
    ed.add_argument("--date", help="AAAA-MM-DD")
    ed.add_argument("--status", choices=tracker.STATUSES)
    de = sub.add_parser("delete", help="apaga uma candidatura (o relatório em reports/ fica)")
    de.add_argument("id", type=int)
    de.add_argument("--yes", action="store_true", help="não pergunta antes de apagar")
    w = sub.add_parser("web", help="abre a interface web (só acessível nesta máquina)")
    w.add_argument("--port", type=int, default=8765)
    w.add_argument("--open", action="store_true", help="abre o navegador")
    i = sub.add_parser("ingest", help="indexa o material (embeddings) para a busca")
    i.add_argument("--rebuild", action="store_true", help="refaz o índice do zero (ex.: ao trocar de provedor)")
    return p


def manage(args) -> None:
    """show, edit e delete. Levanta KeyError/ValueError com mensagem pronta para o usuário."""
    if args.cmd == "show":
        a = tracker.get(args.id)
        print(f"#{a['id']}  {a['company']} | {a['title']}\n"
              f"status: {a['status']}   data: {a['applied_on']}   registrada em: {a['created_at']}")
        report = Path(a["report_path"]) if a["report_path"] else None
        if report and report.is_file():
            print(f"\n--- relatório ({report}) ---\n{report.read_text(encoding='utf-8')}")
        else:
            print("\n(sem relatório associado, ou o arquivo não existe mais)")
    elif args.cmd == "edit":
        tracker.update(args.id, company=args.company, title=args.title, applied_on=args.date, status=args.status)
        print(f"[tracker] #{args.id} atualizada")
    else:
        a = tracker.get(args.id)  # falha cedo se o id não existe
        if not args.yes:
            if not sys.stdin.isatty():
                raise ValueError("para apagar sem terminal interativo, use --yes")
            if input(f"Apagar #{a['id']} ({a['company']} | {a['title']})? [s/N] ").strip().lower() not in ("s", "sim", "y"):
                print("nada foi apagado")
                return
        tracker.delete(args.id)
        print(f"[tracker] #{args.id} apagada")


def main(argv=None):
    p = build_parser()
    args = p.parse_args(argv)
    llm.reset_usage()
    run(p, args)
    summary = llm.usage_summary()
    if summary:
        print(f"[custo] {summary}", file=sys.stderr)


def run(p: argparse.ArgumentParser, args) -> None:

    if args.cmd == "web":
        from .web.app import serve  # import tardio: o Flask só é carregado se for usado

        return serve(args.port, args.open)
    if args.cmd == "add":
        try:
            n = tracker.add(args.company, args.title, args.status, args.date)
        except ValueError:
            p.error(f"data inválida: {args.date!r}. Use AAAA-MM-DD")
        print(f"[tracker] candidatura #{n} registrada ({args.status})")
        return
    if args.cmd in ("show", "edit", "delete"):
        try:
            return manage(args)
        except (KeyError, ValueError) as e:
            p.error(str(e.args[0]))
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
        folder = service.material_folder()
        stats = ingest(folder, rebuild=args.rebuild)
        print(f"[ingest] {folder}: {stats['novos']} arquivo(s) indexado(s), "
              f"{stats['inalterados']} inalterado(s), {stats['removidos']} removido(s)")
        return

    if args.cmd == "extract":
        print(json.dumps(extract_job(read_job(args.vaga)), ensure_ascii=False, indent=2))
        return

    try:
        result = service.run_analysis(read_job(args.vaga), args.lang, args.no_rag, args.yes_send_all)
    except service.PrivacyError as e:
        p.error(f"{e}. Use o material fictício ou confirme com --yes-send-all")
    except (service.NoMaterialError, ValueError, RuntimeError) as e:
        p.error(str(e))
    print(result["report"])
    for w in result["warnings"]:
        print(f"[analyze] AVISO: {w}", file=sys.stderr)
    print(f"\n[analyze] relatório salvo em {result['report_path']}", file=sys.stderr)
    register(result["job"], Path(result["report_path"]), args.register)


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
