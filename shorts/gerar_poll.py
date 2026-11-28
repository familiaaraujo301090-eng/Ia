"""Gera as imagens que faltam via Pollinations (reserva quando o Canva trava).
Uso: python3 gerar_poll.py prompts-lote5.json chave1 chave2 ..."""
import io, json, sys, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image
aqui = Path(__file__).parent
P = json.load(open(aqui / sys.argv[1]))
for k in sys.argv[2:]:
    pasta = next(aqui.glob(f"*-{k}-criasse"))
    for n, prompt in enumerate(P[k]["prompts"], 1):
        alvo = pasta / f"{n}.jpg"
        if alvo.exists():
            continue
        url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt + " Highly detailed Pixar 3D render.")
               + f"?width=1080&height=1920&nologo=true&seed={n * 7 + len(k)}")
        for t in range(4):
            try:
                dados = urllib.request.urlopen(url, timeout=180).read()
                im = Image.open(io.BytesIO(dados)).convert("RGB")
                w, h = im.size
                im = im.crop((0, 0, w, int(h * 0.94)))  # corta a marca d'agua do rodape
                w, h = im.size
                alvo_h = int(w * 16 / 9)
                if alvo_h <= h:
                    im = im.crop((0, (h - alvo_h) // 2, w, (h - alvo_h) // 2 + alvo_h))
                else:
                    nw = int(h * 9 / 16); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
                im.resize((1080, 1920), Image.LANCZOS).save(alvo, quality=94)
                print("ok", k, n, flush=True)
                break
            except Exception as e:
                print("erro", k, n, e, flush=True); time.sleep(10)
        time.sleep(3)
