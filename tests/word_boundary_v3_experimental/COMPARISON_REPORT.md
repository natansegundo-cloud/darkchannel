# Comparação — Word Boundary V3 experimental

Status: **EXPERIMENTAL_COMPLETE**

Gerado em: `2026-09-24T23:49:52-03:00`

Este relatório compara o timing heurístico V2 com timestamps reais emitidos pelo evento `WordBoundary` do Azure Speech SDK.
O `motion_spec.json`, os timings oficiais e o pipeline de render não foram alterados.

## Métricas resumidas

- `mean_absolute_error_ms`: 742.967
- `median_absolute_error_ms`: 695.458
- `max_absolute_error_ms`: 1948.417
- `anchors_over_100ms`: 27
- `anchors_over_200ms`: 24
- `anchors_over_300ms`: 21

Maior erro: `B006` / `cérebro` — heurístico 46964.500 ms, real 45016.083 ms, delta -1948.417 ms.

## Resumo por beat

| Beat | Duração heurística (ms) | Duração real (ms) | Boundaries | Âncoras |
|---|---:|---:|---:|---:|
| B001 | 4251.900 | 4120.083 | 7 | 3 |
| B002 | 10845.500 | 10538.917 | 20 | 6 |
| B003 | 5332.200 | 5129.625 | 10 | 3 |
| B004 | 3911.300 | 3738.167 | 8 | 4 |
| B005 | 17693.900 | 17188.750 | 43 | 8 |
| B006 | 8358.400 | 8135.667 | 17 | 4 |

## Âncoras de motion

| Beat | Âncora | Heurístico (ms) | WordBoundary real (ms) | Delta absoluto (ms) | Delta assinado (ms) |
|---|---|---:|---:|---:|---:|
| B001 | Você recebe a mensagem | 49.800 | 52.083 | 2.283 | +2.283 |
| B001 | seu salário | 1716.600 | 1917.833 | 201.233 | +201.233 |
| B001 | aumentou | 2495.400 | 2699.083 | 203.683 | +203.683 |
| B002 | Por algumas semanas | 4725.400 | 4572.166 | 153.234 | -153.234 |
| B002 | finalmente sobra | 6351.000 | 6007.291 | 343.709 | -343.709 |
| B002 | Três meses depois | 7941.300 | 8391.541 | 450.241 | +450.241 |
| B002 | você está outra vez | 9390.100 | 10269.874 | 879.774 | +879.774 |
| B002 | conferindo o saldo | 10803.700 | 11376.666 | 572.966 | +572.966 |
| B002 | vinte reais | 13454.100 | 13290.708 | 163.392 | -163.392 |
| B003 | O aumento era real | 16019.200 | 15511.083 | 508.117 | -508.117 |
| B003 | Então por que | 17836.900 | 18061.416 | 224.516 | +224.516 |
| B003 | folga sumiu | 19080.600 | 18972.875 | 107.725 | -107.725 |
| B004 | Você | 21778.600 | 21090.708 | 687.892 | -687.892 |
| B004 | não precisa | 22040.700 | 21416.250 | 624.450 | -624.450 |
| B004 | compra | 23679.200 | 23017.791 | 661.409 | -661.409 |
| B004 | absurda | 24072.400 | 23369.375 | 703.025 | -703.025 |
| B005 | Mesmo assim | 26048.200 | 25228.875 | 819.325 | -819.325 |
| B005 | renda | 29367.900 | 28239.500 | 1128.400 | -1128.400 |
| B005 | normal | 30763.200 | 29709.500 | 1053.700 | -1053.700 |
| B005 | compara | 32399.000 | 31425.042 | 973.958 | -973.958 |
| B005 | despesas | 33682.000 | 32612.750 | 1069.250 | -1069.250 |
| B005 | movem | 38172.500 | 37217.542 | 954.958 | -954.958 |
| B005 | tempo | 39134.700 | 38181.083 | 953.617 | -953.617 |
| B005 | invisível | 41813.000 | 40848.042 | 964.958 | -964.958 |
| B006 | A primeira peça | 44183.000 | 42867.625 | 1315.375 | -1315.375 |
| B006 | cérebro | 46964.500 | 45016.083 | 1948.417 | -1948.417 |
| B006 | traição | 49968.700 | 48205.750 | 1762.950 | -1762.950 |
| B006 | adaptação | 50636.200 | 49265.667 | 1370.533 | -1370.533 |

## Referências e limitações

- Timing heurístico: `tests/audiovisual_pilot_s001_s006/timing/03A_AUDIO_TIMING_v2.json` (schema `2.0`).
- Âncoras: extraídas dos `motion_spec.json` existentes, sem modificá-los.
- `audio_offset_ms` e `duration_ms` de palavras são conversões diretas das unidades de 100 ns fornecidas pelo SDK; campos ausentes permanecem `null`.
- A adoção do SDK como caminho oficial depende de decisão humana posterior.
