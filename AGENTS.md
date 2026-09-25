# AGENTS.md — Capital Oculto

## Identidade do projeto

Este diretório contém a operação editorial do canal **Capital Oculto**, um canal brasileiro de entretenimento educativo sobre psicologia do dinheiro, comportamento financeiro, trabalho, consumo e status.

## Ordem de leitura obrigatória

Antes de criar ou alterar qualquer episódio:

1. Leia `START_HERE.md`.
2. Leia `GUIA_DO_CANAL.md`.
3. Consulte o documento específico em `docs/`.
4. Use os prompts em `prompts/`.
5. Trabalhe dentro de uma pasta própria em `episodios/`.

## Fontes de verdade

- `GUIA_DO_CANAL.md`: estratégia editorial e decisões permanentes.
- `START_HERE.md`: estado atual e próxima ação.
- `banco_de_ideias/ideias.csv`: backlog priorizado.
- `analytics/dados/`: histórico numérico sem sobrescrita.
- Pasta do episódio: verdade operacional daquele vídeo.

Se houver conflito, a ordem acima prevalece. Regras globais de segurança continuam válidas.

## Regras invioláveis

- Não alterar nem apagar `ARQUIVOS MODELAR/` sem autorização explícita.
- Modelar mecanismos de sucesso; nunca copiar texto, personagem, composição ou roteiro de terceiros.
- Não publicar recomendação personalizada de investimento, promessa de retorno ou fórmula de enriquecimento.
- Não apresentar personagem gerado por IA como especialista humano real.
- Toda afirmação factual, estatística, histórica ou científica deve constar no ledger de fontes do episódio.
- Não inventar estudo, autor, dado, link, citação ou credencial.
- Distinguir correlação, hipótese, inferência e causalidade.
- Linguagem principal: português brasileiro natural.
- Duração editorial: 5 a 8 minutos; alvo padrão entre 7:00 e 8:00.
- Um vídeo responde uma macropergunta e explica no máximo três mecanismos centrais.
- Título e thumbnail são definidos antes do roteiro.
- Thumbnail e título devem prometer exatamente o que os primeiros 30 segundos entregam.
- CTA de inscrição só depois de um payoff; não pedir inscrição por pena.
- Não usar medo, vergonha ou urgência de forma enganosa.
- Não transformar um template em vídeos intercambiáveis.
- Imagens realistas de pessoas, lugares ou acontecimentos sintéticos devem receber o disclosure adequado no YouTube.
- Revisar manualmente narração, pronúncias, números, texto da thumbnail e legenda antes da publicação.

## Processo obrigatório de episódio

1. Selecionar pauta pelo score e pela hipótese de público.
2. Criar a pasta com `python scripts/novo_episodio.py`.
3. Preencher brief e pesquisa.
4. Criar três pacotes de título + thumbnail realmente diferentes.
5. Aprovar uma promessa principal e duas variantes para teste.
6. Escrever o roteiro de narração.
7. Executar revisão factual e de originalidade.
8. Criar roteiro visual e prompts em lote.
9. Gerar imagens e vídeos mantendo a bíblia visual.
10. Montar, legendar e revisar o vídeo completo.
11. Preparar descrição, fontes e disclosure.
12. Publicar e registrar snapshots de 24h, 72h, 7d e 28d.
13. Escrever post-mortem sem alterar retroativamente os dados brutos.

## Política de experimentos

- Testar uma variável estratégica principal por rodada.
- Preferir o teste nativo do YouTube para até três títulos/thumbnails quando disponível.
- Julgar embalagem por watch time gerado, não apenas por CTR.
- Não declarar vencedor sem volume mínimo útil ou resultado do teste nativo.
- Comparar vídeos com a mediana do próprio canal e com vídeos de idade e origem de tráfego semelhantes.
- Registrar mudança de título ou thumbnail em `analytics/dados/experimentos.csv`.

## Convenções

- IDs de vídeo: `CO-001`, `CO-002`, em sequência.
- Slugs: minúsculos, ASCII e hífens, por exemplo `por-que-ganhar-mais-nao-basta`.
- Datas: `AAAA-MM-DD`.
- Snapshots: uma nova linha por momento; nunca substituir medição anterior.
- Capturas recebidas: `AAAA-MM-DD_CO-001_24h_overview.png`, trocando `overview` por `reach`, `engagement`, `audience` ou `revenue`.

## Escrita e manutenção

- Preservar arquivos e mudanças do usuário.
- Usar `apply_patch` para edições manuais.
- Não instalar dependências sem necessidade e aprovação.
- Os scripts deste projeto devem funcionar apenas com a biblioteca padrão do Python.
- Não deixar arquivos vazios, marcadores de implementação futura ou conteúdo abreviado.
- Ao terminar uma etapa relevante, executar `python scripts/validar_projeto.py`.

