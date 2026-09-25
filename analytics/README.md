# Analytics do Capital Oculto

Este diretório transforma cada publicação em aprendizado acumulado. A unidade de análise é o vídeo; cada leitura do YouTube Studio vira um snapshot cumulativo e cada troca deliberada de embalagem vira um experimento.

## Estrutura

- `dados/videos.csv`: cadastro único de vídeos publicados ou agendados.
- `dados/snapshots.csv`: métricas cumulativas coletadas em momentos definidos.
- `dados/experimentos.csv`: testes de título, thumbnail, abertura ou distribuição.
- `inbox/`: capturas brutas do YouTube Studio enviadas para leitura.
- `relatorios/`: relatórios Markdown gerados por `scripts/analisar_metricas.py`.

As linhas cujo identificador começa por `EXEMPLO` existem apenas para documentar o formato. Elas são ignoradas pelos scripts por padrão e podem ser removidas quando o primeiro vídeo real for cadastrado.

## Rotina de coleta

Para cada vídeo, registre snapshots próximos destas idades:

| Janela | Idade-alvo | Tolerância usada pelo relatório | Decisão principal |
|---|---:|---:|---|
| `24H` | 24 horas | ±6 horas | Força inicial da embalagem e da abertura |
| `72H` | 72 horas | ±12 horas | Sustentação da distribuição |
| `7D` | 168 horas | ±24 horas | Comparação entre pautas e fontes de tráfego |
| `28D` | 672 horas | ±72 horas | Resultado consolidado e aprendizado evergreen |

O valor de `janela_padrao` prevalece quando estiver preenchido corretamente. Caso esteja vazio, o analisador usa `idade_horas`; se essa coluna também estiver vazia, calcula a idade pela diferença entre `data_coleta_hora` e `data_publicacao_hora`.

1. Cadastre o vídeo em `videos.csv` antes da publicação.
2. Salve as capturas necessárias em `inbox/` seguindo a convenção descrita no README daquela pasta.
3. Transcreva os números visíveis para uma nova linha de `snapshots.csv`.
4. Deixe em branco qualquer métrica que não apareça na tela; zero significa zero medido.
5. Execute o relatório e registre a decisão editorial no pós-mortem do episódio.

## Regras de preenchimento

- Arquivos usam UTF-8 e separador vírgula.
- Datas e horas usam ISO 8601 com fuso, por exemplo `2026-09-23T18:00:00-03:00`.
- Percentuais são números sem o símbolo `%`, por exemplo `6.8`.
- Valores decimais usam ponto, inclusive moeda.
- Snapshots são cumulativos desde a publicação, não apenas o incremento da janela.
- `video_id`, `snapshot_id`, `experimento_id` e `slug` não podem se repetir.
- Não altere números anteriores para melhorar o histórico. Se houver erro de digitação, corrija a linha e explique em `observacoes`.
- Não misture métricas de Shorts com as dos vídeos longos na mesma comparação editorial.

## O que o relatório calcula

Para cada janela disponível, o script escolhe no máximo um snapshot por vídeo e apresenta:

- impressões, visualizações, CTR, retenção aos 30 segundos, percentual médio assistido, horas de exibição e inscritos ganhos;
- inscritos líquidos por mil visualizações;
- mediana do canal em cada métrica e janela;
- diferença percentual do vídeo em relação à mediana, quando a mediana permite a divisão;
- histórico e resultado informado dos experimentos.

A mediana reduz a influência de um único vídeo fora da curva. Com menos de três vídeos reais na janela, o relatório marca a referência como amostra inicial. A comparação é diagnóstico, não garantia: CTR deve ser lida junto com impressões e fonte de tráfego; retenção deve ser lida junto com duração e promessa da embalagem.

## Comandos

Na raiz do projeto:

```powershell
python scripts/analisar_metricas.py
python scripts/analisar_metricas.py --video-id CO-V001
python scripts/analisar_metricas.py --saida analytics/relatorios/revisao-semanal.md
python scripts/validar_projeto.py
```

Use `python scripts/analisar_metricas.py --help` para ver filtros e caminhos alternativos. O relatório nunca altera os CSVs de origem.
