"""Folhas de referencia geradas do proprio 3D: personagem (4 vistas), cenario e storyboard."""
import math
from pathlib import Path

import bpy
from PIL import Image, ImageDraw, ImageFont

FONTE = Path(__file__).resolve().parent.parent / "shorts" / "fontes" / "Inter-ExtraBold.otf"


def _fonte(t):
    return ImageFont.truetype(str(FONTE), t)


def configurar_render(cena, larg, alt, amostras):
    cena.render.engine = "CYCLES"
    cena.cycles.device = "CPU"
    cena.cycles.samples = amostras
    cena.cycles.use_denoising = True
    cena.render.resolution_x, cena.render.resolution_y = larg, alt
    cena.render.resolution_percentage = 100
    cena.render.image_settings.file_format = "PNG"
    cena.view_settings.view_transform = "AgX"
    cena.view_settings.look = "AgX - Medium High Contrast"


def foto(cena, caminho):
    cena.render.filepath = str(caminho)
    bpy.ops.render.render(write_still=True)
    return Image.open(caminho).convert("RGB")


def montar_grade(imgs, rotulos, destino, colunas, titulo=None, legendas=None, fundo=(232, 228, 220)):
    """Grade de imagens com rotulo cinza em cima (como uma model sheet) e texto opcional embaixo."""
    w, h = imgs[0].size
    margem, topo, base = 30, 90, (300 if legendas else 30)
    linhas = math.ceil(len(imgs) / colunas)
    extra = 110 if titulo else 0
    folha = Image.new("RGB", (colunas * (w + margem) + margem, extra + linhas * (h + topo + base)), fundo)
    d = ImageDraw.Draw(folha)
    if titulo:
        d.text((margem, 30), titulo, font=_fonte(40), fill=(40, 30, 25))
    for i, (img, rot) in enumerate(zip(imgs, rotulos)):
        c, l = i % colunas, i // colunas
        x, y = margem + c * (w + margem), extra + l * (h + topo + base) + topo
        f = _fonte(34)
        tw = d.textlength(rot, font=f)
        d.rectangle((x + (w - tw) / 2 - 22, y - 70, x + (w + tw) / 2 + 22, y - 18), fill=(190, 186, 178))
        d.text((x + (w - tw) / 2, y - 66), rot, font=f, fill=(25, 20, 18))
        folha.paste(img, (x, y))
        if legendas:
            f2 = _fonte(24)
            linha, yy = "", y + h + 12
            for palavra in legendas[i].split():
                if d.textlength(linha + " " + palavra, font=f2) > w:
                    d.text((x, yy), linha.strip(), font=f2, fill=(40, 30, 25))
                    linha, yy = "", yy + 32
                linha += " " + palavra
            d.text((x, yy), linha.strip(), font=f2, fill=(40, 30, 25))
    folha.save(destino, quality=92)
    return destino


def folha_personagem(destino, tmp, criar_personagem, mats):
    """Cena de estudio separada: fundo claro, luz de tres pontos, 4 vistas como a referencia."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cena = bpy.context.scene
    configurar_render(cena, 600, 1000, 48)
    cena.view_settings.look = "AgX - Base Contrast"
    col = cena.collection
    p = criar_personagem(col, mats())
    p["luz"].data.energy = 3
    mundo = bpy.data.worlds.new("estudio")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.45, 0.43, 0.40, 1)
    mundo.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    cena.world = mundo
    for nome, loc, en in (("chave", (-2, -3, 3.5), 500), ("recorte", (2.5, 2.5, 3), 500), ("preench", (3, -2, 1.5), 150)):
        l = bpy.data.lights.new(nome, "AREA")
        l.energy, l.size = en, 2.5
        o = bpy.data.objects.new(nome, l)
        o.location = loc
        col.objects.link(o)
        o.rotation_euler = (Vector_to_rot(loc, (0, 0, 1)))
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = 85
    cam = bpy.data.objects.new("cam", cam_d)
    cam.location = (0, -5.6, 0.95)
    cam.rotation_euler = (math.radians(90.5), 0, 0)
    col.objects.link(cam)
    cena.camera = cam
    imgs = []
    for ang in (0, -90, 90, 180):
        p["raiz"].rotation_euler = (0, 0, math.radians(ang))
        imgs.append(foto(cena, tmp / f"vista_{ang}.png"))
    return montar_grade(imgs, ["FRENTE", "LADO ESQUERDO", "LADO DIREITO", "COSTAS"], destino, 4,
                        "MESTRE ELIAS - FOLHA DO PERSONAGEM")


def Vector_to_rot(origem, alvo):
    from mathutils import Vector
    return (Vector(alvo) - Vector(origem)).to_track_quat("-Z", "Y").to_euler()
