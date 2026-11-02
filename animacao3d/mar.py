"""Cenario: barco no mar durante a tempestade, que se acalma no meio do video.

criar(col, m)                 -> mar (modificador Ocean), barco, chuva, ceu e luzes
animar(col, m, p, faixas, h)  -> poe o Elias no barco e anima ondas, balanco, chuva, raios e o amanhecer
raios(faixas, h)              -> quadros dos relampagos (usado tambem no som)

A historia diz em "calma" o numero do plano em que o mar se acalma (1 = primeiro plano).
"""
import math
import random

import bmesh
import numpy as np
import bpy

TITULO = "CENARIO: O MAR NA TEMPESTADE"
VISTAS = [("VISAO GERAL", (7, -9, 4.5), (0, 0, 0.6), 24, False),
          ("PLANTA (DE CIMA)", (0, 0, 22), (0, 0, 0), 9, True),
          ("LATERAL", (-6, -1.5, 1.2), (0, 0, 0.8), 28, False),
          ("DETALHE: BARCO", (2.2, -3.4, 2.0), (0, 0.4, 0.7), 30, False)]

COMPRIMENTO, BOCA = 4.6, 1.7  # barco: comprimento (eixo y) e largura


def _no(nt, tipo, **vals):
    n = nt.nodes.new(tipo)
    for k, v in vals.items():
        n.inputs[k].default_value = v
    return n


def _material_agua():
    mat = bpy.data.materials.new("agua")
    mat.use_nodes = True
    nt = mat.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.06
    p.inputs["IOR"].default_value = 1.33
    # Espuma branca nas cristas: altura da onda (coordenada z do objeto) acima de um limiar, quebrada por ruido.
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    ruido = _no(nt, "ShaderNodeTexNoise", Scale=6.0, Detail=6.0)
    nt.links.new(coord.outputs["Object"], ruido.inputs["Vector"])
    soma = nt.nodes.new("ShaderNodeMath")
    soma.operation = "MULTIPLY_ADD"
    soma.inputs[1].default_value = 0.6
    nt.links.new(ruido.outputs["Fac"], soma.inputs[0])
    nt.links.new(sep.outputs["Z"], soma.inputs[2])
    faixa = nt.nodes.new("ShaderNodeMapRange")
    faixa.inputs["From Min"].default_value = 0.85
    faixa.inputs["From Max"].default_value = 1.25
    nt.links.new(soma.outputs[0], faixa.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (0.006, 0.02, 0.028, 1)
    mix.inputs[7].default_value = (0.55, 0.6, 0.62, 1)
    nt.links.new(faixa.outputs[0], mix.inputs["Factor"])
    nt.links.new(mix.outputs[2], p.inputs["Base Color"])
    rug = nt.nodes.new("ShaderNodeMapRange")
    rug.inputs["To Min"].default_value = 0.06
    rug.inputs["To Max"].default_value = 0.7
    nt.links.new(faixa.outputs[0], rug.inputs["Value"])
    nt.links.new(rug.outputs[0], p.inputs["Roughness"])
    return mat


def _achatar_no_barco(obj):
    """Geometry Nodes depois do Ocean: a agua fica rasa e lisa dentro do casco (senao as ondas furam o barco)."""
    ng = bpy.data.node_groups.new("achatar", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nt = ng.nodes
    ent, sai = nt.new("NodeGroupInput"), nt.new("NodeGroupOutput")
    pos = nt.new("GeometryNodeInputPosition")
    sep = nt.new("ShaderNodeSeparateXYZ")
    ng.links.new(pos.outputs[0], sep.inputs[0])
    # distancia eliptica: (x/a)^2 + (y/b)^2
    def mat_op(op, a, b=None):
        n = nt.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                ng.links.new(v, n.inputs[i])
        return n.outputs[0]
    dx = mat_op("POWER", mat_op("DIVIDE", sep.outputs["X"], BOCA * 0.75), 2.0)
    dy = mat_op("POWER", mat_op("DIVIDE", sep.outputs["Y"], COMPRIMENTO * 0.62), 2.0)
    d = mat_op("SQRT", mat_op("ADD", dx, dy))
    peso = nt.new("ShaderNodeMapRange")
    peso.interpolation_type = "SMOOTHSTEP"
    peso.inputs["From Min"].default_value = 1.0
    peso.inputs["From Max"].default_value = 2.1
    ng.links.new(d, peso.inputs["Value"])
    # z_novo = z * peso + (-0.32) * (1 - peso)
    inv = mat_op("SUBTRACT", 1.0, peso.outputs[0])
    znovo = mat_op("ADD", mat_op("MULTIPLY", sep.outputs["Z"], peso.outputs[0]), mat_op("MULTIPLY", inv, -0.32))
    comb = nt.new("ShaderNodeCombineXYZ")
    ng.links.new(sep.outputs["X"], comb.inputs[0])
    ng.links.new(sep.outputs["Y"], comb.inputs[1])
    ng.links.new(znovo, comb.inputs[2])
    sp = nt.new("GeometryNodeSetPosition")
    ng.links.new(ent.outputs[0], sp.inputs["Geometry"])
    ng.links.new(comb.outputs[0], sp.inputs["Position"])
    lis = nt.new("GeometryNodeSetShadeSmooth")
    ng.links.new(sp.outputs[0], lis.inputs["Geometry"])
    ng.links.new(lis.outputs[0], sai.inputs[0])
    mod = obj.modifiers.new("achatar", "NODES")
    mod.node_group = ng


def _mar(col, mat):
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    mar = bpy.context.object
    mar.name = "mar"
    oc = mar.modifiers.new("ondas", "OCEAN")
    oc.geometry_mode = "GENERATE"
    oc.resolution = 14
    oc.spatial_size = 40
    oc.size = 1.0
    oc.repeat_x = oc.repeat_y = 2
    oc.wave_scale = 1.6
    oc.choppiness = 1.3
    oc.wind_velocity = 18
    oc.wave_alignment = 0.6
    oc.wave_direction = math.radians(25)
    oc.random_seed = 7
    _achatar_no_barco(mar)
    mar.data.materials.append(mat)
    for c in mar.users_collection:
        c.objects.unlink(mar)
    col.objects.link(mar)
    return mar


def _casco(mat):
    """Casco por secoes em U ao longo do comprimento, com proa e popa afinando e subindo."""
    bm = bmesh.new()
    n_sec, n_u = 22, 14
    aneis = []
    for i in range(n_sec + 1):
        v = i / n_sec * 2 - 1  # -1 popa ... 1 proa
        y = v * COMPRIMENTO / 2
        afina = (1 - abs(v) ** 2.4) ** 0.55
        meia = BOCA / 2 * max(afina, 0.02)
        fundo = -0.42 * max(afina, 0.15) ** 0.4
        borda = 0.42 + 0.22 * abs(v) ** 3  # proa e popa sobem
        anel = []
        for j in range(n_u + 1):
            a = math.pi * j / n_u  # 0..pi: borda esq -> fundo -> borda dir
            x = -math.cos(a) * meia
            z = borda + (fundo - borda) * math.sin(a) ** 0.7
            anel.append(bm.verts.new((x, y, z)))
        aneis.append(anel)
    for i in range(n_sec):
        for j in range(n_u):
            bm.faces.new((aneis[i][j], aneis[i + 1][j], aneis[i + 1][j + 1], aneis[i][j + 1]))
    malha = bpy.data.meshes.new("casco")
    bm.to_mesh(malha)
    bm.free()
    o = bpy.data.objects.new("casco", malha)
    o.data.materials.append(mat)
    s = o.modifiers.new("espessura", "SOLIDIFY")
    s.thickness = 0.05
    s.offset = 1
    o.modifiers.new("liso", "SUBSURF").levels = 1
    for pol in malha.polygons:
        pol.use_smooth = True
    return o


def _madeira_barco():
    mat = bpy.data.materials.new("madeira_barco")
    mat.use_nodes = True
    nt = mat.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.55
    coord = nt.nodes.new("ShaderNodeTexCoord")
    ondas = _no(nt, "ShaderNodeTexWave", Scale=3.0, Distortion=6.0, Detail=4.0)
    ondas.bands_direction = "Z"
    nt.links.new(coord.outputs["Object"], ondas.inputs["Vector"])
    tabuas = _no(nt, "ShaderNodeTexWave", Scale=9.0, Distortion=0.0)
    tabuas.bands_direction = "Z"
    tabuas.wave_profile = "SAW"
    nt.links.new(coord.outputs["Object"], tabuas.inputs["Vector"])
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (0.05, 0.025, 0.012, 1)
    rampa.color_ramp.elements[1].color = (0.2, 0.11, 0.055, 1)
    nt.links.new(ondas.outputs["Fac"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], p.inputs["Base Color"])
    b = _no(nt, "ShaderNodeBump", Strength=0.35)
    nt.links.new(tabuas.outputs["Fac"], b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    return mat


def _caixa(nome, loc, esc, mat, pai, col):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = nome
    o.scale = esc
    o.data.materials.append(mat)
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    o.parent = pai
    return o


def _barco(col, m):
    madeira = _madeira_barco()
    barco = bpy.data.objects.new("barco", None)
    col.objects.link(barco)
    casco = _casco(madeira)
    col.objects.link(casco)
    casco.parent = barco
    casco.location = (0, 0, -0.02)
    # assoalho (onde o Elias pisa: z = 0 do barco), bancos e mastro com a vela enrolada
    _caixa("assoalho", (0, 0, -0.03), (BOCA * 0.62, COMPRIMENTO * 0.68, 0.04), madeira, barco, col)
    for y in (-1.25, 1.15):
        _caixa("banco", (0, y, 0.24), (BOCA * 0.86, 0.24, 0.05), madeira, barco, col)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.05, depth=3.6, location=(0, 1.15, 1.8))
    mastro = bpy.context.object
    mastro.name = "mastro"
    mastro.data.materials.append(madeira)
    for c in mastro.users_collection:
        c.objects.unlink(mastro)
    col.objects.link(mastro)
    mastro.parent = barco
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.035, depth=2.6, location=(0, 1.15, 2.6),
                                        rotation=(0, math.radians(90), 0))
    verga = bpy.context.object
    verga.data.materials.append(madeira)
    for c in verga.users_collection:
        c.objects.unlink(verga)
    col.objects.link(verga)
    verga.parent = barco
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.09, depth=2.4, location=(0, 1.15, 2.5),
                                        rotation=(0, math.radians(90), 0))
    vela = bpy.context.object
    vela.name = "vela_enrolada"
    vela.data.materials.append(m["papel"])
    for c in vela.users_collection:
        c.objects.unlink(vela)
    col.objects.link(vela)
    vela.parent = barco
    # almofada na popa (onde Jesus dormia) e uma corda enrolada
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, -1.75, 0.34))
    alm = bpy.context.object
    alm.name = "almofada"
    alm.scale = (0.28, 0.17, 0.07)
    alm.data.materials.append(m["la"] if "la" in m else m["couro"])
    bpy.ops.object.shade_smooth()
    for c in alm.users_collection:
        c.objects.unlink(alm)
    col.objects.link(alm)
    alm.parent = barco
    bpy.ops.mesh.primitive_torus_add(major_radius=0.17, minor_radius=0.035, location=(0.42, 0.55, 0.03))
    corda = bpy.context.object
    corda.data.materials.append(m["papel"])
    for c in corda.users_collection:
        c.objects.unlink(corda)
    col.objects.link(corda)
    corda.parent = barco
    return barco


def _chuva(col):
    """Gotas como tracos finos instanciados por Geometry Nodes numa caixa em volta do barco; caem com o tempo."""
    ng = bpy.data.node_groups.new("chuva", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nt, L = ng.nodes, ng.links
    ent, sai = nt.new("NodeGroupInput"), nt.new("NodeGroupOutput")
    pts = nt.new("GeometryNodeDistributePointsOnFaces")
    # pontos num plano no alto; a altura de cada gota vem de um aleatorio + tempo (mod 9)
    plano = nt.new("GeometryNodeMeshGrid")
    plano.inputs["Size X"].default_value = 16
    plano.inputs["Size Y"].default_value = 16
    L.new(plano.outputs["Mesh"], pts.inputs["Mesh"])
    pts.inputs["Density"].default_value = 40
    # some com a densidade: seleciona so os pontos com aleatorio < Densidade
    alea = nt.new("FunctionNodeRandomValue")
    menor = nt.new("ShaderNodeMath")
    menor.operation = "LESS_THAN"
    L.new(alea.outputs[0], menor.inputs[0])
    dens = nt.new("ShaderNodeValue")
    dens.name = "densidade"  # animado: 1 na tempestade, 0 na calma
    dens.outputs[0].default_value = 1.0
    L.new(dens.outputs[0], menor.inputs[1])
    apaga = nt.new("GeometryNodeDeleteGeometry")
    nao = nt.new("FunctionNodeBooleanMath")
    nao.operation = "NOT"
    L.new(pts.outputs["Points"], apaga.inputs["Geometry"])
    L.new(menor.outputs[0], nao.inputs[0])
    L.new(nao.outputs[0], apaga.inputs["Selection"])
    # altura: (aleatorio*9 - tempo*9) mod 9
    alt = nt.new("FunctionNodeRandomValue")
    alt.inputs["Max"].default_value = 9.0
    alt.inputs["Seed"].default_value = 5
    tempo = nt.new("GeometryNodeInputSceneTime")
    vel = nt.new("ShaderNodeMath")
    vel.operation = "MULTIPLY"
    vel.inputs[1].default_value = 9.0
    L.new(tempo.outputs["Seconds"], vel.inputs[0])
    sub = nt.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    L.new(alt.outputs[0], sub.inputs[0])
    L.new(vel.outputs[0], sub.inputs[1])
    mod = nt.new("ShaderNodeMath")
    mod.operation = "FLOORED_MODULO"
    mod.inputs[1].default_value = 9.0
    L.new(sub.outputs[0], mod.inputs[0])
    comb = nt.new("ShaderNodeCombineXYZ")
    L.new(mod.outputs[0], comb.inputs[2])
    off = nt.new("GeometryNodeSetPosition")
    L.new(apaga.outputs[0], off.inputs["Geometry"])
    L.new(comb.outputs[0], off.inputs["Offset"])
    # o traco: cilindro fino e comprido, inclinado pelo vento
    gota = nt.new("GeometryNodeMeshCylinder")
    gota.inputs["Vertices"].default_value = 3
    gota.inputs["Radius"].default_value = 0.004
    gota.inputs["Depth"].default_value = 0.3
    inst = nt.new("GeometryNodeInstanceOnPoints")
    inst.inputs["Rotation"].default_value = (math.radians(14), math.radians(-8), 0)
    L.new(off.outputs[0], inst.inputs["Points"])
    L.new(gota.outputs["Mesh"], inst.inputs["Instance"])
    L.new(inst.outputs[0], sai.inputs[0])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -0.5))
    obj = bpy.context.object
    obj.name = "chuva"
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    gm = obj.modifiers.new("chuva", "NODES")
    gm.node_group = ng
    mat = bpy.data.materials.new("gota")
    mat.use_nodes = True
    nt2 = mat.node_tree
    out = nt2.nodes["Material Output"]
    nt2.nodes.remove(nt2.nodes["Principled BSDF"])
    tr = nt2.nodes.new("ShaderNodeBsdfTransparent")
    em = _no(nt2, "ShaderNodeEmission", Color=(0.7, 0.78, 0.9, 1), Strength=0.25)
    mix = _no(nt2, "ShaderNodeMixShader", Fac=0.22)
    nt2.links.new(tr.outputs[0], mix.inputs[1])
    nt2.links.new(em.outputs[0], mix.inputs[2])
    nt2.links.new(mix.outputs[0], out.inputs["Surface"])
    obj.data.materials.append(mat)
    obj.visible_shadow = False
    return obj, gm


def _ceu():
    """Fundo: gradiente pela altura da direcao de vista, nuvens por ruido; 'dia' mistura tempestade -> amanhecer."""
    w = bpy.data.worlds.new("ceu")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Generated"], sep.inputs[0])
    nuv = _no(nt, "ShaderNodeTexNoise", Scale=2.2, Detail=10.0, Roughness=0.62)
    nt.links.new(coord.outputs["Generated"], nuv.inputs["Vector"])

    meio = nt.nodes.new("ShaderNodeMath")
    meio.operation = "MULTIPLY_ADD"
    meio.inputs[1].default_value = 0.5
    meio.inputs[2].default_value = 0.5
    nt.links.new(sep.outputs["Z"], meio.inputs[0])

    def rampa(cores):
        r = nt.nodes.new("ShaderNodeValToRGB")
        el = r.color_ramp.elements
        el[0].position, el[0].color = cores[0]
        el[1].position, el[1].color = cores[-1]
        for pos, cor in cores[1:-1]:
            e = el.new(pos)
            e.color = cor
        nt.links.new(meio.outputs[0], r.inputs["Fac"])
        return r
    noite = rampa([(0.45, (0.01, 0.012, 0.016, 1)), (0.51, (0.06, 0.07, 0.09, 1)), (0.9, (0.015, 0.018, 0.026, 1))])
    aurora = rampa([(0.45, (0.1, 0.07, 0.06, 1)), (0.5, (1.0, 0.42, 0.14, 1)), (0.53, (0.75, 0.38, 0.2, 1)),
                    (0.62, (0.25, 0.22, 0.3, 1)), (0.95, (0.05, 0.08, 0.18, 1))])
    # nuvens escurecem o ceu da tempestade
    escuro = nt.nodes.new("ShaderNodeMix")
    escuro.data_type = "RGBA"
    escuro.blend_type = "MULTIPLY"
    nt.links.new(nuv.outputs["Fac"], escuro.inputs["Factor"])
    nt.links.new(noite.outputs["Color"], escuro.inputs[6])
    escuro.inputs[7].default_value = (0.35, 0.35, 0.4, 1)
    dia = nt.nodes.new("ShaderNodeMix")
    dia.data_type = "RGBA"
    dia.name = "dia"
    nt.links.new(escuro.outputs[2], dia.inputs[6])
    nt.links.new(aurora.outputs["Color"], dia.inputs[7])
    nt.links.new(dia.outputs[2], bg.inputs["Color"])
    bg.name = "fundo"
    bpy.context.scene.world = w
    return w


def _luz(nome, tipo, loc, energia, cor, col, tamanho=0.5, rot=(0, 0, 0)):
    d = bpy.data.lights.new(nome, tipo)
    d.energy, d.color = energia, cor
    if tipo == "AREA":
        d.size = tamanho
    elif tipo != "SUN":
        d.shadow_soft_size = tamanho
    else:
        d.angle = math.radians(tamanho)
    o = bpy.data.objects.new(nome, d)
    o.location, o.rotation_euler = loc, rot
    col.objects.link(o)
    return o


def _raio_visivel(col, rnd):
    """Um relampago desenhado no ceu: curva em zigue-zague com emissao (acesa so em alguns quadros)."""
    cu = bpy.data.curves.new("raio", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.12
    sp = cu.splines.new("POLY")
    pts = [(0.0, 0.0, 0.0)]
    x, z = 0.0, 0.0
    for _ in range(18):
        x += rnd.uniform(-1.6, 1.6)
        z -= rnd.uniform(1.0, 1.8)
        pts.append((x, 0.0, z))
    sp.points.add(len(pts) - 1)
    for p, (a, b, c) in zip(sp.points, pts):
        p.co = (a, b, c, 1)
    o = bpy.data.objects.new("raio", cu)
    o.location = (-14, 48, 26)
    col.objects.link(o)
    mat = bpy.data.materials.new("raio")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = _no(nt, "ShaderNodeEmission", Color=(0.75, 0.82, 1.0, 1), Strength=0.0)
    e.name = "brilho"
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    cu.materials.append(mat)
    o.visible_shadow = False
    return o, e


def criar(col, m):
    rnd = random.Random(11)
    _mar(col, _material_agua())
    _barco(col, m)
    _chuva(col)
    _ceu()
    _luz("relampago", "AREA", (-6, 18, 22), 0, (0.75, 0.82, 1.0), col, 14, (math.radians(-55), 0, 0))
    _luz("lua", "SUN", (0, 0, 10), 0.8, (0.5, 0.6, 0.85), col, 3, (math.radians(-62), 0, math.radians(200)))
    popa = _luz("luz_popa", "POINT", (0.3, -1.4, 0.7), 6, (1.0, 0.6, 0.3), col, 0.1)
    popa.parent = bpy.data.objects["barco"]
    _luz("preenche", "AREA", (0, -9, 4), 70, (0.4, 0.5, 0.7), col, 6, (math.radians(70), 0, 0))
    _luz("sol", "SUN", (0, 0, 10), 0, (1.0, 0.62, 0.35), col, 2, (math.radians(84), 0, math.radians(180)))
    _raio_visivel(col, rnd)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=6, location=(0, 120, 3))
    sol = bpy.context.object
    sol.name = "disco_sol"
    mat = bpy.data.materials.new("disco_sol")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = _no(nt, "ShaderNodeEmission", Color=(1.0, 0.42, 0.1, 1), Strength=0.0)
    e.name = "brilho"
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    sol.data.materials.append(mat)
    sol.visible_shadow = False
    for c in sol.users_collection:
        c.objects.unlink(sol)
    col.objects.link(sol)


def _quadros_calma(faixas, h):
    q0 = faixas[h["calma"] - 1][0]
    return q0, q0 + 60  # 2,5 s para o mar se acalmar


def raios(faixas, h):
    """Quadros de relampago: um logo no gancho e outros aleatorios ate o mar acalmar."""
    rnd = random.Random(21)
    c0, _ = _quadros_calma(faixas, h)
    fixos = [8] + [faixas[i][0] + 4 for i in h.get("raios_no_corte", [])]
    q = 40
    extra = []
    while q < c0 - 30:
        q += rnd.randint(55, 100)
        if q < c0 - 30:
            extra.append(q)
    return sorted(set(fixos + extra))


def _intensidade(f, c0, c1):
    if f <= c0:
        return 1.0
    if f >= c1:
        return 0.0
    u = (f - c0) / (c1 - c0)
    return 1 - u * u * (3 - 2 * u)


def animar(col, m, p, faixas, h):
    cena = bpy.context.scene
    fim = faixas[-1][1]
    c0, c1 = _quadros_calma(faixas, h)
    barco = bpy.data.objects["barco"]
    # Elias de pe no meio do barco, preso a ele (balanca junto).
    raiz = p["raiz"]
    raiz.parent = barco
    raiz.matrix_parent_inverse.identity()
    mar = bpy.data.objects["mar"]
    oc = mar.modifiers["ondas"]
    gm = bpy.data.objects["chuva"].modifiers["chuva"]
    for f in range(0, fim + 1, 2):
        k = _intensidade(f, c0, c1)
        t = f / 24
        # o mar: o tempo das ondas corre mais rapido na tempestade
        oc.time = t * (0.55 + 0.75 * k)
        oc.keyframe_insert("time", frame=f)
        oc.wave_scale = 0.12 + 1.5 * k
        oc.keyframe_insert("wave_scale", frame=f)
        oc.choppiness = 0.4 + 0.9 * k
        oc.keyframe_insert("choppiness", frame=f)
        # balanco do barco: soma de senos (arfagem, jogo e sobe-desce), quase parado na calmaria
        b = 0.06 + 0.94 * k
        barco.location = (0, 0, 0.3 * b * math.sin(t * 2.1) + 0.12 * b * math.sin(t * 3.7 + 1))
        barco.rotation_euler = (math.radians(9 * b * math.sin(t * 1.7 + 0.4)),
                                math.radians(11 * b * math.sin(t * 1.3) + 3 * b * math.sin(t * 4.1)),
                                math.radians(2 * b * math.sin(t * 0.6)))
        barco.keyframe_insert("location", frame=f)
        barco.keyframe_insert("rotation_euler", frame=f)
    # chuva: some junto com o vento
    for f, v in ((0, 1.0), (c0, 1.0), (c0 + 24, 0.0)):
        dv = gm.node_group.nodes["densidade"].outputs[0]
        dv.default_value = v
        dv.keyframe_insert("default_value", frame=f)
    # relampagos: luz forte, ceu claro e o raio desenhado por 2-3 quadros
    luz = bpy.data.objects["relampago"].data
    fundo = cena.world.node_tree.nodes["fundo"].inputs["Strength"]
    brilho = bpy.data.materials["raio"].node_tree.nodes["brilho"].inputs["Strength"]
    raio_obj = bpy.data.objects["raio"]
    rnd = random.Random(4)
    raio_obj.hide_render = True
    raio_obj.keyframe_insert("hide_render", frame=0)
    luz.energy = 0
    luz.keyframe_insert("energy", frame=0)
    fundo.default_value = 1.0
    fundo.keyframe_insert("default_value", frame=0)
    brilho.default_value = 0
    brilho.keyframe_insert("default_value", frame=0)
    for q in raios(faixas, h):
        forte = rnd.uniform(0.7, 1.0)
        for df, e in ((-1, 0), (0, 1.0), (1, 0.25), (2, 0.8), (4, 0.0)):
            luz.energy = 9000 * forte * e
            luz.keyframe_insert("energy", frame=q + df)
            fundo.default_value = 1 + 14 * forte * e
            fundo.keyframe_insert("default_value", frame=q + df)
            brilho.default_value = 60 * e
            brilho.keyframe_insert("default_value", frame=q + df)
        raio_obj.location = (rnd.uniform(-30, 30), rnd.uniform(40, 60), 26)
        raio_obj.rotation_euler = (0, 0, rnd.uniform(-0.4, 0.4))
        raio_obj.keyframe_insert("location", frame=q)
        raio_obj.keyframe_insert("rotation_euler", frame=q)
        for df, esc in ((-1, True), (0, False), (3, False), (4, True)):
            raio_obj.hide_render = esc
            raio_obj.keyframe_insert("hide_render", frame=q + df)
    # amanhecer: ceu, sol baixo e o disco do sol surgem depois da calma
    dia = cena.world.node_tree.nodes["dia"].inputs["Factor"]
    sol = bpy.data.objects["sol"].data
    disco = bpy.data.materials["disco_sol"].node_tree.nodes["brilho"].inputs["Strength"]
    lua = bpy.data.objects["lua"].data
    disco_obj = bpy.data.objects["disco_sol"]
    for f, esc in ((0, True), (c0 + 12, False)):
        disco_obj.hide_render = esc
        disco_obj.keyframe_insert("hide_render", frame=f)
    for f, d in ((0, 0.0), (c0 + 12, 0.0), (c0 + 110, 1.0), (fim, 1.0)):
        dia.default_value = d
        dia.keyframe_insert("default_value", frame=f)
        sol.energy = 3.2 * d
        sol.keyframe_insert("energy", frame=f)
        disco.default_value = 3 * d
        disco.keyframe_insert("default_value", frame=f)
        lua.energy = 0.8 * (1 - d) + 0.05 * d
        lua.keyframe_insert("energy", frame=f)
    # na calma o fundo volta ao normal e a luz do ceu do amanhecer conta mais
    fundo.default_value = 1.0
    fundo.keyframe_insert("default_value", frame=c0 + 12)
    fundo.default_value = 1.6
    fundo.keyframe_insert("default_value", frame=c0 + 110)


def _filtro(x, taxa, baixo=None, alto=None):
    """Passa-faixa por FFT (rapido para o audio inteiro de uma vez)."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / taxa)
    g = np.ones_like(f)
    if baixo:
        g *= 1 / (1 + (baixo / np.maximum(f, 1e-3)) ** 4)
    if alto:
        g *= 1 / (1 + (f / alto) ** 4)
    return np.fft.irfft(X * g, len(x))


def som(faixas, h, segundos, fps=24, taxa=44100):
    """Som da tempestade: chuva, vento e trovoes nos relampagos; corta na calma e fica so o mar batendo."""
    rng = np.random.default_rng(9)
    n = int(segundos * taxa)
    t = np.arange(n) / taxa
    c0 = _quadros_calma(faixas, h)[0] / fps
    env = np.clip(1 - (t - c0) / 1.0, 0, 1)
    chuva = _filtro(rng.standard_normal(n), taxa, 1500, 9000) * 0.25
    marrom = np.cumsum(rng.standard_normal(n))
    marrom = _filtro(marrom - np.convolve(marrom, np.ones(4410) / 4410, "same"), taxa, 40, 900)
    marrom /= np.max(np.abs(marrom)) + 1e-9
    rajada = 0.55 + 0.45 * np.sin(2 * np.pi * t / 5.3) * np.sin(2 * np.pi * t / 2.1 + 1)
    vento = marrom * rajada
    trovao = np.zeros(n)
    for q in raios(faixas, h):
        a = q / fps + rng.uniform(0.05, 0.35)
        dur = rng.uniform(2.2, 3.2)
        m = int(dur * taxa)
        u = np.arange(m) / taxa
        estalo = rng.standard_normal(m) * np.exp(-u * 18)
        ronco = np.cumsum(rng.standard_normal(m))
        ronco = ronco - np.convolve(ronco, np.ones(2205) / 2205, "same")
        ronco = ronco / (np.max(np.abs(ronco)) + 1e-9) * np.exp(-u * 1.4) * (1 - np.exp(-u * 30))
        i = int(a * taxa)
        if i >= n:
            continue
        k = min(n, i + m)
        trovao[i:k] += (0.5 * estalo + 1.2 * ronco)[: k - i]
    trovao = _filtro(trovao, taxa, 25, 1800)
    tempestade = (chuva + 0.6 * vento + trovao) * env
    # depois da calma: marolas suaves batendo no casco
    marola = _filtro(rng.standard_normal(n), taxa, 150, 1200) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 3.1)) ** 2
    calma = marola * 0.18 * np.clip((t - c0 - 0.6) / 1.5, 0, 1)
    out = tempestade + calma
    return out / (np.max(np.abs(out)) + 1e-9), c0
