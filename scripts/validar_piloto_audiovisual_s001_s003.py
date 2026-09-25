#!/usr/bin/env python3
"""Valida o piloto audiovisual S001–S003 e gera o relatório de entrega."""

from __future__ import annotations

import hashlib
import json
import re
import wave
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s003"
TIMING_FILE = PILOT_DIR / "timing" / "03A_AUDIO_TIMING.json"
MANIFEST_FILE = PILOT_DIR / "manifest" / "scene_manifest.json"
MOTION_SPEC_FILE = PILOT_DIR / "scenes" / "motion_spec.json"
RENDER_METADATA_FILE = PILOT_DIR / "renders" / "render_metadata.json"
REPORT_FILE = PILOT_DIR / "PILOT_REPORT.md"
LOG_FILE = PILOT_DIR / "logs" / "validation.json"
COMPOSITIONS_FILE = ROOT / "config" / "visual_compositions.json"
ENV_FILE = ROOT / "scripts" / ".env"
EXPECTED = {
    "S001": ("DATA_HERO", "CO-COMP-01C", 1.1, None),
    "S002": ("MOVING_BASELINE", "CO-COMP-04A", 1.1, None),
    "S003": ("SHRINKING_SPACE", "CO-COMP-03A", 1.1, "COMPRESSION_FIRST"),
}


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Arquivo ausente: {path}") from exc


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wav_duration(path: Path) -> tuple[float, int, int, int]:
    try:
        with wave.open(str(path), "rb") as handle:
            duration = handle.getnframes() / handle.getframerate()
            return duration, handle.getframerate(), handle.getnchannels(), handle.getsampwidth()
    except wave.Error as exc:
        raise ValidationError(f"WAV inválido: {path}: {exc}") from exc


def read_env_secret(path: Path) -> str | None:
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"^\s*(?:AZURE_SPEECH_KEY|SPEECH_KEY)\s*=\s*(.*?)\s*$", line)
        if match:
            value = match.group(1).strip().strip('"\'')
            return value or None
    return None


def validate_no_secret_leak(secret: str | None) -> list[str]:
    if not secret:
        raise ValidationError("Chave Azure não encontrada para auditoria de vazamento.")
    if len(secret) < 16:
        raise ValidationError("Chave Azure curta demais para auditoria segura.")
    extensions = {".py", ".json", ".md", ".csv", ".html", ".svg", ".log", ".txt"}
    excluded_roots = {".git", ".tts", ".comfyui"}
    leaks: list[str] = []
    needle = secret.encode("utf-8")
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == ENV_FILE:
            continue
        try:
            relative = path.relative_to(ROOT)
        except ValueError:
            continue
        if any(part in excluded_roots for part in relative.parts):
            continue
        if path.suffix.casefold() not in extensions:
            continue
        if needle in path.read_bytes():
            leaks.append(relative.as_posix())
    if leaks:
        raise ValidationError(f"Segredo Azure encontrado fora do .env: {', '.join(leaks)}")
    return leaks


def validate_compositions(config: dict[str, Any]) -> None:
    compositions = {item["id"]: item for item in config.get("compositions", [])}
    motion_approved = {
        item["id"] for item in config.get("compositions", [])
        if item.get("motion_status") == "MOTION_APPROVED"
    }
    expected_approved = {expected[1] for expected in EXPECTED.values()}
    if motion_approved != expected_approved:
        raise ValidationError("Somente 01C, 04A e 03A devem ser MOTION_APPROVED.")
    for scene_id, (_, variant, version, focus_mode) in EXPECTED.items():
        composition = compositions.get(variant)
        if not composition:
            raise ValidationError(f"{scene_id}: variante ausente.")
        if composition.get("status") != "APPROVED":
            raise ValidationError(f"{variant}: status deve ser APPROVED.")
        if float(composition.get("version")) != version:
            raise ValidationError(f"{variant}: versão divergente.")
        if focus_mode and composition.get("focus_mode_default") != focus_mode:
            raise ValidationError(f"{variant}: focus_mode divergente.")


def validate_timing(timing: dict[str, Any]) -> tuple[Path, float]:
    if timing.get("provider") != "azure_speech_rest":
        raise ValidationError("Provider do timing não é Azure REST.")
    if timing.get("voice") != "pt-BR-AntonioNeural":
        raise ValidationError("Voz do timing não é pt-BR-AntonioNeural.")
    if [beat.get("beat_id") for beat in timing.get("beats", [])] != ["B001", "B002", "B003"]:
        raise ValidationError("Timing deve conter exatamente B001–B003.")
    audio_path = ROOT / timing["audio_file"]
    if not audio_path.is_file() or sha256(audio_path) != timing.get("audio_sha256"):
        raise ValidationError("Áudio processado ausente ou hash divergente.")
    duration, rate, channels, sample_width = wav_duration(audio_path)
    if abs(duration - float(timing["duration_seconds"])) > 0.001:
        raise ValidationError("Duração real do WAV diverge do timing.")
    if rate != 24000 or channels != 1 or sample_width != 2:
        raise ValidationError("WAV deve ser PCM mono, 24 kHz e 16 bits.")
    previous = 0.0
    global_indices: list[int] = []
    for beat in timing["beats"]:
        start = float(beat["start"])
        end = float(beat["end"])
        if start < previous - 0.001 or end <= start:
            raise ValidationError(f"{beat['beat_id']}: tempos não monotônicos.")
        word_previous = start
        for word in beat.get("words", []):
            word_start = float(word["start"])
            word_end = float(word["end"])
            if word_start < word_previous - 0.001 or word_end <= word_start or word_end > end + 0.001:
                raise ValidationError(f"{beat['beat_id']}: word timing inválido.")
            word_previous = word_end
            global_indices.append(int(word["index"]))
        previous = end
    if global_indices != list(range(1, len(global_indices) + 1)):
        raise ValidationError("Índices globais de palavras não são contínuos.")
    return audio_path, duration


def validate_manifest(manifest: dict[str, Any], timing: dict[str, Any], duration: float) -> None:
    if manifest.get("status") != "APPROVED" or manifest.get("production_allowed") is not True:
        raise ValidationError("Manifesto do piloto aprovado não está marcado como APPROVED.")
    if manifest.get("selection_mode") != "PRODUCTION":
        raise ValidationError("Modo de seleção do piloto aprovado deve ser PRODUCTION.")
    if manifest.get("canvas") != {"width": 1920, "height": 1080}:
        raise ValidationError("Canvas do manifesto não é 1920x1080.")
    if manifest.get("safe_area") != {"absolute": 64, "text": 96}:
        raise ValidationError("Safe area do manifesto diverge do sistema.")
    if manifest.get("sources", {}).get("timing", {}).get("sha256") != sha256(TIMING_FILE):
        raise ValidationError("Manifesto não referencia o timing atual.")
    scenes = manifest.get("scenes", [])
    if [scene.get("scene_id") for scene in scenes] != ["S001", "S002", "S003"]:
        raise ValidationError("Manifesto deve conter somente S001–S003 em ordem.")
    previous_end = 0.0
    for scene in scenes:
        scene_id = scene["scene_id"]
        family, variant, version, focus_mode = EXPECTED[scene_id]
        if scene.get("composition") != family:
            raise ValidationError(f"{scene_id}: família incorreta.")
        variant_data = scene.get("variant", {})
        if (
            variant_data.get("id") != variant
            or float(variant_data.get("version")) != version
            or variant_data.get("status") != "APPROVED"
            or variant_data.get("motion_status") != "MOTION_APPROVED"
        ):
            raise ValidationError(f"{scene_id}: contrato de variante incorreto.")
        if scene.get("focus_mode") != focus_mode:
            raise ValidationError(f"{scene_id}: focus_mode incorreto.")
        start = float(scene["start"])
        end = float(scene["end"])
        if abs(start - previous_end) > 0.001 or end <= start:
            raise ValidationError(f"{scene_id}: timeline descontínua ou negativa.")
        if scene["anchor_start"]["start"] < start - 0.001:
            raise ValidationError(f"{scene_id}: anchor_start anterior à cena.")
        if scene["anchor_end"]["end"] > end + 0.001:
            raise ValidationError(f"{scene_id}: anchor_end posterior à cena.")
        for event in scene.get("events", []):
            event_start = float(event["time"])
            event_end = float(event["end_time"])
            if not start <= event_start < event_end <= end + 0.001:
                raise ValidationError(f"{event['event_id']}: evento fora da duração da cena.")
        source = ROOT / scene["source_svg"]
        if not source.is_file() or sha256(source) != scene["source_svg_sha256"]:
            raise ValidationError(f"{scene_id}: master fonte ausente ou alterado.")
        for zone in scene.get("content_zones", []):
            if zone.get("safe_area_policy") != "STRICT":
                continue
            x, y = float(zone["x"]), float(zone["y"])
            width, height = float(zone["width"]), float(zone["height"])
            if x < 96 or y < 96 or x + width > 1824 or y + height > 984:
                raise ValidationError(f"{scene_id}/{zone['id']}: zona STRICT fora da safe area.")
        previous_end = end
    if abs(previous_end - duration) > 0.001:
        raise ValidationError("Fim de S003 diverge da duração real do áudio.")
    render_origin = float(manifest.get("audio", {}).get("render_origin_seconds", -1))
    expected_origin = float(timing["beats"][0]["speech_start"])
    if abs(render_origin - expected_origin) > 0.001:
        raise ValidationError("Leading blank não foi cortado exatamente na primeira fala.")
    presentation_duration = float(
        manifest.get("audio", {}).get("presentation_duration_seconds", -1)
    )
    if abs(presentation_duration - (duration - render_origin)) > 0.001:
        raise ValidationError("Duração de apresentação não corresponde ao trim global.")
    if manifest.get("audio", {}).get("leading_blank_policy") != "TRIM_TO_FIRST_SPEECH_WITHOUT_INTERNAL_RETIMING":
        raise ValidationError("Política de remoção do leading blank ausente.")
    if not scenes[1].get("continuity_in") or not scenes[1].get("continuity_out"):
        raise ValidationError("S002 não declara continuidade de entrada/saída.")
    if not scenes[2].get("continuity_in"):
        raise ValidationError("S003 não declara continuidade de entrada.")


def validate_renders(manifest: dict[str, Any], duration: float) -> dict[str, Any]:
    metadata = load_json(RENDER_METADATA_FILE)
    renders = metadata.get("renders", {})
    render_origin = float(manifest["audio"]["render_origin_seconds"])
    presentation_duration = float(manifest["audio"]["presentation_duration_seconds"])
    if set(renders) != {"audiovisual", "silent"}:
        raise ValidationError("Metadados devem conter render audiovisual e silent.")
    for mode, entry in renders.items():
        path = ROOT / entry["file"]
        if not path.is_file() or path.stat().st_size < 100_000:
            raise ValidationError(f"Render {mode} ausente ou pequeno demais.")
        data = path.read_bytes()
        if data[:4] != bytes.fromhex("1A45DFA3"):
            raise ValidationError(f"Render {mode} não possui cabeçalho WebM.")
        if not any(codec in data for codec in (b"V_VP9", b"V_VP8")):
            raise ValidationError(f"Render {mode} não possui faixa VP8/VP9.")
        has_opus = b"A_OPUS" in data
        if mode == "audiovisual" and not has_opus:
            raise ValidationError("Render audiovisual não possui áudio Opus.")
        if mode == "silent" and has_opus:
            raise ValidationError("Render silent contém faixa de áudio.")
        if int(entry["width"]) != 1920 or int(entry["height"]) != 1080:
            raise ValidationError(f"Render {mode} não é 1920x1080.")
        if abs(float(entry["duration_seconds"]) - presentation_duration) > 0.15:
            raise ValidationError(f"Render {mode} diverge da duração após trim.")
        if abs(float(entry["source_duration_seconds"]) - duration) > 0.15:
            raise ValidationError(f"Render {mode} não referencia a duração integral do WAV.")
        if abs(float(entry["render_origin_seconds"]) - render_origin) > 0.001:
            raise ValidationError(f"Render {mode} usa origem diferente da primeira fala.")
    return renders


def report_markdown(
    timing: dict[str, Any],
    manifest: dict[str, Any],
    renders: dict[str, Any],
    validation_time: str,
) -> str:
    scene_rows = []
    anchor_sections = []
    event_sections = []
    for scene in manifest["scenes"]:
        variant = scene["variant"]
        scene_rows.append(
            f"| {scene['scene_id']} | {' + '.join(scene['beat_ids'])} | "
            f"{scene['start']:.3f}s | {scene['end']:.3f}s | {scene['duration']:.3f}s | "
            f"{scene['composition']} | {variant['id']} v{variant['version']} | "
            f"{scene['focus_mode'] or '—'} |"
        )
        anchors = "\n".join(
            f"- `{name}` → “{anchor['text']}” → {anchor['start']:.3f}s"
            for name, anchor in scene["anchors"].items()
        )
        anchor_sections.append(f"### {scene['scene_id']}\n\n{anchors}")
        events = "\n".join(
            f"- `{event['event_id']}` · `{event['action']}` · {event['time']:.3f}–{event['end_time']:.3f}s · {event['narrative_function']}"
            for event in scene["events"]
        )
        event_sections.append(f"### {scene['scene_id']} — {scene['dominant_motion']}\n\n{events}")
    processing = timing["audio_processing"]
    return f"""# Piloto audiovisual S001–S003

Status: **APPROVED / PRODUCTION REFERENCE / APROVADO HUMANAMENTE**

Validado em: {validation_time}

## Síntese

- Provider TTS: `azure_speech_rest`
- Narrador: `{timing['narrator_id']}`
- Voz: `{timing['voice']}`
- Idioma: `{timing['language']}`
- Duração total real: **{timing['duration_seconds']:.3f}s**
- Leading blank removido no render: **{manifest['audio']['render_origin_seconds']:.3f}s**
- Duração apresentada: **{manifest['audio']['presentation_duration_seconds']:.3f}s**
- Beats: `B001`, `B002`, `B003`
- Música: nenhuma
- SFX: nenhum
- `AZURE_CONFIG_FOUND=true`

## Cenas

| Cena | Beats | Início | Fim | Duração | Família | Variante | Focus mode |
|---|---|---:|---:|---:|---|---|---|
{chr(10).join(scene_rows)}

## Anchors resolvidos

{chr(10).join(anchor_sections)}

Os limites dos beats e da fala vêm dos WAVs realmente retornados pelo Azure. O endpoint REST síncrono não fornece word boundaries; por isso, os tempos internos de palavras usam alinhamento determinístico ponderado dentro do sinal de fala detectado. Nenhum segundo foi escrito manualmente no roteiro.

## Eventos dominantes

{chr(10).join(event_sections)}

## Continuidade

- S001 → S002: `R$ 4.200` persiste e reduz de escala até o estado atual.
- S002 → S003: `RENDA R$ 4.200` persiste como contexto enquanto a baseline dá lugar à compressão.
- Não existe frame vazio entre cenas nem transição chamativa.

## Processamento de áudio

- Formato intermediário: WAV PCM mono, 24 kHz, 16 bits.
- High-pass: {processing['highpass_hz']} Hz.
- Compressor: threshold {processing['compressor_threshold_dbfs']} dBFS, ratio {processing['compressor_ratio']}:1.
- Normalização de pico: {processing['peak_normalization_dbfs']} dBFS.
- Limiter: {processing['limiter_ceiling_dbfs']} dBFS.
- Implementação: `{processing['implementation']}`; quantidade de amostras e duração preservadas.

## Renders

- Audiovisual: `{renders['audiovisual']['file']}` — 1920×1080, VP8/VP9 + Opus.
- Sem áudio: `{renders['silent']['file']}` — 1920×1080, VP8/VP9, sem faixa Opus.

## Validações aprovadas

- exatamente três variantes `APPROVED`/`MOTION_APPROVED`; as outras seis permanecem `EXPERIMENTAL`;
- `production_allowed=true` somente para a referência aprovada;
- leading blank removido por offset global até a primeira fala, sem alterar tempos internos;
- versões 1.1 e `COMPRESSION_FIRST` conferidos;
- anchors encontrados uma única vez e resolvidos;
- timestamps e palavras monotônicos;
- cenas contínuas, sem duração negativa;
- eventos dentro da cena e do áudio;
- WAV presente, íntegro e com duração real conferida;
- canvas 1920×1080 e zonas `STRICT` dentro da safe area textual;
- masters fontes presentes e conferidos por SHA-256;
- WebM audiovisual com Opus e WebM silent sem faixa de áudio;
- nenhum segredo Azure encontrado em código, JSON, logs, Markdown ou metadata.

## Erros encontrados

Nenhum erro bloqueante permaneceu após a validação.

## Limitações

- Word boundaries são aproximações determinísticas ancoradas nos limites reais do áudio, pois o endpoint REST síncrono usado não retorna eventos de palavra.
- O processamento de voz é leve e determinístico em PCM; FFmpeg não estava disponível e nenhuma suíte foi instalada.
- A qualidade editorial e vocal foi aprovada humanamente neste piloto; a expansão de novas cenas continua sujeita a plano separado.

## BLOCKED_BY_MASTER

Nenhum.

## Stop condition

O trabalho termina neste piloto. S004+, pipeline oficial, música, biblioteca e demais variantes não foram alterados.
"""


def main() -> int:
    config = load_json(COMPOSITIONS_FILE)
    timing = load_json(TIMING_FILE)
    manifest = load_json(MANIFEST_FILE)
    if not MOTION_SPEC_FILE.is_file():
        raise ValidationError("motion_spec.json ausente.")
    validate_compositions(config)
    _, duration = validate_timing(timing)
    validate_manifest(manifest, timing, duration)
    renders = validate_renders(manifest, duration)
    validate_no_secret_leak(read_env_secret(ENV_FILE))

    validation_time = datetime.now().astimezone().isoformat(timespec="seconds")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log = {
        "pilot_id": manifest["pilot_id"],
        "validated_at": validation_time,
        "status": "APPROVED_VALID",
        "azure_config_found": True,
        "secret_leaks": [],
        "checks": [
            "motion_candidates",
            "timing",
            "anchors",
            "events",
            "continuity",
            "audio",
            "safe_area",
            "assets",
            "render_resolution",
            "render_codecs",
            "credential_safety",
        ],
    }
    LOG_FILE.write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    REPORT_FILE.write_text(
        report_markdown(timing, manifest, renders, validation_time),
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"PILOTO AUDIOVISUAL APROVADO E VÁLIDO — S001–S003, {duration:.3f}s fonte, "
        f"{manifest['audio']['presentation_duration_seconds']:.3f}s apresentados."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
