# Analytics e experimentos — Capital Oculto

## 1. Objetivo

Analytics existe para responder três perguntas diferentes:

1. **A ideia e a embalagem conquistaram o clique?**
2. **O vídeo cumpriu a promessa e manteve atenção?**
3. **O conteúdo gerou valor para o canal além de uma visualização isolada?**

Nenhuma métrica, sozinha, responde às três. O sistema deve evitar decisões emocionais, registrar mudanças e transformar cada vídeo em um aprendizado utilizável.

## 2. Princípios de análise

- comparar primeiro com o próprio canal;
- comparar vídeos de idade, duração e origem de tráfego semelhantes;
- separar assunto, embalagem, conteúdo e distribuição;
- preservar snapshots, não apenas o número atual;
- distinguir dado observado de interpretação;
- testar uma variável relevante por vez quando possível;
- não declarar causalidade a partir de um único vídeo;
- não apagar vídeos apenas por desempenho fraco;
- não alterar título ou thumbnail sem registrar horário e hipótese;
- aceitar que vídeos podem continuar encontrando público por semanas ou meses.

## 3. O funil de desempenho

```text
Público potencial
      ↓
Impressões qualificadas
      ↓  título + thumbnail
Cliques e visualizações
      ↓  promessa + gancho
Retenção inicial
      ↓  progressão + recompensas
Tempo de exibição
      ↓  satisfação + afinidade
Retorno, inscrição e próximo vídeo
```

O ponto de falha mais alto no funil deve ser investigado antes dos pontos abaixo.

## 4. Fontes de dados

Usar como fonte principal o YouTube Studio. Prints ajudam na leitura, mas os valores importantes devem ser transcritos para os arquivos estruturados do projeto.

Fontes complementares permitidas:

- relatório avançado exportado do YouTube;
- histórico de versões de título e thumbnail;
- comentários do vídeo;
- documentação oficial do YouTube;
- planilhas ou CSVs gerados pelo próprio projeto.

Não usar extensões de estimativa externa como verdade sobre receita, retenção ou tráfego de outro canal.

## 5. Cadastro mestre do vídeo

O arquivo de vídeos deve manter uma linha por publicação com, no mínimo:

- `video_id`;
- `slug`;
- `titulo_publicado`;
- `data_hora_publicacao`;
- `duracao_segundos`;
- `pilar`;
- `subtema`;
- `formato_narrativo`;
- `emocao_dominante`;
- `mecanismo_principal`;
- `versao_thumb_inicial`;
- `hipotese_editorial`;
- `dificuldade_producao`;
- `custo_estimado`;
- `status`;
- `observacoes`.

O título atual pode mudar; o título original precisa permanecer registrado.

## 6. Snapshots obrigatórios

Capturar dados acumulados nestes marcos:

- 24 horas;
- 72 horas;
- 7 dias;
- 28 dias.

Snapshots adicionais são úteis quando:

- uma troca de título ou thumbnail acontece;
- o vídeo recebe uma onda de distribuição;
- uma fonte externa importante aparece;
- o vídeo entra em uma comparação trimestral.

### Campos mínimos por snapshot

- `video_id`;
- `capturado_em`;
- `idade_horas`;
- `visualizacoes`;
- `impressoes`;
- `ctr_impressoes_pct`;
- `tempo_exibicao_horas`;
- `duracao_media_segundos`;
- `percentual_medio_assistido`;
- `retencao_30s_pct`;
- `inscritos_ganhos`;
- `likes`;
- `comentarios`;
- `compartilhamentos`, quando disponível;
- `espectadores_unicos`, quando disponível;
- `novos_espectadores`, quando disponível;
- `espectadores_recorrentes`, quando disponível;
- visualizações por fonte de tráfego;
- impressões e CTR por fonte, quando disponíveis;
- `receita_estimada`, somente após monetização;
- `rpm`, somente após monetização;
- `versao_titulo`;
- `versao_thumbnail`;
- `evento_desde_snapshot_anterior`;
- `nota_analista`.

Campo indisponível deve ficar vazio ou marcado como não disponível conforme o padrão do arquivo; nunca inventar zero.

## 7. Pacote de prints

Quando o operador enviar telas para análise, buscar este conjunto:

1. visão geral do vídeo no período correto;
2. aba Alcance com impressões, CTR e fontes;
3. aba Engajamento com duração média e percentual médio;
4. gráfico completo de retenção, incluindo primeiros 30 segundos;
5. momentos importantes identificados pelo Studio;
6. aba Público com novos e recorrentes, quando houver dados;
7. origem de tráfego detalhada;
8. título e thumbnail ativos no momento da captura;
9. comparação com desempenho típico mostrada pela plataforma;
10. receita e RPM somente quando relevante e disponível.

### Como nomear prints

Formato recomendado:

`video_id__marco__painel__AAAA-MM-DD_HHMM.png`

Exemplo:

`CO-007__72h__retencao__2026-10-18_2100.png`

Não cortar data, período selecionado ou legenda do gráfico. Ocultar dados pessoais e informações de pagamento antes de compartilhar.

## 8. Métricas e o que elas realmente indicam

### Impressões

Indicam quantas vezes a thumbnail foi exibida em superfícies contabilizadas. Não representam todo alcance possível e não incluem todas as fontes.

Pergunta: a plataforma está encontrando ocasiões para oferecer o vídeo?

### CTR de impressões

Indica a proporção de impressões contabilizadas que geraram visualização. Muda conforme fonte, público e expansão da distribuição.

Pergunta: naquela origem e audiência, a embalagem convenceu?

### Retenção aos 30 segundos

Ajuda a avaliar confirmação de promessa, clareza do gancho e atrito inicial.

Pergunta: quem clicou percebeu rapidamente que estava no vídeo certo?

### Duração média

Mostra minutos médios assistidos. É útil para comparar vídeos de duração semelhante.

Pergunta: quantos minutos de valor o vídeo sustentou?

### Percentual médio assistido

Normaliza a duração assistida em relação ao tamanho do vídeo. Ainda precisa ser lido com a curva.

Pergunta: qual proporção da experiência foi consumida?

### Tempo de exibição

Combina alcance e permanência. É central para crescimento e para o requisito aplicável de horas públicas do YPP, mas deve respeitar as definições oficiais de horas válidas.

Pergunta: o vídeo produziu tempo de atenção total relevante?

### Inscritos por mil visualizações

Cálculo interno:

`inscritos ganhos ÷ visualizações × 1.000`

Pergunta: o vídeo converteu interesse pontual em intenção de acompanhar o canal?

### RPM

Receita por mil visualizações após a participação do YouTube e considerando receitas incluídas na métrica. Varia por geografia, época, inventário, formato e público.

Pergunta: quanto a audiência atual gera por mil visualizações, sem confundir isso com garantia futura?

## 9. Métricas derivadas internas

### Segundos assistidos por impressão

Estimativa simples:

`CTR em decimal × duração média em segundos`

Ela aproxima a força conjunta de embalagem e consumo nas impressões contabilizadas. Comparar somente em contextos semelhantes, pois nem toda visualização vem de impressão registrada.

### Velocidade de visualizações

`novas visualizações desde o snapshot anterior ÷ horas do intervalo`

Ajuda a identificar aceleração ou desaceleração, sem assumir que a trajetória continuará.

### Conversão de comentário

`comentários ÷ visualizações × 1.000`

Usar como sinal qualitativo. Um tema controverso pode gerar muitos comentários sem maior satisfação.

### Eficiência de produção

`tempo total de exibição ÷ horas de produção`

Métrica interna de operação. Não deve favorecer conteúdo barato se ele comprometer identidade, segurança ou aprendizado.

## 10. Metas internas iniciais

Estas faixas servem apenas como hipóteses de trabalho para vídeos de 5 a 8 minutos. Não são médias universais do YouTube, não garantem distribuição e não devem ser aplicadas sem considerar a origem do tráfego.

| Métrica | Atenção | Faixa de trabalho | Sinal inicial forte |
|---|---:|---:|---:|
| CTR em Início/Recursos de navegação | abaixo de 3,5% | 3,5%–5,5% | acima de 5,5% |
| Retenção aos 30 segundos | abaixo de 55% | 55%–70% | acima de 70% |
| Percentual médio assistido | abaixo de 35% | 35%–45% | acima de 45% |
| Cadência | menos de 2 longos/semana | 2 longos/semana | 2 com buffer preservado |
| Buffer | 0–1 pronto | 2–5 prontos | 6 prontos |

Após pelo menos 12 vídeos comparáveis, substituir o julgamento primário por:

- mediana móvel dos últimos 10 vídeos;
- faixa interquartil do canal;
- comparação por pilar, formato e duração;
- comparação pela mesma fonte de tráfego;
- desempenho relativo no mesmo marco de idade.

Manter as faixas iniciais apenas como referência histórica.

## 11. Linha de base do canal

### Antes de 12 vídeos

Tratar resultados como exploração. Buscar padrões, mas evitar mudanças amplas de posicionamento.

### De 12 a 30 vídeos

Criar linhas de base por:

- CTR em navegação;
- retenção aos 30 segundos;
- percentual médio assistido;
- inscritos por mil visualizações;
- pilar;
- formato narrativo;
- faixa de duração.

### Após 30 vídeos

Avaliar também:

- público recorrente;
- séries e clusters;
- sazonalidade;
- valor de catálogo após 28 dias;
- eficiência de produção;
- receita por geografia e assunto, se monetizado.

Usar mediana em vez de média quando poucos vídeos muito grandes distorcerem o conjunto.

## 12. Janelas de decisão

### Antes de 24 horas

Não otimizar por ansiedade. Corrigir imediatamente apenas:

- erro factual grave;
- título ou thumbnail errados;
- áudio, processamento ou legenda quebrados;
- violação de política;
- discrepância evidente entre embalagem e conteúdo.

### Em 24 horas

- capturar primeiro snapshot;
- verificar fonte de tráfego;
- confirmar que o vídeo está sendo distribuído e processado normalmente;
- anotar sinais, sem declarar vencedor.

### Em 72 horas

- comparar com vídeos da mesma idade;
- analisar combinação de CTR e retenção;
- considerar teste de embalagem quando houver amostra útil;
- identificar quedas iniciais e no meio.

### Em 7 dias

- avaliar assunto, embalagem, conteúdo e conversão;
- decidir se existe pauta adjacente;
- registrar uma conclusão operacional.

### Em 28 dias

- realizar pós-mortem final do ciclo;
- classificar comportamento de catálogo;
- atualizar linhas de base;
- decidir manter, variar, testar ou encerrar a linha.

## 13. Tamanho de amostra e prudência

Como regra interna inicial:

- evitar conclusão sobre CTR de navegação antes de aproximadamente 1.000 impressões relevantes;
- tratar retenção com menos de 100 visualizações como altamente instável;
- preferir comparação no mesmo marco de tempo;
- usar a significância indicada pela ferramenta de teste do YouTube quando disponível;
- não somar origens muito diferentes para diagnosticar thumbnail;
- exigir repetição em pelo menos três vídeos antes de chamar um padrão editorial de comprovado.

Esses limites são decisões de operação, não garantias estatísticas nem requisitos do YouTube. Quanto menor a diferença entre versões, maior deve ser a cautela.

## 14. Matriz de diagnóstico

| Impressões | CTR | Retenção | Diagnóstico prioritário | Ação |
|---|---|---|---|---|
| baixas | inconclusiva | boa | tema ou público ainda não encontrou distribuição | esperar janela, verificar fonte e testar pauta adjacente |
| altas | baixa | boa | embalagem não traduz o valor | testar título ou thumbnail |
| altas | alta | queda até 30s | promessa ou abertura desalinhada | revisar primeiro bloco nos próximos roteiros |
| altas | alta | queda no meio | progressão perdeu novidade | localizar trecho e estudar a função narrativa |
| altas | alta | alta | combinação forte | produzir adjacência, não cópia |
| baixas | baixa | baixa | proposta completa ainda fraca ou amostra inadequada | reavaliar assunto e execução; não trocar tudo sem hipótese |
| crescentes | CTR caindo | retenção estável | expansão para público mais amplo pode estar ocorrendo | observar alcance total antes de intervir |

## 15. Leitura da curva de retenção

Marcar:

- retenção no início;
- primeira queda forte;
- quedas graduais;
- picos de replay;
- trechos estáveis;
- momento em que a promessa principal é entregue;
- início do CTA;
- retenção no encerramento.

Para cada ponto, cruzar:

- frase narrada;
- cena exibida;
- tipo de recompensa;
- pergunta aberta;
- mudança de assunto;
- densidade de informação;
- comentário do público relacionado.

Uma queda não prova a causa. Formular hipótese e procurar recorrência em outros vídeos.

## 16. Taxonomia de causas

Usar uma categoria principal no pós-mortem:

### Assunto

- dor pouco relevante;
- alcance de público estreito;
- tese já conhecida;
- timing inadequado;
- promessa sem consequência.

### Embalagem

- título abstrato;
- thumbnail confusa;
- texto ilegível;
- título e imagem redundantes;
- emoção fraca;
- curiosidade enganosa.

### Abertura

- contexto antes da tensão;
- promessa não confirmada;
- introdução institucional;
- linguagem genérica;
- ritmo lento;
- cena sem identificação.

### Corpo

- repetição;
- excesso de teoria;
- exemplo longo;
- transição confusa;
- pouca novidade;
- visual sem função;
- promessa entregue cedo sem nova camada.

### Distribuição

- amostra pequena;
- tráfego externo atípico;
- público diferente do esperado;
- expansão rápida para audiência ampla;
- catálogo ainda pequeno.

### Operação

- atraso;
- áudio ruim;
- erro de legenda;
- visual inconsistente;
- falta de registro;
- alteração múltipla que impede aprendizado.

## 17. Registro de experimentos

Cada teste deve conter:

- `experimento_id`;
- `video_id`;
- pergunta;
- hipótese;
- variável alterada;
- elemento preservado;
- versão controle;
- versão teste;
- métrica primária;
- métricas de proteção;
- início e fim;
- tamanho da amostra;
- fontes de tráfego incluídas;
- resultado observado;
- grau de confiança: baixo, médio ou alto;
- decisão;
- aprendizado transferível.

### Métricas de proteção

Uma melhoria de CTR não é vitória se a retenção inicial cair por promessa enganosa. Sempre acompanhar:

- retenção aos 30 segundos;
- duração média;
- tempo de exibição;
- comentários que indiquem desalinhamento;
- adequação às políticas.

## 18. Tipos de experimento

### Embalagem

- consequência versus mecanismo no título;
- rosto versus objeto dominante;
- texto curto versus sem texto;
- emoção de medo versus frustração;
- composição dividida versus foco único.

### Gancho

Aplicar em vídeos diferentes comparáveis, pois o vídeo publicado não permite trocar o arquivo:

- história primeiro versus pergunta primeiro;
- consequência primeiro versus dado primeiro;
- personagem em primeira frase versus cenário geral.

### Corpo

- explicação antes do estudo versus estudo antes da explicação;
- personagem recorrente versus exemplos múltiplos;
- mapa visual versus metáfora concreta.

### Publicação

- dia ou horário, somente após volume suficiente;
- uso de Shorts derivados;
- comentário fixado com pergunta específica.

Evitar testar horário quando o canal ainda tem poucos espectadores recorrentes; o efeito pode ser menor do que assunto e embalagem.

## 19. Regras para trocar título ou thumbnail

Trocar quando:

- existe amostra suficiente para sinal direcional;
- CTR está abaixo da linha de base da mesma origem;
- retenção indica que o conteúdo satisfaz melhor do que a embalagem atrai;
- a nova versão expressa hipótese clara;
- a troca e o horário serão registrados.

Não trocar quando:

- há poucas impressões;
- o vídeo está expandindo e a queda de CTR vem acompanhada de forte crescimento de visualizações;
- a nova versão só aumenta exagero;
- título e thumbnail seriam alterados juntos sem necessidade;
- o operador pretende fazer várias trocas rápidas.

Erros, violações e promessa incompatível devem ser corrigidos independentemente da amostra.

## 20. Regras para repetir um assunto

### Criar adjacência quando

- CTR e retenção estão acima da linha de base;
- comentários revelam perguntas relacionadas;
- o mecanismo comporta outra situação concreta;
- o novo vídeo tem promessa própria.

### Testar nova embalagem quando

- retenção e satisfação parecem fortes;
- CTR está abaixo da linha de base;
- o assunto continua relevante;
- a promessa pode ser expressa com mais clareza.

### Encerrar temporariamente quando

- três testes relacionados falham pelo mesmo motivo;
- o assunto exige exagero para gerar clique;
- a produção custa muito e não acrescenta valor;
- as fontes não sustentam novas variações.

Não apagar o aprendizado; registrar por que a linha foi pausada.

## 21. Revisão a cada seis vídeos

Responder:

- quais dois assuntos tiveram melhor resposta e por quê?
- quais duas embalagens foram mais eficientes?
- quais aberturas preservaram mais público aos 30 segundos?
- onde as curvas caem com frequência?
- qual formato consome mais produção do que retorna em atenção?
- quais comentários revelam linguagem do público?
- houve desequilíbrio entre pilares?
- quais hipóteses ainda estão inconclusivas?
- qual única mudança sistêmica entra no próximo bloco?

Uma revisão de seis vídeos ajusta execução. Mudança de posicionamento deve preferencialmente esperar pelo menos doze vídeos e evidência consistente.

## 22. Relatório de 28 dias

Estrutura mínima:

1. identificação do vídeo;
2. hipótese inicial;
3. versões de embalagem e horários;
4. resultados por marco;
5. fontes de tráfego;
6. leitura da curva;
7. qualidade dos comentários;
8. inscritos e retorno;
9. custo e dificuldade;
10. comparação com linha de base;
11. conclusão principal;
12. próxima ação;
13. confiança da conclusão;
14. risco de interpretação.

## 23. Categorias de resultado

Classificar somente após a janela escolhida:

- **Vencedor de sistema:** embalagem e conteúdo fortes; gera pauta adjacente.
- **Vencedor de embalagem:** clique forte, mas conteúdo precisa melhorar.
- **Vencedor de conteúdo:** retenção forte, mas embalagem limita alcance.
- **Exploração útil:** desempenho mediano, aprendizado claro.
- **Inconclusivo:** amostra ou dados insuficientes.
- **Falha diagnosticada:** sinal consistente e causa provável documentada.

“Fracasso” sem diagnóstico não ajuda. “Viral” sem repetibilidade também não constitui sistema.

## 24. Receita e monetização

Após a entrada no YPP, analisar receita separadamente de qualidade editorial.

Segmentar, quando disponível:

- RPM por vídeo;
- geografia da audiência;
- fonte de tráfego;
- duração e presença de intervalos de anúncio elegíveis;
- sazonalidade;
- adequação para anunciantes;
- receita de anúncios versus outras fontes.

Não escolher pauta somente pelo RPM de um vídeo. Um assunto pode ter RPM maior e público muito menor; outro pode construir retorno e catálogo. Avaliar receita total, audiência, custo e sustentabilidade.

## 25. Integridade dos dados

- usar o mesmo fuso horário nos registros;
- manter datas e horas completas;
- não sobrescrever snapshots antigos;
- marcar dados estimados;
- usar vírgula ou ponto decimal de forma consistente no CSV;
- validar que percentuais não foram convertidos duas vezes;
- não preencher campo indisponível com zero;
- preservar ID do vídeo mesmo após troca de título;
- registrar mudanças manuais;
- fazer cópia de segurança regular fora do diretório ativo.

## 26. Privacidade

Antes de salvar ou compartilhar prints:

- ocultar e-mail;
- ocultar dados de pagamento;
- ocultar identificadores pessoais desnecessários;
- não armazenar credenciais;
- não incluir dados individuais de espectadores;
- manter apenas informação necessária para decisão editorial.

## 27. Checklist por snapshot

- [ ] período correto selecionado;
- [ ] idade do vídeo registrada;
- [ ] título e thumbnail ativos anotados;
- [ ] métricas acumuladas copiadas;
- [ ] fontes de tráfego registradas;
- [ ] curva de retenção salva quando disponível;
- [ ] mudanças desde o marco anterior documentadas;
- [ ] dado ausente não foi tratado como zero;
- [ ] observação separa fato e hipótese;
- [ ] próxima ação possui responsável e momento de revisão.

## 28. Regra final

O objetivo da análise não é justificar uma impressão anterior. É reduzir incerteza para a próxima decisão. O canal deve agir sobre padrões repetidos, preservar contexto e continuar testando sem transformar faixas internas em leis universais.
