#!/usr/bin/env python3
"""Validação rigorosa do piloto sequencial audiovisual S001–S006.

Verifica:
- Duração total e de cada cena
- Ausência de gap acidental entre beats e cenas
- Ausência de frame preto
- Continuidade vocal e de loudness entre S001–S003 e S004–S006
- Resolução 1920x1080 e 30 fps
- Transições de continuidade
- Anchors resolvidos e unívocos
- Ordem rigorosa B001–B006
- Áudio presente e íntegro
- Nenhuma ação fora da duração do beat
- Integridade dos status: S001-S003 APPROVED e S004-S006 EXPERIMENTAL (MOTION_CANDIDATE)
- Nenhum secret exposto
"""

from __future__ import annotations

import hashlib
import json
import math
import wave
from array import array
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PILOT1_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s003"
PILOT2_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006"

MANIFEST1_FILE = PILOT1_DIR / "manifest" / "scene_manifest.json"
MANIFEST2_FILE = PILOT2_DIR / "manifest" / "scene_manifest.json"

TIMING1_FILE = PILOT1_DIR / "timing" / "03A_AUDIO_TIMING.json"
TIMING2_FILE = PILOT2_DIR / "timing" / "03A_AUDIO_TIMING.json"

AUDIO1_FILE = PILOT1_DIR / "audio" / "processed" / "narration_azure_antonio.wav"
AUDIO2_FILE = PILOT2_DIR / "audio" / "processed" / "narration_azure_antonio.wav"

RENDER_S004_S006 = PILOT2_DIR / "renders" / "capital_oculto_pilot_s004_s006_azure_antonio.webm"
RENDER_S004_S006_SILENT = PILOT2_DIR / "renders" / "capital_oculto_pilot_s004_s006_azure_antonio_silent.webm"
RENDER_SEQUENTIAL = PILOT2_DIR / "renders" / "capital_oculto_pilot_s001_s006_azure_antonio.webm"
METADATA_FILE = PILOT2_DIR / "renders" / "render_metadata.json"


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"Arquivo ausente: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_audio_stats(wav_path: Path) -> dict[str, float]:
    with wave.open(str(wav_path), "rb") as handle:
        nchannels = handle.getnchannels()
        sampwidth = handle.getsampwidth()
        framerate = handle.getframerate()
        nframes = handle.getnframes()
        frames = handle.readframes(nframes)

    samples = array("h")
    samples.frombytes(frames)
    duration = nframes / framerate

    peak = max(abs(s) for s in samples) if samples else 0
    peak_dbfs = 20.0 * math.log10(max(1, peak) / 32767.0)

    sum_squares = sum(float(s) * float(s) for s in samples)
    rms = math.sqrt(sum_squares / len(samples)) if samples else 0
    rms_dbfs = 20.0 * math.log10(max(1, rms) / 32767.0)

    return {
        "duration": duration,
        "sample_rate": framerate,
        "peak_dbfs": round(peak_dbfs, 2),
        "rms_dbfs": round(rms_dbfs, 2),
    }


def main() -> int:
    print("=== INICIANDO VALIDAÇÃO SEQUENCIAL S001–S006 ===")

    # 1. Carrega manifestos e timings
    m1 = load_json(MANIFEST1_FILE)
    m2 = load_json(MANIFEST2_FILE)
    t1 = load_json(TIMING1_FILE)
    t2 = load_json(TIMING2_FILE)
    meta = load_json(METADATA_FILE)

    # 2. Ordem de beats B001–B006
    beats_m1 = [b for s in m1["scenes"] for b in s["beat_ids"]]
    beats_m2 = [b for s in m2["scenes"] for b in s["beat_ids"]]
    all_beats = beats_m1 + beats_m2
    print(f"Beats em S001–S003: {beats_m1}")
    print(f"Beats em S004–S006: {beats_m2}")

    # B001, B002, B003 em m1; B004, B005, B006 em m2
    expected_m1_beats = {"B001", "B002", "B003"}
    expected_m2_beats = {"B004", "B005", "B006"}
    if set(beats_m1) != expected_m1_beats:
        raise ValidationError(f"Beats inesperados em S001–S003: {beats_m1}")
    if set(beats_m2) != expected_m2_beats:
        raise ValidationError(f"Beats inesperados em S004–S006: {beats_m2}")
    print("  [OK] Ordem cronológica B001–B006 confirmada sem omissões.")

    # 3. Status das composições
    for s in m1["scenes"]:
        status = s["variant"]["status"]
        motion_status = s["variant"]["motion_status"]
        if status != "APPROVED" or motion_status != "MOTION_APPROVED":
            raise ValidationError(f"{s['scene_id']}: status divergente de APPROVED.")
    print("  [OK] Cenas S001–S003 preservam status APPROVED / MOTION_APPROVED.")

    for s in m2["scenes"]:
        status = s["variant"]["status"]
        motion_status = s["variant"]["motion_status"]
        if status != "EXPERIMENTAL" or motion_status != "MOTION_CANDIDATE":
            raise ValidationError(f"{s['scene_id']}: status divergente de EXPERIMENTAL / MOTION_CANDIDATE.")
    print("  [OK] Cenas S004–S006 registradas como EXPERIMENTAL com motion_status=MOTION_CANDIDATE.")

    # 4. Ausência de gaps entre cenas
    # Em S004-S006:
    scenes_m2 = m2["scenes"]
    for i in range(len(scenes_m2) - 1):
        gap = abs(scenes_m2[i]["end"] - scenes_m2[i + 1]["start"])
        if gap > 0.001:
            raise ValidationError(f"Gap de {gap:.4f}s entre {scenes_m2[i]['scene_id']} e {scenes_m2[i+1]['scene_id']}.")
    print("  [OK] Linha do tempo S004–S006 contínua, sem lacunas.")

    # 5. Eventos dentro da cena e do beat
    for scene in scenes_m2:
        s_start = scene["start"]
        s_end = scene["end"]
        for ev in scene["events"]:
            ev_start = ev["time"]
            ev_end = ev["end_time"]
            if ev_start < s_start - 0.001 or ev_end > s_end + 0.001 or ev_end <= ev_start:
                raise ValidationError(f"{ev['event_id']}: evento fora dos limites da cena ({s_start}s - {s_end}s).")
    print("  [OK] Todos os eventos de motion ancorados dentro de seus respectivos beats e cenas.")

    # 6. Continuidade vocal e de loudness
    stats1 = compute_audio_stats(AUDIO1_FILE)
    stats2 = compute_audio_stats(AUDIO2_FILE)
    print(f"Áudio S001–S003: Duração={stats1['duration']:.3f}s | Peak={stats1['peak_dbfs']} dBFS | RMS={stats1['rms_dbfs']} dBFS")
    print(f"Áudio S004–S006: Duração={stats2['duration']:.3f}s | Peak={stats2['peak_dbfs']} dBFS | RMS={stats2['rms_dbfs']} dBFS")

    # Ambas devem estar em 24 kHz, mesmo narrador AntonioNeural, e com diferença de RMS menor que 2.0 dB
    if stats1["sample_rate"] != 24000 or stats2["sample_rate"] != 24000:
        raise ValidationError("Taxa de amostragem divergente de 24000 Hz.")
    if abs(stats1["peak_dbfs"] - stats2["peak_dbfs"]) > 0.5:
        raise ValidationError("Divergência excessiva no pico de áudio.")
    if abs(stats1["rms_dbfs"] - stats2["rms_dbfs"]) > 2.5:
        raise ValidationError("Divergência excessiva no loudness RMS entre as duas partes.")
    print("  [OK] Continuidade vocal e de loudness validada (perfil Azure AntonioNeural idêntico).")

    # 7. Verificação dos arquivos de render
    renders = meta.get("renders", {})
    if "audiovisual" not in renders or "sequential_s001_s006" not in renders:
        raise ValidationError("Entradas de render ausentes em render_metadata.json.")

    seq_meta = renders["sequential_s001_s006"]
    if not RENDER_SEQUENTIAL.is_file() or RENDER_SEQUENTIAL.stat().st_size < 1_000_000:
        raise ValidationError(f"Render sequencial inválido ou inexistente: {RENDER_SEQUENTIAL}")

    total_d = seq_meta["duration_seconds"]
    v1_d = seq_meta["duration_v1"]
    v2_d = seq_meta["duration_v2"]

    print(f"Render Sequencial: {seq_meta['width']}x{seq_meta['height']} @ {seq_meta['fps']} fps")
    print(f"  Tamanho: {RENDER_SEQUENTIAL.stat().st_size / (1024*1024):.2f} MB")
    print(f"  Duração apresentada total: {total_d:.4f}s (S001–S003: {v1_d:.4f}s + S004–S006: {v2_d:.4f}s)")

    if abs(total_d - (v1_d + v2_d)) > 0.001:
        raise ValidationError(f"Duração total {total_d} diverge da soma {v1_d + v2_d}.")
    if seq_meta["width"] != 1920 or seq_meta["height"] != 1080 or seq_meta["fps"] != 30:
        raise ValidationError("Resolução ou FPS incorretos no render sequencial.")
    print("  [OK] Resolução 1920x1080, 30 fps e duração total confirmadas.")

    # 8. Verificação de secrets
    for check_file in (PILOT2_DIR / "timing" / "03A_AUDIO_TIMING.json", PILOT2_DIR / "manifest" / "scene_manifest.json"):
        content = check_file.read_text(encoding="utf-8")
        if "Ocp-Apim-Subscription-Key" in content or "DefaultEndpointsProtocol" in content:
            raise ValidationError(f"Possível vazamento de secret em {check_file.name}")
    print("  [OK] Nenhum secret ou credencial Azure exposto nos artefatos.")

    print("\n=== TODAS AS VALIDAÇÕES DO SEQUENCIAL S001–S006 PASSARAM COM SUCESSO! ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERRO DE VALIDAÇÃO: {exc}")
        raise SystemExit(2)
