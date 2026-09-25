#!/usr/bin/env python3
"""Valida o pacote oficial paralelo S001-S006 com WordBoundary real."""

from __future__ import annotations

import json
import wave
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006_v2_wordboundary"
TIMING_FILE = PILOT_DIR / "timing" / "03A_AUDIO_TIMING_WORD_BOUNDARY.json"
MANIFEST_FILE = PILOT_DIR / "manifest" / "scene_manifest_wordboundary.json"
MOTION_FILE = PILOT_DIR / "scenes" / "motion_spec_wordboundary.json"
RENDER_FILE = PILOT_DIR / "renders" / "capital_oculto_pilot_s001_s006_v2_wordboundary.webm"
QUALITY = "WORD_BOUNDARY_REAL"


class ValidationError(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"Arquivo ausente: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    timing = load(TIMING_FILE)
    manifest = load(MANIFEST_FILE)
    motion = load(MOTION_FILE)
    if timing.get("timing_quality") != QUALITY or manifest["audio"].get("timing_quality") != QUALITY:
        raise ValidationError("Qualidade oficial nao e WORD_BOUNDARY_REAL.")
    if timing["provider"] != "azure_speech_sdk" or timing["voice"] != "pt-BR-AntonioNeural":
        raise ValidationError("Provider ou voz oficial divergente.")
    if timing.get("rate") != "-7%" or timing.get("pitch") != "0%":
        raise ValidationError("Pacing oficial divergente de -7% / 0%.")
    if manifest["audio"].get("synthesis_id") != timing["synthesis_id"]:
        raise ValidationError("synthesis_id do audio e do timing diverge.")
    if manifest.get("protect_primary_type") is not True:
        raise ValidationError("PROTECT_PRIMARY_TYPE nao esta ativo no manifesto.")
    if motion.get("timing_quality") != QUALITY:
        raise ValidationError("Motion spec nao esta marcado como WordBoundary real.")
    resolution = motion["anchor_resolution"]
    if resolution["anchors_ambiguous"] != 0 or resolution["anchors_missing"] != 0:
        raise ValidationError("Existem anchors ambiguos ou ausentes.")
    if resolution["anchors_resolved"] != len(manifest["anchor_index"]):
        raise ValidationError("Contagem do indice de anchors diverge.")

    beats = timing["beats"]
    if [beat["beat_id"] for beat in beats] != [f"B00{i}" for i in range(1, 7)]:
        raise ValidationError("A ordem oficial deve ser B001-B006.")
    audio_path = ROOT / timing["audio_file"]
    if not audio_path.is_file():
        raise ValidationError("Audio composto oficial ausente.")
    with wave.open(str(audio_path), "rb") as audio:
        duration_ms = audio.getnframes() * 1000.0 / audio.getframerate()
    if abs(duration_ms - timing["audio_duration_ms"]) > 1.0:
        raise ValidationError("Duracao do WAV diverge do timing.")

    total_events = 0
    negative_durations = 0
    for index, beat in enumerate(beats):
        required = {
            "schema_version", "synthesis_id", "provider", "voice", "rate", "pitch",
            "audio_file", "audio_duration_ms", "timing_quality", "beat_id", "words",
        }
        if not required.issubset(beat):
            raise ValidationError(f"Schema incompleto em {beat['beat_id']}.")
        if beat["timing_quality"] != QUALITY or beat["provider"] != "azure_speech_sdk":
            raise ValidationError(f"Timing invalido em {beat['beat_id']}.")
        boundary = load(ROOT / beat["boundary_file"])
        if boundary["synthesis_id"] != beat["synthesis_id"] or boundary["beat_id"] != beat["beat_id"]:
            raise ValidationError(f"Boundary file divergente em {beat['beat_id']}.")
        for word in beat["words"]:
            for field in ("text", "audio_offset_ms", "duration_ms", "boundary_type", "text_offset", "word_length"):
                if field not in word or word[field] is None:
                    raise ValidationError(f"WordBoundary incompleto em {beat['beat_id']}.")
            if word["duration_ms"] < 0:
                negative_durations += 1
        if index and abs(beat["composition_start_ms"] - (beats[index - 1]["composition_end_ms"] + beats[index - 1]["pause_after_ms"])) > 1.0:
            raise ValidationError(f"Gap ou overlap entre {beats[index - 1]['beat_id']} e {beat['beat_id']}.")
    if negative_durations:
        raise ValidationError("Existem duracoes de palavra negativas.")

    expected_states = {
        "S004": ["O PROBLEMA", "NAO E", "UMA COMPRA", "ABSURDA"],
        "S005": ["TRILHOS", "REFERENCIA COMPARTILHADA", "NORMAL", "COMPARACAO", "DESPESAS", "O SISTEMA SE MOVE JUNTO"],
        "S006": ["EXTRA", "BASELINE SHIFT", "EXTRA EM SEGUNDO PLANO", "NORMAL", "BASE ESTRUTURAL", "VIROU REFERENCIA"],
    }
    scenes = manifest["scenes"]
    if [scene["scene_id"] for scene in scenes] != [f"S00{i}" for i in range(1, 7)]:
        raise ValidationError("O pacote oficial deve conter somente S001-S006.")
    for index, scene in enumerate(scenes):
        if index and abs(scene["start"] - scenes[index - 1]["end"]) > 0.001:
            raise ValidationError(f"Gap entre cenas {scenes[index - 1]['scene_id']} e {scene['scene_id']}.")
        if scene["first_useful_state_time"] > scene["start"] + 0.35:
            raise ValidationError(f"Guardrail de primeiro estado falhou em {scene['scene_id']}.")
        if scene["scene_id"] == "S006":
            variant = scene["variant"]
            if variant["id"] != "CO-COMP-04D" or variant["version"] != 1.1 or variant["protect_primary_type"] is not True:
                raise ValidationError("CO-COMP-04D@1.1 nao esta protegido.")
        if scene["scene_id"] in expected_states:
            states = [subbeat["visual_state"] for subbeat in scene["visual_subbeats"]]
            if states != expected_states[scene["scene_id"]]:
                raise ValidationError(f"Sequencia visual divergente em {scene['scene_id']}.")
        for event in scene["events"]:
            total_events += 1
            if event.get("timing_source") != QUALITY:
                raise ValidationError(f"Evento sem timing real: {event['event_id']}.")
            if event["end_time"] <= event["time"]:
                raise ValidationError(f"Duracao invalida em {event['event_id']}.")
            if event["time"] < scene["start"] - 0.001 or event["end_time"] > scene["end"] + 0.001:
                raise ValidationError(f"Evento fora da cena: {event['event_id']}.")
            if event["anchor"].get("resolution_method") != QUALITY or event["anchor"].get("audio_offset_ms") is None:
                raise ValidationError(f"Anchor nao real em {event['event_id']}.")
    if total_events == 0:
        raise ValidationError("Nenhum evento de motion foi validado.")
    if timing["speech_overlap"] != 0 or manifest["audio"]["speech_overlap"] != 0:
        raise ValidationError("Speech overlap diferente de zero.")
    if "heuristic" in json.dumps(manifest).casefold() or "heuristic" in json.dumps(motion).casefold():
        raise ValidationError("Heuristico encontrado no manifesto ou motion spec oficial.")
    if not RENDER_FILE.is_file() or RENDER_FILE.stat().st_size < 100_000:
        raise ValidationError("Render WordBoundary ausente ou invalido.")
    print("WORD_BOUNDARY_VALIDATION=PASS")
    print(f"WORD_BOUNDARY_EVENTS={sum(len(beat['words']) for beat in beats)}")
    print(f"MOTION_EVENTS={total_events}")
    print(f"ANCHORS_RESOLVED={resolution['anchors_resolved']}")
    print("ANCHORS_AMBIGUOUS=0")
    print("ANCHORS_MISSING=0")
    print("SPEECH_OVERLAP=0")
    print(f"DENSITY_WARNINGS={len(timing['voice_density_warnings'])}")
    print(f"FINAL_DURATION_MS={timing['audio_duration_ms']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"WORD_BOUNDARY_VALIDATION=FAIL: {exc}")
        raise SystemExit(2)
