# Pipeline audiovisual por beats

Status: **fundação estável validada; produção canônica em Azure Speech SDK com WORD_BOUNDARY_REAL**.

Esta arquitetura separa decisões editoriais, timing real de áudio, direção visual e execução técnica. O Visual System V3 e o rig V4 são fontes independentes e não foram alterados por esta migração.

## Fundação congelada

Fundação atual: **STABLE** (2026-09-25).

- `NARRATION_ENGINE = STABLE`
- `WORD_BOUNDARY = STABLE`
- `VOICE_PROFILE = STABLE`
- `VISUAL_SYSTEM_V3 = STABLE`
- `VISUAL_GEOMETRY_CONTRACT_V1 = STABLE`
- `RIG_V4 = STABLE`

`STABLE` significa que tarefas normais de episódio não modificam o componente sem defeito reproduzível ou decisão humana explícita. O status das composições editoriais continua obedecendo aprovação humana individual.

## Ordem de produção

1. `03_ROTEIRO_NARRACAO.md`: beats estáveis e texto falado.
2. Voz definitiva do provider ativo.
3. `03A_AUDIO_TIMING.json`: duração, palavras, pausas e beats medidos no áudio.
4. `04_ROTEIRO_VISUAL.csv`: direção visual usando `beat_ids` e anchors de texto.
5. `05_ASSET_MANIFEST.csv`: proveniência e integridade dos assets.
6. `04A_SCENE_MANIFEST.json`: cenas, eventos e tempos resolvidos automaticamente.
7. SVG, animação, áudio e render.

`03A` e `04A` são arquivos gerados. É proibido corrigi-los manualmente.

## Contrato do 03

Cada beat usa um heading `### B001` e guarda sua narração em blockquote. Horários são apenas estimativas editoriais. IDs aprovados não são renumerados nem reutilizados.

O gerador de voz ignora títulos e notas e sintetiza somente as linhas iniciadas por `>`.

## Contrato do 03A

O provider local Kokoro usa `create_timed()` e permanece fallback explícito. O caminho de produção usa Azure Speech SDK com boundaries reais; qualquer timing local só é usado quando solicitado explicitamente.

Campos de auditoria incluem provider, voz, velocidade, método de timing, hashes do roteiro e do WAV, taxa de amostragem, duração, beats, palavras e pausas inseridas.

```powershell
python scripts/gerar_narracao_local.py --entrada "episodios/CO-001-por-que-ganhar-mais-nao-basta/03_ROTEIRO_NARRACAO.md" --beats B001,B002,B003,B004,B005,B006 --saida "episodios/CO-001-por-que-ganhar-mais-nao-basta/testes/v3_sequencial_s001_s006/narracao_pipeline.wav" --timing-json "episodios/CO-001-por-que-ganhar-mais-nao-basta/03A_AUDIO_TIMING.json" --episodio-id CO-001
```

## Contrato do 04

O CSV criativo não contém segundos absolutos. Cada cena declara:

- `beat_ids` separados por `|`;
- `anchor_start` e `anchor_end` como palavras ou frases exatas;
- layout, destaque, ideia dominante e contexto;
- papel e escala do personagem;
- `asset_ids` separados por `|`;
- eventos em JSON, cada um ancorado em uma palavra ou frase;
- continuidade de entrada e saída.

Um anchor repetido sem qualificação falha. Quando a repetição for intencional, use o sufixo `#N`, por exemplo `normal#2`.

## Contrato do 05

`05_ASSET_MANIFEST.csv` é o inventário canônico de assets. Ele registra tipo, fonte, provider, licença, método de produção, cenas atendidas, versão, hash e status.

`05_PROMPTS_IMAGENS.csv` permanece temporariamente para compatibilidade. O gerador prefere o novo manifesto quando houver linhas `comfyui` ou `external_generation` com prompt; caso contrário, usa o legado e informa o fallback.

## Resolução do 04A

```powershell
python scripts/resolver_timeline_audiovisual.py CO-001 --visual "episodios/CO-001-por-que-ganhar-mais-nao-basta/testes/v3_sequencial_s001_s006/04_ROTEIRO_VISUAL.csv"
```

O resolvedor:

- verifica IDs, headers, fontes e hashes;
- procura anchors somente nos beats declarados;
- rejeita anchors ausentes ou ambíguos;
- resolve eventos em tempos reais;
- usa o próximo anchor de entrada como fronteira visual da cena;
- registra hashes de 03A, 04 e 05 no 04A.

## Prova S001–S006

O piloto é deliberadamente limitado às seis primeiras cenas. O restante do CO-001 não deve ser migrado antes da aprovação humana.

```powershell
python scripts/gerar_teste_sequencial_v3.py
python scripts/exportar_teste_sequencial_v3.py --timeout 120
python scripts/validar_teste_sequencial_v3.py
```

Artefato para revisão: `teste_sequencial_v3_s001_s006_pipeline.webm`.

## Troca futura de provider

O casting Azure é uma etapa posterior e separada. Ao trocar o provider, permanecem iguais os contratos do 03, 04, 05 e do resolvedor. Somente a produção do áudio e do 03A muda; depois disso, o 04A é regenerado a partir dos novos timestamps.

Não misturar a migração estrutural e a troca de TTS na mesma etapa de diagnóstico.
