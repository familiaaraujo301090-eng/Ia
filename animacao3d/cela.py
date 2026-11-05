"""Cenario: cela romana de pedra (prisao de Paulo, ano 67). Muro de blocos, janela alta com grade e luar,
palha no chao, correntes na parede, porta de madeira com ferragens, mesa rustica, banco, jarro e pao.

criar(col, m)                 -> monta a cela (a mesa fica no mesmo lugar da biblioteca: os planos servem)
animar(col, m, p, faixas, h)  -> nuvens passando pela lua (a luz da janela respira)
"""
import math
import random

import bpy

TITULO = "CENARIO: A CELA DE PAULO"
VISTAS = [("VISAO GERAL", (0.4, -4.6, 2.0), (0.6, 0.4, 1.3), 24, False),
          ("PLANTA (DE CIMA)", (0.6, -0.2, 9), (0.6, -0.2, 0), 9, True),
          ("JANELA E LUAR", (-0.6, -2.2, 1.2), (1.2, 1.15, 2.3), 26, False),
          ("DETALHE: MESA", (0.9, -1.6, 1.25), (1.6, -0.35, 0.85), 30, False)]

MESA_Z = 0.81
X0, X1, Y1, ALTO = -2.3, 3.4, 1.25, 3.4      # paredes: esquerda, direita, fundo; altura


def _cubo(nome, loc, esc, mat, col, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name, o.scale = nome, esc
    if rot:
        o.rotation_euler = rot
    o.data.materials.append(mat)
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def _cil(nome, loc, r, h, mat, col, rot=None, verts=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc)
    o = bpy.context.object
    o.name = nome
    if rot:
        o.rotation_euler = rot
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def _luz(nome, tipo, loc, energia, cor, col, tam=0.2, alvo=None):
    from mathutils import Vector
    d = bpy.data.lights.new(nome, tipo)
    d.energy, d.color = energia, cor
    if tipo == "AREA":
        d.size = tam
    elif tipo == "SPOT":
        d.spot_size, d.spot_blend, d.shadow_soft_size = math.radians(38), 0.35, tam
    else:
        d.shadow_soft_size = tam
    o = bpy.data.objects.new(nome, d)
    o.location = loc
    col.objects.link(o)
    if alvo:
        o.rotation_euler = (Vector(alvo) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def _muro(col, mat, rnd, ox, oy, eixo, comp, alto, furo=None):
    """Parede de blocos de pedra com juntas irregulares (cada bloco um cubo levemente fora do plano)."""
    h_bloco = 0.26
    y = 0.0
    fila = 0
    while y < alto:
        x = -0.25 * (fila % 2)
        while x < comp:
            w = rnd.uniform(0.42, 0.68)
            cx, cz = x + w / 2, y + h_bloco / 2
            if furo and furo[0] < cx < furo[1] and furo[2] < cz < furo[3]:
                x += w
                continue
            prof = rnd.uniform(0.18, 0.24)
            if eixo == "x":
                loc = (ox + cx, oy + rnd.uniform(-0.02, 0.02), cz)
                esc = (w - 0.025, prof, h_bloco - 0.025)
            else:
                loc = (ox + rnd.uniform(-0.02, 0.02), oy + cx, cz)
                esc = (prof, w - 0.025, h_bloco - 0.025)
            b = _cubo("bloco", loc, esc, mat, col, (rnd.uniform(-.015, .015), rnd.uniform(-.015, .015), rnd.uniform(-.01, .01)))
            x += w
        y += h_bloco
        fila += 1


def criar(col, m, semente=8):
    import materiais
    rnd = random.Random(semente)
    pedra = materiais.simples("pedra_cela", (0.20, 0.18, 0.16), 0.92, ruido=0.6, escala_ruido=9, bump=0.6)
    junta = materiais.simples("junta", (0.05, 0.045, 0.04), 1.0)
    ferro = materiais.simples("ferro_cela", (0.12, 0.11, 0.10), 0.5, metal=1.0, ruido=0.3, escala_ruido=40)
    palha = materiais.simples("palha", (0.62, 0.48, 0.22), 0.8, ruido=0.4, escala_ruido=50)
    barro = materiais.simples("barro", (0.42, 0.22, 0.12), 0.75, ruido=0.3, escala_ruido=20, bump=0.2)
    pao = materiais.simples("pao", (0.55, 0.34, 0.15), 0.8, ruido=0.5, escala_ruido=30, bump=0.5)
    # chao de lajes
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0.5, -1, 0))
    chao = bpy.context.object
    chao.data.materials.append(pedra)
    for i in range(-4, 7):
        for j in range(-8, 3):
            if rnd.random() < 0.85:
                _cubo("laje", (i * 0.62 + rnd.uniform(-.03, .03), j * 0.55 + rnd.uniform(-.03, .03), 0.012),
                      (0.58, 0.51, 0.03), pedra, col, (0, 0, rnd.uniform(-.03, .03)))
    # paredes: o fundo tem a janela alta
    _muro(col, pedra, rnd, X0, Y1, "x", X1 - X0, ALTO, furo=(3.0, 3.8, 1.9, 2.75))
    _cubo("esq_massa", (X0 - 0.25, -1.5, ALTO / 2), (0.3, 6.0, ALTO), junta, col)
    _muro(col, pedra, rnd, X0, -4.5, "y", Y1 + 4.5, ALTO)
    _cubo("dir_massa", (X1 + 0.25, -1.5, ALTO / 2), (0.3, 6.0, ALTO), junta, col)
    _muro(col, pedra, rnd, X1, -4.5, "y", Y1 + 4.5, ALTO, furo=(3.85, 4.95, 0.0, 2.15))
    _cubo("teto", (0.5, -1.5, ALTO + 0.1), (6.4, 6.0, 0.2), junta, col)
    # janela: abertura com grade e um ceu frio atras
    jx, jz = X0 + 3.4, 2.32
    for k in range(5):
        _cil("grade", (jx - 0.32 + k * 0.16, Y1 + 0.02, jz), 0.014, 0.8, ferro, col)
    _cil("grade_h", (jx, Y1 + 0.02, jz + 0.12), 0.012, 0.8, ferro, col, (0, math.radians(90), 0))
    ceu = materiais.emissao("ceu_noite", (0.18, 0.26, 0.48), 0.55)
    _cubo("ceu", (jx, Y1 + 0.35, jz), (1.2, 0.02, 1.2), ceu, col)
    # porta de madeira com ferragens na parede direita
    porta = _cubo("porta", (X1 - 0.08, -0.1, 1.05), (0.1, 1.05, 2.1), m["madeira"], col)
    for z in (0.45, 1.05, 1.65):
        _cubo("banda", (X1 - 0.14, -0.1, z), (0.03, 1.1, 0.08), ferro, col)
    _cil("argola", (X1 - 0.17, -0.45, 1.0), 0.05, 0.015, ferro, col, (0, math.radians(90), 0))
    # correntes na parede esquerda: argola chumbada e elos pendurados
    for gy in (-0.6, 0.4):
        _cil("argola_parede", (X0 + 0.14, gy, 1.75), 0.045, 0.02, ferro, col, (0, math.radians(90), 0))
        for i in range(9):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.035, minor_radius=0.009,
                                             location=(X0 + 0.16, gy + 0.01 * math.sin(i), 1.7 - i * 0.058))
            e = bpy.context.object
            e.rotation_euler = (0, math.radians(90), math.radians(90) if i % 2 else 0)
            e.data.materials.append(ferro)
            for c in e.users_collection:
                c.objects.unlink(e)
            col.objects.link(e)
    # palha espalhada junto às paredes e um catre de palha
    for i in range(520):
        if i < 300:
            x, y = rnd.uniform(X0 + 0.15, X0 + 1.4), rnd.uniform(-1.6, Y1 - 0.15)
        else:
            x, y = rnd.uniform(-1.5, 3.2), rnd.uniform(Y1 - 0.8, Y1 - 0.1)
        _cil("palha", (x, y, 0.03 + rnd.random() * 0.04 * (i < 300)), 0.003, rnd.uniform(0.12, 0.3), palha, col,
             (math.radians(90 + rnd.uniform(-15, 15)), 0, rnd.uniform(0, 6.3)), verts=5)
    _cubo("catre", (X0 + 0.75, -0.3, 0.09), (1.1, 1.9, 0.14), palha, col)
    # mesa rustica (o tampo fica na mesma altura e lugar da mesa da biblioteca)
    for k in range(4):
        _cubo("tabua_mesa", (1.6, -0.45 - 0.33 + k * 0.22, MESA_Z - 0.02), (1.4, 0.2, 0.05), m["madeira"], col,
              (0, 0, rnd.uniform(-.01, .01)))
    for dx in (-0.62, 0.62):
        for dy in (-0.33, 0.33):
            _cubo("pe_mesa", (1.6 + dx, -0.45 + dy, MESA_Z / 2 - 0.02), (0.08, 0.08, MESA_Z - 0.02), m["madeira"], col)
    _cubo("banco", (1.6, 0.25, 0.42), (0.9, 0.3, 0.06), m["madeira"], col)
    for dx in (-0.38, 0.38):
        _cubo("pe_banco", (1.6 + dx, 0.25, 0.2), (0.06, 0.26, 0.4), m["madeira"], col)
    # jarro de barro e pao duro no canto da mesa
    jarro = _cil("jarro", (2.18, -0.2, MESA_Z + 0.11), 0.07, 0.22, barro, col, verts=24)
    _cil("boca_jarro", (2.18, -0.2, MESA_Z + 0.235), 0.045, 0.03, barro, col, verts=24)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(2.05, -0.72, MESA_Z + 0.03))
    p = bpy.context.object
    p.scale = (0.09, 0.06, 0.04)
    p.data.materials.append(pao)
    bpy.ops.object.shade_smooth()
    # o processo procura o livro aberto da biblioteca para escondê-lo: deixamos um marcador oculto
    marcador = _cubo("livro_aberto", (1.9, -0.5, MESA_Z), (0.01, 0.01, 0.01), m["papel"], col)
    marcador.hide_render = True
    # luzes: luar frio pela janela, preenchimento fraco, contraluz quente da porta (tocha no corredor)
    _luz("luar", "SPOT", (jx + 0.4, Y1 + 1.6, jz + 0.8), 900, (0.55, 0.66, 1.0), col, 0.15, (1.3, -0.6, 0.6))
    _luz("luar_ar", "AREA", (jx, Y1 - 0.3, jz), 25, (0.5, 0.6, 0.95), col, 0.8, (jx, -1.0, 0.8))
    _luz("preenche", "AREA", (0.5, -4.0, 2.4), 22, (0.5, 0.55, 0.75), col, 3.0, (0.8, 0, 1.0))
    _luz("frestas_porta", "AREA", (X1 - 0.3, -0.1, 0.05), 6, (1.0, 0.55, 0.25), col, 1.0, (X1 - 1.0, -0.1, 0.0))
    mundo = bpy.data.worlds.new("noite_cela")
    mundo.use_nodes = True
    bg = mundo.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.006, 0.007, 0.012, 1)
    bg.inputs[1].default_value = 1.0
    bpy.context.scene.world = mundo


def animar(col, m, p, faixas, h):
    """Nuvens passando pela lua: a luz da janela oscila devagar."""
    luar = bpy.data.objects["luar"].data
    fim = faixas[-1][1]
    for f in range(0, fim + 1, 24):
        luar.energy = 900 * (0.75 + 0.25 * math.sin(f / 24 * 0.7) * math.sin(f / 24 * 0.23 + 1))
        luar.keyframe_insert("energy", frame=f)
