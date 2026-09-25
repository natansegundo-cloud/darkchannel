#!/usr/bin/env python3
"""Compatibilidade explícita para chamadas antigas do provider Azure SDK."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.narration.engine import main as engine_main  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--provider" not in args:
        args.extend(["--provider", "azure_sdk"])
    return engine_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
