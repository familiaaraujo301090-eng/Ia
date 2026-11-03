#!/usr/bin/env python3
"""Baixa as paginas exportadas do Canva (uma URL por linha na entrada) como 1.jpg, 2.jpg... na pasta.

    python baixar_canva.py pasta/ [primeiro_numero] < urls.txt
"""
import subprocess
import sys
from pathlib import Path

pasta = Path(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
for url in (u.strip() for u in sys.stdin if u.strip()):
    subprocess.run(["curl", "-sf", "-o", str(pasta / f"{n}.jpg"), url], check=True)
    n += 1
print("baixadas", n - 1)
