"""Cenario: o sotao das lembrancas. Telhado inclinado com caibros, janela redonda na empena com luz de tarde,
caixas de papelao empilhadas, um cavalinho de balanco, um abajur de pe velho, quadros encostados,
uma lampada pendurada e o bau antigo (centro da acao)."""
import math
import random

import bpy

from babilonia import _cubo, _cil, _luz
from processo import _esf, _emis
from ceu import _gradiente

TITULO = "CENARIO: O SOTAO DAS LEMBRANCAS"
VISTAS = [("VISAO GERAL", (0.3, -4.0, 1.7), (0.6, 0.4, 1.2), 24, False),
          ("PLANTA (DE CIMA)", (0.6, -0.6, 8), (0.6, -0.6, 0), 9, True),
          ("A JANELA REDONDA", (0.6, -2.0, 1.2), (0.6, 1.3, 1.9), 28, False),
          ("DETALHE: O BAU", (0.0, -1.3, 0.9), (0.6, -0.25, 0.5), 30, False)]
CENTRO = (0.6, -0.3, 0.5)


def criar(col, m, semente=16):
    import materiais
    rnd = random.Random(semente)
    piso = materiais.simples("piso_sotao", (0.42, 0.3, 0.2), 0.8, ruido=0.5, escala_ruido=3, bump=0.3)
    forro = materiais.simples("forro", (0.5, 0.37, 0.24), 0.85, ruido=0.5, escala_ruido=4, bump=0.3)
    caibro = materiais.simples("caibro", (0.3, 0.2, 0.12), 0.85, ruido=0.4, escala_ruido=10, bump=0.4)
    empena = materiais.simples("empena", (0.55, 0.42, 0.3), 0.9, ruido=0.4, escala_ruido=3)
    papelao = materiais.simples("papelao", (0.6, 0.45, 0.28), 0.9, ruido=0.3, escala_ruido=20)
    bau = materiais.simples("bau", (0.3, 0.17, 0.08), 0.6, ruido=0.4, escala_ruido=8, bump=0.2)
    ferro = materiais.simples("ferro_bau", (0.12, 0.1, 0.08), 0.5, metal=0.8)
    pano = materiais.simples("pano_velho", (0.75, 0.72, 0.65), 0.95, ruido=0.3, escala_ruido=10)
    cx, cy, cz = CENTRO
    for k in range(-14, 10):
        _cubo("tabua_piso", (0.6, k * 0.2, -0.01), (6.0, 0.19, 0.02), piso, col)
    # telhado em duas aguas: cumeeira ao longo de y, sobre x = 0.6
    larg, alt_cum, Y0, Y1 = 3.2, 3.0, -4.5, 1.3
    ang = math.atan2(alt_cum - 0.4, larg)
    comp = math.hypot(larg, alt_cum - 0.4)
    for s in (-1, 1):
        _cubo("agua", (0.6 + s * larg / 2, (Y0 + Y1) / 2, 0.4 + (alt_cum - 0.4) / 2), (comp, Y1 - Y0, 0.06), forro, col,
              (0, s * ang, 0))
        for k in range(9):
            _cubo("caibro", (0.6 + s * larg / 2, Y1 - 0.2 - k * 0.65, 0.35 + (alt_cum - 0.4) / 2), (comp, 0.08, 0.12), caibro, col,
                  (0, s * ang, 0))
        _cubo("parede_baixa", (0.6 + s * larg, (Y0 + Y1) / 2, 0.2), (0.08, Y1 - Y0, 0.4), empena, col)
    # empena do fundo com janela redonda (vazada) e o ceu de tarde atras
    import bmesh
    bm = bmesh.new()
    jx, jz, jr = 0.6, 1.9, 0.35
    seg = 32
    contorno = [(0.6 - larg, 0), (0.6 + larg, 0), (0.6 + larg, 0.4), (0.6, alt_cum), (0.6 - larg, 0.4)]
    vs_ext = [bm.verts.new((x, Y1, z)) for x, z in contorno]
    bm.faces.new(vs_ext)
    me = bpy.data.meshes.new("empena")
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("empena", me)
    col.objects.link(o)
    me.materials.append(empena)
    bl = o.modifiers.new("furo", "BOOLEAN")
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=jr, depth=0.6, location=(jx, Y1, jz), rotation=(math.radians(90), 0, 0))
    furo = bpy.context.object
    furo.hide_render = furo.hide_viewport = True
    o.modifiers["furo"].object = furo
    sol_mod = o.modifiers.new("esp", "SOLIDIFY")
    sol_mod.thickness = 0.08
    o.modifiers.move(1, 0)
    bpy.ops.mesh.primitive_torus_add(major_radius=jr + 0.03, minor_radius=0.04, location=(jx, Y1 - 0.06, jz), rotation=(math.radians(90), 0, 0))
    bpy.context.object.data.materials.append(caibro)
    for rot in (0, 90):
        _cubo("cruz_janela", (jx, Y1 - 0.05, jz), (0.03, 0.03, jr * 2), caibro, col, (0, math.radians(rot), 0))
    _cubo("ceu", (jx, Y1 + 6, 2.5), (20, 0.1, 10), _gradiente("ceu_sotao", (1.0, 0.65, 0.35), (0.5, 0.6, 0.85), 1.6), col)
    # caixas, cavalinho, abajur velho, quadros, lampada pendurada
    for x, y, w, h, k in ((-1.6, 0.6, 0.6, 0.45, 0), (-1.6, 0.6, 0.5, 0.4, 1), (-1.1, 0.9, 0.5, 0.4, 0), (2.4, 0.7, 0.6, 0.5, 0),
                          (2.4, 0.7, 0.45, 0.35, 1), (2.9, 0.2, 0.5, 0.45, 0), (-2.0, -0.3, 0.5, 0.35, 0)):
        _cubo("caixa", (x, y, h / 2 + k * 0.45), (w, w * 0.8, h), papelao, col, (0, 0, math.radians(rnd.uniform(-10, 10))))
    hx, hy = 1.6, 0.55
    for s in (-1, 1):
        for dy, ang in ((-0.25, 12), (0.0, 0), (0.25, -12)):
            _cubo("cav_arco", (hx + s * 0.12, hy + dy, 0.04 + abs(dy) * 0.12), (0.025, 0.27, 0.03), m["madeira"], col, (math.radians(ang), 0, 0))
        _cubo("cav_perna", (hx + s * 0.12, hy, 0.25), (0.03, 0.4, 0.3), m["madeira"], col)
    _esf("cav_corpo", (hx, hy, 0.48), (0.12, 0.3, 0.12), materiais.simples("cav_pintura", (0.7, 0.62, 0.5), 0.6), col, 16)
    _esf("cav_cabeca", (hx, hy - 0.32, 0.68), (0.08, 0.14, 0.09), materiais.simples("cav_pintura2", (0.7, 0.62, 0.5), 0.6), col, 16)
    _cil("abajur_pe", (-0.9, 0.6, 0.7), 0.015, 1.4, ferro, col)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.25, radius2=0.14, depth=0.25, location=(-0.9, 0.6, 1.5))
    bpy.context.object.data.materials.append(pano)
    for x, ang in ((2.0, -8), (2.15, -12)):
        _cubo("quadro", (x, 1.0, 0.35), (0.5, 0.03, 0.65), caibro, col, (math.radians(ang), 0, 0))
    _cil("fio", (0.6, -0.4, 2.45), 0.004, 0.7, ferro, col)
    _esf("lampada", (0.6, -0.4, 2.05), (0.04, 0.04, 0.05), materiais.simples("vidro_lamp", (0.9, 0.9, 0.85), 0.1), col)
    # o bau
    _cubo("bau", (cx, cy, (cz - 0.06) / 2), (0.58, 0.4, cz - 0.06), bau, col)
    _cubo("bau_tampa", (cx, cy, cz - 0.03), (0.6, 0.42, 0.06), bau, col)
    for dx in (-0.2, 0.2):
        _cubo("bau_cinta", (cx + dx, cy, cz / 2), (0.04, 0.425, cz + 0.005), ferro, col)
    _cubo("bau_fecho", (cx, cy - 0.215, cz - 0.08), (0.06, 0.01, 0.07), m["latao"], col)
    mk = _cubo("livro_aberto", (cx, cy, cz), (0.01, 0.01, 0.01), m["papel"], col)
    mk.hide_render = True
    _luz("sol_janela", "SPOT", (jx, Y1 + 2.0, jz + 0.6), 1800, (1.0, 0.7, 0.42), col, 0.15, (cx - 0.3, cy - 0.4, 0.2))
    _luz("janela_ar", "AREA", (jx, Y1 - 0.3, jz), 30, (1.0, 0.7, 0.45), col, 0.8, (jx, -1, 1.0))
    _luz("preenche", "AREA", (0.6, -4.0, 2.0), 25, (0.6, 0.6, 0.85), col, 3.0, (0.8, 0, 1.0))
    mundo = bpy.data.worlds.new("sotao_mundo")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.02, 0.016, 0.014, 1)
    bpy.context.scene.world = mundo


def animar(col, m, p, faixas, h):
    """A luz da tarde vai baixando e esquentando."""
    sol = bpy.data.objects["sol_janela"].data
    fim = faixas[-1][1]
    for f, e, c in ((0, 1800, (1.0, 0.7, 0.42)), (fim, 1300, (1.0, 0.55, 0.3))):
        sol.energy, sol.color = e, c
        sol.keyframe_insert("energy", frame=f)
        sol.keyframe_insert("color", frame=f)
