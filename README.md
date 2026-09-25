# Capital Oculto

Sistema editorial e operacional para produzir vídeos de 5 a 8 minutos sobre psicologia do dinheiro, comportamento financeiro, trabalho, consumo e status.

O projeto foi desenhado para que o trabalho humano fique concentrado em decisões de qualidade: aprovar pauta, promessa, thumbnail, narração e montagem. Pesquisa, estruturação, prompts, organização e análise são assistidos pelo Codex.

## Princípio central

**A embalagem conquista o clique; o roteiro paga a promessa; os dados decidem o próximo experimento.**

Não existe tema ou fórmula que garanta monetização. Este sistema reduz risco por meio de consistência, originalidade, pesquisa verificável, produção sustentável e ciclos curtos de aprendizado.

## Início rápido

1. Leia `START_HERE.md` e `GUIA_DO_CANAL.md`.
2. Escolha uma pauta em `banco_de_ideias/ideias.csv`.
3. Crie um episódio:

```powershell
python scripts/novo_episodio.py --id CO-002 --titulo "Por que o desconto faz você gastar mais?" --slug por-que-o-desconto-faz-gastar-mais
```

4. Preencha os arquivos do episódio na ordem numérica.
5. Use os prompts correspondentes em `prompts/`.
6. Antes de produzir, aprove um pacote de título + thumbnail.
7. Antes de publicar, execute:

```powershell
python scripts/validar_projeto.py
```

8. Depois de inserir métricas nos CSVs, gere o relatório:

```powershell
python scripts/analisar_metricas.py
```

## Mapa do projeto

| Caminho | Função |
|---|---|
| `GUIA_DO_CANAL.md` | Bíblia editorial e visual |
| `docs/` | Estratégia, copy, retenção, produção, analytics e segurança |
| `docs/PIPELINE_AUDIOVISUAL.md` | Contrato entre beats, áudio cronometrado, anchors, cenas e assets |
| `prompts/` | Instruções reutilizáveis para cada etapa |
| `episodios/_MODELO/` | Pacote-base de um vídeo |
| `episodios/CO-001-*/` | Primeiro episódio completo |
| `banco_de_ideias/ideias.csv` | Backlog pontuado |
| `analytics/dados/` | Banco de métricas e experimentos |
| `analytics/inbox/` | Entrada organizada de screenshots |
| `analytics/relatorios/` | Diagnósticos produzidos pelo script |
| `scripts/` | Criação, análise e validação |
| `assets/` | Biblioteca vetorial, identidade, cenas e arquivos reutilizáveis |
| `ARQUIVOS MODELAR/` | Material original de referência; não editar |

## Dependências

- Python 3.10 ou superior.
- Nenhum pacote externo de Python.
- Um editor de vídeo/legendas, como Adobe Express.
- O pipeline visual principal usa SVG programático e não exige modelo de imagem.
- Geradores de imagem ou vídeo são opcionais e ficam reservados para exceções de alto impacto.

Pavo AI, DreamFace, Google Flow, Roboneo, Dola AI e Vibes.ai podem ser usados conforme custo e qualidade. A operação não depende de uma ferramenta específica: os prompts visuais são neutros e os resultados devem ser avaliados por consistência, legibilidade e velocidade.

Para gerar o protótipo vetorial do primeiro episódio:

```powershell
python scripts/gerar_cenas_svg.py CO-001
```

Consulte `docs/GERACAO_VISUAL_VETORIAL.md` antes de expandir o lote.

## Ritmo recomendado

- Criar um buffer de seis vídeos antes de depender de calendário rígido.
- Publicar dois vídeos longos por semana.
- Derivar de dois a três Shorts de cada vídeo, sem contar esse watch time como parte da meta de vídeos longos.
- Realizar uma revisão semanal curta e uma revisão profunda a cada quatro vídeos.

## Comandos

```powershell
python scripts/novo_episodio.py --help
python scripts/analisar_metricas.py --help
python scripts/validar_projeto.py --help
python scripts/gerar_cenas_svg.py --help
```

## Limites editoriais

O Capital Oculto é entretenimento educativo. Não oferece aconselhamento financeiro, tributário, jurídico ou de investimento. Os conteúdos devem ensinar mecanismos de comportamento e decisão sem prometer resultados individuais.
