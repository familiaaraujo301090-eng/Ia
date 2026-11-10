#!/usr/bin/env python3
"""Baixa uma grade 4x4 exportada do Canva e recorta em imagens 1080x1920.
Uso: python cortar_grade.py <url> <inicio> <ordem.json>   (ordem.json = [[pasta_chave, numero], ...]; pega 16 a partir de inicio)"""
import io, json, sys, urllib.request
from pathlib import Path
from PIL import Image
url, ini, ordem = sys.argv[1], int(sys.argv[2]), json.load(open(sys.argv[3]))
im = Image.open(io.BytesIO(urllib.request.urlopen(url, timeout=120).read()))
print(im.size)
w, h = im.size[0] // 4, im.size[1] // 4
aqui = Path(__file__).parent
for n, (k, i) in enumerate(ordem[ini:ini + 16]):
    pasta = next(aqui.glob(f"*-{k}-criasse")) if not (aqui / k).is_dir() else aqui / k
    im.crop(((n % 4) * w, (n // 4) * h, (n % 4 + 1) * w, (n // 4 + 1) * h)).resize((1080, 1920), Image.LANCZOS).save(pasta / f"{i}.jpg", quality=93)
print("ok")
