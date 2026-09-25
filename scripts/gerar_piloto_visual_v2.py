#!/usr/bin/env python3
"""Gera o piloto visual V2 do Capital Oculto sem alterar as cenas V1."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from xml.sax.saxutils import escape

from validar_rig_personagem import validate_rig


ROOT = Path(__file__).resolve().parents[1]
STYLE_FILE = ROOT / "config" / "vector_style_v2.json"
RIG_FILE = ROOT / "assets" / "characters" / "capital_oculto_character_rig_v4.svg"
ICON_ROOT = ROOT / "assets" / "icons" / "phosphor" / "regular"
OUTPUT_DIR = ROOT / "assets" / "scenes" / "CO-001" / "v2"
PILOT_SCENES = ("S001", "S007", "S033")
ICON_NAMES = ("device-mobile", "trend-up", "ruler", "receipt")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def attrs(**values: Any) -> str:
    result = []
    for key, value in values.items():
        if value is None:
            continue
        key = key.rstrip("_").replace("__", ":").replace("_", "-")
        result.append(f'{key}="{escape(str(value), {"\"": "&quot;"})}"')
    return " ".join(result)


def tag(name: str, content: str = "", **values: Any) -> str:
    properties = attrs(**values)
    if content:
        return f"<{name} {properties}>{content}</{name}>" if properties else f"<{name}>{content}</{name}>"
    return f"<{name} {properties}/>" if properties else f"<{name}/>"


def group(content: str, **values: Any) -> str:
    return tag("g", content, **values)


def text_node(x: float, y: float, value: str, css: str, **values: Any) -> str:
    return tag("text", escape(value), x=x, y=y, class_=css, **values)


def extract_defs(path: Path) -> str:
    source = path.read_text(encoding="utf-8-sig")
    match = re.search(r"<defs>(.*)</defs>", source, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"SVG sem defs: {path}")
    return match.group(1).strip()


def icon_symbol(name: str) -> str:
    path = ICON_ROOT / f"{name}.svg"
    source = path.read_text(encoding="utf-8-sig")
    view_box = re.search(r'viewBox="([^"]+)"', source)
    body = re.search(r"<svg[^>]*>(.*)</svg>", source, flags=re.DOTALL)
    if not view_box or not body:
        raise RuntimeError(f"Ícone SVG inválido: {path}")
    colored_body = group(body.group(1), fill="currentColor")
    return tag("symbol", colored_body, id_=f"icon-{name}", viewBox=view_box.group(1))


def common_defs(style: dict[str, Any]) -> str:
    p = style["palette"]
    t = style["typography"]
    css = f"""
    .title {{ font-family:{t['family']}; font-size:{t['headline_size']}px; font-weight:800; letter-spacing:{t['tracking']}px; fill:{p['ink']}; }}
    .support {{ font-family:{t['family']}; font-size:{t['support_size']}px; font-weight:700; fill:{p['ink']}; }}
    .micro {{ font-family:{t['family']}; font-size:30px; font-weight:800; letter-spacing:1.2px; fill:{p['ink']}; }}
    .micro-light {{ font-family:{t['family']}; font-size:30px; font-weight:800; letter-spacing:1.2px; fill:{p['background']}; }}
    .line {{ fill:none; stroke:{p['ink']}; stroke-width:6; stroke-linecap:round; stroke-linejoin:round; }}
    .detail {{ fill:none; stroke:{p['ink']}; stroke-width:3; stroke-linecap:round; stroke-linejoin:round; }}
    """
    shadow = tag(
        "filter",
        tag("feDropShadow", dx=0, dy=4, stdDeviation=0, flood_color=p["ink"], flood_opacity=.15),
        id="main-shadow",
        x="-10%",
        y="-10%",
        width="120%",
        height="125%",
    )
    marker = tag(
        "marker",
        tag("path", d="M 0 0 L 14 7 L 0 14 Z", fill=p["lime"]),
        id="arrow-lime",
        viewBox="0 0 14 14",
        refX=12,
        refY=7,
        markerWidth=10,
        markerHeight=10,
        orient="auto",
    )
    return tag("defs", tag("style", css) + shadow + marker + extract_defs(RIG_FILE) + "".join(icon_symbol(name) for name in ICON_NAMES))


def background(style: dict[str, Any]) -> str:
    p = style["palette"]
    base = tag("rect", x=0, y=0, width=1920, height=1080, fill=p["background"])
    grain = "".join(tag("circle", cx=x, cy=y, r=1.4, fill=p["ink"], opacity=.055) for x in range(82, 1900, 92) for y in range(78, 1060, 92))
    return base + grain


def character_use(x: float, y: float, height: float, instance_id: str, *, flip: bool = False) -> str:
    width = height / 2
    content = tag("use", href="#char-base", x=0, y=0, width=width, height=height)
    transform = f"translate({x + width} {y}) scale(-1 1)" if flip else f"translate({x} {y})"
    return group(content, id_=instance_id, transform=transform, data_rig="char-base")


def icon_use(name: str, x: float, y: float, size: float, color: str, instance_id: str) -> str:
    return tag("use", href=f"#icon-{name}", x=x, y=y, width=size, height=size, id_=instance_id, style=f"color:{color}")


def scene_001(style: dict[str, Any]) -> str:
    p = style["palette"]
    title = text_node(96, 145, "SEU SALÁRIO AUMENTOU", "title")
    underline = tag("path", d="M 98 180 L 720 180", fill="none", stroke=p["lime"], stroke_width=12, stroke_linecap="round")
    actor = character_use(145, 315, 700, "char-s001")
    panel = tag("rect", x=925, y=225, width=780, height=730, rx=42, fill=p["ink"], filter="url(#main-shadow)")
    phone = icon_use("device-mobile", 1110, 300, 410, p["background"], "phone-s001")
    card = tag("rect", x=1040, y=610, width=550, height=190, rx=24, fill=p["background"])
    trend = icon_use("trend-up", 1090, 650, 105, p["lime"], "trend-s001")
    notification = text_node(1230, 705, "AUMENTO", "support") + text_node(1230, 760, "CONFIRMADO", "micro")
    echo = tag("circle", cx=1315, cy=575, r=245, fill="none", stroke=p["lime"], stroke_width=6, opacity=.24)
    return background(style) + title + underline + actor + panel + echo + phone + card + trend + notification


def scene_007(style: dict[str, Any]) -> str:
    p = style["palette"]
    title = text_node(96, 145, "O NORMAL SE MOVE", "title")
    actor = character_use(1390, 320, 690, "char-s007", flip=True)
    panel = tag("rect", x=110, y=255, width=1110, height=690, rx=42, fill=p["ink"], filter="url(#main-shadow)")
    ruler = icon_use("ruler", 350, 330, 560, p["background"], "ruler-s007")
    old = tag("path", d="M 255 815 L 640 815", fill="none", stroke=p["background"], stroke_width=6, stroke_dasharray="15 18", opacity=.42)
    now = tag("path", d="M 735 435 L 1040 435", fill="none", stroke=p["lime"], stroke_width=14, stroke_linecap="round")
    route = tag("path", d="M 605 785 Q 730 650 860 485", fill="none", stroke=p["lime"], stroke_width=12, stroke_linecap="round", marker_end="url(#arrow-lime)")
    labels = text_node(255, 875, "ANTES", "micro-light") + text_node(905, 395, "AGORA", "micro-light")
    return background(style) + title + panel + ruler + old + route + now + labels + actor


def scene_033(style: dict[str, Any]) -> str:
    p = style["palette"]
    title = text_node(96, 145, "SOBROU R$ 50", "title")
    actor = character_use(125, 325, 690, "char-s033")
    receipt = icon_use("receipt", 745, 250, 260, p["ink"], "receipt-s033")
    total = text_node(1050, 335, "R$ 1.000", "support")
    committed = tag("rect", x=710, y=555, width=855, height=112, rx=12, fill=p["ink"])
    remainder = tag("rect", x=1581, y=555, width=45, height=112, rx=12, fill=p["lime"])
    frame = tag("rect", x=690, y=535, width=956, height=152, rx=24, fill="none", stroke=p["ink"], stroke_width=6, filter="url(#main-shadow)")
    focus = tag("path", d="M 1604 510 L 1604 420", fill="none", stroke=p["lime"], stroke_width=12, stroke_linecap="round", marker_end="url(#arrow-lime)")
    remaining_label = text_node(1420, 385, "5% LIVRE", "support")
    caption = text_node(710, 780, "950 JÁ TÊM DESTINO", "support")
    return background(style) + title + actor + receipt + total + frame + committed + remainder + focus + remaining_label + caption


RENDERERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "S001": scene_001,
    "S007": scene_007,
    "S033": scene_033,
}


def svg_document(content: str, style: dict[str, Any], scene_id: str) -> str:
    metadata = {
        "episode_id": "CO-001",
        "scene_id": scene_id,
        "style_id": style["style_id"],
        "canvas": "1920x1080",
        "character": "char-base",
        "character_rig_version": 4,
        "icon_library": "Phosphor Icons",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img">\n'
        + tag("metadata", escape(json.dumps(metadata, ensure_ascii=False, sort_keys=True)))
        + common_defs(style)
        + content
        + "\n</svg>\n"
    )


def review_board(style: dict[str, Any]) -> str:
    p = style["palette"]
    cards = ""
    for index, scene_id in enumerate(PILOT_SCENES):
        x = 66 + index * 620
        cards += tag("rect", x=x, y=230, width=578, height=348, rx=24, fill=p["background"], stroke=p["ink"], stroke_width=6)
        cards += tag("image", href=f"{scene_id.lower()}.svg", x=x+9, y=239, width=560, height=315, preserveAspectRatio="xMidYMid meet")
        cards += tag("rect", x=x+18, y=190, width=116, height=48, rx=12, fill=p["ink"])
        cards += tag("text", scene_id, x=x+76, y=224, text_anchor="middle", font_family="Segoe UI, Arial, sans-serif", font_size=25, font_weight=800, fill=p["background"])
    title = tag("text", "CAPITAL OCULTO — PILOTO VISUAL V2", x=66, y=105, font_family="Segoe UI, Arial, sans-serif", font_size=66, font_weight=800, letter_spacing=-1.5, fill=p["ink"])
    subtitle = tag("text", "RIG V4: 1 SYMBOL + 8 GROUPS · PHOSPHOR · LONG-FORM 1920×1080", x=70, y=158, font_family="Segoe UI, Arial, sans-serif", font_size=28, font_weight=700, fill=p["ink"], opacity=.66)
    notes = (
        tag("text", "01  CHAR-BASE: ÚNICO SYMBOL", x=92, y=720, font_family="Segoe UI, Arial, sans-serif", font_size=28, font_weight=800, fill=p["ink"])
        + tag("text", "02  PRETO + 1 DESTAQUE", x=686, y=720, font_family="Segoe UI, Arial, sans-serif", font_size=28, font_weight=800, fill=p["ink"])
        + tag("text", "03  ATÉ 2 BLOCOS", x=1306, y=720, font_family="Segoe UI, Arial, sans-serif", font_size=28, font_weight=800, fill=p["ink"])
    )
    footer = tag("rect", x=66, y=835, width=1788, height=150, rx=24, fill=p["ink"]) + tag("text", "VALIDAR A LINGUAGEM ANTES DE MIGRAR AS 48 CENAS", x=960, y=927, text_anchor="middle", font_family="Segoe UI, Arial, sans-serif", font_size=46, font_weight=800, fill=p["background"])
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tag("svg", tag("rect", x=0, y=0, width=1920, height=1080, fill=p["background"]) + title + subtitle + cards + notes + footer, xmlns="http://www.w3.org/2000/svg", width=1920, height=1080, viewBox="0 0 1920 1080") + "\n"


def safe_write(path: Path, content: str, update: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not update:
        return "preservado"
    existed = path.exists()
    path.write_text(content, encoding="utf-8", newline="\n")
    return "atualizado" if existed else "criado"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera o piloto visual V2 sem alterar as cenas V1.")
    parser.add_argument("--atualizar", action="store_true", help="Atualiza os arquivos V2 existentes.")
    args = parser.parse_args()
    validate_rig(RIG_FILE)
    style = load_json(STYLE_FILE)
    manifest = {
        "style_id": style["style_id"],
        "episode_id": "CO-001",
        "character_contract": "char-base=symbol; body-parts=groups",
        "dependencies": {
            "character_rig": {
                "version": 4,
                "file": str(RIG_FILE.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(RIG_FILE.read_bytes()).hexdigest(),
            },
            "icons": [
                {
                    "library": "Phosphor Icons",
                    "license": "MIT",
                    "name": name,
                    "file": str((ICON_ROOT / f"{name}.svg").relative_to(ROOT)).replace("\\", "/"),
                    "sha256": hashlib.sha256((ICON_ROOT / f"{name}.svg").read_bytes()).hexdigest(),
                }
                for name in ICON_NAMES
            ],
        },
        "scenes": [],
    }
    for scene_id in PILOT_SCENES:
        output = OUTPUT_DIR / f"{scene_id.lower()}.svg"
        status = safe_write(output, svg_document(RENDERERS[scene_id](style), style, scene_id), args.atualizar)
        manifest["scenes"].append({"scene_id": scene_id, "file": str(output.relative_to(ROOT)).replace("\\", "/"), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
        print(f"{scene_id}: {status} -> {output.relative_to(ROOT)}")
    board = OUTPUT_DIR / "review_v2_pilot.svg"
    print(f"BOARD: {safe_write(board, review_board(style), args.atualizar)} -> {board.relative_to(ROOT)}")
    safe_write(OUTPUT_DIR / "pilot_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
