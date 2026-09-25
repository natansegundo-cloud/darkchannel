#!/usr/bin/env python3
"""Gera seis frames estáticos do sprint Capital Oculto Art Direction V4."""

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
ART_FILE = ROOT / "config" / "art_direction_v4.json"
RIG_FILE = ROOT / "assets" / "characters" / "capital_oculto_character_rig_v4.svg"
OUTPUT_DIR = ROOT / "episodios" / "CO-001-por-que-ganhar-mais-nao-basta" / "testes" / "art_direction_v4_s001_s006"
SCENES = ("S001", "S002", "S003", "S004", "S005", "S006")
SPECS: dict[str, dict[str, Any]] = {
    "S001": {"visual_class": "data_hero", "accent": "lime", "character": False, "character_function": None, "future_motion": "salary_counter_steps_from_3500_to_4200"},
    "S002": {"visual_class": "transformation", "accent": "lime", "character": False, "character_function": None, "future_motion": "timeline_draws_while_available_income_contracts"},
    "S003": {"visual_class": "scale", "accent": "lime", "character": True, "character_function": "scale", "future_motion": "values_collapse_until_20_remains"},
    "S004": {"visual_class": "editorial_type", "accent": "lime", "character": False, "character_function": None, "future_motion": "routine_word_accumulates_expense_labels"},
    "S005": {"visual_class": "system_map", "accent": "amber", "character": False, "character_function": None, "future_motion": "three_tracks_rise_together"},
    "S006": {"visual_class": "transformation", "accent": "lime", "character": False, "character_function": None, "future_motion": "conquest_repeats_fades_and_becomes_normal"},
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def attrs(**values: Any) -> str:
    result = []
    for key, value in values.items():
        if value is None:
            continue
        key = key.rstrip("_").replace("__", ":").replace("_", "-")
        result.append(f'{key}="{escape(str(value), {chr(34): "&quot;"})}"')
    return " ".join(result)


def tag(name: str, content: str = "", **values: Any) -> str:
    properties = attrs(**values)
    if content:
        return f"<{name} {properties}>{content}</{name}>" if properties else f"<{name}>{content}</{name}>"
    return f"<{name} {properties}/>" if properties else f"<{name}/>"


def group(content: str, **values: Any) -> str:
    return tag("g", content, **values)


def text(x: float, y: float, value: str, css: str, **values: Any) -> str:
    return tag("text", escape(value), x=x, y=y, class_=css, **values)


def line(x1: float, y1: float, x2: float, y2: float, color: str, width: float = 6, **values: Any) -> str:
    return tag("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=color, stroke_width=width, stroke_linecap="round", **values)


def extract_defs(path: Path) -> str:
    source = path.read_text(encoding="utf-8-sig")
    match = re.search(r"<defs>(.*)</defs>", source, flags=re.DOTALL)
    if not match:
        raise RuntimeError(f"SVG sem defs: {path}")
    return match.group(1).strip()


def base_defs(style: dict[str, Any], include_character: bool) -> str:
    p = style["palette"]
    css = f"""
    .display {{ font-family:Bahnschrift,'Arial Narrow',Arial,sans-serif; font-weight:900; letter-spacing:-8px; fill:{p['ink']}; font-variant-numeric:tabular-nums; }}
    .display-light {{ font-family:Bahnschrift,'Arial Narrow',Arial,sans-serif; font-weight:900; letter-spacing:-8px; fill:{p['background']}; font-variant-numeric:tabular-nums; }}
    .headline {{ font-family:Bahnschrift,'Arial Narrow',Arial,sans-serif; font-weight:800; letter-spacing:-3px; fill:{p['ink']}; }}
    .headline-light {{ font-family:Bahnschrift,'Arial Narrow',Arial,sans-serif; font-weight:800; letter-spacing:-3px; fill:{p['background']}; }}
    .label {{ font-family:Bahnschrift,Arial,sans-serif; font-size:28px; font-weight:700; letter-spacing:2.2px; fill:{p['ink']}; }}
    .label-light {{ font-family:Bahnschrift,Arial,sans-serif; font-size:28px; font-weight:700; letter-spacing:2.2px; fill:{p['background']}; }}
    .micro {{ font-family:Bahnschrift,Arial,sans-serif; font-size:22px; font-weight:700; letter-spacing:2.8px; fill:{p['ink']}; }}
    .micro-light {{ font-family:Bahnschrift,Arial,sans-serif; font-size:22px; font-weight:700; letter-spacing:2.8px; fill:{p['background']}; }}
    """
    pattern = tag(
        "pattern",
        tag("circle", cx=2, cy=2, r=1.1, fill=p["ink"], opacity=.055),
        id="paper-grain",
        width=18,
        height=18,
        patternUnits="userSpaceOnUse",
    )
    contents = tag("style", css) + pattern
    if include_character:
        contents += extract_defs(RIG_FILE)
    return tag("defs", contents)


def paper(style: dict[str, Any], dark: bool = False) -> str:
    p = style["palette"]
    fill = p["ink"] if dark else p["background"]
    base = tag("rect", x=0, y=0, width=1920, height=1080, fill=fill)
    if dark:
        return base
    return base + tag("rect", x=0, y=0, width=1920, height=1080, fill="url(#paper-grain)")


def character(x: float, y: float, height: float) -> str:
    return group(
        tag("use", href="#char-base", x=0, y=0, width=height / 2, height=height),
        id="char-s003",
        transform=f"translate({x} {y})",
        data_character_function="scale",
        data_visual_height=round(height * 589 / 640),
    )


def scene_001(style: dict[str, Any]) -> str:
    p = style["palette"]
    slab = tag("rect", x=0, y=0, width=620, height=1080, fill=p["ink"], data_role="surface")
    old = text(72, 470, "R$ 3.500", "display-light", style="font-size:136px;letter-spacing:-5px")
    old += text(100, 550, "ANTES", "micro-light", style="opacity:.62")
    connector = line(500, 630, 760, 630, p["lime"], 14) + tag("polygon", points="760,606 808,630 760,654", fill=p["lime"])
    current = text(690, 620, "4.200", "display", style="font-size:330px", data_dominant="true")
    currency = text(712, 350, "R$", "headline", style="font-size:72px")
    delta = text(720, 785, "+ R$ 700", "headline", style=f"font-size:96px;fill:{p['lime']}")
    label = text(724, 860, "RENDA MENSAL  •  NOVO VALOR", "label")
    title = text(72, 105, "SEU SALÁRIO", "headline-light", style="font-size:48px", data_role="scene-title")
    title += text(72, 165, "AUMENTOU", "headline-light", style=f"font-size:48px;fill:{p['lime']}")
    ghost = text(1190, 1010, "4.200", "display", style=f"font-size:210px;fill:none;stroke:{p['neutral']};stroke-width:3px;opacity:.52")
    return paper(style) + slab + title + old + connector + current + currency + delta + label + ghost


def scene_002(style: dict[str, Any]) -> str:
    p = style["palette"]
    top = text(96, 170, "+ R$ 700", "display", style="font-size:150px", data_dominant="true")
    top += text(100, 225, "DISPONÍVEIS NO INÍCIO", "micro")
    xs = (160, 680, 1180, 1760)
    months = ("SEMANA 1", "MÊS 1", "MÊS 2", "MÊS 3")
    values = ("+700", "+540", "+390", "+20")
    expenses = ("AUMENTO", "+ STREAMING", "+ DELIVERY", "+ PARCELA")
    result = line(96, 540, 1824, 540, p["ink"], 8)
    result += line(96, 540, 1760, 540, p["lime"], 16, opacity=.92)
    for index, x in enumerate(xs):
        radius = 26 if index < 3 else 42
        fill = p["ink"] if index < 3 else p["lime"]
        result += tag("circle", cx=x, cy=540, r=radius, fill=fill)
        result += text(x, 440, values[index], "headline", text_anchor="middle", style=f"font-size:{86 if index < 3 else 126}px;fill:{p['ink']}")
        result += text(x, 640, months[index], "label", text_anchor="middle")
        result += text(x, 704, expenses[index], "micro", text_anchor="middle", style="opacity:.58")
    result += text(1510, 940, "RESTAM", "micro")
    result += text(1510, 1025, "R$ 20", "headline", style="font-size:92px")
    return paper(style) + top + result


def scene_003(style: dict[str, Any]) -> str:
    p = style["palette"]
    trail = ""
    for index, value in enumerate(("700", "525", "390", "210", "80")):
        y = 190 + index * 132
        opacity = .16 + index * .07
        trail += text(110, y, value, "display", style=f"font-size:108px;opacity:{opacity}")
        trail += line(105, y + 24, 430, y + 24, p["neutral"], 5)
    actor = character(430, 675, 320)
    currency = text(720, 270, "R$", "headline", style="font-size:92px")
    amount = text(690, 890, "20", "display", style="font-size:760px;letter-spacing:-34px", data_dominant="true")
    month = text(100, 1010, "MÊS 3", "label")
    label = text(1510, 1010, "SOBRA DO MÊS", "label", text_anchor="end")
    return paper(style) + trail + actor + currency + amount + month + label


def scene_004(style: dict[str, Any]) -> str:
    p = style["palette"]
    backdrop = "".join(
        text(1160, 210 + index * 120, label, "micro-light", style=f"opacity:{.14 + index * .07}")
        for index, label in enumerate(("ALUGUEL", "TRANSPORTE", "DELIVERY", "PLANO", "PARCELA", "ASSINATURA"))
    )
    copy = text(86, 235, "NENHUM", "headline-light", style="font-size:176px")
    copy += text(86, 420, "LUXO.", "headline-light", style="font-size:176px")
    copy += text(90, 590, "SÓ A", "headline-light", style="font-size:92px;opacity:.55")
    copy += text(84, 825, "ROTINA", "headline-light", style=f"font-size:236px;fill:{p['lime']}", data_dominant="true")
    copy += text(96, 930, "PASSOU A CONTAR COM O AUMENTO", "label-light")
    accent = tag("rect", x=1760, y=0, width=160, height=1080, fill=p["lime"])
    return paper(style, dark=True) + backdrop + copy + accent


def scene_005(style: dict[str, Any]) -> str:
    p = style["palette"]
    xs = (390, 950, 1510)
    labels = ("CONFORTO", "COMPARAÇÃO", "CUSTO FIXO")
    result = text(96, 110, "QUANDO A RENDA SOBE", "micro")
    result += line(96, 750, 1824, 750, p["neutral"], 4)
    result += line(96, 345, 1824, 345, p["ink"], 6)
    result += text(1810, 330, "RENDA NOVA", "micro", text_anchor="end")
    result += text(1810, 735, "RENDA ANTIGA", "micro", text_anchor="end", style="opacity:.55")
    for x, label in zip(xs, labels):
        result += text(x, 218, label, "label", text_anchor="middle")
        result += line(x, 790, x, 310, p["amber"], 12)
        result += tag("polygon", points=f"{x-22},335 {x},292 {x+22},335", fill=p["amber"])
        result += tag("rect", x=x - 54, y=630, width=108, height=120, fill=p["neutral"])
        result += tag("rect", x=x - 54, y=345, width=108, height=170, fill=p["ink"], data_dominant="true")
    result += text(96, 1010, "A RENDA SUBIU. AS TRÊS RÉGUAS TAMBÉM.", "headline", style="font-size:62px")
    return paper(style) + result


def scene_006(style: dict[str, Any]) -> str:
    p = style["palette"]
    result = text(96, 100, "ADAPTAÇÃO", "micro-light", style="opacity:.55")
    result += text(88, 300, "CONQUISTA", "headline-light", style="font-size:192px", data_dominant="true")
    result += text(310, 480, "CONQUISTA", "headline-light", style="font-size:128px;opacity:.46")
    result += text(590, 620, "ROTINA", "headline-light", style="font-size:110px;opacity:.34")
    result += line(190, 715, 1520, 715, p["lime"], 10)
    result += tag("polygon", points="1520,688 1574,715 1520,742", fill=p["lime"])
    result += text(895, 970, "NORMAL", "headline-light", style=f"font-size:250px;fill:{p['lime']}")
    result += text(100, 1030, "O GANHO NÃO SUMIU. O PONTO DE PARTIDA MUDOU.", "label-light", style="opacity:.72")
    return paper(style, dark=True) + result


RENDERERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "S001": scene_001,
    "S002": scene_002,
    "S003": scene_003,
    "S004": scene_004,
    "S005": scene_005,
    "S006": scene_006,
}


def document(scene_id: str, style: dict[str, Any], art: dict[str, Any]) -> str:
    spec = SPECS[scene_id]
    sources = [RIG_FILE] if spec["character"] else []
    metadata = {
        "episode_id": "CO-001",
        "scene_id": scene_id,
        "visual_system": style["style_id"],
        "art_direction": art["art_direction_id"],
        "visual_class": spec["visual_class"],
        "accent": spec["accent"],
        "character_present": spec["character"],
        "character_function": spec["character_function"],
        "future_motion": spec["future_motion"],
        "library_icon_area_ratio": 0.0,
        "asset_sources": [path.relative_to(ROOT).as_posix() for path in sources],
        "asset_source_hashes": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    scene = group(
        RENDERERS[scene_id](style),
        id_=f"scene-{scene_id}",
        data_visual_class=spec["visual_class"],
        data_future_motion=spec["future_motion"],
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img">\n'
        + tag("metadata", escape(json.dumps(metadata, ensure_ascii=False, sort_keys=True)))
        + base_defs(style, spec["character"])
        + scene
        + "\n</svg>\n"
    )


def review_board() -> str:
    cells = []
    for index, scene_id in enumerate(SCENES):
        x = 32 + (index % 3) * 496
        y = 32 + (index // 3) * 318
        cells.append(tag("image", href=f"{scene_id.lower()}.svg", x=x, y=y, width=480, height=270, data_scale="0.25"))
        cells.append(text(x, y + 294, f"{scene_id}  /  {SPECS[scene_id]['visual_class'].upper()}", "board-label"))
    css = """
    .board-label { font-family:Bahnschrift,Arial,sans-serif; font-size:16px; font-weight:700; letter-spacing:1.4px; fill:#F4F3EF; }
    """
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="668" viewBox="0 0 1536 668">\n'
        + tag("defs", tag("style", css))
        + tag("rect", x=0, y=0, width=1536, height=668, fill="#111111")
        + "".join(cells)
        + "\n</svg>\n"
    )


def main() -> int:
    validate_rig(RIG_FILE)
    style = load_json(STYLE_FILE)
    art = load_json(ART_FILE)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"art_direction_id": art["art_direction_id"], "status": art["status"], "scenes": []}
    for scene_id in SCENES:
        path = OUTPUT_DIR / f"{scene_id.lower()}.svg"
        path.write_text(document(scene_id, style, art), encoding="utf-8", newline="\n")
        manifest["scenes"].append({"scene_id": scene_id, "file": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), **SPECS[scene_id]})
        print(f"{scene_id}: {path.relative_to(ROOT)}")
    board = OUTPUT_DIR / "review_art_direction_v4_25.svg"
    board.write_text(review_board(), encoding="utf-8", newline="\n")
    (OUTPUT_DIR / "art_direction_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"BOARD: {board.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, KeyError, ValueError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
