#!/usr/bin/env python3
"""Gera a biblioteca editorial V1 e o prototipo estatico S001-S006.

Este script e deliberadamente isolado do pipeline de producao. Ele cria somente
arquivos novos em assets/, config/, docs/ e tests/visual_library/.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PALETTE = {
    "black": "#111111",
    "lime": "#C4E538",
    "amber": "#E8A33D",
    "off_white": "#F4F3EF",
    "gray": "#D9D9D4",
}
VIEW_BOX = "0 0 1200 700"


GROUPS = {
    "counters": [
        ("money-counter-v1", "DATA_HERO", "Contador monetario de leitura imediata.", ["renda", "saldo", "valor acumulado"], "lime", True),
        ("delta-counter-v1", "DATA_HERO", "Diferenca numerica entre dois estados.", ["aumento", "queda", "variacao absoluta"], "amber", True),
        ("before-after-number-v1", "COMPARISON", "Dois numeros ligados por uma mudanca direcional.", ["antes e depois", "mudanca de baseline"], "lime", True),
        ("percentage-counter-v1", "DATA_HERO", "Proporcao circular com centro editorial livre.", ["percentual", "participacao", "taxa"], "lime", False),
        ("remaining-balance-v1", "DATA_HERO", "Saldo remanescente depois de deducoes.", ["folga restante", "dinheiro disponivel"], "amber", True),
    ],
    "bars": [
        ("surplus-bar-v1", "PROGRESS", "Barra de folga financeira com reserva visivel.", ["folga", "reserva", "margem"], "lime", True),
        ("income-expense-bar-v1", "COMPARISON", "Relacao proporcional entre renda e despesa.", ["renda versus gasto", "comprometimento"], "lime", True),
        ("depletion-bar-v1", "TRANSFORMATION", "Barra que evidencia consumo progressivo do total.", ["esgotamento", "perda progressiva"], "amber", True),
    ],
    "meters": [
        ("threshold-meter-v1", "PROGRESS", "Medidor linear com limiar explicito.", ["limite", "ponto critico", "meta"], "amber", True),
        ("two-state-meter-v1", "COMPARISON", "Medidor para contraste de dois estados.", ["estado inicial e final", "mudanca de nivel"], "lime", True),
    ],
    "timelines": [
        ("linear-time-progress-v1", "TIMELINE", "Linha temporal horizontal de progressao limpa.", ["passagem do tempo", "etapas"], "lime", False),
        ("month-progression-v1", "TIMELINE", "Progressao mensal com ritmo acumulativo.", ["meses", "adaptacao gradual"], "amber", False),
        ("accumulation-timeline-v1", "TIMELINE", "Linha temporal que acumula volume em cada marco.", ["acumulacao", "crescimento recorrente"], "lime", False),
        ("before-after-timeline-v1", "TIMELINE", "Linha temporal com ruptura central entre estados.", ["antes e depois no tempo", "virada"], "amber", True),
    ],
    "comparisons": [
        ("split-comparison-v1", "COMPARISON", "Campo bipartido para contraste direto.", ["oposicao", "duas escolhas"], "lime", True),
        ("baseline-vs-current-v1", "COMPARISON", "Baseline fixo comparado ao estado atual.", ["referencia", "desvio do normal"], "amber", True),
        ("gap-comparison-v1", "COMPARISON", "Intervalo entre duas magnitudes como protagonista.", ["lacuna", "distancia", "diferenca"], "amber", True),
        ("proportional-comparison-v1", "SCALE", "Comparacao pela area ocupada, sem eixos decorativos.", ["proporcao", "participacao relativa"], "lime", False),
    ],
    "stacks": [
        ("expense-stack-v1", "SCALE", "Pilha de despesas com peso cumulativo.", ["composicao de gastos", "pressao total"], "amber", True),
        ("fixed-cost-stack-v1", "SCALE", "Pilha de custos fixos que reduz a area livre.", ["custos fixos", "rigidez orcamentaria"], "amber", True),
        ("lifestyle-stack-v1", "TRANSFORMATION", "Camadas de estilo de vida que crescem juntas.", ["inflacao de estilo de vida", "novas obrigacoes"], "lime", True),
        ("accumulation-stack-v1", "PROGRESS", "Pilha crescente para ganhos ou compromissos acumulados.", ["acumulacao", "recorrencia"], "lime", False),
    ],
    "flows": [
        ("cause-effect-flow-v1", "SYSTEM_MAP", "Causa e efeito conectados por direcao dominante.", ["causalidade editorial", "consequencia"], "amber", True),
        ("three-variable-flow-v1", "SYSTEM_MAP", "Tres variaveis interdependentes em um unico sistema.", ["variaveis que se movem juntas", "mecanismo triplo"], "amber", True),
        ("feedback-loop-v1", "SYSTEM_MAP", "Loop de retroalimentacao sem iconografia literal.", ["ciclo", "reforco comportamental"], "lime", True),
        ("money-flow-v1", "SYSTEM_MAP", "Fluxo de entrada, distribuicao e saida de dinheiro.", ["fluxo financeiro", "destino da renda"], "lime", True),
        ("progressive-pressure-v1", "TRANSFORMATION", "Pressao crescente ao longo de uma direcao unica.", ["pressao gradual", "compressao"], "amber", True),
    ],
    "scales": [
        ("status-ladder-v1", "SCALE", "Escada de referencia social e status.", ["comparacao social", "subida de referencia"], "amber", True),
        ("moving-baseline-v1", "TRANSFORMATION", "Linha de base que se desloca e redefine o normal.", ["baseline movel", "adaptacao"], "lime", True),
        ("reference-shift-v1", "TRANSFORMATION", "Mudanca espacial do ponto de referencia.", ["novo normal", "ancoragem"], "amber", True),
        ("scale-contrast-v1", "SCALE", "Contraste editorial entre magnitudes extremas.", ["grande versus pequeno", "assimetria"], "lime", True),
    ],
    "typography": [
        ("giant-number-v1", "EDITORIAL_TYPE", "Estrutura para numero gigante como protagonista.", ["numero de impacto", "dado principal"], "lime", False),
        ("keyword-emphasis-v1", "EDITORIAL_TYPE", "Estrutura de enfase para uma palavra decisiva.", ["palavra-chave", "virada verbal"], "amber", False),
        ("statement-stack-v1", "EDITORIAL_TYPE", "Ritmo vertical para frase curta em camadas.", ["frase-sintese", "conclusao"], "lime", False),
        ("numeric-punchline-v1", "EDITORIAL_TYPE", "Numero final com marca de conclusao visual.", ["payoff numerico", "resultado final"], "amber", False),
    ],
    "metaphor": [
        ("shrinking-surplus-v1", "TRANSFORMATION", "Espaco livre comprimido por despesas crescentes.", ["folga financeira desaparecendo", "dinheiro restante diminuindo"], "amber", True),
        ("lifestyle-creep-v1", "TRANSFORMATION", "Degraus de consumo que avancam sobre a renda.", ["inflacao de estilo de vida", "padrao de vida crescente"], "lime", True),
        ("fixed-cost-pressure-v1", "TRANSFORMATION", "Bloco fixo pressiona e reduz a margem flexivel.", ["custos fixos", "orcamento comprimido"], "amber", True),
        ("salary-gap-v1", "COMPARISON", "Distancia salarial tornada visivel como vazio central.", ["diferenca salarial", "distancia de renda"], "lime", True),
        ("reference-point-shift-v1", "TRANSFORMATION", "O marcador de normalidade muda de posicao.", ["adaptacao hedonica", "novo normal"], "lime", True),
        ("expense-leak-v1", "TRANSFORMATION", "Pequenas saidas drenam um volume maior.", ["vazamento de gastos", "microdespesas"], "amber", True),
    ],
}

METAPHOR_DIR = {
    "shrinking-surplus-v1": "shrinking-surplus",
    "lifestyle-creep-v1": "lifestyle-creep",
    "fixed-cost-pressure-v1": "fixed-cost-pressure",
    "salary-gap-v1": "salary-gap",
    "reference-point-shift-v1": "reference-shift",
    "expense-leak-v1": "expense-pressure",
}

REQUIRED_DIRS = [
    "assets/components/counters", "assets/components/bars", "assets/components/timelines",
    "assets/components/comparisons", "assets/components/stacks", "assets/components/meters",
    "assets/components/flows", "assets/components/scales", "assets/components/typography",
    "assets/components/data", "assets/metaphors/lifestyle-creep", "assets/metaphors/expense-pressure",
    "assets/metaphors/shrinking-surplus", "assets/metaphors/salary-gap",
    "assets/metaphors/status-ladder", "assets/metaphors/reference-shift",
    "assets/metaphors/fixed-cost-pressure", "assets/metaphors/money-flow",
    "assets/motion/reveal", "assets/motion/counter", "assets/motion/fill", "assets/motion/push",
    "assets/motion/collapse", "assets/motion/split", "assets/motion/carry-over",
    "tests/visual_library/s001_s006/previews",
]


def component_path(category: str, asset_id: str) -> Path:
    if category == "metaphor":
        return ROOT / "assets" / "metaphors" / METAPHOR_DIR[asset_id] / f"{asset_id}.svg"
    return ROOT / "assets" / "components" / category / f"{asset_id}.svg"


def symbol_svg(asset_id: str, body: str) -> str:
    # Espessuras maiores devem ser formas preenchidas, nunca contornos. Os
    # renderers usam alguns strokes largos como atalho de desenho; na fonte
    # oficial eles sao normalizados para a escala 6/4/3 exigida pelo V3.
    body = re.sub(
        r'stroke-width="([0-9]+)"',
        lambda match: match.group(0) if match.group(1) in {"3", "4", "6"} else 'stroke-width="6"',
        body,
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VIEW_BOX}">
  <defs>
    <symbol id="vl-{asset_id}" viewBox="{VIEW_BOX}" preserveAspectRatio="xMidYMid meet">
      <g fill="none" stroke="{PALETTE['black']}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">
{body}
      </g>
    </symbol>
  </defs>
</svg>
'''


def counter_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    variants = [
        f'''        <path d="M100 540 H1100"/><path d="M140 190 H760" stroke="{a}" stroke-width="18"/>
        <path d="M820 500 L1040 280 M1040 280 L960 292 M1040 280 L1028 360" stroke="{a}" stroke-width="18"/>
        <path d="M160 460 H540 M660 460 H1040" stroke-width="4"/><circle cx="600" cy="460" r="24" fill="{a}" stroke="none"/>''',
        f'''        <path d="M150 520 V250 M1050 520 V130" stroke-width="12"/>
        <path d="M170 500 H500 M700 500 H1030" stroke="{a}" stroke-width="32"/>
        <path d="M560 350 H840 M800 310 L840 350 L800 390" stroke="{a}" stroke-width="12"/>
        <path d="M205 210 H995" stroke-dasharray="18 22" stroke-width="4"/>''',
        f'''        <path d="M100 560 H1100"/><path d="M170 460 H470 M730 250 H1030" stroke-width="18"/>
        <path d="M505 425 L695 285" stroke="{a}" stroke-width="22"/>
        <path d="M635 276 L695 285 L684 345" stroke="{a}" stroke-width="22"/>
        <circle cx="320" cy="460" r="34" fill="{PALETTE['gray']}" stroke="none"/><circle cx="880" cy="250" r="34" fill="{a}" stroke="none"/>''',
        f'''        <circle cx="600" cy="350" r="238" stroke="{PALETTE['gray']}" stroke-width="42"/>
        <path d="M600 112 A238 238 0 1 1 374 424" stroke="{a}" stroke-width="42"/>
        <path d="M600 74 V150 M1126 350 H1050" stroke-width="4"/>''',
        f'''        <path d="M120 170 H1080 M120 540 H1080"/>
        <path d="M160 250 H1040" stroke="{PALETTE['gray']}" stroke-width="54"/>
        <path d="M160 250 H790" stroke="{a}" stroke-width="54"/>
        <path d="M160 390 H680" stroke="{PALETTE['gray']}" stroke-width="36"/>
        <path d="M160 480 H460" stroke="{PALETTE['black']}" stroke-width="36"/>
        <path d="M790 210 V290" stroke-width="4"/>''',
    ]
    return variants[index]


def bar_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    variants = [
        f'''        <rect x="90" y="250" width="1020" height="200" rx="28" fill="{PALETTE['gray']}" stroke="none"/>
        <path d="M118 350 H760" stroke="{a}" stroke-width="144"/>
        <path d="M780 224 V476" stroke-width="6"/><circle cx="780" cy="350" r="22" fill="{PALETTE['black']}" stroke="none"/>''',
        f'''        <path d="M120 230 H1050" stroke="{a}" stroke-width="96"/>
        <path d="M120 470 H820" stroke="{PALETTE['black']}" stroke-width="96"/>
        <path d="M1050 175 V285 M820 415 V525"/>
        <path d="M120 130 V570" stroke="{PALETTE['gray']}" stroke-width="4"/>''',
        f'''        <rect x="110" y="280" width="980" height="150" rx="28" fill="{PALETTE['gray']}" stroke="none"/>
        <path d="M140 355 H930" stroke="{a}" stroke-width="100"/>
        <path d="M930 280 V430" stroke-width="8"/>
        <path d="M980 210 V510 M1040 240 V480" stroke="{PALETTE['black']}" stroke-width="12"/>''',
    ]
    return variants[index]


def meter_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    if index == 0:
        return f'''        <path d="M110 390 H1090" stroke="{PALETTE['gray']}" stroke-width="76"/>
        <path d="M110 390 H800" stroke="{a}" stroke-width="76"/>
        <path d="M820 205 V555" stroke-width="8"/><path d="M780 205 H860" stroke-width="8"/>
        <circle cx="800" cy="390" r="30" fill="{a}" stroke="none"/>'''
    return f'''        <path d="M120 270 H1080" stroke="{PALETTE['gray']}" stroke-width="48"/>
        <path d="M120 430 H1080" stroke="{PALETTE['gray']}" stroke-width="48"/>
        <path d="M120 270 H520 M120 430 H930" stroke="{a}" stroke-width="48"/>
        <circle cx="520" cy="270" r="34" fill="{PALETTE['black']}" stroke="none"/>
        <circle cx="930" cy="430" r="34" fill="{PALETTE['black']}" stroke="none"/>'''


def timeline_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    xs = [140, 370, 600, 830, 1060]
    nodes = "".join(f'<circle cx="{x}" cy="350" r="{22 + i * (index + 1) * 3}" fill="{a if i <= index + 1 else PALETTE["off_white"]}"/>' for i, x in enumerate(xs))
    stems = "".join(f'<path d="M{x} 300 V{210 - (i % 2) * 45}" stroke-width="4"/>' for i, x in enumerate(xs))
    if index == 3:
        return f'''        <path d="M100 350 H1100" stroke="{PALETTE['gray']}" stroke-width="10"/>
        <path d="M100 350 H560" stroke="{a}" stroke-width="18"/><path d="M640 350 H1100" stroke="{PALETTE['black']}" stroke-width="18"/>
        <path d="M600 120 V580" stroke-dasharray="18 18"/>
        <circle cx="300" cy="350" r="34" fill="{a}"/><circle cx="900" cy="350" r="60" fill="{a}"/>'''
    return f'''        <path d="M100 350 H1100" stroke="{PALETTE['gray']}" stroke-width="10"/>
        <path d="M100 350 H{xs[min(index + 2, 4)]}" stroke="{a}" stroke-width="18"/>
        {nodes}{stems}
        <path d="M1040 315 L1100 350 L1040 385 Z" fill="{PALETTE['black']}" stroke="none"/>'''


def comparison_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    variants = [
        f'''        <path d="M600 90 V610" stroke-width="4"/>
        <path d="M120 500 H510" stroke="{PALETTE['gray']}" stroke-width="96"/>
        <path d="M690 250 H1080" stroke="{a}" stroke-width="96"/>
        <circle cx="315" cy="500" r="28" fill="{PALETTE['black']}" stroke="none"/><circle cx="885" cy="250" r="28" fill="{PALETTE['black']}" stroke="none"/>''',
        f'''        <path d="M100 470 H1100" stroke="{PALETTE['black']}" stroke-width="8"/>
        <path d="M100 330 H1100" stroke="{PALETTE['gray']}" stroke-width="8" stroke-dasharray="20 20"/>
        <path d="M260 470 V330 M940 470 V160" stroke="{a}" stroke-width="48"/>
        <circle cx="260" cy="330" r="25" fill="{a}" stroke="none"/><circle cx="940" cy="160" r="25" fill="{a}" stroke="none"/>''',
        f'''        <path d="M120 350 H410 M790 350 H1080" stroke-width="30"/>
        <path d="M420 280 V420 M780 280 V420"/>
        <path d="M450 350 H750" stroke="{a}" stroke-width="12"/>
        <path d="M480 315 L450 350 L480 385 M720 315 L750 350 L720 385" stroke="{a}" stroke-width="12"/>''',
        f'''        <circle cx="340" cy="360" r="150" fill="{PALETTE['gray']}" stroke="none"/>
        <circle cx="850" cy="330" r="250" fill="{a}" stroke="none"/>
        <path d="M340 585 H850" stroke-width="6"/><path d="M340 555 V615 M850 555 V615"/>''',
    ]
    return variants[index]


def stack_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    widths = ([820, 680, 540, 400], [900, 900, 900, 900], [480, 620, 760, 900], [360, 520, 700, 880])[index]
    ys = [500, 390, 280, 170]
    parts = []
    for i, (w, y) in enumerate(zip(widths, ys)):
        x = 600 - w / 2
        fill = a if i == (3 if index in (2, 3) else 0) else PALETTE["gray"]
        parts.append(f'<rect x="{x:g}" y="{y}" width="{w}" height="82" rx="20" fill="{fill}" stroke="none"/>')
    return "        " + "\n        ".join(parts) + f'''\n        <path d="M90 620 H1110"/><path d="M1040 550 L1090 600 L1040 650" stroke="{a}" stroke-width="12"/>'''


def flow_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    if index == 0:
        return f'''        <circle cx="260" cy="350" r="140" fill="{a}" stroke="none"/>
        <circle cx="940" cy="350" r="190" fill="{PALETTE['gray']}" stroke="none"/>
        <path d="M420 350 H710" stroke-width="24"/><path d="M680 285 L760 350 L680 415 Z" fill="{PALETTE['black']}" stroke="none"/>'''
    if index == 1:
        return f'''        <circle cx="220" cy="350" r="105" fill="{PALETTE['gray']}" stroke="none"/>
        <circle cx="600" cy="190" r="135" fill="{a}" stroke="none"/>
        <circle cx="980" cy="350" r="165" fill="{PALETTE['gray']}" stroke="none"/>
        <path d="M330 310 L455 250 M745 250 L825 310 M330 405 L825 405" stroke-width="18"/>
        <path d="M795 370 L845 405 L795 440 Z" fill="{PALETTE['black']}" stroke="none"/>'''
    if index == 2:
        return f'''        <path d="M350 190 C750 20 1080 280 900 530 C710 720 270 650 150 390 C80 220 180 120 350 190" stroke="{a}" stroke-width="24"/>
        <path d="M275 160 L355 188 L300 250 Z" fill="{a}" stroke="none"/>
        <circle cx="310" cy="420" r="80" fill="{PALETTE['gray']}" stroke="none"/><circle cx="850" cy="300" r="110" fill="{PALETTE['black']}" stroke="none"/>'''
    if index == 3:
        return f'''        <path d="M100 350 H1100" stroke="{PALETTE['gray']}" stroke-width="80"/>
        <path d="M100 350 H800" stroke="{a}" stroke-width="80"/>
        <path d="M350 220 V480 M650 220 V480 M930 220 V480"/>
        <path d="M1040 290 L1120 350 L1040 410 Z" fill="{PALETTE['black']}" stroke="none"/>'''
    return f'''        <path d="M130 550 L320 420 L520 360 L720 250 L1030 120" stroke="{a}" stroke-width="44"/>
        <path d="M130 620 H1080"/><path d="M300 190 V500 M590 140 V390 M880 90 V280" stroke="{PALETTE['gray']}" stroke-width="28"/>
        <path d="M970 105 L1040 115 L1010 180 Z" fill="{a}" stroke="none"/>'''


def scale_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    variants = [
        f'''        <path d="M130 590 H1070" stroke-width="10"/>
        <path d="M190 590 V500 H380 V405 H570 V310 H760 V215 H950 V120" stroke="{a}" stroke-width="44"/>
        <circle cx="190" cy="500" r="24" fill="{PALETTE['black']}" stroke="none"/><circle cx="950" cy="120" r="38" fill="{PALETTE['black']}" stroke="none"/>''',
        f'''        <path d="M110 470 H1090" stroke="{PALETTE['gray']}" stroke-width="10"/>
        <path d="M110 470 C400 470 450 470 600 350 S900 220 1090 220" stroke="{a}" stroke-width="24"/>
        <path d="M600 130 V570" stroke-dasharray="20 18"/><circle cx="600" cy="350" r="28" fill="{a}" stroke="none"/>''',
        f'''        <path d="M150 500 H500 M700 240 H1050" stroke-width="20"/>
        <path d="M500 500 C620 500 580 240 700 240" stroke="{a}" stroke-width="28"/>
        <circle cx="500" cy="500" r="32" fill="{PALETTE['gray']}"/><circle cx="700" cy="240" r="32" fill="{a}"/>''',
        f'''        <circle cx="270" cy="420" r="95" fill="{PALETTE['gray']}" stroke="none"/>
        <circle cx="850" cy="320" r="270" fill="{a}" stroke="none"/>
        <path d="M270 570 H850"/><path d="M270 540 V600 M850 540 V600"/>''',
    ]
    return variants[index]


def typography_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    variants = [
        f'''        <path d="M150 120 H1050 M150 580 H1050" stroke-width="4"/>
        <path d="M190 490 H720" stroke="{a}" stroke-width="42"/>
        <path d="M760 180 V520" stroke="{PALETTE['gray']}" stroke-width="8"/>''',
        f'''        <path d="M130 220 H1070 M130 480 H820" stroke="{PALETTE['gray']}" stroke-width="34"/>
        <path d="M390 220 H820" stroke="{a}" stroke-width="58"/>
        <path d="M360 145 V295 M850 145 V295"/>''',
        f'''        <path d="M140 180 H920" stroke="{PALETTE['black']}" stroke-width="54"/>
        <path d="M140 350 H1080" stroke="{a}" stroke-width="54"/>
        <path d="M140 520 H740" stroke="{PALETTE['black']}" stroke-width="54"/>
        <path d="M110 110 V590" stroke-width="6"/>''',
        f'''        <path d="M140 520 H1060" stroke-width="8"/>
        <path d="M170 420 H830" stroke="{PALETTE['gray']}" stroke-width="40"/>
        <path d="M760 170 L1040 450" stroke="{a}" stroke-width="32"/>
        <path d="M980 450 H1040 V390" stroke="{a}" stroke-width="20"/>''',
    ]
    return variants[index]


def metaphor_body(index: int, accent: str) -> str:
    a = PALETTE[accent]
    variants = [
        f'''        <path d="M100 180 H1100 V540 H100 Z" stroke-width="8"/>
        <path d="M120 210 H1080 V360 H120 Z" fill="{PALETTE['gray']}" stroke="none"/>
        <path d="M120 390 H470 V510 H120 Z" fill="{a}" stroke="none"/>
        <path d="M760 150 V570" stroke-width="18"/><path d="M700 500 L760 560 L820 500" stroke-width="18"/>''',
        f'''        <path d="M110 590 H1090"/><path d="M160 590 V500 H360 V400 H560 V300 H760 V200 H960 V110" stroke="{a}" stroke-width="58"/>
        <path d="M230 470 L400 370 L600 270 L800 170" stroke-width="18"/>
        <path d="M750 135 L820 160 L775 220 Z" fill="{PALETTE['black']}" stroke="none"/>''',
        f'''        <rect x="110" y="160" width="980" height="390" rx="26" fill="{PALETTE['gray']}" stroke="none"/>
        <rect x="110" y="160" width="680" height="390" rx="26" fill="{PALETTE['black']}" stroke="none"/>
        <rect x="820" y="160" width="270" height="390" rx="26" fill="{a}" stroke="none"/>
        <path d="M790 110 V600" stroke-width="12"/><path d="M740 150 L790 100 L840 150" stroke-width="12"/>''',
        f'''        <path d="M140 510 V300 M1060 510 V120" stroke-width="64"/>
        <path d="M190 510 H1010" stroke="{a}" stroke-width="16" stroke-dasharray="24 20"/>
        <path d="M190 250 H1010" stroke="{PALETTE['gray']}" stroke-width="8"/>
        <path d="M230 420 H970" stroke-width="4"/>''',
        f'''        <path d="M100 500 H520 M680 230 H1100" stroke="{PALETTE['gray']}" stroke-width="18"/>
        <path d="M520 500 C650 500 550 230 680 230" stroke="{a}" stroke-width="38"/>
        <circle cx="520" cy="500" r="38" fill="{PALETTE['black']}" stroke="none"/><circle cx="680" cy="230" r="38" fill="{a}" stroke="none"/>
        <path d="M600 120 V590" stroke-dasharray="18 18"/>''',
        f'''        <path d="M120 170 H920 V530 H120 Z" stroke-width="12"/>
        <path d="M170 230 H870 V470 H170 Z" fill="{a}" stroke="none"/>
        <path d="M920 260 C1020 260 1060 300 1060 370 C1060 440 1010 480 930 480" stroke="{a}" stroke-width="34"/>
        <circle cx="1040" cy="520" r="24" fill="{a}" stroke="none"/><circle cx="980" cy="600" r="16" fill="{a}" stroke="none"/>''',
    ]
    return variants[index]


RENDERERS = {
    "counters": counter_body,
    "bars": bar_body,
    "meters": meter_body,
    "timelines": timeline_body,
    "comparisons": comparison_body,
    "stacks": stack_body,
    "flows": flow_body,
    "scales": scale_body,
    "typography": typography_body,
    "metaphor": metaphor_body,
}


def build_assets() -> list[dict]:
    catalog = []
    for directory in REQUIRED_DIRS:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)

    for category, entries in GROUPS.items():
        renderer = RENDERERS[category]
        for index, (asset_id, visual_type, description, semantic_use, accent, supports_character) in enumerate(entries):
            source_path = component_path(category, asset_id)
            source_path.parent.mkdir(parents=True, exist_ok=True)
            svg = symbol_svg(asset_id, renderer(index, accent))
            source_path.write_text(svg, encoding="utf-8", newline="\n")
            rel = source_path.relative_to(ROOT).as_posix()
            catalog.append({
                "id": asset_id,
                "category": category,
                "visual_type": visual_type,
                "description": description,
                "semantic_use": semantic_use,
                "allowed_accents": [accent],
                "supports_character": supports_character,
                "supports_animation": True,
                "preferred_size": "dominant-55-75-percent-safe-area",
                "dominance_allowed": True,
                "source": rel,
                "version": 1,
                "symbol_id": f"vl-{asset_id}",
                "view_box": VIEW_BOX,
                "sha256": hashlib.sha256(svg.encode("utf-8")).hexdigest(),
            })
    return catalog


MOTION_RECIPES = [
    ("reveal-v1", "reveal", ["DATA_HERO", "EDITORIAL_TYPE", "TIMELINE"], "250-400"),
    ("counter-v1", "counter", ["DATA_HERO"], "500-900"),
    ("fill-v1", "fill", ["PROGRESS", "TIMELINE"], "500-900"),
    ("push-v1", "push", ["TRANSFORMATION", "SYSTEM_MAP"], "250-450"),
    ("collapse-v1", "collapse", ["TRANSFORMATION", "SCALE"], "500-900"),
    ("split-v1", "split", ["COMPARISON"], "250-450"),
    ("carry-over-v1", "carry-over", ["TIMELINE", "SYSTEM_MAP", "TRANSFORMATION"], "250-450"),
]


def write_catalog(assets: list[dict]) -> None:
    recipes = []
    for recipe_id, folder, types, duration in MOTION_RECIPES:
        recipe = {
            "id": recipe_id,
            "category": "motion",
            "description": f"Receita declarativa de movimento {folder}; nao integrada ao pipeline.",
            "eligible_visual_types": types,
            "duration_reference_ms": duration,
            "audio_anchor_required": True,
            "dominant_motion_limit": 1,
            "version": 1,
            "source": f"assets/motion/{folder}/{recipe_id}.json",
        }
        path = ROOT / recipe["source"]
        path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        recipes.append(recipe)

    payload = {
        "library": "CAPITAL_OCULTO_VISUAL_LIBRARY_V1",
        "status": "EXPERIMENTAL_STATIC_PROTOTYPE",
        "integrated_with_production": False,
        "canvas": {"width": 1920, "height": 1080, "safe_area": 64, "text_safe_area": 96},
        "palette": PALETTE,
        "visual_types": [
            "DATA_HERO", "SYSTEM_MAP", "TRANSFORMATION", "SCALE", "EDITORIAL_TYPE",
            "TIMELINE", "COMPARISON", "PROGRESS", "CHARACTER_INTERACTION",
        ],
        "selection_order": [
            "specific_metaphor", "editorial_component", "data_or_number",
            "transformation", "character_if_meaningful", "support_icon",
        ],
        "constraints": {
            "support_icon_area_max_ratio": 0.10,
            "dominant_area_ratio": [0.55, 0.75],
            "max_semantic_accents_per_scene": 1,
            "character_source": "assets/characters/capital_oculto_character_rig_v4.svg",
            "character_functions": ["REACTION", "ACTION", "SCALE", "CAUSE", "CONTINUITY", "CONTRAST"],
            "card_requires_semantic_function": True,
        },
        "assets": assets,
        "motion_recipes": recipes,
    }
    target = ROOT / "config" / "visual_library.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def extract_symbol(asset_id: str, assets_by_id: dict[str, dict]) -> str:
    text = (ROOT / assets_by_id[asset_id]["source"]).read_text(encoding="utf-8")
    match = re.search(r"    (<symbol\b[\s\S]*?</symbol>)", text)
    if not match:
        raise RuntimeError(f"Symbol ausente em {asset_id}")
    return match.group(1)


def extract_rig_defs() -> str:
    text = (ROOT / "assets/characters/capital_oculto_character_rig_v4.svg").read_text(encoding="utf-8")
    match = re.search(r"<defs>([\s\S]*?)</defs>", text)
    if not match:
        raise RuntimeError("Defs do rig V4 ausente")
    return match.group(1).strip()


FONT = "font-family=\"Arial, sans-serif\""


def scene_svg(scene_id: str, accent: str, defs: str, content: str, dominant_id: str, ratio: float) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1920 1080">
  <metadata>{{"scene_id":"{scene_id}","library":"V1","dominant_asset":"{dominant_id}","dominant_area_ratio":{ratio:.3f},"static_prototype":true}}</metadata>
  <defs>
{defs}
  </defs>
  <rect width="1920" height="1080" fill="{PALETTE['off_white']}"/>
  <g id="scene-{scene_id}" {FONT} fill="{PALETTE['black']}">
{content}
  </g>
</svg>
'''


def build_scenes(assets: list[dict]) -> list[dict]:
    by_id = {asset["id"]: asset for asset in assets}
    out = ROOT / "tests" / "visual_library" / "s001_s006"
    out.mkdir(parents=True, exist_ok=True)
    rig_defs = extract_rig_defs()

    scenes = [
        {
            "scene_id": "S001", "asset": "before-after-number-v1", "visual_type": "DATA_HERO",
            "layout": "E_DATA_DELTA", "accent": "lime", "character": False, "character_function": None,
            "ratio": 0.684, "use": (210, 220, 1500, 700),
            "justification": "O aumento e a diferenca numerica ocupam o quadro; nenhum objeto literal compete com o dado.",
            "overlay": f'''    <text x="96" y="130" font-size="28" font-weight="800" letter-spacing="2">S001 · RENDA</text>
    <use href="#vl-before-after-number-v1" x="210" y="220" width="1500" height="700" data-role="dominant"/>
    <text x="250" y="480" font-size="44" font-weight="700">ANTES</text>
    <text x="250" y="650" font-size="132" font-weight="900" letter-spacing="-7">R$ 3.200</text>
    <text x="1090" y="360" font-size="44" font-weight="700">AGORA</text>
    <text x="1080" y="530" font-size="132" font-weight="900" letter-spacing="-7">R$ 5.000</text>
    <text x="1270" y="875" font-size="58" font-weight="900" fill="{PALETTE['lime']}">+ R$ 1.800</text>''',
        },
        {
            "scene_id": "S002", "asset": "month-progression-v1", "visual_type": "TIMELINE",
            "layout": "F_MONTHLY_PROGRESS", "accent": "amber", "character": False, "character_function": None,
            "ratio": 0.699, "use": (135, 230, 1650, 650),
            "justification": "O tempo aparece como progressao continua e acumulativa, sem calendario ou card protagonista.",
            "overlay": f'''    <text x="96" y="150" font-size="86" font-weight="900" letter-spacing="-4">E ENTÃO O TEMPO PASSA.</text>
    <use href="#vl-month-progression-v1" x="135" y="230" width="1650" height="650" data-role="dominant"/>
    <text x="260" y="760" font-size="28" font-weight="800">MÊS 1</text><text x="620" y="760" font-size="28" font-weight="800">MÊS 3</text>
    <text x="990" y="760" font-size="28" font-weight="800">MÊS 6</text><text x="1425" y="760" font-size="28" font-weight="800">MÊS 12</text>
    <text x="1110" y="945" font-size="48" font-weight="900" fill="{PALETTE['amber']}">O NOVO SALÁRIO JÁ PARECE NORMAL.</text>''',
        },
        {
            "scene_id": "S003", "asset": "shrinking-surplus-v1", "visual_type": "TRANSFORMATION",
            "layout": "A_METAPHOR_SCALE", "accent": "amber", "character": True, "character_function": "SCALE",
            "ratio": 0.593, "use": (80, 240, 1300, 700),
            "justification": "A folga encolhe por proporcao; o personagem existe apenas para dar escala humana ao valor final.",
            "overlay": f'''    <text x="96" y="150" font-size="74" font-weight="900" letter-spacing="-3">A FOLGA ENCOLHE.</text>
    <use href="#vl-shrinking-surplus-v1" x="80" y="240" width="1300" height="700" data-role="dominant"/>
    <text x="230" y="555" font-size="34" font-weight="800">RENDA</text><text x="250" y="805" font-size="34" font-weight="800">RESTOU</text>
    <text x="420" y="875" font-size="128" font-weight="900" letter-spacing="-6" fill="{PALETTE['amber']}">R$ 180</text>
    <use href="#char-base" x="1480" y="355" width="320" height="640"/>
    <path d="M1420 825 H1600" stroke="{PALETTE['black']}" stroke-width="6" stroke-linecap="round"/>
    <text x="1510" y="300" font-size="26" font-weight="800">ESCALA HUMANA</text>''',
        },
        {
            "scene_id": "S004", "asset": "three-variable-flow-v1", "visual_type": "SYSTEM_MAP",
            "layout": "B_SYSTEM_TRIAD", "accent": "amber", "character": False, "character_function": None,
            "ratio": 0.684, "use": (210, 230, 1500, 700),
            "justification": "As tres variaveis formam um unico mecanismo conectado; nao sao tres icones independentes.",
            "overlay": f'''    <text x="96" y="150" font-size="82" font-weight="900" letter-spacing="-4">TUDO SOBE JUNTO.</text>
    <use href="#vl-three-variable-flow-v1" x="210" y="230" width="1500" height="700" data-role="dominant"/>
    <text x="330" y="640" font-size="34" font-weight="900">CONFORTO</text>
    <text x="790" y="350" font-size="34" font-weight="900">COMPARAÇÃO</text>
    <text x="1305" y="640" font-size="34" font-weight="900">CUSTO FIXO</text>
    <text x="570" y="955" font-size="44" font-weight="800" fill="{PALETTE['amber']}">UM SISTEMA. NÃO TRÊS CULPADOS.</text>''',
        },
        {
            "scene_id": "S005", "asset": "fixed-cost-pressure-v1", "visual_type": "TRANSFORMATION",
            "layout": "B_PRESSURE_FIELD", "accent": "amber", "character": False, "character_function": None,
            "ratio": 0.665, "use": (210, 230, 1500, 680),
            "justification": "O mecanismo e a compressao da margem flexivel, nao a ilustracao literal de uma conta.",
            "overlay": f'''    <text x="96" y="145" font-size="30" font-weight="800" letter-spacing="2">S005 · PRESSÃO ESTRUTURAL</text>
    <use href="#vl-fixed-cost-pressure-v1" x="210" y="230" width="1500" height="680" data-role="dominant"/>
    <text x="350" y="590" font-size="82" font-weight="900" fill="{PALETTE['off_white']}">FIXO</text>
    <text x="1310" y="520" font-size="38" font-weight="900">FOLGA</text>
    <text x="1290" y="610" font-size="92" font-weight="900">14%</text>
    <text x="1070" y="950" font-size="48" font-weight="900" fill="{PALETTE['amber']}">MENOS ESPAÇO PARA ESCOLHER.</text>''',
        },
        {
            "scene_id": "S006", "asset": "reference-point-shift-v1", "visual_type": "TRANSFORMATION",
            "layout": "D_REFERENCE_SHIFT", "accent": "lime", "character": False, "character_function": None,
            "ratio": 0.684, "use": (210, 210, 1500, 700),
            "justification": "O ponto de referencia se desloca fisicamente; a cena mostra adaptacao, nao um substantivo decorativo.",
            "overlay": f'''    <text x="96" y="145" font-size="30" font-weight="800" letter-spacing="2">S006 · REFERÊNCIA</text>
    <use href="#vl-reference-point-shift-v1" x="210" y="210" width="1500" height="700" data-role="dominant"/>
    <text x="250" y="820" font-size="32" font-weight="800">ANTES</text><text x="1380" y="430" font-size="32" font-weight="800">AGORA</text>
    <text x="770" y="465" font-size="42" font-weight="900" fill="{PALETTE['lime']}">NOVO NORMAL</text>
    <text x="830" y="975" font-size="76" font-weight="900" letter-spacing="-3">O EXTRA DESAPARECE.</text>''',
        },
    ]

    manifest_scenes = []
    for scene in scenes:
        asset_defs = extract_symbol(scene["asset"], by_id)
        defs = asset_defs + ("\n" + rig_defs if scene["character"] else "")
        svg = scene_svg(scene["scene_id"], scene["accent"], defs, scene["overlay"], scene["asset"], scene["ratio"])
        filename = scene["scene_id"].lower() + ".svg"
        (out / filename).write_text(svg, encoding="utf-8", newline="\n")
        manifest_scenes.append({
            "scene_id": scene["scene_id"], "file": filename, "dominant_asset": scene["asset"],
            "visual_type": scene["visual_type"], "layout": scene["layout"],
            "dominant_area_ratio": scene["ratio"], "character": scene["character"],
            "character_function": scene["character_function"], "phosphor": False,
            "accent": scene["accent"], "justification": scene["justification"],
        })

    manifest = {
        "test": "VISUAL_LIBRARY_V1_S001_S006",
        "status": "STATIC_HUMAN_REVIEW_REQUIRED",
        "production_replacement": False,
        "audio": False,
        "animation": False,
        "scenes": manifest_scenes,
    }
    (out / "scene_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(out, manifest_scenes)
    write_contact_sheet(out)
    return manifest_scenes


def write_report(out: Path, scenes: list[dict]) -> None:
    rows = []
    for scene in scenes:
        rows.append(
            f"| {scene['scene_id']} | `{scene['dominant_asset']}` | {scene['visual_type']} | "
            f"{'sim — ' + scene['character_function'] if scene['character'] else 'não'} | não | {scene['justification']} |"
        )
    report = """# Teste estático — Visual Library V1 / S001–S006

**STATUS: PROTÓTIPO SEPARADO — REVISÃO HUMANA NECESSÁRIA**

Este teste não substitui cenas oficiais, não contém áudio, não contém animação e não está integrado ao pipeline de produção.

| Cena | Asset dominante | Visual type | Personagem | Phosphor | Justificativa |
|---|---|---|---|---|---|
""" + "\n".join(rows) + """

## Leitura da sequência

- Alternância: dado → timeline → transformação com escala humana → sistema → pressão → mudança de referência.
- Phosphor: não utilizado; nenhum ícone era necessário para explicar os mecanismos.
- Personagem: usado apenas em S003, com função `SCALE` declarada.
- Aprovação: observar os seis frames parados, sem narração, e o contact sheet a 25%.
"""
    (out / "REPORT.md").write_text(report, encoding="utf-8", newline="\n")


def write_contact_sheet(out: Path) -> None:
    cells = []
    positions = [(240, 270), (720, 270), (1200, 270), (240, 540), (720, 540), (1200, 540)]
    for index, (x, y) in enumerate(positions, start=1):
        cells.append(f'  <image href="s{index:03d}.svg" x="{x}" y="{y}" width="480" height="270"/>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080">
  <rect width="1920" height="1080" fill="{PALETTE['black']}"/>
  <text x="240" y="190" font-family="Arial, sans-serif" font-size="52" font-weight="900" fill="{PALETTE['off_white']}">VISUAL LIBRARY V1 · S001–S006 · 25%</text>
  <text x="1680" y="190" text-anchor="end" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="{PALETTE['lime']}">3 × 2 / STATIC</text>
{chr(10).join(cells)}
  <text x="240" y="890" font-family="Arial, sans-serif" font-size="26" font-weight="700" fill="{PALETTE['off_white']}">Avaliar hierarquia, leitura em 2 segundos e variedade — sem áudio.</text>
</svg>
'''
    (out / "contact_sheet_25.svg").write_text(svg, encoding="utf-8", newline="\n")


def main() -> None:
    assets = build_assets()
    write_catalog(assets)
    scenes = build_scenes(assets)
    print(f"Visual Library V1 gerada: {len(assets)} assets, {len(MOTION_RECIPES)} receitas, {len(scenes)} frames.")


if __name__ == "__main__":
    main()
