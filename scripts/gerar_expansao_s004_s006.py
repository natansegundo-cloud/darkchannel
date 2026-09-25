#!/usr/bin/env python3
"""Gera o teste estático isolado da expansão editorial para S004–S006.

Escopo deliberadamente limitado:
- CO-COMP-05A / 05B (EDITORIAL_TYPE)
- CO-COMP-06A / 06B (SYSTEM_MAP)
- CO-COMP-04D (MOVING_BASELINE conceitual)

Não gera áudio, motion, cenas S007+ nem integra o pipeline oficial.
Usa somente a biblioteca padrão do Python.
"""

from __future__ import annotations

import base64
import datetime as dt
import html
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "visual_compositions.json"
RULES_PATH = ROOT / "config" / "visual_composition_rules.json"
ASSET_ROOT = ROOT / "assets" / "compositions"
TEST_ROOT = ROOT / "tests" / "editorial_compositions_v1"
MASTERS_ROOT = TEST_ROOT / "masters"
RUN_ROOT = TEST_ROOT / "s004_s006"
CANDIDATES_ROOT = RUN_ROOT / "candidates"
SELECTED_ROOT = RUN_ROOT / "selected"
CONTACT_ROOT = TEST_ROOT / "contact_sheets"

INK = "#111111"
LIME = "#C4E538"
AMBER = "#E8A33D"
BG = "#F4F3EF"
GRAY = "#D9D9D4"
FONT = "Bahnschrift,'Arial Narrow',Arial,sans-serif"

NEW_IDS = {
    "CO-COMP-05A",
    "CO-COMP-05B",
    "CO-COMP-06A",
    "CO-COMP-06B",
    "CO-COMP-04D",
}
APPROVED_IDS = {"CO-COMP-01C", "CO-COMP-04A", "CO-COMP-03A"}
CONTENT_FORMATS = {
    "currency_short",
    "currency_delta",
    "percentage",
    "plain_number",
    "short_label",
    "headline",
    "keyword",
    "short_statement",
}
TEXTUAL_TYPES = {
    "text_stack",
    "display_number",
    "headline",
    "label",
    "composite",
    "keyword",
    "short_statement",
}
BLEED_TYPES = {"structural_line", "structural_surface", "highlight_space", "display_number"}

SELECTION = {
    "S004": "CO-COMP-05A",
    "S005": "CO-COMP-06A",
    "S006": "CO-COMP-04D",
}

GEOMETRY_PROMOTIONS = {
    "CO-COMP-06A": {"version": 1.1, "protect_primary_type": True},
    "CO-COMP-04D": {"version": 1.2, "protect_primary_type": True},
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def composition_map(config: dict) -> dict[str, dict]:
    return {item["id"]: item for item in config["compositions"]}


def validate_contracts(config: dict, rules: dict) -> None:
    errors: list[str] = []
    compositions = composition_map(config)

    if set(config.get("families", [])) != {
        "DATA_HERO", "MOVING_BASELINE", "SHRINKING_SPACE", "EDITORIAL_TYPE", "SYSTEM_MAP"
    }:
        errors.append("catálogo deve conter exatamente as cinco famílias contratadas")
    if len(compositions) != 14:
        errors.append(f"catálogo deve conter 14 variantes; contém {len(compositions)}")
    if not NEW_IDS.issubset(compositions):
        errors.append(f"faltam variantes: {sorted(NEW_IDS - set(compositions))}")
    for comp_id in NEW_IDS:
        if compositions.get(comp_id, {}).get("status") != "EXPERIMENTAL":
            errors.append(f"{comp_id} deve permanecer EXPERIMENTAL")
    current_approved = {cid for cid, comp in compositions.items() if comp.get("status") == "APPROVED"}
    if current_approved != APPROVED_IDS:
        errors.append(f"conjunto APPROVED foi alterado: {sorted(current_approved)}")

    for comp_id in NEW_IDS:
        comp = compositions.get(comp_id, {})
        for required in (
            "version", "semantic_use", "entry_motion_candidates",
            "exit_motion_candidates", "continuity_candidates", "content_zones",
        ):
            if not comp.get(required):
                errors.append(f"{comp_id}: {required} ausente")
        for zone in comp.get("content_zones", []):
            zone_id = zone.get("id", "SEM_ID")
            required_zone_fields = {
                "x", "y", "width", "height", "content_type", "font_size",
                "max_chars", "max_lines", "overflow_policy", "safe_area_policy",
            }
            missing = required_zone_fields - set(zone)
            if missing:
                errors.append(f"{comp_id}/{zone_id}: faltam {sorted(missing)}")
                continue
            if zone["overflow_policy"] != "REJECT_COMPOSITION":
                errors.append(f"{comp_id}/{zone_id}: overflow_policy inválida")
            policy = zone["safe_area_policy"]
            if policy == "STRICT":
                if zone["x"] < 96 or zone["y"] < 96:
                    errors.append(f"{comp_id}/{zone_id}: invade o início da safe area de texto")
                if zone["x"] + zone["width"] > 1824 or zone["y"] + zone["height"] > 984:
                    errors.append(f"{comp_id}/{zone_id}: excede a safe area de texto")
            elif policy == "BLEED_ALLOWED":
                if zone["content_type"] not in BLEED_TYPES:
                    errors.append(f"{comp_id}/{zone_id}: conteúdo legível não pode sangrar")
            else:
                errors.append(f"{comp_id}/{zone_id}: safe_area_policy inválida")
            content_format = zone.get("content_format")
            if zone["content_type"] in TEXTUAL_TYPES and content_format not in CONTENT_FORMATS:
                errors.append(f"{comp_id}/{zone_id}: content_format ausente ou inválido")
            if content_format and content_format not in CONTENT_FORMATS:
                errors.append(f"{comp_id}/{zone_id}: content_format desconhecido")

    mechanisms = rules.get("mechanisms", {})
    if mechanisms.get("strong_statement", {}).get("primary_family") != "EDITORIAL_TYPE":
        errors.append("strong_statement deve rotear para EDITORIAL_TYPE")
    system_rule = mechanisms.get("system_relationship", {})
    if system_rule.get("primary_family") != "SYSTEM_MAP":
        errors.append("system_relationship deve rotear para SYSTEM_MAP")
    compression_routes = system_rule.get("conditional_routing", {})
    for key in ("compression", "pressure", "constraint", "loss_of_space", "dual_force_squeeze"):
        if compression_routes.get(key) != "SHRINKING_SPACE":
            errors.append(f"system_relationship/{key} deve permanecer em SHRINKING_SPACE")
    time_rule = mechanisms.get("time_adaptation", {})
    if time_rule.get("primary_family") != "MOVING_BASELINE":
        errors.append("time_adaptation deve permanecer em MOVING_BASELINE")
    if time_rule.get("variant_routing", {}).get("conceptual_keywords") != "CO-COMP-04D":
        errors.append("time_adaptation conceitual deve rotear para CO-COMP-04D")

    if errors:
        raise ValueError("Contratos inválidos:\n- " + "\n- ".join(errors))


def style_defs() -> str:
    return f"""<defs>
  <style>
    .display {{ font-family:{FONT}; font-weight:900; letter-spacing:-8px; fill:{INK}; }}
    .headline {{ font-family:{FONT}; font-weight:900; letter-spacing:-4px; fill:{INK}; }}
    .label {{ font-family:{FONT}; font-size:28px; font-weight:800; letter-spacing:2.4px; fill:{INK}; }}
    .light {{ fill:{BG}; }}
  </style>
  <pattern id="paper-grain" width="18" height="18" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1.1" fill="{INK}" opacity="0.055"/>
  </pattern>
</defs>"""


def metadata(scene_id: str, comp_id: str, family: str, accent: str) -> str:
    data = {
        "scene_id": scene_id,
        "composition_id": comp_id,
        "family": family,
        "status": "EXPERIMENTAL",
        "selection_mode": "EXPERIMENTAL_TEST",
        "visual_system": "CO_VISUAL_V3",
        "art_direction": "CO_ART_DIRECTION_V4",
        "accent": accent,
        "character_present": False,
        "audio_present": False,
        "motion_present": False,
        "generated_at": dt.datetime.now().astimezone().isoformat(),
    }
    if comp_id in GEOMETRY_PROMOTIONS:
        data.update({
            **GEOMETRY_PROMOTIONS[comp_id],
            "geometry_change_reason": "VISUAL_GEOMETRY_MASTER_DEFECT",
            "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0",
            "instance_geometry_override": False,
        })
    return f"<metadata>{html.escape(json.dumps(data, ensure_ascii=False))}</metadata>"


def wrap(scene_id: str, comp_id: str, family: str, accent: str, body: str) -> str:
    promotion = GEOMETRY_PROMOTIONS.get(comp_id)
    version_label = f" v{promotion['version']}" if promotion else ""
    version_attribute = f' data-version="{promotion["version"]}"' if promotion else ""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-label="{scene_id} {comp_id}{version_label}">
{style_defs()}
{metadata(scene_id, comp_id, family, accent)}
<g id="scene-{scene_id}" data-composition="{comp_id}"{version_attribute} data-static-test="true">
  <rect width="1920" height="1080" fill="{BG}"/>
  <rect width="1920" height="1080" fill="url(#paper-grain)"/>
{body}
</g>
</svg>
'''


def render_05a(scene_id: str) -> str:
    body = f'''
  <rect x="96" y="112" width="112" height="12" rx="6" fill="{AMBER}"/>
  <text x="96" y="250" class="headline" style="font-size:112px">O PROBLEMA</text>
  <text x="86" y="548" class="display" style="font-size:270px;fill:{AMBER};letter-spacing:-14px">NÃO É</text>
  <g transform="translate(678 622)">
    <text x="0" y="112" class="headline" style="font-size:118px">UMA COMPRA</text>
    <text x="0" y="290" class="display" style="font-size:176px;letter-spacing:-9px">ABSURDA</text>
    <rect x="0" y="318" width="920" height="14" rx="7" fill="{INK}"/>
  </g>'''
    return wrap(scene_id, "CO-COMP-05A", "EDITORIAL_TYPE", "amber", body)


def render_05b(scene_id: str) -> str:
    body = f'''
  <path d="M0 0 H700 L560 1080 H0 Z" fill="{INK}"/>
  <text x="96" y="226" class="label light">O PROBLEMA</text>
  <text x="84" y="590" class="display light" style="font-size:246px;letter-spacing:-14px">NÃO</text>
  <text x="96" y="730" class="headline light" style="font-size:110px">É UMA</text>
  <text x="760" y="298" class="headline" style="font-size:116px">COMPRA</text>
  <text x="744" y="670" class="display" style="font-size:244px;letter-spacing:-14px">ABSURDA</text>
  <path d="M720 570 L1814 716" stroke="{AMBER}" stroke-width="28" stroke-linecap="round"/>
  <text x="1818" y="936" class="label" text-anchor="end">NÃO FOI UMA EXCEÇÃO ISOLADA</text>'''
    return wrap(scene_id, "CO-COMP-05B", "EDITORIAL_TYPE", "amber", body)


def render_06a(scene_id: str) -> str:
    body = f'''
  <g data-layer="20" data-geometry-type="TRACK">
    <rect x="560" y="272" width="636" height="86" rx="18" fill="{INK}" data-routing="STOP_BEFORE_ACCENT_BLOCK"/>
    <rect x="1196" y="272" width="386" height="86" rx="18" fill="{LIME}"/>
    <rect x="560" y="522" width="826" height="86" rx="18" fill="{INK}" data-routing="STOP_BEFORE_ACCENT_BLOCK"/>
    <rect x="1386" y="522" width="268" height="86" rx="18" fill="{LIME}"/>
    <rect x="560" y="772" width="1016" height="86" rx="18" fill="{INK}" data-routing="STOP_BEFORE_ACCENT_BLOCK"/>
    <rect x="1576" y="772" width="184" height="86" rx="18" fill="{LIME}"/>
  </g>
  <path d="M610 904 L1390 220" stroke="{LIME}" stroke-width="30" stroke-linecap="round" opacity="0.95" data-layer="40" data-geometry-type="ACCENT_LINE" data-routing="STOP_BEFORE" data-arrowhead="false" data-semantic-role="REFERENCIA_COMPARTILHADA"/>
  <g data-layer="50">
    <text x="96" y="330" class="headline" style="font-size:82px">NORMAL</text>
    <text x="96" y="580" class="headline" style="font-size:70px">COMPARAÇÃO</text>
    <text x="96" y="830" class="headline" style="font-size:82px">DESPESAS</text>
  </g>
  <g data-layer="60">
    <text x="1824" y="136" class="label" text-anchor="end">QUANDO A RENDA SOBE</text>
    <text x="1824" y="966" class="label" text-anchor="end">O SISTEMA SE MOVE JUNTO</text>
  </g>'''
    return wrap(scene_id, "CO-COMP-06A", "SYSTEM_MAP", "lime", body)


def render_06b(scene_id: str) -> str:
    body = f'''
  <path d="M0 0 H520 V1080 H0 Z" fill="{INK}"/>
  <rect x="480" y="96" width="96" height="888" rx="24" fill="{LIME}"/>
  <text x="96" y="486" class="label light">FORÇA COMUM</text>
  <text x="88" y="606" class="headline light" style="font-size:92px">RENDA</text>
  <g>
    <path d="M540 180 H1740 L1816 254 L1740 328 H540 Z" fill="{INK}"/>
    <text x="740" y="284" class="headline light" style="font-size:88px">NORMAL</text>
  </g>
  <g>
    <path d="M540 450 H1630 L1706 524 L1630 598 H540 Z" fill="{INK}"/>
    <text x="740" y="554" class="headline light" style="font-size:76px">COMPARAÇÃO</text>
  </g>
  <g>
    <path d="M540 720 H1780 L1856 794 L1780 868 H540 Z" fill="{INK}"/>
    <text x="740" y="824" class="headline light" style="font-size:88px">DESPESAS</text>
  </g>
  <text x="1824" y="966" class="label" text-anchor="end">TRÊS EFEITOS • UM MESMO SISTEMA</text>'''
    return wrap(scene_id, "CO-COMP-06B", "SYSTEM_MAP", "lime", body)


def render_04d(scene_id: str) -> str:
    body = f'''
  <g data-layer="20" data-protect-primary-type="true">
    <path d="M-40 990 L48 990" stroke="{INK}" stroke-width="36" stroke-linecap="round" data-geometry-type="STRUCTURAL_LINE" data-routing="STOP_BEFORE"/>
    <path d="M540 970 L1020 511" stroke="{INK}" stroke-width="36" stroke-linecap="round" data-geometry-type="STRUCTURAL_LINE" data-routing="ROUTE_AROUND"/>
    <path d="M1020 511 L1824 511" stroke="{LIME}" stroke-width="18" stroke-linecap="round" data-geometry-type="ACCENT_LINE" data-routing="TRANSFORM_TO_UNDERLINE"/>
  </g>
  <g opacity="0.48">
    <text x="96" y="774" class="label">ANTES</text>
    <text x="88" y="928" class="display" style="font-size:148px;letter-spacing:-7px">EXTRA</text>
  </g>
  <text x="1824" y="154" class="label" text-anchor="end">AGORA</text>
  <text x="1818" y="438" class="display" text-anchor="end" style="font-size:252px;letter-spacing:-14px">NORMAL</text>
  <text x="1824" y="636" class="headline" text-anchor="end" style="font-size:66px">VIROU REFERÊNCIA</text>
  <text x="1824" y="964" class="label" text-anchor="end">O GANHO NÃO SUMIU • A BASE MUDOU</text>'''
    return wrap(scene_id, "CO-COMP-04D", "MOVING_BASELINE", "lime", body)


RENDERERS = {
    "CO-COMP-05A": render_05a,
    "CO-COMP-05B": render_05b,
    "CO-COMP-06A": render_06a,
    "CO-COMP-06B": render_06b,
    "CO-COMP-04D": render_04d,
}

SCENE_FOR_VARIANT = {
    "CO-COMP-05A": "S004",
    "CO-COMP-05B": "S004",
    "CO-COMP-06A": "S005",
    "CO-COMP-06B": "S005",
    "CO-COMP-04D": "S006",
}

FAMILY_DIR = {
    "CO-COMP-05A": "editorial_type",
    "CO-COMP-05B": "editorial_type",
    "CO-COMP-06A": "system_map",
    "CO-COMP-06B": "system_map",
    "CO-COMP-04D": "moving_baseline",
}


def svg_data_uri(svg_text: str) -> str:
    payload = base64.b64encode(svg_text.encode("utf-8")).decode("ascii")
    return "data:image/svg+xml;base64," + payload


def contact_sheet(title: str, panels: list[tuple[str, str]], mode: str) -> str:
    if mode == "candidates":
        placements = [
            (72, 188, 560, 315), (680, 188, 560, 315), (1288, 188, 560, 315),
            (376, 650, 560, 315), (984, 650, 560, 315),
        ]
    elif mode == "final":
        placements = [(72, 270, 560, 315), (680, 270, 560, 315), (1288, 270, 560, 315)]
    elif mode == "quarter":
        placements = [(96, 350, 480, 270), (720, 350, 480, 270), (1344, 350, 480, 270)]
    else:
        raise ValueError(mode)

    blocks = []
    for (label, svg_text), (x, y, width, height) in zip(panels, placements):
        blocks.append(
            f'<text x="{x}" y="{y - 28}" class="sheet-label">{html.escape(label)}</text>'
            f'<rect x="{x - 4}" y="{y - 4}" width="{width + 8}" height="{height + 8}" '
            f'rx="16" fill="{INK}" opacity="0.12"/>'
            f'<image href="{svg_data_uri(svg_text)}" x="{x}" y="{y}" width="{width}" height="{height}"/>'
        )
    subtitle = {
        "candidates": "5 CANDIDATOS • EXPERIMENTAL_TEST • SEM MOTION",
        "final": "SELEÇÃO EXPERIMENTAL • NÃO APROVADA PARA PRODUÇÃO",
        "quarter": "SIMULAÇÃO EXATA A 25% • 480 × 270 POR CENA",
    }[mode]
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <style>
    .sheet-title {{ font-family:{FONT}; font-size:54px; font-weight:900; letter-spacing:-2px; fill:{INK}; }}
    .sheet-subtitle {{ font-family:{FONT}; font-size:22px; font-weight:800; letter-spacing:2px; fill:{INK}; opacity:.58; }}
    .sheet-label {{ font-family:{FONT}; font-size:24px; font-weight:900; letter-spacing:1px; fill:{INK}; }}
  </style>
  <rect width="1920" height="1080" fill="{BG}"/>
  <text x="72" y="76" class="sheet-title">{html.escape(title)}</text>
  <text x="72" y="112" class="sheet-subtitle">{subtitle}</text>
  {''.join(blocks)}
</svg>
'''


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    config = read_json(CONFIG_PATH)
    rules = read_json(RULES_PATH)
    validate_contracts(config, rules)

    rendered: dict[str, str] = {}
    for comp_id in sorted(NEW_IDS):
        scene_id = SCENE_FOR_VARIANT[comp_id]
        svg = RENDERERS[comp_id](scene_id)
        rendered[comp_id] = svg

        official_path = ASSET_ROOT / FAMILY_DIR[comp_id] / f"{comp_id}.svg"
        write_text(official_path, svg)
        MASTERS_ROOT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(official_path, MASTERS_ROOT / f"{comp_id}.svg")
        write_text(CANDIDATES_ROOT / f"{scene_id.lower()}_{comp_id}.svg", svg)

    selected_panels: list[tuple[str, str]] = []
    for scene_id, comp_id in SELECTION.items():
        selected_path = SELECTED_ROOT / f"{scene_id.lower()}.svg"
        write_text(selected_path, rendered[comp_id])
        selected_panels.append((f"{scene_id} • {comp_id}", rendered[comp_id]))

    candidate_order = [
        "CO-COMP-05A", "CO-COMP-05B", "CO-COMP-06A", "CO-COMP-06B", "CO-COMP-04D"
    ]
    candidate_panels = [
        (f"{SCENE_FOR_VARIANT[cid]} • {cid}", rendered[cid]) for cid in candidate_order
    ]
    write_text(
        CONTACT_ROOT / "contact_s004_s006_candidates.svg",
        contact_sheet("S004–S006 • CANDIDATOS", candidate_panels, "candidates"),
    )
    write_text(
        CONTACT_ROOT / "contact_s004_s006_final.svg",
        contact_sheet("S004–S006 • SELEÇÃO FINAL", selected_panels, "final"),
    )
    write_text(
        CONTACT_ROOT / "contact_s004_s006_25pct.svg",
        contact_sheet("S004–S006 • TESTE DE LEGIBILIDADE", selected_panels, "quarter"),
    )

    print("[OK] 5 contratos novos validados como EXPERIMENTAL")
    print("[OK] 5 masters oficiais e cópias de teste gerados")
    print("[OK] 5 candidatos estáticos gerados")
    print("[OK] contact sheets de candidatos, seleção e 25% gerados")
    print("[STOP] nenhum áudio, motion, Azure, S007+ ou integração de pipeline executados")


if __name__ == "__main__":
    main()
