# Lote 5 (videos 123-142) — como continuar

Pronto: roteiros, vozes (narracao.wav), trilhas (musica.wav) e video.json das 20 pastas `2026-11-18-<chave>-criasse`.
Novidades do lote: `whoosh` (som em cada troca de cena) e `barra` (barra de progresso) no video.json.

Falta: as 7 imagens de cada video (140 no total).
- Prompts prontos em `prompts-lote5.json` (sempre usar `aspectRatio: PORTRAIT_9_16`).
- Media ids ja feitos ficam em `ids-lote5.json` (`python3 anota.py ids-lote5.json <chave> n=MAH...`).
- Job pendente: davi 1 (job gerado em 22/11; se expirou, gerar de novo).
- Depois: `python3 grade.py ids-lote5.json` -> grade Canva DAHYxf_hmrY (pagina 1) -> exportar jpg 4320x7680
  -> `python3 cortar_grade.py <url> 0 ordem-atual.json` -> `./montar.sh <chave> <num> <nome>` (num/nome em prompts-lote5.json).
- Montar um video por vez (dois ao mesmo tempo na mesma pasta corrompem o arquivo).
