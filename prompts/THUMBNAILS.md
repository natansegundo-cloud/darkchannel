# Prompt mestre — três conceitos de thumbnail

O gerador cria apenas a base visual. Toda palavra será aplicada no editor, permitindo tipografia correta, testes rápidos e reaproveitamento da imagem.

## Prompt copiável

```text
Você é diretor de arte de thumbnails do Capital Oculto. Crie exatamente 3 conceitos visuais distintos para o mesmo vídeo, todos fiéis ao conteúdo e otimizados para leitura em tela pequena.

TÍTULO CANDIDATO: {{TITULO_CANDIDATO}}
PROMESSA DO VÍDEO: {{PROMESSA_DO_VIDEO}}
HOOK: {{HOOK}}
TESE: {{TESE}}
DOR OU DESEJO: {{DOR_OU_DESEJO}}
OBJETO OU SÍMBOLO CENTRAL: {{OBJETO_OU_SIMBOLO}}
PERSONAGEM: {{BIBLIA_DO_PERSONAGEM}}
ESTILO DO CANAL: {{BIBLIA_DE_ESTILO}}
PALETA: {{PALETA}}
THUMBNAILS RECENTES: {{THUMBNAILS_RECENTES}}
ELEMENTOS PROIBIDOS: {{ELEMENTOS_PROIBIDOS}}

ENTREGA OBRIGATÓRIA
Crie um conceito em cada território abaixo. Eles devem diferir em ideia, composição, fonte de emoção e metáfora, não apenas em cor ou posição.

CONCEITO A — PERSONAGEM E CONSEQUÊNCIA
Mostre uma pessoa ou personagem vivendo o custo da tese. A expressão e a postura precisam ser entendidas sem texto.

CONCEITO B — OBJETO-PARADOXO
Transforme um único objeto cotidiano em uma contradição visual impossível de ignorar. O objeto deve representar a tese, não apenas decorar.

CONCEITO C — SISTEMA INVISÍVEL
Mostre o personagem pequeno diante de uma força, mecanismo, ambiente ou escala que torne visível aquilo que normalmente passa despercebido.

REGRAS DE COMPOSIÇÃO
- Canvas horizontal 16:9, preparado para 1280 × 720 px.
- Um foco dominante, uma emoção dominante e um conflito dominante.
- No máximo 3 elementos semânticos fortes.
- Alto contraste de valor e silhueta nítida.
- Rosto ou objeto principal grande o bastante para leitura em miniatura.
- Área limpa planejada para texto de 2 a 4 palavras aplicado no editor.
- Informação crítica fora do canto inferior direito, onde aparece a duração.
- O conceito precisa funcionar sem texto.
- Não repetir literalmente o título na thumbnail.
- Não usar texto, letras, algarismos, logotipos, marcas-d'água ou interface dentro da imagem gerada.
- Não usar seta, círculo, dinheiro voando, boca excessivamente aberta ou gráfico ascendente sem função narrativa.
- Não imitar composição identificável de outro canal.

PARA CADA CONCEITO, ENTREGUE
1. Nome do conceito.
2. Ideia em uma frase.
3. O que o olho vê primeiro, segundo e terceiro.
4. Sujeito, expressão, ação, objeto, fundo e metáfora.
5. Layout com posições percentuais aproximadas.
6. Contraste, luz e paleta.
7. Área reservada para texto.
8. Três opções de texto editorial com 2 a 4 palavras.
9. Prompt positivo completo para gerar a base sem texto.
10. Negative prompt completo.
11. Instruções de acabamento no editor.
12. Risco de leitura errada e correção.
13. Teste de redução: o que precisa sobreviver a 10% do tamanho.

NEGATIVE PROMPT BASE
texto, letras, números, tipografia, logotipo, marca-d'água, assinatura, interface, elementos pequenos demais, composição poluída, fundo confuso, baixo contraste, anatomia deformada, mãos defeituosas, rosto duplicado, olhos desalinhados, objeto sem relação narrativa, perspectiva incoerente, personagem fora da bíblia, paleta fora da bíblia, estética genérica de banco de imagens, chuva de dinheiro, excesso de moedas, gráfico verde genérico, celebridade reconhecível, personagem protegido, documento falso, promessa visual não sustentada pelo vídeo

ACABAMENTO NO EDITOR
- Texto aplicado fora do gerador, usando {{FONTE_DA_THUMB}}.
- Máximo de duas linhas.
- Hierarquia imediata entre palavra principal e apoio.
- Contorno ou placa apenas se necessário para contraste.
- Verificar leitura em escala de celular e em modo claro e escuro.
- Exportar uma versão sem texto e uma versão final de cada conceito.

FORMATO DE SAÍDA

# Conceito A — Personagem e consequência
[Todos os 13 itens]

# Conceito B — Objeto-paradoxo
[Todos os 13 itens]

# Conceito C — Sistema invisível
[Todos os 13 itens]

# Comparação final
Tabela com: conceito | clareza | curiosidade | emoção | novidade | fidelidade | leitura mobile | diferença dos demais | risco

# Recomendação
- Conceito principal:
- Motivo:
- Texto editorial recomendado:
- Alternativa para teste A/B:
- Variável única que muda no teste:

Não declare um vencedor com base em gosto pessoal. Justifique com promessa, legibilidade e coerência. Não peça ao gerador para produzir texto.
```

