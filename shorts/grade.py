#!/usr/bin/env python3
"""grade.py <ids.json> -> escolhe as proximas 16 imagens ainda nao baixadas (sem N.jpg na pasta),
grava ordem-atual.json e imprime as operacoes update_fill para a grade do Canva."""
import json, sys
from pathlib import Path
aqui = Path(__file__).parent
d = json.load(open(sys.argv[1])); g = json.load(open(aqui / "grade-canva.json"))
falta = [(k, i) for k, v in d.items() for i in sorted(v) if not (next(aqui.glob(f"*-{k}-criasse")) / f"{i}.jpg").exists()][:16]
json.dump(falta, open(aqui / "ordem-atual.json", "w"))
print(len(falta), file=sys.stderr)
print(json.dumps([{"type": "update_fill", "locator_id": c, "asset_type": "image", "asset_id": d[k][i], "alt_text": f"{k} {i}"}
                  for c, (k, i) in zip(g["celulas"], falta)]))
