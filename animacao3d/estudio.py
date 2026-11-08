"""Cenario: o estudio do podcast. Paredes escuras com placas de espuma acustica, um letreiro de neon
'SOCRATES CAST', luz vermelha 'NO AR', dois microfones em bracos articulados, ring light, sofa, plantas
e uma caixa de som de madeira (centro da acao)."""
import math
import random

import bpy

from babilonia import _cubo, _cil, _luz
from processo import _esf, _emis, _texto, _cilindro

TITULO = "CENARIO: O ESTUDIO DO PODCAST"
VISTAS = [("VISAO GERAL", (0.3, -4.2, 1.7), (0.6, 0.6, 1.3), 24, False),
          ("PLANTA (DE CIMA)", (0.6, -0.6, 8), (0.6, -0.6, 0), 9, True),
          ("O LETREIRO", (0.6, -1.8, 1.5), (0.4, 1.2, 1.9), 28, False),
          ("DETALHE: A CAIXA DE SOM", (0.0, -1.3, 1.0), (0.6, -0.25, 0.62), 30, False)]
CENTRO = (0.6, -0.3, 0.62)


def criar(col, m, semente=4):
    import materiais
    rnd = random.Random(semente)
    parede = materiais.simples("parede_estudio", (0.05, 0.05, 0.06), 0.9)
    espuma = materiais.simples("espuma", (0.07, 0.07, 0.09), 0.95, ruido=0.4, escala_ruido=60, bump=0.6)
    espuma2 = materiais.simples("espuma2", (0.12, 0.06, 0.05), 0.95, ruido=0.4, escala_ruido=60, bump=0.6)
    piso = materiais.simples("piso_estudio", (0.2, 0.17, 0.15), 0.4, ruido=0.3, escala_ruido=3)
    preto = materiais.simples("preto_fosco", (0.015, 0.015, 0.018), 0.5, metal=0.3)
    sofa = materiais.simples("sofa", (0.35, 0.22, 0.12), 0.7, ruido=0.2, escala_ruido=20)
    folha = materiais.simples("planta_est", (0.12, 0.3, 0.1), 0.6, ruido=0.5, escala_ruido=20)
    cx, cy, cz = CENTRO
    Y1, X0, X1, ALTO = 1.2, -2.4, 3.6, 3.0
    bpy.ops.mesh.primitive_plane_add(size=14, location=(0.6, -1, 0))
    bpy.context.object.data.materials.append(piso)
    _cubo("tapete", (0.6, -0.6, 0.005), (3.0, 2.2, 0.01), materiais.simples("tapete_est", (0.15, 0.12, 0.2), 0.95, ruido=0.4, escala_ruido=50), col)
    _cubo("parede_fundo", (0.6, Y1 + 0.05, ALTO / 2), (6.2, 0.1, ALTO), parede, col)
    for x in (X0, X1):
        _cubo("parede_lado", (x, -1.5, ALTO / 2), (0.1, 5.6, ALTO), parede, col)
    _cubo("teto", (0.6, -1.5, ALTO), (6.2, 5.6, 0.1), parede, col)
    # placas de espuma (grade de quadrados com cunhas alternadas)
    for i in range(12):
        for j in range(6):
            x, z = X0 + 0.35 + i * 0.5, 0.45 + j * 0.42
            if -0.7 < x < 1.9 and 1.45 < z < 2.4:
                continue          # espaco do letreiro
            mat = espuma2 if (i * 7 + j * 3) % 9 == 0 else espuma
            _cubo("espuma", (x, Y1 - 0.03, z), (0.46, 0.06, 0.38), mat, col, (0, math.radians(90 * ((i + j) % 2)), 0))
            for k in range(3):
                _cubo("cunha", (x, Y1 - 0.07, z - 0.12 + k * 0.12), (0.44, 0.03, 0.05), mat, col)
    # letreiro de neon
    neon = _emis("neon", (1.0, 0.25, 0.65), 12.0)
    neon2 = _emis("neon2", (0.25, 0.8, 1.0), 10.0)
    _texto("letreiro", "SÓCRATES", (0.6, Y1 - 0.06, 2.1), 0.32, neon, col, ext=0.005)
    _texto("letreiro2", "CAST", (0.6, Y1 - 0.06, 1.72), 0.26, neon2, col, ext=0.005)
    _luz("luz_neon", "AREA", (0.6, Y1 - 0.4, 1.95), 40, (1.0, 0.35, 0.7), col, 1.4, (0.6, -1, 1.2))
    # luz NO AR
    _cubo("no_ar_caixa", (-1.6, Y1 - 0.06, 2.55), (0.5, 0.06, 0.18), preto, col)
    _texto("no_ar", "NO AR", (-1.6, Y1 - 0.1, 2.55), 0.1, _emis("no_ar", (1.0, 0.08, 0.05), 8), col, ext=0.003)
    # microfones em bracos articulados (um de cada lado)
    for x, s in ((-0.3, 1), (1.6, -1)):
        _cilindro("mic_base", (x, -0.9, 0.02), 0.12, 0.03, preto, col)
        _cilindro("mic_haste", (x, -0.9, 0.62), 0.012, 1.2, preto, col)
        _cilindro("mic_braco", (x + s * 0.18, -0.9, 1.3), 0.01, 0.5, preto, col, (0, math.radians(s * 60), 0))
        _cilindro("mic", (x + s * 0.4, -0.9, 1.38), 0.035, 0.16, preto, col, (math.radians(10), 0, 0))
        _esf("mic_grade", (x + s * 0.4, -0.9, 1.47), (0.036, 0.036, 0.04), materiais.simples("grade", (0.2, 0.2, 0.22), 0.4, metal=0.9), col, 16)
    # ring light
    bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.025, location=(2.7, -1.6, 1.6), rotation=(math.radians(90), 0, math.radians(-40)))
    bpy.context.object.data.materials.append(_emis("ring", (1.0, 0.95, 0.9), 6))
    _cilindro("ring_pe", (2.7, -1.6, 0.72), 0.015, 1.45, preto, col)
    _luz("ring_luz", "AREA", (2.6, -1.7, 1.6), 80, (1.0, 0.95, 0.9), col, 0.6, (0.6, -0.2, 1.2))
    # sofa e plantas
    _cubo("sofa_base", (2.7, 0.6, 0.22), (1.4, 0.7, 0.44), sofa, col)
    _cubo("sofa_encosto", (2.7, 0.9, 0.62), (1.4, 0.18, 0.5), sofa, col)
    for x, y in ((-1.9, 0.8), (3.3, -0.4)):
        _cilindro("vaso_est", (x, y, 0.22), 0.16, 0.44, preto, col)
        for k in range(7):
            a = k / 7 * math.tau
            f = _esf("folha_est", (x + 0.15 * math.cos(a), y + 0.15 * math.sin(a), 0.75 + rnd.uniform(0, 0.3)), (0.06, 0.2, 0.02), folha, col, 10)
            f.rotation_euler = (math.radians(50), 0, a + math.pi / 2)
    # a caixa de som de madeira (centro da acao)
    _cubo("caixa_som", (cx, cy, cz / 2), (0.52, 0.42, cz), m["madeira"], col)
    _cubo("tela_som", (cx, cy - 0.215, cz / 2), (0.44, 0.01, cz - 0.1), materiais.simples("tela_tecido", (0.08, 0.08, 0.09), 0.95, ruido=0.3, escala_ruido=200, bump=0.5), col)
    for dz in (0.18, 0.42):
        _cilindro("alto_falante", (cx, cy - 0.222, dz), 0.08 if dz < 0.3 else 0.05, 0.01, preto, col, (math.radians(90), 0, 0))
    mk = _cubo("livro_aberto", (cx, cy, cz), (0.01, 0.01, 0.01), m["papel"], col)
    mk.hide_render = True
    _luz("chave", "AREA", (-1.2, -2.4, 2.4), 120, (1.0, 0.85, 0.7), col, 1.5, (0.4, -0.3, 1.0))
    _luz("contra", "SPOT", (0.6, 0.9, 2.8), 300, (0.4, 0.6, 1.0), col, 0.3, (cx, cy, cz))
    mundo = bpy.data.worlds.new("estudio_mundo")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.01, 0.01, 0.015, 1)
    bpy.context.scene.world = mundo


def animar(col, m, p, faixas, h):
    """O neon pisca de leve no comeco."""
    em = bpy.data.materials["neon"].node_tree.nodes["Emission"].inputs["Strength"]
    for f, s in ((0, 12), (4, 3), (7, 12), (11, 5), (14, 12)):
        em.default_value = s
        em.keyframe_insert("default_value", frame=f)
