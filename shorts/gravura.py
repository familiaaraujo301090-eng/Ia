#!/usr/bin/env python3
"""Transforma imagens em gravura antiga (hachura em papel envelhecido) e monta o banco de
recortes usado na rajada de abertura dos shorts.

Uso:
    python gravura.py imagem.jpg saida.jpg      converte uma imagem
    python gravura.py --banco [quantidade]      recria shorts/banco/ com recortes de todas
                                                as imagens do canal (padrao 240)

Os edits virais de filosofia usam gravuras antigas trocando a cada 2 quadros. Em vez de
gerar centenas de imagens, o banco recorta detalhes (rosto, mao, lamparina, paisagem) das
imagens que ja temos e passa todos pelo mesmo filtro, para parecerem do mesmo livro velho.
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

LARGURA, ALTURA = 1080, 1920
PASSO = 7  # distancia entre as linhas da hachura, em pixels
TINTA, PAPEL = (24, 21, 19), (232, 224, 205)
SHORTS = Path(__file__).parent
BANCO = SHORTS / "banco"


def enquadrar(img, zoom=1.0, cx=0.5, cy=0.5):
    """Recorta a imagem em 9:16, ampliada por zoom e centrada em (cx, cy)."""
    w, h = img.size
    ch = min(h, w * ALTURA / LARGURA) / zoom
    cw = ch * LARGURA / ALTURA
    x = min(max(0, cx * w - cw / 2), w - cw)
    y = min(max(0, cy * h - ch / 2), h - ch)
    return img.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((LARGURA, ALTURA), Image.LANCZOS)


def gravura(img):
    """Hachura diagonal cuja espessura segue o escuro da imagem; cruza nas sombras fundas."""
    cinza = ImageOps.autocontrast(img.convert("L"), cutoff=2)
    # Nossas imagens sao escuras (luz de lamparina); clarear antes deixa o papel aparecer,
    # como nas gravuras de livro antigo.
    a = 0.12 + 0.88 * (np.asarray(cinza, dtype=float) / 255) ** 0.5
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    linha = ((xx + yy) % PASSO) / PASSO < (1 - a) * 1.05
    cruz = ((xx - yy) % PASSO) / PASSO < (1 - a - 0.45) * 1.6
    tinta = np.clip(linha.astype(float) + cruz, 0, 1)
    saida = Image.fromarray(((1 - tinta) * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.7))
    return ImageOps.colorize(saida, TINTA, PAPEL)


def imagens_do_canal():
    return sorted(p for p in SHORTS.glob("20*/*.jpg"))


def montar_banco(quantidade=240, semente=7):
    """Recortes aleatorios (zoom de 1,3 a 2,6x) de todas as imagens, ja em gravura."""
    rng = random.Random(semente)
    fontes = imagens_do_canal()
    BANCO.mkdir(exist_ok=True)
    for antigo in BANCO.glob("*.jpg"):
        antigo.unlink()
    for i in range(quantidade):
        img = Image.open(rng.choice(fontes)).convert("RGB")
        recorte = enquadrar(img, rng.uniform(1.3, 2.6), rng.uniform(0.25, 0.75), rng.uniform(0.2, 0.8))
        if rng.random() < 0.5:
            recorte = ImageOps.mirror(recorte)
        gravura(recorte).save(BANCO / f"{i:03d}.jpg", quality=85)
    print(f"Banco: {quantidade} recortes de {len(fontes)} imagens em {BANCO}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--banco":
        montar_banco(int(sys.argv[2]) if len(sys.argv) > 2 else 240)
    elif len(sys.argv) == 3:
        gravura(enquadrar(Image.open(sys.argv[1]).convert("RGB"))).save(sys.argv[2], quality=92)
    else:
        sys.exit(__doc__)
