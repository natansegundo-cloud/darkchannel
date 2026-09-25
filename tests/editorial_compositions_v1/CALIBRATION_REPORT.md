# Capital Oculto — Calibration Report

**STATUS: EXPERIMENTAL_TEST — APROVAÇÃO HUMANA PENDENTE**

Esta rodada calibra masters existentes. Não cria família, variante ou integração de produção.

## S001

- defect_type: `MASTER_DEFECT`
- family: `DATA_HERO`
- variant_before: `CO-COMP-01C v1`
- variant_after: `CO-COMP-01C v1.1`
- master_changed: `sim`
- generalized_rule: `hero_crop_intensity=MODERATE`; `delta_prominence=SECONDARY_STRONG`; `microcontext_dominance=SUBORDINATE`
- reason: o conceito já funcionava, mas o crop comprometia parte da leitura e o delta perdia importância a 25%. O master agora preserva escala oversized com leitura mais segura e delta mais presente.

## S002

- defect_type: `SELECTION_DEFECT`
- family: `MOVING_BASELINE`
- variant_before: `CO-COMP-04C v1`
- variant_after: `CO-COMP-04A v1.1`
- master_changed: `sim — CO-COMP-04A`
- generalized_rule: `old_state_visibility_ratio=0.42`; `baseline_emphasis=HIGH`; `current_state_dominance=PRIMARY_STRONG`
- reason: 04C dependia de dois números sobrepostos e permanecia próximo de DATA_HERO. A seleção 04A torna baseline antiga, baseline atual e deslocamento partes explícitas do mecanismo.

## S003

- defect_type: `MASTER_DEFECT`
- family: `SHRINKING_SPACE`
- variant_before: `CO-COMP-03A v1`
- variant_after: `CO-COMP-03A v1.1`
- focus_mode: `COMPRESSION_FIRST`
- master_changed: `sim`
- generalized_rule: `focus_mode=COMPRESSION_FIRST`; `gap_dominance=PRIMARY`; `result_dominance=SECONDARY`; `gap_ratio=0.208`
- reason: o objetivo narrativo é “a folga encolheu”. O gap comprimido agora é o elemento dominante; o valor final permanece como consequência legível, não como novo DATA_HERO.

## Efeito reutilizável

- DATA_HERO ganha controle semântico de crop e proeminência do delta.
- MOVING_BASELINE exige estado antigo perceptível, baseline estrutural e estado atual dominante.
- SHRINKING_SPACE passa a declarar `COMPRESSION_FIRST` ou `RESULT_FIRST` sem criar variantes adicionais.

Nenhuma composição foi marcada como `APPROVED`.
