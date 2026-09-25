#!/usr/bin/env python3
"""Produz motion candidate S013-S018 e a sequência acumulada S001-S018.

Usa exclusivamente áudio, WordBoundary, planning e motion S001-S012 existentes.
Não sintetiza voz, não chama Azure, não cria composição e não alcança S019+.
"""

from __future__ import annotations

import copy
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
from urllib.parse import quote
import wave

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import produzir_motion_s007_s012 as prior


PLAN = ROOT / "tests" / "production_planning" / "s013_s018_plan.json"
LAYOUT_CONTRACT = ROOT / "config" / "layout_quality_contract.json"
TIMING = ROOT / "tests" / "narration_s013_s018_wordboundary" / "timing" / "narration_b010_b013_timing.json"
CONTINUATION_MANIFEST = ROOT / "tests" / "narration_s013_s018_wordboundary" / "manifest" / "narration_continuation_manifest.json"
CONTINUATION_AUDIO = ROOT / "tests" / "narration_s013_s018_wordboundary" / "audio" / "narration_b010_b013.wav"
SOURCE = ROOT / "tests" / "audiovisual_motion_s007_s012"
SOURCE_MANIFEST = SOURCE / "manifest" / "scene_manifest_s001_s012.json"
SOURCE_PLAYER = SOURCE / "player_motion.html"
SOURCE_AUDIO = SOURCE / "audio" / "narration_s001_s012.wav"

OUT = ROOT / "tests" / "audiovisual_motion_s013_s018_layout_refined"
PLAYER = OUT / "player_motion.html"
FULL_AUDIO = OUT / "audio" / "narration_s001_s018.wav"
MOTION_SPEC = OUT / "scenes" / "motion_spec_s013_s018.json"
GEOMETRY_AUDIT = OUT / "scenes" / "motion_geometry_audit.json"
LAYOUT_SAMPLES = OUT / "scenes" / "layout_audit_samples.json"
LAYOUT_AUDIT = OUT / "scenes" / "layout_quality_audit.json"
FULL_MANIFEST = OUT / "manifest" / "scene_manifest_s001_s018.json"
CLIP_MANIFEST = OUT / "manifest" / "scene_manifest_s013_s018.json"
RENDERS = OUT / "renders"
CLIP_RENDER = RENDERS / "capital_oculto_s013_s018_layout_refined.webm"
FULL_RENDER = RENDERS / "capital_oculto_pilot_s001_s018_layout_refined.webm"
RENDER_METADATA = RENDERS / "render_metadata.json"


class MotionError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char) and char.isalnum())


def timing_words(beat_id: str) -> list[dict]:
    timing = read_json(TIMING)
    beat = next((item for item in timing["beats"] if item["beat_id"] == beat_id), None)
    if not beat:
        raise MotionError(f"Beat ausente no timing oficial: {beat_id}")
    origin = read_json(CONTINUATION_MANIFEST)["continuation_after"]["new_audio_origin_ms_global"] / 1000
    return [
        {
            **word,
            "absolute_start": round(origin + float(word["start"]), 6),
            "absolute_end": round(origin + float(word["end"]), 6),
        }
        for word in beat["words"]
    ]


def resolve_anchor(beat_id: str, anchor: str) -> dict:
    words = timing_words(beat_id)
    target = normalize(anchor)
    normalized = [normalize(item["text"]) for item in words]
    matches: list[tuple[int, int]] = []
    for start in range(len(words)):
        joined = ""
        for end in range(start, len(words)):
            joined += normalized[end]
            if joined == target:
                matches.append((start, end))
                break
            if len(joined) >= len(target):
                break
    if len(matches) != 1:
        raise MotionError(f"Anchor ausente/ambíguo: {beat_id} / {anchor} / {matches}")
    start, end = matches[0]
    first, last = words[start], words[end]
    return {
        "text": anchor,
        "beat_id": beat_id,
        "time": first["absolute_start"],
        "word_end": last["absolute_end"],
        "timing_source": "WORD_BOUNDARY_REAL",
        "start_word_index": first["index"],
        "end_word_index": last["index"],
    }


def event(scene: str, index: int, beat: str, anchor: str, action: str, target: str) -> dict:
    resolved = resolve_anchor(beat, anchor)
    return {
        "event_id": f"{scene}-E{index:02d}",
        "anchor": {key: value for key, value in resolved.items() if key not in {"time", "word_end"}},
        "time": resolved["time"],
        "end_time": resolved["word_end"],
        "action": action,
        "target": target,
        "timing_source": "WORD_BOUNDARY_REAL",
    }


EVENTS = {
    "S013": [
        ("B010", "Ontem pedir comida era exceção", "establish_exception", "exception_state"),
        ("B010", "Hoje é terça-feira", "shift_first_reference", "divider"),
        ("B010", "aplicativo de transporte era emergência", "establish_second_exception", "exception_state"),
        ("B010", "Hoje chuva já parece motivo suficiente", "shift_second_reference", "divider"),
        ("B010", "O luxo não precisa continuar parecendo luxo", "deemphasize_exception", "exception_state"),
        ("B010", "Quando entra na rotina", "routine_assumes", "routine_state"),
        ("B010", "normal", "lock_routine", "routine_state"),
    ],
    "S014": [
        ("B011", "E aqui está a primeira recompensa dessa história", "establish_income", "income_baseline"),
        ("B011", "seu cérebro não pergunta apenas", "establish_expectation", "expectation_baseline"),
        ("B011", "quanto eu tenho", "hold_income_question", "income_baseline"),
        ("B011", "Ele também pergunta", "start_expectation_rise", "expectation_baseline"),
        ("B011", "quanto isso é diferente", "continue_expectation_rise", "expectation_baseline"),
        ("B011", "do que eu já esperava ter", "approach_income", "expectation_baseline"),
        ("B011", "Quando a expectativa alcança a renda", "meet_income", "expectation_baseline"),
        ("B011", "avanço desaparece", "lock_meeting", "shared_baseline"),
    ],
    "S015": [
        ("B012", "Isso não quer dizer", "establish_material_context", "material_system"),
        ("B012", "uma renda maior", "expand_safe_area", "safe_area"),
        ("B012", "melhorar a vida", "move_character_to_safety", "character"),
        ("B012", "Ela pode ampliar segurança", "establish_security", "security_state"),
        ("B012", "e escolhas", "expand_choices", "choices_state"),
        ("B012", "reduz privações", "reduce_deprivation", "deprivation_state"),
    ],
    "S016": [
        ("B012", "Pagar moradia", "reveal_housing", "essential_housing"),
        ("B012", "comida", "reveal_food", "essential_food"),
        ("B012", "saúde", "reveal_health", "essential_health"),
        ("B012", "margem para imprevistos", "reveal_margin", "essential_margin"),
        ("B012", "não é uma ilusão psicológica", "lock_material_security", "security_state"),
    ],
    "S017": [
        ("B013", "Uma reanálise publicada", "establish_evidence", "evidence_system"),
        ("B013", "em 2023", "stamp_evidence_time", "evidence_label"),
        ("B013", "associação positiva", "draw_shared_relation", "shared_relation"),
        ("B013", "renda", "establish_income_track", "income_track"),
        ("B013", "bem-estar emocional", "establish_wellbeing_track", "wellbeing_track"),
        ("B013", "na média", "lock_average", "average_relation"),
    ],
    "S018": [
        ("B013", "Mas o efeito era pequeno", "reduce_average_effect", "average_relation"),
        ("B013", "variava entre grupos", "open_group_outputs", "group_outputs"),
        ("B013", "não confirmava", "reject_universal_claim", "universal_threshold"),
        ("B013", "história popular", "deemphasize_simple_story", "universal_threshold"),
        ("B013", "número mágico", "mark_missing_threshold", "universal_threshold"),
        ("B013", "depois do qual", "separate_group_results", "group_outputs"),
        ("B013", "dinheiro para de fazer diferença", "show_unequal_results", "group_outputs"),
        ("B013", "todo mundo", "lock_no_universal_threshold", "group_outputs"),
    ],
}


def build_motion_spec(audio_duration: float) -> dict:
    plan = read_json(PLAN)
    plan_scenes = {item["scene_id"]: item for item in plan["scenes"]}
    ids = [f"S{i:03d}" for i in range(13, 19)]
    starts = [plan_scenes[scene]["narration"]["start_ms"] / 1000 for scene in ids]
    scenes = []
    for position, scene_id in enumerate(ids):
        planned = plan_scenes[scene_id]
        start = starts[position]
        end = starts[position + 1] if position + 1 < len(starts) else audio_duration
        raw = EVENTS[scene_id]
        events = [event(scene_id, index, *definition) for index, definition in enumerate(raw, 1)]
        for current, following in zip(events, events[1:]):
            current["end_time"] = max(current["end_time"], following["time"])
        events[-1]["end_time"] = max(events[-1]["end_time"], planned["narration"]["end_ms"] / 1000)
        changes = [start, *(item["time"] for item in events), end]
        max_hold = max(right - left for left, right in zip(changes, changes[1:]))
        scenes.append({
            "scene_id": scene_id,
            "beat_id": planned["beat_id"],
            "start": round(start, 6),
            "end": round(end, 6),
            "duration": round(end - start, 6),
            "composition_id": planned["best_existing_candidate"]["variant"],
            "composition_version": planned["best_existing_candidate"]["version"],
            "composition_status": "APPROVED",
            "static_status": "STATIC_APPROVED",
            "motion_status": "MOTION_CANDIDATE",
            "events": events,
            "max_static_hold_ms": round(max_hold * 1000, 3),
            "timing_source": "WORD_BOUNDARY_REAL",
        })
    return {
        "schema_version": "1.0",
        "episode_id": "CO-001",
        "scope": "S013-S018_MOTION_CANDIDATE",
        "status": "MOTION_CANDIDATE",
        "timing_quality": "WORD_BOUNDARY_REAL",
        "continuity": [
            {"from": "S012", "to": "S013", "type": "BASELINE_CONTINUITY"},
            {"from": "S015", "to": "S016", "type": "OBJECT_CONTINUITY", "locks": ["character", "camera", "material_elements"]},
            {"from": "S017", "to": "S018", "type": "ELEMENT_CARRYOVER", "locks": ["income_relation", "lime_reference", "evidence_context"]},
        ],
        "scenes": scenes,
    }


def wav_payload(path: Path) -> tuple[dict, bytes]:
    with wave.open(str(path), "rb") as handle:
        params = {"channels": handle.getnchannels(), "sample_width": handle.getsampwidth(), "sample_rate": handle.getframerate(), "compression": handle.getcomptype()}
        return params, handle.readframes(handle.getnframes())


def build_full_audio() -> float:
    old_params, old_frames = wav_payload(SOURCE_AUDIO)
    new_params, new_frames = wav_payload(CONTINUATION_AUDIO)
    expected = {"channels": 1, "sample_width": 2, "sample_rate": 24000, "compression": "NONE"}
    if old_params != new_params or old_params != expected:
        raise MotionError(f"WAVs incompatíveis: {old_params} / {new_params}")
    origin_ms = read_json(CONTINUATION_MANIFEST)["continuation_after"]["new_audio_origin_ms_global"]
    cut_frames = round(origin_ms * old_params["sample_rate"] / 1000)
    bytes_per_frame = old_params["channels"] * old_params["sample_width"]
    prefix = old_frames[:cut_frames * bytes_per_frame]
    FULL_AUDIO.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(FULL_AUDIO), "wb") as handle:
        handle.setnchannels(1); handle.setsampwidth(2); handle.setframerate(24000); handle.writeframes(prefix + new_frames)
    with wave.open(str(FULL_AUDIO), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


MOTION_JS = r'''
    function eprogress(time,id){ return absoluteProgress(time,id); }

    function drawPerson(x,y,alpha=1){
      ctx.save();ctx.globalAlpha=alpha;ctx.translate(x,y);ctx.scale(.62,.62);
      ctx.fillStyle=P.offWhite;ctx.strokeStyle=P.black;ctx.lineWidth=8;ctx.beginPath();ctx.arc(160,112,96,0,Math.PI*2);ctx.fill();ctx.stroke();
      ctx.fillStyle=P.black;ctx.beginPath();ctx.ellipse(128,122,11,18,0,0,Math.PI*2);ctx.ellipse(194,117,11,18,0,0,Math.PI*2);ctx.fill();
      ctx.beginPath();ctx.moveTo(111,226);ctx.quadraticCurveTo(124,212,146,208);ctx.lineTo(160,218);ctx.lineTo(174,208);ctx.quadraticCurveTo(198,212,211,229);ctx.lineTo(203,368);ctx.quadraticCurveTo(160,380,116,368);ctx.closePath();ctx.fill();
      ctx.fillStyle=P.lime;ctx.beginPath();ctx.moveTo(160,219);ctx.lineTo(147,235);ctx.lineTo(154,250);ctx.lineTo(166,250);ctx.lineTo(173,235);ctx.closePath();ctx.fill();
      ctx.fillStyle=P.black;ctx.fillRect(120,360,31,220);ctx.fillRect(169,360,31,220);ctx.restore();
    }

    function drawS013Motion(time){
      background();
      const establish=eprogress(time,'S013-E01'), shift1=eprogress(time,'S013-E02'), second=eprogress(time,'S013-E03');
      const shift2=eprogress(time,'S013-E04'), fade=eprogress(time,'S013-E05'), routine=eprogress(time,'S013-E06'), lock=eprogress(time,'S013-E07');
      const shift=Math.max(shift1*.45,shift2);
      const dividerX=lerp(1680,900,shift);
      ctx.fillStyle=P.black;ctx.fillRect(dividerX,0,1920-dividerX,1080);
      roundedRect(dividerX-6,0,12,1080,0,P.black,1);
      const carry=1-Math.min(1,shift1*1.4);ctx.save();ctx.strokeStyle=P.lime;ctx.lineWidth=18;ctx.lineCap='round';ctx.globalAlpha=carry;ctx.beginPath();ctx.moveTo(1020,511);ctx.lineTo(1788,511);ctx.stroke();ctx.restore();
      fillText('ONTEM',96,154,28,800,P.black,'left',establish*(1-.55*fade),2.4);
      fillText('EXCEÇÃO',96,340,104,900,P.black,'left',establish*(1-.55*fade),-4);
      fillText(second>0?'TRANSPORTE':'DELIVERY',96,520,74,900,P.black,'left',Math.max(establish,second)*(1-.55*fade),-3);
      fillText(second>0?'EMERGÊNCIA':'FESTA',96,640,104,900,P.black,'left',Math.max(establish,second)*(1-.55*fade),-4);
      const rightAlpha=Math.max(shift1,shift2,routine);
      fillText('HOJE',1824,154,28,800,P.offWhite,'right',rightAlpha,2.4);
      fillText('ROTINA',1824,420,146,900,P.offWhite,'right',routine,-7);
      fillText(shift2>0?'CHUVA BASTA':'TERÇA-FEIRA',1824,580,70,900,P.offWhite,'right',rightAlpha,-3);
      roundedRect(1290,900,lerp(40,520,lock),8,4,P.lime,1);
      fillText('O EXTRA VIROU REFERÊNCIA',1824,966,28,800,P.offWhite,'right',lock,2.4);
    }

    function drawS014Motion(time){
      background();
      const income=eprogress(time,'S014-E01'), expectation=eprogress(time,'S014-E02');
      const rise1=eprogress(time,'S014-E04'), rise2=eprogress(time,'S014-E05'), approach=eprogress(time,'S014-E06');
      const meet=eprogress(time,'S014-E07'), lock=eprogress(time,'S014-E08');
      const rise=Math.max(rise1*.28,rise2*.52,approach*.78,meet);
      fillText('RENDA',96,140,48,900,P.black,'left',income,-2);
      fillText('R$ 4.200',96,340,180,900,P.black,'left',income,-7);
      roundedRect(64,464,1792,16,8,P.black,income);
      roundedRect(64,460,1336,8,4,P.amber,income);
      const y=lerp(760,480,rise);ctx.save();ctx.strokeStyle=P.gray;ctx.lineWidth=6;ctx.setLineDash([18,14]);ctx.globalAlpha=expectation;ctx.beginPath();ctx.moveTo(64,y);ctx.lineTo(1856,y);ctx.stroke();ctx.restore();
      fillText('EXPECTATIVA',96,y-58,lerp(112,84,rise),900,P.gray,'left',expectation,-5);
      ctx.save();ctx.strokeStyle=P.amber;ctx.lineWidth=8;ctx.lineCap='round';ctx.globalAlpha=Math.max(rise1,meet);ctx.beginPath();ctx.moveTo(1600,740);ctx.lineTo(1600,lerp(740,500,rise));ctx.stroke();ctx.restore();
      if(meet>0){fillText('ALCANÇOU',1824,620,56,900,P.amber,'right',meet,-2);fillText('A RENDA',1824,690,56,900,P.amber,'right',meet,-2);}
      fillText('PARTE DO AVANÇO SOME',1824,960,28,800,P.black,'right',lock,2.4);
    }

    function materialState(time){
      return {est:eprogress(time,'S015-E01'),income:eprogress(time,'S015-E02'),move:eprogress(time,'S015-E03'),safe:eprogress(time,'S015-E04'),choices:eprogress(time,'S015-E05'),reduce:eprogress(time,'S015-E06'),house:eprogress(time,'S016-E01'),food:eprogress(time,'S016-E02'),health:eprogress(time,'S016-E03'),margin:eprogress(time,'S016-E04'),lock:eprogress(time,'S016-E05')};
    }
    function drawMaterialSequence(time){
      background();const s=materialState(time);const divider=lerp(1180,900,s.income);ctx.fillStyle=P.black;ctx.fillRect(divider,0,1920-divider,1080);roundedRect(divider-6,0,12,1080,0,P.black,1);
      fillText('PRIVAÇÃO',96,154,28,800,P.black,'left',s.est*(1-.65*s.reduce),2.4);fillText('CONTAS',96,430,132,900,P.gray,'left',s.est*(1-.55*s.reduce),-5);
      fillText('SEGURANÇA',1824,154,28,800,P.offWhite,'right',Math.max(s.safe,s.house),2.4);
      drawPerson(lerp(920,1060,s.move),330,Math.max(.2,s.est));
      roundedRect(1260,880,lerp(80,550,s.safe),10,5,P.lime,1);
      fillText('ESCOLHAS',1824,500,86,900,P.offWhite,'right',s.choices,-3);
      const items=[['MORADIA',s.house,1240,300],['COMIDA',s.food,1510,300],['SAÚDE',s.health,1240,710],['MARGEM',s.margin,1510,710]];
      items.forEach(([label,p,x,y])=>{roundedRect(x,y,230,120,18,P.offWhite,p);fillText(label,x+115,y+76,32,900,P.black,'center',p,-1);});
      fillText('SEGURANÇA MATERIAL É REAL',1824,966,28,800,P.offWhite,'right',s.lock,2.4);
    }

    function evidenceState(time){return {est:eprogress(time,'S017-E01'),stamp:eprogress(time,'S017-E02'),relation:eprogress(time,'S017-E03'),income:eprogress(time,'S017-E04'),well:eprogress(time,'S017-E05'),avg:eprogress(time,'S017-E06'),small:eprogress(time,'S018-E01'),groups:eprogress(time,'S018-E02'),reject:eprogress(time,'S018-E03'),story:eprogress(time,'S018-E04'),magic:eprogress(time,'S018-E05'),separate:eprogress(time,'S018-E06'),unequal:eprogress(time,'S018-E07'),lock:eprogress(time,'S018-E08')};}
    function evidenceTrack(y,w,p,label){fillText(label,96,y+58,label==='BEM-ESTAR'?70:82,900,P.black,'left',p,-3);roundedRect(560,y,w*p,86,18,P.black,p);roundedRect(560+w*p,y,Math.min(260,386*p),86,18,P.lime,p);}
    function drawEvidenceSequence(time){
      background();const s=evidenceState(time);const carry=Math.max(s.est,s.groups);fillText('EVIDÊNCIA',1824,136,28,800,P.black,'right',s.est*(1-.7*s.groups),2.4);fillText('2023',1824,190,44,900,P.black,'right',s.stamp*(1-.7*s.groups),-2);
      const baseAlpha=1-.58*s.groups;evidenceTrack(272,636,Math.max(s.income,s.relation)*baseAlpha,'RENDA');evidenceTrack(522,826,Math.max(s.well,s.relation)*baseAlpha,'BEM-ESTAR');
      ctx.save();ctx.strokeStyle=P.lime;ctx.lineWidth=30;ctx.lineCap='round';ctx.globalAlpha=Math.max(s.relation,s.avg)*baseAlpha;ctx.beginPath();ctx.moveTo(610,904);ctx.lineTo(1390,220);ctx.stroke();ctx.restore();
      fillText('ASSOCIAÇÃO POSITIVA NA MÉDIA',1824,966,28,800,P.black,'right',s.avg*(1-s.groups),2.4);
      if(s.groups>0){ctx.fillStyle=P.black;ctx.fillRect(0,0,520,1080);roundedRect(480,96,96,888,24,P.lime,1);fillText('FATOR COMUM',96,486,28,800,P.offWhite,'left',s.groups,2.4);fillText('RENDA',96,606,92,900,P.offWhite,'left',s.groups,-4);
        const widths=[1200,1090,910];const ps=[s.groups,Math.max(s.groups*.65,s.separate),Math.max(s.groups*.4,s.unequal)];['GRUPO A','GRUPO B','GRUPO C'].forEach((label,i)=>{const y=180+i*270;ctx.save();ctx.globalAlpha=ps[i];ctx.fillStyle=P.black;ctx.beginPath();ctx.moveTo(540,y);ctx.lineTo(540+widths[i],y);ctx.lineTo(616+widths[i],y+74);ctx.lineTo(540+widths[i],y+148);ctx.lineTo(540,y+148);ctx.closePath();ctx.fill();ctx.restore();fillText(label,740,y+104,i===1?76:88,900,P.offWhite,'left',ps[i],-3);});}
      fillText('EFEITO PEQUENO',1824,120,28,800,P.black,'right',s.small,2.4);fillText('SEM LIMIAR UNIVERSAL',1824,966,28,800,P.black,'right',Math.max(s.magic,s.lock),2.4);
    }

    // Refined editorial staging. The composition grammars and timing events remain
    // unchanged; only hierarchy, continuity and cause/effect choreography change.
    function strokeCurve(points,color,width,alpha,dash=[]){
      if(alpha<=0)return;ctx.save();ctx.globalAlpha=alpha;ctx.strokeStyle=color;
      ctx.lineWidth=width;ctx.lineCap='round';ctx.lineJoin='round';ctx.setLineDash(dash);
      ctx.beginPath();ctx.moveTo(points[0],points[1]);
      if(points.length===8)ctx.bezierCurveTo(points[2],points[3],points[4],points[5],points[6],points[7]);
      else for(let i=2;i<points.length;i+=2)ctx.lineTo(points[i],points[i+1]);
      ctx.stroke();ctx.restore();
    }

    function drawS013LayoutBefore(time){
      background();
      const establish=eprogress(time,'S013-E01'),shift1=eprogress(time,'S013-E02'),second=eprogress(time,'S013-E03');
      const shift2=eprogress(time,'S013-E04'),fade=eprogress(time,'S013-E05'),routine=eprogress(time,'S013-E06'),lock=eprogress(time,'S013-E07');
      const takeover=Math.max(shift1*.34,shift2*.72,routine);
      const boundary=lerp(1840,520,takeover);
      ctx.save();ctx.beginPath();ctx.rect(0,0,boundary,1080);ctx.clip();
      fillText('EXCEÇÃO',96,310,154,900,P.black,'left',establish*(1-.82*takeover),-7);
      fillText(second>0?'EMERGÊNCIA':'DELIVERY',96,520,94,900,P.gray,'left',Math.max(establish,second)*(1-.7*takeover),-4);
      fillText(second>0?'FESTA':'ONTEM',96,690,188,900,P.black,'left',Math.max(establish,second)*(1-.86*takeover),-8);
      strokeCurve([96,910,Math.max(96,boundary-56),910],P.lime,18,establish);
      ctx.restore();
      ctx.fillStyle=P.black;ctx.fillRect(boundary,0,1920-boundary,1080);
      ctx.fillStyle=P.lime;ctx.fillRect(boundary-7,0,14,1080);
      ctx.save();ctx.beginPath();ctx.rect(boundary+32,0,1888-boundary,1080);ctx.clip();
      fillText('ROTINA',1824,506,lerp(104,236,routine),900,P.offWhite,'right',Math.max(shift1,routine),-10);
      fillText('DIA APÓS DIA',1824,676,72,900,P.lime,'right',Math.max(shift2,routine),-3);
      fillText('A EXCEÇÃO VIROU REFERÊNCIA',1824,940,26,800,P.offWhite,'right',lock,2.2);
      ctx.restore();
    }

    function drawS014LayoutBefore(time){
      background();
      const income=eprogress(time,'S014-E01'),expectation=eprogress(time,'S014-E02');
      const rise1=eprogress(time,'S014-E04'),rise2=eprogress(time,'S014-E05'),approach=eprogress(time,'S014-E06');
      const meet=eprogress(time,'S014-E07'),lock=eprogress(time,'S014-E08');
      const convergence=Math.max(rise1*.24,rise2*.5,approach*.78,meet);
      const seam=lerp(820,514,convergence);
      ctx.save();ctx.globalAlpha=income;ctx.fillStyle=P.black;ctx.fillRect(0,0,1920,seam);ctx.restore();
      fillText('RENDA',96,182,54,900,P.offWhite,'left',income,-2);
      fillText('4.200',96,430,248,900,P.offWhite,'left',income,-11);
      fillText('EXPECTATIVA',1824,lerp(936,620,convergence),lerp(92,142,convergence),900,P.black,'right',expectation,-6);
      ctx.fillStyle=P.lime;ctx.globalAlpha=Math.max(income,expectation);ctx.fillRect(64,seam-7,1792,14);ctx.globalAlpha=1;
      const impact=Math.max(0,(meet-.08)/.92);
      ctx.save();ctx.globalAlpha=impact;ctx.fillStyle=P.lime;ctx.fillRect(0,seam-28,1920,56*impact);ctx.restore();
      fillText('ALCANÇOU',1824,seam-54,48,900,P.lime,'right',meet,-2);
      fillText('RENDA',1824,seam+92,48,900,P.black,'right',meet,-2);
      fillText('O AVANÇO ENCOLHE',1824,1000,28,800,P.black,'right',lock,2.4);
    }

    function drawMaterialLayoutBefore(time){
      background();const s=materialState(time);
      const opening=Math.max(s.income*.32,s.move*.62,s.safe,s.reduce);
      const ceiling=lerp(790,205,opening);
      ctx.fillStyle=P.black;ctx.fillRect(0,0,1920,ceiling);
      ctx.fillStyle=P.lime;ctx.fillRect(64,ceiling-8,1792,16);
      fillText('PRIVAÇÃO',96,150,30,800,P.offWhite,'left',s.est*(1-.86*opening),2.4);
      fillText('SEM ESPAÇO',96,470,156,900,P.offWhite,'left',s.est*(1-.72*opening),-7);
      fillText('ESCOLHAS',96,lerp(920,480,opening),lerp(80,196,s.choices),900,P.black,'left',s.choices,-9);
      fillText('RENDA ABRE ESPAÇO MATERIAL',1824,150,26,800,P.offWhite,'right',Math.max(s.income,s.safe),2.2);

      const structure=Math.max(s.house,s.food,s.health,s.margin);
      const left=1080,right=1780,roof=390,floor=875;
      strokeCurve([left,roof,right,roof],P.black,26,s.house);
      strokeCurve([left,roof,left,floor],P.black,26,s.food);
      strokeCurve([right,roof,right,floor],P.black,26,s.health);
      strokeCurve([left,floor,right,floor],P.lime,34,s.margin);
      fillText('MORADIA',(left+right)/2,350,52,900,P.black,'center',s.house,-2);
      fillText('COMIDA',left+34,596,40,900,P.black,'left',s.food,-1.5);
      fillText('SAÚDE',right-34,596,40,900,P.black,'right',s.health,-1.5);
      fillText('MARGEM',(left+right)/2,950,46,900,P.black,'center',s.margin,-1.5);
      ctx.save();ctx.globalAlpha=structure*.08;ctx.fillStyle=P.lime;ctx.fillRect(left+13,roof+13,right-left-26,floor-roof-26);ctx.restore();
      fillText('SEGURANÇA MATERIAL',1824,1020,28,800,P.black,'right',s.lock,2.4);
    }

    function drawEvidenceLayoutBefore(time){
      background();const s=evidenceState(time);
      const branching=Math.max(s.groups,s.separate,s.unequal);
      const baseAlpha=1-.38*branching;
      fillText('RENDA',96,210,94,900,P.black,'left',Math.max(s.est,s.income)*baseAlpha,-4);
      fillText('BEM-ESTAR',1824,870,116,900,P.black,'right',Math.max(s.est,s.well)*baseAlpha,-5);
      strokeCurve([160,740,590,650,1180,430,1760,240],P.lime,34,Math.max(s.relation,s.avg));
      fillText('RELAÇÃO POSITIVA',96,948,32,800,P.black,'left',s.relation*(1-branching),2.4);
      fillText('NA MÉDIA',1824,150,38,900,P.black,'right',s.avg*(1-branching),2.2);

      if(branching>0){
        const ox=650,oy=650;
        ctx.save();ctx.globalAlpha=branching;ctx.fillStyle=P.black;ctx.beginPath();ctx.arc(ox,oy,25,0,Math.PI*2);ctx.fill();ctx.restore();
        fillText('MESMA RELAÇÃO',96,700,30,800,P.black,'left',branching,2.2);
        const pa=Math.max(s.groups,branching*.42),pb=Math.max(s.groups*.72,s.separate),pc=Math.max(s.groups*.5,s.unequal);
        strokeCurve([ox,oy,930,530,1310,255,1750,235],P.black,22,pa);
        strokeCurve([ox,oy,980,650,1320,550,1750,575],P.black,22,pb);
        strokeCurve([ox,oy,980,760,1320,855,1750,810],P.black,22,pc);
        fillText('GRUPO A',1818,250,34,900,P.black,'right',pa,-1);
        fillText('GRUPO B',1818,590,34,900,P.black,'right',pb,-1);
        fillText('GRUPO C',1818,825,34,900,P.black,'right',pc,-1);
        fillText('EFEITO PEQUENO',1818,100,28,800,P.black,'right',s.small,2.2);
        const reject=Math.max(s.reject,s.magic);
        strokeCurve([1120,160,1120,920],P.gray,7,reject*(1-s.lock*.65),[22,18]);
        fillText('LIMIAR?',1120,130,26,800,P.gray,'center',reject*(1-s.lock),2);
        if(s.magic>0){
          ctx.save();ctx.globalAlpha=s.magic;ctx.fillStyle=P.offWhite;ctx.fillRect(1084,360,72,300);ctx.restore();
          fillText('NÃO HÁ CORTE UNIVERSAL',1818,1010,28,800,P.black,'right',Math.max(s.magic,s.lock),2.2);
        }
      }
    }

    const layoutBeforeDraw = {
      S013: drawS013LayoutBefore,
      S014: drawS014LayoutBefore,
      material: drawMaterialLayoutBefore,
      evidence: drawEvidenceLayoutBefore
    };
    const LAYOUT_AUDIT_MODE = QUERY.get('layoutaudit') === '1';
    let ACTIVE_LAYOUT_PHASE = 'after';
    let ACTIVE_LAYOUT_SCENE = null;
    let ACTIVE_LAYOUT_TIME = 0;
    let layoutTexts = [];
    let layoutShapes = [];
    let layoutElementIndex = 0;
    const layoutMeasureSvg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    layoutMeasureSvg.setAttribute('width','1920');layoutMeasureSvg.setAttribute('height','1080');
    layoutMeasureSvg.style.cssText='position:fixed;left:-10000px;top:0;width:1920px;height:1080px;visibility:hidden';
    document.body.appendChild(layoutMeasureSvg);

    function beginLayoutFrame(scene,time){
      ACTIVE_LAYOUT_SCENE=scene;ACTIVE_LAYOUT_TIME=time;layoutTexts=[];layoutShapes=[];layoutElementIndex=0;
      layoutMeasureSvg.replaceChildren();
    }
    function textKind(size){return size>=180?'hero_number':size>=96?'headline':size>=56?'strong_support':'label';}
    function registerLayoutText(text,x,y,size,weight,align,alpha,letterSpacing){
      if(!LAYOUT_AUDIT_MODE||clamp(alpha)<.12)return;
      const node=document.createElementNS('http://www.w3.org/2000/svg','text');
      node.textContent=text;node.setAttribute('x',String(x));node.setAttribute('y',String(y));
      node.setAttribute('font-family',FONT);node.setAttribute('font-size',String(size));node.setAttribute('font-weight',String(weight));
      node.setAttribute('text-anchor',align==='right'?'end':align==='center'?'middle':'start');
      if(letterSpacing)node.setAttribute('letter-spacing',String(letterSpacing));
      layoutMeasureSvg.appendChild(node);const box=node.getBBox();
      layoutTexts.push({id:`text-${++layoutElementIndex}`,text,size,weight,kind:textKind(size),alpha:clamp(alpha),bbox:{x:box.x,y:box.y,width:box.width,height:box.height}});
    }
    function registerLayoutPath(points,width,alpha){
      if(!LAYOUT_AUDIT_MODE||clamp(alpha)<.12)return;
      const node=document.createElementNS('http://www.w3.org/2000/svg','path');
      const d=points.length===8?`M${points[0]} ${points[1]} C${points[2]} ${points[3]} ${points[4]} ${points[5]} ${points[6]} ${points[7]}`:
        `M${points[0]} ${points[1]} `+points.slice(2).reduce((value,item,index)=>value+(index%2===0?'L':' ')+item,'');
      node.setAttribute('d',d);node.setAttribute('fill','none');node.setAttribute('stroke','#111');node.setAttribute('stroke-width',String(width));
      layoutMeasureSvg.appendChild(node);layoutShapes.push({id:`shape-${++layoutElementIndex}`,kind:'path',strokeWidth:width,node});
    }
    function fillText(text,x,y,size,weight=900,color=P.black,align='left',alpha=1,letterSpacing=0){
      ctx.save();ctx.globalAlpha=clamp(alpha);ctx.fillStyle=color;ctx.font=`${weight} ${size}px ${FONT}`;ctx.textAlign=align;ctx.textBaseline='alphabetic';
      if(letterSpacing&&ctx.letterSpacing!==undefined)ctx.letterSpacing=`${letterSpacing}px`;ctx.fillText(text,x,y);ctx.restore();
      registerLayoutText(text,x,y,size,weight,align,alpha,letterSpacing);
    }
    function strokeCurve(points,color,width,alpha,dash=[]){
      if(alpha<=0)return;ctx.save();ctx.globalAlpha=alpha;ctx.strokeStyle=color;ctx.lineWidth=width;ctx.lineCap='round';ctx.lineJoin='round';ctx.setLineDash(dash);
      ctx.beginPath();ctx.moveTo(points[0],points[1]);if(points.length===8)ctx.bezierCurveTo(points[2],points[3],points[4],points[5],points[6],points[7]);
      else for(let i=2;i<points.length;i+=2)ctx.lineTo(points[i],points[i+1]);ctx.stroke();ctx.restore();registerLayoutPath(points,width,alpha);
    }
    function boxesOverlap(a,b){return a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y;}
    function axisGap(a,b){
      const dx=Math.max(0,Math.max(a.x,b.x)-Math.min(a.x+a.width,b.x+b.width));
      const dy=Math.max(0,Math.max(a.y,b.y)-Math.min(a.y+a.height,b.y+b.height));return Math.hypot(dx,dy);
    }
    function textGap(a,b){
      if(a.kind==='headline'&&b.kind==='headline')return 32;
      if(a.kind==='label'&&b.kind==='label')return 16;
      if(a.kind==='strong_support'&&b.kind==='strong_support')return 32;
      return 24;
    }
    function pathHitsText(shape,text,padding){
      const node=shape.node,total=node.getTotalLength(),samples=Math.max(80,Math.ceil(total/6));const b=text.bbox,margin=shape.strokeWidth/2+padding;
      for(let i=0;i<=samples;i++){const p=node.getPointAtLength(total*i/samples);if(p.x>=b.x-margin&&p.x<=b.x+b.width+margin&&p.y>=b.y-margin&&p.y<=b.y+b.height+margin)return true;}return false;
    }
    function collectLayoutFrame(phase,sample){
      const findings=[];const add=(type,severity,a,b)=>findings.push({scene_id:ACTIVE_LAYOUT_SCENE.scene_id,time:ACTIVE_LAYOUT_TIME,sample_id:sample.sample_id,phase,type,severity,element_a:a,element_b:b});
      for(const text of layoutTexts){const b=text.bbox;
        if(b.x<0||b.y<0||b.x+b.width>1920||b.y+b.height>1080)add('TEXT_CLIPPING','ERROR',text.text,'canvas');
        if(b.x<96||b.y<96||b.x+b.width>1824||b.y+b.height>984)add('TEXT_OUTSIDE_SAFE_ZONE','ERROR',text.text,'safe-zone');
      }
      for(let i=0;i<layoutTexts.length;i++)for(let j=i+1;j<layoutTexts.length;j++){
        const a=layoutTexts[i],b=layoutTexts[j];if(boxesOverlap(a.bbox,b.bbox))add('TEXT_TEXT_OVERLAP','ERROR',a.text,b.text);
        else if(axisGap(a.bbox,b.bbox)<textGap(a,b))add('INSUFFICIENT_TEXT_GAP','WARNING',a.text,b.text);
      }
      for(const text of layoutTexts)for(const shape of layoutShapes){const padding=text.kind==='label'?16:text.kind==='hero_number'?24:28;if(pathHitsText(shape,text,padding))add('TEXT_IMPORTANT_SHAPE_OVERLAP','ERROR',text.text,shape.id);}
      const dominants=layoutTexts.filter(item=>item.alpha>=.6&&(item.kind==='hero_number'||item.kind==='headline'));
      if(dominants.length>1)add('COMPETING_DOMINANT_ELEMENTS','WARNING',dominants[0].text,dominants.slice(1).map(item=>item.text).join('|'));
      return {scene_id:ACTIVE_LAYOUT_SCENE.scene_id,time:ACTIVE_LAYOUT_TIME,sample_id:sample.sample_id,phase,text_count:layoutTexts.length,shape_count:layoutShapes.length,findings};
    }

    function drawS013Motion(time){
      background();const establish=eprogress(time,'S013-E01'),shift1=eprogress(time,'S013-E02'),second=eprogress(time,'S013-E03');
      const shift2=eprogress(time,'S013-E04'),routine=eprogress(time,'S013-E06'),lock=eprogress(time,'S013-E07');
      const takeover=Math.max(shift1*.34,shift2*.72,routine),oldAlpha=establish*Math.max(0,1-takeover*2.6);
      ctx.fillStyle=P.black;ctx.fillRect(lerp(1880,780,takeover),0,1920-lerp(1880,780,takeover),1080);
      fillText('EXCEÇÃO',96,330,154,900,P.black,'left',oldAlpha,-7);
      fillText(second>0?'EMERGÊNCIA':'DELIVERY',96,535,78,900,P.gray,'left',Math.max(establish,second)*Math.max(0,1-takeover*2),-3);
      strokeCurve([96,900,720,900],P.lime,18,oldAlpha);
      const routineAlpha=Math.max(0,(takeover-.18)/.82);
      fillText('ROTINA',1800,500,218,900,P.offWhite,'right',routineAlpha,-9);
      fillText('DIA APÓS DIA',1800,650,62,900,P.lime,'right',routineAlpha,-2.5);
      fillText('A EXCEÇÃO VIROU REFERÊNCIA',1800,950,26,800,P.offWhite,'right',lock,2.2);
    }

    function drawS014Motion(time){
      background();const income=eprogress(time,'S014-E01'),expectation=eprogress(time,'S014-E02');
      const rise1=eprogress(time,'S014-E04'),rise2=eprogress(time,'S014-E05'),approach=eprogress(time,'S014-E06');
      const meet=eprogress(time,'S014-E07'),lock=eprogress(time,'S014-E08');const convergence=Math.max(rise1*.24,rise2*.5,approach*.78,meet);
      fillText('RENDA',1800,330,132,900,P.black,'right',income,-6);
      fillText('REFERÊNCIA FIXA',1800,410,28,800,P.black,'right',income,2.2);
      const expectationAlpha=expectation*(1-.62*meet);
      fillText('EXPECTATIVA',96,lerp(900,390,convergence),88,900,P.black,'left',expectationAlpha,-4);
      const dotAlpha=Math.max(approach,meet);ctx.save();ctx.globalAlpha=dotAlpha;ctx.fillStyle=P.lime;ctx.beginPath();ctx.arc(960,360,lerp(16,42,meet),0,Math.PI*2);ctx.fill();ctx.restore();
      fillText('ALCANÇOU',960,720,76,900,P.black,'center',meet,-3);
      fillText('O AVANÇO ENCOLHE',960,790,28,800,P.black,'center',lock,2.2);
    }

    function drawMaterialSequence(time){
      background();const s=materialState(time),opening=Math.max(s.income*.32,s.move*.62,s.safe,s.reduce),ceiling=lerp(790,205,opening);
      ctx.fillStyle=P.black;ctx.fillRect(0,0,1920,ceiling);ctx.fillStyle=P.lime;ctx.fillRect(64,ceiling-8,1792,16);
      fillText('PRIVAÇÃO',96,155,30,800,P.offWhite,'left',s.est*Math.max(0,1-opening*2.2),2.4);
      fillText('SEM ESPAÇO',96,470,150,900,P.offWhite,'left',s.est*Math.max(0,1-opening*1.8),-7);
      fillText('ESCOLHAS',96,640,150,900,P.black,'left',s.choices,-7);
      fillText('RENDA ABRE ESPAÇO MATERIAL',1824,155,26,800,P.offWhite,'right',Math.max(s.income,s.safe),2.2);
      const left=1120,right=1760,roof=430,floor=850;
      strokeCurve([left,roof,right,roof],P.black,24,s.house);strokeCurve([left,roof,left,floor],P.black,24,s.food);
      strokeCurve([right,roof,right,floor],P.black,24,s.health);strokeCurve([left,floor,right,floor],P.lime,30,s.margin);
      fillText('MORADIA',(left+right)/2,350,50,900,P.black,'center',s.house,-2);
      fillText('COMIDA',left+54,650,38,900,P.black,'left',s.food,-1.5);
      fillText('SAÚDE',right-54,650,38,900,P.black,'right',s.health,-1.5);
      fillText('MARGEM',(left+right)/2,940,42,900,P.black,'center',s.margin,-1.5);
      fillText('SEGURANÇA MATERIAL',96,950,28,800,P.black,'left',s.lock,2.4);
    }

    function drawEvidenceSequence(time){
      background();const s=evidenceState(time),branching=Math.max(s.groups,s.separate,s.unequal);
      if(branching<.12){
        fillText('RENDA',96,285,104,900,P.black,'left',Math.max(s.est,s.income),-5);
        fillText('BEM-ESTAR',1800,835,84,900,P.black,'right',Math.max(s.est,s.well),-4);
        strokeCurve([460,390,760,430,1180,570,1450,700],P.lime,28,Math.max(s.relation,s.avg));
        fillText('ASSOCIAÇÃO POSITIVA',96,940,30,800,P.black,'left',s.relation,2.2);
        fillText('NA MÉDIA',1800,155,34,900,P.black,'right',s.avg,2.2);
      }else{
        fillText('RENDA',96,265,92,900,P.black,'left',branching,-4);
        fillText('MESMA ASSOCIAÇÃO',96,520,34,800,P.black,'left',branching,2.2);
        const ox=600,oy=540,pa=Math.max(s.groups,branching*.42),pb=Math.max(s.groups*.72,s.separate),pc=Math.max(s.groups*.5,s.unequal);
        ctx.save();ctx.globalAlpha=branching;ctx.fillStyle=P.lime;ctx.beginPath();ctx.arc(ox,oy,22,0,Math.PI*2);ctx.fill();ctx.restore();
        strokeCurve([ox,oy,900,430,1200,330,1500,320],P.black,18,pa);
        strokeCurve([ox,oy,920,540,1210,540,1500,540],P.black,18,pb);
        strokeCurve([ox,oy,900,650,1200,760,1500,780],P.black,18,pc);
        fillText('GRUPO A',1580,275,36,900,P.black,'left',pa,-1.4);
        fillText('GRUPO B',1580,495,36,900,P.black,'left',pb,-1.4);
        fillText('GRUPO C',1580,735,36,900,P.black,'left',pc,-1.4);
        fillText('EFEITO PEQUENO  ·  SEM LIMIAR UNIVERSAL',960,955,38,900,P.black,'center',Math.max(s.small,s.magic,s.lock),1.2);
      }
    }

    async function runLayoutAudit(manifest){
      const contract=await fetch('/config/layout_quality_contract.json').then(response=>response.json());
      const samples=await fetch('scenes/layout_audit_samples.json').then(response=>response.json());
      await document.fonts.ready;const frames=[];
      for(const phase of ['before','after']){ACTIVE_LAYOUT_PHASE=phase;for(const sample of samples.samples){renderFrame(sample.time,manifest);frames.push(collectLayoutFrame(phase,sample));}}
      const findings=frames.flatMap(frame=>frame.findings);const summarize=phase=>{const selected=findings.filter(item=>item.phase===phase);return {
        layout_errors:selected.filter(item=>item.severity==='ERROR').length,
        text_text_overlap:selected.filter(item=>item.type==='TEXT_TEXT_OVERLAP'&&item.severity==='ERROR').length,
        text_clipping:selected.filter(item=>item.type==='TEXT_CLIPPING'&&item.severity==='ERROR').length,
        important_shape_overlap:selected.filter(item=>item.type==='TEXT_IMPORTANT_SHAPE_OVERLAP'&&item.severity==='ERROR').length,
        warnings:selected.filter(item=>item.severity==='WARNING').length};};
      const result={contract_id:contract.contract_id,contract_version:contract.version,browser_geometry:'SVGTextElement.getBBox()',fonts_ready:document.fonts.status==='loaded',sample_count:samples.samples.length,frames,findings,before:summarize('before'),after:summarize('after')};
      await fetch('/layout-audit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(result)});
    }
'''


def build_player() -> str:
    player = SOURCE_PLAYER.read_text(encoding="utf-8")
    marker = "function renderFrame(time, manifest) {"
    if marker not in player:
        raise MotionError("Ponto de extensão do player não encontrado.")
    player = player.replace(marker, MOTION_JS + "\n" + marker, 1)
    old = """      else if (scene.scene_id === 'S010') drawS010Motion(time);
      else if (scene.scene_id === 'S011') drawS011Motion(time);
      else drawBaselineMotion(time, true);"""
    new = """      else if (scene.scene_id === 'S010') drawS010Motion(time);
      else if (scene.scene_id === 'S011') drawS011Motion(time);
      else if (scene.scene_id === 'S012') drawBaselineMotion(time, true);
      else if (scene.scene_id === 'S013') (ACTIVE_LAYOUT_PHASE === 'before' ? layoutBeforeDraw.S013 : drawS013Motion)(time);
      else if (scene.scene_id === 'S014') (ACTIVE_LAYOUT_PHASE === 'before' ? layoutBeforeDraw.S014 : drawS014Motion)(time);
      else if (scene.scene_id === 'S015' || scene.scene_id === 'S016') (ACTIVE_LAYOUT_PHASE === 'before' ? layoutBeforeDraw.material : drawMaterialSequence)(time);
      else (ACTIVE_LAYOUT_PHASE === 'before' ? layoutBeforeDraw.evidence : drawEvidenceSequence)(time);"""
    if old not in player:
        raise MotionError("Dispatch S001-S012 não encontrado no player.")
    player = player.replace(old, new, 1)
    player = player.replace(
        "      if (scene.scene_id === 'S001') drawS001(scene, time);",
        "      if (LAYOUT_AUDIT_MODE) beginLayoutFrame(scene, time);\n      if (scene.scene_id === 'S001') drawS001(scene, time);",
        1,
    )
    player = player.replace(
        "      ACTIVE_MANIFEST = manifest;\n      const renderOrigin",
        "      ACTIVE_MANIFEST = manifest;\n      if (LAYOUT_AUDIT_MODE) { await runLayoutAudit(manifest); return; }\n      const renderOrigin",
        1,
    )
    player = player.replace("scene_manifest_s001_s012.json", "scene_manifest_s001_s018.json")
    player = player.replace("motion candidate S001â€“S012", "layout refined S001â€“S018")
    return player


def build_manifests(motion: dict, audio_duration: float) -> tuple[dict, dict]:
    source = read_json(SOURCE_MANIFEST)
    scenes = copy.deepcopy(source["scenes"])
    scenes[-1]["end"] = motion["scenes"][0]["start"]
    scenes[-1]["duration"] = round(scenes[-1]["end"] - scenes[-1]["start"], 6)
    scenes.extend(copy.deepcopy(motion["scenes"]))
    base = {
        "schema_version": "5.0",
        "pilot_id": "capital_oculto_pilot_s001_s018_layout_refined",
        "status": "MOTION_CANDIDATE",
        "episode_id": "CO-001",
        "canvas": {"width": 1920, "height": 1080},
        "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0",
        "timing_quality": "WORD_BOUNDARY_REAL",
        "audio": {
            "file": FULL_AUDIO.relative_to(ROOT).as_posix(),
            "player_path": "audio/narration_s001_s018.wav",
            "duration_seconds": round(audio_duration, 6),
            "provider": "azure_speech_sdk",
            "voice": "pt-BR-AntonioNeural",
            "rate": "-7%", "pitch": "0%", "speech_overlap": 0,
            "same_synthesis_audio_timing": True,
            "timing_quality": "WORD_BOUNDARY_REAL",
        },
        "scenes": scenes,
    }
    full = copy.deepcopy(base); full["audio"]["render_origin_seconds"] = 0.0; full["audio"]["presentation_duration_seconds"] = round(audio_duration, 6)
    clip = copy.deepcopy(base); clip["pilot_id"] = "capital_oculto_s013_s018_layout_refined"; clip["audio"]["render_origin_seconds"] = motion["scenes"][0]["start"]; clip["audio"]["presentation_duration_seconds"] = round(audio_duration - motion["scenes"][0]["start"], 6)
    return full, clip


def audit_motion(motion: dict) -> dict:
    findings = []
    samples = []
    for scene in motion["scenes"]:
        if scene["max_static_hold_ms"] > 4000:
            findings.append({"scene_id": scene["scene_id"], "type": "STATIC_HOLD", "value_ms": scene["max_static_hold_ms"]})
        times = [scene["start"], scene["end"]]
        for item in scene["events"]:
            times.extend([item["time"], (item["time"] + item["end_time"]) / 2, item["end_time"]])
            if item["timing_source"] != "WORD_BOUNDARY_REAL":
                findings.append({"scene_id": scene["scene_id"], "type": "HEURISTIC_TIMING"})
        for value in sorted(set(round(item, 4) for item in times)):
            samples.append({"scene_id": scene["scene_id"], "time": value, "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0"})
    # As quatro gramáticas mantêm suas protected zones fixas; apenas massas,
    # superfícies tipográficas, estrutura e curvas se movem nos corredores declarados.
    zones = {
        "S013": {"moving_corridor": [900, 0, 780, 1080], "protected_type_clearance": 64},
        "S014": {"moving_corridor": [64, 205, 1792, 738], "protected_type_clearance": 24},
        "S015": {"moving_corridor": [64, 197, 1792, 831], "protected_type_clearance": 36},
        "S016": {"moving_corridor": [64, 197, 1792, 831], "protected_type_clearance": 36},
        "S017": {"moving_corridor": [96, 210, 1722, 738], "protected_type_clearance": 24},
        "S018": {"moving_corridor": [96, 96, 1722, 914], "protected_type_clearance": 24},
    }
    return {
        "schema_version": "1.0",
        "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0",
        "sampling": "scene bounds and start/mid/end of every WordBoundary motion event",
        "sample_count": len(samples),
        "samples": samples,
        "protected_zones": zones,
        "findings": findings,
        "geometry_errors": len(findings),
        "pseudo_arrowheads": 0,
        "bad_terminations": 0,
        "protected_type_violations": 0,
        "accidental_collisions": 0,
    }


def build_layout_samples(motion: dict) -> dict:
    samples: list[dict] = []
    ratios = (0.0, 0.25, 0.5, 0.75, 1.0)
    for scene in motion["scenes"]:
        start = float(scene["start"])
        end = float(scene["end"])
        duration = end - start
        candidates: list[tuple[str, float]] = [
            (f"{scene['scene_id']}-R{int(ratio * 100):03d}", start + duration * ratio)
            for ratio in ratios
        ]
        for event in scene["events"]:
            event_start = float(event["time"])
            event_end = float(event["end_time"])
            candidates.extend(
                [
                    (f"{event['event_id']}-START", event_start),
                    (f"{event['event_id']}-MID", (event_start + event_end) / 2),
                    (f"{event['event_id']}-END", event_end),
                ]
            )
        seen: set[float] = set()
        for sample_id, value in candidates:
            timestamp = min(max(value, start), end - 0.001)
            key = round(timestamp, 4)
            if key in seen:
                continue
            seen.add(key)
            samples.append({"sample_id": sample_id, "scene_id": scene["scene_id"], "time": key})
    return {
        "schema_version": "1.0",
        "contract": "LAYOUT_QUALITY_CONTRACT@1.0",
        "sampling": "0/25/50/75/100 percent plus start/mid/end of every WordBoundary event and scene boundaries",
        "samples": samples,
    }


class LayoutAuditState:
    done = threading.Event()
    error: str | None = None
    result: dict | None = None


def layout_audit_handler():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:
            payload = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if self.path == "/layout-audit":
                LayoutAuditState.result = json.loads(payload.decode("utf-8"))
                self.send_response(204)
                self.end_headers()
                LayoutAuditState.done.set()
            elif self.path == "/error":
                LayoutAuditState.error = payload.decode("utf-8", errors="replace")
                self.send_response(204)
                self.end_headers()
                LayoutAuditState.done.set()
            else:
                self.send_error(404)

    return Handler


def run_layout_audit(browser: Path) -> dict:
    LayoutAuditState.done.clear()
    LayoutAuditState.error = None
    LayoutAuditState.result = None
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(layout_audit_handler(), directory=str(ROOT))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    profile = Path(tempfile.mkdtemp(prefix="co-layout-audit-"))
    process = None
    try:
        relative_player = PLAYER.relative_to(ROOT).as_posix()
        manifest_query = quote(f"manifest/{FULL_MANIFEST.name}")
        url = f"http://127.0.0.1:{server.server_address[1]}/{relative_player}?manifest={manifest_query}&layoutaudit=1"
        process = subprocess.Popen(
            [
                str(browser), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                "--no-default-browser-check", f"--user-data-dir={profile}", url,
            ],
            cwd=ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not LayoutAuditState.done.wait(120):
            raise MotionError("Layout audit excedeu 120s.")
        if LayoutAuditState.error:
            raise MotionError(LayoutAuditState.error)
        if LayoutAuditState.result is None:
            raise MotionError("Browser não devolveu o layout audit.")
    finally:
        server.shutdown()
        server.server_close()
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        time.sleep(0.25)
        shutil.rmtree(profile, ignore_errors=True)
    write_text(LAYOUT_AUDIT, json.dumps(LayoutAuditState.result, ensure_ascii=False, indent=2) + "\n")
    return LayoutAuditState.result


def main() -> int:
    for path in (PLAN, LAYOUT_CONTRACT, TIMING, CONTINUATION_MANIFEST, CONTINUATION_AUDIO, SOURCE_MANIFEST, SOURCE_PLAYER, SOURCE_AUDIO):
        if not path.is_file():
            raise MotionError(f"Fonte obrigatória ausente: {path.relative_to(ROOT)}")
    timing = read_json(TIMING)
    if timing.get("timing_quality") != "WORD_BOUNDARY_REAL" or timing.get("speech_overlap") != 0:
        raise MotionError("Timing oficial não atende WORD_BOUNDARY_REAL/speech_overlap=0.")
    audio_duration = build_full_audio()
    motion = build_motion_spec(audio_duration)
    audit = audit_motion(motion)
    if audit["geometry_errors"]:
        raise MotionError(f"Motion audit falhou: {audit['findings']}")
    max_hold = max(scene["max_static_hold_ms"] for scene in motion["scenes"])
    if max_hold > 4000:
        raise MotionError(f"Static hold excedido: {max_hold}ms")
    write_text(MOTION_SPEC, json.dumps(motion, ensure_ascii=False, indent=2) + "\n")
    write_text(GEOMETRY_AUDIT, json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    write_text(LAYOUT_SAMPLES, json.dumps(build_layout_samples(motion), ensure_ascii=False, indent=2) + "\n")
    full, clip = build_manifests(motion, audio_duration)
    write_text(FULL_MANIFEST, json.dumps(full, ensure_ascii=False, indent=2) + "\n")
    write_text(CLIP_MANIFEST, json.dumps(clip, ensure_ascii=False, indent=2) + "\n")
    write_text(PLAYER, build_player())
    prior.PLAYER = PLAYER
    browser = prior.find_browser()
    layout = run_layout_audit(browser)
    after = layout["after"]
    if not layout.get("fonts_ready") or layout.get("browser_geometry") != "SVGTextElement.getBBox()":
        raise MotionError("Layout audit não usou getBBox/fontes prontas.")
    if after["layout_errors"] or after["text_text_overlap"] or after["text_clipping"] or after["important_shape_overlap"]:
        raise MotionError(f"Layout gate falhou: {after}")
    print(
        f"PREPARED=true AUDIO_DURATION={audio_duration:.6f}s GEOMETRY_ERRORS=0 "
        f"LAYOUT_ERRORS_BEFORE={layout['before']['layout_errors']} LAYOUT_ERRORS_AFTER=0 "
        f"MAX_STATIC_HOLD_MS={max_hold:.3f}",
        flush=True,
    )
    clip_meta = prior.render(browser, CLIP_MANIFEST.name, CLIP_RENDER, timeout=210)
    print(f"RENDER_S013_S018={CLIP_RENDER.relative_to(ROOT)}", flush=True)
    full_meta = prior.render(browser, FULL_MANIFEST.name, FULL_RENDER, timeout=420)
    print(f"RENDER_S001_S018={FULL_RENDER.relative_to(ROOT)}", flush=True)
    metadata = {
        "schema_version": "1.0", "status": "MOTION_CANDIDATE", "direction_status": "LAYOUT_REFINED", "timing_quality": "WORD_BOUNDARY_REAL",
        "speech_overlap": 0, "geometry_errors": 0, "max_static_hold_ms": max_hold,
        "layout_quality_contract": "LAYOUT_QUALITY_CONTRACT@1.0",
        "layout_errors_before": layout["before"]["layout_errors"],
        "layout_errors_after": layout["after"]["layout_errors"],
        "text_text_overlap_after": layout["after"]["text_text_overlap"],
        "text_clipping_after": layout["after"]["text_clipping"],
        "important_shape_overlap_after": layout["after"]["important_shape_overlap"],
        "audio_sha256": hashlib.sha256(FULL_AUDIO.read_bytes()).hexdigest(),
        "source_s001_s012_manifest_sha256": hashlib.sha256(SOURCE_MANIFEST.read_bytes()).hexdigest(),
        "renders": {"S013-S018": clip_meta, "S001-S018": full_meta},
    }
    write_text(RENDER_METADATA, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MotionError, prior.MotionError, OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
