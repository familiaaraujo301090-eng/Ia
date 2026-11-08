"""Cenario: a varanda de uma casa de madeira no por do sol. Parede de tabuas com janela acesa, guarda-corpo,
colunas, cadeira de balanco, vasos de plantas, um caixote (centro da acao) e o campo com arvores la fora."""
import math
import random

import bpy

from babilonia import _cubo, _cil, _luz
from processo import _esf, _emis
from ceu import _gradiente

TITULO = "CENARIO: A VARANDA AOS 80 ANOS"
VISTAS = [("VISAO GERAL", (0.3, -4.4, 1.8), (0.6, 0.4, 1.0), 24, False),
          ("PLANTA (DE CIMA)", (0.6, -0.6, 9), (0.6, -0.6, 0), 9, True),
          ("O CAMPO", (0.4, 0.4, 1.4), (-2.0, -6.0, 1.0), 24, False),
          ("DETALHE: O CAIXOTE", (0.0, -1.3, 0.9), (0.6, -0.25, 0.5), 30, False)]
CENTRO = (0.6, -0.3, 0.5)


def criar(col, m, semente=8):
    import materiais
    rnd = random.Random(semente)
    tabua = materiais.simples("tabua_casa", (0.55, 0.42, 0.3), 0.8, ruido=0.4, escala_ruido=4, bump=0.2)
    tabua2 = materiais.simples("tabua_casa2", (0.5, 0.38, 0.27), 0.8, ruido=0.4, escala_ruido=4, bump=0.2)
    assoalho = materiais.simples("assoalho", (0.38, 0.25, 0.15), 0.6, ruido=0.4, escala_ruido=3, bump=0.2)
    branco = materiais.simples("pintura_branca", (0.85, 0.83, 0.78), 0.6)
    grama = materiais.simples("grama", (0.25, 0.32, 0.1), 0.95, ruido=0.6, escala_ruido=3, bump=0.3)
    folha = materiais.simples("copa_arvore", (0.2, 0.26, 0.1), 0.8, ruido=0.6, escala_ruido=20, bump=0.4)
    tronco = materiais.simples("tronco_arv", (0.2, 0.15, 0.1), 0.9)
    vaso = materiais.simples("vaso_barro", (0.6, 0.3, 0.17), 0.8)
    mad = m["madeira"]
    cx, cy, cz = CENTRO
    # assoalho da varanda e o campo
    for k in range(-16, 10):
        _cubo("assoalho", (0.6, k * 0.15, 0.04), (6.0, 0.14, 0.08), assoalho, col)
    bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 0, -0.4))
    bpy.context.object.data.materials.append(grama)
    # parede de tabuas da casa (ao fundo) com janela acesa e porta
    Y1 = 1.2
    for k in range(18):
        z = k * 0.16 + 0.08
        for x0, x1 in ((-2.4, -0.6), (0.6, 3.6)) if 0.8 < z < 2.0 else ((-2.4, 3.6),):
            _cubo("tabua_parede", ((x0 + x1) / 2, Y1, z), (x1 - x0, 0.06, 0.15), tabua if k % 2 else tabua2, col)
        if not (0.8 < z < 2.0):
            continue
    _cubo("janela_luz", (0.0, Y1 + 0.03, 1.4), (1.2, 0.02, 1.2), _emis("janela_quente", (1.0, 0.62, 0.32), 0.9), col)
    for dx, dz, sx, sz in ((0, 0.62, 1.3, 0.06), (0, -0.62, 1.3, 0.06), (0.62, 0, 0.06, 1.3), (-0.62, 0, 0.06, 1.3), (0, 0, 0.04, 1.2)):
        _cubo("caixilho", (dx, Y1 - 0.04, 1.4 + dz), (sx, 0.05, sz), branco, col)
    _cubo("teto_varanda", (0.6, -0.8, 2.85), (6.2, 4.4, 0.08), tabua2, col)
    # colunas e guarda-corpo na frente/lados
    for x in (-2.3, 3.5):
        for y in (-2.9, -0.8):
            _cubo("coluna_v", (x, y, 1.45), (0.12, 0.12, 2.8), branco, col)
    for y0 in (-2.9,):
        pass
    for x in (-2.3, 3.5):
        _cubo("corrimao", (x, -1.85, 0.95), (0.08, 2.1, 0.06), branco, col)
        for k in range(14):
            _cubo("balaustre", (x, -2.85 + k * 0.15, 0.5), (0.03, 0.03, 0.85), branco, col)
    # campo: arvores e colinas la fora; ceu de por do sol
    for k in range(14):
        x, y = rnd.choice([rnd.uniform(-14, -3.5), rnd.uniform(4.5, 14)]), rnd.uniform(-12, 6)
        h = rnd.uniform(2.5, 4.5)
        _cil("tronco", (x, y, h / 2 - 0.4), 0.12, h, tronco, col, verts=8)
        _esf("copa", (x, y, h - 0.2), (rnd.uniform(1.0, 1.6),) * 2 + (rnd.uniform(0.9, 1.3),), folha, col, 16)
    for k in range(4):
        _esf("colina", (-20 + k * 13, -30 + k * 2, -4), (14, 8, 6), grama, col, 24)
    _cubo("ceu", (0, -45, 8), (140, 0.1, 40), _gradiente("ceu_tarde_v", (1.0, 0.55, 0.25), (0.35, 0.45, 0.75), 1.6), col)
    _cubo("ceu_lado1", (-30, 0, 8), (0.1, 100, 40), _gradiente("ceu_tarde_v2", (1.0, 0.55, 0.25), (0.35, 0.45, 0.75), 1.4), col)
    _cubo("ceu_lado2", (30, 0, 8), (0.1, 100, 40), _gradiente("ceu_tarde_v3", (1.0, 0.6, 0.3), (0.35, 0.45, 0.75), 1.2), col)
    # cadeira de balanco a direita, com uma manta
    rx, ry = 1.45, -0.05
    for s in (-1, 1):
        for k, (dy, ang) in enumerate(((-0.3, 14), (0.0, 0), (0.3, -14))):   # o arco do balanco em 3 pedacos
            _cubo("balanco_arco", (rx + s * 0.22, ry + dy, 0.05 + abs(dy) * 0.12), (0.03, 0.31, 0.04), mad, col,
                  (math.radians(ang), 0, 0))
        _cubo("balanco_pe", (rx + s * 0.22, ry, 0.27), (0.04, 0.04, 0.4), mad, col)
    _cubo("balanco_assento", (rx, ry, 0.47), (0.5, 0.5, 0.05), mad, col)
    for k in range(5):
        _cubo("balanco_ripa", (rx - 0.2 + k * 0.1, ry + 0.25, 0.85), (0.05, 0.03, 0.75), mad, col, (math.radians(-10), 0, 0))
    _cubo("manta", (rx + 0.05, ry - 0.05, 0.52), (0.45, 0.4, 0.04), materiais.simples("manta_xadrez", (0.5, 0.12, 0.08), 0.95, ruido=0.4, escala_ruido=30), col)
    # vasos de plantas
    for x, y in ((-1.9, 0.9), (-1.6, 1.0), (3.1, 0.9)):
        _cil("vaso", (x, y, 0.25), 0.16, 0.34, vaso, col)
        _esf("planta", (x, y, 0.6), (0.3, 0.3, 0.35), folha, col, 16)
    # o caixote de madeira (centro da acao)
    for k in range(4):
        _cubo("caixote_ripa", (cx, cy, 0.06 + k * 0.125), (0.5, 0.42, 0.1), mad, col)
    _cubo("caixote_topo", (cx, cy, cz - 0.01), (0.52, 0.44, 0.02), mad, col)
    mk = _cubo("livro_aberto", (cx, cy, cz), (0.01, 0.01, 0.01), m["papel"], col)
    mk.hide_render = True
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy, sol.color, sol.angle = 3.5, (1.0, 0.62, 0.35), math.radians(3)
    o = bpy.data.objects.new("sol", sol)
    o.rotation_euler = (math.radians(75), 0, math.radians(-30))
    col.objects.link(o)
    _luz("janela_dentro", "AREA", (0.0, Y1 - 0.3, 1.4), 60, (1.0, 0.7, 0.4), col, 1.2, (0.4, -1, 0.8))
    _luz("preenche", "AREA", (0.6, -4.0, 2.4), 60, (0.6, 0.65, 0.95), col, 3.0, (0.8, 0, 1.0))
    mundo = bpy.data.worlds.new("tarde_varanda")
    mundo.use_nodes = True
    bg = mundo.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.5, 0.42, 0.45, 1)
    bg.inputs[1].default_value = 0.5
    bpy.context.scene.world = mundo


def animar(col, m, p, faixas, h):
    """O sol desce durante o minuto."""
    sol = bpy.data.objects["sol"]
    fim = faixas[-1][1]
    for f, e, c, inc in ((0, 3.5, (1.0, 0.62, 0.35), 75), (fim, 2.2, (1.0, 0.45, 0.22), 82)):
        sol.data.energy, sol.data.color = e, c
        sol.data.keyframe_insert("energy", frame=f)
        sol.data.keyframe_insert("color", frame=f)
        sol.rotation_euler[0] = math.radians(inc)
        sol.keyframe_insert("rotation_euler", frame=f)
