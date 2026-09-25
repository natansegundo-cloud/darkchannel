#!/usr/bin/env python3
"""Captura frames de QA diretamente do canvas do piloto."""

from __future__ import annotations

import functools
import http.server
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s003"
RENDER_DIR = PILOT_DIR / "renders"
BROWSER_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
)
PREVIEWS = (("s001", 3.20), ("s002", 8.10), ("s003", 16.30))


class State:
    done = threading.Event()
    target: Path | None = None
    error: str | None = None


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        if self.path == "/preview" and State.target is not None:
            State.target.write_bytes(payload)
            self.send_response(204)
            self.end_headers()
            State.done.set()
            return
        if self.path == "/error":
            State.error = payload.decode("utf-8", errors="replace")
            self.send_response(204)
            self.end_headers()
            State.done.set()
            return
        self.send_error(404)


def browser_path() -> Path:
    for path in BROWSER_CANDIDATES:
        if path.is_file():
            return path
    raise RuntimeError("Edge ou Chrome não encontrado.")


def main() -> int:
    if not (PILOT_DIR / "player.html").is_file():
        raise RuntimeError("Player do piloto ausente.")
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    browser = browser_path()
    handler = functools.partial(Handler, directory=str(PILOT_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        for scene_id, preview_time in PREVIEWS:
            State.done.clear()
            State.error = None
            State.target = RENDER_DIR / f"preview_{scene_id}.png"
            profile = Path(tempfile.mkdtemp(prefix=f"co-preview-{scene_id}-"))
            process: subprocess.Popen[bytes] | None = None
            try:
                command = [
                    str(browser),
                    "--headless=new",
                    "--disable-gpu",
                    "--hide-scrollbars",
                    "--no-first-run",
                    "--no-default-browser-check",
                    f"--user-data-dir={profile}",
                    f"http://127.0.0.1:{port}/player.html?preview={preview_time}&capture=1",
                ]
                process = subprocess.Popen(
                    command,
                    cwd=ROOT,
                    creationflags=creation_flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if not State.done.wait(30):
                    raise RuntimeError(f"Timeout ao capturar {scene_id}.")
                if State.error:
                    raise RuntimeError(f"Player falhou em {scene_id}: {State.error}")
                if not State.target.is_file() or State.target.stat().st_size < 10_000:
                    raise RuntimeError(f"Preview inválido para {scene_id}.")
                print(f"{scene_id.upper()}: {State.target.relative_to(ROOT)}")
            finally:
                if process and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                shutil.rmtree(profile, ignore_errors=True)
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
