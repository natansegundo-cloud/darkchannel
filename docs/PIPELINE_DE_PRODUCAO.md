# Pipeline de produção — Capital Oculto

## 1. Objetivo

Este pipeline permite produzir dois vídeos longos por semana com qualidade controlada, baixo atrito e histórico completo de decisões. Ele foi desenhado para uma operação em que o Codex organiza e gera os pacotes, enquanto o operador revisa, copia os prompts para ferramentas externas, escolhe resultados e publica.

O fluxo é independente de fornecedor. Pavo AI, DreamFace, Google Flow, Roboneo, Dola AI, Vibes.ai e ferramentas equivalentes podem ser usadas conforme qualidade, custo e disponibilidade. Nenhuma delas é obrigatória para todas as etapas.

## 2. Princípios operacionais

1. **Embalagem antes de produção cara:** título e thumbnail precisam funcionar antes de gerar dezenas de cenas.
2. **Uma fonte de verdade por episódio:** decisões, versões e ativos ficam no diretório do episódio.
3. **Aprovação por portões:** a etapa seguinte só começa quando a anterior cumpre critérios objetivos.
4. **Lotes pequenos e verificáveis:** gerar primeiro amostras de estilo; escalar apenas depois da aprovação.
5. **Ferramentas substituíveis:** prompts descrevem intenção e não dependem de um único aplicativo.
6. **Automação com revisão:** nenhum texto, dado, imagem com texto ou alegação factual é publicado sem conferência.
7. **Dificuldade controlada:** usar movimento e edição sobre imagens-base antes de transformar cada cena em vídeo gerado.
8. **Registro de aprendizado:** toda publicação termina em análise, não apenas em upload.

## 3. Papéis

### Codex — orquestração editorial

- manter guias, modelos e banco de ideias;
- pontuar pautas;
- preparar pesquisa com fontes;
- gerar opções de títulos e conceitos de thumbnail;
- escrever e revisar roteiro de narração;
- decompor roteiro visual;
- produzir prompts em lote;
- verificar consistência entre os documentos;
- preparar descrição, capítulos e checklist;
- organizar a análise das métricas e dos prints enviados.

### Operador — direção e aprovação

- aprovar pauta e promessa;
- validar tom, fatos sensíveis e decisões criativas;
- copiar prompts para os geradores;
- escolher e baixar os melhores ativos;
- montar ou supervisionar edição;
- conferir voz, legenda, música e direitos;
- publicar no YouTube;
- fornecer snapshots e prints de analytics;
- aprovar mudanças de título ou thumbnail.

### Ferramentas de geração

- produzir imagens, clipes, variações e voz conforme prompts aprovados;
- não decidir tese, fonte, promessa ou política editorial;
- não substituir revisão humana de texto dentro de imagem;
- não determinar sozinhas o uso comercial permitido de seus resultados.

## 4. Estrutura recomendada por episódio

Cada episódio deve manter estes artefatos, mesmo que o formato físico seja adaptado pelo modelo do projeto:

```text
episodios/AAAA-MM-DD-slug-do-video/
├── 00_briefing.md
├── 01_pesquisa.md
├── 02_embalagem.md
├── 03_roteiro_narracao.md
├── 04_roteiro_visual.md
├── 05_prompts_imagens.md
├── 06_prompts_thumbnail.md
├── 07_publicacao.md
├── 08_qa.md
├── 09_pos_mortem.md
└── assets/
    ├── referencias/
    ├── gerados/
    ├── selecionados/
    ├── audio/
    ├── legendas/
    ├── thumbnails/
    └── exportacoes/
```

Arquivos brutos, selecionados e finais não devem ser misturados. Isso evita editar o ativo errado e facilita refazer uma etapa.

## 5. Estados do episódio

Um episódio percorre uma sequência única:

`IDEIA → PESQUISA → EMBALAGEM → ROTEIRO → PLANO VISUAL → GERAÇÃO → EDIÇÃO → QA → AGENDADO → PUBLICADO → ANALISADO`

Registrar o estado no briefing. Não usar “quase pronto”; indicar o portão pendente.

## 6. Etapa 0 — entrada e triagem

### Entradas

- ideia do banco;
- tendência observada;
- comentário de espectador;
- aprendizado de vídeo anterior;
- variação adjacente de assunto comprovado.

### Ações

1. escrever a tese em uma frase;
2. identificar pilar, formato e público específico;
3. pontuar os sete critérios editoriais;
4. classificar dificuldade e risco;
5. formular uma hipótese de aprendizado.

### Saída

`00_briefing.md` com decisão “seguir”, “reformular” ou “arquivar”.

### Portão 0

- pontuação editorial suficiente;
- integridade e sustentação com nota mínima 3;
- escopo adequado a 5–8 minutos;
- diferença clara em relação aos vídeos recentes.

## 7. Etapa 1 — pesquisa

### Ações

1. decompor a tese em afirmações verificáveis;
2. localizar fontes primárias ou institucionais;
3. registrar URL, título, autor ou instituição e data de acesso;
4. anotar exatamente o que cada fonte sustenta;
5. registrar limites, exceções e controvérsias;
6. selecionar exemplos e analogias;
7. remover afirmações que não possam ser defendidas.

### Saída

`01_pesquisa.md` com dossiê factual, notas de uso e fonte de cada dado.

### Portão 1

- toda estatística possui fonte rastreável;
- estudos não foram apresentados de forma mais forte do que permitem;
- a tese sobrevive à principal objeção;
- não há acusação sobre pessoa ou empresa sem base sólida;
- o vídeo pode ser escrito sem aconselhamento financeiro individual.

## 8. Etapa 2 — embalagem

### Ações

1. gerar no mínimo 10 rotas de título, distribuídas entre famílias diferentes;
2. rejeitar títulos que exigem vídeo diferente;
3. criar no mínimo 5 conceitos de thumbnail;
4. compor 3 pares título + thumbnail;
5. testar leitura em tamanho pequeno;
6. escolher uma versão principal e duas reservas;
7. escrever a promessa exata que o roteiro deve cumprir.

### Saída

`02_embalagem.md` com:

- título principal;
- títulos alternativos;
- thumbnail principal;
- thumbnails alternativas;
- emoção e mecanismo;
- justificativa do par;
- promessa de conteúdo;
- riscos de interpretação.

### Portão 2

- título compreensível sem contexto;
- thumbnail comunica uma ideia;
- título e thumbnail se complementam;
- o par desperta curiosidade sem alegação falsa;
- a tese comporta a promessa;
- existe uma alternativa suficientemente distinta para teste.

## 9. Etapa 3 — roteiro de narração

### Ordem de escrita

1. gancho;
2. virada final;
3. mapa de blocos;
4. recompensas de cada bloco;
5. corpo do roteiro;
6. transições;
7. callback;
8. CTA;
9. revisão de fatos e oralidade.

### Saída

`03_roteiro_narracao.md` contendo:

- versão numerada;
- duração estimada;
- texto integral de locução;
- marcações de pausa e ênfase quando essenciais;
- notas de pronúncia;
- referências associadas aos trechos factuais;
- mapa de pequenas recompensas.

### Teste de voz

Ler ou sintetizar uma versão de teste e medir duração real. Ajustar pelo áudio, não apenas pela contagem de palavras.

### Portão 3

- duração entre 5 e 8 minutos;
- promessa confirmada nos primeiros 15 segundos;
- valor inicial entregue até 30 segundos;
- uma tese principal;
- recompensa a cada bloco de 20–40 segundos, em média;
- conclusão fecha as perguntas relevantes;
- CTA aparece depois da entrega;
- roteiro soa falado, não como artigo.

## 10. Etapa 4 — roteiro visual

Dividir a narração em unidades visuais. Uma unidade pode usar a mesma cena-base com enquadramentos diferentes, desde que exista mudança perceptível.

### Campos por cena

- código da cena;
- intervalo aproximado;
- trecho da narração;
- função narrativa;
- descrição visual;
- personagem e expressão;
- cenário e objetos;
- composição e movimento;
- texto na tela;
- origem do ativo;
- prioridade: essencial, apoio ou opcional;
- continuidade necessária;
- observações de segurança ou direitos.

### Meta de complexidade

Ponto de partida para 5–8 minutos:

- 24–36 cenas-base;
- 50–80 eventos visuais após edição;
- 3–6 clipes gerados de maior impacto;
- restante apoiado em imagens com movimento, gráficos simples, tipografia e montagem.

Esses números são metas internas e podem variar com o estilo do episódio.

### Portão 4

- toda fala abstrata possui apoio visual compreensível;
- cenas essenciais estão identificadas;
- continuidade de personagem foi planejada;
- não existe dependência de texto gerado dentro da imagem;
- a carga cabe na semana de produção.

## 11. Etapa 5 — prompts de imagens em lote

### Estratégia de lote

Agrupar por consistência, não pela ordem do vídeo:

1. ficha do personagem;
2. expressões e poses;
3. cenário principal;
4. objetos recorrentes;
5. cenas narrativas;
6. metáforas visuais;
7. clipes prioritários;
8. thumbnail em fluxo separado.

### Bloco fixo do prompt

Todo prompt de um episódio deve herdar:

- estilo visual do canal;
- aparência fixa do personagem;
- paleta;
- proporção de tela;
- iluminação;
- nível de detalhe;
- restrições de texto, marcas e anatomia;
- lista de elementos que não devem aparecer.

### Bloco variável

- ação;
- expressão;
- objeto;
- cenário;
- enquadramento;
- direção de olhar;
- área negativa para texto ou movimento;
- posição na narrativa.

### Fluxo econômico

1. gerar duas cenas de teste;
2. aprovar consistência;
3. gerar lote de poses e cenários;
4. corrigir o bloco fixo uma vez;
5. gerar cenas essenciais;
6. selecionar antes de gerar opcionais;
7. documentar seed, referência ou configuração quando a ferramenta permitir.

Não continuar gerando variações apenas por perfeccionismo. A imagem precisa cumprir sua função na tela e no tempo em que será vista.

## 12. Etapa 6 — voz e áudio

### Voz

- manter a mesma identidade vocal entre episódios;
- evitar interpretação excessivamente publicitária;
- revisar pronúncia de nomes, siglas e valores;
- usar pausas para hierarquia, não após toda frase;
- conferir licença comercial do fornecedor;
- não imitar voz de pessoa real sem autorização.

### Música e efeitos

- usar somente ativos licenciados para o canal;
- registrar origem e licença;
- manter a narração inteligível;
- usar mudança musical para marcar virada, não para fabricar emoção sem conteúdo;
- evitar efeitos que pareçam alertas enganosos ou sons de aplicativo sem função.

### Portão 6

- áudio sem cortes, clipping ou palavras incorretas;
- volume de voz consistente;
- música não compete com fala;
- direitos documentados;
- duração ainda está entre 5 e 8 minutos.

## 13. Etapa 7 — edição e legendas

### Primeira montagem

Montar primeiro a narração e os pontos de virada. Depois encaixar visuais. Não usar a ordem dos ativos gerados para determinar o ritmo da história.

### Revisão de ritmo

- cortar pausas involuntárias;
- preservar pausas de significado;
- retirar repetições verbais;
- variar escala ou composição nos momentos de recompensa;
- conferir se imagem explica ou acrescenta, em vez de apenas repetir;
- manter textos de tela curtos e legíveis.

### Legendas

Adobe Express ou ferramenta equivalente pode gerar a base automática. A versão publicada precisa de revisão humana para:

- ortografia;
- nomes próprios;
- números e moedas;
- sincronização;
- divisão de linhas;
- pontuação;
- termos técnicos;
- ausência de palavras ofensivas criadas por erro de reconhecimento.

### Portão 7

- nenhuma tela preta ou ativo ausente;
- nenhuma marca d'água não autorizada;
- visuais não contradizem a narração;
- legendas correspondem ao áudio;
- texto cabe em celular;
- encerramento não se prolonga após a conclusão.

## 14. Etapa 8 — thumbnail final

Gerar a arte separadamente do vídeo. Inserir texto em ferramenta de edição quando o gerador não garantir ortografia.

Exportar:

- versão principal;
- alternativa A;
- alternativa B;
- arquivo editável quando existir;
- miniaturas de teste em tamanho reduzido.

### Portão 8

- foco compreendido em um segundo;
- contraste funciona em tela pequena;
- não há detalhe falso ou impossível que altere a promessa;
- texto correto;
- título e imagem somam informações;
- identidade é própria.

## 15. Etapa 9 — QA editorial e técnico

Executar a revisão completa sem depender da memória de quem editou.

### Editorial

- [ ] título, thumbnail, gancho e conclusão cumprem o mesmo contrato;
- [ ] não há trecho copiado de referência;
- [ ] todas as afirmações importantes continuam corretas após os cortes;
- [ ] fato, inferência e dramatização estão distinguíveis;
- [ ] o vídeo não dá aconselhamento financeiro individual;
- [ ] o CTA não interrompe a entrega.

### Visual

- [ ] personagem consistente;
- [ ] mãos, rostos, números e objetos essenciais sem erro perturbador;
- [ ] texto em imagem revisado;
- [ ] nenhum logotipo ou pessoa real usados de forma enganosa;
- [ ] conteúdo sintético realista sinalizado quando exigido.

### Técnico

- [ ] resolução e proporção corretas;
- [ ] áudio em ambos os canais;
- [ ] sem clipping ou ruído forte;
- [ ] legendas revisadas;
- [ ] tela final e capítulos funcionam;
- [ ] exportação assistida do início ao fim.

### Direitos e política

- [ ] licença de música e ativos registrada;
- [ ] nenhuma voz clonada sem permissão;
- [ ] ausência de dados pessoais indevidos;
- [ ] descrição não promete resultado financeiro;
- [ ] configuração de conteúdo alterado ou sintético revisada;
- [ ] vídeo compatível com políticas de monetização e comunidade.

## 16. Etapa 10 — publicação

Preparar em `07_publicacao.md`:

- título final;
- descrição concisa;
- fontes citadas quando úteis ou necessárias;
- capítulos com nomes que acrescentem contexto;
- comentário fixado;
- CTA de comentário;
- vídeo relacionado e tela final;
- thumbnail escolhida;
- idioma e legendas;
- declaração de conteúdo sintético, quando aplicável;
- data e horário;
- hipótese do vídeo;
- versões alternativas reservadas.

Após agendar, assistir ao processamento final no YouTube para conferir áudio, resolução, legenda, thumbnail e capítulos.

## 17. Etapa 11 — monitoramento

Capturar snapshots em:

- 24 horas;
- 72 horas;
- 7 dias;
- 28 dias.

Registrar qualquer troca de título ou thumbnail como evento. Sem horário da mudança, os dados anteriores e posteriores ficam misturados e perdem valor.

Não reagir a oscilações pequenas a cada hora. Usar as regras descritas no guia de analytics.

## 18. Etapa 12 — pós-mortem

O arquivo `09_pos_mortem.md` deve responder:

- qual hipótese foi testada?
- qual público e origem de tráfego responderam?
- assunto, embalagem e conteúdo tiveram quais sinais?
- onde ocorreu a maior queda de retenção?
- houve pico ou comentário que revele valor?
- qual decisão manter?
- qual variável mudar no próximo teste?
- o vídeo autoriza pauta adjacente, exige nova embalagem ou deve encerrar a linha?

Registrar uma conclusão principal e uma ação. Muitas conclusões com pouca amostra criam ruído.

## 19. Calendário semanal padrão

Com buffer ativo, duas linhas de produção podem se sobrepor:

| Dia | Episódio A | Episódio B | Sistema |
|---|---|---|---|
| Segunda | pesquisa e embalagem | triagem | revisar analytics e banco |
| Terça | roteiro e aprovação | pesquisa | gerar lotes comuns |
| Quarta | visual e geração | embalagem e roteiro | organizar ativos |
| Quinta | edição e QA | visual e geração | preparar publicação |
| Sexta | publicar ou agendar | edição | registrar snapshot anterior |
| Sábado | monitorar | QA e agendar | derivar Shorts opcionais |
| Domingo | sem produção crítica | publicar ou manter agenda | revisar capacidade |

O calendário é uma referência de capacidade. Datas de publicação devem ser estáveis, mas não se publica um vídeo que falhou em um portão crítico apenas para obedecer ao dia.

## 20. Estratégia de buffer

### Formação

Antes da cadência pública completa, concluir seis vídeos:

- dois agendados;
- dois finalizados;
- dois em produção avançada.

### Manutenção

- **6 ou mais prontos:** operação saudável; experimentar uma pauta de dificuldade média.
- **4–5 prontos:** manter complexidade atual.
- **2–3 prontos:** reduzir clipes gerados e temas de alta pesquisa.
- **0–1 pronto:** pausar expansão, Shorts extras e experimentos visuais; reconstruir estoque.

Buffer não serve para publicar conteúdo fraco. Serve para evitar decisões apressadas.

## 21. Convenções de nomes e versões

### Pastas e arquivos

- usar data ISO e slug sem acento: `2026-10-02-por-que-ganhar-mais-nao-basta`;
- manter os prefixos numéricos dos documentos;
- não usar nomes como `final-final-agora-vai`;
- numerar versões relevantes: `roteiro-v01`, `roteiro-v02`;
- marcar versão aprovada: `roteiro-v03-aprovado`.

### Ativos

Formato sugerido:

`EP##_CENA##_TIPO_VARIANTE.ext`

Exemplos:

- `EP03_CENA07_PERSONAGEM_A.png`
- `EP03_CENA07_CLIP_A.mp4`
- `EP03_THUMB_B_SEM-TEXTO.png`

Não incluir credenciais, nome pessoal ou informação sensível em arquivos.

## 22. Controle de custo e dificuldade

Antes de gerar, classificar cada ativo:

- **Essencial:** sem ele, a compreensão cai.
- **Apoio:** melhora ritmo, mas pode ser substituído.
- **Opcional:** acabamento se houver tempo e crédito.

Ordem de gasto: essencial → thumbnail → apoio → opcional.

Regras:

- não gerar vídeo quando movimento de câmera sobre imagem resolve;
- não pagar nova geração antes de testar recorte, espelhamento permitido, zoom e composição;
- não manter assinatura de ferramenta sem uso mensurável;
- comparar custo por ativo aproveitado, não por ativo gerado;
- revisar mensalmente licenças e limites comerciais.

## 23. Falhas e contingências

### Personagem inconsistente

Voltar à ficha visual, reduzir variáveis do prompt e gerar poses em lote antes das cenas.

### Texto ilegível em imagem

Gerar arte sem texto e inserir tipografia na edição.

### Ferramenta indisponível

Usar o prompt mestre em outro fornecedor; substituir clipe por imagem animada se necessário.

### Roteiro acima de oito minutos

Cortar exemplos repetidos, contexto histórico e ressalvas duplicadas. Não acelerar artificialmente a voz.

### Roteiro abaixo de cinco minutos

Adicionar apenas evidência, consequência, objeção ou cena que aprofunde a tese. Não preencher com repetição.

### Fonte duvidosa

Remover a afirmação ou reformular com grau de certeza correto. Não atrasar o vídeo para defender um detalhe dispensável.

### Produção atrasada

Usar episódio reserva do buffer. Não pular QA.

### Resultado visual fraco

Priorizar composição simples, tipografia e objeto forte. Complexidade não corrige direção ruim.

## 24. Regra de automação

Uma tarefa pode ser automatizada quando:

- é repetitiva;
- possui entrada e saída definidas;
- pode ser verificada por checklist;
- o erro é detectável antes da publicação;
- não exige decisão ética ou factual implícita.

Uma tarefa exige revisão humana quando:

- altera promessa, tese ou contexto;
- interpreta fonte;
- usa rosto, voz ou marca real;
- envolve aconselhamento financeiro;
- decide o que omitir;
- responde a um alerta de política;
- aprova o vídeo final.

## 25. Checklist de conclusão do episódio

- [ ] briefing aprovado;
- [ ] pesquisa e fontes registradas;
- [ ] embalagem principal e reservas prontas;
- [ ] roteiro de 5–8 minutos testado em áudio;
- [ ] pequenas recompensas mapeadas;
- [ ] roteiro visual completo;
- [ ] ativos organizados e licenciados;
- [ ] voz e música aprovadas;
- [ ] legendas revisadas;
- [ ] thumbnail validada em tela pequena;
- [ ] QA editorial, técnico e de política concluído;
- [ ] metadados e configurações revisados;
- [ ] hipótese registrada;
- [ ] snapshots programados;
- [ ] pós-mortem previsto para 28 dias.

## 26. Definição de pronto

Um vídeo está pronto apenas quando pode ser publicado, compreendido, auditado e analisado. Ter um arquivo exportado não basta. O pacote precisa preservar a lógica editorial, as fontes, os direitos, as decisões de embalagem e a hipótese que será medida.
