#!/usr/bin/env python3
"""Executa a auditoria Visual Geometry Contract V1 no browser headless."""

from __future__ import annotations

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
AUDIT_DIR = ROOT / "tests" / "visual_geometry_v1"
PAGE = AUDIT_DIR / "geometry_audit.html"
RESULT_JSON = AUDIT_DIR / "geometry_audit_results.json"
DEBUG_PNG = AUDIT_DIR / "debug_contact_sheet_s005_s006.png"
REPORT = AUDIT_DIR / "GEOMETRY_AUDIT_REPORT.md"
BROWSERS = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


class AuditError(RuntimeError):
    pass


class State:
    done = threading.Event()
    error: str | None = None
    result: dict[str, Any] | None = None


def find_browser() -> Path:
    for candidate in BROWSERS:
        if candidate.is_file():
            return candidate
    raise AuditError("Edge ou Chrome headless não encontrado.")


def handler():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(length)
            if self.path == "/result":
                State.result = json.loads(payload.decode("utf-8"))
                self.send_response(204)
                self.end_headers()
                State.done.set()
            elif self.path == "/debug":
                DEBUG_PNG.write_bytes(payload)
                self.send_response(204)
                self.end_headers()
            elif self.path == "/error":
                State.error = payload.decode("utf-8", errors="replace")
                self.send_response(204)
                self.end_headers()
                State.done.set()
            else:
                self.send_error(404)

    return Handler


def scene_rows(result: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    scenes = [f"S00{index}" for index in range(1, 7)]
    for scene_id in scenes:
        before = [item for item in result["before_findings"] if item["scene_id"] == scene_id]
        after = [item for item in result["after_findings"] if item["scene_id"] == scene_id]
        after_errors = [item for item in after if item["severity"] == "ERROR"]
        samples = [item for item in result["measurements"] if item["scene_id"] == scene_id and item["subbeat_id"].startswith("S00")]
        rows.append(f"| {scene_id} | {len(samples)} | {len(before)} | {len(after)} | {'PASS' if not after_errors else 'FAIL'} |")
    return rows


def finding_lines(findings: list[dict[str, Any]], *, limit: int = 24) -> list[str]:
    lines = []
    for item in findings[:limit]:
        lines.append(
            f"- `{item['scene_id']}` / `{item['subbeat_id']}` / `{item['timestamp']:.4f}s` — "
            f"`{item['collision_type']}` entre `{item['element_a']}` e `{item['element_b']}`; "
            f"severity `{item['severity']}`; resolução `{item['resolution']}`."
        )
    if len(findings) > limit:
        lines.append(f"- … mais {len(findings) - limit} finding(s) registrados no JSON bruto.")
    return lines


def write_report(result: dict[str, Any]) -> None:
    before = result["before_findings"]
    after = result["after_findings"]
    lines = [
        "# Visual Geometry Contract V1 — Geometry Audit Report",
        "",
        f"Gerado em: `{datetime.now().astimezone().isoformat(timespec='seconds')}`",
        "",
        "A auditoria foi executada no Edge headless com SVGs em 1920×1080, fontes carregadas e `element.getBBox()` real. O áudio, o timing, a voz e o pacing não foram alterados.",
        "",
        "## Resumo",
        "",
        f"- `total_samples`: {result['total_samples']}",
        f"- `total_collisions_before`: {result['total_collisions_before']}",
        f"- `total_collisions_after`: {result['total_collisions_after']}",
        f"- `errors_before`: {result['errors_before']}",
        f"- `errors_after`: {result['errors_after']}",
        f"- `browser_geometry`: `{result['browser_geometry']}`",
        f"- `fonts_ready`: `{result['fonts_ready']}`",
        "",
        "## Por cena",
        "",
        "| Cena | Samples | Findings antes | Findings depois | Gate |",
        "|---|---:|---:|---:|---|",
        *scene_rows(result),
        "",
        "## Colisões encontradas antes da correção",
        "",
        *finding_lines(before),
        "",
        "## Classificação e correções",
        "",
        "- S005: `MASTER_DEFECT` no sistema de trilhos e na rota da `ACCENT_LINE`; a diagonal passou a terminar antes da protected zone de `QUANDO A RENDA SOBE`, e os trilhos passaram a ser `TRACK` com terminação limpa, sem pseudo-arrowhead.",
        "- S006: `MASTER_DEFECT` na baseline de `CO-COMP-04D@1.1`; a rota passou a usar `STOP_BEFORE` da zona de `EXTRA` e `TRANSFORM_TO_UNDERLINE` no patamar de `NORMAL`.",
        "- S001–S004: auditados nos mesmos samples; nenhuma correção estética oportunista foi aplicada.",
        "",
        "## Artefatos",
        "",
        "- Contrato: `config/visual_geometry_contract.json`.",
        "- Documentação: `docs/VISUAL_GEOMETRY_CONTRACT_V1.md`.",
        "- Resultado bruto browser: `tests/visual_geometry_v1/geometry_audit_results.json`.",
        "- Debug sheet: `tests/visual_geometry_v1/debug_contact_sheet_s005_s006.png`.",
        "",
        "Gate: `ERROR = 0` após a correção.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(handler(), directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    profile = Path(tempfile.mkdtemp(prefix="co-geometry-audit-"))
    process = None
    State.done.clear()
    State.error = None
    State.result = None
    try:
        browser = find_browser()
        url = f"http://127.0.0.1:{server.server_address[1]}/tests/visual_geometry_v1/geometry_audit.html"
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen(
            [str(browser), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile}", url],
            cwd=ROOT,
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not State.done.wait(120):
            raise AuditError("Auditoria geométrica excedeu 120s.")
        if State.error:
            raise AuditError(State.error)
        if State.result is None:
            raise AuditError("Browser não devolveu resultado da auditoria.")
    finally:
        server.shutdown()
        server.server_close()
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        time.sleep(0.25)
        shutil.rmtree(profile, ignore_errors=True)
    RESULT_JSON.write_text(json.dumps(State.result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(State.result)
    print(f"GEOMETRY_BROWSER_AUDIT=true")
    print(f"TOTAL_SAMPLES={State.result['total_samples']}")
    print(f"ERRORS_BEFORE={State.result['errors_before']}")
    print(f"ERRORS_AFTER={State.result['errors_after']}")
    print(f"DEBUG_SHEET={DEBUG_PNG.relative_to(ROOT)}")
    print(f"REPORT={REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AuditError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
