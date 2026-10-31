# Gerador da narração

Vozes neurais abertas, rodando localmente com [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx):

- **Kokoro v1.0** (recomendado): `dora` (feminina), `alex` e `santa` (masculinas)
- **Piper** (alternativa): `dii-high`, `cadu-medium`, `jeff-medium`, `faber-medium`

## Preparar

```bash
python3 -m venv venv
./venv/bin/pip install "sherpa-onnx==1.12.40" soundfile numpy
# modelo Kokoro (cerca de 350 MB)
curl -L -O https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_0.tar.bz2
tar xjf kokoro-multi-lang-v1_0.tar.bz2
```

Também é preciso ter o `ffmpeg` instalado.

## Gerar

```bash
./venv/bin/python gerar_narracao.py dora saida/dora           # todas as falas
./venv/bin/python gerar_narracao.py alex saida/alex principal-02-papel   # só uma fala
```

Os textos, a velocidade de cada fala e as pausas ficam no dicionário `FALAS` no início do script.
O tratamento (equalização, compressão, sala e volume em -18 LUFS) fica na variável `chain`.

## Testar a clareza

`testar_com_whisper.py` transcreve as falas com o Whisper e mede o erro em relação ao roteiro.
Precisa do modelo `sherpa-onnx-whisper-small` (release `asr-models` do sherpa-onnx).
