#!/usr/bin/env python3
"""Gera as seis cenas consecutivas do teste audiovisual do Visual System V3."""

from __future__ import annotations

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
TEST_DIR = ROOT / "episodios" / "CO-001-por-que-ganhar-mais-nao-basta" / "testes" / "v3_sequencial_s001_s006"
EPISODE_DIR = TEST_DIR.parents[1]
RESOLVED_MANIFEST = EPISODE_DIR / "04A_SCENE_MANIFEST.json"
SCENE_DIR = TEST_DIR / "scenes"
PILOT_SCENES = ("S001", "S002", "S003", "S004", "S005", "S006")
COMPONENT_FILES = {
    "calendar": ROOT / "assets" / "components" / "v3" / "calendar_strip.svg",
    "triad": ROOT / "assets" / "metaphors" / "v3" / "mechanism_triad.svg",
    "brain": ROOT / "assets" / "metaphors" / "v3" / "brain_adaptation.svg",
}
SCENE_SPECS: dict[str, dict[str, Any]] = {
    "S001": {"layout": "A", "accent": "lime", "character": True, "icons": ("device-mobile", "trend-up"), "components": (), "continuity": "phone_to_s002"},
    "S002": {"layout": "F", "accent": "lime", "character": False, "icons": ("device-mobile",), "components": ("calendar",), "continuity": "phone_from_s001_to_s003"},
    "S003": {"layout": "A", "accent": "lime", "character": True, "icons": ("device-mobile",), "components": (), "continuity": "phone_from_s002_balance_to_s004"},
    "S004": {"layout": "D", "accent": "lime", "character": False, "icons": ("receipt",), "components": (), "continuity": "three_choices_to_s005"},
    "S005": {"layout": "C", "accent": "amber", "character": False, "icons": (), "components": ("triad",), "continuity": "three_mechanisms_to_s006"},
    "S006": {"layout": "A", "accent": "lime", "character": True, "icons": (), "components": ("brain",), "continuity": "triad_condenses_into_brain"},
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
    return tag("symbol", group(body.group(1), fill="currentColor"), id_=f"icon-{name}", viewBox=view_box.group(1))


def scene_defs(style: dict[str, Any], spec: dict[str, Any]) -> str:
    p = style["palette"]
    t = style["typography"]
    css = f"""
    .title {{ font-family:{t['family']}; font-size:96px; font-weight:900; letter-spacing:-1.8px; fill:{p['ink']}; }}
    .support {{ font-family:{t['family']}; font-size:48px; font-weight:700; fill:{p['ink']}; }}
    .label {{ font-family:{t['family']}; font-size:28px; font-weight:800; letter-spacing:.8px; fill:{p['ink']}; }}
    .label-light {{ font-family:{t['family']}; font-size:28px; font-weight:800; letter-spacing:.8px; fill:{p['background']}; }}
    .display {{ font-family:{t['family']}; font-size:142px; font-weight:900; letter-spacing:-4px; fill:{p['ink']}; }}
    """
    shadow = tag("filter", tag("feDropShadow", dx=0, dy=4, stdDeviation=0, flood_color=p["ink"], flood_opacity=.15), id="main-shadow", x="-10%", y="-10%", width="120%", height="125%")
    parts = [tag("style", css), shadow]
    if spec["character"]:
        parts.append(extract_defs(RIG_FILE))
    parts.extend(icon_symbol(name) for name in spec["icons"])
    parts.extend(extract_defs(COMPONENT_FILES[name]) for name in spec["components"])
    return tag("defs", "".join(parts))


def background(style: dict[str, Any]) -> str:
    p = style["palette"]
    dots = "".join(tag("circle", cx=x, cy=y, r=1.4, fill=p["ink"], opacity=.045) for x in range(82, 1900, 92) for y in range(78, 1060, 92))
    return tag("rect", x=0, y=0, width=1920, height=1080, fill=p["background"]) + dots


def use(href: str, x: float, y: float, width: float, height: float, color: str, instance_id: str) -> str:
    return tag("use", href=f"#{href}", x=x, y=y, width=width, height=height, id_=instance_id, style=f"color:{color}")


def character(x: float, y: float, height: float, instance_id: str) -> str:
    width = height / 2
    visual_height = round(height * 589 / 640)
    return group(tag("use", href="#char-base", x=0, y=0, width=width, height=height), id_=instance_id, transform=f"translate({x} {y})", data_rig="char-base", data_visual_height=visual_height)


def header(style: dict[str, Any], title: str, kicker: str, *, long: bool = False) -> str:
    p = style["palette"]
    title_style = "font-size:82px" if long else None
    return text_node(96, 142, title, "title", style=title_style) + tag("rect", x=96, y=176, width=230, height=12, rx=6, fill=p[kicker])


def scene_001(style: dict[str, Any]) -> str:
    p = style["palette"]
    panel = tag("rect", x=96, y=230, width=1120, height=754, rx=24, fill=p["ink"], filter="url(#main-shadow)")
    phone = use("icon-device-mobile", 356, 292, 480, 480, p["background"], "phone-s001")
    card = tag("rect", x=250, y=720, width=812, height=170, rx=20, fill=p["background"])
    trend = use("icon-trend-up", 310, 752, 110, 110, p["lime"], "trend-s001")
    copy = text_node(480, 790, "AUMENTO CONFIRMADO", "support") + text_node(482, 840, "A RENDA SUBIU", "label")
    actor = character(1440, 374, 560, "char-s001")
    return background(style) + header(style, "SEU SALÁRIO AUMENTOU", "lime") + panel + phone + card + trend + copy + actor


def scene_002(style: dict[str, Any]) -> str:
    p = style["palette"]
    phone_panel = tag("rect", x=96, y=280, width=320, height=600, rx=24, fill=p["ink"])
    phone = use("icon-device-mobile", 146, 366, 220, 220, p["background"], "phone-s002")
    check = tag("circle", cx=256, cy=700, r=64, fill=p["lime"]) + tag("path", d="M220 700 L246 726 L296 674", fill="none", stroke=p["ink"], stroke_width=12, stroke_linecap="round", stroke_linejoin="round")
    calendar = use("component-calendar-strip", 490, 290, 1330, 444, p["ink"], "calendar-s002")
    accent = tag("rect", x=1435, y=525, width=210, height=122, rx=16, fill=p["lime"])
    labels = text_node(550, 800, "SEMANA 1", "support") + text_node(1425, 800, "MÊS 3", "support")
    return background(style) + header(style, "O TEMPO PASSA", "lime") + phone_panel + phone + check + calendar + accent + labels


def scene_003(style: dict[str, Any]) -> str:
    p = style["palette"]
    panel = tag("rect", x=96, y=230, width=1120, height=754, rx=24, fill=p["ink"])
    phone = use("icon-device-mobile", 230, 290, 520, 520, p["background"], "phone-s003")
    balance_frame = tag("rect", x=260, y=790, width=790, height=100, rx=16, fill=p["background"])
    balance = tag("rect", x=282, y=812, width=128, height=56, rx=12, fill=p["lime"]) + tag("rect", x=426, y=812, width=602, height=56, rx=12, fill=p["neutral"])
    amount = text_node(790, 420, "R$ 20", "display", style=f"fill:{p['background']}")
    actor = character(1435, 375, 560, "char-s003")
    question = text_node(1322, 952, "CADÊ A FOLGA?", "support")
    return background(style) + header(style, "TRÊS MESES DEPOIS", "lime") + panel + phone + amount + balance_frame + balance + actor + question


def scene_004(style: dict[str, Any]) -> str:
    p = style["palette"]
    receipt_panel = tag("rect", x=1180, y=220, width=640, height=770, rx=24, fill=p["ink"], filter="url(#main-shadow)")
    receipt = use("icon-receipt", 1350, 320, 300, 300, p["background"], "receipt-s004")
    bars = ""
    labels = (("ALUGUEL", 680), ("TRANSPORTE", 800), ("DELIVERY", 920))
    widths = (620, 450, 330)
    for (label, y), width in zip(labels, widths):
        bars += text_node(96, y - 22, label, "label")
        bars += tag("rect", x=96, y=y, width=820, height=72, rx=16, fill=p["neutral"])
        bars += tag("rect", x=96, y=y, width=width, height=72, rx=16, fill=p["lime"])
    note = text_node(1282, 760, "SEM EXCESSO", "support", style=f"fill:{p['background']}") + text_node(1308, 818, "SÓ ROTINA", "label-light")
    return background(style) + header(style, "NENHUMA COMPRA ABSURDA", "lime", long=True) + bars + receipt_panel + receipt + note


def scene_005(style: dict[str, Any]) -> str:
    p = style["palette"]
    triad = use("metaphor-mechanism-triad", 170, 280, 1580, 674, p["ink"], "triad-s005")
    halo = tag("rect", x=120, y=230, width=1680, height=760, rx=24, fill="none", stroke=p["amber"], stroke_width=6)
    labels = (
        text_node(300, 860, "NORMAL", "support", text_anchor="middle", style="font-size:42px")
        + text_node(960, 860, "COMPARAÇÃO", "support", text_anchor="middle", style="font-size:42px")
        + text_node(1620, 860, "CONTAS", "support", text_anchor="middle", style="font-size:42px")
    )
    footer = text_node(960, 960, "AS TRÊS SE MOVEM COM A RENDA", "support", text_anchor="middle", style="font-size:42px")
    return background(style) + header(style, "TRÊS COISAS SE MOVEM", "amber") + halo + triad + labels + footer


def scene_006(style: dict[str, Any]) -> str:
    p = style["palette"]
    actor = character(140, 400, 560, "char-s006")
    brain_panel = tag("rect", x=610, y=210, width=1210, height=780, rx=24, fill=p["ink"], filter="url(#main-shadow)")
    brain = use("metaphor-brain-adaptation", 760, 250, 860, 700, p["background"], "brain-s006")
    marker = tag("rect", x=1168, y=590, width=300, height=92, rx=16, fill=p["lime"])
    marker_text = text_node(1318, 650, "NOVO NORMAL", "label", text_anchor="middle")
    return background(style) + header(style, "ADAPTAÇÃO", "lime") + actor + brain_panel + brain + marker + marker_text


RENDERERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "S001": scene_001,
    "S002": scene_002,
    "S003": scene_003,
    "S004": scene_004,
    "S005": scene_005,
    "S006": scene_006,
}


def svg_document(
    content: str,
    style: dict[str, Any],
    scene_id: str,
    resolved_scene: dict[str, Any],
) -> str:
    spec = SCENE_SPECS[scene_id]
    sources = [RIG_FILE] if spec["character"] else []
    sources.extend(ICON_ROOT / f"{name}.svg" for name in spec["icons"])
    sources.extend(COMPONENT_FILES[name] for name in spec["components"])
    metadata = {
        "episode_id": "CO-001",
        "scene_id": scene_id,
        "style_id": style["style_id"],
        "test_id": "v3_sequencial_s001_s006",
        "layout": spec["layout"],
        "accent": spec["accent"],
        "character_present": spec["character"],
        "continuity": spec["continuity"],
        "beat_ids": resolved_scene["beat_ids"],
        "resolved_start": resolved_scene["start"],
        "resolved_end": resolved_scene["end"],
        "events": resolved_scene["events"],
        "asset_sources": [str(path.relative_to(ROOT)).replace("\\", "/") for path in sources],
        "asset_source_hashes": {str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img">\n'
        + tag("metadata", escape(json.dumps(metadata, ensure_ascii=False, sort_keys=True)))
        + scene_defs(style, spec)
        + group(content, id_=f"scene-{scene_id}")
        + "\n</svg>\n"
    )


def main() -> int:
    validate_rig(RIG_FILE)
    style = load_json(STYLE_FILE)
    resolved = load_json(RESOLVED_MANIFEST)
    resolved_scenes = resolved.get("scenes", [])
    if tuple(scene.get("scene_id") for scene in resolved_scenes) != PILOT_SCENES:
        raise RuntimeError("04A deve conter exatamente S001–S006 para este piloto.")
    resolved_by_id = {scene["scene_id"]: scene for scene in resolved_scenes}
    for scene_id in PILOT_SCENES:
        scene = resolved_by_id[scene_id]
        expected = SCENE_SPECS[scene_id]
        character_present = scene.get("character", {}).get("role") != "none"
        if scene.get("layout_id") != expected["layout"] or scene.get("accent") != expected["accent"]:
            raise RuntimeError(f"{scene_id}: layout ou destaque diverge do 04A.")
        if character_present != expected["character"]:
            raise RuntimeError(f"{scene_id}: presença do personagem diverge do 04A.")
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "test_id": "v3_sequencial_s001_s006",
        "style_id": style["style_id"],
        "status": "candidate",
        "source_04A": str(RESOLVED_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "scenes": [],
    }
    for scene_id in PILOT_SCENES:
        path = SCENE_DIR / f"{scene_id.lower()}.svg"
        resolved_scene = resolved_by_id[scene_id]
        path.write_text(
            svg_document(RENDERERS[scene_id](style), style, scene_id, resolved_scene),
            encoding="utf-8",
            newline="\n",
        )
        manifest["scenes"].append(
            {
                "scene_id": scene_id,
                "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "beat_ids": resolved_scene["beat_ids"],
                "start": resolved_scene["start"],
                "end": resolved_scene["end"],
                "events": resolved_scene["events"],
                **SCENE_SPECS[scene_id],
            }
        )
        print(f"{scene_id}: {path.relative_to(ROOT)}")
    (TEST_DIR / "scene_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    audio_source = ROOT / resolved["audio"]["file"]
    try:
        audio_relative = audio_source.relative_to(TEST_DIR).as_posix()
    except ValueError as exc:
        raise RuntimeError("O áudio do piloto deve estar dentro da pasta do teste.") from exc
    timeline = {
        "test_id": "v3_sequencial_s001_s006",
        "source": "04A_SCENE_MANIFEST.json",
        "audio": audio_relative,
        "duration_seconds": resolved["audio"]["duration_seconds"],
        "transition_seconds": 0.35,
        "scenes": [
            {
                "scene_id": scene["scene_id"],
                "file": f"scenes/{scene['scene_id'].lower()}.svg",
                "start": scene["start"],
                "end": scene["end"],
                "cue": scene["anchor_start"]["text"],
                "dominant_motion": scene["events"][0]["action"] if scene["events"] else "hold",
                "continuity_in": scene["continuity_in"],
                "continuity_out": scene["continuity_out"],
            }
            for scene in resolved_scenes
        ],
    }
    (TEST_DIR / "timeline.json").write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
