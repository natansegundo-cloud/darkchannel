#!/usr/bin/env python3
"""Renderiza o piloto S001-S006 com o Visual Geometry Contract e audio existente."""

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


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006_v3_geometry"
RENDERS_DIR = PILOT_DIR / "renders"
OUTPUT = RENDERS_DIR / "capital_oculto_pilot_s001_s006_v3_geometry.webm"
METADATA = RENDERS_DIR / "render_metadata_geometry.json"
BROWSERS = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


class RenderError(RuntimeError):
    pass


class State:
    done = threading.Event()
    error: str | None = None
    headers: dict[str, str] = {}


def browser() -> Path:
    for candidate in BROWSERS:
        if candidate.is_file():
            return candidate
    raise RenderError("Edge ou Chrome nao encontrado.")


def handler(output: Path):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length)
            if self.path == "/save":
                output.write_bytes(payload)
                State.headers = {name: self.headers.get(header, "") for name, header in {
                    "duration_seconds": "X-Duration",
                    "source_duration_seconds": "X-Source-Duration",
                    "render_origin_seconds": "X-Render-Origin",
                    "width": "X-Width", "height": "X-Height", "fps": "X-Fps",
                    "silent": "X-Silent", "mime_type": "Content-Type",
                }.items()}
                self.send_response(204)
                self.end_headers()
                State.done.set()
            elif self.path == "/error":
                State.error = payload.decode("utf-8", errors="replace")
                self.send_response(204)
                self.end_headers()
                State.done.set()
            else:
                self.send_error(404)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    required = (
        PILOT_DIR / "player_geometry.html",
        PILOT_DIR / "manifest" / "scene_manifest_geometry.json",
        ROOT / "tests" / "audiovisual_pilot_s001_s006_v2_wordboundary" / "audio" / "narration_wordboundary.wav",
    )
    for path in required:
        if not path.is_file():
            raise RenderError(f"Arquivo obrigatorio ausente: {path}")
    if OUTPUT.exists():
        raise RenderError(f"Render ja existe e nao sera sobrescrito: {OUTPUT}")
    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    State.done.clear()
    State.error = None
    State.headers = {}
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(handler(OUTPUT), directory=str(ROOT))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    profile = Path(tempfile.mkdtemp(prefix="co-av-geometry-"))
    process = None
    try:
        command = [
            str(browser()), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--no-first-run", "--no-default-browser-check", "--autoplay-policy=no-user-gesture-required",
            f"--user-data-dir={profile}",
            f"http://127.0.0.1:{server.server_address[1]}/tests/audiovisual_pilot_s001_s006_v3_geometry/player_geometry.html",
        ]
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen(command, cwd=ROOT, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not State.done.wait(args.timeout):
            raise RenderError(f"Exportacao excedeu {args.timeout}s.")
        if State.error:
            raise RenderError(f"Erro no player: {State.error}")
        if not OUTPUT.is_file() or OUTPUT.stat().st_size < 100_000:
            raise RenderError("O navegador nao produziu um WebM valido.")
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

    metadata = {
        "schema_version": "1.0",
        "timing_quality": "WORD_BOUNDARY_REAL",
        "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0",
        "audio_source": "tests/audiovisual_pilot_s001_s006_v2_wordboundary/audio/narration_wordboundary.wav",
        "render": {
            "file": OUTPUT.relative_to(ROOT).as_posix(),
            "size_bytes": OUTPUT.stat().st_size,
            "duration_seconds": float(State.headers["duration_seconds"]),
            "source_duration_seconds": float(State.headers["source_duration_seconds"]),
            "render_origin_seconds": float(State.headers["render_origin_seconds"]),
            "width": int(State.headers["width"]), "height": int(State.headers["height"]),
            "fps": int(State.headers["fps"]), "mime_type": State.headers["mime_type"],
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        },
    }
    METADATA.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"RENDER={OUTPUT.relative_to(ROOT)}")
    print(f"DURATION={State.headers['duration_seconds']}s")
    print(f"SIZE={OUTPUT.stat().st_size}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RenderError, OSError, ValueError, KeyError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
