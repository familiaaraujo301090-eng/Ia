#!/usr/bin/env python3
"""
Motor de tipografia cinética (estilo "lyric edit" do TikTok).

Uso:
    python3 tipografia.py projetos/earned_it.json             # gera o MP4 (sem áudio)
    python3 tipografia.py projetos/earned_it.json --audio musica.mp3 --inicio 42.5
    python3 tipografia.py projetos/earned_it.json --preview   # só alguns frames PNG

Estilos de cena (campo "estilo"):
    revelar   palavra entra cinza e acende pra branco, frase se monta no centro
    pilha     CAIXA ALTA empilhada, palavra nova entra com glitch + risco
    flash     fundo alterna preto/branco a cada palavra, texto invertido
    gigante   uma palavra só, ENORME, condensada, com "soco" de escala
    serifa    serifa bold, fundo bordô/bege alternando, linhas antigas desfocadas
    cursiva   letra cursiva sendo "escrita" letra a letra, com vinheta
    maquina   máquina de escrever por sílaba (use "-" pra quebrar: "a mi-nha")
    circulo   transição: círculo cresce do centro e vira faixa com o texto
"""
import argparse, json, math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import numpy as np
from PIL import ImageOps
from elementos import Elementos
import cenario  # noqa: F401  (registra os cenários de anime nos Elementos)

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTES = {
    "anton": "Anton.ttf", "bebas": "BebasNeue.ttf", "serif": "DMSerifDisplay.ttf",
    "cursiva": "GreatVibes.ttf", "black": "Montserrat-Black.ttf", "bold": "Montserrat-Bold.ttf",
    "medium": "Montserrat-Medium.ttf", "playfair": "Playfair-Black.ttf",
    "italico": "Playfair-Italic.ttf", "oswald": "Oswald-Bold.ttf",
}
_cache = {}


def fonte(nome, tam):
    k = (nome, int(tam))
    if k not in _cache:
        _cache[k] = ImageFont.truetype(os.path.join(AQUI, "fonts", FONTES.get(nome, nome)), int(tam))
    return _cache[k]


def cor(c):
    if isinstance(c, (tuple, list)):
        return tuple(c)
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_back(t):  # passa do ponto e volta ("soco")
    t = max(0.0, min(1.0, t))
    c = 1.7
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


# ----------------------------------------------------------------- fundos
class Fundos:
    def __init__(s, W, H):
        s.W, s.H = W, H
        rng = np.random.default_rng(7)
        s.rng = rng
        s.grao_base = Image.fromarray((rng.normal(0, 1, (H + 256, W + 256)).clip(-3, 3) * 34 + 128).astype(np.uint8), "L")
        y, x = np.mgrid[0:H, 0:W]
        d = np.sqrt(((x - W / 2) / (W * .75)) ** 2 + ((y - H / 2) / (H * .62)) ** 2)
        s.vinheta = Image.fromarray((np.clip(d, 0, 1) ** 1.8 * 255).astype(np.uint8), "L")

    def solido(s, c):
        return Image.new("RGB", (s.W, s.H), cor(c))

    def vinheta_sobre(s, img, forca=0.85, c=(0, 0, 0)):
        escuro = Image.new("RGB", img.size, c)
        m = s.vinheta.point(lambda v: int(v * forca))
        return Image.composite(escuro, img, m)

    def grao(s, img, frame, forca=0.08):
        if not forca:
            return img
        r = random.Random(frame)
        ox, oy = r.randrange(256), r.randrange(256)
        g = s.grao_base.crop((ox, oy, ox + s.W, oy + s.H)).convert("RGB")
        return Image.blend(img, ImageChops.overlay(img, g), forca * 4)

    def acabamento(s, img, tempo, t_cena, dur_cena, frame, proj):
        """Camera viva + brilho de lente + flicker de filme. É o que tira a cara de 'gerado'."""
        W, H = s.W, s.H
        # 1) push-in lento na cena + deriva de mão (ruído suave, nunca periódico perfeito)
        z = 1 + proj.get("zoom", 0.035) * ease_out(t_cena / max(0.1, dur_cena))
        amp = proj.get("deriva", 4.0)
        dx = amp * (math.sin(tempo * 0.83) + 0.6 * math.sin(tempo * 2.17 + 1.3) + 0.3 * math.sin(tempo * 5.3))
        dy = amp * (math.sin(tempo * 0.71 + 2.0) + 0.6 * math.sin(tempo * 1.93) + 0.3 * math.sin(tempo * 4.7 + .5))
        rot = proj.get("giro", 0.25) * math.sin(tempo * 0.6)
        for b in proj.get("batidas", []):  # soco de zoom na batida
            if 0 <= tempo - b < 0.22:
                z += 0.045 * (1 - (tempo - b) / 0.22) ** 2
        if z != 1 or dx or dy or rot:
            img = img.rotate(rot, resample=Image.BICUBIC, center=(W / 2 + dx, H / 2 + dy),
                             translate=(-dx, -dy), fillcolor=img.getpixel((2, 2)))
            w, h = int(W * z), int(H * z)
            img = img.resize((w, h), Image.BICUBIC).crop(((w - W) // 2, (h - H) // 2, (w - W) // 2 + W, (h - H) // 2 + H))
        # 2) brilho de lente (halation) suave nas partes claras
        gl = proj.get("brilho", 0.22)
        if gl:
            pequeno = img.resize((W // 6, H // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
            img = Image.blend(img, ImageChops.screen(img, pequeno.resize((W, H), Image.BILINEAR)), gl)
        # 3) flicker de exposição bem sutil
        fl = 1 + 0.018 * math.sin(frame * 1.7) * math.sin(frame * 0.37)
        img = img.point(lambda v: min(255, int(v * fl)))
        return img


# paletas tiradas dos vídeos de referência (pixel a pixel)
PALETAS = {
    # vermelho-sangue puro (sem verde/azul), centro aceso -> bordas fundas; texto laranja queimado
    "sangue": {"bg": "#3a0000", "bg2": "#a30000", "cores": ["#f1ede6", "#ff8418", "#ff8418"], "cor": "#ff8418"},
    # mesma base, texto quase preto (igual ao "VOCÊ SABE QUE NEM..." da referência)
    "sangue_preto": {"bg": "#3a0000", "bg2": "#a30000", "cores": ["#120000"], "cor": "#120000", "cor_apagada": "#6e0000"},
    "bordo":  {"bg": "#5e0b1c", "cor": "#cbc2b1"},
    "rosa":   {"bg": "#0a0006", "bg2": "#3d0020", "cores": ["#ffd1e8", "#ff4fa3", "#ff006e"]},
}


def com_paleta(cena):
    pal = PALETAS.get(cena.get("paleta"), {})
    return {**pal, **cena}


def fundo(ctx, cena, padrao="#0b0b0b", vinheta=0.7):
    img = ctx.fx.solido(cena.get("bg", padrao))
    if cena.get("bg2"):
        return Image.composite(img, ctx.fx.solido(cena["bg2"]), ctx.fx.vinheta)
    v = cena.get("vinheta", vinheta)
    if sum(cor(cena.get("bg", padrao))) > 600:  # fundo claro: vinheta leve e clara, sem cantos sujos
        return ctx.fx.vinheta_sobre(img, min(v, 0.25), (200, 200, 200))
    return ctx.fx.vinheta_sobre(img, v)


# ----------------------------------------------------------------- texto
def medir(f, txt):
    b = f.getbbox(txt)
    return b[2] - b[0], b[3] - b[1], b


# área segura: o texto nunca passa de 80% da largura/altura. Já desconta o zoom máximo da câmera
# (push-in 3,5% + soco 4,5%), a deriva e o foco de entrada, então NADA encosta na borda.
SEGURA = 0.80


def caber(nome, tam, textos, largura, altura=None, linhas=1, entrelinha=1.2):
    """Diminui a fonte até o maior texto caber na largura (e o bloco na altura)."""
    tam = int(tam)
    while tam > 12:
        f = fonte(nome, tam)
        w = max((medir(f, x)[0] for x in textos if x), default=0)
        h = tam * entrelinha * linhas
        if w <= largura and (altura is None or h <= altura):
            return f
        tam = int(tam * 0.94)
    return fonte(nome, tam)


def quebrar(palavras, f, largura_max):
    """Quebra lista de palavras em linhas que caibam na largura."""
    linhas, atual = [], []
    for i, p in enumerate(palavras):
        teste = " ".join(x for _, x in atual + [(i, p)])
        if atual and medir(f, teste)[0] > largura_max:
            linhas.append(atual)
            atual = []
        atual.append((i, p))
    if atual:
        linhas.append(atual)
    # evita palavra órfã sozinha na última linha
    if len(linhas) > 1 and len(linhas[-1]) == 1 and len(linhas[-2]) > 2:
        linhas[-1].insert(0, linhas[-2].pop())
    return linhas


def texto_esticado(txt, f, alvo_w, alvo_h, c, fundo=None):
    """Renderiza texto e estica pra caber em alvo_w x alvo_h (efeito condensado alto)."""
    w, h, b = medir(f, txt)
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - b[0], 10 - b[1]), txt, font=f, fill=cor(c))
    return im.resize((max(1, int(alvo_w)), max(1, int(alvo_h))), Image.LANCZOS)


def tempos_palavras(cena, n):
    """Tempo (relativo à cena) em que cada palavra entra."""
    if "tempos" in cena:
        ts = [t - cena["inicio"] for t in cena["tempos"]][:n]
        if len(ts) < n:  # faltou tempo pra alguma palavra: espalha o resto no que sobra da cena
            ult = ts[-1] if ts else 0.0
            resto = (cena["fim"] - cena["inicio"]) * 0.85 - ult
            falta = n - len(ts)
            ts += [ult + resto * (k + 1) / (falta + 1) for k in range(falta)]
        return ts
    dur = cena["fim"] - cena["inicio"]
    janela = dur * cena.get("ritmo", 0.7)
    ts = [janela * i / max(1, n) for i in range(n)]
    if cena.get("bpm"):  # encaixa cada palavra na grade da música (colcheia por padrão)
        passo = 60 / cena["bpm"] / cena.get("grade", 2)
        ini, out, ult = cena["inicio"], [], -1
        for t in ts:
            k = max(ult + 1, round((ini + t) / passo - 1e-6) if t else math.ceil(ini / passo - 1e-6))
            ult = k
            out.append(max(0.0, k * passo - ini))
        ts = out
    return ts


# ----------------------------------------------------------------- entrada com foco
FOCO = 0.38  # segundos que a palavra leva pra "assentar"


def camada_texto(txt, f, c, pad=40):
    w, h, b = medir(f, txt)
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), txt, font=f, fill=cor(c) + (255,))
    return im, b


def colar_foco(img, txt, f, c, x, y, k, anchor="lm", blur_max=16, escala=0.10, subir=14, modo=None):
    """Desenha txt em (x,y). k: 0 = começando a entrar, 1 = assentado.
    Desfoque -> nítido, levemente maior -> tamanho real, opacidade 0 -> 1.  Sem listras, sem glitch."""
    if k >= 1:
        ImageDraw.Draw(img).text((x, y), txt, font=f, fill=cor(c), anchor=anchor)
        return
    e = ease_out(k)
    im, b = camada_texto(txt, f, c)
    if modo == "cortina":
        corte = Image.new("L", im.size, 0)
        larg = int(im.width * min(1.0, e * 1.08))
        ImageDraw.Draw(corte).rectangle([0, 0, larg, im.height], fill=255)
        corte = corte.filter(ImageFilter.GaussianBlur(6))
        im.putalpha(ImageChops.multiply(im.getchannel("A"), corte))
        blur_max, escala, subir = 0, 0, 16
    z = 1 + escala * (1 - e)
    if modo == "pop":      # nasce grande e assenta com um quiquinho
        z = 1 + 0.95 * (1 - ease_back(k))
        blur_max = 8
    elif modo == "zoom":   # nasce pequeno e cresce passando do ponto
        z = 0.25 + 0.75 * ease_back(k)
        blur_max = 8
    elif modo == "subir":
        subir = 120
    elif modo == "queda":
        subir = -120
    # a palavra nunca passa da área segura, nem no pico do pop/zoom
    w_txt0 = b[2] - b[0]
    if w_txt0 > 0:
        z = min(z, img.width * 0.92 / w_txt0)
        if anchor[0] == "l":  # ancorado à esquerda: cresce a partir do centro da palavra; não deixa encostar
            cxp = x + w_txt0 / 2
            z = min(z, 2 * min(cxp, img.width - cxp) * 0.96 / w_txt0)
        else:
            z = min(z, 2 * min(x, img.width - x) * 0.96 / w_txt0)
    z = max(z, 0.05)
    if z != 1:
        im = im.resize((max(1, int(im.width * z)), max(1, int(im.height * z))), Image.BICUBIC)
    r = blur_max * (1 - e) ** 1.5
    if r > 0.4:
        im = im.filter(ImageFilter.GaussianBlur(r))
    a = im.getchannel("A").point(lambda v: int(v * min(1, e * 1.6)))
    im.putalpha(a)
    # posiciona pelo mesmo ponto de ancoragem do texto nítido
    w_txt, h_txt = b[2] - b[0], b[3] - b[1]
    cx = x + (w_txt / 2 if anchor[0] == "l" else 0) + b[0]
    asc, desc = f.getmetrics()
    cy = y + (b[1] + h_txt / 2 - (asc + desc) / 2 if anchor[1] == "m" else 0) + subir * (1 - e)
    img.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def frase_em_foco(img, palavras, ts, t, f, cor_fn, W, cy, largura_max, lh, recentrar=True, modos=None, cx=None):
    """Layout de frase palavra a palavra; a palavra nova entra com foco."""
    linhas = quebrar(palavras, f, largura_max)
    esp = medir(f, " ")[0] or f.size * .28
    y0 = cy - lh * (len(linhas) - 1) / 2
    for li, linha in enumerate(linhas):
        vis = [(i, p) for i, p in linha if t >= ts[i]] if recentrar else linha
        if not vis:
            continue
        larg = medir(f, " ".join(p for _, p in vis))[0]
        x = (W / 2 if cx is None else cx) - larg / 2
        for i, p in vis:
            if t >= ts[i]:
                k = (t - ts[i]) / FOCO
                colar_foco(img, p, f, cor_fn(i, k), x, y0 + li * lh, k, modo=modos[i % len(modos)] if modos else None)
            x += medir(f, p)[0] + esp


# ----------------------------------------------------------------- estilos
def est_revelar(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    img = ctx.elem(fundo(ctx, cena), cena, t)
    palavras = cena["texto"].split()
    ts = tempos_palavras(cena, len(palavras))
    LARG = W * cena.get("largura", SEGURA)
    CX = W / 2 + cena.get("dx", 0)
    f = caber(cena.get("fonte", "oswald"), cena.get("tamanho", 92), palavras, LARG)
    c_on, c_off = cor(cena.get("cor", "#ece9e4")), cor(cena.get("cor_apagada", "#5a5a5a"))
    # palavra acende de cinza pra branco um pouco DEPOIS de assentar (igual aos edits)
    cor_fn = lambda i, k: mix(c_off, c_on, ease_out((k - 0.4) / 1.2))
    modos = [cena["entrada"]] if cena.get("entrada") else (["subir", "pop", "queda", "zoom"] if cena.get("animar") else None)
    if cena.get("sombra") or cena.get("animar") or cena.get("entrada"):
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cy = H / 2 + cena.get("dy", 0)
        frase_em_foco(cam, palavras, ts, t, f, cor_fn, W, cy, LARG, f.size * 1.18, modos=modos, cx=CX)
        if cena.get("pulsar"):  # a frase pulsa em cada ataque da música
            agora = cena["inicio"] + t
            pul = min(1.0, sum(math.exp(-(agora - a) * 9) for a in ctx.ataques if 0 <= agora - a < 0.6))
            z = 1 + 0.045 * pul + 0.015 * t / max(0.5, cena["fim"] - cena["inicio"])
            if z != 1:
                w2, h2 = int(W * z), int(H * z)
                big = cam.resize((w2, h2), Image.BICUBIC)
                cam = big.crop(((w2 - W) // 2, int(cy * z - cy), (w2 - W) // 2 + W, int(cy * z - cy) + H))
        if not cena.get("sombra"):
            img.paste(cam, (0, 0), cam)
            return img
        sb = cam.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.75))
        img = Image.composite(Image.new("RGB", (W, H), (20, 10, 10)), img, ImageChops.offset(sb, 3, 5))
        img.paste(cam, (0, 0), cam)
        return img
    frase_em_foco(img, palavras, ts, t, f, cor_fn, W, H / 2 + cena.get("dy", 0), LARG, f.size * 1.18, cx=CX)
    return img


def est_pilha(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    img = ctx.elem(fundo(ctx, cena, "#000000"), cena, t)
    palavras = cena["texto"].upper().split("/") if "/" in cena["texto"] else cena["texto"].upper().split()
    palavras = [p.strip() for p in palavras]
    ts = tempos_palavras(cena, len(palavras))
    f = caber(cena.get("fonte", "black"), cena.get("tamanho", 120), palavras, W * cena.get("largura", SEGURA),
              H * SEGURA, len(palavras), 1.02)
    PX = W / 2 + cena.get("dx", 0)
    cores = [cor(c) for c in cena.get("cores", ["#f5f5f5"])]
    lh = f.size * 1.02
    # a pilha sobe suavemente conforme cresce (interpola em vez de pular)
    n_vis = sum(ease_out((t - x) / FOCO) for x in ts if t >= x)
    alvo = H / 2 - lh * n_vis / 2 + cena.get("dy", 0)
    d = ImageDraw.Draw(img)
    for i, p in enumerate(palavras):
        if t < ts[i]:
            break
        k = (t - ts[i])
        c = cores[min(i * len(cores) // max(1, len(palavras)), len(cores) - 1)] if cena.get("degrade") else cores[i % len(cores)]
        y = alvo + i * lh + lh / 2
        colar_foco(img, p, f, c, PX, y, k / FOCO, anchor="mm", blur_max=20, subir=24,
                   modo=cena.get("entrada") or (["pop", "subir", "zoom", "queda"][i % 4] if cena.get("animar") else None))
    return img


def est_flash(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    palavras = cena["texto"].split()
    ts = tempos_palavras(cena, len(palavras))
    n = sum(1 for x in ts if t >= x)
    claro = (n % 2 == 1) if cena.get("alternar", True) else False
    pulo = 0.0
    if cena.get("piscar"):
        # frase repetida: inverte preto/branco em cada ataque da música (detectado no áudio)
        agora = cena["inicio"] + t
        ons = [o for o in ctx.ataques if cena["inicio"] - 0.02 <= o <= agora]
        claro = len(ons) % 2 == 1
        if ons:
            pulo = max(0.0, 1 - (agora - ons[-1]) / 0.14)
        if "tempos" not in cena:  # sem tempos: frase inteira já na tela
            n = len(palavras)
            ts = [-1] * n
    bg, fg = ((242, 242, 242), (10, 10, 10)) if claro else ((8, 8, 8), (240, 240, 240))
    img = ctx.fx.solido(bg)
    if claro:
        img = ctx.fx.vinheta_sobre(img, 0.35, (150, 150, 150))
    img = ctx.elem(img, cena, t)
    tam = cena.get("tamanho", 84) * (1 + 0.07 * pulo)
    f = caber(cena.get("fonte", "medium"), tam, palavras, W * SEGURA / (1 + 0.07 * pulo))
    frase_em_foco(img, palavras, ts, t, f, lambda i, k: fg, W, H / 2 + cena.get("dy", 0), W * SEGURA, f.size * 1.25,
                  modos=[cena["entrada"]] if cena.get("entrada") else None)
    return img


def est_gigante(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    inverter = cena.get("inverter", False)
    if cena.get("piscar"):  # palavra repetida: inverte a cada ataque da música
        inverter = inverter ^ (sum(1 for a in ctx.ataques if cena["inicio"] - 0.02 <= a <= cena["inicio"] + t) % 2 == 1)
    bg = cor(cena.get("bg", "#ebe8e2" if inverter else "#0a0a0a"))
    fg = cor(cena.get("cor", "#111111" if inverter else "#eeebe5"))
    img = ctx.elem(ctx.fx.solido(bg), cena, t)
    txt = cena["texto"]
    t -= tempos_palavras(cena, 1)[0]  # pode esperar o segundo exato em que a palavra é cantada
    if t < 0:
        return img
    f = fonte(cena.get("fonte", "anton"), 400)
    k = ease_back(t / 0.3)
    # pico do soco (~1.1x) ainda cabe na área segura; "sangrar" foi aposentado (letra não sai da tela)
    teto = SEGURA / 1.02
    alt = H * min(cena.get("altura", 0.42), teto) * (0.86 + 0.14 * k)
    larg = W * min(cena.get("largura", teto), teto) * (0.86 + 0.14 * k)
    im = texto_esticado(txt, f, larg, alt, fg)
    km = t / 0.22
    if km < 1:  # desfoque de movimento no impacto (some em ~7 quadros)
        e = 1 - ease_out(km)
        borrado = im.resize((im.width, max(1, int(min(H * SEGURA, im.height * (1 + 0.25 * e))))), Image.BICUBIC)
        borrado = borrado.filter(ImageFilter.BoxBlur(int(2 + 18 * e)))
        borrado.putalpha(borrado.getchannel("A").point(lambda v: int(v * min(1, 0.3 + km))))
        im = borrado
    gy = H / 2 + cena.get("dy", 0)
    img.paste(im, (int(W / 2 - im.width / 2), int(gy - im.height / 2)), im)
    if cena.get("sub"):
        fs = fonte("bold", 46)
        ImageDraw.Draw(img).text((W / 2, H / 2 + cena.get("dy", 0) + alt / 2 + 70), cena["sub"], font=fs, fill=fg, anchor="mm")
    if cena.get("sobre"):
        fs = fonte("bold", 46)
        ImageDraw.Draw(img).text((W / 2, H / 2 - alt / 2 - 60), cena["sobre"], font=fs, fill=fg, anchor="mm")
    return img


def est_serifa(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    A, B = cor(cena.get("cor_a", "#5e0b1c")), cor(cena.get("cor_b", "#cbc2b1"))
    linhas = [l.strip() for l in cena["texto"].split("/")]
    ts = tempos_palavras(cena, len(linhas))
    n = sum(1 for x in ts if t >= x)
    troca = cena.get("alternar", True) and n % 2 == 0
    bg, fg = (B, A) if troca else (A, B)
    img = ctx.elem(ctx.fx.solido(bg), cena, t)
    f = caber(cena.get("fonte", "serif"), cena.get("tamanho", 120), linhas, W * SEGURA, H * SEGURA, len(linhas), 0.95)
    lh = f.size * 0.9
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nitida = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y0 = H / 2 - lh * (n - 1) / 2
    for i in range(n - 1):
        ImageDraw.Draw(camada).text((W / 2, y0 + i * lh), linhas[i], font=f, fill=fg + (140,), anchor="mm")
    if n:
        colar_foco(nitida, linhas[n - 1], f, fg, W / 2, y0 + (n - 1) * lh, (t - ts[n - 1]) / FOCO,
                   anchor="mm", blur_max=18, subir=26)
    if n > 1:
        camada = camada.filter(ImageFilter.GaussianBlur(9))
        img.paste(camada, (0, 0), camada)
    img.paste(nitida, (0, 0), nitida)
    return img


def est_cursiva(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    claro = cena.get("claro", False)
    img = ctx.fx.solido("#f4f4f4" if claro else "#060606")
    img = ctx.elem(ctx.fx.vinheta_sobre(img, 0.75 if claro else 0.5, (120, 120, 120) if claro else (0, 0, 0)), cena, t)
    fg = (25, 25, 25) if claro else (235, 235, 235)
    txt = cena["texto"]
    f = caber(cena.get("fonte", "cursiva"), cena.get("tamanho", 150), txt.split(), W * SEGURA)
    dur = (cena["fim"] - cena["inicio"]) * cena.get("ritmo", 0.7)
    n = int(len(txt) * min(1, t / max(.01, dur))) + 1
    d = ImageDraw.Draw(img)
    linhas = quebrar(txt.split(), f, W * SEGURA)
    lh = f.size * 1.05
    cont = 0
    for li, ln in enumerate(linhas):
        s = " ".join(p for _, p in ln)
        vis = s[:max(0, n - cont)]
        cont += len(s) + 1
        # ancora pela linha inteira pra letra não "pular" enquanto digita
        w = medir(f, s)[0]
        d.text((W / 2 - w / 2, H / 2 + (li - (len(linhas) - 1) / 2) * lh), vis, font=f, fill=fg, anchor="lm")
    return img


def est_maquina(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    silabas = cena["texto"].replace("-", "-\x00").replace(" ", " \x00").split("\x00")
    silabas = [s for s in silabas if s]
    ts = tempos_palavras(cena, len(silabas))
    n = sum(1 for x in ts if t >= x)
    tons = [cor(c) for c in cena.get("tons", ["#e9e9e9", "#c9c9c9", "#ffffff", "#0a0a0a", "#bdbdbd"])]
    bg = tons[cena.get("tom", 0) % len(tons)]
    fg = (15, 15, 15) if sum(bg) > 380 else (240, 240, 240)
    img = ctx.elem(ctx.fx.solido(bg), cena, t)
    # hífen só fica visível na última sílaba mostrada ("a mi-" -> "a minha")
    s = "".join(silabas[:max(0, n - 1)]).replace("-", "") + (silabas[n - 1] if n else "")
    if n == len(silabas):
        s = s.rstrip("-")
    f = caber(cena.get("fonte", "medium"), cena.get("tamanho", 74), [cena["texto"].replace("-", "")], W * SEGURA)
    ImageDraw.Draw(img).text((W / 2, H / 2), s, font=f, fill=fg, anchor="mm")
    return img


def est_circulo(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    img = ctx.elem(ctx.fx.solido(cena.get("bg", "#000000")), cena, t)
    faixa_h = H * cena.get("faixa", 0.26)
    k1 = ease_out(t / 0.45)          # círculo cresce
    k2 = ease_out((t - 0.4) / 0.4)   # vira faixa
    m = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(m)
    r = faixa_h / 2 * k1
    meia = (W / 2 + r) * k2
    dm.rounded_rectangle([W / 2 - r - meia, H / 2 - r, W / 2 + r + meia, H / 2 + r], radius=r * (1 - k2) + 1, fill=255)
    faixa = Image.new("RGB", (W, H), (245, 245, 245))
    # leve degradê de cima/baixo como nos vídeos
    grad = Image.linear_gradient("L").resize((1, H)).resize((W, H))
    faixa = ImageChops.multiply(faixa, Image.merge("RGB", [grad.point(lambda v: 255 - int(abs(v - 128) / 128 * 55))] * 3))
    img.paste(faixa, (0, 0), m)
    if t > 0.75:
        cena2 = dict(cena, inicio=cena["inicio"] + 0.75)
        palavras = cena["texto"].upper().split()
        ts = tempos_palavras(cena2, len(palavras))
        n = sum(1 for x in ts if t - 0.75 >= x)
        f = caber(cena.get("fonte", "black"), cena.get("tamanho", 66), [" ".join(palavras)], W * SEGURA, faixa_h * 0.8)
        ImageDraw.Draw(img).text((W / 2, H / 2), " ".join(palavras[:n]), font=f, fill=(15, 15, 15), anchor="mm")
    return img


def est_inclinado(cv, cena, t, ctx):
    """Tela branca: linhas de texto inclinadas, a última maior; riscos diagonais finos atravessando."""
    W, H = ctx.W, ctx.H
    img = ctx.fx.vinheta_sobre(ctx.fx.solido(cena.get("bg", "#f3f2ef")), 0.35, (170, 170, 170))
    img = ctx.elem(img, cena, t)
    linhas = [l.strip() for l in cena["texto"].split("/")]
    ts = tempos_palavras(cena, len(linhas))
    n = sum(1 for x in ts if t >= x)
    cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fg = cor(cena.get("cor", "#4a4a4a"))
    base = cena.get("tamanho", 80)
    ini = max(0, n - 2)  # mostra no máximo as 2 últimas linhas
    blocos = []
    for i in range(ini, n):
        grande = i == n - 1 and n > ini + 1 or (n == 1)
        f = caber(cena.get("fonte", "bebas"), base * (1.5 if grande else 1.0), [linhas[i]], W * 0.62)
        blocos.append((i, f))
    alt = sum(f.size * 1.05 for _, f in blocos)
    y = H / 2 - alt / 2
    for i, f in blocos:
        txt = linhas[i]
        if cena.get("digitar", True):  # escreve letra por letra, ancorado na linha inteira
            nchar = max(1, int(len(txt) * min(1.0, (t - ts[i]) / 0.45)) + 1)
            w_full = medir(f, txt)[0]
            parcial = txt[:nchar]
            colar_foco(cam, parcial, f, fg, W / 2 - w_full / 2, y + f.size * 0.5, (t - ts[i]) / FOCO,
                       anchor="lm", blur_max=10, subir=10)
        else:
            colar_foco(cam, txt, f, fg, W / 2, y + f.size * 0.5, (t - ts[i]) / FOCO, anchor="mm", blur_max=14, subir=18)
        y += f.size * 1.05
    dur = max(0.5, cena["fim"] - cena["inicio"])
    giro = cena.get("angulo", 9) + 5 * t / dur
    zz = 1 + 0.10 * t / dur
    if zz != 1:
        w2, h2 = int(W * zz), int(H * zz)
        cam = cam.resize((w2, h2), Image.BICUBIC).crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))
    cam = cam.rotate(giro, resample=Image.BICUBIC, center=(W / 2, H / 2))
    img.paste(cam, (0, 0), cam)
    d = ImageDraw.Draw(img)
    a = t * 12
    d.line([(W * 0.62 + a, -20), (W * 0.98 + a, H + 20)], fill=(70, 70, 70), width=3)
    d.line([(W * 0.40 - a * 0.6, -20), (W * 0.30 - a * 0.6, H + 20)], fill=(150, 150, 150), width=1)
    return img


def _palavra_espacada(txt, f, c, track):
    """Desenha a palavra letra a letra com espaçamento extra (tracking)."""
    larg = sum(f.getlength(ch) for ch in txt) + track * max(0, len(txt) - 1)
    asc, desc = f.getmetrics()
    pad = 30
    im = Image.new("RGBA", (int(larg) + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for ch in txt:
        d.text((x, pad), ch, font=f, fill=c + (255,))
        x += f.getlength(ch) + track
    return im, larg, pad


def _achatar(cam, e, cx, cy):
    """Saída em 'chicote': achata na vertical, estica e borra na horizontal, apaga."""
    if e <= 0:
        return cam
    W, H = cam.size
    sy = max(0.06, 1 - 0.9 * e)
    sx = 1.0  # sem esticar: a letra não passa da borda
    w2, h2 = int(W * sx), max(1, int(H * sy))
    im = cam.resize((w2, h2), Image.BICUBIC)
    borrado = im.resize((max(1, int(w2 / (1 + 14 * e))), h2), Image.BILINEAR).resize((w2, h2), Image.BILINEAR)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(borrado, (int(cx - w2 * cx / W), int(cy - h2 * cy / H)))
    out.putalpha(out.getchannel("A").point(lambda v: int(v * (1 - e) ** 1.2)))
    return out


def est_linhas(cv, cena, t, ctx):
    """Só letras, com as animações da referência: palavras surgem desfocadas e cinza e clareiam,
    o espaçamento entre letras abre devagar, troca de frase em 'chicote' (achata+borra), leve
    inclinação, aproximação lenta, soco de zoom nas palavras de impacto e brilho suave."""
    W, H = ctx.W, ctx.H
    bg = cor(cena.get("bg", "#060606"))
    img = fundo(ctx, cena, "#060606", 0.55)
    img = ctx.elem(img, cena, t)
    claro = sum(bg) > 380
    if cena.get("faixa"):  # faixa de cor oposta atravessando a tela, com a letra dentro (abre rápido)
        kf = ease_out(t / 0.25)
        hf = H * cena.get("faixa_altura", 0.24) * kf
        cyf = H / 2 + cena.get("dy", 0)
        cf = (244, 243, 240) if not claro else (10, 10, 10)
        df = ImageDraw.Draw(img)
        rnd_f = random.Random(int(cena["inicio"] * 10))
        topo = [(x, cyf - hf / 2 + rnd_f.uniform(-3, 3)) for x in range(0, W + 40, 40)]
        base = [(x, cyf + hf / 2 + rnd_f.uniform(-3, 3)) for x in range(W + 40, -40, -40)]
        df.polygon(topo + base, fill=cf)
        claro = not claro
    fg_pad = (18, 18, 18) if claro else (242, 240, 235)
    cinza = (150, 150, 150) if claro else (120, 118, 114)
    dur = max(0.5, cena["fim"] - cena["inicio"])
    LARG = W * cena.get("largura", 0.84)
    linhas = cena["linhas"]
    # layout reservado (não pula quando a linha de baixo chega)
    medidas = []
    for ln in linhas:
        g0 = max(ln["grupos"], key=lambda g: len(g["texto"]))
        nome = g0.get("fonte", ln.get("fonte", "serif"))
        tam = ln.get("tamanho", 90)
        f = caber(nome, tam, [g0["texto"]], LARG * 0.86)
        medidas.append(f.size * 1.25)
    alt = sum(medidas)
    bloco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = H / 2 + cena.get("dy", 0) - alt / 2
    for ln, h in zip(linhas, medidas):
        grupos = ln["grupos"]
        ativo = None
        for gi, g in enumerate(grupos):
            if t >= g["tempos"][0] - cena["inicio"]:
                ativo = gi
        cy = y + h / 2
        y += h
        if ativo is None:
            continue
        g = grupos[ativo]
        g_ini = g["tempos"][0] - cena["inicio"]
        g_fim = (grupos[ativo + 1]["tempos"][0] - cena["inicio"]) if ativo + 1 < len(grupos) else dur
        nome = g.get("fonte", ln.get("fonte", "serif"))
        tam = g.get("tamanho", ln.get("tamanho", 90))
        f = caber(nome, tam, [g["texto"]], LARG * 0.86)
        c = cor(g.get("cor", ln.get("cor", fg_pad)))
        # espaçamento abrindo com o tempo (mais na serifa, menos no negrito)
        abre = {"serif": 7.0, "italico": 5.0}.get(nome, 2.5) * ln.get("abrir", 1.0)
        track = f.size * 0.02 + abre * (t - g_ini)
        palavras = g["texto"].split()
        ts = [x - cena["inicio"] for x in g["tempos"]]
        while len(ts) < len(palavras):
            ts.append(ts[-1] + 0.15)
        imgs = [_palavra_espacada(p, f, c, track) for p in palavras]
        esp = f.getlength(" ") + track * 1.5
        total = sum(w for _, w, _ in imgs) + esp * (len(imgs) - 1)
        if total > LARG:  # nunca passa da área segura
            track = max(0.0, track - (total - LARG) / max(1, sum(len(p) for p in palavras)))
            imgs = [_palavra_espacada(p, f, c, track) for p in palavras]
            esp = f.getlength(" ") + track * 1.5
            total = sum(w for _, w, _ in imgs) + esp * (len(imgs) - 1)
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        x = W / 2 - total / 2
        asc, desc = f.getmetrics()
        for (im, w, pad), t0 in zip(imgs, ts):
            k = (t - t0) / 0.45
            if k <= 0:
                x += w + esp
                continue
            e = ease_out(k)
            col = mix(cinza, c, ease_out((k - 0.15) / 0.9))
            if col != c:  # recolore (cinza -> branco)
                im = Image.merge("RGBA", (*[Image.new("L", im.size, v) for v in col], im.getchannel("A")))
            r = 7 * (1 - e) ** 1.4
            if r > 0.4:
                im = im.filter(ImageFilter.GaussianBlur(r))
            im.putalpha(im.getchannel("A").point(lambda v, e=e: int(v * min(1, e * 1.4))))
            cam.paste(im, (int(x - pad), int(cy - (asc + desc) / 2 - pad + 8 * (1 - e))), im)
            x += w + esp
        # soco de zoom (palavra de impacto) — limitado à área segura
        if g.get("soco"):
            kz = ease_out((t - g_ini) / 0.6)
            z = 1 + g["soco"] * kz
            z = min(z, (W * 0.92) / max(1, total))
            if z > 1.001:
                w2, h2 = int(W * z), int(H * z)
                cam = cam.resize((w2, h2), Image.BICUBIC).crop((int((w2 - W) / 2), int(cy * z - cy), int((w2 - W) / 2) + W, int(cy * z - cy) + H))
        # troca de frase: a antiga sai em chicote nos últimos 0,16s antes da nova
        if ativo + 1 < len(grupos) and t > g_fim - 0.16:
            cam = _achatar(cam, (t - (g_fim - 0.16)) / 0.16, W / 2, cy)
        bloco.alpha_composite(cam)
    # aproximação lenta + leve inclinação (como na referência), saída da cena em chicote
    z = 1 + cena.get("zoom_texto", 0.05) * ease_out(t / dur)
    if z != 1:
        w2, h2 = int(W * z), int(H * z)
        bloco = bloco.resize((w2, h2), Image.BICUBIC).crop(((w2 - W) // 2, (h2 - H) // 2, (w2 - W) // 2 + W, (h2 - H) // 2 + H))
    # trava final: o bloco montado nunca passa de 86% da tela (soco + zoom + espaçamento somados)
    caixa = bloco.getchannel("A").getbbox()
    if caixa:
        bw, bh = caixa[2] - caixa[0], caixa[3] - caixa[1]
        # 86%: sobra margem pra inclinação e pro zoom/deriva da câmera que vêm depois
        lim = min(W * 0.86 / max(1, bw), H * 0.86 / max(1, bh), 1.0)
        bx = (caixa[0] + caixa[2]) / 2
        if lim < 1.0 or caixa[0] < W * 0.07 or caixa[2] > W * 0.93:
            w2, h2 = max(1, int(W * lim)), max(1, int(H * lim))
            menor = bloco.resize((w2, h2), Image.BICUBIC)
            bloco = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bloco.paste(menor, (int(W / 2 - bx * lim), int(H / 2 - H / 2 * lim)))
    rnd = random.Random(int(cena["inicio"] * 100))
    ang = cena.get("inclinacao", rnd.uniform(-1.6, 1.6)) + 0.5 * (t / dur)
    bloco = bloco.rotate(ang, resample=Image.BICUBIC, center=(W / 2, H / 2))
    if t > dur - 0.2:
        bloco = _achatar(bloco, (t - (dur - 0.2)) / 0.2, W / 2, H / 2 + cena.get("dy", 0))
    a = bloco.getchannel("A")
    brilho = a.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * (0.55 if not claro else 0.25)))
    img = Image.composite(Image.new("RGB", (W, H), (200, 196, 188) if not claro else (120, 120, 120)), img, brilho)
    img.paste(bloco, (0, 0), bloco)
    return img


ESTILOS = dict(linhas=est_linhas, inclinado=est_inclinado, revelar=est_revelar, pilha=est_pilha, flash=est_flash, gigante=est_gigante,
               serifa=est_serifa, cursiva=est_cursiva, maquina=est_maquina, circulo=est_circulo)


# ----------------------------------------------------------------- render
class Ctx:
    pass


def quadro(proj, ctx, tempo, idx):
    cena = None
    for c in proj["cenas"]:
        if c["inicio"] <= tempo < c["fim"]:
            cena = c
    if cena is None:
        img = ctx.fx.solido(proj.get("bg", "#000000"))
    else:
        t = tempo - cena["inicio"]
        cfg = com_paleta(cena)
        for k in ("bpm", "grade", "animar"):
            if k in proj and k not in cfg:
                cfg[k] = proj[k]
        lista = cfg.get("elementos", proj.get("elementos", []))
        ctx.elem = lambda im, c, tt: ctx.el.aplicar(im, lista, tempo, tt, c, proj.get("batidas", []))
        img = ESTILOS[cena["estilo"]](None, cfg, t, ctx)
        if cfg.get("piscar_inverte"):  # frase repetida: a tela inteira (foto junto) inverte em cada ataque
            n_at = sum(1 for x in ctx.ataques if cena["inicio"] + 0.15 <= x <= tempo)
            if n_at % 2 == 1:
                img = ImageOps.invert(img)
        img = ctx.fx.acabamento(img, tempo, t, cena["fim"] - cena["inicio"], idx, proj)
        # fade curtinho entre cenas
        fade = cena.get("fade", proj.get("fade", 0.12))
        restante = cena["fim"] - tempo
        if fade and restante < fade:
            img = Image.blend(img, ctx.fx.solido("#000"), 1 - restante / fade)
    if proj.get("pb"):  # preto e branco com curva de filme (pretos fundos, brancos cremosos)
        g = ImageOps.grayscale(img).point(lambda v: int(255 * (0.5 - 0.5 * math.cos(math.pi * v / 255)) ** 0.92))
        img = Image.merge("RGB", [g, g, g.point(lambda v: max(0, v - 4))])
    return ctx.fx.grao(img, idx, proj.get("grao", 0.05))


def render(proj, saida, audio=None, inicio=0.0, preview=False):
    W, H, fps = proj.get("w", 1080), proj.get("h", 1920), proj.get("fps", 30)
    ctx = Ctx()
    ctx.W, ctx.H = W, H
    ctx.fx = Fundos(W, H)
    ctx.el = Elementos(W, H)
    ctx.elem = lambda im, c, tt: im
    dur = proj.get("duracao", max(c["fim"] for c in proj["cenas"]))
    ctx.ataques = []
    if audio:
        try:
            from sincronizar import carregar, detectar_batidas
            ctx.ataques = [round(x, 3) for x in detectar_batidas(carregar(audio, inicio, inicio + dur), 4, 0.6)]
        except Exception as e:
            print("aviso: não detectei ataques do áudio:", e, file=sys.stderr)
    ctx.el.ataques = ctx.ataques
    random.seed(1)
    if preview:
        os.makedirs(saida, exist_ok=True)
        for c in proj["cenas"]:
            tm = c["inicio"] + (c["fim"] - c["inicio"]) * 0.8
            quadro(proj, ctx, tm, 0).save(os.path.join(saida, f"{tm:06.2f}_{c['estilo']}.png"))
        print("previews em", saida)
        return
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-"]
    if audio:
        cmd += ["-ss", str(inicio), "-t", str(dur), "-i", audio, "-map", "0:v", "-map", "1:a",
                "-af", f"afade=t=out:st={max(0, dur - 0.35):.3f}:d=0.35", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", saida]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = int(dur * fps)
    for i in range(total):
        p.stdin.write(quadro(proj, ctx, i / fps, i).tobytes())
        if i % fps == 0:
            print(f"\r{i / fps:5.1f}s / {dur:.1f}s", end="", file=sys.stderr)
    p.stdin.close()
    p.wait()
    print(f"\nok -> {saida}", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("projeto")
    ap.add_argument("-o", "--saida")
    ap.add_argument("--audio", help="arquivo de música (mp3/m4a/wav) que você tem direito de usar")
    ap.add_argument("--inicio", type=float, default=0.0, help="segundo da música onde o vídeo começa")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    proj = json.load(open(a.projeto, encoding="utf-8"))
    base = os.path.splitext(os.path.basename(a.projeto))[0]
    saida = a.saida or os.path.join(AQUI, "saida", base + ("_preview" if a.preview else ".mp4"))
    os.makedirs(os.path.dirname(saida) if not a.preview else saida, exist_ok=True)
    audio = a.audio or proj.get("audio")
    if audio and not os.path.exists(audio) and os.path.exists(os.path.join(AQUI, audio)):
        audio = os.path.join(AQUI, audio)
    if not audio and not a.preview:
        print("AVISO: projeto sem música. Use --audio musica.mp3, ou gere uma trilha original com musica.py", file=sys.stderr)
    render(proj, saida, audio, a.inicio or proj.get("audio_inicio", 0), a.preview)
