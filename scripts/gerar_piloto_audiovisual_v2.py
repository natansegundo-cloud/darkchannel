#!/usr/bin/env python3
"""Gera o manifesto e o player do piloto audiovisual V2 com Visual Sub-Beats.

Implementa:
- 6 cenas (S001–S006) em timeline contínua (52.493s)
- Visual sub-beats (S001.A..C, S002.A..C, S003.A..D, S004.A..D, S005.A..F, S006.A..F)
- Primeiro estado útil imediato (< 350ms em todas as cenas)
- Ritmo visual controlado (mudança a cada 2–4s, max static hold <= 4000ms)
- Proteção da tipografia principal (CO-COMP-04D v1.1 com baseline como base estrutural sem cruzar letras)
- Suporte a status: S001-S003 APPROVED, S004-S006 EXPERIMENTAL (MOTION_CANDIDATE)
- Não sobrescreve os artefatos anteriores; gera manifest_v2 e player_v2.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PILOT_DIR = ROOT / "tests" / "audiovisual_pilot_s001_s006"
TIMING_FILE = PILOT_DIR / "timing" / "03A_AUDIO_TIMING_v2.json"
MANIFEST_FILE = PILOT_DIR / "manifest" / "scene_manifest_v2.json"
MOTION_SPEC_FILE = PILOT_DIR / "scenes" / "motion_spec_v2.json"
PLAYER_FILE = PILOT_DIR / "player_v2.html"
MOTION_CONTRACT_FILE = ROOT / "config" / "motion_contract.json"
COMPOSITIONS_FILE = ROOT / "config" / "visual_compositions.json"

CANVAS = {"width": 1920, "height": 1080}
SAFE_AREA = {"absolute": 64, "text": 96}


SCENE_DEFINITIONS = [
    {
        "scene_id": "S001",
        "beat_ids": ["B001"],
        "composition": "DATA_HERO",
        "variant": "CO-COMP-01C",
        "version": 1.1,
        "status": "APPROVED",
        "motion_status": "MOTION_APPROVED",
        "subbeats": [
            {
                "subbeat_id": "S001.A",
                "label": "primeiro_estado_util_e_salario_inicial",
                "narrative_function": "estabelecer imediatamente R$ 3.500 e contexto inicial nos primeiros 350ms",
                "anchor": "Você",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S001.B",
                "label": "counter_de_aumento",
                "narrative_function": "materializar aumento de 3.500 para 4.200",
                "anchor": "seu salário",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S001.C",
                "label": "assentamento_e_delta",
                "narrative_function": "assentar 4.200 e revelar + R$ 700 em lima",
                "anchor": "aumentou",
                "offset_ms": 0,
            },
        ],
    },
    {
        "scene_id": "S002",
        "beat_ids": ["B002"],
        "composition": "MOVING_BASELINE",
        "variant": "CO-COMP-04A",
        "version": 1.1,
        "status": "APPROVED",
        "motion_status": "MOTION_APPROVED",
        "subbeats": [
            {
                "subbeat_id": "S002.A",
                "label": "estado_antigo_estabelecido",
                "narrative_function": "estabelecer referência antiga 3.500 e estado atual 4.200",
                "anchor": "Por algumas semanas",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S002.B",
                "label": "referencia_sobe",
                "narrative_function": "mover fisicamente a linha de base para o novo patamar",
                "anchor": "Três meses depois",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S002.C",
                "label": "novo_valor_assume",
                "narrative_function": "des-enfatizar 3.500 e consolidar 4.200 como NOVO NORMAL",
                "anchor": "outra vez",
                "offset_ms": 0,
            },
        ],
    },
    {
        "scene_id": "S003",
        "beat_ids": ["B003"],
        "composition": "SHRINKING_SPACE",
        "variant": "CO-COMP-03A",
        "version": 1.1,
        "status": "APPROVED",
        "motion_status": "MOTION_APPROVED",
        "subbeats": [
            {
                "subbeat_id": "S003.A",
                "label": "folga_inicial",
                "narrative_function": "mostrar folga ampla inicial antes da compressão",
                "anchor": "O aumento",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S003.B",
                "label": "primeira_compressao",
                "narrative_function": "massa escura da esquerda (gastos fixos) avança",
                "anchor": "era real",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S003.C",
                "label": "compressao_final",
                "narrative_function": "massa escura da direita (gastos novos) avança",
                "anchor": "Então por que",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S003.D",
                "label": "r20_estabiliza",
                "narrative_function": "assentar R$ 20 como consequência e travar compressão",
                "anchor": "folga sumiu",
                "offset_ms": 0,
            },
        ],
    },
    {
        "scene_id": "S004",
        "beat_ids": ["B004"],
        "composition": "EDITORIAL_TYPE",
        "variant": "CO-COMP-05A",
        "version": 1.0,
        "status": "EXPERIMENTAL",
        "motion_status": "MOTION_CANDIDATE",
        "subbeats": [
            {
                "subbeat_id": "S004.A",
                "label": "o_problema_discreto",
                "narrative_function": "revelar O PROBLEMA e tag âmbar nos primeiros 350ms",
                "anchor": "Você",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S004.B",
                "label": "nao_e_dominante",
                "narrative_function": "revelar NÃO É com peso dominante de 270px em âmbar",
                "anchor": "não precisa",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S004.C",
                "label": "uma_compra_revelada",
                "narrative_function": "revelar UMA COMPRA na sequência do raciocínio",
                "anchor": "compra",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S004.D",
                "label": "absurda_e_underline",
                "narrative_function": "fechar com ABSURDA e expandir sublinhado estrutural",
                "anchor": "absurda",
                "offset_ms": 0,
            },
        ],
    },
    {
        "scene_id": "S005",
        "beat_ids": ["B005"],
        "composition": "SYSTEM_MAP",
        "variant": "CO-COMP-06A",
        "version": 1.0,
        "status": "EXPERIMENTAL",
        "motion_status": "MOTION_CANDIDATE",
        "subbeats": [
            {
                "subbeat_id": "S005.A",
                "label": "estabelecer_tres_trilhos",
                "narrative_function": "estabelecer imediatamente os três trilhos no canvas (NORMAL, COMPARAÇÃO, DESPESAS)",
                "anchor": "Mesmo assim",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S005.B",
                "label": "referencia_compartilhada",
                "narrative_function": "introduzir driver QUANDO A RENDA SOBE e diagonal lima de referência compartilhada",
                "anchor": "renda",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S005.C",
                "label": "normal_responde",
                "narrative_function": "variável NORMAL responde e se desloca no trilho",
                "anchor": "normal",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S005.D",
                "label": "comparacao_responde",
                "narrative_function": "variável COMPARAÇÃO responde e se desloca no trilho",
                "anchor": "compara",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S005.E",
                "label": "despesas_responde",
                "narrative_function": "variável DESPESAS responde e se desloca no trilho",
                "anchor": "despesas",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S005.F",
                "label": "sistema_se_move_junto",
                "narrative_function": "três estados finais perfeitamente assentados com payoff O SISTEMA SE MOVE JUNTO",
                "anchor": "movem",
                "offset_ms": 0,
            },
        ],
    },
    {
        "scene_id": "S006",
        "beat_ids": ["B006"],
        "composition": "MOVING_BASELINE",
        "variant": "CO-COMP-04D",
        "version": 1.1,
        "status": "EXPERIMENTAL",
        "motion_status": "MOTION_CANDIDATE",
        "subbeats": [
            {
                "subbeat_id": "S006.A",
                "label": "extra_domina_estado_antigo",
                "narrative_function": "EXTRA domina no nível inferior com presença inicial de 100%",
                "anchor": "A primeira peça",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S006.B",
                "label": "referencia_muda",
                "narrative_function": "baseline diagonal sobe conectando EXTRA ao novo nível",
                "anchor": "cérebro",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S006.C",
                "label": "extra_perde_presenca",
                "narrative_function": "EXTRA perde peso e opacidade (reduzindo para 40%)",
                "anchor": "traição",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S006.D",
                "label": "normal_assume_patamar",
                "narrative_function": "NORMAL assume o novo nível como estado dominante",
                "anchor": "adaptação",
                "offset_ms": 0,
            },
            {
                "subbeat_id": "S006.E",
                "label": "baseline_trava_sem_cruzar",
                "narrative_function": "baseline resolve como base estrutural de NORMAL sem cruzar nenhuma letra (protect_primary_type)",
                "anchor": "adaptação",
                "offset_ms": 300,
            },
            {
                "subbeat_id": "S006.F",
                "label": "virou_referencia_confirma",
                "narrative_function": "confirmação final com VIROU REFERÊNCIA e label inferior",
                "anchor": "adaptação",
                "offset_ms": 650,
            },
        ],
    },
]


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in plain if char.isalnum())


def parse_anchor(value: str) -> list[str]:
    tokens = [normalize(token) for token in re.findall(r"\S+", value)]
    return [t for t in tokens if t]


def resolve_anchor(value: str, words: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = parse_anchor(value)
    normalized = [word.get("normalized") or normalize(word["text"]) for word in words]
    matches = []
    for i in range(0, len(words) - len(tokens) + 1):
        if normalized[i : i + len(tokens)] == tokens:
            matches.append((words[i], words[i + len(tokens) - 1]))
    if not matches:
        raise RuntimeError(f"Anchor não encontrado: '{value}'")
    if len(matches) > 1:
        # Se houver mais de uma ocorrência, escolhe a primeira explicitamente
        first, last = matches[0]
    else:
        first, last = matches[0]
    return {
        "text": value,
        "start": float(first["start"]),
        "end": float(last["end"]),
        "start_word_index": int(first["index"]),
        "end_word_index": int(last["index"]),
    }


def main() -> int:
    timing = json.loads(TIMING_FILE.read_text(encoding="utf-8-sig"))
    contract = json.loads(MOTION_CONTRACT_FILE.read_text(encoding="utf-8-sig"))
    total_audio_duration = float(timing["duration_seconds"])

    beat_map = {b["beat_id"]: b for b in timing["beats"]}
    all_words = [w for b in timing["beats"] for w in b["words"]]

    resolved_scenes = []

    # Mapeamento temporal de cada cena baseado nos beats
    # S001: B001
    # S002: B002
    # S003: B003
    # S004: B004
    # S005: B005
    # S006: B006
    for i, sdef in enumerate(SCENE_DEFINITIONS):
        beat_id = sdef["beat_ids"][0]
        beat = beat_map[beat_id]
        scene_words = beat["words"]

        # Início e fim da cena
        if i == 0:
            s_start = 0.0
        else:
            s_start = float(beat["start"])

        if i == len(SCENE_DEFINITIONS) - 1:
            s_end = total_audio_duration
        else:
            next_beat_id = SCENE_DEFINITIONS[i + 1]["beat_ids"][0]
            s_end = float(beat_map[next_beat_id]["start"])

        s_duration = round(s_end - s_start, 4)

        # Resolver visual sub-beats
        resolved_subbeats = []
        for sb_idx, sb in enumerate(sdef["subbeats"]):
            anc = resolve_anchor(sb["anchor"], scene_words)
            sb_time = round(anc["start"] + (sb.get("offset_ms", 0) / 1000.0), 4)
            # Garante limites
            sb_time = max(s_start, min(s_end - 0.05, sb_time))
            resolved_subbeats.append(
                {
                    "subbeat_id": sb["subbeat_id"],
                    "label": sb["label"],
                    "time": sb_time,
                    "anchor_text": sb["anchor"],
                    "anchor_start": anc["start"],
                    "anchor_end": anc["end"],
                    "narrative_function": sb["narrative_function"],
                }
            )

        # Ordena subbeats por tempo
        resolved_subbeats.sort(key=lambda x: x["time"])

        # Calcula static hold máximo nesta cena
        holds = []
        for k in range(len(resolved_subbeats) - 1):
            hold = resolved_subbeats[k + 1]["time"] - resolved_subbeats[k]["time"]
            holds.append(hold)
        if resolved_subbeats:
            end_hold = s_end - resolved_subbeats[-1]["time"]
            holds.append(end_hold)
        max_hold = round(max(holds) if holds else s_duration, 3)

        resolved_scenes.append(
            {
                "scene_id": sdef["scene_id"],
                "beat_ids": sdef["beat_ids"],
                "start": round(s_start, 4),
                "end": round(s_end, 4),
                "duration": s_duration,
                "composition": sdef["composition"],
                "variant": {
                    "id": sdef["variant"],
                    "version": sdef["version"],
                    "status": sdef["status"],
                    "motion_status": sdef["motion_status"],
                },
                "first_useful_state_time": round(s_start + 0.25, 4),
                "visual_subbeats": resolved_subbeats,
                "max_static_hold_seconds": max_hold,
            }
        )

    manifest_v2 = {
        "schema_version": "2.0",
        "pilot_id": "capital_oculto_audiovisual_s001_s006_v2",
        "status": "PILOT_V2_STABILIZATION",
        "selection_mode": "PILOT_V2_CONTINUITY",
        "production_allowed": False,
        "episode_id": "CO-001",
        "canvas": CANVAS,
        "safe_area": SAFE_AREA,
        "motion_contract": "CO_MOTION_CONTRACT_V1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "audio": {
            "file": timing["audio_file"],
            "player_path": "audio/processed/narration_azure_antonio_v2.wav",
            "sha256": timing["audio_sha256"],
            "provider": timing["provider"],
            "voice": timing["voice"],
            "delivery": timing["delivery"],
            "duration_seconds": total_audio_duration,
            "render_origin_seconds": 0.0,
            "speech_overlap": timing["anti_atropelamento"]["speech_overlap"],
            "voice_density_warnings": timing["voice_density_warnings"],
        },
        "scenes": resolved_scenes,
    }

    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(
        json.dumps(manifest_v2, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Manifesto V2 gerado: {MANIFEST_FILE.relative_to(ROOT)}")
    for sc in resolved_scenes:
        print(
            f"  {sc['scene_id']}: {sc['start']:.2f}s–{sc['end']:.2f}s (dur={sc['duration']:.2f}s) | "
            f"{len(sc['visual_subbeats'])} sub-beats | max_hold={sc['max_static_hold_seconds']}s"
        )

    # Gera motion spec V2
    motion_spec_v2 = {
        "pilot_id": manifest_v2["pilot_id"],
        "pacing_contract": contract,
        "scenes": resolved_scenes,
    }
    MOTION_SPEC_FILE.write_text(
        json.dumps(motion_spec_v2, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
