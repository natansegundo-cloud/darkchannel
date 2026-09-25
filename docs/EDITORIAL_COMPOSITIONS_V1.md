# Capital Oculto — Editorial Compositions V1

**STATUS: APROVAÇÃO PARCIAL — 3 VARIANTES APROVADAS HUMANAMENTE**

## Princípio

A unidade principal de design do Capital Oculto não é o ícone. É a **composição editorial**.

Uma composição editorial é uma estrutura visual completa que expressa um mecanismo narrativo usando escala, hierarquia, tipografia e relação espacial. Ícones de biblioteca (Phosphor) funcionam apenas como apoio — nunca como protagonistas.

## Fluxo de decisão

```
mecanismo narrativo
→ família editorial (via tabela de decisão)
→ variante estrutural (via compatibilidade de conteúdo)
→ conteúdo real (números, labels, personagem)
→ assets auxiliares (ícones, linhas, superfícies)
```

O fluxo contrário — "qual ícone cabe aqui?" — é explicitamente proibido.

## Famílias

### 1. DATA HERO

**Objetivo:** usar número, valor, percentual ou delta como protagonista visual.

O dado ocupa 55–75% da atenção visual. Tudo no canvas existe para dar significado ao número.

| Variante | ID | Estrutura |
|---|---|---|
| Hero lateral | CO-COMP-01A | Número dominante à direita, contexto empilhado à esquerda |
| Hero central | CO-COMP-01B | Número centrado no canvas, contexto mínimo acima e abaixo |
| Hero oversized | CO-COMP-01C | Número cortado pelas bordas do canvas, contexto como anotação |

### 2. MOVING BASELINE

**Objetivo:** mostrar mudança de referência. O que era exceção virou padrão.

O foco não é na passagem do tempo, mas no deslocamento do ponto de comparação.

| Variante | ID | Estrutura |
|---|---|---|
| Baseline horizontal | CO-COMP-04A | Linha horizontal divide novo (acima) e antigo (abaixo, desbotado) |
| Baseline vertical | CO-COMP-04B | Divisão vertical: estado antigo à esquerda, novo à direita |
| Ghost overlay | CO-COMP-04C | Estado novo domina; antigo permanece como sobreposição fantasma |

### 3. SHRINKING SPACE

**Objetivo:** mostrar que uma margem, folga ou liberdade está sendo comprimida.

A compressão deve ser compreendida visualmente antes da leitura de qualquer texto.

| Variante | ID | Estrutura |
|---|---|---|
| Compressão horizontal | CO-COMP-03A | Duas massas se aproximam lateralmente, espremendo espaço central |
| Compressão vertical | CO-COMP-03B | Pressão de cima e de baixo sobre faixa central |
| Duas forças | CO-COMP-03C | Forças nomeadas convergem sobre alvo central (personagem ou valor) |

## Regras de composição

### Ícones

Phosphor Icons continuam sendo a biblioteca oficial. Porém:
- Nenhum ícone pode ser o elemento dominante
- A área visual de um ícone de apoio não deve dominar mais de ~10% da área útil
- Ícones existem como marcadores, indicadores e detalhes

### Personagem

- Fonte única: `assets/characters/capital_oculto_character_rig_v4.svg`
- Aparece somente com função narrativa: REACTION, SCALE, ACTION, CAUSE, CONTINUITY, CONTRAST
- Se remover o personagem não muda o significado: não usar

### Headlines

- Não obrigatórias
- Nunca narrar o que a composição já mostra
- Devem acrescentar interpretação, não descrever o óbvio

### Repetição

- Não usar a mesma variante em cenas consecutivas quando alternativa adequada existir
- Semântica sempre vem primeiro
- Mas evitar aparência de template repetitivo

## Content zones

Cada variante declara zonas fixas com:
- Posição e dimensões (x, y, width, height)
- Tipo de conteúdo
- Limites de caracteres e linhas
- Política de overflow: `REJECT_COMPOSITION`
- Política de safe area: `STRICT` ou `BLEED_ALLOWED`
- `content_format` nas zonas legíveis compatíveis

Se o conteúdo não cabe: escolher outra variante. Nunca diminuir fonte, empurrar elementos ou quebrar grid.

### Safe area policy

- `STRICT`: obrigatório para texto essencial, labels, personagem e números que precisam ser lidos integralmente. A zona inteira deve permanecer dentro da safe area de texto de 96 px.
- `BLEED_ALLOWED`: permitido somente para massas, formas, elementos gráficos e números oversized cujo corte seja uma intenção editorial explícita. Exceder o canvas não invalida automaticamente essa zona.
- Labels e informação que precise ser lida integralmente nunca usam `BLEED_ALLOWED`.

### Formatos de conteúdo

Os formatos iniciais são `currency_short`, `currency_delta`, `percentage`, `plain_number`, `short_label` e `headline`. Eles não medem glyphs nem substituem `max_chars`; apenas impedem conteúdo semanticamente incompatível com a zona.

## Modos de seleção

- `EXPERIMENTAL_TEST`: aceita variantes `APPROVED` e `EXPERIMENTAL`; nunca é produção.
- `PRODUCTION`: aceita somente variantes `APPROVED`.

Os previews S001–S003 nasceram em `EXPERIMENTAL_TEST`. Após aprovação humana do piloto audiovisual, `CO-COMP-01C` v1.1, `CO-COMP-04A` v1.1 e `CO-COMP-03A` v1.1 podem ser resolvidas por `PRODUCTION`. As outras seis variantes permanecem `EXPERIMENTAL`.

## Status

| Status | Significado |
|---|---|
| DRAFT | Em construção |
| EXPERIMENTAL | Pronto para teste, não aprovado |
| APPROVED | Aprovado por humano para produção |
| REJECTED | Descartado |
| DEPRECATED | Substituído por versão posterior |

Status atual: **3 APPROVED** (`01C`, `04A`, `03A`) e **6 EXPERIMENTAL**. A aprovação não alterou geometria, content zones, paleta ou motion.

## Calibração de masters

Parâmetros reutilizáveis substituem correções específicas por cena:

- `DATA_HERO`: `hero_crop_intensity` e `delta_prominence`.
- `MOVING_BASELINE`: `old_state_visibility_ratio`, `baseline_emphasis` e `current_state_dominance`.
- `SHRINKING_SPACE`: `focus_mode`, `gap_dominance` e `result_dominance`.

`SHRINKING_SPACE` aceita dois modos:

- `COMPRESSION_FIRST`: a redução espacial domina e o valor final é consequência.
- `RESULT_FIRST`: o valor final domina e as massas explicam por que ele ficou pequeno.

Masters calibrados nesta rodada:

| Master | Versão | Regra principal |
|---|---:|---|
| CO-COMP-01C | 1.1 | crop moderado e delta secundário forte |
| CO-COMP-04A | 1.1 | baseline enfatizada e estado antigo visível |
| CO-COMP-03A | 1.1 | foco explícito em compressão ou resultado |

## Validação

A validação automática cobre apenas propriedades determinísticas:
- Canvas e safe areas corretos
- Coordenadas dentro dos limites
- Limites de caracteres e linhas
- Paleta válida
- IDs sem duplicação
- Referências e assets existentes

Não existe medição tipográfica real em Python puro. A defesa contra overlap é estrutural (content zones).

## Referências

- Visual System V3: `docs/VISUAL_SYSTEM_V3.md`
- Art Direction V4: `docs/ART_DIRECTION_V4.md`
- Config: `config/visual_compositions.json`
- Regras: `config/visual_composition_rules.json`
- Seleção: `docs/VISUAL_COMPOSITION_SELECTION.md`
