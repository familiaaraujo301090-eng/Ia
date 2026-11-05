"""Cenario: sala de um mercador da Babilonia ao por do sol. Parede de tijolos esmaltados azuis (como a
Porta de Ishtar) com faixa de rosetas, paredes de tijolo de barro, vigas de palmeira, janela em arco com o
zigurate e uma palmeira contra o ceu laranja, anforas, sacos de grao, tapete e uma balanca.

criar(col, m)                 -> monta a sala (a mesa fica no mesmo lugar da biblioteca: os planos servem)
animar(col, m, p, faixas, h)  -> o sol baixa devagar (a luz da janela esquenta e enfraquece)
"""
import math
import random

import bpy

TITULO = "CENARIO: A CASA DO MERCADOR, BABILONIA"
VISTAS = [("VISAO GERAL", (0.4, -4.6, 2.0), (0.6, 0.4, 1.3), 24, False),
          ("PLANTA (DE CIMA)", (0.6, -0.2, 9), (0.6, -0.2, 0), 9, True),
          ("A JANELA DO POR DO SOL", (1.4, -2.4, 1.3), (-2.3, 0.2, 1.7), 26, False),
          ("DETALHE: MESA", (0.9, -1.6, 1.25), (1.6, -0.35, 0.85), 30, False)]

MESA_Z = 0.81
X0, X1, Y1, ALTO = -2.3, 3.4, 1.25, 3.6


def _obj(o, col):
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def _cubo(nome, loc, esc, mat, col, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name, o.scale = nome, esc
    if rot:
        o.rotation_euler = rot
    o.data.materials.append(mat)
    return _obj(o, col)


def _cil(nome, loc, r, h, mat, col, rot=None, verts=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc)
    o = bpy.context.object
    o.name = nome
    if rot:
        o.rotation_euler = rot
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return _obj(o, col)


def _torno(nome, perfil, loc, mat, col, segs=32):
    """Objeto de revolucao (anfora, jarro) a partir de um perfil [(raio, altura)]."""
    import bmesh
    bm = bmesh.new()
    aneis = []
    for j in range(segs):
        a = j / segs * math.tau
        aneis.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for r, z in perfil])
    for j in range(segs):
        for i in range(len(perfil) - 1):
            bm.faces.new((aneis[j][i], aneis[(j + 1) % segs][i], aneis[(j + 1) % segs][i + 1], aneis[j][i + 1]))
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(nome, me)
    o.location = loc
    col.objects.link(o)
    o.modifiers.new("esp", "SOLIDIFY").thickness = 0.01
    return o


def _luz(nome, tipo, loc, energia, cor, col, tam=0.2, alvo=None):
    from mathutils import Vector
    d = bpy.data.lights.new(nome, tipo)
    d.energy, d.color = energia, cor
    if tipo == "AREA":
        d.size = tam
    elif tipo == "SPOT":
        d.spot_size, d.spot_blend, d.shadow_soft_size = math.radians(45), 0.4, tam
    else:
        d.shadow_soft_size = tam
    o = bpy.data.objects.new(nome, d)
    o.location = loc
    col.objects.link(o)
    if alvo:
        o.rotation_euler = (Vector(alvo) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def _tijolos(col, mats, rnd, ox, oy, eixo, comp, alto, furo=None, h=0.17, w=0.34):
    fila, z = 0, 0.0
    while z < alto:
        x = -w / 2 * (fila % 2)
        while x < comp:
            cx, cz = x + w / 2, z + h / 2
            if not (furo and furo(cx, cz)):
                mat = mats(fila, cx, cz)
                if eixo == "x":
                    _cubo("tijolo", (ox + cx, oy + rnd.uniform(-.008, .008), cz), (w - 0.018, 0.16, h - 0.018), mat, col)
                else:
                    _cubo("tijolo", (ox + rnd.uniform(-.008, .008), oy + cx, cz), (0.16, w - 0.018, h - 0.018), mat, col)
            x += w
        z += h
        fila += 1


def criar(col, m, semente=12):
    import materiais
    rnd = random.Random(semente)
    azul = materiais.simples("esmalte_azul", (0.03, 0.12, 0.42), 0.18, ruido=0.35, escala_ruido=25)
    azul2 = materiais.simples("esmalte_azul2", (0.05, 0.18, 0.55), 0.2, ruido=0.3, escala_ruido=25)
    amarelo = materiais.simples("esmalte_amarelo", (0.75, 0.52, 0.12), 0.25)
    branco = materiais.simples("esmalte_branco", (0.85, 0.8, 0.7), 0.3)
    adobe = materiais.simples("adobe", (0.48, 0.33, 0.2), 0.95, ruido=0.5, escala_ruido=12, bump=0.5)
    adobe2 = materiais.simples("adobe2", (0.42, 0.28, 0.17), 0.95, ruido=0.5, escala_ruido=12, bump=0.5)
    terra = materiais.simples("terra_batida", (0.32, 0.22, 0.14), 0.95, ruido=0.6, escala_ruido=5, bump=0.3)
    palma = materiais.simples("palmeira", (0.22, 0.14, 0.08), 0.85, ruido=0.6, escala_ruido=30, bump=0.6)
    barro = materiais.simples("barro_bab", (0.55, 0.3, 0.16), 0.7, ruido=0.3, escala_ruido=18, bump=0.2)
    saco = materiais.simples("saco", (0.5, 0.42, 0.28), 0.95, ruido=0.5, escala_ruido=60, bump=0.4)
    tapete = materiais.simples("tapete", (0.42, 0.05, 0.04), 0.9, ruido=0.4, escala_ruido=40, bump=0.2)
    silh = materiais.simples("silhueta", (0.02, 0.012, 0.01), 1.0)
    # chao de terra batida e tapete
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0.5, -1, 0))
    bpy.context.object.data.materials.append(terra)
    _cubo("tapete", (0.9, -0.4, 0.006), (2.6, 1.7, 0.01), tapete, col)
    for dx, dy, sx, sy in ((0, 0.78, 2.6, 0.06), (0, -0.78, 2.6, 0.06), (1.22, 0, 0.06, 1.7), (-1.22, 0, 0.06, 1.7)):
        _cubo("borda_tapete", (0.9 + dx, -0.4 + dy, 0.012), (sx, sy, 0.012), amarelo, col)
    # parede do fundo: tijolos esmaltados azuis com faixa de rosetas
    def mats_fundo(fila, cx, cz):
        return azul if (fila + int(cx / 0.34)) % 3 else azul2
    _tijolos(col, mats_fundo, rnd, X0, Y1, "x", X1 - X0, ALTO)
    for k in range(14):
        x = X0 + 0.25 + k * 0.42
        for zz in (1.05, 2.45):
            _cil("roseta", (x, Y1 - 0.09, zz), 0.075, 0.02, branco, col, (math.radians(90), 0, 0), 20)
            _cil("miolo", (x, Y1 - 0.1, zz), 0.035, 0.02, amarelo, col, (math.radians(90), 0, 0), 16)
    for zz in (0.93, 1.17, 2.33, 2.57):
        _cubo("filete", (0.55, Y1 - 0.085, zz), (X1 - X0, 0.012, 0.025), amarelo, col)
    # parede esquerda de adobe com janela em arco (o por do sol)
    jy, jz, jw, jh = -0.2, 1.75, 1.0, 1.5
    def furo_esq(cx, cz):
        y = -4.5 + cx
        if abs(y - jy) < jw / 2 and jz - jh / 2 < cz < jz + jh / 2 - jw / 2:
            return True
        dy, dz = y - jy, cz - (jz + jh / 2 - jw / 2)
        return dz >= 0 and dy * dy + dz * dz < (jw / 2) ** 2
    _tijolos(col, lambda f, cx, cz: adobe if f % 2 else adobe2, rnd, X0, -4.5, "y", Y1 + 4.5, ALTO, furo_esq)
    _tijolos(col, lambda f, cx, cz: adobe if f % 2 else adobe2, rnd, X1, -4.5, "y", Y1 + 4.5, ALTO)
    # ceu do por do sol, zigurate e palmeira la fora
    ceu = bpy.data.materials.new("ceu_tarde")
    ceu.use_nodes = True
    nt = ceu.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (1.0, 0.42, 0.12, 1)
    rampa.color_ramp.elements[1].color = (0.25, 0.18, 0.35, 1)
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], em.inputs["Color"])
    em.inputs["Strength"].default_value = 2.2
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    _cubo("ceu", (X0 - 6, jy, 2.5), (0.05, 12, 7), ceu, col)
    for k, (w, hh) in enumerate([(3.2, 0.6), (2.4, 0.55), (1.7, 0.5), (1.1, 0.45), (0.6, 0.4)]):
        z0 = sum(x[1] for x in [(3.2, 0.6), (2.4, 0.55), (1.7, 0.5), (1.1, 0.45), (0.6, 0.4)][:k])
        _cubo("zigurate", (X0 - 5, jy + 0.6, 0.35 + z0 + hh / 2), (w * 0.8, w, hh), silh, col)
    _cil("tronco", (X0 - 2.2, jy - 0.9, 1.6), 0.07, 3.2, silh, col, (0, math.radians(6), 0), 10)
    for k in range(9):
        a = k / 9 * math.tau
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.09, radius2=0.0, depth=1.3,
                                        location=(X0 - 2.2 + 0.18 + math.cos(a) * 0.5, jy - 0.9 + math.sin(a) * 0.5, 3.1 - 0.15))
        f = bpy.context.object
        f.rotation_euler = (math.radians(70) * math.sin(a), math.radians(70) * math.cos(a), 0)
        f.scale = (1, 0.3, 1)
        f.data.materials.append(silh)
        _obj(f, col)
    # vigas de palmeira no teto
    _cubo("teto", (0.5, -1.5, ALTO + 0.12), (6.4, 6.4, 0.12), adobe2, col)
    for k in range(7):
        _cil("viga", (0.5, -3.6 + k * 0.78, ALTO - 0.02), 0.08, 6.0, palma, col, (0, math.radians(90), 0), 12)
    # anforas, jarros e sacos de grao pelos cantos
    anf = [(0.02, 0.0), (0.09, 0.04), (0.17, 0.2), (0.19, 0.38), (0.15, 0.55), (0.07, 0.66), (0.06, 0.74), (0.09, 0.77)]
    for x, y, s in ((2.9, 0.9, 1.0), (2.6, 1.0, 0.85), (3.05, 0.55, 0.75), (-1.9, 0.95, 1.1), (-1.6, 1.0, 0.8)):
        _torno("anfora", [(r * s, z * s) for r, z in anf], (x, y, 0), barro, col)
    for x, y in ((2.85, 0.2), (2.55, 0.45), (2.95, -0.15)):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x, y, 0.18))
        sc = bpy.context.object
        sc.scale = (0.22, 0.2, 0.2)
        sc.data.materials.append(saco)
        bpy.ops.object.shade_smooth()
        _obj(sc, col)
    # mesa de madeira (mesmo lugar e altura da biblioteca) e uma balanca de latao ao lado
    _cubo("mesa_tampo", (1.6, -0.45, MESA_Z - 0.02), (1.4, 0.8, 0.05), m["madeira"], col)
    for dx in (-0.62, 0.62):
        for dy in (-0.33, 0.33):
            _cubo("pe_mesa", (1.6 + dx, -0.45 + dy, MESA_Z / 2 - 0.02), (0.07, 0.07, MESA_Z - 0.02), m["madeira"], col)
    bx, by = 0.55, 0.55
    _cil("balanca_haste", (bx, by, 0.65), 0.012, 1.3, m["latao"], col)
    _cil("balanca_trave", (bx, by, 1.28), 0.01, 0.6, m["latao"], col, (0, math.radians(90), 0))
    for s in (-1, 1):
        _cil("balanca_corda", (bx + s * 0.28, by, 1.12), 0.003, 0.32, m["latao"], col)
        _cil("balanca_prato", (bx + s * 0.28, by, 0.96), 0.1, 0.012, m["latao"], col)
    _cil("balanca_base", (bx, by, 0.01), 0.14, 0.02, m["latao"], col)
    # o processo procura o livro aberto da biblioteca para escondê-lo: marcador oculto
    mk = _cubo("livro_aberto", (1.9, -0.5, MESA_Z), (0.01, 0.01, 0.01), m["papel"], col)
    mk.hide_render = True
    # lamparinas de oleo nas paredes
    for x, y in ((X1 - 0.12, -1.4), (X1 - 0.12, 0.6)):
        _cil("lamparina_parede", (x, y, 1.9), 0.05, 0.03, barro, col)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(x - 0.03, y, 1.95))
        fl = bpy.context.object
        fl.scale = (0.012, 0.012, 0.03)
        fl.data.materials.append(m["chama"])
        _obj(fl, col)
        _luz("lamp_parede", "POINT", (x - 0.12, y, 2.0), 18, (1.0, 0.6, 0.3), col, 0.05)
    # luzes: sol baixo pela janela, ambiente quente e preenchimento frio
    _luz("sol_janela", "SPOT", (X0 - 2.0, jy + 0.3, 2.3), 2600, (1.0, 0.55, 0.25), col, 0.3, (1.4, -0.4, 0.6))
    _luz("janela_ar", "AREA", (X0 + 0.2, jy, jz), 60, (1.0, 0.6, 0.35), col, 1.0, (1.0, jy, 1.0))
    _luz("preenche", "AREA", (0.5, -4.0, 2.6), 25, (0.55, 0.6, 0.85), col, 3.0, (0.8, 0, 1.0))
    mundo = bpy.data.worlds.new("tarde_bab")
    mundo.use_nodes = True
    bg = mundo.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.02, 0.014, 0.012, 1)
    bpy.context.scene.world = mundo


def animar(col, m, p, faixas, h):
    """O sol baixa: a luz da janela fica mais laranja e mais fraca ao longo do video."""
    sol = bpy.data.objects["sol_janela"].data
    fim = faixas[-1][1]
    for f, e, c in ((0, 2600, (1.0, 0.6, 0.3)), (fim, 1700, (1.0, 0.42, 0.18))):
        sol.energy, sol.color = e, c
        sol.keyframe_insert("energy", frame=f)
        sol.keyframe_insert("color", frame=f)
