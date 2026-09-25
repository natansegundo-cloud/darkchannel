# Capital Oculto — Visual Library V1

**STATUS: EXPERIMENTAL — PROTÓTIPO ESTÁTICO — NÃO INTEGRADO À PRODUÇÃO**

Esta biblioteca expande o Capital Oculto sem substituir o Visual System V3, a Art Direction V4, o rig V4, os assets V3 ou o pipeline audiovisual. Sua função é oferecer composições editoriais reutilizáveis para números, relações, progressões, transformações, escalas e mecanismos.

O teste desta versão termina nos frames estáticos S001–S006 em `tests/visual_library/s001_s006/`. Integração com cenas oficiais, áudio, animação e migração do CO-001 dependem de aprovação humana e de uma tarefa separada.

## Princípio central

**Ícones não são protagonistas.**

Phosphor continua sendo a biblioteca principal de ícones de apoio. Um ícone isolado não pode carregar a metáfora dominante nem ocupar mais de aproximadamente 10% da área útil. A cena deve procurar primeiro uma relação editorial que mostre o mecanismo.

Ordem obrigatória de escolha:

1. metáfora específica da biblioteca;
2. componente editorial adequado;
3. composição baseada em dado ou número;
4. transformação que explique a ideia;
5. personagem, somente quando acrescentar significado;
6. ícone de apoio, somente depois das opções anteriores.

Exemplos:

- tempo → timeline, progressão ou transformação acumulativa;
- dinheiro → counter, fluxo, barra, stack ou comparação numérica;
- pressão → compressão espacial ou redução proporcional;
- adaptação → deslocamento de baseline ou ponto de referência.

## Contrato visual herdado

- Canvas: `1920 × 1080`.
- Safe area absoluta: `64 px`.
- Safe area recomendada para texto: `96 px`.
- Paleta: `#111111`, `#C4E538`, `#E8A33D`, `#F4F3EF`, `#D9D9D4`.
- Regra de cor: fundo + preto + no máximo um destaque semântico.
- Traços: 6 px principal, 4 px secundário e 3 px de detalhe.
- Linecap e linejoin: `round`.
- Elemento dominante: aproximadamente 55% a 75% da área útil.
- Uma ideia dominante e, no máximo, um elemento de contexto.

O Visual System V3 permanece a fonte de verdade para regras gerais. Este documento não o modifica.

## Arquitetura dos assets

Cada fonte SVG contém exatamente um `<symbol>` com `viewBox="0 0 1200 700"`. O ID segue o padrão:

```text
vl-<nome-semântico>-v1
```

Os symbols não contêm texto nem dependem de fontes. Números, palavras e labels pertencem à composição da cena, permanecendo editáveis e contextualizados. O asset é incorporado mecanicamente a partir de sua fonte oficial e instanciado por `<use>`.

É proibido:

- redesenhar ou corrigir a geometria dentro de uma cena;
- manter uma cópia local modificada;
- converter a cena inteira em symbol por padrão;
- usar filtros pesados, texto rasterizado ou assets externos não versionados;
- criar card decorativo para abrigar um componente que funciona diretamente no canvas.

O catálogo `config/visual_library.json` registra, para cada asset, categoria, tipo visual, uso semântico, destaque permitido, compatibilidade com personagem e animação, tamanho preferido, fonte, versão e hash SHA-256.

## Tipos visuais oficiais

- `DATA_HERO`: número ou magnitude é o protagonista.
- `SYSTEM_MAP`: relações e dependências formam um sistema.
- `TRANSFORMATION`: um estado se torna outro.
- `SCALE`: proporção e contraste de magnitude.
- `EDITORIAL_TYPE`: texto curto participa da composição dominante.
- `TIMELINE`: passagem de tempo e progressão.
- `COMPARISON`: dois estados ou magnitudes em contraste.
- `PROGRESS`: preenchimento, avanço ou aproximação de limite.
- `CHARACTER_INTERACTION`: composição em que a ação do personagem é necessária para o mecanismo.

## Categorias V1

| Categoria | Função | Quantidade |
|---|---|---:|
| Counters | valores, deltas e saldos | 5 |
| Bars | proporção linear e consumo | 3 |
| Meters | limiar e estado | 2 |
| Timelines | passagem de tempo | 4 |
| Comparisons | contraste direto | 4 |
| Stacks | acúmulo e pressão | 4 |
| Flows | sistemas e relações | 5 |
| Scales | referência e magnitude | 4 |
| Typography | estruturas editoriais sem glyphs embutidos | 4 |
| Metaphors | mecanismos financeiros recorrentes | 6 |
| **Total de SVGs** |  | **41** |

O total de 41 preserva todos os recursos do inventário inicial sugerido. As sete receitas de movimento são metadados separados e não entram nessa contagem.

## Personagem

Única fonte permitida:

```text
assets/characters/capital_oculto_character_rig_v4.svg
```

O rig não é parte desta biblioteca e não foi modificado. O personagem só entra quando cumprir `REACTION`, `ACTION`, `SCALE`, `CAUSE`, `CONTINUITY` ou `CONTRAST`. A função deve ser declarada no manifesto da cena. Sem função, não usar personagem.

## Cards

Card é objeto semântico, não solução de layout. É permitido apenas quando representa documento, extrato, notificação, interface, objeto físico ou agrupamento lógico indispensável.

É proibido o padrão decorativo:

```text
fundo → card → outro card → ícone
```

## Movimento

`assets/motion/` contém apenas receitas declarativas e ainda não executáveis. Elas registram tipos visuais elegíveis, faixa de duração e exigência de anchor de áudio. Não existe integração com o pipeline nesta etapa.

As receitas obedecem às regras já vigentes:

- o áudio determina o timing final;
- apenas um movimento dominante por vez;
- todo movimento enfatiza uma palavra, número, mudança ou conclusão;
- carry-over preserva continuidade quando a narrativa desenvolve a mesma ideia.

## Teste S001–S006

| Cena | Classe | Asset dominante | Personagem |
|---|---|---|---|
| S001 | `DATA_HERO` | `before-after-number-v1` | não |
| S002 | `TIMELINE` | `month-progression-v1` | não |
| S003 | `TRANSFORMATION` | `shrinking-surplus-v1` | sim — `SCALE` |
| S004 | `SYSTEM_MAP` | `three-variable-flow-v1` | não |
| S005 | `TRANSFORMATION` | `fixed-cost-pressure-v1` | não |
| S006 | `TRANSFORMATION` | `reference-point-shift-v1` | não |

Os seis arquivos são estáticos, não substituem cenas oficiais e não contêm Phosphor porque nenhum ícone era necessário para explicar os mecanismos.

## Gate de aprovação humana

Avaliar cada frame:

1. parado;
2. sem narração;
3. no contact sheet a 25%;
4. com compreensão em aproximadamente dois segundos;
5. perguntando: “isto parece motion editorial profissional ou slide de apresentação?”.

Se parecer slide, ajustar a composição do protótipo. Não alterar o Visual System V3, o rig V4 ou o pipeline para acomodar uma cena.

Somente depois da aprovação explícita:

1. planejar a integração em tarefa separada;
2. resolver como o pipeline selecionará e incorporará assets;
3. validar animação contra anchors narrativos;
4. manter a troca de provider TTS fora dessa integração.
