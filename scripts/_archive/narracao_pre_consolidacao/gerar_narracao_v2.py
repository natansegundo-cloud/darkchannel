#!/usr/bin/env python3
"""Síntese de voz V2 com Voice Pacing Contract para B001–B006.

Implementa:
- 1 beat = 1 request SSML contextual com breaks estruturais
- Rate fixo de -7%
- Pausas editoriais por intenção retórica e pontuação
- Concatenação temporal determinística com zero speech overlap
- Cálculo de words_per_second por beat com warnings de densidade
- Pós-processamento de voz idêntico (highpass, compressor, peak -1dBFS, limiter -0.8dBFS)
- Salva artefatos com sufixo _v2 preservando os originais
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
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
DEFAULT_ENV_PATH = ROOT / "scripts" / ".env"
NARRATORS_PATH = ROOT / "config" / "narrators.json"
MOTION_CONTRACT_PATH = ROOT / "config" / "motion_contract.json"
OUTPUT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006"

BEATS_DATA = [
    {
        "beat_id": "B001",
        "title": "A notícia do aumento",
        "raw_text": "Você recebe a mensagem: seu salário aumentou.",
        # Break após "mensagem:" (mudança pequena de oração)
        "ssml_body": 'Você recebe a mensagem:<break time="160ms"/> seu salário aumentou.',
        "pause_after_ms": 400,
    },
    {
        "beat_id": "B002",
        "title": "A folga dura pouco",
        "raw_text": "Por algumas semanas, finalmente sobra. Três meses depois, você está outra vez conferindo o saldo antes de gastar vinte reais.",
        # Breaks: vírgula lógica (120ms), fim sentença (340ms), virada temporal (420ms)
        "ssml_body": 'Por algumas semanas,<break time="120ms"/> finalmente sobra.<break time="340ms"/> Três meses depois,<break time="420ms"/> você está outra vez conferindo o saldo antes de gastar vinte reais.',
        "pause_after_ms": 400,
    },
    {
        "beat_id": "B003",
        "title": "A contradição",
        "raw_text": "O aumento era real. Então por que a folga sumiu?",
        # Break: fim de afirmação antes de pergunta retórica (480ms)
        "ssml_body": 'O aumento era real.<break time="480ms"/> Então por que a folga sumiu?',
        "pause_after_ms": 450,
    },
    {
        "beat_id": "B004",
        "title": "Sem compra absurda",
        "raw_text": "Você não precisa ter feito nenhuma compra absurda.",
        "ssml_body": "Você não precisa ter feito nenhuma compra absurda.",
        "pause_after_ms": 400,
    },
    {
        "beat_id": "B005",
        "title": "O mapa das três forças",
        "raw_text": "Mesmo assim, três coisas podem mudar junto com a renda: o que parece normal, com quem você se compara e quantas despesas passam a contar com aquele dinheiro. Quando as três se movem ao mesmo tempo, um aumento real pode ficar quase invisível.",
        # Breaks em enumeração e transição para conclusão
        "ssml_body": 'Mesmo assim,<break time="120ms"/> três coisas podem mudar junto com a renda:<break time="220ms"/> o que parece normal,<break time="140ms"/> com quem você se compara<break time="120ms"/> e quantas despesas passam a contar com aquele dinheiro.<break time="360ms"/> Quando as três se movem ao mesmo tempo,<break time="180ms"/> um aumento real pode ficar quase invisível.',
        "pause_after_ms": 450,
    },
    {
        "beat_id": "B006",
        "title": "A primeira peça",
        "raw_text": "A primeira peça é uma habilidade útil do cérebro que, neste caso, parece uma pequena traição: adaptação.",
        # Break antes da revelação de "adaptação" (500ms)
        "ssml_body": 'A primeira peça é uma habilidade útil do cérebro que,<break time="120ms"/> neste caso,<break time="140ms"/> parece uma pequena traição:<break time="500ms"/> adaptação.',
        "pause_after_ms": 400,
    },
]


class NarrationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.is_file():
        for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            values[key] = value
    values.update({key: value for key, value in os.environ.items() if value})
    return values


def normalize_word(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in plain if char.isalnum())


def read_pcm_wav(data: bytes) -> tuple[int, array]:
    with wave.open(io.BytesIO(data), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        sample_rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
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


def synthesize_azure_ssml(
    ssml_body: str,
    *,
    key: str,
    region: str,
    voice: str,
    language: str,
    rate: str,
    output_format: str,
) -> bytes:
    ssml = (
        f'<speak version="1.0" xml:lang="{escape(language)}">'
        f'<voice name="{escape(voice)}">'
        f'<prosody rate="{escape(rate)}">{ssml_body}</prosody>'
        f"</voice></speak>"
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
            "User-Agent": "capital-oculto-pipeline-v2",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            if response.status != 200:
                raise NarrationError(f"Azure Speech retornou HTTP {response.status}.")
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read(512).decode("utf-8", errors="replace").strip()
        raise NarrationError(f"Azure Speech retornou HTTP {exc.code}: {detail}") from exc
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
        (round(max(-limiter, min(limiter, value * gain))) for value in filtered),
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


def main() -> int:
    env = load_env(DEFAULT_ENV_PATH)
    narrators = load_json(NARRATORS_PATH)
    default_narrator = narrators["narrators"][0]
    motion_contract = load_json(MOTION_CONTRACT_PATH)

    voice_cfg = motion_contract["voice_pacing"]
    rate = voice_cfg["rate"]  # -7%
    voice = voice_cfg["voice"]  # pt-BR-AntonioNeural

    key = env.get("AZURE_SPEECH_KEY") or env.get("SPEECH_KEY")
    region = env.get("AZURE_SPEECH_REGION") or env.get("SPEECH_REGION")
    if not key or not region:
        raise NarrationError("Credenciais Azure ausentes em scripts/.env.")

    raw_dir = OUTPUT_DIR / "audio" / "raw_v2"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_combined_path = raw_dir / "narration_raw_v2.wav"
    processed_path = OUTPUT_DIR / "audio" / "processed" / "narration_azure_antonio_v2.wav"
    timing_path = OUTPUT_DIR / "timing" / "03A_AUDIO_TIMING_v2.json"

    print(f"SÍNTESE V2 — Azure Speech | voz={voice} | rate={rate}")

    combined = array("h")
    timing_beats: list[dict[str, Any]] = []
    timing_pauses: list[dict[str, Any]] = []
    sample_rate: int | None = None
    cursor_samples = 0
    global_index = 1
    warnings: list[str] = []

    for index, beat_info in enumerate(BEATS_DATA, start=1):
        beat_id = beat_info["beat_id"]
        raw_text = beat_info["raw_text"]
        ssml_body = beat_info["ssml_body"]
        pause_after_ms = beat_info["pause_after_ms"]

        audio_bytes = synthesize_azure_ssml(
            ssml_body,
            key=key,
            region=region,
            voice=voice,
            language="pt-BR",
            rate=rate,
            output_format="riff-24khz-16bit-mono-pcm",
        )
        current_rate, samples = read_pcm_wav(audio_bytes)
        if sample_rate is None:
            sample_rate = current_rate
        elif current_rate != sample_rate:
            raise NarrationError("Taxa de amostragem divergente entre beats.")

        raw_path = raw_dir / f"{beat_id.lower()}_azure_antonio_v2.wav"
        write_pcm_wav(raw_path, sample_rate, samples)

        offset = cursor_samples / sample_rate
        words, speech_start, speech_end = align_words(
            raw_text,
            samples,
            sample_rate,
            offset_seconds=offset,
            global_index=global_index,
        )
        global_index += len(words)
        beat_duration = len(samples) / sample_rate
        words_count = len(words)
        active_speech_duration = speech_end - speech_start
        words_per_sec = round(words_count / max(0.1, active_speech_duration), 2)

        density_warning = False
        if words_per_sec > voice_cfg["speech_density"]["warning_threshold_words_per_sec"]:
            density_warning = True
            warn_msg = f"VOICE_DENSITY_WARNING em {beat_id}: {words_per_sec} palavras/s (> {voice_cfg['speech_density']['warning_threshold_words_per_sec']})"
            warnings.append(warn_msg)
            print(f"  [ALERTA] {warn_msg}")

        combined.extend(samples)
        cursor_samples += len(samples)

        timing_beats.append(
            {
                "beat_id": beat_id,
                "title": beat_info["title"],
                "text": raw_text,
                "start": round(offset, 4),
                "speech_start": speech_start,
                "speech_end": speech_end,
                "end": round(cursor_samples / sample_rate, 4),
                "duration_seconds": round(beat_duration, 4),
                "words_count": words_count,
                "words_per_second": words_per_sec,
                "voice_density_warning": density_warning,
                "raw_audio_file": raw_path.relative_to(ROOT).as_posix(),
                "raw_audio_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                "words": words,
            }
        )

        print(
            f"  [{index}/{len(BEATS_DATA)}] {beat_id} recebido: dur={beat_duration:.2f}s | "
            f"fala={active_speech_duration:.2f}s | {words_per_sec} pal/s"
        )

        # Pausa temporal entre beats (garante zero speech overlap)
        if index < len(BEATS_DATA):
            pause_start = cursor_samples / sample_rate
            pause_samples = round(sample_rate * pause_after_ms / 1000)
            combined.extend(array("h", [0]) * pause_samples)
            cursor_samples += pause_samples
            timing_pauses.append(
                {
                    "after_beat_id": beat_id,
                    "start": round(pause_start, 4),
                    "end": round(cursor_samples / sample_rate, 4),
                    "duration_ms": pause_after_ms,
                    "source": "motion_contract.voice_pacing.pauses_ms.beat_end",
                }
            )

    if sample_rate is None:
        raise NarrationError("Nenhum áudio recebido.")

    write_pcm_wav(raw_combined_path, sample_rate, combined)
    processed, processing = process_voice(combined, sample_rate)
    write_pcm_wav(processed_path, sample_rate, processed)

    total_duration = len(processed) / sample_rate

    # Validação anti-atropelamento (speech overlap = 0)
    speech_overlap_count = 0
    for i in range(len(timing_beats) - 1):
        b_curr = timing_beats[i]
        b_next = timing_beats[i + 1]
        if b_curr["speech_end"] > b_next["speech_start"]:
            speech_overlap_count += 1
            print(f"  [ERRO] Speech overlap entre {b_curr['beat_id']} e {b_next['beat_id']}!")

    contract_timing = {
        "schema_version": "2.0",
        "episode_id": "CO-001",
        "scope": "pilot_s001_s006_v2",
        "provider": "azure_speech_rest",
        "voice": voice,
        "language": "pt-BR",
        "delivery": {"rate": rate, "pitch": "0%", "volume": "default"},
        "pacing_contract": "CO_MOTION_CONTRACT_V1",
        "anti_atropelamento": {
            "speech_overlap": speech_overlap_count,
            "overlap_allowed": False,
            "rule_passed": speech_overlap_count == 0,
        },
        "voice_density_warnings": warnings,
        "raw_audio_file": raw_combined_path.relative_to(ROOT).as_posix(),
        "raw_audio_sha256": hashlib.sha256(raw_combined_path.read_bytes()).hexdigest(),
        "audio_file": processed_path.relative_to(ROOT).as_posix(),
        "audio_sha256": hashlib.sha256(processed_path.read_bytes()).hexdigest(),
        "sample_rate": sample_rate,
        "channels": 1,
        "duration_seconds": round(total_duration, 4),
        "audio_processing": processing,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "beats": timing_beats,
        "pauses": timing_pauses,
    }

    timing_path.parent.mkdir(parents=True, exist_ok=True)
    timing_path.write_text(
        json.dumps(contract_timing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(f"\nSÍNTESE V2 CONCLUÍDA:")
    print(f"  WAV: {processed_path.relative_to(ROOT)}")
    print(f"  Timing: {timing_path.relative_to(ROOT)}")
    print(f"  Duração total: {total_duration:.3f}s")
    print(f"  Speech overlap: {speech_overlap_count} (regra anti-atropelamento: {'PASSOU' if speech_overlap_count == 0 else 'FALHOU'})")
    print(f"  Warnings de densidade: {len(warnings)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (NarrationError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
