# Arquivo morto — narração pré-consolidação

Estes arquivos foram movidos em 2026-09-25 durante a Fase 1 de consolidação da narração. Nenhum conteúdo foi deletado; o diretório preserva os pontos de reversão e o histórico Git.

## Destino da lógica

- `gerar_narracao_ORIGINAL.py.bak`: antigo dispatcher REST/Kokoro; a entrada fina agora está em `scripts/gerar_narracao.py` e delega para `src/narration/engine.py`.
- `gerar_narracao_v2.py`: implementação aprovada do Voice Pacing V2; sua lógica compartilhada foi consolidada em `src/narration/providers/voice_pacing_v2.py` e a orquestração foi para `src/narration/engine.py`.
- `gerar_narracao_local.py`: implementação Kokoro anterior; o provider isolado agora está em `src/narration/providers/local_kokoro.py`.
- `gerar_narracao_v3_sdk_experimental.py`: experimento Azure SDK/WordBoundary; o provider agora está em `src/narration/providers/azure_sdk.py`.
- `gerar_narracao_sdk_ORIGINAL.py.bak`: adapter SDK criado durante a etapa anterior; o caminho compatível agora delega diretamente para `src/narration/engine.py`.

`src/narration/providers/azure_rest.py` concentra a síntese REST. `src/narration/config.py` concentra a leitura de narradores, voz local e variáveis Azure.

## Reversão

A tag de segurança criada antes da reorganização foi executada com:

```text
git tag estado-funcional-pre-refatoracao-narracao
```

Ela aponta para o commit `72a38a7c1226b254fe0b5451066650f4096ac6e6`.
