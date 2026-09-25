#!/usr/bin/env python3
"""Valida o gate do contrato geométrico e a instância V3 renderizada."""

from __future__ import annotations

import hashlib
import json
import wave
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests" / "audiovisual_pilot_s001_s006_v2_wordboundary"
TARGET = ROOT / "tests" / "audiovisual_pilot_s001_s006_v3_geometry"


class ValidationError(RuntimeError):
    pass


def load(path: Path) -> dict:
    if not path.is_file():
        raise ValidationError(f"Arquivo ausente: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def without_geometry(value: object) -> object:
    if isinstance(value, list):
        return [without_geometry(item) for item in value]
    if isinstance(value, dict):
        return {key: without_geometry(item) for key, item in value.items() if key not in {"geometry_contract", "geometry_routes"}}
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    contract = load(ROOT / "config" / "visual_geometry_contract.json")
    audit = load(ROOT / "tests" / "visual_geometry_v1" / "geometry_audit_results.json")
    source_manifest = load(SOURCE / "manifest" / "scene_manifest_wordboundary.json")
    target_manifest = load(TARGET / "manifest" / "scene_manifest_geometry.json")
    source_motion = load(SOURCE / "scenes" / "motion_spec_wordboundary.json")
    target_motion = load(TARGET / "scenes" / "motion_spec_geometry.json")
    routes = load(TARGET / "scenes" / "geometry_routes.json")
    metadata = load(TARGET / "renders" / "render_metadata_geometry.json")

    if contract.get("version") != "1.0" or contract.get("status") != "ACTIVE_FOR_PILOT_V3":
        raise ValidationError("Contrato geométrico não está ativo na versão esperada.")
    if audit.get("browser_geometry") is not True or audit.get("errors_after") != 0:
        raise ValidationError(f"Gate geométrico falhou: errors_after={audit.get('errors_after')}.")
    if audit.get("total_samples") != 90:
        raise ValidationError("Amostragem geométrica não cobre os 90 pontos esperados.")

    if target_manifest["pilot_id"] != "capital_oculto_pilot_s001_s006_v3_geometry":
        raise ValidationError("Pilot ID V3 divergente.")
    if [scene["scene_id"] for scene in target_manifest["scenes"]] != [f"S00{i}" for i in range(1, 7)]:
        raise ValidationError("O pacote V3 deve conter somente S001-S006.")
    if source_manifest["anchor_index"] != target_manifest["anchor_index"]:
        raise ValidationError("Anchor index foi alterado na migração geométrica.")
    if without_geometry(source_manifest["scenes"]) != without_geometry(target_manifest["scenes"]):
        raise ValidationError("Timing ou eventos de cena foram alterados na migração geométrica.")
    if without_geometry(source_motion) != without_geometry(target_motion):
        raise ValidationError("Motion spec foi alterado além dos metadados geométricos.")
    for field in ("provider", "voice", "rate", "pitch", "synthesis_id", "duration_seconds", "timing_quality"):
        if source_manifest["audio"].get(field) != target_manifest["audio"].get(field):
            raise ValidationError(f"Campo de áudio alterado: {field}.")
    if target_manifest["audio"]["player_path"] != "../audiovisual_pilot_s001_s006_v2_wordboundary/audio/narration_wordboundary.wav":
        raise ValidationError("V3 não aponta para o áudio WordBoundary existente.")

    s005 = routes["scenes"]["S005"]
    if s005["reference"]["geometry_type"] != "ACCENT_LINE" or s005["reference"]["arrowhead"] is not False:
        raise ValidationError("Contrato S005 não classifica a diagonal como ACCENT_LINE sem seta.")
    if s005["tracks"]["geometry_type"] != "TRACK":
        raise ValidationError("Contrato S005 não classifica os trilhos como TRACK.")
    s006 = routes["scenes"]["S006"]["baseline"]
    if s006["protect_primary_type"] is not True or s006["route"] != ["STOP_BEFORE", "ROUTE_AROUND", "TRANSFORM_TO_UNDERLINE"]:
        raise ValidationError("Contrato S006 não protege a tipografia com a rota exigida.")

    audio_path = SOURCE / "audio" / "narration_wordboundary.wav"
    render_path = ROOT / metadata["render"]["file"]
    if not audio_path.is_file() or not render_path.is_file() or render_path.stat().st_size < 100_000:
        raise ValidationError("Áudio fonte ou render V3 ausente/inválido.")
    with wave.open(str(audio_path), "rb") as audio:
        audio_duration = audio.getnframes() / audio.getframerate()
    if abs(audio_duration - target_manifest["audio"]["duration_seconds"]) > 0.01:
        raise ValidationError("Duração do áudio fonte diverge do manifesto V3.")
    if abs(float(metadata["render"]["duration_seconds"]) - target_manifest["audio"]["duration_seconds"]) > 0.01:
        raise ValidationError("Duração do render V3 diverge do áudio preservado.")

    print("VISUAL_GEOMETRY_VALIDATION=PASS")
    print(f"GEOMETRY_ERRORS_AFTER={audit['errors_after']}")
    print(f"GEOMETRY_SAMPLES={audit['total_samples']}")
    print(f"AUDIO_SHA256={sha256(audio_path)}")
    print(f"RENDER_SHA256={sha256(render_path)}")
    print(f"RENDER_SIZE={render_path.stat().st_size}")
    print(f"RENDER_DURATION={metadata['render']['duration_seconds']}s")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"VISUAL_GEOMETRY_VALIDATION=FAIL: {exc}")
        raise SystemExit(2)
