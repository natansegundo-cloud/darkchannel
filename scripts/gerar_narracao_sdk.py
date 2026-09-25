#!/usr/bin/env python3
"""Caminho oficial de narracao Azure Speech SDK + WordBoundary real.

O alinhador de ``gerar_narracao_v2.py`` nao participa deste caminho. Falhas de
SDK, credencial ou eventos WordBoundary interrompem a geracao; o fallback
heuristico so pode ser solicitado explicitamente por outro fluxo e recebe
``timing_quality=HEURISTIC``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import wave
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NARRATORS_PATH = ROOT / "config" / "narrators.json"
DEFAULT_OUTPUT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006_v2_wordboundary"
RATE = "-7%"
PITCH = "0%"
TIMING_QUALITY = "WORD_BOUNDARY_REAL"
SDK_PACKAGE = "azure-cognitiveservices-speech==1.51.2"


class OfficialNarrationError(RuntimeError):
    """Erro seguro do caminho oficial sem imprimir segredo Azure."""


def load_engine() -> Any:
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    try:
        from gerar_narracao_v3_sdk_experimental import (
            ExperimentalNarrationError,
            build_ssml,
            connection_test,
            load_env,
            load_json,
            synthesize_ssml,
        )
    except ImportError as exc:
        raise OfficialNarrationError("Motor Azure SDK oficial indisponivel.") from exc
    return {
        "ExperimentalNarrationError": ExperimentalNarrationError,
        "build_ssml": build_ssml,
        "connection_test": connection_test,
        "load_env": load_env,
        "load_json": load_json,
        "synthesize_ssml": synthesize_ssml,
    }


def beat_data() -> list[dict[str, Any]]:
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from gerar_narracao_v2 import BEATS_DATA

    return BEATS_DATA


def narrator_config(engine: dict[str, Any]) -> dict[str, Any]:
    config = engine["load_json"](NARRATORS_PATH)
    narrator_id = config["default_narrator"]
    return next(item for item in config["narrators"] if item["id"] == narrator_id)


def resolve_credentials(engine: dict[str, Any], narrator: dict[str, Any], env_file: Path) -> tuple[str, str]:
    env = engine["load_env"](env_file)
    azure = narrator["azure"]
    key = next((env[name] for name in azure["key_names"] if env.get(name, "").strip()), None)
    region = next((env[name] for name in azure["region_names"] if env.get(name, "").strip()), None)
    if not key or not region:
        raise OfficialNarrationError(
            "OFFICIAL_SDK_FAILURE: credenciais Azure ausentes; nenhum fallback heuristico foi acionado."
        )
    return key, region


def synthesis_id(beat: dict[str, Any], narrator: dict[str, Any]) -> str:
    material = "|".join(
        [beat["beat_id"], beat["raw_text"], narrator["voice"], RATE, PITCH, SDK_PACKAGE]
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:12]
    return f"CO-001-V2-WB-{beat['beat_id']}-{digest}"


def read_wav(path: Path) -> tuple[wave._wave_params, bytes, float]:
    try:
        with wave.open(str(path), "rb") as handle:
            params = handle.getparams()
            frames = handle.readframes(handle.getnframes())
            duration_ms = handle.getnframes() * 1000.0 / handle.getframerate()
    except (OSError, wave.Error) as exc:
        raise OfficialNarrationError(f"WAV oficial invalido: {path.name}") from exc
    return params, frames, duration_ms


def write_wav(path: Path, params: wave._wave_params, frames: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setparams(params)
        handle.writeframes(frames)


def synthesize_beat(
    beat: dict[str, Any],
    *,
    narrator: dict[str, Any],
    key: str,
    region: str,
    engine: dict[str, Any],
    output_dir: Path,
    allow_existing: bool = False,
) -> dict[str, Any]:
    output_path = output_dir / "audio" / f"{beat['beat_id']}_azure_sdk_word_boundary.wav"
    if output_path.exists() and not allow_existing:
        raise OfficialNarrationError(f"Artefato oficial ja existe e nao sera sobrescrito: {output_path}")
    try:
        ssml = engine["build_ssml"](beat, narrator, rate_override=RATE)
        audio_data, boundaries = engine["synthesize_ssml"](
            ssml, narrator=narrator, key=key, region=region
        )
    except Exception as exc:
        if isinstance(exc, engine["ExperimentalNarrationError"]):
            raise OfficialNarrationError(f"OFFICIAL_SDK_FAILURE: {exc}") from exc
        raise OfficialNarrationError("OFFICIAL_SDK_FAILURE: sintese Azure interrompida.") from exc
    if not boundaries or any(item.get("audio_offset_ms") is None for item in boundaries):
        raise OfficialNarrationError(
            f"OFFICIAL_SDK_FAILURE: {beat['beat_id']} nao retornou WordBoundary completo; fallback nao foi acionado."
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio_data)
    params, _frames, duration_ms = read_wav(output_path)
    sid = synthesis_id(beat, narrator)
    words = []
    for index, item in enumerate(boundaries, start=1):
        words.append(
            {
                "index": index,
                "text": item["text"],
                "normalized": item["normalized"],
                "audio_offset_ms": item["audio_offset_ms"],
                "duration_ms": item["duration_ms"],
                "boundary_type": item["boundary_type"],
                "text_offset": item["text_offset"],
                "word_length": item["word_length"],
            }
        )
    density = len(words) / (duration_ms / 1000.0) if duration_ms else 0.0
    return {
        "schema_version": "3.0",
        "synthesis_id": sid,
        "provider": "azure_speech_sdk",
        "sdk_package": SDK_PACKAGE,
        "voice": narrator["voice"],
        "language": narrator.get("language", "pt-BR"),
        "rate": RATE,
        "pitch": PITCH,
        "audio_file": output_path.relative_to(ROOT).as_posix(),
        "audio_duration_ms": round(duration_ms, 3),
        "sample_rate": params.framerate,
        "channels": params.nchannels,
        "timing_quality": TIMING_QUALITY,
        "beat_id": beat["beat_id"],
        "title": beat["title"],
        "text": beat["raw_text"],
        "ssml_body": beat["ssml_body"],
        "pause_after_ms": int(beat["pause_after_ms"]),
        "words": words,
        "words_per_second": round(density, 3),
        "voice_density_warning": density > 3.2,
    }


def compose_audio(beat_rows: list[dict[str, Any]], output_dir: Path) -> tuple[str, float, list[dict[str, Any]]]:
    combined_path = output_dir / "audio" / "narration_wordboundary.wav"
    if combined_path.exists():
        raise OfficialNarrationError(f"Artefato oficial ja existe e nao sera sobrescrito: {combined_path}")
    params = None
    frames = bytearray()
    cursor_ms = 0.0
    composed = []
    for index, row in enumerate(beat_rows):
        wav_path = ROOT / row["audio_file"]
        current_params, current_frames, duration_ms = read_wav(wav_path)
        if params is None:
            params = current_params
        elif (
            current_params.nchannels != params.nchannels
            or current_params.sampwidth != params.sampwidth
            or current_params.framerate != params.framerate
            or current_params.comptype != params.comptype
        ):
            raise OfficialNarrationError("WAVs oficiais possuem parametros incompatíveis.")
        row["composition_start_ms"] = round(cursor_ms, 3)
        row["composition_end_ms"] = round(cursor_ms + duration_ms, 3)
        for word in row["words"]:
            word["absolute_audio_offset_ms"] = round(cursor_ms + word["audio_offset_ms"], 3)
        frames.extend(current_frames)
        cursor_ms += duration_ms
        if index < len(beat_rows) - 1:
            pause_ms = int(row["pause_after_ms"])
            frames.extend(b"\x00" * round(params.framerate * params.sampwidth * pause_ms / 1000))
            row["composition_pause_after_ms"] = pause_ms
            cursor_ms += pause_ms
        composed.append(row)
    if params is None:
        raise OfficialNarrationError("Nenhum beat oficial foi sintetizado.")
    write_wav(combined_path, params, bytes(frames))
    return combined_path.relative_to(ROOT).as_posix(), round(cursor_ms, 3), composed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / "scripts" / ".env")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--repair-incomplete",
        action="store_true",
        help="Permite substituir WAVs parciais gerados por uma execucao oficial interrompida.",
    )
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    timing_path = output_dir / "timing" / "03A_AUDIO_TIMING_WORD_BOUNDARY.json"
    if timing_path.exists():
        raise OfficialNarrationError("Timing oficial ja existe e nao sera sobrescrito.")
    engine = load_engine()
    narrator = narrator_config(engine)
    key, region = resolve_credentials(engine, narrator, args.env_file)
    print("AZURE_CONFIG_FOUND=true")
    print(f"AZURE_REGION={region}")
    try:
        probe_count = engine["connection_test"](narrator=narrator, key=key, region=region)
    except Exception as exc:
        raise OfficialNarrationError("OFFICIAL_SDK_FAILURE: teste de conexao sem WordBoundary; fallback nao foi acionado.") from exc
    print(f"AZURE_CONNECTION_TEST=OK boundaries={probe_count}")
    beats = beat_data()
    beat_rows = [
        synthesize_beat(
            beat,
            narrator=narrator,
            key=key,
            region=region,
            engine=engine,
            output_dir=output_dir,
            allow_existing=args.repair_incomplete,
        )
        for beat in beats
    ]
    audio_file, total_ms, beat_rows = compose_audio(beat_rows, output_dir)
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    output_dir.joinpath("timing", "boundaries").mkdir(parents=True, exist_ok=True)
    for row in beat_rows:
        boundary_file = output_dir / "timing" / "boundaries" / f"{row['beat_id']}.json"
        row["boundary_file"] = boundary_file.relative_to(ROOT).as_posix()
        boundary_file.write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timing = {
        "schema_version": "3.0",
        "synthesis_id": "CO-001-V2-WB-COMPOSITION-" + hashlib.sha256(audio_file.encode()).hexdigest()[:12],
        "episode_id": "CO-001",
        "provider": "azure_speech_sdk",
        "sdk_package": SDK_PACKAGE,
        "voice": narrator["voice"],
        "language": narrator.get("language", "pt-BR"),
        "rate": RATE,
        "pitch": PITCH,
        "audio_file": audio_file,
        "audio_duration_ms": total_ms,
        "audio_duration_seconds": round(total_ms / 1000.0, 3),
        "timing_quality": TIMING_QUALITY,
        "connection_test_word_boundaries": probe_count,
        "speech_overlap": 0,
        "overlap_allowed": False,
        "fallback_policy": {
            "legacy_script": "scripts/gerar_narracao_v2.py",
            "legacy_aligner": "heuristic_token_weight",
            "status": "LEGACY_FALLBACK_ONLY",
            "silent_fallback": False,
            "fallback_timing_quality": "HEURISTIC",
        },
        "beats": beat_rows,
        "resolved_anchors": [],
        "voice_density_warnings": [
            {"beat_id": row["beat_id"], "words_per_second": row["words_per_second"]}
            for row in beat_rows
            if row["voice_density_warning"]
        ],
        "generated_at": generated_at,
    }
    timing_path.parent.mkdir(parents=True, exist_ok=True)
    timing_path.write_text(json.dumps(timing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WORD_BOUNDARY_EVENTS={sum(len(row['words']) for row in beat_rows)}")
    print(f"TIMING_QUALITY={TIMING_QUALITY}")
    print(f"TIMING={timing_path.relative_to(ROOT)}")
    print(f"AUDIO={audio_file}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OfficialNarrationError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(2)
