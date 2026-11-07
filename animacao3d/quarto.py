"""Cenario: um quarto de madrugada. Parede pintada com rodape, janela com a cidade e a lua, cortina,
cama desfeita, criado-mudo (onde a acao acontece), tapete, quadro, abajur apagado e uma cadeira com roupa.

criar(col, m)                 -> monta o quarto (o criado-mudo fica no 'centro' da historia)
animar(col, m, p, faixas, h)  -> a madrugada escurece no meio e amanhece no fim
"""
import math
import random

import bpy

from babilonia import _cubo, _cil, _luz, _obj
from atenas import _esfera

TITULO = "CENARIO: O QUARTO, 3 DA MANHA"
VISTAS = [("VISAO GERAL", (0.3, -4.4, 2.0), (0.6, 0.4, 1.0), 24, False),
          ("PLANTA (DE CIMA)", (0.6, -0.4, 9), (0.6, -0.4, 0), 9, True),
          ("A JANELA", (1.6, -2.0, 1.3), (0.4, 1.2, 1.6), 28, False),
          ("DETALHE: CRIADO-MUDO", (0.2, -1.4, 0.9), (0.6, -0.25, 0.55), 30, False)]

CRIADO = (0.6, -0.3, 0.55)        # topo do criado-mudo: centro da acao
X0, X1, Y1, ALTO = -2.4, 3.6, 1.2, 2.8


def _emissao(nome, cor, forca):
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*cor, 1)
    em.inputs["Strength"].default_value = forca
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return mat


def criar(col, m, semente=5):
    import materiais
    rnd = random.Random(semente)
    parede = materiais.simples("parede_quarto", (0.36, 0.42, 0.5), 0.9, ruido=0.15, escala_ruido=4)
    rodape = materiais.simples("rodape", (0.85, 0.83, 0.78), 0.5)
    piso = materiais.simples("piso_madeira", (0.35, 0.22, 0.13), 0.55, ruido=0.5, escala_ruido=3, bump=0.15)
    lencol = materiais.simples("lencol", (0.78, 0.8, 0.84), 0.9, ruido=0.2, escala_ruido=30, bump=0.3)
    coberta = materiais.simples("coberta", (0.18, 0.24, 0.38), 0.95, ruido=0.4, escala_ruido=50, bump=0.5)
    tapete = materiais.simples("tapete_quarto", (0.55, 0.5, 0.42), 0.95, ruido=0.5, escala_ruido=80, bump=0.6)
    movel = materiais.simples("movel", (0.42, 0.28, 0.17), 0.5, ruido=0.3, escala_ruido=10, bump=0.1)
    cortina = materiais.simples("cortina", (0.5, 0.42, 0.34), 0.95, ruido=0.3, escala_ruido=8)
    metal = materiais.simples("metal_preto", (0.04, 0.04, 0.045), 0.35, metal=0.8)
    cupula = materiais.simples("cupula", (0.85, 0.78, 0.62), 0.9, sss=0.2)
    # piso de tabuas, tapete, paredes e teto
    for k in range(-8, 12):
        _cubo("tabua", (0.6, -1.4 + k * 0.18, -0.01), (6.2, 0.17, 0.02), piso, col)
    _cubo("tapete", (0.4, -0.9, 0.006), (2.4, 1.6, 0.012), tapete, col)
    jx, jz, jw, jh = 0.6, 1.55, 1.1, 1.2       # janela atras do criado-mudo
    _cubo("parede_esq_jan", ((X0 + jx - jw / 2) / 2, Y1, ALTO / 2), (jx - jw / 2 - X0, 0.12, ALTO), parede, col)
    _cubo("parede_dir_jan", ((X1 + jx + jw / 2) / 2, Y1, ALTO / 2), (X1 - jx - jw / 2, 0.12, ALTO), parede, col)
    _cubo("parede_baixo_jan", (jx, Y1, (jz - jh / 2) / 2), (jw, 0.12, jz - jh / 2), parede, col)
    _cubo("parede_cima_jan", (jx, Y1, (ALTO + jz + jh / 2) / 2), (jw, 0.12, ALTO - jz - jh / 2), parede, col)
    for x in (X0, X1):
        _cubo("parede_lado", (x, -1.5, ALTO / 2), (0.12, 5.6, ALTO), parede, col)
    _cubo("teto", (0.6, -1.5, ALTO + 0.06), (6.2, 5.6, 0.12), rodape, col)
    _cubo("rodape", (0.6, Y1 - 0.07, 0.06), (6.0, 0.02, 0.12), rodape, col)
    # moldura e vidro da janela; la fora, ceu noturno com a lua e predios com janelas acesas
    for dx, dz, sx, sz in ((0, jh / 2, jw + 0.1, 0.05), (0, -jh / 2, jw + 0.16, 0.06), (jw / 2, 0, 0.05, jh),
                           (-jw / 2, 0, 0.05, jh), (0, 0, 0.03, jh), (0, 0.1, jw, 0.03)):
        _cubo("caixilho", (jx + dx, Y1 - 0.04, jz + dz), (sx, 0.06, sz), rodape, col)
    ceu = _emissao("ceu_noite", (0.05, 0.08, 0.2), 1.0)
    ceu.name = "ceu_noite"
    _cubo("ceu", (jx, Y1 + 6, 2.5), (12, 0.1, 8), ceu, col)
    lua = _emissao("lua", (0.9, 0.92, 1.0), 6.0)
    _esfera("lua", (jx + 1.4, Y1 + 5.8, 3.4), (0.3, 0.05, 0.3), lua, col)
    predio = materiais.simples("predio", (0.02, 0.02, 0.03), 1.0)
    jan_acesa = _emissao("janela_acesa", (1.0, 0.75, 0.4), 3.0)
    for k in range(7):
        x, h, w = jx - 2.4 + k * 0.75 + rnd.uniform(-0.1, 0.1), rnd.uniform(1.6, 3.4), rnd.uniform(0.4, 0.65)
        _cubo("predio", (x, Y1 + 4.5, h / 2 - 0.5), (w, 0.6, h), predio, col)
        for i in range(5):
            if rnd.random() < 0.35:
                _cubo("janelinha", (x + rnd.uniform(-w / 3, w / 3), Y1 + 4.18, rnd.uniform(0.0, h - 0.7)),
                      (0.06, 0.02, 0.08), jan_acesa, col)
    for s in (-1, 1):
        for k in range(6):       # pregas verticais
            _cubo("cortina", (jx + s * (jw / 2 + 0.05 + k * 0.065), Y1 - 0.12 - 0.025 * (k % 2), jz + 0.05),
                  (0.07, 0.03, jh + 0.55), cortina, col)
    _cil("varao", (jx, Y1 - 0.12, jz + jh / 2 + 0.32), 0.012, jw + 1.1, metal, col, (0, math.radians(90), 0))
    # a cama a direita, desfeita
    bx, by = 1.75, 0.0
    _cubo("cama_base", (bx, by, 0.2), (1.5, 2.1, 0.3), movel, col)
    _cubo("cabeceira", (bx, Y1 - 0.1, 0.65), (1.55, 0.08, 1.0), movel, col)
    _cubo("colchao", (bx, by, 0.44), (1.45, 2.0, 0.2), lencol, col)
    tr = _cubo("travesseiro", (bx - 0.3, Y1 - 0.38, 0.6), (0.6, 0.35, 0.14), lencol, col, (math.radians(-12), 0, 0))
    tr.modifiers.new("macio", "SUBSURF").levels = 2
    cb = _cubo("coberta", (bx + 0.08, by - 0.35, 0.57), (1.5, 1.3, 0.06), coberta, col, (0, math.radians(3), math.radians(-6)))
    cb.modifiers.new("macio", "SUBSURF").levels = 2
    # o criado-mudo: o palco da historia (sem mesa: e so o movel ao lado da cama)
    cx, cy, cz = CRIADO
    _cubo("criado_mudo", (cx, cy, cz / 2), (0.5, 0.42, cz - 0.01), movel, col)
    _cubo("gaveta", (cx, cy - 0.215, cz * 0.62), (0.44, 0.01, 0.16), movel, col)
    _cil("puxador", (cx, cy - 0.225, cz * 0.62), 0.012, 0.02, metal, col, (math.radians(90), 0, 0))
    # abajur apagado, livro e copo d'agua no criado-mudo (no canto de tras)
    _cil("abajur_pe", (cx + 0.16, cy + 0.12, cz + 0.13), 0.012, 0.26, metal, col)
    _cil("abajur_base", (cx + 0.16, cy + 0.12, cz + 0.01), 0.06, 0.02, metal, col)
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.11, radius2=0.07, depth=0.14,
                                    location=(cx + 0.16, cy + 0.12, cz + 0.3))
    c = bpy.context.object
    c.data.materials.append(cupula)
    _obj(c, col)
    # quadro na parede e cadeira com uma camisa largada
    _cubo("quadro", (-1.2, Y1 - 0.08, 1.6), (0.7, 0.03, 0.5), metal, col)
    _cubo("quadro_tela", (-1.2, Y1 - 0.1, 1.6), (0.62, 0.01, 0.42), coberta, col)
    for dx in (-0.2, 0.2):
        for dy in (-0.2, 0.2):
            _cil("cadeira_pe", (-1.6 + dx, -0.4 + dy, 0.22), 0.02, 0.44, movel, col)
    _cubo("cadeira_assento", (-1.6, -0.4, 0.46), (0.46, 0.46, 0.04), movel, col)
    _cubo("cadeira_costas", (-1.6, -0.19, 0.75), (0.46, 0.04, 0.55), movel, col)
    cam = _cubo("camisa", (-1.58, -0.3, 0.6), (0.5, 0.3, 0.02), cortina, col, (math.radians(70), 0, math.radians(8)))
    cam.modifiers.new("macio", "SUBSURF").levels = 2
    mk = _cubo("livro_aberto", (cx, cy, cz), (0.01, 0.01, 0.01), m["papel"], col)
    mk.hide_render = True
    # luz: a lua entra fria pela janela; um resto de luz da rua; quase nada de preenchimento
    _luz("luar", "SPOT", (jx + 0.4, Y1 + 1.6, 2.6), 900, (0.55, 0.65, 1.0), col, 0.4, (cx - 0.2, cy - 0.6, 0.3))
    _luz("rua", "AREA", (jx, Y1 + 0.3, jz), 25, (0.5, 0.6, 1.0), col, 1.0, (jx, -1, 1.0))
    _luz("preenche", "AREA", (0.6, -4.0, 2.2), 12, (0.45, 0.5, 0.75), col, 3.0, (0.6, 0, 0.8))
    mundo = bpy.data.worlds.new("noite_quarto")
    mundo.use_nodes = True
    mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.005, 0.007, 0.015, 1)
    bpy.context.scene.world = mundo


def animar(col, m, p, faixas, h):
    """A madrugada pesa no meio (a ansiedade cresce) e amanhece no fim (o ceu e o luar esquentam)."""
    luar = bpy.data.objects["luar"].data
    ceu = bpy.data.materials["ceu_noite"].node_tree.nodes["Emission"].inputs
    pico, calma, fim = faixas[4][0], faixas[5][0], faixas[-1][1]
    for f, e, c, cc, fc in ((0, 900, (0.55, 0.65, 1.0), (0.05, 0.08, 0.2), 1.0),
                            (pico, 900, (0.55, 0.65, 1.0), (0.05, 0.08, 0.2), 1.0),
                            (pico + 40, 350, (0.45, 0.5, 0.9), (0.03, 0.04, 0.12), 0.6),
                            (calma, 350, (0.45, 0.5, 0.9), (0.03, 0.04, 0.12), 0.6),
                            (calma + 90, 1400, (1.0, 0.7, 0.45), (0.9, 0.55, 0.35), 1.6),
                            (fim, 1500, (1.0, 0.75, 0.5), (0.95, 0.65, 0.42), 1.8)):
        luar.energy, luar.color = e, c
        luar.keyframe_insert("energy", frame=f)
        luar.keyframe_insert("color", frame=f)
        ceu["Color"].default_value = (*cc, 1)
        ceu["Color"].keyframe_insert("default_value", frame=f)
        ceu["Strength"].default_value = fc
        ceu["Strength"].keyframe_insert("default_value", frame=f)
