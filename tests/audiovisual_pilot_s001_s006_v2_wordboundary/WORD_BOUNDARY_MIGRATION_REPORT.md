# WordBoundary Migration Report

Status: `OFFICIAL_PILOT_COMPLETE`

Escopo: somente S001-S006 V2. Nenhum S007, variante nova ou faixa de voz/musica foi criado.

## Resultado

- Provider oficial: `azure_speech_sdk` / `azure-cognitiveservices-speech==1.51.2`
- Voz: `pt-BR-AntonioNeural`; pacing: `rate=-7%`, `pitch=0%`
- `synthesis_id`: `CO-001-V2-WB-COMPOSITION-c22d116db822`
- Total de eventos WordBoundary reais: `105`
- Eventos de motion re-resolvidos: `30`
- Anchors resolvidos: `60`
- Anchors ambiguos: `0`
- Anchors ausentes: `0`
- Speech overlap: `0`
- Duracoes negativas: `0`
- Avisos de densidade > 3.2 palavras/s: `0`
- Primeiro estado visual: validado em todas as seis cenas dentro do guardrail de 350 ms
- `CO-COMP-04D@1.1`: `PROTECT_PRIMARY_TYPE=true`; baseline estrutural sem cruzar o tipo primario
- Duracao final: `52.388 s`
- Render: `1920x1080`, `30 fps`

## Artefatos promovidos

- [narracao oficial e timing](timing/03A_AUDIO_TIMING_WORD_BOUNDARY.json)
- [boundaries por beat](timing/boundaries/)
- [audio composto](audio/narration_wordboundary.wav)
- [manifest oficial](manifest/scene_manifest_wordboundary.json)
- [motion spec oficial](scenes/motion_spec_wordboundary.json)
- [player oficial](player_wordboundary.html)
- [render final](renders/capital_oculto_pilot_s001_s006_v2_wordboundary.webm)

## Compatibilidade e legado

- [gerar_narracao_v2.py](../../scripts/gerar_narracao_v2.py) e seu alinhador heuristico permanecem `LEGACY_FALLBACK`.
- [gerar_narracao_v3_sdk_experimental.py](../../scripts/gerar_narracao_v3_sdk_experimental.py) e [word_boundary_v3_experimental](../word_boundary_v3_experimental/) foram preservados.
- O caminho oficial nao faz fallback silencioso: ausencia do SDK, falha Azure ou falha de WordBoundary interrompe a execucao. Um fallback explicito deve declarar `timing_quality=HEURISTIC`.
- Os audios, timings, manifests, motion specs e renders V1/V2 anteriores nao foram alterados.

## Validações

Comando executado: `python scripts/validar_piloto_wordboundary.py`

Resultado: `WORD_BOUNDARY_VALIDATION=PASS`.
