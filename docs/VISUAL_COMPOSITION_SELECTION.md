# Capital Oculto — Seleção de composição visual

**STATUS: EXPERIMENTAL**

## Processo de seleção

### 0. Declarar o modo

- `EXPERIMENTAL_TEST`: permite `EXPERIMENTAL` e `APPROVED`; usado somente em testes isolados.
- `PRODUCTION`: permite exclusivamente `APPROVED`.

Uma variante `EXPERIMENTAL` nunca pode entrar no pipeline oficial. O piloto S001–S003 usa `EXPERIMENTAL_TEST`.

### 1. Identificar o mecanismo narrativo

Consultar `config/visual_composition_rules.json`. Cada beat do roteiro deve mapear para um dos mecanismos documentados:

- `surprising_number`
- `state_change`
- `progressive_loss`
- `time_adaptation`
- `accumulation`
- `system_relationship`
- `two_forces`
- `scale_difference`
- `strong_statement`
- `captured_flow`
- `comparison`
- `baseline_shift`

### 2. Determinar família primária

A tabela de decisão indica a família primária e as secundárias para cada mecanismo. Usar a primária por padrão. Usar secundária apenas quando:

- A variante primária foi usada na cena anterior
- O conteúdo específico se encaixa melhor na secundária
- A primária não possui variante compatível com o conteúdo

### 3. Selecionar variante

Dentro da família, escolher a variante cujas `content_zones` comportem o conteúdo real. Verificar:

- `max_chars` suficiente para os textos
- `max_lines` suficiente
- `content_type` compatível com o que será exibido
- `supports_character` se o personagem for necessário

Se nenhuma variante comporta o conteúdo: a composição é `REJECT_COMPOSITION`. Nunca adaptar o grid.

Para `SHRINKING_SPACE`, declarar também o foco:

- fala enfatiza a margem encolhendo → `COMPRESSION_FIRST`;
- fala enfatiza quanto restou → `RESULT_FIRST`.

No piloto calibrado, S002 usa `CO-COMP-04A` porque a baseline horizontal comunica a mudança de referência com mais clareza que o overlay 04C. S003 usa `CO-COMP-03A` com `COMPRESSION_FIRST`.

Antes da seleção, validar em cada zone:

- `safe_area_policy=STRICT`: a zona inteira deve permanecer dentro da safe area de texto de 96 px;
- `safe_area_policy=BLEED_ALLOWED`: o corte pode ultrapassar canvas somente para forma, massa ou oversized intencional;
- `content_format`: precisa aceitar o tipo real do conteúdo;
- `max_chars` e `max_lines`: continuam sendo travas estruturais adicionais.

### 4. Verificar regra de não-repetição

Se a cena anterior usou a mesma variante E existe outra variante semanticamente adequada: trocar.

Se a cena anterior usou a mesma família (variante diferente): aceitável desde que a estrutura visual mude perceptivelmente.

### 5. Verificar continuidade

Consultar `continuity_candidates` da composição escolhida. Pelo menos um elemento de continuidade deve conectar com a cena anterior, ou o corte total deve ser justificado.

## Quando nenhuma família serve

Se o mecanismo narrativo indica `NEEDS_NEW_COMPOSITION`:

- Registrar a necessidade no relatório
- Não improvisar layout genérico
- Priorizar para o próximo sprint de composições

Regras específicas deste piloto:

- `strong_statement` sempre retorna `NEEDS_NEW_COMPOSITION` enquanto não existir `EDITORIAL_TYPE`.
- `system_relationship` só usa `SHRINKING_SPACE` em `compression`, `pressure`, `constraint`, `loss_of_space` ou `dual_force_squeeze`. Feedback, rede, dependência e relações com mais de dois elementos sem compressão retornam `NEEDS_NEW_COMPOSITION`.
- `accumulation` só usa `SHRINKING_SPACE` quando o acúmulo consome um recurso limitado. Se o total final for a ideia dominante, usar `DATA_HERO`; caso contrário, retornar `NEEDS_NEW_COMPOSITION`.

## Regras imutáveis

- Composições EXPERIMENTAL não entram no pipeline oficial
- Composições APPROVED exigem aprovação humana
- Nunca diminuir fonte para caber conteúdo
- Nunca reposicionar zones dinamicamente
- Nunca usar ícone como elemento dominante
- Nunca adicionar personagem sem função declarada
