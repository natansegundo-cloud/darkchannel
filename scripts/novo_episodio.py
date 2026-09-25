#!/usr/bin/env python3
"""Cria um episódio do Capital Oculto a partir do diretório-modelo."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ID_PATTERN = re.compile(r"^CO-\d{3,}$", re.IGNORECASE)
TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
}
PIPELINE_TEMPLATE_FILES = (
    "03_ROTEIRO_NARRACAO.md",
    "03A_AUDIO_TIMING.json",
    "04_ROTEIRO_VISUAL.csv",
    "04A_SCENE_MANIFEST.json",
    "05_ASSET_MANIFEST.csv",
    "05_PROMPTS_IMAGENS.csv",
)


class EpisodeCreationError(Exception):
    """Erro esperado de validação ou criação."""


def default_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_from_root(project_root: Path, value: Path) -> Path:
    if value.is_absolute():
        return value.resolve()
    return (project_root / value).resolve()


def title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").capitalize()


def find_next_episode_id(project_root: Path, destination_root: Path) -> str:
    sequence_pattern = re.compile(r"^CO-(\d{3,})(?:-|$)", re.IGNORECASE)
    numbers: set[int] = set()
    if destination_root.is_dir():
        for child in destination_root.iterdir():
            if not child.is_dir():
                continue
            match = sequence_pattern.match(child.name)
            if match:
                numbers.add(int(match.group(1)))

    videos_csv = project_root / "analytics" / "dados" / "videos.csv"
    if videos_csv.is_file():
        try:
            with videos_csv.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    match = sequence_pattern.match((row.get("video_id") or "").strip())
                    if match:
                        numbers.add(int(match.group(1)))
        except (OSError, UnicodeDecodeError, csv.Error):
            pass
    return f"CO-{max(numbers, default=0) + 1:03d}"


def find_id_collision(destination_root: Path, episode_id: str) -> Path | None:
    if not destination_root.is_dir():
        return None
    prefix = f"{episode_id}-".casefold()
    for child in destination_root.iterdir():
        if not child.is_dir() or child.name == "_MODELO":
            continue
        if child.name.casefold() == episode_id.casefold() or child.name.casefold().startswith(prefix):
            return child
        metadata_path = child / "episodio.json"
        if metadata_path.is_file():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if str(metadata.get("episodio_id", "")).strip().casefold() == episode_id.casefold():
                return child
    return None


def find_slug_collision(destination_root: Path, slug: str) -> Path | None:
    if not destination_root.is_dir():
        return None
    folder_pattern = re.compile(
        r"^CO-\d{3,}-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)$", re.IGNORECASE
    )
    for child in destination_root.iterdir():
        if not child.is_dir() or child.name == "_MODELO":
            continue
        match = folder_pattern.fullmatch(child.name)
        if match and match.group("slug").casefold() == slug.casefold():
            return child
        metadata_path = child / "episodio.json"
        if metadata_path.is_file():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if str(metadata.get("slug", "")).strip().casefold() == slug.casefold():
                return child
    return None


def validate_inputs(
    slug: str,
    episode_id: str,
    creation_date: str,
    model_dir: Path,
    destination_root: Path,
) -> None:
    if not SLUG_PATTERN.fullmatch(slug):
        raise EpisodeCreationError(
            "O slug deve conter apenas letras minúsculas sem acento, números e hífens."
        )
    if not ID_PATTERN.fullmatch(episode_id):
        raise EpisodeCreationError(
            "O ID deve seguir CO-###, com ao menos três algarismos."
        )
    try:
        date.fromisoformat(creation_date)
    except ValueError as exc:
        raise EpisodeCreationError("A data deve usar o formato AAAA-MM-DD.") from exc
    if not model_dir.is_dir():
        raise EpisodeCreationError(f"Diretório-modelo não encontrado: {model_dir}")
    if not any(model_dir.iterdir()):
        raise EpisodeCreationError(f"O diretório-modelo está vazio: {model_dir}")
    missing_pipeline = [name for name in PIPELINE_TEMPLATE_FILES if not (model_dir / name).is_file()]
    if missing_pipeline:
        raise EpisodeCreationError(
            "O diretório-modelo não contém o pipeline audiovisual completo: "
            + ", ".join(missing_pipeline)
        )
    if destination_root.exists() and not destination_root.is_dir():
        raise EpisodeCreationError(
            f"O destino-raiz existe, mas não é um diretório: {destination_root}"
        )
    collision = find_id_collision(destination_root, episode_id)
    if collision is not None:
        raise EpisodeCreationError(
            f"O ID {episode_id} já pertence a outro episódio: {collision}"
        )
    slug_collision = find_slug_collision(destination_root, slug)
    if slug_collision is not None:
        raise EpisodeCreationError(
            f"O slug {slug} já pertence a outro episódio: {slug_collision}"
        )


def replace_tokens(directory: Path, values: dict[str, str]) -> int:
    changed_files = 0
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            original = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise EpisodeCreationError(
                f"Arquivo textual do modelo não está em UTF-8: {path}"
            ) from exc
        updated = original
        for token, value in values.items():
            updated = updated.replace(token, value)
        if updated != original:
            with path.open("w", encoding="utf-8", newline="") as handle:
                handle.write(updated)
            changed_files += 1
    return changed_files


def create_episode(
    *,
    slug: str,
    title: str,
    episode_id: str,
    creation_date: str,
    model_dir: Path,
    destination_root: Path,
    project_root: Path,
) -> tuple[Path, int]:
    validate_inputs(slug, episode_id, creation_date, model_dir, destination_root)
    destination_root.mkdir(parents=True, exist_ok=True)
    folder_name = f"{episode_id}-{slug}"
    target = (destination_root / folder_name).resolve()
    if target.parent != destination_root.resolve():
        raise EpisodeCreationError("O destino calculado saiu do diretório de episódios.")
    if target.exists():
        raise EpisodeCreationError(
            f"O episódio já existe e não será sobrescrito: {target}"
        )

    temporary_root = Path(
        tempfile.mkdtemp(prefix=".novo-episodio-", dir=str(destination_root))
    )
    staging = temporary_root / folder_name
    try:
        shutil.copytree(model_dir, staging)
        token_values = {
            f"{{{{{name}}}}}": value
            for name, value in (
                ("EPISODIO_ID", episode_id),
                ("EPISODIO_SLUG", slug),
                ("EPISODIO_TITULO", title),
                ("DATA_CRIACAO", creation_date),
            )
        }
        changed_files = replace_tokens(staging, token_values)

        try:
            model_reference = str(model_dir.relative_to(project_root))
        except ValueError:
            model_reference = str(model_dir)
        metadata = {
            "episodio_id": episode_id,
            "slug": slug,
            "titulo": title,
            "data_criacao": creation_date,
            "pasta": folder_name,
            "modelo_origem": model_reference,
        }
        metadata_path = staging / "episodio.json"
        with metadata_path.open("w", encoding="utf-8", newline="") as handle:
            json.dump(metadata, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        if target.exists():
            raise EpisodeCreationError(
                f"O episódio passou a existir durante a criação e não será sobrescrito: {target}"
            )
        staging.rename(target)
        return target, changed_files
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Copia episodios/_MODELO para uma nova pasta, personaliza marcadores "
            "conhecidos e impede sobrescrita."
        )
    )
    parser.add_argument(
        "slug_positional",
        nargs="?",
        help="Slug sem acento; pode ser informado aqui ou pela opção --slug.",
    )
    parser.add_argument(
        "--slug",
        dest="slug_option",
        help="Slug sem acento, por exemplo: por-que-o-salario-some.",
    )
    parser.add_argument(
        "--titulo",
        help="Título de trabalho. Por padrão, é derivado do slug.",
    )
    parser.add_argument(
        "--episodio-id",
        "--id",
        dest="episodio_id",
        help="ID único, por exemplo CO-002. O padrão usa o próximo CO-### livre.",
    )
    parser.add_argument(
        "--data-criacao",
        default=date.today().isoformat(),
        help="Data em AAAA-MM-DD. Padrão: data local de hoje.",
    )
    parser.add_argument(
        "--projeto-raiz",
        type=Path,
        default=default_project_root(),
        help="Raiz do projeto. Padrão: detectada pela localização do script.",
    )
    parser.add_argument(
        "--modelo",
        type=Path,
        default=Path("episodios/_MODELO"),
        help="Diretório-modelo absoluto ou relativo à raiz do projeto.",
    )
    parser.add_argument(
        "--destino-raiz",
        type=Path,
        default=Path("episodios"),
        help="Diretório de episódios absoluto ou relativo à raiz do projeto.",
    )
    parser.add_argument(
        "--simular",
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Valida e mostra o destino sem criar arquivos.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_root = args.projeto_raiz.resolve()
    model_dir = resolve_from_root(project_root, args.modelo)
    destination_root = resolve_from_root(project_root, args.destino_raiz)
    if args.slug_positional and args.slug_option and args.slug_positional != args.slug_option:
        print("ERRO: o slug posicional e --slug são diferentes.", file=sys.stderr)
        return 2
    slug = args.slug_option or args.slug_positional
    if not slug:
        print("ERRO: informe o slug como argumento posicional ou com --slug.", file=sys.stderr)
        return 2
    title = (args.titulo or title_from_slug(slug)).strip()
    if not title:
        print("ERRO: o título não pode ficar vazio.", file=sys.stderr)
        return 2
    episode_id = args.episodio_id or find_next_episode_id(project_root, destination_root)

    try:
        validate_inputs(
            slug,
            episode_id,
            args.data_criacao,
            model_dir,
            destination_root,
        )
        target = (destination_root / f"{episode_id}-{slug}").resolve()
        if target.parent != destination_root.resolve():
            raise EpisodeCreationError(
                "O destino calculado saiu do diretório de episódios."
            )
        if target.exists():
            raise EpisodeCreationError(
                f"O episódio já existe e não será sobrescrito: {target}"
            )
        if args.dry_run:
            print("Simulação validada.")
            print(f"Modelo: {model_dir}")
            print(f"Destino: {target}")
            print(f"ID: {episode_id}")
            print(f"Título: {title}")
            return 0

        created_path, changed_files = create_episode(
            slug=slug,
            title=title,
            episode_id=episode_id,
            creation_date=args.data_criacao,
            model_dir=model_dir,
            destination_root=destination_root,
            project_root=project_root,
        )
    except EpisodeCreationError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERRO de sistema ao criar o episódio: {exc}", file=sys.stderr)
        return 1

    print(f"Episódio criado: {created_path}")
    print(f"Arquivos personalizados por marcadores: {changed_files}")
    print("Metadados: episodio.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
