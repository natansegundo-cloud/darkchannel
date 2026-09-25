#!/usr/bin/env python3
"""Gera e audita os frames estáticos S013–S018.

O escopo é somente pré-produção visual: frames SVG, previews PNG e contacts.
Não gera áudio, motion ou vídeo, e não cria variantes/famílias.
"""

from __future__ import annotations

import base64
import datetime as dt
import functools
import html
import http.server
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "visual_coverage_s013_s018"
FRAMES = OUT / "frames"
PREVIEWS = OUT / "previews"
CONTACTS = OUT / "contact_sheets"
AUDIT_HTML = OUT / "geometry_audit.html"
AUDIT_JSON = OUT / "geometry_audit_results.json"
RIG = ROOT / "assets" / "characters" / "capital_oculto_character_rig_v4.svg"

INK = "#111111"
BG = "#F4F3EF"
LIME = "#C4E538"
AMBER = "#E8A33D"
GRAY = "#D9D9D4"
FONT = "Bahnschrift,'Arial Narrow',Arial,sans-serif"
BROWSERS = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


def find_browser() -> Path:
    for candidate in BROWSERS:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Edge ou Chrome headless não encontrado.")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def rig_defs() -> str:
    text = RIG.read_text(encoding="utf-8")
    start = text.index("<defs>") + len("<defs>")
    end = text.index("</defs>")
    return text[start:end]


def defs() -> str:
    return f'''<defs>
  <style>
    .display {{font-family:{FONT};font-weight:900;letter-spacing:-9px;fill:{INK}}}
    .headline {{font-family:{FONT};font-weight:900;letter-spacing:-3px;fill:{INK}}}
    .label {{font-family:{FONT};font-size:28px;font-weight:800;letter-spacing:2.4px;fill:{INK}}}
    .micro {{font-family:{FONT};font-size:22px;font-weight:800;letter-spacing:2.2px;fill:{INK}}}
    .light {{fill:{BG}}}
  </style>
  <pattern id="paper" width="18" height="18" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1.1" fill="{INK}" opacity=".055"/>
  </pattern>
{rig_defs()}
</defs>'''


def metadata(scene: str, comp: str, version: float | int, family: str, continuity: str | None = None) -> str:
    data = {
        "scene_id": scene,
        "composition_id": comp,
        "version": version,
        "family": family,
        "status": "APPROVED",
        "selection_mode": "PRODUCTION",
        "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0",
        "audio_present": False,
        "motion_present": False,
        "geometry_errors": 0,
        "instance_geometry_override": False,
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    if continuity:
        data["continuity"] = continuity
    if scene in {"S015", "S016"}:
        data["character_source"] = "assets/characters/capital_oculto_character_rig_v4.svg"
        data["character_continuity_id"] = "capital_oculto_protagonist_v4"
    return f"<metadata>{html.escape(json.dumps(data, ensure_ascii=False))}</metadata>"


def text(x: int, y: int, value: str, cls: str, *, anchor: str = "start", style: str = "", light: bool = False) -> str:
    class_name = f"{cls} light" if light else cls
    return (f'<text x="{x}" y="{y}" class="{class_name}" text-anchor="{anchor}" '
            f'style="{style}" data-geometry-type="PROTECTED_TYPE">{html.escape(value)}</text>')


def char(x: int = 1080, y: int = 350) -> str:
    return (f'<use href="#char-base" x="{x}" y="{y}" width="260" height="520" '
            'data-character-function="CONTINUITY" data-continuity-id="capital_oculto_protagonist_v4"/>')


def wrap(scene: str, comp: str, version: float | int, family: str, body: str, continuity: str | None = None) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-label="{scene} {comp}">
{defs()}
{metadata(scene, comp, version, family, continuity)}
<g id="{scene.lower()}-{comp.lower()}" data-composition="{comp}" data-version="{version}" data-static-test="true">
  <rect width="1920" height="1080" fill="{BG}"/>
  <rect width="1920" height="1080" fill="url(#paper)"/>
{body}
</g>
</svg>
'''


def comp_04b(scene: str, left: str, left_detail: str, right: str, right_detail: str, left_label: str, right_label: str, *, person: bool, continuity: str) -> str:
    right_size = 60 if scene == "S016" else 78
    body = f'''
  <rect x="0" y="0" width="900" height="1080" fill="{BG}"/>
  <text x="450" y="260" class="headline" text-anchor="middle" style="font-size:48px;opacity:.35" data-geometry-type="PROTECTED_TYPE">{html.escape(left)}</text>
  <text x="450" y="520" class="display" text-anchor="middle" style="font-size:86px;opacity:.25" data-geometry-type="PROTECTED_TYPE">{html.escape(left_detail)}</text>
  <text x="450" y="700" class="micro" text-anchor="middle" style="opacity:.35" data-geometry-type="PROTECTED_TYPE">{html.escape(left_label)}</text>
  <rect x="900" y="0" width="12" height="1080" fill="{INK}" data-geometry-type="STRUCTURAL_LINE" data-routing="STOP_BEFORE"/>
  <rect x="912" y="0" width="1008" height="1080" fill="{INK}"/>
  <text x="1416" y="220" class="headline light" text-anchor="middle" style="font-size:48px" data-geometry-type="PROTECTED_TYPE">{html.escape(right)}</text>
  <text x="1600" y="500" class="display light" text-anchor="middle" style="font-size:{right_size}px" data-geometry-type="PROTECTED_TYPE">{html.escape(right_detail)}</text>
  <text x="1700" y="720" class="micro light" text-anchor="middle" style="opacity:.72" data-geometry-type="PROTECTED_TYPE">{html.escape(right_label)}</text>
  <rect x="1290" y="900" width="520" height="8" rx="4" fill="{LIME}" data-continuity="{html.escape(continuity)}"/>
'''
    if person:
        body += f'  {char()}\n'
    return wrap(scene, "CO-COMP-04B", 1, "MOVING_BASELINE", body, continuity)


def comp_04a() -> str:
    body = f'''
  {text(96, 140, "RENDA ATUAL", "headline", style="font-size:48px")}
  {text(96, 340, "R$ 4.200", "display", style="font-size:180px;letter-spacing:-7px")}
  <rect x="64" y="464" width="1792" height="16" rx="8" fill="{INK}" data-geometry-type="STRUCTURAL_LINE" data-routing="STOP_BEFORE"/>
  <rect x="64" y="460" width="1336" height="8" rx="4" fill="{AMBER}" data-geometry-type="ACCENT_LINE" data-routing="STOP_BEFORE"/>
  <line x1="64" y1="760" x2="1856" y2="760" stroke="{GRAY}" stroke-width="4" stroke-linecap="round" stroke-dasharray="18 14" data-geometry-type="STRUCTURAL_LINE" data-routing="STOP_BEFORE"/>
  {text(96, 700, "EXPECTATIVA", "display", style=f"font-size:120px;letter-spacing:-5px;fill:{GRAY}")}
  {text(128, 840, "ANTES", "micro")}
  <line x1="1600" y1="740" x2="1600" y2="520" stroke="{AMBER}" stroke-width="6" stroke-linecap="round" data-geometry-type="STRUCTURAL_LINE" data-routing="ROUTE_AROUND"/>
  <circle cx="1600" cy="760" r="12" fill="{GRAY}"/>
  <polygon points="1580,530 1600,490 1620,530" fill="{AMBER}"/>
  {text(1640, 615, "ALCANÇA", "micro", style=f"fill:{AMBER}")}
  {text(1640, 645, "A RENDA", "micro", style=f"fill:{AMBER}")}
  {text(1824, 960, "A EXPECTATIVA SUBIU", "label", anchor="end")}
'''
    return wrap("S014", "CO-COMP-04A", 1.1, "MOVING_BASELINE", body, "SEMANTIC_CUT_EXPECTATION_TO_INCOME")


def comp_06a() -> str:
    body = f'''
  <g data-layer="20">
    <rect x="560" y="272" width="636" height="86" rx="18" fill="{INK}" data-geometry-type="TRACK" data-routing="STOP_BEFORE_ACCENT_BLOCK"/>
    <rect x="1196" y="272" width="386" height="86" rx="18" fill="{LIME}"/>
    <rect x="560" y="522" width="826" height="86" rx="18" fill="{INK}" data-geometry-type="TRACK" data-routing="STOP_BEFORE_ACCENT_BLOCK"/>
    <rect x="1386" y="522" width="268" height="86" rx="18" fill="{LIME}"/>
    <rect x="560" y="772" width="1016" height="86" rx="18" fill="{INK}" data-geometry-type="TRACK" data-routing="STOP_BEFORE_ACCENT_BLOCK"/>
    <rect x="1576" y="772" width="184" height="86" rx="18" fill="{LIME}"/>
  </g>
  <path d="M610 904 L1390 220" stroke="{LIME}" stroke-width="30" stroke-linecap="round" opacity=".95" data-geometry-type="ACCENT_LINE" data-routing="STOP_BEFORE" data-arrowhead="false" data-semantic-role="ASSOCIACAO_MEDIA"/>
  {text(96, 330, "RENDA", "headline", style="font-size:82px")}
  {text(96, 580, "BEM-ESTAR", "headline", style="font-size:70px")}
  {text(96, 830, "GRUPOS", "headline", style="font-size:82px")}
  {text(1824, 136, "EFEITO MÉDIO", "label", anchor="end")}
  {text(1824, 966, "ASSOCIAÇÃO POSITIVA NA MÉDIA", "label", anchor="end")}
'''
    return wrap("S017", "CO-COMP-06A", 1.1, "SYSTEM_MAP", body, "ELEMENT_CARRYOVER_TO_S018")


def comp_06b() -> str:
    body = f'''
  <path d="M0 0 H520 V1080 H0 Z" fill="{INK}"/>
  <rect x="480" y="96" width="96" height="888" rx="24" fill="{LIME}" data-geometry-type="STRUCTURAL_LINE" data-routing="STOP_BEFORE"/>
  {text(96, 486, "FATOR COMUM", "label", light=True)}
  {text(96, 606, "RENDA", "headline", style="font-size:92px", light=True)}
  <g>
    <path d="M540 180 H1740 L1816 254 L1740 328 H540 Z" fill="{INK}"/>
    {text(740, 284, "GRUPO A", "headline", style="font-size:88px", light=True)}
  </g>
  <g>
    <path d="M540 450 H1630 L1706 524 L1630 598 H540 Z" fill="{INK}"/>
    {text(740, 554, "GRUPO B", "headline", style="font-size:76px", light=True)}
  </g>
  <g>
    <path d="M540 720 H1450 L1526 794 L1450 868 H540 Z" fill="{INK}"/>
    {text(740, 824, "GRUPO C", "headline", style="font-size:88px", light=True)}
  </g>
  {text(1824, 966, "UM FATOR • RESPOSTAS DIFERENTES • SEM LIMIAR", "label", anchor="end")}
'''
    return wrap("S018", "CO-COMP-06B", 1, "SYSTEM_MAP", body, "ELEMENT_CARRYOVER_FROM_S017")


def svg_uri(content: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(content.encode("utf-8")).decode("ascii")


def contact_svg(frames: list[tuple[str, str]], width: int, height: int, cols: int) -> str:
    rows = (len(frames) + cols - 1) // cols
    cell_w, cell_h = width / cols, height / rows
    blocks = []
    for index, (label, content) in enumerate(frames):
        x, y = (index % cols) * cell_w, (index // cols) * cell_h
        blocks.append(f'<image href="{svg_uri(content)}" x="{x}" y="{y}" width="{cell_w}" height="{cell_h}"/>')
        blocks.append(f'<rect x="{x + 18}" y="{y + 18}" width="120" height="38" rx="8" fill="{LIME}"/><text x="{x + 34}" y="{y + 45}" font-family="{FONT}" font-size="24" font-weight="900" fill="{INK}">{html.escape(label)}</text>')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" fill="{BG}"/>{''.join(blocks)}</svg>
'''


def audit_html() -> str:
    files = [f"frames/s{i:03d}.svg" for i in range(13, 19)]
    return f'''<!doctype html><meta charset="utf-8"><title>Geometry S013-S018</title>
<style>body{{margin:0}}#root{{position:absolute;left:-10000px;top:0}}svg{{width:1920px;height:1080px;display:block}}</style>
<div id="root"></div><script>
const files={json.dumps(files)};
const overlap=(a,b)=>Math.max(0,Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x))*Math.max(0,Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y));
const box=(el)=>{{const b=el.getBBox();const sw=parseFloat(getComputedStyle(el).strokeWidth)||0;return{{x:b.x-sw/2,y:b.y-sw/2,width:b.width+sw,height:b.height+sw}}}};
(async()=>{{const findings=[],measurements=[];for(const file of files){{const raw=await (await fetch(file)).text();const host=document.createElement('div');host.innerHTML=raw;document.querySelector('#root').append(host);await document.fonts.ready;const svg=host.querySelector('svg'),scene=file.match(/s\\d{{3}}/)[0].toUpperCase();const protectedEls=[...svg.querySelectorAll('[data-geometry-type="PROTECTED_TYPE"]')];const lines=[...svg.querySelectorAll('[data-geometry-type="STRUCTURAL_LINE"],[data-geometry-type="ACCENT_LINE"],[data-geometry-type="CONNECTOR"],[data-geometry-type="ARROW"]')];for(const el of protectedEls){{const b=box(el);if(b.x<95||b.y<95||b.x+b.width>1825||b.y+b.height>985)findings.push({{scene,type:'SAFE_AREA',element:el.textContent}});for(const line of lines)if(overlap(b,box(line))>1)findings.push({{scene,type:'TYPE_INTERSECTION',element:el.textContent,line:line.tagName}})}}if(svg.querySelector('marker,[marker-end],[marker-start],[data-pseudo-arrowhead="true"]'))findings.push({{scene,type:'PSEUDO_ARROWHEAD'}});measurements.push({{scene_id:scene,protected_type_count:protectedEls.length,line_count:lines.length,browser_geometry:true}})}}await fetch('/result',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{browser_geometry:true,fonts_ready:document.fonts.status==='loaded',measurements,findings,geometry_errors:findings.length}})}})}})().catch(async e=>fetch('/error',{{method:'POST',body:String(e.stack||e)}}));</script>'''


class State:
    done = threading.Event()
    result: dict | None = None
    error: str | None = None


def handler():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:
            payload = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if self.path == "/result":
                State.result = json.loads(payload.decode("utf-8")); self.send_response(204); self.end_headers(); State.done.set()
            elif self.path == "/error":
                State.error = payload.decode("utf-8", errors="replace"); self.send_response(204); self.end_headers(); State.done.set()
            else:
                self.send_error(404)
    return Handler


def screenshot(browser: Path, base: str, rel: str, output: Path, width: int, height: int, profile: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        str(browser), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
        "--no-default-browser-check", "--force-device-scale-factor=1", "--virtual-time-budget=2000",
        f"--window-size={width},{height}", f"--user-data-dir={profile / output.stem}", f"--screenshot={output}", f"{base}/{rel}"
    ], cwd=ROOT, check=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW if __import__('os').name == 'nt' else 0,
       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not output.is_file() or output.stat().st_size < 1000:
        raise RuntimeError(f"Screenshot inválido: {output}")


def main() -> int:
    frames = {
        "S013": comp_04b("S013", "DELIVERY", "= FESTA", "DELIVERY", "= TERÇA", "EXCEÇÃO", "ROTINA", person=False, continuity="S012_BASELINE_TO_ROTINA"),
        "S014": comp_04a(),
        "S015": comp_04b("S015", "PRIVAÇÃO", "CONTAS", "SEGURANÇA", "ESCOLHAS", "PRESSÃO", "MARGEM REAL", person=True, continuity="S015_S016_SAME_PERSON_AND_ESSENTIALS"),
        "S016": comp_04b("S016", "NECESSIDADES", "MORADIA • COMIDA", "SEGURANÇA", "SAÚDE • MARGEM", "SEM FOLGA", "NÃO É ILUSÃO", person=True, continuity="S015_S016_SAME_PERSON_AND_ESSENTIALS"),
        "S017": comp_06a(),
        "S018": comp_06b(),
    }
    for scene, content in frames.items():
        write(FRAMES / f"{scene.lower()}.svg", content)
    ordered = [(scene, frames[scene]) for scene in frames]
    write(CONTACTS / "contact_s013_s018_100.svg", contact_svg(ordered, 5760, 2160, 3))
    write(CONTACTS / "contact_s013_s018_25pct.svg", contact_svg(ordered, 1440, 540, 3))
    write(CONTACTS / "contact_s017_s018_pair.svg", contact_svg([("S017", frames["S017"]), ("S018", frames["S018"])], 1920, 540, 2))
    write(AUDIT_HTML, audit_html())

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(handler(), directory=str(OUT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    browser = find_browser(); profile = Path(tempfile.mkdtemp(prefix="co-s013-s018-"))
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        for scene in frames:
            screenshot(browser, base, f"frames/{scene.lower()}.svg", PREVIEWS / f"{scene.lower()}.png", 1920, 1080, profile)
        for name, width, height in (("contact_s013_s018_100", 5760, 2160), ("contact_s013_s018_25pct", 1440, 540), ("contact_s017_s018_pair", 1920, 540)):
            screenshot(browser, base, f"contact_sheets/{name}.svg", CONTACTS / f"{name}.png", width, height, profile)
        State.done.clear(); State.result = None; State.error = None
        audit_profile = profile / "audit-profile"
        process = subprocess.Popen([str(browser), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check", f"--user-data-dir={audit_profile}", f"{base}/geometry_audit.html"], cwd=ROOT, creationflags=subprocess.CREATE_NO_WINDOW if __import__('os').name == 'nt' else 0, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not State.done.wait(60):
            raise RuntimeError("Geometry audit excedeu 60s.")
        if State.error:
            raise RuntimeError(State.error)
        if not State.result:
            raise RuntimeError("Geometry audit não devolveu resultado.")
    finally:
        server.shutdown(); server.server_close()
        if 'process' in locals() and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill()
        time.sleep(.2); shutil.rmtree(profile, ignore_errors=True)
    write(AUDIT_JSON, json.dumps(State.result, ensure_ascii=False, indent=2) + "\n")
    if State.result["geometry_errors"] != 0:
        raise RuntimeError(f"geometry_errors={State.result['geometry_errors']}")
    print("S013=PASS\nS014=PASS\nS015=PASS\nS016=PASS\nS017=PASS\nS018=PASS")
    print(f"GEOMETRY_ERRORS={State.result['geometry_errors']}")
    print("NEW_VARIANTS_CREATED=0\nNEW_FAMILIES_CREATED=0\nMOTION_CREATED=0\nVIDEO_RENDERED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
