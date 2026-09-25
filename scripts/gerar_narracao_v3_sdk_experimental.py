#!/usr/bin/env python3
"""Gera áudio experimental com word boundaries reais do Azure Speech SDK.

Este caminho é deliberadamente isolado do pipeline oficial. Ele sintetiza os
beats B001–B006 em WAVs próprios, registra os eventos WordBoundary do SDK e
produz um relatório comparativo contra o timing heurístico V2.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import wave
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
NARRATORS_PATH = ROOT / "config" / "narrators.json"
HEURISTIC_TIMING_PATH = ROOT / "tests" / "audiovisual_pilot_s001_s006" / "timing" / "03A_AUDIO_TIMING_v2.json"
MOTION_SPEC_PATHS = (
    ROOT / "tests" / "audiovisual_pilot_s001_s003" / "scenes" / "motion_spec.json",
    ROOT / "tests" / "audiovisual_pilot_s001_s006" / "scenes" / "motion_spec.json",
)
DEFAULT_OUTPUT_DIR = ROOT / "tests" / "word_boundary_v3_experimental"


class ExperimentalNarrationError(RuntimeError):
    """Erro operacional sem expor credenciais ou respostas completas do serviço."""


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_env(path: Path) -> dict[str, str]:
    values = {key: value for key, value in os.environ.items() if value}
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) and key not in values:
                values[key] = value.strip().strip("\"'")
    return values


def normalize_word(value: str) -> str:
    import unicodedata

    decomposed = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in plain if char.isalnum())


def duration_to_100ns(value: Any) -> int | None:
    if value is None:
        return None
    if hasattr(value, "total_seconds"):
        return round(value.total_seconds() * 10_000_000)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def optional_int(value: Any) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None


def build_ssml(
    beat: dict[str, Any],
    narrator: dict[str, Any],
    *,
    rate_override: str | None = None,
) -> str:
    delivery = narrator.get("delivery", {})
    language = narrator.get("language", "pt-BR")
    voice = narrator.get("voice", "pt-BR-AntonioNeural")
    rate = rate_override if rate_override is not None else delivery.get("rate", "0%")
    pitch = delivery.get("pitch", "0%")
    volume = delivery.get("volume", "default")
    body = beat["ssml_body"]
    return (
        f'<speak version="1.0" xml:lang="{escape(language)}">'
        f'<voice name="{escape(voice)}">'
        f'<prosody rate="{escape(rate)}" pitch="{escape(pitch)}" volume="{escape(volume)}">'
        f"{body}</prosody></voice></speak>"
    )


def load_sdk() -> Any:
    try:
        import azure.cognitiveservices.speech as speechsdk
    except ImportError as exc:
        raise ExperimentalNarrationError(
            "SDK ausente. Instale exatamente azure-cognitiveservices-speech==1.51.2."
        ) from exc
    return speechsdk


def synthesize_ssml(
    ssml: str,
    *,
    narrator: dict[str, Any],
    key: str,
    region: str,
) -> tuple[bytes, list[dict[str, Any]]]:
    speechsdk = load_sdk()
    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_synthesis_voice_name = narrator["voice"]
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
    )
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    boundaries: list[dict[str, Any]] = []

    def on_word_boundary(event: Any) -> None:
        text = str(getattr(event, "text", "") or "")
        normalized = normalize_word(text)
        if not normalized:
            return
        audio_offset_100ns = duration_to_100ns(getattr(event, "audio_offset", None))
        duration_100ns = duration_to_100ns(getattr(event, "duration", None))
        boundaries.append(
            {
                "text": text,
                "normalized": normalized,
                "text_offset": optional_int(getattr(event, "text_offset", None)),
                "word_length": optional_int(getattr(event, "word_length", None)),
                "audio_offset_100ns": audio_offset_100ns,
                "audio_offset_ms": None if audio_offset_100ns is None else round(audio_offset_100ns / 10_000, 3),
                "duration_100ns": duration_100ns,
                "duration_ms": None if duration_100ns is None else round(duration_100ns / 10_000, 3),
                "boundary_type": (
                    None
                    if getattr(event, "boundary_type", None) is None
                    else str(event.boundary_type)
                ),
            }
        )

    word_boundary_signal = synthesizer.synthesis_word_boundary
    word_boundary_signal.connect(on_word_boundary)
    try:
        result = synthesizer.speak_ssml_async(ssml).get()
    finally:
        word_boundary_signal.disconnect_all()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        details = getattr(result, "cancellation_details", None)
        reason = getattr(details, "reason", "unknown")
        error = getattr(details, "error_details", "")
        safe_error = re.sub(r"[A-Za-z0-9+/=_-]{24,}", "[redacted]", str(error))
        raise ExperimentalNarrationError(
            f"Falha na síntese Azure: reason={reason}; details={safe_error}"
        )

    audio_data = bytes(result.audio_data)
    boundaries.sort(
        key=lambda item: (
            item["audio_offset_100ns"] is None,
            item["audio_offset_100ns"] or 0,
        )
    )
    return audio_data, boundaries


def connection_test(*, narrator: dict[str, Any], key: str, region: str) -> int:
    probe = {
        "ssml_body": escape("Teste de conexão."),
    }
    audio_data, boundaries = synthesize_ssml(
        build_ssml(probe, narrator),
        narrator=narrator,
        key=key,
        region=region,
    )
    if not audio_data:
        raise ExperimentalNarrationError("Teste Azure não retornou áudio.")
    if not boundaries:
        raise ExperimentalNarrationError("Teste Azure não retornou nenhum evento WordBoundary.")
    if any(item["audio_offset_ms"] is None for item in boundaries):
        raise ExperimentalNarrationError("Teste Azure retornou WordBoundary sem audio_offset.")
    return len(boundaries)


def synthesize_beat(
    beat: dict[str, Any],
    *,
    narrator: dict[str, Any],
    key: str,
    region: str,
    output_path: Path,
) -> dict[str, Any]:
    audio_data, boundaries = synthesize_ssml(
        build_ssml(beat, narrator),
        narrator=narrator,
        key=key,
        region=region,
    )
    if not boundaries:
        raise ExperimentalNarrationError(f"{beat['beat_id']} não retornou WordBoundary.")
    if any(item["audio_offset_ms"] is None for item in boundaries):
        raise ExperimentalNarrationError(f"{beat['beat_id']} retornou WordBoundary sem audio_offset.")
    if output_path.exists():
        raise ExperimentalNarrationError(f"WAV experimental já existe e não será sobrescrito: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(audio_data)
    try:
        with wave.open(str(output_path), "rb") as handle:
            duration_ms = round(handle.getnframes() * 1000 / handle.getframerate(), 3)
            sample_rate = handle.getframerate()
            channels = handle.getnchannels()
    except wave.Error as exc:
        raise ExperimentalNarrationError(f"WAV inválido produzido para {beat['beat_id']}.") from exc

    return {
        "beat_id": beat["beat_id"],
        "title": beat["title"],
        "text": beat["raw_text"],
        "audio_file": output_path.relative_to(ROOT).as_posix(),
        "duration_ms": duration_ms,
        "sample_rate": sample_rate,
        "channels": channels,
        "words": boundaries,
    }


def read_heuristic() -> dict[str, Any]:
    if not HEURISTIC_TIMING_PATH.is_file():
        raise ExperimentalNarrationError(f"Timing heurístico não encontrado: {HEURISTIC_TIMING_PATH}")
    return load_json(HEURISTIC_TIMING_PATH)


def motion_anchors(heuristic: dict[str, Any]) -> dict[str, list[str]]:
    anchors: dict[str, list[str]] = {}
    beat_ranges = [
        (beat["beat_id"], beat["words"][0]["index"], beat["words"][-1]["index"])
        for beat in heuristic.get("beats", [])
        if beat.get("words")
    ]
    b003_end = next(end for beat_id, _start, end in beat_ranges if beat_id == "B003")
    for path in MOTION_SPEC_PATHS:
        spec = load_json(path)
        local_offset = b003_end if "s001_s006" in path.as_posix() else 0
        for scene in spec.get("scenes", []):
            for event in scene.get("events", []):
                anchor = event.get("anchor", {})
                text = str(anchor.get("text", "")).strip()
                local_index = optional_int(anchor.get("start_word_index"))
                if not text or local_index is None:
                    continue
                global_index = local_index + local_offset
                beat_id = next(
                    (
                        candidate
                        for candidate, start, end in beat_ranges
                        if start <= global_index <= end
                    ),
                    None,
                )
                if beat_id is None:
                    continue
                if text and text not in anchors.setdefault(beat_id, []):
                    anchors[beat_id].append(text)
    return anchors


def find_phrase(words: list[dict[str, Any]], phrase: str) -> dict[str, Any] | None:
    wanted = [normalize_word(token) for token in re.findall(r"\S+", phrase)]
    wanted = [token for token in wanted if token]
    available = [str(word.get("normalized", "")) for word in words]
    if not wanted:
        return None
    for index in range(len(available) - len(wanted) + 1):
        if available[index : index + len(wanted)] == wanted:
            return words[index]
    return None


def compare(heuristic: dict[str, Any], real_beats: list[dict[str, Any]]) -> dict[str, Any]:
    heuristic_by_id = {beat["beat_id"]: beat for beat in heuristic.get("beats", [])}
    anchors_by_beat = motion_anchors(heuristic)
    real_cursor_ms = 0.0
    beat_rows: list[dict[str, Any]] = []
    anchor_rows: list[dict[str, Any]] = []
    for real in real_beats:
        old = heuristic_by_id[real["beat_id"]]
        beat_anchor_rows: list[dict[str, Any]] = []
        for anchor in anchors_by_beat.get(real["beat_id"], []):
            old_word = find_phrase(old.get("words", []), anchor)
            real_word = find_phrase(real["words"], anchor)
            heuristic_ms = None if old_word is None else round(old_word["start"] * 1000, 3)
            real_ms = (
                None
                if real_word is None or real_word["audio_offset_ms"] is None
                else round(real_cursor_ms + real_word["audio_offset_ms"], 3)
            )
            delta_ms = None if heuristic_ms is None or real_ms is None else round(real_ms - heuristic_ms, 3)
            item = {
                "beat_id": real["beat_id"],
                "anchor": anchor,
                "heuristic_ms": heuristic_ms,
                "real_ms": real_ms,
                "delta_ms": delta_ms,
                "absolute_delta_ms": None if delta_ms is None else round(abs(delta_ms), 3),
            }
            beat_anchor_rows.append(item)
            anchor_rows.append(item)
        beat_rows.append(
            {
                "beat_id": real["beat_id"],
                "heuristic_duration_ms": round(old["duration_seconds"] * 1000, 3),
                "real_duration_ms": real["duration_ms"],
                "duration_difference_ms": round(real["duration_ms"] - old["duration_seconds"] * 1000, 3),
                "word_boundary_count": len(real["words"]),
                "anchors": beat_anchor_rows,
            }
        )
        pause_after_ms = next(
            int(item.get("pause_after_ms", 0))
            for item in _beats_data()
            if item["beat_id"] == real["beat_id"]
        )
        real_cursor_ms += real["duration_ms"] + pause_after_ms

    valid = [item for item in anchor_rows if item["absolute_delta_ms"] is not None]
    if not valid:
        raise ExperimentalNarrationError("Nenhuma âncora pôde ser comparada entre timing heurístico e real.")
    absolute_errors = [float(item["absolute_delta_ms"]) for item in valid]
    largest = max(valid, key=lambda item: float(item["absolute_delta_ms"]))
    metrics = {
        "mean_absolute_error_ms": round(statistics.mean(absolute_errors), 3),
        "median_absolute_error_ms": round(statistics.median(absolute_errors), 3),
        "max_absolute_error_ms": round(max(absolute_errors), 3),
        "anchors_over_100ms": sum(value > 100 for value in absolute_errors),
        "anchors_over_200ms": sum(value > 200 for value in absolute_errors),
        "anchors_over_300ms": sum(value > 300 for value in absolute_errors),
        "largest_error": {
            "beat": largest["beat_id"],
            "anchor": largest["anchor"],
            "heuristic_ms": largest["heuristic_ms"],
            "real_ms": largest["real_ms"],
            "delta_ms": largest["delta_ms"],
        },
    }
    return {"beats": beat_rows, "anchors": anchor_rows, "metrics": metrics}


def format_ms(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "null"
    return f"{value:+.3f}" if signed else f"{value:.3f}"


def write_report(
    path: Path,
    *,
    heuristic: dict[str, Any],
    comparison: dict[str, Any],
    generated_at: str,
) -> None:
    metrics = comparison["metrics"]
    largest = metrics["largest_error"]
    lines = [
        "# Comparação — Word Boundary V3 experimental",
        "",
        "Status: **EXPERIMENTAL_COMPLETE**",
        "",
        f"Gerado em: `{generated_at}`",
        "",
        "Este relatório compara o timing heurístico V2 com timestamps reais emitidos pelo evento `WordBoundary` do Azure Speech SDK.",
        "O `motion_spec.json`, os timings oficiais e o pipeline de render não foram alterados.",
        "",
        "## Métricas resumidas",
        "",
        f"- `mean_absolute_error_ms`: {metrics['mean_absolute_error_ms']:.3f}",
        f"- `median_absolute_error_ms`: {metrics['median_absolute_error_ms']:.3f}",
        f"- `max_absolute_error_ms`: {metrics['max_absolute_error_ms']:.3f}",
        f"- `anchors_over_100ms`: {metrics['anchors_over_100ms']}",
        f"- `anchors_over_200ms`: {metrics['anchors_over_200ms']}",
        f"- `anchors_over_300ms`: {metrics['anchors_over_300ms']}",
        "",
        "Maior erro: "
        f"`{largest['beat']}` / `{largest['anchor']}` — heurístico {largest['heuristic_ms']:.3f} ms, "
        f"real {largest['real_ms']:.3f} ms, delta {largest['delta_ms']:+.3f} ms.",
        "",
        "## Resumo por beat",
        "",
        "| Beat | Duração heurística (ms) | Duração real (ms) | Boundaries | Âncoras |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in comparison["beats"]:
        lines.append(
            f"| {row['beat_id']} | {row['heuristic_duration_ms']:.3f} | {row['real_duration_ms']:.3f} | "
            f"{row['word_boundary_count']} | {len(row['anchors'])} |"
        )
    lines.extend(
        [
            "",
            "## Âncoras de motion",
            "",
            "| Beat | Âncora | Heurístico (ms) | WordBoundary real (ms) | Delta absoluto (ms) | Delta assinado (ms) |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for item in comparison["anchors"]:
        lines.append(
            f"| {item['beat_id']} | {item['anchor']} | {format_ms(item['heuristic_ms'])} | "
            f"{format_ms(item['real_ms'])} | {format_ms(item['absolute_delta_ms'])} | "
            f"{format_ms(item['delta_ms'], signed=True)} |"
        )
    lines.extend(
        [
            "",
            "## Referências e limitações",
            "",
            f"- Timing heurístico: `{HEURISTIC_TIMING_PATH.relative_to(ROOT).as_posix()}` (schema `{heuristic.get('schema_version', 'unknown')}`).",
            "- Âncoras: extraídas dos `motion_spec.json` existentes, sem modificá-los.",
            "- `audio_offset_ms` e `duration_ms` de palavras são conversões diretas das unidades de 100 ns fornecidas pelo SDK; campos ausentes permanecem `null`.",
            "- A adoção do SDK como caminho oficial depende de decisão humana posterior.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _beats_data() -> list[dict[str, Any]]:
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from gerar_narracao_v2 import BEATS_DATA

    return BEATS_DATA


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT / "scripts" / ".env")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--beats", default="B001,B002,B003,B004,B005,B006")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    boundary_path = output_dir / "timing" / "boundary_real.json"
    report_path = output_dir / "COMPARISON_REPORT.md"
    if args.report_only:
        if not boundary_path.is_file():
            raise ExperimentalNarrationError("boundary_real.json não existe para recalcular o relatório.")
        payload = load_json(boundary_path)
        heuristic = read_heuristic()
        comparison = compare(heuristic, payload["beats"])
        payload["comparison"] = comparison
        boundary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_report(
            report_path,
            heuristic=heuristic,
            comparison=comparison,
            generated_at=payload["generated_at"],
        )
        print("REPORT_RECALCULATED=true")
        return 0

    config = load_json(NARRATORS_PATH)
    narrator_id = config["default_narrator"]
    narrator = next(item for item in config["narrators"] if item["id"] == narrator_id)
    env = load_env(args.env_file)
    azure = narrator["azure"]
    key = next((env[name] for name in azure["key_names"] if env.get(name, "").strip()), None)
    region = next((env[name] for name in azure["region_names"] if env.get(name, "").strip()), None)
    if not key or not region:
        raise ExperimentalNarrationError(
            "Credenciais Azure ausentes. Disponibilize as variáveis configuradas sem gravá-las no repositório."
        )
    print("AZURE_CONFIG_FOUND=true")
    print(f"AZURE_REGION={region}")
    connection_boundary_count = connection_test(narrator=narrator, key=key, region=region)
    print(f"AZURE_CONNECTION_TEST=OK boundaries={connection_boundary_count}")
    selected = {item.strip().upper() for item in args.beats.split(",") if item.strip()}
    beats = [item for item in _beats_data() if item["beat_id"] in selected]
    if {item["beat_id"] for item in beats} != selected:
        raise ExperimentalNarrationError("A seleção deve conter somente beats existentes em B001–B006.")

    if boundary_path.exists() or report_path.exists():
        raise ExperimentalNarrationError("Artefatos experimentais já existem e não serão sobrescritos.")

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    real_beats = []
    for beat in beats:
        audio_path = output_dir / "audio" / f"{beat['beat_id']}_azure_sdk_word_boundary.wav"
        real_beats.append(
            synthesize_beat(
                beat,
                narrator=narrator,
                key=key,
                region=region,
                output_path=audio_path,
            )
        )
    heuristic = read_heuristic()
    comparison = compare(heuristic, real_beats)
    boundary_path.parent.mkdir(parents=True, exist_ok=True)
    boundary_path.write_text(
        json.dumps(
            {
                "schema_version": "3.0-experimental",
                "episode_id": "CO-001",
                "provider": "azure_speech_sdk",
                "sdk_package": "azure-cognitiveservices-speech==1.51.2",
                "voice": narrator["voice"],
                "language": narrator["language"],
                "generated_at": generated_at,
                "status": "EXPERIMENTAL_COMPLETE",
                "connection_test_word_boundaries": connection_boundary_count,
                "official_pipeline_untouched": True,
                "beats": real_beats,
                "comparison": comparison,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_report(report_path, heuristic=heuristic, comparison=comparison, generated_at=generated_at)
    total_boundaries = sum(len(beat["words"]) for beat in real_beats)
    print(f"Word boundaries reais gerados para {len(real_beats)} beats.")
    print(f"WORD_BOUNDARY_EVENTS={total_boundaries}")
    print(f"Timing: {boundary_path.relative_to(ROOT)}")
    print(f"Relatório: {report_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExperimentalNarrationError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(2)
