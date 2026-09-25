# Capital Oculto — Expansão controlada S004–S006

Data: 2026-09-24  
Modo de seleção: `EXPERIMENTAL_TEST`  
Escopo: teste estático, sem áudio, motion, Azure ou integração com o pipeline oficial.

## Resultado

### S004

- `narrative_mechanism`: `strong_statement`
- `variants_tested`: `CO-COMP-05A@1`, `CO-COMP-05B@1`
- `selected_candidate`: `CO-COMP-05A@1 — STATEMENT_STACK`
- `status`: `EXPERIMENTAL`
- `reason`: a pilha assimétrica estabelece primeiro “O PROBLEMA”, torna “NÃO É” o evento dominante e fecha em “UMA COMPRA ABSURDA”. A leitura permanece fiel ao beat, funciona sem ícone e preserva melhor a ordem semântica a 25%. A 05B é mais agressiva, porém o grande risco sobre “ABSURDA” compete com a negação e a massa preta aproxima a leitura de uma peça de campanha, não da virada narrativa pedida.

Validação sem áudio: **“não foi uma compra absurda isolada.”**

### S005

- `narrative_mechanism`: `system_relationship`
- `variants_tested`: `CO-COMP-06A@1`, `CO-COMP-06B@1`
- `selected_candidate`: `CO-COMP-06A@1 — PARALLEL_SHIFT`
- `status`: `EXPERIMENTAL`
- `reason`: os três trilhos compartilham uma referência diagonal e terminam deslocados na mesma direção. A relação aparece pela repetição e pelo alinhamento antes da leitura dos labels. A 06B continua válida como master experimental, mas sua massa lateral de renda e suas três saídas se aproximam mais da lógica “driver → outputs”; para este beat, 06A comunica melhor um sistema que se move junto e evita aparência de fluxograma.

Validação sem áudio: **“normal, comparação e despesas fazem parte de um mesmo sistema.”**

### S006

- `narrative_mechanism`: `time_adaptation`
- `variant_tested`: `CO-COMP-04D@1 — CONCEPTUAL_BASELINE`
- `selected_candidate`: `CO-COMP-04D@1`
- `status`: `EXPERIMENTAL`
- `reason`: “EXTRA” aparece como estado anterior reduzido, enquanto a referência diagonal desloca o olhar até “NORMAL”, que domina o estado atual. A construção preserva a gramática de `MOVING_BASELINE`, mas é estruturalmente conceitual e não substitui artificialmente um número por uma palavra na 04A. Não usa calendário nem relógio.

Validação sem áudio: **“o que era extra virou normal.”**

## Expansão criada

Somente os itens autorizados foram adicionados:

- família `EDITORIAL_TYPE`
  - `CO-COMP-05A — STATEMENT_STACK`
  - `CO-COMP-05B — KEYWORD_CONTRAST`
- família `SYSTEM_MAP`
  - `CO-COMP-06A — PARALLEL_SHIFT`
  - `CO-COMP-06B — SHARED_DRIVER`
- família existente `MOVING_BASELINE`
  - `CO-COMP-04D — CONCEPTUAL_BASELINE`

Todas as cinco variantes permanecem `EXPERIMENTAL`. Nenhuma recebeu `APPROVED` ou `MOTION_APPROVED`.

## Regras alteradas

- `strong_statement.primary_family = EDITORIAL_TYPE`.
- `system_relationship.primary_family = SYSTEM_MAP` quando não existe compressão explícita.
- `compression`, `pressure`, `constraint`, `loss_of_space` e `dual_force_squeeze` continuam roteando exclusivamente para `SHRINKING_SPACE`.
- `time_adaptation.primary_family` continua `MOVING_BASELINE`.
- conteúdo monetário de `time_adaptation` continua associado à 04A; conteúdo por palavras conceituais pode usar 04D.
- formatos `keyword` e `short_statement` foram adicionados ao contrato estrutural.

As regras de `accumulation`, os selection modes e os fallbacks não relacionados foram preservados.

## Content zones e segurança

Todas as novas variantes declaram:

- `max_chars` e `max_lines`;
- `content_format` para zonas legíveis;
- `safe_area_policy`;
- `overflow_policy = REJECT_COMPOSITION`;
- `semantic_use`;
- candidatos de entrada, saída e continuidade.

Todo texto usa `STRICT` e permanece dentro da safe area textual de 96 px. Somente linhas, trilhos e massas gráficas usam `BLEED_ALLOWED`.

## Arquivos criados

### Masters oficiais

- `assets/compositions/editorial_type/CO-COMP-05A.svg`
- `assets/compositions/editorial_type/CO-COMP-05B.svg`
- `assets/compositions/system_map/CO-COMP-06A.svg`
- `assets/compositions/system_map/CO-COMP-06B.svg`
- `assets/compositions/moving_baseline/CO-COMP-04D.svg`

Os mesmos cinco arquivos foram copiados automaticamente para `tests/editorial_compositions_v1/masters/`; nenhuma geometria reutilizável foi recriada ou modificada manualmente dentro de uma cena.

### Candidatos e previews

- `tests/editorial_compositions_v1/s004_s006/candidates/s004_CO-COMP-05A.svg`
- `tests/editorial_compositions_v1/s004_s006/candidates/s004_CO-COMP-05B.svg`
- `tests/editorial_compositions_v1/s004_s006/candidates/s005_CO-COMP-06A.svg`
- `tests/editorial_compositions_v1/s004_s006/candidates/s005_CO-COMP-06B.svg`
- `tests/editorial_compositions_v1/s004_s006/candidates/s006_CO-COMP-04D.svg`
- cinco PNGs correspondentes em `tests/editorial_compositions_v1/s004_s006/candidates/previews/`

### Seleção experimental e contact sheets

- `tests/editorial_compositions_v1/s004_s006/selected/s004.svg`
- `tests/editorial_compositions_v1/s004_s006/selected/s005.svg`
- `tests/editorial_compositions_v1/s004_s006/selected/s006.svg`
- `tests/editorial_compositions_v1/contact_sheets/contact_s004_s006_candidates.svg`
- `tests/editorial_compositions_v1/contact_sheets/contact_s004_s006_final.svg`
- `tests/editorial_compositions_v1/contact_sheets/contact_s004_s006_25pct.svg`
- PNGs correspondentes em `tests/editorial_compositions_v1/contact_sheets/previews/`

### Implementação

- `scripts/gerar_expansao_s004_s006.py`

Arquivos atualizados:

- `config/visual_compositions.json`
- `config/visual_composition_rules.json`
- `scripts/gerar_editorial_compositions_v1.py` — somente contratos de validação do catálogo expandido; o gerador legado de S001–S003 não foi executado.

## Validações executadas

- JSON dos dois contratos carregado sem erros.
- catálogo contém exatamente 14 variantes e cinco famílias.
- conjunto `APPROVED` permanece exatamente `01C`, `04A` e `03A`.
- cinco variantes novas validadas como `EXPERIMENTAL`.
- todas as content zones novas passaram nas políticas de formato, overflow e safe area.
- rotas semânticas de `strong_statement`, `system_relationship` e `time_adaptation` passaram.
- 16 SVGs relevantes analisados como XML válido: masters, candidatos, seleção e contact sheets.
- cinco previews renderizados em 1920×1080.
- seleção final conferida em contact sheet e em simulação exata de 480×270 por cena (25%).
- não foi detectado `MASTER_DEFECT`, `SELECTION_DEFECT` ou `CONTENT_DEFECT` bloqueante.

## Limitações

- O teste é exclusivamente estático; candidatos de motion são declarativos e não foram executados.
- Não há medição tipográfica por `bbox`; as travas são estruturais (`content_format`, `max_chars`, `max_lines` e safe area).
- A legibilidade a 25% foi validada visualmente para as ideias dominantes. Micro-labels permanecem deliberadamente secundários.
- Nenhuma das cinco variantes está autorizada para produção antes da aprovação humana.

## NEEDS_NEW_COMPOSITION residual

- Em `EXPERIMENTAL_TEST`: nenhum residual para S004–S006.
- Em `PRODUCTION`: S004, S005 e S006 continuam retornando `NEEDS_NEW_COMPOSITION` enquanto 05A, 06A e 04D permanecerem `EXPERIMENTAL`. Esse bloqueio é intencional e preserva a aprovação humana.

## Stop condition

Execução encerrada após os cinco previews, as três contact sheets e este relatório. Não houve animação, Azure, criação de S007+, nova família adicional, promoção para `APPROVED`, integração de pipeline ou migração do episódio.
