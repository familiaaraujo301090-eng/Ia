#!/usr/bin/env python3
"""
Compositor de trilhas ORIGINAIS (livres de direitos) pra testar e postar os edits.

    python3 musica.py --estilo rnb  --bpm 80  --compassos 5 -o trilhas/noite.wav
    python3 musica.py --estilo funk --bpm 130 --compassos 6 -o trilhas/rosa.wav

Estilos:
  rnb   R&B lento/sensual: kick seco, clap, hats com rolos, 808 longo, pad com 7ª/9ª, sino
  funk  pegada funk BR: kick + 808 no padrão "tamborzão", clap no 2 e 4, chimbal aberto
  trap  trap escuro: hats rápidos com rolos, 808 deslizando, pad menor
Também grava <saida>.json com os tempos de cada batida e compasso (pra sincronizar o vídeo).
"""
import argparse, json, os, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(3)


def nota(n):  # número MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n, a=0.002, d=0.3, curva=4.0):
    t = np.arange(n) / SR
    e = np.exp(-t / max(1e-4, d) * (curva / 4))
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e


def passa_baixa(x, corte):
    # 1 polo, simples e musical
    a = np.exp(-2 * np.pi * corte / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # trechos curtos; ok
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def lp_rapido(x, corte):
    """Passa-baixa via FFT (pra sinais longos)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (f / corte) ** 4)
    return np.fft.irfft(X, len(x))


def hp_rapido(x, corte):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (corte / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X, len(x))


# ---------------------------------------------------------------- instrumentos
def kick(dur=0.45, f0=150, f1=45):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.22)
    clique = rng.normal(0, 1, n) * env(n, 0.0005, 0.004) * 0.3
    return np.tanh((s + clique) * 1.8)


def b808(freq, dur, glide_de=None):
    n = int(dur * SR); t = np.arange(n) / SR
    f = np.full(n, freq)
    if glide_de:
        f = freq + (glide_de - freq) * np.exp(-t * 18)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    s = np.tanh(s * 2.2) * env(n, 0.004, dur * 0.55)
    return s


def clap():
    n = int(0.35 * SR)
    ruido = hp_rapido(rng.normal(0, 1, n), 900)
    e = np.zeros(n)
    for k, off in enumerate((0, 0.011, 0.022)):
        i = int(off * SR)
        e[i:] += env(n - i, 0.0005, 0.012 if k < 2 else 0.12)
    return ruido * e * 0.55


def hat(aberto=False):
    n = int((0.22 if aberto else 0.05) * SR)
    s = hp_rapido(rng.normal(0, 1, n), 7000)
    return s * env(n, 0.0005, 0.09 if aberto else 0.018) * 0.32


def pad(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.13):  # supersaw suave
            fase = rng.random()
            s += ((t * f * 2 ** (det / 12) + fase) % 1.0) * 2 - 1
    s = lp_rapido(s / (len(freqs) * 3), 900)
    a = np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.25)
    return s * a * 0.5


def sino(freq, dur=1.2):
    n = int(dur * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2.01 * t)
         + 0.15 * np.sin(2 * np.pi * freq * 3.98 * t))
    return s * env(n, 0.002, 0.45) * 0.22


def reverb(x, tempo=1.6, mix=0.22):
    n = int(tempo * SR)
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 4.5 / tempo)
    ir = lp_rapido(ir, 5000)
    L = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    y /= (np.abs(y).max() + 1e-9)
    return x * (1 - mix) + y * mix * np.abs(x).max()


# ---------------------------------------------------------------- arranjo
PROGRESSOES = {
    # acordes (MIDI) — tons menores, com 7ª/9ª pra soar "noturno"
    "rnb":  [[57, 60, 64, 67, 71], [53, 57, 60, 64, 67], [50, 53, 57, 60, 64], [52, 56, 59, 62, 66]],  # Am9 Fmaj9 Dm9 E7
    "funk": [[57, 60, 64, 67], [55, 58, 62, 65], [53, 57, 60, 64], [55, 59, 62, 65]],                    # Am7 Gm7 Fmaj7 G7
    "trap": [[52, 55, 59, 62], [48, 52, 55, 59], [50, 53, 57, 60], [47, 50, 54, 57]],                    # Em7 Cmaj7 Dm7 Bm7b5
}
MELODIAS = {"rnb": [76, 74, 72, 69, 72, 71], "funk": [81, 79, 76, 79], "trap": [76, 79, 74, 71]}


def compor(estilo, bpm, compassos, intro=1):
    seminima = 60 / bpm
    total = compassos * 4 * seminima + 1.5
    N = int(total * SR)
    trilhas = {k: np.zeros(N) for k in ("kick", "bass", "clap", "hat", "pad", "sino")}

    def por(nome, som, tempo, ganho=1.0):
        i = int(tempo * SR)
        if i >= N:
            return
        j = min(N, i + len(som))
        trilhas[nome][i:j] += som[:j - i] * ganho

    prog = PROGRESSOES[estilo]
    batidas, compassos_t = [], []
    for c in range(compassos):
        t0 = c * 4 * seminima
        compassos_t.append(round(t0, 4))
        acorde = prog[c % len(prog)]
        raiz = nota(acorde[0] - 24)
        por("pad", pad([nota(n) for n in acorde], 4 * seminima + 0.3), t0, 0.9)
        cheio = c >= intro  # 1º compasso = intro só com pad + sino (respira)
        for b in range(4):
            batidas.append(round(t0 + b * seminima, 4))
        if estilo == "funk":
            # tamborzão: kick em 1, 1.75(3/16), 2.5 ... em semicolcheias
            padrao = [0, 3, 6, 10, 12] if c % 2 == 0 else [0, 3, 6, 8, 11, 14]
            for s in padrao:
                if cheio:
                    por("kick", kick(0.3, 170, 50), t0 + s * seminima / 4, 0.9)
                    por("bass", b808(raiz * (1.5 if s in (10, 11) else 1), seminima * 0.9), t0 + s * seminima / 4, 0.55)
            for b in (1, 3):
                if cheio:
                    por("clap", clap(), t0 + b * seminima, 0.9)
            for s in range(16):
                if cheio and s % 2 == 0:
                    por("hat", hat(aberto=(s % 8 == 6)), t0 + s * seminima / 4, 0.8 + 0.2 * rng.random())
        else:
            ks = [0, 2.5] if estilo == "rnb" else [0, 1.75, 2.5]
            for k in ks:
                if cheio:
                    por("kick", kick(), t0 + k * seminima)
            if cheio:
                glide = raiz * 1.5 if (estilo == "trap" and c % 2) else None
                por("bass", b808(raiz, 3.2 * seminima, glide), t0, 0.75)
                por("bass", b808(raiz * 1.189, 0.9 * seminima), t0 + 3 * seminima, 0.6)
                por("clap", clap(), t0 + 1 * seminima)
                por("clap", clap(), t0 + 3 * seminima)
            div = 4 if estilo == "trap" else 2
            for s in range(4 * div):
                tt = t0 + s * seminima / div
                if not cheio:
                    continue
                por("hat", hat(), tt, 0.55 + 0.45 * ((s % 2) == 0) * rng.random())
                if s == 4 * div - 2 and c % 2 == 1:  # rolo de chimbal no fim do compasso
                    for r in range(6):
                        por("hat", hat(), tt + r * seminima / 12, 0.4 + r * 0.08)
        # sino/melodia esparsa
        mel = MELODIAS[estilo]
        for k, pos in enumerate((0, 1.5, 3) if estilo == "rnb" else (0, 2)):
            por("sino", sino(nota(mel[(c * 3 + k) % len(mel)])), t0 + pos * seminima, 0.8)

    # mix
    ducking = np.ones(N)  # sidechain: pad abaixa no kick (balanço "respirando")
    k_env = np.abs(trilhas["kick"])
    k_env = np.convolve(k_env, np.ones(2000) / 2000, mode="same")
    ducking -= np.clip(k_env * 2.5, 0, 0.55)
    pad_mix = reverb(trilhas["pad"] * ducking, 2.2, 0.35)
    sino_mix = reverb(trilhas["sino"], 2.5, 0.45)
    clap_mix = reverb(trilhas["clap"], 0.9, 0.18)
    m = (trilhas["kick"] * 0.9 + trilhas["bass"] * 0.8 + clap_mix * 0.7 + trilhas["hat"] * 0.6
         + pad_mix * 0.55 + sino_mix * 0.6)
    # estéreo: hats/sino levemente abertos, graves no centro
    lado = hp_rapido(np.roll(trilhas["hat"] * 0.6 + sino_mix * 0.4, 400), 300)
    L, R = m + lado * 0.25, m - lado * 0.25
    est = np.stack([L, R], 1)
    est = np.tanh(est / (np.abs(est).max() + 1e-9) * 1.4) * 0.89  # "master": saturação + teto
    # fade final
    fo = int(1.2 * SR)
    est[-fo:] *= np.linspace(1, 0, fo)[:, None]
    return est, {"bpm": bpm, "batidas": batidas, "compassos": compassos_t, "duracao": round(total, 3)}


def salvar_wav(caminho, est):
    os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
    pcm = (np.clip(est, -1, 1) * 32767).astype("<i2")
    with wave.open(caminho, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--estilo", choices=list(PROGRESSOES), default="rnb")
    ap.add_argument("--bpm", type=float, default=80)
    ap.add_argument("--compassos", type=int, default=4)
    ap.add_argument("--intro", type=int, default=1, help="compassos de intro sem bateria")
    ap.add_argument("-o", "--saida", default="trilhas/trilha.wav")
    a = ap.parse_args()
    est, info = compor(a.estilo, a.bpm, a.compassos, a.intro)
    salvar_wav(a.saida, est)
    json.dump(info, open(os.path.splitext(a.saida)[0] + ".json", "w"), indent=2)
    print(f"ok -> {a.saida}  ({info['duracao']}s, {a.bpm} bpm)")
