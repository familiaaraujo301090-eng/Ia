#!/usr/bin/env python3
"""Som do filme, todo sintetizado: drone de cordas graves, relógio de woodblock, frame drum nos cortes,
faca na madeira, papel, multidão, moedas, metal da chama, pena no pergaminho. Voz por cima, com ducking."""
import json
import numpy as np
import soundfile as sf

SR = 48000
ev = json.load(open('events.json'))
DUR = ev['dur']
EV = ev['ev']
TL = json.loads(open('timeline.js').read().split('=', 1)[1].rstrip().rstrip(';'))
starts = [p['t'] for p in TL['plates']]
N = int((DUR + 0.5) * SR)
rng = np.random.default_rng(7)
t = np.arange(N) / SR


def add(buf, x, at, g=1.0, pan=0.0):
    i = int(at * SR)
    if i >= N or i + len(x) <= 0:
        return
    x = x[: N - i] * g
    L, R = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    buf[i:i + len(x), 0] += x * L
    buf[i:i + len(x), 1] += x * R


def bp(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = 1 / (1 + (lo / np.maximum(f, 1)) ** 4) / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * g, len(x))


def env(n, a=0.002, d=0.3):
    k = np.arange(n) / SR
    return np.minimum(1, k / a) * np.exp(-k / d)


def modal(freqs, decs, amps, dur):
    k = np.arange(int(dur * SR)) / SR
    out = sum(a * np.sin(2 * np.pi * f * k) * np.exp(-k / d) for f, d, a in zip(freqs, decs, amps))
    hit = bp(rng.standard_normal(len(k)), 1500, 9000) * np.exp(-k / 0.004) * 0.3
    return out + hit


music = np.zeros((N, 2))
foley = np.zeros((N, 2))

# ---- drone de contrabaixo / violoncelo (serra filtrada, desafinada) ----
def bowed(freq, dur, g=1.0):
    k = np.arange(int(dur * SR)) / SR
    x = np.zeros_like(k)
    for det in (-0.25, 0.0, 0.3):
        f = freq * 2 ** (det / 12 / 4)
        ph = (k * f + 0.003 * np.sin(2 * np.pi * 5.1 * k)) % 1
        x += (2 * ph - 1)
    x = bp(x, 35, 900)
    a = np.minimum(1, k / 1.2) * np.minimum(1, (dur - k) / 1.0)
    return x * a * g / 3

D2, A1, F2, C2, E2 = 73.42, 55.0, 87.31, 65.41, 82.41
# uma nota por prancha; some na prancha 5 (silêncio) e volta suave na 6
notes = [(D2, 0.7), (D2, 0.8), (A1 * 2, 0.9), (F2, 0.9), (A1, 0.8), (None, 0), (D2, 0.55), (F2, 0.5)]
for i, (f, g) in enumerate(notes):
    if not f:
        continue
    a = starts[i]
    b = starts[i + 1] if i + 1 < len(starts) else DUR
    if i == 4:
        b = starts[5] - 1.4          # o drone morre antes do silêncio
    add(music, bowed(f, b - a + 1.0), a, 0.32 * g, -0.2)
    add(music, bowed(f * 1.5, b - a + 1.0), a, 0.13 * g, 0.25)
# pizzicato grave ao fim (resolução)
for k, f in enumerate([D2 * 2, A1 * 2, D2 * 2]):
    add(music, modal([f, f * 2.01, f * 3.02], [0.6, 0.35, 0.2], [1, 0.4, 0.15], 2.0), starts[7] + 1.0 + k * 1.6, 0.35)

# ---- relógio: woodblock que acelera de 9h a 15h e para no pôr do sol ----
def woodblock(hi=False):
    f0 = 1150 if hi else 820
    return modal([f0, f0 * 2.7, f0 * 4.1], [0.05, 0.03, 0.02], [1, 0.4, 0.2], 0.18)

tick_t = []
x = starts[1] + 0.4
while x < starts[5] - 2.2:
    tick_t.append(x)
    if x < starts[2]:
        rate = 1.3
    elif x < starts[3]:
        rate = 1.9
    elif x < starts[4]:
        rate = 2.6
    else:
        rate = max(0.7, 2.6 - (x - starts[4]) * 0.45)
    x += 1 / rate
for k, x in enumerate(tick_t):
    add(foley, woodblock(k % 2 == 0), x, 0.28, -0.35 if k % 2 else 0.35)
add(foley, woodblock(True), TL['sents'][-2]['a'] - 0.3, 0.32)   # um último tique na pergunta final

# ---- frame drum nas impressões e gran cassa nas folhas ----
def drum(freq=72, dec=0.5):
    k = np.arange(int(1.2 * SR)) / SR
    f = freq * (1 + 0.6 * np.exp(-k / 0.03))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-k / dec)
    skin = bp(rng.standard_normal(len(k)), 120, 1800) * np.exp(-k / 0.03) * 0.5
    return body + skin

def paper(dur=0.9):
    n = int(dur * SR)
    k = np.arange(n) / SR
    x = bp(rng.standard_normal(n), 900, 7000) * np.sin(np.pi * k / dur) ** 1.5
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * 9 * k)
    return x

def knife(n_cuts, dur):
    out = np.zeros(int(dur * SR) + SR)
    times = np.sort(rng.random(n_cuts)) ** 1.3 * dur
    for c in times:
        m = int((0.05 + rng.random() * 0.12) * SR)
        k = np.arange(m) / SR
        s = bp(rng.standard_normal(m), 1800 + rng.random() * 2500, 7500) * np.exp(-k / 0.04) * (0.4 + rng.random() * 0.6)
        s[:40] += rng.standard_normal(40) * 0.8
        i = int(c * SR)
        out[i:i + m] += s
    return out

for e in EV:
    if e['type'] == 'impression':
        add(foley, drum(70, 0.45), e['t'], 0.55)
    elif e['type'] == 'peel':
        add(foley, paper(0.95), e['t'], 0.4, 0.15)
        add(foley, drum(58, 0.7), e['t'] + 0.55, 0.45)
    elif e['type'] == 'first':
        add(foley, drum(52, 0.9), 0.02, 0.6)
    elif e['type'] == 'carve':
        add(foley, knife(int(28 * e['d']), e['d']), e['t'], 0.16, rng.uniform(-0.3, 0.3))

# ---- ambiências ----
murmur = bp(rng.standard_normal(N), 250, 1400)
mur_env = np.zeros(N)
def span(a, b, g, fade=0.6):
    i, j = int(a * SR), int(b * SR)
    k = np.arange(j - i) / SR
    mur_env[i:j] += g * np.minimum(1, k / fade) * np.minimum(1, (b - a - k) / fade)
span(starts[1], starts[2], 0.10)
span(starts[2], starts[3], 0.16)
foley[:, 0] += murmur * mur_env
foley[:, 1] += np.roll(murmur, 997) * mur_env
# o rugido da multidão no "mais alto"
roar_t = next(e['t'] for e in EV if e['type'] == 'roar')
n = int(2.6 * SR); k = np.arange(n) / SR
roar = bp(rng.standard_normal(n), 300, 2600) * np.minimum(1, k / 0.15) * np.exp(-np.maximum(0, k - 0.5) / 0.9)
add(foley, roar, roar_t, 0.5)
add(foley, drum(48, 1.0), roar_t, 0.5)
# vento no pôr do sol
n = int((starts[5] - starts[4]) * SR); k = np.arange(n) / SR
wind = bp(rng.standard_normal(n), 120, 900) * (0.6 + 0.4 * np.sin(2 * np.pi * k / 3.7)) * np.minimum(1, k / 1.5) * np.minimum(1, (k[-1] - k) / 1.5)
add(foley, wind, starts[4], 0.12)
# tam-tam: o sol cai
tam = modal([96, 151, 203, 287, 344, 470], [3.5, 3.0, 2.5, 2.0, 1.6, 1.2], [1, 0.8, 0.7, 0.5, 0.4, 0.3], 6.0)
add(music, tam * np.minimum(1, np.arange(len(tam)) / SR / 0.25), starts[4] + 0.05, 0.22)

# ---- moedas, chama, pena ----
co = next(e for e in EV if e['type'] == 'coins')
for c in np.sort(rng.random(7)) * co['d']:
    f0 = 2600 + rng.random() * 1400
    add(foley, modal([f0, f0 * 1.52, f0 * 2.31], [0.25, 0.18, 0.1], [1, 0.6, 0.3], 0.6), co['t'] + c, 0.12, 0.3)
ig = next(e['t'] for e in EV if e['type'] == 'ignite')
add(music, modal([220, 593, 1104, 1690], [4.0, 2.6, 1.6, 1.0], [1, 0.6, 0.35, 0.2], 6.0), ig, 0.3)   # o primeiro som depois do silêncio
n = int(0.5 * SR); k = np.arange(n) / SR
add(foley, bp(rng.standard_normal(n), 200, 3000) * np.minimum(1, k / 0.05) * np.exp(-k / 0.18), ig, 0.25)
n = int((DUR - starts[5]) * SR)
crackle = np.zeros(n)
for c in rng.random(int(n / SR * 9)) * n:
    i = int(c); m = 120
    crackle[i:i + m] += rng.standard_normal(min(m, n - i)) * np.exp(-np.arange(min(m, n - i)) / 25)
add(foley, bp(crackle, 1500, 8000), starts[5] + 0.3, 0.05)
wr = next(e for e in EV if e['type'] == 'write')
for c in np.arange(0, wr['d'], 0.11):
    m = int(0.07 * SR); k = np.arange(m) / SR
    add(foley, bp(rng.standard_normal(m), 2500, 9000) * np.sin(np.pi * k / 0.07), wr['t'] + c + rng.random() * 0.04, 0.05, 0.4)

# ---- voz e mixagem ----
voz, vsr = sf.read('narracao.wav', always_2d=True)
voz = voz.mean(axis=1)
if vsr != SR:
    import soxr
    voz = soxr.resample(voz, vsr, SR)
v = np.zeros(N); v[:min(N, len(voz))] = voz[:N]
# compressão simples da voz
e_v = np.sqrt(np.convolve(v ** 2, np.ones(960) / 960, 'same'))
gain = np.where(e_v > 0.08, (0.08 / np.maximum(e_v, 1e-6)) ** 0.5, 1.0)
v = v * gain
voice_env = np.convolve((e_v > 0.01).astype(float), np.ones(SR // 5) / (SR // 5), 'same')
duck_m = 1 - 0.6 * np.clip(voice_env, 0, 1)
duck_f = 1 - 0.35 * np.clip(voice_env, 0, 1)
rms = lambda x: np.sqrt(np.mean(x ** 2) + 1e-12)
vg = 1.0 / rms(v[np.abs(v) > 0.01])
music *= 0.32 / max(rms(music), 1e-6) * 0.08
foley *= 0.22 / max(rms(foley), 1e-6) * 0.09
# silêncio real antes da chama: música e efeitos caem a zero (a voz continua)
i0, i1 = int((ig - 1.15) * SR), int((ig - 0.02) * SR)
fade = np.ones(N); fade[i0 - 2400:i0] = np.linspace(1, 0, 2400); fade[i0:i1] = 0
mix = (music * duck_m[:, None] + foley * duck_f[:, None]) * fade[:, None]
mix[:, 0] += v * vg * 0.12
mix[:, 1] += v * vg * 0.12
mix /= max(1.0, np.max(np.abs(mix)) / 0.95)
sf.write('out/mix.wav', mix.astype(np.float32), SR)
print('mix ok', round(N / SR, 2), 's')
