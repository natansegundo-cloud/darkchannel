#!/usr/bin/env python3
"""Valida a Visual Library V1 sem tocar no pipeline de producao."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "config" / "visual_library.json"
TEST_ROOT = ROOT / "tests" / "visual_library" / "s001_s006"
PALETTE = {"#111111", "#C4E538", "#E8A33D", "#F4F3EF", "#D9D9D4"}
VISUAL_TYPES = {
    "DATA_HERO", "SYSTEM_MAP", "TRANSFORMATION", "SCALE", "EDITORIAL_TYPE",
    "TIMELINE", "COMPARISON", "PROGRESS", "CHARACTER_INTERACTION",
}
REQUIRED_FIELDS = {
    "id", "category", "visual_type", "description", "semantic_use", "allowed_accents",
    "supports_character", "supports_animation", "preferred_size", "dominance_allowed",
    "source", "version",
}
REQUIRED_DIRS = [
    "assets/components/counters", "assets/components/bars", "assets/components/timelines",
    "assets/components/comparisons", "assets/components/stacks", "assets/components/meters",
    "assets/components/flows", "assets/components/scales", "assets/components/typography",
    "assets/components/data", "assets/metaphors/lifestyle-creep", "assets/metaphors/expense-pressure",
    "assets/metaphors/shrinking-surplus", "assets/metaphors/salary-gap",
    "assets/metaphors/status-ladder", "assets/metaphors/reference-shift",
    "assets/metaphors/fixed-cost-pressure", "assets/metaphors/money-flow",
    "assets/motion/reveal", "assets/motion/counter", "assets/motion/fill", "assets/motion/push",
    "assets/motion/collapse", "assets/motion/split", "assets/motion/carry-over",
    "tests/visual_library/s001_s006",
]


class Validation:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def extract_symbol(text: str) -> str:
    match = re.search(r"    (<symbol\b[\s\S]*?</symbol>)", text)
    return match.group(1) if match else ""


def validate_catalog(v: Validation) -> tuple[dict, dict[str, dict]]:
    v.require(CATALOG_PATH.exists(), "config/visual_library.json ausente")
    if not CATALOG_PATH.exists():
        return {}, {}
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    v.require(catalog.get("integrated_with_production") is False, "biblioteca nao pode estar integrada a producao")
    v.require(set(catalog.get("visual_types", [])) == VISUAL_TYPES, "classes visuais oficiais divergentes")
    v.require(catalog.get("selection_order", [])[-1:] == ["support_icon"], "icone deve ser a ultima opcao")
    assets = catalog.get("assets", [])
    v.require(30 <= len(assets) <= 45, f"quantidade de assets fora da meta enxuta: {len(assets)}")
    ids = [asset.get("id") for asset in assets]
    v.require(len(ids) == len(set(ids)), "IDs de asset duplicados")
    for asset in assets:
        missing = REQUIRED_FIELDS - set(asset)
        v.require(not missing, f"{asset.get('id')}: campos ausentes {sorted(missing)}")
        v.require(asset.get("visual_type") in VISUAL_TYPES, f"{asset.get('id')}: visual_type invalido")
        v.require(asset.get("dominance_allowed") is True, f"{asset.get('id')}: dominance_allowed deve ser true")
        v.require(asset.get("version") == 1, f"{asset.get('id')}: versao inesperada")
        accents = asset.get("allowed_accents", [])
        v.require(len(accents) <= 1 and set(accents) <= {"lime", "amber"}, f"{asset.get('id')}: accents invalidos")
    recipes = catalog.get("motion_recipes", [])
    v.require(len(recipes) == 7, "sete receitas declarativas de movimento eram esperadas")
    return catalog, {asset["id"]: asset for asset in assets}


def validate_source(v: Validation, asset: dict) -> None:
    path = ROOT / asset["source"]
    v.require(path.exists(), f"fonte ausente: {asset['source']}")
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    try:
        tree = ET.fromstring(text)
    except ET.ParseError as exc:
        v.errors.append(f"XML invalido em {asset['source']}: {exc}")
        return
    v.require(tree.attrib.get("viewBox") == "0 0 1200 700", f"{asset['id']}: viewBox raiz divergente")
    symbols = [node for node in tree.iter() if local_name(node.tag) == "symbol"]
    v.require(len(symbols) == 1, f"{asset['id']}: deve conter exatamente um symbol")
    if symbols:
        v.require(symbols[0].attrib.get("id") == asset.get("symbol_id"), f"{asset['id']}: symbol_id divergente")
        v.require(symbols[0].attrib.get("viewBox") == "0 0 1200 700", f"{asset['id']}: viewBox do symbol divergente")
    forbidden = {"text", "image", "filter", "foreignObject"}
    found_forbidden = {local_name(node.tag) for node in tree.iter()} & forbidden
    v.require(not found_forbidden, f"{asset['id']}: elementos proibidos {sorted(found_forbidden)}")
    for node in tree.iter():
        for key in ("fill", "stroke"):
            value = node.attrib.get(key)
            if value and value not in PALETTE and value != "none":
                v.errors.append(f"{asset['id']}: cor fora da paleta {value}")
        width = node.attrib.get("stroke-width")
        if width:
            v.require(width in {"3", "4", "6"}, f"{asset['id']}: stroke-width fora de 6/4/3: {width}")
    actual_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    v.require(actual_hash == asset.get("sha256"), f"{asset['id']}: hash da fonte divergente")


def validate_test(v: Validation, assets: dict[str, dict]) -> None:
    manifest_path = TEST_ROOT / "scene_manifest.json"
    v.require(manifest_path.exists(), "manifesto do teste ausente")
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes = manifest.get("scenes", [])
    v.require([scene.get("scene_id") for scene in scenes] == [f"S{i:03d}" for i in range(1, 7)], "teste deve conter S001-S006")
    required_coverage = {"DATA_HERO", "TIMELINE", "TRANSFORMATION", "SYSTEM_MAP"}
    coverage = {scene.get("visual_type") for scene in scenes}
    v.require(required_coverage <= coverage, f"cobertura visual incompleta: {sorted(required_coverage - coverage)}")
    v.require(any(scene.get("character") for scene in scenes), "teste precisa de uma cena com personagem")
    v.require(any(not scene.get("character") for scene in scenes), "teste precisa de uma cena sem personagem")
    layouts = [scene.get("layout") for scene in scenes]
    v.require(all(a != b for a, b in zip(layouts, layouts[1:])), "layout repetido em cenas consecutivas")
    v.require(all(scene.get("phosphor") is False for scene in scenes), "teste nao deveria depender de Phosphor")

    rig_text = (ROOT / "assets/characters/capital_oculto_character_rig_v4.svg").read_text(encoding="utf-8")
    rig_defs = re.search(r"<defs>([\s\S]*?)</defs>", rig_text)
    for scene in scenes:
        scene_id = scene["scene_id"]
        path = TEST_ROOT / scene["file"]
        v.require(path.exists(), f"{scene_id}: SVG ausente")
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        root = ET.fromstring(text)
        v.require(root.attrib.get("viewBox") == "0 0 1920 1080", f"{scene_id}: canvas divergente")
        ratio = scene.get("dominant_area_ratio", 0)
        v.require(0.55 <= ratio <= 0.75, f"{scene_id}: area dominante fora da faixa: {ratio}")
        asset_id = scene.get("dominant_asset")
        v.require(asset_id in assets, f"{scene_id}: asset dominante nao catalogado")
        if asset_id in assets:
            source_text = (ROOT / assets[asset_id]["source"]).read_text(encoding="utf-8")
            v.require(extract_symbol(source_text) in text, f"{scene_id}: symbol nao foi incorporado mecanicamente")
            v.require(f'href="#{assets[asset_id]["symbol_id"]}"' in text, f"{scene_id}: asset dominante nao e instanciado por use")
        if scene.get("character"):
            v.require(scene.get("character_function") in {"REACTION", "ACTION", "SCALE", "CAUSE", "CONTINUITY", "CONTRAST"}, f"{scene_id}: funcao de personagem invalida")
            v.require('href="#char-base"' in text, f"{scene_id}: personagem nao usa char-base")
            v.require(bool(rig_defs and rig_defs.group(1).strip() in text), f"{scene_id}: rig nao foi incorporado da fonte oficial")
        else:
            v.require('id="char-base"' not in text, f"{scene_id}: rig incorporado sem personagem")
        v.require("phosphor" not in text.lower(), f"{scene_id}: referencia inesperada a Phosphor")

    contact = TEST_ROOT / "contact_sheet_25.svg"
    v.require(contact.exists(), "contact sheet SVG ausente")
    if contact.exists():
        text = contact.read_text(encoding="utf-8")
        root = ET.fromstring(text)
        images = [node for node in root.iter() if local_name(node.tag) == "image"]
        v.require(len(images) == 6, "contact sheet deve conter seis frames")
        v.require(all(node.attrib.get("width") == "480" and node.attrib.get("height") == "270" for node in images), "frames do contact sheet nao estao a 25%")


def main() -> int:
    v = Validation()
    for directory in REQUIRED_DIRS:
        v.require((ROOT / directory).is_dir(), f"diretorio ausente: {directory}")
    catalog, assets = validate_catalog(v)
    for asset in assets.values():
        validate_source(v, asset)
    validate_test(v, assets)
    docs = ROOT / "docs" / "VISUAL_LIBRARY_V1.md"
    v.require(docs.exists(), "docs/VISUAL_LIBRARY_V1.md ausente")
    if catalog:
        counts = Counter(asset["category"] for asset in assets.values())
        v.note("assets por categoria: " + ", ".join(f"{key}={counts[key]}" for key in sorted(counts)))
        v.note(f"total: {len(assets)} SVGs + {len(catalog.get('motion_recipes', []))} receitas")
    if v.errors:
        print("Visual Library V1: FALHOU")
        for error in v.errors:
            print(f"- {error}")
        return 1
    print("Visual Library V1: OK")
    for note in v.notes:
        print(f"- {note}")
    print("- prototipo separado; nenhuma integracao de producao detectada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
