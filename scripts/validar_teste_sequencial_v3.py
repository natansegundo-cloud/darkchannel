#!/usr/bin/env python3
"""Valida assets, timing, continuidade e artefatos do teste sequencial V3."""

from __future__ import annotations

import hashlib
import json
import wave
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from validar_rig_personagem import EXPECTED_GROUPS, validate_rig


ROOT = Path(__file__).resolve().parents[1]
STYLE_FILE = ROOT / "config" / "vector_style_v3.json"
TEST_DIR = ROOT / "episodios" / "CO-001-por-que-ganhar-mais-nao-basta" / "testes" / "v3_sequencial_s001_s006"
EPISODE_DIR = TEST_DIR.parents[1]
SCENE_DIR = TEST_DIR / "scenes"
TIMELINE_FILE = TEST_DIR / "timeline.json"
MANIFEST_FILE = TEST_DIR / "scene_manifest.json"
TIMING_FILE = EPISODE_DIR / "03A_AUDIO_TIMING.json"
RESOLVED_FILE = EPISODE_DIR / "04A_SCENE_MANIFEST.json"
VIDEO_FILE = TEST_DIR / "teste_sequencial_v3_s001_s006_pipeline.webm"
EXPECTED_SCENES = ("S001", "S002", "S003", "S004", "S005", "S006")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def find_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    return next((element for element in root.iter() if element.attrib.get("id") == element_id), None)


def signature(element: ET.Element) -> tuple[Any, ...]:
    attributes = tuple(sorted((local_name(key), value) for key, value in element.attrib.items()))
    children = tuple(signature(child) for child in list(element))
    text = (element.text or "").strip()
    return local_name(element.tag), attributes, text, children


def path_signatures(element: ET.Element) -> list[tuple[tuple[str, str], ...]]:
    return [tuple(sorted((local_name(key), value) for key, value in child.attrib.items())) for child in element.iter() if local_name(child.tag) == "path"]


def validate_embedded_source(scene_root: ET.Element, source_path: Path) -> None:
    source_root = ET.parse(source_path).getroot()
    relative = source_path.relative_to(ROOT).as_posix()
    if source_path == ROOT / "assets" / "characters" / "capital_oculto_character_rig_v4.svg":
        for element_id in (*EXPECTED_GROUPS, "char-base"):
            source_element = find_by_id(source_root, element_id)
            scene_element = find_by_id(scene_root, element_id)
            if source_element is None or scene_element is None or signature(source_element) != signature(scene_element):
                raise RuntimeError(f"Geometria do rig alterada durante incorporação: {relative}#{element_id}")
        return
    if "/icons/phosphor/" in f"/{relative}":
        symbol = find_by_id(scene_root, f"icon-{source_path.stem}")
        if symbol is None or path_signatures(source_root) != path_signatures(symbol):
            raise RuntimeError(f"Paths do ícone foram alterados durante incorporação: {relative}")
        return
    source_symbols = [element for element in source_root.iter() if local_name(element.tag) == "symbol"]
    if not source_symbols:
        raise RuntimeError(f"Asset reutilizável sem symbol: {relative}")
    for source_symbol in source_symbols:
        element_id = source_symbol.attrib.get("id", "")
        scene_symbol = find_by_id(scene_root, element_id)
        if scene_symbol is None or signature(source_symbol) != signature(scene_symbol):
            raise RuntimeError(f"Asset alterado durante incorporação: {relative}#{element_id}")


def validate_scene(scene_id: str, manifest_entry: dict[str, Any], style: dict[str, Any]) -> None:
    path = ROOT / manifest_entry["file"]
    root = ET.parse(path).getroot()
    if root.attrib.get("viewBox") != "0 0 1920 1080":
        raise RuntimeError(f"{scene_id}: canvas inválido.")
    scene_group = find_by_id(root, f"scene-{scene_id}")
    if scene_group is None or local_name(scene_group.tag) != "g":
        raise RuntimeError(f"{scene_id}: raiz deve permanecer um group.")
    metadata_element = next((child for child in root if local_name(child.tag) == "metadata"), None)
    if metadata_element is None or not metadata_element.text:
        raise RuntimeError(f"{scene_id}: metadata ausente.")
    metadata = json.loads(metadata_element.text)
    if metadata.get("style_id") != style["style_id"] or metadata.get("continuity") != manifest_entry.get("continuity"):
        raise RuntimeError(f"{scene_id}: metadata visual divergente do manifesto.")
    sources = [ROOT / value for value in metadata.get("asset_sources", [])]
    source_hashes = metadata.get("asset_source_hashes", {})
    for source in sources:
        relative = source.relative_to(ROOT).as_posix()
        if source_hashes.get(relative) != hashlib.sha256(source.read_bytes()).hexdigest():
            raise RuntimeError(f"{scene_id}: hash de fonte desatualizado para {relative}.")
        validate_embedded_source(root, source)
    symbols = {element.attrib.get("id") for element in root.iter() if local_name(element.tag) == "symbol"}
    if bool(manifest_entry["character"]) != ("char-base" in symbols):
        raise RuntimeError(f"{scene_id}: incorporação do rig não corresponde à presença do personagem.")
    if manifest_entry["character"]:
        character = find_by_id(scene_group, f"char-{scene_id.lower()}")
        if character is None:
            raise RuntimeError(f"{scene_id}: instância do personagem ausente.")
        visual_height = int(character.attrib.get("data-visual-height", "0"))
        minimum, maximum = style["character"]["protagonist_height_range"]
        if not minimum <= visual_height <= maximum:
            raise RuntimeError(f"{scene_id}: personagem fora da escala protagonista.")
    if manifest_entry.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
        raise RuntimeError(f"{scene_id}: hash da cena desatualizado no manifesto.")


def validate_timeline(timeline: dict[str, Any], resolved: dict[str, Any]) -> None:
    if timeline.get("source") != "04A_SCENE_MANIFEST.json":
        raise RuntimeError("Timeline de reprodução não foi derivada do 04A.")
    scenes = timeline.get("scenes", [])
    if tuple(scene.get("scene_id") for scene in scenes) != EXPECTED_SCENES:
        raise RuntimeError("Timeline deve conter S001–S006 em ordem e sem lacunas.")
    resolved_scenes = resolved.get("scenes", [])
    if len(resolved_scenes) != len(scenes):
        raise RuntimeError("Timeline e 04A possuem quantidades de cenas diferentes.")
    previous_end = 0.0
    for scene, source_scene in zip(scenes, resolved_scenes):
        start = float(scene["start"])
        end = float(scene["end"])
        if scene["scene_id"] == "S001":
            previous_end = start
        if abs(start - previous_end) > .001 or end <= start:
            raise RuntimeError(f"Timeline descontínua em {scene['scene_id']}.")
        if abs(start - float(source_scene["start"])) > .0001 or abs(end - float(source_scene["end"])) > .0001:
            raise RuntimeError(f"{scene['scene_id']}: tempos divergem do 04A.")
        if not scene.get("cue") or not scene.get("dominant_motion"):
            raise RuntimeError(f"{scene['scene_id']}: cue narrativo ou movimento dominante ausente.")
        if scene["scene_id"] != "S001" and not scene.get("continuity_in"):
            raise RuntimeError(f"{scene['scene_id']}: continuidade de entrada não declarada.")
        if scene["scene_id"] != "S006" and not scene.get("continuity_out"):
            raise RuntimeError(f"{scene['scene_id']}: continuidade de saída não declarada.")
        previous_end = end
    duration = float(timeline["duration_seconds"])
    if abs(previous_end - duration) > .001 or not 20 <= duration <= 55:
        raise RuntimeError("Teste deve durar 20–40 s; até 55 s é tolerado somente pelo áudio real dos beats aprovados.")


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as audio:
        return audio.getnframes() / audio.getframerate()


def main() -> int:
    style = load_json(STYLE_FILE)
    if style["lock_policy"]["current_status"] != "candidate_sequential_test_pending":
        raise RuntimeError("O V3 não pode ser bloqueado antes da aprovação humana do teste.")
    validate_rig()
    manifest = load_json(MANIFEST_FILE)
    entries = {entry["scene_id"]: entry for entry in manifest.get("scenes", [])}
    if tuple(entries) != EXPECTED_SCENES:
        raise RuntimeError("Manifesto deve listar exatamente S001–S006 em ordem.")
    for scene_id in EXPECTED_SCENES:
        validate_scene(scene_id, entries[scene_id], style)
    timing = load_json(TIMING_FILE)
    if timing.get("provider") != "kokoro_onnx":
        raise RuntimeError("Esta etapa deve permanecer no provider Kokoro ONNX.")
    if timing.get("timing_method") != "kokoro_create_timed_duration_output":
        raise RuntimeError("03A não foi produzido por create_timed().")
    if tuple(beat.get("beat_id") for beat in timing.get("beats", [])) != tuple(f"B{i:03d}" for i in range(1, 7)):
        raise RuntimeError("03A deve conter exatamente B001–B006 nesta prova.")
    timing_audio = ROOT / timing["audio_file"]
    if timing.get("audio_sha256") != hashlib.sha256(timing_audio.read_bytes()).hexdigest():
        raise RuntimeError("Hash do WAV diverge do 03A.")
    resolved = load_json(RESOLVED_FILE)
    if resolved.get("scope") != "pilot_s001_s006":
        raise RuntimeError("04A não está limitado ao piloto S001–S006.")
    if resolved.get("audio", {}).get("sha256") != timing.get("audio_sha256"):
        raise RuntimeError("04A não referencia o mesmo áudio do 03A.")
    for source in resolved.get("sources", {}).values():
        source_path = ROOT / source["file"]
        if source.get("sha256") != hashlib.sha256(source_path.read_bytes()).hexdigest():
            raise RuntimeError(f"Fonte do 04A foi alterada depois da resolução: {source_path.name}")
    timeline = load_json(TIMELINE_FILE)
    validate_timeline(timeline, resolved)
    audio_file = ROOT / resolved["audio"]["file"]
    duration = wav_duration(audio_file)
    if abs(duration - float(timeline["duration_seconds"])) > .1:
        raise RuntimeError("Duração do WAV diverge da timeline.")
    if not VIDEO_FILE.is_file() or VIDEO_FILE.stat().st_size < 100_000:
        raise RuntimeError("Vídeo WebM ausente ou pequeno demais.")
    video_data = VIDEO_FILE.read_bytes()
    if video_data[:4] != bytes.fromhex("1A45DFA3"):
        raise RuntimeError("Arquivo de vídeo não possui cabeçalho WebM/EBML válido.")
    if b"A_OPUS" not in video_data:
        raise RuntimeError("Faixa de áudio Opus ausente no WebM.")
    if not any(codec in video_data for codec in (b"V_VP9", b"V_VP8")):
        raise RuntimeError("Faixa de vídeo VP8/VP9 ausente no WebM.")
    print(f"TESTE V3 VÁLIDO — 6 cenas, {duration:.1f}s, assets íntegros, cues e continuidade declarados.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, ValueError, json.JSONDecodeError, ET.ParseError, wave.Error) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
