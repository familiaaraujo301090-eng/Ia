"""Mestre Elias em 3D, montado so com primitivas e modificadores (sem modelo externo).

Hierarquia (para animar por codigo):
    raiz      (pes no chao)      -> andar, girar o corpo
      cabeca  (base do pescoco)  -> virar e inclinar a cabeca
      bracos  (ombros)           -> erguer a lamparina
        luz   (chama)            -> tremular
Referencia visual: manto marrom de la com capuz, cinto de corda, barba branca longa,
botas de couro e lamparina de latao acesa nas duas maos.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector


def _obj(nome, mat, colecao):
    o = bpy.context.object
    o.name = nome
    if mat:
        o.data.materials.append(mat)
    for c in o.users_collection:
        c.objects.unlink(o)
    colecao.objects.link(o)
    bpy.ops.object.shade_smooth()
    return o


def _pai(filho, pai):
    filho.parent = pai
    filho.matrix_parent_inverse = pai.matrix_world.inverted()


def _vazio(nome, loc, colecao, pai=None):
    e = bpy.data.objects.new(nome, None)
    e.location = loc
    colecao.objects.link(e)
    bpy.context.view_layer.update()
    if pai:
        _pai(e, pai)
    return e


def _entre(nome, a, b, r_a, r_b, mat, colecao):
    """Cone de a ate b (mangas, cordas)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=r_a, radius2=r_b, depth=d.length,
                                    location=(a + b) / 2)
    o = _obj(nome, mat, colecao)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    return o


def _dobras(o, forca=0.025, escala=7.0, nivel=2):
    """Dobras verticais de tecido: subdivisao + deslocamento por ondas esticadas."""
    s = o.modifiers.new("sub", "SUBSURF")
    s.levels = s.render_levels = nivel
    t = bpy.data.textures.new(o.name + "_ondas", "WOOD")
    t.wood_type = "BANDNOISE"
    t.noise_basis_2 = "SIN"
    t.turbulence = 4
    t.noise_scale = 1.0 / escala
    d = o.modifiers.new("dobras", "DISPLACE")
    d.texture = t
    d.texture_coords = "LOCAL"
    d.strength = forca
    d.mid_level = 0.5


# ---------------------------------------------------------------------------
# Versao 2 (realista): cabeca esculpida por deformacoes, olhos com iris e palpebras,
# pele com subsurface e textura, barba/bigode/sobrancelhas de fios (particulas de cabelo).
# ---------------------------------------------------------------------------
CENTRO_CABECA = Vector((0, -0.05, 1.67))
ESCALA_CABECA = Vector((0.108, 0.12, 0.138))


def _g(p, c, s):
    d = p - Vector(c)
    if isinstance(s, (int, float)):
        return math.exp(-d.length_squared / (2 * s * s))
    return math.exp(-((d.x / s[0]) ** 2 + (d.y / s[1]) ** 2 + (d.z / s[2]) ** 2) / 2)


def _suave(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def _forma_rosto(p):
    """p na esfera unitaria (frente = -y). Devolve o ponto deformado, ainda em unidades da esfera."""
    n = p.normalized()
    d = 0.0
    for s in (1, -1):
        d -= 0.11 * _g(p, (0.36 * s, -0.86, 0.14), 0.15)      # orbitas
        d += 0.05 * _g(p, (0.36 * s, -0.86, 0.32), (0.2, 0.2, 0.08))  # arco da sobrancelha
        d += 0.06 * _g(p, (0.55 * s, -0.72, -0.12), 0.2)      # macas do rosto
        d -= 0.04 * _g(p, (0.86 * s, -0.4, 0.3), 0.2)         # temporas
        d += 0.07 * _g(p, (0.15 * s, -0.95, -0.27), 0.065)    # asas do nariz
        d += 0.12 * _g(p, (1.0 * s, 0.05, 0.0), (0.05, 0.12, 0.16))  # orelhas
    d -= 0.035 * _g(p, (0, -0.95, -0.48), (0.22, 0.2, 0.05))  # boca
    d += 0.05 * _g(p, (0, -0.85, -0.8), 0.15)                 # queixo
    q = p + n * d
    # Nariz: crista no meio do rosto, mais alta na ponta.
    if p.y < -0.5:
        perfil = (0.04 * _suave(0.32, 0.1, p.z) + 0.11 * _suave(0.1, -0.12, p.z)) * _suave(-0.42, -0.2, p.z)
        largura = 0.075 + 0.05 * _suave(0.0, -0.3, p.z)
        q.y -= 2.6 * perfil * math.exp(-(p.x / largura) ** 2) * _suave(-0.5, -0.85, p.y)
        q.y -= 0.09 * _g(p, (0, -0.97, -0.22), 0.07)         # ponta do nariz
    # Mandibula mais estreita embaixo.
    q.x *= 1 - 0.22 * _suave(-0.25, -1.0, p.z)
    return q


def _pele_material(nome, com_cor):
    """Pele: subsurface, poros e rugas finas na testa; cor por vertice (bochechas e nariz mais rosados)."""
    m = bpy.data.materials.get(nome)
    if m:
        return m
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.42, 0.25, 0.17, 1)
    if com_cor:
        ca = nt.nodes.new("ShaderNodeVertexColor")
        ca.layer_name = "cor_pele"
        nt.links.new(ca.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.5
    p.inputs["Subsurface Weight"].default_value = 0.3
    p.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    p.inputs["Subsurface Scale"].default_value = 0.015
    p.inputs["Specular IOR Level"].default_value = 0.4
    tc = nt.nodes.new("ShaderNodeTexCoord")
    poro = nt.nodes.new("ShaderNodeTexNoise")
    poro.inputs["Scale"].default_value = 900
    poro.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], poro.inputs["Vector"])
    ruga = nt.nodes.new("ShaderNodeTexWave")
    ruga.bands_direction = "Z"
    ruga.inputs["Scale"].default_value = 18
    ruga.inputs["Distortion"].default_value = 3
    nt.links.new(tc.outputs["Object"], ruga.inputs["Vector"])
    soma = nt.nodes.new("ShaderNodeMath")
    soma.operation = "MULTIPLY_ADD"
    soma.inputs[1].default_value = 0.35
    nt.links.new(ruga.outputs["Fac"], soma.inputs[0])
    nt.links.new(poro.outputs["Fac"], soma.inputs[2])
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = 0.12
    b.inputs["Distance"].default_value = 0.002
    nt.links.new(soma.outputs[0], b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    return m


def _olho_material():
    m = bpy.data.materials.get("olho_real")
    if m:
        return m
    m = bpy.data.materials.new("olho_real")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.06
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    junta = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], junta.inputs["X"])
    nt.links.new(sep.outputs["Z"], junta.inputs["Y"])
    raio = nt.nodes.new("ShaderNodeVectorMath")
    raio.operation = "LENGTH"
    nt.links.new(junta.outputs[0], raio.inputs[0])
    # Raio no plano da frente, normalizado pelo raio do globo (0.016): pupila, iris e esclera.
    norm = nt.nodes.new("ShaderNodeMath")
    norm.operation = "DIVIDE"
    norm.inputs[1].default_value = 0.016
    nt.links.new(raio.outputs["Value"], norm.inputs[0])
    frente = nt.nodes.new("ShaderNodeMath")
    frente.operation = "LESS_THAN"
    frente.inputs[1].default_value = 0.0
    nt.links.new(sep.outputs["Y"], frente.inputs[0])
    mapa = nt.nodes.new("ShaderNodeMath")
    mapa.operation = "MAXIMUM"
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(frente.outputs[0], inv.inputs[1])
    nt.links.new(norm.outputs[0], mapa.inputs[0])
    nt.links.new(inv.outputs[0], mapa.inputs[1])
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    el = rampa.color_ramp.elements
    el[0].position, el[0].color = 0.0, (0.01, 0.008, 0.006, 1)
    el[1].position, el[1].color = 0.62, (0.85, 0.82, 0.78, 1)
    for pos, cor in ((0.2, (0.01, 0.008, 0.006, 1)), (0.24, (0.18, 0.1, 0.04, 1)), (0.5, (0.07, 0.04, 0.02, 1)),
                     (0.56, (0.85, 0.82, 0.78, 1))):
        e = el.new(pos)
        e.color = cor
    nt.links.new(mapa.outputs[0], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], p.inputs["Base Color"])
    return m


def _cabelo_material():
    m = bpy.data.materials.get("fios_brancos")
    if m:
        return m
    m = bpy.data.materials.new("fios_brancos")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    h = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    h.parametrization = "MELANIN"
    h.inputs["Melanin"].default_value = 0.03
    h.inputs["Melanin Redness"].default_value = 0.15
    h.inputs["Roughness"].default_value = 0.4
    h.inputs["Radial Roughness"].default_value = 0.5
    nt.links.new(h.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def _fios(o, nome, grupo, quantos, comprimento, direcao, normal, filhos=10, aglomerar=0.5, grupo_comp=None):
    mod = o.modifiers.new(nome, "PARTICLE_SYSTEM")
    ps = mod.particle_system
    ps.vertex_group_density = grupo
    if grupo_comp:
        ps.vertex_group_length = grupo_comp
    s = ps.settings
    s.name = nome
    s.type = "HAIR"
    s.use_advanced_hair = True
    s.count = quantos
    s.emit_from = "FACE"
    s.use_emit_random = True
    # No modo avancado o comprimento sai da "velocidade" (~4 unidades por unidade de velocidade).
    v = Vector(direcao) + Vector((0, 0, 0))
    k = comprimento / (7.4 * max((v.length ** 2 + normal ** 2) ** 0.5, 1e-6))
    s.normal_factor = normal * k
    s.object_align_factor = tuple(c * k for c in direcao)
    s.child_type = "INTERPOLATED"
    s.child_percent = filhos
    s.rendered_child_count = filhos
    s.clump_factor = aglomerar
    s.roughness_1 = 0.003
    s.roughness_endpoint = 0.004
    s.kink = "WAVE"
    s.kink_amplitude = 0.003
    s.kink_frequency = 3
    s.root_radius = 1.0
    s.tip_radius = 0.2
    s.radius_scale = 0.0011
    s.display_step = s.render_step = 4
    s.material_slot = "fios_brancos"
    s.hair_length = comprimento  # depois das velocidades: no modo avancado ele reescala a direcao
    return ps


def cabeca_realista(colecao, m):
    """Devolve as pecas da cabeca V2 (todas para serem filhas do vazio da cabeca)."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1, location=(0, 0, 0))
    rosto = _obj("rosto", None, colecao)
    me = rosto.data
    cores = me.color_attributes.new("cor_pele", "FLOAT_COLOR", "POINT")
    barba_g = rosto.vertex_groups.new(name="barba")
    bigode_g = rosto.vertex_groups.new(name="bigode")
    sob_g = rosto.vertex_groups.new(name="sobrancelha")
    comp_g = rosto.vertex_groups.new(name="comprimento")
    for v in me.vertices:
        p = v.co.copy()
        q = _forma_rosto(p)
        v.co = Vector((q.x * ESCALA_CABECA.x, q.y * ESCALA_CABECA.y, q.z * ESCALA_CABECA.z))
        # Cor: base, nariz e bochechas avermelhados, olheiras levemente escuras.
        verm = max(_g(p, (0, -0.97, -0.15), 0.13), max(_g(p, (s * 0.5, -0.8, -0.2), 0.16) for s in (1, -1)))
        olheira = max(_g(p, (s * 0.36, -0.88, 0.0), 0.08) for s in (1, -1))
        cor = Vector((0.4, 0.24, 0.16)).lerp(Vector((0.52, 0.21, 0.15)), 0.7 * verm) * (1 - 0.25 * olheira)
        cores.data[v.index].color = (*cor, 1)
        frente = p.y < 0.2
        if frente and p.z < -0.2 and abs(p.x) < 0.8 and not (abs(p.x) < 0.3 and p.z > -0.55 and p.y < -0.8):
            w = _suave(-0.2, -0.45, p.z)
            barba_g.add([v.index], w, "REPLACE")
            comp_g.add([v.index], 0.3 + 0.7 * (1 - abs(p.x) / 0.8) ** 1.5, "REPLACE")
        if p.y < -0.7 and -0.46 < p.z < -0.3 and abs(p.x) < 0.42:
            bigode_g.add([v.index], 1.0, "REPLACE")
        for s in (1, -1):
            if _g(p, (0.36 * s, -0.86, 0.33), (0.17, 0.3, 0.05)) > 0.5:
                sob_g.add([v.index], 1.0, "REPLACE")
    rosto.location = CENTRO_CABECA
    me.materials.append(_pele_material("pele_rosto", True))
    me.materials.append(_cabelo_material())
    sub = rosto.modifiers.new("sub", "SUBSURF")
    sub.levels, sub.render_levels = 0, 1
    _fios(rosto, "barba", "barba", 2200, 0.26, (0, -0.15, -1.0), 0.1, 10, 0.6, "comprimento")
    _fios(rosto, "bigode", "bigode", 500, 0.075, (0, -0.4, -1.0), 0.6, 8, 0.6)
    _fios(rosto, "sobrancelha", "sobrancelha", 260, 0.022, (0, -0.6, 0.35), 0.4, 6, 0.3)
    pecas = [rosto]
    # Volume interno da barba (evita ver atraves dos fios).
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.025, radius2=0.085, depth=0.3,
                                    location=(0, -0.12, 1.43), rotation=(0.14, 0, 0))
    miolo = _obj("barba_miolo", m["barba"], colecao)
    miolo.scale = (1.0, 0.7, 1.0)
    pecas.append(miolo)
    # Olhos e palpebras.
    olho_m = _olho_material()
    pele_l = _pele_material("pele_lisa", False)
    for s in (1, -1):
        alvo = _forma_rosto(Vector((0.36 * s, -0.86, 0.14)).normalized())
        c = Vector((alvo.x * ESCALA_CABECA.x, alvo.y * ESCALA_CABECA.y, alvo.z * ESCALA_CABECA.z)) + CENTRO_CABECA
        c.y += 0.009
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.016, location=c)
        pecas.append(_obj("olho", olho_m, colecao))
        for nome, corte, inclina in (("palpebra_sup", 0.78, -0.25), ("palpebra_inf", -0.78, 0.2)):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.0172, location=c)
            pal = _obj(nome, pele_l, colecao)
            bm = bmesh.new()
            bm.from_mesh(pal.data)
            if corte > 0:
                fora = [v for v in bm.verts if v.co.z + inclina * v.co.y < 0.0172 * (corte - 0.5)]
            else:
                fora = [v for v in bm.verts if v.co.z + inclina * v.co.y > 0.0172 * (corte + 0.15)]
            bmesh.ops.delete(bm, geom=fora, context="VERTS")
            bm.to_mesh(pal.data)
            bm.free()
            pecas.append(pal)
    return pecas


def _la_material():
    m = bpy.data.materials.get("la_tecida")
    if m:
        return m
    m = bpy.data.materials.new("la_tecida")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.92
    p.inputs["Sheen Weight"].default_value = 0.3
    p.inputs["Sheen Tint"].default_value = (0.6, 0.4, 0.25, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    var = nt.nodes.new("ShaderNodeTexNoise")
    var.inputs["Scale"].default_value = 6
    nt.links.new(tc.outputs["Object"], var.inputs["Vector"])
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (0.04, 0.02, 0.011, 1)
    rampa.color_ramp.elements[1].color = (0.085, 0.045, 0.025, 1)
    nt.links.new(var.outputs["Fac"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], p.inputs["Base Color"])
    trama = nt.nodes.new("ShaderNodeTexWave")
    trama.wave_type = "BANDS"
    trama.bands_direction = "DIAGONAL"
    trama.inputs["Scale"].default_value = 260
    trama.inputs["Distortion"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], trama.inputs["Vector"])
    fio = nt.nodes.new("ShaderNodeTexNoise")
    fio.inputs["Scale"].default_value = 500
    nt.links.new(tc.outputs["Object"], fio.inputs["Vector"])
    soma = nt.nodes.new("ShaderNodeMath")
    soma.operation = "ADD"
    nt.links.new(trama.outputs["Fac"], soma.inputs[0])
    nt.links.new(fio.outputs["Fac"], soma.inputs[1])
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = 0.35
    nt.links.new(soma.outputs[0], b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    return m


def maos_realistas(colecao, s):
    """Mao segurando a lamparina por baixo: palma + 4 dedos curvados + polegar por cima."""
    pele = _pele_material("pele_lisa", False)
    pecas = []
    palma = Vector((0.07 * s, -0.33, 1.125))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=palma)
    o = _obj("palma", pele, colecao)
    o.scale = (0.03, 0.045, 0.02)
    pecas.append(o)
    for i in range(4):
        y = -0.355 + 0.016 * i
        a = palma + Vector((-0.01 * s, y + 0.33, -0.005))
        b = Vector((0.02 * s, y, 1.112))
        c = Vector((-0.005 * s, y - 0.002, 1.13))
        for ini, fim in ((a, b), (b, c)):
            pecas.append(_entre("dedo", ini, fim, 0.0085, 0.0075, pele, colecao))
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0078, location=fim)
            pecas.append(_obj("junta", pele, colecao))
    t0 = palma + Vector((-0.01 * s, -0.03, 0.01))
    t1 = Vector((0.035 * s, -0.4, 1.165))
    pecas.append(_entre("polegar", t0, t1, 0.01, 0.009, pele, colecao))
    return pecas


def criar(colecao, mats, local=(0, 0, 0), realista=True):
    m = dict(mats)
    if realista:
        m["la"] = _la_material()
    raiz = _vazio("elias_raiz", (0, 0, 0), colecao)

    # Manto: cone largo embaixo, estreito nos ombros, com dobras.
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=0.38, radius2=0.19, depth=1.42, location=(0, 0, 0.81),
                                    end_fill_type="NOTHING")
    manto = _obj("manto", m["la"], colecao)
    _dobras(manto, 0.03, 9)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1, location=(0, 0.0, 1.45))
    ombros = _obj("ombros", m["la"], colecao)
    ombros.scale = (0.29, 0.17, 0.14)
    # Cinto de corda e pontas penduradas.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.27, minor_radius=0.016, location=(0, 0, 1.0))
    cinto = _obj("cinto", m["corda"], colecao)
    pontas = [_entre(f"corda{i}", (0.06 * s, -0.27, 1.0), (0.08 * s, -0.29, 0.62 + 0.06 * i), 0.012, 0.012,
                     m["corda"], colecao) for i, s in enumerate((1, -1))]
    botas = []
    for s in (1, -1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0.1 * s, -0.1, 0.06))
        b = _obj("bota", m["couro"], colecao)
        b.scale = (0.075, 0.14, 0.065)
        botas.append(b)
    for o in (manto, ombros, cinto, *pontas, *botas):
        _pai(o, raiz)

    # Cabeca: rosto, olhos, nariz, bigode, barba longa e capuz aberto na frente.
    cab = _vazio("elias_cabeca", (0, 0, 1.55), colecao, raiz)
    pecas = []
    if realista:
        pecas += cabeca_realista(colecao, m)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, -0.05, 1.67))
        rosto = _obj("rosto", m["pele"], colecao)
        rosto.scale = (0.9, 1.0, 1.15)
        pecas.append(rosto)
        for s in (1, -1):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.013, location=(0.04 * s, -0.158, 1.69))
            pecas.append(_obj("olho", m["olho"], colecao))
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0.045 * s, -0.152, 1.717))
            so = _obj("sobrancelha", m["barba"], colecao)
            so.scale = (0.026, 0.01, 0.007)
            pecas.append(so)
        bpy.ops.mesh.primitive_cone_add(radius1=0.022, radius2=0.005, depth=0.055, location=(0, -0.18, 1.66),
                                        rotation=(math.pi / 2, 0, 0))
        pecas.append(_obj("nariz", m["pele"], colecao))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, -0.165, 1.625))
        big = _obj("bigode", m["barba"], colecao)
        big.scale = (0.072, 0.026, 0.021)
        pecas.append(big)
        bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=0.04, radius2=0.115, depth=0.42, location=(0, -0.14, 1.39),
                                        rotation=(0.12, 0, 0))
        barba = _obj("barba", m["barba"], colecao)
        _dobras(barba, 0.012, 40)
        pecas.append(barba)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.2, location=(0, -0.02, 1.69))
    capuz = _obj("capuz", m["la"], colecao)
    bm = bmesh.new()
    bm.from_mesh(capuz.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.y < -0.075 and v.co.z > -0.15], context="VERTS")
    bm.to_mesh(capuz.data)
    bm.free()
    capuz.scale = (1.0, 1.05, 1.12)
    sol = capuz.modifiers.new("espessura", "SOLIDIFY")
    sol.thickness = 0.018
    _dobras(capuz, 0.01, 12)
    pecas.append(capuz)
    for o in pecas:
        _pai(o, cab)
    if realista:
        # Luz suave no rosto: sem ela, so a chama de baixo ilumina e o rosto some no escuro.
        lr = bpy.data.lights.new("luz_rosto", "AREA")
        lr.energy, lr.size, lr.color = 2.2, 0.5, (1.0, 0.85, 0.7)
        lro = bpy.data.objects.new("luz_rosto", lr)
        lro.location = (-0.3, -0.75, 1.95)
        colecao.objects.link(lro)
        lro.rotation_euler = (CENTRO_CABECA - lro.location).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        _pai(lro, cab)

    # Bracos: mangas largas ate as maos, que seguram a lamparina na altura do peito.
    bracos = _vazio("elias_bracos", (0, 0, 1.42), colecao, raiz)
    pb = []
    for s in (1, -1):
        manga = _entre("manga", (0.25 * s, 0.0, 1.42), (0.11 * s, -0.27, 1.14), 0.08, 0.1, m["la"], colecao)
        _dobras(manga, 0.008, 15, 1)
        pb.append(manga)
        if realista:
            pb += maos_realistas(colecao, s)
            continue
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0.065 * s, -0.33, 1.13))
        mao = _obj("mao", m["pele"], colecao)
        mao.scale = (0.042, 0.06, 0.032)
        pb.append(mao)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.07, location=(0, -0.37, 1.17))
    corpo_l = _obj("lamparina", m["latao"], colecao)
    corpo_l.scale = (1.0, 0.85, 0.45)
    pb.append(corpo_l)
    pb.append(_entre("bico", (0.04, -0.37, 1.18), (0.135, -0.37, 1.205), 0.022, 0.009, m["latao"], colecao))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.007, location=(-0.08, -0.37, 1.18),
                                     rotation=(math.pi / 2, 0, 0))
    pb.append(_obj("alca", m["latao"], colecao))
    bpy.ops.mesh.primitive_cone_add(radius1=0.025, radius2=0.004, depth=0.03, location=(0, -0.37, 1.215))
    pb.append(_obj("tampa", m["latao"], colecao))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0.137, -0.37, 1.235))
    chama = _obj("chama", m["chama"], colecao)
    chama.scale = (0.011, 0.011, 0.03)
    pb.append(chama)
    for o in pb:
        _pai(o, bracos)
    luz_d = bpy.data.lights.new("luz_lamparina", "POINT")
    luz_d.energy = 14
    luz_d.color = (1.0, 0.58, 0.25)
    luz_d.shadow_soft_size = 0.02
    luz = bpy.data.objects.new("luz_lamparina", luz_d)
    luz.location = (0.137, -0.38, 1.26)
    colecao.objects.link(luz)
    bpy.context.view_layer.update()
    _pai(luz, bracos)

    raiz.location = local
    return {"raiz": raiz, "cabeca": cab, "bracos": bracos, "luz": luz, "chama": chama}


def tremular(partes, inicio, fim, semente=7):
    """Chama viva: energia e altura da chama mudam a cada 2 quadros."""
    rnd = random.Random(semente)
    luz, chama = partes["luz"], partes["chama"]
    for f in range(inicio, fim + 1, 2):
        k = rnd.uniform(0.75, 1.2)
        luz.data.energy = 14 * k
        luz.data.keyframe_insert("energy", frame=f)
        chama.scale = (0.011, 0.011, 0.03 * (0.85 + 0.3 * k))
        chama.keyframe_insert("scale", frame=f)
