# Visual Geometry Contract V1

Contrato reutilizável para o piloto visual S001–S006. Esta camada controla
apenas geometria, proteção tipográfica, rotas, terminação e ordem de desenho;
não altera roteiro, áudio, voz, pacing, paleta ou identidade editorial.

## Tipos e camadas

Os elementos são classificados como `PROTECTED_TYPE`, `STRUCTURAL_LINE`,
`CONNECTOR`, `ARROW`, `TRACK`, `ACCENT_LINE`, `DATA_MASS` ou `BACKGROUND`.
As camadas lógicas são background (0), guias estruturais (10), trilhos e
baselines (20), massas (30), acentos (40), tipografia principal (50), labels
(60) e ênfase temporária (70). Tipografia principal permanece acima de linhas
estruturais por padrão.

## Proteção e interseção

Cada texto importante gera uma zona a partir do `getBBox()` real do browser,
com padding de 24 px para headline, 20 px para número hero, 16 px para label
secundária e 10 px para micro-label. Ao encontrar uma zona protegida, a ordem
é `STOP_BEFORE`, `ROUTE_AROUND`, `MASK_BEHIND` e
`TRANSFORM_TO_UNDERLINE`. `PASS_THROUGH` só é permitido com
`overlap_intent=EXPLICIT` documentado.

## Setas, conectores e trilhos

`ARROW` exige shaft, arrowhead explícito, direção inequívoca e terminação limpa.
Linhas sem direção são `LINE`, `TRACK` ou `ACCENT_LINE`; não recebem
pseudo-arrowhead. Conectores declaram anchors, padding, routing e papel
semântico, e não terminam no meio de palavras ou objetos.

## Auditoria

A auditoria executa JavaScript no Edge headless, aguarda as fontes, carrega os
SVGs em tamanho real e mede texto com `element.getBBox()` e comprimento quando
necessário. Cada visual sub-beat é amostrado no início, em 50% e no fim, além
de entradas, transições e mudanças de baseline. O gate de produção exige zero
`ERROR`.

O contrato completo está em `config/visual_geometry_contract.json`.
