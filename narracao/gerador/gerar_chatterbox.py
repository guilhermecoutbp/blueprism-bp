# Chatterbox frase a frase, com conferência automática pelo Whisper e nova tentativa se desandar
import sys, os, re, time, subprocess, unicodedata, numpy as np, torch, torchaudio as ta, sherpa_onnx
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
FALAS = {
    "principal-01-entrada": "Vellaro Design.",
    "principal-02-papel": "Tudo começa no papel. Antes da madeira, vem o traço. Cada móvel é desenhado para o seu espaço, linha por linha.",
    "principal-03-medida": "Cada medida importa. Medimos o ambiente com precisão, para que o móvel encaixe ao milímetro.",
    "principal-04-volume": "O desenho ganha volume. Profundidade, nichos, portas e encaixes são definidos antes do primeiro corte.",
    "principal-05-acabamento": "Madeira, pedra, metal e luz. Ripado de madeira, mármore, detalhes em latão e iluminação embutida. Acabamento de alto padrão em cada peça.",
    "principal-06-final": "Seu espaço. Seu estilo. A Vellaro Design cria móveis sob medida com identidade: cozinhas, closets, salas, banheiros e ambientes completos, do projeto à montagem.",
}
outdir, ref = sys.argv[1], (sys.argv[2] if sys.argv[2] != "-" else None)
exag, cfg, temp = float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
only = sys.argv[6:] or list(FALAS)
os.makedirs(outdir, exist_ok=True)
model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
w = "sherpa-onnx-whisper-small"
asr = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{w}/small-encoder.int8.onnx", decoder=f"{w}/small-decoder.int8.onnx",
                                                tokens=f"{w}/small-tokens.txt", language="pt", task="transcribe", num_threads=4)
def norm(t):
    t = unicodedata.normalize("NFD", t.lower()); t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", t).split()
def wer(r, h):
    d = np.arange(len(h) + 1)
    for i, rw in enumerate(r, 1):
        prev, d[0] = d.copy(), i
        for j, hw in enumerate(h, 1): d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (rw != hw))
    return d[len(h)] / max(1, len(r))
def transcribe(x, sr):
    y = ta.functional.resample(torch.from_numpy(x).unsqueeze(0), sr, 16000)[0].numpy()
    s = asr.create_stream(); s.accept_waveform(16000, y); asr.decode_stream(s); return s.result.text.strip()
def trim(x, thr=0.012):
    i = np.where(np.abs(x) > thr)[0]
    return x[max(0, i[0] - 240): i[-1] + 2400] if len(i) else x
def sentences(text):
    return [p.strip() for p in re.split(r"(?<=[.:])\s+", text) if p.strip()]
chain = ",".join(["aresample=44100:resampler=soxr", "highpass=f=70", "equalizer=f=180:t=q:w=0.9:g=1.2", "deesser=i=0.2",
                  "acompressor=threshold=-22dB:ratio=2:attack=15:release=160:makeup=1.5", "loudnorm=I=-18:TP=-1.5:LRA=7", "afade=t=in:d=0.03"])
for name in only:
    t0 = time.time(); pieces = []
    for sent in sentences(FALAS[name]):
        words = norm(sent); expected = 0.42 * len(words) + 0.5
        best = None
        for attempt in range(5):
            torch.manual_seed(11 + attempt * 101)
            x = model.generate(sent, language_id="pt", audio_prompt_path=ref, exaggeration=exag, cfg_weight=cfg, temperature=temp)[0].numpy()
            x = trim(x); dur = len(x) / model.sr
            hyp = transcribe(x, model.sr)
            # o nome Vellaro o Whisper não conhece: não conta como erro
            e = wer([w for w in words if w != "vellaro"], [w for w in norm(hyp) if not w.startswith("vel") and w not in ("avelar", "o") or w == "o" and "o" in words])
            ok = e <= 0.15 and dur <= expected * 1.7
            score = e + max(0, dur / expected - 1.3)
            if best is None or score < best[0]: best = (score, x, hyp, dur, e)
            print(f"  {name} | tentativa {attempt + 1} | {dur:.1f}s (esperado ~{expected:.1f}s) | erro {e*100:.0f}% | {hyp}", flush=True)
            if ok: break
        pieces += [best[1], np.zeros(int(0.2 * model.sr), np.float32)]
    audio = np.concatenate([np.zeros(int(0.12 * model.sr), np.float32), *pieces[:-1], np.zeros(int(0.45 * model.sr), np.float32)])
    raw = f"{outdir}/{name}.raw.wav"; ta.save(raw, torch.from_numpy(audio).unsqueeze(0), model.sr)
    out = f"{outdir}/{name}.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", chain, "-ac", "1", "-ar", "44100", "-b:a", "96k", out], check=True)
    os.remove(raw)
    print(f"{name}: {len(audio)/model.sr:.1f}s pronto em {time.time()-t0:.0f}s", flush=True)
