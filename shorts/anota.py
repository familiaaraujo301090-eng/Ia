#!/usr/bin/env python3
"""anota.py <arquivo.json> <chave> n=id n=id ...  -> grava os ids das imagens do Canva"""
import json, sys
a, k = sys.argv[1], sys.argv[2]
d = json.load(open(a))
d.setdefault(k, {}).update(dict(x.split("=") for x in sys.argv[3:]))
json.dump(d, open(a, "w"))
print({c: len(v) for c, v in d.items()})
