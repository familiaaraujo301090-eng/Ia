#!/usr/bin/env python3
"""Gera a narracao do Mestre Elias a partir de pasta/roteiro.txt (um paragrafo por linha).

Uso:
    python gerar_voz.py pasta_do_video/ [voz] [velocidade]

Cria pasta/narracao.wav e pasta/tempos.json (inicio e fim de cada paragrafo,
usados por editar_short.py para sincronizar as legendas). Precisa de
`pip install kokoro-onnx soundfile` e dos arquivos do modelo em shorts/modelo-voz/:
https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

MODELO = Path(__file__).parent / "modelo-voz"
PAUSA = 0.45  # segundos de silencio entre paragrafos


def gerar(pasta, voz="pm_santa", velocidade=0.9):
    pasta = Path(pasta)
    kokoro = Kokoro(str(MODELO / "kokoro-v1.0.onnx"), str(MODELO / "voices-v1.0.bin"))
    paragrafos = [p.strip() for p in (pasta / "roteiro.txt").read_text(encoding="utf-8").splitlines()
                  if p.strip()]
    taxa = 24000
    partes, tempos, t = [np.zeros(int(taxa * 0.3), dtype=np.float32)], [], 0.3
    for paragrafo in paragrafos:
        audio, taxa = kokoro.create(paragrafo, voice=voz, speed=velocidade, lang="pt-br")
        tempos.append([round(t, 3), round(t + len(audio) / taxa, 3)])
        t += len(audio) / taxa + PAUSA
        partes += [audio.astype(np.float32), np.zeros(int(taxa * PAUSA), dtype=np.float32)]
    crua = pasta / "voz_crua.wav"
    sf.write(crua, np.concatenate(partes), taxa)
    # Deixa a voz um pouco mais grave e encorpada sem mudar a duracao, e normaliza o volume.
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(crua), "-af",
        f"asetrate={taxa}*0.93,aresample={taxa},atempo=1/0.93,bass=g=3:f=120,"
        "aecho=0.8:0.5:40:0.12,loudnorm=I=-15:TP=-1.5",
        "-ar", "44100", str(pasta / "narracao.wav"),
    ], check=True)
    crua.unlink()
    (pasta / "tempos.json").write_text(json.dumps(tempos))
    print(f"Pronto: {pasta / 'narracao.wav'} ({t:.1f}s)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    gerar(sys.argv[1], *sys.argv[2:3], *[float(v) for v in sys.argv[3:4]])
