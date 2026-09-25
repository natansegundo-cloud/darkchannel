# Geração visual vetorial local

## Decisão

O Capital Oculto usa SVG programático como pipeline visual principal. A prioridade é produzir dezenas de cenas com custo zero, funcionamento offline, baixo consumo de RAM e consistência entre episódios.

O estilo publicado permanece `CO_SKETCH_V1`, configurado em `config/vector_style.json`. O sistema candidato é `CO_VISUAL_V3`, definido em `config/vector_style_v3.json`; `CO_VECTOR_V2` foi preservado como etapa histórica e nenhuma cena anterior é sobrescrita durante a avaliação.

## Migração visual V3

O V3 mantém o episódio em long-form horizontal `1920x1080` e corrige os principais pontos fracos dos pilotos anteriores:

- personagem único vindo do rig V4: `char-base` é o único `symbol`, enquanto as oito partes corporais permanecem como `g` no mesmo sistema de coordenadas;
- Phosphor Icons como biblioteca local principal, com licença preservada;
- paleta reduzida a fundo, preto e um destaque por cena;
- traço limpo sem filtro de roughness;
- uma ideia visual dominante e no máximo um elemento de contexto;
- personagem como identidade opcional, não obrigação;
- seis layouts oficiais para controlar ritmo e evitar repetição;
- composições assimétricas, safe area absoluta de 64 px e safe area de texto de 96 px;
- validação obrigatória parada, sem narração, a 25% e com leitura aproximada de dois segundos.

O piloto usa S001, S007 e S033 por cobrirem respectivamente abertura emocional, metáfora conceitual e visualização numérica. Ele é gerado sem alterar o V1:

```powershell
python scripts/gerar_piloto_visual_v3.py --atualizar
powershell -ExecutionPolicy Bypass -File scripts/renderizar_svg_preview.ps1 -Episode CO-001 -Variant v3 -Files s001,s007,s033,review_v3_pilot_25 -Update
python scripts/validar_visual_v3.py
```

Fonte de verdade do novo sistema: `docs/VISUAL_SYSTEM_V3.md`.

### Sprint de direção de arte V4

O V3 técnico permanece, mas a linguagem visual candidata agora é definida em `docs/ART_DIRECTION_V4.md`. Antes de qualquer nova animação, gerar e aprovar os seis frames estáticos:

```powershell
python scripts/gerar_sprint_art_direction_v4.py
powershell -ExecutionPolicy Bypass -File scripts/renderizar_svg_preview.ps1 -SceneRoot "episodios/CO-001-por-que-ganhar-mais-nao-basta/testes/art_direction_v4_s001_s006" -Files "s001,s002,s003,s004,s005,s006,review_art_direction_v4_25" -Update
python scripts/validar_art_direction_v4.py
```

Ícones de biblioteca não podem ser protagonistas nem ocupar mais de 10% da tela. O personagem só aparece com função narrativa declarada. O board estático é a próxima barreira de aprovação.

Antes de qualquer geração V2, o contrato estrutural do personagem deve passar em:

```powershell
python scripts/validar_rig_personagem.py
```

O validador do rig impede regressões para a arquitetura antiga de symbols aninhados. O arquivo canônico é `assets/characters/capital_oculto_character_rig_v4.svg`; nenhuma cena pode copiar a geometria do personagem. O validador do V3 verifica também canvas, grid, raiz de cena como grupo, presença planejada do personagem, escala visual, layouts, manifesto e board exato a 25%.

Antes da migração integral, o teste sequencial S001–S006 deve passar por:

```powershell
python scripts/gerar_narracao_local.py --entrada "episodios/CO-001-por-que-ganhar-mais-nao-basta/03_ROTEIRO_NARRACAO.md" --beats B001,B002,B003,B004,B005,B006 --saida "episodios/CO-001-por-que-ganhar-mais-nao-basta/testes/v3_sequencial_s001_s006/narracao_pipeline.wav" --timing-json "episodios/CO-001-por-que-ganhar-mais-nao-basta/03A_AUDIO_TIMING.json" --episodio-id CO-001
python scripts/resolver_timeline_audiovisual.py CO-001 --visual "episodios/CO-001-por-que-ganhar-mais-nao-basta/testes/v3_sequencial_s001_s006/04_ROTEIRO_VISUAL.csv"
python scripts/gerar_teste_sequencial_v3.py
python scripts/exportar_teste_sequencial_v3.py --timeout 120
python scripts/validar_teste_sequencial_v3.py
```

O teste usa 39,5 segundos da voz Santa, seis beats e seis cenas consecutivas. Os cortes e eventos vêm dos timestamps reais de `create_timed()`, resolvidos por anchors narrativos no `04A_SCENE_MANIFEST.json`. A aprovação humana do WebM é pré-requisito para trocar o sistema de `CANDIDATE` para `LOCKED FOR CO-001`.

O contrato completo está em `docs/PIPELINE_AUDIOVISUAL.md`.

## Como a cena é montada

Cada cena combina uma ideia visual dominante com, no máximo, um elemento de contexto. O personagem só entra quando acrescenta emoção, escala humana, continuidade ou reação. Metáforas, gráficos e números podem ocupar o quadro sozinhos.

A paleta, espessuras, tipografia, grid, proporções e semântica de cor ficam centralizadas. O acabamento vem de escala, hierarquia e composição editorial — não da multiplicação de miniaturas ou efeitos.

## Estrutura

- `assets/characters/`: personagens mestres `CO_WORKER_V1` e `CO_ANA_V1`.
- `assets/expressions/`: expressões isoladas.
- `assets/poses/`: poses de corpo inteiro.
- `assets/objects/`: objetos reutilizáveis.
- `assets/backgrounds/`: fundos aprovados.
- `assets/scenes/CO-001/`: cenas finais e manifesto do protótipo.
- `assets/library_manifest_v3.csv`: origem e primeira utilização dos assets do sistema candidato.
- `episodios/CO-001-*/assets/vector_scenes.json`: descritores de cena, câmera e ações.
- `config/vector_style_v3.json`: configuração do sistema visual candidato.
- `docs/VISUAL_SYSTEM_V3.md`: fonte de verdade visual da migração.
- `scripts/gerar_piloto_visual_v3.py`: compositor do piloto V3.
- `scripts/validar_visual_v3.py`: contrato automatizado do V3.
- `scripts/gerar_cenas_svg.py`: compositor com biblioteca padrão do Python.
- `scripts/renderizar_svg_preview.ps1`: renderizador local de previews PNG para revisão.

## Regra de criação sob demanda

Nenhum asset é produzido para “talvez usar depois”. Ele só entra na biblioteca quando uma cena real do episódio exige sua existência. `first_used_scene` é obrigatório e o gerador valida se o arquivo e a cena de estreia existem.

## Histórico V1 preservado

S001–S005 formam o style board original e exercitam cinco famílias visuais diferentes:

1. close dramático com celular;
2. passagem de tempo com calendários;
3. contradição entre aumento e saldo;
4. montagem em três vinhetas;
5. mapa de três mecanismos.

S006–S010 acrescentam apenas os componentes exigidos pelo mecanismo de adaptação:

1. console cerebral;
2. régua do novo normal;
3. celular genérico com estado brilhante e estado cotidiano;
4. expressão fascinada;
5. curva original de três ondas.

S011–S015 fecham o mecanismo de adaptação e introduzem a ressalva material:

1. rotas opostas de emoção e aspiração;
2. pódio que se transforma no novo piso;
3. sacola genérica de delivery em composição antes/depois;
4. trajetórias convergentes de renda e expectativa;
5. guarda-chuva de segurança sobre necessidades concretas.

S016–S020 sustentam a nuance com evidência e abrem o mecanismo de comparação:

1. travessia da pressão financeira para uma zona segura;
2. página científica abstrata com lupa e curva original;
3. cinco respostas individuais em níveis diferentes;
4. placa que nega um número mágico universal;
5. elevadores paralelos para renda e nova referência social.

S021–S025 desenvolvem a comparação social e a posição relativa:

1. grupo profissional equivalente antes da promoção;
2. novo grupo cercado por sinais moderados de padrão mais alto;
3. repetição dos elevadores como payoff sincronizado;
4. escada de posição relativa com foco nos degraus superiores;
5. close do protagonista com atenção seletiva voltada para cima.

S026–S030 fecham a comparação e abrem o exemplo concreto da Ana:

1. réguas de renda e referência que se afastam;
2. envelope abstrato com informação sobre pares e ressalva de efeito pequeno;
3. redistribuição parcial do orçamento para bens duráveis;
4. feed genérico que atualiza a régua mental;
5. contracheque-base em quatro blocos e aumento em um quinto bloco.

S031–S035 quantificam como o aumento se transforma em compromissos:

1. cinco melhorias cotidianas legítimas ao redor da Ana;
2. barra proporcional com despesas de 350, 180, 170, 120 e 130;
3. destaque dos R$ 50 restantes em um total de R$ 1.000;
4. ficha explicitamente fictícia e didática;
5. contraste entre novidade que desaparece e cobrança recorrente.

S036–S040 fecham o mecanismo e sintetizam o modelo de “suficiente”:

1. cobranças recorrentes avançam ao primeiro plano;
2. três engrenagens representam adaptação, comparação e compromissos;
3. fluxo de conquista para normal e aperto;
4. triângulo entre renda, contas e régua do normal;
5. intervalo de decisão antes da primeira nova despesa fixa.

S041–S045 transformam a síntese em escolha e retomam a abertura:

1. balança entre conforto escolhido e upgrades automáticos;
2. três destinos visuais para o dinheiro novo, sem porcentagens ou recomendação;
3. contracheque grande com uma pequena área de liberdade após as contas;
4. callback do celular da abertura conectado aos três mecanismos;
5. calendário abstrato em que pequenos upgrades se fixam como compromissos.

O protagonista agora é um rig. Cabeça, torso, braço esquerdo, braço direito, perna esquerda e perna direita recebem IDs separados em cada cena.

Gerar sem substituir arquivos existentes:

```powershell
python scripts/gerar_cenas_svg.py CO-001
```

Atualizar explicitamente depois de uma mudança aprovada no código ou estilo:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --atualizar
```

Escolher cenas do protótipo:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --cenas S001,S003,S005
```

Gerar o segundo bloco:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --cenas S006,S007,S008,S009,S010
```

Gerar o terceiro bloco:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --cenas S011,S012,S013,S014,S015
```

Gerar o quarto bloco:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --cenas S016,S017,S018,S019,S020
```

Gerar o quinto bloco:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --cenas S021,S022,S023,S024,S025
```

Gerar o sexto bloco:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --cenas S026,S027,S028,S029,S030
```

Gerar o sétimo bloco:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --cenas S031,S032,S033,S034,S035
```

Gerar o oitavo bloco:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --cenas S036,S037,S038,S039,S040
```

Gerar o nono bloco:

```powershell
python scripts/gerar_cenas_svg.py CO-001 --cenas S041,S042,S043,S044,S045
```

Renderizar previews locais para revisão:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/renderizar_svg_preview.ps1 -Episode CO-001 -Files s006,s007,s008,s009,s010,review_s006_s010
```

Para o terceiro bloco, troque a lista por `s011,s012,s013,s014,s015,review_s011_s015`.

Para o quarto bloco, use `s016,s017,s018,s019,s020,review_s016_s020`.

Para o quinto bloco, use `s021,s022,s023,s024,s025,review_s021_s025`.

Para o sexto bloco, use `s026,s027,s028,s029,s030,review_s026_s030`.

Para o sétimo bloco, use `s031,s032,s033,s034,s035,review_s031_s035`.

Para o oitavo bloco, use `s036,s037,s038,s039,s040,review_s036_s040`.

Para o nono bloco, use `s041,s042,s043,s044,s045,review_s041_s045`.

O script lê `04_ROTEIRO_VISUAL.csv`, preserva `motion`, `visual` e `asset_id` nos metadados e gera SVG 1920x1080. Arquivos existentes não são alterados sem `--atualizar`.

## Critérios para aprovar o V3

- leitura da ideia em menos de dois segundos;
- personagem reconhecível quando estiver presente, sem depender do texto;
- fundo e objetos não competem com a ação;
- expressão funciona em tela pequena;
- escala e hierarquia parecem editoriais, não tímidas;
- cada cena tem uma composição própria sem quebrar o universo visual.

Antes de aprovar qualquer cena, aplicar também o checklist de acabamento:

- a metáfora deve ser compreensível mesmo sem a narração;
- cada seta, legenda e objeto precisa ter uma função inequívoca;
- texto, personagem e objetos não podem colidir;
- expressão e gesto devem reforçar exatamente o mesmo beat narrativo;
- manter uma ideia visual dominante e, no máximo, um elemento de contexto;
- retirar o personagem quando ele apenas repetir a informação;
- revisar em tamanho cheio e reduzido antes de liberar o próximo bloco.

## Etapa de animação

A animação será uma etapa separada. O manifesto cumulativo e `vector_scenes.json` já preservam alvos, tempos e ações para alimentar:

- zoom e pan de câmera;
- entrada e saída de grupos;
- rotação curta de cabeça e braços;
- troca entre duas poses;
- revelação de gráficos e linhas;
- deslocamento de objetos.

O bloco final S046–S048 continua bloqueado até a migração e revisão visual dos blocos anteriores no V3. Esse ciclo curto impede que um erro de linguagem visual seja replicado pelo episódio inteiro.
