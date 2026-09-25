#!/usr/bin/env python3
"""Promove somente o piloto S001-S006 para timing WordBoundary real.

O script lê os seis beats sintetizados pelo caminho oficial do Azure SDK,
resolve os anchors dos motion specs existentes e escreve um pacote paralelo.
Nenhum artefato V1, heuristico ou experimental e alterado.
"""

from __future__ import annotations

import copy
import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006_v2_wordboundary"
TIMING_FILE = PILOT_DIR / "timing" / "03A_AUDIO_TIMING_WORD_BOUNDARY.json"
MANIFEST_FILE = PILOT_DIR / "manifest" / "scene_manifest_wordboundary.json"
MOTION_SPEC_FILE = PILOT_DIR / "scenes" / "motion_spec_wordboundary.json"
PLAYER_FILE = PILOT_DIR / "player_wordboundary.html"
CONTRACT_FILE = ROOT / "config" / "motion_contract.json"
S001_S003_MOTION = ROOT / "tests" / "audiovisual_pilot_s001_s003" / "scenes" / "motion_spec.json"
S004_S006_MOTION = ROOT / "tests" / "audiovisual_pilot_s001_s006" / "scenes" / "motion_spec.json"
S001_PLAYER = ROOT / "tests" / "audiovisual_pilot_s001_s003" / "player.html"
S004_PLAYER = ROOT / "tests" / "audiovisual_pilot_s001_s006" / "player.html"

CANVAS = {"width": 1920, "height": 1080}
SAFE_AREA = {"absolute": 64, "text": 96}
TIMING_SOURCE = "WORD_BOUNDARY_REAL"

VISUAL_STATES = {
    "S001": ["R$ 3.500", "R$ 4.200", "+ R$ 700"],
    "S002": ["ESTADO ANTIGO", "BASELINE SHIFT", "NOVO NORMAL"],
    "S003": ["FOLGA", "COMPRESSAO PROGRESSIVA", "COMPRESSAO FINAL", "R$ 20"],
    "S004": ["O PROBLEMA", "NAO E", "UMA COMPRA", "ABSURDA"],
    "S005": ["TRILHOS", "REFERENCIA COMPARTILHADA", "NORMAL", "COMPARACAO", "DESPESAS", "O SISTEMA SE MOVE JUNTO"],
    "S006": ["EXTRA", "BASELINE SHIFT", "EXTRA EM SEGUNDO PLANO", "NORMAL", "BASE ESTRUTURAL", "VIROU REFERENCIA"],
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in plain if char.isalnum())


def tokens(value: str) -> list[str]:
    return [item for item in (normalize(part) for part in re.findall(r"\S+", value)) if item]


def source_events() -> list[tuple[dict[str, Any], int]]:
    first = load_json(S001_S003_MOTION)
    second = load_json(S004_S006_MOTION)
    # B001-B003 contain 37 boundary words in the official V2 script.
    return [
        (event, 0)
        for scene in first["scenes"]
        for event in scene.get("events", [])
    ] + [
        (event, 37)
        for scene in second["scenes"]
        for event in scene.get("events", [])
    ]


def beat_words(timing: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[int, tuple[str, dict[str, Any]]]]:
    by_id: dict[str, dict[str, Any]] = {}
    by_global: dict[int, tuple[str, dict[str, Any]]] = {}
    global_index = 1
    for beat in timing["beats"]:
        beat_copy = beat
        by_id[beat["beat_id"]] = beat_copy
        for word in beat["words"]:
            word["global_index"] = global_index
            by_global[global_index] = (beat["beat_id"], word)
            global_index += 1
    return by_id, by_global


def find_anchor(
    phrase: str,
    words: list[dict[str, Any]],
    *,
    beat_id: str,
    source_index: int | None = None,
) -> dict[str, Any]:
    wanted = tokens(phrase)
    normalized = [word.get("normalized") or normalize(word["text"]) for word in words]
    matches = []
    for index in range(len(normalized) - len(wanted) + 1):
        if normalized[index : index + len(wanted)] == wanted:
            matches.append((words[index], words[index + len(wanted) - 1]))
    if not matches:
        raise RuntimeError(
            f"ANCHOR_MISSING: '{phrase}' em {beat_id}" +
            (f" (source_index={source_index})" if source_index is not None else "")
        )
    if len(matches) > 1:
        raise RuntimeError(f"ANCHOR_AMBIGUOUS: '{phrase}' em {beat_id}")
    first, last = matches[0]
    return {
        "text": phrase,
        "beat_id": beat_id,
        "word_event": f"{beat_id}:word_{first['index']}",
        "audio_offset_ms": first["absolute_audio_offset_ms"],
        "duration_ms": round(
            (last["absolute_audio_offset_ms"] + (last.get("duration_ms") or 0))
            - first["absolute_audio_offset_ms"],
            3,
        ),
        "boundary_type": first["boundary_type"],
        "text_offset": first["text_offset"],
        "word_length": first["word_length"],
        "start_word_index": first["global_index"],
        "end_word_index": last["global_index"],
        "resolution_method": TIMING_SOURCE,
    }


def resolve_source_anchor(
    anchor: dict[str, Any],
    *,
    offset: int,
    by_global: dict[int, tuple[str, dict[str, Any]]],
    by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_index = int(anchor["start_word_index"]) + offset
    try:
        beat_id, _word = by_global[source_index]
    except KeyError as exc:
        raise RuntimeError(f"ANCHOR_MISSING: source word index {source_index}") from exc
    resolved = find_anchor(anchor["text"], by_id[beat_id]["words"], beat_id=beat_id, source_index=source_index)
    return resolved


def resolve_subbeat_anchor(
    phrase: str,
    *,
    by_id: dict[str, dict[str, Any]],
    preferred_beats: list[str],
) -> dict[str, Any]:
    matches = []
    for beat_id in preferred_beats:
        try:
            matches.append(find_anchor(phrase, by_id[beat_id]["words"], beat_id=beat_id))
        except RuntimeError as exc:
            if str(exc).startswith("ANCHOR_AMBIGUOUS"):
                raise
    if not matches:
        raise RuntimeError(f"ANCHOR_MISSING: '{phrase}' em beats {preferred_beats}")
    if len(matches) > 1:
        raise RuntimeError(f"ANCHOR_AMBIGUOUS: '{phrase}' em beats {preferred_beats}")
    return matches[0]


def event_index(timing: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_id, by_global = beat_words(timing)
    result: dict[str, dict[str, Any]] = {}
    for event, offset in source_events():
        anchor = resolve_source_anchor(event["anchor"], offset=offset, by_global=by_global, by_id=by_id)
        item = copy.deepcopy(event)
        item["anchor"] = anchor
        if event.get("end_anchor"):
            item["end_anchor"] = resolve_source_anchor(
                event["end_anchor"], offset=offset, by_global=by_global, by_id=by_id
            )
        start = anchor["audio_offset_ms"] / 1000.0
        original_duration = max(0.05, float(event.get("end_time", event["time"])) - float(event["time"]))
        end = start + original_duration
        if item.get("end_anchor"):
            end = max(end, item["end_anchor"]["audio_offset_ms"] / 1000.0 + item["end_anchor"]["duration_ms"] / 1000.0)
        item["time"] = round(start, 4)
        item["end_time"] = round(end, 4)
        item["duration"] = round(end - start, 4)
        item["timing_source"] = TIMING_SOURCE
        result[item["event_id"]] = item
    return result


def player_html() -> str:
    first = S001_PLAYER.read_text(encoding="utf-8-sig")
    second = S004_PLAYER.read_text(encoding="utf-8-sig")
    first_draws = first.split("function drawS001", 1)[1].split("function renderFrame", 1)[0]
    second_prefix = second.split("function drawS004", 1)[0]
    second_prefix += "\n    function formatMoney(value) { return Math.round(value).toLocaleString('pt-BR'); }\n"
    second_prefix += """\n    function dashedLine(x1, y, x2, color, width, alpha = 1) {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      ctx.lineCap = 'round';
      ctx.setLineDash([18, 14]);
      ctx.beginPath();
      ctx.moveTo(x1, y);
      ctx.lineTo(x2, y);
      ctx.stroke();
      ctx.restore();
    }
"""
    second_draws = second.split("function drawS004", 1)[1].split("function renderFrame", 1)[0]
    runtime = second.split("function renderFrame", 1)[1]
    runtime = "function renderFrame" + runtime
    runtime = runtime.replace(
        "if (scene.scene_id === 'S004') drawS004(scene, time);\n      else if (scene.scene_id === 'S005') drawS005(scene, time);\n      else drawS006(scene, time);",
        "if (scene.scene_id === 'S001') drawS001(scene, time);\n      else if (scene.scene_id === 'S002') drawS002(scene, time);\n      else if (scene.scene_id === 'S003') drawS003(scene, time);\n      else if (scene.scene_id === 'S004') drawS004(scene, time);\n      else if (scene.scene_id === 'S005') drawS005(scene, time);\n      else drawS006(scene, time);",
    )
    runtime = runtime.replace("manifest/scene_manifest.json", "manifest/scene_manifest_wordboundary.json")
    html = second_prefix + "function drawS001" + first_draws + "function drawS004" + second_draws + runtime
    html = html.replace("piloto audiovisual S004–S006", "piloto audiovisual S001–S006 V2 WordBoundary")
    html = html.replace("carregando piloto S004–S006…", "carregando piloto S001–S006 V2 WordBoundary…")
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Atualiza somente os artefatos oficiais deste pacote paralelo.")
    args = parser.parse_args()
    if not TIMING_FILE.is_file():
        raise RuntimeError(f"Timing oficial ausente: {TIMING_FILE}")
    timing = load_json(TIMING_FILE)
    contract = load_json(CONTRACT_FILE)
    if timing.get("timing_quality") != TIMING_SOURCE:
        raise RuntimeError("Timing nao possui qualidade WORD_BOUNDARY_REAL.")
    by_id, _by_global = beat_words(timing)
    events = event_index(timing)
    b004_start = next(row for row in timing["beats"] if row["beat_id"] == "B004")["composition_start_ms"] / 1000.0
    b005_start = next(row for row in timing["beats"] if row["beat_id"] == "B005")["composition_start_ms"] / 1000.0
    b006_start = next(row for row in timing["beats"] if row["beat_id"] == "B006")["composition_start_ms"] / 1000.0
    total_duration = timing["audio_duration_ms"] / 1000.0
    s003_start = events["S003-E01"]["time"]
    scene_boundaries = {
        "S001": (0.0, next(row for row in timing["beats"] if row["beat_id"] == "B002")["composition_start_ms"] / 1000.0),
        "S002": (next(row for row in timing["beats"] if row["beat_id"] == "B002")["composition_start_ms"] / 1000.0, s003_start),
        "S003": (s003_start, b004_start),
        "S004": (b004_start, b005_start),
        "S005": (b005_start, b006_start),
        "S006": (b006_start, total_duration),
    }
    from gerar_piloto_audiovisual_v2 import SCENE_DEFINITIONS

    scenes = []
    anchors_index = []
    for definition in SCENE_DEFINITIONS:
        sdef = copy.deepcopy(definition)
        if sdef["scene_id"] == "S003":
            sdef["beat_ids"] = ["B002", "B003"]
            sdef["subbeats"][0]["anchor"] = "vinte reais"
            sdef["subbeats"][0]["label"] = "r20_estabiliza"
            sdef["subbeats"][0]["narrative_function"] = "assentar R$ 20 como consequencia visivel antes da compressao final"
        scene_id = sdef["scene_id"]
        scene_start, scene_end = scene_boundaries[scene_id]
        subbeats = []
        for subbeat in sdef["subbeats"]:
            anchor = resolve_subbeat_anchor(
                subbeat["anchor"], by_id=by_id, preferred_beats=sdef["beat_ids"]
            )
            time = anchor["audio_offset_ms"] / 1000.0 + float(subbeat.get("offset_ms", 0)) / 1000.0
            if not scene_start - 0.001 <= time <= scene_end + 0.001:
                raise RuntimeError(f"Sub-beat fora da cena: {subbeat['subbeat_id']}")
            subbeats.append(
                {
                    "subbeat_id": subbeat["subbeat_id"],
                    "label": subbeat["label"],
                    "time": round(time, 4),
                    "anchor_text": subbeat["anchor"],
                    "anchor": anchor,
                    "narrative_function": subbeat["narrative_function"],
                    "visual_state": VISUAL_STATES[scene_id][len(subbeats)],
                    "timing_source": TIMING_SOURCE,
                }
            )
            anchors_index.append({"scene_id": scene_id, "subbeat_id": subbeat["subbeat_id"], **anchor})
        subbeats.sort(key=lambda row: row["time"])
        holds = [subbeats[i + 1]["time"] - subbeats[i]["time"] for i in range(len(subbeats) - 1)]
        holds.append(scene_end - subbeats[-1]["time"])
        scene_events = [event for event_id, event in events.items() if event_id.startswith(scene_id + "-")]
        for event in scene_events:
            anchors_index.append({"scene_id": scene_id, "event_id": event["event_id"], **event["anchor"]})
            if event.get("end_anchor"):
                anchors_index.append({"scene_id": scene_id, "event_id": event["event_id"] + ":end", **event["end_anchor"]})
        scene = {
            "scene_id": scene_id,
            "beat_ids": sdef["beat_ids"],
            "start": round(scene_start, 4),
            "end": round(scene_end, 4),
            "duration": round(scene_end - scene_start, 4),
            "composition": sdef["composition"],
            "variant": {
                "id": sdef["variant"],
                "version": sdef["version"],
                "status": sdef["status"],
                "motion_status": sdef["motion_status"],
                "protect_primary_type": scene_id == "S006",
            },
            "first_useful_state_time": round(scene_start + 0.25, 4),
            "visual_subbeats": subbeats,
            "events": scene_events,
            "max_static_hold_seconds": round(max(holds), 3),
            "timing_source": TIMING_SOURCE,
        }
        scenes.append(scene)
    if len(anchors_index) == 0:
        raise RuntimeError("Nenhum anchor resolvido.")
    composition_id = timing["synthesis_id"]
    manifest = {
        "schema_version": "3.0",
        "pilot_id": "capital_oculto_pilot_s001_s006_v2_wordboundary",
        "status": "PILOT_V2_WORDBOUNDARY_REAL",
        "selection_mode": "PILOT_V2_CONTINUITY",
        "production_allowed": False,
        "episode_id": "CO-001",
        "canvas": CANVAS,
        "safe_area": SAFE_AREA,
        "motion_contract": "CO_MOTION_CONTRACT_V1",
        "protect_primary_type": True,
        "composition_id": composition_id,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "audio": {
            "file": timing["audio_file"],
            "player_path": "audio/narration_wordboundary.wav",
            "provider": timing["provider"],
            "voice": timing["voice"],
            "rate": timing["rate"],
            "pitch": timing["pitch"],
            "synthesis_id": timing["synthesis_id"],
            "duration_seconds": timing["audio_duration_seconds"],
            "render_origin_seconds": 0.0,
            "speech_overlap": timing["speech_overlap"],
            "voice_density_warnings": timing["voice_density_warnings"],
            "timing_quality": TIMING_SOURCE,
        },
        "anchor_index": anchors_index,
        "scenes": scenes,
    }
    motion_spec = {
        "schema_version": "3.0",
        "pilot_id": manifest["pilot_id"],
        "pacing_contract": contract,
        "timing_quality": TIMING_SOURCE,
        "anchor_resolution": {
            "resolution_method": TIMING_SOURCE,
            "anchors_resolved": len(anchors_index),
            "anchors_ambiguous": 0,
            "anchors_missing": 0,
        },
        "scenes": scenes,
    }
    for path, payload in ((MANIFEST_FILE, manifest), (MOTION_SPEC_FILE, motion_spec)):
        if path.exists() and not args.refresh:
            raise RuntimeError(f"Artefato audiovisual oficial ja existe: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if PLAYER_FILE.exists() and not args.refresh:
        raise RuntimeError(f"Player oficial ja existe: {PLAYER_FILE}")
    PLAYER_FILE.parent.mkdir(parents=True, exist_ok=True)
    PLAYER_FILE.write_text(player_html(), encoding="utf-8")
    print(f"MANIFEST={MANIFEST_FILE.relative_to(ROOT)}")
    print(f"MOTION_SPEC={MOTION_SPEC_FILE.relative_to(ROOT)}")
    print(f"PLAYER={PLAYER_FILE.relative_to(ROOT)}")
    print(f"ANCHORS_RESOLVED={len(anchors_index)}")
    print(f"TIMING_SOURCE={TIMING_SOURCE}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(2)
