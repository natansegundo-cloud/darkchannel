#!/usr/bin/env python3
"""Gera narração PT-BR local com as vozes masculinas aprovadas do Kokoro."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".tts" / "venv" / "Scripts" / "python.exe"
CONFIG_PATH = ROOT / "config" / "voz_local.json"


def garantir_ambiente_isolado() -> None:
    """Relança este script no Python isolado quando necessário."""
    if not VENV_PYTHON.exists():
        raise SystemExit(
            "Ambiente de voz não encontrado em .tts/venv. "
            "Execute a instalação local antes de gerar áudio."
        )
    if Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        comando = [str(VENV_PYTHON), str(Path(__file__).resolve()), *sys.argv[1:]]
        raise SystemExit(subprocess.call(comando, cwd=ROOT))


garantir_ambiente_isolado()

import numpy as np  # noqa: E402
import onnxruntime as ort  # noqa: E402
import soundfile as sf  # noqa: E402
from kokoro_onnx import Kokoro  # noqa: E402
from misaki.espeak import EspeakG2P  # noqa: E402


ort.set_default_logger_severity(3)


def carregar_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def caminho_do_projeto(valor: str) -> Path:
    caminho = Path(valor)
    return caminho if caminho.is_absolute() else ROOT / caminho


def limpar_texto(texto: str) -> str:
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r" *\n *", "\n", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def extrair_beats_markdown(texto: str) -> list[dict[str, str]]:
    """Extrai narrações em blockquote de seções ``### B001``.

    O blockquote é intencional: separa o texto falado das notas editoriais sem
    introduzir YAML ou outra dependência no roteiro.
    """
    cabecalhos = list(re.finditer(r"(?m)^###\s+(B\d{3,})\b([^\r\n]*)$", texto))
    beats: list[dict[str, str]] = []
    for indice, match in enumerate(cabecalhos):
        fim = cabecalhos[indice + 1].start() if indice + 1 < len(cabecalhos) else len(texto)
        bloco = texto[match.end() : fim]
        linhas = []
        for linha in bloco.splitlines():
            quote = re.match(r"^>\s?(.*)$", linha)
            if quote:
                linhas.append(quote.group(1).strip())
        narracao = limpar_texto(" ".join(linhas))
        if not narracao:
            continue
        titulo = match.group(2).strip().lstrip("—-").strip()
        beats.append({"beat_id": match.group(1), "title": titulo, "text": narracao})
    return beats


def selecionar_beats(beats: list[dict[str, str]], selecao: str | None) -> list[dict[str, str]]:
    if not selecao:
        return beats
    ids = [item.strip().upper() for item in selecao.split(",") if item.strip()]
    mapa = {beat["beat_id"]: beat for beat in beats}
    ausentes = [beat_id for beat_id in ids if beat_id not in mapa]
    if ausentes:
        raise SystemExit(f"Beat(s) não encontrado(s): {', '.join(ausentes)}")
    return [mapa[beat_id] for beat_id in ids]


def normalizar_palavra(valor: str) -> str:
    decomposed = unicodedata.normalize("NFKD", valor.casefold())
    sem_acentos = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in sem_acentos if char.isalnum())


def palavras_com_timing(
    texto: str,
    timings: list,
    *,
    offset: float,
    indice_global: int,
) -> list[dict]:
    tokens = re.findall(r"\S+", texto)
    grupos: list[list] = []
    atual: list = []
    for timing in timings:
        if timing.phoneme.isspace():
            if atual:
                grupos.append(atual)
                atual = []
            continue
        atual.append(timing)
    if atual:
        grupos.append(atual)
    if len(tokens) != len(grupos):
        raise RuntimeError(
            "Não foi possível alinhar palavras e fonemas: "
            f"{len(tokens)} palavra(s), {len(grupos)} grupo(s)."
        )
    palavras = []
    for indice, (token, grupo) in enumerate(zip(tokens, grupos), start=1):
        palavras.append(
            {
                "index": indice_global + indice - 1,
                "beat_word_index": indice,
                "text": token,
                "normalized": normalizar_palavra(token),
                "start": round(offset + float(grupo[0].start), 4),
                "end": round(offset + float(grupo[-1].end), 4),
            }
        )
    return palavras


def quebrar_bloco(bloco: str, limite: int) -> list[str]:
    frases = re.split(r"(?<=[.!?…])\s+", bloco.strip())
    trechos: list[str] = []
    atual = ""

    def adicionar(parte: str) -> None:
        nonlocal atual
        candidato = f"{atual} {parte}".strip()
        if atual and len(candidato) > limite:
            trechos.append(atual)
            atual = parte
        else:
            atual = candidato

    for frase in frases:
        frase = frase.strip()
        if not frase:
            continue
        if len(frase) <= limite:
            adicionar(frase)
            continue

        partes = re.split(r"(?<=[,;:—])\s+", frase)
        for parte in partes:
            if len(parte) <= limite:
                adicionar(parte)
                continue
            palavras = parte.split()
            pedaco = ""
            for palavra in palavras:
                candidato = f"{pedaco} {palavra}".strip()
                if pedaco and len(candidato) > limite:
                    adicionar(pedaco)
                    pedaco = palavra
                else:
                    pedaco = candidato
            if pedaco:
                adicionar(pedaco)

    if atual:
        trechos.append(atual)
    return trechos


def segmentar(texto: str, limite: int) -> list[tuple[str, bool]]:
    paragrafos = [p.replace("\n", " ").strip() for p in texto.split("\n\n")]
    resultado: list[tuple[str, bool]] = []
    for paragrafo in (p for p in paragrafos if p):
        trechos = quebrar_bloco(paragrafo, limite)
        for indice, trecho in enumerate(trechos):
            resultado.append((trecho, indice == len(trechos) - 1))
    return resultado


def silencio(duracao_ms: int, taxa: int) -> np.ndarray:
    quantidade = max(0, round(taxa * duracao_ms / 1000))
    return np.zeros(quantidade, dtype=np.float32)


def argumentos(config: dict) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera WAV local em português brasileiro com Kokoro ONNX."
    )
    entrada = parser.add_mutually_exclusive_group()
    entrada.add_argument("--entrada", type=Path, help="Arquivo TXT/MD em UTF-8.")
    entrada.add_argument("--texto", help="Texto curto informado diretamente.")
    parser.add_argument("--saida", type=Path, help="Arquivo WAV de destino.")
    parser.add_argument(
        "--voz",
        choices=sorted(config["vozes_permitidas"]),
        default=config["voz_padrao"],
        help="Voz masculina autorizada.",
    )
    parser.add_argument(
        "--velocidade",
        type=float,
        default=float(config["velocidade_padrao"]),
        help="Velocidade de fala; recomendado entre 0.90 e 1.05.",
    )
    parser.add_argument(
        "--listar-vozes", action="store_true", help="Lista as vozes permitidas e encerra."
    )
    parser.add_argument(
        "--timing-json",
        type=Path,
        help="Gera o contrato 03A_AUDIO_TIMING.json junto com o WAV.",
    )
    parser.add_argument(
        "--beats",
        help="IDs de beat separados por vírgula. Requer roteiro Markdown com seções ### B001.",
    )
    parser.add_argument(
        "--episodio-id",
        help="ID registrado no timing; quando omitido, tenta ler episodio.json ao lado da entrada.",
    )
    return parser.parse_args()


def main() -> int:
    config = carregar_config()
    args = argumentos(config)

    if args.listar_vozes:
        for apelido, identificador in config["vozes_permitidas"].items():
            padrao = " (padrão)" if apelido == config["voz_padrao"] else ""
            print(f"{apelido}: {identificador}{padrao}")
        return 0

    if not 0.75 <= args.velocidade <= 1.25:
        raise SystemExit("A velocidade deve estar entre 0.75 e 1.25.")
    if not args.entrada and not args.texto:
        raise SystemExit("Informe --entrada ou --texto.")
    if not args.saida:
        raise SystemExit("Informe --saida com extensão .wav.")
    if args.saida.suffix.lower() != ".wav":
        raise SystemExit("A saída deve usar a extensão .wav.")

    entrada: Path | None = None
    if args.entrada:
        entrada = caminho_do_projeto(str(args.entrada))
        if not entrada.is_file():
            raise SystemExit(f"Arquivo de entrada não encontrado: {entrada}")
        texto_fonte = entrada.read_text(encoding="utf-8-sig")
    else:
        texto_fonte = args.texto

    beats = extrair_beats_markdown(texto_fonte) if entrada and entrada.suffix.lower() == ".md" else []
    if args.beats and not beats:
        raise SystemExit("--beats requer um Markdown com seções ### B001 e narração em blockquote.")
    beats = selecionar_beats(beats, args.beats)
    texto = limpar_texto("\n\n".join(beat["text"] for beat in beats) if beats else texto_fonte)
    if not texto:
        raise SystemExit("O texto está vazio.")

    modelo = caminho_do_projeto(config["modelo"])
    vozes = caminho_do_projeto(config["banco_de_vozes"])
    for arquivo in (modelo, vozes):
        if not arquivo.is_file():
            raise SystemExit(f"Dependência não encontrada: {arquivo}")

    voz = config["vozes_permitidas"][args.voz]
    kokoro = Kokoro(str(modelo), str(vozes))
    if voz not in kokoro.get_voices():
        raise SystemExit(f"A voz {voz} não existe no banco instalado.")

    g2p = EspeakG2P(language=config["idioma"])
    audios: list[np.ndarray] = []
    taxa_final: int | None = None
    timing_beats: list[dict] = []
    timing_pauses: list[dict] = []
    indice_global = 1

    if args.timing_json:
        unidades = beats or [{"beat_id": "B001", "title": "narração", "text": texto}]
        print(f"Gerando {len(unidades)} beat(s) cronometrado(s) com {voz}...")
        cursor = 0.0
        pausa_ms = int(config["pausa_entre_trechos_ms"])
        for indice, beat in enumerate(unidades, start=1):
            fonemas, _ = g2p(beat["text"])
            amostras, taxa, timings = kokoro.create_timed(
                fonemas, voice=voz, speed=args.velocidade, is_phonemes=True
            )
            if not timings:
                raise RuntimeError("O modelo Kokoro não retornou timings de fonema.")
            taxa_final = taxa
            trecho_audio = np.asarray(amostras, dtype=np.float32)
            audios.append(trecho_audio)
            palavras = palavras_com_timing(
                beat["text"], timings, offset=cursor, indice_global=indice_global
            )
            indice_global += len(palavras)
            duracao_trecho = len(trecho_audio) / taxa
            timing_beats.append(
                {
                    "beat_id": beat["beat_id"],
                    "title": beat["title"],
                    "text": beat["text"],
                    "start": round(cursor, 4),
                    "speech_start": palavras[0]["start"],
                    "speech_end": palavras[-1]["end"],
                    "end": round(cursor + duracao_trecho, 4),
                    "words": palavras,
                }
            )
            cursor += duracao_trecho
            if indice < len(unidades):
                pausa_inicio = cursor
                pausa = silencio(pausa_ms, taxa)
                audios.append(pausa)
                cursor += len(pausa) / taxa
                timing_pauses.append(
                    {
                        "after_beat_id": beat["beat_id"],
                        "start": round(pausa_inicio, 4),
                        "end": round(cursor, 4),
                        "duration_ms": pausa_ms,
                        "source": "config.pausa_entre_trechos_ms",
                    }
                )
            print(f"  [{indice}/{len(unidades)}] {beat['beat_id']} — {beat['text'][:64]}")
    else:
        trechos = segmentar(texto, int(config["maximo_caracteres_por_trecho"]))
        print(f"Gerando {len(trechos)} trecho(s) com {voz}...")
        for indice, (trecho, fim_de_paragrafo) in enumerate(trechos, start=1):
            fonemas, _ = g2p(trecho)
            amostras, taxa = kokoro.create(
                fonemas, voice=voz, speed=args.velocidade, is_phonemes=True
            )
            taxa_final = taxa
            audios.append(np.asarray(amostras, dtype=np.float32))
            if indice < len(trechos):
                chave = (
                    "pausa_entre_paragrafos_ms"
                    if fim_de_paragrafo
                    else "pausa_entre_trechos_ms"
                )
                audios.append(silencio(int(config[chave]), taxa))
            print(f"  [{indice}/{len(trechos)}] {trecho[:72]}")

    if taxa_final is None or not audios:
        raise SystemExit("Nenhum áudio foi produzido.")

    saida = caminho_do_projeto(str(args.saida))
    saida.parent.mkdir(parents=True, exist_ok=True)
    audio = np.concatenate(audios)
    sf.write(saida, audio, taxa_final, subtype="PCM_16")
    duracao = len(audio) / taxa_final
    if args.timing_json:
        episodio_id = args.episodio_id
        if not episodio_id and entrada:
            metadata_path = entrada.parent / "episodio.json"
            if metadata_path.is_file():
                episodio_id = json.loads(metadata_path.read_text(encoding="utf-8-sig")).get(
                    "episodio_id"
                )
        timing_path = caminho_do_projeto(str(args.timing_json))
        timing_path.parent.mkdir(parents=True, exist_ok=True)
        source_path = None
        source_sha256 = None
        if entrada:
            try:
                source_path = entrada.relative_to(ROOT).as_posix()
            except ValueError:
                source_path = str(entrada)
            source_sha256 = hashlib.sha256(entrada.read_bytes()).hexdigest()
        try:
            audio_path = saida.relative_to(ROOT).as_posix()
        except ValueError:
            audio_path = str(saida)
        contrato = {
            "schema_version": "1.0",
            "episode_id": episodio_id,
            "scope": "selected_beats" if args.beats else "full_input",
            "provider": "kokoro_onnx",
            "voice": voz,
            "speed": args.velocidade,
            "language": config["idioma"],
            "timing_method": "kokoro_create_timed_duration_output",
            "timing_level": "phoneme_native_word_derived",
            "source_file": source_path,
            "source_sha256": source_sha256,
            "text_sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
            "audio_file": audio_path,
            "audio_sha256": hashlib.sha256(saida.read_bytes()).hexdigest(),
            "sample_rate": taxa_final,
            "duration_seconds": round(duracao, 4),
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "beats": timing_beats,
            "pauses": timing_pauses,
        }
        timing_path.write_text(
            json.dumps(contrato, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"Timing: {timing_path}")
    print(f"Concluído: {saida}")
    print(f"Duração: {duracao:.1f}s | Taxa: {taxa_final} Hz | Voz: {voz}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
