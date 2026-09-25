#!/usr/bin/env python3
"""Gera um relatório Markdown a partir dos CSVs de analytics do canal."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


VIDEO_HEADERS = {
    "video_id",
    "slug",
    "status",
    "data_publicacao_hora",
    "titulo",
    "duracao_segundos",
}
SNAPSHOT_HEADERS = {
    "snapshot_id",
    "video_id",
    "data_coleta_hora",
    "idade_horas",
    "janela_padrao",
    "impressoes",
    "visualizacoes",
    "ctr_impressoes_pct",
    "percentual_medio_assistido_pct",
    "retencao_30s_pct",
    "horas_exibicao",
    "inscritos_ganhos",
    "inscritos_perdidos",
}
EXPERIMENT_HEADERS = {
    "experimento_id",
    "video_id",
    "tipo",
    "status",
    "variante_controle",
    "variante_teste",
    "metrica_primaria",
    "valor_controle",
    "valor_teste",
    "delta_pct",
    "decisao",
    "aprendizado",
}


@dataclass(frozen=True)
class Window:
    label: str
    target_hours: float
    tolerance_hours: float


WINDOWS = (
    Window("24H", 24.0, 6.0),
    Window("72H", 72.0, 12.0),
    Window("7D", 168.0, 24.0),
    Window("28D", 672.0, 72.0),
)
WINDOW_BY_LABEL = {window.label: window for window in WINDOWS}
WINDOW_ALIASES = {
    "1D": "24H",
    "24H": "24H",
    "3D": "72H",
    "72H": "72H",
    "7D": "7D",
    "168H": "7D",
    "28D": "28D",
    "672H": "28D",
}

METRICS = (
    ("impressoes", "Impressões", "integer"),
    ("visualizacoes", "Views", "integer"),
    ("ctr_impressoes_pct", "CTR", "percent"),
    ("retencao_30s_pct", "Ret. 30s", "percent"),
    ("percentual_medio_assistido_pct", "Média assistida", "percent"),
    ("horas_exibicao", "Horas", "decimal"),
    ("inscritos_por_mil", "Inscr. líquidos/mil", "decimal"),
)


class AnalyticsError(Exception):
    """Erro esperado nos arquivos ou argumentos de analytics."""


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_from_root(project_root: Path, value: Path) -> Path:
    if value.is_absolute():
        return value.resolve()
    return (project_root / value).resolve()


def read_csv_rows(path: Path, required_headers: set[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise AnalyticsError(f"CSV não encontrado: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise AnalyticsError(f"CSV sem cabeçalho: {path}")
            headers = [header.strip() for header in reader.fieldnames if header]
            missing = sorted(required_headers - set(headers))
            if missing:
                raise AnalyticsError(
                    f"Cabeçalhos ausentes em {path}: {', '.join(missing)}"
                )
            rows = []
            for row in reader:
                cleaned = {
                    (key or "").strip(): (value or "").strip()
                    for key, value in row.items()
                }
                if any(cleaned.values()):
                    rows.append(cleaned)
            return rows
    except UnicodeDecodeError as exc:
        raise AnalyticsError(f"CSV não está em UTF-8: {path}") from exc
    except csv.Error as exc:
        raise AnalyticsError(f"CSV inválido em {path}: {exc}") from exc


def begins_as_example(value: str) -> bool:
    return value.strip().upper().startswith("EXEMPLO")


def is_example_row(row: dict[str, str]) -> bool:
    keys = ("video_id", "snapshot_id", "experimento_id", "status")
    return any(begins_as_example(row.get(key, "")) for key in keys)


def index_unique(
    rows: Iterable[dict[str, str]], key: str, source_name: str
) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for line_number, row in enumerate(rows, start=2):
        value = row.get(key, "").strip()
        if not value:
            raise AnalyticsError(
                f"{source_name}: linha {line_number} sem valor em {key}."
            )
        normalized = value.casefold()
        if normalized in indexed:
            raise AnalyticsError(
                f"{source_name}: valor duplicado em {key}: {value}"
            )
        indexed[normalized] = row
    return indexed


def optional_number(value: str, field: str, record_id: str) -> float | None:
    text = value.strip()
    if not text:
        return None
    try:
        number = float(text.replace(",", "."))
    except ValueError as exc:
        raise AnalyticsError(
            f"Valor numérico inválido em {record_id}, campo {field}: {value}"
        ) from exc
    if not math.isfinite(number):
        raise AnalyticsError(
            f"Valor não finito em {record_id}, campo {field}: {value}"
        )
    return number


def parse_datetime(value: str, field: str, record_id: str) -> datetime | None:
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise AnalyticsError(
            f"Data inválida em {record_id}, campo {field}: {value}"
        ) from exc


def normalized_window(value: str) -> str | None:
    compact = value.strip().upper().replace(" ", "")
    return WINDOW_ALIASES.get(compact)


def calculate_age_hours(
    snapshot: dict[str, str],
    video: dict[str, str],
    record_id: str,
) -> float | None:
    explicit_age = optional_number(snapshot.get("idade_horas", ""), "idade_horas", record_id)
    if explicit_age is not None:
        if explicit_age < 0:
            raise AnalyticsError(f"Idade negativa no snapshot {record_id}.")
        return explicit_age

    collected = parse_datetime(
        snapshot.get("data_coleta_hora", ""), "data_coleta_hora", record_id
    )
    published = parse_datetime(
        video.get("data_publicacao_hora", ""), "data_publicacao_hora", record_id
    )
    if collected is None or published is None:
        return None
    if (collected.tzinfo is None) != (published.tzinfo is None):
        raise AnalyticsError(
            f"Datas com fusos incompatíveis no snapshot {record_id}."
        )
    age = (collected - published).total_seconds() / 3600.0
    if age < 0:
        raise AnalyticsError(f"Coleta anterior à publicação no snapshot {record_id}.")
    return age


def metric_values(snapshot: dict[str, str], record_id: str) -> dict[str, float | None]:
    values: dict[str, float | None] = {}
    source_fields = {
        "impressoes",
        "visualizacoes",
        "ctr_impressoes_pct",
        "retencao_30s_pct",
        "percentual_medio_assistido_pct",
        "horas_exibicao",
        "inscritos_ganhos",
        "inscritos_perdidos",
    }
    for field in source_fields:
        values[field] = optional_number(snapshot.get(field, ""), field, record_id)

    for field in source_fields:
        value = values[field]
        if value is not None and value < 0:
            raise AnalyticsError(
                f"Valor negativo em {record_id}, campo {field}: {value}"
            )
    for field in (
        "ctr_impressoes_pct",
        "retencao_30s_pct",
        "percentual_medio_assistido_pct",
    ):
        value = values[field]
        if value is not None and value > 100:
            raise AnalyticsError(
                f"Percentual acima de 100 em {record_id}, campo {field}: {value}"
            )

    gained = values["inscritos_ganhos"]
    lost = values["inscritos_perdidos"]
    net = None
    if gained is not None or lost is not None:
        net = (gained or 0.0) - (lost or 0.0)
    values["inscritos_liquidos"] = net
    views = values["visualizacoes"]
    values["inscritos_por_mil"] = (
        net / views * 1000.0 if net is not None and views not in (None, 0.0) else None
    )
    return values


def select_snapshots(
    rows: Iterable[dict[str, str]],
    videos: dict[str, dict[str, str]],
    warnings: list[str],
) -> dict[tuple[str, str], dict[str, object]]:
    selected: dict[tuple[str, str], dict[str, object]] = {}
    warned: set[str] = set()

    for row in rows:
        snapshot_id = row.get("snapshot_id", "sem-id")
        video_id = row.get("video_id", "").strip()
        video = videos.get(video_id.casefold())
        if video is None:
            message = f"Snapshot {snapshot_id} ignorado: vídeo {video_id or 'vazio'} não cadastrado."
            if message not in warned:
                warnings.append(message)
                warned.add(message)
            continue

        age_hours = calculate_age_hours(row, video, snapshot_id)
        declared = row.get("janela_padrao", "").strip()
        window_label = normalized_window(declared)
        if declared and window_label is None:
            warnings.append(
                f"Snapshot {snapshot_id}: janela '{declared}' inválida; tentativa de inferência pela idade."
            )

        if window_label is not None:
            window = WINDOW_BY_LABEL[window_label]
            distance = (
                abs(age_hours - window.target_hours) if age_hours is not None else 0.0
            )
        else:
            if age_hours is None:
                warnings.append(
                    f"Snapshot {snapshot_id} ignorado: sem janela e sem idade calculável."
                )
                continue
            window = min(WINDOWS, key=lambda item: abs(age_hours - item.target_hours))
            distance = abs(age_hours - window.target_hours)
            if distance > window.tolerance_hours:
                warnings.append(
                    f"Snapshot {snapshot_id} ignorado: idade {age_hours:.1f}h fora das tolerâncias padrão."
                )
                continue
            window_label = window.label

        collected = parse_datetime(
            row.get("data_coleta_hora", ""), "data_coleta_hora", snapshot_id
        )
        if collected is not None:
            if collected.tzinfo is None:
                collected_rank = collected.timestamp()
            else:
                collected_rank = collected.astimezone().timestamp()
        else:
            collected_rank = 0.0

        enriched: dict[str, object] = dict(row)
        enriched["_window"] = window_label
        enriched["_age_hours"] = age_hours
        enriched["_distance"] = distance
        enriched["_collected_rank"] = collected_rank
        enriched["_metrics"] = metric_values(row, snapshot_id)
        key = (video_id.casefold(), window_label)
        current = selected.get(key)
        if current is None:
            selected[key] = enriched
            continue
        current_rank = (
            float(current["_distance"]),
            -float(current["_collected_rank"]),
        )
        new_rank = (distance, -collected_rank)
        if new_rank < current_rank:
            selected[key] = enriched

    return selected


def calculate_baselines(
    selected: dict[tuple[str, str], dict[str, object]]
) -> dict[str, dict[str, float | int | None]]:
    baselines: dict[str, dict[str, float | int | None]] = {}
    for window in WINDOWS:
        snapshots = [
            snapshot
            for (_, label), snapshot in selected.items()
            if label == window.label
        ]
        window_stats: dict[str, float | int | None] = {"n": len(snapshots)}
        for metric_key, _, _ in METRICS:
            samples = [
                float(metrics[metric_key])
                for snapshot in snapshots
                for metrics in [snapshot["_metrics"]]
                if isinstance(metrics, dict) and metrics.get(metric_key) is not None
            ]
            window_stats[metric_key] = statistics.median(samples) if samples else None
        baselines[window.label] = window_stats
    return baselines


def format_number(value: float | int | None, kind: str) -> str:
    if value is None:
        return "—"
    number = float(value)
    if kind == "integer":
        return f"{number:,.0f}".replace(",", ".")
    if kind == "percent":
        return f"{number:.1f}%".replace(".", ",")
    return f"{number:.1f}".replace(".", ",")


def format_delta(value: float | None, baseline: float | int | None) -> str:
    if value is None or baseline is None:
        return "—"
    reference = float(baseline)
    if reference == 0:
        return "n/d"
    delta = (value - reference) / abs(reference) * 100.0
    return f"{delta:+.1f}%".replace(".", ",")


def markdown_text(value: str) -> str:
    return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def relative_label(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def build_report(
    *,
    project_root: Path,
    video_path: Path,
    snapshot_path: Path,
    experiment_path: Path,
    videos: dict[str, dict[str, str]],
    selected: dict[tuple[str, str], dict[str, object]],
    experiments: list[dict[str, str]],
    baselines: dict[str, dict[str, float | int | None]],
    warnings: list[str],
    video_filter: str | None,
    include_examples: bool,
) -> str:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "# Relatório de performance — Capital Oculto",
        "",
        f"Gerado em `{generated_at}`.",
        "",
        "## Escopo",
        "",
        f"- Vídeos: `{relative_label(video_path, project_root)}`",
        f"- Snapshots: `{relative_label(snapshot_path, project_root)}`",
        f"- Experimentos: `{relative_label(experiment_path, project_root)}`",
        f"- Filtro de vídeo: `{video_filter or 'todos'}`",
        f"- Linhas EXEMPLO incluídas: `{'sim' if include_examples else 'não'}`",
        "",
        "## Baseline mediano do canal",
        "",
        "A referência usa um snapshot por vídeo em cada janela. `N < 3` é marcado como amostra inicial.",
        "",
        "| Janela | N | Confiança | Impressões | Views | CTR | Ret. 30s | Média assistida | Horas | Inscr. líquidos/mil |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    metric_kind = {key: kind for key, _, kind in METRICS}
    for window in WINDOWS:
        stats = baselines[window.label]
        sample_size = int(stats["n"] or 0)
        confidence = "inicial" if sample_size < 3 else "comparável"
        lines.append(
            "| "
            + " | ".join(
                [
                    window.label,
                    str(sample_size),
                    confidence,
                    format_number(stats["impressoes"], metric_kind["impressoes"]),
                    format_number(stats["visualizacoes"], metric_kind["visualizacoes"]),
                    format_number(stats["ctr_impressoes_pct"], metric_kind["ctr_impressoes_pct"]),
                    format_number(stats["retencao_30s_pct"], metric_kind["retencao_30s_pct"]),
                    format_number(
                        stats["percentual_medio_assistido_pct"],
                        metric_kind["percentual_medio_assistido_pct"],
                    ),
                    format_number(stats["horas_exibicao"], metric_kind["horas_exibicao"]),
                    format_number(stats["inscritos_por_mil"], metric_kind["inscritos_por_mil"]),
                ]
            )
            + " |"
        )

    filtered_videos = [
        video
        for normalized_id, video in videos.items()
        if video_filter is None or normalized_id == video_filter.casefold()
    ]
    filtered_videos.sort(
        key=lambda item: (item.get("data_publicacao_hora", ""), item.get("video_id", ""))
    )
    lines.extend(["", "## Desempenho por vídeo", ""])
    if not filtered_videos:
        lines.extend(
            [
                "Nenhum vídeo elegível foi encontrado. Cadastre o primeiro vídeo real ou use `--incluir-exemplos` para testar o formato.",
                "",
            ]
        )

    for video in filtered_videos:
        video_id = video["video_id"]
        title = markdown_text(video.get("titulo", "Sem título"))
        duration = optional_number(
            video.get("duracao_segundos", ""), "duracao_segundos", video_id
        )
        duration_text = "não informada"
        if duration is not None:
            total_seconds = max(0, int(round(duration)))
            duration_text = f"{total_seconds // 60}:{total_seconds % 60:02d}"
        lines.extend(
            [
                f"### {markdown_text(video_id)} — {title}",
                "",
                f"Status: `{markdown_text(video.get('status', '') or 'não informado')}` · Duração: `{duration_text}` · Pilar: `{markdown_text(video.get('pilar', '') or 'não informado')}`",
                "",
                "| Janela | Idade medida | Views | vs. mediana | CTR | vs. mediana | Ret. 30s | Média assistida | Horas | Inscr. líquidos |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        has_snapshot = False
        for window in WINDOWS:
            snapshot = selected.get((video_id.casefold(), window.label))
            if snapshot is None:
                lines.append(
                    f"| {window.label} | — | — | — | — | — | — | — | — | — |"
                )
                continue
            has_snapshot = True
            values = snapshot["_metrics"]
            if not isinstance(values, dict):
                raise AnalyticsError(f"Falha interna nas métricas de {video_id}.")
            age = snapshot["_age_hours"]
            age_text = f"{float(age):.1f}h".replace(".", ",") if age is not None else "—"
            baseline = baselines[window.label]
            lines.append(
                "| "
                + " | ".join(
                    [
                        window.label,
                        age_text,
                        format_number(values.get("visualizacoes"), "integer"),
                        format_delta(values.get("visualizacoes"), baseline["visualizacoes"]),
                        format_number(values.get("ctr_impressoes_pct"), "percent"),
                        format_delta(
                            values.get("ctr_impressoes_pct"), baseline["ctr_impressoes_pct"]
                        ),
                        format_number(values.get("retencao_30s_pct"), "percent"),
                        format_number(
                            values.get("percentual_medio_assistido_pct"), "percent"
                        ),
                        format_number(values.get("horas_exibicao"), "decimal"),
                        format_number(values.get("inscritos_liquidos"), "integer"),
                    ]
                )
                + " |"
            )
        if not has_snapshot:
            lines.extend(["", "Ainda não há snapshot utilizável para este vídeo."])
        lines.append("")

    lines.extend(["## Experimentos registrados", ""])
    filtered_experiments = [
        experiment
        for experiment in experiments
        if video_filter is None
        or experiment.get("video_id", "").casefold() == video_filter.casefold()
    ]
    if not filtered_experiments:
        lines.extend(["Nenhum experimento elegível foi registrado.", ""])
    else:
        lines.extend(
            [
                "| ID | Vídeo | Tipo | Status | Controle | Teste | Métrica | Delta | Decisão | Aprendizado |",
                "|---|---|---|---|---|---|---|---:|---|---|",
            ]
        )
        for experiment in filtered_experiments:
            record_id = experiment.get("experimento_id", "sem-id")
            control = optional_number(
                experiment.get("valor_controle", ""), "valor_controle", record_id
            )
            test = optional_number(
                experiment.get("valor_teste", ""), "valor_teste", record_id
            )
            delta = optional_number(experiment.get("delta_pct", ""), "delta_pct", record_id)
            if delta is None and control not in (None, 0.0) and test is not None:
                delta = (test - control) / abs(control) * 100.0
            delta_text = (
                f"{delta:+.1f}%".replace(".", ",") if delta is not None else "—"
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        markdown_text(record_id),
                        markdown_text(experiment.get("video_id", "")),
                        markdown_text(experiment.get("tipo", "")),
                        markdown_text(experiment.get("status", "")),
                        markdown_text(experiment.get("variante_controle", "")),
                        markdown_text(experiment.get("variante_teste", "")),
                        markdown_text(experiment.get("metrica_primaria", "")),
                        delta_text,
                        markdown_text(experiment.get("decisao", "") or "—"),
                        markdown_text(experiment.get("aprendizado", "") or "—"),
                    ]
                )
                + " |"
            )
        lines.append("")

    lines.extend(
        [
            "## Leitura responsável",
            "",
            "- CTR alto com poucas impressões ainda pode refletir uma audiência pequena e muito alinhada.",
            "- CTR baixo com distribuição crescente pode refletir expansão para públicos mais frios.",
            "- Retenção inicial mede a entrega da promessa; duração média e percentual assistido mostram a sustentação.",
            "- Uma mudança deve ser associada a um experimento antes de receber crédito pelo resultado.",
            "",
            "## Alertas de qualidade dos dados",
            "",
        ]
    )
    if warnings:
        lines.extend(f"- {markdown_text(message)}" for message in warnings)
    else:
        lines.append("- Nenhum alerta detectado.")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Lê vídeos, snapshots e experimentos; calcula as janelas 24H, 72H, 7D e 28D; "
            "compara com a mediana do canal e grava um relatório Markdown."
        )
    )
    parser.add_argument(
        "--projeto-raiz",
        type=Path,
        default=default_project_root(),
        help="Raiz do projeto. Padrão: detectada pela localização do script.",
    )
    parser.add_argument(
        "--videos",
        type=Path,
        default=Path("analytics/dados/videos.csv"),
        help="CSV de vídeos, absoluto ou relativo à raiz.",
    )
    parser.add_argument(
        "--snapshots",
        type=Path,
        default=Path("analytics/dados/snapshots.csv"),
        help="CSV de snapshots, absoluto ou relativo à raiz.",
    )
    parser.add_argument(
        "--experimentos",
        type=Path,
        default=Path("analytics/dados/experimentos.csv"),
        help="CSV de experimentos, absoluto ou relativo à raiz.",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        help="Arquivo Markdown de saída. O padrão usa data e hora em analytics/relatorios.",
    )
    parser.add_argument(
        "--video-id",
        help="Limita as seções detalhadas a um vídeo; o baseline continua usando todo o canal.",
    )
    parser.add_argument(
        "--incluir-exemplos",
        action="store_true",
        help="Inclui linhas marcadas como EXEMPLO para testar o relatório.",
    )
    parser.add_argument(
        "--sobrescrever",
        action="store_true",
        help="Permite substituir explicitamente o arquivo indicado em --saida.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = args.projeto_raiz.resolve()
    video_path = resolve_from_root(project_root, args.videos)
    snapshot_path = resolve_from_root(project_root, args.snapshots)
    experiment_path = resolve_from_root(project_root, args.experimentos)
    if args.saida is None:
        stamp = datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")
        output_path = project_root / "analytics" / "relatorios" / f"relatorio-{stamp}.md"
    else:
        output_path = resolve_from_root(project_root, args.saida)

    try:
        video_rows = read_csv_rows(video_path, VIDEO_HEADERS)
        snapshot_rows = read_csv_rows(snapshot_path, SNAPSHOT_HEADERS)
        experiment_rows = read_csv_rows(experiment_path, EXPERIMENT_HEADERS)
        index_unique(video_rows, "video_id", "videos.csv")
        index_unique(snapshot_rows, "snapshot_id", "snapshots.csv")
        index_unique(experiment_rows, "experimento_id", "experimentos.csv")

        if not args.incluir_exemplos:
            video_rows = [row for row in video_rows if not is_example_row(row)]
            snapshot_rows = [row for row in snapshot_rows if not is_example_row(row)]
            experiment_rows = [row for row in experiment_rows if not is_example_row(row)]

        videos = {row["video_id"].casefold(): row for row in video_rows}
        if args.video_id and args.video_id.casefold() not in videos:
            raise AnalyticsError(
                f"Vídeo não encontrado no escopo atual: {args.video_id}."
            )

        warnings: list[str] = []
        selected = select_snapshots(snapshot_rows, videos, warnings)
        baselines = calculate_baselines(selected)
        report = build_report(
            project_root=project_root,
            video_path=video_path,
            snapshot_path=snapshot_path,
            experiment_path=experiment_path,
            videos=videos,
            selected=selected,
            experiments=experiment_rows,
            baselines=baselines,
            warnings=warnings,
            video_filter=args.video_id,
            include_examples=args.incluir_exemplos,
        )

        if output_path.exists() and not args.sobrescrever:
            raise AnalyticsError(
                f"O relatório já existe; use outro nome ou --sobrescrever: {output_path}"
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(report)
    except AnalyticsError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERRO de sistema: {exc}", file=sys.stderr)
        return 1

    print(f"Relatório criado: {output_path}")
    print(f"Vídeos no escopo: {len(videos)}")
    print(f"Snapshots selecionados: {len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
