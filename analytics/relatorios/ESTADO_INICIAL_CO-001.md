# Relatório de performance — Capital Oculto

Gerado em `2026-09-23T21:39:14-03:00`.

## Escopo

- Vídeos: `analytics\dados\videos.csv`
- Snapshots: `analytics\dados\snapshots.csv`
- Experimentos: `analytics\dados\experimentos.csv`
- Filtro de vídeo: `CO-001`
- Linhas EXEMPLO incluídas: `não`

## Baseline mediano do canal

A referência usa um snapshot por vídeo em cada janela. `N < 3` é marcado como amostra inicial.

| Janela | N | Confiança | Impressões | Views | CTR | Ret. 30s | Média assistida | Horas | Inscr. líquidos/mil |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 24H | 0 | inicial | — | — | — | — | — | — | — |
| 72H | 0 | inicial | — | — | — | — | — | — | — |
| 7D | 0 | inicial | — | — | — | — | — | — | — |
| 28D | 0 | inicial | — | — | — | — | — | — | — |

## Desempenho por vídeo

### CO-001 — Você ganha mais. Por que ainda parece insuficiente?

Status: `PRE_PRODUCAO` · Duração: `7:43` · Pilar: `Dinheiro cotidiano`

| Janela | Idade medida | Views | vs. mediana | CTR | vs. mediana | Ret. 30s | Média assistida | Horas | Inscr. líquidos |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 24H | — | — | — | — | — | — | — | — | — |
| 72H | — | — | — | — | — | — | — | — | — |
| 7D | — | — | — | — | — | — | — | — | — |
| 28D | — | — | — | — | — | — | — | — | — |

Ainda não há snapshot utilizável para este vídeo.

## Experimentos registrados

| ID | Vídeo | Tipo | Status | Controle | Teste | Métrica | Delta | Decisão | Aprendizado |
|---|---|---|---|---|---|---|---:|---|---|
| CO-001-EXP-001 | CO-001 | titulo_thumbnail | PLANEJADO | A | B\|C | watch_time_share | — | AGUARDAR | Resultado será registrado após amostra suficiente |

## Leitura responsável

- CTR alto com poucas impressões ainda pode refletir uma audiência pequena e muito alinhada.
- CTR baixo com distribuição crescente pode refletir expansão para públicos mais frios.
- Retenção inicial mede a entrega da promessa; duração média e percentual assistido mostram a sustentação.
- Uma mudança deve ser associada a um experimento antes de receber crédito pelo resultado.

## Alertas de qualidade dos dados

- Nenhum alerta detectado.
