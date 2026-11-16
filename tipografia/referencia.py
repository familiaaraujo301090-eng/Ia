#!/usr/bin/env python3
"""
Acerta os tempos de um projeto usando um VÍDEO DE REFERÊNCIA (ex.: um edit do TikTok com a mesma música):
detecta, quadro a quadro, quando o texto troca na referência e encaixa cada tempo do projeto na troca mais próxima.

    python3 referencia.py projetos/x.json video_referencia.mp4 [--offset 2.2]

No projeto, escreva os tempos como você leu no vídeo de referência (aprox.). --offset desconta o
trecho inicial (o vídeo final começa nesse segundo da referência; use o mesmo em "audio_inicio").
"""
import argparse, json, subprocess
import numpy as np


def trocas(video, W=128, H=72):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"scale={W}:{H}", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    q = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)[:, 8:64, 20:108]  # ignora marca d'água
    d = np.abs(np.diff(q, axis=0)).mean(axis=(1, 2))
    return np.array([(i + 1) / 30 for i in range(len(d))
                     if d[i] > 1.5 and d[i] >= d[max(0, i - 1)] and d[i] >= d[min(len(d) - 1, i + 1)]])


def encaixar(t, ev):
    c = ev[(ev >= t - 0.22) & (ev <= t + 0.06)]
    return float(c[np.argmin(abs(c - (t - 0.08)))]) if len(c) else t - 0.08


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto"); ap.add_argument("video")
    ap.add_argument("--offset", type=float, default=0.0)
    a = ap.parse_args()
    ev = trocas(a.video)
    p = json.load(open(a.projeto, encoding="utf-8"))
    cs = p["cenas"]
    for i, c in enumerate(cs):
        if "tempos" in c:
            ts = [encaixar(t, ev) for t in c["tempos"]]
            for k in range(1, len(ts)):
                ts[k] = max(ts[k], ts[k - 1] + 0.05)
            c["tempos"] = ts
        c["inicio"] = encaixar(c["inicio"], ev) if i else c["inicio"]
    for i, c in enumerate(cs):  # cortes colados e tudo relativo ao offset
        if "tempos" in c:
            c["inicio"] = min(c["inicio"], c["tempos"][0])
        c["fim"] = cs[i + 1]["inicio"] if i + 1 < len(cs) else c["fim"]
    for c in cs:
        for k in ("inicio", "fim"):
            c[k] = round(max(0.0, c[k] - a.offset), 3)
        if "tempos" in c:
            c["tempos"] = [round(max(c["inicio"], t - a.offset), 3) for t in c["tempos"]]
        for k in ("casal_t0", "porta_t0"):
            if k in c:
                c[k] = round(c[k] - a.offset, 3)
    cs[0]["inicio"] = 0.0
    p["audio_inicio"] = p.get("audio_inicio", 0) + a.offset
    p["duracao"] = cs[-1]["fim"]
    p["batidas"] = [c.get("tempos", [c["inicio"]])[0] for c in cs if c["estilo"] == "gigante"]
    json.dump(p, open(a.projeto, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"ok: {len(ev)} trocas na referência; projeto ajustado ({p['duracao']}s)")


if __name__ == "__main__":
    main()
