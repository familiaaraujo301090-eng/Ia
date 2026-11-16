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
