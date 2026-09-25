# Teste sequencial V3 — S001 a S006

Status: nova arquitetura audiovisual validada tecnicamente; pronto para revisão humana. Este teste não congela o sistema automaticamente.

## Objetivo

Provar o Visual System V3 em seis cenas reais consecutivas, sincronizadas à voz oficial, antes da migração das 48 cenas.

## Arco visual

| Cena | Função | Layout | Ideia dominante | Continuidade |
|---|---|---|---|---|
| S001 | personagem + gatilho | A | notificação de aumento | celular segue para S002 |
| S002 | transformação temporal | F | semanas viram três meses | celular permanece; calendário cresce ao redor |
| S003 | personagem / reação | A | saldo volta a apertar | mesmo celular e enquadramento invertido |
| S004 | contexto sem culpa | D | gastos cotidianos, nenhum absurdo | saldo vira régua de escolhas |
| S005 | mapa / dado | C | três forças movem juntas | três escolhas condensam em três mecanismos |
| S006 | metáfora / conclusão | B | mecanismo mental de adaptação | o círculo “normal” entra no cérebro |

## Regras do teste

- Duração-alvo: 20–40 segundos; tolerância máxima de dois segundos somente se a locução oficial exigir.
- O áudio define todos os cortes e cues por `create_timed()`, beats e anchors narrativos.
- Cada transição preserva ao menos um objeto, posição, número, direção ou enquadramento.
- Um único movimento dominante por vez.
- Assets vêm exclusivamente das fontes oficiais em `assets/`.
- Aprovar em movimento antes de alterar o status do V3 para `LOCKED FOR CO-001`.

## Artefatos

- Narração da prova estrutural: `narracao_pipeline.wav` — 39,5 s, voz Santa via Kokoro ONNX.
- Timing de palavras e beats: `../../03A_AUDIO_TIMING.json`.
- Direção visual por anchors: `04_ROTEIRO_VISUAL.csv`.
- Manifesto resolvido: `../../04A_SCENE_MANIFEST.json`.
- Timeline de reprodução derivada do 04A: `timeline.json`.
- Cenas vetoriais: `scenes/s001.svg` a `scenes/s006.svg`.
- Vídeo para aprovação: `teste_sequencial_v3_s001_s006_pipeline.webm`.
