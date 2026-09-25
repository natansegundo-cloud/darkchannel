# START HERE — Estado do Capital Oculto

## Situação atual

- Canal criado: **Capital Oculto**.
- Idioma principal aprovado: **português brasileiro**.
- Nicho aprovado: **psicologia do dinheiro e comportamento financeiro**, com trabalho, carreira, consumo e status como adjacências.
- Formato aprovado: vídeos narrados de **5 a 8 minutos** com ilustração vetorial 2D simples.
- Cadência-base: **dois vídeos longos por semana**.
- Voz oficial aprovada: **SANTA** (`pm_santa`), gerada localmente com Kokoro ONNX.
- Material de modelagem: analisado e preservado em `ARQUIVOS MODELAR/`.
- Operação: documentação, templates, banco de pautas, analytics e automação local instalados neste diretório.
- Pipeline visual principal: **SVG programático offline**, sem modelo de difusão; `CO_SKETCH_V1` foi preservado, `CO_VECTOR_V2` tornou-se histórico e `CO_VISUAL_V3` está em validação visual.
- Formato oficial do `CO-001`: **long-form horizontal 1920x1080**, com 48 cenas. A referência anterior a Shorts verticais e 44 cenas foi descartada como erro de especificação.
- Episódio `CO-001`: roteiro, fontes, plano legado de 48 cenas, 49 prompts e três embalagens auditados; as cenas V1 S001–S045 permanecem preservadas.
- Arquitetura audiovisual por beats validada tecnicamente no piloto: `B001–B006` geram `03A_AUDIO_TIMING.json` pelo `create_timed()` do Kokoro, anchors do 04 são resolvidos em `04A_SCENE_MANIFEST.json` e os assets vêm de `05_ASSET_MANIFEST.csv`.
- Novo teste sequencial S001–S006 exportado com 39,5 s de voz Santa. O Visual System V3 continua candidato até revisão humana; o restante do CO-001 não foi migrado.
- O teste confirmou a engenharia, mas a direção de arte foi rejeitada por aparência de apresentação. A camada candidata `CO_ART_DIRECTION_V4` refaz S001–S006 como motion graphics editorial: cinco classes visuais, zero ícones dominantes e personagem somente quando cumpre função.
- O sprint V4 está disponível apenas como frames estáticos e board a 25%. Áudio, animação, Azure e as demais 42 cenas permanecem suspensos até aprovação visual.

## Decisões que não devem ser reabertas sem dados

1. Não misturar uploads separados em português e inglês no mesmo feed inicial.
2. Validar a operação em PT-BR antes de expandir por dublagem/localização.
3. Não entrar em recomendações de ações, ETFs, apostas, crédito predatório ou promessas de enriquecimento.
4. Produzir entretenimento educativo sobre mecanismos psicológicos invisíveis.
5. Começar com títulos e thumbnails; roteiro vem depois.
6. Usar um personagem ilustrado como representação do espectador, nunca como falso especialista.
7. Avaliar resultados contra a mediana do próprio canal.

## Próxima ação

Revisar e aprovar ou pedir ajustes no board estático: `episodios/CO-001-por-que-ganhar-mais-nao-basta/testes/art_direction_v4_s001_s006/review_art_direction_v4_25.png`.

Somente depois da aprovação:

1. congelar a Art Direction V4 para o CO-001;
2. animar somente S001–S006 usando as transformações já declaradas;
3. manter a migração estrutural separada do casting Azure;
4. realizar o casting e trocar apenas o provider de narração;
5. regenerar 03A e 04A, validar novamente o piloto e só então migrar as demais cenas.

Depois:

1. Preservar `CO_SKETCH_V1` e `CO_VECTOR_V2` como históricos durante a validação formal do `CO_VISUAL_V3`.
2. Revisar ritmo, sincronização e continuidade do teste S001–S006 resolvido por anchors.
3. Após aprovação explícita, fazer o casting Azure como etapa independente, sem alterar 03, 04, 05 ou o resolvedor.
4. Validar o mesmo piloto com o novo provider antes de travar o V3.
5. Migrar em blocos curtos usando o rig oficial apenas quando o personagem agregar significado e ícones locais versionados.
6. Finalizar o `CO-001`, preparar `CO-002` e `CO-003` e montar o buffer.

## Ao retomar o projeto em outra sessão

Diga: **“retomar Capital Oculto”**.

O Codex deve ler este arquivo, `GUIA_DO_CANAL.md`, o conteúdo da pasta do episódio em andamento e o relatório mais recente em `analytics/relatorios/` antes de agir.

## Como entregar screenshots para análise

Coloque as capturas em uma subpasta de `analytics/inbox/` usando a data da coleta. Exemplo:

```text
analytics/inbox/2026-10-15/2026-10-15_CO-001_72h_overview.png
analytics/inbox/2026-10-15/2026-10-15_CO-001_72h_reach.png
analytics/inbox/2026-10-15/2026-10-15_CO-001_72h_engagement.png
```

Não recorte escalas, datas ou comparativos do gráfico de retenção. O contexto da captura é necessário para interpretar corretamente os números.

## Definição de sucesso da fase inicial

O objetivo dos primeiros 12 vídeos não é provar que toda pauta funciona. É descobrir uma combinação repetível de:

- assunto que recebe impressões;
- promessa que conquista clique qualificado;
- abertura que retém;
- mecanismo que gera satisfação;
- sistema visual que pode ser mantido por meses.

Um único viral não valida a operação. Um padrão repetido em pelo menos três vídeos adjacentes começa a validá-la.
