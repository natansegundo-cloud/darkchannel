#!/usr/bin/env python3
"""Ponto de entrada do projeto para o domínio atualmente consolidado."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.narration import engine  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capital Oculto")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser(
        "narracao",
        parents=[engine.build_parser(add_help=False)],
        help="Gera narração, áudio e timing pelo engine consolidado.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    build_parser().parse_args(raw_args)
    if not raw_args or raw_args[0] != "narracao":
        raise SystemExit("O subcomando narracao é o único domínio implementado nesta fase.")
    return engine.main(raw_args[1:])


if __name__ == "__main__":
    raise SystemExit(main())
