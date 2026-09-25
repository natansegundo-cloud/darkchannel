# {{EPISODIO_ID}} — Roteiro de narração

## Contrato editorial

- Os horários são estimativas editoriais, nunca o contrato técnico do vídeo.
- Cada ideia falada recebe um `beat_id` estável (`B001`, `B002`...).
- Depois da aprovação, um ID não é reutilizado. Beats removidos são marcados como aposentados.
- A narração de cada beat fica em blockquote. O gerador de voz lê apenas essas linhas.
- O áudio final gera automaticamente `03A_AUDIO_TIMING.json`.

## Título de produção

{{EPISODIO_TITULO}}

## Beats

### B001 — {{TITULO_B001}}

- **Janela editorial estimada:** {{JANELA_B001}}
- **Função:** {{FUNCAO_B001}}
- **Payoff:** {{PAYOFF_B001}}
- **Claims:** {{CLAIMS_B001}}
- **Ênfase:** {{ENFASE_B001}}
- **Pausa:** {{PAUSA_B001}}

> {{NARRACAO_B001}}

### B002 — {{TITULO_B002}}

- **Janela editorial estimada:** {{JANELA_B002}}
- **Função:** {{FUNCAO_B002}}
- **Payoff:** {{PAYOFF_B002}}
- **Claims:** {{CLAIMS_B002}}
- **Ênfase:** {{ENFASE_B002}}
- **Pausa:** {{PAUSA_B002}}

> {{NARRACAO_B002}}

## Notas de locução

- Ritmo, intenção e pronúncias: {{NOTAS_LOCUCAO}}
- Provider inicial: Kokoro ONNX. A troca futura de provider não altera os contratos 03A, 04 ou 04A.

## Geração do áudio e timing

```powershell
python scripts/gerar_narracao_local.py --entrada "episodios/{{EPISODIO_ID}}-{{EPISODIO_SLUG}}/03_ROTEIRO_NARRACAO.md" --beats B001,B002 --saida "episodios/{{EPISODIO_ID}}-{{EPISODIO_SLUG}}/audio/narracao.wav" --timing-json "episodios/{{EPISODIO_ID}}-{{EPISODIO_SLUG}}/03A_AUDIO_TIMING.json" --episodio-id {{EPISODIO_ID}}
```
