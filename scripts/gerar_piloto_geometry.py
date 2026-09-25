#!/usr/bin/env python3
"""Gera a instância V3 do piloto com as rotas do Visual Geometry Contract."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests" / "audiovisual_pilot_s001_s006_v2_wordboundary"
TARGET = ROOT / "tests" / "audiovisual_pilot_s001_s006_v3_geometry"


S005_FUNCTION = r'''function drawS005(scene, time) {
      background();
      const pTracks = progress(time, eventById(scene, 'S005-E01'));
      const pDriver = progress(time, eventById(scene, 'S005-E02'));
      const pNormal = progress(time, eventById(scene, 'S005-E03'));
      const pComp = progress(time, eventById(scene, 'S005-E04'));
      const pExp = progress(time, eventById(scene, 'S005-E05'));
      const pRef = progress(time, eventById(scene, 'S005-E06'));
      const pShift = progress(time, eventById(scene, 'S005-E07'));
      const pLock = progress(time, eventById(scene, 'S005-E08'));
      const enterAlpha = easeOut((time - scene.start) / 0.35);

      // ACCENT_LINE: referencia compartilhada, sem ponta de seta.
      // O endpoint termina antes da zona do label superior.
      if (pRef > 0) {
        ctx.save();
        ctx.strokeStyle = P.lime;
        ctx.lineWidth = 30;
        ctx.lineCap = 'round';
        ctx.globalAlpha = 0.95 * pRef * enterAlpha;
        const startX = 610, startY = 904;
        const targetX = 1390, targetY = 220;
        const curX = lerp(startX, targetX, pRef);
        const curY = lerp(startY, targetY, pRef);
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(curX, curY);
        ctx.stroke();
        ctx.restore();
      }

      if (pDriver > 0) {
        fillText('QUANDO A RENDA SOBE', 1824, 136, 28, 800, P.black, 'right', pDriver * enterAlpha, 2.4);
      }

      const shiftNormal = easeOut(clamp((pShift - 0.00) / 0.85));
      const shiftComp = easeOut(clamp((pShift - 0.08) / 0.85));
      const shiftExp = easeOut(clamp((pShift - 0.16) / 0.85));
      const xNorm = lerp(1196 - 240, 1196, shiftNormal);
      const xComp = lerp(1386 - 240, 1386, shiftComp);
      const xExp = lerp(1576 - 240, 1576, shiftExp);

      // TRACKS: terminacao ortogonal limpa antes dos blocos lime.
      if (pTracks > 0) roundedRect(560, 272, 636, 86, 18, P.black, pTracks * enterAlpha);
      if (pNormal > 0) {
        fillText('NORMAL', 96, 330, 82, 900, P.black, 'left', pNormal * enterAlpha, -4);
        roundedRect(xNorm, 272, 386, 86, 18, P.lime, pNormal * enterAlpha);
      }

      if (pTracks > 0) roundedRect(560, 522, 826, 86, 18, P.black, pTracks * enterAlpha);
      if (pComp > 0) {
        fillText('COMPARAÇÃO', 96, 580, 70, 900, P.black, 'left', pComp * enterAlpha, -4);
        roundedRect(xComp, 522, 268, 86, 18, P.lime, pComp * enterAlpha);
      }

      if (pTracks > 0) roundedRect(560, 772, 1016, 86, 18, P.black, pTracks * enterAlpha);
      if (pExp > 0) {
        fillText('DESPESAS', 96, 830, 82, 900, P.black, 'left', pExp * enterAlpha, -4);
        roundedRect(xExp, 772, 184, 86, 18, P.lime, pExp * enterAlpha);
      }

      if (pLock > 0) {
        fillText('O SISTEMA SE MOVE JUNTO', 1824, 966, 28, 800, P.black, 'right', pLock * enterAlpha, 2.4);
      }
    }
'''


S006_FUNCTION = r'''function drawS006(scene, time) {
      background();
      const pOld = progress(time, eventById(scene, 'S006-E01'));
      const pRise = progress(time, eventById(scene, 'S006-E02'));
      const pDeemp = progress(time, eventById(scene, 'S006-E03'));
      const pNormal = progress(time, eventById(scene, 'S006-E04'));
      const pLock = progress(time, eventById(scene, 'S006-E05'));
      const enterAlpha = easeOut((time - scene.start) / 0.35);

      // STOP_BEFORE: o trecho antigo termina antes de EXTRA.
      if (pOld > 0) {
        ctx.save();
        ctx.strokeStyle = P.black;
        ctx.lineWidth = 36;
        ctx.lineCap = 'round';
        ctx.globalAlpha = pOld * enterAlpha;
        ctx.beginPath();
        ctx.moveTo(-40, 990);
        ctx.lineTo(lerp(-40, 48, pOld), 990);
        ctx.stroke();
        ctx.restore();
      }

      // STOP_BEFORE + ROUTE_AROUND: o trecho ascendente inicia depois de EXTRA.
      if (pRise > 0) {
        ctx.save();
        ctx.strokeStyle = P.black;
        ctx.lineWidth = 36;
        ctx.lineCap = 'round';
        ctx.globalAlpha = pRise * enterAlpha;
        const curX = lerp(540, 1020, pRise);
        const curY = lerp(970, 511, pRise);
        ctx.beginPath();
        ctx.moveTo(540, 970);
        ctx.lineTo(curX, curY);
        ctx.stroke();
        ctx.restore();
      }

      // TRANSFORM_TO_UNDERLINE: o destaque acompanha a base de NORMAL.
      if (pRise > 0) {
        ctx.save();
        ctx.strokeStyle = P.lime;
        ctx.lineWidth = 36;
        ctx.lineCap = 'round';
        ctx.globalAlpha = pRise * enterAlpha;
        ctx.beginPath();
        ctx.moveTo(1020, 511);
        ctx.lineTo(lerp(1020, 1824, pRise), 511);
        ctx.stroke();
        ctx.restore();
      }

      if (pOld > 0) {
        const extraAlpha = pOld * lerp(1.0, 0.40, pDeemp) * enterAlpha;
        fillText('ANTES', 96, 774, 28, 800, P.black, 'left', extraAlpha, 2.4);
        fillText('EXTRA', 88, 928, 148, 900, P.black, 'left', extraAlpha, -7);
      }

      if (pNormal > 0) {
        const normAlpha = pNormal * enterAlpha;
        const normScale = lerp(0.97, 1.0, pNormal);
        fillText('AGORA', 1824, 154, 28, 800, P.black, 'right', normAlpha, 2.4);
        ctx.save();
        ctx.translate(1818, 438);
        ctx.scale(normScale, normScale);
        fillText('NORMAL', 0, 0, 252, 900, P.black, 'right', normAlpha, -14);
        ctx.restore();
        roundedRect(1824 - 804 * pNormal, 502, 804 * pNormal, 18, 9, P.lime, normAlpha);
      }

      if (pLock > 0) {
        const lockAlpha = pLock * enterAlpha;
        fillText('VIROU REFERÊNCIA', 1824, 636, 66, 900, P.black, 'right', lockAlpha, -4);
        fillText('O GANHO NÃO SUMIU • A BASE MUDOU', 1824, 964, 28, 800, P.black, 'right', lockAlpha, 2.4);
      }
    }
'''


GEOMETRY_ROUTES = {
    "contract": "config/visual_geometry_contract.json",
    "scenes": {
        "S005": {
            "master_finding": "MASTER_DEFECT",
            "reference": {
                "geometry_type": "ACCENT_LINE",
                "route": "STOP_BEFORE",
                "start": [610, 904],
                "end": [1390, 220],
                "arrowhead": False,
                "semantic_role": "REFERENCIA_COMPARTILHADA"
            },
            "tracks": {
                "geometry_type": "TRACK",
                "termination": "ORTHOGONAL_CLEAN_TERMINATION",
                "endpoints": {"normal": 1196, "comparison": 1386, "expenses": 1576}
            }
        },
        "S006": {
            "master_finding": "MASTER_DEFECT",
            "baseline": {
                "geometry_type": "STRUCTURAL_LINE",
                "route": ["STOP_BEFORE", "ROUTE_AROUND", "TRANSFORM_TO_UNDERLINE"],
                "old_segment": [[-40, 990], [48, 990]],
                "rising_segment": [[540, 970], [1020, 511]],
                "underline_segment": [[1020, 511], [1824, 511]],
                "protect_primary_type": True
            }
        }
    }
}


def replace_between(source: str, start: str, end: str, replacement: str) -> str:
    start_index = source.index(start)
    end_index = source.index(end, start_index)
    return source[:start_index] + replacement + source[end_index:]


def build_player() -> str:
    player = (SOURCE / "player_wordboundary.html").read_text(encoding="utf-8")
    player = player.replace("V2 WordBoundary", "V3 Geometry Contract")
    player = player.replace("carregando piloto S001–S006 V2 WordBoundary", "carregando piloto S001–S006 V3 Geometry Contract")
    player = player.replace("manifest/scene_manifest_wordboundary.json", "manifest/scene_manifest_geometry.json")
    player = replace_between(player, "function drawS005", "function drawS006", S005_FUNCTION)
    player = replace_between(player, "function drawS006", "function renderFrame", S006_FUNCTION)
    return player


def main() -> int:
    source_manifest = json.loads((SOURCE / "manifest" / "scene_manifest_wordboundary.json").read_text(encoding="utf-8-sig"))
    manifest = copy.deepcopy(source_manifest)
    manifest["pilot_id"] = "capital_oculto_pilot_s001_s006_v3_geometry"
    manifest["status"] = "PILOT_V3_GEOMETRY_CONTRACT"
    manifest["selection_mode"] = "PILOT_V3_GEOMETRY"
    manifest["geometry_contract"] = "config/visual_geometry_contract.json"
    manifest["geometry_routes"] = "scenes/geometry_routes.json"
    manifest["audio"]["player_path"] = "../audiovisual_pilot_s001_s006_v2_wordboundary/audio/narration_wordboundary.wav"
    for scene in manifest.get("scenes", []):
        scene["geometry_contract"] = "VISUAL_GEOMETRY_CONTRACT@1.0"
    motion = json.loads((SOURCE / "scenes" / "motion_spec_wordboundary.json").read_text(encoding="utf-8-sig"))
    motion["geometry_contract"] = "VISUAL_GEOMETRY_CONTRACT@1.0"
    motion["geometry_routes"] = "scenes/geometry_routes.json"

    (TARGET / "manifest").mkdir(parents=True, exist_ok=True)
    (TARGET / "scenes").mkdir(parents=True, exist_ok=True)
    (TARGET / "renders").mkdir(parents=True, exist_ok=True)
    (TARGET / "manifest" / "scene_manifest_geometry.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (TARGET / "scenes" / "motion_spec_geometry.json").write_text(json.dumps(motion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (TARGET / "scenes" / "geometry_routes.json").write_text(json.dumps(GEOMETRY_ROUTES, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (TARGET / "player_geometry.html").write_text(build_player(), encoding="utf-8")
    print(f"PLAYER={TARGET.relative_to(ROOT) / 'player_geometry.html'}")
    print(f"MANIFEST={TARGET.relative_to(ROOT) / 'manifest' / 'scene_manifest_geometry.json'}")
    print(f"AUDIO_SOURCE={manifest['audio']['player_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
