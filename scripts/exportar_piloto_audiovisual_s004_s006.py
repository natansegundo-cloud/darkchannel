#!/usr/bin/env python3
"""Exporta o piloto audiovisual S004–S006 pelo MediaRecorder do navegador local."""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006"
RENDERS_DIR = PILOT_DIR / "renders"
METADATA_FILE = RENDERS_DIR / "render_metadata.json"
BROWSER_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


class ExportError(RuntimeError):
    pass


class ExportState:
    done = threading.Event()
    error: str | None = None
    headers: dict[str, str] = {}


def load_render_metadata() -> dict[str, Any]:
    if not METADATA_FILE.is_file():
        return {"schema_version": "1.0", "renders": {}}
    return json.loads(METADATA_FILE.read_text(encoding="utf-8-sig"))


def find_browser() -> Path:
    for candidate in BROWSER_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise ExportError("Edge ou Chrome não encontrado.")


def output_for(silent: bool) -> Path:
    name = (
        "capital_oculto_pilot_s004_s006_azure_antonio_silent.webm"
        if silent
        else "capital_oculto_pilot_s004_s006_azure_antonio.webm"
    )
    return RENDERS_DIR / name


def handler_for(output: Path, mode: str):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length)
            if self.path == "/save":
                output.write_bytes(payload)
                ExportState.headers = {
                    "duration_seconds": self.headers.get("X-Duration", ""),
                    "source_duration_seconds": self.headers.get("X-Source-Duration", ""),
                    "render_origin_seconds": self.headers.get("X-Render-Origin", ""),
                    "width": self.headers.get("X-Width", ""),
                    "height": self.headers.get("X-Height", ""),
                    "fps": self.headers.get("X-Fps", ""),
                    "silent": self.headers.get("X-Silent", ""),
                    "mime_type": self.headers.get("Content-Type", ""),
                }
                self.send_response(204)
                self.end_headers()
                ExportState.done.set()
                return
            if self.path == "/error":
                ExportState.error = payload.decode("utf-8", errors="replace")
                self.send_response(204)
                self.end_headers()
                ExportState.done.set()
                return
            self.send_error(404)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--silent", action="store_true", help="Exporta sem faixa de áudio.")
    parser.add_argument("--timeout", type=int, default=150)
    args = parser.parse_args()
    for required in (
        PILOT_DIR / "player.html",
        PILOT_DIR / "manifest" / "scene_manifest.json",
        PILOT_DIR / "audio" / "processed" / "narration_azure_antonio.wav",
    ):
        if not required.is_file():
            raise ExportError(f"Arquivo obrigatório ausente: {required}")
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    output = output_for(args.silent)
    mode = "silent" if args.silent else "audiovisual"
    browser = find_browser()

    ExportState.done.clear()
    ExportState.error = None
    ExportState.headers = {}
    handler = functools.partial(handler_for(output, mode), directory=str(PILOT_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    profile = Path(tempfile.mkdtemp(prefix="co-av-pilot-s004-s006-"))
    process: subprocess.Popen[bytes] | None = None
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    query = "?silent=1" if args.silent else ""
    try:
        command = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--autoplay-policy=no-user-gesture-required",
            f"--user-data-dir={profile}",
            f"http://127.0.0.1:{port}/player.html{query}",
        ]
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not ExportState.done.wait(args.timeout):
            raise ExportError(f"Exportação excedeu {args.timeout}s.")
        if ExportState.error:
            raise ExportError(f"Erro no player: {ExportState.error}")
        if not output.is_file() or output.stat().st_size < 100_000:
            raise ExportError("O navegador não produziu um WebM válido.")
    finally:
        server.shutdown()
        server.server_close()
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        time.sleep(0.35)
        shutil.rmtree(profile, ignore_errors=True)

    metadata = load_render_metadata()
    metadata["renders"][mode] = {
        "file": output.relative_to(ROOT).as_posix(),
        "size_bytes": output.stat().st_size,
        "duration_seconds": float(ExportState.headers["duration_seconds"]),
        "source_duration_seconds": float(ExportState.headers["source_duration_seconds"]),
        "render_origin_seconds": float(ExportState.headers["render_origin_seconds"]),
        "width": int(ExportState.headers["width"]),
        "height": int(ExportState.headers["height"]),
        "fps": int(ExportState.headers["fps"]),
        "silent": ExportState.headers["silent"].casefold() == "true",
        "mime_type": ExportState.headers["mime_type"],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    METADATA_FILE.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"VÍDEO S004–S006 EXPORTADO — {output.relative_to(ROOT)}")
    print(
        f"{ExportState.headers['width']}x{ExportState.headers['height']} | "
        f"{ExportState.headers['duration_seconds']}s | modo={mode}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExportError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
