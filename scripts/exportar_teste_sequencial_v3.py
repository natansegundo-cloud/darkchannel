#!/usr/bin/env python3
"""Exporta o teste sequencial V3 para WebM usando o MediaRecorder do navegador local."""

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
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "episodios" / "CO-001-por-que-ganhar-mais-nao-basta" / "testes" / "v3_sequencial_s001_s006"
OUTPUT = TEST_DIR / "teste_sequencial_v3_s001_s006_pipeline.webm"
BROWSER_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


class ExportState:
    done = threading.Event()
    error: str | None = None
    duration: str | None = None


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)
        if self.path == "/save":
            OUTPUT.write_bytes(payload)
            ExportState.duration = self.headers.get("X-Duration")
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


def find_browser() -> Path:
    for candidate in BROWSER_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Edge ou Chrome não encontrado.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=90, help="Tempo máximo de exportação em segundos.")
    args = parser.parse_args()
    for required in (TEST_DIR / "player.html", TEST_DIR / "timeline.json"):
        if not required.is_file():
            raise RuntimeError(f"Arquivo obrigatório ausente: {required}")
    timeline = json.loads((TEST_DIR / "timeline.json").read_text(encoding="utf-8-sig"))
    audio_file = TEST_DIR / timeline.get("audio", "")
    if not audio_file.is_file():
        raise RuntimeError(f"Áudio declarado na timeline não encontrado: {audio_file}")

    browser = find_browser()
    ExportState.done.clear()
    ExportState.error = None
    handler = functools.partial(Handler, directory=str(TEST_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process: subprocess.Popen[bytes] | None = None
    profile = Path(tempfile.mkdtemp(prefix="co-v3-export-"))
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
            f"http://127.0.0.1:{port}/player.html",
        ]
        process = subprocess.Popen(command, cwd=ROOT, creationflags=creation_flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not ExportState.done.wait(args.timeout):
            raise RuntimeError(f"Exportação excedeu {args.timeout}s.")
        if ExportState.error:
            raise RuntimeError(f"Erro no player: {ExportState.error}")
        if not OUTPUT.is_file() or OUTPUT.stat().st_size < 100_000:
            raise RuntimeError("O navegador não produziu um vídeo WebM válido.")
    finally:
        server.shutdown()
        server.server_close()
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        time.sleep(.5)
        shutil.rmtree(profile, ignore_errors=True)

    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"VÍDEO EXPORTADO — {OUTPUT.relative_to(ROOT)}")
    print(f"Duração de áudio: {ExportState.duration or 'não informada'}s | Tamanho: {size_mb:.1f} MB")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
