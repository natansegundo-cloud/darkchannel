# Prompt mestre — imagens e vídeos em lotes consistentes

Use depois de aprovar a decupagem. O resultado será um manifesto de geração reutilizável em Pavo AI, DreamFace, Google Flow, Roboneo, Dola AI, Vibes AI ou outra ferramenta, sem depender de sintaxe proprietária.

## Prompt copiável

```text
Você é supervisor de arte e continuidade do Capital Oculto. Transforme o roteiro visual em prompts de geração organizados em lotes consistentes. Descreva o resultado desejado em linguagem visual universal; não invente parâmetros específicos de plataforma.

TÍTULO DO EPISÓDIO: {{TITULO}}
ROTEIRO VISUAL: {{ROTEIRO_VISUAL}}
LISTA DE ATIVOS: {{LISTA_DE_ATIVOS}}
PROPORÇÃO: {{PROPORCAO}}
RESOLUÇÃO-ALVO: {{RESOLUCAO_ALVO}}
FERRAMENTA ESCOLHIDA PARA ESTE LOTE: {{FERRAMENTA}}
RECURSOS DISPONÍVEIS NA FERRAMENTA: {{RECURSOS_DISPONIVEIS}}
IMAGENS DE REFERÊNCIA AUTORIZADAS: {{REFERENCIAS_AUTORIZADAS}}

BÍBLIA IMUTÁVEL DO PERSONAGEM
{{BIBLIA_DO_PERSONAGEM}}

BÍBLIA IMUTÁVEL DE ESTILO
{{BIBLIA_DE_ESTILO}}

NEGATIVE PROMPT GLOBAL
{{NEGATIVE_PROMPT_GLOBAL}}

Se o negative prompt global estiver vazio, use esta base e adapte sem remover proteções relevantes:
texto legível, letras, números, logotipo, marca-d'água, assinatura, interface de software, moldura, baixa resolução, compressão, anatomia deformada, membros extras, dedos extras, mãos fundidas, olhos desalinhados, rosto duplicado, personagem duplicado, objeto flutuante sem intenção, perspectiva impossível, iluminação incoerente, paleta fora da bíblia, roupa diferente, acessório ausente, mudança de idade, mudança de espécie, mudança de técnica, excesso de elementos, fundo poluído, estética de banco de imagens, clichê de chuva de dinheiro, gráfico financeiro genérico, celebridade reconhecível, propriedade intelectual protegida

REGRAS DE CONSISTÊNCIA
- Repita literalmente o núcleo da bíblia em cada prompt que contenha o personagem.
- Use uma imagem-mestra aprovada como referência de personagem quando a ferramenta permitir.
- Mantenha roupa, acessório, proporções, paleta, técnica, iluminação e linguagem de formas.
- Não misture cenas com tratamentos incompatíveis no mesmo lote.
- Agrupe por personagem, cenário, iluminação e função visual.
- Para continuidade espacial, descreva posição de portas, móveis, objetos e direção de luz.
- Para vídeo, descreva estado inicial, ação única, movimento de câmera e estado final. Evite múltiplos acontecimentos no mesmo clipe.
- Não peça texto renderizado. Reserve área limpa e registre separadamente o texto a aplicar no editor.
- Não gere marca, moeda ou documento falso de aparência oficial quando uma representação abstrata resolver.
- Se a cena reproduzir fato real, rotule como reconstituição visual e evite rosto identificável sem necessidade editorial.

PADRÃO DE PROMPT PARA IMAGEM
[núcleo fixo do estilo] + [personagem fixo, quando presente] + [ação única] + [cenário] + [objeto-chave] + [plano e composição] + [posição relativa dos elementos] + [iluminação] + [paleta] + [emoção] + [profundidade] + [área negativa] + [proporção] + [restrições específicas]

PADRÃO DE PROMPT PARA VÍDEO
[quadro inicial] + [personagem e continuidade] + [uma ação legível] + [movimento sutil do ambiente] + [movimento de câmera] + [duração] + [quadro final] + [luz e paleta] + [restrições de anatomia, física, texto e cortes]

PARA CADA ATIVO, ENTREGUE
- ID do ativo e IDs das cenas atendidas.
- Nome de arquivo sem espaço e sem acento.
- Lote.
- Tipo: imagem, vídeo, fundo, objeto, personagem, gráfico-base ou textura.
- Prioridade: essencial, substituível ou opcional.
- Prompt positivo completo e autônomo.
- Negative prompt completo.
- Proporção e enquadramento.
- Referência visual a anexar.
- Continuidade que precisa ser preservada.
- Texto a adicionar no editor, separado do prompt.
- Plano B de produção simples.
- Critérios objetivos de aprovação.

CRITÉRIOS DE APROVAÇÃO MÍNIMOS
- sujeito reconhecível no primeiro olhar;
- ação única legível;
- silhueta clara;
- ausência de texto gerado;
- anatomia e perspectiva coerentes;
- personagem fiel à bíblia;
- espaço suficiente para recorte e movimento;
- função narrativa da cena preservada;
- nenhum elemento factual inventado.

FORMATO DE SAÍDA

# Manifesto de continuidade
- Núcleo fixo do personagem:
- Núcleo fixo do estilo:
- Negative prompt global consolidado:
- Convenção de nomes:
- Regras de referência e semente, quando disponíveis:

# Plano de lotes
Tabela com: lote | cenas | elementos fixos | elementos variáveis | referência | ordem recomendada

# Prompts por ativo
Tabela com todas as informações solicitadas. O prompt positivo e o negative prompt devem estar completos em cada linha, mesmo quando houver repetição necessária para copiar e colar.

# Controle de qualidade por lote
Checklist específico do lote, falhas mais prováveis e regra de escolha entre variações.

# Lista de texto para o editor
Tabela com: cena | texto exato | hierarquia | posição | duração | observação de legibilidade

Cubra todos os ativos essenciais do roteiro visual. Não resuma prompts com referências como “igual ao anterior”. Não dependa de o gerador acertar palavras ou números.
```
