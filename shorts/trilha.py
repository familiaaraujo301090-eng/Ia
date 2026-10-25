#!/usr/bin/env python3
"""Compoe trilhas instrumentais livres de direitos, com o tempo exato de cada batida.

Uso:
    python trilha.py <clima> <segundos> saida.wav [--pausa SEGUNDO]

Climas (um para cada modelo de edicao, medidos nos videos virais de referencia):
    sombria  95 BPM  piano grave em menor, pulso de bumbo e tique (modelo gravura)
    epica    128 BPM tambores, cordas e baixo; aceita --pausa: um silencio seco antes da
                     virada, como no video do cavaleiro (modelo tipografia)
    piano    72 BPM  acordes lentos de piano com eco longo (modelo citacao)
    pulso    81 BPM  batida lenta pesada, sino e baixo (modelo colagem)

Ao lado do .wav sai um .json com {"bpm", "batidas": [segundos...], "compassos": [...]},
que o editor usa para cortar as imagens no tempo da musica.
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

TAXA = 44100
# Notas em Hz (la menor e vizinhos).
NOTA = {"A1": 55.0, "C2": 65.41, "D2": 73.42, "E2": 82.41, "F2": 87.31, "G2": 98.0,
        "A2": 110.0, "C3": 130.81, "D3": 146.83, "E3": 164.81, "F3": 174.61, "G3": 196.0,
        "G#3": 207.65, "A3": 220.0, "B3": 246.94, "C4": 261.63, "D4": 293.66, "E4": 329.63,
        "F4": 349.23, "G4": 392.0, "A4": 440.0, "C5": 523.25, "E5": 659.26}
# Progressao sombria classica: Am - F - Dm - E (o E maior da a tensao de volta).
ACORDES = [("A2", ["A3", "C4", "E4"]), ("F2", ["F3", "A3", "C4"]),
           ("D2", ["D3", "F3", "A3"]), ("E2", ["E3", "G#3", "B3"])]
# Progressao alegre em do maior (C - G - Am - F), para o canal infantil.
ALEGRES = [("C3", ["C4", "E4", "G4"]), ("G2", ["G3", "B3", "D4"]),
           ("A2", ["A3", "C4", "E4"]), ("F2", ["F3", "A3", "C4"])]
CLIMAS = {"sombria": 95, "epica": 128, "piano": 72, "pulso": 81, "alegre": 112}


def env(n, ataque=0.005, queda=0.5):
    t = np.arange(n) / TAXA
    return np.minimum(1, t / max(ataque, 1e-4)) * np.exp(-t / queda)


def piano(freq, dur, queda=0.9):
    """Nota de piano aproximada: harmonicos que caem mais rapido quanto mais agudos."""
    n = int(dur * TAXA)
    t = np.arange(n) / TAXA
    som = sum(np.sin(2 * np.pi * freq * k * t) * (0.6 / k ** 1.3) * np.exp(-t * k * 0.9 / queda)
              for k in range(1, 7))
    return som * env(n, 0.004, queda * 2)


def bumbo(dur=0.5, grave=48):
    n = int(dur * TAXA)
    t = np.arange(n) / TAXA
    freq = grave + 110 * np.exp(-t * 28)
    corpo = np.sin(2 * np.pi * np.cumsum(freq) / TAXA) * np.exp(-t * 7)
    # Estalo de ataque: e ele que o ouvido (e o corte da imagem) sente como "a batida".
    estalo = np.random.default_rng(int(grave)).standard_normal(n) * np.exp(-t * 400) * 0.5
    return corpo + estalo


def ruido(dur, queda, rng, passa_alta=True):
    n = int(dur * TAXA)
    r = rng.standard_normal(n)
    if passa_alta:
        r = np.diff(r, prepend=0)
    return r * env(n, 0.001, queda)


def corda(freq, dur, rng):
    """Cordas: serra desafinada e filtrada, entrada lenta."""
    n = int(dur * TAXA)
    t = np.arange(n) / TAXA
    som = np.zeros(n)
    for d in (-0.6, 0, 0.7):
        f = freq * 2 ** (d / 1200 * 10)
        som += 2 * ((t * f) % 1) - 1
    som = passa_baixa(som / 3, 1800)
    return som * np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.3)


def passa_baixa(x, corte):
    a = np.exp(-2 * np.pi * corte / TAXA)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def reverb(x, segundos=2.2, mistura=0.3, rng=None):
    """Convolucao com ruido que decai: sala grande e escura."""
    rng = rng or np.random.default_rng(1)
    n = int(segundos * TAXA)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / TAXA * 6.9 / segundos)
    ir[0] = 0
    ir /= np.sqrt(np.sum(ir ** 2))
    tam = len(x) + n
    molhado = np.fft.irfft(np.fft.rfft(x, tam) * np.fft.rfft(ir, tam), tam)[:len(x)]
    return x * (1 - mistura) + molhado * mistura


def por(faixa, som, inicio, vol=1.0):
    i = int(inicio * TAXA)
    if i >= len(faixa):
        return
    fim = min(len(faixa), i + len(som))
    faixa[i:fim] += som[:fim - i] * vol


def compor(clima, segundos, pausa=None, semente=3):
    bpm = CLIMAS[clima]
    batida = 60 / bpm
    rng = np.random.default_rng(semente)
    n = int((segundos + 3) * TAXA)
    tonal, ritmo = np.zeros(n), np.zeros(n)
    total = int(segundos / batida) + 2
    batidas = [round(i * batida, 4) for i in range(total)]

    for i, t in enumerate(batidas):
        compasso, tempo = divmod(i, 4)
        grave, acorde = (ALEGRES if clima == "alegre" else ACORDES)[compasso % 4]
        if pausa and pausa - batida * 2 <= t < pausa:
            continue  # silencio seco antes da virada
        if clima == "sombria":
            if tempo == 0:
                por(tonal, piano(NOTA[grave], 3.5, 1.4), t, 0.9)
                for j, nota in enumerate(acorde):
                    por(tonal, piano(NOTA[nota], 2.5, 1.0), t + j * batida / 2, 0.35)
            if tempo in (0, 2):
                por(ritmo, bumbo(0.6, 44), t, 0.8)
            por(ritmo, ruido(0.05, 0.015, rng), t + batida / 2, 0.02)
            if compasso % 2 == 1 and tempo == 3:
                por(tonal, piano(NOTA[acorde[-1]] * 2, 1.5, 0.6), t, 0.18)
        elif clima == "epica":
            if tempo == 0:
                por(tonal, corda(NOTA[acorde[0]], batida * 4, rng), t, 0.22)
                por(tonal, corda(NOTA[acorde[2]], batida * 4, rng), t, 0.16)
                por(ritmo, bumbo(1.2, 38), t, 1.0)
            por(tonal, piano(NOTA[grave], batida * 0.9, 0.25), t, 0.5)
            if tempo in (1, 3):
                por(ritmo, ruido(0.25, 0.08, rng, passa_alta=False), t, 0.18)
                por(ritmo, bumbo(0.3, 90), t, 0.4)
            por(ritmo, ruido(0.04, 0.012, rng), t + batida / 2, 0.05)
        elif clima == "piano":
            if tempo == 0:
                por(tonal, piano(NOTA[grave], 5, 2.0), t, 0.6)
            por(tonal, piano(NOTA[acorde[tempo % 3]], 3.0, 1.6), t, 0.33)
            if tempo == 2 and compasso % 2 == 0:
                por(tonal, piano(NOTA[acorde[1]] * 2, 2.5, 1.2), t + batida / 2, 0.14)
        elif clima == "alegre":
            # Baixo saltitante, acorde em colcheias (glockenspiel) e palminha no 2 e 4.
            por(tonal, piano(NOTA[grave], batida * 0.9, 0.3), t, 0.45)
            for k, nota in enumerate(acorde + [acorde[1]]):
                por(tonal, piano(NOTA[nota] * 2, 0.4, 0.18), t + k * batida / 4, 0.16)
            if tempo in (1, 3):
                por(ritmo, ruido(0.12, 0.03, rng, passa_alta=False), t, 0.14)
            if tempo == 0:
                por(ritmo, bumbo(0.4, 60), t, 0.5)
        elif clima == "pulso":
            if tempo == 0 or (tempo == 2 and compasso % 2):
                por(ritmo, bumbo(0.9, 40), t, 1.0)
            if tempo == 2:
                por(ritmo, ruido(0.3, 0.09, rng, passa_alta=False), t, 0.25)
            for k in range(4):
                if k:
                    por(ritmo, ruido(0.03, 0.01, rng), t + k * batida / 4, 0.02 if k % 2 else 0.03)
            if tempo == 0:
                por(tonal, piano(NOTA[grave] / 2, batida * 4, 1.0), t, 0.7)
            sino = NOTA[acorde[(i * 2) % 3]] * 2
            por(tonal, piano(sino, 1.2, 0.35), t + (batida / 2 if tempo % 2 else 0), 0.16)

    ritmo = passa_baixa(ritmo, 9000) if clima != "pulso" else ritmo
    mistura = reverb(tonal, 3.0 if clima == "piano" else 2.2, 0.45 if clima == "piano" else 0.3, rng)
    mistura = mistura + reverb(ritmo, 1.0, 0.12, rng)
    mistura = mistura[: int(segundos * TAXA)]
    sai = int(1.5 * TAXA)
    mistura[-sai:] *= np.linspace(1, 0, sai)
    mistura /= np.max(np.abs(mistura)) + 1e-9
    batidas = [b for b in batidas if b < segundos]
    return mistura * 0.89, {"bpm": bpm, "batidas": batidas, "compassos": batidas[::4],
                            "pausa": pausa}


def salvar(destino, audio, info):
    destino = Path(destino)
    dados = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    estereo = np.column_stack([dados, dados]).ravel()
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(estereo.tobytes())
    destino.with_suffix(".json").write_text(json.dumps(info), encoding="utf-8")


if __name__ == "__main__":
    args = sys.argv[1:]
    pausa = None
    if "--pausa" in args:
        k = args.index("--pausa")
        pausa = float(args[k + 1])
        del args[k:k + 2]
    if len(args) != 3 or args[0] not in CLIMAS:
        sys.exit(__doc__)
    audio, info = compor(args[0], float(args[1]), pausa)
    salvar(args[2], audio, info)
    print(f"Pronto: {args[2]} ({info['bpm']} BPM, {len(info['batidas'])} batidas)")
