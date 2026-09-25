#!/usr/bin/env python3
"""Gera instâncias dos masters S005/S006 e valida o contrato no browser."""

from __future__ import annotations

import functools
import hashlib
import html
import http.server
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / "tests" / "visual_geometry_master_promotion"
INSTANCES = TEST_DIR / "instances"
RESULT = TEST_DIR / "master_audit_results.json"
MASTERS = {
    "S005": ROOT / "assets" / "compositions" / "system_map" / "CO-COMP-06A.svg",
    "S006": ROOT / "assets" / "compositions" / "moving_baseline" / "CO-COMP-04D.svg",
}
TEST_MASTERS = {
    "S005": ROOT / "tests" / "editorial_compositions_v1" / "masters" / "CO-COMP-06A.svg",
    "S006": ROOT / "tests" / "editorial_compositions_v1" / "masters" / "CO-COMP-04D.svg",
}
INSTANCE_PATHS = {
    "S005": INSTANCES / "s005_from_master.svg",
    "S006": INSTANCES / "s006_from_master.svg",
}
BROWSERS = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


class ValidationError(RuntimeError):
    pass


class State:
    done = threading.Event()
    result: dict | None = None
    error: str | None = None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(path: Path) -> dict:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    node = root.find("{http://www.w3.org/2000/svg}metadata")
    if node is None or not node.text:
        raise ValidationError(f"Metadata ausente: {path.relative_to(ROOT)}")
    return json.loads(html.unescape(node.text))


def browser() -> Path:
    for candidate in BROWSERS:
        if candidate.is_file():
            return candidate
    raise ValidationError("Edge ou Chrome não encontrado.")


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
            elif self.path == "/error":
                State.error = payload.decode("utf-8", errors="replace")
                self.send_response(204)
                self.end_headers()
                State.done.set()
            else:
                self.send_error(404)

    return Handler


def run_browser_audit() -> dict:
    State.done.clear()
    State.result = None
    State.error = None
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(handler(), directory=str(ROOT))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    profile = Path(tempfile.mkdtemp(prefix="co-master-geometry-"))
    process = None
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/tests/visual_geometry_master_promotion/master_audit.html"
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        process = subprocess.Popen(
            [str(browser()), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile}", url],
            cwd=ROOT,
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not State.done.wait(120):
            raise ValidationError("Auditoria dos masters excedeu 120s.")
        if State.error:
            raise ValidationError(State.error)
        if State.result is None:
            raise ValidationError("Browser não devolveu resultado.")
        return State.result
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


def main() -> int:
    INSTANCES.mkdir(parents=True, exist_ok=True)
    for scene_id, master in MASTERS.items():
        if not master.is_file():
            raise ValidationError(f"Master ausente: {master.relative_to(ROOT)}")
        shutil.copyfile(master, INSTANCE_PATHS[scene_id])

    expected = {"S005": ("CO-COMP-06A", 1.1), "S006": ("CO-COMP-04D", 1.2)}
    for scene_id, (composition_id, version) in expected.items():
        data = metadata(MASTERS[scene_id])
        if data.get("composition_id") != composition_id or data.get("version") != version:
            raise ValidationError(f"Versão incorreta em {composition_id}.")
        if data.get("geometry_change_reason") != "VISUAL_GEOMETRY_MASTER_DEFECT":
            raise ValidationError(f"Reason ausente em {composition_id}.")
        if data.get("geometry_contract") != "VISUAL_GEOMETRY_CONTRACT@1.0":
            raise ValidationError(f"Contrato ausente em {composition_id}.")
        if data.get("instance_geometry_override") is not False:
            raise ValidationError(f"Override indevido em {composition_id}.")
        if sha256(MASTERS[scene_id]) != sha256(INSTANCE_PATHS[scene_id]):
            raise ValidationError(f"Instância {scene_id} diverge do master.")
        if sha256(MASTERS[scene_id]) != sha256(TEST_MASTERS[scene_id]):
            raise ValidationError(f"Cópia de teste {scene_id} diverge do master oficial.")

    catalog = json.loads((ROOT / "config" / "visual_compositions.json").read_text(encoding="utf-8"))
    catalog_by_id = {item["id"]: item for item in catalog["compositions"]}
    for _scene_id, (composition_id, version) in expected.items():
        item = catalog_by_id[composition_id]
        if item.get("version") != version or item.get("geometry_change_reason") != "VISUAL_GEOMETRY_MASTER_DEFECT":
            raise ValidationError(f"Catálogo divergente em {composition_id}.")

    result = run_browser_audit()
    errors = {scene["scene_id"]: scene["errors"] for scene in result["scenes"]}
    if errors != {"S005": 0, "S006": 0}:
        raise ValidationError(f"Erros geométricos: {errors}")
    result["master_versions"] = {"CO-COMP-06A": 1.1, "CO-COMP-04D": 1.2}
    result["master_geometry_promoted"] = True
    result["instance_hash_matches_master"] = {scene_id: True for scene_id in MASTERS}
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("CO-COMP-06A_VERSION=1.1")
    print("CO-COMP-04D_VERSION=1.2")
    print("MASTER_GEOMETRY_PROMOTED=true")
    print("S005_ERRORS=0")
    print("S006_ERRORS=0")
    print("INSTANCE_GEOMETRY_OVERRIDE_S005=false")
    print("INSTANCE_GEOMETRY_OVERRIDE_S006=false")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, ValueError, KeyError, json.JSONDecodeError, ET.ParseError) as exc:
        print(f"MASTER_GEOMETRY_VALIDATION=FAIL: {exc}")
        raise SystemExit(2)
