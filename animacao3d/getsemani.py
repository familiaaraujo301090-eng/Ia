"""Cenario: o jardim do Getsemani, noite. Chao de terra com pedras, oliveiras retorcidas, um muro baixo de pedra,
a muralha de Jerusalem ao longe com janelas acesas, a lua, e tochas que se aproximam no fim.
A acao acontece sobre uma rocha chata (centro)."""
import math
import random

import bpy

from babilonia import _cubo, _cil, _luz
from processo import _esf, _emis
from ceu import _gradiente

TITULO = "CENARIO: O JARDIM DO GETSEMANI"
VISTAS = [("VISAO GERAL", (0.3, -4.6, 1.8), (0.6, 1.0, 1.0), 24, False),
          ("PLANTA (DE CIMA)", (0.6, 0.0, 10), (0.6, 0.0, 0), 10, True),
          ("A MURALHA", (0.6, -1.5, 1.2), (-1.0, 20, 2.0), 26, False),
          ("DETALHE: A ROCHA", (0.0, -1.3, 0.8), (0.6, -0.25, 0.4), 30, False)]
CENTRO = (0.6, -0.3, 0.42)


def _oliveira(x, y, rnd, tronco, folha, col, esc=1.0):
    for k in range(5):
        a = k * 1.4 + rnd.uniform(0, 1)
        _cil("oliveira", (x + 0.1 * math.sin(a) * esc, y + 0.08 * math.cos(a) * esc, (0.25 + k * 0.38) * esc),
             (0.16 - k * 0.02) * esc, 0.48 * esc, tronco, col,
             (math.radians(12 * math.sin(a)), math.radians(14 * math.cos(a)), 0), 9)
    for k in range(8):
        a = k / 8 * math.tau
        _esf("copa", (x + 0.8 * esc * math.cos(a) * rnd.uniform(0.5, 1.1), y + 0.7 * esc * math.sin(a) * rnd.uniform(0.5, 1.1),
                      (2.2 + rnd.uniform(-0.3, 0.4)) * esc), (0.6 * esc, 0.55 * esc, 0.4 * esc), folha, col, 14)


def criar(col, m, semente=33):
    import materiais
    rnd = random.Random(semente)
    terra = materiais.simples("terra_noite", (0.28, 0.22, 0.16), 0.95, ruido=0.6, escala_ruido=5, bump=0.4)
    pedra = materiais.simples("pedra_jardim", (0.45, 0.42, 0.38), 0.9, ruido=0.5, escala_ruido=8, bump=0.6)
    tronco = materiais.simples("oliveira_t", (0.22, 0.18, 0.14), 0.9, ruido=0.6, escala_ruido=20, bump=0.8)
    folha = materiais.simples("oliveira_f", (0.2, 0.26, 0.16), 0.75, ruido=0.6, escala_ruido=30, bump=0.5)
    muralha = materiais.simples("muralha", (0.5, 0.44, 0.34), 0.9, ruido=0.5, escala_ruido=4, bump=0.3)
    bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 10, 0))
    bpy.context.object.data.materials.append(terra)
    cx, cy, cz = CENTRO
    for k in range(40):
        x, y = rnd.uniform(-4, 5), rnd.uniform(-3, 4)
        if -1.2 < x < 1.5 and -2.5 < y < 0.4:
            continue
        r = rnd.uniform(0.06, 0.22)
        _esf("pedrinha", (x, y, r * 0.3), (r, r * 0.8, r * 0.5), pedra, col, 10)
    for x, y, e in ((-1.9, 1.0, 1.0), (2.8, 1.4, 1.1), (-0.4, 2.6, 0.9), (1.6, 3.2, 1.0), (-3.0, 3.0, 1.2), (3.8, -0.6, 0.9)):
        _oliveira(x, y, rnd, tronco, folha, col, e)
    x = -4.0
    while x < 5.0:            # muro baixo de pedras irregulares, duas fiadas
        w = rnd.uniform(0.3, 0.55)
        for fila in range(2):
            pd = _cubo("muro", (x + w / 2 + fila * 0.15, 4.6 + rnd.uniform(-0.04, 0.04), 0.14 + fila * 0.27),
                       (w - 0.03, 0.4, rnd.uniform(0.22, 0.28)), pedra, col,
                       (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), rnd.uniform(-0.06, 0.06)))
            pd.modifiers.new("canto", "BEVEL").width = 0.04
        x += w
    # Jerusalem ao longe: muralha com ameias, torres e janelas acesas
    acesa = _emis("janela_jer", (1.0, 0.6, 0.25), 4.0)
    for k in range(30):
        _cubo("muralha", (-14 + k * 1.0, 22, 1.6), (0.98, 1.0, 3.2), muralha, col)
        if k % 2:
            _cubo("ameia", (-14 + k * 1.0, 22, 3.35), (0.5, 1.0, 0.3), muralha, col)
    for x in (-10, -3, 4, 11):
        _cubo("torre", (x, 22, 2.6), (2.0, 1.4, 5.2), muralha, col)
    for k in range(18):
        _cubo("janela_jer", (rnd.uniform(-13, 15), 21.45, rnd.uniform(1.0, 4.6)), (0.12, 0.05, 0.2), acesa, col)
    _cubo("ceu", (0, 40, 8), (120, 0.1, 40), _gradiente("ceu_noite_jer", (0.06, 0.07, 0.14), (0.01, 0.015, 0.04), 1.0), col)
    _esf("lua", (8, 38, 14), (1.4, 0.1, 1.4), _emis("lua_jer", (0.95, 0.95, 1.0), 6.0), col)
    # a rocha chata (centro da acao)
    rocha = _cubo("rocha", (cx, cy, cz / 2), (0.62, 0.5, cz), pedra, col, (0, 0, math.radians(5)))
    rocha.modifiers.new("canto", "BEVEL").width = 0.04
    # tochas que vao chegar (luzes desligadas ate o fim)
    for k, (x, y) in enumerate(((-2.5, 6.5), (-1.8, 7.2), (-3.2, 7.8))):
        _cil("tocha", (x, y, 1.2), 0.025, 0.7, m["madeira"], col)
        _esf("fogo_tocha", (x, y, 1.62), (0.05, 0.05, 0.1), m["chama"], col, 10)
        _luz(f"tocha{k}", "POINT", (x, y, 1.75), 0, (1.0, 0.5, 0.2), col, 0.1)
    mk = _cubo("livro_aberto", (cx, cy, cz), (0.01, 0.01, 0.01), m["papel"], col)
    mk.hide_render = True
    _luz("luar", "SPOT", (6, 14, 9), 9000, (0.55, 0.65, 1.0), col, 0.4, (cx, cy, 0.3))
    _luz("preenche", "AREA", (0.6, -4.0, 2.2), 20, (0.45, 0.5, 0.8), col, 3.0, (0.6, 0, 0.8))
    mundo = bpy.data.worlds.new("noite_jer")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.012, 0.025, 1)
    bpy.context.scene.world = mundo


def animar(col, m, p, faixas, h):
    """As tochas acendem e tremulam no plano das trinta moedas e somem depois."""
    f0, f1 = faixas[4]
    for k in range(3):
        luz = bpy.data.objects[f"tocha{k}"].data
        for f, e in ((0, 0), (f0, 0), (f0 + 15, 160), (f1, 180), (f1 + 30, 0)):
            luz.energy = e
            luz.keyframe_insert("energy", frame=f)
