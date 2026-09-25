#!/usr/bin/env python3
"""Resolve o manifesto experimental e prepara o player do piloto audiovisual S004–S006.

Mantém estritamente o status EXPERIMENTAL com motion_status=MOTION_CANDIDATE
e resolve os anchors narrativos a partir do timing real de Azure Speech (pt-BR-AntonioNeural).
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006"
TIMING_FILE = PILOT_DIR / "timing" / "03A_AUDIO_TIMING.json"
MANIFEST_FILE = PILOT_DIR / "manifest" / "scene_manifest.json"
MOTION_SPEC_FILE = PILOT_DIR / "scenes" / "motion_spec.json"
PLAYER_FILE = PILOT_DIR / "player.html"
COMPOSITIONS_FILE = ROOT / "config" / "visual_compositions.json"
SOURCE_DIR = ROOT / "tests" / "editorial_compositions_v1" / "s004_s006" / "selected"

SAFE_AREA = 64
TEXT_SAFE_AREA = 96
CANVAS = {"width": 1920, "height": 1080}


SCENE_PLANS: list[dict[str, Any]] = [
    {
        "scene_id": "S004",
        "beat_ids": ["B004"],
        "composition": "EDITORIAL_TYPE",
        "variant": "CO-COMP-05A",
        "version": 1.0,
        "focus_mode": None,
        "anchor_start": "Você",
        "anchor_end": "absurda",
        "anchors": {
            "scene_entry": "Você",
            "negation": "não precisa",
            "purchase": "compra",
            "absurd": "absurda",
        },
        "events": [
            {
                "event_id": "S004-E01",
                "anchor": "Você",
                "anchor_edge": "start",
                "duration": 0.25,
                "target": "premise_tag_and_headline",
                "action": "reveal",
                "narrative_function": "estabelecer O PROBLEMA de forma discreta",
            },
            {
                "event_id": "S004-E02",
                "anchor": "não precisa",
                "anchor_edge": "start",
                "duration": 0.6355,
                "target": "negation_keyword",
                "action": "reveal_dominant",
                "narrative_function": "revelar NÃO É com peso visual dominante e destaque em âmbar",
            },
            {
                "event_id": "S004-E03",
                "anchor": "compra",
                "anchor_edge": "start",
                "duration": 0.3813,
                "target": "purchase_headline",
                "action": "reveal",
                "narrative_function": "revelar UMA COMPRA na sequência do raciocínio",
            },
            {
                "event_id": "S004-E04",
                "anchor": "absurda",
                "anchor_edge": "start",
                "duration": 0.6356,
                "target": "absurd_display",
                "action": "reveal",
                "narrative_function": "fechar a afirmação editorial com ABSURDA",
            },
            {
                "event_id": "S004-E05",
                "anchor": "absurda",
                "anchor_edge": "end",
                "duration": 0.35,
                "target": "statement_underline",
                "action": "expand_and_lock",
                "narrative_function": "sublinhado estrutural trava a composição",
            },
        ],
        "continuity_in": "Fade contextual e redução do residual de S003",
        "continuity_out": "Estrutura tipográfica recua em wipe/slide suave abrindo espaço para os três trilhos de S005",
        "dominant_motion": "semantic_negation_reveal",
    },
    {
        "scene_id": "S005",
        "beat_ids": ["B005"],
        "composition": "SYSTEM_MAP",
        "variant": "CO-COMP-06A",
        "version": 1.0,
        "focus_mode": None,
        "anchor_start": "Mesmo assim",
        "anchor_end": "invisível",
        "anchors": {
            "scene_entry": "Mesmo assim",
            "driver_context": "renda",
            "track_normal": "normal",
            "track_comparison": "compara",
            "track_expenses": "despesas",
            "shared_reference": "movem",
            "parallel_shift": "tempo",
            "system_settle": "invisível",
        },
        "events": [
            {
                "event_id": "S005-E01",
                "anchor": "Mesmo assim",
                "anchor_edge": "start",
                "duration": 0.8119,
                "target": "tracks_foundation",
                "action": "establish",
                "narrative_function": "estabelecer os três trilhos no canvas",
            },
            {
                "event_id": "S005-E02",
                "anchor": "renda",
                "anchor_edge": "start",
                "duration": 0.4558,
                "target": "driver_label",
                "action": "reveal",
                "narrative_function": "revelar o driver superior do sistema (QUANDO A RENDA SOBE)",
            },
            {
                "event_id": "S005-E03",
                "anchor": "normal",
                "anchor_edge": "start",
                "duration": 0.5270,
                "target": "track_normal",
                "action": "stagger_reveal",
                "narrative_function": "estabelecer primeira variável do sistema (NORMAL)",
            },
            {
                "event_id": "S005-E04",
                "anchor": "compara",
                "anchor_edge": "start",
                "duration": 0.4985,
                "target": "track_comparison",
                "action": "stagger_reveal",
                "narrative_function": "estabelecer segunda variável do sistema (COMPARAÇÃO)",
            },
            {
                "event_id": "S005-E05",
                "anchor": "despesas",
                "anchor_edge": "start",
                "duration": 0.5697,
                "target": "track_expenses",
                "action": "stagger_reveal",
                "narrative_function": "estabelecer terceira variável do sistema (DESPESAS)",
            },
            {
                "event_id": "S005-E06",
                "anchor": "movem",
                "anchor_edge": "start",
                "duration": 0.8546,
                "target": "shared_reference_diagonal",
                "action": "traverse_and_align",
                "narrative_function": "diagonal lima percorre e conecta os três trilhos como referência compartilhada",
            },
            {
                "event_id": "S005-E07",
                "anchor": "tempo",
                "anchor_edge": "start",
                "duration": 1.6664,
                "target": "all_three_tracks",
                "action": "parallel_shift",
                "narrative_function": "os três trilhos se deslocam em paralelo respondendo à referência compartilhada",
            },
            {
                "event_id": "S005-E08",
                "anchor": "invisível",
                "anchor_edge": "start",
                "duration": 0.8545,
                "target": "system_label",
                "action": "settle_and_confirm",
                "narrative_function": "assentar o sistema e confirmar o comportamento compartilhado (O SISTEMA SE MOVE JUNTO)",
            },
        ],
        "continuity_in": "Trilhos de S005 entram enquanto a tipografia de S004 recua sem deixar tela vazia",
        "continuity_out": "Direção de movimento compartilhada serve de origem visual para a baseline de S006",
        "dominant_motion": "parallel_system_shift",
    },
    {
        "scene_id": "S006",
        "beat_ids": ["B006"],
        "composition": "MOVING_BASELINE",
        "variant": "CO-COMP-04D",
        "version": 1.0,
        "focus_mode": None,
        "anchor_start": "A primeira peça",
        "anchor_end": "adaptação",
        "anchors": {
            "scene_entry": "A primeira peça",
            "old_state": "A primeira peça",
            "baseline_rise": "cérebro",
            "deemphasize": "traição",
            "new_normal": "adaptação",
        },
        "events": [
            {
                "event_id": "S006-E01",
                "anchor": "A primeira peça",
                "anchor_edge": "start",
                "duration": 0.9996,
                "target": "old_state_and_base",
                "action": "establish_dominant",
                "narrative_function": "EXTRA estabelece o estado anterior com presença dominante",
            },
            {
                "event_id": "S006-E02",
                "anchor": "cérebro",
                "anchor_edge": "start",
                "duration": 1.5566,
                "target": "baseline_diagonal",
                "action": "ascend_and_transfer",
                "narrative_function": "referência diagonal sobe conectando o patamar anterior ao novo nível",
            },
            {
                "event_id": "S006-E03",
                "anchor": "traição",
                "anchor_edge": "start",
                "duration": 0.5998,
                "target": "old_state_extra",
                "action": "deemphasize",
                "narrative_function": "EXTRA perde peso e opacidade virando memória",
            },
            {
                "event_id": "S006-E04",
                "anchor": "adaptação",
                "anchor_edge": "start",
                "duration": 0.8568,
                "target": "new_state_normal",
                "action": "lock_dominant",
                "narrative_function": "NORMAL trava no topo como estado dominante",
            },
            {
                "event_id": "S006-E05",
                "anchor": "adaptação",
                "anchor_edge": "end",
                "duration": 0.45,
                "target": "interpretation_labels",
                "action": "reveal",
                "narrative_function": "confirmação conceitual de que a referência mudou (VIROU REFERÊNCIA)",
            },
        ],
        "continuity_in": "Reaproveita a sensação e direção do deslocamento de S005 como origem da baseline diagonal",
        "continuity_out": "NORMAL estabilizado e travado no novo patamar fechando o raciocínio das 6 cenas",
        "dominant_motion": "conceptual_reference_shift",
    },
]


class PilotError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise PilotError(f"Arquivo ausente: {path}") from exc


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in plain if char.isalnum())


def parse_anchor(value: str) -> list[str]:
    tokens = [normalize(token) for token in re.findall(r"\S+", value)]
    tokens = [token for token in tokens if token]
    if not tokens:
        raise PilotError(f"Anchor inválido: {value!r}")
    return tokens


def words_for_beats(timing: dict[str, Any], beat_ids: list[str]) -> list[dict[str, Any]]:
    mapping = {beat["beat_id"]: beat for beat in timing.get("beats", [])}
    missing = [beat_id for beat_id in beat_ids if beat_id not in mapping]
    if missing:
        raise PilotError(f"Beat(s) ausente(s) no timing: {', '.join(missing)}")
    return [word for beat_id in beat_ids for word in mapping[beat_id]["words"]]


def resolve_anchor(value: str, beat_ids: list[str], timing: dict[str, Any]) -> dict[str, Any]:
    tokens = parse_anchor(value)
    words = words_for_beats(timing, beat_ids)
    normalized = [word.get("normalized") or normalize(word["text"]) for word in words]
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index in range(0, len(words) - len(tokens) + 1):
        if normalized[index : index + len(tokens)] == tokens:
            matches.append((words[index], words[index + len(tokens) - 1]))
    if not matches:
        raise PilotError(f"Anchor não encontrado: '{value}' em {','.join(beat_ids)}")
    if len(matches) > 1:
        raise PilotError(f"Anchor ambíguo: '{value}' tem {len(matches)} ocorrências")
    first, last = matches[0]
    return {
        "text": value,
        "start": float(first["start"]),
        "end": float(last["end"]),
        "start_word_index": int(first["index"]),
        "end_word_index": int(last["index"]),
    }


def composition_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in config.get("compositions", [])}


def read_svg_metadata(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    metadata = root.find("{http://www.w3.org/2000/svg}metadata")
    if metadata is None or not metadata.text:
        raise PilotError(f"Metadata ausente no master de cena: {path.name}")
    return json.loads(metadata.text)


def event_with_time(
    event: dict[str, Any],
    *,
    beat_ids: list[str],
    timing: dict[str, Any],
    scene_start: float,
    scene_end: float,
) -> dict[str, Any]:
    anchor = resolve_anchor(event["anchor"], beat_ids, timing)
    edge = event.get("anchor_edge", "start")
    start = anchor[edge]
    end_anchor = None
    if event.get("end_anchor"):
        end_anchor = resolve_anchor(event["end_anchor"], beat_ids, timing)
        end = end_anchor["start"]
    else:
        end = start + float(event.get("duration", 0.3))
    start = max(scene_start, min(scene_end, start))
    end = max(start + 0.001, min(scene_end, end))
    resolved = dict(event)
    resolved["anchor"] = anchor
    if end_anchor:
        resolved["end_anchor"] = end_anchor
    resolved["time"] = round(start, 4)
    resolved["end_time"] = round(end, 4)
    resolved["duration"] = round(end - start, 4)
    resolved.pop("anchor_edge", None)
    return resolved


def generate_player_html(output_file: Path) -> None:
    html_content = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Capital Oculto — piloto audiovisual S004–S006</title>
  <style>
    html, body { margin: 0; width: 100%; height: 100%; overflow: hidden; background: #111111; }
    body { display: grid; place-items: center; }
    canvas { display: block; width: min(100vw, 177.777vh); height: min(56.25vw, 100vh); background: #F4F3EF; }
    #status { position: fixed; left: 14px; bottom: 10px; color: #F4F3EF; font: 600 12px/1.2 system-ui, sans-serif; opacity: .65; }
  </style>
</head>
<body>
  <canvas id="stage" width="1920" height="1080"></canvas>
  <div id="status">carregando piloto S004–S006…</div>
  <script>
    const canvas = document.querySelector('#stage');
    const ctx = canvas.getContext('2d', { alpha: false });
    const statusNode = document.querySelector('#status');
    const QUERY = new URLSearchParams(location.search);
    const SILENT = QUERY.get('silent') === '1';
    const PREVIEW_TIME = QUERY.has('preview') ? Number(QUERY.get('preview')) : NaN;
    const P = {
      black: '#111111', lime: '#C4E538', amber: '#E8A33D',
      offWhite: '#F4F3EF', gray: '#D9D9D4'
    };
    const FONT = "Bahnschrift, 'Arial Narrow', Arial, sans-serif";

    const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value));
    const easeOut = value => 1 - Math.pow(1 - clamp(value), 3);
    const lerp = (start, end, value) => start + (end - start) * clamp(value);
    const progress = (time, event) => {
      if (!event) return 0;
      return easeOut((time - event.time) / Math.max(.001, event.end_time - event.time));
    };
    const eventById = (scene, id) => scene.events.find(event => event.event_id === id);

    function fillText(text, x, y, size, weight = 900, color = P.black, align = 'left', alpha = 1, letterSpacing = 0) {
      ctx.save();
      ctx.globalAlpha = clamp(alpha);
      ctx.fillStyle = color;
      ctx.font = `${weight} ${size}px ${FONT}`;
      ctx.textAlign = align;
      ctx.textBaseline = 'alphabetic';
      if (letterSpacing && ctx.letterSpacing !== undefined) {
        ctx.letterSpacing = `${letterSpacing}px`;
      }
      ctx.fillText(text, x, y);
      ctx.restore();
    }

    function background() {
      ctx.fillStyle = P.offWhite;
      ctx.fillRect(0, 0, 1920, 1080);
      ctx.fillStyle = 'rgba(17,17,17,.045)';
      for (let y = 18; y < 1080; y += 18) {
        for (let x = 18; x < 1920; x += 18) ctx.fillRect(x, y, 1.2, 1.2);
      }
    }

    function roundedRect(x, y, width, height, radius, color, alpha = 1) {
      ctx.save();
      ctx.globalAlpha = clamp(alpha);
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(x, y, width, height, radius);
      ctx.fill();
      ctx.restore();
    }

    // ========================================================
    // S004 — STATEMENT_STACK (CO-COMP-05A)
    // "Você não precisa ter feito nenhuma compra absurda."
    // Reveal semântico da negação:
    // 1. "O PROBLEMA" aparece discreto
    // 2. "NÃO É" entra como elemento dominante
    // 3. pequena pausa visual
    // 4. "UMA COMPRA" aparece
    // 5. "ABSURDA" fecha a frase
    // 6. underline estrutural finaliza
    // ========================================================
    function drawS004(scene, time) {
      background();
      const pEntry = progress(time, eventById(scene, 'S004-E01'));
      const pNegation = progress(time, eventById(scene, 'S004-E02'));
      const pPurchase = progress(time, eventById(scene, 'S004-E03'));
      const pAbsurd = progress(time, eventById(scene, 'S004-E04'));
      const pLock = progress(time, eventById(scene, 'S004-E05'));

      // Transição de saída nos últimos 300ms de S004
      const exitProgress = time > scene.end - 0.35 ? easeOut((time - (scene.end - 0.35)) / 0.35) : 0;
      const sceneAlpha = 1 - exitProgress * 0.75;
      const slideOutX = -exitProgress * 90;

      ctx.save();
      ctx.translate(slideOutX, 0);

      // 1. Barra âmbar + "O PROBLEMA"
      if (pEntry > 0) {
        const yOffset = (1 - pEntry) * 14;
        roundedRect(96, 112 + yOffset, 112, 12, 6, P.amber, pEntry * sceneAlpha);
        fillText('O PROBLEMA', 96, 250 + yOffset, 112, 900, P.black, 'left', pEntry * sceneAlpha, -4);
      }

      // 2. "NÃO É" — Elemento dominante com maior peso visual
      if (pNegation > 0) {
        const scale = lerp(0.97, 1.0, pNegation);
        const yOffset = (1 - pNegation) * 18;
        ctx.save();
        ctx.translate(86, 548 + yOffset);
        ctx.scale(scale, scale);
        fillText('NÃO É', 0, 0, 270, 900, P.amber, 'left', pNegation * sceneAlpha, -14);
        ctx.restore();
      }

      // 4. "UMA COMPRA"
      if (pPurchase > 0) {
        const yOffset = (1 - pPurchase) * 12;
        fillText('UMA COMPRA', 678, 734 + yOffset, 118, 900, P.black, 'left', pPurchase * sceneAlpha, -4);
      }

      // 5. "ABSURDA"
      if (pAbsurd > 0) {
        const yOffset = (1 - pAbsurd) * 14;
        fillText('ABSURDA', 678, 912 + yOffset, 176, 900, P.black, 'left', pAbsurd * sceneAlpha, -9);
      }

      // 6. Underline estrutural finalizando a composição
      if (pLock > 0) {
        const currentWidth = 920 * pLock;
        roundedRect(678, 940, currentWidth, 14, 7, P.black, pLock * sceneAlpha);
      }

      ctx.restore();
    }

    // ========================================================
    // S005 — PARALLEL_SHIFT (CO-COMP-06A)
    // "NORMAL, COMPARAÇÃO, DESPESAS fazem parte de um sistema que se move junto."
    // 1. estabelecer três trilhos
    // 2. estabelecer labels
    // 3. referência comum começa a se deslocar
    // 4. NORMAL responde
    // 5. COMPARAÇÃO responde
    // 6. DESPESAS responde
    // 7. os três terminam deslocados na mesma direção
    // ========================================================
    function drawS005(scene, time) {
      background();
      const pTracks = progress(time, eventById(scene, 'S005-E01'));
      const pDriver = progress(time, eventById(scene, 'S005-E02'));
      const pNormal = progress(time, eventById(scene, 'S005-E03'));
      const pComp = progress(time, eventById(scene, 'S005-E04'));
      const pExp = progress(time, eventById(scene, 'S005-E05'));
      const pRef = progress(time, eventById(scene, 'S005-E06'));
      const pShift = progress(time, eventById(scene, 'S005-E07'));
      const pLock = progress(time, eventById(scene, 'S005-E08'));

      // Transição de entrada suave
      const enterAlpha = easeOut((time - scene.start) / 0.35);

      // Label superior: "QUANDO A RENDA SOBE"
      if (pDriver > 0) {
        fillText('QUANDO A RENDA SOBE', 1824, 136, 28, 800, P.black, 'right', pDriver * enterAlpha, 2.4);
      }

      // Referência comum compartilhada (diagonal lima M610 904 L1690 132)
      // Representa referência compartilhada do sistema
      if (pRef > 0) {
        ctx.save();
        ctx.strokeStyle = P.lime;
        ctx.lineWidth = 30;
        ctx.lineCap = 'round';
        ctx.globalAlpha = 0.95 * pRef * enterAlpha;

        const startX = 610, startY = 904;
        const targetX = 1690, targetY = 132;
        const curX = lerp(startX, targetX, pRef);
        const curY = lerp(startY, targetY, pRef);

        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(curX, curY);
        ctx.stroke();
        ctx.restore();
      }

      // Deslocamento compartilhado dos blocos nos três trilhos:
      // Pequeno stagger harmônico
      const shiftNormal = easeOut(clamp((pShift - 0.00) / 0.85));
      const shiftComp = easeOut(clamp((pShift - 0.08) / 0.85));
      const shiftExp = easeOut(clamp((pShift - 0.16) / 0.85));

      // Posições finais dos blocos lima conforme SVG original:
      // NORMAL: x=1196, w=386
      // COMPARAÇÃO: x=1386, w=268
      // DESPESAS: x=1576, w=184
      // Posição inicial pré-deslocamento tem recuo de 240px
      const xNorm = lerp(1196 - 240, 1196, shiftNormal);
      const xComp = lerp(1386 - 240, 1386, shiftComp);
      const xExp = lerp(1576 - 240, 1576, shiftExp);

      // Trilho 1 — NORMAL
      if (pTracks > 0) {
        // Base preta
        ctx.save();
        ctx.fillStyle = P.black;
        ctx.globalAlpha = pTracks * enterAlpha;
        ctx.beginPath();
        ctx.moveTo(560, 272);
        ctx.lineTo(1110, 272);
        ctx.lineTo(1228, 358);
        ctx.lineTo(560, 358);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }
      if (pNormal > 0) {
        fillText('NORMAL', 96, 330, 82, 900, P.black, 'left', pNormal * enterAlpha, -4);
        roundedRect(xNorm, 272, 386, 86, 18, P.lime, pNormal * enterAlpha);
      }

      // Trilho 2 — COMPARAÇÃO
      if (pTracks > 0) {
        ctx.save();
        ctx.fillStyle = P.black;
        ctx.globalAlpha = pTracks * enterAlpha;
        ctx.beginPath();
        ctx.moveTo(560, 522);
        ctx.lineTo(1300, 522);
        ctx.lineTo(1418, 608);
        ctx.lineTo(560, 608);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }
      if (pComp > 0) {
        fillText('COMPARAÇÃO', 96, 580, 70, 900, P.black, 'left', pComp * enterAlpha, -4);
        roundedRect(xComp, 522, 268, 86, 18, P.lime, pComp * enterAlpha);
      }

      // Trilho 3 — DESPESAS
      if (pTracks > 0) {
        ctx.save();
        ctx.fillStyle = P.black;
        ctx.globalAlpha = pTracks * enterAlpha;
        ctx.beginPath();
        ctx.moveTo(560, 772);
        ctx.lineTo(1490, 772);
        ctx.lineTo(1608, 858);
        ctx.lineTo(560, 858);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }
      if (pExp > 0) {
        fillText('DESPESAS', 96, 830, 82, 900, P.black, 'left', pExp * enterAlpha, -4);
        roundedRect(xExp, 772, 184, 86, 18, P.lime, pExp * enterAlpha);
      }

      // Label inferior: "O SISTEMA SE MOVE JUNTO"
      if (pLock > 0) {
        fillText('O SISTEMA SE MOVE JUNTO', 1824, 966, 28, 800, P.black, 'right', pLock * enterAlpha, 2.4);
      }
    }

    // ========================================================
    // S006 — CONCEPTUAL_BASELINE (CO-COMP-04D)
    // "o que era EXTRA virou NORMAL."
    // Motion dominante: MUDANÇA DE REFERÊNCIA.
    // 1. EXTRA estabelece o estado anterior dominante
    // 2. baseline/referência começa a subir
    // 3. EXTRA perde peso/opacidade
    // 4. NORMAL aparece no novo patamar dominante
    // 5. VIROU REFERÊNCIA entra como confirmação
    // ========================================================
    function drawS006(scene, time) {
      background();
      const pOld = progress(time, eventById(scene, 'S006-E01'));
      const pRise = progress(time, eventById(scene, 'S006-E02'));
      const pDeemp = progress(time, eventById(scene, 'S006-E03'));
      const pNormal = progress(time, eventById(scene, 'S006-E04'));
      const pLock = progress(time, eventById(scene, 'S006-E05'));

      const enterAlpha = easeOut((time - scene.start) / 0.35);

      // Linha diagonal preta estrutural: M-40 930 L1910 182
      if (pOld > 0) {
        ctx.save();
        ctx.strokeStyle = P.black;
        ctx.lineWidth = 36;
        ctx.lineCap = 'round';
        ctx.globalAlpha = pOld * enterAlpha;

        const startX = -40, startY = 930;
        const targetX = 1910, targetY = 182;
        const curX = lerp(startX, targetX, Math.max(pOld, pRise));
        const curY = lerp(startY, targetY, Math.max(pOld, pRise));

        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(curX, curY);
        ctx.stroke();
        ctx.restore();
      }

      // Linha lima de destaque no patamar superior: M1110 495 L1910 188
      if (pRise > 0) {
        ctx.save();
        ctx.strokeStyle = P.lime;
        ctx.lineWidth = 36;
        ctx.lineCap = 'round';
        ctx.globalAlpha = pRise * enterAlpha;

        const startX = 1110, startY = 495;
        const targetX = 1910, targetY = 188;
        const curX = lerp(startX, targetX, pRise);
        const curY = lerp(startY, targetY, pRise);

        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(curX, curY);
        ctx.stroke();
        ctx.restore();
      }

      // Estado anterior: "ANTES / EXTRA"
      // Inicia dominante (opacidade 1.0) e perde peso até 0.40 com pDeemp
      if (pOld > 0) {
        const extraAlpha = pOld * lerp(1.0, 0.40, pDeemp) * enterAlpha;
        fillText('ANTES', 96, 774, 28, 800, P.black, 'left', extraAlpha, 2.4);
        fillText('EXTRA', 88, 928, 148, 900, P.black, 'left', extraAlpha, -7);
      }

      // Novo patamar dominante: "AGORA / NORMAL"
      if (pNormal > 0) {
        const normAlpha = pNormal * enterAlpha;
        const normScale = lerp(0.97, 1.0, pNormal);

        fillText('AGORA', 1824, 154, 28, 800, P.black, 'right', normAlpha, 2.4);

        ctx.save();
        ctx.translate(1818, 438);
        ctx.scale(normScale, normScale);
        fillText('NORMAL', 0, 0, 252, 900, P.black, 'right', normAlpha, -14);
        ctx.restore();

        // Barra horizontal lima abaixo de NORMAL
        const curBarWidth = 804 * pNormal;
        roundedRect(1824 - curBarWidth, 502, curBarWidth, 18, 9, P.lime, normAlpha);
      }

      // Confirmação: "VIROU REFERÊNCIA" e label inferior
      if (pLock > 0) {
        const lockAlpha = pLock * enterAlpha;
        fillText('VIROU REFERÊNCIA', 1824, 636, 66, 900, P.black, 'right', lockAlpha, -4);
        fillText('O GANHO NÃO SUMIU • A BASE MUDOU', 1824, 964, 28, 800, P.black, 'right', lockAlpha, 2.4);
      }
    }

    function renderFrame(time, manifest) {
      let scene = manifest.scenes.find(item => time >= item.start && time < item.end);
      if (!scene) scene = time < 0 ? manifest.scenes[0] : manifest.scenes.at(-1);
      if (scene.scene_id === 'S004') drawS004(scene, time);
      else if (scene.scene_id === 'S005') drawS005(scene, time);
      else drawS006(scene, time);
      statusNode.textContent = `${scene.scene_id} · ${time.toFixed(2)}s${SILENT ? ' · silent' : ''}`;
    }

    async function start() {
      const manifest = await fetch('manifest/scene_manifest.json').then(response => {
        if (!response.ok) throw new Error(`manifest HTTP ${response.status}`);
        return response.json();
      });
      const renderOrigin = Number(manifest.audio.render_origin_seconds || 0);
      const presentationDuration = Number(
        manifest.audio.presentation_duration_seconds || (manifest.audio.duration_seconds - renderOrigin)
      );
      renderFrame(renderOrigin, manifest);
      if (Number.isFinite(PREVIEW_TIME)) {
        renderFrame(clamp(PREVIEW_TIME, 0, manifest.audio.duration_seconds), manifest);
        statusNode.textContent = `preview · ${PREVIEW_TIME.toFixed(2)}s`;
        if (QUERY.get('capture') === '1') {
          canvas.toBlob(blob => fetch('/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'image/png', 'X-Preview-Time': String(PREVIEW_TIME) },
            body: blob
          }), 'image/png');
        }
        return;
      }
      const audioData = await fetch(manifest.audio.player_path).then(response => {
        if (!response.ok) throw new Error(`audio HTTP ${response.status}`);
        return response.arrayBuffer();
      });
      const audioContext = new AudioContext({ sampleRate: 48000 });
      const audioBuffer = await audioContext.decodeAudioData(audioData);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      const audioDestination = audioContext.createMediaStreamDestination();
      source.connect(audioDestination);

      const videoStream = canvas.captureStream(30);
      const tracks = [...videoStream.getVideoTracks()];
      if (!SILENT) tracks.push(...audioDestination.stream.getAudioTracks());
      const combined = new MediaStream(tracks);
      const preferred = SILENT
        ? ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm']
        : ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'];
      const mimeType = preferred.find(type => MediaRecorder.isTypeSupported(type)) || '';
      const recorder = new MediaRecorder(combined, {
        mimeType,
        videoBitsPerSecond: 7000000,
        ...(!SILENT ? { audioBitsPerSecond: 128000 } : {})
      });
      const chunks = [];
      recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
      recorder.onerror = event => fetch('/error', { method: 'POST', body: String(event.error || event) });
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: recorder.mimeType || 'video/webm' });
        await fetch('/save', {
          method: 'POST',
          headers: {
            'Content-Type': blob.type,
            'X-Duration': String(presentationDuration),
            'X-Source-Duration': String(audioBuffer.duration),
            'X-Render-Origin': String(renderOrigin),
            'X-Width': String(canvas.width),
            'X-Height': String(canvas.height),
            'X-Fps': '30',
            'X-Silent': String(SILENT)
          },
          body: blob
        });
      };

      await audioContext.resume();
      const startAt = audioContext.currentTime + .15;
      recorder.start(1000);
      source.start(startAt, renderOrigin);
      function tick() {
        const outputTime = Math.max(0, audioContext.currentTime - startAt);
        const sourceTime = renderOrigin + outputTime;
        renderFrame(sourceTime, manifest);
        if (outputTime < presentationDuration + .1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
      source.onended = () => setTimeout(() => recorder.stop(), 280);
    }

    start().catch(error => {
      statusNode.textContent = `erro: ${error.message}`;
      fetch('/error', { method: 'POST', body: error.stack || String(error) });
    });
  </script>
</body>
</html>
"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content, encoding="utf-8")


def main() -> int:
    timing = load_json(TIMING_FILE)
    if timing.get("provider") != "azure_speech_rest":
        raise PilotError("O piloto exige timing produzido pelo provider Azure REST.")
    if [beat.get("beat_id") for beat in timing.get("beats", [])] != ["B004", "B005", "B006"]:
        raise PilotError("O timing deve conter somente B004–B006.")
    audio_path = ROOT / timing["audio_file"]
    if not audio_path.is_file() or sha256(audio_path) != timing.get("audio_sha256"):
        raise PilotError("WAV processado ausente ou divergente do timing.")

    config = load_json(COMPOSITIONS_FILE)
    compositions = composition_map(config)
    beat_map = {beat["beat_id"]: beat for beat in timing["beats"]}

    source_paths = {
        "S004": SOURCE_DIR / "s004.svg",
        "S005": SOURCE_DIR / "s005.svg",
        "S006": SOURCE_DIR / "s006.svg",
    }
    for path in source_paths.values():
        if not path.is_file():
            raise PilotError(f"SVG de cena ausente: {path}")

    for directory in (
        PILOT_DIR / "scenes",
        PILOT_DIR / "manifest",
        PILOT_DIR / "renders",
        PILOT_DIR / "logs",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    scenes: list[dict[str, Any]] = []
    for plan in SCENE_PLANS:
        composition = compositions.get(plan["variant"])
        if not composition:
            raise PilotError(f"Variante ausente no catálogo: {plan['variant']}")
        if composition.get("status") != "EXPERIMENTAL":
            raise PilotError(f"{plan['variant']}: status esperado é EXPERIMENTAL.")

        source_path = source_paths[plan["scene_id"]]
        metadata = read_svg_metadata(source_path)
        if metadata.get("composition_id") != plan["variant"]:
            raise PilotError(f"{plan['scene_id']}: SVG fonte usa variante incorreta.")

        resolved_anchors = {
            name: resolve_anchor(text, plan["beat_ids"], timing)
            for name, text in plan["anchors"].items()
        }
        anchor_start = resolve_anchor(plan["anchor_start"], plan["beat_ids"], timing)
        anchor_end = resolve_anchor(plan["anchor_end"], plan["beat_ids"], timing)

        if plan["scene_id"] == "S004":
            start = 0.0
            end = float(beat_map["B005"]["start"])
        elif plan["scene_id"] == "S005":
            start = float(beat_map["B005"]["start"])
            end = float(beat_map["B006"]["start"])
        else:
            start = float(beat_map["B006"]["start"])
            end = float(timing["duration_seconds"])

        if end <= start or anchor_start["start"] < start - 0.001 or anchor_end["end"] > end + 0.001:
            raise PilotError(f"{plan['scene_id']}: limites narrativos inválidos ({start}s - {end}s).")

        events = [
            event_with_time(
                event,
                beat_ids=plan["beat_ids"],
                timing=timing,
                scene_start=start,
                scene_end=end,
            )
            for event in plan["events"]
        ]
        for event in events:
            if not start <= event["time"] < event["end_time"] <= end + 0.001:
                raise PilotError(f"{event['event_id']}: evento fora da cena.")

        scenes.append(
            {
                "scene_id": plan["scene_id"],
                "beat_ids": plan["beat_ids"],
                "start": round(start, 4),
                "end": round(end, 4),
                "duration": round(end - start, 4),
                "composition": plan["composition"],
                "variant": {
                    "id": plan["variant"],
                    "version": plan["version"],
                    "status": "EXPERIMENTAL",
                    "motion_status": "MOTION_CANDIDATE",
                },
                "focus_mode": plan["focus_mode"],
                "anchor_start": anchor_start,
                "anchor_end": anchor_end,
                "anchors": resolved_anchors,
                "resolved_times": {
                    name: {"start": anchor["start"], "end": anchor["end"]}
                    for name, anchor in resolved_anchors.items()
                },
                "events": events,
                "dominant_motion": plan["dominant_motion"],
                "continuity_in": plan["continuity_in"],
                "continuity_out": plan["continuity_out"],
                "source_svg": relative(source_path),
                "source_svg_sha256": sha256(source_path),
                "content_zones": composition.get("content_zones", []),
            }
        )

    if any(abs(scenes[i]["end"] - scenes[i + 1]["start"]) > 0.001 for i in range(len(scenes) - 1)):
        raise PilotError("Timeline possui lacuna entre cenas.")

    manifest = {
        "schema_version": "1.0",
        "pilot_id": "capital_oculto_audiovisual_s004_s006",
        "status": "EXPERIMENTAL",
        "selection_mode": "EXPERIMENTAL_TEST",
        "production_allowed": False,
        "episode_id": "CO-001",
        "canvas": CANVAS,
        "safe_area": {"absolute": SAFE_AREA, "text": TEXT_SAFE_AREA},
        "visual_system": "CO_VISUAL_V3",
        "art_direction": "CO_ART_DIRECTION_V4",
        "composition_system": "CO_EDITORIAL_COMPOSITIONS_V1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "audio": {
            "file": relative(audio_path),
            "player_path": "audio/processed/narration_azure_antonio.wav",
            "sha256": timing["audio_sha256"],
            "provider": timing["provider"],
            "narrator_id": timing["narrator_id"],
            "voice": timing["voice"],
            "duration_seconds": timing["duration_seconds"],
            "render_origin_seconds": 0.0,
            "presentation_duration_seconds": timing["duration_seconds"],
            "leading_blank_policy": "PRESERVE_INITIAL_LEAD_FOR_TRANSITION",
            "timing_method": timing["timing_method"],
        },
        "sources": {
            "timing": {"file": relative(TIMING_FILE), "sha256": sha256(TIMING_FILE)},
            "compositions": {
                "file": relative(COMPOSITIONS_FILE),
                "sha256": sha256(COMPOSITIONS_FILE),
            },
        },
        "scenes": scenes,
    }
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    motion_spec = {
        "pilot_id": manifest["pilot_id"],
        "status": "EXPERIMENTAL",
        "palette": {
            "black": "#111111",
            "lime": "#C4E538",
            "amber": "#E8A33D",
            "off_white": "#F4F3EF",
            "gray": "#D9D9D4",
        },
        "motion_language": {
            "easing": "ease_out_cubic",
            "idle": "none",
            "dominant_movements_simultaneous": 1,
            "micro_reveal_ms": [200, 350],
            "explanatory_ms": [450, 900],
            "major_transform_ms": [700, 1400],
            "transition_ms": [250, 500],
        },
        "scenes": [
            {
                "scene_id": scene["scene_id"],
                "source_svg": scene["source_svg"],
                "source_svg_sha256": scene["source_svg_sha256"],
                "variant": scene["variant"],
                "focus_mode": scene["focus_mode"],
                "events": scene["events"],
            }
            for scene in scenes
        ],
    }
    MOTION_SPEC_FILE.write_text(
        json.dumps(motion_spec, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    generate_player_html(PLAYER_FILE)

    print(f"MANIFESTO RESOLVIDO — {relative(MANIFEST_FILE)}")
    for scene in scenes:
        print(
            f"  {scene['scene_id']}: {scene['start']:.3f}s–{scene['end']:.3f}s (dur={scene['duration']:.3f}s) | "
            f"{scene['variant']['id']} v{scene['variant']['version']} [{scene['variant']['motion_status']}]"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PilotError, OSError, KeyError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
