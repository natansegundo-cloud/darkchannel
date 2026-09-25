#!/usr/bin/env python3
"""Compositor vetorial offline do Capital Oculto.

Le o roteiro visual do episodio e cria cenas SVG 1920x1080. O compositor
implementa os blocos aprovados; nenhuma biblioteca externa ou modelo generativo e usado.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
STYLE_FILE = ROOT / "config" / "vector_style.json"
ASSET_REGISTRY = [
    ("CO_WORKER_V1", "character", "assets/characters/worker.svg", "S001", "Protagonista principal"),
    ("CO_ANA_V1", "character", "assets/characters/ana.svg", "S004", "Estreia como amiga na vinheta central"),
    ("expression_neutral", "expression", "assets/expressions/neutral.svg", "S004", "Expressao cotidiana"),
    ("expression_surprised", "expression", "assets/expressions/surprised.svg", "S001", "Reacao ao aumento"),
    ("expression_worried", "expression", "assets/expressions/worried.svg", "S003", "Tensao diante do saldo"),
    ("expression_relieved", "expression", "assets/expressions/relieved.svg", "S002", "Alivio temporario"),
    ("expression_thinking", "expression", "assets/expressions/thinking.svg", "S005", "Compreensao dos mecanismos"),
    ("expression_fascinated", "expression", "assets/expressions/fascinated.svg", "S008", "Encanto do primeiro dia"),
    ("expression_realization", "expression", "assets/expressions/realization.svg", "S007", "Descoberta de que a referencia mudou"),
    ("pose_neutral", "pose", "assets/poses/neutral.svg", "S004", "Pose-base"),
    ("pose_celebrate", "pose", "assets/poses/celebrate.svg", "S002", "Celebracao e alivio"),
    ("pose_phone", "pose", "assets/poses/phone.svg", "S001", "Segurando celular"),
    ("pose_tension", "pose", "assets/poses/tension.svg", "S003", "Corpo contraido"),
    ("pose_pulled", "pose", "assets/poses/pulled.svg", "S005", "Puxado por mecanismos"),
    ("pose_pointing", "pose", "assets/poses/pointing.svg", "S007", "Aponta para a regua interna"),
    ("pose_umbrella", "pose", "assets/poses/umbrella.svg", "S015", "Segura a protecao sobre necessidades basicas"),
    ("pose_walking", "pose", "assets/poses/walking.svg", "S016", "Caminha da pressao para a zona segura"),
    ("phone_raise", "object", "assets/objects/phone_raise.svg", "S001", "Notificacao de aumento"),
    ("calendar", "object", "assets/objects/calendar.svg", "S002", "Passagem do tempo"),
    ("bills", "object", "assets/objects/bills.svg", "S005", "Contas recorrentes"),
    ("brain_console", "object", "assets/objects/brain_console.svg", "S006", "Mecanismo de recalibracao"),
    ("normality_ruler", "object", "assets/objects/normality_ruler.svg", "S006", "Regua do novo normal"),
    ("phone_generic", "object", "assets/objects/phone_generic.svg", "S008", "Celular reutilizavel com estados"),
    ("emotion_curve", "object", "assets/objects/emotion_curve.svg", "S010", "Curva original de tres ondas"),
    ("opposing_routes", "object", "assets/objects/opposing_routes.svg", "S011", "Emocao desce enquanto aspiracao sobe"),
    ("podium_floor", "object", "assets/objects/podium_floor.svg", "S012", "Conquista elevada que se transforma em piso"),
    ("delivery_bag", "object", "assets/objects/delivery_bag.svg", "S013", "Sacola generica para habito de delivery"),
    ("expectation_race", "object", "assets/objects/expectation_race.svg", "S014", "Renda e expectativa em trajetorias convergentes"),
    ("security_umbrella", "object", "assets/objects/security_umbrella.svg", "S015", "Protecao material para necessidades concretas"),
    ("safety_path", "object", "assets/objects/safety_path.svg", "S016", "Travessia da pressao para seguranca e escolha"),
    ("research_page", "object", "assets/objects/research_page.svg", "S017", "Pagina cientifica abstrata sem reproduzir estudo real"),
    ("income_levels", "object", "assets/objects/income_levels.svg", "S018", "Niveis de renda com respostas individuais variadas"),
    ("magic_number_sign", "object", "assets/objects/magic_number_sign.svg", "S019", "Placa abstrata negando um teto universal"),
    ("comparison_elevator", "object", "assets/objects/comparison_elevator.svg", "S020", "Elevadores paralelos de renda e referencia social"),
    ("office_stations", "object", "assets/objects/office_stations.svg", "S021", "Estacoes equivalentes do grupo anterior a promocao"),
    ("status_signals", "object", "assets/objects/status_signals.svg", "S022", "Sinais moderados de carro viagem e moradia"),
    ("relative_steps", "object", "assets/objects/relative_steps.svg", "S024", "Escada de posicao dentro do grupo de comparacao"),
    ("upward_gaze", "object", "assets/objects/upward_gaze.svg", "S025", "Campo de atencao seletiva voltado para cima"),
    ("racing_rulers", "object", "assets/objects/racing_rulers.svg", "S026", "Renda sobe enquanto a referencia se afasta"),
    ("peer_envelope", "object", "assets/objects/peer_envelope.svg", "S027", "Envelope abstrato com informacao sobre pares"),
    ("budget_shift", "object", "assets/objects/budget_shift.svg", "S028", "Redistribuicao parcial para bens duraveis"),
    ("comparison_feed", "object", "assets/objects/comparison_feed.svg", "S029", "Feed generico com carro moradia e viagem"),
    ("paycheck_blocks", "object", "assets/objects/paycheck_blocks.svg", "S030", "Contracheque-base em quatro blocos mais um"),
    ("small_upgrades", "object", "assets/objects/small_upgrades.svg", "S031", "Cinco melhorias cotidianas sem luxo"),
    ("commitment_bar", "object", "assets/objects/commitment_bar.svg", "S032", "Barra proporcional de mil com novecentos e cinquenta comprometidos"),
    ("fictional_case_file", "object", "assets/objects/fictional_case_file.svg", "S034", "Ficha didatica sem dados pessoais ou aparencia oficial"),
    ("pleasure_vs_bill", "object", "assets/objects/pleasure_vs_bill.svg", "S035", "Prazer que perde brilho e cobranca que permanece"),
    ("walking_bills", "object", "assets/objects/walking_bills.svg", "S036", "Cobrancas recorrentes que avancam ao primeiro plano"),
    ("three_gears", "object", "assets/objects/three_gears.svg", "S037", "Sintese de adaptacao comparacao e compromissos"),
    ("synthesis_flow", "object", "assets/objects/synthesis_flow.svg", "S038", "Fluxo de conquista para normal e aperto"),
    ("enough_triangle", "object", "assets/objects/enough_triangle.svg", "S039", "Relacao entre renda compromissos e normal"),
    ("decision_interval", "object", "assets/objects/decision_interval.svg", "S040", "Espaco de decisao antes de nova despesa fixa"),
    ("conscious_balance", "object", "assets/objects/conscious_balance.svg", "S041", "Balanca entre conforto escolhido e upgrades automaticos"),
    ("destination_envelopes", "object", "assets/objects/destination_envelopes.svg", "S042", "Tres destinos visuais sem percentuais ou recomendacao financeira"),
    ("freedom_shadow", "object", "assets/objects/freedom_shadow.svg", "S043", "Contracheque amplo com pequena area livre apos as contas"),
    ("callback_threads", "object", "assets/objects/callback_threads.svg", "S044", "Tres fios que reconectam a mensagem aos mecanismos centrais"),
    ("locking_calendar", "object", "assets/objects/locking_calendar.svg", "S045", "Calendario abstrato em que upgrades se tornam compromissos"),
    ("background_paper", "background", "assets/backgrounds/paper.svg", "S002", "Fundo de papel quente"),
    ("background_graphite", "background", "assets/backgrounds/graphite.svg", "S001", "Fundo escuro"),
]


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Arquivo nao encontrado: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON invalido em {path}: {exc}") from exc


def resolve_episode(value: str) -> Path:
    direct = Path(value)
    if direct.is_dir():
        return direct.resolve()
    local = ROOT / value
    if local.is_dir():
        return local.resolve()
    matches = sorted((ROOT / "episodios").glob(f"{value}-*"))
    if len(matches) == 1:
        return matches[0].resolve()
    if not matches:
        raise RuntimeError(f"Episodio nao encontrado: {value}")
    raise RuntimeError(f"Episodio ambiguo: {value}")


def episode_id(episode: Path) -> str:
    metadata = load_json(episode / "episodio.json")
    return str(metadata.get("episodio_id") or metadata.get("id") or episode.name)


def read_visual_script(episode: Path) -> list[dict[str, str]]:
    source = episode / "04_ROTEIRO_VISUAL.csv"
    try:
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Roteiro visual nao encontrado: {source}") from exc
    required = {"scene_id", "asset_id", "visual", "motion", "text_on_screen"}
    fields = set(rows[0].keys()) if rows else set()
    missing = required - fields
    if missing:
        raise RuntimeError(f"Colunas ausentes no roteiro visual: {', '.join(sorted(missing))}")
    return rows


def read_scene_specs(episode: Path) -> dict[str, dict[str, Any]]:
    path = episode / "assets" / "vector_scenes.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    if payload.get("episode_id") != episode_id(episode):
        raise RuntimeError(f"episode_id divergente em {path}")
    if payload.get("style_id") != "CO_SKETCH_V1":
        raise RuntimeError(f"style_id divergente em {path}")
    scenes = payload.get("scenes")
    if not isinstance(scenes, dict):
        raise RuntimeError(f"Campo scenes invalido em {path}")
    return {str(key).upper(): value for key, value in scenes.items()}


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


def text_node(x: float, y: float, value: str, css: str = "headline", **values: Any) -> str:
    return tag("text", escape(value), x=round(x, 2), y=round(y, 2), class_=css, **values)


def line(x1: float, y1: float, x2: float, y2: float, css: str = "ink", **values: Any) -> str:
    return tag("line", x1=x1, y1=y1, x2=x2, y2=y2, class_=css, **values)


def path(d: str, css: str = "ink", **values: Any) -> str:
    return tag("path", d=d, class_=css, **values)


def rough_line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    seed: int,
    css: str = "ink",
    bend: float = 8,
) -> str:
    rng = random.Random(seed)
    mx = (x1 + x2) / 2 + rng.uniform(-bend, bend)
    my = (y1 + y2) / 2 + rng.uniform(-bend, bend)
    d1 = f"M {x1:.1f} {y1:.1f} Q {mx:.1f} {my:.1f} {x2:.1f} {y2:.1f}"
    d2 = f"M {x1 + rng.uniform(-2, 2):.1f} {y1 + rng.uniform(-2, 2):.1f} Q {mx + rng.uniform(-3, 3):.1f} {my + rng.uniform(-3, 3):.1f} {x2 + rng.uniform(-2, 2):.1f} {y2 + rng.uniform(-2, 2):.1f}"
    return path(d1, css) + path(d2, css + " ghost")


def face(expression: str) -> str:
    eye_y = -342
    parts = [
        tag("circle", cx=-27, cy=eye_y, r=7, class_="eye"),
        tag("circle", cx=27, cy=eye_y, r=7, class_="eye"),
    ]
    if expression == "surprised":
        parts.extend(
            [
                path("M -45 -368 Q -27 -382 -9 -368", "face-line"),
                path("M 9 -368 Q 27 -382 45 -368", "face-line"),
                tag("circle", cx=0, cy=-310, r=15, class_="mouth-open"),
            ]
        )
    elif expression == "worried":
        parts.extend(
            [
                path("M -48 -370 Q -28 -356 -9 -363", "face-line"),
                path("M 9 -363 Q 28 -356 48 -370", "face-line"),
                path("M -27 -298 Q 0 -325 27 -298", "face-line"),
            ]
        )
    elif expression == "relieved":
        parts.extend(
            [
                path("M -45 -368 Q -27 -374 -9 -368", "face-line"),
                path("M 9 -368 Q 27 -374 45 -368", "face-line"),
                path("M -28 -318 Q 0 -290 28 -318", "face-line"),
            ]
        )
    elif expression == "thinking":
        parts.extend(
            [
                path("M -46 -372 L -10 -365", "face-line"),
                path("M 10 -365 L 46 -378", "face-line"),
                path("M -22 -303 Q 1 -312 27 -303", "face-line"),
            ]
        )
    elif expression == "fascinated":
        parts.extend(
            [
                path("M -48 -375 Q -27 -389 -7 -374", "face-line"),
                path("M 7 -374 Q 27 -389 48 -375", "face-line"),
                path("M -34 -316 Q 0 -276 34 -316", "face-line"),
                tag("circle", cx=-27, cy=eye_y, r=14, fill="none", class_="face-line"),
                tag("circle", cx=27, cy=eye_y, r=14, fill="none", class_="face-line"),
            ]
        )
    elif expression == "realization":
        parts.extend(
            [
                path("M -48 -378 Q -28 -392 -8 -376", "face-line"),
                path("M 8 -368 Q 28 -376 47 -366", "face-line"),
                path("M -27 -314 Q 0 -284 29 -310", "face-line"),
            ]
        )
    else:
        parts.extend(
            [
                path("M -44 -369 Q -27 -376 -10 -369", "face-line"),
                path("M 10 -369 Q 27 -376 44 -369", "face-line"),
                path("M -24 -310 Q 0 -298 24 -310", "face-line"),
            ]
        )
    return "".join(parts)


POSES: dict[str, dict[str, tuple[float, float]]] = {
    "neutral": {
        "left_hand": (-120, -90),
        "right_hand": (120, -90),
        "left_foot": (-68, 92),
        "right_foot": (68, 92),
    },
    "celebrate": {
        "left_hand": (-145, -290),
        "right_hand": (145, -290),
        "left_foot": (-76, 92),
        "right_foot": (76, 92),
    },
    "phone": {
        "left_hand": (-105, -75),
        "right_hand": (82, -205),
        "left_foot": (-70, 92),
        "right_foot": (70, 92),
    },
    "tension": {
        "left_hand": (-115, -205),
        "right_hand": (95, -215),
        "left_foot": (-92, 92),
        "right_foot": (54, 92),
    },
    "pulled": {
        "left_hand": (-145, -190),
        "right_hand": (142, -120),
        "left_foot": (-92, 92),
        "right_foot": (76, 92),
    },
    "pointing": {
        "left_hand": (-205, -414),
        "right_hand": (118, -92),
        "left_foot": (-72, 92),
        "right_foot": (72, 92),
    },
    "umbrella": {
        "left_hand": (-72, -230),
        "right_hand": (72, -230),
        "left_foot": (-72, 92),
        "right_foot": (72, 92),
    },
    "walking": {
        "left_hand": (-145, -150),
        "right_hand": (138, -245),
        "left_foot": (-118, 92),
        "right_foot": (96, 55),
    },
}


def character(
    x: float,
    y: float,
    *,
    scale: float = 1.0,
    expression: str = "neutral",
    pose: str = "neutral",
    flip: bool = False,
    head_tilt: float = 0,
    variant: str = "worker",
    instance_id: str | None = None,
) -> str:
    points = POSES.get(pose, POSES["neutral"])
    flip_scale = -scale if flip else scale
    instance_id = instance_id or f"{variant}-{round(x)}-{round(y)}"
    torso = tag("rect", x=-62, y=-244, width=124, height=188, rx=42, class_="outfit")
    pocket = tag("rect", x=18, y=-199, width=26, height=28, rx=5, class_="pocket")
    arm_left = group(
        rough_line(-43, -200, *points["left_hand"], seed=101, css="limb", bend=12),
        id_=f"{instance_id}--arm-left",
        class_="rig-part",
        data_part="arm-left",
        style="transform-origin:-43px -200px",
    )
    arm_right = group(
        rough_line(43, -200, *points["right_hand"], seed=102, css="limb", bend=12),
        id_=f"{instance_id}--arm-right",
        class_="rig-part",
        data_part="arm-right",
        style="transform-origin:43px -200px",
    )
    leg_left = group(
        rough_line(-32, -65, *points["left_foot"], seed=103, css="limb", bend=10)
        + line(points["left_foot"][0] - 22, points["left_foot"][1], points["left_foot"][0] + 18, points["left_foot"][1], "shoe"),
        id_=f"{instance_id}--leg-left",
        class_="rig-part",
        data_part="leg-left",
        style="transform-origin:-32px -65px",
    )
    leg_right = group(
        rough_line(32, -65, *points["right_foot"], seed=104, css="limb", bend=10)
        + line(points["right_foot"][0] - 18, points["right_foot"][1], points["right_foot"][0] + 22, points["right_foot"][1], "shoe"),
        id_=f"{instance_id}--leg-right",
        class_="rig-part",
        data_part="leg-right",
        style="transform-origin:32px -65px",
    )
    hair_back = ""
    hair_front = ""
    if variant == "ana":
        hair_back = tag("path", d="M -91 -346 Q -82 -445 8 -438 Q 99 -425 96 -326 L 70 -263 L 48 -326 L -63 -326 L -72 -263 L -98 -323 Z", class_="hair")
        hair_front = tag("path", d="M -72 -385 Q -22 -443 62 -393 L 49 -357 Q 4 -390 -58 -350 Z", class_="hair")
    head_content = hair_back + tag("circle", cx=0, cy=-334, r=91, class_="head") + hair_front + face(expression)
    head = group(
        head_content,
        id_=f"{instance_id}--head",
        class_="rig-part",
        data_part="head",
        style="transform-origin:0px -334px",
        transform=f"rotate({head_tilt} 0 -334)",
    )
    torso_group = group(
        torso + pocket + line(0, -248, 0, -257, "neck"),
        id_=f"{instance_id}--torso",
        class_="rig-part",
        data_part="torso",
    )
    content = leg_left + leg_right + arm_left + arm_right + torso_group + head
    transform = f"translate({x} {y}) scale({flip_scale} {scale})"
    return group(
        content,
        id_=instance_id,
        class_="character rough character-rig",
        data_rig="CO_ANA_V1" if variant == "ana" else "CO_WORKER_V1",
        data_expression=expression,
        data_pose=pose,
        transform=transform,
    )


def phone(x: float, y: float, *, scale: float = 1.0, alert: bool = True) -> str:
    shell = tag("rect", x=-110, y=-205, width=220, height=410, rx=42, class_="phone-shell")
    screen = tag("rect", x=-85, y=-165, width=170, height=310, rx=18, class_="phone-screen")
    speaker = line(-30, -183, 30, -183, "phone-detail")
    content = shell + screen + speaker
    if alert:
        content += tag("rect", x=-62, y=-75, width=124, height=94, rx=18, class_="alert-card")
        content += path("M -34 -12 L -4 -42 L 18 -20 L 51 -59", "growth")
        content += path("M 30 -59 L 51 -59 L 51 -38", "growth")
    else:
        content += path("M -48 -20 Q -10 -58 22 -21 T 58 -44", "balance-low")
    return group(content, class_="rough", transform=f"translate({x} {y}) scale({scale})")


def calendar(x: float, y: float, *, scale: float = 1.0, faded: bool = False) -> str:
    opacity = 0.35 if faded else 1
    body = tag("path", d="M -150 -115 Q 0 -132 150 -115 L 142 118 Q 0 130 -146 115 Z", class_="paper-card")
    body += path("M -150 -52 Q 0 -64 148 -50", "calendar-line")
    for col in (-82, 0, 82):
        body += tag("circle", cx=col, cy=5, r=14, class_="calendar-dot")
        body += tag("circle", cx=col, cy=62, r=14, class_="calendar-dot")
    return group(body, class_="rough", opacity=opacity, transform=f"translate({x} {y}) scale({scale})")


def bill_stack(x: float, y: float, *, scale: float = 1.0) -> str:
    content = ""
    for index, offset in enumerate((0, 42, 84)):
        content += tag("path", d=f"M {-120 + offset/5:.1f} {-105 + offset:.1f} Q 0 {-120 + offset:.1f} 120 {-102 + offset:.1f} L 112 {-45 + offset:.1f} Q 0 {-58 + offset:.1f} -116 {-42 + offset:.1f} Z", class_="bill")
        content += tag("circle", cx=60, cy=-76 + offset, r=9, class_="bill-dot")
    return group(content, class_="rough", transform=f"translate({x} {y}) scale({scale})")


def generic_phone(x: float, y: float, *, scale: float = 1.0, glowing: bool = False, instance_id: str = "phone-generic") -> str:
    shell = tag("rect", x=-110, y=-205, width=220, height=410, rx=42, class_="phone-shell")
    screen = tag("rect", x=-85, y=-165, width=170, height=310, rx=18, class_="phone-screen")
    speaker = line(-30, -183, 30, -183, "phone-detail")
    app = tag("rect", x=-48, y=-48, width=96, height=96, rx=22, class_="alert-card")
    app += path("M -24 20 Q 0 -14 24 20 M 0 -14 L 0 -35", "growth")
    content = shell + screen + speaker + app
    if glowing:
        rays = "".join(
            line(x1, y1, x2, y2, "growth")
            for x1, y1, x2, y2 in ((-142, -150, -182, -188), (142, -150, 182, -188), (-150, 0, -205, 0), (150, 0, 205, 0), (-132, 154, -174, 196), (132, 154, 174, 196))
        )
        glow = group(tag("ellipse", cx=0, cy=0, rx=188, ry=280, fill="#A8D83E", opacity=.16) + rays, id_=f"{instance_id}--glow", data_part="glow")
        content = glow + content
    return group(content, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="phone-generic")


def normality_ruler(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, level: float = .72, instance_id: str = "normality-ruler") -> str:
    p = style["palette"]
    body = tag("path", d="M -80 -245 Q 0 -258 80 -244 L 74 244 Q 0 258 -76 242 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=11)
    ticks = ""
    for index in range(7):
        tick_y = 190 - index * 64
        length = 56 if index % 2 == 0 else 36
        ticks += line(-55, tick_y, -55 + length, tick_y, "face-line")
    marker_y = 190 - max(0.0, min(1.0, level)) * 384
    marker = tag("path", d=f"M 20 {marker_y:.1f} L 112 {marker_y:.1f} L 82 {marker_y-24:.1f} M 112 {marker_y:.1f} L 82 {marker_y+24:.1f}", id_=f"{instance_id}--marker", data_part="marker", fill="none", stroke=p["lime"], stroke_width=14, stroke_linecap="round", stroke_linejoin="round")
    return group(body + ticks + marker, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="normality-ruler", data_level=level)


def brain_console(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "brain-console") -> str:
    p = style["palette"]
    panel = tag("path", d="M -285 -205 Q 0 -235 285 -205 L 270 215 Q 0 240 -275 210 Z", fill=p["graphite_soft"], stroke=p["graphite"], stroke_width=14)
    screen = tag("path", d="M -238 -158 Q -78 -175 70 -153 L 62 142 Q -82 160 -230 138 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=10)
    brain = path("M -150 18 C -205 -12 -196 -95 -136 -103 C -116 -158 -35 -164 -5 -116 C 38 -148 105 -120 108 -68 C 164 -50 164 34 115 55 C 112 112 40 135 3 96 C -38 137 -111 111 -112 60 C -160 61 -184 38 -150 18 Z", "growth")
    folds = path("M -115 -60 Q -70 -25 -108 20 M -38 -105 Q -4 -62 -42 -24 M 32 -102 Q 69 -55 31 -16 M 78 12 Q 38 43 74 80 M -54 42 Q -15 70 -50 96", "face-line")
    controls = "".join(tag("circle", cx=112 + index * 50, cy=118, r=14, fill=color, stroke=p["graphite"], stroke_width=5) for index, color in enumerate((p["lime"], p["yellow"], p["red"])))
    return group(panel + screen + brain + folds + controls, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="brain-console")


def emotion_curve(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "emotion-curve") -> str:
    p = style["palette"]
    curve = tag("path", d="M -360 105 C -310 -130 -220 -150 -150 24 C -90 -92 0 -92 65 44 C 122 -48 220 -36 318 78", id_=f"{instance_id}--path", data_part="path", fill="none", stroke=p["lime"], stroke_width=17, stroke_linecap="round", stroke_linejoin="round")
    guide = tag("path", d="M -380 145 Q 0 170 360 145", fill="none", stroke=p["graphite_soft"], stroke_width=8, stroke_linecap="round", stroke_dasharray="18 22", opacity=.55)
    points = group("".join(tag("circle", cx=px, cy=py, r=17, fill=p["paper_light"], stroke=p["graphite"], stroke_width=8) for px, py in ((-265, -70), (-45, -34), (190, 10))), id_=f"{instance_id}--markers", data_part="markers")
    return group(guide + curve + points, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="emotion-curve")


def flame_icon(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, opacity: float = 1.0) -> str:
    p = style["palette"]
    outer = tag(
        "path",
        d="M 0 82 C -60 55 -66 -6 -25 -49 C -20 -15 1 -24 8 -88 C 72 -42 74 40 30 75 C 20 83 10 87 0 82 Z",
        fill=p["yellow"],
        stroke=p["graphite"],
        stroke_width=10,
        stroke_linejoin="round",
    )
    inner = tag("path", d="M 2 55 C -22 38 -16 9 8 -18 C 34 8 34 38 16 55 Z", fill=p["paper_light"], opacity=.78)
    return group(outer + inner, class_="rough", opacity=opacity, transform=f"translate({x} {y}) scale({scale})")


def opposing_routes(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "opposing-routes") -> str:
    p = style["palette"]
    divider = tag("path", d="M 0 -250 Q 10 0 0 250", fill="none", stroke=p["paper_light"], stroke_width=7, stroke_dasharray="15 18", opacity=.35)
    emotion_path = tag("path", d="M -360 -145 Q -270 -40 -165 135", id_=f"{instance_id}--emotion-path", fill="none", stroke=p["yellow"], stroke_width=17, stroke_linecap="round", marker_end="url(#arrow-yellow)")
    aspiration_path = tag("path", d="M 150 145 Q 255 35 365 -145", id_=f"{instance_id}--aspiration-path", fill="none", stroke=p["lime"], stroke_width=17, stroke_linecap="round", marker_end="url(#arrow)")
    flames = flame_icon(-390, -160, style, scale=.72) + flame_icon(-275, -40, style, scale=.54, opacity=.8) + flame_icon(-165, 126, style, scale=.36, opacity=.62)
    steps = "".join(
        tag("rect", x=135 + index * 80, y=105 - index * 82, width=92, height=74 + index * 4, rx=8, fill=p["lime"], stroke=p["graphite"], stroke_width=8)
        for index in range(4)
    )
    return group(divider + emotion_path + aspiration_path + flames + steps, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="opposing-routes")


def podium_floor(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "podium-floor") -> str:
    p = style["palette"]
    surface = tag(
        "path",
        d="M -470 110 L -470 -55 L -280 -55 L -280 10 Q -170 95 -35 110 L 470 110 L 470 190 L -470 190 Z",
        id_=f"{instance_id}--surface",
        fill=p["lime"],
        stroke=p["graphite"],
        stroke_width=13,
        stroke_linejoin="round",
    )
    seam = tag("path", d="M -280 -55 L -280 10 Q -170 95 -35 110", fill="none", stroke=p["paper_light"], stroke_width=8, stroke_dasharray="18 16", opacity=.72)
    arrow = tag("path", d="M -195 -120 Q -40 -55 115 45", fill="none", stroke=p["graphite"], stroke_width=12, stroke_linecap="round", marker_end="url(#arrow-dark)")
    return group(surface + seam + arrow, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="podium-floor")


def delivery_bag(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "delivery-bag", faded: bool = False) -> str:
    p = style["palette"]
    body = tag("path", d="M -90 -62 Q 0 -82 90 -62 L 78 100 Q 0 116 -82 98 Z", fill=p["red"], stroke=p["graphite"], stroke_width=11)
    handles = tag("path", d="M -42 -58 Q -38 -130 0 -130 Q 38 -130 42 -58", fill="none", stroke=p["graphite"], stroke_width=11, stroke_linecap="round")
    mark = tag("circle", cx=0, cy=20, r=27, fill=p["paper_light"], stroke=p["graphite"], stroke_width=7)
    return group(body + handles + mark, id_=instance_id, class_="rough", opacity=.48 if faded else 1, transform=f"translate({x} {y}) scale({scale})", data_object="delivery-bag")


def expectation_race(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "expectation-race") -> str:
    p = style["palette"]
    baseline = tag("path", d="M -510 195 L 510 195", fill="none", stroke=p["graphite_soft"], stroke_width=9, stroke_linecap="round", opacity=.45)
    income = tag("path", d="M -470 145 L -205 20 L 40 -120 L 460 -175", id_=f"{instance_id}--income", data_part="income", fill="none", stroke=p["lime"], stroke_width=34, stroke_linecap="round", stroke_linejoin="round")
    expectation = tag("path", d="M -470 145 L -115 110 L 150 -15 L 460 -175", id_=f"{instance_id}--expectation", data_part="expectation", fill="none", stroke=p["yellow"], stroke_width=27, stroke_linecap="round", stroke_linejoin="round")
    finish = tag("circle", cx=460, cy=-175, r=28, fill=p["paper_light"], stroke=p["graphite"], stroke_width=10)
    labels = text_node(-475, 245, "RENDA", "label") + text_node(235, 105, "EXPECTATIVA", "label")
    return group(baseline + income + expectation + finish + labels, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="expectation-race")


def security_umbrella(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "security-umbrella") -> str:
    p = style["palette"]
    canopy = tag("path", d="M -360 0 Q -300 -250 0 -265 Q 300 -250 360 0 Q 270 -72 180 0 Q 90 -72 0 0 Q -90 -72 -180 0 Q -270 -72 -360 0 Z", id_=f"{instance_id}--canopy", data_part="canopy", fill=p["lime"], stroke=p["graphite"], stroke_width=14, stroke_linejoin="round")
    stem = tag("path", d="M 0 0 L 0 330 Q 0 390 72 370", id_=f"{instance_id}--stem", data_part="stem", fill="none", stroke=p["graphite"], stroke_width=16, stroke_linecap="round")
    ribs = tag("path", d="M -180 0 Q -130 -210 0 -265 M 180 0 Q 130 -210 0 -265 M 0 0 L 0 -265", fill="none", stroke=p["lime_dark"], stroke_width=8, opacity=.72)
    return group(canopy + ribs + stem, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="security-umbrella")


def safety_path(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "safety-path") -> str:
    p = style["palette"]
    road = tag("path", d="M -470 180 Q -210 95 20 120 Q 230 140 470 -80", id_=f"{instance_id}--road", data_part="road", fill="none", stroke=p["paper_light"], stroke_width=150, stroke_linecap="round", opacity=.96)
    guide = tag("path", d="M -470 180 Q -210 95 20 120 Q 230 140 470 -80", fill="none", stroke=p["lime"], stroke_width=15, stroke_linecap="round", stroke_dasharray="26 22", marker_end="url(#arrow)")
    boundary = tag("path", d="M 55 -230 Q 105 0 55 235", fill="none", stroke=p["blue"], stroke_width=10, stroke_dasharray="20 18", opacity=.7)
    return group(road + guide + boundary, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="safety-path")


def research_page(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "research-page") -> str:
    p = style["palette"]
    sheet = tag("path", d="M -400 -275 Q 0 -305 400 -270 L 380 275 Q 0 305 -392 270 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=13)
    heading = tag("rect", x=-330, y=-215, width=315, height=28, rx=14, fill=p["graphite"])
    lines = "".join(tag("rect", x=-330, y=-150 + index * 52, width=230 + (index % 2) * 65, height=13, rx=6, fill=p["graphite_soft"], opacity=.42) for index in range(5))
    curve = tag("path", d="M -55 145 Q 70 105 135 5 Q 205 -85 320 -110", id_=f"{instance_id}--curve", data_part="curve", fill="none", stroke=p["lime"], stroke_width=14, stroke_linecap="round")
    points = group("".join(tag("circle", cx=px, cy=py, r=15, fill=p["paper_light"], stroke=p["graphite"], stroke_width=7) for px, py in ((-25, 132), (45, 100), (110, 36), (190, -50), (295, -100))), id_=f"{instance_id}--groups", data_part="groups")
    lens = tag("circle", cx=205, cy=18, r=116, fill=p["paper_light"], fill_opacity=.12, stroke=p["blue"], stroke_width=14)
    handle = tag("path", d="M 285 102 L 365 190", fill="none", stroke=p["blue"], stroke_width=22, stroke_linecap="round")
    return group(sheet + heading + lines + curve + points + lens + handle, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="research-page")


def income_levels(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "income-levels") -> str:
    p = style["palette"]
    heights = (95, 5, -100, -40, -175)
    platforms = ""
    for index, height in enumerate(heights):
        px = -400 + index * 200
        platforms += tag("path", d=f"M {px-72} {height} Q {px} {height-10} {px+72} {height}", fill="none", stroke=p["paper_light"], stroke_width=18, stroke_linecap="round")
    arrow = tag("path", d="M -485 205 Q -120 100 120 -15 Q 290 -95 465 -225", id_=f"{instance_id}--income-arrow", data_part="income-arrow", fill="none", stroke=p["lime"], stroke_width=15, stroke_linecap="round", marker_end="url(#arrow)")
    return group(platforms + arrow, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="income-levels", data_heights=",".join(str(value) for value in heights))


def magic_number_sign(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "magic-number-sign") -> str:
    p = style["palette"]
    plate = tag("path", d="M -235 -245 Q 0 -270 235 -245 L 220 245 Q 0 270 -225 242 Z", fill=p["graphite"], stroke=p["graphite"], stroke_width=13)
    number = text_node(0, 105, "?", "headline-light", text_anchor="middle", font_size=310)
    band = tag("path", d="M -275 190 L 265 -190", id_=f"{instance_id}--band", data_part="band", fill="none", stroke=p["red"], stroke_width=88, stroke_linecap="round")
    band_edge = tag("path", d="M -275 190 L 265 -190", fill="none", stroke=p["paper_light"], stroke_width=8, stroke_dasharray="20 18", opacity=.65)
    return group(plate + number + band + band_edge, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="magic-number-sign")


def comparison_elevator(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "comparison-elevator") -> str:
    p = style["palette"]
    content = ""
    for index, offset in enumerate((-260, 260)):
        cabin_id = "income" if index == 0 else "peers"
        content += tag("rect", x=offset-205, y=-285, width=410, height=570, rx=28, fill=p["paper_light"], stroke=p["graphite"], stroke_width=14)
        content += tag("path", d=f"M {offset} -285 L {offset} 285", fill="none", stroke=p["graphite_soft"], stroke_width=8, opacity=.35)
        content += tag("path", d=f"M {offset-168} 228 L {offset+168} 228", id_=f"{instance_id}--{cabin_id}-floor", data_part=f"{cabin_id}-floor", fill="none", stroke=p["lime"] if index == 0 else p["yellow"], stroke_width=16, stroke_linecap="round")
        content += tag("path", d=f"M {offset} -360 L {offset} -310 M {offset-20} -338 L {offset} -360 L {offset+20} -338", fill="none", stroke=p["lime"] if index == 0 else p["yellow"], stroke_width=10, stroke_linecap="round", stroke_linejoin="round")
    beam = tag("path", d="M -520 -305 L 520 -305", fill="none", stroke=p["graphite"], stroke_width=18, stroke_linecap="round")
    return group(beam + content, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="comparison-elevator")


def office_stations(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "office-stations") -> str:
    p = style["palette"]
    content = ""
    for index, px in enumerate((-420, -140, 140, 420)):
        content += tag("path", d=f"M {px-112} 45 Q {px} 30 {px+112} 45", fill="none", stroke=p["graphite"], stroke_width=17, stroke_linecap="round")
        content += tag("path", d=f"M {px-78} 48 L {px-88} 170 M {px+78} 48 L {px+88} 170", fill="none", stroke=p["graphite"], stroke_width=12, stroke_linecap="round")
        content += tag("rect", x=px-48, y=-55, width=96, height=72, rx=12, fill=p["paper_light"], stroke=p["graphite"], stroke_width=8)
        content += tag("circle", cx=px+70, cy=5, r=15, fill=p["lime"], stroke=p["graphite"], stroke_width=5)
    thread = tag("path", d="M -490 205 Q 0 240 490 205", id_=f"{instance_id}--thread", data_part="thread", fill="none", stroke=p["lime"], stroke_width=11, stroke_dasharray="22 18", stroke_linecap="round")
    return group(content + thread, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="office-stations")


def status_signals(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "status-signals") -> str:
    p = style["palette"]
    cards = ""
    card_specs = ((-330, -50, "key"), (0, -155, "travel"), (330, -50, "home"))
    for px, py, kind in card_specs:
        cards += tag("rect", x=px-120, y=py-95, width=240, height=190, rx=28, fill=p["paper_light"], stroke=p["graphite"], stroke_width=11)
        if kind == "key":
            icon = tag("circle", cx=px-25, cy=py, r=32, fill="none", stroke=p["yellow"], stroke_width=14) + tag("path", d=f"M {px+5} {py} L {px+75} {py} M {px+45} {py} L {px+45} {py+28}", fill="none", stroke=p["yellow"], stroke_width=14, stroke_linecap="round")
        elif kind == "travel":
            icon = tag("rect", x=px-55, y=py-45, width=110, height=100, rx=18, fill=p["blue"], stroke=p["graphite"], stroke_width=9) + tag("path", d=f"M {px-28} {py-45} Q {px} {py-95} {px+28} {py-45}", fill="none", stroke=p["graphite"], stroke_width=9)
        else:
            icon = tag("path", d=f"M {px-66} {py} L {px} {py-62} L {px+66} {py} L {px+56} {py+65} L {px-56} {py+65} Z", fill="none", stroke=p["lime"], stroke_width=13, stroke_linejoin="round") + tag("rect", x=px-15, y=py+20, width=30, height=45, fill=p["yellow"], stroke=p["graphite"], stroke_width=6)
        cards += icon
    thread = tag("path", d="M -410 160 Q 0 270 410 160", id_=f"{instance_id}--thread", data_part="thread", fill="none", stroke=p["lime"], stroke_width=11, stroke_linecap="round")
    return group(cards + thread, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="status-signals")


def relative_steps(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "relative-steps") -> str:
    p = style["palette"]
    steps = ""
    for index in range(5):
        px = -480 + index * 190
        top = 180 - index * 105
        steps += tag("path", d=f"M {px} {top} L {px+190} {top} L {px+190} 270 L {px} 270 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=11)
    marker = tag("path", d="M -20 145 L -20 -42 L 170 -42", id_=f"{instance_id}--marker", data_part="marker", fill="none", stroke=p["lime"], stroke_width=14, stroke_linecap="round", marker_end="url(#arrow)")
    return group(steps + marker, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="relative-steps")


def upward_gaze(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "upward-gaze") -> str:
    p = style["palette"]
    beam = tag("path", d="M -390 190 Q -40 -80 390 -230 L 440 -80 Q 20 45 -325 265 Z", id_=f"{instance_id}--beam", data_part="beam", fill=p["lime"], opacity=.13)
    focus_line = tag("path", d="M -340 185 Q 20 -40 380 -185", fill="none", stroke=p["lime"], stroke_width=13, stroke_linecap="round", marker_end="url(#arrow)")
    platforms = ""
    for index, (px, py) in enumerate(((30, -10), (205, -115), (380, -220), (-105, 155), (-250, 230))):
        opacity = 1 if index < 3 else .26
        platforms += tag("path", d=f"M {px-62} {py} L {px+62} {py}", fill="none", stroke=p["paper_light"], stroke_width=15, stroke_linecap="round", opacity=opacity)
        platforms += tag("circle", cx=px, cy=py-48, r=28, fill=p["yellow"] if index < 3 else p["paper_light"], stroke=p["graphite"], stroke_width=8, opacity=opacity)
        platforms += tag("path", d=f"M {px} {py-20} L {px} {py-2}", fill="none", stroke=p["graphite"], stroke_width=13, stroke_linecap="round", opacity=opacity)
    return group(beam + focus_line + platforms, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="upward-gaze")


def racing_rulers(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "racing-rulers") -> str:
    p = style["palette"]
    content = ""
    for offset, color, top, part in ((-210, p["lime"], -105, "income"), (210, p["red"], -245, "reference")):
        content += tag("path", d=f"M {offset-65} -260 Q {offset} -275 {offset+65} -260 L {offset+60} 260 Q {offset} 275 {offset-62} 258 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=12)
        for index in range(7):
            tick_y = 205 - index * 68
            content += tag("path", d=f"M {offset-42} {tick_y} L {offset+5+(index%2)*18} {tick_y}", fill="none", stroke=p["graphite"], stroke_width=8, stroke_linecap="round")
        content += tag("path", d=f"M {offset+25} 205 L {offset+25} {top}", id_=f"{instance_id}--{part}", data_part=part, fill="none", stroke=color, stroke_width=18, stroke_linecap="round", marker_end="url(#arrow)" if part == "income" else "url(#arrow-red)")
    gap = tag("path", d="M -130 -105 Q 0 -185 130 -245", fill="none", stroke=p["graphite_soft"], stroke_width=9, stroke_dasharray="18 18", opacity=.55)
    return group(content + gap, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="racing-rulers")


def peer_envelope(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "peer-envelope") -> str:
    p = style["palette"]
    envelope = tag("rect", x=-235, y=-35, width=470, height=285, rx=25, fill=p["paper_light"], stroke=p["graphite"], stroke_width=13)
    envelope += tag("path", d="M -235 -25 L 0 135 L 235 -25", fill="none", stroke=p["graphite"], stroke_width=11, stroke_linejoin="round")
    flap = tag("path", d="M -235 -30 L 0 -205 L 235 -30 Z", id_=f"{instance_id}--flap", data_part="flap", fill=p["lime"], stroke=p["graphite"], stroke_width=13, stroke_linejoin="round")
    peers = ""
    for index, (px, py) in enumerate(((-135, -250), (0, -315), (135, -235))):
        peers += tag("circle", cx=px, cy=py, r=34, fill=p["paper"], stroke=p["graphite"], stroke_width=9)
        peers += tag("path", d=f"M {px} {py+36} L {px} {py+100}", fill="none", stroke=p["graphite"], stroke_width=16, stroke_linecap="round")
    guide = tag("path", d="M -165 -195 Q 0 -390 165 -180", fill="none", stroke=p["yellow"], stroke_width=12, stroke_linecap="round")
    return group(peers + guide + flap + envelope, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="peer-envelope")


def budget_shift(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "budget-shift") -> str:
    p = style["palette"]
    basket = tag("path", d="M -485 -40 L -315 -40 L -340 145 L -460 145 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=11)
    basket += tag("path", d="M -452 -40 Q -400 -145 -348 -40", fill="none", stroke=p["graphite"], stroke_width=11)
    sofa = tag("path", d="M -80 15 Q -65 -70 0 -70 Q 65 -70 80 15 L 110 15 L 110 125 L -110 125 L -110 15 Z", fill=p["blue"], stroke=p["graphite"], stroke_width=10)
    screen = tag("rect", x=165, y=-95, width=145, height=115, rx=12, fill=p["paper_light"], stroke=p["graphite"], stroke_width=10) + tag("path", d="M 237 20 L 237 78 M 190 78 L 284 78", fill="none", stroke=p["graphite"], stroke_width=10, stroke_linecap="round")
    car = tag("path", d="M 345 65 L 390 -20 L 485 -20 L 530 65 Z", fill=p["yellow"], stroke=p["graphite"], stroke_width=10, stroke_linejoin="round") + tag("circle", cx=395, cy=72, r=25, fill=p["graphite"]) + tag("circle", cx=485, cy=72, r=25, fill=p["graphite"])
    tokens = "".join(tag("circle", cx=-250 + index * 82, cy=210 - (index % 2) * 22, r=22, fill=p["lime"] if index < 4 else p["yellow"], stroke=p["graphite"], stroke_width=7) for index in range(8))
    move = tag("path", d="M -260 235 Q 30 315 365 185", id_=f"{instance_id}--tokens", data_part="tokens", fill="none", stroke=p["lime"], stroke_width=12, stroke_dasharray="20 18", stroke_linecap="round", marker_end="url(#arrow)")
    return group(basket + sofa + screen + car + tokens + move, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="budget-shift")


def comparison_feed(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "comparison-feed") -> str:
    p = style["palette"]
    shell = tag("rect", x=-245, y=-340, width=490, height=680, rx=55, fill=p["graphite"], stroke=p["graphite"], stroke_width=12)
    screen = tag("rect", x=-215, y=-295, width=430, height=570, rx=28, fill=p["paper_light"])
    cards = ""
    for index, (py, color) in enumerate(((-220, p["yellow"]), (-35, p["lime"]), (150, p["blue"]))):
        cards += tag("rect", x=-175, y=py, width=350, height=145, rx=22, fill=p["paper"], stroke=p["graphite"], stroke_width=8)
        if index == 0:
            icon = tag("path", d=f"M -105 {py+85} L -65 {py+25} L 25 {py+25} L 70 {py+85} Z", fill=color, stroke=p["graphite"], stroke_width=8) + tag("circle", cx=-60, cy=py+92, r=18, fill=p["graphite"]) + tag("circle", cx=30, cy=py+92, r=18, fill=p["graphite"])
        elif index == 1:
            icon = tag("path", d=f"M -115 {py+65} L -55 {py+5} L 5 {py+65} L -5 {py+120} L -105 {py+120} Z", fill="none", stroke=color, stroke_width=11, stroke_linejoin="round") + tag("rect", x=20, y=py+28, width=105, height=92, fill="none", stroke=p["graphite"], stroke_width=8)
        else:
            icon = tag("circle", cx=-75, cy=py+52, r=28, fill=color, stroke=p["graphite"], stroke_width=7) + tag("path", d=f"M -145 {py+120} Q -45 {py+70} 70 {py+120} M 35 {py+110} L 125 {py+20}", fill="none", stroke=p["graphite"], stroke_width=10, stroke_linecap="round")
        cards += icon
    return group(shell + screen + cards, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="comparison-feed")


def paycheck_blocks(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "paycheck-blocks") -> str:
    p = style["palette"]
    card = tag("path", d="M -330 -220 Q 0 -245 330 -220 L 315 225 Q 0 248 -320 220 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=13)
    base = "".join(tag("rect", x=-260 + index * 105, y=35, width=82, height=120, rx=14, fill=p["lime"], stroke=p["graphite"], stroke_width=8) for index in range(4))
    plus = tag("rect", x=205, y=-135, width=92, height=150, rx=15, id_=f"{instance_id}--increase", data_part="increase", fill=p["yellow"], stroke=p["graphite"], stroke_width=9)
    arrow = tag("path", d="M 80 -95 L 175 -95", fill="none", stroke=p["lime"], stroke_width=14, stroke_linecap="round", marker_end="url(#arrow)")
    lines = tag("rect", x=-260, y=-145, width=230, height=22, rx=11, fill=p["graphite"]) + tag("rect", x=-260, y=-92, width=160, height=14, rx=7, fill=p["graphite_soft"], opacity=.42)
    return group(card + lines + base + arrow + plus, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="paycheck-blocks")


def small_upgrades(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "small-upgrades") -> str:
    p = style["palette"]
    cards = ""
    specs = ((-360, -125, "home"), (0, -230, "car"), (360, -125, "delivery"), (-225, 165, "plan"), (225, 165, "parcel"))
    for index, (px, py, kind) in enumerate(specs):
        cards += tag("rect", x=px-100, y=py-82, width=200, height=164, rx=26, fill=p["paper_light"], stroke=p["graphite"], stroke_width=10)
        if kind == "home":
            icon = tag("path", d=f"M {px-58} {py} L {px} {py-55} L {px+58} {py} L {px+48} {py+55} L {px-48} {py+55} Z", fill="none", stroke=p["lime"], stroke_width=12, stroke_linejoin="round")
        elif kind == "car":
            icon = tag("path", d=f"M {px-68} {py+25} L {px-35} {py-28} L {px+35} {py-28} L {px+68} {py+25} Z", fill=p["blue"], stroke=p["graphite"], stroke_width=9) + tag("circle", cx=px-35, cy=py+34, r=17, fill=p["graphite"]) + tag("circle", cx=px+35, cy=py+34, r=17, fill=p["graphite"])
        elif kind == "delivery":
            icon = tag("path", d=f"M {px-52} {py-30} L {px+52} {py-30} L {px+44} {py+58} L {px-45} {py+58} Z", fill=p["red"], stroke=p["graphite"], stroke_width=9) + tag("path", d=f"M {px-25} {py-30} Q {px} {py-75} {px+25} {py-30}", fill="none", stroke=p["graphite"], stroke_width=9)
        elif kind == "plan":
            icon = tag("circle", cx=px, cy=py, r=58, fill=p["yellow"], stroke=p["graphite"], stroke_width=9) + tag("path", d=f"M {px-28} {py} L {px+28} {py} M {px} {py-28} L {px} {py+28}", fill="none", stroke=p["graphite"], stroke_width=12, stroke_linecap="round")
        else:
            icon = "".join(tag("rect", x=px-62+step*45, y=py-30+step*10, width=72, height=74, rx=12, fill=p["paper"], stroke=p["graphite"], stroke_width=8) for step in range(3))
        cards += group(icon, id_=f"{instance_id}--choice-{index+1}", data_part=f"choice-{index+1}")
    thread = tag("path", d="M -430 45 Q 0 345 430 45", fill="none", stroke=p["lime"], stroke_width=11, stroke_dasharray="20 18", stroke_linecap="round")
    return group(cards + thread, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="small-upgrades")


def commitment_bar(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, payoff: bool = False, instance_id: str = "commitment-bar") -> str:
    p = style["palette"]
    total_width = 1200
    values = (350, 180, 170, 120, 130)
    colors = (p["red"], p["yellow"], p["red"], p["yellow"], p["red"])
    labels = ("350", "180", "170", "120", "130")
    border = tag("rect", x=-600, y=-105, width=total_width, height=210, rx=35, fill=p["paper_light"], stroke=p["graphite"], stroke_width=14)
    cursor = -585
    blocks = ""
    for index, (value, color, label) in enumerate(zip(values, colors, labels)):
        width = value / 1000 * 1170
        blocks += tag("rect", x=round(cursor, 2), y=-90, width=round(width, 2), height=180, rx=12 if index in (0, 4) else 4, id_=f"{instance_id}--expense-{index+1}", data_part=f"expense-{index+1}", fill=color, stroke=p["graphite"], stroke_width=6)
        if not payoff:
            blocks += text_node(cursor + width/2, 15, label, "label-light" if color == p["red"] else "label", text_anchor="middle")
        cursor += width
    remaining_width = 50 / 1000 * 1170
    remaining = tag("rect", x=round(cursor, 2), y=-90, width=round(remaining_width, 2), height=180, rx=10, id_=f"{instance_id}--remaining", data_part="remaining", fill=p["lime"], stroke=p["graphite"], stroke_width=6)
    if payoff:
        remaining += tag("ellipse", cx=cursor+remaining_width/2, cy=0, rx=remaining_width*.9, ry=145, fill=p["lime"], opacity=.16)
    return group(border + blocks + remaining, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="commitment-bar", data_total="1000", data_committed="950", data_remaining="50")


def fictional_case_file(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "fictional-case-file") -> str:
    p = style["palette"]
    paper = tag("path", d="M -390 -275 Q 0 -300 390 -275 L 375 275 Q 0 300 -380 272 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=13)
    portrait = tag("circle", cx=-245, cy=-110, r=72, fill=p["paper"], stroke=p["graphite"], stroke_width=10) + path("M -275 -108 Q -245 -155 -215 -108 M -270 -75 Q -245 -52 -220 -75", "face-line")
    fields = "".join(tag("rect", x=-120, y=-180+index*65, width=365-index*28, height=18, rx=9, fill=p["graphite_soft"], opacity=.38) for index in range(4))
    mini_bar = tag("rect", x=-285, y=115, width=560, height=75, rx=18, fill=p["paper"], stroke=p["graphite"], stroke_width=8) + "".join(tag("rect", x=-270+index*105, y=128, width=90, height=50, rx=10, fill=p["red"] if index < 4 else p["lime"], stroke=p["graphite"], stroke_width=5) for index in range(5))
    stamp = tag("rect", x=-245, y=-95, width=490, height=190, rx=26, id_=f"{instance_id}--stamp", data_part="stamp", fill="none", stroke=p["red"], stroke_width=22, transform="rotate(-12)")
    return group(paper + portrait + fields + mini_bar + stamp, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="fictional-case-file")


def pleasure_vs_bill(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "pleasure-vs-bill") -> str:
    p = style["palette"]
    gifts = ""
    for index, (px, opacity, size) in enumerate(((-390, 1.0, 1.0), (-220, .62, .82), (-75, .28, .64))):
        w = 130*size
        gifts += tag("rect", x=px-w/2, y=-w/2, width=w, height=w, rx=14, fill=p["yellow"], stroke=p["graphite"], stroke_width=9, opacity=opacity)
        gifts += tag("path", d=f"M {px} {-w/2} L {px} {w/2} M {px-w/2} 0 L {px+w/2} 0", fill="none", stroke=p["paper_light"], stroke_width=10, opacity=opacity)
    calendars = ""
    for index in range(3):
        calendars += group(calendar(170 + index*130, index*18, scale=.62, faded=False), id_=f"{instance_id}--bill-{index+1}", data_part=f"bill-{index+1}")
    divider = tag("path", d="M 20 -210 Q 5 0 20 210", fill="none", stroke=p["paper_light"], stroke_width=8, stroke_dasharray="18 18", opacity=.38)
    return group(gifts + divider + calendars, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="pleasure-vs-bill")


def walking_bills(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "walking-bills") -> str:
    p = style["palette"]
    content = ""
    for index, (px, py, size) in enumerate(((-260, 30, .78), (0, -30, 1.0), (270, 20, .82))):
        w, h = 220*size, 270*size
        card = tag("path", d=f"M {px-w/2} {py-h/2} Q {px} {py-h/2-14} {px+w/2} {py-h/2} L {px+w/2-8} {py+h/2} Q {px} {py+h/2+14} {px-w/2+8} {py+h/2} Z", fill=p["paper_light"], stroke=p["red"], stroke_width=11)
        lines = "".join(tag("path", d=f"M {px-w*.32} {py-h*.22+j*45*size} L {px+w*.3} {py-h*.22+j*45*size}", fill="none", stroke=p["graphite_soft"], stroke_width=8, stroke_linecap="round", opacity=.55) for j in range(3))
        legs = tag("path", d=f"M {px-w*.2} {py+h/2} L {px-w*.34} {py+h/2+95*size} M {px+w*.2} {py+h/2} L {px+w*.36} {py+h/2+80*size}", fill="none", stroke=p["graphite"], stroke_width=15, stroke_linecap="round")
        feet = tag("path", d=f"M {px-w*.44} {py+h/2+95*size} L {px-w*.26} {py+h/2+95*size} M {px+w*.29} {py+h/2+80*size} L {px+w*.47} {py+h/2+80*size}", fill="none", stroke=p["graphite"], stroke_width=18, stroke_linecap="round")
        content += group(card + lines + legs + feet, id_=f"{instance_id}--bill-{index+1}", data_part=f"bill-{index+1}")
    return group(content, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="walking-bills")


def gear_shape(cx: float, cy: float, radius: float, fill: str, style: dict[str, Any]) -> str:
    p = style["palette"]
    teeth = ""
    for index in range(8):
        angle = index * math.pi / 4
        x1 = cx + math.cos(angle) * (radius + 2)
        y1 = cy + math.sin(angle) * (radius + 2)
        x2 = cx + math.cos(angle) * (radius + 42)
        y2 = cy + math.sin(angle) * (radius + 42)
        teeth += tag("path", d=f"M {x1:.1f} {y1:.1f} L {x2:.1f} {y2:.1f}", fill="none", stroke=p["graphite"], stroke_width=28, stroke_linecap="round")
    wheel = tag("circle", cx=cx, cy=cy, r=radius, fill=fill, stroke=p["graphite"], stroke_width=13)
    hub = tag("circle", cx=cx, cy=cy, r=34, fill=p["paper_light"], stroke=p["graphite"], stroke_width=10)
    return teeth + wheel + hub


def three_gears(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "three-gears") -> str:
    p = style["palette"]
    top = group(gear_shape(0, -175, 150, p["lime"], style), id_=f"{instance_id}--adaptation", data_part="adaptation")
    left = group(gear_shape(-235, 135, 150, p["yellow"], style), id_=f"{instance_id}--comparison", data_part="comparison")
    right = group(gear_shape(235, 135, 150, p["red"], style), id_=f"{instance_id}--commitments", data_part="commitments")
    ruler = tag("path", d="M -55 -240 L 55 -240 L 55 -110 L -55 -110 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=8) + "".join(tag("path", d=f"M -40 {-215+i*28} L {5+(i%2)*20} {-215+i*28}", fill="none", stroke=p["graphite"], stroke_width=6) for i in range(4))
    people = tag("circle", cx=-275, cy=90, r=25, fill=p["paper_light"], stroke=p["graphite"], stroke_width=7) + tag("circle", cx=-195, cy=90, r=25, fill=p["paper_light"], stroke=p["graphite"], stroke_width=7) + tag("path", d="M -275 118 L -275 170 M -195 118 L -195 170", fill="none", stroke=p["graphite"], stroke_width=11, stroke_linecap="round")
    bills = tag("rect", x=170, y=72, width=130, height=115, rx=15, fill=p["paper_light"], stroke=p["graphite"], stroke_width=8) + tag("path", d="M 195 110 L 275 110 M 195 145 L 255 145", fill="none", stroke=p["red"], stroke_width=7, stroke_linecap="round")
    return group(top + left + right + ruler + people + bills, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="three-gears")


def synthesis_flow(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "synthesis-flow") -> str:
    p = style["palette"]
    panels = ""
    for index, px in enumerate((-390, 0, 390)):
        fill = p["paper_light"] if index != 1 else p["graphite"]
        panels += tag("rect", x=px-155, y=-210, width=310, height=420, rx=28, fill=fill, stroke=p["graphite"], stroke_width=12)
    celebration = tag("circle", cx=-390, cy=-75, r=55, fill=p["paper"], stroke=p["graphite"], stroke_width=9) + tag("path", d="M -450 50 L -390 -10 L -330 50", fill="none", stroke=p["lime"], stroke_width=16, stroke_linecap="round")
    normal = tag("path", d="M -105 75 L 105 75", fill="none", stroke=p["lime"], stroke_width=20, stroke_linecap="round") + tag("circle", cx=0, cy=-45, r=55, fill=p["paper"], stroke=p["paper_light"], stroke_width=9)
    squeeze = tag("path", d="M 275 -100 L 340 -10 L 275 80 M 505 -100 L 440 -10 L 505 80", fill="none", stroke=p["red"], stroke_width=19, stroke_linecap="round", stroke_linejoin="round") + tag("circle", cx=390, cy=-10, r=52, fill=p["paper"], stroke=p["graphite"], stroke_width=9)
    arrows = tag("path", d="M -220 0 L -165 0 M 165 0 L 220 0", fill="none", stroke=p["lime"], stroke_width=13, stroke_linecap="round", marker_end="url(#arrow)")
    thread = tag("path", d="M -500 170 Q 0 255 500 170", id_=f"{instance_id}--thread", data_part="thread", fill="none", stroke=p["lime"], stroke_width=10, stroke_dasharray="20 18")
    return group(panels + celebration + normal + squeeze + arrows + thread, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="synthesis-flow")


def enough_triangle(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "enough-triangle") -> str:
    p = style["palette"]
    triangle = tag("path", d="M 0 -300 L 390 250 L -390 250 Z", id_=f"{instance_id}--lines", data_part="lines", fill="none", stroke=p["paper_light"], stroke_width=15, stroke_linejoin="round")
    income = tag("path", d="M -55 -235 L 20 -300 L 95 -225", fill="none", stroke=p["lime"], stroke_width=18, stroke_linecap="round", stroke_linejoin="round")
    bills = tag("rect", x=-370, y=105, width=120, height=135, rx=15, fill=p["paper_light"], stroke=p["red"], stroke_width=9) + tag("path", d="M -345 145 L -275 145 M -345 185 L -290 185", fill="none", stroke=p["red"], stroke_width=7)
    ruler = tag("rect", x=250, y=65, width=100, height=175, rx=12, fill=p["paper_light"], stroke=p["graphite"], stroke_width=9) + "".join(tag("path", d=f"M 270 {95+i*34} L {315+(i%2)*18} {95+i*34}", fill="none", stroke=p["graphite"], stroke_width=7) for i in range(4))
    center = tag("circle", cx=0, cy=75, r=120, fill=p["lime"], opacity=.18) + tag("circle", cx=0, cy=75, r=72, fill=p["paper"], stroke=p["lime"], stroke_width=12)
    return group(triangle + income + bills + ruler + center, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="enough-triangle")


def decision_interval(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "decision-interval") -> str:
    p = style["palette"]
    axis = tag("path", d="M -500 80 L 500 80", fill="none", stroke=p["graphite"], stroke_width=14, stroke_linecap="round")
    ticks = "".join(tag("circle", cx=-400+index*200, cy=80, r=20, fill=p["paper_light"], stroke=p["graphite"], stroke_width=8) for index in range(5))
    interval = tag("path", d="M -330 80 L 330 80", id_=f"{instance_id}--interval", data_part="interval", fill="none", stroke=p["lime"], stroke_width=20, stroke_linecap="round")
    phone_icon = generic_phone(-500, -120, scale=.48, glowing=True, instance_id=f"{instance_id}--phone")
    lock = tag("rect", x=420, y=-155, width=160, height=175, rx=28, fill=p["red"], stroke=p["graphite"], stroke_width=11) + tag("path", d="M 455 -155 Q 500 -255 545 -155", fill="none", stroke=p["graphite"], stroke_width=14) + tag("circle", cx=500, cy=-70, r=18, fill=p["paper_light"])
    bracket = tag("path", d="M -320 145 L -320 195 L 320 195 L 320 145", fill="none", stroke=p["lime"], stroke_width=12, stroke_linecap="round", stroke_linejoin="round")
    return group(axis + ticks + interval + phone_icon + lock + bracket, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="decision-interval")


def conscious_balance(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "conscious-balance") -> str:
    p = style["palette"]
    beam = tag("path", d="M -430 -70 Q 0 -25 430 -70", id_=f"{instance_id}--beam", data_part="beam", fill="none", stroke=p["graphite"], stroke_width=18, stroke_linecap="round")
    fulcrum = tag("path", d="M -75 205 L 0 -45 L 75 205 Z", fill=p["yellow"], stroke=p["graphite"], stroke_width=12, stroke_linejoin="round") + tag("path", d="M -125 205 L 125 205", fill="none", stroke=p["graphite"], stroke_width=18, stroke_linecap="round")
    strings = tag("path", d="M -430 -70 L -500 110 M -430 -70 L -300 110 M 430 -70 L 300 110 M 430 -70 L 520 110", fill="none", stroke=p["graphite"], stroke_width=9)
    plates = tag("path", d="M -555 110 Q -400 175 -245 110", fill=p["paper_light"], stroke=p["lime"], stroke_width=14, stroke_linecap="round") + tag("path", d="M 245 110 Q 410 175 575 110", fill=p["paper_light"], stroke=p["red"], stroke_width=14, stroke_linecap="round")
    chosen = tag("path", d="M -460 55 Q -400 5 -340 55 L -350 120 L -450 120 Z", fill=p["lime"], stroke=p["graphite"], stroke_width=9) + tag("path", d="M -438 58 L -400 92 L -360 48", fill="none", stroke=p["paper_light"], stroke_width=12, stroke_linecap="round", stroke_linejoin="round")
    automatic = "".join(tag("rect", x=315+i*75, y=35-(i%2)*22, width=58, height=70, rx=12, fill=p["paper_light"], stroke=p["graphite"], stroke_width=8) for i in range(3))
    token = tag("circle", cx=-160, cy=-185, r=34, id_=f"{instance_id}--token", data_part="token", fill=p["lime"], stroke=p["graphite"], stroke_width=9)
    route = tag("path", d="M -155 -145 Q -250 -70 -345 35", fill="none", stroke=p["lime"], stroke_width=11, stroke_dasharray="17 15", marker_end="url(#arrow)")
    return group(beam + fulcrum + strings + plates + chosen + automatic + route + token, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="conscious-balance")


def destination_envelopes(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "destination-envelopes") -> str:
    p = style["palette"]
    content = ""
    centers = (-360, 0, 360)
    for index, cx in enumerate(centers):
        envelope = tag("path", d=f"M {cx-155} -95 Q {cx} -115 {cx+155} -95 L {cx+145} 135 Q {cx} 160 {cx-145} 135 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=11)
        flap = tag("path", d=f"M {cx-145} -85 L {cx} 28 L {cx+145} -85", fill="none", stroke=p["graphite"], stroke_width=10, stroke_linejoin="round")
        if index == 0:
            icon = tag("path", d=f"M {cx-48} 55 Q {cx} 5 {cx+48} 55 Q {cx} 112 {cx-48} 55 Z", fill=p["lime"], stroke=p["graphite"], stroke_width=7)
        elif index == 1:
            icon = tag("circle", cx=cx, cy=70, r=45, fill=p["paper"], stroke=p["lime"], stroke_width=12) + tag("circle", cx=cx, cy=70, r=13, fill=p["lime"])
        else:
            icon = tag("path", d=f"M {cx-62} 96 Q {cx} 18 {cx+62} 96", fill="none", stroke=p["lime"], stroke_width=12, stroke_linecap="round") + tag("circle", cx=cx, cy=55, r=22, fill=p["yellow"], stroke=p["graphite"], stroke_width=6)
        content += group(envelope + flap + icon, id_=f"{instance_id}--envelope-{index+1}", data_part=f"envelope-{index+1}")
    tokens = "".join(tag("circle", cx=-480+i*120, cy=-230-(i%2)*24, r=25, fill=p["lime"], stroke=p["graphite"], stroke_width=7) for i in range(9))
    paths = "".join(tag("path", d=f"M {-480+i*240} -195 Q {-360+i*180} -145 {-360+i*360} -92", fill="none", stroke=p["lime"], stroke_width=8, stroke_dasharray="14 14", opacity=.72) for i in range(3))
    return group(tokens + paths + content, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="destination-envelopes")


def freedom_shadow(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "freedom-shadow") -> str:
    p = style["palette"]
    paycheck = tag("path", d="M -520 -250 Q 0 -285 520 -250 L 500 225 Q 0 260 -505 225 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=14)
    header = tag("rect", x=-450, y=-190, width=900, height=60, rx=20, fill=p["lime"], opacity=.72)
    lines = "".join(tag("rect", x=-430, y=-75+i*78, width=330+i*65, height=23, rx=11, fill=p["graphite_soft"], opacity=.35) for i in range(3))
    shadow = tag("path", d="M -500 235 Q 0 350 500 235 L 290 390 Q 0 455 -290 390 Z", id_=f"{instance_id}--shadow", data_part="shadow", fill=p["graphite"], opacity=.22)
    bills = ""
    for index, bx in enumerate((-355, -115, 125, 365)):
        bills += group(tag("rect", x=bx-88, y=240, width=176, height=165, rx=18, fill=p["paper_light"], stroke=p["red"], stroke_width=10) + tag("path", d=f"M {bx-52} 290 L {bx+52} 290 M {bx-52} 340 L {bx+25} 340", fill="none", stroke=p["red"], stroke_width=8, stroke_linecap="round"), id_=f"{instance_id}--bill-{index+1}", data_part=f"bill-{index+1}")
    opening = tag("path", d="M -45 410 Q 0 360 45 410 L 30 480 L -30 480 Z", fill=p["lime"], stroke=p["graphite"], stroke_width=8)
    return group(paycheck + header + lines + shadow + bills + opening, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="freedom-shadow")


def callback_threads(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "callback-threads") -> str:
    p = style["palette"]
    threads = tag("path", d="M 0 160 Q -150 55 -365 -40 M 0 160 Q 0 5 0 -170 M 0 160 Q 155 55 365 -40", id_=f"{instance_id}--threads", data_part="threads", fill="none", stroke=p["lime"], stroke_width=12, stroke_dasharray="18 16", stroke_linecap="round")
    ruler = tag("rect", x=-430, y=-110, width=130, height=150, rx=12, fill=p["paper_light"], stroke=p["graphite"], stroke_width=9) + "".join(tag("path", d=f"M -405 {-78+i*34} L {-340+(i%2)*18} {-78+i*34}", fill="none", stroke=p["graphite"], stroke_width=7) for i in range(4))
    peers = tag("circle", cx=-45, cy=-205, r=28, fill=p["paper_light"], stroke=p["graphite"], stroke_width=8) + tag("circle", cx=45, cy=-205, r=28, fill=p["paper_light"], stroke=p["graphite"], stroke_width=8) + tag("path", d="M -45 -174 L -45 -105 M 45 -174 L 45 -105", fill="none", stroke=p["graphite"], stroke_width=10)
    bill = tag("rect", x=300, y=-115, width=135, height=165, rx=14, fill=p["paper_light"], stroke=p["red"], stroke_width=9) + tag("path", d="M 330 -70 L 405 -70 M 330 -25 L 390 -25", fill="none", stroke=p["red"], stroke_width=7)
    return group(threads + ruler + peers + bill, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="callback-threads")


def locking_calendar(x: float, y: float, style: dict[str, Any], *, scale: float = 1.0, instance_id: str = "locking-calendar") -> str:
    p = style["palette"]
    axis = tag("path", d="M -520 120 Q 0 80 520 120", fill="none", stroke=p["graphite"], stroke_width=14, stroke_linecap="round")
    cards = ""
    for index, cx in enumerate((-360, 0, 360)):
        card = tag("rect", x=cx-125, y=-195, width=250, height=260, rx=25, fill=p["paper_light"], stroke=p["graphite"], stroke_width=11)
        rings = tag("path", d=f"M {cx-70} -220 L {cx-70} -160 M {cx+70} -220 L {cx+70} -160", fill="none", stroke=p["graphite"], stroke_width=15, stroke_linecap="round")
        upgrade = tag("rect", x=cx-52, y=-95, width=104, height=72, rx=15, fill=(p["yellow"] if index == 0 else p["paper"]), stroke=p["graphite"], stroke_width=8)
        lock = tag("rect", x=cx-58, y=5, width=116, height=105, rx=20, fill=p["red"], stroke=p["graphite"], stroke_width=9) + tag("path", d=f"M {cx-34} 5 Q {cx} -70 {cx+34} 5", fill="none", stroke=p["graphite"], stroke_width=12) + tag("circle", cx=cx, cy=58, r=13, fill=p["paper_light"])
        cards += group(card + rings + upgrade + lock, id_=f"{instance_id}--lock-{index+1}", data_part=f"lock-{index+1}")
    after = tag("path", d="M -510 185 Q 0 245 510 185", fill="none", stroke=p["red"], stroke_width=10, stroke_dasharray="18 17", opacity=.68)
    return group(axis + cards + after, id_=instance_id, class_="rough", transform=f"translate({x} {y}) scale({scale})", data_object="locking-calendar")


def common_defs(style: dict[str, Any]) -> str:
    p = style["palette"]
    line_cfg = style["line"]
    font = style["typography"]["family"]
    css = f"""
    .ink,.limb,.shoe,.neck,.face-line,.growth,.balance-low,.calendar-line,.phone-detail {{ fill:none; stroke:{p['graphite']}; stroke-width:{line_cfg['primary_width']}; stroke-linecap:round; stroke-linejoin:round; }}
    .ghost {{ opacity:.16; stroke-width:{line_cfg['detail_width']}; }}
    .limb {{ stroke-width:18; }} .shoe {{ stroke-width:24; }} .neck {{ stroke-width:18; }}
    .face-line {{ stroke-width:8; }} .eye {{ fill:{p['graphite']}; }} .mouth-open {{ fill:{p['graphite']}; }}
    .head {{ fill:{p['paper']}; stroke:{p['graphite']}; stroke-width:13; }} .hair {{ fill:{p['graphite']}; stroke:{p['graphite']}; stroke-width:8; stroke-linejoin:round; }}
    .outfit {{ fill:{p['graphite']}; stroke:{p['graphite']}; stroke-width:10; }} .pocket {{ fill:{p['lime']}; }}
    .phone-shell {{ fill:{p['graphite']}; stroke:{p['paper_light']}; stroke-width:8; }}
    .phone-screen {{ fill:#26302C; stroke:{p['graphite_soft']}; stroke-width:4; }}
    .phone-detail {{ stroke:{p['paper_light']}; stroke-width:6; }} .alert-card {{ fill:{p['paper_light']}; stroke:{p['lime']}; stroke-width:9; }}
    .growth {{ stroke:{p['lime']}; stroke-width:15; }} .balance-low {{ stroke:{p['red']}; stroke-width:13; }}
    .paper-card {{ fill:{p['paper_light']}; stroke:{p['graphite']}; stroke-width:11; }}
    .calendar-line {{ stroke-width:10; }} .calendar-dot {{ fill:{p['yellow']}; stroke:{p['graphite']}; stroke-width:5; }}
    .bill {{ fill:{p['paper_light']}; stroke:{p['red']}; stroke-width:9; }} .bill-dot {{ fill:{p['red']}; }}
    .headline {{ font-family:{font}; font-size:{style['typography']['headline_size']}px; font-weight:900; letter-spacing:1px; fill:{p['graphite']}; }}
    .headline-light {{ font-family:{font}; font-size:{style['typography']['headline_size']}px; font-weight:900; letter-spacing:1px; fill:{p['paper_light']}; }}
    .label {{ font-family:{font}; font-size:{style['typography']['label_size']}px; font-weight:800; fill:{p['graphite']}; }}
    .label-light {{ font-family:{font}; font-size:{style['typography']['label_size']}px; font-weight:800; fill:{p['paper_light']}; }}
    .rough {{ filter:url(#roughen); }}
    """
    defs = tag("style", css)
    defs += tag(
        "filter",
        tag("feTurbulence", type="fractalNoise", baseFrequency="0.009", numOctaves="1", seed=line_cfg["filter_seed"], result="noise")
        + tag("feDisplacementMap", in_="SourceGraphic", in2="noise", scale=line_cfg["roughness"], xChannelSelector="R", yChannelSelector="G"),
        id="roughen",
        x="-5%",
        y="-5%",
        width="110%",
        height="110%",
    )
    dots = tag("circle", cx=4, cy=4, r=1.1, fill=p["graphite"], opacity=.10)
    defs += tag("pattern", dots, id="paperDots", width=22, height=22, patternUnits="userSpaceOnUse")
    defs += tag("marker", path("M 0 0 L 12 6 L 0 12 Z", css="arrow-fill"), id="arrow", viewBox="0 0 12 12", refX=10, refY=6, markerWidth=10, markerHeight=10, orient="auto-start-reverse")
    defs += tag("marker", tag("path", d="M 0 0 L 12 6 L 0 12 Z", fill=p["yellow"]), id="arrow-yellow", viewBox="0 0 12 12", refX=10, refY=6, markerWidth=10, markerHeight=10, orient="auto-start-reverse")
    defs += tag("marker", tag("path", d="M 0 0 L 12 6 L 0 12 Z", fill=p["graphite"]), id="arrow-dark", viewBox="0 0 12 12", refX=10, refY=6, markerWidth=10, markerHeight=10, orient="auto-start-reverse")
    defs += tag("marker", tag("path", d="M 0 0 L 12 6 L 0 12 Z", fill=p["red"]), id="arrow-red", viewBox="0 0 12 12", refX=10, refY=6, markerWidth=10, markerHeight=10, orient="auto-start-reverse")
    defs += tag("style", f".arrow-fill{{fill:{p['lime']};stroke:none}}")
    return tag("defs", defs)


def background(style: dict[str, Any], kind: str = "paper") -> str:
    p = style["palette"]
    fill = p["graphite"] if kind == "graphite" else p["paper"]
    base = tag("rect", x=0, y=0, width=1920, height=1080, fill=fill)
    if kind == "paper":
        base += tag("rect", x=0, y=0, width=1920, height=1080, fill="url(#paperDots)")
    else:
        base += path("M 0 910 Q 450 875 930 914 T 1920 890 L 1920 1080 L 0 1080 Z", css="", fill=p["graphite_soft"], opacity=.42)
    return base


def scene_001(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    glow = "".join(tag("circle", cx=1430, cy=555, r=r, fill="none", stroke=p["lime"], stroke_width=8, opacity=o) for r, o in ((300, .10), (250, .16), (205, .24)))
    headline = text_node(110, 155, row["text_on_screen"], "headline-light")
    underline = path("M 112 185 Q 420 204 760 180", css="", fill="none", stroke=p["lime"], stroke_width=14, stroke_linecap="round")
    actor = character(530, 850, scale=1.55, expression="surprised", pose="phone", head_tilt=-6)
    device = phone(1430, 570, scale=1.33, alert=True)
    sparks = "".join(line(x, y, x + dx, y + dy, "growth") for x, y, dx, dy in ((1190,260,-40,-54),(1570,260,44,-52),(1682,470,72,-5),(1196,810,-58,38)))
    return background(style, "graphite") + glow + headline + underline + actor + device + sparks


def scene_002(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 150, row["text_on_screen"])
    sheets = calendar(325, 365, scale=.84, faded=True) + calendar(585, 415, scale=.98, faded=True) + calendar(885, 470, scale=1.15)
    trail = path("M 175 820 Q 600 730 1060 805 T 1760 750", css="", fill="none", stroke=p["lime"], stroke_width=18, stroke_linecap="round", stroke_dasharray="22 24")
    actor = character(1330, 880, scale=1.25, expression="relieved", pose="celebrate", head_tilt=4)
    gauge = tag("path", d="M 1510 760 Q 1670 720 1800 756", fill="none", stroke=p["graphite"], stroke_width=12, stroke_linecap="round")
    gauge += tag("path", d="M 1510 760 Q 1608 738 1698 744", fill="none", stroke=p["lime"], stroke_width=22, stroke_linecap="round")
    gauge += tag("circle", cx=1698, cy=744, r=20, fill=p["lime"], stroke=p["graphite"], stroke_width=7)
    return background(style) + headline + sheets + trail + actor + group(gauge, class_="rough")


def scene_003(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 150, row["text_on_screen"])
    faded_raise = group(
        tag("circle", cx=0, cy=0, r=145, fill=p["lime"], opacity=.12)
        + path("M -80 50 L -18 -14 L 26 22 L 91 -72", css="", fill="none", stroke=p["lime_dark"], stroke_width=25, stroke_linecap="round", stroke_linejoin="round"),
        transform="translate(330 440)",
        opacity=.48,
        class_="rough",
    )
    actor = character(920, 900, scale=1.34, expression="worried", pose="tension", head_tilt=8)
    device = phone(1170, 590, scale=.68, alert=False)
    purchase = group(
        tag("path", d="M -145 -30 Q 0 -52 145 -28 L 125 100 Q 0 120 -126 98 Z", class_="paper-card")
        + tag("circle", cx=-72, cy=120, r=20, fill=p["graphite"])
        + tag("circle", cx=74, cy=120, r=20, fill=p["graphite"])
        + tag("circle", cx=0, cy=18, r=36, fill=p["yellow"], stroke=p["graphite"], stroke_width=8),
        transform="translate(1530 760)",
        class_="rough",
    )
    timeline = path("M 188 930 Q 430 965 635 925", css="", fill="none", stroke=p["graphite_soft"], stroke_width=12, stroke_linecap="round")
    timeline += tag("circle", cx=195, cy=930, r=15, fill=p["lime"])
    timeline += tag("circle", cx=630, cy=926, r=15, fill=p["red"])
    timeline += text_node(190, 1000, "AUMENTO", "label") + text_node(500, 1000, "AGORA", "label")
    return background(style) + headline + faded_raise + actor + device + purchase + group(timeline, class_="rough")


def mini_house(x: float, y: float) -> str:
    return group(path("M -95 20 L 0 -72 L 95 20 L 78 20 L 78 105 L -78 105 L -78 20 Z", "ink") + tag("rect", x=-23, y=35, width=46, height=70, class_="alert-card"), transform=f"translate({x} {y}) scale(.72)")


def scene_004(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    frames = ""
    centers = (375, 960, 1545)
    colors = (p["blue"], p["yellow"], p["lime"])
    for index, (cx, color) in enumerate(zip(centers, colors)):
        frame_path = f"M {cx-245} 260 Q {cx} {230 + index*9} {cx+245} 260 L {cx+230} 900 Q {cx} {925-index*8} {cx-235} 900 Z"
        frames += tag("path", d=frame_path, fill=p["paper_light"], stroke=color, stroke_width=13, stroke_linecap="round", stroke_linejoin="round", class_="rough")
    first = mini_house(375, 440) + character(375, 825, scale=.75, expression="thinking", pose="neutral")
    friends = character(865, 800, scale=.63, expression="relieved", pose="celebrate") + character(1055, 800, scale=.63, expression="relieved", pose="celebrate", flip=True, variant="ana")
    invite = path("M 900 420 Q 960 365 1020 420 Q 960 492 900 420 Z", css="", fill=p["yellow"], stroke=p["graphite"], stroke_width=9)
    third = character(1480, 815, scale=.72, expression="neutral", pose="phone")
    shopping = group(tag("path", d="M -78 -65 L 78 -65 L 60 75 Q 0 92 -60 75 Z", class_="paper-card") + path("M -45 -67 Q 0 -130 45 -67", "ink"), transform="translate(1665 590) scale(.78)")
    captions = text_node(225, 970, "MORAR MELHOR", "label") + text_node(845, 970, "ACEITAR O CONVITE", "label") + text_node(1400, 970, "COMPRA PEQUENA", "label")
    return background(style) + headline + frames + first + friends + invite + third + shopping + captions


def ruler_icon(x: float, y: float, style: dict[str, Any]) -> str:
    p = style["palette"]
    marks = "".join(line(-95 + i * 38, 32, -95 + i * 38, 32 - (40 if i % 2 == 0 else 24), "face-line") for i in range(6))
    body = tag("path", d="M -120 -45 Q 0 -58 120 -42 L 112 55 Q 0 68 -115 52 Z", fill=p["yellow"], stroke=p["graphite"], stroke_width=10)
    return group(body + marks, class_="rough", transform=f"translate({x} {y})")


def peers_icon(x: float, y: float, style: dict[str, Any]) -> str:
    p = style["palette"]
    steps = path("M -165 92 L -55 92 L -55 32 L 55 32 L 55 -28 L 165 -28", "ink")
    people = ""
    for px, py in ((-112, 20), (0, -42), (112, -102)):
        people += tag("circle", cx=px, cy=py, r=25, fill=p["paper"], stroke=p["graphite"], stroke_width=8)
        people += line(px, py + 26, px, py + 85, "limb")
    return group(steps + people, class_="rough", transform=f"translate({x} {y})")


def scene_005(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    actor = character(960, 875, scale=1.34, expression="thinking", pose="pulled", head_tilt=-5)
    threads = ""
    threads += tag("path", d="M 815 620 Q 610 460 410 390", fill="none", stroke=p["lime"], stroke_width=13, stroke_linecap="round", marker_end="url(#arrow)")
    threads += tag("path", d="M 1100 682 Q 1320 470 1530 378", fill="none", stroke=p["lime"], stroke_width=13, stroke_linecap="round", marker_end="url(#arrow)")
    threads += tag("path", d="M 1072 790 Q 1360 850 1585 850", fill="none", stroke=p["red"], stroke_width=13, stroke_linecap="round", marker_end="url(#arrow)")
    icons = ruler_icon(350, 385, style) + peers_icon(1570, 390, style) + bill_stack(1590, 820, scale=.85)
    labels = text_node(205, 610, "O NOVO NORMAL", "label") + text_node(1375, 620, "COMPARAÇÃO", "label") + text_node(1420, 1010, "CONTAS FIXAS", "label")
    halo = tag("ellipse", cx=960, cy=610, rx=260, ry=320, fill=p["lime"], opacity=.08)
    return background(style) + headline + halo + threads + icons + actor + labels


def scene_006(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    console = brain_console(660, 575, style, scale=1.18, instance_id="brain-console-s006")
    ruler = normality_ruler(1040, 560, style, scale=.92, level=.78, instance_id="normality-ruler-s006")
    actor = character(1510, 900, scale=1.25, expression="thinking", pose="neutral", head_tilt=-7, instance_id="worker-s006")
    cable = tag("path", d="M 970 765 Q 1180 850 1330 750", fill="none", stroke=p["lime"], stroke_width=13, stroke_linecap="round", stroke_dasharray="20 18")
    label = text_node(380, 935, "O CÉREBRO RECALIBRA", "label")
    upward = tag("path", d="M 1090 800 L 1090 660 M 1090 660 L 1060 700 M 1090 660 L 1120 700", fill="none", stroke=p["lime"], stroke_width=14, stroke_linecap="round", stroke_linejoin="round")
    return background(style) + headline + console + ruler + cable + upward + actor + label


def scene_007(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    focus_panel = tag("path", d="M 215 250 Q 690 215 1125 250 L 1105 955 Q 665 985 230 945 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=7, opacity=.72)
    halo = tag("ellipse", cx=760, cy=595, rx=330, ry=390, fill=p["lime"], opacity=.07)
    ruler = normality_ruler(760, 600, style, scale=1.38, level=.82, instance_id="normality-ruler-s007")
    actor = character(1500, 950, scale=1.25, expression="realization", pose="pointing", head_tilt=-4, instance_id="worker-s007")

    old_y = 744
    new_y = 426
    old_reference = tag("path", d=f"M 315 {old_y} L 650 {old_y}", fill="none", stroke=p["graphite_soft"], stroke_width=10, stroke_dasharray="18 18", stroke_linecap="round", opacity=.55)
    old_reference += tag("circle", cx=650, cy=old_y, r=15, fill=p["paper_light"], stroke=p["graphite_soft"], stroke_width=8)
    new_reference = tag("path", d=f"M 920 {new_y} L 1240 {new_y}", fill="none", stroke=p["lime"], stroke_width=15, stroke_linecap="round")
    new_reference += tag("circle", cx=920, cy=new_y, r=18, fill=p["paper_light"], stroke=p["lime"], stroke_width=10)

    before_pill = group(
        tag("rect", x=0, y=0, width=170, height=62, rx=31, fill=p["graphite_soft"], opacity=.16)
        + text_node(85, 43, "ANTES", "label", text_anchor="middle"),
        transform="translate(285 785)",
    )
    now_pill = group(
        tag("rect", x=0, y=0, width=174, height=62, rx=31, fill=p["lime"])
        + text_node(87, 43, "AGORA", "label", text_anchor="middle"),
        transform="translate(1050 338)",
    )
    return background(style) + headline + focus_panel + halo + old_reference + new_reference + ruler + before_pill + now_pill + actor


def phone_day_scene(row: dict[str, str], style: dict[str, Any], *, fresh: bool) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    expression = "fascinated" if fresh else "neutral"
    actor = character(650, 910, scale=1.42, expression=expression, pose="phone", head_tilt=-4 if fresh else 0, instance_id=f"worker-{row['scene_id'].lower()}")
    device = generic_phone(1270, 575, scale=1.27, glowing=fresh, instance_id=f"phone-{row['scene_id'].lower()}")
    table = tag("path", d="M 1030 870 Q 1320 840 1585 875", fill="none", stroke=p["graphite"], stroke_width=18, stroke_linecap="round")
    if fresh:
        accent = tag("path", d="M 1050 245 Q 1270 185 1490 245", fill="none", stroke=p["yellow"], stroke_width=18, stroke_linecap="round")
        accent += text_node(1120, 190, "NOVO!", "label")
    else:
        accent = tag("path", d="M 1090 265 Q 1270 300 1450 265", fill="none", stroke=p["graphite_soft"], stroke_width=10, stroke_linecap="round", opacity=.38)
        accent += text_node(1080, 205, "VIROU ROTINA", "label")
    return background(style) + headline + accent + actor + device + table


def scene_008(row: dict[str, str], style: dict[str, Any]) -> str:
    return phone_day_scene(row, style, fresh=True)


def scene_009(row: dict[str, str], style: dict[str, Any]) -> str:
    return phone_day_scene(row, style, fresh=False)


def scene_010(row: dict[str, str], style: dict[str, Any]) -> str:
    headline = text_node(116, 142, row["text_on_screen"])
    curve = emotion_curve(960, 515, style, scale=1.72, instance_id="emotion-curve-s010")
    moments = calendar(510, 745, scale=.55) + calendar(950, 745, scale=.55) + calendar(1390, 745, scale=.55)
    actors = (
        character(510, 1035, scale=.36, expression="fascinated", pose="celebrate", instance_id="worker-s010-wave-1")
        + character(950, 1035, scale=.36, expression="relieved", pose="neutral", instance_id="worker-s010-wave-2")
        + character(1390, 1035, scale=.36, expression="neutral", pose="neutral", instance_id="worker-s010-wave-3")
    )
    labels = text_node(405, 860, "ONDA 1", "label") + text_node(845, 860, "ONDA 2", "label") + text_node(1285, 860, "ONDA 3", "label")
    return background(style) + headline + curve + moments + actors + labels


def scene_011(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    routes = opposing_routes(960, 555, style, scale=1.24, instance_id="opposing-routes-s011")
    actor_halo = tag("ellipse", cx=960, cy=745, rx=160, ry=215, fill=p["paper_light"], opacity=.08)
    actor = character(960, 1010, scale=.74, expression="realization", pose="neutral", instance_id="worker-s011")
    labels = text_node(260, 940, "PERDE FORÇA", "label-light") + text_node(1370, 940, "SOBE", "label-light")
    return background(style, "graphite") + headline + routes + actor_halo + actor + labels


def scene_012(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    platform = podium_floor(960, 650, style, scale=1.55, instance_id="podium-floor-s012")
    before = character(415, 548, scale=.58, expression="fascinated", pose="celebrate", instance_id="worker-s012-before")
    after = character(1400, 790, scale=.82, expression="neutral", pose="neutral", instance_id="worker-s012-after")
    starting = text_node(295, 885, "CONQUISTA", "label")
    normal = group(tag("rect", x=0, y=0, width=325, height=66, rx=33, fill=p["paper_light"], stroke=p["graphite"], stroke_width=7) + text_node(162, 46, "PONTO DE PARTIDA", "label", text_anchor="middle"), transform="translate(1220 900)")
    return background(style) + headline + platform + before + after + starting + normal


def scene_013(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    split = tag("path", d="M 960 220 Q 945 580 960 1010", fill="none", stroke=p["graphite_soft"], stroke_width=8, stroke_dasharray="18 18", opacity=.4)
    left_halo = tag("ellipse", cx=490, cy=625, rx=330, ry=320, fill=p["yellow"], opacity=.1)
    table_left = tag("path", d="M 170 845 Q 505 815 825 845", fill="none", stroke=p["graphite"], stroke_width=19, stroke_linecap="round")
    table_right = tag("path", d="M 1090 845 Q 1430 815 1750 845", fill="none", stroke=p["graphite"], stroke_width=19, stroke_linecap="round")
    before = character(340, 930, scale=.72, expression="fascinated", pose="neutral", instance_id="worker-s013-before")
    after = character(1260, 930, scale=.72, expression="neutral", pose="neutral", instance_id="worker-s013-after")
    bag_before = delivery_bag(670, 730, style, scale=.75, instance_id="delivery-s013-before")
    bags_after = delivery_bag(1510, 740, style, scale=.74, instance_id="delivery-s013-now") + delivery_bag(1650, 785, style, scale=.54, instance_id="delivery-s013-old-1", faded=True) + delivery_bag(1390, 795, style, scale=.5, instance_id="delivery-s013-old-2", faded=True)
    connector = tag("path", d="M 720 500 Q 960 390 1200 500", fill="none", stroke=p["lime"], stroke_width=12, stroke_linecap="round", marker_end="url(#arrow)")
    labels = text_node(305, 315, "ERA ESPECIAL", "label") + text_node(1220, 315, "VIROU TERÇA", "label")
    return background(style) + headline + split + left_halo + connector + labels + table_left + table_right + before + after + bag_before + bags_after


def scene_014(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    race = expectation_race(835, 585, style, scale=1.12, instance_id="expectation-race-s014")
    meeting_halo = tag("circle", cx=1350, cy=390, r=105, fill=p["yellow"], opacity=.13)
    actor = character(1580, 910, scale=1.0, expression="neutral", pose="pointing", flip=True, head_tilt=3, instance_id="worker-s014")
    payoff = group(tag("rect", x=0, y=0, width=380, height=72, rx=36, fill=p["graphite"]) + text_node(190, 50, "MESMO PATAMAR", "label-light", text_anchor="middle"), transform="translate(1160 895)")
    return background(style) + headline + meeting_halo + race + actor + payoff


def need_icon(kind: str, x: float, y: float, style: dict[str, Any]) -> str:
    p = style["palette"]
    if kind == "home":
        content = tag("path", d="M -62 2 L 0 -55 L 62 2 L 52 68 L -52 68 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=9, stroke_linejoin="round") + tag("rect", x=-14, y=25, width=28, height=43, fill=p["lime"], stroke=p["graphite"], stroke_width=6)
    elif kind == "food":
        content = tag("path", d="M -70 25 Q 0 82 70 25", fill=p["paper_light"], stroke=p["graphite"], stroke_width=9) + tag("path", d="M -78 20 L 78 20", fill="none", stroke=p["graphite"], stroke_width=9, stroke_linecap="round") + tag("path", d="M -35 -12 Q -18 -50 0 -12 Q 20 -55 38 -12", fill="none", stroke=p["lime"], stroke_width=9, stroke_linecap="round")
    elif kind == "health":
        content = tag("circle", cx=0, cy=10, r=72, fill=p["paper_light"], stroke=p["graphite"], stroke_width=9) + tag("path", d="M -38 10 L 38 10 M 0 -28 L 0 48", fill="none", stroke=p["red"], stroke_width=18, stroke_linecap="round")
    else:
        content = tag("path", d="M -75 -38 Q 0 -58 75 -38 L 68 64 Q 0 82 -70 62 Z", fill=p["paper_light"], stroke=p["graphite"], stroke_width=9) + tag("circle", cx=38, cy=10, r=13, fill=p["lime"], stroke=p["graphite"], stroke_width=5)
    return group(content, class_="rough", transform=f"translate({x} {y})")


def scene_015(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    shelter = tag("ellipse", cx=960, cy=700, rx=570, ry=300, fill=p["paper"], opacity=.96)
    umbrella = security_umbrella(960, 480, style, scale=1.22, instance_id="security-umbrella-s015")
    actor = character(960, 1005, scale=.68, expression="relieved", pose="umbrella", instance_id="worker-s015")
    needs = need_icon("home", 560, 720, style) + need_icon("food", 805, 720, style) + need_icon("health", 1115, 710, style) + need_icon("reserve", 1370, 720, style)
    labels = text_node(475, 875, "MORADIA", "label") + text_node(750, 875, "COMIDA", "label") + text_node(1045, 875, "SAÚDE", "label") + text_node(1290, 875, "RESERVA", "label")
    rain = "".join(tag("path", d=f"M {rx} {ry} l -28 70", fill="none", stroke=p["red"], stroke_width=10, stroke_linecap="round", opacity=.72) for rx, ry in ((170, 280), (320, 470), (1600, 330), (1760, 530), (1510, 720), (400, 250)))
    return background(style, "graphite") + headline + rain + shelter + umbrella + needs + labels + actor


def scene_016(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    pressure = tag("path", d="M 0 205 L 770 205 Q 670 570 760 1080 L 0 1080 Z", fill=p["graphite"])
    rain = "".join(tag("path", d=f"M {rx} {ry} l -30 78", fill="none", stroke=p["red"], stroke_width=11, stroke_linecap="round", opacity=.72) for rx, ry in ((120, 300), (250, 520), (410, 280), (570, 650), (690, 380)))
    bills = bill_stack(260, 820, scale=.82) + bill_stack(565, 900, scale=.6)
    route = safety_path(965, 610, style, scale=1.25, instance_id="safety-path-s016")
    actor = character(1110, 830, scale=.86, expression="relieved", pose="walking", head_tilt=-3, instance_id="worker-s016")
    safe_halo = tag("ellipse", cx=1480, cy=600, rx=300, ry=330, fill=p["lime"], opacity=.08)
    safe_icons = need_icon("home", 1420, 520, style) + need_icon("food", 1615, 665, style) + need_icon("reserve", 1400, 775, style)
    labels = text_node(165, 990, "PRESSÃO", "label-light") + text_node(1400, 965, "ESCOLHA", "label")
    return background(style) + headline + pressure + rain + bills + safe_halo + route + safe_icons + actor + labels


def scene_017(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    shadow = tag("ellipse", cx=970, cy=930, rx=590, ry=70, fill=p["graphite"], opacity=.12)
    page = research_page(960, 585, style, scale=1.36, instance_id="research-page-s017")
    evidence_pill = group(tag("rect", x=0, y=0, width=310, height=68, rx=34, fill=p["graphite"]) + text_node(155, 47, "MÉDIA POSITIVA", "label-light", text_anchor="middle"), transform="translate(195 850)")
    caveat_pill = group(tag("rect", x=0, y=0, width=330, height=68, rx=34, fill=p["yellow"], stroke=p["graphite"], stroke_width=7) + text_node(165, 47, "EFEITO VARIÁVEL", "label", text_anchor="middle"), transform="translate(1395 850)")
    return background(style) + headline + shadow + page + evidence_pill + caveat_pill


def scene_018(row: dict[str, str], style: dict[str, Any]) -> str:
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    levels = income_levels(960, 635, style, scale=1.22, instance_id="income-levels-s018")
    actors = (
        character(472, 705, scale=.5, expression="worried", pose="tension", instance_id="worker-s018-1")
        + character(716, 595, scale=.5, expression="neutral", pose="neutral", instance_id="worker-s018-2")
        + character(960, 466, scale=.5, expression="relieved", pose="neutral", instance_id="worker-s018-3")
        + character(1204, 540, scale=.5, expression="thinking", pose="neutral", instance_id="worker-s018-4")
        + character(1448, 375, scale=.5, expression="fascinated", pose="celebrate", instance_id="worker-s018-5")
    )
    caption = text_node(650, 1005, "MESMA DIREÇÃO. RESPOSTAS DIFERENTES.", "label-light")
    return background(style, "graphite") + headline + levels + actors + caption


def scene_019(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    sign = magic_number_sign(960, 580, style, scale=1.05, instance_id="magic-number-sign-s019")
    left_path = tag("path", d="M 190 850 Q 350 580 600 570", fill="none", stroke=p["lime"], stroke_width=14, stroke_linecap="round", marker_end="url(#arrow)")
    right_path = tag("path", d="M 1730 850 Q 1570 590 1325 545", fill="none", stroke=p["yellow"], stroke_width=14, stroke_linecap="round", marker_end="url(#arrow-yellow)")
    lower_path = tag("path", d="M 640 965 Q 960 860 1280 965", fill="none", stroke=p["blue"], stroke_width=13, stroke_linecap="round")
    people = character(220, 1015, scale=.42, expression="neutral", pose="walking", instance_id="worker-s019-left") + character(1700, 1015, scale=.42, expression="relieved", pose="walking", flip=True, instance_id="worker-s019-right") + character(960, 1035, scale=.38, expression="thinking", pose="neutral", instance_id="worker-s019-center")
    stamp = group(tag("rect", x=0, y=0, width=430, height=72, rx=36, fill=p["red"]) + text_node(215, 50, "NÃO É UNIVERSAL", "label-light", text_anchor="middle"), transform="translate(745 830)")
    return background(style) + headline + left_path + right_path + lower_path + sign + stamp + people


def scene_020(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    shafts = comparison_elevator(960, 595, style, scale=1.12, instance_id="comparison-elevator-s020")
    worker = character(669, 785, scale=.64, expression="realization", pose="neutral", instance_id="worker-s020")
    peers = character(1150, 790, scale=.42, expression="neutral", pose="neutral", variant="ana", instance_id="peer-s020-1") + character(1325, 790, scale=.42, expression="relieved", pose="neutral", instance_id="peer-s020-2")
    lifestyle = mini_house(1235, 455) + tag("rect", x=1350, y=505, width=105, height=72, rx=16, fill=p["yellow"], stroke=p["graphite"], stroke_width=9) + tag("path", d="M 1373 505 Q 1400 450 1430 505", fill="none", stroke=p["graphite"], stroke_width=9)
    labels = text_node(565, 960, "VOCÊ", "label-light") + text_node(1135, 960, "NOVA REFERÊNCIA", "label-light")
    bell = tag("circle", cx=960, cy=235, r=42, fill=p["yellow"], stroke=p["graphite"], stroke_width=10)
    return background(style, "graphite") + headline + shafts + bell + lifestyle + worker + peers + labels


def scene_021(row: dict[str, str], style: dict[str, Any]) -> str:
    headline = text_node(116, 142, row["text_on_screen"])
    people = (
        character(414, 710, scale=.58, expression="neutral", pose="neutral", instance_id="peer-s021-1")
        + character(778, 710, scale=.58, expression="relieved", pose="neutral", variant="ana", instance_id="peer-s021-2")
        + character(1142, 710, scale=.58, expression="neutral", pose="neutral", instance_id="worker-s021")
        + character(1506, 710, scale=.58, expression="relieved", pose="neutral", instance_id="peer-s021-3")
    )
    stations = office_stations(960, 675, style, scale=1.3, instance_id="office-stations-s021")
    caption = text_node(600, 1000, "MESMO CARGO. MESMA REFERÊNCIA.", "label")
    return background(style) + headline + people + stations + caption


def scene_022(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    signals = status_signals(960, 500, style, scale=1.24, instance_id="status-signals-s022")
    peers = character(550, 760, scale=.48, expression="relieved", pose="neutral", instance_id="peer-s022-car") + character(960, 635, scale=.48, expression="fascinated", pose="neutral", variant="ana", instance_id="peer-s022-travel") + character(1370, 760, scale=.48, expression="neutral", pose="neutral", instance_id="peer-s022-home")
    actor_halo = tag("ellipse", cx=960, cy=885, rx=185, ry=170, fill=p["red"], opacity=.09)
    actor = character(960, 990, scale=.72, expression="worried", pose="tension", instance_id="worker-s022")
    caption = text_node(180, 1015, "A REFERÊNCIA MUDOU", "label-light")
    return background(style, "graphite") + headline + signals + peers + actor_halo + actor + caption


def scene_023(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    shafts = comparison_elevator(960, 585, style, scale=1.12, instance_id="comparison-elevator-s023")
    worker = character(669, 780, scale=.64, expression="realization", pose="celebrate", instance_id="worker-s023")
    peers = character(1150, 785, scale=.42, expression="neutral", pose="neutral", variant="ana", instance_id="peer-s023-1") + character(1325, 785, scale=.42, expression="relieved", pose="neutral", instance_id="peer-s023-2")
    sync = tag("path", d="M 420 910 Q 960 990 1500 910", fill="none", stroke=p["blue"], stroke_width=12, stroke_dasharray="22 18", stroke_linecap="round")
    labels = text_node(520, 1005, "SALÁRIO", "label") + text_node(1125, 1005, "COMPARAÇÃO", "label")
    bells = tag("circle", cx=670, cy=215, r=30, fill=p["lime"], stroke=p["graphite"], stroke_width=8) + tag("circle", cx=1250, cy=215, r=30, fill=p["yellow"], stroke=p["graphite"], stroke_width=8)
    return background(style) + headline + sync + shafts + bells + worker + peers + labels


def scene_024(row: dict[str, str], style: dict[str, Any]) -> str:
    headline = text_node(116, 142, row["text_on_screen"])
    steps = relative_steps(960, 560, style, scale=1.25, instance_id="relative-steps-s024")
    people = (
        character(479, 747, scale=.42, expression="neutral", pose="neutral", instance_id="peer-s024-1")
        + character(716, 656, scale=.42, expression="relieved", pose="neutral", instance_id="peer-s024-2")
        + character(954, 559, scale=.46, expression="realization", pose="pointing", flip=True, head_tilt=-5, instance_id="worker-s024")
        + character(1191, 428, scale=.42, expression="neutral", pose="neutral", instance_id="peer-s024-3")
        + character(1429, 297, scale=.42, expression="fascinated", pose="celebrate", instance_id="peer-s024-4")
    )
    caption = text_node(585, 1010, "O LUGAR NO GRUPO MUDA A LEITURA", "label")
    return background(style) + headline + steps + people + caption


def scene_025(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    focus = upward_gaze(1240, 585, style, scale=1.28, instance_id="upward-gaze-s025")
    close_actor = character(420, 1120, scale=1.52, expression="worried", pose="neutral", head_tilt=-8, instance_id="worker-s025")
    eye_trace = tag("path", d="M 390 570 Q 665 430 880 390", fill="none", stroke=p["lime"], stroke_width=13, stroke_linecap="round", stroke_dasharray="20 18", marker_end="url(#arrow)")
    upper_label = group(tag("rect", x=0, y=0, width=270, height=68, rx=34, fill=p["yellow"], stroke=p["graphite"], stroke_width=7) + text_node(135, 47, "MAIS VISÍVEL", "label", text_anchor="middle"), transform="translate(1420 245)")
    return background(style, "graphite") + headline + focus + close_actor + eye_trace + upper_label


def scene_026(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    rulers = racing_rulers(960, 565, style, scale=1.24, instance_id="racing-rulers-s026")
    actor = character(960, 990, scale=.7, expression="worried", pose="neutral", instance_id="worker-s026")
    income_label = group(tag("rect", x=0, y=0, width=220, height=66, rx=33, fill=p["lime"], stroke=p["graphite"], stroke_width=7) + text_node(110, 46, "RENDA", "label", text_anchor="middle"), transform="translate(410 830)")
    reference_label = group(tag("rect", x=0, y=0, width=300, height=66, rx=33, fill=p["red"]) + text_node(150, 46, "REFERÊNCIA", "label-light", text_anchor="middle"), transform="translate(1290 690)")
    gap = text_node(790, 300, "DISTÂNCIA", "label")
    return background(style) + headline + rulers + income_label + reference_label + gap + actor


def scene_027(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    envelope = peer_envelope(960, 630, style, scale=1.1, instance_id="peer-envelope-s027")
    adult_left = character(430, 930, scale=.78, expression="realization", pose="neutral", instance_id="adult-s027-1")
    adult_right = character(1490, 930, scale=.78, expression="thinking", pose="neutral", variant="ana", instance_id="adult-s027-2")
    attention = tag("path", d="M 575 620 Q 730 500 820 530 M 1345 620 Q 1190 500 1100 530", fill="none", stroke=p["lime"], stroke_width=11, stroke_dasharray="18 18", stroke_linecap="round")
    caveat = group(tag("rect", x=0, y=0, width=390, height=68, rx=34, fill=p["yellow"], stroke=p["graphite"], stroke_width=7) + text_node(195, 47, "EFEITO PEQUENO", "label", text_anchor="middle"), transform="translate(765 935)")
    return background(style) + headline + attention + envelope + adult_left + adult_right + caveat


def scene_028(row: dict[str, str], style: dict[str, Any]) -> str:
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    shift = budget_shift(960, 545, style, scale=1.22, instance_id="budget-shift-s028")
    actor = character(960, 990, scale=.64, expression="realization", pose="pointing", instance_id="worker-s028")
    labels = text_node(255, 915, "COTIDIANO", "label-light") + text_node(1280, 915, "BENS DURÁVEIS", "label-light")
    return background(style, "graphite") + headline + shift + labels + actor


def scene_029(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    ruler = normality_ruler(520, 610, style, scale=1.12, level=.9, instance_id="normality-ruler-s029")
    actor = character(560, 970, scale=.9, expression="worried", pose="phone", head_tilt=-4, instance_id="worker-s029")
    feed = comparison_feed(1320, 585, style, scale=1.08, instance_id="comparison-feed-s029")
    thread = tag("path", d="M 730 640 Q 910 500 1050 485", fill="none", stroke=p["lime"], stroke_width=13, stroke_dasharray="20 18", stroke_linecap="round", marker_end="url(#arrow)")
    label = group(tag("rect", x=0, y=0, width=300, height=68, rx=34, fill=p["graphite"]) + text_node(150, 47, "RÉGUA MENTAL", "label-light", text_anchor="middle"), transform="translate(120 900)")
    return background(style) + headline + ruler + thread + actor + feed + label


def scene_030(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    ana_halo = tag("ellipse", cx=520, cy=610, rx=300, ry=350, fill=p["lime"], opacity=.08)
    ana = character(520, 960, scale=1.05, expression="relieved", pose="celebrate", variant="ana", instance_id="ana-s030")
    paycheck = paycheck_blocks(1270, 610, style, scale=1.08, instance_id="paycheck-blocks-s030")
    base_label = group(tag("rect", x=0, y=0, width=300, height=66, rx=33, fill=p["graphite"]) + text_node(150, 46, "RENDA BASE", "label-light", text_anchor="middle"), transform="translate(1015 910)")
    increase_label = group(tag("rect", x=0, y=0, width=245, height=66, rx=33, fill=p["yellow"], stroke=p["graphite"], stroke_width=7) + text_node(122, 46, "AUMENTO", "label", text_anchor="middle"), transform="translate(1400 910)")
    return background(style) + headline + ana_halo + ana + paycheck + base_label + increase_label


def scene_031(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    upgrades = small_upgrades(960, 500, style, scale=1.02, instance_id="small-upgrades-s031")
    ana_halo = tag("ellipse", cx=960, cy=760, rx=190, ry=220, fill=p["lime"], opacity=.09)
    ana = character(960, 980, scale=.72, expression="relieved", pose="neutral", variant="ana", instance_id="ana-s031")
    caption = group(tag("rect", x=0, y=0, width=310, height=68, rx=34, fill=p["graphite"]) + text_node(155, 47, "NADA ABSURDO", "label-light", text_anchor="middle"), transform="translate(145 910)")
    return background(style) + headline + upgrades + ana_halo + ana + caption


def scene_032(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    bar = commitment_bar(960, 540, style, scale=1.15, payoff=False, instance_id="commitment-bar-s032")
    ana = character(960, 1010, scale=.65, expression="surprised", pose="neutral", variant="ana", instance_id="ana-s032")
    total = group(tag("rect", x=0, y=0, width=285, height=68, rx=34, fill=p["lime"], stroke=p["graphite"], stroke_width=7) + text_node(142, 47, "TOTAL: 1.000", "label", text_anchor="middle"), transform="translate(1350 770)")
    brace = tag("path", d="M 280 720 Q 960 790 1640 720", fill="none", stroke=p["paper_light"], stroke_width=10, stroke_linecap="round", opacity=.7)
    return background(style, "graphite") + headline + bar + brace + total + ana


def scene_033(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    bar = commitment_bar(1200, 555, style, scale=.86, payoff=True, instance_id="commitment-bar-s033")
    ana = character(420, 970, scale=.82, expression="surprised", pose="pointing", flip=True, instance_id="ana-s033", variant="ana")
    focus = tag("path", d="M 610 600 Q 1100 300 1640 505", fill="none", stroke=p["lime"], stroke_width=13, stroke_dasharray="20 18", stroke_linecap="round", marker_end="url(#arrow)")
    remaining = group(tag("rect", x=0, y=0, width=240, height=74, rx=37, fill=p["lime"], stroke=p["graphite"], stroke_width=8) + text_node(120, 51, "R$ 50", "label", text_anchor="middle"), transform="translate(1495 755)")
    caption = text_node(865, 920, "950 JÁ TÊM DESTINO", "label")
    return background(style) + headline + focus + bar + ana + remaining + caption


def scene_034(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    shadow = tag("ellipse", cx=960, cy=930, rx=530, ry=75, fill=p["paper_light"], opacity=.08)
    case_file = fictional_case_file(960, 585, style, scale=1.17, instance_id="fictional-case-file-s034")
    stamp_text = group(tag("rect", x=0, y=0, width=420, height=92, rx=20, fill=p["paper_light"], stroke=p["red"], stroke_width=12) + text_node(210, 63, "FICTÍCIO", "headline", text_anchor="middle", fill=p["red"], font_size=58), transform="translate(750 530) rotate(-12 210 46)")
    note = text_node(660, 1015, "CONTA DIDÁTICA • NÃO É MÉDIA NACIONAL", "label-light")
    return background(style, "graphite") + headline + shadow + case_file + stamp_text + note


def scene_035(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    contrast = pleasure_vs_bill(960, 520, style, scale=1.28, instance_id="pleasure-vs-bill-s035")
    ana = character(960, 1010, scale=.67, expression="realization", pose="neutral", variant="ana", instance_id="ana-s035")
    left_label = text_node(240, 900, "NOVIDADE", "label-light")
    right_label = text_node(1375, 900, "RECORRENTE", "label-light")
    thread = tag("path", d="M 610 790 Q 960 880 1310 790", fill="none", stroke=p["lime"], stroke_width=11, stroke_dasharray="18 18", stroke_linecap="round")
    return background(style, "graphite") + headline + contrast + thread + ana + left_label + right_label


def scene_036(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    faded_home = group(need_icon("home", 430, 430, style), opacity=.22)
    faded_car = group(tag("path", d="M 720 480 L 785 390 L 925 390 L 990 480 Z", fill=p["blue"], stroke=p["graphite"], stroke_width=12) + tag("circle", cx=790, cy=495, r=32, fill=p["graphite"]) + tag("circle", cx=920, cy=495, r=32, fill=p["graphite"]), opacity=.22)
    faded_plan = group(need_icon("reserve", 1260, 450, style), opacity=.22)
    actor = character(960, 850, scale=.72, expression="realization", pose="neutral", instance_id="worker-s036")
    bills = walking_bills(1100, 700, style, scale=1.05, instance_id="walking-bills-s036")
    floor = tag("path", d="M 0 970 Q 960 900 1920 970 L 1920 1080 L 0 1080 Z", fill=p["graphite_soft"], opacity=.7)
    return background(style, "graphite") + headline + floor + faded_home + faded_car + faded_plan + actor + bills


def scene_037(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    gears = three_gears(960, 520, style, scale=1.12, instance_id="three-gears-s037")
    actor_halo = tag("ellipse", cx=960, cy=835, rx=170, ry=190, fill=p["lime"], opacity=.08)
    actor = character(960, 1000, scale=.64, expression="realization", pose="neutral", instance_id="worker-s037")
    labels = text_node(785, 245, "ADAPTAÇÃO", "label") + text_node(380, 910, "COMPARAÇÃO", "label") + text_node(1260, 910, "COMPROMISSOS", "label")
    return background(style) + headline + gears + actor_halo + actor + labels


def scene_038(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    flow = synthesis_flow(960, 570, style, scale=1.28, instance_id="synthesis-flow-s038")
    labels = (
        group(tag("rect", x=0, y=0, width=270, height=66, rx=33, fill=p["lime"], stroke=p["graphite"], stroke_width=7) + text_node(135, 46, "CONQUISTA", "label", text_anchor="middle"), transform="translate(205 885)")
        + group(tag("rect", x=0, y=0, width=235, height=66, rx=33, fill=p["graphite"]) + text_node(117, 46, "NORMAL", "label-light", text_anchor="middle"), transform="translate(842 885)")
        + group(tag("rect", x=0, y=0, width=225, height=66, rx=33, fill=p["red"]) + text_node(112, 46, "APERTO", "label-light", text_anchor="middle"), transform="translate(1470 885)")
    )
    return background(style) + headline + flow + labels


def scene_039(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    triangle = enough_triangle(960, 590, style, scale=1.05, instance_id="enough-triangle-s039")
    actor = character(960, 805, scale=.46, expression="relieved", pose="neutral", instance_id="worker-s039")
    center_label = group(tag("rect", x=0, y=0, width=320, height=72, rx=36, fill=p["lime"], stroke=p["graphite"], stroke_width=8) + text_node(160, 50, "SUFICIENTE", "label", text_anchor="middle"), transform="translate(800 865)")
    labels = text_node(835, 250, "RENDA", "label-light") + text_node(340, 935, "CONTAS", "label-light") + text_node(1420, 935, "NORMAL", "label-light")
    return background(style, "graphite") + headline + triangle + actor + center_label + labels


def scene_040(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    interval = decision_interval(960, 545, style, scale=1.14, instance_id="decision-interval-s040")
    actor_halo = tag("ellipse", cx=960, cy=755, rx=180, ry=210, fill=p["lime"], opacity=.09)
    actor = character(960, 990, scale=.67, expression="realization", pose="neutral", instance_id="worker-s040")
    choice = group(tag("rect", x=0, y=0, width=270, height=70, rx=35, fill=p["lime"], stroke=p["graphite"], stroke_width=8) + text_node(135, 49, "ESCOLHA", "label", text_anchor="middle"), transform="translate(620 850)")
    labels = text_node(255, 925, "AUMENTO", "label") + text_node(1390, 925, "NOVA CONTA", "label")
    return background(style) + headline + interval + actor_halo + actor + choice + labels


def scene_041(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    halo = tag("ellipse", cx=810, cy=580, rx=565, ry=350, fill=p["lime"], opacity=.065)
    balance = conscious_balance(800, 570, style, scale=1.08, instance_id="conscious-balance-s041")
    actor = character(1510, 965, scale=.92, expression="relieved", pose="pointing", flip=True, head_tilt=2, instance_id="worker-s041")
    chosen = group(tag("rect", x=0, y=0, width=300, height=68, rx=34, fill=p["lime"], stroke=p["graphite"], stroke_width=7) + text_node(150, 47, "ESCOLHIDO", "label", text_anchor="middle"), transform="translate(290 895)")
    automatic = group(tag("rect", x=0, y=0, width=320, height=68, rx=34, fill=p["paper_light"], stroke=p["red"], stroke_width=7) + text_node(160, 47, "AUTOMÁTICO", "label", text_anchor="middle"), transform="translate(940 895)")
    return background(style) + headline + halo + balance + actor + chosen + automatic


def scene_042(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    envelopes = destination_envelopes(960, 570, style, scale=1.18, instance_id="destination-envelopes-s042")
    labels = text_node(350, 880, "VIVER MELHOR", "label") + text_node(870, 880, "MARGEM", "label") + text_node(1320, 880, "FUTURO", "label")
    actor_halo = tag("ellipse", cx=1680, cy=920, rx=145, ry=130, fill=p["lime"], opacity=.08)
    actor = character(1680, 1050, scale=.48, expression="realization", pose="pointing", flip=True, instance_id="worker-s042")
    stop = tag("path", d="M 1775 405 L 1775 720", fill="none", stroke=p["red"], stroke_width=18, stroke_linecap="round") + tag("circle", cx=1775, cy=350, r=54, fill=p["paper_light"], stroke=p["red"], stroke_width=12)
    return background(style) + headline + envelopes + labels + actor_halo + actor + stop


def scene_043(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"], "headline-light")
    shadow = freedom_shadow(1030, 530, style, scale=1.12, instance_id="freedom-shadow-s043")
    actor = character(350, 990, scale=.84, expression="worried", pose="pointing", instance_id="worker-s043")
    paper_label = group(tag("rect", x=0, y=0, width=300, height=68, rx=34, fill=p["lime"], stroke=p["graphite"], stroke_width=7) + text_node(150, 47, "CONTRACHEQUE", "label", text_anchor="middle"), transform="translate(820 250)")
    freedom_label = group(tag("rect", x=0, y=0, width=260, height=66, rx=33, fill=p["paper_light"], stroke=p["graphite"], stroke_width=7) + text_node(130, 46, "LIBERDADE", "label", text_anchor="middle"), transform="translate(900 925)")
    pointer = tag("path", d="M 505 710 Q 690 735 850 900", fill="none", stroke=p["lime"], stroke_width=11, stroke_dasharray="18 16", marker_end="url(#arrow)")
    return background(style, "graphite") + headline + shadow + pointer + actor + paper_label + freedom_label


def scene_044(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(110, 150, row["text_on_screen"], "headline-light")
    underline = path("M 112 180 Q 425 205 810 178", css="", fill="none", stroke=p["lime"], stroke_width=14, stroke_linecap="round")
    threads = callback_threads(1335, 660, style, scale=1.05, instance_id="callback-threads-s044")
    glow = "".join(tag("circle", cx=1335, cy=600, r=r, fill="none", stroke=p["lime"], stroke_width=8, opacity=o) for r, o in ((315, .08), (255, .12)))
    device = phone(1335, 600, scale=1.18, alert=True)
    actor = character(470, 930, scale=1.36, expression="realization", pose="phone", head_tilt=-5, instance_id="worker-s044")
    return background(style, "graphite") + glow + headline + underline + threads + actor + device


def scene_045(row: dict[str, str], style: dict[str, Any]) -> str:
    p = style["palette"]
    headline = text_node(116, 142, row["text_on_screen"])
    calendar_lock = locking_calendar(960, 590, style, scale=1.13, instance_id="locking-calendar-s045")
    actor = character(1680, 1035, scale=.52, expression="realization", pose="neutral", instance_id="worker-s045")
    silence = group(tag("rect", x=0, y=0, width=440, height=70, rx=35, fill=p["graphite"]) + text_node(220, 49, "PERÍODO SILENCIOSO", "label-light", text_anchor="middle"), transform="translate(740 875)")
    faint_wave = tag("path", d="M 210 935 Q 360 895 510 935 T 810 935 M 1110 935 Q 1260 895 1410 935 T 1710 935", fill="none", stroke=p["graphite_soft"], stroke_width=8, opacity=.28)
    return background(style) + headline + calendar_lock + faint_wave + silence + actor


SCENE_RENDERERS: dict[str, Callable[[dict[str, str], dict[str, Any]], str]] = {
    "S001": scene_001,
    "S002": scene_002,
    "S003": scene_003,
    "S004": scene_004,
    "S005": scene_005,
    "S006": scene_006,
    "S007": scene_007,
    "S008": scene_008,
    "S009": scene_009,
    "S010": scene_010,
    "S011": scene_011,
    "S012": scene_012,
    "S013": scene_013,
    "S014": scene_014,
    "S015": scene_015,
    "S016": scene_016,
    "S017": scene_017,
    "S018": scene_018,
    "S019": scene_019,
    "S020": scene_020,
    "S021": scene_021,
    "S022": scene_022,
    "S023": scene_023,
    "S024": scene_024,
    "S025": scene_025,
    "S026": scene_026,
    "S027": scene_027,
    "S028": scene_028,
    "S029": scene_029,
    "S030": scene_030,
    "S031": scene_031,
    "S032": scene_032,
    "S033": scene_033,
    "S034": scene_034,
    "S035": scene_035,
    "S036": scene_036,
    "S037": scene_037,
    "S038": scene_038,
    "S039": scene_039,
    "S040": scene_040,
    "S041": scene_041,
    "S042": scene_042,
    "S043": scene_043,
    "S044": scene_044,
    "S045": scene_045,
}


def svg_document(content: str, style: dict[str, Any], metadata: dict[str, Any], *, width: int = 1920, height: int = 1080) -> str:
    meta = tag("metadata", escape(json.dumps(metadata, ensure_ascii=False, sort_keys=True)))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">\n'
        + meta
        + common_defs(style)
        + content
        + "\n</svg>\n"
    )


def safe_write(path: Path, data: str, update: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    if existed and not update:
        return "preservado"
    path.write_text(data, encoding="utf-8", newline="\n")
    return "atualizado" if existed else "criado"


def standalone_asset(content: str, style: dict[str, Any], width: int, height: int, name: str) -> str:
    translated = group(content, transform=f"translate({width/2} {height*.78})")
    return svg_document(
        tag("rect", x=0, y=0, width=width, height=height, fill=style["palette"]["paper_light"]) + translated,
        style,
        {"asset": name, "style_id": style["style_id"]},
        width=width,
        height=height,
    )


def generate_library(style: dict[str, Any], update: bool) -> list[tuple[Path, str]]:
    generated: list[tuple[Path, str]] = []
    assets: list[tuple[Path, str]] = []
    assets.append((ROOT / "assets" / "characters" / "worker.svg", standalone_asset(character(0, 0, scale=1.0, expression="neutral", pose="neutral"), style, 640, 820, "CO_WORKER_V1")))
    assets.append((ROOT / "assets" / "characters" / "ana.svg", standalone_asset(character(0, 0, scale=1.0, expression="relieved", pose="neutral", variant="ana"), style, 640, 820, "CO_ANA_V1")))
    for expression in ("neutral", "surprised", "worried", "relieved", "thinking", "fascinated", "realization"):
        head = group(tag("circle", cx=0, cy=-334, r=91, class_="head") + face(expression), transform="translate(0 0)")
        expression_svg = svg_document(
            tag("rect", x=0, y=0, width=360, height=360, fill=style["palette"]["paper_light"])
            + group(head, transform="translate(180 510)"),
            style,
            {"asset": expression, "style_id": style["style_id"]},
            width=360,
            height=360,
        )
        assets.append((ROOT / "assets" / "expressions" / f"{expression}.svg", expression_svg))
    for pose in POSES:
        assets.append((ROOT / "assets" / "poses" / f"{pose}.svg", standalone_asset(character(0, 0, scale=1.0, expression="neutral", pose=pose), style, 640, 820, pose)))
    assets.extend(
        [
            (ROOT / "assets" / "objects" / "phone_raise.svg", standalone_asset(phone(0, -170, scale=.8, alert=True), style, 500, 700, "phone_raise")),
            (ROOT / "assets" / "objects" / "calendar.svg", standalone_asset(calendar(0, -80, scale=1.0), style, 520, 430, "calendar")),
            (ROOT / "assets" / "objects" / "bills.svg", standalone_asset(bill_stack(0, -70, scale=1.0), style, 520, 430, "bills")),
            (ROOT / "assets" / "objects" / "brain_console.svg", standalone_asset(brain_console(0, -70, style, scale=.72), style, 700, 560, "brain_console")),
            (ROOT / "assets" / "objects" / "normality_ruler.svg", standalone_asset(normality_ruler(0, -80, style, scale=.82, level=.78), style, 430, 650, "normality_ruler")),
            (ROOT / "assets" / "objects" / "phone_generic.svg", standalone_asset(generic_phone(0, -170, scale=.8, glowing=False), style, 500, 700, "phone_generic")),
            (ROOT / "assets" / "objects" / "emotion_curve.svg", standalone_asset(emotion_curve(0, -80, style, scale=.72), style, 720, 500, "emotion_curve")),
            (ROOT / "assets" / "objects" / "opposing_routes.svg", standalone_asset(opposing_routes(0, -110, style, scale=.68), style, 820, 620, "opposing_routes")),
            (ROOT / "assets" / "objects" / "podium_floor.svg", standalone_asset(podium_floor(0, -90, style, scale=.62), style, 820, 500, "podium_floor")),
            (ROOT / "assets" / "objects" / "delivery_bag.svg", standalone_asset(delivery_bag(0, -90, style, scale=1.0), style, 420, 440, "delivery_bag")),
            (ROOT / "assets" / "objects" / "expectation_race.svg", standalone_asset(expectation_race(0, -100, style, scale=.62), style, 820, 520, "expectation_race")),
            (ROOT / "assets" / "objects" / "security_umbrella.svg", standalone_asset(security_umbrella(0, -155, style, scale=.62), style, 820, 620, "security_umbrella")),
            (ROOT / "assets" / "objects" / "safety_path.svg", standalone_asset(safety_path(0, -120, style, scale=.62), style, 820, 560, "safety_path")),
            (ROOT / "assets" / "objects" / "research_page.svg", standalone_asset(research_page(0, -145, style, scale=.64), style, 820, 650, "research_page")),
            (ROOT / "assets" / "objects" / "income_levels.svg", standalone_asset(income_levels(0, -110, style, scale=.62), style, 820, 560, "income_levels")),
            (ROOT / "assets" / "objects" / "magic_number_sign.svg", standalone_asset(magic_number_sign(0, -165, style, scale=.62), style, 620, 680, "magic_number_sign")),
            (ROOT / "assets" / "objects" / "comparison_elevator.svg", standalone_asset(comparison_elevator(0, -165, style, scale=.62), style, 820, 680, "comparison_elevator")),
            (ROOT / "assets" / "objects" / "office_stations.svg", standalone_asset(office_stations(0, -125, style, scale=.62), style, 820, 560, "office_stations")),
            (ROOT / "assets" / "objects" / "status_signals.svg", standalone_asset(status_signals(0, -125, style, scale=.62), style, 820, 560, "status_signals")),
            (ROOT / "assets" / "objects" / "relative_steps.svg", standalone_asset(relative_steps(0, -135, style, scale=.62), style, 820, 600, "relative_steps")),
            (ROOT / "assets" / "objects" / "upward_gaze.svg", standalone_asset(upward_gaze(0, -120, style, scale=.62), style, 820, 600, "upward_gaze")),
            (ROOT / "assets" / "objects" / "racing_rulers.svg", standalone_asset(racing_rulers(0, -150, style, scale=.62), style, 680, 650, "racing_rulers")),
            (ROOT / "assets" / "objects" / "peer_envelope.svg", standalone_asset(peer_envelope(0, -120, style, scale=.62), style, 720, 650, "peer_envelope")),
            (ROOT / "assets" / "objects" / "budget_shift.svg", standalone_asset(budget_shift(0, -115, style, scale=.62), style, 820, 560, "budget_shift")),
            (ROOT / "assets" / "objects" / "comparison_feed.svg", standalone_asset(comparison_feed(0, -170, style, scale=.62), style, 620, 760, "comparison_feed")),
            (ROOT / "assets" / "objects" / "paycheck_blocks.svg", standalone_asset(paycheck_blocks(0, -145, style, scale=.62), style, 720, 620, "paycheck_blocks")),
            (ROOT / "assets" / "objects" / "small_upgrades.svg", standalone_asset(small_upgrades(0, -125, style, scale=.62), style, 820, 620, "small_upgrades")),
            (ROOT / "assets" / "objects" / "commitment_bar.svg", standalone_asset(commitment_bar(0, -95, style, scale=.62), style, 900, 420, "commitment_bar")),
            (ROOT / "assets" / "objects" / "fictional_case_file.svg", standalone_asset(fictional_case_file(0, -150, style, scale=.62), style, 760, 680, "fictional_case_file")),
            (ROOT / "assets" / "objects" / "pleasure_vs_bill.svg", standalone_asset(pleasure_vs_bill(0, -110, style, scale=.62), style, 820, 560, "pleasure_vs_bill")),
            (ROOT / "assets" / "objects" / "walking_bills.svg", standalone_asset(walking_bills(0, -150, style, scale=.62), style, 760, 680, "walking_bills")),
            (ROOT / "assets" / "objects" / "three_gears.svg", standalone_asset(three_gears(0, -140, style, scale=.62), style, 760, 680, "three_gears")),
            (ROOT / "assets" / "objects" / "synthesis_flow.svg", standalone_asset(synthesis_flow(0, -125, style, scale=.62), style, 900, 600, "synthesis_flow")),
            (ROOT / "assets" / "objects" / "enough_triangle.svg", standalone_asset(enough_triangle(0, -150, style, scale=.62), style, 760, 680, "enough_triangle")),
            (ROOT / "assets" / "objects" / "decision_interval.svg", standalone_asset(decision_interval(0, -120, style, scale=.62), style, 900, 600, "decision_interval")),
            (ROOT / "assets" / "objects" / "conscious_balance.svg", standalone_asset(conscious_balance(0, -120, style, scale=.62), style, 900, 620, "conscious_balance")),
            (ROOT / "assets" / "objects" / "destination_envelopes.svg", standalone_asset(destination_envelopes(0, -110, style, scale=.62), style, 900, 600, "destination_envelopes")),
            (ROOT / "assets" / "objects" / "freedom_shadow.svg", standalone_asset(freedom_shadow(0, -165, style, scale=.58), style, 820, 720, "freedom_shadow")),
            (ROOT / "assets" / "objects" / "callback_threads.svg", standalone_asset(callback_threads(0, -120, style, scale=.72), style, 820, 620, "callback_threads")),
            (ROOT / "assets" / "objects" / "locking_calendar.svg", standalone_asset(locking_calendar(0, -120, style, scale=.62), style, 900, 650, "locking_calendar")),
            (ROOT / "assets" / "backgrounds" / "paper.svg", svg_document(background(style), style, {"asset": "paper", "style_id": style["style_id"]})),
            (ROOT / "assets" / "backgrounds" / "graphite.svg", svg_document(background(style, "graphite"), style, {"asset": "graphite", "style_id": style["style_id"]})),
        ]
    )
    for path_obj, data in assets:
        generated.append((path_obj, safe_write(path_obj, data, update)))
    return generated


def write_library_manifest(style: dict[str, Any], update: bool) -> str:
    fields = ["asset_id", "category", "file", "style_id", "first_used_episode", "first_used_scene", "status", "notes"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for asset_id, category, relative_file, first_scene, notes in ASSET_REGISTRY:
        path = ROOT / relative_file
        if not path.exists():
            raise RuntimeError(f"Asset registrado sem arquivo: {relative_file}")
        if first_scene not in SCENE_RENDERERS:
            raise RuntimeError(f"Asset sem cena de estreia implementada: {asset_id} -> {first_scene}")
        writer.writerow(
            {
                "asset_id": asset_id,
                "category": category,
                "file": relative_file,
                "style_id": style["style_id"],
                "first_used_episode": "CO-001",
                "first_used_scene": first_scene,
                "status": "active",
                "notes": notes,
            }
        )
    return safe_write(ROOT / "assets" / "library_manifest.csv", buffer.getvalue(), update)


def write_review_board(
    output_dir: Path,
    selected: list[str],
    *,
    title: str,
    filename: str,
    update: bool,
) -> str:
    if len(selected) > 5:
        raise RuntimeError("O board de revisao aceita no maximo cinco cenas.")
    positions = ((90, 150), (680, 150), (1270, 150), (385, 570), (975, 570))
    cards = []
    for scene_id, (x, y) in zip(selected, positions):
        cards.append(
            f'<rect x="{x-10}" y="{y-10}" width="580" height="345" rx="18" fill="#FFFFFF" stroke="#171918" stroke-width="7"/>'
            f'<image href="{scene_id.lower()}.svg" x="{x}" y="{y}" width="560" height="315" preserveAspectRatio="xMidYMid meet"/>'
            f'<rect x="{x}" y="{y-52}" width="112" height="42" rx="21" fill="#171918"/>'
            f'<text x="{x+56}" y="{y-22}" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="800" fill="#F3EBDD">{scene_id}</text>'
        )
    board = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">'
        '<rect width="1920" height="1080" fill="#F3EBDD"/>'
        f'<text x="90" y="92" font-family="Arial, sans-serif" font-size="54" font-weight="900" fill="#171918">{escape(title)}</text>'
        + "".join(cards)
        + "</svg>\n"
    )
    return safe_write(output_dir / filename, board, update)


def render_scenes(episode: Path, style: dict[str, Any], selected: list[str], update: bool) -> list[dict[str, Any]]:
    rows = read_visual_script(episode)
    by_id = {row["scene_id"].strip().upper(): row for row in rows}
    specs = read_scene_specs(episode)
    ep_id = episode_id(episode)
    output_dir = ROOT / style["output"]["episode_folder"] / ep_id
    rendered: list[dict[str, Any]] = []
    for scene_id in selected:
        row = by_id.get(scene_id)
        if not row:
            raise RuntimeError(f"Cena ausente no roteiro: {scene_id}")
        renderer = SCENE_RENDERERS.get(scene_id)
        if not renderer:
            raise RuntimeError(f"Cena ainda nao implementada: {scene_id}")
        scene_number = int(scene_id[1:])
        spec = specs.get(scene_id)
        if 6 <= scene_number <= 45 and spec is None:
            raise RuntimeError(f"Cena sem descritor vetorial: {scene_id}")
        metadata = {
            "episode_id": ep_id,
            "scene_id": scene_id,
            "asset_id": row["asset_id"],
            "style_id": style["style_id"],
            "source": "04_ROTEIRO_VISUAL.csv",
            "descriptor_source": "assets/vector_scenes.json" if spec else None,
            "motion": row["motion"],
            "visual": row["visual"],
            "duration_seconds": spec.get("duration_seconds") if spec else None,
            "composition": spec.get("composition") if spec else None,
            "camera": spec.get("camera") if spec else None,
            "actions": spec.get("actions", []) if spec else [],
            "rigged_characters": True,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        document = svg_document(renderer(row, style), style, metadata)
        output = output_dir / f"{scene_id.lower()}.svg"
        status = safe_write(output, document, update)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        entry = {
            **metadata,
            "file": str(output.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest,
            "status": status,
            "width": 1920,
            "height": 1080,
        }
        rendered.append(entry)
        print(f"{scene_id}: {status} -> {output.relative_to(ROOT)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    cumulative_path = output_dir / "scene_manifest.json"
    legacy_path = output_dir / "prototype_manifest.json"
    if cumulative_path.exists():
        cumulative = load_json(cumulative_path)
    elif legacy_path.exists():
        legacy = load_json(legacy_path)
        cumulative = {
            "schema_version": 1,
            "style_id": style["style_id"],
            "episode_id": ep_id,
            "scenes": legacy.get("scenes", []),
        }
    else:
        cumulative = {"schema_version": 1, "style_id": style["style_id"], "episode_id": ep_id, "scenes": []}
    by_scene = {entry["scene_id"]: entry for entry in cumulative.get("scenes", [])}
    for entry in rendered:
        if entry["status"] != "preservado" or entry["scene_id"] not in by_scene:
            by_scene[entry["scene_id"]] = entry
    cumulative["scenes"] = [by_scene[key] for key in sorted(by_scene, key=lambda value: int(value[1:]))]
    cumulative_path.write_text(json.dumps(cumulative, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    prototype_ids = [str(value).upper() for value in style["output"]["prototype_scene_ids"]]
    if selected == prototype_ids:
        write_review_board(
            output_dir,
            selected,
            title="CAPITAL OCULTO — PROTÓTIPO CO_SKETCH_V1",
            filename="prototype_board.svg",
            update=update,
        )
    if selected == ["S006", "S007", "S008", "S009", "S010"]:
        write_review_board(
            output_dir,
            selected,
            title="CAPITAL OCULTO — BLOCO 02: ADAPTAÇÃO",
            filename="review_s006_s010.svg",
            update=update,
        )
    if selected == ["S011", "S012", "S013", "S014", "S015"]:
        write_review_board(
            output_dir,
            selected,
            title="CAPITAL OCULTO — BLOCO 03: EXPECTATIVA",
            filename="review_s011_s015.svg",
            update=update,
        )
    if selected == ["S016", "S017", "S018", "S019", "S020"]:
        write_review_board(
            output_dir,
            selected,
            title="CAPITAL OCULTO — BLOCO 04: DINHEIRO E COMPARAÇÃO",
            filename="review_s016_s020.svg",
            update=update,
        )
    if selected == ["S021", "S022", "S023", "S024", "S025"]:
        write_review_board(
            output_dir,
            selected,
            title="CAPITAL OCULTO — BLOCO 05: POSIÇÃO RELATIVA",
            filename="review_s021_s025.svg",
            update=update,
        )
    if selected == ["S026", "S027", "S028", "S029", "S030"]:
        write_review_board(
            output_dir,
            selected,
            title="CAPITAL OCULTO — BLOCO 06: A RÉGUA E O AUMENTO",
            filename="review_s026_s030.svg",
            update=update,
        )
    if selected == ["S031", "S032", "S033", "S034", "S035"]:
        write_review_board(
            output_dir,
            selected,
            title="CAPITAL OCULTO — BLOCO 07: O AUMENTO EMPREGADO",
            filename="review_s031_s035.svg",
            update=update,
        )
    if selected == ["S036", "S037", "S038", "S039", "S040"]:
        write_review_board(
            output_dir,
            selected,
            title="CAPITAL OCULTO — BLOCO 08: O SUFICIENTE",
            filename="review_s036_s040.svg",
            update=update,
        )
    if selected == ["S041", "S042", "S043", "S044", "S045"]:
        write_review_board(
            output_dir,
            selected,
            title="CAPITAL OCULTO — BLOCO 09: ESCOLHA CONSCIENTE",
            filename="review_s041_s045.svg",
            update=update,
        )
    return rendered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compoe cenas SVG offline do Capital Oculto.")
    parser.add_argument("episodio", help="ID, nome da pasta ou caminho do episodio.")
    parser.add_argument("--cenas", help="IDs separados por virgula. Padrao: S001-S005.")
    parser.add_argument("--sem-biblioteca", action="store_true", help="Nao cria os assets-base reutilizaveis.")
    parser.add_argument("--atualizar", action="store_true", help="Atualiza SVGs existentes de forma explicita.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    episode = resolve_episode(args.episodio)
    style = load_json(STYLE_FILE)
    selected = (
        [value.strip().upper() for value in args.cenas.split(",") if value.strip()]
        if args.cenas
        else [str(value).upper() for value in style["output"]["prototype_scene_ids"]]
    )
    unsupported = [scene for scene in selected if scene not in SCENE_RENDERERS]
    if unsupported:
        raise RuntimeError(f"Fora do escopo do prototipo: {', '.join(unsupported)}")

    if not args.sem_biblioteca:
        library = generate_library(style, args.atualizar)
        manifest_status = write_library_manifest(style, args.atualizar)
        counts: dict[str, int] = {}
        for _, status in library:
            counts[status] = counts.get(status, 0) + 1
        print("Biblioteca: " + ", ".join(f"{value} {key}(s)" for key, value in sorted(counts.items())))
        print(f"Manifesto da biblioteca: {manifest_status}")
    scenes = render_scenes(episode, style, selected, args.atualizar)
    print(f"Concluido: {len(scenes)} cena(s), SVG 1920x1080, sem modelo de IA.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise SystemExit(2)
