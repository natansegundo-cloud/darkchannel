# Style guide visual V2 — Capital Oculto

> Status: histórico e substituído por `docs/VISUAL_SYSTEM_V3.md`. Não usar para novas cenas.

## Formato oficial

- Conteúdo principal: long-form horizontal.
- Canvas: `1920x1080`, proporção 16:9.
- Total do `CO-001`: 48 cenas.
- Margem de segurança: 64 px em todos os lados.
- O formato `1080x1920`, a classificação como Shorts e a contagem de 44 cenas pertenciam a uma especificação equivocada e não se aplicam ao episódio.

## Paleta

| Uso | Cor | Hex |
|---|---|---|
| Traço, personagem e texto | Preto | `#111111` |
| Dinheiro, base e resultado positivo | Verde-lima | `#C4E538` |
| Ação, alerta e aumento | Âmbar | `#E8A33D` |
| Fundo | Off-white | `#F4F3EF` |
| Neutro secundário | Cinza claro | `#D9D9D4` |

Cada cena usa o fundo, o preto e no máximo um destaque. Lima e âmbar não disputam protagonismo na mesma composição.

## Personagem oficial

- Fonte única: `assets/characters/capital_oculto_character_rig_v4.svg`.
- Cena estática: `<use href="#char-base">`.
- Cena articulada: instanciar somente os grupos de partes fornecidos pelo rig.
- Somente `char-base` pode ser `<symbol>`. `char-head`, `char-neck`, `char-torso`, `char-tie`, `char-arm-left`, `char-arm-right`, `char-leg-left` e `char-leg-right` devem permanecer `<g>` no mesmo sistema de coordenadas.
- É proibido converter novamente qualquer parte do corpo para `<symbol>`.
- É proibido redesenhar proporções, rosto, gravata, silhueta, paleta ou espessuras.
- Movimentos de idle usam amplitudes pequenas e os pivôs documentados no arquivo de instruções do rig.

## Traço, forma e tipo

- Contorno principal: 6 px; detalhe interno: 3 px.
- `stroke-linecap="round"` e `stroke-linejoin="round"`.
- Cartões e retângulos: `rx="12"`.
- Títulos: caixa alta, peso 800, entre 72 e 96 px.
- Apoio: 36 a 48 px.
- Texto sempre preto no fundo claro ou off-white em área preta.
- Não usar filtro de roughness. Sombra, quando necessária, aparece apenas no elemento principal.

## Ícones

- Biblioteca principal: Phosphor Icons, incorporada localmente e versionada.
- Lucide só pode preencher lacunas reais; não misturar famílias na mesma cena.
- Os ícones entram como symbols e são reutilizados por `<use>`.
- Licenças e origem precisam acompanhar os assets em `assets/icons/`.

## Composição

- No máximo dois blocos de informação: personagem + uma metáfora ou gráfico.
- Evitar centralização morta; trabalhar com terços e assimetria controlada.
- Nenhum elemento essencial invade a margem de segurança.
- A ideia precisa ser entendida em até dois segundos, inclusive em miniatura.

## Checklist

- [ ] Canvas horizontal `1920x1080` e 64 px de margem.
- [ ] Somente preto, fundo e um destaque.
- [ ] Personagem vindo do rig oficial por `<use>`.
- [ ] Ícones vindos da biblioteca local por `<use>`.
- [ ] No máximo dois blocos de informação.
- [ ] Título legível e sem colisões.
- [ ] Retângulos com cantos arredondados.
- [ ] Metáfora compreensível sem depender da narração.
