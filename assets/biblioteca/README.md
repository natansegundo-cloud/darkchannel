# Biblioteca visual permanente

Esta biblioteca guarda apenas assets aprovados para reutilizacao. Geracoes brutas pertencem ao episodio; um arquivo so entra aqui depois de revisao humana.

## Pastas

- `personagens/`: folhas mestras de A00, Ana e futuros personagens.
- `expressoes/`: recortes aprovados de expressoes.
- `poses/`: poses corporais reutilizaveis.
- `objetos/`: celular, carteira, contas, calendarios e simbolos proprios.
- `cenarios/`: fundos simples e modulares.
- `efeitos/`: fios, brilhos, setas e elementos de transicao.

## Regra de composicao

`personagem + expressao + pose + objeto + cenario = cena`

Essa montagem e a rota mais previsivel para consistencia. O gerador cria materia-prima; a biblioteca aprovada e o editor preservam identidade entre videos.

## Promocao de um asset

1. Selecione o arquivo em `episodios/<episodio>/assets/selecionados/`.
2. Copie para a categoria correta com nome estavel, sem apagar versoes anteriores.
3. Registre uma linha em `manifest.csv`, incluindo origem, licenca, `STYLE_ID` e data.
4. Nunca substitua silenciosamente um asset aprovado. Crie `v002`, `v003` e assim por diante.

O estilo vigente e `CO_EDITORIAL_V1`, definido em `config/visual_style.json`.
