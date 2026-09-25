#!/usr/bin/env python3
"""Valida estrutura, CSVs e integridade textual do projeto Capital Oculto."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Iterable


REQUIRED_DIRECTORIES = (
    Path("ARQUIVOS MODELAR"),
    Path("docs"),
    Path("prompts"),
    Path("episodios"),
    Path("episodios/_MODELO"),
    Path("banco_de_ideias"),
    Path("analytics"),
    Path("analytics/dados"),
    Path("analytics/inbox"),
    Path("analytics/relatorios"),
    Path("scripts"),
)

REQUIRED_FILES = (
    Path("AGENTS.md"),
    Path("README.md"),
    Path("START_HERE.md"),
    Path("GUIA_DO_CANAL.md"),
    Path("docs/POSICIONAMENTO.md"),
    Path("docs/SISTEMA_DE_CONTEUDO.md"),
    Path("docs/COPY_THUMB_RETENCAO.md"),
    Path("docs/PIPELINE_DE_PRODUCAO.md"),
    Path("docs/ANALYTICS_E_EXPERIMENTOS.md"),
    Path("docs/SEGURANCA_YPP_E_IA.md"),
    Path("docs/PIPELINE_AUDIOVISUAL.md"),
    Path("docs/ART_DIRECTION_V4.md"),
    Path("prompts/PESQUISA.md"),
    Path("prompts/IDEIAS_E_ANGULOS.md"),
    Path("prompts/TITULOS_E_THUMBNAILS.md"),
    Path("prompts/ROTEIRO_DE_NARRACAO.md"),
    Path("prompts/ROTEIRO_VISUAL.md"),
    Path("prompts/IMAGENS_EM_LOTE.md"),
    Path("prompts/THUMBNAILS.md"),
    Path("prompts/REVISAO_FINAL.md"),
    Path("episodios/_MODELO/00_BRIEF.md"),
    Path("episodios/_MODELO/01_PESQUISA_E_FONTES.md"),
    Path("episodios/_MODELO/02_EMBALAGEM.md"),
    Path("episodios/_MODELO/03_ROTEIRO_NARRACAO.md"),
    Path("episodios/_MODELO/03A_AUDIO_TIMING.json"),
    Path("episodios/_MODELO/04_ROTEIRO_VISUAL.csv"),
    Path("episodios/_MODELO/04A_SCENE_MANIFEST.json"),
    Path("episodios/_MODELO/05_ASSET_MANIFEST.csv"),
    Path("episodios/_MODELO/05_PROMPTS_IMAGENS.csv"),
    Path("episodios/_MODELO/06_THUMBNAILS.md"),
    Path("episodios/_MODELO/07_PACOTE_UPLOAD.md"),
    Path("episodios/_MODELO/08_CHECKLIST_PUBLICACAO.md"),
    Path("episodios/_MODELO/09_POST_MORTEM.md"),
    Path("banco_de_ideias/ideias.csv"),
    Path("analytics/README.md"),
    Path("analytics/dados/videos.csv"),
    Path("analytics/dados/snapshots.csv"),
    Path("analytics/dados/experimentos.csv"),
    Path("analytics/inbox/README.md"),
    Path("analytics/relatorios/README.md"),
    Path("scripts/novo_episodio.py"),
    Path("scripts/analisar_metricas.py"),
    Path("scripts/validar_projeto.py"),
    Path("scripts/resolver_timeline_audiovisual.py"),
    Path("scripts/gerar_sprint_art_direction_v4.py"),
    Path("scripts/validar_art_direction_v4.py"),
    Path("config/art_direction_v4.json"),
)

CSV_SCHEMAS = {
    Path("episodios/_MODELO/04_ROTEIRO_VISUAL.csv"): (
        "scene_id",
        "beat_ids",
        "anchor_start",
        "anchor_end",
        "layout_id",
        "accent",
        "dominant_idea",
        "context",
        "character_role",
        "character_scale",
        "asset_ids",
        "events_json",
        "continuity_in",
        "continuity_out",
        "status",
    ),
    Path("episodios/_MODELO/05_ASSET_MANIFEST.csv"): (
        "asset_id",
        "asset_type",
        "source",
        "provider",
        "license",
        "production_method",
        "scene_ids",
        "first_used_scene",
        "version",
        "sha256",
        "status",
        "legacy_asset_id",
        "prompt_positive",
        "prompt_negative",
    ),
    Path("banco_de_ideias/ideias.csv"): (
        "ordem",
        "id",
        "status",
        "pilar",
        "titulo_base",
        "thumb_base",
        "tese",
        "potencial_clique_1a5",
        "potencial_retencao_1a5",
        "facilidade_producao_1a5",
        "potencial_evergreen_1a5",
        "adequacao_marca_1a5",
        "score_total_25",
        "risco_factual",
        "observacoes",
    ),
    Path("analytics/dados/videos.csv"): (
        "video_id",
        "slug",
        "status",
        "data_publicacao_hora",
        "timezone",
        "titulo",
        "thumbnail_variante",
        "pilar",
        "formato",
        "duracao_segundos",
        "idioma",
        "url",
        "objetivo",
        "hipotese",
        "cta",
        "fonte_trafego_prioritaria",
        "observacoes",
    ),
    Path("analytics/dados/snapshots.csv"): (
        "snapshot_id",
        "video_id",
        "data_coleta_hora",
        "idade_horas",
        "janela_padrao",
        "impressoes",
        "visualizacoes",
        "visualizacoes_origem_impressoes",
        "ctr_impressoes_pct",
        "duracao_media_segundos",
        "percentual_medio_assistido_pct",
        "retencao_30s_pct",
        "retencao_60s_pct",
        "horas_exibicao",
        "inscritos_ganhos",
        "inscritos_perdidos",
        "likes",
        "comentarios",
        "compartilhamentos",
        "espectadores_unicos",
        "novos_espectadores",
        "espectadores_recorrentes",
        "origem_pagina_inicial_pct",
        "origem_sugeridos_pct",
        "origem_pesquisa_pct",
        "origem_externa_pct",
        "rpm_brl",
        "receita_estimada_brl",
        "observacoes",
    ),
    Path("analytics/dados/experimentos.csv"): (
        "experimento_id",
        "video_id",
        "tipo",
        "status",
        "data_inicio_hora",
        "data_fim_hora",
        "janela_avaliacao_horas",
        "variante_controle",
        "variante_teste",
        "metrica_primaria",
        "valor_controle",
        "valor_teste",
        "delta_pct",
        "amostra_controle",
        "amostra_teste",
        "decisao",
        "aprendizado",
        "observacoes",
    ),
}

MANAGED_TEXT_ROOTS = (
    Path("assets"),
    Path("docs"),
    Path("prompts"),
    Path("episodios"),
    Path("banco_de_ideias"),
    Path("analytics"),
    Path("scripts"),
)
ROOT_TEXT_FILES = (
    Path("AGENTS.md"),
    Path("README.md"),
    Path("START_HERE.md"),
    Path("GUIA_DO_CANAL.md"),
)
TEXT_EXTENSIONS = {".csv", ".json", ".md", ".py", ".txt", ".yaml", ".yml"}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OMISSION_LINE_PATTERN = re.compile(r"(?m)^\s*(?:\.{3}|…)\s*$")
GENERIC_FIELD_PATTERN = re.compile(
    r"\[\s*(?:texto|conte[uú]do|inserir|preencher)\s*\]", re.IGNORECASE
)
UNRESOLVED_TOKEN_PATTERN = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def add_unique(messages: list[str], message: str) -> None:
    if message not in messages:
        messages.append(message)


def is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def inspect_structure(project_root: Path, errors: list[str]) -> None:
    for relative in REQUIRED_DIRECTORIES:
        path = project_root / relative
        if not path.is_dir():
            add_unique(errors, f"Diretório obrigatório ausente: {relative}")
    for relative in REQUIRED_FILES:
        path = project_root / relative
        if not path.is_file():
            add_unique(errors, f"Arquivo obrigatório ausente: {relative}")


def read_csv(
    project_root: Path,
    relative: Path,
    expected_headers: tuple[str, ...],
    errors: list[str],
) -> list[dict[str, str]]:
    path = project_root / relative
    if not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                add_unique(errors, f"CSV sem cabeçalho: {relative}")
                return []
            actual_headers = [header.strip() for header in reader.fieldnames if header]
            if len(actual_headers) != len(set(actual_headers)):
                add_unique(errors, f"CSV com cabeçalhos duplicados: {relative}")
            missing = [header for header in expected_headers if header not in actual_headers]
            extra = [header for header in actual_headers if header not in expected_headers]
            if missing:
                add_unique(
                    errors,
                    f"CSV {relative} sem colunas: {', '.join(missing)}",
                )
            if extra:
                add_unique(
                    errors,
                    f"CSV {relative} com colunas não previstas: {', '.join(extra)}",
                )
            if not missing and not extra and tuple(actual_headers) != expected_headers:
                add_unique(errors, f"CSV com ordem de colunas incorreta: {relative}")

            rows: list[dict[str, str]] = []
            for line_number, raw_row in enumerate(reader, start=2):
                if None in raw_row:
                    add_unique(
                        errors,
                        f"CSV {relative}, linha {line_number}: há valores além do cabeçalho.",
                    )
                row = {
                    (key or "").strip(): (value or "").strip()
                    for key, value in raw_row.items()
                    if key is not None
                }
                if any(row.values()):
                    row["_line"] = str(line_number)
                    rows.append(row)
            if not rows:
                add_unique(errors, f"CSV sem linhas de dados: {relative}")
            return rows
    except UnicodeDecodeError:
        add_unique(errors, f"Arquivo não está em UTF-8: {relative}")
    except csv.Error as exc:
        add_unique(errors, f"CSV inválido em {relative}: {exc}")
    except OSError as exc:
        add_unique(errors, f"Falha ao ler {relative}: {exc}")
    return []


def check_unique(
    rows: Iterable[dict[str, str]],
    key: str,
    label: str,
    errors: list[str],
) -> set[str]:
    found: dict[str, str] = {}
    values: set[str] = set()
    for row in rows:
        value = row.get(key, "").strip()
        line = row.get("_line", "?")
        if not value:
            add_unique(errors, f"{label}: linha {line} sem {key}.")
            continue
        normalized = value.casefold()
        if normalized in found:
            add_unique(
                errors,
                f"{label}: {key} duplicado '{value}' nas linhas {found[normalized]} e {line}.",
            )
        else:
            found[normalized] = line
            values.add(normalized)
    return values


def as_integer(
    value: str,
    field: str,
    label: str,
    line: str,
    errors: list[str],
) -> int | None:
    try:
        return int(value)
    except ValueError:
        add_unique(errors, f"{label}: linha {line}, {field} deve ser inteiro.")
        return None


def inspect_ideas(rows: list[dict[str, str]], errors: list[str]) -> None:
    label = "banco_de_ideias/ideias.csv"
    check_unique(rows, "id", label, errors)
    if len(rows) < 40:
        add_unique(errors, f"{label}: esperado ao menos 40 pautas; encontradas {len(rows)}.")

    score_fields = (
        "potencial_clique_1a5",
        "potencial_retencao_1a5",
        "facilidade_producao_1a5",
        "potencial_evergreen_1a5",
        "adequacao_marca_1a5",
    )
    previous_total: int | None = None
    seen_orders: set[int] = set()
    for row in rows:
        line = row.get("_line", "?")
        order = as_integer(row.get("ordem", ""), "ordem", label, line, errors)
        if order is not None:
            if order in seen_orders:
                add_unique(errors, f"{label}: ordem duplicada {order}.")
            seen_orders.add(order)

        scores: list[int] = []
        for field in score_fields:
            score = as_integer(row.get(field, ""), field, label, line, errors)
            if score is not None:
                if not 1 <= score <= 5:
                    add_unique(
                        errors,
                        f"{label}: linha {line}, {field} deve ficar entre 1 e 5.",
                    )
                scores.append(score)
        total = as_integer(
            row.get("score_total_25", ""), "score_total_25", label, line, errors
        )
        if total is not None and len(scores) == len(score_fields):
            if total != sum(scores):
                add_unique(
                    errors,
                    f"{label}: linha {line}, total {total} difere da soma {sum(scores)}.",
                )
            if previous_total is not None and total > previous_total:
                add_unique(errors, f"{label}: pautas não estão em score decrescente.")
            previous_total = total
    if seen_orders and seen_orders != set(range(1, len(rows) + 1)):
        add_unique(errors, f"{label}: a coluna ordem deve formar a sequência de 1 a {len(rows)}.")


def inspect_analytics(
    videos: list[dict[str, str]],
    snapshots: list[dict[str, str]],
    experiments: list[dict[str, str]],
    errors: list[str],
) -> None:
    video_label = "analytics/dados/videos.csv"
    snapshot_label = "analytics/dados/snapshots.csv"
    experiment_label = "analytics/dados/experimentos.csv"
    video_ids = check_unique(videos, "video_id", video_label, errors)
    check_unique(videos, "slug", video_label, errors)
    check_unique(snapshots, "snapshot_id", snapshot_label, errors)
    check_unique(experiments, "experimento_id", experiment_label, errors)

    for row in videos:
        slug = row.get("slug", "")
        if slug and not SLUG_PATTERN.fullmatch(slug):
            add_unique(
                errors,
                f"{video_label}: linha {row.get('_line', '?')}, slug inválido '{slug}'.",
            )

    logical_snapshots: dict[tuple[str, str], str] = {}
    for row in snapshots:
        line = row.get("_line", "?")
        video_id = row.get("video_id", "").casefold()
        if not video_id:
            add_unique(errors, f"{snapshot_label}: linha {line} sem video_id.")
        elif video_id not in video_ids:
            add_unique(
                errors,
                f"{snapshot_label}: linha {line} referencia vídeo não cadastrado '{row.get('video_id', '')}'.",
            )
        key = (video_id, row.get("data_coleta_hora", "").casefold())
        if key[0] and key[1]:
            if key in logical_snapshots:
                add_unique(
                    errors,
                    f"{snapshot_label}: coleta duplicada para vídeo e horário nas linhas {logical_snapshots[key]} e {line}.",
                )
            else:
                logical_snapshots[key] = line

    for row in experiments:
        line = row.get("_line", "?")
        video_id = row.get("video_id", "").casefold()
        if not video_id:
            add_unique(errors, f"{experiment_label}: linha {line} sem video_id.")
        elif video_id not in video_ids:
            add_unique(
                errors,
                f"{experiment_label}: linha {line} referencia vídeo não cadastrado '{row.get('video_id', '')}'.",
            )


def managed_text_files(project_root: Path) -> Iterable[Path]:
    yielded: set[Path] = set()
    for relative in ROOT_TEXT_FILES:
        path = project_root / relative
        if path.is_file():
            yielded.add(path.resolve())
            yield path
    for relative_root in MANAGED_TEXT_ROOTS:
        root = project_root / relative_root
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if (
                path.is_file()
                and path.suffix.lower() in TEXT_EXTENSIONS
                and "__pycache__" not in path.parts
                and path.resolve() not in yielded
            ):
                yielded.add(path.resolve())
                yield path


def inspect_text_files(project_root: Path, errors: list[str]) -> None:
    model_root = (project_root / "episodios" / "_MODELO").resolve()
    prompts_root = (project_root / "prompts").resolve()
    uppercase_markers = (
        "TO" + "DO",
        "FIX" + "ME",
        "T" + "BD",
    )
    forbidden_markers = (
        "lorem" + " ipsum",
        "[pre" + "encher]",
        "<pre" + "encher>",
        "conteúdo" + " aqui",
    )
    for relative_root in MANAGED_TEXT_ROOTS:
        root = project_root / relative_root
        if not root.is_dir():
            continue
        for candidate in root.rglob("*"):
            if not candidate.is_file() or "__pycache__" in candidate.parts:
                continue
            try:
                if candidate.stat().st_size == 0:
                    add_unique(errors, f"Arquivo vazio: {candidate.relative_to(project_root)}")
            except OSError as exc:
                add_unique(
                    errors,
                    f"Falha ao inspecionar {candidate.relative_to(project_root)}: {exc}",
                )
    for path in managed_text_files(project_root):
        relative = path.relative_to(project_root)
        try:
            if path.stat().st_size == 0:
                add_unique(errors, f"Arquivo vazio: {relative}")
                continue
            content = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            add_unique(errors, f"Arquivo textual não está em UTF-8: {relative}")
            continue
        except OSError as exc:
            add_unique(errors, f"Falha ao ler {relative}: {exc}")
            continue
        if not content.strip():
            add_unique(errors, f"Arquivo sem conteúdo útil: {relative}")
            continue

        if is_within(path.resolve(), model_root):
            continue
        for marker in uppercase_markers:
            if re.search(rf"(?<!\w){re.escape(marker)}(?!\w)", content):
                add_unique(errors, f"Marcador proibido em {relative}: {marker}")
        folded = content.casefold()
        for marker in forbidden_markers:
            if marker.casefold() in folded:
                add_unique(errors, f"Marcador proibido em {relative}: {marker}")
        if OMISSION_LINE_PATTERN.search(content):
            add_unique(errors, f"Linha de omissão encontrada em {relative}.")
        if GENERIC_FIELD_PATTERN.search(content):
            add_unique(errors, f"Campo genérico não resolvido em {relative}.")
        if (
            not is_within(path.resolve(), prompts_root)
            and UNRESOLVED_TOKEN_PATTERN.search(content)
        ):
            add_unique(errors, f"Token editorial não resolvido em {relative}.")


def inspect_episode_metadata(project_root: Path, errors: list[str], warnings: list[str]) -> None:
    episodes_root = project_root / "episodios"
    if not episodes_root.is_dir():
        return
    ids: dict[str, Path] = {}
    slugs: dict[str, Path] = {}
    folder_pattern = re.compile(
        r"^(CO-\d{3,})-([a-z0-9]+(?:-[a-z0-9]+)*)$", re.IGNORECASE
    )
    for directory in sorted(episodes_root.iterdir()):
        if not directory.is_dir() or directory.name == "_MODELO":
            continue
        metadata_path = directory / "episodio.json"
        if not metadata_path.is_file():
            match = folder_pattern.fullmatch(directory.name)
            if match is None:
                add_unique(
                    warnings,
                    f"Episódio sem episodio.json e fora da convenção: {directory.relative_to(project_root)}",
                )
                continue
            episode_id, slug = match.groups()
            if episode_id.casefold() in ids:
                add_unique(errors, f"episodio_id duplicado na pasta {directory.relative_to(project_root)}.")
            else:
                ids[episode_id.casefold()] = directory
            if slug.casefold() in slugs:
                add_unique(errors, f"slug duplicado na pasta {directory.relative_to(project_root)}.")
            else:
                slugs[slug.casefold()] = directory
            continue
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            add_unique(errors, f"Metadados inválidos em {metadata_path.relative_to(project_root)}: {exc}")
            continue
        episode_id = str(data.get("episodio_id", "")).strip()
        slug = str(data.get("slug", "")).strip()
        if not episode_id:
            add_unique(errors, f"episodio_id ausente em {metadata_path.relative_to(project_root)}")
        elif episode_id.casefold() in ids:
            add_unique(
                errors,
                f"episodio_id duplicado entre {ids[episode_id.casefold()].relative_to(project_root)} e {metadata_path.relative_to(project_root)}.",
            )
        else:
            ids[episode_id.casefold()] = metadata_path
        if not slug:
            add_unique(errors, f"slug ausente em {metadata_path.relative_to(project_root)}")
        elif not SLUG_PATTERN.fullmatch(slug):
            add_unique(errors, f"slug inválido em {metadata_path.relative_to(project_root)}: {slug}")
        elif slug.casefold() in slugs:
            add_unique(
                errors,
                f"slug duplicado entre {slugs[slug.casefold()].relative_to(project_root)} e {metadata_path.relative_to(project_root)}.",
            )
        else:
            slugs[slug.casefold()] = metadata_path
        expected_folder = f"{episode_id}-{slug}" if episode_id and slug else ""
        if expected_folder and directory.name.casefold() != expected_folder.casefold():
            add_unique(
                errors,
                f"Pasta '{directory.name}' difere da convenção '{expected_folder}' em episodio.json.",
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Confere a estrutura do Capital Oculto, cabeçalhos CSV, IDs e slugs duplicados, "
            "arquivos vazios e marcadores editoriais proibidos."
        )
    )
    parser.add_argument(
        "--projeto-raiz",
        type=Path,
        default=default_project_root(),
        help="Raiz do projeto. Padrão: detectada pela localização do script.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emite o resultado em JSON para automação.",
    )
    parser.add_argument(
        "--quieto",
        action="store_true",
        help="Sem saída quando a validação termina sem erros ou avisos.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = args.projeto_raiz.resolve()
    if not project_root.is_dir():
        message = f"Raiz do projeto não encontrada: {project_root}"
        if args.json_output:
            print(json.dumps({"valido": False, "erros": [message], "avisos": []}, ensure_ascii=False))
        else:
            print(f"ERRO: {message}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    inspect_structure(project_root, errors)

    csv_rows: dict[Path, list[dict[str, str]]] = {}
    for relative, headers in CSV_SCHEMAS.items():
        csv_rows[relative] = read_csv(project_root, relative, headers, errors)
    inspect_ideas(csv_rows[Path("banco_de_ideias/ideias.csv")], errors)
    inspect_analytics(
        csv_rows[Path("analytics/dados/videos.csv")],
        csv_rows[Path("analytics/dados/snapshots.csv")],
        csv_rows[Path("analytics/dados/experimentos.csv")],
        errors,
    )
    inspect_text_files(project_root, errors)
    inspect_episode_metadata(project_root, errors, warnings)

    result = {
        "valido": not errors,
        "erros": errors,
        "avisos": warnings,
        "arquivos_obrigatorios": len(REQUIRED_FILES),
        "pautas": len(csv_rows[Path("banco_de_ideias/ideias.csv")]),
        "videos": len(csv_rows[Path("analytics/dados/videos.csv")]),
        "snapshots": len(csv_rows[Path("analytics/dados/snapshots.csv")]),
        "experimentos": len(csv_rows[Path("analytics/dados/experimentos.csv")]),
    }
    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print(f"VALIDAÇÃO FALHOU — {len(errors)} erro(s), {len(warnings)} aviso(s).")
        for error in errors:
            print(f"[ERRO] {error}")
        for warning in warnings:
            print(f"[AVISO] {warning}")
    elif warnings:
        print(f"PROJETO VÁLIDO COM {len(warnings)} AVISO(S).")
        for warning in warnings:
            print(f"[AVISO] {warning}")
    elif not args.quieto:
        print("PROJETO VÁLIDO — estrutura, CSVs e conteúdo textual aprovados.")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
