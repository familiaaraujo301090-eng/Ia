"""Cenario: a sala de espera do ceu. Chao de nuvens, ceu claro, um portal em arco de onde sai luz,
colunas brancas perdidas nas nuvens e uma unica cadeira de madeira: a do candidato (centro da acao)."""
import math
import random

import bpy

from babilonia import _cubo, _cil, _luz
from processo import _esf, _emis

TITULO = "CENARIO: A ENTREVISTA NO CEU"
VISTAS = [("VISAO GERAL", (0.3, -4.6, 1.8), (0.6, 1.0, 1.2), 24, False),
          ("PLANTA (DE CIMA)", (0.6, 0.4, 11), (0.6, 0.4, 0), 10, True),
          ("O PORTAL", (0.2, -2.0, 1.0), (0.6, 3.5, 1.6), 26, False),
          ("DETALHE: A CADEIRA", (0.0, -1.3, 0.8), (0.6, -0.25, 0.45), 30, False)]
CENTRO = (0.6, -0.3, 0.46)


def _gradiente(nome, base, topo, forca):
    mat = _emis(nome, base, forca)
    nt = mat.node_tree
    em = nt.nodes["Emission"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (*base, 1)
    rampa.color_ramp.elements[1].color = (*topo, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], em.inputs["Color"])
    return mat


def criar(col, m, semente=3):
    import materiais
    rnd = random.Random(semente)
    nuvem = materiais.simples("nuvem", (0.93, 0.93, 0.96), 0.95, sss=0.4, ruido=0.2, escala_ruido=6, bump=0.3)
    marmore = materiais.simples("marmore_ceu", (0.92, 0.9, 0.86), 0.4, ruido=0.2, escala_ruido=6)
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 10, 0))
    bpy.context.object.data.materials.append(nuvem)
    cx, cy, cz = CENTRO
    for k in range(70):
        x, y = rnd.uniform(-6, 7), rnd.uniform(-3, 14)
        if -1.0 < x < 2.0 and -2.5 < y < 0.8:
            continue
        r = rnd.uniform(0.35, 1.1) * (1 + max(0, y) * 0.06)
        _esf("nuvem", (x, y, -r * 0.35), (r, r * 0.9, r * 0.6), nuvem, col, 20)
    for k in range(12):
        x, y = rnd.uniform(-8, 9), rnd.uniform(10, 25)
        _esf("nuvem_longe", (x, y, rnd.uniform(1, 6)), (rnd.uniform(1.5, 3), 1, rnd.uniform(0.4, 0.8)), nuvem, col, 16)
    _cubo("ceu", (0, 32, 8), (120, 0.1, 40), _gradiente("ceu_claro", (1.0, 0.92, 0.8), (0.55, 0.72, 0.95), 1.4), col)
    # o portal: dois pilares, o arco e a luz que sai de dentro
    px, py = cx, 3.6
    for s in (-1, 1):
        _cubo("pilar", (px + s * 0.85, py, 1.4), (0.3, 0.4, 2.8), marmore, col)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.85, minor_radius=0.16, location=(px, py, 2.8),
                                     rotation=(math.radians(90), 0, 0))
    arco = bpy.context.object
    arco.data.materials.append(marmore)
    bpy.ops.object.shade_smooth()
    luz_portal = _emis("luz_portal", (1.0, 0.93, 0.78), 6.0)
    _cubo("porta_luz", (px, py + 0.05, 1.4), (1.4, 0.05, 2.8), luz_portal, col)
    _esf("porta_luz_arco", (px, py + 0.05, 2.8), (0.7, 0.03, 0.7), luz_portal, col, 24)
    # colunas brancas aqui e ali, metade nas nuvens
    for x, y, h in ((-2.6, 2.0, 3.4), (-1.6, 4.5, 3.8), (3.0, 2.4, 3.2), (4.2, 5.2, 4.0), (-3.6, 6.0, 4.4)):
        _cil("coluna", (x, y, h / 2 - 0.3), 0.22, h, marmore, col, verts=20)
        _cubo("capitel", (x, y, h - 0.25), (0.6, 0.6, 0.12), marmore, col)
    # a cadeira do candidato
    mad = m["madeira"]
    _cubo("assento", (cx, cy, cz - 0.02), (0.46, 0.42, 0.04), mad, col)
    for dx in (-0.2, 0.2):
        for dy in (-0.18, 0.18):
            _cubo("pe_cadeira", (cx + dx, cy + dy, (cz - 0.04) / 2), (0.04, 0.04, cz - 0.04), mad, col)
    for dx in (-0.2, 0.2):
        _cubo("encosto_pe", (cx + dx, cy + 0.19, cz + 0.4), (0.04, 0.04, 0.8), mad, col)
    for dz in (0.55, 0.75):
        _cubo("encosto", (cx, cy + 0.19, cz + dz), (0.44, 0.03, 0.08), mad, col)
    mk = _cubo("livro_aberto", (cx, cy, cz), (0.01, 0.01, 0.01), m["papel"], col)
    mk.hide_render = True
    _luz("luz_porta", "AREA", (px, py - 0.3, 1.5), 600, (1.0, 0.92, 0.78), col, 1.6, (cx, cy, 0.6))
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy, sol.color, sol.angle = 2.5, (1.0, 0.92, 0.8), math.radians(8)
    o = bpy.data.objects.new("sol", sol)
    o.rotation_euler = (math.radians(50), 0, math.radians(160))
    col.objects.link(o)
    _luz("preenche", "AREA", (0.6, -4.5, 2.8), 150, (0.8, 0.88, 1.0), col, 5.0, (0.8, 0, 1.0))
    mundo = bpy.data.worlds.new("ceu_mundo")
    mundo.use_nodes = True
    bg = mundo.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.75, 0.8, 0.9, 1)
    bg.inputs[1].default_value = 0.7
    bpy.context.scene.world = mundo


def animar(col, m, p, faixas, h):
    """No fim, a luz do portal cresce."""
    em = bpy.data.materials["luz_portal"].node_tree.nodes["Emission"].inputs["Strength"]
    luz = bpy.data.objects["luz_porta"].data
    f0 = faixas[5][0]
    for f, s, e in ((0, 6.0, 600), (f0, 6.0, 600), (f0 + 60, 14.0, 1500)):
        em.default_value = s
        em.keyframe_insert("default_value", frame=f)
        luz.energy = e
        luz.keyframe_insert("energy", frame=f)
