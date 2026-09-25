#!/usr/bin/env python3
"""Gera imagens de um episodio pela API local do ComfyUI.

O script usa apenas a biblioteca padrao, nunca sobrescreve arquivos e registra
eventos em JSONL para permitir retomada segura depois de uma interrupcao.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = PROJECT_ROOT / "config" / "visual_style.json"
MODEL_PATH = PROJECT_ROOT / "config" / "modelos_visuais.json"
REQUIRED_COLUMNS = {
    "asset_id",
    "batch",
    "tool_target",
    "duration_seconds",
    "reference_input",
    "prompt_final",
    "negative_prompt",
}
ASSET_MANIFEST_COLUMNS = {
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
}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Arquivo obrigatorio nao encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON invalido em {path}: {exc}") from exc


def resolve_episode(value: str) -> Path:
    candidate = Path(value)
    if candidate.is_dir():
        return candidate.resolve()

    candidate = PROJECT_ROOT / value
    if candidate.is_dir():
        return candidate.resolve()

    matches = sorted((PROJECT_ROOT / "episodios").glob(f"{value}-*"))
    if len(matches) == 1:
        return matches[0].resolve()
    if not matches:
        raise RuntimeError(f"Episodio nao encontrado: {value}")
    raise RuntimeError(f"ID ambiguo; informe a pasta completa: {value}")


def episode_id(episode: Path) -> str:
    metadata = episode / "episodio.json"
    if metadata.exists():
        data = load_json(metadata)
        for key in ("id", "episode_id", "video_id"):
            if data.get(key):
                return str(data[key])
    return episode.name.split("-", 2)[0] + "-" + episode.name.split("-", 2)[1]


def read_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - fields
            if missing:
                raise RuntimeError(
                    f"Colunas ausentes em {path.name}: {', '.join(sorted(missing))}"
                )
            return [dict(row) for row in reader]
    except FileNotFoundError as exc:
        raise RuntimeError(f"CSV de prompts nao encontrado: {path}") from exc


def read_asset_manifest(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing = ASSET_MANIFEST_COLUMNS - fields
            if missing:
                raise RuntimeError(
                    f"Colunas ausentes em {path.name}: {', '.join(sorted(missing))}"
                )
            rows = []
            for row in reader:
                method = (row.get("production_method") or "").strip().lower()
                prompt = (row.get("prompt_positive") or "").strip()
                if method not in {"comfyui", "external_generation"} or not prompt:
                    continue
                rows.append(
                    {
                        "asset_id": (row.get("asset_id") or "").strip(),
                        "batch": "asset_manifest",
                        "tool_target": "image",
                        "duration_seconds": "",
                        "reference_input": (row.get("source") or "").strip(),
                        "prompt_final": prompt,
                        "negative_prompt": (row.get("prompt_negative") or "").strip(),
                    }
                )
            return rows
    except FileNotFoundError as exc:
        raise RuntimeError(f"Manifesto de assets nao encontrado: {path}") from exc


def normalize_base_url(value: str) -> str:
    return value.rstrip("/")


def http_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} em {url}: {detail[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"ComfyUI indisponivel em {url}: {exc.reason}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Resposta nao JSON recebida de {url}") from exc


def verify_server(base_url: str, timeout: float) -> None:
    stats = http_json(f"{base_url}/system_stats", timeout=timeout)
    if "system" not in stats and "devices" not in stats:
        raise RuntimeError("A API respondeu, mas /system_stats nao parece ser do ComfyUI.")

    required_nodes = (
        "CheckpointLoaderSimple",
        "EmptyLatentImage",
        "CLIPTextEncode",
        "KSampler",
        "VAEDecode",
        "SaveImage",
        "ImageScaleBy",
    )
    objects = http_json(f"{base_url}/object_info", timeout=timeout)
    missing = [node for node in required_nodes if node not in objects]
    if missing:
        raise RuntimeError(f"Nodes obrigatorios ausentes no ComfyUI: {', '.join(missing)}")


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def prompt_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def deterministic_seed(ep_id: str, asset_id: str, style_id: str, digest: str) -> int:
    raw = f"{ep_id}|{asset_id}|{style_id}|{digest}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & ((1 << 63) - 1)


def join_prompt(*parts: str) -> str:
    cleaned = [part.strip().strip(",") for part in parts if part and part.strip()]
    return ", ".join(cleaned)


def build_workflow(
    template: dict[str, Any],
    generation: dict[str, Any],
    positive: str,
    negative: str,
    seed: int,
    filename_prefix: str,
    upscale: bool,
) -> dict[str, Any]:
    workflow = copy.deepcopy(template)

    workflow["3"]["inputs"].update(
        {
            "seed": seed,
            "steps": int(generation["steps"]),
            "cfg": float(generation["cfg"]),
            "sampler_name": generation["sampler_name"],
            "scheduler": generation["scheduler"],
            "denoise": float(generation["denoise"]),
        }
    )
    loader_inputs = workflow["4"]["inputs"]
    if "ckpt_name" in loader_inputs:
        loader_inputs["ckpt_name"] = generation["model_path"]
    elif "model_path" in loader_inputs:
        loader_inputs["model_path"] = generation["model_path"]
    else:
        raise RuntimeError("Node 4 do workflow nao possui ckpt_name nem model_path.")
    workflow["5"]["inputs"].update(
        {
            "width": int(generation["width"]),
            "height": int(generation["height"]),
            "batch_size": int(generation.get("batch_size", 1)),
        }
    )
    workflow["6"]["inputs"]["text"] = positive
    workflow["7"]["inputs"]["text"] = negative
    workflow["9"]["inputs"]["filename_prefix"] = filename_prefix

    if upscale:
        workflow["10"] = {
            "class_type": "ImageScaleBy",
            "inputs": {
                "image": ["8", 0],
                "upscale_method": generation.get("upscale_method", "lanczos"),
                "scale_by": float(generation.get("upscale_factor", 2.0)),
            },
        }
        workflow["9"]["inputs"]["images"] = ["10", 0]
    return workflow


def queue_prompt(base_url: str, workflow: dict[str, Any], client_id: str, timeout: float) -> str:
    response = http_json(
        f"{base_url}/prompt",
        method="POST",
        payload={"prompt": workflow, "client_id": client_id},
        timeout=timeout,
    )
    prompt_id = response.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI nao devolveu prompt_id: {response}")
    return str(prompt_id)


def execution_error(entry: dict[str, Any]) -> str | None:
    status = entry.get("status") or {}
    for message in status.get("messages") or []:
        if not isinstance(message, list) or len(message) < 2:
            continue
        if message[0] in {"execution_error", "execution_interrupted"}:
            return json.dumps(message[1], ensure_ascii=False)
    if status.get("completed") is False and status.get("status_str") == "error":
        return json.dumps(status, ensure_ascii=False)
    return None


def wait_for_image(
    base_url: str,
    prompt_id: str,
    *,
    request_timeout: float,
    generation_timeout: float,
    poll_interval: float,
) -> dict[str, str]:
    deadline = time.monotonic() + generation_timeout
    while time.monotonic() < deadline:
        history = http_json(
            f"{base_url}/history/{urllib.parse.quote(prompt_id)}",
            timeout=request_timeout,
        )
        entry = history.get(prompt_id)
        if entry:
            error = execution_error(entry)
            if error:
                raise RuntimeError(f"Falha de execucao no ComfyUI: {error}")
            outputs = entry.get("outputs") or {}
            preferred = outputs.get("9") or {}
            images = preferred.get("images") or []
            if not images:
                for output in outputs.values():
                    images = output.get("images") or []
                    if images:
                        break
            if images:
                return images[0]
        time.sleep(poll_interval)
    raise RuntimeError(f"Tempo limite excedido para o prompt {prompt_id}")


def download_image(base_url: str, image_info: dict[str, str], timeout: float) -> bytes:
    query = urllib.parse.urlencode(
        {
            "filename": image_info["filename"],
            "subfolder": image_info.get("subfolder", ""),
            "type": image_info.get("type", "output"),
        }
    )
    request = urllib.request.Request(f"{base_url}/view?{query}", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Falha ao baixar imagem do ComfyUI: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Falha ao baixar imagem do ComfyUI: {exc.reason}") from exc
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("O arquivo devolvido pelo ComfyUI nao e um PNG valido.")
    return data


def existing_output(output_dir: Path, asset_id: str, style_slug: str, short_hash: str) -> Path | None:
    matches = sorted(output_dir.glob(f"{asset_id}__{style_slug}__{short_hash}__v*.png"))
    return matches[0] if matches else None


def next_output_path(output_dir: Path, asset_id: str, style_slug: str, short_hash: str) -> Path:
    for version in range(1, 10000):
        path = output_dir / f"{asset_id}__{style_slug}__{short_hash}__v{version:03d}.png"
        if not path.exists():
            return path
    raise RuntimeError(f"Limite de versoes excedido para {asset_id}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera assets ComfyUI do 05_ASSET_MANIFEST.csv, com fallback legado temporario."
    )
    parser.add_argument(
        "episodio",
        help="ID (ex.: CO-001), nome da pasta ou caminho para o episodio.",
    )
    parser.add_argument(
        "--assets",
        help="Lista de asset_id separada por virgulas. Padrao: todas as linhas image.",
    )
    parser.add_argument("--limite", type=int, help="Numero maximo de imagens nesta execucao.")
    parser.add_argument("--upscale", action="store_true", help="Aplica upscale Lanczos 2x no ComfyUI.")
    parser.add_argument("--dry-run", action="store_true", help="Valida e mostra a fila sem gerar.")
    parser.add_argument("--servidor", help="URL da API, substitui a configuracao central.")
    parser.add_argument("--timeout", type=float, help="Tempo maximo por imagem, em segundos.")
    parser.add_argument(
        "--legado",
        action="store_true",
        help="Forca a leitura temporaria de 05_PROMPTS_IMAGENS.csv.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limite is not None and args.limite < 1:
        raise RuntimeError("--limite deve ser maior que zero.")

    episode = resolve_episode(args.episodio)
    ep_id = episode_id(episode)
    style = load_json(STYLE_PATH)
    model_registry = load_json(MODEL_PATH)
    workflow_path = PROJECT_ROOT / style["comfyui"]["workflow"]
    workflow_template = load_json(workflow_path)
    asset_manifest = episode / "05_ASSET_MANIFEST.csv"
    legacy_manifest = episode / "05_PROMPTS_IMAGENS.csv"
    rows: list[dict[str, str]] = []
    manifest_source = legacy_manifest
    if asset_manifest.is_file() and not args.legado:
        rows = read_asset_manifest(asset_manifest)
        manifest_source = asset_manifest
    if not rows:
        if asset_manifest.is_file() and not args.legado:
            print(
                "05_ASSET_MANIFEST.csv nao possui assets ComfyUI; "
                "usando 05_PROMPTS_IMAGENS.csv durante a compatibilidade temporaria."
            )
        rows = read_rows(legacy_manifest)
        manifest_source = legacy_manifest

    override_path = episode / "assets" / "prompt_modelo.json"
    overrides = load_json(override_path) if override_path.exists() else {}
    requested = None
    if args.assets:
        requested = {item.strip().upper() for item in args.assets.split(",") if item.strip()}

    image_rows = [row for row in rows if row["tool_target"].strip().lower() == "image"]
    if requested is not None:
        known = {row["asset_id"].strip().upper() for row in image_rows}
        unknown = requested - known
        if unknown:
            raise RuntimeError(f"Assets nao encontrados ou nao-image: {', '.join(sorted(unknown))}")
        image_rows = [row for row in image_rows if row["asset_id"].strip().upper() in requested]
    if args.limite is not None:
        image_rows = image_rows[: args.limite]
    if not image_rows:
        raise RuntimeError("Nenhuma imagem selecionada para gerar.")

    output_dir = episode / "assets" / "gerados"
    logs_dir = episode / "assets" / "logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    run_stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    run_log = logs_dir / f"geracao_{run_stamp}.jsonl"
    manifest = episode / "assets" / "manifesto_geracao.jsonl"

    comfy = style["comfyui"]
    base_url = normalize_base_url(args.servidor or comfy["api_base"])
    request_timeout = float(comfy.get("request_timeout_seconds", 30))
    generation_timeout = float(args.timeout or comfy.get("generation_timeout_seconds", 1200))
    poll_interval = float(comfy.get("poll_interval_seconds", 2))
    style_id = str(style["style_id"])
    style_slug = style_id.lower()
    model_revision = model_registry["active_model"]["revision"]

    start_event = {
        "timestamp": now_iso(),
        "event": "run_start",
        "episode_id": ep_id,
        "style_id": style_id,
        "model_revision": model_revision,
        "selected_assets": [row["asset_id"] for row in image_rows],
        "manifest_source": str(manifest_source.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "upscale": args.upscale,
        "dry_run": args.dry_run,
    }
    append_jsonl(run_log, start_event)

    if not args.dry_run:
        try:
            verify_server(base_url, request_timeout)
        except RuntimeError as exc:
            raise RuntimeError(
                f"{exc}\nInicie antes com: powershell -ExecutionPolicy Bypass "
                f"-File scripts/iniciar_comfyui.ps1"
            ) from exc

    print(f"Episodio: {ep_id}")
    print(f"STYLE_ID: {style_id}")
    print(f"Fila: {len(image_rows)} imagem(ns) | upscale: {'sim' if args.upscale else 'nao'}")
    if args.dry_run:
        print("Modo dry-run: nenhum prompt sera enviado e nenhum PNG sera criado.")

    totals = {"generated": 0, "skipped": 0, "failed": 0}
    client_id = str(uuid.uuid4())
    for position, row in enumerate(image_rows, start=1):
        asset_id = row["asset_id"].strip().upper()
        override = overrides.get(asset_id, {})
        scene_positive = str(override.get("positive") or row["prompt_final"])
        scene_negative = str(override.get("negative") or row["negative_prompt"])
        generation = copy.deepcopy(style["generation"])
        generation.update(override.get("generation") or {})
        for dimension in ("width", "height"):
            value = int(generation[dimension])
            if value < 256 or value > 2048 or value % 8:
                raise RuntimeError(
                    f"{asset_id}: {dimension} deve estar entre 256 e 2048 e ser multiplo de 8."
                )
        positive = join_prompt(style["positive_prompt"], scene_positive)
        negative = join_prompt(style["negative_prompt"], scene_negative)
        identity = {
            "style_id": style_id,
            "style_version": style.get("style_version", 1),
            "model_revision": model_revision,
            "asset_id": asset_id,
            "positive": positive,
            "negative": negative,
            "generation": generation,
            "upscale": args.upscale,
        }
        digest = prompt_hash(identity)
        short_hash = digest[:8]
        seed = deterministic_seed(ep_id, asset_id, style_id, digest)
        present = existing_output(output_dir, asset_id, style_slug, short_hash)

        if present:
            totals["skipped"] += 1
            event = {
                "timestamp": now_iso(),
                "event": "skip_existing",
                "asset_id": asset_id,
                "prompt_hash": digest,
                "file": str(present.relative_to(PROJECT_ROOT)),
            }
            append_jsonl(run_log, event)
            print(f"[{position}/{len(image_rows)}] {asset_id}: ja concluido, pulando")
            continue

        destination = next_output_path(output_dir, asset_id, style_slug, short_hash)
        print(f"[{position}/{len(image_rows)}] {asset_id}: {'validado' if args.dry_run else 'gerando'}")
        if args.dry_run:
            append_jsonl(
                run_log,
                {
                    "timestamp": now_iso(),
                    "event": "dry_run_asset",
                    "asset_id": asset_id,
                    "prompt_hash": digest,
                    "seed": seed,
                    "reference_input": row["reference_input"],
                    "planned_file": str(destination.relative_to(PROJECT_ROOT)),
                },
            )
            continue

        started = time.monotonic()
        try:
            workflow = build_workflow(
                workflow_template,
                generation,
                positive,
                negative,
                seed,
                f"capital_oculto/{ep_id}/{asset_id}_{short_hash}",
                args.upscale,
            )
            queued_id = queue_prompt(base_url, workflow, client_id, request_timeout)
            append_jsonl(
                run_log,
                {
                    "timestamp": now_iso(),
                    "event": "queued",
                    "asset_id": asset_id,
                    "prompt_id": queued_id,
                    "prompt_hash": digest,
                    "seed": seed,
                },
            )
            image_info = wait_for_image(
                base_url,
                queued_id,
                request_timeout=request_timeout,
                generation_timeout=generation_timeout,
                poll_interval=poll_interval,
            )
            png = download_image(base_url, image_info, request_timeout)
            with destination.open("xb") as handle:
                handle.write(png)
            elapsed = round(time.monotonic() - started, 2)
            success = {
                "timestamp": now_iso(),
                "event": "success",
                "episode_id": ep_id,
                "asset_id": asset_id,
                "batch": row["batch"],
                "reference_input": row["reference_input"],
                "style_id": style_id,
                "model_revision": model_revision,
                "prompt_hash": digest,
                "seed": seed,
                "upscale": args.upscale,
                "elapsed_seconds": elapsed,
                "bytes": len(png),
                "file": str(destination.relative_to(PROJECT_ROOT)),
                "comfy_prompt_id": queued_id,
            }
            append_jsonl(run_log, success)
            append_jsonl(manifest, success)
            totals["generated"] += 1
            print(f"    salvo: {destination.name} ({elapsed:.1f}s)")
        except Exception as exc:  # registra a unidade e continua o lote
            totals["failed"] += 1
            append_jsonl(
                run_log,
                {
                    "timestamp": now_iso(),
                    "event": "error",
                    "asset_id": asset_id,
                    "prompt_hash": digest,
                    "elapsed_seconds": round(time.monotonic() - started, 2),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            print(f"    ERRO: {exc}", file=sys.stderr)

    finish_event = {
        "timestamp": now_iso(),
        "event": "run_finish",
        "totals": totals,
    }
    append_jsonl(run_log, finish_event)
    print(
        "Resumo: "
        f"{totals['generated']} gerada(s), {totals['skipped']} retomada(s), "
        f"{totals['failed']} erro(s)."
    )
    print(f"Log: {run_log.relative_to(PROJECT_ROOT)}")
    return 1 if totals["failed"] else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nGeracao interrompida. Execute novamente para retomar sem repetir.", file=sys.stderr)
        raise SystemExit(130)
    except RuntimeError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(2)
