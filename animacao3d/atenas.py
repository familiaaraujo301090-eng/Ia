"""Cenario: a agora de Atenas, fim de tarde. Chao de lajes de pedra, colunata dorica (a stoa) ao fundo,
a Acropole com o Partenon no morro distante, o grande barril de barro (pithos) deitado onde Diogenes
dormia, o cao dele enrolado ao lado, uma oliveira, anforas e uma mesa de marmore.

criar(col, m)                 -> monta a praca (a mesa fica no mesmo lugar da biblioteca: os planos servem)
animar(col, m, p, faixas, h)  -> o cao respira; o sol desce e esquenta
"""
import math
import random

import bpy

from babilonia import _cubo, _cil, _torno, _luz, _obj

TITULO = "CENARIO: A AGORA DE ATENAS"
VISTAS = [("VISAO GERAL", (0.3, -4.8, 2.0), (0.6, 0.6, 1.3), 24, False),
          ("PLANTA (DE CIMA)", (0.6, -0.2, 10), (0.6, -0.2, 0), 10, True),
          ("O BARRIL E O CAO", (0.6, -1.8, 1.2), (-1.5, 0.6, 0.5), 28, False),
          ("DETALHE: MESA", (0.9, -1.6, 1.25), (1.6, -0.35, 0.85), 30, False)]

MESA_Z = 0.81


def _esfera(nome, loc, esc, mat, col, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1, location=loc)
    o = bpy.context.object
    o.name, o.scale = nome, esc
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return _obj(o, col)


def _coluna(x, y, h, r, mat, col):
    _cubo("plinto", (x, y, 0.06), (r * 2.6, r * 2.6, 0.12), mat, col)
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=r, depth=h, location=(x, y, 0.12 + h / 2))
    c = bpy.context.object
    c.name = "coluna"
    c.data.materials.append(mat)
    tc = c.modifiers.new("afina", "SIMPLE_DEFORM")
    tc.deform_method, tc.factor = "TAPER", -0.18
    _obj(c, col)
    _cil("equino", (x, y, 0.12 + h + 0.05), r * 1.25, 0.1, mat, col, verts=20)
    _cubo("abaco", (x, y, 0.12 + h + 0.14), (r * 2.7, r * 2.7, 0.08), mat, col)


def _ceu(col):
    ceu = bpy.data.materials.new("ceu_atenas")
    ceu.use_nodes = True
    nt = ceu.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (1.0, 0.72, 0.42, 1)
    rampa.color_ramp.elements[1].position = 0.55
    rampa.color_ramp.elements[1].color = (0.32, 0.52, 0.85, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.6
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    _cubo("ceu", (0, 40, 8), (120, 0.1, 40), ceu, col)


def criar(col, m, semente=21):
    import materiais
    rnd = random.Random(semente)
    marmore = materiais.simples("marmore", (0.86, 0.82, 0.74), 0.45, ruido=0.25, escala_ruido=8, bump=0.1)
    calcario = materiais.simples("calcario", (0.78, 0.68, 0.52), 0.85, ruido=0.4, escala_ruido=10, bump=0.3)
    laje = materiais.simples("laje", (0.62, 0.55, 0.45), 0.9, ruido=0.5, escala_ruido=6, bump=0.4)
    laje2 = materiais.simples("laje2", (0.55, 0.48, 0.39), 0.9, ruido=0.5, escala_ruido=6, bump=0.4)
    barro = materiais.simples("barro_pithos", (0.62, 0.32, 0.17), 0.75, ruido=0.35, escala_ruido=14, bump=0.3)
    escuro = materiais.simples("dentro_barril", (0.03, 0.02, 0.015), 1.0)
    manta = materiais.simples("manta", (0.45, 0.36, 0.25), 0.95, ruido=0.5, escala_ruido=50, bump=0.5)
    pelo = materiais.simples("pelo_cao", (0.45, 0.3, 0.17), 0.9, ruido=0.5, escala_ruido=70, bump=0.6)
    tronco = materiais.simples("oliveira_tronco", (0.25, 0.2, 0.15), 0.9, ruido=0.6, escala_ruido=20, bump=0.8)
    folha = materiais.simples("oliveira_folha", (0.25, 0.32, 0.18), 0.7, ruido=0.6, escala_ruido=30, bump=0.5)
    morro = materiais.simples("morro", (0.42, 0.38, 0.28), 0.95, ruido=0.6, escala_ruido=3, bump=0.3)
    telha = materiais.simples("telha", (0.55, 0.22, 0.12), 0.8, ruido=0.3, escala_ruido=30)
    # chao: terra clara ao longe e lajes de pedra perto da mesa
    bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 10, -0.005))
    bpy.context.object.data.materials.append(calcario)
    for i in range(-6, 8):
        for j in range(-9, 5):
            w = 0.62
            _cubo("laje", (i * w + rnd.uniform(-.01, .01), j * w, rnd.uniform(0.0, 0.012)),
                  (w - 0.025, w - 0.025, 0.03), laje if (i + j) % 3 else laje2, col)
    # a stoa: colunata dorica com entablamento, parede do fundo e telhado
    yc = 2.4
    for k in range(9):
        _coluna(-3.4 + k * 0.95, yc, 3.2, 0.2, marmore, col)
    _cubo("arquitrave", (0.4, yc, 3.62), (8.4, 0.5, 0.3), marmore, col)
    for k in range(26):
        _cubo("triglifo", (-3.7 + k * 0.32, yc - 0.26, 3.93), (0.12, 0.04, 0.3), calcario, col)
    _cubo("friso", (0.4, yc, 3.93), (8.4, 0.46, 0.32), marmore, col)
    _cubo("cornija", (0.4, yc + 0.5, 4.14), (8.8, 1.6, 0.1), marmore, col)
    _cubo("telhado", (0.4, yc + 1.4, 4.45), (8.8, 2.6, 0.08), telha, col, (math.radians(-12), 0, 0))
    _cubo("parede_stoa", (0.4, yc + 2.0, 1.8), (8.4, 0.2, 3.6), calcario, col)
    _cubo("piso_stoa", (0.4, yc + 0.9, 0.06), (8.6, 2.4, 0.12), marmore, col)
    # a Acropole no morro, longe, e o Partenon em silhueta clara
    _esfera("morro", (-7.0, 26, -3.2), (12, 7, 6.2), morro, col, 32)
    pz, px, py = 2.9, -6.6, 25.0
    _cubo("partenon_base", (px, py, pz), (4.2, 2.0, 0.25), marmore, col)
    for k in range(9):
        _cil("partenon_col", (px - 1.9 + k * 0.475, py - 0.9, pz + 0.75), 0.09, 1.3, marmore, col, verts=10)
    _cubo("partenon_topo", (px, py, pz + 1.5), (4.2, 2.0, 0.22), marmore, col)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=1.0, depth=1.0, location=(px, py - 1.0, pz + 1.75))
    fr = bpy.context.object
    fr.scale, fr.rotation_euler = (2.1, 0.45, 1.0), (math.radians(90), math.radians(90), 0)
    fr.data.materials.append(marmore)
    _obj(fr, col)
    _ceu(col)
    # o pithos deitado: o barril de Diogenes, com a manta saindo da boca
    perfil = [(0.18, -0.7), (0.4, -0.6), (0.55, -0.3), (0.58, 0.0), (0.55, 0.3), (0.45, 0.55), (0.32, 0.66), (0.33, 0.72)]
    bx, by = -1.25, 0.55
    p = _torno("pithos", perfil, (bx, by, 0.56), barro, col)
    p.rotation_euler = (math.radians(90), 0, math.radians(-35))
    boca = _cil("boca_escura", (0, 0, 0), 0.3, 0.02, escuro, col)
    boca.parent = p
    boca.location = (0, 0, 0.7)
    mt = _cubo("manta", (bx + 0.55, by - 0.62, 0.03), (0.6, 0.5, 0.03), manta, col, (0, 0, math.radians(-30)))
    mt.modifiers.new("dobras", "SUBSURF").levels = 2
    # o cao enrolado ao lado do barril
    cx, cy = bx + 1.0, by - 0.25
    corpo = _esfera("cao_corpo", (cx, cy, 0.16), (0.32, 0.2, 0.16), pelo, col)
    corpo.rotation_euler = (0, 0, math.radians(25))
    cab = _esfera("cao_cabeca", (cx - 0.3, cy - 0.2, 0.15), (0.12, 0.1, 0.1), pelo, col)
    _esfera("cao_focinho", (cx - 0.38, cy - 0.3, 0.12), (0.06, 0.05, 0.045), pelo, col)
    _esfera("cao_nariz", (cx - 0.42, cy - 0.35, 0.13), (0.015, 0.015, 0.012), escuro, col)
    for s in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.04, depth=0.09,
                                        location=(cx - 0.28 + s * 0.06, cy - 0.17 + s * 0.03, 0.25))
        o = bpy.context.object
        o.rotation_euler = (math.radians(-20), math.radians(s * 20), 0)
        o.data.materials.append(pelo)
        _obj(o, col)
    rabo = _esfera("cao_rabo", (cx + 0.2, cy - 0.18, 0.06), (0.2, 0.04, 0.04), pelo, col)
    rabo.rotation_euler = (0, 0, math.radians(-40))
    # a oliveira a direita e anforas encostadas nas colunas
    ox, oy = 3.4, 0.9
    for k in range(5):
        a = k * 1.3
        seg = _cil("oliveira", (ox + 0.08 * math.sin(a), oy + 0.06 * math.cos(a), 0.3 + k * 0.42), 0.13 - k * 0.015,
                   0.5, tronco, col, (math.radians(8 * math.sin(a)), math.radians(10 * math.cos(a)), 0), 10)
    for k in range(9):
        a = k / 9 * math.tau
        _esfera("copa", (ox + 0.6 * math.cos(a) * rnd.uniform(0.5, 1.1), oy + 0.5 * math.sin(a) * rnd.uniform(0.5, 1.1),
                         2.4 + rnd.uniform(-0.3, 0.4)), (0.55, 0.5, 0.38), folha, col, 16)
    anf = [(0.02, 0.0), (0.09, 0.04), (0.17, 0.2), (0.19, 0.38), (0.15, 0.55), (0.07, 0.66), (0.06, 0.74), (0.09, 0.77)]
    for x, y, s in ((-2.6, 2.0, 1.0), (-2.35, 2.1, 0.8), (1.9, 2.0, 0.9), (-0.3, 1.9, 0.75)):
        _torno("anfora", [(r * s, z * s) for r, z in anf], (x, y, 0.02), barro, col)
    # mesa de marmore no lugar de sempre
    _cubo("mesa_tampo", (1.6, -0.45, MESA_Z - 0.03), (1.4, 0.8, 0.06), marmore, col)
    for dx in (-0.5, 0.5):
        _cubo("pe_mesa", (1.6 + dx, -0.45, MESA_Z / 2 - 0.03), (0.16, 0.6, MESA_Z - 0.06), marmore, col)
    mk = _cubo("livro_aberto", (1.9, -0.5, MESA_Z), (0.01, 0.01, 0.01), m["papel"], col)
    mk.hide_render = True
    # luz: sol baixo de fim de tarde pela esquerda, ceu azul preenchendo
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy, sol.color, sol.angle = 4.2, (1.0, 0.8, 0.6), math.radians(2)
    o = bpy.data.objects.new("sol", sol)
    o.rotation_euler = (math.radians(62), 0, math.radians(-118))
    col.objects.link(o)
    _luz("preenche", "AREA", (0.6, -4.5, 2.8), 120, (0.6, 0.7, 1.0), col, 4.0, (0.8, 0, 1.0))
    mundo = bpy.data.worlds.new("tarde_atenas")
    mundo.use_nodes = True
    bg = mundo.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.35, 0.45, 0.65, 1)
    bg.inputs[1].default_value = 0.6
    bpy.context.scene.world = mundo


def animar(col, m, p, faixas, h):
    """O cao respira devagar; o sol desce, fica mais laranja e mais fraco."""
    fim = faixas[-1][1]
    corpo = bpy.data.objects["cao_corpo"]
    s = tuple(corpo.scale)
    for f in range(0, fim + 1, 36):
        corpo.scale = (s[0], s[1], s[2] * (1.06 if (f // 36) % 2 else 1.0))
        corpo.keyframe_insert("scale", frame=f)
    sol = bpy.data.objects["sol"]
    for f, e, c, inc in ((0, 4.2, (1.0, 0.8, 0.6), 62), (fim, 3.0, (1.0, 0.6, 0.35), 70)):
        sol.data.energy, sol.data.color = e, c
        sol.data.keyframe_insert("energy", frame=f)
        sol.data.keyframe_insert("color", frame=f)
        sol.rotation_euler[0] = math.radians(inc)
        sol.keyframe_insert("rotation_euler", frame=f)
