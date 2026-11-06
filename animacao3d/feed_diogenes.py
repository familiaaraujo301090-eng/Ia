"""Gera a textura do feed que rola na tela do celular (3 posts empilhados): carro novo, selfie com filtro, briga."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).parent
F = AQUI.parent / "shorts" / "fontes" / "Inter-ExtraBold.otf"
W, H = 540, 960


def fonte(t):
    return ImageFont.truetype(str(F), t)


def moldura(d, y0, nome, cor):
    d.rectangle((0, y0, W, y0 + H), fill=(250, 250, 250))
    d.ellipse((24, y0 + 30, 84, y0 + 90), fill=cor)
    d.text((100, y0 + 42), nome, font=fonte(30), fill=(20, 20, 20))
    d.text((W - 60, y0 + 34), "...", font=fonte(34), fill=(60, 60, 60))


def rodape(d, y0, curtidas, legenda):
    y = y0 + 720
    for k, x in enumerate((30, 110, 190)):
        d.ellipse((x, y, x + 50, y + 50), outline=(30, 30, 30), width=6)
    d.ellipse((30, y, 80, y + 50), fill=(235, 50, 80))
    d.text((30, y + 75), curtidas, font=fonte(32), fill=(20, 20, 20))
    d.text((30, y + 130), legenda, font=fonte(30), fill=(40, 40, 40))


img = Image.new("RGB", (W, H * 3), (250, 250, 250))
d = ImageDraw.Draw(img)
# post 1: o carro novo
moldura(d, 0, "ostentacao.top", (240, 160, 40))
d.rectangle((0, 120, W, 690), fill=(120, 170, 220))
d.rectangle((0, 520, W, 690), fill=(90, 90, 95))
d.rounded_rectangle((60, 380, 480, 520), 40, fill=(210, 30, 40))
d.polygon([(150, 380), (210, 300), (360, 300), (420, 380)], fill=(190, 25, 35))
d.polygon([(175, 375), (222, 315), (290, 315), (290, 375)], fill=(170, 210, 240))
d.polygon([(305, 375), (305, 315), (350, 315), (395, 375)], fill=(170, 210, 240))
for x in (140, 400):
    d.ellipse((x - 50, 470, x + 50, 570), fill=(25, 25, 25))
    d.ellipse((x - 22, 498, x + 22, 542), fill=(180, 180, 185))
rodape(d, 0, "2.341 curtidas", "Carro novo. Quem pode, pode.")
# post 2: a selfie com filtro
moldura(d, H, "vida.perfeita", (200, 90, 200))
y = H + 120
d.rectangle((0, y, W, y + 570), fill=(255, 205, 225))
d.ellipse((150, y + 110, 390, y + 380), fill=(250, 215, 190))
d.ellipse((205, y + 210, 235, y + 240), fill=(40, 30, 30))
d.ellipse((305, y + 210, 335, y + 240), fill=(40, 30, 30))
d.arc((215, y + 270, 325, y + 330), 10, 170, fill=(200, 60, 90), width=8)
for x, yy in ((80, 80), (460, 120), (420, 420), (100, 450), (270, 60)):
    d.regular_polygon((x, y + yy, 26), 4, rotation=45, fill=(255, 255, 255))
d.ellipse((140, y + 70, 400, y + 160), fill=(110, 70, 50))
rodape(d, H, "18.902 curtidas", "Acordei assim #semfiltro")
# post 3: a briga nos comentarios
moldura(d, 2 * H, "opiniao.forte", (60, 120, 220))
y = 2 * H + 130
bal = [("VOCÊ ESTÁ ERRADO!!", (255, 225, 225), (190, 20, 30)), ("ERRADO É VOCÊ!!!", (225, 235, 255), (20, 60, 170)),
       ("NEM LEU O POST", (255, 225, 225), (190, 20, 30)), ("BLOQUEADO.", (230, 230, 230), (40, 40, 40))]
for k, (t, fundo, cor) in enumerate(bal):
    x0 = 30 if k % 2 == 0 else 120
    d.rounded_rectangle((x0, y + k * 140, x0 + 390, y + k * 140 + 110), 30, fill=fundo)
    d.text((x0 + 28, y + k * 140 + 34), t, font=fonte(34), fill=cor)
rodape(d, 2 * H, "847 comentários", "Quem concorda? Fala aí")
img.save(AQUI / "texturas" / "feed-diogenes.png")
print("ok")
