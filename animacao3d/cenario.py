"""Cenario: biblioteca antiga de pedra, com estantes, colunas, mesa e velas. Tudo procedural."""
import math
import random

import bpy


def _cubo(nome, loc, escala, mat, col):
    """Caixa que compartilha uma unica malha; o material fica no objeto (rapido para centenas de livros)."""
    malha = bpy.data.meshes.get("_cubo_base")
    if malha is None:
        bpy.ops.mesh.primitive_cube_add(size=1)
        tmp = bpy.context.object
        malha = tmp.data
        malha.name = "_cubo_base"
        malha.materials.append(None)
        bpy.data.objects.remove(tmp)
    o = bpy.data.objects.new(nome, malha)
    o.location, o.scale = loc, escala
    col.objects.link(o)
    o.material_slots[0].link = "OBJECT"
    o.material_slots[0].material = mat
    return o


def _luz(nome, tipo, loc, energia, cor, col, tamanho=0.1, rot=None):
    d = bpy.data.lights.new(nome, tipo)
    d.energy, d.color = energia, cor
    if tipo == "AREA":
        d.size = tamanho
    else:
        d.shadow_soft_size = tamanho
    o = bpy.data.objects.new(nome, d)
    o.location = loc
    if rot:
        o.rotation_euler = rot
    col.objects.link(o)
    return o


def estante(x, y, col, m, rnd, largura=2.2, altura=3.2, prateleiras=6):
    madeira = m["madeira"]
    _cubo("estante_fundo", (x, y + 0.2, altura / 2), (largura, 0.04, altura), madeira, col)
    for s in (-1, 1):
        _cubo("estante_lado", (x + s * largura / 2, y, altura / 2), (0.08, 0.45, altura), madeira, col)
    capas = [m["capa1"], m["capa2"], m["capa3"], m["couro"], m["papel"]]
    passo = altura / prateleiras
    for i in range(prateleiras + 1):
        z = i * passo
        _cubo("prateleira", (x, y, z + 0.02), (largura, 0.45, 0.04), madeira, col)
        if i == prateleiras:
            break
        bx = x - largura / 2 + 0.06
        while bx < x + largura / 2 - 0.12:
            if rnd.random() < 0.08:
                bx += rnd.uniform(0.1, 0.25)
                continue
            w, h = rnd.uniform(0.04, 0.09), rnd.uniform(0.6, 0.9) * passo
            inc = rnd.uniform(-0.06, 0.06) if rnd.random() < 0.15 else 0
            b = _cubo("livro", (bx + w / 2, y - 0.02, z + 0.04 + h / 2), (w, rnd.uniform(0.25, 0.32), h),
                      rnd.choice(capas), col)
            b.rotation_euler = (0, inc, 0)
            bx += w + 0.004


def criar(col, m, semente=3):
    rnd = random.Random(semente)
    # Chao e paredes de pedra.
    bpy.ops.mesh.primitive_plane_add(size=16, location=(0, 0, 0))
    chao = bpy.context.object
    chao.data.materials.append(m["pedra"])
    for nome, loc, esc in (("parede_fundo", (0, 3.6, 3), (12, 0.3, 6)), ("parede_esq", (-4.3, 0, 3), (0.3, 12, 6)),
                           ("parede_dir", (4.3, 0, 3), (0.3, 12, 6))):
        _cubo(nome, loc, esc, m["pedra"], col)
    # Tres estantes no fundo e uma em cada lado.
    for x in (-2.35, 0, 2.35):
        estante(x, 3.2, col, m, rnd)
    for s in (-1, 1):
        for y in (-0.6, 1.8):
            antes = set(col.objects)
            estante(0, 0, col, m, rnd)
            piv = bpy.data.objects.new("estante_lateral", None)
            col.objects.link(piv)
            for o in set(col.objects) - antes - {piv}:
                o.parent = piv
            piv.location = (s * 3.95, y, 0)
            piv.rotation_euler = (0, 0, -s * math.pi / 2)
    # Colunas.
    for x in (-3.0, 3.0):
        for y in (-2.2, 2.4):
            bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.28, depth=6, location=(x, y, 3))
            c = bpy.context.object
            c.data.materials.append(m["pedra"])
            bpy.ops.object.shade_smooth()
    # Mesa com livros abertos e vela.
    _cubo("mesa_tampo", (1.7, -0.4, 0.78), (1.4, 0.8, 0.06), m["madeira"], col)
    for dx in (-0.62, 0.62):
        for dy in (-0.33, 0.33):
            _cubo("mesa_pe", (1.7 + dx, -0.4 + dy, 0.38), (0.07, 0.07, 0.76), m["madeira"], col)
    for i in range(5):
        _cubo("livro_mesa", (1.3 + 0.02 * i, -0.2, 0.84 + 0.05 * i), (0.32, 0.24, 0.045),
              rnd.choice([m["capa1"], m["capa2"], m["capa3"]]), col).rotation_euler = (0, 0, rnd.uniform(-0.3, 0.3))
    _cubo("livro_aberto", (1.9, -0.5, 0.82), (0.5, 0.34, 0.02), m["papel"], col)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.18, location=(2.2, -0.2, 0.9))
    bpy.context.object.data.materials.append(m["papel"])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(2.2, -0.2, 1.01))
    ch = bpy.context.object
    ch.scale = (0.012, 0.012, 0.028)
    ch.data.materials.append(m["chama"])
    _luz("vela", "POINT", (2.2, -0.2, 1.05), 6, (1, 0.6, 0.3), col, 0.02)
    # Luz de recorte fria por tras e um leve preenchimento.
    _luz("recorte", "AREA", (0.5, 2.2, 3.4), 160, (0.55, 0.65, 1.0), col, 1.5, (math.radians(-40), 0, 0))
    _luz("lua", "SPOT", (-3.5, -3.0, 5.5), 320, (0.6, 0.7, 1.0), col, 0.3,
         (math.radians(50), math.radians(-25), math.radians(-50)))
    mundo = bpy.data.worlds.new("noite")
    mundo.use_nodes = True
    bg = mundo.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.012, 0.014, 0.022, 1)
    bg.inputs[1].default_value = 1.0
    bpy.context.scene.world = mundo
