# Capital Oculto — Art Direction V4

**STATUS: CANDIDATE — SPRINT ESTÁTICO S001–S006**

Esta camada herda integralmente a engenharia do Visual System V3: canvas, grid, paleta, rig V4, beats, anchors, manifests, integridade de assets e timing. Ela substitui somente a linguagem de composição ainda não aprovada.

## Regra central

Uma ideia dominante expressa por uma composição editorial original; ícones de biblioteca apenas apoiam essa composição.

Phosphor pode aparecer em micro-labels, indicadores, botões, marcadores e detalhes de interface. Um ícone de biblioteca nunca pode:

- ser o maior elemento da cena;
- carregar sozinho a metáfora;
- ocupar mais de 10% do canvas;
- aparecer gigante dentro de um card genérico.

## O que deixa de ser padrão

- título grande obrigatório no topo;
- underline decorativo repetido;
- card preto contendo card claro;
- label que apenas descreve literalmente o desenho;
- personagem usado para preencher espaço;
- uma cena totalmente reconstruída a cada corte.

Cards continuam permitidos quando o objeto narrativo for realmente um card, uma interface, um documento ou uma superfície que precise de contêiner.

## Linguagem

A referência é motion graphics editorial: números, relações, proporções e tipografia fazem a informação acontecer. O SVG continua programático, leve e bidimensional.

Cada cena deve combinar três planos gráficos:

1. elemento dominante enorme, possivelmente cortado pelo quadro;
2. informação intermediária que explica a relação;
3. micro-label que orienta sem narrar novamente a imagem.

## Classes visuais

- `data_hero`: número protagonista;
- `system_map`: relações de causa, dependência ou movimento conjunto;
- `transformation`: um estado se transforma em outro;
- `scale`: contraste de proporções;
- `editorial_type`: frase curta é a própria composição.

As classes complementam os layouts A–F; não os substituem no contrato técnico.

## Títulos

Título grande existe somente em turning points editoriais. Cenas de continuidade devem ser compreendidas pelo visual, por labels contextuais e pela transformação preservada.

## Personagem

Toda aparição declara uma função: `reaction`, `scale`, `action`, `cause` ou `continuity`. Se nenhuma delas existir, remover o personagem. O rig V4 continua imutável.

## Sprint atual

S001–S006 serão avaliadas primeiro como frames estáticos, sem áudio e sem animação. Nenhum trabalho nas demais 42 cenas e nenhum casting de voz começam antes da aprovação desses frames.

Critério de passagem: “eu colocaria este frame em um vídeo publicado?”. Se a resposta for não, o frame não recebe animação.
