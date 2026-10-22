#!/usr/bin/env python3
"""Gera a narracao do Mestre Elias a partir de pasta/roteiro.txt (um paragrafo por linha).

Uso:
    python gerar_voz.py pasta_do_video/ [voz] [velocidade] [tom]

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


def gerar(pasta, voz="pm_santa", velocidade=0.87, tom=0.96):
    pasta = Path(pasta)
    kokoro = Kokoro(str(MODELO / "kokoro-v1.0.onnx"), str(MODELO / "voices-v1.0.bin"))
    paragrafos = [p.strip() for p in (pasta / "roteiro.txt").read_text(encoding="utf-8").splitlines()
                  if p.strip()]
    taxa = 24000
    partes, tempos, t = [np.zeros(int(taxa * 0.3), dtype=np.float32)], [], 0.3
    for n, paragrafo in enumerate(paragrafos, 1):
        # Uma frase por vez: a legenda de cada frase comeca e termina junto com a fala.
        frases = re.split(r"(?<=[.!?])\s+", paragrafo)
        for i, frase in enumerate(frases):
            fala = frase.replace("*", "")  # *destaque* e so visual
            audio, taxa = kokoro.create(fala, voice=voz, speed=velocidade, lang="pt-br")
            tempos.append([round(t, 3), round(t + len(audio) / taxa, 3), frase, n])
            pausa = PAUSA_FRASE if i < len(frases) - 1 else PAUSA_PARAGRAFO
            t += len(audio) / taxa + pausa
            partes += [audio.astype(np.float32), np.zeros(int(taxa * pausa), dtype=np.float32)]
    crua = pasta / "voz_crua.wav"
    sf.write(crua, np.concatenate(partes), taxa)
    # Deixa a voz levemente mais grave e suave (sem mudar a duracao), com um pouco de ambiencia.
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(crua), "-af",
        f"asetrate={taxa}*{tom},aresample={taxa},atempo=1/{tom},bass=g=2:f=110,"
        "treble=g=-3:f=6000,aecho=0.8:0.6:60:0.15,loudnorm=I=-16:TP=-1.5",
        "-ar", "44100", str(pasta / "narracao.wav"),
    ], check=True)
    crua.unlink()
    (pasta / "tempos.json").write_text("[\n" + ",\n".join(json.dumps(x, ensure_ascii=False) for x in tempos) + "\n]\n",
                                       encoding="utf-8")
    print(f"Pronto: {pasta / 'narracao.wav'} ({t:.1f}s)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gerar(sys.argv[1], *sys.argv[2:3], *[float(v) for v in sys.argv[3:5]])
