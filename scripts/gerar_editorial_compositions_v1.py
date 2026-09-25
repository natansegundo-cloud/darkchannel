#!/usr/bin/env python3
"""
Capital Oculto — Gerador de Composições Editoriais V1

Gera o núcleo original de 9 SVG master e reconstrói experimentalmente
S001–S003. Também valida o catálogo expandido de 14 variantes.

Todos os SVGs seguem:
- Canvas 1920×1080
- Safe area 64 px (absoluta), 96 px (texto)
- Paleta CO_VISUAL_V3
- Traço 6/4/3 px round
- Tipografia Bahnschrift

Este script usa APENAS a biblioteca padrão do Python.
"""

import json
import os
import hashlib
import datetime
import re

# ── Caminhos ──────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPOSITIONS_DIR = os.path.join(PROJECT_ROOT, "assets", "compositions")
MASTERS_DIR = os.path.join(PROJECT_ROOT, "tests", "editorial_compositions_v1", "masters")
SCENES_DIR = os.path.join(PROJECT_ROOT, "tests", "editorial_compositions_v1", "s001_s003")
CONTACT_DIR = os.path.join(PROJECT_ROOT, "tests", "editorial_compositions_v1", "contact_sheets")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "visual_compositions.json")
RULES_PATH = os.path.join(PROJECT_ROOT, "config", "visual_composition_rules.json")
RIG_PATH = os.path.join(PROJECT_ROOT, "assets", "characters", "capital_oculto_character_rig_v4.svg")
SELECTION_MODE = "EXPERIMENTAL_TEST"
CALIBRATION_TARGETS = {"CO-COMP-01C", "CO-COMP-04A", "CO-COMP-03A"}
APPROVED_TARGETS = CALIBRATION_TARGETS
S003_FOCUS_MODE = "COMPRESSION_FIRST"

# ── Paleta ────────────────────────────────────────────────────
INK = "#111111"
LIME = "#C4E538"
AMBER = "#E8A33D"
BG = "#F4F3EF"
NEUTRAL = "#D9D9D4"

# ── Tipografia ────────────────────────────────────────────────
FONT_STACK = "Bahnschrift,'Arial Narrow',Arial,sans-serif"

# ── SVG helpers ───────────────────────────────────────────────

SVG_HEADER = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img">
<defs><style>
    .display {{ font-family:{FONT_STACK}; font-weight:900; letter-spacing:-8px; fill:{INK}; font-variant-numeric:tabular-nums; }}
    .display-light {{ font-family:{FONT_STACK}; font-weight:900; letter-spacing:-8px; fill:{BG}; font-variant-numeric:tabular-nums; }}
    .headline {{ font-family:{FONT_STACK}; font-weight:800; letter-spacing:-3px; fill:{INK}; }}
    .headline-light {{ font-family:{FONT_STACK}; font-weight:800; letter-spacing:-3px; fill:{BG}; }}
    .label {{ font-family:{FONT_STACK}; font-size:28px; font-weight:700; letter-spacing:2.2px; fill:{INK}; }}
    .label-light {{ font-family:{FONT_STACK}; font-size:28px; font-weight:700; letter-spacing:2.2px; fill:{BG}; }}
    .micro {{ font-family:{FONT_STACK}; font-size:22px; font-weight:700; letter-spacing:2.8px; fill:{INK}; }}
    .micro-light {{ font-family:{FONT_STACK}; font-size:22px; font-weight:700; letter-spacing:2.8px; fill:{BG}; }}
</style>
<pattern id="paper-grain" width="18" height="18" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1.1" fill="{INK}" opacity="0.055"/>
</pattern>
</defs>
'''

SVG_FOOTER = '</svg>\n'


def svg_bg():
    return (
        f'<rect x="0" y="0" width="1920" height="1080" fill="{BG}"/>\n'
        f'<rect x="0" y="0" width="1920" height="1080" fill="url(#paper-grain)"/>\n'
    )


def svg_safe_area_guides():
    """Guias visuais sutis para safe areas (apenas nos masters)."""
    return (
        f'<rect x="64" y="64" width="1792" height="952" fill="none" '
        f'stroke="{NEUTRAL}" stroke-width="1" stroke-dasharray="8 8" opacity="0.3"/>\n'
        f'<rect x="96" y="96" width="1728" height="888" fill="none" '
        f'stroke="{NEUTRAL}" stroke-width="1" stroke-dasharray="4 8" opacity="0.2"/>\n'
    )


def svg_metadata(comp_id, family, accent, character_present, character_function, visual_class,
                 focus_mode=None):
    config = load_json(CONFIG_PATH)
    composition = composition_by_id(config, comp_id)
    meta = {
        "composition_id": comp_id,
        "family": family,
        "status": composition["status"] if composition else "EXPERIMENTAL",
        "accent": accent,
        "visual_system": "CO_VISUAL_V3",
        "art_direction": "CO_ART_DIRECTION_V4",
        "composition_system": "CO_EDITORIAL_COMPOSITIONS_V1",
        "selection_mode": SELECTION_MODE,
        "character_present": character_present,
        "character_function": character_function,
        "visual_class": visual_class,
        "composition_version": composition["version"] if composition else None,
        "calibration": composition.get("calibration", {}) if composition else {},
        "generated_at": datetime.datetime.now().astimezone().isoformat(),
    }
    if focus_mode:
        meta["focus_mode"] = focus_mode
    if character_present:
        meta["asset_sources"] = ["assets/characters/capital_oculto_character_rig_v4.svg"]
        with open(RIG_PATH, "rb") as f:
            meta["asset_source_hashes"] = {
                "assets/characters/capital_oculto_character_rig_v4.svg": hashlib.sha256(f.read()).hexdigest()
            }
    else:
        meta["asset_sources"] = []
        meta["asset_source_hashes"] = {}
    return f'<metadata>{json.dumps(meta, ensure_ascii=False)}</metadata>\n'


def read_rig_defs():
    """Lê o conteúdo do rig V4 para incorporar nos defs das cenas com personagem."""
    with open(RIG_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    # Extrair o conteúdo entre <defs> e </defs>
    start = content.find("<!--")
    end = content.find("</defs>")
    if start >= 0 and end >= 0:
        return content[start:end]
    return ""


RIG_DEFS = None


def get_rig_defs():
    global RIG_DEFS
    if RIG_DEFS is None:
        RIG_DEFS = read_rig_defs()
    return RIG_DEFS


# ── Contratos determinísticos ────────────────────────────────────────────────

ZONE_FIELDS = {
    "id", "x", "y", "width", "height", "content_type", "font_size",
    "max_chars", "max_lines", "align", "overflow_policy", "safe_area_policy",
}
CONTENT_FORMATS = {
    "currency_short", "currency_delta", "percentage", "plain_number",
    "short_label", "headline", "keyword", "short_statement",
}
TEXTUAL_ZONE_TYPES = {
    "text_stack", "display_number", "headline", "label", "composite",
    "keyword", "short_statement",
}
BLEED_CONTENT_TYPES = {
    "structural_line", "structural_surface", "highlight_space", "display_number",
}

MASTER_CONTENT = {
    "CO-COMP-01A": {"context_stack": ["SALÁRIO ANTERIOR", "3.500", "RENDA MENSAL"], "hero_number": "4.200", "delta_label": "+ R$ 700", "micro_context": "RENDA MENSAL • NOVO VALOR"},
    "CO-COMP-01B": {"top_label": "SOBRA DO MÊS • MÊS 3", "hero_number": "R$ 20", "currency_prefix": "R$", "bottom_context": ["O AUMENTO ERA DE R$ 700", "RESTAM VINTE"]},
    "CO-COMP-01C": {"hero_number": "4200", "currency_prefix": "R$", "annotation_label": ["NOVO SALÁRIO MENSAL", "O AUMENTO FOI REAL"], "accent_detail": "+ R$ 700"},
    "CO-COMP-04A": {"new_state_label": "AGORA", "new_state_number": "R$ 4.200", "old_state_ghost": "R$ 3.500", "old_state_label": "ANTES", "time_micro": "3 MESES DEPOIS"},
    "CO-COMP-04B": {"old_state_area": ["DELIVERY", "= FESTA"], "new_state_area": ["DELIVERY", "= TERÇA"], "old_label": "EXCEÇÃO", "new_label": "ROTINA"},
    "CO-COMP-04C": {"ghost_number": "700", "current_number": "700", "interpretation_label": ["O AUMENTO PARECE", "INVISÍVEL"], "time_marker": "3 MESES DEPOIS"},
    "CO-COMP-03A": {"left_mass_label": ["GASTOS", "FIXOS"], "gap_value": "700", "right_mass_label": ["GASTOS", "NOVOS"], "bottom_label": "RENDA R$ 4.200"},
    "CO-COMP-03B": {"top_label": "EXPECTATIVA", "remaining_value": "R$ 20", "bottom_label": "GASTOS REAIS", "side_context": ["MARGEM", "RESTANTE", "MÊS 3"]},
    "CO-COMP-03C": {"force_left": "2.8k", "force_left_label": "GASTOS FIXOS", "center_target": "20", "center_label": "SOBRA", "force_right": "680", "force_right_label": "GASTOS NOVOS"},
}

SCENE_CONTENT = {
    "CO-COMP-01C": {"hero_number": "4.200", "currency_prefix": "R$", "annotation_label": "SEU SALÁRIO AUMENTOU", "accent_detail": "+ R$ 700"},
    "CO-COMP-04A": {"new_state_label": "AGORA", "new_state_number": "R$ 4.200", "old_state_ghost": "R$ 3.500", "old_state_label": "ANTES", "time_micro": "A REFERÊNCIA SUBIU"},
    "CO-COMP-03A": {"left_mass_label": ["GASTOS", "FIXOS"], "gap_value": "20", "right_mass_label": ["GASTOS", "NOVOS"], "bottom_label": "RENDA R$ 4.200"},
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as source:
        return json.load(source)


def composition_by_id(config, comp_id):
    return next((item for item in config["compositions"] if item["id"] == comp_id), None)


def select_composition(config, rules, comp_id, mode):
    """Resolve uma variante sem permitir EXPERIMENTAL em produção."""
    mode_contract = rules.get("selection_modes", {}).get(mode)
    if not mode_contract:
        return "NEEDS_NEW_COMPOSITION"
    composition = composition_by_id(config, comp_id)
    if not composition:
        return "NEEDS_NEW_COMPOSITION"
    if composition["status"] not in mode_contract.get("allowed_statuses", []):
        return "NEEDS_NEW_COMPOSITION"
    return composition


def validate_composition_contracts(config, rules, mode):
    """Valida apenas propriedades declaradas; não mede tipografia real."""
    errors = []
    if mode not in {"EXPERIMENTAL_TEST", "PRODUCTION"}:
        errors.append(f"selection_mode inválido: {mode}")

    modes = rules.get("selection_modes", {})
    if modes.get("EXPERIMENTAL_TEST", {}).get("allowed_statuses") != ["APPROVED", "EXPERIMENTAL"]:
        errors.append("EXPERIMENTAL_TEST deve aceitar APPROVED e EXPERIMENTAL")
    if modes.get("PRODUCTION", {}).get("allowed_statuses") != ["APPROVED"]:
        errors.append("PRODUCTION deve aceitar somente APPROVED")

    compositions = config.get("compositions", [])
    if len(compositions) != 14:
        errors.append(f"esperadas 14 variantes; encontradas {len(compositions)}")
    expected_families = {
        "DATA_HERO", "MOVING_BASELINE", "SHRINKING_SPACE",
        "EDITORIAL_TYPE", "SYSTEM_MAP",
    }
    if set(config.get("families", [])) != expected_families:
        errors.append("o catálogo deve conter exatamente as 5 famílias contratadas")

    family_parameters = config.get("family_parameters", {})
    focus_modes = family_parameters.get("SHRINKING_SPACE", {}).get("focus_modes", {})
    if set(focus_modes) != {"COMPRESSION_FIRST", "RESULT_FIRST"}:
        errors.append("SHRINKING_SPACE deve declarar COMPRESSION_FIRST e RESULT_FIRST")
    if S003_FOCUS_MODE not in focus_modes:
        errors.append(f"focus_mode de S003 inválido: {S003_FOCUS_MODE}")

    ids = set()
    for composition in compositions:
        comp_id = composition.get("id", "SEM_ID")
        if comp_id in ids:
            errors.append(f"ID duplicado: {comp_id}")
        ids.add(comp_id)
        expected_status = "APPROVED" if comp_id in APPROVED_TARGETS else "EXPERIMENTAL"
        if composition.get("status") != expected_status:
            errors.append(f"{comp_id}: status deve ser {expected_status}")
        for zone in composition.get("content_zones", []):
            missing = ZONE_FIELDS - set(zone)
            if missing:
                errors.append(f"{comp_id}/{zone.get('id')}: campos ausentes {sorted(missing)}")
                continue
            if zone["overflow_policy"] != "REJECT_COMPOSITION":
                errors.append(f"{comp_id}/{zone['id']}: overflow_policy inválida")
            policy = zone["safe_area_policy"]
            if policy not in {"STRICT", "BLEED_ALLOWED"}:
                errors.append(f"{comp_id}/{zone['id']}: safe_area_policy inválida")
            if policy == "STRICT":
                if zone["x"] < 96 or zone["y"] < 96:
                    errors.append(f"{comp_id}/{zone['id']}: STRICT invade início da safe area de texto")
                if zone["x"] + zone["width"] > 1824 or zone["y"] + zone["height"] > 984:
                    errors.append(f"{comp_id}/{zone['id']}: STRICT excede safe area de texto")
            elif zone["content_type"] not in BLEED_CONTENT_TYPES:
                errors.append(f"{comp_id}/{zone['id']}: BLEED_ALLOWED aplicado a conteúdo legível")

            content_format = zone.get("content_format")
            if zone["content_type"] in TEXTUAL_ZONE_TYPES and content_format not in CONTENT_FORMATS:
                errors.append(f"{comp_id}/{zone['id']}: content_format ausente ou inválido")
            if content_format and content_format not in CONTENT_FORMATS:
                errors.append(f"{comp_id}/{zone['id']}: content_format desconhecido")

    expected_calibrations = {
        "CO-COMP-01C": {"hero_crop_intensity", "delta_prominence", "microcontext_dominance"},
        "CO-COMP-04A": {"old_state_visibility_ratio", "baseline_emphasis", "current_state_dominance"},
        "CO-COMP-03A": {"focus_mode", "gap_dominance", "result_dominance", "gap_ratio"},
    }
    for comp_id, keys in expected_calibrations.items():
        composition = composition_by_id(config, comp_id)
        if not composition or composition.get("version") != 1.1:
            errors.append(f"{comp_id}: versão calibrada 1.1 ausente")
            continue
        if set(composition.get("calibration", {})) != keys:
            errors.append(f"{comp_id}: parâmetros de calibração divergentes")
    if composition_by_id(config, "CO-COMP-03A").get("focus_mode_default") != S003_FOCUS_MODE:
        errors.append("CO-COMP-03A não declara o focus_mode usado por S003")

    # PRODUCTION aceita somente as variantes aprovadas humanamente.
    production_ids = {
        item["id"] for item in compositions
        if select_composition(config, rules, item["id"], "PRODUCTION") != "NEEDS_NEW_COMPOSITION"
    }
    if production_ids != APPROVED_TARGETS:
        errors.append("PRODUCTION deve aceitar somente 01C, 04A e 03A")

    mechanisms = rules.get("mechanisms", {})
    strong_statement = mechanisms.get("strong_statement", {})
    if strong_statement.get("primary_family") != "EDITORIAL_TYPE":
        errors.append("strong_statement deve resolver EDITORIAL_TYPE")
    if "DATA_HERO" not in strong_statement.get("forbidden_families", []):
        errors.append("strong_statement não pode usar DATA_HERO como fallback")
    system_routes = mechanisms.get("system_relationship", {}).get("conditional_routing", {})
    for semantic in ("feedback", "network", "dependency", "more_than_two_without_compression"):
        if system_routes.get(semantic) != "SYSTEM_MAP":
            errors.append(f"system_relationship/{semantic} deve resolver SYSTEM_MAP")
    for semantic in ("compression", "pressure", "constraint", "loss_of_space", "dual_force_squeeze"):
        if system_routes.get(semantic) != "SHRINKING_SPACE":
            errors.append(f"system_relationship/{semantic} deve resolver SHRINKING_SPACE")
    accumulation = mechanisms.get("accumulation", {}).get("conditional_routing", {})
    if accumulation.get("limited_resource_consumed") != "SHRINKING_SPACE":
        errors.append("accumulation limitada deve resolver SHRINKING_SPACE")
    if accumulation.get("final_total_is_dominant") != "DATA_HERO":
        errors.append("accumulation com total dominante deve resolver DATA_HERO")
    if accumulation.get("generic_accumulation") != "NEEDS_NEW_COMPOSITION":
        errors.append("accumulation genérica deve exigir nova composição")
    time_adaptation = mechanisms.get("time_adaptation", {})
    if time_adaptation.get("primary_family") != "MOVING_BASELINE":
        errors.append("time_adaptation deve permanecer em MOVING_BASELINE")
    if time_adaptation.get("variant_routing", {}).get("conceptual_keywords") != "CO-COMP-04D":
        errors.append("time_adaptation conceitual deve resolver CO-COMP-04D")
    return errors


def validate_content_bindings(config, bindings, binding_name):
    """Aplica formato/linhas/caracteres sem fingir medição tipográfica."""
    errors = []
    numeric_patterns = {
        "currency_short": r"R\$\s?[0-9][0-9.,kK]*",
        "currency_delta": r"[+-]\s?R\$\s?[0-9][0-9.,kK]*",
        "percentage": r"[+-]?[0-9]+%",
        "plain_number": r"[0-9][0-9.,kK]*",
    }
    for comp_id, zone_values in bindings.items():
        composition = composition_by_id(config, comp_id)
        if not composition:
            errors.append(f"{binding_name}/{comp_id}: composição ausente")
            continue
        zones = {zone["id"]: zone for zone in composition["content_zones"]}
        expected = {zone_id for zone_id, zone in zones.items() if zone.get("content_format")}
        if set(zone_values) != expected:
            errors.append(f"{binding_name}/{comp_id}: bindings divergentes; esperado {sorted(expected)}, recebido {sorted(zone_values)}")
            continue
        for zone_id, raw_value in zone_values.items():
            zone = zones[zone_id]
            lines = raw_value if isinstance(raw_value, list) else [raw_value]
            if len(lines) > zone["max_lines"]:
                errors.append(f"{binding_name}/{comp_id}/{zone_id}: max_lines excedido")
            for value in lines:
                if len(value) > zone["max_chars"]:
                    errors.append(f"{binding_name}/{comp_id}/{zone_id}: max_chars excedido por {value!r}")
                pattern = numeric_patterns.get(zone["content_format"])
                if pattern and not re.fullmatch(pattern, value):
                    errors.append(f"{binding_name}/{comp_id}/{zone_id}: {value!r} incompatível com {zone['content_format']}")
    return errors


# ── Geradores de composições master ──────────────────────────


def gen_comp_01a():
    """CO-COMP-01A — Data Hero lateral."""
    body = svg_bg()
    body += svg_safe_area_guides()

    # Superfície escura à esquerda como container de contexto
    body += f'<rect x="0" y="0" width="620" height="1080" fill="{INK}" data-role="context-surface"/>\n'

    # Contexto empilhado na coluna esquerda
    body += f'<text x="96" y="200" class="headline-light" style="font-size:48px">SALÁRIO ANTERIOR</text>\n'
    body += f'<text x="96" y="340" class="display-light" style="font-size:120px;letter-spacing:-5px">3.500</text>\n'
    body += f'<text x="96" y="400" class="micro-light" style="opacity:.6">RENDA MENSAL</text>\n'

    # Seta de transição
    body += (f'<line x1="520" y1="540" x2="720" y2="540" stroke="{LIME}" '
             f'stroke-width="8" stroke-linecap="round"/>\n')
    body += f'<polygon points="720,520 760,540 720,560" fill="{LIME}"/>\n'

    # Hero number — dominante à direita
    body += (f'<text x="700" y="680" class="display" style="font-size:330px" '
             f'data-dominant="true">4.200</text>\n')
    body += f'<text x="720" y="340" class="headline" style="font-size:72px">R$</text>\n'

    # Delta com destaque
    body += f'<text x="720" y="820" class="headline" style="font-size:96px;fill:{LIME}">+ R$ 700</text>\n'

    # Micro-label
    body += f'<text x="720" y="900" class="label">RENDA MENSAL  •  NOVO VALOR</text>\n'

    return body


def gen_comp_01b():
    """CO-COMP-01B — Data Hero central."""
    body = svg_bg()
    body += svg_safe_area_guides()

    # Label superior
    body += f'<text x="96" y="140" class="label">SOBRA DO MÊS  •  MÊS 3</text>\n'

    # Superfície dividida: metade superior = background, metade inferior escura
    body += f'<rect x="0" y="580" width="1920" height="500" fill="{INK}" data-role="contrast-surface"/>\n'

    # Número hero centrado
    body += (f'<text x="960" y="620" class="display" text-anchor="middle" '
             f'style="font-size:440px;letter-spacing:-18px" data-dominant="true">R$ 20</text>\n')

    # Context inferior
    body += f'<text x="96" y="980" class="label-light">O AUMENTO ERA DE R$ 700</text>\n'
    body += f'<text x="1824" y="980" class="label-light" text-anchor="end">RESTAM VINTE</text>\n'

    return body


def gen_comp_01c():
    """CO-COMP-01C — Data Hero oversized / cropped."""
    body = svg_bg()
    body += svg_safe_area_guides()

    # Número tão grande que sai do frame
    body += (f'<text x="-40" y="750" class="display" '
             f'style="font-size:640px;letter-spacing:-26px;opacity:0.10" '
             f'data-role="ghost">4200</text>\n')
    body += (f'<text x="-20" y="730" class="display" '
             f'style="font-size:640px;letter-spacing:-26px" '
             f'data-dominant="true">4200</text>\n')
    body += f'<text x="96" y="170" class="headline" style="font-size:96px">R$</text>\n'

    # Anotação editorial no canto inferior esquerdo
    body += f'<text x="96" y="940" class="label">NOVO SALÁRIO MENSAL</text>\n'
    body += f'<text x="96" y="970" class="micro" style="opacity:.55">O AUMENTO FOI REAL</text>\n'

    # Accent detail no canto inferior direito
    body += f'<text x="1824" y="955" class="headline" text-anchor="end" style="font-size:88px;fill:{LIME}">+ R$ 700</text>\n'

    return body


def gen_comp_04a():
    """CO-COMP-04A — Moving Baseline horizontal."""
    body = svg_bg()
    body += svg_safe_area_guides()

    # Novo estado (acima da baseline)
    body += f'<text x="96" y="140" class="headline" style="font-size:48px">AGORA</text>\n'
    body += (f'<text x="96" y="340" class="display" '
             f'style="font-size:180px;letter-spacing:-7px">R$ 4.200</text>\n')

    # Baseline atual forte e baseline anterior fantasma.
    body += f'<rect x="64" y="464" width="1792" height="16" rx="8" fill="{INK}" data-role="current-baseline"/>\n'
    body += f'<rect x="64" y="460" width="1336" height="8" rx="4" fill="{AMBER}" data-role="baseline-accent"/>\n'
    body += (f'<line x1="64" y1="760" x2="1856" y2="760" stroke="{NEUTRAL}" '
             f'stroke-width="4" stroke-linecap="round" stroke-dasharray="18 14" data-role="old-baseline"/>\n')

    # Estado antigo (abaixo, ghosted)
    body += (f'<text x="96" y="700" class="display" '
             f'style="font-size:140px;letter-spacing:-5px;fill:{NEUTRAL}">R$ 3.500</text>\n')
    body += f'<text x="96" y="840" class="micro">ANTES</text>\n'

    # Seta indicando deslocamento da baseline
    body += f'<line x1="1600" y1="740" x2="1600" y2="520" stroke="{AMBER}" stroke-width="6" stroke-linecap="round"/>\n'
    body += f'<circle cx="1600" cy="760" r="12" fill="{NEUTRAL}"/>\n'
    body += f'<polygon points="1580,530 1600,490 1620,530" fill="{AMBER}"/>\n'
    body += f'<text x="1640" y="615" class="micro" style="fill:{AMBER}">REFERÊNCIA</text>\n'
    body += f'<text x="1640" y="645" class="micro" style="fill:{AMBER}">SUBIU</text>\n'

    # Time marker
    body += f'<text x="1824" y="960" class="label" text-anchor="end">3 MESES DEPOIS</text>\n'

    return body


def gen_comp_04b():
    """CO-COMP-04B — Moving Baseline vertical."""
    body = svg_bg()
    body += svg_safe_area_guides()

    # Lado esquerdo — estado antigo (desbotado)
    body += f'<rect x="0" y="0" width="900" height="1080" fill="{BG}" data-role="old-state"/>\n'
    body += f'<rect x="0" y="0" width="900" height="1080" fill="url(#paper-grain)"/>\n'

    body += f'<text x="200" y="260" class="headline" text-anchor="middle" style="font-size:48px;opacity:0.35">ANTES</text>\n'
    body += (f'<text x="450" y="520" class="display" text-anchor="middle" '
             f'style="font-size:96px;opacity:0.25">DELIVERY</text>\n')
    body += (f'<text x="450" y="620" class="display" text-anchor="middle" '
             f'style="font-size:96px;opacity:0.25">= FESTA</text>\n')
    body += f'<text x="450" y="700" class="micro" text-anchor="middle" style="opacity:.25">RARO E ESPECIAL</text>\n'

    # Divisor vertical forte
    body += (f'<rect x="900" y="0" width="12" height="1080" fill="{INK}" '
             f'data-role="baseline-divider"/>\n')

    # Lado direito — estado novo (dominante)
    body += f'<rect x="912" y="0" width="1008" height="1080" fill="{INK}" data-role="new-state"/>\n'

    body += f'<text x="1416" y="260" class="headline-light" text-anchor="middle" style="font-size:48px">AGORA</text>\n'
    body += (f'<text x="1416" y="520" class="display-light" text-anchor="middle" '
             f'style="font-size:96px">DELIVERY</text>\n')
    body += (f'<text x="1416" y="620" class="display-light" text-anchor="middle" '
             f'style="font-size:96px">= TERÇA</text>\n')
    body += f'<text x="1416" y="700" class="micro-light" style="opacity:.6" text-anchor="middle">ROTINA COMUM</text>\n'

    # Labels inferiores
    body += f'<text x="450" y="980" class="label" text-anchor="middle" style="opacity:0.35">EXCEÇÃO</text>\n'
    body += f'<text x="1416" y="980" class="label-light" text-anchor="middle">ROTINA</text>\n'

    return body


def gen_comp_04c():
    """CO-COMP-04C — Moving Baseline ghost overlay."""
    body = svg_bg()
    body += svg_safe_area_guides()

    # Ghost number (estado antigo) — oversized, muito transparente
    body += (f'<text x="960" y="620" class="display" text-anchor="middle" '
             f'style="font-size:380px;letter-spacing:-16px;opacity:0.08" '
             f'data-role="ghost-state">700</text>\n')

    # Current number (estado novo — a sobra que parece igual)
    body += (f'<text x="960" y="640" class="display" text-anchor="middle" '
             f'style="font-size:380px;letter-spacing:-16px" '
             f'data-dominant="true">700</text>\n')

    # A sobreposição cria tensão: o mesmo número, dois significados

    # Interpretação
    body += (f'<text x="96" y="860" class="headline" '
             f'style="font-size:56px">O AUMENTO PARECE</text>\n')
    body += (f'<text x="96" y="930" class="headline" '
             f'style="font-size:56px;fill:{AMBER}">INVISÍVEL</text>\n')

    # Time marker
    body += f'<text x="1824" y="960" class="label" text-anchor="end">3 MESES DEPOIS</text>\n'

    # Linhas de marca — a baseline antiga cruzada
    body += (f'<line x1="300" y1="680" x2="1620" y2="680" stroke="{NEUTRAL}" '
             f'stroke-width="3" stroke-linecap="round" stroke-dasharray="12 8" opacity="0.4"/>\n')

    return body


def gen_comp_03a(focus_mode=S003_FOCUS_MODE):
    """CO-COMP-03A — Shrinking Space horizontal."""
    body = svg_bg()
    body += svg_safe_area_guides()

    gap_width = 400 if focus_mode == "COMPRESSION_FIRST" else 520
    mass_width = (1920 - gap_width) // 2
    gap_end = mass_width + gap_width
    value_size = 180 if focus_mode == "COMPRESSION_FIRST" else 240
    gap_dominant = ' data-dominant="true"' if focus_mode == "COMPRESSION_FIRST" else ''
    value_dominant = ' data-dominant="true"' if focus_mode == "RESULT_FIRST" else ''

    # Massa esquerda (gastos fixos)
    body += f'<rect x="0" y="0" width="{mass_width}" height="1080" fill="{INK}" data-role="left-force"/>\n'
    body += (f'<text x="{mass_width / 2:g}" y="500" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">GASTOS</text>\n')
    body += (f'<text x="{mass_width / 2:g}" y="560" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">FIXOS</text>\n')
    body += f'<text x="{mass_width / 2:g}" y="640" class="display-light" text-anchor="middle" style="font-size:120px">2.800</text>\n'

    # Gap (folga) — faixa central iluminada com accent
    body += f'<rect x="{mass_width}" y="0" width="{gap_width}" height="1080" fill="{LIME}" opacity="0.15" data-role="gap" data-focus-mode="{focus_mode}"{gap_dominant}/>\n'
    body += (f'<line x1="{mass_width}" y1="0" x2="{mass_width}" y2="1080" stroke="{LIME}" '
             f'stroke-width="4" stroke-linecap="round"/>\n')
    body += (f'<line x1="{gap_end}" y1="0" x2="{gap_end}" y2="1080" stroke="{LIME}" '
             f'stroke-width="4" stroke-linecap="round"/>\n')

    # Valor da folga no gap
    body += (f'<text x="960" y="520" class="display" text-anchor="middle" '
             f'style="font-size:{value_size}px;fill:{LIME}" data-role="result"{value_dominant}>700</text>\n')
    body += f'<text x="960" y="600" class="label" text-anchor="middle" style="fill:{INK}">FOLGA</text>\n'

    # Setas de compressão
    body += f'<polygon points="{mass_width - 20},540 {mass_width - 60},520 {mass_width - 60},560" fill="{INK}"/>\n'
    body += f'<polygon points="{gap_end + 20},540 {gap_end + 60},520 {gap_end + 60},560" fill="{INK}"/>\n'

    # Massa direita (gastos novos)
    body += f'<rect x="{gap_end}" y="0" width="{mass_width}" height="1080" fill="{INK}" data-role="right-force"/>\n'
    body += (f'<text x="{gap_end + mass_width / 2:g}" y="500" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">GASTOS</text>\n')
    body += (f'<text x="{gap_end + mass_width / 2:g}" y="560" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">NOVOS</text>\n')
    body += f'<text x="{gap_end + mass_width / 2:g}" y="640" class="display-light" text-anchor="middle" style="font-size:120px">680</text>\n'

    # Label inferior
    body += f'<text x="960" y="980" class="label" text-anchor="middle">RENDA R$ 4.200</text>\n'

    return body


def gen_comp_03b():
    """CO-COMP-03B — Shrinking Space vertical."""
    body = svg_bg()
    body += svg_safe_area_guides()

    # Pressão superior (expectativa descendo)
    body += f'<rect x="460" y="0" width="1000" height="340" fill="{INK}" data-role="top-pressure"/>\n'
    body += (f'<text x="960" y="220" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">EXPECTATIVA</text>\n')
    body += f'<text x="960" y="290" class="display-light" text-anchor="middle" style="font-size:72px">↓</text>\n'

    # Seta de pressão descendo
    body += f'<polygon points="940,340 960,380 980,340" fill="{INK}"/>\n'

    # Faixa central — margem restante
    body += f'<rect x="460" y="380" width="1000" height="320" fill="{LIME}" opacity="0.15" data-role="remaining-band"/>\n'
    body += (f'<line x1="460" y1="380" x2="1460" y2="380" stroke="{LIME}" '
             f'stroke-width="4" stroke-linecap="round"/>\n')
    body += (f'<line x1="460" y1="700" x2="1460" y2="700" stroke="{LIME}" '
             f'stroke-width="4" stroke-linecap="round"/>\n')

    body += (f'<text x="960" y="570" class="display" text-anchor="middle" '
             f'style="font-size:180px;fill:{LIME}" data-dominant="true">R$ 20</text>\n')

    # Seta de pressão subindo
    body += f'<polygon points="940,740 960,700 980,740" fill="{INK}"/>\n'

    # Pressão inferior (gastos subindo)
    body += f'<rect x="460" y="740" width="1000" height="340" fill="{INK}" data-role="bottom-pressure"/>\n'
    body += (f'<text x="960" y="880" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">GASTOS REAIS</text>\n')
    body += f'<text x="960" y="950" class="display-light" text-anchor="middle" style="font-size:72px">↑</text>\n'

    # Contexto lateral
    body += f'<text x="96" y="540" class="label">MARGEM</text>\n'
    body += f'<text x="96" y="580" class="label">RESTANTE</text>\n'
    body += f'<text x="96" y="640" class="micro" style="opacity:.55">MÊS 3</text>\n'

    return body


def gen_comp_03c():
    """CO-COMP-03C — Shrinking Space entre duas forças."""
    body = svg_bg()
    body += svg_safe_area_guides()

    # Força esquerda — círculo grande representando gastos fixos
    body += f'<circle cx="380" cy="480" r="300" fill="{INK}" data-role="force-left"/>\n'
    body += (f'<text x="380" y="460" class="display-light" text-anchor="middle" '
             f'style="font-size:120px">2.8k</text>\n')

    # Seta da força esquerda
    body += f'<polygon points="680,460 720,480 680,500" fill="{INK}"/>\n'

    # Alvo central — personagem e valor
    body += (f'<text x="960" y="460" class="display" text-anchor="middle" '
             f'style="font-size:160px;fill:{LIME}" data-dominant="true">20</text>\n')
    body += f'<text x="960" y="530" class="label" text-anchor="middle">SOBRA</text>\n'

    # Seta da força direita
    body += f'<polygon points="1240,460 1200,480 1240,500" fill="{INK}"/>\n'

    # Força direita — círculo representando gastos novos
    body += f'<circle cx="1540" cy="480" r="280" fill="{INK}" data-role="force-right"/>\n'
    body += (f'<text x="1540" y="460" class="display-light" text-anchor="middle" '
             f'style="font-size:120px">680</text>\n')

    # Labels de força
    body += f'<text x="380" y="840" class="label" text-anchor="middle">GASTOS FIXOS</text>\n'
    body += f'<text x="1540" y="840" class="label" text-anchor="middle">GASTOS NOVOS</text>\n'

    # Micro context
    body += f'<text x="960" y="980" class="micro" text-anchor="middle" style="opacity:.55">RENDA: R$ 4.200  •  MÊS 3</text>\n'

    return body


# ── Geradores S001–S003 ──────────────────────────────────────


def gen_s001():
    """S001 — Aumento de renda. Mecanismo: state_change / surprising_number.
    Composição: CO-COMP-01C (Data Hero oversized/cropped).

    Justificativa: O momento é o impacto emocional do número novo.
    O espectador deve SENTIR a escala do 4.200 antes de processar.
    A variante oversized/cropped cria esse efeito de escala extrema
    sem depender de ícones, cards ou elementos decorativos.
    """
    meta = svg_metadata("CO-COMP-01C", "DATA_HERO", "lime",
                         False, None, "data_hero")
    body = svg_bg()

    # Número oversized — cortado pelo canvas
    # O "4.200" é tão grande que as extremidades saem do frame
    body += (f'<text x="-40" y="750" class="display" '
             f'style="font-size:640px;letter-spacing:-26px;fill:{NEUTRAL};opacity:0.08" '
             f'data-role="ghost-shadow">4.200</text>\n')
    body += (f'<text x="-20" y="730" class="display" '
             f'style="font-size:640px;letter-spacing:-26px" '
             f'data-dominant="true">4.200</text>\n')

    # R$ como prefixo editorial posicionado no espaço superior
    body += f'<text x="96" y="170" class="headline" style="font-size:96px">R$</text>\n'

    # Delta com accent — a informação interpretativa
    body += f'<text x="1824" y="955" class="headline" text-anchor="end" style="font-size:88px;fill:{LIME}">+ R$ 700</text>\n'

    # Micro-label editorial
    body += f'<text x="96" y="960" class="label">SEU SALÁRIO AUMENTOU</text>\n'

    scene_id = "S001"
    composition = "CO-COMP-01C"
    return wrap_scene(scene_id, composition, "data_hero",
                      "salary_counter_steps_from_3500_to_4200", meta, body)


def gen_s002():
    """S002 — O novo salário parece normal. Mecanismo: time_adaptation / baseline_shift.
    Composição: CO-COMP-04A (Moving Baseline horizontal).

    Justificativa: 04C aproximava demais a cena de DATA_HERO. A 04A
    torna a referência antiga, o deslocamento e o novo patamar partes
    inseparáveis da mesma composição.
    """
    meta = svg_metadata("CO-COMP-04A", "MOVING_BASELINE", "amber",
                         False, None, "transformation")
    body = svg_bg()

    # Estado atual domina acima da baseline nova.
    body += f'<text x="96" y="140" class="headline" style="font-size:48px">AGORA</text>\n'
    body += (f'<text x="96" y="340" class="display" '
             f'style="font-size:180px;letter-spacing:-7px" data-dominant="true">R$ 4.200</text>\n')

    # Duas referências tornam o deslocamento inequívoco.
    body += f'<rect x="64" y="464" width="1792" height="16" rx="8" fill="{INK}" data-role="current-baseline"/>\n'
    body += f'<rect x="64" y="460" width="1336" height="8" rx="4" fill="{AMBER}" data-role="baseline-accent"/>\n'
    body += (f'<line x1="64" y1="760" x2="1856" y2="760" stroke="{NEUTRAL}" '
             f'stroke-width="4" stroke-linecap="round" stroke-dasharray="18 14" data-role="old-baseline"/>\n')

    # Estado anterior permanece visível, mas secundário.
    body += (f'<text x="96" y="700" class="display" '
             f'style="font-size:140px;letter-spacing:-5px;fill:{NEUTRAL}" '
             f'data-role="old-state">R$ 3.500</text>\n')
    body += f'<text x="96" y="840" class="micro">ANTES</text>\n'

    # Vetor de mudança conecta fisicamente as duas baselines.
    body += f'<line x1="1600" y1="740" x2="1600" y2="520" stroke="{AMBER}" stroke-width="6" stroke-linecap="round"/>\n'
    body += f'<circle cx="1600" cy="760" r="12" fill="{NEUTRAL}"/>\n'
    body += f'<polygon points="1580,530 1600,490 1620,530" fill="{AMBER}"/>\n'
    body += f'<text x="1824" y="960" class="label" text-anchor="end">A REFERÊNCIA SUBIU</text>\n'

    scene_id = "S002"
    composition = "CO-COMP-04A"
    return wrap_scene(scene_id, composition, "transformation",
                      "old_baseline_moves_to_current_baseline", meta, body)


def gen_s003():
    """S003 — Folga financeira diminuindo. Mecanismo: progressive_loss.
    Composição: CO-COMP-03A (Shrinking Space horizontal).

    Justificativa: A ideia é compressão — o espectador precisa VER
    o espaço encolhendo antes de ler qualquer número. As duas massas
    escuras (gastos fixos e gastos novos) se aproximam lateralmente,
    deixando uma faixa central cada vez mais estreita. O R$ 20 restante
    dentro da faixa comunica a escala do problema.
    """
    meta = svg_metadata("CO-COMP-03A", "SHRINKING_SPACE", "lime",
                         False, None, "scale", focus_mode=S003_FOCUS_MODE)
    body = svg_bg()

    # ── Massa esquerda — gastos fixos ──
    body += f'<rect x="0" y="0" width="760" height="1080" fill="{INK}" data-role="left-force"/>\n'

    # Conteúdo na massa esquerda — texto rotacionado não é confiável em SVG puro,
    # então usamos posicionamento vertical empilhado
    body += (f'<text x="380" y="400" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">GASTOS</text>\n')
    body += (f'<text x="380" y="460" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">FIXOS</text>\n')
    body += (f'<text x="380" y="600" class="display-light" text-anchor="middle" '
             f'style="font-size:140px">2.8k</text>\n')
    body += f'<text x="380" y="680" class="micro-light" text-anchor="middle" style="opacity:.5">ALUGUEL • LUZ • MERCADO</text>\n'

    # ── Gap central — folga financeira ──
    # A faixa é propositalmente estreita para comunicar compressão
    body += f'<rect x="760" y="0" width="400" height="1080" fill="{LIME}" opacity="0.12" data-role="gap" data-focus-mode="{S003_FOCUS_MODE}" data-dominant="true"/>\n'
    body += (f'<line x1="760" y1="0" x2="760" y2="1080" stroke="{LIME}" '
             f'stroke-width="4" stroke-linecap="round"/>\n')
    body += (f'<line x1="1160" y1="0" x2="1160" y2="1080" stroke="{LIME}" '
             f'stroke-width="4" stroke-linecap="round"/>\n')

    # Valor restante no centro do gap
    body += f'<text x="960" y="420" class="headline" text-anchor="middle" style="font-size:72px">R$</text>\n'
    body += (f'<text x="960" y="620" class="display" text-anchor="middle" '
             f'style="font-size:180px;fill:{LIME}" data-role="result">20</text>\n')
    body += f'<text x="960" y="700" class="label" text-anchor="middle">SOBRA</text>\n'

    # Setas de compressão
    body += f'<polygon points="730,540 690,520 690,560" fill="{INK}"/>\n'
    body += f'<polygon points="1190,540 1230,520 1230,560" fill="{INK}"/>\n'

    # ── Massa direita — gastos novos ──
    body += f'<rect x="1160" y="0" width="760" height="1080" fill="{INK}" data-role="right-force"/>\n'

    body += (f'<text x="1540" y="400" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">GASTOS</text>\n')
    body += (f'<text x="1540" y="460" class="headline-light" text-anchor="middle" '
             f'style="font-size:48px">NOVOS</text>\n')
    body += (f'<text x="1540" y="600" class="display-light" text-anchor="middle" '
             f'style="font-size:140px">680</text>\n')
    body += f'<text x="1540" y="680" class="micro-light" text-anchor="middle" style="opacity:.5">DELIVERY • STREAMING • PARCELA</text>\n'

    # ── Label inferior ──
    body += f'<text x="960" y="980" class="micro" text-anchor="middle" style="opacity:.55">RENDA R$ 4.200</text>\n'

    scene_id = "S003"
    composition = "CO-COMP-03A"
    return wrap_scene(scene_id, composition, "scale",
                      "masses_approach_and_gap_narrows", meta, body,
                      focus_mode=S003_FOCUS_MODE)


def wrap_scene(scene_id, composition, visual_class, future_motion, meta, body,
               focus_mode=None):
    """Envolve o conteúdo da cena no grupo correto."""
    return (
        meta +
        f'<g id="scene-{scene_id}" data-composition="{composition}" '
        f'data-visual-class="{visual_class}" '
        f'data-future-motion="{future_motion}"'
        + (f' data-focus-mode="{focus_mode}"' if focus_mode else '')
        + '>\n'
        + body +
        '</g>\n'
    )


# ── Contact sheet generator ─────────────────────────────────


def gen_contact_sheet(items, cols, title, scale=1.0):
    """Gera um contact sheet SVG com múltiplos frames.

    items: lista de (label, svg_path)
    cols: colunas do grid
    title: título do contact sheet
    scale: escala dos frames (1.0 = 100%, 0.25 = 25%)
    """
    frame_w = int(1920 * scale)
    frame_h = int(1080 * scale)
    padding = 32
    label_h = 48

    rows = (len(items) + cols - 1) // cols
    total_w = cols * (frame_w + padding) + padding
    total_h = rows * (frame_h + label_h + padding) + padding + 80  # 80 para título

    lines = []
    lines.append(f'<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                 f'width="{total_w}" height="{total_h}" '
                 f'viewBox="0 0 {total_w} {total_h}">')
    lines.append(f'<rect width="{total_w}" height="{total_h}" fill="#E8E8E4"/>')
    lines.append(f'<text x="{total_w//2}" y="50" text-anchor="middle" '
                 f'font-family="{FONT_STACK}" font-size="32" font-weight="800" '
                 f'fill="{INK}">{title}</text>')

    for i, (label, svg_path) in enumerate(items):
        row = i // cols
        col = i % cols
        x = padding + col * (frame_w + padding)
        y = 80 + row * (frame_h + label_h + padding)

        # Frame border
        lines.append(f'<rect x="{x-1}" y="{y-1}" width="{frame_w+2}" height="{frame_h+2}" '
                     f'fill="none" stroke="{NEUTRAL}" stroke-width="2"/>')

        # Embed the SVG as image reference
        # Convertemos para caminho relativo
        rel_path = os.path.relpath(svg_path, CONTACT_DIR).replace(os.sep, "/")
        lines.append(f'<image x="{x}" y="{y}" width="{frame_w}" height="{frame_h}" '
                     f'href="{rel_path}"/>')

        # Label
        lines.append(f'<text x="{x + frame_w//2}" y="{y + frame_h + 30}" text-anchor="middle" '
                     f'font-family="{FONT_STACK}" font-size="20" font-weight="700" '
                     f'fill="{INK}">{label}</text>')

    lines.append('</svg>')
    return '\n'.join(lines)


# ── Validador ────────────────────────────────────────────────


def validate_svg(svg_content, comp_id):
    """Validação determinística do SVG gerado."""
    errors = []

    # Canvas correto
    if 'width="1920"' not in svg_content:
        errors.append(f"{comp_id}: canvas width != 1920")
    if 'height="1080"' not in svg_content:
        errors.append(f"{comp_id}: canvas height != 1080")
    if 'viewBox="0 0 1920 1080"' not in svg_content:
        errors.append(f"{comp_id}: viewBox incorreto")

    # Paleta — verificar cores não autorizadas
    allowed_colors = {INK, LIME, AMBER, BG, NEUTRAL, "none", "url(#paper-grain)"}
    # Checar fills e strokes (heurística básica)
    import re
    fills = re.findall(r'fill="(#[0-9A-Fa-f]{6})"', svg_content)
    strokes = re.findall(r'stroke="(#[0-9A-Fa-f]{6})"', svg_content)
    for color in fills + strokes:
        if color.upper() not in {c.upper() for c in allowed_colors if c.startswith("#")}:
            errors.append(f"{comp_id}: cor não autorizada: {color}")

    # IDs duplicados
    ids = re.findall(r'id="([^"]+)"', svg_content)
    seen = set()
    for id_val in ids:
        if id_val in seen:
            errors.append(f"{comp_id}: ID duplicado: {id_val}")
        seen.add(id_val)

    # Metadata presente
    if '<metadata>' not in svg_content:
        errors.append(f"{comp_id}: metadata ausente")

    return errors


# ── Main ─────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("CAPITAL OCULTO — GERADOR DE COMPOSIÇÕES EDITORIAIS V1")
    print("=" * 60)
    print()

    config = load_json(CONFIG_PATH)
    rules = load_json(RULES_PATH)
    contract_errors = validate_composition_contracts(config, rules, SELECTION_MODE)
    contract_errors.extend(validate_content_bindings(config, MASTER_CONTENT, "masters"))
    contract_errors.extend(validate_content_bindings(config, SCENE_CONTENT, "S001-S003"))
    for comp_id in ("CO-COMP-01C", "CO-COMP-04A", "CO-COMP-03A"):
        if select_composition(config, rules, comp_id, SELECTION_MODE) == "NEEDS_NEW_COMPOSITION":
            contract_errors.append(f"{comp_id}: indisponível em {SELECTION_MODE}")
    if contract_errors:
        print("-- CONTRATO INVALIDO - PREVIEWS NAO SERAO GERADOS --")
        for error in contract_errors:
            print(f"  [ERRO] {error}")
        return len(contract_errors)
    print(f"  [OK] Contrato validado em selection_mode={SELECTION_MODE}")
    print("  [OK] PRODUCTION aceita somente 01C, 04A e 03A; outras 11 seguem EXPERIMENTAL")
    print()

    # Criar diretórios
    for d in [
        os.path.join(COMPOSITIONS_DIR, "data_hero"),
        os.path.join(COMPOSITIONS_DIR, "moving_baseline"),
        os.path.join(COMPOSITIONS_DIR, "shrinking_space"),
        MASTERS_DIR,
        SCENES_DIR,
        CONTACT_DIR,
    ]:
        os.makedirs(d, exist_ok=True)
        print(f"  [DIR] {os.path.relpath(d, PROJECT_ROOT)}")

    print()

    # ── Gerar masters ────────────────────────────────────────
    masters = [
        ("CO-COMP-01A", "data_hero", gen_comp_01a),
        ("CO-COMP-01B", "data_hero", gen_comp_01b),
        ("CO-COMP-01C", "data_hero", gen_comp_01c),
        ("CO-COMP-04A", "moving_baseline", gen_comp_04a),
        ("CO-COMP-04B", "moving_baseline", gen_comp_04b),
        ("CO-COMP-04C", "moving_baseline", gen_comp_04c),
        ("CO-COMP-03A", "shrinking_space", gen_comp_03a),
        ("CO-COMP-03B", "shrinking_space", gen_comp_03b),
        ("CO-COMP-03C", "shrinking_space", gen_comp_03c),
    ]

    all_errors = []
    print("-- CALIBRANDO MASTERS AFETADOS --")
    for comp_id, family, gen_func in masters:
        if comp_id not in CALIBRATION_TARGETS:
            print(f"  [PRESERVADO] {comp_id}")
            continue
        body = gen_func()
        focus_mode = S003_FOCUS_MODE if comp_id == "CO-COMP-03A" else None
        accent = "amber" if comp_id == "CO-COMP-04A" else "lime"
        meta = svg_metadata(comp_id, family.upper().replace("_", " ").title().replace(" ", "_").upper(),
                            accent, False, None, family, focus_mode=focus_mode)

        svg = SVG_HEADER + meta
        svg += f'<g id="master-{comp_id}" data-family="{family}">\n'
        svg += body
        svg += '</g>\n'
        svg += SVG_FOOTER

        # Salvar na família
        family_path = os.path.join(COMPOSITIONS_DIR, family, f"{comp_id}.svg")
        with open(family_path, "w", encoding="utf-8") as f:
            f.write(svg)

        # Salvar no masters
        master_path = os.path.join(MASTERS_DIR, f"{comp_id}.svg")
        with open(master_path, "w", encoding="utf-8") as f:
            f.write(svg)

        # Validar
        errors = validate_svg(svg, comp_id)
        all_errors.extend(errors)

        status = "OK" if not errors else f"ERRO ({len(errors)} erros)"
        print(f"  [{status}] {comp_id} -> {os.path.relpath(family_path, PROJECT_ROOT)}")

    print()

    # ── Gerar cenas S001–S003 ────────────────────────────────
    scenes = [
        ("S001", gen_s001),
        ("S002", gen_s002),
        ("S003", gen_s003),
    ]

    scene_paths = []

    print("-- GERANDO CENAS S001-S003 --")
    for scene_id, gen_func in scenes:
        content = gen_func()
        svg = SVG_HEADER + content + SVG_FOOTER

        scene_path = os.path.join(SCENES_DIR, f"{scene_id.lower()}.svg")
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write(svg)

        scene_paths.append((scene_id, scene_path))

        # Validar
        errors = validate_svg(svg, scene_id)
        all_errors.extend(errors)

        status = "OK" if not errors else f"ERRO ({len(errors)} erros)"
        print(f"  [{status}] {scene_id} -> {os.path.relpath(scene_path, PROJECT_ROOT)}")

    print()

    # ── Gerar contact sheets ─────────────────────────────────
    print("-- GERANDO CONTACT SHEETS --")

    # 1. Contact sheet S001–S003 a 100% (um por linha)
    cs_scenes_full = gen_contact_sheet(scene_paths, 1,
                                       "S001–S003 — PILOTO EDITORIAL (100%)", scale=1.0)
    cs_scenes_path = os.path.join(CONTACT_DIR, "contact_s001_s003_100.svg")
    with open(cs_scenes_path, "w", encoding="utf-8") as f:
        f.write(cs_scenes_full)
    print(f"  [OK] S001-S003 100% -> {os.path.relpath(cs_scenes_path, PROJECT_ROOT)}")

    # 2. Contact sheet S001–S003 simulando 25%
    cs_scenes_25 = gen_contact_sheet(scene_paths, 3,
                                     "S001–S003 — SIMULAÇÃO 25%", scale=0.25)
    cs_scenes_25_path = os.path.join(CONTACT_DIR, "contact_s001_s003_25pct.svg")
    with open(cs_scenes_25_path, "w", encoding="utf-8") as f:
        f.write(cs_scenes_25)
    print(f"  [OK] S001-S003 25% -> {os.path.relpath(cs_scenes_25_path, PROJECT_ROOT)}")

    print()

    # ── Relatório de validação ───────────────────────────────
    print("-- VALIDACAO --")
    if not all_errors:
        print("  [OK] Todas as validacoes deterministicas passaram.")
    else:
        for err in all_errors:
            print(f"  [ERRO] {err}")
    print()

    print(f"Total de erros: {len(all_errors)}")
    print()
    print("=" * 60)
    print("GERAÇÃO CONCLUÍDA")
    print("=" * 60)

    return len(all_errors)


if __name__ == "__main__":
    exit(main())
