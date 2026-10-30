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


def criar(colecao, mats, local=(0, 0, 0)):
    m = mats
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

    # Bracos: mangas largas ate as maos, que seguram a lamparina na altura do peito.
    bracos = _vazio("elias_bracos", (0, 0, 1.42), colecao, raiz)
    pb = []
    for s in (1, -1):
        pb.append(_entre("manga", (0.25 * s, 0.0, 1.42), (0.11 * s, -0.27, 1.14), 0.08, 0.1, m["la"], colecao))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0.065 * s, -0.33, 1.13))
        mao = _obj("mao", m["pele"], colecao)
        mao.scale = (0.042, 0.06, 0.032)
        pb.append(mao)
    _dobras(pb[0], 0.008, 15, 1)
    _dobras(pb[2], 0.008, 15, 1)
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
