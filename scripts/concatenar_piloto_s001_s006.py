#!/usr/bin/env python3
"""Concatena localmente os renders S001–S003 e S004–S006 sem alterar os originais.

Reutiliza o render aprovado existente de S001–S003 e o novo render de S004–S006,
unindo-os sequencialmente através do player de concatenação headless, garantindo
continuidade sem gaps, sem frames pretos, sem dessincronização e com máxima fidelidade vocal.
"""

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
PILOT1_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s003"
PILOT2_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006"
RENDERS_DIR = PILOT2_DIR / "renders"
METADATA_FILE = RENDERS_DIR / "render_metadata.json"

VIDEO1_PATH = PILOT1_DIR / "renders" / "capital_oculto_pilot_s001_s003_azure_antonio.webm"
VIDEO2_PATH = PILOT2_DIR / "renders" / "capital_oculto_pilot_s004_s006_azure_antonio.webm"
AUDIO1_PATH = PILOT1_DIR / "audio" / "processed" / "narration_azure_antonio.wav"
AUDIO2_PATH = PILOT2_DIR / "audio" / "processed" / "narration_azure_antonio.wav"

OUTPUT_PATH = RENDERS_DIR / "capital_oculto_pilot_s001_s006_azure_antonio.webm"

BROWSER_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


class ConcatError(RuntimeError):
    pass


class ConcatState:
    done = threading.Event()
    error: str | None = None
    headers: dict[str, str] = {}


def find_browser() -> Path:
    for candidate in BROWSER_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise ConcatError("Edge ou Chrome não encontrado.")


def load_render_metadata() -> dict[str, Any]:
    if not METADATA_FILE.is_file():
        return {"schema_version": "1.0", "renders": {}}
    return json.loads(METADATA_FILE.read_text(encoding="utf-8-sig"))


def generate_concat_html(
    output_file: Path,
    v1_rel: str,
    v2_rel: str,
    a1_rel: str,
    a2_rel: str,
    d1: float,
    d2: float,
    a1_origin: float,
) -> None:
    total_d = d1 + d2
    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Capital Oculto — Concatenação S001–S006</title>
  <style>
    html, body {{ margin: 0; width: 100%; height: 100%; overflow: hidden; background: #111111; }}
    body {{ display: grid; place-items: center; }}
    canvas {{ display: block; width: min(100vw, 177.777vh); height: min(56.25vw, 100vh); background: #F4F3EF; }}
    #status {{ position: fixed; left: 14px; bottom: 10px; color: #F4F3EF; font: 600 12px/1.2 system-ui, sans-serif; opacity: .7; }}
    video {{ display: none; }}
  </style>
</head>
<body>
  <canvas id="stage" width="1920" height="1080"></canvas>
  <video id="v1" src="{v1_rel}" preload="auto" muted playsinline></video>
  <video id="v2" src="{v2_rel}" preload="auto" muted playsinline></video>
  <div id="status">carregando vídeos e áudios para concatenação…</div>
  <script>
    const canvas = document.querySelector('#stage');
    const ctx = canvas.getContext('2d', {{ alpha: false }});
    const statusNode = document.querySelector('#status');
    const v1 = document.querySelector('#v1');
    const v2 = document.querySelector('#v2');

    const DURATION_V1 = {d1:.4f};
    const DURATION_V2 = {d2:.4f};
    const AUDIO1_ORIGIN = {a1_origin:.4f};
    const TOTAL_DURATION = {total_d:.4f};

    async function waitReady(video) {{
      if (video.readyState >= 3) return;
      return new Promise((resolve, reject) => {{
        video.addEventListener('canplay', resolve, {{ once: true }});
        video.addEventListener('error', () => reject(new Error('Erro ao carregar ' + video.src)), {{ once: true }});
      }});
    }}

    async function loadAudioBuffer(ctx, url) {{
      const response = await fetch(url);
      if (!response.ok) throw new Error('HTTP ' + response.status + ' carregando ' + url);
      const data = await response.arrayBuffer();
      return ctx.decodeAudioData(data);
    }}

    async function start() {{
      statusNode.textContent = 'carregando buffers…';
      const audioCtx = new AudioContext({{ sampleRate: 48000 }});
      await audioCtx.resume();

      const [buf1, buf2] = await Promise.all([
        loadAudioBuffer(audioCtx, '{a1_rel}'),
        loadAudioBuffer(audioCtx, '{a2_rel}'),
        waitReady(v1),
        waitReady(v2)
      ]);

      statusNode.textContent = `V1=${{DURATION_V1.toFixed(2)}}s | V2=${{DURATION_V2.toFixed(2)}}s | Total=${{TOTAL_DURATION.toFixed(2)}}s`;

      const audioDest = audioCtx.createMediaStreamDestination();

      const src1 = audioCtx.createBufferSource();
      src1.buffer = buf1;
      src1.connect(audioDest);

      const src2 = audioCtx.createBufferSource();
      src2.buffer = buf2;
      src2.connect(audioDest);

      const videoStream = canvas.captureStream(30);
      const combinedStream = new MediaStream([
        ...videoStream.getVideoTracks(),
        ...audioDest.stream.getAudioTracks()
      ]);

      const preferred = [
        'video/webm;codecs=vp9,opus',
        'video/webm;codecs=vp8,opus',
        'video/webm'
      ];
      const mimeType = preferred.find(type => MediaRecorder.isTypeSupported(type)) || '';
      const recorder = new MediaRecorder(combinedStream, {{
        mimeType,
        videoBitsPerSecond: 8000000,
        audioBitsPerSecond: 192000
      }});

      const chunks = [];
      recorder.ondataavailable = event => {{ if (event.data.size) chunks.push(event.data); }};
      recorder.onerror = event => fetch('/error', {{ method: 'POST', body: String(event.error || event) }});
      recorder.onstop = async () => {{
        const blob = new Blob(chunks, {{ type: recorder.mimeType || 'video/webm' }});
        await fetch('/save', {{
          method: 'POST',
          headers: {{
            'Content-Type': blob.type,
            'X-Duration': String(TOTAL_DURATION),
            'X-Duration-V1': String(DURATION_V1),
            'X-Duration-V2': String(DURATION_V2),
            'X-Width': String(canvas.width),
            'X-Height': String(canvas.height),
            'X-Fps': '30',
            'X-Silent': 'false'
          }},
          body: blob
        }});
      }};

      // Renderiza primeiro frame de V1 no canvas
      ctx.drawImage(v1, 0, 0, 1920, 1080);

      recorder.start(1000);

      const startAt = audioCtx.currentTime + 0.15;
      // Inicia áudio 1 exatamente com o offset de render_origin_seconds
      src1.start(startAt, AUDIO1_ORIGIN, DURATION_V1);
      // Inicia áudio 2 imediatamente na fronteira exata de V1
      src2.start(startAt + DURATION_V1, 0, DURATION_V2);

      let phase = 1;
      let v1Started = false;
      let v2Started = false;

      function tick() {{
        const now = audioCtx.currentTime;
        const elapsed = now - startAt;

        if (elapsed >= 0 && !v1Started) {{
          v1Started = true;
          v1.currentTime = 0;
          v1.play();
        }}

        if (elapsed < DURATION_V1) {{
          if (v1Started) {{
            ctx.drawImage(v1, 0, 0, 1920, 1080);
          }}
          statusNode.textContent = `S001–S003 · ${{Math.max(0, elapsed).toFixed(2)}}s / ${{DURATION_V1.toFixed(2)}}s`;
        }} else if (elapsed < TOTAL_DURATION) {{
          if (!v2Started) {{
            v2Started = true;
            phase = 2;
            v1.pause();
            v2.currentTime = 0;
            v2.play();
          }}
          ctx.drawImage(v2, 0, 0, 1920, 1080);
          const v2Elapsed = elapsed - DURATION_V1;
          statusNode.textContent = `S004–S006 · ${{v2Elapsed.toFixed(2)}}s / ${{DURATION_V2.toFixed(2)}}s (Total: ${{elapsed.toFixed(2)}}s)`;
        }} else {{
          if (phase === 2) {{
            phase = 3;
            v2.pause();
            statusNode.textContent = 'concatenação concluída! Finalizando gravação…';
            setTimeout(() => recorder.stop(), 200);
            return;
          }}
        }}

        requestAnimationFrame(tick);
      }}

      requestAnimationFrame(tick);
    }}

    start().catch(err => {{
      statusNode.textContent = 'Erro: ' + err.message;
      fetch('/error', {{ method: 'POST', body: err.stack || String(err) }});
    }});
  </script>
</body>
</html>
"""
    output_file.write_text(html, encoding="utf-8")


def handler_for(output: Path):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length)
            if self.path == "/save":
                output.write_bytes(payload)
                ConcatState.headers = {
                    "duration_seconds": self.headers.get("X-Duration", ""),
                    "duration_v1": self.headers.get("X-Duration-V1", ""),
                    "duration_v2": self.headers.get("X-Duration-V2", ""),
                    "width": self.headers.get("X-Width", ""),
                    "height": self.headers.get("X-Height", ""),
                    "fps": self.headers.get("X-Fps", ""),
                    "mime_type": self.headers.get("Content-Type", ""),
                }
                self.send_response(204)
                self.end_headers()
                ConcatState.done.set()
                return
            if self.path == "/error":
                ConcatState.error = payload.decode("utf-8", errors="replace")
                self.send_response(204)
                self.end_headers()
                ConcatState.done.set()
                return
            self.send_error(404)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=int, default=240)
    args = parser.parse_args()

    for path in (VIDEO1_PATH, VIDEO2_PATH, AUDIO1_PATH, AUDIO2_PATH):
        if not path.is_file():
            raise ConcatError(f"Arquivo necessário ausente: {path}")

    # Lê metadados dos vídeos originais para usar valores oficiais certificados
    meta1 = json.loads((PILOT1_DIR / "renders" / "render_metadata.json").read_text(encoding="utf-8-sig"))
    meta2 = json.loads((PILOT2_DIR / "renders" / "render_metadata.json").read_text(encoding="utf-8-sig"))

    d1 = float(meta1["renders"]["audiovisual"]["duration_seconds"])  # 18.699s
    a1_origin = float(meta1["renders"]["audiovisual"].get("render_origin_seconds", 0.101))
    d2 = float(meta2["renders"]["audiovisual"]["duration_seconds"])  # 27.6022s

    RENDERS_DIR.mkdir(parents=True, exist_ok=True)
    browser = find_browser()

    concat_html = PILOT2_DIR / "concat_player.html"
    v1_rel = "/" + VIDEO1_PATH.resolve().relative_to(ROOT).as_posix()
    v2_rel = "/" + VIDEO2_PATH.resolve().relative_to(ROOT).as_posix()
    a1_rel = "/" + AUDIO1_PATH.resolve().relative_to(ROOT).as_posix()
    a2_rel = "/" + AUDIO2_PATH.resolve().relative_to(ROOT).as_posix()

    generate_concat_html(concat_html, v1_rel, v2_rel, a1_rel, a2_rel, d1, d2, a1_origin)

    ConcatState.done.clear()
    ConcatState.error = None
    ConcatState.headers = {}

    handler = functools.partial(handler_for(OUTPUT_PATH), directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    profile = Path(tempfile.mkdtemp(prefix="co-concat-s001-s006-"))
    process: subprocess.Popen[bytes] | None = None
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    html_url_path = concat_html.resolve().relative_to(ROOT).as_posix()

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
            f"http://127.0.0.1:{port}/{html_url_path}",
        ]
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not ConcatState.done.wait(args.timeout):
            raise ConcatError(f"Concatenação excedeu {args.timeout}s.")
        if ConcatState.error:
            raise ConcatError(f"Erro na concatenação: {ConcatState.error}")
        if not OUTPUT_PATH.is_file() or OUTPUT_PATH.stat().st_size < 200_000:
            raise ConcatError("O navegador não produziu um WebM sequencial válido.")
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
    metadata["renders"]["sequential_s001_s006"] = {
        "file": OUTPUT_PATH.relative_to(ROOT).as_posix(),
        "size_bytes": OUTPUT_PATH.stat().st_size,
        "duration_seconds": float(ConcatState.headers["duration_seconds"]),
        "duration_v1": float(ConcatState.headers["duration_v1"]),
        "duration_v2": float(ConcatState.headers["duration_v2"]),
        "width": int(ConcatState.headers["width"]),
        "height": int(ConcatState.headers["height"]),
        "fps": int(ConcatState.headers["fps"]),
        "silent": False,
        "mime_type": ConcatState.headers["mime_type"],
        "source_v1": VIDEO1_PATH.relative_to(ROOT).as_posix(),
        "source_v2": VIDEO2_PATH.relative_to(ROOT).as_posix(),
        "method": "browser_headless_seamless_media_stream_concat",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    METADATA_FILE.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"PILOTO SEQUENCIAL S001–S006 CONCATENADO — {OUTPUT_PATH.relative_to(ROOT)}")
    print(
        f"{ConcatState.headers['width']}x{ConcatState.headers['height']} | "
        f"Duração total: {float(ConcatState.headers['duration_seconds']):.4f}s "
        f"(S001–S003: {float(ConcatState.headers['duration_v1']):.4f}s + S004–S006: {float(ConcatState.headers['duration_v2']):.4f}s)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConcatError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
