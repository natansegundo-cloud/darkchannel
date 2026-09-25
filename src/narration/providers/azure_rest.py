"""Provider Azure Speech REST preservando a síntese SSML V2."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from typing import Any

from xml.sax.saxutils import escape

from . import ProviderError, ProviderResult
from .voice_pacing_v2 import build_ssml


def synthesize(
    beat: dict[str, Any],
    *,
    narrator: dict[str, Any],
    key: str,
    region: str,
) -> ProviderResult:
    if not re.fullmatch(r"[a-z0-9-]+", region.casefold()):
        raise ProviderError("Região Azure inválida na configuração local.")
    azure = narrator.get("azure", {})
    voice = narrator["voice"]
    language = narrator.get("language", "pt-BR")
    delivery = narrator.get("delivery", {})
    ssml = build_ssml(
        beat,
        voice=voice,
        language=language,
        rate=delivery.get("rate", "0%"),
    )
    # O endpoint V2 usa o campo de volume somente no gerador legado. Mantê-lo
    # ausente aqui preserva exatamente o SSML aprovado do Voice Pacing Contract.
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    request = urllib.request.Request(
        url,
        data=ssml,
        method="POST",
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml; charset=utf-8",
            "X-Microsoft-OutputFormat": azure.get("output_format", "riff-24khz-16bit-mono-pcm"),
            "User-Agent": "capital-oculto-pipeline-v2",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            if response.status != 200:
                raise ProviderError(f"Azure Speech retornou HTTP {response.status}.")
            audio_data = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read(512).decode("utf-8", errors="replace").strip()
        safe_detail = re.sub(r"[A-Za-z0-9+/=_-]{24,}", "[redacted]", detail)
        raise ProviderError(f"Azure Speech retornou HTTP {exc.code}: {safe_detail}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"Falha de rede ao acessar Azure Speech: {exc.reason}") from exc
    return ProviderResult(audio_data=audio_data, sample_rate=0, metadata={"timing_quality": "HEURISTIC"})
