# Narração local — Capital Oculto

O projeto usa Kokoro ONNX em um ambiente Python isolado dentro de `.tts/`. O
Python padrão do Windows não é alterado e o áudio é processado localmente pela
CPU, sem consumo de créditos.

## Vozes autorizadas

- `santa` → `pm_santa` — voz oficial e padrão do canal.
- `alex` → `pm_alex` — voz masculina de contingência.

O gerador rejeita qualquer voz fora dessa lista.

## Teste rápido

```powershell
python scripts/gerar_narracao_local.py --texto "Dinheiro não muda apenas o que você compra. Ele muda o que você acredita merecer." --voz alex --saida "episodios/CO-001-por-que-ganhar-mais-nao-basta/audio/teste-alex.wav"
```

Troque `--voz alex` por `--voz santa` para gerar a segunda amostra.

## Gerar a partir de um arquivo

O arquivo de entrada deve conter somente o texto que será falado, sem títulos,
marcações de cena ou instruções para o narrador.

```powershell
python scripts/gerar_narracao_local.py --entrada "caminho/roteiro-limpo.txt" --voz alex --velocidade 0.95 --saida "caminho/narracao.wav"
```

O gerador divide textos longos automaticamente, aplica pausas entre parágrafos
e produz WAV mono em 24 kHz. A saída WAV evita instalar FFmpeg e pode ser
importada diretamente no editor.

## Gerar beats com timing real

Roteiros estruturados usam headings `### B001` e colocam a narração em blockquote. Com `--timing-json`, o gerador chama `create_timed()` e produz o WAV e o `03A_AUDIO_TIMING.json` na mesma execução:

```powershell
python scripts/gerar_narracao_local.py --entrada "episodios/CO-001-por-que-ganhar-mais-nao-basta/03_ROTEIRO_NARRACAO.md" --beats B001,B002,B003,B004,B005,B006 --saida "episodios/CO-001-por-que-ganhar-mais-nao-basta/testes/v3_sequencial_s001_s006/narracao_pipeline.wav" --timing-json "episodios/CO-001-por-que-ganhar-mais-nao-basta/03A_AUDIO_TIMING.json" --episodio-id CO-001
```

O JSON guarda os tempos nativos de fonema agrupados por palavra, hashes e pausas. Ele é gerado automaticamente e não deve ser editado.

O provider continua sendo Kokoro nesta etapa. Consulte `docs/PIPELINE_AUDIOVISUAL.md` antes de gerar ou resolver cenas.

## Ajustes

As configurações ficam em `config/voz_local.json`. Para preservar consistência
entre episódios, faça testes de velocidade em amostras curtas antes de alterar
o valor padrão. Não substitua a voz aprovada no meio de uma série.
