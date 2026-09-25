#!/usr/bin/env python3
"""Valida o contrato estrutural do rig oficial do Capital Oculto."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RIG = ROOT / "assets" / "characters" / "capital_oculto_character_rig_v4.svg"
SVG_NS = "{http://www.w3.org/2000/svg}"
EXPECTED_GROUPS = (
    "char-head",
    "char-neck",
    "char-torso",
    "char-tie",
    "char-arm-left",
    "char-arm-right",
    "char-leg-left",
    "char-leg-right",
)
EXPECTED_LAYER_ORDER = (
    "char-leg-left",
    "char-leg-right",
    "char-neck",
    "char-torso",
    "char-tie",
    "char-arm-left",
    "char-arm-right",
    "char-head",
)
EXPECTED_PIVOTS = {
    "char-head": "160 205",
    "char-torso": "160 225",
    "char-tie": "160 225",
    "char-arm-left": "112 231",
    "char-arm-right": "208 231",
    "char-leg-left": "137 370",
    "char-leg-right": "183 370",
}
ALLOWED_COLORS = {"#111111", "#C4E538", "#F4F3EF"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def validate_rig(path: Path = DEFAULT_RIG) -> dict[str, Any]:
    try:
        tree = ET.parse(path)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Rig V4 não encontrado: {path}") from exc
    except ET.ParseError as exc:
        raise RuntimeError(f"Rig V4 contém XML inválido: {exc}") from exc

    root = tree.getroot()
    if root.attrib.get("viewBox") != "0 0 320 640":
        raise RuntimeError("O rig V4 deve usar viewBox 0 0 320 640.")

    elements = list(root.iter())
    ids = [element.attrib["id"] for element in elements if "id" in element.attrib]
    duplicates = sorted(key for key, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise RuntimeError(f"IDs duplicados no rig V4: {', '.join(duplicates)}")
    by_id = {element.attrib["id"]: element for element in elements if "id" in element.attrib}

    symbols = [element for element in elements if local_name(element.tag) == "symbol"]
    if len(symbols) != 1 or symbols[0].attrib.get("id") != "char-base":
        found = ", ".join(element.attrib.get("id", "sem-id") for element in symbols) or "nenhum"
        raise RuntimeError(f"Contrato violado: somente char-base pode ser <symbol>. Encontrados: {found}")

    for group_id in EXPECTED_GROUPS:
        element = by_id.get(group_id)
        if element is None:
            raise RuntimeError(f"Grupo obrigatório ausente: {group_id}")
        if local_name(element.tag) != "g":
            raise RuntimeError(f"Contrato violado: {group_id} deve permanecer <g>, nunca <{local_name(element.tag)}>.")
        if "viewBox" in element.attrib:
            raise RuntimeError(f"Contrato violado: {group_id} não pode criar viewport próprio.")

    char_base = by_id["char-base"]
    references = []
    for child in list(char_base):
        if local_name(child.tag) != "use":
            raise RuntimeError("char-base deve conter somente instâncias <use> das partes do corpo.")
        href = child.attrib.get("href") or child.attrib.get("{http://www.w3.org/1999/xlink}href")
        references.append((href or "").removeprefix("#"))
    if tuple(references) != EXPECTED_LAYER_ORDER:
        raise RuntimeError("A ordem de camadas do char-base diverge do contrato V4.")

    for group_id, pivot in EXPECTED_PIVOTS.items():
        if by_id[group_id].attrib.get("data-pivot") != pivot:
            raise RuntimeError(f"Pivô inválido em {group_id}; esperado {pivot}.")

    colors = {
        value.upper()
        for element in elements
        for attribute in ("fill", "stroke")
        if (value := element.attrib.get(attribute, "")).startswith("#")
    }
    unexpected_colors = sorted(colors - ALLOWED_COLORS)
    if unexpected_colors:
        raise RuntimeError(f"Cores fora da paleta fixa do rig: {', '.join(unexpected_colors)}")

    return {
        "file": str(path),
        "symbol": "char-base",
        "groups": list(EXPECTED_GROUPS),
        "view_box": root.attrib["viewBox"],
        "colors": sorted(colors),
    }


def main() -> int:
    result = validate_rig()
    print(
        "RIG V4 VÁLIDO — "
        f"1 symbol ({result['symbol']}), {len(result['groups'])} grupos no mesmo sistema de coordenadas."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
