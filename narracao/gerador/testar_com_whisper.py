# Transcreve cada fala com o Whisper e mede quanto bate com o roteiro (WER)
import sys, glob, subprocess, numpy as np, sherpa_onnx, re, unicodedata
REF = {
 "principal-01-entrada": "Vellaro Design.",
 "principal-02-papel": "Tudo começa no papel. Antes da madeira, vem o traço. Cada móvel é desenhado para o seu espaço, linha por linha.",
 "principal-03-medida": "Cada medida importa. Medimos o ambiente com precisão para que o móvel encaixe ao milímetro.",
 "principal-04-volume": "O desenho ganha volume. Profundidade, nichos, portas e encaixes são definidos antes do primeiro corte.",
 "principal-05-acabamento": "Madeira, pedra, metal e luz. Ripado de madeira, mármore, detalhes em latão e iluminação embutida. Acabamento de alto padrão em cada peça.",
 "principal-06-final": "Seu espaço. Seu estilo. A Vellaro Design cria móveis sob medida com identidade: cozinhas, closets, salas, banheiros e ambientes completos, do projeto à montagem.",
}
w = "sherpa-onnx-whisper-small"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{w}/small-encoder.int8.onnx", decoder=f"{w}/small-decoder.int8.onnx",
                                                tokens=f"{w}/small-tokens.txt", language="pt", task="transcribe", num_threads=4)
def norm(t):
    t = unicodedata.normalize("NFD", t.lower()); t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", t).split()
def wer(r, h):
    d = np.arange(len(h) + 1)
    for i, rw in enumerate(r, 1):
        prev, d[0] = d.copy(), i
        for j, hw in enumerate(h, 1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (rw != hw))
    return d[len(h)] / max(1, len(r))
for voice in sys.argv[1:]:
    errs = []
    for f in sorted(glob.glob(f"out/{voice}/*.mp3")):
        if "01-entrada" in f: continue
        name = f.split("/")[-1][:-4]
        pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
        x = np.frombuffer(pcm, dtype=np.float32)
        s = rec.create_stream(); s.accept_waveform(16000, x); rec.decode_stream(s)
        hyp = s.result.text.strip()
        e = wer(norm(REF[name]), norm(hyp)); errs.append(e)
        print(f"{voice:7} {name:24} erro {e*100:5.1f}%  | {hyp}")
    print(f"== {voice}: erro médio {np.mean(errs)*100:.1f}%\n")
