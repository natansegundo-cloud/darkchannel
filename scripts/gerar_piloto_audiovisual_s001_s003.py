#!/usr/bin/env python3
"""Resolve o manifesto e prepara o player do piloto audiovisual S001–S003."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s003"
TIMING_FILE = PILOT_DIR / "timing" / "03A_AUDIO_TIMING.json"
MANIFEST_FILE = PILOT_DIR / "manifest" / "scene_manifest.json"
MOTION_SPEC_FILE = PILOT_DIR / "scenes" / "motion_spec.json"
PLAYER_FILE = PILOT_DIR / "player.html"
PLAYER_TEMPLATE = ROOT / "scripts" / "templates" / "audiovisual_pilot_s001_s003_player.html"
COMPOSITIONS_FILE = ROOT / "config" / "visual_compositions.json"
SOURCE_DIR = ROOT / "tests" / "editorial_compositions_v1" / "s001_s003"
SAFE_AREA = 64
TEXT_SAFE_AREA = 96
CANVAS = {"width": 1920, "height": 1080}


SCENE_PLANS: list[dict[str, Any]] = [
    {
        "scene_id": "S001",
        "beat_ids": ["B001"],
        "composition": "DATA_HERO",
        "variant": "CO-COMP-01C",
        "version": 1.1,
        "focus_mode": None,
        "anchor_start": "Você recebe a mensagem",
        "anchor_end": "salário aumentou",
        "anchors": {
            "scene_entry": "Você recebe a mensagem",
            "counter_start": "seu salário",
            "counter_settle": "aumentou",
        },
        "events": [
            {
                "event_id": "S001-E01",
                "anchor": "Você recebe a mensagem",
                "anchor_edge": "start",
                "duration": 0.32,
                "target": "salary_initial",
                "action": "reveal",
                "narrative_function": "estabelecer R$ 3.500 como estado inicial",
            },
            {
                "event_id": "S001-E02",
                "anchor": "seu salário",
                "end_anchor": "aumentou",
                "anchor_edge": "start",
                "target": "salary_value",
                "action": "counter",
                "narrative_function": "materializar o aumento de 3.500 para 4.200",
            },
            {
                "event_id": "S001-E03",
                "anchor": "aumentou",
                "anchor_edge": "start",
                "duration": 0.28,
                "target": "salary_delta",
                "action": "reveal_and_settle",
                "narrative_function": "assentar o valor final e revelar + R$ 700",
            },
        ],
        "continuity_in": None,
        "continuity_out": "R$ 4.200 persiste e reduz de escala para o estado atual de S002",
        "dominant_motion": "salary_counter",
    },
    {
        "scene_id": "S002",
        "beat_ids": ["B002"],
        "composition": "MOVING_BASELINE",
        "variant": "CO-COMP-04A",
        "version": 1.1,
        "focus_mode": None,
        "anchor_start": "Por algumas semanas",
        "anchor_end": "antes de gastar",
        "anchors": {
            "old_state": "Por algumas semanas",
            "current_state": "finalmente sobra",
            "baseline_shift": "Três meses depois",
            "old_deemphasis": "você está outra vez",
            "new_normal": "conferindo o saldo",
        },
        "events": [
            {
                "event_id": "S002-E01",
                "anchor": "Por algumas semanas",
                "anchor_edge": "start",
                "duration": 0.34,
                "target": "old_state_and_baseline",
                "action": "reveal",
                "narrative_function": "estabelecer a referência antiga de R$ 3.500",
            },
            {
                "event_id": "S002-E02",
                "anchor": "finalmente sobra",
                "anchor_edge": "start",
                "duration": 0.34,
                "target": "current_state",
                "action": "reveal",
                "narrative_function": "preservar R$ 4.200 como estado atual",
            },
            {
                "event_id": "S002-E03",
                "anchor": "Três meses depois",
                "end_anchor": "você está outra vez",
                "anchor_edge": "start",
                "target": "baseline",
                "action": "translate_up",
                "narrative_function": "mover fisicamente a referência para o novo patamar",
            },
            {
                "event_id": "S002-E04",
                "anchor": "você está outra vez",
                "anchor_edge": "start",
                "duration": 0.42,
                "target": "old_state",
                "action": "deemphasize",
                "narrative_function": "reduzir a presença da referência antiga",
            },
            {
                "event_id": "S002-E05",
                "anchor": "conferindo o saldo",
                "anchor_edge": "start",
                "duration": 0.35,
                "target": "new_normal_label",
                "action": "reveal",
                "narrative_function": "estabilizar R$ 4.200 como novo normal",
            },
        ],
        "continuity_in": "R$ 4.200 vem da escala dominante de S001",
        "continuity_out": "Renda R$ 4.200 persiste como contexto inferior de S003",
        "dominant_motion": "baseline_translation",
    },
    {
        "scene_id": "S003",
        "beat_ids": ["B002", "B003"],
        "composition": "SHRINKING_SPACE",
        "variant": "CO-COMP-03A",
        "version": 1.1,
        "focus_mode": "COMPRESSION_FIRST",
        "anchor_start": "vinte reais",
        "anchor_end": "folga sumiu",
        "anchors": {
            "scene_entry": "vinte reais",
            "compression_start": "O aumento era real",
            "right_pressure": "Então por que",
            "compression_end": "folga sumiu",
        },
        "events": [
            {
                "event_id": "S003-E01",
                "anchor": "vinte reais",
                "anchor_edge": "start",
                "duration": 0.36,
                "target": "wide_gap",
                "action": "establish",
                "narrative_function": "mostrar folga inicial antes da compressão",
            },
            {
                "event_id": "S003-E02",
                "anchor": "O aumento era real",
                "end_anchor": "Então por que",
                "anchor_edge": "start",
                "target": "left_mass",
                "action": "advance",
                "narrative_function": "iniciar a perda de espaço por gastos fixos",
            },
            {
                "event_id": "S003-E03",
                "anchor": "Então por que",
                "end_anchor": "folga sumiu",
                "anchor_edge": "start",
                "target": "right_mass",
                "action": "advance",
                "narrative_function": "completar a compressão com gastos novos",
            },
            {
                "event_id": "S003-E04",
                "anchor": "folga sumiu",
                "anchor_edge": "start",
                "duration": 0.32,
                "target": "remaining_value",
                "action": "settle",
                "narrative_function": "assentar R$ 20 como consequência",
            },
        ],
        "continuity_in": "Renda R$ 4.200 desce para o contexto enquanto a distribuição ocupa o quadro",
        "continuity_out": "R$ 20 permanece estável no encerramento do piloto",
        "dominant_motion": "gap_compression",
    },
]


class PilotError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise PilotError(f"Arquivo ausente: {path}") from exc


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in plain if char.isalnum())


def parse_anchor(value: str) -> list[str]:
    tokens = [normalize(token) for token in re.findall(r"\S+", value)]
    tokens = [token for token in tokens if token]
    if not tokens:
        raise PilotError(f"Anchor inválido: {value!r}")
    return tokens


def words_for_beats(timing: dict[str, Any], beat_ids: list[str]) -> list[dict[str, Any]]:
    mapping = {beat["beat_id"]: beat for beat in timing.get("beats", [])}
    missing = [beat_id for beat_id in beat_ids if beat_id not in mapping]
    if missing:
        raise PilotError(f"Beat(s) ausente(s) no timing: {', '.join(missing)}")
    return [word for beat_id in beat_ids for word in mapping[beat_id]["words"]]


def resolve_anchor(value: str, beat_ids: list[str], timing: dict[str, Any]) -> dict[str, Any]:
    tokens = parse_anchor(value)
    words = words_for_beats(timing, beat_ids)
    normalized = [word.get("normalized") or normalize(word["text"]) for word in words]
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index in range(0, len(words) - len(tokens) + 1):
        if normalized[index : index + len(tokens)] == tokens:
            matches.append((words[index], words[index + len(tokens) - 1]))
    if not matches:
        raise PilotError(f"Anchor não encontrado: '{value}' em {','.join(beat_ids)}")
    if len(matches) > 1:
        raise PilotError(f"Anchor ambíguo: '{value}' tem {len(matches)} ocorrências")
    first, last = matches[0]
    return {
        "text": value,
        "start": float(first["start"]),
        "end": float(last["end"]),
        "start_word_index": int(first["index"]),
        "end_word_index": int(last["index"]),
    }


def composition_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in config.get("compositions", [])}


def validate_strict_zones(composition: dict[str, Any]) -> None:
    for zone in composition.get("content_zones", []):
        if zone.get("safe_area_policy") != "STRICT":
            continue
        x = float(zone["x"])
        y = float(zone["y"])
        width = float(zone["width"])
        height = float(zone["height"])
        if x < TEXT_SAFE_AREA or y < TEXT_SAFE_AREA:
            raise PilotError(f"{composition['id']}/{zone['id']}: zona STRICT invade safe area.")
        if x + width > CANVAS["width"] - TEXT_SAFE_AREA:
            raise PilotError(f"{composition['id']}/{zone['id']}: zona STRICT excede largura segura.")
        if y + height > CANVAS["height"] - TEXT_SAFE_AREA:
            raise PilotError(f"{composition['id']}/{zone['id']}: zona STRICT excede altura segura.")


def read_svg_metadata(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    metadata = root.find("{http://www.w3.org/2000/svg}metadata")
    if metadata is None or not metadata.text:
        raise PilotError(f"Metadata ausente no master de cena: {path.name}")
    return json.loads(metadata.text)


def event_with_time(
    event: dict[str, Any],
    *,
    beat_ids: list[str],
    timing: dict[str, Any],
    scene_start: float,
    scene_end: float,
) -> dict[str, Any]:
    anchor = resolve_anchor(event["anchor"], beat_ids, timing)
    edge = event.get("anchor_edge", "start")
    start = anchor[edge]
    end_anchor = None
    if event.get("end_anchor"):
        end_anchor = resolve_anchor(event["end_anchor"], beat_ids, timing)
        end = end_anchor["start"]
    else:
        end = start + float(event.get("duration", 0.3))
    start = max(scene_start, min(scene_end, start))
    end = max(start + 0.001, min(scene_end, end))
    resolved = dict(event)
    resolved["anchor"] = anchor
    if end_anchor:
        resolved["end_anchor"] = end_anchor
    resolved["time"] = round(start, 4)
    resolved["end_time"] = round(end, 4)
    resolved["duration"] = round(end - start, 4)
    resolved.pop("anchor_edge", None)
    return resolved


def main() -> int:
    timing = load_json(TIMING_FILE)
    if timing.get("provider") != "azure_speech_rest":
        raise PilotError("O piloto exige timing produzido pelo provider Azure REST.")
    if [beat.get("beat_id") for beat in timing.get("beats", [])] != ["B001", "B002", "B003"]:
        raise PilotError("O timing experimental deve conter somente B001–B003.")
    audio_path = ROOT / timing["audio_file"]
    if not audio_path.is_file() or sha256(audio_path) != timing.get("audio_sha256"):
        raise PilotError("WAV processado ausente ou divergente do timing.")

    config = load_json(COMPOSITIONS_FILE)
    compositions = composition_map(config)
    beat_map = {beat["beat_id"]: beat for beat in timing["beats"]}
    source_paths = {
        "S001": SOURCE_DIR / "s001.svg",
        "S002": SOURCE_DIR / "s002.svg",
        "S003": SOURCE_DIR / "s003.svg",
    }
    for directory in (
        PILOT_DIR / "audio" / "raw",
        PILOT_DIR / "audio" / "processed",
        PILOT_DIR / "timing",
        PILOT_DIR / "scenes",
        PILOT_DIR / "manifest",
        PILOT_DIR / "renders",
        PILOT_DIR / "logs",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    scenes: list[dict[str, Any]] = []
    for index, plan in enumerate(SCENE_PLANS):
        composition = compositions.get(plan["variant"])
        if not composition:
            raise PilotError(f"Variante ausente: {plan['variant']}")
        if composition.get("status") != "APPROVED":
            raise PilotError(f"{plan['variant']}: status de produção não é APPROVED.")
        if composition.get("motion_status") != "MOTION_APPROVED":
            raise PilotError(f"{plan['variant']}: motion_status não é MOTION_APPROVED.")
        if float(composition.get("version")) != plan["version"]:
            raise PilotError(f"{plan['variant']}: versão divergente.")
        if plan["focus_mode"] and composition.get("focus_mode_default") != plan["focus_mode"]:
            raise PilotError(f"{plan['variant']}: focus_mode divergente.")
        validate_strict_zones(composition)

        source_path = source_paths[plan["scene_id"]]
        metadata = read_svg_metadata(source_path)
        if metadata.get("composition_id") != plan["variant"]:
            raise PilotError(f"{plan['scene_id']}: SVG fonte usa variante incorreta.")
        if float(metadata.get("composition_version")) != plan["version"]:
            raise PilotError(f"{plan['scene_id']}: SVG fonte usa versão incorreta.")
        if plan["focus_mode"] and metadata.get("focus_mode") != plan["focus_mode"]:
            raise PilotError(f"{plan['scene_id']}: SVG fonte usa focus_mode incorreto.")

        resolved_anchors = {
            name: resolve_anchor(text, plan["beat_ids"], timing)
            for name, text in plan["anchors"].items()
        }
        anchor_start = resolve_anchor(plan["anchor_start"], plan["beat_ids"], timing)
        anchor_end = resolve_anchor(plan["anchor_end"], plan["beat_ids"], timing)
        if plan["scene_id"] == "S001":
            start = 0.0
            end = float(beat_map["B002"]["start"])
        elif plan["scene_id"] == "S002":
            start = float(beat_map["B002"]["start"])
            end = resolve_anchor("vinte reais", ["B002"], timing)["start"]
        else:
            start = resolve_anchor("vinte reais", ["B002"], timing)["start"]
            end = float(timing["duration_seconds"])
        if end <= start or anchor_start["start"] < start - 0.001 or anchor_end["end"] > end + 0.001:
            raise PilotError(f"{plan['scene_id']}: limites narrativos inválidos.")
        events = [
            event_with_time(
                event,
                beat_ids=plan["beat_ids"],
                timing=timing,
                scene_start=start,
                scene_end=end,
            )
            for event in plan["events"]
        ]
        for event in events:
            if not start <= event["time"] < event["end_time"] <= end + 0.001:
                raise PilotError(f"{event['event_id']}: evento fora da cena.")
        scenes.append(
            {
                "scene_id": plan["scene_id"],
                "beat_ids": plan["beat_ids"],
                "start": round(start, 4),
                "end": round(end, 4),
                "duration": round(end - start, 4),
                "composition": plan["composition"],
                "variant": {
                    "id": plan["variant"],
                    "version": plan["version"],
                    "status": composition["status"],
                    "motion_status": composition["motion_status"],
                },
                "focus_mode": plan["focus_mode"],
                "anchor_start": anchor_start,
                "anchor_end": anchor_end,
                "anchors": resolved_anchors,
                "resolved_times": {
                    name: {"start": anchor["start"], "end": anchor["end"]}
                    for name, anchor in resolved_anchors.items()
                },
                "events": events,
                "dominant_motion": plan["dominant_motion"],
                "continuity_in": plan["continuity_in"],
                "continuity_out": plan["continuity_out"],
                "source_svg": relative(source_path),
                "source_svg_sha256": sha256(source_path),
                "content_zones": composition["content_zones"],
            }
        )

    if any(abs(scenes[i]["end"] - scenes[i + 1]["start"]) > 0.001 for i in range(2)):
        raise PilotError("Timeline possui lacuna entre cenas.")
    manifest = {
        "schema_version": "1.0",
        "pilot_id": "capital_oculto_audiovisual_s001_s003",
        "status": "APPROVED",
        "selection_mode": "PRODUCTION",
        "production_allowed": True,
        "approval": {
            "approved_by": "human",
            "approved_on": "2026-09-24",
            "geometry_changed": False,
            "motion_changed": False,
            "content_zones_changed": False,
        },
        "episode_id": "CO-001",
        "canvas": CANVAS,
        "safe_area": {"absolute": SAFE_AREA, "text": TEXT_SAFE_AREA},
        "visual_system": "CO_VISUAL_V3",
        "art_direction": "CO_ART_DIRECTION_V4",
        "composition_system": "CO_EDITORIAL_COMPOSITIONS_V1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "audio": {
            "file": relative(audio_path),
            "player_path": "audio/processed/narration_azure_antonio.wav",
            "sha256": timing["audio_sha256"],
            "provider": timing["provider"],
            "narrator_id": timing["narrator_id"],
            "voice": timing["voice"],
            "duration_seconds": timing["duration_seconds"],
            "render_origin_seconds": timing["beats"][0]["speech_start"],
            "presentation_duration_seconds": round(
                float(timing["duration_seconds"]) - float(timing["beats"][0]["speech_start"]), 4
            ),
            "leading_blank_policy": "TRIM_TO_FIRST_SPEECH_WITHOUT_INTERNAL_RETIMING",
            "timing_method": timing["timing_method"],
        },
        "sources": {
            "timing": {"file": relative(TIMING_FILE), "sha256": sha256(TIMING_FILE)},
            "compositions": {
                "file": relative(COMPOSITIONS_FILE),
                "sha256": sha256(COMPOSITIONS_FILE),
            },
        },
        "scenes": scenes,
    }
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    motion_spec = {
        "pilot_id": manifest["pilot_id"],
        "palette": {
            "black": "#111111",
            "lime": "#C4E538",
            "amber": "#E8A33D",
            "off_white": "#F4F3EF",
            "gray": "#D9D9D4",
        },
        "motion_language": {
            "easing": "ease_out_cubic",
            "idle": "none",
            "dominant_movements_simultaneous": 1,
            "micro_reveal_ms": [200, 350],
            "explanatory_ms": [450, 900],
            "major_transform_ms": [700, 1400],
            "transition_ms": [250, 500],
        },
        "scenes": [
            {
                "scene_id": scene["scene_id"],
                "source_svg": scene["source_svg"],
                "source_svg_sha256": scene["source_svg_sha256"],
                "variant": scene["variant"],
                "focus_mode": scene["focus_mode"],
                "events": scene["events"],
            }
            for scene in scenes
        ],
    }
    MOTION_SPEC_FILE.write_text(
        json.dumps(motion_spec, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if not PLAYER_TEMPLATE.is_file():
        raise PilotError(f"Template do player ausente: {PLAYER_TEMPLATE}")
    shutil.copyfile(PLAYER_TEMPLATE, PLAYER_FILE)
    print(f"MANIFESTO RESOLVIDO — {relative(MANIFEST_FILE)}")
    for scene in scenes:
        print(
            f"  {scene['scene_id']}: {scene['start']:.3f}s–{scene['end']:.3f}s | "
            f"{scene['variant']['id']} v{scene['variant']['version']}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PilotError, OSError, KeyError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
