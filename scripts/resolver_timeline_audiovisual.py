#!/usr/bin/env python3
"""Resolve anchors narrativos de 04 em tempos reais de 03A.

O resultado 04A é um contrato técnico gerado. Ele não deve ser editado à mão.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VISUAL_COLUMNS = (
    "scene_id",
    "beat_ids",
    "anchor_start",
    "anchor_end",
    "layout_id",
    "accent",
    "dominant_idea",
    "context",
    "character_role",
    "character_scale",
    "asset_ids",
    "events_json",
    "continuity_in",
    "continuity_out",
    "status",
)
ASSET_COLUMNS = (
    "asset_id",
    "asset_type",
    "source",
    "provider",
    "license",
    "production_method",
    "scene_ids",
    "first_used_scene",
    "version",
    "sha256",
    "status",
    "legacy_asset_id",
    "prompt_positive",
    "prompt_negative",
)


class ResolutionError(RuntimeError):
    pass


def project_path(value: Path) -> Path:
    return value.resolve() if value.is_absolute() else (ROOT / value).resolve()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ResolutionError(f"Arquivo não encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ResolutionError(f"JSON inválido em {path}: {exc}") from exc


def read_csv(path: Path, expected: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = tuple(reader.fieldnames or ())
            if fields != expected:
                raise ResolutionError(
                    f"Cabeçalho inválido em {path.name}. Esperado: {', '.join(expected)}"
                )
            return [
                {key: (value or "").strip() for key, value in row.items()}
                for row in reader
                if any((value or "").strip() for value in row.values())
            ]
    except FileNotFoundError as exc:
        raise ResolutionError(f"CSV não encontrado: {path}") from exc


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in plain if char.isalnum())


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def relative_or_absolute(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def parse_anchor(value: str) -> tuple[list[str], int]:
    occurrence = 1
    match = re.search(r"#(\d+)$", value.strip())
    if match:
        occurrence = int(match.group(1))
        value = value[: match.start()].rstrip()
    tokens = [normalize(token) for token in re.findall(r"\S+", value)]
    tokens = [token for token in tokens if token]
    if not tokens:
        raise ResolutionError("Anchor vazio ou sem palavras pesquisáveis.")
    return tokens, occurrence


def words_for_beats(timing: dict[str, Any], beat_ids: list[str]) -> list[dict[str, Any]]:
    beats = {beat["beat_id"]: beat for beat in timing.get("beats", [])}
    missing = [beat_id for beat_id in beat_ids if beat_id not in beats]
    if missing:
        raise ResolutionError(f"Beat(s) ausente(s) no 03A: {', '.join(missing)}")
    return [word for beat_id in beat_ids for word in beats[beat_id].get("words", [])]


def resolve_anchor(
    value: str,
    *,
    beat_ids: list[str],
    timing: dict[str, Any],
) -> dict[str, Any]:
    tokens, occurrence = parse_anchor(value)
    words = words_for_beats(timing, beat_ids)
    normalized = [word.get("normalized") or normalize(word["text"]) for word in words]
    matches = []
    length = len(tokens)
    for index in range(0, len(words) - length + 1):
        if normalized[index : index + length] == tokens:
            matches.append((words[index], words[index + length - 1]))
    if len(matches) < occurrence:
        raise ResolutionError(
            f"Anchor '{value}' não encontrado na sequência {','.join(beat_ids)}."
        )
    if len(matches) > 1 and "#" not in value:
        raise ResolutionError(
            f"Anchor ambíguo '{value}' ({len(matches)} ocorrências); use #N."
        )
    first, last = matches[occurrence - 1]
    return {
        "text": value,
        "occurrence": occurrence,
        "start": float(first["start"]),
        "end": float(last["end"]),
        "start_word_index": int(first["index"]),
        "end_word_index": int(last["index"]),
    }


def parse_events(raw: str, scene_id: str) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        events = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ResolutionError(f"{scene_id}: events_json inválido: {exc}") from exc
    if not isinstance(events, list):
        raise ResolutionError(f"{scene_id}: events_json deve ser uma lista.")
    return events


def validate_assets(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    assets: dict[str, dict[str, str]] = {}
    for row in rows:
        asset_id = row["asset_id"]
        if not asset_id or asset_id in assets:
            raise ResolutionError(f"asset_id vazio ou duplicado: {asset_id or '<vazio>'}")
        source = row["source"]
        if source and row["production_method"] not in {"comfyui", "external_generation"}:
            source_path = project_path(Path(source))
            if not source_path.is_file():
                raise ResolutionError(f"Fonte do asset não encontrada: {source}")
            digest = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if row["sha256"] and row["sha256"] != digest:
                raise ResolutionError(f"Hash divergente para {asset_id}: {source}")
            row = dict(row)
            row["sha256"] = digest
        assets[asset_id] = row
    return assets


def resolve(
    timing_path: Path,
    visual_path: Path,
    asset_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    timing = load_json(timing_path)
    visual_rows = read_csv(visual_path, VISUAL_COLUMNS)
    asset_rows = read_csv(asset_path, ASSET_COLUMNS)
    assets = validate_assets(asset_rows)
    if not visual_rows:
        raise ResolutionError("04_ROTEIRO_VISUAL.csv não possui cenas.")

    scene_ids: set[str] = set()
    scenes = []
    for row in visual_rows:
        scene_id = row["scene_id"].upper()
        if not re.fullmatch(r"S\d{3,}", scene_id) or scene_id in scene_ids:
            raise ResolutionError(f"scene_id inválido ou duplicado: {scene_id}")
        scene_ids.add(scene_id)
        beat_ids = [item.upper() for item in split_ids(row["beat_ids"])]
        if not beat_ids:
            raise ResolutionError(f"{scene_id}: beat_ids obrigatório.")
        start_anchor = resolve_anchor(row["anchor_start"], beat_ids=beat_ids, timing=timing)
        end_anchor = resolve_anchor(row["anchor_end"], beat_ids=beat_ids, timing=timing)
        if end_anchor["end"] <= start_anchor["start"]:
            raise ResolutionError(f"{scene_id}: anchor_end não sucede anchor_start.")
        asset_ids = split_ids(row["asset_ids"])
        missing_assets = [asset_id for asset_id in asset_ids if asset_id not in assets]
        if missing_assets:
            raise ResolutionError(
                f"{scene_id}: asset(s) ausente(s) no 05: {', '.join(missing_assets)}"
            )
        events = parse_events(row["events_json"], scene_id)
        resolved_events = []
        for index, event in enumerate(events, start=1):
            anchor_text = str(event.get("anchor", "")).strip()
            if not anchor_text:
                raise ResolutionError(f"{scene_id}: evento {index} sem anchor.")
            anchor = resolve_anchor(anchor_text, beat_ids=beat_ids, timing=timing)
            resolved_events.append(
                {
                    "event_id": event.get("event_id") or f"{scene_id}-E{index:02d}",
                    "anchor": anchor,
                    "target": event.get("target"),
                    "action": event.get("action"),
                    "narrative_function": event.get("narrative_function"),
                    "time": anchor["start"],
                }
            )
        scenes.append(
            {
                "scene_id": scene_id,
                "beat_ids": beat_ids,
                "anchor_start": start_anchor,
                "anchor_end": end_anchor,
                "start": start_anchor["start"],
                "anchor_end_time": end_anchor["end"],
                "layout_id": row["layout_id"],
                "accent": row["accent"],
                "dominant_idea": row["dominant_idea"],
                "context": row["context"] or None,
                "character": {
                    "role": row["character_role"] or "none",
                    "scale": row["character_scale"] or None,
                },
                "asset_ids": asset_ids,
                "assets": [
                    {
                        "asset_id": asset_id,
                        "source": assets[asset_id]["source"],
                        "sha256": assets[asset_id]["sha256"],
                    }
                    for asset_id in asset_ids
                ],
                "events": resolved_events,
                "continuity_in": row["continuity_in"] or None,
                "continuity_out": row["continuity_out"] or None,
                "status": row["status"],
            }
        )

    # A primeira cena cobre o silêncio técnico inicial antes da primeira palavra.
    # O próximo anchor de entrada é a fronteira visual real. Assim, pausas e
    # respirações ficam cobertas sem inventar segundos no roteiro criativo.
    scenes[0]["start"] = 0.0
    for index, scene in enumerate(scenes):
        scene["end"] = (
            scenes[index + 1]["start"]
            if index + 1 < len(scenes)
            else float(timing["duration_seconds"])
        )
        scene["duration"] = round(scene["end"] - scene["start"], 4)
        if scene["duration"] <= 0:
            raise ResolutionError(f"{scene['scene_id']}: duração resolvida inválida.")
        if scene["anchor_end_time"] > scene["end"] + 0.001:
            raise ResolutionError(
                f"{scene['scene_id']}: anchor_end ultrapassa a entrada da próxima cena."
            )

    output = {
        "schema_version": "1.0",
        "episode_id": timing.get("episode_id"),
        "scope": "pilot_s001_s006" if [s["scene_id"] for s in scenes] == [f"S{i:03d}" for i in range(1, 7)] else "selected_scenes",
        "generated_by": "scripts/resolver_timeline_audiovisual.py",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "audio": {
            "file": timing["audio_file"],
            "sha256": timing["audio_sha256"],
            "provider": timing["provider"],
            "voice": timing["voice"],
            "duration_seconds": timing["duration_seconds"],
            "timing_method": timing["timing_method"],
        },
        "sources": {
            "03A_AUDIO_TIMING.json": {
                "file": relative_or_absolute(timing_path),
                "sha256": hashlib.sha256(timing_path.read_bytes()).hexdigest(),
            },
            "04_ROTEIRO_VISUAL.csv": {
                "file": relative_or_absolute(visual_path),
                "sha256": hashlib.sha256(visual_path.read_bytes()).hexdigest(),
            },
            "05_ASSET_MANIFEST.csv": {
                "file": relative_or_absolute(asset_path),
                "sha256": hashlib.sha256(asset_path.read_bytes()).hexdigest(),
            },
        },
        "scenes": scenes,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gera 04A_SCENE_MANIFEST.json a partir de 03A + 04 + 05.")
    parser.add_argument("episodio", help="Pasta do episódio ou ID CO-###.")
    parser.add_argument("--timing", type=Path, help="Sobrescreve o caminho de 03A.")
    parser.add_argument("--visual", type=Path, help="Sobrescreve o caminho de 04.")
    parser.add_argument("--assets", type=Path, help="Sobrescreve o caminho de 05.")
    parser.add_argument("--saida", type=Path, help="Sobrescreve o caminho de 04A.")
    return parser


def resolve_episode(value: str) -> Path:
    candidate = project_path(Path(value))
    if candidate.is_dir():
        return candidate
    matches = sorted((ROOT / "episodios").glob(f"{value}-*"))
    if len(matches) != 1:
        raise ResolutionError(f"Episódio não encontrado ou ambíguo: {value}")
    return matches[0]


def main() -> int:
    args = build_parser().parse_args()
    episode = resolve_episode(args.episodio)
    timing = project_path(args.timing) if args.timing else episode / "03A_AUDIO_TIMING.json"
    visual = project_path(args.visual) if args.visual else episode / "04_ROTEIRO_VISUAL.csv"
    assets = project_path(args.assets) if args.assets else episode / "05_ASSET_MANIFEST.csv"
    output = project_path(args.saida) if args.saida else episode / "04A_SCENE_MANIFEST.json"
    result = resolve(timing, visual, assets, output)
    print(
        f"04A gerado: {relative_or_absolute(output)} — "
        f"{len(result['scenes'])} cena(s), {result['audio']['duration_seconds']:.2f}s"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ResolutionError, OSError, KeyError, ValueError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
