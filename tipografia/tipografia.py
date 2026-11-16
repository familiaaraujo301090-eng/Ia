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
        s.graos = [Image.fromarray(rng.normal(0, 1, (H // 2, W // 2)).clip(-3, 3).__mul__(40).__add__(128)
                                   .astype(np.uint8), "L").resize((W, H)) for _ in range(6)]
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
        g = s.graos[frame % len(s.graos)].convert("RGB")
        return Image.blend(img, ImageChops.overlay(img, g), forca * 4) if forca else img


# ----------------------------------------------------------------- texto
def medir(f, txt):
    b = f.getbbox(txt)
    return b[2] - b[0], b[3] - b[1], b


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
        return [t - cena["inicio"] for t in cena["tempos"]]
    dur = cena["fim"] - cena["inicio"]
    janela = dur * cena.get("ritmo", 0.7)
    return [janela * i / max(1, n) for i in range(n)]


# ----------------------------------------------------------------- estilos
def est_revelar(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    bg = cena.get("bg", "#0b0b0b")
    img = ctx.fx.solido(bg)
    img = ctx.fx.vinheta_sobre(img, 0.7)
    palavras = cena["texto"].split()
    ts = tempos_palavras(cena, len(palavras))
    f = fonte(cena.get("fonte", "oswald"), cena.get("tamanho", 92))
    c_on, c_off = cor(cena.get("cor", "#f2f2f2")), cor(cena.get("cor_apagada", "#5a5a5a"))
    d = ImageDraw.Draw(img)
    linhas = quebrar(palavras, f, W * .82)
    esp = medir(f, " ")[0] or f.size * .28
    lh = f.size * 1.18
    y0 = H / 2 - lh * len(linhas) / 2 + cena.get("dy", 0)
    for li, linha in enumerate(linhas):
        visiveis = [(i, p) for i, p in linha if t >= ts[i]]
        if not visiveis:
            continue
        # a linha recentra conforme as palavras entram (igual aos vídeos)
        largura = medir(f, " ".join(p for _, p in visiveis))[0]
        x = W / 2 - largura / 2
        for i, p in visiveis:
            k = (t - ts[i]) / 0.35
            col = mix(c_off, c_on, ease_out(k))
            dy = (1 - ease_out(k * 1.5)) * 18
            d.text((x, y0 + li * lh + dy), p, font=f, fill=col, anchor="lm")
            x += medir(f, p)[0] + esp
    return img


def est_pilha(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    img = ctx.fx.solido(cena.get("bg", "#000000"))
    if cena.get("bg2"):
        # gradiente radial pra dar profundidade (fundo vermelho dos vídeos)
        g = ctx.fx.solido(cena["bg2"])
        img = Image.composite(img, g, ctx.fx.vinheta)
    palavras = cena["texto"].upper().split("/") if "/" in cena["texto"] else cena["texto"].upper().split()
    palavras = [p.strip() for p in palavras]
    ts = tempos_palavras(cena, len(palavras))
    f = fonte(cena.get("fonte", "black"), cena.get("tamanho", 120))
    cores = [cor(c) for c in cena.get("cores", ["#f5f5f5"])]
    lh = f.size * 1.02
    n_vis = sum(1 for x in ts if t >= x)
    # a pilha sobe suavemente conforme cresce
    alvo = H / 2 - lh * n_vis / 2
    d = ImageDraw.Draw(img)
    for i, p in enumerate(palavras):
        if t < ts[i]:
            break
        k = (t - ts[i])
        c = cores[min(i * len(cores) // max(1, len(palavras)), len(cores) - 1)] if cena.get("degrade") else cores[i % len(cores)]
        y = alvo + i * lh + lh / 2
        if k < 0.22:  # glitch de entrada
            for off, cc in ((-9, (255, 40, 60)), (9, (40, 200, 255))):
                d.text((W / 2 + off * random.random(), y), p, font=f, fill=cc, anchor="mm")
            d.text((W / 2, y), p, font=f, fill=mix((90, 90, 90), c, k / 0.22), anchor="mm")
            w = medir(f, p)[0]
            d.rectangle([W / 2 - w / 2 - 10, y - 6, W / 2 + w / 2 + 10, y + 6], fill=c)
        else:
            d.text((W / 2, y), p, font=f, fill=c, anchor="mm")
    return img


def est_flash(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    palavras = cena["texto"].split()
    ts = tempos_palavras(cena, len(palavras))
    n = sum(1 for x in ts if t >= x)
    claro = (n % 2 == 1) if cena.get("alternar", True) else False
    bg, fg = ((242, 242, 242), (10, 10, 10)) if claro else ((8, 8, 8), (240, 240, 240))
    img = ctx.fx.solido(bg)
    if claro:
        img = ctx.fx.vinheta_sobre(img, 0.35, (150, 150, 150))
    f = fonte(cena.get("fonte", "medium"), cena.get("tamanho", 84))
    txt = " ".join(palavras[:n])
    d = ImageDraw.Draw(img)
    linhas = quebrar(txt.split(), f, W * .86)
    lh = f.size * 1.25
    for li, ln in enumerate(linhas):
        d.text((W / 2, H / 2 + (li - (len(linhas) - 1) / 2) * lh), " ".join(p for _, p in ln),
               font=f, fill=fg, anchor="mm")
    return img


def est_gigante(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    inverter = cena.get("inverter", False)
    bg = cor(cena.get("bg", "#f0f0f0" if inverter else "#050505"))
    fg = cor(cena.get("cor", "#0a0a0a" if inverter else "#f5f5f5"))
    img = ctx.fx.solido(bg)
    txt = cena["texto"]
    f = fonte(cena.get("fonte", "anton"), 400)
    k = ease_back(t / 0.28)
    alt = H * cena.get("altura", 0.42) * (0.75 + 0.25 * k)
    larg = W * cena.get("largura", 0.94) * (0.75 + 0.25 * k)
    if cena.get("sangrar"):  # palavra maior que a tela, cortada nas bordas
        larg *= 1.35
    im = texto_esticado(txt, f, larg, alt, fg)
    sx = int(math.sin(t * 60) * 6 * max(0, 1 - t / 0.3))  # tremidinha no impacto
    img.paste(im, (int(W / 2 - im.width / 2) + sx, int(H / 2 - im.height / 2)), im)
    if cena.get("sub"):
        fs = fonte("bold", 46)
        ImageDraw.Draw(img).text((W / 2, H / 2 + alt / 2 + 70), cena["sub"], font=fs, fill=fg, anchor="mm")
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
    img = ctx.fx.solido(bg)
    f = fonte(cena.get("fonte", "serif"), cena.get("tamanho", 120))
    lh = f.size * 0.9
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nitida = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y0 = H / 2 - lh * (n - 1) / 2
    for i in range(n):
        alvo = nitida if i == n - 1 else camada
        k = ease_out((t - ts[i]) / 0.3)
        ImageDraw.Draw(alvo).text((W / 2, y0 + i * lh + (1 - k) * 30), linhas[i], font=f,
                                  fill=fg + (int(255 * (k if i == n - 1 else 0.55)),), anchor="mm")
    if n > 1:
        camada = camada.filter(ImageFilter.GaussianBlur(9))
        img.paste(camada, (0, 0), camada)
    img.paste(nitida, (0, 0), nitida)
    return img


def est_cursiva(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    claro = cena.get("claro", False)
    img = ctx.fx.solido("#f4f4f4" if claro else "#060606")
    img = ctx.fx.vinheta_sobre(img, 0.75 if claro else 0.5, (120, 120, 120) if claro else (0, 0, 0))
    fg = (25, 25, 25) if claro else (235, 235, 235)
    txt = cena["texto"]
    f = fonte(cena.get("fonte", "cursiva"), cena.get("tamanho", 150))
    dur = (cena["fim"] - cena["inicio"]) * cena.get("ritmo", 0.7)
    n = int(len(txt) * min(1, t / max(.01, dur))) + 1
    d = ImageDraw.Draw(img)
    linhas = quebrar(txt.split(), f, W * .8)
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
    img = ctx.fx.solido(bg)
    # hífen só fica visível na última sílaba mostrada ("a mi-" -> "a minha")
    s = "".join(silabas[:max(0, n - 1)]).replace("-", "") + (silabas[n - 1] if n else "")
    if n == len(silabas):
        s = s.rstrip("-")
    f = fonte(cena.get("fonte", "medium"), cena.get("tamanho", 74))
    ImageDraw.Draw(img).text((W / 2, H / 2), s, font=f, fill=fg, anchor="mm")
    return img


def est_circulo(cv, cena, t, ctx):
    W, H = ctx.W, ctx.H
    img = ctx.fx.solido(cena.get("bg", "#000000"))
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
        f = fonte(cena.get("fonte", "black"), cena.get("tamanho", 66))
        ImageDraw.Draw(img).text((W / 2, H / 2), " ".join(palavras[:n]), font=f, fill=(15, 15, 15), anchor="mm")
    return img


ESTILOS = dict(revelar=est_revelar, pilha=est_pilha, flash=est_flash, gigante=est_gigante,
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
        img = ESTILOS[cena["estilo"]](None, cena, t, ctx)
        # tremida de câmera opcional em batidas
        for b in proj.get("batidas", []):
            if 0 <= tempo - b < 0.18:
                k = 1 - (tempo - b) / 0.18
                z = 1 + 0.06 * k
                w, h = int(ctx.W * z), int(ctx.H * z)
                img = img.resize((w, h)).crop(((w - ctx.W) // 2, (h - ctx.H) // 2, (w - ctx.W) // 2 + ctx.W, (h - ctx.H) // 2 + ctx.H))
        # fade curtinho entre cenas
        fade = cena.get("fade", 0.12)
        restante = cena["fim"] - tempo
        if fade and restante < fade:
            img = Image.blend(img, ctx.fx.solido("#000"), 1 - restante / fade)
    return ctx.fx.grao(img, idx, proj.get("grao", 0.05))


def render(proj, saida, audio=None, inicio=0.0, preview=False):
    W, H, fps = proj.get("w", 1080), proj.get("h", 1920), proj.get("fps", 30)
    ctx = Ctx()
    ctx.W, ctx.H = W, H
    ctx.fx = Fundos(W, H)
    dur = proj.get("duracao", max(c["fim"] for c in proj["cenas"]))
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
        cmd += ["-ss", str(inicio), "-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
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
    render(proj, saida, a.audio or proj.get("audio"), a.inicio or proj.get("audio_inicio", 0), a.preview)
