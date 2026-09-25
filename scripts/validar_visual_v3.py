#!/usr/bin/env python3
"""Valida o piloto e os contratos estruturais do Visual System V3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from validar_rig_personagem import DEFAULT_RIG, validate_rig


ROOT = Path(__file__).resolve().parents[1]
STYLE_FILE = ROOT / "config" / "vector_style_v3.json"
SCENE_DIR = ROOT / "assets" / "scenes" / "CO-001" / "v3"
MANIFEST_FILE = SCENE_DIR / "pilot_manifest.json"
PILOT_SCENES = ("S001", "S007", "S033")
EXPECTED = {
    "S001": {"layout": "A", "accent": "lime", "character_present": True},
    "S007": {"layout": "B", "accent": "amber", "character_present": False},
    "S033": {"layout": "E", "accent": "lime", "character_present": False},
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    return next((element for element in root.iter() if element.attrib.get("id") == element_id), None)


def href(element: ET.Element) -> str:
    return element.attrib.get("href") or element.attrib.get("{http://www.w3.org/1999/xlink}href", "")


def validate_style(style: dict[str, Any]) -> None:
    canvas = style["canvas"]
    grid = style["grid"]
    if (canvas["width"], canvas["height"], canvas["format"]) != (1920, 1080, "long_form_16_9"):
        raise RuntimeError("O V3 deve permanecer em 1920x1080 long-form 16:9.")
    if canvas["safe_margin_absolute"] != 64 or canvas["safe_margin_text"] != 96:
        raise RuntimeError("Safe areas do V3 divergentes do contrato 64/96 px.")
    computed_width = (canvas["width"] - 2 * canvas["safe_margin_absolute"] - (grid["columns"] - 1) * grid["gutter"]) / grid["columns"]
    if computed_width != grid["column_width"]:
        raise RuntimeError("A largura de coluna não fecha com canvas, safe area e gutters.")
    if style["character"]["base_symbol"] != "char-base" or style["character"]["part_type"] != "group":
        raise RuntimeError("Contrato de personagem do V3 inválido.")
    if style["composition"]["character_required"]:
        raise RuntimeError("O personagem deve permanecer opcional no V3.")
    integrity = style["asset_integrity"]
    if integrity["geometry_source_of_truth"] != "assets/" or not integrity["automatic_source_copy_required"]:
        raise RuntimeError("A biblioteca assets/ deve permanecer a fonte única de geometria.")
    if integrity["path_mutation_during_embed_allowed"] or integrity["scene_local_asset_variants_allowed"]:
        raise RuntimeError("O V3 não permite mutação de path ou variantes locais de assets.")
    if style["motion"]["timing_source_of_truth"] != "narration_audio" or not style["motion"]["motion_requires_narrative_cue"]:
        raise RuntimeError("O áudio e os cues narrativos devem governar o timing do V3.")
    if not style["continuity"]["declare_between_consecutive_scenes"]:
        raise RuntimeError("A continuidade entre cenas deve ser declarada.")
    if style["lock_policy"]["current_status"] != "candidate_sequential_test_pending":
        raise RuntimeError("O V3 só pode receber lock depois da aprovação humana do teste sequencial.")


def validate_scene(scene_id: str, style: dict[str, Any]) -> dict[str, Any]:
    path = SCENE_DIR / f"{scene_id.lower()}.svg"
    try:
        root = ET.parse(path).getroot()
    except (FileNotFoundError, ET.ParseError) as exc:
        raise RuntimeError(f"Cena {scene_id} ausente ou inválida: {exc}") from exc
    if root.attrib.get("width") != "1920" or root.attrib.get("height") != "1080" or root.attrib.get("viewBox") != "0 0 1920 1080":
        raise RuntimeError(f"{scene_id}: canvas deve ser 1920x1080.")

    scene = find_by_id(root, f"scene-{scene_id}")
    if scene is None or local_name(scene.tag) != "g":
        raise RuntimeError(f"{scene_id}: a raiz da cena deve ser <g id=\"scene-{scene_id}\">.")
    if any(local_name(element.tag) == "symbol" and element.attrib.get("id") == f"scene-{scene_id}" for element in root.iter()):
        raise RuntimeError(f"{scene_id}: a cena inteira não pode virar symbol.")

    metadata_element = next((element for element in root if local_name(element.tag) == "metadata"), None)
    if metadata_element is None or not metadata_element.text:
        raise RuntimeError(f"{scene_id}: metadata ausente.")
    metadata = json.loads(metadata_element.text)
    expected = EXPECTED[scene_id]
    for key, value in expected.items():
        if metadata.get(key) != value:
            raise RuntimeError(f"{scene_id}: metadata {key} deve ser {value!r}.")
    if metadata.get("style_id") != style["style_id"]:
        raise RuntimeError(f"{scene_id}: style_id divergente.")

    uses = [href(element) for element in scene.iter() if local_name(element.tag) == "use"]
    character_instances = [value for value in uses if value == "#char-base"]
    if len(character_instances) != int(expected["character_present"]):
        raise RuntimeError(f"{scene_id}: presença do personagem diverge do plano visual.")
    defs_symbols = {element.attrib.get("id") for element in root.iter() if local_name(element.tag) == "symbol"}
    if expected["character_present"] and "char-base" not in defs_symbols:
        raise RuntimeError(f"{scene_id}: usa personagem, mas não incorpora char-base.")
    if not expected["character_present"] and "char-base" in defs_symbols:
        raise RuntimeError(f"{scene_id}: cena sem personagem não deve carregar o rig.")

    if expected["character_present"]:
        character = find_by_id(scene, f"char-{scene_id.lower()}")
        if character is None:
            raise RuntimeError(f"{scene_id}: instância identificada do personagem ausente.")
        visual_height = int(character.attrib.get("data-visual-height", "0"))
        minimum, maximum = style["character"]["protagonist_height_range"]
        if not minimum <= visual_height <= maximum:
            raise RuntimeError(f"{scene_id}: altura visual do protagonista ({visual_height}) fora de {minimum}–{maximum} px.")

    return metadata


def validate_board() -> None:
    board = SCENE_DIR / "review_v3_pilot_25.svg"
    try:
        root = ET.parse(board).getroot()
    except (FileNotFoundError, ET.ParseError) as exc:
        raise RuntimeError(f"Board V3 ausente ou inválido: {exc}") from exc
    images = [element for element in root.iter() if local_name(element.tag) == "image"]
    if len(images) != len(PILOT_SCENES):
        raise RuntimeError("O board de 25% deve conter exatamente as três cenas-piloto.")
    for image in images:
        if image.attrib.get("width") != "480" or image.attrib.get("height") != "270":
            raise RuntimeError("Cada cena no board deve medir exatamente 480x270 (25%).")


def validate_manifest() -> None:
    manifest = load_json(MANIFEST_FILE)
    if manifest.get("style_id") != "CO_VISUAL_V3":
        raise RuntimeError("Manifesto não aponta para CO_VISUAL_V3.")
    rig = manifest.get("dependencies", {}).get("character_rig", {})
    if rig.get("sha256") != hashlib.sha256(DEFAULT_RIG.read_bytes()).hexdigest():
        raise RuntimeError("Hash do rig no manifesto está desatualizado.")
    manifest_scenes = {scene["scene_id"]: scene for scene in manifest.get("scenes", [])}
    if set(manifest_scenes) != set(PILOT_SCENES):
        raise RuntimeError("Manifesto deve listar exatamente as três cenas-piloto.")
    for scene_id, expected in EXPECTED.items():
        entry = manifest_scenes[scene_id]
        for key, value in expected.items():
            if entry.get(key) != value:
                raise RuntimeError(f"Manifesto {scene_id}: {key} divergente.")
        scene_path = ROOT / entry["file"]
        if entry.get("sha256") != hashlib.sha256(scene_path.read_bytes()).hexdigest():
            raise RuntimeError(f"Manifesto {scene_id}: hash desatualizado.")


def main() -> int:
    style = load_json(STYLE_FILE)
    validate_style(style)
    validate_rig(DEFAULT_RIG)
    metadata = [validate_scene(scene_id, style) for scene_id in PILOT_SCENES]
    layouts = {item["layout"] for item in metadata}
    if len(layouts) != len(PILOT_SCENES):
        raise RuntimeError("O piloto deve exercitar três layouts distintos.")
    validate_board()
    validate_manifest()
    print("VISUAL V3 VÁLIDO — 1920x1080, rig V4 íntegro, 3 layouts e board exato a 25%.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
