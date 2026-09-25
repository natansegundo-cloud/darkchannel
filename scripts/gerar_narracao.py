#!/usr/bin/env python3
"""Seleciona o provider de TTS e gera áudio/timing sem expor credenciais.

Azure usa somente a biblioteca padrão e sintetiza um WAV por beat. Kokoro
permanece disponível por delegação ao gerador local já existente.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
import wave
from array import array
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
NARRATORS_PATH = ROOT / "config" / "narrators.json"
DEFAULT_ENV_PATH = ROOT / "scripts" / ".env"
KOKORO_SCRIPT = ROOT / "scripts" / "gerar_narracao_local.py"


class NarrationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def project_path(value: Path | str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def relative_or_absolute(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                continue
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            values[key] = value
    values.update({key: value for key, value in os.environ.items() if value})
    return values


def find_first(env: dict[str, str], names: list[str]) -> str | None:
    return next((env[name].strip() for name in names if env.get(name, "").strip()), None)


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_beats_markdown(text: str) -> list[dict[str, str]]:
    headings = list(re.finditer(r"(?m)^###\s+(B\d{3,})\b([^\r\n]*)$", text))
    beats: list[dict[str, str]] = []
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        block = text[match.end() : end]
        spoken = []
        for line in block.splitlines():
            quote = re.match(r"^>\s?(.*)$", line)
            if quote:
                spoken.append(quote.group(1).strip())
        narration = clean_text(" ".join(spoken))
        if narration:
            title = match.group(2).strip().lstrip("—-").strip()
            beats.append({"beat_id": match.group(1), "title": title, "text": narration})
    return beats


def select_beats(beats: list[dict[str, str]], selection: str | None) -> list[dict[str, str]]:
    if not selection:
        return beats
    ids = [item.strip().upper() for item in selection.split(",") if item.strip()]
    mapping = {beat["beat_id"]: beat for beat in beats}
    missing = [beat_id for beat_id in ids if beat_id not in mapping]
    if missing:
        raise NarrationError(f"Beat(s) não encontrado(s): {', '.join(missing)}")
    return [mapping[beat_id] for beat_id in ids]


def normalize_word(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in plain if char.isalnum())


def narrator_by_id(config: dict[str, Any], narrator_id: str) -> dict[str, Any]:
    for narrator in config.get("narrators", []):
        if narrator.get("id") == narrator_id:
            return narrator
    raise NarrationError(f"Narrador não configurado: {narrator_id}")


def read_pcm_wav(data: bytes) -> tuple[int, array]:
    try:
        with wave.open(io.BytesIO(data), "rb") as handle:
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
            sample_rate = handle.getframerate()
            compression = handle.getcomptype()
            frames = handle.readframes(handle.getnframes())
    except wave.Error as exc:
        raise NarrationError(f"Azure não retornou WAV PCM válido: {exc}") from exc
    if channels != 1 or sample_width != 2 or compression != "NONE":
        raise NarrationError(
            "Formato Azure inesperado; esperado PCM mono de 16 bits. "
            f"Recebido: channels={channels}, width={sample_width}, compression={compression}."
        )
    samples = array("h")
    samples.frombytes(frames)
    if sys.byteorder != "little":
        samples.byteswap()
    return sample_rate, samples


def write_pcm_wav(path: Path, sample_rate: int, samples: array) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = array("h", samples)
    if sys.byteorder != "little":
        payload.byteswap()
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(payload.tobytes())


def synthesize_azure(
    text: str,
    *,
    key: str,
    region: str,
    voice: str,
    language: str,
    output_format: str,
    delivery: dict[str, str],
) -> bytes:
    if not re.fullmatch(r"[a-z0-9-]+", region.casefold()):
        raise NarrationError("Região Azure inválida na configuração local.")
    prosody = {
        "rate": delivery.get("rate", "0%"),
        "pitch": delivery.get("pitch", "0%"),
        "volume": delivery.get("volume", "default"),
    }
    ssml = (
        f'<speak version="1.0" xml:lang="{escape(language)}">'
        f'<voice name="{escape(voice)}">'
        f'<prosody rate="{escape(prosody["rate"])}" pitch="{escape(prosody["pitch"])}" '
        f'volume="{escape(prosody["volume"])}">{escape(text)}</prosody>'
        "</voice></speak>"
    ).encode("utf-8")
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    request = urllib.request.Request(
        url,
        data=ssml,
        method="POST",
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml; charset=utf-8",
            "X-Microsoft-OutputFormat": output_format,
            "User-Agent": "capital-oculto-local-pipeline",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            if response.status != 200:
                raise NarrationError(f"Azure Speech retornou HTTP {response.status}.")
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read(512).decode("utf-8", errors="replace").strip()
        safe_detail = re.sub(r"[A-Za-z0-9+/=_-]{24,}", "[redacted]", detail)
        raise NarrationError(f"Azure Speech retornou HTTP {exc.code}: {safe_detail}") from exc
    except urllib.error.URLError as exc:
        raise NarrationError(f"Falha de rede ao acessar Azure Speech: {exc.reason}") from exc


def detect_speech_bounds(samples: array, sample_rate: int) -> tuple[int, int]:
    if not samples:
        raise NarrationError("Chunk Azure vazio.")
    peak = max(abs(sample) for sample in samples)
    if peak < 64:
        raise NarrationError("Chunk Azure sem sinal de voz detectável.")
    threshold = max(96, round(peak * 0.018))
    active = [index for index, sample in enumerate(samples) if abs(sample) >= threshold]
    if not active:
        raise NarrationError("Não foi possível detectar os limites de fala no WAV Azure.")
    padding = round(sample_rate * 0.025)
    return max(0, active[0] - padding), min(len(samples), active[-1] + padding + 1)


def token_weight(token: str) -> float:
    base = max(2, len(normalize_word(token)))
    if re.search(r"[.!?…][\"')\]]*$", token):
        return base + 3.0
    if re.search(r"[,;:][\"')\]]*$", token):
        return base + 1.4
    return float(base)


def align_words(
    text: str,
    samples: array,
    sample_rate: int,
    *,
    offset_seconds: float,
    global_index: int,
) -> tuple[list[dict[str, Any]], float, float]:
    tokens = re.findall(r"\S+", text)
    if not tokens:
        raise NarrationError("Beat sem palavras para alinhamento.")
    speech_first, speech_last = detect_speech_bounds(samples, sample_rate)
    speech_start = offset_seconds + speech_first / sample_rate
    speech_end = offset_seconds + speech_last / sample_rate
    available = speech_end - speech_start
    weights = [token_weight(token) for token in tokens]
    total_weight = sum(weights)
    cursor = speech_start
    words: list[dict[str, Any]] = []
    for beat_word_index, (token, weight) in enumerate(zip(tokens, weights), start=1):
        duration = available * weight / total_weight
        end = speech_end if beat_word_index == len(tokens) else cursor + duration
        words.append(
            {
                "index": global_index + beat_word_index - 1,
                "beat_word_index": beat_word_index,
                "text": token,
                "normalized": normalize_word(token),
                "start": round(cursor, 4),
                "end": round(end, 4),
            }
        )
        cursor = end
    return words, round(speech_start, 4), round(speech_end, 4)


def process_voice(samples: array, sample_rate: int) -> tuple[array, dict[str, Any]]:
    highpass_hz = 70.0
    compressor_threshold_dbfs = -18.0
    compressor_ratio = 2.5
    target_peak_dbfs = -1.0
    limiter_dbfs = -0.8

    rc = 1.0 / (2.0 * math.pi * highpass_hz)
    dt = 1.0 / sample_rate
    alpha = rc / (rc + dt)
    previous_input = 0.0
    previous_output = 0.0
    threshold = 32767.0 * (10.0 ** (compressor_threshold_dbfs / 20.0))
    filtered: list[float] = []
    for sample in samples:
        value = float(sample)
        highpassed = alpha * (previous_output + value - previous_input)
        previous_input = value
        previous_output = highpassed
        magnitude = abs(highpassed)
        if magnitude > threshold:
            magnitude = threshold + (magnitude - threshold) / compressor_ratio
            highpassed = math.copysign(magnitude, highpassed)
        filtered.append(highpassed)

    peak = max((abs(value) for value in filtered), default=1.0)
    target_peak = 32767.0 * (10.0 ** (target_peak_dbfs / 20.0))
    gain = min(4.0, target_peak / max(1.0, peak))
    limiter = 32767.0 * (10.0 ** (limiter_dbfs / 20.0))
    processed = array(
        "h",
        (
            round(max(-limiter, min(limiter, value * gain)))
            for value in filtered
        ),
    )
    parameters = {
        "implementation": "python_stdlib_deterministic_pcm",
        "highpass_hz": highpass_hz,
        "compressor_threshold_dbfs": compressor_threshold_dbfs,
        "compressor_ratio": compressor_ratio,
        "peak_normalization_dbfs": target_peak_dbfs,
        "limiter_ceiling_dbfs": limiter_dbfs,
        "duration_preserved": True,
    }
    return processed, parameters


def run_kokoro(args: argparse.Namespace, narrator: dict[str, Any]) -> int:
    fallback = narrator.get("fallback", {})
    if fallback.get("provider") != "kokoro":
        raise NarrationError("Narrador sem fallback Kokoro configurado.")
    command = [
        sys.executable,
        str(KOKORO_SCRIPT),
        "--entrada",
        str(args.entrada),
        "--saida",
        str(args.saida),
        "--voz",
        fallback.get("voice_alias", "santa"),
    ]
    if args.beats:
        command.extend(["--beats", args.beats])
    if args.timing_json:
        command.extend(["--timing-json", str(args.timing_json)])
    if args.episodio_id:
        command.extend(["--episodio-id", args.episodio_id])
    return subprocess.call(command, cwd=ROOT)


def build_parser(default_provider: str, default_narrator: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", required=True, type=Path, help="Roteiro Markdown com beats.")
    parser.add_argument("--beats", required=True, help="IDs de beat separados por vírgula.")
    parser.add_argument("--saida", required=True, type=Path, help="WAV processado de destino.")
    parser.add_argument("--timing-json", required=True, type=Path, help="Contrato de timing gerado.")
    parser.add_argument("--raw-dir", type=Path, help="Diretório para WAVs brutos por beat.")
    parser.add_argument("--raw-combined", type=Path, help="WAV bruto concatenado.")
    parser.add_argument("--episodio-id", default="CO-001")
    parser.add_argument("--narrator", default=default_narrator)
    parser.add_argument("--provider", choices=("azure", "kokoro"), default=default_provider)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV_PATH)
    parser.add_argument("--pause-ms", type=int, default=180)
    parser.add_argument("--no-processing", action="store_true")
    return parser


def main() -> int:
    config = load_json(NARRATORS_PATH)
    env_preview = load_env(DEFAULT_ENV_PATH)
    default_narrator_id = config["default_narrator"]
    default_narrator = narrator_by_id(config, default_narrator_id)
    default_provider = env_preview.get("TTS_PROVIDER", default_narrator["provider"]).casefold()
    args = build_parser(default_provider, default_narrator_id).parse_args()
    narrator = narrator_by_id(config, args.narrator)

    args.entrada = project_path(args.entrada)
    args.saida = project_path(args.saida)
    args.timing_json = project_path(args.timing_json)
    args.env_file = project_path(args.env_file)
    args.raw_dir = project_path(args.raw_dir) if args.raw_dir else args.saida.parent / "raw"
    args.raw_combined = (
        project_path(args.raw_combined)
        if args.raw_combined
        else args.raw_dir / "narration_raw.wav"
    )
    if not args.entrada.is_file():
        raise NarrationError(f"Roteiro não encontrado: {args.entrada}")
    if args.pause_ms < 0 or args.pause_ms > 2000:
        raise NarrationError("--pause-ms deve ficar entre 0 e 2000.")
    if args.provider == "kokoro":
        return run_kokoro(args, narrator)

    env = load_env(args.env_file)
    azure_config = narrator["azure"]
    key = find_first(env, azure_config["key_names"])
    region = find_first(env, azure_config["region_names"])
    if not key or not region:
        raise NarrationError(
            "Credenciais Azure ausentes. Configure uma chave e uma região em scripts/.env."
        )
    configured_voice = env.get(azure_config.get("voice_name_override", ""), "").strip()
    voice = configured_voice or narrator["voice"]
    if voice != narrator["voice"]:
        raise NarrationError(
            f"A voz configurada ({voice}) diverge da voz aprovada ({narrator['voice']})."
        )

    source = args.entrada.read_text(encoding="utf-8-sig")
    beats = select_beats(extract_beats_markdown(source), args.beats)
    if not beats:
        raise NarrationError("Nenhum beat selecionado para síntese.")
    text = clean_text("\n\n".join(beat["text"] for beat in beats))
    args.raw_dir.mkdir(parents=True, exist_ok=True)

    combined = array("h")
    timing_beats: list[dict[str, Any]] = []
    timing_pauses: list[dict[str, Any]] = []
    sample_rate: int | None = None
    cursor_samples = 0
    global_index = 1
    print(f"AZURE_CONFIG_FOUND=true | provider=azure | voice={voice}")
    for index, beat in enumerate(beats, start=1):
        audio_bytes = synthesize_azure(
            beat["text"],
            key=key,
            region=region,
            voice=voice,
            language=narrator["language"],
            output_format=azure_config["output_format"],
            delivery=narrator["delivery"],
        )
        current_rate, samples = read_pcm_wav(audio_bytes)
        if sample_rate is None:
            sample_rate = current_rate
        elif current_rate != sample_rate:
            raise NarrationError("Azure retornou taxas de amostragem diferentes entre beats.")
        raw_path = args.raw_dir / f"{beat['beat_id'].lower()}_azure_antonio.wav"
        write_pcm_wav(raw_path, sample_rate, samples)
        offset = cursor_samples / sample_rate
        words, speech_start, speech_end = align_words(
            beat["text"],
            samples,
            sample_rate,
            offset_seconds=offset,
            global_index=global_index,
        )
        global_index += len(words)
        combined.extend(samples)
        cursor_samples += len(samples)
        timing_beats.append(
            {
                "beat_id": beat["beat_id"],
                "title": beat["title"],
                "text": beat["text"],
                "start": round(offset, 4),
                "speech_start": speech_start,
                "speech_end": speech_end,
                "end": round(cursor_samples / sample_rate, 4),
                "raw_audio_file": relative_or_absolute(raw_path),
                "raw_audio_sha256": sha256(raw_path),
                "words": words,
            }
        )
        print(f"  [{index}/{len(beats)}] {beat['beat_id']} — WAV Azure recebido e medido")
        if index < len(beats):
            pause_start = cursor_samples / sample_rate
            pause_samples = round(sample_rate * args.pause_ms / 1000)
            combined.extend(array("h", [0]) * pause_samples)
            cursor_samples += pause_samples
            timing_pauses.append(
                {
                    "after_beat_id": beat["beat_id"],
                    "start": round(pause_start, 4),
                    "end": round(cursor_samples / sample_rate, 4),
                    "duration_ms": args.pause_ms,
                    "source": "cli.pause_ms",
                }
            )

    if sample_rate is None:
        raise NarrationError("Azure não produziu áudio.")
    write_pcm_wav(args.raw_combined, sample_rate, combined)
    if args.no_processing:
        processed = array("h", combined)
        processing = {"implementation": "none", "duration_preserved": True}
    else:
        processed, processing = process_voice(combined, sample_rate)
    write_pcm_wav(args.saida, sample_rate, processed)
    duration = len(processed) / sample_rate
    contract = {
        "schema_version": "1.0",
        "episode_id": args.episodio_id,
        "scope": "selected_beats",
        "provider": "azure_speech_rest",
        "narrator_id": narrator["id"],
        "voice": voice,
        "language": narrator["language"],
        "delivery": narrator["delivery"],
        "timing_method": "azure_rest_real_chunk_duration_detected_speech_weighted_alignment",
        "timing_level": "beat_duration_native_word_boundaries_deterministic",
        "timing_limitations": (
            "O endpoint REST síncrono retorna o WAV, mas não word boundaries. "
            "Os limites de cada beat e de fala vêm do áudio real; palavras são distribuídas "
            "deterministicamente dentro do sinal detectado por peso textual."
        ),
        "source_file": relative_or_absolute(args.entrada),
        "source_sha256": sha256(args.entrada),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "raw_audio_file": relative_or_absolute(args.raw_combined),
        "raw_audio_sha256": sha256(args.raw_combined),
        "audio_file": relative_or_absolute(args.saida),
        "audio_sha256": sha256(args.saida),
        "sample_rate": sample_rate,
        "sample_width_bits": 16,
        "channels": 1,
        "duration_seconds": round(duration, 4),
        "audio_processing": processing,
        "azure_config_found": True,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "beats": timing_beats,
        "pauses": timing_pauses,
    }
    args.timing_json.parent.mkdir(parents=True, exist_ok=True)
    args.timing_json.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Concluído: {relative_or_absolute(args.saida)}")
    print(f"Timing: {relative_or_absolute(args.timing_json)}")
    print(f"Duração real: {duration:.3f}s | Taxa: {sample_rate} Hz")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NarrationError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
