# Capital Oculto — Visual System V3

Este documento é a fonte de verdade visual para a migração das 48 cenas do `CO-001`.

**SYSTEM STATUS: STABLE — FUNDAÇÃO VALIDADA**

O V1 está preservado e o V2 é histórico; nenhum deles deve ser sobrescrito pela migração. O V3 é a fundação visual estável; cada composição ainda depende de aprovação humana e dos contratos geométricos aplicáveis.

## Camada de direção de arte

A engenharia deste documento permanece válida, mas a linguagem de composição é governada pela camada candidata `docs/ART_DIRECTION_V4.md`. O sprint V4 existe porque o primeiro teste sequencial provou timing, rig e integridade, mas não atingiu o acabamento editorial necessário.

Até a aprovação dos frames estáticos S001–S006, não animar novamente o trecho, não migrar as demais cenas e não iniciar casting de voz.

## Canvas e grid

- Canvas: `1920x1080`, long-form 16:9.
- Safe area absoluta: 64 px.
- Safe area recomendada para texto: 96 px.
- Grid: oito colunas de 196 px, com gutters de 32 px.
- Escala de espaçamento: 16, 24, 32, 48, 64 e 96 px.

## Paleta e semântica

| Uso | Cor | Hex |
|---|---|---|
| Personagem, texto e estrutura | Preto | `#111111` |
| Dinheiro, positivo, base e conclusão favorável | Lima | `#C4E538` |
| Atenção, mudança, aumento e ação | Âmbar | `#E8A33D` |
| Fundo | Off-white | `#F4F3EF` |
| Informação secundária | Cinza | `#D9D9D4` |

Cada cena usa o fundo, o preto e somente um destaque semântico. O cinza pode aparecer apenas como informação secundária e não conta como novo foco. Lima e âmbar nunca competem.

O rig possui uma gravata lima imutável. Portanto, cenas com personagem usam lima como destaque padrão e não introduzem âmbar. Cenas sem personagem podem usar âmbar quando a ideia for mudança, alerta ou ação.

## Tipografia

- Título: 72–96 px, peso 800–900.
- Texto secundário: 36–48 px, peso 600–800.
- Labels: 24–30 px, peso 600–800.
- Frases curtas; nunca depender de parágrafos na tela.
- Títulos grandes usam tracking levemente negativo.

## Traço e cantos

- Traço principal: 6 px.
- Traço secundário: 4 px.
- Detalhe: 3 px.
- Linecap e linejoin: `round`.
- Cards grandes: raio entre 20 e 24 px.
- Componentes pequenos: raio entre 12 e 16 px.

## Personagem

Fonte única: `assets/characters/capital_oculto_character_rig_v4.svg`.

- Estático: `<use href="#char-base">`.
- Articulado: usar exclusivamente os oito grupos existentes no rig.
- `char-base` é o único symbol do personagem.
- Nunca redesenhar, reinterpretar o rosto, alterar proporções ou criar variantes automaticamente.
- Protagonista: altura visual entre 420 e 520 px.
- Personagem secundário: 280–380 px.
- Evitar qualquer personagem abaixo de 240 px.

O personagem é identidade, não obrigação. Ele aparece quando acrescenta emoção, escala humana, continuidade ou reação. Se a metáfora, o gráfico ou o número forem mais fortes sozinhos, o personagem deve sair da cena.

## Assets e estrutura de cena

Assets reutilizáveis podem existir como symbols:

- `char-base`;
- `icons/*`;
- `components/*`;
- `metaphors/*`.

Cada cena nasce como `<g id="scene-SXXX">` e monta assets por `<use>`. A cena inteira não vira symbol por padrão. As partes corporais do rig V4 permanecem grupos.

Cada arquivo inclui somente os assets usados por aquela cena. Uma cena sem personagem não incorpora o rig em seus `<defs>`.

## Integridade dos assets

Os arquivos em `assets/` são a única fonte de geometria reutilizável.

Ao gerar uma cena, o pipeline pode incorporar nos `<defs>` somente os assets necessários para aquela cena, mas deve copiá-los automaticamente das fontes oficiais. A incorporação é uma operação mecânica: não pode alterar paths, proporções, IDs internos ou estrutura do asset.

É proibido:

- recriar geometria equivalente dentro da cena;
- alterar o path de um asset durante a incorporação;
- manter versões locais modificadas de personagem, ícone, componente ou metáfora;
- corrigir um asset apenas em uma cena.

Alterações em um asset reutilizável acontecem somente no arquivo-fonte oficial. Depois da alteração, todas as cenas afetadas devem ser regeneradas pelo pipeline e seus hashes atualizados no manifesto.

## Regra de composição

Uma ideia dominante expressa por uma composição editorial original; ícones apenas apoiam essa composição. Pode existir no máximo um elemento de contexto.

“Bloco” significa unidade de informação, não quantidade de formas internas. Um gráfico pode conter barras, labels e marcadores e continuar sendo uma única ideia visual.

O elemento dominante deve ocupar aproximadamente 55% a 75% da área útil. Evitar miniaturas espalhadas e grandes vazios sem intenção editorial.

## Layouts oficiais

- A — personagem + metáfora;
- B — metáfora dominante;
- C — gráfico + headline;
- D — comparação A/B;
- E — número dominante + apoio;
- F — progresso ou sequência.

Não repetir o mesmo layout por muitas cenas consecutivas. A sequência deve alternar presença humana, metáfora, dado e movimento.

Antes da geração em lote, cada beat deve declarar seu layout, destaque semântico, ideia dominante, contexto opcional e presença ou ausência do personagem.

## Movimento

- Entrada: 250–400 ms.
- Explicação: 500–900 ms.
- Transição: 250–450 ms.
- Idle: mínimo.

Priorizar fade, translate, scale, draw/reveal, progress fill e counter. Evitar bounce gratuito, wiggle exagerado, rotação aleatória e múltiplas animações dominantes simultâneas.

Somente um elemento executa o movimento dominante por vez.

## Timing narrativo

Os tempos de 250–900 ms são referências de velocidade visual, não durações obrigatórias.

O áudio é a fonte de verdade do timing final. A animação deve ser sincronizada ao beat de narração correspondente. Nenhuma animação começa apenas porque a cena entrou: cada movimento enfatiza uma palavra, número, mudança ou conclusão específica.

Cada cue de movimento deve registrar:

- o trecho ou marcador de áudio que o dispara;
- o alvo visual;
- a ação;
- o tempo inicial e final;
- a função narrativa da ação.

Silêncio e permanência também são decisões de timing. Não preencher todos os intervalos com movimento.

## Continuidade

Nem toda troca de beat exige reconstrução visual total. Sempre que a narrativa desenvolver a mesma ideia, preservar entre cenas consecutivas pelo menos um elemento visual:

- posição;
- objeto;
- número;
- gráfico;
- personagem;
- direção do movimento;
- enquadramento.

Priorizar transformações progressivas, match cuts e evolução do mesmo asset. Evitar a sequência repetitiva `cena entra → tudo some → nova cena entra → tudo some`.

Cada par de cenas consecutivas deve declarar o elemento de continuidade ou justificar explicitamente um corte total.

## Prova sequencial e congelamento

Antes da migração das 48 cenas, produzir um teste com 6–8 cenas reais consecutivas e 20–40 segundos de narração. O trecho deve exercitar personagem, metáfora, dado ou número, transformação visual, reação e conclusão.

Depois da aprovação audiovisual, substituir o status no topo por:

`SYSTEM STATUS: LOCKED FOR CO-001`

Durante a migração, as regras do sistema não podem ser alteradas automaticamente pelo agente. Se uma cena não funcionar dentro do sistema:

1. mudar a composição;
2. mudar o layout;
3. simplificar a metáfora.

Nunca alterar o sistema visual para acomodar uma única cena. Qualquer mudança após o lock exige decisão explícita de projeto, justificativa registrada e nova validação das cenas afetadas.

## Validação

A cena precisa funcionar:

1. parada;
2. sem narração;
3. a 25% do tamanho;
4. compreendida em aproximadamente dois segundos.

Se falhar em qualquer ponto, simplificar. Não corrigir falta de hierarquia adicionando elementos.

## Checklist de aprovação

- [ ] Canvas, safe areas e grid respeitados.
- [ ] Uma ideia dominante e no máximo um contexto.
- [ ] Apenas um destaque semântico.
- [ ] Personagem presente somente quando agrega significado.
- [ ] Escala do personagem dentro da faixa definida.
- [ ] Elemento dominante ocupa espaço editorial real.
- [ ] Texto legível a 25%.
- [ ] Cena compreensível sem áudio em cerca de dois segundos.
- [ ] Rig V4 e ícones usados por referência; geometria não duplicada.
- [ ] Assets incorporados mecanicamente a partir das fontes oficiais, sem alteração de paths.
- [ ] Somente um movimento dominante por vez.
- [ ] Movimentos sincronizados a palavras, números, mudanças ou conclusões da narração.
- [ ] Continuidade declarada com a cena anterior ou corte total justificado.
