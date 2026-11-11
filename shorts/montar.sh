#!/bin/bash
# montar.sh <chave> <numero> <nome-do-arquivo>  -> monta o short (se tiver as 7 imagens) e copia para postar/
cd "$(dirname "$0")"
d=$(ls -d *-$1-criasse | tail -1)
[ $(ls $d/[1-7].jpg 2>/dev/null | wc -l) -eq 7 ] || { echo "faltam imagens em $d"; exit 1; }
python3 editar_short.py $d > /dev/null 2>&1 && python3 idades.py $d > /dev/null 2>&1 && cp $d/final.mp4 ../postar/$2-$3.mp4 && echo "OK $2 $3" || echo "FALHOU $1"
