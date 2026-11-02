#!/usr/bin/env python3
"""Gera a narracao do Mestre Elias a partir de pasta/roteiro.txt (um paragrafo por linha).

Uso:
    python gerar_voz.py pasta_do_video/ [voz] [velocidade] [tom] [--rapido]

Vozes: pm_santa / pm_alex (Kokoro, local) ou pt-BR-AntonioNeural (Microsoft, precisa de rede;
a melhor em entonacao). Ex.: python gerar_voz.py pasta/ pt-BR-AntonioNeural 1.08 0.96 --rapido
--limpa: voz limpa, sem baixar o tom e sem eco (mais clara; padrao desde 02/11).
--rapido: ritmo novo (PUBLICO-E-PROGRESSAO.md), com pausas curtas e a primeira palavra ja no
primeiro quadro; use com velocidade ~1.05.

O tom abaixo de 1 deixa a voz mais grave (0.96 e o padrao, sereno; 0.9 fica bem grave).
Cria pasta/narracao.wav e pasta/tempos.json ([inicio, fim, texto, paragrafo] de cada frase,
usados por editar_short.py para sincronizar as legendas). Precisa de
`pip install kokoro-onnx soundfile` e dos arquivos do modelo em shorts/modelo-voz/:
https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

MODELO = Path(__file__).parent / "modelo-voz"
PAUSA_PARAGRAFO = 0.6  # silencio entre paragrafos: deixa a fala serena sem arrastar
PAUSA_FRASE = 0.25
SILENCIO_INICIAL = 0.3
RAPIDO = {"PAUSA_PARAGRAFO": 0.3, "PAUSA_FRASE": 0.12, "SILENCIO_INICIAL": 0.05}
LIMPA = False  # --limpa: sem baixar o tom e sem eco (voz mais clara)


def falar_neural(texto, voz, velocidade, tom, taxa=24000):
    """Uma frase com as vozes neurais da Microsoft (edge-tts): bem mais entonacao que o Kokoro.

    Precisa de `pip install edge-tts` e de speech.platform.bing.com liberado na rede.
    velocidade 1.1 = 10% mais rapido; tom 0.95 = um pouco mais grave.
    """
    import asyncio
    import os
    import edge_tts
    if not os.environ.get("SSL_CERT_FILE") and os.path.exists("/root/.ccr/ca-bundle.crt"):
        os.environ["SSL_CERT_FILE"] = "/root/.ccr/ca-bundle.crt"  # proxy do ambiente na nuvem

    async def baixar():
        com = edge_tts.Communicate(texto, voz, rate=f"{round((velocidade - 1) * 100):+d}%",
                                   pitch=f"{round((tom - 1) * 200):+d}Hz",
                                   proxy=os.environ.get("HTTPS_PROXY") or None)
        dados = b""
        async for parte in com.stream():
            if parte["type"] == "audio":
                dados += parte["data"]
        return dados
    mp3 = asyncio.run(baixar())
    pcm = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0", "-f", "f32le",
                          "-ac", "1", "-ar", str(taxa), "pipe:1"], input=mp3, capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    # tira o silencio que a Microsoft poe no comeco e no fim de cada frase
    voz_ativa = np.nonzero(np.abs(audio) > 0.01)[0]
    if len(voz_ativa):
        audio = audio[max(0, voz_ativa[0] - int(0.03 * taxa)): voz_ativa[-1] + int(0.06 * taxa)]
    return audio, taxa


def gerar(pasta, voz="pm_santa", velocidade=0.87, tom=0.96):
    pasta = Path(pasta)
    neural = "Neural" in voz  # voz da Microsoft (edge-tts), ex.: pt-BR-AntonioNeural
    kokoro = None if neural else Kokoro(str(MODELO / "kokoro-v1.0.onnx"), str(MODELO / "voices-v1.0.bin"))
    paragrafos = [p.strip() for p in (pasta / "roteiro.txt").read_text(encoding="utf-8").splitlines()
                  if p.strip()]
    taxa = 24000
    partes, tempos, t = [np.zeros(int(taxa * SILENCIO_INICIAL), dtype=np.float32)], [], SILENCIO_INICIAL
    for n, paragrafo in enumerate(paragrafos, 1):
        # Uma frase por vez: a legenda de cada frase comeca e termina junto com a fala.
        frases = re.split(r"(?<=[.!?])\s+", paragrafo)
        for i, frase in enumerate(frases):
            fala = frase.replace("*", "")  # *destaque* e so visual
            if neural:
                audio, taxa = falar_neural(fala, voz, velocidade, tom)
            else:
                audio, taxa = kokoro.create(fala, voice=voz, speed=velocidade, lang="pt-br")
            tempos.append([round(t, 3), round(t + len(audio) / taxa, 3), frase, n])
            pausa = PAUSA_FRASE if i < len(frases) - 1 else PAUSA_PARAGRAFO
            t += len(audio) / taxa + pausa
            partes += [audio.astype(np.float32), np.zeros(int(taxa * pausa), dtype=np.float32)]
    crua = pasta / "voz_crua.wav"
    sf.write(crua, np.concatenate(partes), taxa)
    # Deixa a voz levemente mais grave e suave (sem mudar a duracao), com um pouco de ambiencia.
    if LIMPA or neural:
        # Voz limpa (pedido de 02/11: a antiga soava abafada e arrastada): sem mudar o tom,
        # sem eco; so um corpo leve no grave e mais presenca nas consoantes.
        filtro = "highpass=f=70,bass=g=1.5:f=120,equalizer=f=3200:t=q:w=1.2:g=3,loudnorm=I=-16:TP=-1.5"
    else:
        filtro = (f"asetrate={taxa}*{tom},aresample={taxa},atempo=1/{tom},bass=g=2:f=110,"
                  "treble=g=-3:f=6000,aecho=0.8:0.6:60:0.15,loudnorm=I=-16:TP=-1.5")
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(crua), "-af", filtro,
        "-ar", "44100", str(pasta / "narracao.wav"),
    ], check=True)
    crua.unlink()
    (pasta / "tempos.json").write_text("[\n" + ",\n".join(json.dumps(x, ensure_ascii=False) for x in tempos) + "\n]\n",
                                       encoding="utf-8")
    print(f"Pronto: {pasta / 'narracao.wav'} ({t:.1f}s)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--rapido" in args:
        args.remove("--rapido")
        globals().update(RAPIDO)
    if "--limpa" in args:
        args.remove("--limpa")
        LIMPA = True
    if not args:
        sys.exit(__doc__)
    gerar(args[0], *args[1:2], *[float(v) for v in args[2:4]])
