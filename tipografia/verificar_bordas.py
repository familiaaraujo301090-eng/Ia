#!/usr/bin/env python3
"""Confere se alguma letra encosta/sai da tela: procura contornos fortes nas bordas de cada quadro.
    python3 verificar_bordas.py saida/video.mp4"""
import subprocess, sys
import numpy as np
from PIL import Image, ImageFilter

def quadros(video, W=270, H=480, fps=15):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={fps},scale={W}:{H}", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
    i = 0
    while True:
        b = p.stdout.read(W * H)
        if len(b) < W * H:
            break
        yield i / fps, np.frombuffer(b, np.uint8).reshape(H, W)
        i += 1

def checar(video, margem=0.06, limiar=45):
    ruins = []
    for t, q in quadros(video):
        q = np.asarray(Image.fromarray(q).filter(ImageFilter.MedianFilter(3)), np.int16)  # tira o grão
        H, W = q.shape
        mx, my = int(W * margem), int(H * margem)
        esq, dir_ = q[:, :mx], q[:, -mx:]
        topo, base = q[:my, :], q[-my:, :]
        g = max(np.abs(np.diff(esq, axis=1)).max(), np.abs(np.diff(dir_, axis=1)).max(),
                np.abs(np.diff(topo, axis=0)).max(), np.abs(np.diff(base, axis=0)).max())
        if g > limiar:
            ruins.append((round(t, 2), int(g)))
    return ruins

if __name__ == "__main__":
    ok = True
    for v in sys.argv[1:]:
        r = checar(v)
        print(("OK   " if not r else "BORDA") + f"  {v}" + ("" if not r else f"  quadros: {r[:12]}"))
        ok &= not r
    sys.exit(0 if ok else 1)
