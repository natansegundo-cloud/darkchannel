# Pacote de upload — {{EPISODIO_ID}}

## Arquivos finais

| Item | Arquivo | Status |
|---|---|---|
| Vídeo master | `{{ARQUIVO_VIDEO_MASTER}}` | {{STATUS_VIDEO_MASTER}} |
| Thumbnail principal | `{{ARQUIVO_THUMB_PRINCIPAL}}` | {{STATUS_THUMB_PRINCIPAL}} |
| Thumbnail alternativa | `{{ARQUIVO_THUMB_ALTERNATIVA}}` | {{STATUS_THUMB_ALTERNATIVA}} |
| Legenda SRT | `{{ARQUIVO_LEGENDA_SRT}}` | {{STATUS_LEGENDA}} |
| Transcrição limpa | `{{ARQUIVO_TRANSCRICAO}}` | {{STATUS_TRANSCRICAO}} |
| Projeto editável | `{{ARQUIVO_PROJETO}}` | {{STATUS_PROJETO}} |
| Comprovantes de licença | `{{PASTA_LICENCAS}}` | {{STATUS_LICENCAS}} |

## Metadados principais

- **Título final:** {{TITULO_FINAL}}
- **Título alternativo:** {{TITULO_ALTERNATIVO}}
- **Texto da thumbnail:** {{TEXTO_THUMB_FINAL}}
- **Nome interno da versão:** {{VERSAO_EMBALAGEM}}
- **Categoria:** {{CATEGORIA_YOUTUBE}}
- **Idioma do vídeo:** Português (Brasil)
- **Idioma do título e descrição:** Português (Brasil)
- **Playlist:** {{PLAYLIST}}
- **Data e hora de publicação:** {{DATA_HORA_PUBLICACAO}}
- **Fuso horário:** America/Sao_Paulo
- **Visibilidade inicial:** {{VISIBILIDADE_INICIAL}}

## Descrição pronta para colar

```text
{{ABERTURA_DA_DESCRICAO_EM_1_OU_2_FRASES}}

Neste vídeo, você vai entender:
• {{APRENDIZADO_1}}
• {{APRENDIZADO_2}}
• {{APRENDIZADO_3}}

{{CONTEXTO_OU_CONVITE_CURTO}}

FONTES E LEITURAS
• {{FONTE_1_TITULO}} — {{FONTE_1_INSTITUICAO}}: {{FONTE_1_URL}}
• {{FONTE_2_TITULO}} — {{FONTE_2_INSTITUICAO}}: {{FONTE_2_URL}}
• {{FONTE_3_TITULO}} — {{FONTE_3_INSTITUICAO}}: {{FONTE_3_URL}}
• {{FONTE_4_TITULO}} — {{FONTE_4_INSTITUICAO}}: {{FONTE_4_URL}}
• {{FONTE_5_OU_REMOVER}} — {{FONTE_5_INSTITUICAO}}: {{FONTE_5_URL}}

TRANSPARÊNCIA
{{DISCLOSURE_DE_IA_OU_DECLARACAO_DE_NAO_APLICABILIDADE}}
{{DECLARACAO_DE_RECONSTITUICAO_OU_NAO_APLICABILIDADE}}

AVISO
Este conteúdo é educativo e informativo. Ele não constitui recomendação individual de investimento, crédito, imposto ou planejamento financeiro. Decisões financeiras dependem do contexto, dos objetivos e dos riscos de cada pessoa.

#CapitalOculto #PsicologiaDoDinheiro #ComportamentoFinanceiro
```

Remova do texto final apenas as linhas explicitamente marcadas como `OU_REMOVER` ou `NAO_APLICABILIDADE` quando não forem necessárias. Não publique variáveis não preenchidas.

## Capítulos

Os títulos dos capítulos devem informar progresso sem entregar toda a conclusão.

```text
00:00 {{CAPITULO_00}}
{{TEMPO_CAPITULO_01}} {{CAPITULO_01}}
{{TEMPO_CAPITULO_02}} {{CAPITULO_02}}
{{TEMPO_CAPITULO_03}} {{CAPITULO_03}}
{{TEMPO_CAPITULO_04}} {{CAPITULO_04}}
{{TEMPO_CAPITULO_05}} {{CAPITULO_05}}
{{TEMPO_CAPITULO_FINAL}} {{CAPITULO_FINAL}}
```

## Comentário fixado

```text
{{PERGUNTA_ESPECIFICA_PARA_COMENTARIOS}}

O ponto do vídeo que mais muda a leitura do problema é: {{MICRO_RESUMO_DA_TESE}}.

Fontes completas estão na descrição. Este conteúdo é educativo e não é recomendação financeira individual.
```

## Tela final e cards

| Momento | Elemento | Destino | Motivo |
|---|---|---|---|
| {{TEMPO_CARD_1}} | Card | {{DESTINO_CARD_1}} | {{MOTIVO_CARD_1}} |
| {{TEMPO_CARD_2}} | Card | {{DESTINO_CARD_2}} | {{MOTIVO_CARD_2}} |
| {{TEMPO_TELA_FINAL}} | Vídeo recomendado | {{DESTINO_TELA_FINAL_1}} | {{MOTIVO_TELA_FINAL_1}} |
| {{TEMPO_TELA_FINAL}} | Inscrição | Canal Capital Oculto | {{MOTIVO_INSCRICAO}} |

## Legendas

- **Origem:** {{ORIGEM_LEGENDAS}}
- **Revisão humana concluída:** {{STATUS_REVISAO_LEGENDAS}}
- **Nomes e termos conferidos:** {{TERMOS_CONFERIDOS}}
- **Números e moedas conferidos:** {{NUMEROS_CONFERIDOS}}
- **Quebras adequadas para celular:** {{STATUS_QUEBRAS}}

## Conteúdo sintético e reconstituições

- **Há mídia sintética realista de pessoa, lugar ou evento real?** {{HA_MIDIA_SINTETICA_REALISTA}}
- **A opção de conteúdo alterado ou sintético deve ser marcada?** {{MARCAR_CONTEUDO_ALTERADO}}
- **Justificativa:** {{JUSTIFICATIVA_DISCLOSURE}}
- **Texto exibido no vídeo:** {{TEXTO_DISCLOSURE_NO_VIDEO}}
- **Reconstituições identificadas:** {{RECONSTITUICOES_IDENTIFICADAS}}

## Links externos

| Texto | URL | Origem autorizada | UTM | Verificado |
|---|---|---|---|---|
| {{LINK_1_TEXTO}} | {{LINK_1_URL}} | {{LINK_1_ORIGEM}} | {{LINK_1_UTM}} | {{LINK_1_STATUS}} |
| {{LINK_2_TEXTO}} | {{LINK_2_URL}} | {{LINK_2_ORIGEM}} | {{LINK_2_UTM}} | {{LINK_2_STATUS}} |

Não inclua link de afiliado sem declaração clara. Não inclua encurtador desconhecido ou URL que exponha dado sensível.

## Registro da embalagem publicada

- **Versão:** A
- **Título:** {{TITULO_PUBLICADO_A}}
- **Thumbnail:** {{THUMB_PUBLICADA_A}}
- **Data e hora de início:** {{INICIO_VERSAO_A}}
- **Hipótese:** {{HIPOTESE_VERSAO_A}}
- **Condição de reavaliação:** {{CONDICAO_REAVALIACAO_A}}

## Checklist do pacote

- [ ] Título corresponde ao arquivo aprovado.
- [ ] Thumbnail tem 1280 × 720 px e menos que o limite atual da plataforma.
- [ ] Descrição não contém variável sem preencher.
- [ ] Links de fontes abrem diretamente.
- [ ] Aviso financeiro está presente quando aplicável.
- [ ] Disclosure de IA ou reconstituição foi decidido conscientemente.
- [ ] Capítulos correspondem ao corte final.
- [ ] Legendas foram revisadas depois do render final.
- [ ] Cards e tela final levam a destinos válidos.
- [ ] Playlist foi selecionada.
- [ ] Comentário fixado está pronto.
- [ ] Versão A da embalagem foi registrada para análise posterior.

