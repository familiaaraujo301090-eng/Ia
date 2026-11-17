"""
Cenários originais com clima de anime (cel-shading, luz quente), desenhados por código.
Nenhum personagem, quadro ou arte de anime é copiado: são paisagens/objetos genéricos.

Elementos (use em "elementos"): por_do_sol, crepusculo, muralha, cachecol, janela, campo_azul
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from elementos import Elementos, _ruido_fractal

_cache = {}


def _grad(W, H, paradas):
    """Degradê vertical com paradas [(pos 0..1, (r,g,b)), ...]."""
    y = np.linspace(0, 1, H)[:, None]
    out = np.zeros((H, 1, 3), np.float32)
    for (p0, c0), (p1, c1) in zip(paradas, paradas[1:]):
        m = (y >= p0) & (y <= p1)
        u = np.clip((y - p0) / max(1e-6, p1 - p0), 0, 1)
        for k in range(3):
            out[..., k] = np.where(m, c0[k] + (c1[k] - c0[k]) * u, out[..., k])
    return Image.fromarray(np.repeat(out, W, axis=1).astype(np.uint8))


def _morro(W, H, base, amp, semente, suave=6):
    rng = np.random.default_rng(semente)
    pts = rng.random(suave + 2)
    xs = np.linspace(0, W, suave + 2)
    xx = np.arange(W + 1)
    ys = np.interp(xx, xs, pts)
    ys = np.convolve(ys, np.ones(80) / 80, mode="same")
    return [(0, H)] + [(int(x), int(base - amp * y)) for x, y in zip(xx[::6], ys[::6])] + [(W, H)]


def _nuvens(s, W, H, tempo, vel, topo, base, sombra, luz, meio, semente=0, escala=1.0):
    """Cúmulos estilo anime: aglomerado de bolhas com 3 tons (sombra embaixo, meio, brilho no topo)."""
    hh = int(base - topo)
    key = ("cumulos", W, hh, semente)
    if key not in _cache:
        rng = random.Random(100 + semente)
        nuvens = []
        for k in range(7):
            cx = rng.uniform(0, W * 1.6)
            cy = rng.uniform(0.22, 0.75) * hh
            R = rng.uniform(0.06, 0.12) * W * escala
            bolhas = []
            for b in range(rng.randint(9, 15)):
                ox = rng.uniform(-1.7, 1.7)
                oy = -rng.uniform(0, 0.9) * (1 - abs(ox) / 2.2)
                r = R * rng.uniform(0.45, 0.95) * (1 - abs(ox) / 3.2)
                bolhas.append((ox * R, oy * R, r))
            bolhas.append((0, R * 0.15, R * 1.2))  # base achatada
            nuvens.append((cx, cy, R, bolhas))
        _cache[key] = nuvens
    nuvens = _cache[key]
    tudo = Image.new("L", (W, hh), 0)
    meio_m = Image.new("L", (W, hh), 0)
    luz_m = Image.new("L", (W, hh), 0)
    da, dm, dl = ImageDraw.Draw(tudo), ImageDraw.Draw(meio_m), ImageDraw.Draw(luz_m)
    larg = W * 1.6
    for cx, cy, R, bolhas in nuvens:
        x0 = (cx + tempo * vel) % larg - W * 0.3
        for bx, by, r in bolhas:
            x, y = x0 + bx, cy + by
            if by > R * 0.1:  # a base achatada é elipse
                da.ellipse([x - r * 1.6, y - r * 0.35, x + r * 1.6, y + r * 0.35], fill=255)
                continue
            da.ellipse([x - r, y - r, x + r, y + r], fill=255)
            r2 = r * 0.86
            dm.ellipse([x - r2 - r * 0.10, y - r2 - r * 0.20, x + r2 - r * 0.10, y + r2 - r * 0.20], fill=255)
            r3 = r * 0.55
            dl.ellipse([x - r3 - r * 0.22, y - r3 - r * 0.38, x + r3 - r * 0.22, y + r3 - r * 0.38], fill=255)
    meio_m = ImageChops.multiply(meio_m, tudo)
    luz_m = ImageChops.multiply(luz_m, meio_m)
    c = Image.new("RGB", (W, hh), sombra)
    c.paste(Image.new("RGB", (W, hh), meio), (0, 0), meio_m.filter(ImageFilter.GaussianBlur(1)))
    c.paste(Image.new("RGB", (W, hh), luz), (0, 0), luz_m.filter(ImageFilter.GaussianBlur(1)))
    return c, tudo.filter(ImageFilter.GaussianBlur(1.2))


def _arvore(d, x, y, esc, cor):
    d.line([(x, y), (x - 4 * esc, y - 120 * esc)], fill=cor, width=int(16 * esc))
    d.line([(x - 4 * esc, y - 90 * esc), (x + 40 * esc, y - 140 * esc)], fill=cor, width=int(8 * esc))
    rng = random.Random(int(x))
    for _ in range(26):
        cx = x + rng.uniform(-95, 95) * esc
        cy = y - 160 * esc + rng.uniform(-60, 45) * esc
        r = rng.uniform(32, 60) * esc
        d.ellipse([cx - r, cy - r * 0.85, cx + r, cy + r * 0.85], fill=cor)


def _ceu_quente(s, W, H, tempo, escuro=False):
    key = ("ceu", W, H, escuro)
    if key not in _cache:
        if escuro:
            _cache[key] = _grad(W, H, [(0, (24, 22, 52)), (0.45, (120, 60, 90)), (0.7, (236, 128, 80)), (1, (250, 190, 120))])
        else:
            _cache[key] = _grad(W, H, [(0, (52, 70, 128)), (0.4, (214, 118, 110)), (0.66, (246, 160, 92)), (1, (255, 222, 160))])
    return _cache[key].copy()


def _sol_e_raios(img, W, H, sx, sy, tempo, forte=1.0):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for k in range(14):
        a = k * math.pi / 7 + tempo * 0.03
        L = W * 1.2
        w = 0.035 + 0.02 * math.sin(k * 2.3)
        d.polygon([(sx, sy), (sx + L * math.cos(a - w), sy + L * math.sin(a - w)), (sx + L * math.cos(a + w), sy + L * math.sin(a + w))],
                  fill=int(28 * forte))
    m = m.filter(ImageFilter.GaussianBlur(18))
    d2 = ImageDraw.Draw(m)
    for r, v in ((150, 70), (90, 140), (55, 255)):
        d2.ellipse([sx - r, sy - r, sx + r, sy + r], fill=v)
    m = m.filter(ImageFilter.GaussianBlur(10))
    return Image.composite(Image.new("RGB", (W, H), (255, 244, 214)), img, m)


def _faiscas(img, W, H, tempo, n=60, cor=(255, 210, 150), semente=3):
    rng = random.Random(semente)
    cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cam)
    for i in range(n):
        x0, y0, z, f = rng.random(), rng.random(), rng.uniform(0.3, 1), rng.random() * 6.28
        x = ((x0 + tempo * 0.03 * z) % 1.1 - 0.05) * W
        y = ((y0 - tempo * 0.04 * z) % 1.1 - 0.05) * H + 10 * math.sin(tempo + f)
        r = 1.5 + 3 * z
        d.ellipse([x - r, y - r, x + r, y + r], fill=cor + (int(200 * z * (0.6 + 0.4 * math.sin(tempo * 3 + f))),))
    cam = cam.filter(ImageFilter.GaussianBlur(1.2))
    img.paste(cam, (0, 0), cam)
    return img


# ------------------------------------------------------------------ cenas
def por_do_sol(s, img, tempo, t, cena, claro, escuro=False):
    W, H = img.size
    ceu = _ceu_quente(s, W, H, tempo, escuro)
    sx, sy = W * 0.70, H * (0.60 + 0.02 * math.sin(t * 0.2))
    ceu = _sol_e_raios(ceu, W, H, sx, sy, tempo, 0.7 if escuro else 1.0)
    c, m = _nuvens(s, W, H, tempo, 14, 0, H * 0.55, (150, 78, 112), (255, 196, 150), (222, 128, 122) if not escuro else (150, 80, 110))
    ceu.paste(c, (0, 0), m)
    d = ImageDraw.Draw(ceu)
    par = t * 6
    cores = [(196, 110, 96), (112, 58, 70), (40, 24, 34)] if not escuro else [(120, 64, 80), (60, 32, 50), (18, 12, 22)]
    for i, (base, amp, cor) in enumerate(zip((0.70, 0.78, 0.88), (90, 110, 90), cores)):
        pts = _morro(W + 200, H, H * base, amp, 10 + i)
        pts = [(x - 100 - par * (i + 1) * 0.6, y) for x, y in pts]
        d.polygon(pts, fill=cor)
    # grama balançando na frente
    rng = random.Random(5)
    for k in range(160):
        x = rng.random() * W
        y = H * 0.86 + rng.random() * H * 0.16
        L = rng.uniform(18, 42)
        bal = 8 * math.sin(tempo * 2.2 + x * 0.01)
        d.line([(x, y), (x + bal, y - L)], fill=cores[2], width=3)
    _arvore(d, W * 0.18 - par * 1.6, H * 0.86, 1.2, cores[2])
    ceu = _faiscas(ceu, W, H, tempo, 40)
    return ceu


def crepusculo(s, img, tempo, t, cena, claro):
    return por_do_sol(s, img, tempo, t, cena, claro, escuro=True)


def muralha(s, img, tempo, t, cena, claro):
    W, H = img.size
    ceu = _ceu_quente(s, W, H, tempo, cena.get("escuro", False))
    ceu = _sol_e_raios(ceu, W, H, W * 0.25, H * 0.40, tempo, 0.8)
    c, m = _nuvens(s, W, H, tempo, 10, 0, H * 0.45, (140, 74, 104), (255, 200, 156), (210, 124, 120), semente=2)
    ceu.paste(c, (0, 0), m)
    d = ImageDraw.Draw(ceu)
    zoom = 1 + 0.04 * t
    topo, base = H * (0.40 - 0.03 * zoom), H * 0.80
    cor_m, cor_j = (150, 96, 92), (118, 72, 74)
    d.rectangle([0, topo, W, base], fill=cor_m)
    # luz quente no topo, sombra embaixo
    for i in range(40):
        y = topo + (base - topo) * i / 40
        d.line([(0, y), (W, y)], fill=tuple(int(v * (1.12 - 0.5 * i / 40)) for v in cor_m), width=int((base - topo) / 40) + 1)
    linhas = 9
    for i in range(1, linhas):
        y = topo + (base - topo) * i / linhas
        d.line([(0, y), (W, y)], fill=cor_j, width=2)
        off = (i % 2) * 45
        for x in range(-90 + off, W + 90, 90):
            d.line([(x, y - (base - topo) / linhas), (x, y)], fill=cor_j, width=2)
    d.line([(0, topo), (W, topo)], fill=(255, 210, 160), width=4)
    d.rectangle([0, base, W, H], fill=(36, 24, 30))
    rng = random.Random(9)
    for k in range(120):
        x, y = rng.random() * W, base + rng.random() * (H - base)
        d.line([(x, y), (x + 6 * math.sin(tempo * 2 + x), y - rng.uniform(14, 34))], fill=(20, 14, 18), width=3)
    # pássaros
    for i in range(7):
        bx = ((0.1 + i * 0.13 + tempo * 0.035) % 1.2 - 0.1) * W
        by = H * (0.18 + 0.05 * math.sin(i * 1.7)) + 8 * math.sin(tempo * 2 + i)
        asa = 10 + 6 * math.sin(tempo * 9 + i * 2)
        d.line([(bx - 16, by - asa), (bx, by), (bx + 16, by - asa)], fill=(40, 26, 40), width=3, joint="curve")
    ceu = _faiscas(ceu, W, H, tempo, 30)
    return ceu


def cachecol(s, img, tempo, t, cena, claro):
    """Cachecol vermelho tremulando ao vento contra o céu."""
    W, H = img.size
    ceu = _ceu_quente(s, W, H, tempo).filter(ImageFilter.GaussianBlur(3))
    c, m = _nuvens(s, W, H, tempo, 30, 0, H * 0.7, (160, 84, 116), (255, 206, 162), (224, 134, 126), semente=4)
    ceu.paste(c, (0, 0), m)
    cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(cam)
    yb = H * cena.get("cachecol_y", 0.42)
    voa = cena.get("cachecol_voa", 0.0) * t * 120  # sobe/afasta com o tempo (despedida)
    larg0 = H * 0.13
    n = 60
    cima, baixo, sombras = [], [], []
    for i in range(n + 1):
        u = i / n
        x = -W * 0.1 + u * W * 1.25
        amp = 20 + 110 * u
        fase = u * 7 - tempo * 4.2
        y = yb - voa * u + amp * math.sin(fase) + 25 * math.sin(fase * 0.5 + 1)
        larg = larg0 * (1 - 0.25 * u) * (0.75 + 0.25 * math.cos(fase))  # torção
        cima.append((x, y - larg / 2))
        baixo.append((x, y + larg / 2))
        sombras.append(math.cos(fase))
    for i in range(n):
        tom = sombras[i]
        k = 0.55 + 0.45 * (tom * 0.5 + 0.5)
        cor = (int(190 * k), int(22 * k), int(38 * k))
        d.polygon([cima[i], cima[i + 1], baixo[i + 1], baixo[i]], fill=cor + (255,))
        if tom > 0.85:  # brilho do tecido
            d.line([cima[i], cima[i + 1]], fill=(255, 140, 130, 160), width=3)
    # franja na ponta
    xe, ye1 = cima[-1]
    _, ye2 = baixo[-1]
    for k in range(9):
        yy = ye1 + (ye2 - ye1) * k / 8
        d.line([(xe, yy), (xe + 40 + 8 * math.sin(tempo * 9 + k), yy + 10 * math.sin(tempo * 7 + k))], fill=(150, 18, 30, 255), width=4)
    sombra = cam.getchannel("A").filter(ImageFilter.GaussianBlur(20)).point(lambda v: int(v * 0.35))
    ceu = Image.composite(Image.new("RGB", (W, H), (60, 20, 40)), ceu, ImageChops.offset(sombra, 20, 30))
    ceu.paste(cam, (0, 0), cam)
    return _faiscas(ceu, W, H, tempo, 30)


def janela(s, img, tempo, t, cena, claro):
    """Interior quente: luz de fim de tarde entrando pela janela, feixes e poeira."""
    W, H = img.size
    key = ("jan", W, H)
    if key not in _cache:
        _cache[key] = _grad(W, H, [(0, (40, 24, 18)), (0.7, (70, 40, 26)), (1, (30, 18, 14))])
    base = _cache[key].copy()
    jx0, jy0, jx1, jy1 = W * 0.08, H * 0.10, W * 0.36, H * 0.55
    luz = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(luz)
    dx = W * 0.55 + 20 * math.sin(tempo * 0.3)
    d.polygon([(jx0, jy0), (jx1, jy0), (jx1 + dx, H), (jx0 + dx * 0.55, H)], fill=60)
    luz = luz.filter(ImageFilter.GaussianBlur(30))
    d = ImageDraw.Draw(luz)
    d.rectangle([jx0, jy0, jx1, jy1], fill=255)
    luz = luz.filter(ImageFilter.GaussianBlur(4))
    base = Image.composite(Image.new("RGB", (W, H), (255, 228, 176)), base, luz)
    d2 = ImageDraw.Draw(base)
    cor = (34, 20, 16)
    d2.rectangle([jx0, jy0, jx1, jy1], outline=cor, width=14)
    d2.line([((jx0 + jx1) / 2, jy0), ((jx0 + jx1) / 2, jy1)], fill=cor, width=10)
    d2.line([(jx0, (jy0 + jy1) / 2), (jx1, (jy0 + jy1) / 2)], fill=cor, width=10)
    # cortina balançando
    pts = [(jx1 + 10 + 18 * math.sin(tempo * 1.2 + y * 0.02), y) for y in range(int(jy0 - 20), int(jy1 + 60), 8)]
    d2.polygon(pts + [(jx1 + 90, jy1 + 60), (jx1 + 90, jy0 - 20)], fill=(120, 60, 40))
    base = _faiscas(base, W, H, tempo, 80, (255, 236, 200), 8)
    return base


def campo_azul(s, img, tempo, t, cena, claro):
    W, H = img.size
    key = ("azul", W, H)
    if key not in _cache:
        _cache[key] = _grad(W, H, [(0, (40, 110, 200)), (0.55, (150, 205, 245)), (1, (220, 240, 255))])
    ceu = _cache[key].copy()
    c, m = _nuvens(s, W, H, tempo, 12, 0, H * 0.55, (176, 196, 228), (255, 255, 255), (226, 236, 250), semente=6)
    ceu.paste(c, (0, 0), m)
    d = ImageDraw.Draw(ceu)
    par = t * 5
    for i, (b, a, cor) in enumerate(zip((0.62, 0.70), (60, 70), ((120, 160, 150), (70, 120, 90)))):
        pts = _morro(W + 200, H, H * b, a, 30 + i)
        d.polygon([(x - 100 - par * (i + 1) * 0.5, y) for x, y in pts], fill=cor)
    d.rectangle([0, H * 0.74, W, H], fill=(46, 96, 64))
    _arvore(d, W * 0.12 - par, H * 0.76, 1.3, (30, 66, 48))
    rng = random.Random(12)
    for k in range(900):
        x = rng.random() * W
        yy = rng.random()
        y = H * 0.74 + (yy ** 1.6) * H * 0.27
        z = 0.3 + yy
        r = 2 + 7 * z * z
        bal = 5 * z * math.sin(tempo * 2 + x * 0.02)
        cor = rng.choice([(58, 78, 200), (92, 110, 232), (130, 150, 255), (40, 52, 160)])
        d.ellipse([x + bal - r, y - r, x + bal + r, y + r * 0.8], fill=cor)
    return _faiscas(ceu, W, H, tempo, 40, (255, 255, 255), 14)


for _f in (por_do_sol, crepusculo, muralha, cachecol, janela, campo_azul):
    setattr(Elementos, _f.__name__, _f)
