#!/usr/bin/env python3
"""Formato "E se X te criasse?": poe a idade ("5 ANOS", "10 ANOS"...) grande no topo do short.

    python idades.py pasta/
Le "idades" do video.json ({paragrafo: rotulo}) e os tempos da narracao; gera pasta/final.mp4
a partir de pasta/short.mp4. Cada idade fica na tela ate a proxima.
"""
import json
import subprocess
import sys
from pathlib import Path

import editar_short as base
import modelos

pasta = Path(sys.argv[1])
cfg = json.loads((pasta / "video.json").read_text(encoding="utf-8"))
tempos = json.loads((pasta / "tempos.json").read_text(encoding="utf-8"))
total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                       "-of", "csv=p=0", str(pasta / "short.mp4")]))
comeco = {}
for a, _, _, par in tempos:
    comeco.setdefault(par, a)
marcas = sorted((int(p), r) for p, r in cfg["idades"].items())
dourado = modelos.ass_cor("#F0C860")
leg = modelos.cabecalho([
    f"Style: Idade,Inter ExtraBold,120,{dourado},{dourado},&H00101010,&H96000000,0,0,0,0,100,100,4,0,1,6,4,8,60,60,335,1",
])
# Gancho: texto grande lido sem som no primeiro meio segundo (sem fade de entrada)
fim_gancho = 0.0
if cfg.get("gancho"):
    fim_gancho = cfg.get("gancho_dur", 3.2)
    amarelo = modelos.ass_cor("#FFD84A")
    leg.insert(next(i for i, l in enumerate(leg) if l.startswith("Style: Idade")) + 1,
               f"Style: Gancho,Inter ExtraBold,82,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,3,18,0,8,70,70,260,1")
    txt = cfg["gancho"].replace("|", "\\N").replace("[", "{\\c" + amarelo + "}").replace("]", "{\\c&H00FFFFFF&}")
    leg.append(modelos.dialogo(1, 0.0, fim_gancho, "Gancho", "{\\fad(0,200)}" + txt))
for k, (par, rotulo) in enumerate(marcas):
    a = fim_gancho if k == 0 else max(fim_gancho, comeco[par] - base.TRANSICAO)
    b = comeco[marcas[k + 1][0]] - base.TRANSICAO if k + 1 < len(marcas) else total
    pop = "\\fscx140\\fscy140\\t(0,160,\\fscx100\\fscy100)"
    leg.append(modelos.dialogo(0, a, b, "Idade", f"{{{pop}}}{rotulo}"))
(pasta / "idades.ass").write_text("\n".join(leg) + "\n", encoding="utf-8")
fontes = Path(__file__).parent / "fontes"
subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", "short.mp4", "-vf",
                f"subtitles=idades.ass:fontsdir='{fontes}'", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
                "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", "final.mp4"],
               cwd=pasta, check=True)
print("Pronto:", pasta / "final.mp4")
