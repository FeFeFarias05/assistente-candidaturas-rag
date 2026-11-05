import argparse
import json
import sys
from pathlib import Path

from .extract import extract_job


def read_job(path: str | None) -> str:
    return Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()


def main(argv=None):
    p = argparse.ArgumentParser(prog="jobassist", description="Assistente de candidaturas")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract", help="extrai os requisitos de uma vaga")
    e.add_argument("vaga", nargs="?", help="arquivo .txt (omita para colar no stdin)")
    args = p.parse_args(argv)

    if args.cmd == "extract":
        print(json.dumps(extract_job(read_job(args.vaga)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
