# Benchmark encerrado: difusão local

Data do teste: 2026-09-24.

## Hardware

- Samsung Galaxy Book2 / 550XED.
- Intel Core i5-1235U, 10 núcleos e 12 threads.
- 8 GB de RAM compartilhada.
- Intel Iris Xe, sem GPU NVIDIA e sem CUDA.
- Execução do ComfyUI em CPU.

## Resultados

1. Segmind Tiny-SD, cerca de 1 GB: o ComfyUI 0.37.0 não reconheceu a arquitetura reduzida do UNet pelo `DiffusersLoader`.
2. Stable Diffusion 1.5 FP16, A00 em 512x288 e 12 passos: 385,55 segundos. O resultado foi abstrato e inutilizável como folha de personagem.
3. Stable Diffusion 1.5 FP16, prompt reduzido e A00 em 384x384: 848,23 segundos. O resultado continuou inutilizável e incluiu texto corrompido.
4. O modo `cache-none` também provocou uma segunda carga do checkpoint e falta de memória. `cache-lru 1` evitou a recarga duplicada, mas não resolveu velocidade nem qualidade.

Uma extrapolação simples para 44 imagens daria aproximadamente 4h43 no melhor teste e 10h22 no segundo, antes de qualquer nova tentativa. Como os dois resultados precisariam ser refeitos, esse caminho foi reprovado como pipeline principal.

## O que foi preservado

- `scripts/gerar_imagens_lote.py`.
- `scripts/iniciar_comfyui.ps1`.
- `workflows/comfyui/txt2img_api.json`.
- `config/visual_style.json` e `config/modelos_visuais.json`.
- Os dois PNGs A00 em `episodios/CO-001-por-que-ganhar-mais-nao-basta/assets/gerados/`.
- Logs e manifesto em `episodios/CO-001-por-que-ganhar-mais-nao-basta/assets/logs/` e `manifesto_geracao.jsonl`.

## O que foi removido

O runtime `.comfyui`, os modelos, o ambiente virtual e seus caches, totalizando aproximadamente 4,696 GB. A narração local em `.tts` foi preservada.

## Decisão

O pipeline principal passa a ser SVG programático offline. Difusão local fica apenas como benchmark histórico e não deve ser reinstalada sem mudança relevante de hardware ou uma necessidade visual excepcional.
