"""Provider local Kokoro em processo isolado, sem importar dependências no engine."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from typing import Any

from . import ProviderError, ProviderResult


ROOT = Path(__file__).resolve().parents[3]
VENV_PYTHON = ROOT / ".tts" / "venv" / "Scripts" / "python.exe"


def synthesize(
    beat: dict[str, Any],
    *,
    narrator: dict[str, Any],
    key: str = "",
    region: str = "",
) -> ProviderResult:
    """Sintetiza um beat no mesmo ambiente Kokoro usado pelo script arquivado."""
    del key, region
    if not VENV_PYTHON.is_file():
        raise ProviderError(f"Ambiente Kokoro não encontrado: {VENV_PYTHON}")
    alias = narrator.get("fallback", {}).get("voice_alias", "santa")
    speed = str(narrator.get("delivery", {}).get("speed", "0.95"))
    with tempfile.TemporaryDirectory(prefix="co-kokoro-") as temporary:
        output = Path(temporary) / "beat.wav"
        command = [
            str(VENV_PYTHON), str(Path(__file__).resolve()), "--worker",
            "--text", beat["raw_text"], "--output", str(output), "--voice", alias, "--speed", speed,
        ]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0 or not output.is_file():
            detail = (result.stderr or result.stdout).strip()[-500:]
            raise ProviderError(f"Falha no provider Kokoro: {detail}")
        audio_data = output.read_bytes()
        with wave.open(str(output), "rb") as handle:
            sample_rate = handle.getframerate()
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
    return ProviderResult(
        audio_data=audio_data,
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width,
        metadata={"timing_quality": "HEURISTIC", "voice_alias": alias},
    )


def _worker(args: argparse.Namespace) -> int:
    # As importações pesadas ficam confinadas ao processo .tts/venv.
    import numpy as np
    import soundfile as sf
    from kokoro_onnx import Kokoro
    from misaki.espeak import EspeakG2P

    config_path = ROOT / "config" / "voz_local.json"
    import json

    config = json.loads(config_path.read_text(encoding="utf-8"))
    model = ROOT / config["modelo"]
    voices = ROOT / config["banco_de_vozes"]
    voice = config["vozes_permitidas"][args.voice]
    kokoro = Kokoro(str(model), str(voices))
    g2p = EspeakG2P(language=config["idioma"])
    phonemes, _ = g2p(args.text)
    audio, sample_rate = kokoro.create(phonemes, voice=voice, speed=float(args.speed), is_phonemes=True)
    output = np.asarray(audio, dtype=np.float32)
    sf.write(args.output, output, sample_rate, subtype="PCM_16")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--text")
    parser.add_argument("--output")
    parser.add_argument("--voice", default="santa")
    parser.add_argument("--speed", default="0.95")
    args = parser.parse_args()
    if not args.worker or not args.text or not args.output:
        raise SystemExit("local_kokoro.py é um provider interno; use scripts/gerar_narracao.py.")
    return _worker(args)


if __name__ == "__main__":
    raise SystemExit(main())
