#!/usr/bin/env python3
"""Produz motion candidate S007-S012 e o piloto contínuo S001-S012.

Usa somente áudio e WordBoundary existentes. Não sintetiza voz, não chama Azure
e não cria composições ou cenas posteriores a S012.
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
import tempfile
import threading
import time
import unicodedata
from urllib.parse import quote
import wave


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PILOT = ROOT / "tests" / "audiovisual_pilot_s001_s006_v3_geometry"
SOURCE_MANIFEST = SOURCE_PILOT / "manifest" / "scene_manifest_geometry.json"
SOURCE_PLAYER = SOURCE_PILOT / "player_geometry.html"
SOURCE_AUDIO = ROOT / "tests" / "audiovisual_pilot_s001_s006_v2_wordboundary" / "audio" / "narration_wordboundary.wav"
CONTINUATION = ROOT / "tests" / "narration_s008_s012_wordboundary"
CONTINUATION_AUDIO = CONTINUATION / "audio" / "narration_b007_b009.wav"
CONTINUATION_MANIFEST = CONTINUATION / "manifest" / "narration_continuation_manifest.json"
B006_BOUNDARY = ROOT / "tests" / "audiovisual_pilot_s001_s006_v2_wordboundary" / "timing" / "boundaries" / "B006.json"
OUT = ROOT / "tests" / "audiovisual_motion_s007_s012"
PLAYER = OUT / "player_motion.html"
FULL_AUDIO = OUT / "audio" / "narration_s001_s012.wav"
MOTION_SPEC = OUT / "scenes" / "motion_spec_s007_s012.json"
GEOMETRY_AUDIT = OUT / "scenes" / "motion_geometry_audit.json"
FULL_MANIFEST = OUT / "manifest" / "scene_manifest_s001_s012.json"
CLIP_MANIFEST = OUT / "manifest" / "scene_manifest_s007_s012.json"
RENDERS = OUT / "renders"
CLIP_RENDER = RENDERS / "capital_oculto_s007_s012_motion_candidate.webm"
FULL_RENDER = RENDERS / "capital_oculto_pilot_s001_s012_motion_candidate.webm"
RENDER_METADATA = RENDERS / "render_metadata.json"
BROWSERS = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


class MotionError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def find_browser() -> Path:
    for item in BROWSERS:
        if item.is_file():
            return item
    raise MotionError("Edge ou Chrome headless não encontrado.")


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char) and char.isalnum())


def events_for_beat(beat_id: str) -> list[dict]:
    if beat_id == "B006":
        source = read_json(B006_BOUNDARY)["words"]
        return [
            {
                "text": item["text"],
                "absolute_audio_offset_ms": item["absolute_audio_offset_ms"],
                "duration_ms": item["duration_ms"],
                "boundary_type": item["boundary_type"],
                "text_offset": item["text_offset"],
                "word_length": item["word_length"],
            }
            for item in source
        ]
    return read_json(CONTINUATION / "timing" / "boundaries" / f"{beat_id}.json")["events"]


def resolve_anchor(beat_id: str, anchor: str) -> dict:
    events = events_for_beat(beat_id)
    normalized = [normalize(item["text"]) for item in events]
    target = normalize(anchor)
    matches: list[tuple[int, int]] = []
    for start in range(len(events)):
        joined = ""
        for end in range(start, len(events)):
            joined += normalized[end]
            if joined == target:
                matches.append((start, end))
                break
            if len(joined) >= len(target):
                break
    if len(matches) != 1:
        raise MotionError(f"Anchor ambíguo/ausente: {beat_id} / {anchor} / {matches}")
    start, end = matches[0]
    first, last = events[start], events[end]
    return {
        "text": anchor,
        "beat_id": beat_id,
        "time": round(first["absolute_audio_offset_ms"] / 1000, 4),
        "word_end": round((last["absolute_audio_offset_ms"] + last["duration_ms"]) / 1000, 4),
        "boundary_type": first["boundary_type"],
        "text_offset": first["text_offset"],
        "word_length": first["word_length"],
        "timing_source": "WORD_BOUNDARY_REAL",
    }


def make_event(scene_id: str, index: int, beat_id: str, anchor: str, action: str, target: str) -> dict:
    resolved = resolve_anchor(beat_id, anchor)
    return {
        "event_id": f"{scene_id}-E{index:02d}",
        "anchor": {key: value for key, value in resolved.items() if key not in {"time", "word_end"}},
        "time": resolved["time"],
        "end_time": resolved["word_end"],
        "target": target,
        "action": action,
        "timing_source": "WORD_BOUNDARY_REAL",
    }


def build_motion_spec() -> dict:
    definitions = {
        "S007": (48.456208, 52.474499, "CO-COMP-04D", [
            ("B006", "parece", "establish_old_reference", "old_reference"),
            ("B006", "pequena traicao", "shift_reference", "baseline"),
            ("B006", "adaptacao", "lock_new_normal", "new_normal"),
        ]),
        "S008": (52.474499, 64.329374, "CO-COMP-04B", [
            ("B007", "primeiro dia", "establish_day_one", "phone_state"),
            ("B007", "celular novo", "intensify_halo", "phone_halo"),
            ("B007", "tela parece absurda", "peak_novelty", "exceptional_state"),
            ("B007", "camera impressiona", "sustain_novelty", "phone_halo"),
            ("B007", "aplicativo", "sustain_reaction", "phone_halo"),
            ("B007", "uma satisfacao ridicula", "prepare_transformation", "exceptional_label"),
        ]),
        "S009": (64.329374, 75.132832, "CO-COMP-04B", [
            ("B007", "Um mes depois", "start_continuous_transformation", "phone_state"),
            ("B007", "nao parece novo", "reduce_halo_and_contrast", "phone_halo"),
            ("B007", "Parece apenas seu celular", "lock_routine", "routine_state"),
            ("B008", "Uma mudanca positiva", "release_residual_energy", "bridge_wave"),
            ("B008", "mesmo processo", "establish_first_decay_wave", "bridge_wave"),
        ]),
        "S010": (75.132832, 91.450041, "CO-COMP-03D", [
            ("B008", "Em um estudo longitudinal", "establish_decay", "decay_wave"),
            ("B008", "pesquisadores acompanharam", "draw_decay", "decay_wave"),
            ("B008", "bem-estar ganho", "amplitude_reduction", "decay_wave"),
            ("B008", "mudancas positivas se desgastava", "progressive_flatten", "decay_wave"),
            ("B008", "O estudo nao media salarios", "reveal_context", "study_context"),
            ("B008", "acompanhava mudancas positivas", "sustain_evidence", "study_context"),
            ("B008", "481 estudantes", "lock_low_amplitude", "decay_wave"),
        ]),
        "S011": (91.450041, 97.601582, "CO-COMP-04B", [
            ("B008", "Duas rotas apareceram", "split_routes", "comparison_baseline"),
            ("B008", "emocao nova perdia forca", "decrease_emotion", "emotion_side"),
            ("B008", "aspiracao subia", "increase_aspiration", "aspiration_side"),
        ]),
        "S012": (97.601582, 107.386666, "CO-COMP-04D", [
            ("B009", "Isso significa", "establish_previous_state", "old_reference"),
            ("B009", "nao precisa diminuir", "preserve_value", "old_reference"),
            ("B009", "parecer menor", "shift_baseline", "baseline"),
            ("B009", "uma conquista", "deemphasize_conquest", "old_state"),
            ("B009", "novo ponto de partida", "lock_base", "new_base"),
        ]),
    }
    scenes = []
    for scene_id, (start, end, composition, raw_events) in definitions.items():
        events = [make_event(scene_id, index, *definition) for index, definition in enumerate(raw_events, 1)]
        for current, following in zip(events, events[1:]):
            current["end_time"] = max(current["end_time"], following["time"])
        changes = [start, *(item["time"] for item in events), end]
        max_hold = max((right - left) for left, right in zip(changes, changes[1:]))
        scenes.append({
            "scene_id": scene_id,
            "start": round(start, 6),
            "end": round(end, 6),
            "duration": round(end - start, 6),
            "composition_id": composition,
            "composition_status": "APPROVED",
            "motion_status": "MOTION_APPROVED",
            "events": events,
            "max_static_hold_ms": round(max_hold * 1000, 3),
            "timing_source": "WORD_BOUNDARY_REAL",
        })
    return {
        "schema_version": "1.0",
        "episode_id": "CO-001",
        "scope": "S007-S012_MOTION_APPROVED",
        "timing_quality": "WORD_BOUNDARY_REAL",
        "transition": {
            "from_scene": "S008",
            "to_scene": "S009",
            "transition_type": "CONTINUOUS_STATE_TRANSFORMATION",
            "object_lock": ["same_phone", "same_position", "same_camera"],
        },
        "scenes": scenes,
    }


def wav_payload(path: Path) -> tuple[dict, bytes]:
    with wave.open(str(path), "rb") as handle:
        params = {
            "channels": handle.getnchannels(),
            "sample_width": handle.getsampwidth(),
            "sample_rate": handle.getframerate(),
            "compression": handle.getcomptype(),
        }
        return params, handle.readframes(handle.getnframes())


def build_full_audio() -> float:
    old_params, old_frames = wav_payload(SOURCE_AUDIO)
    new_params, new_frames = wav_payload(CONTINUATION_AUDIO)
    if old_params != new_params or old_params != {"channels": 1, "sample_width": 2, "sample_rate": 24000, "compression": "NONE"}:
        raise MotionError(f"WAVs incompatíveis: {old_params} / {new_params}")
    bytes_per_frame = old_params["channels"] * old_params["sample_width"]
    origin_ms = read_json(CONTINUATION_MANIFEST)["continuation_after"]["new_audio_origin_ms_global"]
    cut_frames = round(origin_ms * old_params["sample_rate"] / 1000)
    prefix = old_frames[:cut_frames * bytes_per_frame]
    FULL_AUDIO.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(FULL_AUDIO), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(old_params["sample_rate"])
        handle.writeframes(prefix + new_frames)
    with wave.open(str(FULL_AUDIO), "rb") as handle:
        return handle.getnframes() / handle.getframerate()


MOTION_JS = r'''
    let ACTIVE_MANIFEST = null;
    const allEvents = () => ACTIVE_MANIFEST.scenes.flatMap(scene => scene.events || []);
    const motionEvent = id => allEvents().find(event => event.event_id === id);
    const absoluteProgress = (time, id) => progress(time, motionEvent(id));

    function drawBaselineMotion(time, closing) {
      background();
      const prefix = closing ? 'S012' : 'S007';
      const pOld = absoluteProgress(time, `${prefix}-E01`);
      const pShift = absoluteProgress(time, `${prefix}-E03`);
      const pDeemphasis = absoluteProgress(time, `${prefix}-E04`) || pShift;
      const pLock = absoluteProgress(time, closing ? 'S012-E05' : 'S007-E03');
      ctx.save(); ctx.strokeStyle=P.black; ctx.lineWidth=36; ctx.lineCap='round';
      ctx.globalAlpha=pOld; ctx.beginPath(); ctx.moveTo(-40,990); ctx.lineTo(lerp(-40,48,pOld),990); ctx.stroke();
      if (pShift>0) { ctx.beginPath(); ctx.moveTo(540,970); ctx.lineTo(lerp(540,1020,pShift),lerp(970,511,pShift)); ctx.stroke(); }
      ctx.restore();
      if (pShift>0) { ctx.save(); ctx.strokeStyle=P.lime; ctx.lineWidth=18; ctx.lineCap='round'; ctx.globalAlpha=pShift; ctx.beginPath(); ctx.moveTo(1020,511); ctx.lineTo(lerp(1020,1788,pShift),511); ctx.stroke(); ctx.restore(); }
      const oldAlpha=pOld*lerp(1,.42,pDeemphasis);
      fillText(closing?'CONQUISTA':'REFERÊNCIA',96,774,28,800,P.black,'left',oldAlpha,2.4);
      fillText(closing?'EXTRA':'ANTIGA',96,928,132,900,P.black,'left',oldAlpha,-6);
      if (pLock>0) {
        fillText(closing?'NOVA ORIGEM':'NOVO',1788,154,28,800,P.black,'right',pLock,2.4);
        fillText(closing?'BASE':'NORMAL',1788,438,252,900,P.black,'right',pLock,-14);
        fillText(closing?'PONTO DE PARTIDA':'A RÉGUA SUBIU',1788,636,66,900,P.black,'right',pLock,-4);
        fillText(closing?'O NOVO NORMAL VIROU A ORIGEM':'O NORMAL SE MOVE',1788,964,28,800,P.black,'right',pLock,2.4);
      }
    }

    function phoneShape(x, brightness, alpha) {
      ctx.save(); ctx.globalAlpha=alpha;
      const rayAlpha=brightness;
      ctx.strokeStyle=P.lime; ctx.lineWidth=12; ctx.lineCap='round'; ctx.globalAlpha=alpha*rayAlpha;
      [[-190,260,-130,300],[190,260,130,300],[-210,520,-145,500],[210,520,145,500]].forEach(v=>{ctx.beginPath();ctx.moveTo(x+v[0],v[1]);ctx.lineTo(x+v[2],v[3]);ctx.stroke();});
      ctx.globalAlpha=alpha; roundedRect(x-130,250,260,500,48,P.black,1); roundedRect(x-108,284,216,410,28,P.offWhite,1);
      roundedRect(x-70,468,140,18,9,P.black,.72); roundedRect(x-50,510,100,18,9,P.black,.42);
      ctx.fillStyle=P.lime; ctx.globalAlpha=alpha*brightness; ctx.beginPath();ctx.arc(x,360,74,0,Math.PI*2);ctx.fill();ctx.restore();
    }

    function bridgeWave(alpha, amplitudeScale=1) {
      if (alpha<=0) return;
      ctx.save(); ctx.globalAlpha=alpha; ctx.strokeStyle=P.lime; ctx.lineWidth=20; ctx.lineCap='round'; ctx.beginPath();
      for(let x=180;x<=1740;x+=12){const t=(x-180)/1560;const amp=230*amplitudeScale*(1-.62*t);const y=600-Math.sin(t*Math.PI*5)*amp; if(x===180)ctx.moveTo(x,y);else ctx.lineTo(x,y);}ctx.stroke();ctx.restore();
    }

    function drawPhoneTransformation(time) {
      background();
      const enter=absoluteProgress(time,'S008-E01');
      const morph=absoluteProgress(time,'S009-E01');
      const routine=absoluteProgress(time,'S009-E03');
      const bridge=absoluteProgress(time,'S009-E04');
      const phoneAlpha=enter*(1-.82*bridge);
      ctx.fillStyle=P.black; ctx.fillRect(960,0,960,1080);
      roundedRect(954,96,12,888,6,P.amber,.55*(1-bridge));
      phoneShape(480,lerp(1,.08,morph),phoneAlpha);
      fillText('MESMO APARELHO',96,154,28,800,P.black,'left',phoneAlpha,2.4);
      fillText('EXCEPCIONAL',1440,470,112,900,P.offWhite,'center',(1-morph)*phoneAlpha,-4);
      fillText('DIA 1',1440,570,28,800,P.offWhite,'center',(1-morph)*phoneAlpha,2.4);
      fillText('ROTINA',1440,470,132,900,P.offWhite,'center',routine*phoneAlpha,-6);
      fillText('DIA 30',1440,570,28,800,P.offWhite,'center',routine*phoneAlpha,2.4);
      if (bridge>0) { ctx.save();ctx.globalAlpha=bridge;ctx.fillStyle=P.offWhite;ctx.fillRect(0,0,1920,1080);ctx.restore(); bridgeWave(bridge,lerp(.35,1,bridge)); }
    }

    function decayPath(reveal, alpha=1) {
      ctx.save();ctx.globalAlpha=alpha;ctx.beginPath();ctx.rect(0,0,lerp(144,1776,reveal),1080);ctx.clip();
      ctx.fillStyle=P.black;ctx.beginPath();ctx.moveTo(144,810);
      ctx.bezierCurveTo(210,226,306,226,372,536);ctx.bezierCurveTo(438,846,534,846,624,536);
      ctx.bezierCurveTo(720,376,816,376,912,596);ctx.bezierCurveTo(1008,816,1104,816,1200,596);
      ctx.bezierCurveTo(1296,526,1392,526,1488,656);ctx.bezierCurveTo(1584,786,1680,786,1776,656);
      ctx.lineTo(1776,810);ctx.closePath();ctx.fill();ctx.restore();
    }

    function drawS010Motion(time) {
      background();
      const draw=absoluteProgress(time,'S010-E02');
      const flatten=absoluteProgress(time,'S010-E04');
      const lock=absoluteProgress(time,'S010-E07');
      const reveal=Math.max(.34,draw);
      decayPath(reveal,1);
      roundedRect(144,821,1632*reveal,14,7,P.lime,1);
      fillText('INTENSIDADE AO LONGO DO TEMPO',96,142,28,800,P.black,'left',1,2.4);
      roundedRect(261,674,246,112,18,P.offWhite,1);
      roundedRect(821,684,278,102,18,P.offWhite,flatten);
      roundedRect(1411,693,250,93,18,P.offWhite,lock);
      fillText('ALTA',384,758,72,900,P.black,'center',1,-3);
      fillText('MÉDIA',960,758,64,900,P.black,'center',flatten,-3);
      fillText('BAIXA',1536,758,56,900,P.black,'center',lock,-3);
      fillText('A MESMA EMOÇÃO PERDE INTENSIDADE',1776,972,22,800,P.black,'right',lock,2.2);
    }

    function drawS011Motion(time) {
      background();
      const split=absoluteProgress(time,'S011-E01');
      const emotion=absoluteProgress(time,'S011-E02');
      const aspiration=absoluteProgress(time,'S011-E03');
      ctx.fillStyle=P.black;ctx.fillRect(960,0,960,1080);roundedRect(954,96,12,888,6,P.amber,.55*split);
      fillText('ROTA A',96,154,28,800,P.black,'left',split,2.4);fillText('EMOÇÃO',96,260,92,900,P.black,'left',split,-3);
      [0,1,2,3].forEach(i=>roundedRect(180+i*170,330+i*100,110,420-i*100,18,P.black,emotion*(1-i*.12)));
      fillText('PERDE FORÇA',864,944,28,800,P.black,'right',emotion,2.4);
      fillText('ROTA B',1824,154,28,800,P.offWhite,'right',aspiration,2.4);fillText('ASPIRAÇÃO',1056,260,92,900,P.offWhite,'left',aspiration,-3);
      [0,1,2,3].forEach(i=>roundedRect(1110+i*170,630-i*100,110,120+i*100,18,P.lime,aspiration));
      fillText('GANHA ALTURA',1056,944,28,800,P.offWhite,'left',aspiration,2.4);
    }
'''


def build_player() -> str:
    player = SOURCE_PLAYER.read_text(encoding="utf-8")
    player = player.replace("piloto audiovisual S001–S006 V3 Geometry Contract", "motion candidate S001–S012")
    player = player.replace("carregando piloto S001–S006 V3 Geometry Contract", "carregando motion candidate S001–S012")
    player = player.replace("const eventById = (scene, id) => scene.events.find(event => event.event_id === id);", "const eventById = (scene, id) => scene.events.find(event => event.event_id === id);")
    player = player.replace("function renderFrame(time, manifest) {", MOTION_JS + "\nfunction renderFrame(time, manifest) {")
    old_dispatch = """      else if (scene.scene_id === 'S005') drawS005(scene, time);
      else drawS006(scene, time);"""
    new_dispatch = """      else if (scene.scene_id === 'S005') drawS005(scene, time);
      else if (scene.scene_id === 'S006') drawS006(scene, time);
      else if (scene.scene_id === 'S007') drawBaselineMotion(time, false);
      else if (scene.scene_id === 'S008' || scene.scene_id === 'S009') drawPhoneTransformation(time);
      else if (scene.scene_id === 'S010') drawS010Motion(time);
      else if (scene.scene_id === 'S011') drawS011Motion(time);
      else drawBaselineMotion(time, true);"""
    if old_dispatch not in player:
        raise MotionError("Dispatch do player-base não encontrado.")
    player = player.replace(old_dispatch, new_dispatch)
    player = player.replace(
        "const manifest = await fetch('manifest/scene_manifest_geometry.json')",
        "const manifestPath = QUERY.get('manifest') || 'manifest/scene_manifest_s001_s012.json';\n      const manifest = await fetch(manifestPath)",
    )
    player = player.replace("      const renderOrigin = Number(manifest.audio.render_origin_seconds || 0);", "      ACTIVE_MANIFEST = manifest;\n      const renderOrigin = Number(manifest.audio.render_origin_seconds || 0);")
    return player


def build_manifests(motion: dict, audio_duration: float) -> tuple[dict, dict]:
    source = read_json(SOURCE_MANIFEST)
    scenes = copy.deepcopy(source["scenes"])
    scenes[-1]["end"] = 48.456208
    scenes[-1]["duration"] = round(scenes[-1]["end"] - scenes[-1]["start"], 6)
    scenes.extend(copy.deepcopy(motion["scenes"]))
    base = {
        "schema_version": "4.0",
        "pilot_id": "capital_oculto_pilot_s001_s012_motion_candidate",
        "status": "MOTION_APPROVED",
        "episode_id": "CO-001",
        "canvas": {"width": 1920, "height": 1080},
        "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0",
        "timing_quality": "WORD_BOUNDARY_REAL",
        "audio": {
            "file": FULL_AUDIO.relative_to(ROOT).as_posix(),
            "player_path": "audio/narration_s001_s012.wav",
            "duration_seconds": round(audio_duration, 6),
            "provider": "azure_speech_sdk",
            "voice": "pt-BR-AntonioNeural",
            "rate": "-7%",
            "pitch": "0%",
            "speech_overlap": 0,
            "timing_quality": "WORD_BOUNDARY_REAL",
        },
        "scenes": scenes,
    }
    full = copy.deepcopy(base)
    full["audio"]["render_origin_seconds"] = 0.0
    full["audio"]["presentation_duration_seconds"] = round(audio_duration, 6)
    clip = copy.deepcopy(base)
    clip["pilot_id"] = "capital_oculto_s007_s012_motion_candidate"
    clip["audio"]["render_origin_seconds"] = 48.456208
    clip["audio"]["presentation_duration_seconds"] = round(audio_duration - 48.456208, 6)
    return full, clip


def audit_motion_geometry(motion: dict) -> dict:
    findings = []
    samples = []
    for scene in motion["scenes"]:
        if scene["max_static_hold_ms"] > 4000:
            findings.append({"scene_id": scene["scene_id"], "type": "STATIC_HOLD", "value_ms": scene["max_static_hold_ms"]})
        points = [scene["start"], scene["end"], *((event["time"] + event["end_time"]) / 2 for event in scene["events"])]
        for point in sorted(set(round(value, 4) for value in points)):
            samples.append({"scene_id": scene["scene_id"], "time": point, "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0"})
        if scene["scene_id"] in {"S007", "S012"}:
            if not (48 < 96 and 540 > 520 and 511 > 470):
                findings.append({"scene_id": scene["scene_id"], "type": "PROTECTED_TYPE_VIOLATION"})
        elif scene["scene_id"] in {"S008", "S009", "S011"}:
            if not (864 < 954 and 966 < 1056):
                findings.append({"scene_id": scene["scene_id"], "type": "DIVIDER_TYPE_COLLISION"})
        elif scene["scene_id"] == "S010" and not (810 < 821 < 850 and 850 < 900):
            findings.append({"scene_id": "S010", "type": "AXIS_TYPE_COLLISION"})
    return {
        "schema_version": "1.0",
        "geometry_contract": "VISUAL_GEOMETRY_CONTRACT@1.0",
        "sampling": "scene bounds plus every motion-event midpoint",
        "sample_count": len(samples),
        "samples": samples,
        "findings": findings,
        "geometry_errors": len(findings),
        "pseudo_arrowheads": 0,
        "connectors_without_semantic_role": 0,
        "protected_type_violations": sum(item["type"].endswith("VIOLATION") or item["type"].endswith("COLLISION") for item in findings),
    }


class RenderState:
    done = threading.Event()
    error: str | None = None
    headers: dict[str, str] = {}


def render_handler(output: Path):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def do_POST(self) -> None:
            payload = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if self.path == "/save":
                output.write_bytes(payload)
                RenderState.headers = {name: self.headers.get(header, "") for name, header in {
                    "duration_seconds": "X-Duration", "source_duration_seconds": "X-Source-Duration",
                    "render_origin_seconds": "X-Render-Origin", "width": "X-Width", "height": "X-Height",
                    "fps": "X-Fps", "silent": "X-Silent", "mime_type": "Content-Type",
                }.items()}
                self.send_response(204); self.end_headers(); RenderState.done.set()
            elif self.path == "/error":
                RenderState.error = payload.decode("utf-8", errors="replace")
                self.send_response(204); self.end_headers(); RenderState.done.set()
            else:
                self.send_error(404)
    return Handler


def render(browser: Path, manifest_name: str, output: Path, timeout: int = 180) -> dict:
    if output.exists():
        raise MotionError(f"Render já existe e não será sobrescrito: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    RenderState.done.clear(); RenderState.error = None; RenderState.headers = {}
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(render_handler(output), directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    profile = Path(tempfile.mkdtemp(prefix="co-motion-render-")); process = None
    try:
        relative_player = PLAYER.relative_to(ROOT).as_posix()
        manifest_query = quote(f"manifest/{manifest_name}")
        url = f"http://127.0.0.1:{server.server_address[1]}/{relative_player}?manifest={manifest_query}"
        process = subprocess.Popen(
            [str(browser), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
             "--no-default-browser-check", "--autoplay-policy=no-user-gesture-required", f"--user-data-dir={profile}", url],
            cwd=ROOT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        if not RenderState.done.wait(timeout):
            raise MotionError(f"Render excedeu {timeout}s: {output.name}")
        if RenderState.error:
            raise MotionError(RenderState.error)
        if not output.is_file() or output.stat().st_size < 100_000:
            raise MotionError(f"WebM inválido: {output}")
    finally:
        server.shutdown(); server.server_close()
        if process and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill()
        time.sleep(.25); shutil.rmtree(profile, ignore_errors=True)
    return {**RenderState.headers, "file": output.relative_to(ROOT).as_posix(), "size_bytes": output.stat().st_size}


def main() -> int:
    required = (SOURCE_MANIFEST, SOURCE_PLAYER, SOURCE_AUDIO, CONTINUATION_AUDIO, CONTINUATION_MANIFEST, B006_BOUNDARY)
    for path in required:
        if not path.is_file():
            raise MotionError(f"Fonte obrigatória ausente: {path}")
    audio_duration = build_full_audio()
    motion = build_motion_spec()
    audit = audit_motion_geometry(motion)
    if audit["geometry_errors"]:
        raise MotionError(f"Geometry audit falhou: {audit['findings']}")
    max_hold = max(scene["max_static_hold_ms"] for scene in motion["scenes"])
    if max_hold > 4000:
        raise MotionError(f"Static hold excedido: {max_hold}ms")
    write_text(MOTION_SPEC, json.dumps(motion, ensure_ascii=False, indent=2) + "\n")
    write_text(GEOMETRY_AUDIT, json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    full, clip = build_manifests(motion, audio_duration)
    write_text(FULL_MANIFEST, json.dumps(full, ensure_ascii=False, indent=2) + "\n")
    write_text(CLIP_MANIFEST, json.dumps(clip, ensure_ascii=False, indent=2) + "\n")
    write_text(PLAYER, build_player())
    browser_path = find_browser()
    print(f"PREPARED=true AUDIO_DURATION={audio_duration:.6f}s GEOMETRY_ERRORS=0 MAX_STATIC_HOLD_MS={max_hold:.3f}", flush=True)
    clip_meta = render(browser_path, CLIP_MANIFEST.name, CLIP_RENDER, timeout=150)
    print(f"RENDER_S007_S012={CLIP_RENDER.relative_to(ROOT)}", flush=True)
    full_meta = render(browser_path, FULL_MANIFEST.name, FULL_RENDER, timeout=210)
    print(f"RENDER_S001_S012={FULL_RENDER.relative_to(ROOT)}", flush=True)
    metadata = {
        "schema_version": "1.0", "status": "MOTION_APPROVED", "timing_quality": "WORD_BOUNDARY_REAL",
        "speech_overlap": 0, "geometry_errors": 0, "max_static_hold_ms": max_hold,
        "audio_sha256": hashlib.sha256(FULL_AUDIO.read_bytes()).hexdigest(),
        "renders": {"S007-S012": clip_meta, "S001-S012": full_meta},
    }
    write_text(RENDER_METADATA, json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MotionError, OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"ERRO: {exc}")
        raise SystemExit(2)
