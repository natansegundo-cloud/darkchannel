#!/usr/bin/env python3
"""Gera o piloto do Visual System V3 sem alterar os sistemas anteriores."""

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
STYLE_FILE = ROOT / "config" / "vector_style_v3.json"
RIG_FILE = ROOT / "assets" / "characters" / "capital_oculto_character_rig_v4.svg"
ICON_ROOT = ROOT / "assets" / "icons" / "phosphor" / "regular"
OUTPUT_DIR = ROOT / "assets" / "scenes" / "CO-001" / "v3"
PILOT_SCENES = ("S001", "S007", "S033")
ICON_NAMES = ("device-mobile", "trend-up", "ruler", "receipt")
SCENE_SPECS: dict[str, dict[str, Any]] = {
    "S001": {
        "layout": "A",
        "accent": "lime",
        "character_present": True,
        "icons": ("device-mobile", "trend-up"),
        "dominant_visual": "phone_notification",
        "context_element": "character",
    },
    "S007": {
        "layout": "B",
        "accent": "amber",
        "character_present": False,
        "icons": ("ruler",),
        "dominant_visual": "moving_normality_ruler",
        "context_element": "before_after_labels",
        "arrow_marker": True,
    },
    "S033": {
        "layout": "E",
        "accent": "lime",
        "character_present": False,
        "icons": ("receipt",),
        "dominant_visual": "remaining_fifty",
        "context_element": "commitment_bar",
    },
}


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


def common_defs(style: dict[str, Any], spec: dict[str, Any]) -> str:
    p = style["palette"]
    t = style["typography"]
    css = f"""
    .title {{ font-family:{t['family']}; font-size:{t['headline_size']}px; font-weight:{t['headline_weight']}; letter-spacing:{t['headline_tracking']}px; fill:{p['ink']}; }}
    .support {{ font-family:{t['family']}; font-size:{t['support_size']}px; font-weight:{t['support_weight']}; fill:{p['ink']}; }}
    .micro {{ font-family:{t['family']}; font-size:{t['label_size']}px; font-weight:{t['label_weight']}; letter-spacing:.8px; fill:{p['ink']}; }}
    .micro-light {{ font-family:{t['family']}; font-size:{t['label_size']}px; font-weight:{t['label_weight']}; letter-spacing:.8px; fill:{p['background']}; }}
    .number {{ font-family:{t['family']}; font-size:260px; font-weight:900; letter-spacing:-8px; font-variant-numeric:tabular-nums; fill:{p['lime']}; }}
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
    marker = ""
    if spec.get("arrow_marker"):
        marker = tag(
            "marker",
            tag("path", d="M 0 0 L 14 7 L 0 14 Z", fill=p[spec["accent"]]),
            id="arrow-accent",
            viewBox="0 0 14 14",
            refX=12,
            refY=7,
            markerWidth=10,
            markerHeight=10,
            orient="auto",
        )
    rig = extract_defs(RIG_FILE) if spec["character_present"] else ""
    icons = "".join(icon_symbol(name) for name in spec["icons"])
    return tag("defs", tag("style", css) + shadow + marker + rig + icons)


def background(style: dict[str, Any]) -> str:
    p = style["palette"]
    base = tag("rect", x=0, y=0, width=1920, height=1080, fill=p["background"])
    grain = "".join(tag("circle", cx=x, cy=y, r=1.4, fill=p["ink"], opacity=.055) for x in range(82, 1900, 92) for y in range(78, 1060, 92))
    return base + grain


def character_use(x: float, y: float, height: float, instance_id: str, *, flip: bool = False) -> str:
    width = height / 2
    content = tag("use", href="#char-base", x=0, y=0, width=width, height=height)
    transform = f"translate({x + width} {y}) scale(-1 1)" if flip else f"translate({x} {y})"
    visual_height = round(height * 589 / 640)
    return group(content, id_=instance_id, transform=transform, data_rig="char-base", data_visual_height=visual_height)


def icon_use(name: str, x: float, y: float, size: float, color: str, instance_id: str) -> str:
    return tag("use", href=f"#icon-{name}", x=x, y=y, width=size, height=size, id_=instance_id, style=f"color:{color}")


def scene_001(style: dict[str, Any]) -> str:
    p = style["palette"]
    title = text_node(96, 150, "SEU SALÁRIO AUMENTOU", "title")
    underline = tag("path", d="M 98 190 L 770 190", fill="none", stroke=p["lime"], stroke_width=12, stroke_linecap="round")
    actor = character_use(150, 360, 560, "char-s001")
    panel = tag("rect", x=720, y=230, width=1136, height=770, rx=24, fill=p["ink"], filter="url(#main-shadow)")
    phone = icon_use("device-mobile", 1015, 285, 560, p["background"], "phone-s001")
    echo = tag("circle", cx=1295, cy=585, r=330, fill="none", stroke=p["lime"], stroke_width=6, opacity=.22)
    card = tag("rect", x=880, y=675, width=820, height=205, rx=20, fill=p["background"])
    trend = icon_use("trend-up", 950, 718, 120, p["lime"], "trend-s001")
    notification = text_node(1140, 770, "AUMENTO", "support") + text_node(1142, 825, "CONFIRMADO", "micro")
    return background(style) + title + underline + actor + panel + echo + phone + card + trend + notification


def scene_007(style: dict[str, Any]) -> str:
    p = style["palette"]
    title = text_node(96, 150, "O NORMAL SE MOVE", "title")
    ruler = icon_use("ruler", 390, 175, 880, p["ink"], "ruler-s007")
    old = tag("path", d="M 160 900 L 780 900", fill="none", stroke=p["ink"], stroke_width=6, stroke_dasharray="18 20", opacity=.28)
    now = tag("path", d="M 1190 285 L 1760 285", fill="none", stroke=p["amber"], stroke_width=16, stroke_linecap="round")
    route = tag("path", d="M 470 860 Q 900 650 1430 330", fill="none", stroke=p["amber"], stroke_width=24, stroke_linecap="round", marker_end="url(#arrow-accent)")
    labels = text_node(165, 955, "ANTES", "micro") + text_node(1590, 250, "AGORA", "micro")
    return background(style) + title + ruler + old + route + now + labels


def scene_033(style: dict[str, Any]) -> str:
    p = style["palette"]
    title = text_node(96, 145, "SOBROU", "title")
    number = text_node(96, 455, "R$ 50", "number")
    total = text_node(112, 535, "DE R$ 1.000", "support")
    receipt = icon_use("receipt", 1510, 120, 260, p["ink"], "receipt-s033")
    frame = tag("rect", x=96, y=650, width=1728, height=180, rx=24, fill="none", stroke=p["ink"], stroke_width=6, filter="url(#main-shadow)")
    committed = tag("rect", x=120, y=674, width=1573, height=132, rx=16, fill=p["ink"])
    remainder = tag("rect", x=1709, y=674, width=91, height=132, rx=16, fill=p["lime"])
    caption = text_node(120, 925, "950 JÁ TÊM DESTINO", "support")
    remaining_label = text_node(1590, 620, "5% LIVRE", "micro")
    return background(style) + title + number + total + receipt + frame + committed + remainder + caption + remaining_label


RENDERERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "S001": scene_001,
    "S007": scene_007,
    "S033": scene_033,
}


def svg_document(content: str, style: dict[str, Any], scene_id: str) -> str:
    spec = SCENE_SPECS[scene_id]
    metadata = {
        "episode_id": "CO-001",
        "scene_id": scene_id,
        "style_id": style["style_id"],
        "canvas": "1920x1080",
        "character": "char-base",
        "character_rig_version": 4,
        "character_present": spec["character_present"],
        "icon_library": "Phosphor Icons",
        "layout": spec["layout"],
        "accent": spec["accent"],
        "dominant_visual": spec["dominant_visual"],
        "context_element": spec["context_element"],
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img">\n'
        + tag("metadata", escape(json.dumps(metadata, ensure_ascii=False, sort_keys=True)))
        + common_defs(style, spec)
        + group(content, id_=f"scene-{scene_id}")
        + "\n</svg>\n"
    )


def review_board(style: dict[str, Any]) -> str:
    p = style["palette"]
    cards = ""
    layouts = ("A · PERSONAGEM + METÁFORA", "B · METÁFORA DOMINANTE", "E · NÚMERO DOMINANTE")
    for index, (scene_id, layout) in enumerate(zip(PILOT_SCENES, layouts)):
        x = 80 + index * 640
        cards += tag("rect", x=x-6, y=214, width=492, height=282, rx=20, fill=p["background"], stroke=p["ink"], stroke_width=4)
        cards += tag("image", href=f"{scene_id.lower()}.svg", x=x, y=220, width=480, height=270, preserveAspectRatio="xMidYMid meet")
        cards += tag("rect", x=x, y=172, width=108, height=44, rx=12, fill=p["ink"])
        cards += tag("text", scene_id, x=x+54, y=203, text_anchor="middle", font_family="Segoe UI, Arial, sans-serif", font_size=23, font_weight=800, fill=p["background"])
        cards += tag("text", layout, x=x, y=545, font_family="Segoe UI, Arial, sans-serif", font_size=25, font_weight=800, fill=p["ink"])
    title = tag("text", "CAPITAL OCULTO — VISUAL SYSTEM V3", x=64, y=90, font_family="Segoe UI, Arial, sans-serif", font_size=60, font_weight=900, letter_spacing=-1.5, fill=p["ink"])
    subtitle = tag("text", "VALIDAÇÃO EXATA A 25% · HIERARQUIA, ESCALA E COMPOSIÇÃO", x=68, y=140, font_family="Segoe UI, Arial, sans-serif", font_size=26, font_weight=700, fill=p["ink"], opacity=.66)
    notes = (
        tag("text", "1 IDEIA DOMINANTE", x=96, y=675, font_family="Segoe UI, Arial, sans-serif", font_size=34, font_weight=900, fill=p["ink"])
        + tag("text", "PERSONAGEM OPCIONAL", x=700, y=675, font_family="Segoe UI, Arial, sans-serif", font_size=34, font_weight=900, fill=p["ink"])
        + tag("text", "1 MOVIMENTO POR VEZ", x=1325, y=675, font_family="Segoe UI, Arial, sans-serif", font_size=34, font_weight=900, fill=p["ink"])
    )
    footer = tag("rect", x=64, y=790, width=1792, height=190, rx=24, fill=p["ink"]) + tag("text", "SE NÃO FUNCIONA PARADA, SEM ÁUDIO E PEQUENA: SIMPLIFICAR", x=960, y=905, text_anchor="middle", font_family="Segoe UI, Arial, sans-serif", font_size=42, font_weight=900, fill=p["background"])
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tag("svg", tag("rect", x=0, y=0, width=1920, height=1080, fill=p["background"]) + title + subtitle + cards + notes + footer, xmlns="http://www.w3.org/2000/svg", width=1920, height=1080, viewBox="0 0 1920 1080") + "\n"


def safe_write(path: Path, content: str, update: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not update:
        return "preservado"
    existed = path.exists()
    path.write_text(content, encoding="utf-8", newline="\n")
    return "atualizado" if existed else "criado"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera o piloto do Visual System V3 sem alterar os sistemas anteriores.")
    parser.add_argument("--atualizar", action="store_true", help="Atualiza os arquivos V3 existentes.")
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
        spec = SCENE_SPECS[scene_id]
        manifest["scenes"].append(
            {
                "scene_id": scene_id,
                "file": str(output.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "layout": spec["layout"],
                "accent": spec["accent"],
                "character_present": spec["character_present"],
                "icons": list(spec["icons"]),
                "dominant_visual": spec["dominant_visual"],
                "context_element": spec["context_element"],
            }
        )
        print(f"{scene_id}: {status} -> {output.relative_to(ROOT)}")
    board = OUTPUT_DIR / "review_v3_pilot_25.svg"
    print(f"BOARD: {safe_write(board, review_board(style), args.atualizar)} -> {board.relative_to(ROOT)}")
    safe_write(OUTPUT_DIR / "pilot_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
