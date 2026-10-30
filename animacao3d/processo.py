"""Objetos de video "processo": algo sendo construido na frente da camera, um passo por plano.

criar_livro_medieval monta, sobre a mesa do cenario, as 5 etapas de um manuscrito:
pergaminho esticado, tinta de galhas, pena de ganso, escrita e encadernacao.
Cada objeto entra no seu plano com um "pop" (cresce com um leve exagero) e algumas
etapas tem movimento proprio (o pergaminho se desenrola, o texto vai sendo escrito,
a capa desce sobre o miolo).
"""
import math

import bpy

MESA_Z = 0.81  # tampo da mesa do cenario


def _caixa(nome, loc, esc, mat, col):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = nome
    o.scale = esc
    o.data.materials.append(mat)
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def _chave(o, prop, valor, f):
    setattr(o, prop, valor)
    o.keyframe_insert(prop, frame=f)


def pop(o, f, escala_final=None):
    """Some ate o quadro f, depois cresce com exagero e assenta."""
    s = tuple(escala_final or o.scale)
    _chave(o, "scale", (0, 0, 0), 0)
    _chave(o, "scale", (0, 0, 0), f)
    _chave(o, "scale", tuple(v * 1.15 for v in s), f + 5)
    _chave(o, "scale", s, f + 9)


def sumir(o, f):
    s = tuple(o.scale)
    _chave(o, "scale", s, f)
    _chave(o, "scale", (0, 0, 0), f + 6)


def criar_livro_medieval(col, m, faixas):
    passos = faixas[1:6]  # planos 2 a 6 = passos 1 a 5
    bpy.data.objects["livro_aberto"].hide_render = True
    cx, cy, z = 1.55, -0.45, MESA_Z

    # Passo 1: bastidor de madeira e pergaminho que se desenrola da esquerda para a direita.
    f0, f1 = passos[0]
    barras = [_caixa("bastidor", (cx, cy + dy, z + 0.012), (0.54, 0.025, 0.025), m["madeira"], col) for dy in (-0.19, 0.19)]
    barras += [_caixa("bastidor", (cx + dx, cy, z + 0.012), (0.025, 0.4, 0.025), m["madeira"], col) for dx in (-0.26, 0.26)]
    for b in barras:
        pop(b, f0)
    perg = _caixa("pergaminho", (cx, cy, z + 0.016), (0.48, 0.34, 0.004), m["papel"], col)
    esq = cx - 0.24
    _chave(perg, "scale", (0, 0.34, 0.004), 0)
    _chave(perg, "location", (esq, cy, z + 0.016), 0)
    _chave(perg, "scale", (0, 0.34, 0.004), f0 + 8)
    _chave(perg, "location", (esq, cy, z + 0.016), f0 + 8)
    _chave(perg, "scale", (0.48, 0.34, 0.004), f0 + (f1 - f0) // 2)
    _chave(perg, "location", (cx, cy, z + 0.016), f0 + (f1 - f0) // 2)

    # Passo 2: tinteiro e galhas de carvalho.
    f0, _ = passos[1]
    bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=0.06, location=(1.97, -0.66, z + 0.03))
    tint = bpy.context.object
    tint.data.materials.append(m["olho"])
    pop(tint, f0)
    for i in range(6):
        a = i * 1.1
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.016, location=(2.07 + 0.04 * math.cos(a), -0.58 + 0.04 * math.sin(a), z + 0.016))
        g = bpy.context.object
        g.data.materials.append(m["couro"])
        bpy.ops.object.shade_smooth()
        pop(g, f0 + 3 * i)

    # Passo 3: pena de ganso que surge e desce ate o tinteiro.
    f0, f1 = passos[2]
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.004, radius2=0.03, depth=0.28)
    pena = bpy.context.object
    pena.data.materials.append(m["barba"])
    pena.scale = (1, 0.25, 1)
    bpy.ops.object.shade_smooth()
    pena.rotation_euler = (math.radians(35), 0, math.radians(-30))
    pop(pena, f0, (1, 0.25, 1))
    _chave(pena, "location", (1.95, -0.66, z + 0.30), f0)
    _chave(pena, "location", (1.97, -0.66, z + 0.17), f1 - 6)

    # Passo 4: o texto aparece sobre o pergaminho, como se fosse escrito.
    f0, f1 = passos[3]
    texto = _caixa("texto", (esq + 0.02, cy, z + 0.02), (0, 0.3, 0.001), m["pagina"], col)
    _chave(texto, "scale", (0, 0.3, 0.001), 0)
    _chave(texto, "scale", (0, 0.3, 0.001), f0)
    _chave(texto, "location", (esq + 0.02, cy, z + 0.02), f0)
    _chave(texto, "scale", (0.44, 0.3, 0.001), f1)
    _chave(texto, "location", (cx, cy, z + 0.02), f1)

    # Passo 5: bastidor e folhas somem, o miolo cresce e a capa de couro desce por cima.
    f0, f1 = passos[4]
    for o in barras + [perg, texto]:
        sumir(o, f0)
    miolo = _caixa("miolo", (cx, cy, z + 0.03), (0.3, 0.22, 0.05), m["papel"], col)
    pop(miolo, f0 + 4)
    tras = _caixa("capa_tras", (cx, cy, z + 0.004), (0.32, 0.24, 0.008), m["couro"], col)
    pop(tras, f0 + 2)
    capa = _caixa("capa", (cx, cy, z + 0.06), (0.32, 0.24, 0.01), m["couro"], col)
    pop(capa, f0 + 10)
    _chave(capa, "location", (cx, cy, z + 0.30), f0 + 10)
    _chave(capa, "location", (cx, cy, z + 0.06), f0 + (f1 - f0) // 2)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.006, location=(cx, cy, z + 0.066))
    fecho = bpy.context.object
    fecho.data.materials.append(m["latao"])
    pop(fecho, f0 + (f1 - f0) // 2 + 2)


def _raiz(nome, pontos, espessura, mat, col):
    """Curva com espessura que pode 'crescer' animando bevel_factor_end de 0 a 1."""
    c = bpy.data.curves.new(nome, "CURVE")
    c.dimensions = "3D"
    c.bevel_depth = espessura
    c.bevel_resolution = 2
    c.use_fill_caps = True
    s = c.splines.new("POLY")
    s.points.add(len(pontos) - 1)
    for p, xyz in zip(s.points, pontos):
        p.co = (*xyz, 1)
    s.use_smooth = True
    c.splines[0].order_u = 3
    o = bpy.data.objects.new(nome, c)
    o.data.materials.append(mat)
    col.objects.link(o)
    return o


def crescer(o, f0, f1, de=0.0, ate=1.0):
    o.data.bevel_factor_end = de
    o.data.keyframe_insert("bevel_factor_end", frame=0 if de == 0 else f0)
    o.data.keyframe_insert("bevel_factor_end", frame=f0)
    o.data.bevel_factor_end = ate
    o.data.keyframe_insert("bevel_factor_end", frame=f1)


def criar_semente(col, m, faixas):
    """Corte de terra sobre a mesa: em cima nada muda; embaixo a semente enfrenta escuro, peso,
    raizes e pressao ate a flor romper a superficie (planos 2 a 6)."""
    import random

    import materiais
    rnd = random.Random(7)
    passos = faixas[1:6]
    bpy.data.objects["livro_aberto"].hide_render = True
    terra = materiais.simples("terra", (0.075, 0.042, 0.022), 1.0, ruido=0.8, escala_ruido=90, bump=0.8)
    raiz = materiais.simples("raiz", (0.55, 0.45, 0.32), 0.6, sss=0.2)
    folha = materiais.simples("folha", (0.06, 0.25, 0.04), 0.5, sss=0.3)
    petala = materiais.simples("petala", (0.9, 0.62, 0.12), 0.45, sss=0.4)
    cx, cy, z = 1.6, -0.45, MESA_Z
    alt = 0.24
    topo = z + alt
    frente = cy - 0.077  # tudo o que cresce fica colado na face cortada da terra
    # Luz quente e suave so na face cortada, para o corte de terra ler bem no escuro da biblioteca.
    luz = bpy.data.lights.new("luz_corte", "AREA")
    luz.energy, luz.size, luz.color = 9, 0.5, (1.0, 0.8, 0.6)
    lo = bpy.data.objects.new("luz_corte", luz)
    lo.location = (cx - 0.25, cy - 0.75, z + 0.45)
    col.objects.link(lo)
    from mathutils import Vector
    lo.rotation_euler = (Vector((cx, frente, z + 0.12)) - lo.location).to_track_quat("-Z", "Y").to_euler()
    _caixa("terra", (cx, cy, z + alt / 2), (0.36, 0.14, alt), terra, col)
    for dx in (-0.19, 0.19):
        _caixa("caixa_lado", (cx + dx, cy, z + 0.14), (0.02, 0.16, 0.28), m["madeira"], col)
    _caixa("caixa_fundo", (cx, cy + 0.08, z + 0.14), (0.4, 0.02, 0.28), m["madeira"], col)
    _caixa("caixa_base", (cx, cy, z + 0.01), (0.4, 0.17, 0.02), m["madeira"], col)
    _caixa("moldura", (cx, cy - 0.08, z + 0.27), (0.4, 0.012, 0.012), m["madeira"], col)

    # Dia 1: a semente cai no escuro.
    f0, f1 = passos[0]
    sz = topo - 0.07
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(cx, frente, sz))
    sem = bpy.context.object
    sem.data.materials.append(materiais.simples("semente", (0.3, 0.14, 0.05), 0.35))
    bpy.ops.object.shade_smooth()
    pop(sem, f0 + 4, (0.02, 0.013, 0.013))
    _chave(sem, "location", (cx, frente, topo + 0.12), f0 + 4)
    _chave(sem, "location", (cx, frente, sz), f0 + 16)

    # Dia 12: o peso; a semente treme, racha e solta a primeira raiz.
    f0, f1 = passos[1]
    for k in range(0, 24, 3):
        sem.rotation_euler = (0, math.radians(8 if k % 2 else -8), 0)
        sem.keyframe_insert("rotation_euler", frame=f0 + k)
    sem.rotation_euler = (0, 0, 0)
    sem.keyframe_insert("rotation_euler", frame=f0 + 26)
    principal = [(cx + 0.003 * math.sin(i), frente, sz - 0.012 * i) for i in range(12)]
    r0 = _raiz("raiz_principal", principal, 0.003, raiz, col)
    crescer(r0, f0 + 10, f1, 0, 0.35)

    # Dia 30: em cima nada; embaixo as raizes se espalham.
    f0, f1 = passos[2]
    crescer(r0, f0, f1, 0.35, 1.0)
    for i in range(7):
        x, zz = cx, sz - 0.015 - 0.016 * i
        lado = -1 if i % 2 else 1
        pts = [(x, frente, zz)]
        for _ in range(7):
            x += lado * rnd.uniform(0.008, 0.02)
            zz -= rnd.uniform(0.002, 0.012)
            pts.append((x, frente, max(zz, z + 0.03)))
        r = _raiz(f"raiz_{i}", pts, 0.0016, raiz, col)
        crescer(r, f0 + 4 * i, f1 - 2)

    # Dia 60 e 90: o broto empurra a terra, rompe a superficie e vira flor.
    f0, f1 = passos[3]
    caule = [(cx + 0.012 * math.sin(i * 0.5), frente, sz + 0.015 * i) for i in range(24)]
    c = _raiz("caule", caule, 0.0035, folha, col)
    acima = (topo - sz) / (caule[-1][2] - sz)
    crescer(c, f0 + 6, f1, 0, acima + 0.04)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(cx, frente + 0.03, topo))
    monte = bpy.context.object
    monte.data.materials.append(terra)
    pop(monte, f0 + 10, (0.05, 0.05, 0.012))
    f0, f1 = passos[4]
    crescer(c, f0, f0 + (f1 - f0) // 2, acima + 0.04, 1.0)
    ponta = caule[-1]
    meio = f0 + (f1 - f0) // 2
    for i, (h, lado) in enumerate(((0.09, 1), (0.15, -1))):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(cx + lado * 0.035, frente + 0.01, topo + h))
        fo = bpy.context.object
        fo.data.materials.append(folha)
        bpy.ops.object.shade_smooth()
        fo.rotation_euler = (0, math.radians(-lado * 30), 0)
        pop(fo, f0 + 8 + 6 * i, (0.04, 0.012, 0.004))
    for i in range(6):
        a = i * math.pi / 3
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(ponta[0] + 0.028 * math.cos(a), frente,
                                                                 ponta[2] + 0.028 * math.sin(a)))
        pe = bpy.context.object
        pe.data.materials.append(petala)
        bpy.ops.object.shade_smooth()
        pe.rotation_euler = (0, -a, 0)
        pop(pe, meio + 2 * i, (0.028, 0.006, 0.012))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=(ponta[0], frente - 0.004, ponta[2]))
    miolo = bpy.context.object
    miolo.data.materials.append(m["couro"])
    pop(miolo, meio + 12)
