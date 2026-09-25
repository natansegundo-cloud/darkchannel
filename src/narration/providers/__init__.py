"""Interface comum dos providers de narração."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderResult:
    """Resultado uniforme de uma síntese de um beat."""

    audio_data: bytes
    sample_rate: int
    channels: int = 1
    sample_width: int = 2
    boundaries: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderError(RuntimeError):
    """Falha de síntese reportada ao engine."""
