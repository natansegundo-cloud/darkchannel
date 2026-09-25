# Visual Geometry Contract V1 — Geometry Audit Report

Gerado em: `2026-09-25T00:55:05-03:00`

A auditoria foi executada no Edge headless com SVGs em 1920×1080, fontes carregadas e `element.getBBox()` real. O áudio, o timing, a voz e o pacing não foram alterados.

## Resumo

- `total_samples`: 90
- `total_collisions_before`: 270
- `total_collisions_after`: 210
- `errors_before`: 60
- `errors_after`: 0
- `browser_geometry`: `True`
- `fonts_ready`: `True`

## Por cena

| Cena | Samples | Findings antes | Findings depois | Gate |
|---|---:|---:|---:|---|
| S001 | 22 | 0 | 0 | PASS |
| S002 | 22 | 0 | 0 | PASS |
| S003 | 28 | 168 | 168 | PASS |
| S004 | 28 | 42 | 42 | PASS |
| S005 | 40 | 20 | 0 | PASS |
| S006 | 40 | 40 | 0 | PASS |

## Colisões encontradas antes da correção

- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-0`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-1`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-2`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-3`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-4`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-5`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-6`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-11`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-7`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-8`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-9`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.scene` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-10`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-0`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-1`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-2`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-3`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-4`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-5`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-6`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-11`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-7`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-8`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-9`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- `S003` / `S003.A` / `13.6770s` — `LINE_TYPE_INTERSECTION` entre `STRUCTURAL_LINE` e `S003-text-10`; severity `INFO`; resolução `MASK_BEHIND_EXPLICIT_DATA_MASS`.
- … mais 246 finding(s) registrados no JSON bruto.

## Classificação e correções

- S005: `MASTER_DEFECT` no sistema de trilhos e na rota da `ACCENT_LINE`; a diagonal passou a terminar antes da protected zone de `QUANDO A RENDA SOBE`, e os trilhos passaram a ser `TRACK` com terminação limpa, sem pseudo-arrowhead.
- S006: `MASTER_DEFECT` na baseline de `CO-COMP-04D@1.1`; a rota passou a usar `STOP_BEFORE` da zona de `EXTRA` e `TRANSFORM_TO_UNDERLINE` no patamar de `NORMAL`.
- S001–S004: auditados nos mesmos samples; nenhuma correção estética oportunista foi aplicada.

## Artefatos

- Contrato: `config/visual_geometry_contract.json`.
- Documentação: `docs/VISUAL_GEOMETRY_CONTRACT_V1.md`.
- Resultado bruto browser: `tests/visual_geometry_v1/geometry_audit_results.json`.
- Debug sheet: `tests/visual_geometry_v1/debug_contact_sheet_s005_s006.png`.

Gate: `ERROR = 0` após a correção.
