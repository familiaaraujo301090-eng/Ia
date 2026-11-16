"""
Elementos dinâmicos (preto e branco) desenhados POR TRÁS da letra.
Uso numa cena:  "elementos": ["perfil", "fumaca", "particulas"]
ou no projeto inteiro: "elementos": [...]  (a cena pode sobrescrever)

  particulas  poeira/bokeh subindo devagar, piscando
  fumaca      névoa que se move (fica linda com "perfil")
  perfil      silhueta de rosto de perfil, soprando fumaça pela boca
  lua         esfera grande com textura, subindo atrás do texto
  traco       traços de desenho a lápis sendo desenhados (estilo sketch)
  aneis       anéis que nascem no centro a cada batida
  linhas      linhas finas atravessando a tela (scanner)
  luz         vazamento de luz/flash branco nas batidas
  chuva       riscos finos caindo, com profundidade
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops


def _ruido_fractal(w, h, semente, oitavas=5):
    rng = np.random.default_rng(semente)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(oitavas):
        s = 2 ** (o + 2)
        r = rng.random((max(2, int(s * h / w)), s)).astype(np.float32)
        r = np.asarray(Image.fromarray((r * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
        acc += r * amp
        tot += amp
        amp *= 0.55
    acc /= tot
    acc = (acc - acc.min()) / (acc.max() - acc.min() + 1e-9)
    return acc


def _catmull(pts, n=12):
    out = []
    P = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1])
    return out


# perfil virado pra esquerda (unidades: altura do rosto ~1). Desenho original.
PERFIL = [(1.10, -0.55), (0.70, -0.62), (0.40, -0.52), (0.24, -0.30), (0.20, -0.08), (0.17, 0.00),
          (0.20, 0.04), (0.04, 0.17), (0.07, 0.21), (0.17, 0.22), (0.15, 0.28), (0.18, 0.31),
          (0.21, 0.32), (0.16, 0.36), (0.17, 0.40), (0.22, 0.44), (0.18, 0.53), (0.24, 0.60),
          (0.42, 0.64), (0.44, 0.80), (0.40, 1.30), (1.40, 1.30), (1.40, -0.55)]
BOCA = (0.10, 0.32)


class Elementos:
    def __init__(s, W, H):
        s.W, s.H = W, H
        s.nevoa = _ruido_fractal(W // 4 + 200, H // 4 + 200, 11)
        s._lua = None
        rng = random.Random(5)
        s.part = [(rng.random(), rng.random(), rng.uniform(0.3, 1), rng.random() * 6.28, rng.random()) for _ in range(140)]
        s.gotas = [(rng.random(), rng.random(), rng.uniform(0.4, 1)) for _ in range(90)]
        s.tracos = []
        for _ in range(9):
            x0, y0 = rng.uniform(-0.1, 1.1), rng.uniform(0.05, 0.95)
            pts = [(x0, y0)]
            ang = rng.uniform(0, 6.28)
            for _ in range(6):
                ang += rng.uniform(-0.9, 0.9)
                pts.append((pts[-1][0] + math.cos(ang) * 0.12, pts[-1][1] + math.sin(ang) * 0.07))
            s.tracos.append(_catmull(pts, 10))

    # -------------------------------------------------------------- util
    def _tom(s, img):
        """Cor dos elementos conforme o fundo: claro no escuro e escuro no claro."""
        px = [img.getpixel((x, y)) for x, y in ((40, 40), (s.W // 2, 60), (s.W - 40, s.H // 2), (60, s.H - 60))]
        lum = sum(0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2] for p in px) / len(px)
        return (lum > 128), lum

    def _sobre(s, img, cam, alpha=1.0):
        if alpha < 1:
            cam.putalpha(cam.getchannel("A").point(lambda v: int(v * alpha)))
        img.paste(cam, (0, 0), cam)
        return img

    # -------------------------------------------------------------- elementos
    def particulas(s, img, tempo, t, cena, claro):
        W, H = s.W, s.H
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(cam)
        c = (20, 20, 20) if claro else (235, 235, 235)
        for i, (x, y, z, fase, b) in enumerate(s.part):
            yy = ((y - tempo * 0.018 * z) % 1.1) - 0.05
            xx = x + 0.015 * math.sin(tempo * 0.6 + fase)
            r = 1 + 3.2 * z ** 2
            a = int(255 * (0.25 + 0.6 * z) * (0.6 + 0.4 * math.sin(tempo * 3 * b + fase)))
            if b > 0.88:  # bokeh grande e suave
                r *= 5
                a //= 4
            d.ellipse([xx * W - r, yy * H - r, xx * W + r, yy * H + r], fill=c + (a,))
        return s._sobre(img, cam.filter(ImageFilter.GaussianBlur(1.2)))

    def fumaca(s, img, tempo, t, cena, claro, mascara_y=None):
        W, H = s.W, s.H
        ox = int(60 + 50 * math.sin(tempo * 0.13)) + int(tempo * 9) % 120
        oy = int(100 - tempo * 14) % 180
        n = s.nevoa[oy:oy + H // 4, ox:ox + W // 4]
        n = np.clip((n - 0.45) * 2.2, 0, 1) ** 1.4
        m = Image.fromarray((n * 255 * cena.get("fumaca_forca", 0.38)).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        m = m.filter(ImageFilter.GaussianBlur(6))
        c = (25, 25, 25) if claro else (200, 200, 200)
        return Image.composite(Image.new("RGB", (W, H), c), img, m)

    def perfil(s, img, tempo, t, cena, claro):
        W, H = s.W, s.H
        lado = cena.get("perfil_lado", "direita")
        esc = H * 0.42
        bx, by = W * (0.62 if lado == "direita" else 0.38), H * 0.42
        bx += math.sin(tempo * 0.5) * 6
        pts = PERFIL
        if lado != "direita":
            pts = [(-x + 0.6, y) for x, y in pts]
        cont = [(bx + (x - 0.4) * esc, by + y * esc) for x, y in _catmull(pts, 8)]
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(cam)
        corpo = (190, 190, 190) if claro else (58, 58, 58)
        borda = (70, 70, 70) if claro else (215, 215, 215)
        d.polygon(cont, fill=corpo + (255,))
        d.line(cont[:-3], fill=borda + (110,), width=10)  # halo de luz de recorte
        d.line(cont[:-3], fill=borda + (235,), width=3)   # contorno nítido
        cam = cam.filter(ImageFilter.GaussianBlur(1.5))
        img = s._sobre(img, cam, min(1, t / 0.4))
        # fumaça saindo da boca
        mx = bx + ((BOCA[0] if lado == "direita" else -BOCA[0] + 0.6) - 0.4) * esc
        my = by + BOCA[1] * esc
        fum = Image.new("L", (W, H), 0)
        df = ImageDraw.Draw(fum)
        dirx = -1 if lado == "direita" else 1
        for k in range(26):
            idade = (tempo * 0.7 + k / 26) % 1.0
            px = mx + dirx * idade * W * 0.42 + math.sin(idade * 7 + k) * 40 * idade
            py = my - idade * H * 0.10 + math.cos(idade * 5 + k * 1.3) * 30 * idade
            r = 18 + idade * 120
            df.ellipse([px - r, py - r, px + r, py + r], fill=int(120 * (1 - idade) ** 1.3))
        fum = fum.filter(ImageFilter.GaussianBlur(28))
        c = (30, 30, 30) if claro else (225, 225, 225)
        return Image.composite(Image.new("RGB", (W, H), c), img, fum)

    def lua(s, img, tempo, t, cena, claro):
        W, H = s.W, s.H
        R = int(W * 0.34)
        if s._lua is None:
            y, x = np.mgrid[-R:R, -R:R].astype(np.float32)
            r = np.sqrt(x * x + y * y) / R
            dentro = np.clip((1 - r) * R / 2, 0, 1)
            nz = np.ones_like(r)
            tex = _ruido_fractal(2 * R, 2 * R, 21, 6)
            sombra = np.clip(1.15 - ((x + R * 0.35) ** 2 + (y + R * 0.3) ** 2) ** 0.5 / (R * 1.6), 0.25, 1)
            v = (0.62 + 0.38 * tex) * sombra * nz
            s._lua = (Image.fromarray((v * 255).astype(np.uint8)), Image.fromarray((dentro * 255).astype(np.uint8)))
        tex, alpha = s._lua
        sobe = (1 - min(1, t / 2.5)) * 80
        cx, cy = W // 2, int(H * 0.36 + sobe)
        brilho = Image.new("L", (W, H), 0)
        ImageDraw.Draw(brilho).ellipse([cx - R * 1.25, cy - R * 1.25, cx + R * 1.25, cy + R * 1.25], fill=70)
        brilho = brilho.filter(ImageFilter.GaussianBlur(60))
        img = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), img, brilho)
        cor = Image.merge("RGB", [tex] * 3)
        if claro:
            cor = ImageChops.invert(cor)
        forca = (0.55 if claro else 1.0) * min(1, t / 0.6)
        img.paste(cor, (cx - R, cy - R), alpha.point(lambda v: int(v * forca)))
        return img

    def traco(s, img, tempo, t, cena, claro):
        W, H = s.W, s.H
        dur = max(0.5, (cena["fim"] - cena["inicio"]) * 0.9)
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(cam)
        c = (30, 30, 30) if claro else (215, 215, 215)
        semente = int(cena["inicio"] * 10) % len(s.tracos)
        for j in range(5):
            tr = s.tracos[(semente + j) % len(s.tracos)]
            k = max(0.0, min(1.0, (t - j * 0.12) / dur))
            n = int(len(tr) * k)
            if n > 1:
                pts = [(x * W + math.sin(i * 0.7) * 2, y * H) for i, (x, y) in enumerate(tr[:n])]
                for w, a in ((12, 45), (3, 225)):  # grafite: halo + traço
                    d.line(pts, fill=c + (a,), width=w, joint="curve")
        return s._sobre(img, cam.filter(ImageFilter.GaussianBlur(0.8)))

    def aneis(s, img, tempo, t, cena, claro, batidas=()):
        W, H = s.W, s.H
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(cam)
        c = (20, 20, 20) if claro else (235, 235, 235)
        for b in list(batidas) + [cena["inicio"]]:
            idade = tempo - b
            if 0 <= idade < 1.4:
                e = 1 - (1 - idade / 1.4) ** 3
                r = 60 + e * W * 0.75
                a = int(200 * (1 - idade / 1.4))
                d.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], outline=c + (a,), width=3)
        return s._sobre(img, cam)

    def linhas(s, img, tempo, t, cena, claro):
        W, H = s.W, s.H
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(cam)
        c = (20, 20, 20) if claro else (230, 230, 230)
        for k in range(4):
            y = ((tempo * (0.08 + k * 0.03) + k * 0.27) % 1.2 - 0.1) * H
            d.line([(0, y), (W, y)], fill=c + (45,), width=14)  # brilho da linha
            d.line([(0, y), (W, y)], fill=c + (140 + 30 * k,), width=2 + (k == 0))
        return s._sobre(img, cam)

    def chuva(s, img, tempo, t, cena, claro):
        W, H = s.W, s.H
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(cam)
        c = (30, 30, 30) if claro else (220, 220, 220)
        for x, y, z in s.gotas:
            yy = ((y + tempo * 0.9 * z) % 1.2 - 0.1) * H
            xx = x * W - (yy / H) * 40
            L = 30 + 70 * z
            d.line([(xx, yy), (xx - 10 * z, yy + L)], fill=c + (int(50 + 120 * z),), width=1 + int(z > 0.8))
        return s._sobre(img, cam.filter(ImageFilter.GaussianBlur(0.6)))

    def luz(s, img, tempo, t, cena, claro, batidas=()):
        W, H = s.W, s.H
        for b in batidas:
            idade = tempo - b
            if 0 <= idade < 0.35:
                k = (1 - idade / 0.35) ** 2
                m = Image.new("L", (W, H), 0)
                ImageDraw.Draw(m).ellipse([-W * 0.3, -H * 0.1, W * 0.7, H * 0.5], fill=int(150 * k))
                m = m.filter(ImageFilter.GaussianBlur(120))
                img = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), img, m)
        return img

    # -------------------------------------------------------------- entrada
    def aplicar(s, img, lista, tempo, t, cena, batidas):
        if not lista:
            return img
        claro, _ = s._tom(img)
        for nome in lista:
            f = getattr(s, nome, None)
            if f is None:
                continue
            if nome in ("aneis", "luz"):
                img = f(img, tempo, t, cena, claro, batidas)
            else:
                img = f(img, tempo, t, cena, claro)
        return img


# ====================================================================== CASAL
# Dois perfis originais (virados pra ESQUERDA; espelhados quando preciso). Unidade = altura do rosto.
PERFIL_ELE = [(1.00, -0.55), (0.66, -0.67), (0.36, -0.56), (0.24, -0.39), (0.17, -0.16), (0.21, -0.07),
              (0.17, 0.01), (0.02, 0.18), (0.11, 0.22), (0.15, 0.25), (0.11, 0.29), (0.16, 0.31),
              (0.12, 0.34), (0.17, 0.39), (0.13, 0.48), (0.16, 0.56), (0.42, 0.60), (0.45, 0.75),
              (0.44, 1.00), (0.35, 1.40), (1.60, 1.40), (1.40, 0.90), (1.08, 0.55), (1.07, 0.00)]
BOCA_ELE = (0.11, 0.31)
PERFIL_ELA = [(1.08, -0.60), (0.72, -0.71), (0.40, -0.60), (0.26, -0.43), (0.20, -0.18), (0.23, -0.08),
              (0.19, 0.00), (0.08, 0.15), (0.14, 0.20), (0.17, 0.23), (0.115, 0.28), (0.18, 0.31),
              (0.125, 0.345), (0.19, 0.39), (0.155, 0.47), (0.22, 0.54), (0.40, 0.58), (0.42, 0.72),
              (0.40, 0.95), (0.30, 1.40), (1.60, 1.40), (1.40, 0.95), (1.30, 0.62), (1.24, 0.20),
              (1.17, -0.25)]
BOCA_ELA = (0.125, 0.31)
CABELO_ELE = [(0.30, -0.47), (0.36, -0.64), (0.62, -0.76), (0.98, -0.68), (1.13, -0.36), (1.10, 0.04),
              (0.99, -0.10), (0.86, -0.36), (0.60, -0.50), (0.42, -0.50)]
CABELO_ELA = [(0.28, -0.50), (0.42, -0.76), (0.80, -0.84), (1.16, -0.64), (1.34, -0.20), (1.40, 0.32),
              (1.48, 0.86), (1.36, 1.16), (1.20, 0.78), (1.08, 0.34), (0.98, -0.06), (0.74, -0.44),
              (0.48, -0.56)]
MECHA_ELA = [(0.60, -0.46), (0.70, -0.05), (0.66, 0.38), (0.58, 0.78), (0.50, 1.12), (0.64, 1.15),
             (0.77, 0.80), (0.86, 0.38), (0.90, -0.02), (0.84, -0.48)]
CILIOS_ELA = [((0.205, -0.075), (0.15, -0.10)), ((0.21, -0.065), (0.155, -0.075)), ((0.215, -0.055), (0.165, -0.05))]


def _contorno(pts, cx, cy, esc, espelhar):
    sx = -1 if espelhar else 1
    return [(cx + sx * (x - 0.4) * esc, cy + y * esc) for x, y in _catmull(pts, 10)]


def _amostrar_contorno(cont, n, rng):
    seg = [math.dist(cont[i], cont[i + 1]) for i in range(len(cont) - 1)]
    tot = sum(seg)
    out = []
    for k in range(n):
        alvo = tot * (k + rng.random() * 0.5) / n
        acc = 0
        for i, L in enumerate(seg):
            if acc + L >= alvo:
                u = (alvo - acc) / max(L, 1e-6)
                out.append((cont[i][0] + (cont[i + 1][0] - cont[i][0]) * u, cont[i][1] + (cont[i + 1][1] - cont[i][1]) * u))
                break
            acc += L
    return out


_FIOS = {}


def _fios(W, H, vertical):
    """Textura de fios de cabelo: ruído esticado numa direção."""
    if vertical not in _FIOS:
        rng = np.random.default_rng(31 + vertical)
        if vertical:
            r = rng.random((10, W // 5))
        else:
            r = rng.random((H // 9, 14))
        im = Image.fromarray((r * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
        _FIOS[vertical] = im.point(lambda v: int(max(0, v - 90) * 1.6))
    return _FIOS[vertical]


def _silhueta(W, H, cont, base, rim, alpha, luz_da_direita=True, cabelo=None, cabelo_vertical=True, cilios=()):
    """Silhueta com volume: miolo em degradê, cabelo com fios, luz de recorte só do lado do rosto."""
    m = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(m)
    dm.polygon(cont, fill=255)
    mc = None
    if cabelo:
        mc = Image.new("L", (W, H), 0)
        polis = cabelo if isinstance(cabelo[0][0], (list, tuple)) else [cabelo]
        for pl in polis:
            ImageDraw.Draw(mc).polygon(pl, fill=255)
        mc = mc.filter(ImageFilter.GaussianBlur(2.5))  # pontas macias
        m = ImageChops.lighter(m, mc)
    for (a, b) in cilios:
        dm2 = ImageDraw.Draw(m)
        dm2.line([a, b], fill=255, width=3)
    m = m.filter(ImageFilter.GaussianBlur(1.2))
    miolo = m.filter(ImageFilter.GaussianBlur(30))
    borda = ImageChops.subtract(m, miolo).point(lambda v: min(255, v * 3))
    lado = Image.linear_gradient("L").rotate(90 if luz_da_direita else -90).resize((W, H))
    borda = ImageChops.multiply(borda, lado.point(lambda v: int(40 + 215 * (v / 255) ** 1.6)))
    grad = Image.linear_gradient("L").resize((W, H)).point(lambda v: int(base * (1.2 - 0.45 * v / 255)))
    corpo = Image.merge("RGB", [grad] * 3)
    if mc is not None:
        # cabelo = massa mais escura que a pele + fios quase imperceptíveis (só dão textura)
        escuro = tuple(int(base * 0.45) for _ in range(3)) if base < 128 else tuple(int(base * 0.7) for _ in range(3))
        mc_d = ImageChops.subtract(mc, Image.new("L", (W, H), 0)).filter(ImageFilter.GaussianBlur(10))
        corpo = Image.composite(Image.new("RGB", (W, H), escuro), corpo, mc_d)
        f = _fios(W, H, cabelo_vertical).filter(ImageFilter.GaussianBlur(1.5))
        fios = ImageChops.multiply(f, mc).point(lambda v: int(v * 0.16))
        corpo = Image.composite(Image.new("RGB", (W, H), rim), corpo, fios)
    corpo = Image.composite(Image.new("RGB", (W, H), rim), corpo, borda)
    return corpo, m.point(lambda v: int(v * alpha))


def casal(s, img, tempo, t, cena, claro):
    """ELE respira, solta fumaça, e a fumaça forma o rosto DELA. Linha do tempo (s, a partir de casal_t0):
    0.0-0.5 inspira | 0.5 solta | 0.6-2.1 partículas viajam e desenham o rosto dela | 1.7-2.4 ela ganha corpo."""
    W, H = s.W, s.H
    T = tempo - cena.get("casal_t0", cena["inicio"])
    esc = H * 0.23
    cy = H * 0.33
    XA, XB = W * 0.25, W * 0.75
    base = 70 if not claro else 175
    rim = (225, 225, 225) if not claro else (60, 60, 60)
    # --- ELE (esquerda, olhando pra direita), respirando
    insp = math.sin(min(1, max(0, T / 0.5)) * math.pi / 2) if T < 0.5 else max(0, 1 - (T - 0.5) / 0.6)
    resp = 0.5 + 0.5 * math.sin(tempo * 2.1)  # respiração contínua bem leve
    dy = -7 * insp - 2 * resp
    e_esc = esc * (1 + 0.012 * insp)
    ele = _contorno(PERFIL_ELE, XA, cy + dy, e_esc, True)
    cab = _contorno(CABELO_ELE, XA, cy + dy, e_esc, True)
    corpo, m = _silhueta(W, H, ele, base, rim, min(1, (T + 0.6) / 0.5), True, cab, False)
    img = Image.composite(corpo, img, m)
    bx = XA + (BOCA_ELE[0] - 0.4) * esc * -1
    by = cy + dy + BOCA_ELE[1] * esc
    # --- DELA: pontos-alvo (contorno + miolo)
    if not hasattr(s, "_ela"):
        rng = random.Random(9)
        cont = _contorno(PERFIL_ELA, XB, cy, esc, False)
        cab = [_contorno(CABELO_ELA, XB, cy, esc, False), _contorno(MECHA_ELA, XB, cy, esc, False)]
        cil = [((XB + (a[0] - 0.4) * esc, cy + a[1] * esc), (XB + (b[0] - 0.4) * esc, cy + b[1] * esc)) for a, b in CILIOS_ELA]
        alvos = _amostrar_contorno(cont[:-5], 300, rng) + _amostrar_contorno(cab[0], 80, rng) + _amostrar_contorno(cab[1], 60, rng)
        mk = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mk).polygon(cont, fill=255)
        xs = [p[0] for p in cont]; ys = [p[1] for p in cont]
        while len(alvos) < 460:
            p = (rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), min(max(ys), cy + esc * 0.9)))
            if 0 <= p[0] < W and 0 <= p[1] < H and mk.getpixel((int(p[0]), int(p[1]))) > 0:
                alvos.append(p)
        dados = [(a, rng.random() * 0.45, rng.uniform(-1, 1), rng.uniform(-1, 1), rng.random() * 6.28) for a in alvos]
        s._ela = (cont, dados, cab, cil)
    cont, dados, cab, cil = s._ela
    # --- fumaça da expiração (nuvem que sai da boca dele)
    fum = Image.new("L", (W // 2, H // 2), 0)
    df = ImageDraw.Draw(fum)
    if 0.45 < T < 2.6:
        for k in range(18):
            idade = (T - 0.45) * 0.9 - k * 0.05
            if 0 < idade < 1.2:
                px = bx + idade * W * 0.28 + math.sin(idade * 6 + k) * 25
                py = by - idade * H * 0.05 + math.cos(idade * 4 + k * 1.7) * 20
                r = 14 + idade * 90
                a = int(110 * max(0, 1 - idade / 1.2) * min(1, idade * 6))
                df.ellipse([(px - r) / 2, (py - r) / 2, (px + r) / 2, (py + r) / 2], fill=a)
    # --- partículas que desenham o rosto dela
    for (ax, ay), atraso, j1, j2, fase in dados:
        k = (T - 0.6 - atraso) / 1.1
        if k <= 0:
            continue
        e = 1 - (1 - min(1, k)) ** 3
        c1 = ((bx + ax) / 2 + j1 * 60, min(by, ay) - H * 0.10 + j2 * 50)  # curva pra cima, como fumaça
        u = e
        px = (1 - u) ** 2 * bx + 2 * (1 - u) * u * c1[0] + u * u * ax
        py = (1 - u) ** 2 * by + 2 * (1 - u) * u * c1[1] + u * u * ay
        turb = (1 - e) * 35
        px += math.sin(tempo * 3 + fase) * turb + (math.sin(tempo * 1.3 + fase) * 3 if k > 1 else 0)
        py += math.cos(tempo * 2.6 + fase) * turb
        r = 10 + 34 * (1 - e)
        a = int(70 * min(1, k * 4) * (1 - 0.6 * max(0, min(1, (T - 2.2) / 0.8))))
        df.ellipse([(px - r) / 2, (py - r) / 2, (px + r) / 2, (py + r) / 2], fill=a)
    fum = fum.filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BICUBIC)
    # --- ela ganha corpo
    corpo_ela = max(0.0, min(1.0, (T - 1.7) / 0.7))
    if corpo_ela > 0:
        resp2 = 2 * math.sin(tempo * 1.9 + 1)
        mv = lambda L: [(x, y + resp2) for x, y in L]
        corpo, m = _silhueta(W, H, mv(cont), base, rim, corpo_ela, False, [mv(c) for c in cab], True,
                             [(mv([a])[0], mv([b])[0]) for a, b in cil])
        img = Image.composite(corpo, img, m)
    cor = (215, 215, 215) if not claro else (40, 40, 40)
    return Image.composite(Image.new("RGB", (W, H), cor), img, fum)


Elementos.casal = casal


# ====================================================================== PORTA (música: "me deixe entrar")
def porta(s, img, tempo, t, cena, claro):
    """Porta no fundo do quarto se abrindo: fresta -> vão de luz, luz derramando no chão,
    poeira no feixe e uma silhueta no vão quando abre. porta_t0 / porta_dur controlam a abertura."""
    W, H = s.W, s.H
    k = max(0.0, min(1.0, (tempo - cena.get("porta_t0", cena["inicio"])) / cena.get("porta_dur", 3.0)))
    abre = 1 - (1 - k) ** 2.2
    tremor = 1 + 0.03 * math.sin(tempo * 13) * math.sin(tempo * 3.1)  # luz viva, não de estúdio
    cx, topo, base = W * 0.5, H * 0.17, H * 0.56
    meia = W * (0.006 + 0.15 * abre)
    luz = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(luz)
    # chão: trapézio de luz em perspectiva
    d.polygon([(cx - meia, base), (cx + meia, base), (cx + meia * 4.2, H * 1.02), (cx - meia * 4.2, H * 1.02)],
              fill=int(80 * tremor))
    luz = luz.filter(ImageFilter.GaussianBlur(28))
    vao = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vao).rectangle([cx - meia, topo, cx + meia, base], fill=255)
    halo = vao.filter(ImageFilter.GaussianBlur(45)).point(lambda v: int(v * 0.8 * tremor))
    luz = ImageChops.lighter(luz, halo)
    luz = ImageChops.lighter(luz, vao.filter(ImageFilter.GaussianBlur(2)))
    # moldura da porta (sutil)
    mold = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mold).rectangle([cx - W * 0.155, topo - 8, cx + W * 0.155, base], outline=60, width=5)
    luz = ImageChops.lighter(luz, mold.filter(ImageFilter.GaussianBlur(1.5)))
    cor = (245, 243, 238) if not claro else (15, 15, 15)
    img = Image.composite(Image.new("RGB", (W, H), cor), img, luz)
    # silhueta no vão (aparece com a porta aberta)
    if abre > 0.55:
        a = min(1, (abre - 0.55) / 0.3)
        fig = Image.new("L", (W, H), 0)
        df = ImageDraw.Draw(fig)
        hx, hy, hr = cx + W * 0.008, topo + (base - topo) * 0.16, W * 0.034
        df.ellipse([hx - hr, hy - hr * 1.2, hx + hr, hy + hr * 1.15], fill=255)
        pe = (base - hy) / hr  # pés no chão do vão
        corpo = [(-0.45, 0.95), (0.45, 0.95), (0.6, 1.35), (2.2, 1.7), (2.6, 2.4), (2.7, 7.4), (2.25, 7.7),
                 (1.95, 3.4), (1.75, 8.2), (1.3, pe), (0.25, pe), (0.05, 9.2), (-0.15, pe), (-1.3, pe),
                 (-1.75, 8.2), (-1.9, 3.4), (-2.2, 7.7), (-2.7, 7.4), (-2.6, 2.4), (-2.2, 1.7), (-0.6, 1.35)]
        df.polygon([(hx + x * hr, hy + y * hr) for x, y in corpo], fill=255)
        fig = fig.filter(ImageFilter.GaussianBlur(3)).point(lambda v: int(v * a))
        fig = ImageChops.multiply(fig, vao.filter(ImageFilter.GaussianBlur(4)).point(lambda v: min(255, v * 2)))
        img = Image.composite(Image.new("RGB", (W, H), (12, 12, 12) if not claro else (240, 240, 240)), img, fig)
    # poeira no feixe
    if abre > 0.1:
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dp = ImageDraw.Draw(cam)
        for i, (x, y, z, fase, b) in enumerate(s.part[:70]):
            yy = topo + ((y + tempo * 0.02 * z) % 1) * (H - topo)
            larg = meia * (1 + 3.2 * (yy - base) / (H - base)) if yy > base else meia
            xx = cx + (x * 2 - 1) * larg
            r = 1 + 2.5 * z
            dp.ellipse([xx - r, yy - r, xx + r, yy + r], fill=cor + (int(150 * z * abre),))
        img.paste(cam, (0, 0), cam.filter(ImageFilter.GaussianBlur(0.8)))
    return img


# ====================================================================== VIDRO (música: "banheiro")
def vidro(s, img, tempo, t, cena, claro):
    """Vidro de box embaçado: vapor, gotas paradas e gotas escorrendo que limpam o vapor."""
    W, H = s.W, s.H
    w2, h2 = W // 2, H // 2
    if not hasattr(s, "_vidro"):
        rng = random.Random(77)
        s._vidro = ([(rng.random(), rng.random(), rng.uniform(1.5, 6)) for _ in range(520)],
                    [(rng.random(), rng.uniform(0.04, 0.16), rng.random(), rng.uniform(5, 10)) for _ in range(16)])
    paradas, correm = s._vidro
    # vapor (névoa clara) com respiração lenta
    nev = s.nevoa[40:40 + h2 // 2, 40:40 + w2 // 2]
    vapor = Image.fromarray((np.clip(0.55 + 0.45 * nev, 0, 1) * 255).astype(np.uint8)).resize((w2, h2), Image.BICUBIC)
    vapor = vapor.point(lambda v: int(v * (0.30 + 0.04 * math.sin(tempo * 0.7))))
    limpo = Image.new("L", (w2, h2), 0)
    dl = ImageDraw.Draw(limpo)
    gotas = Image.new("RGBA", (w2, h2), (0, 0, 0, 0))
    dg = ImageDraw.Draw(gotas)
    clara = (235, 235, 235) if not claro else (30, 30, 30)
    escura = (0, 0, 0) if not claro else (255, 255, 255)
    for x, y, r in paradas:
        px, py, rr = x * w2, y * h2, r / 2
        dg.ellipse([px - rr, py - rr, px + rr, py + rr], fill=escura + (70,))
        dg.ellipse([px - rr * 0.5, py - rr * 0.6, px - rr * 0.05, py - rr * 0.1], fill=clara + (170,))
    for x, vel, fase, r in correm:
        # escorre aos trancos (gota real para e solta)
        prog = (tempo * vel + fase) % 1.3
        y = (prog + 0.04 * math.sin(prog * 40 + fase * 9)) * h2
        px = x * w2 + 3 * math.sin(prog * 12 + fase * 5)
        for seg in range(10):  # rastro limpo que vai sumindo pra cima (o vapor volta)
            y0 = y - h2 * 0.30 * (seg + 1) / 10
            y1 = y - h2 * 0.30 * seg / 10
            dl.line([(px + math.sin(seg + fase) * 1.5, max(0, y0)), (px, y1)], fill=int(110 * (1 - seg / 10)),
                    width=max(2, int(r * 0.55)))
        rr = r / 2
        dg.ellipse([px - rr, y - rr * 1.3, px + rr, y + rr], fill=escura + (60,))
        dg.ellipse([px - rr * 0.5, y - rr, px, y - rr * 0.3], fill=clara + (210,))
    limpo = limpo.filter(ImageFilter.GaussianBlur(3.5))
    vapor = ImageChops.subtract(vapor, limpo)
    neb = (210, 210, 210) if not claro else (60, 60, 60)
    img = Image.composite(Image.new("RGB", (W, H), neb), img, vapor.resize((W, H), Image.BICUBIC))
    g = gotas.resize((W, H), Image.BICUBIC)
    img.paste(g, (0, 0), g)
    return img


Elementos.porta = porta
Elementos.vidro = vidro
