#!/usr/bin/env python3
"""Gera e audita a cobertura visual estática S007–S012.

Escopo: reutilizar CO-COMP-04B/04D, criar somente CO-COMP-03D,
exportar frames/contact sheets e executar geometry audit em browser real.
Não gera áudio, motion ou vídeo.
"""

from __future__ import annotations

import base64
import functools
import html
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "visual_compositions.json"
RULES = ROOT / "config" / "visual_composition_rules.json"
MASTER_03D = ROOT / "assets" / "compositions" / "shrinking_space" / "CO-COMP-03D.svg"
OUT = ROOT / "tests" / "visual_coverage_s007_s012"
FRAMES = OUT / "frames"
PREVIEWS = OUT / "previews"
CONTACTS = OUT / "contact_sheets"
AUDIT_HTML = OUT / "geometry_audit.html"
AUDIT_JSON = OUT / "geometry_audit_results.json"

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


def browser() -> Path:
    for candidate in BROWSERS:
        if candidate.is_file():
            return candidate
    raise RuntimeError("Edge ou Chrome headless não encontrado.")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


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
</defs>'''


def metadata(scene: str | None, comp: str, version: float | int, family: str) -> str:
    data = {
        "scene_id": scene,
        "composition_id": comp,
        "version": version,
        "family": family,
        "status": "EXPERIMENTAL",
        "selection_mode": "EXPERIMENTAL_TEST",
        "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0",
        "audio_present": False,
        "motion_present": False,
        "instance_geometry_override": False,
    }
    return f"<metadata>{html.escape(json.dumps(data, ensure_ascii=False))}</metadata>"


def wrap(scene: str | None, comp: str, version: float | int, family: str, body: str) -> str:
    label = scene or "MASTER"
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-label="{label} {comp}">
{defs()}
{metadata(scene, comp, version, family)}
<g id="{label.lower()}-{comp.lower()}" data-composition="{comp}" data-version="{version}" data-static-test="true">
  <rect width="1920" height="1080" fill="{BG}"/>
  <rect width="1920" height="1080" fill="url(#paper)"/>
{body}
</g>
</svg>
'''


def protected_text(x: int, y: int, text: str, cls: str, style: str = "", anchor: str = "start", opacity: str = "1") -> str:
    return (f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" opacity="{opacity}" '
            f'style="{style}" data-geometry-type="PROTECTED_TYPE">{html.escape(text)}</text>')


def baseline_scene(scene: str, old_label: str, old_word: str, new_label: str, new_word: str, interpretation: str, footer: str) -> str:
    body = f'''
  <g data-layer="20" data-protect-primary-type="true">
    <path d="M-40 990 L48 990" stroke="{INK}" stroke-width="36" stroke-linecap="round" data-geometry-type="STRUCTURAL_LINE" data-routing="STOP_BEFORE"/>
    <path d="M540 970 L1020 511" stroke="{INK}" stroke-width="36" stroke-linecap="round" data-geometry-type="STRUCTURAL_LINE" data-routing="ROUTE_AROUND"/>
    <path d="M1020 511 L1824 511" stroke="{LIME}" stroke-width="18" stroke-linecap="round" data-geometry-type="ACCENT_LINE" data-routing="TRANSFORM_TO_UNDERLINE" data-arrowhead="false"/>
  </g>
  <g opacity=".48">
    {protected_text(96, 774, old_label, 'label')}
    {protected_text(96, 928, old_word, 'display', 'font-size:132px;letter-spacing:-6px')}
  </g>
  {protected_text(1824, 154, new_label, 'label', anchor='end')}
  {protected_text(1788, 438, new_word, 'display', 'font-size:252px;letter-spacing:-14px', 'end')}
  {protected_text(1788, 636, interpretation, 'headline', 'font-size:66px', 'end')}
  {protected_text(1788, 964, footer, 'label', anchor='end')}
'''
    return wrap(scene, "CO-COMP-04D", 1.2, "MOVING_BASELINE", body)


def phone(x: int, intensity: str, accent: str) -> str:
    halo_opacity = ".95" if intensity == "high" else ".12"
    body_opacity = "1" if intensity == "high" else ".42"
    rays = "".join(
        f'<line x1="{x + ax}" y1="{ay}" x2="{x + bx}" y2="{by}" stroke="{accent}" stroke-width="12" stroke-linecap="round" opacity="{halo_opacity}" data-geometry-type="ACCENT_LINE" data-routing="STOP_BEFORE" data-arrowhead="false"/>'
        for ax, ay, bx, by in [(-190,260,-130,300),(190,260,130,300),(-210,520,-145,500),(210,520,145,500)]
    )
    return f'''<g opacity="{body_opacity}" data-object-id="phone-shared">
      {rays}
      <rect x="{x - 130}" y="250" width="260" height="500" rx="48" fill="{INK}"/>
      <rect x="{x - 108}" y="284" width="216" height="410" rx="28" fill="{BG}"/>
      <circle cx="{x}" cy="720" r="12" fill="{BG}"/>
      <circle cx="{x}" cy="360" r="74" fill="{accent}" opacity="{halo_opacity}"/>
      <rect x="{x - 70}" y="468" width="140" height="18" rx="9" fill="{INK}" opacity=".72"/>
      <rect x="{x - 50}" y="510" width="100" height="18" rx="9" fill="{INK}" opacity=".42"/>
    </g>'''


def phone_pair_scene(scene: str, focus: str) -> str:
    left_high = focus == "day1"
    left_opacity = "1" if left_high else ".38"
    right_opacity = ".32" if left_high else "1"
    divider = f'<rect x="954" y="96" width="12" height="888" rx="6" fill="{INK}" data-geometry-type="STRUCTURAL_LINE" data-routing="STOP_BEFORE"/>'
    body = f'''
  <rect x="0" y="0" width="960" height="1080" fill="{BG}"/>
  <rect x="960" y="0" width="960" height="1080" fill="{INK}" opacity="{'.06' if left_high else '.92'}"/>
  {divider}
  <g opacity="{left_opacity}">
    {protected_text(96, 154, 'PRIMEIRO CONTATO', 'label')}
    {phone(480, 'high' if left_high else 'low', LIME)}
    {protected_text(480, 884, 'EXCEPCIONAL', 'headline', 'font-size:68px', 'middle')}
    {protected_text(480, 960, 'DIA 1', 'label', anchor='middle')}
  </g>
  <g opacity="{right_opacity}">
    {protected_text(1824, 154, 'MESMO APARELHO', 'label light' if not left_high else 'label', anchor='end')}
    {phone(1440, 'low', GRAY if not left_high else INK)}
    {protected_text(1440, 884, 'ROTINA', 'headline light' if not left_high else 'headline', 'font-size:68px', 'middle')}
    {protected_text(1440, 960, 'DIA 30', 'label light' if not left_high else 'label', anchor='middle')}
  </g>
'''
    return wrap(scene, "CO-COMP-04B", 1, "MOVING_BASELINE", body)


def decay_body(title: str) -> str:
    return f'''
  {protected_text(96, 142, title, 'label')}
  <g data-layer="30">
    <path d="M144 536 C210 226 306 226 372 536 C438 846 534 846 624 536 L624 810 L144 810 Z" fill="{INK}" data-geometry-type="DATA_MASS"/>
    <path d="M720 596 C786 376 882 376 948 596 C1014 816 1110 816 1200 596 L1200 810 L720 810 Z" fill="{INK}" opacity=".76" data-geometry-type="DATA_MASS"/>
    <path d="M1296 656 C1362 526 1458 526 1524 656 C1590 786 1686 786 1776 656 L1776 810 L1296 810 Z" fill="{INK}" opacity=".48" data-geometry-type="DATA_MASS"/>
  </g>
  <line x1="144" y1="828" x2="1776" y2="828" stroke="{LIME}" stroke-width="14" stroke-linecap="round" data-geometry-type="ACCENT_LINE" data-routing="STOP_BEFORE" data-arrowhead="false"/>
  {protected_text(384, 758, 'ALTA', 'headline light', 'font-size:72px', 'middle')}
  {protected_text(960, 758, 'MÉDIA', 'headline light', 'font-size:64px', 'middle')}
  {protected_text(1536, 758, 'BAIXA', 'headline light', 'font-size:56px', 'middle')}
  {protected_text(144, 942, 'ESTADO 1', 'label')}
  {protected_text(960, 942, 'ESTADO 2', 'label', anchor='middle')}
  {protected_text(1776, 942, 'ESTADO 3', 'label', anchor='end')}
  {protected_text(1776, 972, 'A MESMA EMOÇÃO PERDE INTENSIDADE', 'micro', anchor='end')}
'''


def decay_scene(scene: str | None = "S010") -> str:
    return wrap(scene, "CO-COMP-03D", 1.0, "SHRINKING_SPACE", decay_body("INTENSIDADE AO LONGO DO TEMPO"))


def comparison_scene() -> str:
    left_bars = "".join(f'<rect x="{180+i*170}" y="{330+i*100}" width="110" height="{420-i*100}" rx="18" fill="{INK}" opacity="{1-i*.18}" data-geometry-type="DATA_MASS"/>' for i in range(4))
    right_bars = "".join(f'<rect x="{1110+i*170}" y="{630-i*100}" width="110" height="{120+i*100}" rx="18" fill="{LIME}" data-geometry-type="DATA_MASS"/>' for i in range(4))
    body = f'''
  <rect x="0" y="0" width="960" height="1080" fill="{BG}"/>
  <rect x="960" y="0" width="960" height="1080" fill="{INK}"/>
  <rect x="954" y="96" width="12" height="888" rx="6" fill="{AMBER}" data-geometry-type="STRUCTURAL_LINE" data-routing="STOP_BEFORE"/>
  {protected_text(96, 154, 'ROTA A', 'label')}
  {protected_text(96, 260, 'EMOÇÃO', 'headline', 'font-size:92px')}
  {left_bars}
  {protected_text(864, 944, 'PERDE FORÇA', 'label', anchor='end')}
  {protected_text(1824, 154, 'ROTA B', 'label light', anchor='end')}
  {protected_text(1056, 260, 'ASPIRAÇÃO', 'headline light', 'font-size:92px')}
  {right_bars}
  {protected_text(1056, 944, 'GANHA ALTURA', 'label light')}
'''
    return wrap("S011", "CO-COMP-04B", 1, "MOVING_BASELINE", body)


def svg_uri(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def contact_svg(frames: list[tuple[str, str]], width: int, height: int, cols: int) -> str:
    rows = (len(frames) + cols - 1) // cols
    cell_w, cell_h = width / cols, height / rows
    images = []
    for i, (label, content) in enumerate(frames):
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        tag_w, tag_h = cell_w * .08, cell_h * .045
        margin = cell_w * .012
        font_size = cell_h * .026
        images.append(f'<image href="{svg_uri(content)}" x="{x}" y="{y}" width="{cell_w}" height="{cell_h}"/>')
        images.append(f'<rect x="{x+margin}" y="{y+margin}" width="{tag_w}" height="{tag_h}" rx="{tag_h*.24}" fill="{LIME}"/><text x="{x+margin+tag_w*.14}" y="{y+margin+tag_h*.72}" class="tag" style="font-size:{font_size}px">{label}</text>')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>.tag{{font-family:{FONT};font-size:28px;font-weight:900;fill:{INK}}}</style>
<rect width="100%" height="100%" fill="{BG}"/>{''.join(images)}</svg>'''


def audit_html() -> str:
    scene_files = [f"frames/s{i:03d}.svg" for i in range(7, 13)]
    return f'''<!doctype html><meta charset="utf-8"><title>Geometry S007-S012</title>
<style>body{{margin:0}}#root{{position:absolute;left:-10000px;top:0}}svg{{width:1920px;height:1080px;display:block}}</style>
<div id="root"></div><script>
const files={json.dumps(scene_files)};
const overlap=(a,b)=>Math.max(0,Math.min(a.x+a.width,b.x+b.width)-Math.max(a.x,b.x))*Math.max(0,Math.min(a.y+a.height,b.y+b.height)-Math.max(a.y,b.y));
const box=(el)=>{{const b=el.getBBox();const sw=parseFloat(getComputedStyle(el).strokeWidth)||0;return{{x:b.x-sw/2,y:b.y-sw/2,width:b.width+sw,height:b.height+sw}}}};
(async()=>{{
  const findings=[],measurements=[];
  for(const file of files){{
    const text=await (await fetch(file)).text();
    const host=document.createElement('div');host.innerHTML=text;document.querySelector('#root').append(host);
    await document.fonts.ready;
    const svg=host.querySelector('svg'), scene=file.match(/s\\d{{3}}/)[0].toUpperCase();
    const protectedEls=[...svg.querySelectorAll('[data-geometry-type="PROTECTED_TYPE"]')];
    const lineEls=[...svg.querySelectorAll('[data-geometry-type="STRUCTURAL_LINE"],[data-geometry-type="ACCENT_LINE"],[data-geometry-type="TRACK"],[data-geometry-type="CONNECTOR"],[data-geometry-type="ARROW"]')];
    for(const t of protectedEls){{
      const b=box(t);if(b.x<95||b.y<95||b.x+b.width>1825||b.y+b.height>985)findings.push({{scene_id:scene,type:'SAFE_AREA',element:t.textContent}});
      for(const line of lineEls)if(overlap(b,box(line))>1)findings.push({{scene_id:scene,type:'TYPE_INTERSECTION',element:t.textContent,line:line.tagName}});
    }}
    if(svg.querySelector('marker, [marker-end], [marker-start], [data-pseudo-arrowhead="true"]'))findings.push({{scene_id:scene,type:'PSEUDO_ARROWHEAD'}});
    for(const c of svg.querySelectorAll('[data-geometry-type="CONNECTOR"]'))if(!c.dataset.semanticRole)findings.push({{scene_id:scene,type:'CONNECTOR_WITHOUT_SEMANTIC_ROLE'}});
    measurements.push({{scene_id:scene,protected_type_count:protectedEls.length,line_count:lineEls.length,browser_geometry:true}});
  }}
  await fetch('/result',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{browser_geometry:true,fonts_ready:document.fonts.status==='loaded',measurements,findings,errors:findings.length}})}});
}})().catch(async e=>fetch('/error',{{method:'POST',body:String(e.stack||e)}}));
</script>'''


class AuditState:
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
                AuditState.result = json.loads(payload.decode("utf-8"))
                self.send_response(204); self.end_headers(); AuditState.done.set()
            elif self.path == "/error":
                AuditState.error = payload.decode("utf-8", errors="replace")
                self.send_response(204); self.end_headers(); AuditState.done.set()
            else:
                self.send_error(404)
    return Handler


def screenshot(browser_path: Path, base_url: str, rel_svg: str, output: Path, width: int, height: int, profile_root: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    profile = profile_root / (output.stem + "-profile")
    cmd = [str(browser_path), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           "--no-default-browser-check", "--force-device-scale-factor=1", "--virtual-time-budget=2000", f"--window-size={width},{height}",
           f"--user-data-dir={profile}", f"--screenshot={output}", f"{base_url}/{rel_svg}"]
    subprocess.run(cmd, cwd=ROOT, check=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not output.is_file() or output.stat().st_size < 1000:
        raise RuntimeError(f"Screenshot inválido: {output}")


def validate_catalog() -> None:
    catalog = json.loads(CONFIG.read_text(encoding="utf-8"))["compositions"]
    matches = [x for x in catalog if x["id"] == "CO-COMP-03D"]
    if len(matches) != 1 or matches[0]["status"] != "EXPERIMENTAL" or matches[0]["family"] != "SHRINKING_SPACE":
        raise ValueError("Contrato de CO-COMP-03D inválido no catálogo.")
    if sum(x["id"].endswith("03D") for x in catalog) != 1:
        raise ValueError("Mais de uma variante 03D detectada.")
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    route = rules["mechanisms"]["progressive_loss"]["variant_routing"].get("temporal_decay")
    if route != "CO-COMP-03D":
        raise ValueError("Roteamento temporal_decay não aponta para CO-COMP-03D.")


def main() -> int:
    validate_catalog()
    frames = {
        "S007": baseline_scene("S007", "REFERÊNCIA", "ANTIGA", "NOVO", "NORMAL", "A RÉGUA SUBIU", "O NORMAL SE MOVE"),
        "S008": phone_pair_scene("S008", "day1"),
        "S009": phone_pair_scene("S009", "day30"),
        "S010": decay_scene("S010"),
        "S011": comparison_scene(),
        "S012": baseline_scene("S012", "CONQUISTA", "EXTRA", "NOVA ORIGEM", "BASE", "PONTO DE PARTIDA", "O NOVO NORMAL VIROU A ORIGEM"),
    }
    write(MASTER_03D, decay_scene(None))
    for scene, content in frames.items():
        write(FRAMES / f"{scene.lower()}.svg", content)

    ordered = [(scene, frames[scene]) for scene in sorted(frames)]
    write(CONTACTS / "contact_s007_s012_100.svg", contact_svg(ordered, 5760, 2160, 3))
    write(CONTACTS / "contact_s007_s012_25pct.svg", contact_svg(ordered, 1440, 540, 3))
    write(CONTACTS / "contact_s008_s009_pair.svg", contact_svg([(s, frames[s]) for s in ("S008", "S009")], 1920, 540, 2))
    write(AUDIT_HTML, audit_html())

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(handler(), directory=str(OUT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    browser_path = browser()
    profile_root = Path(tempfile.mkdtemp(prefix="co-s007-s012-"))
    audit_process = None
    try:
        for scene in sorted(frames):
            screenshot(browser_path, base_url, f"frames/{scene.lower()}.svg", PREVIEWS / f"{scene.lower()}.png", 1920, 1080, profile_root)
        for name, width, height in (
            ("contact_s007_s012_100", 5760, 2160),
            ("contact_s007_s012_25pct", 1440, 540),
            ("contact_s008_s009_pair", 1920, 540),
        ):
            screenshot(browser_path, base_url, f"contact_sheets/{name}.svg", CONTACTS / f"{name}.png", width, height, profile_root)

        AuditState.done.clear(); AuditState.result = None; AuditState.error = None
        audit_profile = profile_root / "audit-profile"
        audit_process = subprocess.Popen(
            [str(browser_path), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
             "--no-default-browser-check", f"--user-data-dir={audit_profile}", f"{base_url}/geometry_audit.html"],
            cwd=ROOT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if not AuditState.done.wait(60):
            raise RuntimeError("Geometry audit excedeu 60s.")
        if AuditState.error:
            raise RuntimeError(AuditState.error)
        if not AuditState.result:
            raise RuntimeError("Geometry audit não devolveu resultado.")
    finally:
        server.shutdown(); server.server_close()
        if audit_process and audit_process.poll() is None:
            audit_process.terminate()
            try: audit_process.wait(timeout=5)
            except subprocess.TimeoutExpired: audit_process.kill()
        time.sleep(.2)
        shutil.rmtree(profile_root, ignore_errors=True)

    write(AUDIT_JSON, json.dumps(AuditState.result, ensure_ascii=False, indent=2) + "\n")
    if AuditState.result["errors"]:
        raise RuntimeError(f"Geometry audit falhou: {AuditState.result['findings']}")
    print("S007=PASS\nS008=PASS\nS009=PASS\nS010=PASS\nS011=PASS\nS012=PASS")
    print("NEW_VARIANTS_CREATED=1\nNEW_FAMILIES_CREATED=0")
    print(f"GEOMETRY_ERRORS={AuditState.result['errors']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, json.JSONDecodeError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
