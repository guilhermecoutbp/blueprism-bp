# Trilha do vídeo: 75 BPM em ré maior, um acorde por compasso, tudo na mesma grade de tempos.
# Gera work/audio/trilha.wav (música + voz, com a música abaixando sob a voz).
import numpy as np
import wave
import subprocess

SR = 48000
DUR = 20.0
BEAT = 60 / 75  # 0,8 s
BAR = BEAT * 4  # 3,2 s
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def hz(note):
    names = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    name, octave = note[:-1], int(note[-1])
    return 440.0 * 2 ** ((names[name] + 12 * (octave + 1) - 69) / 12)


def env_adsr(n, a, r, sustain_len):
    e = np.ones(n)
    ai = min(n, int(a * SR))
    ri = int(r * SR)
    s = min(n, int(sustain_len * SR))
    e[:ai] = np.linspace(0, 1, ai)
    e[s : s + ri] = np.linspace(1, 0, min(ri, n - s))[: len(e[s : s + ri])]
    e[s + ri :] = 0
    return e


def place(buf, sig, start):
    i = int(start * SR)
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


# Acordes: Dmaj7, Bm7, Gmaj7, A6sus, Dmaj7, Gmaj7, D
CHORDS = [
    ["D3", "F#3", "A3", "C#4", "E4"],
    ["B2", "D3", "F#3", "A3", "D4"],
    ["G2", "B2", "D3", "F#3", "A3"],
    ["A2", "D3", "E3", "F#3", "B3"],
    ["D3", "F#3", "A3", "C#4", "E4"],
    ["G2", "B2", "D3", "F#3", "A3"],
    ["D3", "F#3", "A3", "D4", "E4"],
]
ROOTS = ["D2", "B1", "G1", "A1", "D2", "G1", "D2"]

pad = np.zeros(N)
bass = np.zeros(N)
for k, chord in enumerate(CHORDS):
    start = k * BAR
    length = min(BAR + 1.2, DUR - start)
    if length <= 0:
        continue
    n = int(length * SR)
    tt = np.arange(n) / SR
    e = env_adsr(n, 0.9 if k else 1.6, 1.2, max(0.1, length - 1.2))
    for note in chord:
        f = hz(note)
        for det in (-0.12, 0.12):  # leve desafinação: coro suave
            ph = rng.uniform(0, 2 * np.pi)
            v = (np.sin(2 * np.pi * f * (1 + det / 100) * tt + ph)
                 + 0.32 * np.sin(2 * np.pi * 2 * f * tt + ph)
                 + 0.12 * np.sin(2 * np.pi * 3 * f * tt + ph))
            pad[int(start * SR): int(start * SR) + n] += 0.035 * v * e
    # baixo no início do compasso
    fb = hz(ROOTS[k])
    nb = int(min(BAR, DUR - start) * SR)
    tb = np.arange(nb) / SR
    eb = np.minimum(1, tb / 0.05) * np.exp(-tb / 1.6)
    place(bass, 0.075 * (np.sin(2 * np.pi * fb * tb) + 0.25 * np.sin(2 * np.pi * 2 * fb * tb)) * eb, start)

# respiração lenta do pad
pad *= 0.85 + 0.15 * np.sin(2 * np.pi * t / (BAR * 2))


def piano(note, amp=0.12, decay=1.5):
    f = hz(note)
    n = int(3.0 * SR)
    tt = np.arange(n) / SR
    e = np.minimum(1, tt / 0.004) * np.exp(-tt / decay)
    s = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt / 0.6) + 0.12 * np.sin(2 * np.pi * 3 * f * tt) * np.exp(-tt / 0.3)
    return amp * s * e


keys = np.zeros(N)
# notas do piano, sempre em cima de um tempo (número do tempo, nota)
MELODY = [
    (2, "A4"), (3, "F#4"),               # entrada: sob a voz, bem leve
    (4, "D5"), (6, "C#5"), (7, "A4"),    # compasso 2
    (8, "B4"), (10, "D5"), (11, "F#5"),  # compasso 3
    (12, "E5"), (14, "D5"), (15, "B4"),  # chegada do 3D
    (16, "A4"), (18, "C#5"), (19, "E5"),
    (20, "F#5"), (22, "D5"),             # fecho
]
for beat, note in MELODY:
    amp = 0.07 if beat < 4 else 0.11
    place(keys, piano(note, amp), beat * BEAT)

# swell enquanto o desenho sai do papel (pico no tempo 12 = 9,6 s): acorde agudo de ré crescendo
swell = np.zeros(N)
s0, s1 = 8.0, 9.6
n = int((s1 - s0 + 1.0) * SR)
tt = np.arange(n) / SR
rise = np.clip(tt / (s1 - s0), 0, 1) ** 2.2
fall = np.where(tt > (s1 - s0), np.exp(-(tt - (s1 - s0)) / 0.35), 1)
for note in ["D5", "A5", "F#5", "D6"]:
    swell_part = np.sin(2 * np.pi * hz(note) * tt + rng.uniform(0, 6)) * rise * fall
    place(swell, 0.03 * swell_part, s0)

# sino no fecho (tempo 23 = 18,4 s), em ré e lá
bell = np.zeros(N)
for note, amp in (("D6", 0.07), ("A5", 0.05)):
    f = hz(note)
    n = int(1.6 * SR)
    tt = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt / d) for r, a, d in ((1, 1, 1.1), (2.76, 0.35, 0.5), (5.4, 0.12, 0.25)))
    place(bell, amp * s * np.minimum(1, tt / 0.003), 23 * BEAT)

music = pad + bass + keys + swell + bell

# reverb de sala: ruído com decaimento exponencial, diferente em cada canal
def reverb(x, seconds=2.4, mix=0.32):
    n = int(seconds * SR)
    out = []
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR / (seconds / 6.9))
        ir /= np.sqrt(np.sum(ir ** 2))
        size = 1 << int(np.ceil(np.log2(len(x) + n)))
        wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
        out.append((1 - mix) * x + mix * wet)
    return np.stack(out, axis=1)


def read_wav(path):
    pcm = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(pcm, dtype=np.float32).astype(np.float64)


voice = np.zeros(N)
VOICES = [("audio/voz-entrada.wav", 2 * BEAT), ("audio/voz-seu-estilo.wav", 21 * BEAT)]
duck = np.ones(N)
for path, start in VOICES:
    v = read_wav(path)
    place(voice, v * 1.15, start)
    i, j = int(start * SR), int((start + len(v) / SR) * SR)
    duck[max(0, i - int(0.15 * SR)): min(N, j + int(0.25 * SR))] = 10 ** (-7 / 20)
# suaviza a abaixada da música
k = int(0.15 * SR)
duck = np.convolve(duck, np.ones(k) / k, mode="same")

mix = reverb(music * duck, mix=0.35) + reverb(voice, seconds=1.2, mix=0.1)
# entrada e saída suaves
fade = np.ones(N)
fade[: int(0.8 * SR)] = np.linspace(0, 1, int(0.8 * SR)) ** 2
fade[-int(1.4 * SR):] *= np.linspace(1, 0, int(1.4 * SR)) ** 1.5
mix *= fade[:, None]
mix /= np.max(np.abs(mix)) / 0.9

with wave.open("audio/trilha-bruta.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("trilha-bruta.wav", DUR, "s")
