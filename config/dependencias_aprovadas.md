# Dependências aprovadas — Capital Oculto

Registro curado de dependências externas autorizadas para limitações técnicas documentadas. A aprovação desta entrada foi registrada por Natan antes do primeiro uso em código experimental.

| Tipo | Pacote/ferramenta | Versão travada | Motivo | Aprovado por | Data |
|---|---|---:|---|---|---|
| Pacote Python | `azure-cognitiveservices-speech` | `1.51.2` | TTS oficial do Capital Oculto com `pt-BR-AntonioNeural` e timestamps reais de `WordBoundary` emitidos pelo Azure Speech SDK, substituindo o alinhamento heurístico na sincronização de narração e motion. | Natan | 2026-09-24 |
| Ferramenta externa | `ffmpeg` | ambiente local; versão a registrar quando usado | Já usado implicitamente no ambiente para inspeção/mux; tornar explícito que `subprocess` para `ffmpeg` é permitido e não conta como dependência Python. | Natan | 2026-09-24 |

O SDK Azure é o caminho oficial de TTS e word boundary para o piloto V2; `scripts/gerar_narracao_v3_sdk_experimental.py` permanece preservado como experimento de comparação. `scripts/gerar_narracao_v2.py` e seu alinhador heurístico permanecem disponíveis somente como `LEGACY_FALLBACK`, com `timing_quality=HEURISTIC` explícito. A geração de SVG, validação estrutural, regras de composição e content zones continuam stdlib-only.
