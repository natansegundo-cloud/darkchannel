#!/usr/bin/env python3
"""Valida o sprint estático S001–S006 da Art Direction V4."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from validar_rig_personagem import validate_rig


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "art_direction_v4.json"
RIG = ROOT / "assets" / "characters" / "capital_oculto_character_rig_v4.svg"
SPRINT = ROOT / "episodios" / "CO-001-por-que-ganhar-mais-nao-basta" / "testes" / "art_direction_v4_s001_s006"
MANIFEST = SPRINT / "art_direction_manifest.json"
BOARD = SPRINT / "review_art_direction_v4_25.svg"
BOARD_PNG = SPRINT / "review_art_direction_v4_25.png"
EXPECTED = tuple(f"S{i:03d}" for i in range(1, 7))
CHARACTER_FUNCTIONS = {"reaction", "scale", "action", "cause", "continuity"}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    return next((node for node in root.iter() if node.attrib.get("id") == element_id), None)


def href(node: ET.Element) -> str:
    return node.attrib.get("href") or node.attrib.get("{http://www.w3.org/1999/xlink}href", "")


def validate_scene(entry: dict[str, Any], config: dict[str, Any]) -> str:
    scene_id = entry["scene_id"]
    path = ROOT / entry["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise RuntimeError(f"{scene_id}: hash desatualizado no manifesto.")
    root = ET.parse(path).getroot()
    if root.attrib.get("viewBox") != "0 0 1920 1080":
        raise RuntimeError(f"{scene_id}: canvas diferente de 1920x1080.")
    scene = find_by_id(root, f"scene-{scene_id}")
    if scene is None or local_name(scene.tag) != "g":
        raise RuntimeError(f"{scene_id}: raiz da cena deve ser group.")
    visual_class = scene.attrib.get("data-visual-class")
    if visual_class != entry["visual_class"] or visual_class not in config["visual_classes"]:
        raise RuntimeError(f"{scene_id}: classe visual inválida.")
    if not scene.attrib.get("data-future-motion"):
        raise RuntimeError(f"{scene_id}: transformação futura não declarada.")

    metadata_node = next((node for node in root if local_name(node.tag) == "metadata"), None)
    if metadata_node is None or not metadata_node.text:
        raise RuntimeError(f"{scene_id}: metadata ausente.")
    metadata = json.loads(metadata_node.text)
    if metadata.get("art_direction") != config["art_direction_id"]:
        raise RuntimeError(f"{scene_id}: art direction incorreta.")
    if float(metadata.get("library_icon_area_ratio", 1)) > float(config["library_icon_max_area_ratio"]):
        raise RuntimeError(f"{scene_id}: ícones ocupam mais de 10% do canvas.")

    uses = [node for node in root.iter() if local_name(node.tag) == "use"]
    icon_uses = [node for node in uses if href(node).startswith("#icon-")]
    icon_area = 0.0
    for icon in icon_uses:
        if icon.attrib.get("data-dominant") == "true":
            raise RuntimeError(f"{scene_id}: ícone de biblioteca marcado como dominante.")
        icon_area += float(icon.attrib.get("width", "0")) * float(icon.attrib.get("height", "0"))
    if icon_area / (1920 * 1080) > float(config["library_icon_max_area_ratio"]):
        raise RuntimeError(f"{scene_id}: área calculada dos ícones excede 10%.")

    titles = [node for node in scene.iter() if node.attrib.get("data-role") == "scene-title"]
    if len(titles) > 1 or (scene_id != "S001" and titles):
        raise RuntimeError(f"{scene_id}: título de slide repetitivo detectado.")
    if any(node.attrib.get("data-role") == "card" for node in scene.iter()):
        raise RuntimeError(f"{scene_id}: card genérico proibido no sprint.")
    if not any(node.attrib.get("data-dominant") == "true" for node in scene.iter()):
        raise RuntimeError(f"{scene_id}: elemento dominante não declarado.")

    symbols = [node.attrib.get("id") for node in root.iter() if local_name(node.tag) == "symbol"]
    character_uses = [node for node in uses if href(node) == "#char-base"]
    character_present = bool(character_uses)
    if character_present != bool(entry["character"]):
        raise RuntimeError(f"{scene_id}: presença do personagem diverge do manifesto.")
    if character_present:
        function = metadata.get("character_function")
        if function not in CHARACTER_FUNCTIONS:
            raise RuntimeError(f"{scene_id}: personagem decorativo ou sem função válida.")
        if set(symbols) != {"char-base"}:
            raise RuntimeError(f"{scene_id}: rig deve manter char-base como único symbol.")
        character = find_by_id(scene, f"char-{scene_id.lower()}")
        if character is None or character.attrib.get("data-character-function") != function:
            raise RuntimeError(f"{scene_id}: função do personagem não está materializada na instância.")
    elif symbols:
        raise RuntimeError(f"{scene_id}: symbol incorporado sem necessidade.")
    return visual_class


def validate_board() -> None:
    root = ET.parse(BOARD).getroot()
    images = [node for node in root.iter() if local_name(node.tag) == "image"]
    if len(images) != 6:
        raise RuntimeError("Board deve conter seis frames.")
    for image in images:
        if image.attrib.get("width") != "480" or image.attrib.get("height") != "270" or image.attrib.get("data-scale") != "0.25":
            raise RuntimeError("Board não preserva cada frame em escala exata de 25%.")
    if not BOARD_PNG.is_file() or BOARD_PNG.stat().st_size < 10_000:
        raise RuntimeError("Preview PNG do board ausente ou pequeno demais.")
    for scene_id in EXPECTED:
        png = SPRINT / "previews" / f"{scene_id.lower()}.png"
        if not png.is_file() or png.stat().st_size < 10_000:
            raise RuntimeError(f"Preview ausente ou inválido: {png.name}")


def main() -> int:
    validate_rig(RIG)
    config = load_json(CONFIG)
    if config.get("inherits") != "CO_VISUAL_V3" or config.get("status") != "candidate_static_sprint":
        raise RuntimeError("V4 deve permanecer uma camada candidata sobre o V3.")
    manifest = load_json(MANIFEST)
    entries = manifest.get("scenes", [])
    if tuple(entry.get("scene_id") for entry in entries) != EXPECTED:
        raise RuntimeError("Manifesto deve conter somente S001–S006 em ordem.")
    classes = {validate_scene(entry, config) for entry in entries}
    if len(classes) < 4:
        raise RuntimeError("Sprint deve exercitar ao menos quatro classes visuais.")
    validate_board()
    print(
        "ART DIRECTION V4 VÁLIDA — 6 frames, "
        f"{len(classes)} classes, ícones não dominantes e board exato a 25%."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, KeyError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
