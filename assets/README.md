# Assets reutilizáveis

Esta pasta guarda somente recursos cuja origem e direito de uso sejam conhecidos.

## Organização ativa

- `identidade/`: logo, banner, paleta e tipografia aprovada.
- `characters/`: personagens vetoriais mestres.
- `expressions/`: rostos e emoções reutilizáveis.
- `poses/`: configurações de braços, pernas e corpo.
- `objects/`: celulares, calendários, contas e objetos financeiros.
- `backgrounds/`: fundos vetoriais aprovados.
- `scenes/`: composições 1920x1080 por episódio.
- `biblioteca/`: manifesto histórico e categorias auxiliares.
- `audio/`: efeitos e trilhas com licença comercial documentada.
- `thumbs/`: exports finais e arquivos editáveis de thumbnail.

## Regras

- Registrar a ferramenta ou origem de cada recurso.
- Não guardar cópia de thumbnail de concorrente como asset de produção.
- Não usar rosto, voz, marca ou personagem protegido sem autorização.
- Manter os arquivos de referência dos personagens em proporção e cores consistentes.
- Texto de thumbnail deve ser aplicado no editor, não incorporado pelo gerador.

O estilo central é `CO_SKETCH_V1`, definido em `config/vector_style.json`. Os SVGs são produzidos localmente por `scripts/gerar_cenas_svg.py`, sem modelo generativo e sem upscale.

`library_manifest.csv` registra a categoria e a primeira cena real de uso de cada componente. Um asset sem `first_used_scene` não deve entrar na biblioteca.
