#!/usr/bin/env python3
"""Gera uma folha de revisao com quadros de um ou mais shorts, para conferir de uma vez.

Uso:
    python revisar.py saida.png pasta1/ [pasta2/ ...]

Cada pasta vira uma linha com 8 quadros espalhados pelo video (pegando o primeiro
segundo, para conferir o gancho, e o fim, para conferir o fechamento).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

QUADROS, LARGURA = 8, 180


def duracao(video):
    saida = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=nw=1:nk=1", str(video)],
                           capture_output=True, text=True, check=True)
    return float(saida.stdout)


def linha(video, temp):
    total = duracao(video)
    tempos = [0.8 + (total - 1.6) * i / (QUADROS - 1) for i in range(QUADROS)]
    imagens = []
    for i, t in enumerate(tempos):
        arquivo = Path(temp) / f"{video.parent.name}-{i}.png"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video),
                        "-frames:v", "1", "-vf", f"scale={LARGURA}:-1", str(arquivo)], check=True)
        imagem = Image.open(arquivo).convert("RGB")
        ImageDraw.Draw(imagem).text((6, 6), f"{t:.0f}s", fill="white")
        imagens.append(imagem)
    return imagens


def main(destino, pastas):
    with tempfile.TemporaryDirectory() as temp:
        linhas = [linha(Path(p) / "short.mp4", temp) for p in pastas]
    altura = linhas[0][0].height
    folha = Image.new("RGB", (LARGURA * QUADROS, altura * len(linhas)))
    for r, imagens in enumerate(linhas):
        for c, imagem in enumerate(imagens):
            folha.paste(imagem, (c * LARGURA, r * altura))
    folha.save(destino)
    print(f"Folha salva em {destino}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2:])
