# Piloto Audiovisual S004–S006 + Continuidade Sequencial S001–S006

Status: **EXPERIMENTAL / MOTION_CANDIDATE** (S004–S006) · **APPROVED / REFERENCE** (S001–S003 preservado)  
Data de geração: 2026-09-24  
Projeto: Capital Oculto — Episódio CO-001  

---

## 1. Síntese Executiva

- **TTS Provider:** `azure_speech_rest`
- **Voz:** `pt-BR-AntonioNeural`
- **Idioma:** `pt-BR`
- **Perfil vocal:** `-4% rate`, `0% pitch`, `default volume`
- **Beats processados:** `B004`, `B005`, `B006`
- **Duração S004:** **3.9703s** (0.0000s → 3.9703s)
- **Duração S005:** **16.0146s** (3.9703s → 19.9849s)
- **Duração S006:** **7.6173s** (19.9849s → 27.6022s)
- **Duração audiovisual S004–S006:** **27.6022s**
- **Duração reutilizada S001–S003:** **18.6990s**
- **Duração total sequencial S001–S006:** **46.3012s**
- **Música:** Nenhuma (voz + motion rigoroso)
- **SFX:** Nenhum
- **BLOCKED_BY_MASTER:** Nenhum

---

## 2. Cenas e Composições

| Cena | Beat(s) | Família | Variante | Versão | Status Contrato | Status Motion | Início | Fim | Duração |
|---|---|---|---|:---:|:---:|:---:|---:|---:|---:|
| **S001** | B001 | DATA_HERO | CO-COMP-01C | 1.1 | APPROVED | MOTION_APPROVED | 0.000s | 4.242s | 4.242s |
| **S002** | B002 | MOVING_BASELINE | CO-COMP-04A | 1.1 | APPROVED | MOTION_APPROVED | 4.242s | 12.044s | 7.801s |
| **S003** | B002+B003 | SHRINKING_SPACE | CO-COMP-03A | 1.1 | APPROVED | MOTION_APPROVED | 12.044s | 18.699s | 6.656s |
| **S004** | B004 | EDITORIAL_TYPE | CO-COMP-05A | 1.0 | EXPERIMENTAL | MOTION_CANDIDATE | 0.000s | 3.970s | 3.970s |
| **S005** | B005 | SYSTEM_MAP | CO-COMP-06A | 1.0 | EXPERIMENTAL | MOTION_CANDIDATE | 3.970s | 19.985s | 16.015s |
| **S006** | B006 | MOVING_BASELINE | CO-COMP-04D | 1.0 | EXPERIMENTAL | MOTION_CANDIDATE | 19.985s | 27.602s | 7.617s |

*Nota sobre a timeline concatenada S001–S006:*
- S001: 0.000s – 4.242s (4.242s)
- S002: 4.242s – 12.044s (7.802s)
- S003: 12.044s – 18.699s (6.655s)
- S004: 18.699s – 22.669s (3.970s)
- S005: 22.669s – 38.684s (16.015s)
- S006: 38.684s – 46.301s (7.617s)

---

## 3. Anchors Resolvidos no Áudio Real (B004–B006)

Os tempos foram extraídos deterministicamente pelo detector de fala e alinhador ponderado de tokens do Azure Speech REST:

### S004 — Beat B004
*Texto: “Você não precisa ter feito nenhuma compra absurda.”*
- `scene_entry` → “Você” → 0.0945s – 0.3487s
- `negation` → “não precisa” → 0.3487s – 0.9842s
- `purchase` → “compra” → 1.9375s – 2.3188s
- `absurd` → “absurda” → 2.3188s – 2.9544s
- `structural_close` → “absurda” (end edge) → 2.9544s

### S005 — Beat B005
*Texto: “Mesmo assim, três coisas podem mudar junto com a renda: o que parece normal, com quem você se compara e quantas despesas passam a contar com aquele dinheiro. Quando as três se movem ao mesmo tempo, um aumento real pode ficar quase invisível.”*
- `scene_entry` → “Mesmo assim” → 4.0815s – 4.8934s
- `driver_context` → “renda” → 7.0298s – 7.4856s
- `track_normal` → “normal” → 8.2690s – 8.7960s
- `track_comparison` → “compara” → 9.7218s – 10.2203s
- `track_expenses` → “despesas” → 10.8612s – 11.4309s
- `shared_reference` → “movem” → 14.8493s – 15.2054s
- `parallel_shift` → “tempo” → 15.7039s – 16.1596s
- `system_settle` → “invisível” → 18.0825s – 18.9370s

### S006 — Beat B006
*Texto: “A primeira peça é uma habilidade útil do cérebro que, neste caso, parece uma pequena traição: adaptação.”*
- `scene_entry` / `old_state` → “A primeira peça” → 20.0829s – 21.0825s
- `baseline_rise` → “cérebro” → 22.5820s – 23.0818s
- `extra_deemphasis` → “traição” → 25.2810s – 25.8808s
- `new_normal` → “adaptação” → 25.8808s – 26.7376s
- `confirmation` → “adaptação” (end edge) → 26.7376s

---

## 4. Eventos Dominantes de Motion

### S004 — STATEMENT_STACK (CO-COMP-05A)
*Objetivo narrativo: Reveal semântico da negação.*
- `S004-E01` · `reveal` · 0.0945–0.3445s · Estabelecer “O PROBLEMA” e a tag âmbar de forma discreta.
- `S004-E02` · `reveal_dominant` · 0.3487–0.9842s · “NÃO É” entra como elemento dominante com maior peso visual, tamanho 270px em tom âmbar `#E8A33D`.
- *(Pausa visual)* · 0.9842–1.9375s · A negação permanece fixa durante a locução intermediária, ancorando o conceito na mente do espectador.
- `S004-E03` · `reveal` · 1.9375–2.3188s · “UMA COMPRA” aparece na linha do raciocínio.
- `S004-E04` · `reveal` · 2.3188–2.9544s · “ABSURDA” fecha a afirmação editorial em tipografia display de 176px.
- `S004-E05` · `expand_and_lock` · 2.9544–3.3044s · Sublinhado estrutural preto de 920px se expande da esquerda para a direita, travando a composição.

### S005 — PARALLEL_SHIFT (CO-COMP-06A)
*Objetivo narrativo: Sistema conjunto em movimento paralelo.*
- `S005-E01` · `establish` · 4.0815–4.8934s · Estabelecer a base geométrica dos três trilhos horizontais no canvas.
- `S005-E02` · `reveal` · 7.0298–7.4856s · Revelar o driver contextual superior “QUANDO A RENDA SOBE”.
- `S005-E03` · `stagger_reveal` · 8.2690–8.7960s · Estabelecer primeira variável do sistema (“NORMAL”).
- `S005-E04` · `stagger_reveal` · 9.7218–10.2203s · Estabelecer segunda variável do sistema (“COMPARAÇÃO”).
- `S005-E05` · `stagger_reveal` · 10.8612–11.4309s · Estabelecer terceira variável do sistema (“DESPESAS”).
- `S005-E06` · `traverse_and_align` · 14.8493–15.7039s · Diagonal lima de 30px surge e conecta os três trilhos como referência compartilhada do sistema.
- `S005-E07` · `parallel_shift` · 15.7039–17.3703s · Os blocos nos três trilhos se deslocam em paralelo respondendo à referência compartilhada com sutil stagger harmônico.
- `S005-E08` · `settle_and_confirm` · 18.0825–18.9370s · Assentar o sistema no estado final e confirmar com o label “O SISTEMA SE MOVE JUNTO”.

### S006 — CONCEPTUAL_BASELINE (CO-COMP-04D)
*Objetivo narrativo: Mudança de referência (o que era EXTRA virou NORMAL).*
- `S006-E01` · `establish_dominant` · 20.0829–21.0825s · “ANTES / EXTRA” estabelece o estado anterior como presença visual dominante inicial (opacidade 1.0).
- `S006-E02` · `ascend_and_transfer` · 22.5820–24.1386s · A referência diagonal sobe e a linha guia lima superior desenha a elevação do patamar.
- `S006-E03` · `deemphasize` · 25.2810–25.8808s · “EXTRA” perde peso e opacidade (reduzindo de 1.0 para 0.40), tornando-se registro anterior.
- `S006-E04` · `lock_dominant` · 25.8808–26.7376s · “AGORA / NORMAL” emerge no novo nível e trava como estado dominante (252px, display) junto com a barra horizontal lima de 804px.
- `S006-E05` · `reveal` · 26.7376–27.1876s · Confirmação secundária com “VIROU REFERÊNCIA” e label inferior “O GANHO NÃO SUMIU • A BASE MUDOU”.

---

## 5. Transições e Continuidade

1. **S003 → S004 (Transição Editorial)**:
   - S003 encerra com as duas massas escuras comprimidas e o residual de R$ 20.
   - S004 inicia com redução contextual e fade do espaço residual, introduzindo a barra âmbar de "O PROBLEMA" sem corte morto e sem wipe intrusivo.
2. **S004 → S005 (Mecanismo Sistêmico)**:
   - A estrutura tipográfica de S004 desliza suavemente em fade/slide para a esquerda enquanto os três trilhos pretos de S005 entram progressivamente pela direita/centro. Não há frame vazio.
3. **S005 → S006 (Transmissão de Eixo)**:
   - S005 termina com a diagonal lima conectando os três trilhos deslocados. S006 aproveita exatamente a mesma direção e ângulo de inclinação ascendente para iniciar a baseline diagonal de transição conceitual.

---

## 6. Processamento de Áudio e Continuidade Vocal

- **WAVs brutos:** gravados por beat em `tests/audiovisual_pilot_s001_s006/audio/raw/` (`b004_azure_antonio.wav`, `b005_azure_antonio.wav`, `b006_azure_antonio.wav`, `narration_raw.wav`).
- **WAV processado:** `tests/audiovisual_pilot_s001_s006/audio/processed/narration_azure_antonio.wav`.
- **Formato:** PCM mono, 24 kHz, 16 bits.
- **High-pass filter:** 70.0 Hz (1-pole IIR determinístico).
- **Compressor:** threshold -18.0 dBFS, ratio 2.5:1.
- **Normalização de pico:** -1.0 dBFS.
- **Limiter:** ceiling -0.8 dBFS.
- **Continuidade de Loudness:**
  - S001–S003: Peak = -1.00 dBFS, RMS = -14.74 dBFS
  - S004–S006: Peak = -1.00 dBFS, RMS = -15.13 dBFS
  - Diferença RMS de apenas **0.39 dB**, assegurando consistência vocal imperceptível entre blocos.

---

## 7. Arquivos Reutilizados e Arquivos Novos

### Arquivos Reutilizados (Intocados)
- `tests/audiovisual_pilot_s001_s003/renders/capital_oculto_pilot_s001_s003_azure_antonio.webm` (Render de referência aprovado humanamente, 18.699s)
- `tests/audiovisual_pilot_s001_s003/audio/processed/narration_azure_antonio.wav`
- `tests/editorial_compositions_v1/s004_s006/selected/s004.svg`
- `tests/editorial_compositions_v1/s004_s006/selected/s005.svg`
- `tests/editorial_compositions_v1/s004_s006/selected/s006.svg`
- `config/visual_compositions.json`
- `config/narrators.json`

### Arquivos Novos Gerados
- `tests/audiovisual_pilot_s001_s006/audio/raw/` (WAVs brutos de B004, B005, B006 e raw combinado)
- `tests/audiovisual_pilot_s001_s006/audio/processed/narration_azure_antonio.wav`
- `tests/audiovisual_pilot_s001_s006/timing/03A_AUDIO_TIMING.json`
- `tests/audiovisual_pilot_s001_s006/manifest/scene_manifest.json` (Manifest experimental)
- `tests/audiovisual_pilot_s001_s006/scenes/motion_spec.json`
- `tests/audiovisual_pilot_s001_s006/player.html`
- `tests/audiovisual_pilot_s001_s006/player_sequencial.html`
- `tests/audiovisual_pilot_s001_s006/renders/capital_oculto_pilot_s004_s006_azure_antonio.webm` (Render S004–S006, 27.6022s)
- `tests/audiovisual_pilot_s001_s006/renders/capital_oculto_pilot_s004_s006_azure_antonio_silent.webm` (Render silent S004–S006, 27.6022s)
- `tests/audiovisual_pilot_s001_s006/renders/capital_oculto_pilot_s001_s006_azure_antonio.webm` (Render sequencial completo S001–S006, 46.3012s)
- `tests/audiovisual_pilot_s001_s006/renders/render_metadata.json`
- `scripts/gerar_piloto_audiovisual_s004_s006.py`
- `scripts/exportar_piloto_audiovisual_s004_s006.py`
- `scripts/concatenar_piloto_s001_s006.py`
- `scripts/validar_piloto_audiovisual_s001_s006.py`

---

## 8. Resultados da Validação

Todas as 10 verificações de conformidade foram aprovadas:
1. **Ordem de Beats:** B001 → B002 → B003 → B004 → B005 → B006 verificada e preservada.
2. **Status de Contrato:** S001–S003 permanecem `APPROVED` / `MOTION_APPROVED`; S004–S006 permanecem `EXPERIMENTAL` / `MOTION_CANDIDATE`. Nenhum master foi alterado.
3. **Ausência de Gaps:** Ambas as timelines (interna e sequencial) contínuas, sem buracos ou descontinuidades.
4. **Ausência de Frame Preto:** Transições desenhadas sem tela vazia entre blocos.
5. **Eventos de Motion:** 100% dos eventos ancorados com limites de tempo estritamente dentro dos beats correspondentes.
6. **Continuidade Vocal e de Loudness:** Parâmetros idênticos de compressão, limitação e pico (-1.0 dBFS), diferença RMS de 0.39 dB.
7. **Resolução e FPS:** 1920×1080 @ 30 fps em todos os renders.
8. **Integridade de Formato:** WebM (VP9 + Opus), sem perda de sincronia.
9. **Duração Sequencial Exata:** 46.3012s conferida via metadata e inspeção de clusters.
10. **Segurança de Credenciais:** Nenhum secret Azure vazado nos manifestos, códigos ou logs.

---

## 9. Limitações Técnicas Documentadas

- **Word Boundaries:** O endpoint REST síncrono do Azure Speech não retorna marcações temporais de palavras individuais em nível de fonemas; os boundaries internos usam alinhamento determinístico ponderado por peso de token dentro do envelope de fala detectado no áudio real.
- **Concatenação Local Sem FFmpeg:** A concatenação local de S001–S003 com S004–S006 foi realizada através do player de concatenação headless com MediaRecorder, decodificação dos áudios originais diretamente no Web Audio API a 48 kHz e comutação instantânea de frames no canvas, sem dependência de ferramentas externas como FFmpeg.
- **Status das Variantes:** `CO-COMP-05A`, `CO-COMP-06A` e `CO-COMP-04D` continuam marcadas como `EXPERIMENTAL` com `motion_status: "MOTION_CANDIDATE"`. A aprovação final para produção depende exclusivamente da decisão humana após revisão deste piloto sequencial.

---

## 10. Conclusão e Stop Condition

O primeiro teste sequencial S001–S006 está concluído e validado com sucesso. Todos os artefatos foram criados sem alteração de masters, sem criação de novas famílias/variantes e sem acréscimo de trilhas musicais.

A próxima etapa é a revisão humana assistindo ao vídeo:  
`tests/audiovisual_pilot_s001_s006/renders/capital_oculto_pilot_s001_s006_azure_antonio.webm`.
