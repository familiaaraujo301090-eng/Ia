"""Trilha e efeitos sonoros sintetizados por código (numpy), sem samples externos.

Gera dois WAV estéreo:
  musica.wav  batida pop/eletrônica animada; com "estilo": "energia", pop/house com sidechain,
              supersaw, melodia com eco, subida de tensão e pratos
  efeitos.wav whoosh nos cortes, "pop" nos selos, fita + torcida na chegada e "ding" no final

uso: python3 audio/trilha.py --info output/audio/timeline.json --out output/audio
"""
import argparse
import json
import os
import wave

import numpy as np

SR = 44100
rng = np.random.default_rng(1908)


def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    e = np.exp(-t / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def lowpass(x, k):
    k = max(1, int(k))
    return np.convolve(x, np.ones(k) / k, mode="same")


def place(buf, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i : i + len(sig), 0] += sig * gain * l * 1.414
    buf[i : i + len(sig), 1] += sig * gain * r * 1.414


def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def saw(f, n, harmonics=12, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for h in range(1, harmonics + 1):
        if f * h > SR / 2.5:
            break
        out += np.sin(2 * np.pi * f * h * t * (1 + detune)) / h
    return out


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.04)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, 0.001, 0.12) + 0.3 * rng.standard_normal(n) * env(n, 0.0005, 0.004)


def clap():
    n = int(0.25 * SR)
    x = np.diff(rng.standard_normal(n + 1))
    x = lowpass(x, 3)
    e = env(n, 0.001, 0.07)
    for k in (0.008, 0.016):
        e += 0.6 * np.roll(env(n, 0.001, 0.01), int(k * SR))
    return lowpass(x * e, 2) * 0.4


def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    x = np.diff(np.diff(rng.standard_normal(n + 2)))
    return x * env(n, 0.0005, 0.06 if open_ else 0.012) * 0.25


def musica(total, bpm):
    beat = 60 / bpm
    buf = np.zeros((int((total + 1) * SR), 2))
    # Lá menor - Fá - Dó - Sol (vi-IV-I-V), um acorde por compasso
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]
    bars = int(total / (beat * 4)) + 1
    k, c, h = kick(), clap(), hat()
    ho = hat(True)
    for b in range(bars):
        root, chord = prog[b % 4]
        t0 = b * 4 * beat
        intro = b == 0
        for s in range(16):  # semicolcheias
            t = t0 + s * beat / 4
            if t > total:
                break
            if s % 4 == 0 and not intro:
                place(buf, k, t, 0.9)
            if s in (4, 12) and not intro:
                place(buf, c, t, 0.55, 0.1)
            if s % 2 == 0:
                place(buf, ho if s % 4 == 2 else h, t, 0.16 if s % 4 == 2 else 0.1, -0.3)
            # baixo pulsando em colcheias
            if s % 2 == 0 and not intro:
                n = int(beat / 2 * SR)
                f = note_hz(root - 12 + (12 if s in (6, 14) else 0))
                place(buf, lowpass(saw(f, n, 8), 6) * env(n, 0.003, 0.12), t, 0.32)
            # acordes "stab" no contratempo
            if s in (2, 6, 10, 14):
                n = int(0.22 * SR)
                st = sum(saw(note_hz(m + 12), n, 10, d) for m in chord for d in (-0.004, 0.004))
                place(buf, lowpass(st, 4) * env(n, 0.004, 0.09), t, 0.05, 0.25 if s % 4 == 2 else -0.25)
            # arpejo suave
            if not intro:
                m = chord[(s + b) % 3] + 24
                n = int(0.12 * SR)
                tt = np.arange(n) / SR
                place(buf, np.sin(2 * np.pi * note_hz(m) * tt) * env(n, 0.002, 0.05), t, 0.06, 0.5 if s % 2 else -0.5)
    fade = int(1.5 * SR)
    end = int(total * SR)
    buf[end - fade : end] *= np.linspace(1, 0, fade)[:, None]
    buf[end:] = 0
    return buf[:end]


def supersaw(f, n, vozes=5, harmonics=10):
    out = np.zeros(n)
    for v in range(vozes):
        d = (v - (vozes - 1) / 2) * 0.006
        out += saw(f, n, harmonics, d)
    return out / vozes


def crash():
    n = int(1.8 * SR)
    x = np.diff(rng.standard_normal(n + 1))
    return lowpass(x, 2) * env(n, 0.001, 0.6) * 0.35


def riser(dur):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    for i, k in enumerate((40, 24, 14, 8, 4, 2)):  # filtro abrindo
        a, b = i * n // 6, (i + 1) * n // 6
        out[a:b] = lowpass(x, k)[a:b]
    return out * t ** 2 * 0.6


def musica_energia(total, bpm):
    """Pop/house animado: bumbo 4x4 com pad "respirando" (sidechain), baixo no
    contratempo, acordes supersaw, melodia em pluck com eco, palmas, chimbais,
    subida de tensão antes da entrada e prato a cada 8 compassos."""
    beat = 60 / bpm
    bar = beat * 4
    N = int((total + 2) * SR)
    drums = np.zeros((N, 2))
    musica_ = np.zeros((N, 2))
    # Fá - Sol - Lá menor - Dó (IV-V-vi-I em Dó maior): progressão alegre e "pra cima"
    prog = [(53, [57, 60, 65]), (55, [59, 62, 67]), (57, [60, 64, 69]), (48, [60, 64, 67])]
    intro = 2  # compassos sem bumbo
    bars = int(total / bar) + 1
    k, c, h, ho = kick(), clap(), hat(), hat(True)
    # envelope de sidechain: abaixa depois de cada bumbo
    duck = np.ones(N)
    for b in range(intro, bars):
        for q in range(4):
            i = int((b * bar + q * beat) * SR)
            n = int(beat * SR)
            seg = 1 - 0.65 * np.exp(-np.arange(n) / (0.09 * SR))
            duck[i : i + n] = seg[: max(0, min(n, N - i))]
    melodia = [0, 2, 1, 2, 0, 2, 1, 3, 0, 2, 1, 2, 2, 1, 0, 1]
    for b in range(bars):
        root, chord = prog[b % 4]
        t0 = b * bar
        cheio = b >= intro
        # pad supersaw sustentado o compasso inteiro
        n = int(bar * SR)
        pad = sum(supersaw(note_hz(m), n) for m in chord)
        pad = lowpass(pad, 3 if cheio else 7) * np.minimum(1, np.arange(n) / (0.05 * SR)) * env(n, 0.01, 3.0)
        place(musica_, pad, t0, 0.11 if cheio else 0.07, 0.0)
        for s in range(16):
            t = t0 + s * beat / 4
            if t > total:
                break
            if cheio:
                if s % 4 == 0:
                    place(drums, k, t, 1.0)
                if s in (4, 12):
                    place(drums, c, t, 0.6, 0.1)
                if s % 4 == 2:
                    place(drums, ho, t, 0.13, -0.3)
                elif s % 2 == 1:
                    place(drums, h, t, 0.07, 0.3)
                # baixo no contratempo
                if s % 4 == 2:
                    nb = int(beat / 2 * SR)
                    place(musica_, lowpass(saw(note_hz(root - 12), nb, 6), 5) * env(nb, 0.004, 0.16), t, 0.42)
            # melodia em pluck (entra no 3º compasso) com eco de 3/16
            if b >= intro and s % 2 == 0:
                m = chord[melodia[(s + b * 3) % 16] % 3] + 12 + (12 if melodia[s] == 3 else 0)
                npl = int(0.25 * SR)
                tt = np.arange(npl) / SR
                pl = (np.sin(2 * np.pi * note_hz(m) * tt) + 0.4 * np.sin(4 * np.pi * note_hz(m) * tt)) * env(npl, 0.002, 0.08)
                for e, g in ((0, 0.16), (3 * beat / 4, 0.07), (6 * beat / 4, 0.03)):
                    place(musica_, pl, t + e, g, (-0.4, 0.4, -0.2)[int(e / (3 * beat / 4)) % 3])
        if b == intro or (b > intro and (b - intro) % 8 == 0):
            place(drums, crash(), t0, 0.5, 0.2)
    # subida de tensão antes da batida entrar
    place(drums, riser(bar * intro * 0.9), bar * intro * 0.1, 0.5)
    mix = musica_ * duck[:, None] + drums
    mix = np.tanh(mix * 1.3) / 1.3  # saturação suave
    fade = int(1.5 * SR)
    end = int(total * SR)
    mix[end - fade : end] *= np.linspace(1, 0, fade)[:, None]
    return mix[:end]


def whoosh():
    n = int(0.45 * SR)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    for i, k in enumerate((40, 20, 10, 6, 10, 20)):  # varredura de filtro
        a, b = i * n // 6, (i + 1) * n // 6
        out[a:b] = lowpass(x, k)[a:b]
    t = np.linspace(0, 1, n)
    return out * np.sin(np.pi * t) ** 2 * 1.4


def pop():
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    f = 700 + 900 * (1 - np.exp(-t / 0.02))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.035)


def ding():
    n = int(1.5 * SR)
    t = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f * t) * w for f, w in ((1318.5, 1), (2637, 0.3), (1975.5, 0.25))) * env(n, 0.002, 0.45) * 0.5


def torcida(dur=3.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for _ in range(14):  # várias "vozes" de ruído modulado
        x = lowpass(rng.standard_normal(n), rng.integers(3, 9))
        am = 0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(3, 8) * t + rng.uniform(0, 6))
        out += x * am
    e = np.minimum(1, t / 0.3) * np.exp(-np.maximum(0, t - 1.2) / 0.8)
    return out / 14 * e * 2.2


def fita():
    n = int(0.08 * SR)
    return np.diff(rng.standard_normal(n + 1)) * env(n, 0.0005, 0.015)


def efeitos(info):
    total = info["total"]
    buf = np.zeros((int(total * SR) + SR, 2))
    for c in info["cenas"]:
        if c["inicio"] > 0:
            place(buf, whoosh(), c["inicio"] - 0.25, 0.35)
        place(buf, pop(), c["inicio"] + 0.12, 0.35)
    place(buf, fita(), info["fitaT"], 0.8)
    place(buf, torcida(), info["fitaT"] - 0.2, 0.55)
    place(buf, ding(), info["logoT"], 0.4)
    return buf[: int(total * SR)]


def salvar(path, buf):
    buf = np.clip(buf, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    info = json.load(open(a.info))
    os.makedirs(a.out, exist_ok=True)
    gerar = musica_energia if info.get("estilo") == "energia" else musica
    salvar(os.path.join(a.out, "musica.wav"), gerar(info["total"], info["bpm"]))
    salvar(os.path.join(a.out, "efeitos.wav"), efeitos(info))
    print("trilha ->", a.out)
