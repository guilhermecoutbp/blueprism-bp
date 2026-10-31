# Gera a narração do site principal: cada fala em trechos, com as pausas do roteiro
import sys, glob, subprocess, os, numpy as np, soundfile as sf, sherpa_onnx

FALAS = {
    "principal-01-entrada": (0.80, [["Vellaro Design."]]),
    "principal-02-papel": (0.86, [["Tudo começa no papel."], ["Antes da madeira, vem o traço.", "Cada móvel é desenhado para o seu espaço, linha por linha."]]),
    "principal-03-medida": (0.86, [["Cada medida importa."], ["Medimos o ambiente com precisão, para que o móvel encaixe, ao milímetro."]]),
    "principal-04-volume": (0.86, [["O desenho ganha volume."], ["Profundidade, nichos, portas e encaixes, são definidos antes do primeiro corte."]]),
    "principal-05-acabamento": (0.86, [["Madeira, pedra, metal, e luz."], ["Ripado de madeira, mármore, detalhes em latão, e iluminação embutida.", "Acabamento de alto padrão, em cada peça."]]),
    "principal-06-final": (0.86, [["Seu espaço.", "Seu estilo."], ["A Vellaro Design cria móveis sob medida com identidade:", "cozinhas, clósets, salas, banheiros, e ambientes completos,", "do projeto à montagem."]]),
}
SHORT, LONG = 0.32, 0.75  # pausa entre frases e pausa longa (//)

voice, outdir = sys.argv[1], sys.argv[2]
only = sys.argv[3:] or list(FALAS)
KOKORO = {"dora": 42, "alex": 43, "santa": 44}
os.makedirs(outdir, exist_ok=True)
tts_cache = {}

def engine(speed):
    if speed in tts_cache: return tts_cache[speed]
    if voice in KOKORO:
        k = "kokoro-multi-lang-v1_0"
        model = sherpa_onnx.OfflineTtsModelConfig(kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
            model=f"{k}/model.onnx", voices=f"{k}/voices.bin", tokens=f"{k}/tokens.txt",
            data_dir=f"{k}/espeak-ng-data", length_scale=1.0 / speed, lang="pt-br"), num_threads=4)
    else:
        d = f"vits-piper-pt_BR-{voice}"
        onnx = glob.glob(f"{d}/*.onnx")[0]
        model = sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(
            model=onnx, tokens=f"{d}/tokens.txt", data_dir=f"{d}/espeak-ng-data",
            length_scale=1.0 / speed, noise_scale=0.6, noise_scale_w=0.75), num_threads=4)
    tts_cache[speed] = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=model))
    return tts_cache[speed]

def synth(text, speed):
    a = engine(speed).generate(text, sid=KOKORO.get(voice, 0), speed=1.0)
    x = np.array(a.samples, dtype=np.float32)
    # apara silêncio das pontas
    idx = np.where(np.abs(x) > 0.01)[0]
    if len(idx): x = x[max(0, idx[0] - 200): idx[-1] + 800]
    return x, a.sample_rate

for name in only:
    speed, blocks = FALAS[name]
    parts, sr = [], 22050
    for bi, block in enumerate(blocks):
        for si, sentence in enumerate(block):
            x, sr = synth(sentence, speed)
            parts.append(x)
            if si < len(block) - 1: parts.append(np.zeros(int(SHORT * sr), np.float32))
        if bi < len(blocks) - 1: parts.append(np.zeros(int(LONG * sr), np.float32))
    audio = np.concatenate([np.zeros(int(0.12 * sr), np.float32), *parts, np.zeros(int(0.45 * sr), np.float32)])
    raw = f"{outdir}/{name}.raw.wav"
    sf.write(raw, audio, sr)
    # Tratamento de estúdio: calor, menos aspereza, sem "s" chiado, compressão leve, sala discreta e volume padrão
    chain = ",".join([
        "aresample=44100:resampler=soxr",
        "highpass=f=70",
        "equalizer=f=170:t=q:w=0.9:g=2.2",
        "equalizer=f=3300:t=q:w=1.2:g=-2.5",
        "equalizer=f=9500:t=q:w=0.8:g=1.2",
        "deesser=i=0.35",
        "acompressor=threshold=-21dB:ratio=2.4:attack=12:release=140:makeup=2",
        "aecho=0.85:0.75:22|41:0.11|0.07",
        "loudnorm=I=-18:TP=-1.5:LRA=7",
        "afade=t=in:d=0.04",
        f"areverse,afade=t=in:d=0.3,areverse",
    ])
    out = f"{outdir}/{name}.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", chain, "-ac", "1", "-ar", "44100", "-b:a", "96k", out], check=True)
    os.remove(raw)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
    print(voice, name, f"{dur:.1f}s")
