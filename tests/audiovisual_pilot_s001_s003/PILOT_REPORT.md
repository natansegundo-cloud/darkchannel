# Piloto audiovisual S001–S003

Status: **APPROVED / PRODUCTION REFERENCE / APROVADO HUMANAMENTE**

Validado em: 2026-09-24T20:12:14-03:00

## Síntese

- Provider TTS: `azure_speech_rest`
- Narrador: `capital_oculto_narrator_v1`
- Voz: `pt-BR-AntonioNeural`
- Idioma: `pt-BR`
- Duração total real: **18.800s**
- Leading blank removido no render: **0.101s**
- Duração apresentada: **18.699s**
- Beats: `B001`, `B002`, `B003`
- Música: nenhuma
- SFX: nenhum
- `AZURE_CONFIG_FOUND=true`

## Cenas

| Cena | Beats | Início | Fim | Duração | Família | Variante | Focus mode |
|---|---|---:|---:|---:|---|---|---|
| S001 | B001 | 0.000s | 4.242s | 4.242s | DATA_HERO | CO-COMP-01C v1.1 | — |
| S002 | B002 | 4.242s | 12.044s | 7.801s | MOVING_BASELINE | CO-COMP-04A v1.1 | — |
| S003 | B002 + B003 | 12.044s | 18.800s | 6.756s | SHRINKING_SPACE | CO-COMP-03A v1.1 | COMPRESSION_FIRST |

## Anchors resolvidos

### S001

- `scene_entry` → “Você recebe a mensagem” → 0.101s
- `counter_start` → “seu salário” → 1.652s
- `counter_settle` → “aumentou” → 2.377s
### S002

- `old_state` → “Por algumas semanas” → 4.377s
- `current_state` → “finalmente sobra” → 5.805s
- `baseline_shift` → “Três meses depois” → 7.202s
- `old_deemphasis` → “você está outra vez” → 8.474s
- `new_normal` → “conferindo o saldo” → 9.716s
### S003

- `scene_entry` → “vinte reais” → 12.044s
- `compression_start` → “O aumento era real” → 14.208s
- `right_pressure` → “Então por que” → 15.777s
- `compression_end` → “folga sumiu” → 16.851s

Os limites dos beats e da fala vêm dos WAVs realmente retornados pelo Azure. O endpoint REST síncrono não fornece word boundaries; por isso, os tempos internos de palavras usam alinhamento determinístico ponderado dentro do sinal de fala detectado. Nenhum segundo foi escrito manualmente no roteiro.

## Eventos dominantes

### S001 — salary_counter

- `S001-E01` · `reveal` · 0.101–0.421s · estabelecer R$ 3.500 como estado inicial
- `S001-E02` · `counter` · 1.652–2.377s · materializar o aumento de 3.500 para 4.200
- `S001-E03` · `reveal_and_settle` · 2.377–2.657s · assentar o valor final e revelar + R$ 700
### S002 — baseline_translation

- `S002-E01` · `reveal` · 4.377–4.717s · estabelecer a referência antiga de R$ 3.500
- `S002-E02` · `reveal` · 5.805–6.145s · preservar R$ 4.200 como estado atual
- `S002-E03` · `translate_up` · 7.202–8.474s · mover fisicamente a referência para o novo patamar
- `S002-E04` · `deemphasize` · 8.474–8.894s · reduzir a presença da referência antiga
- `S002-E05` · `reveal` · 9.716–10.066s · estabilizar R$ 4.200 como novo normal
### S003 — gap_compression

- `S003-E01` · `establish` · 12.044–12.404s · mostrar folga inicial antes da compressão
- `S003-E02` · `advance` · 14.208–15.777s · iniciar a perda de espaço por gastos fixos
- `S003-E03` · `advance` · 15.777–16.851s · completar a compressão com gastos novos
- `S003-E04` · `settle` · 16.851–17.171s · assentar R$ 20 como consequência

## Continuidade

- S001 → S002: `R$ 4.200` persiste e reduz de escala até o estado atual.
- S002 → S003: `RENDA R$ 4.200` persiste como contexto enquanto a baseline dá lugar à compressão.
- Não existe frame vazio entre cenas nem transição chamativa.

## Processamento de áudio

- Formato intermediário: WAV PCM mono, 24 kHz, 16 bits.
- High-pass: 70.0 Hz.
- Compressor: threshold -18.0 dBFS, ratio 2.5:1.
- Normalização de pico: -1.0 dBFS.
- Limiter: -0.8 dBFS.
- Implementação: `python_stdlib_deterministic_pcm`; quantidade de amostras e duração preservadas.

## Renders

- Audiovisual: `tests/audiovisual_pilot_s001_s003/renders/capital_oculto_pilot_s001_s003_azure_antonio.webm` — 1920×1080, VP8/VP9 + Opus.
- Sem áudio: `tests/audiovisual_pilot_s001_s003/renders/capital_oculto_pilot_s001_s003_azure_antonio_silent.webm` — 1920×1080, VP8/VP9, sem faixa Opus.

## Validações aprovadas

- exatamente três variantes `APPROVED`/`MOTION_APPROVED`; as outras seis permanecem `EXPERIMENTAL`;
- `production_allowed=true` somente para a referência aprovada;
- leading blank removido por offset global até a primeira fala, sem alterar tempos internos;
- versões 1.1 e `COMPRESSION_FIRST` conferidos;
- anchors encontrados uma única vez e resolvidos;
- timestamps e palavras monotônicos;
- cenas contínuas, sem duração negativa;
- eventos dentro da cena e do áudio;
- WAV presente, íntegro e com duração real conferida;
- canvas 1920×1080 e zonas `STRICT` dentro da safe area textual;
- masters fontes presentes e conferidos por SHA-256;
- WebM audiovisual com Opus e WebM silent sem faixa de áudio;
- nenhum segredo Azure encontrado em código, JSON, logs, Markdown ou metadata.

## Erros encontrados

Nenhum erro bloqueante permaneceu após a validação.

## Limitações

- Word boundaries são aproximações determinísticas ancoradas nos limites reais do áudio, pois o endpoint REST síncrono usado não retorna eventos de palavra.
- O processamento de voz é leve e determinístico em PCM; FFmpeg não estava disponível e nenhuma suíte foi instalada.
- A qualidade editorial e vocal foi aprovada humanamente neste piloto; a expansão de novas cenas continua sujeita a plano separado.

## BLOCKED_BY_MASTER

Nenhum.

## Stop condition

O trabalho termina neste piloto. S004+, pipeline oficial, música, biblioteca e demais variantes não foram alterados.
