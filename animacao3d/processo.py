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


# ---------------------------------------------------------------------------
# Jornadas de transformacao: um objeto na mesa enfrenta 5 etapas ate o resultado.
# ---------------------------------------------------------------------------
CX, CY = 1.6, -0.45


def _preparar(col, energia=9):
    """Esconde o livro aberto da mesa e poe uma luz suave na frente do objeto."""
    from mathutils import Vector
    bpy.data.objects["livro_aberto"].hide_render = True
    luz = bpy.data.lights.new("luz_objeto", "AREA")
    luz.energy, luz.size, luz.color = energia, 0.6, (1.0, 0.82, 0.65)
    o = bpy.data.objects.new("luz_objeto", luz)
    o.location = (CX - 0.3, CY - 0.8, MESA_Z + 0.5)
    col.objects.link(o)
    o.rotation_euler = (Vector((CX, CY, MESA_Z + 0.12)) - o.location).to_track_quat("-Z", "Y").to_euler()


def _no(mat):
    return mat.node_tree.nodes["Principled BSDF"].inputs


def _valor(entrada, valor, f):
    entrada.default_value = valor
    entrada.keyframe_insert("default_value", frame=f)


def _energia(luz, valor, f):
    luz.data.energy = valor
    luz.data.keyframe_insert("energy", frame=f)


def _ponto(nome, loc, cor, col):
    d = bpy.data.lights.new(nome, "POINT")
    d.color, d.shadow_soft_size = cor, 0.05
    o = bpy.data.objects.new(nome, d)
    o.location = loc
    col.objects.link(o)
    _energia(o, 0, 0)
    return o


def _vidro(nome, ior):
    import materiais
    mat = materiais.simples(nome, (0.95, 0.97, 1.0), 0.02)
    _no(mat)["Transmission Weight"].default_value = 1.0
    _no(mat)["IOR"].default_value = ior
    return mat


def _ouro():
    import materiais
    return materiais.simples("ouro", (1.0, 0.7, 0.25), 0.22, metal=1.0)


def _fatia_vaso(nome, a0, a1, perfil, mat, col, segs=5):
    import bmesh
    bm = bmesh.new()
    grade = []
    for j in range(segs + 1):
        a = a0 + (a1 - a0) * j / segs
        grade.append([bm.verts.new((r * math.cos(a), r * math.sin(a), h)) for r, h in perfil])
    for j in range(segs):
        for i in range(len(perfil) - 1):
            bm.faces.new((grade[j][i], grade[j + 1][i], grade[j + 1][i + 1], grade[j][i + 1]))
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(nome, me)
    col.objects.link(o)
    o.modifiers.new("espessura", "SOLIDIFY").thickness = 0.006
    return o


def criar_kintsugi(col, m, faixas):
    """Vaso que cai, vira cacos, e colado e tem as rachaduras preenchidas com ouro."""
    import random

    import materiais
    rnd = random.Random(11)
    _preparar(col)
    p = faixas[1:6]
    z = MESA_Z
    ceramica = materiais.simples("ceramica", (0.05, 0.1, 0.22), 0.3)
    ouro = _ouro()
    perfil = [(0.001, 0), (0.05, 0), (0.085, 0.04), (0.1, 0.11), (0.08, 0.18), (0.045, 0.23), (0.05, 0.26),
              (0.06, 0.27)]
    vaso = bpy.data.objects.new("vaso", None)
    col.objects.link(vaso)
    vaso.location = (CX, CY, z)
    n = 6
    cacos = []
    for k in range(n):
        o = _fatia_vaso(f"caco{k}", k * 2 * math.pi / n, (k + 1) * 2 * math.pi / n, perfil, ceramica, col)
        o.parent = vaso
        cacos.append(o)
    # Etapa 1: o vaso aparece inteiro e se parte.
    f0, f1 = p[0]
    pop(vaso, f0, (1, 1, 1))
    queda = f0 + int((f1 - f0) * 0.55)
    for k, o in enumerate(cacos):
        a = (k + 0.5) * 2 * math.pi / n
        _chave(o, "location", (0, 0, 0), queda)
        _chave(o, "rotation_euler", (0, 0, 0), queda)
        fora = (0.14 * math.cos(a), 0.14 * math.sin(a), 0)
        giro = (rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), rnd.uniform(-0.6, 0.6))
        _chave(o, "location", fora, queda + 6)
        _chave(o, "rotation_euler", giro, queda + 6)
        # Etapa 3: cada caco volta ao lugar, um por um.
        g0, g1 = p[2]
        volta = g0 + k * (g1 - g0 - 12) // n
        _chave(o, "location", fora, volta)
        _chave(o, "rotation_euler", giro, volta)
        _chave(o, "location", (0, 0, 0), volta + 10)
        _chave(o, "rotation_euler", (0, 0, 0), volta + 10)
    # Etapa 4: as rachaduras viram ouro.
    f0, f1 = p[3]
    for k in range(n):
        a = k * 2 * math.pi / n
        pts = [((r + 0.004) * math.cos(a), (r + 0.004) * math.sin(a), h) for r, h in perfil[1:]]
        c = _raiz(f"emenda{k}", pts, 0.0035, ouro, col)
        c.parent = vaso
        crescer(c, f0 + 4 * k, f0 + 4 * k + (f1 - f0) // 2)
    # Etapa 5: o vaso gira, mais bonito que antes.
    f0, f1 = p[4]
    _chave(vaso, "rotation_euler", (0, 0, 0), f0)
    _chave(vaso, "rotation_euler", (0, 0, 2 * math.pi), f1 + 120)


def criar_ouro_fogo(col, m, faixas):
    """Cadinho no fogo: minerio, fogo, impurezas subindo, ourives retirando, ouro espelhado."""
    import random

    import materiais
    rnd = random.Random(5)
    _preparar(col, 6)
    p = faixas[1:6]
    z = MESA_Z
    pedra = materiais.simples("fornalha", (0.16, 0.15, 0.14), 0.95, bump=0.6)
    cadinho_m = materiais.simples("cadinho", (0.1, 0.085, 0.075), 0.9, bump=0.5)
    minerio = materiais.simples("minerio", (0.3, 0.24, 0.13), 0.7, metal=0.3, bump=0.6)
    escoria = materiais.simples("escoria", (0.03, 0.025, 0.02), 1.0, bump=0.8)
    liquido = materiais.simples("ouro_liquido", (1.0, 0.72, 0.25), 0.4, metal=1.0)
    _no(liquido)["Emission Color"].default_value = (1.0, 0.42, 0.08, 1)
    fogo = materiais.emissao("fogo", (1.0, 0.3, 0.04), 2.5)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.14, depth=0.06, location=(CX, CY, z + 0.03))
    bpy.context.object.data.materials.append(pedra)
    topo = z + 0.06 + 0.13
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.09, depth=0.13, location=(CX, CY, z + 0.06 + 0.065))
    cad = bpy.context.object
    cad.data.materials.append(cadinho_m)
    bpy.ops.object.shade_smooth()
    luz = _ponto("luz_fogo", (CX, CY - 0.17, z + 0.12), (1.0, 0.5, 0.15), col)

    # Etapa 1: as pedras de minerio caem no cadinho.
    f0, f1 = p[0]
    pedras = []
    for i in range(5):
        a = i * 2 * math.pi / 5
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.028,
                                              location=(CX + 0.04 * math.cos(a), CY + 0.04 * math.sin(a), topo + 0.01))
        o = bpy.context.object
        o.data.materials.append(minerio)
        o.rotation_euler = (rnd.random(), rnd.random(), rnd.random())
        loc = tuple(o.location)
        _chave(o, "location", (loc[0], loc[1], loc[2] + 0.35), 0)
        _chave(o, "location", (loc[0], loc[1], loc[2] + 0.35), f0 + 4 * i)
        _chave(o, "location", loc, f0 + 4 * i + 8)
        pedras.append(o)
    # Etapa 2: o fogo acende e cresce.
    f0, f1 = p[1]
    chamas = []
    for i in range(10):
        a = i * 2 * math.pi / 10
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.022, radius2=0.0, depth=0.09,
                                        location=(CX + 0.12 * math.cos(a), CY + 0.12 * math.sin(a), z + 0.1))
        o = bpy.context.object
        o.data.materials.append(fogo)
        pop(o, f0 + 2 * i, (1, 1, 1))
        fim = p[4][0] + 20
        for f in range(f0 + 2 * i + 10, fim, 3):
            _chave(o, "scale", (1, 1, rnd.uniform(0.7, 1.4)), f)
        _chave(o, "scale", (1, 1, 1), fim)
        _chave(o, "scale", (0, 0, 0), fim + 10)
        chamas.append(o)
    _energia(luz, 0, f0)
    _energia(luz, 8, f0 + 30)
    # Etapa 3: o minerio derrete e a impureza sobe.
    f0, f1 = p[2]
    for i, o in enumerate(pedras):
        _chave(o, "scale", (1, 1, 1), f0 + 3 * i)
        _chave(o, "scale", (0, 0, 0), f0 + 3 * i + 25)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.08, depth=0.01, location=(CX, CY, topo + 0.001))
    liq = bpy.context.object
    liq.data.materials.append(liquido)
    pop(liq, f0 + 6, (1, 1, 1))
    _valor(_no(liquido)["Emission Strength"], 2.0, 0)
    sujeira = []
    for i in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.01, 0.06)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.012,
                                              location=(CX + r * math.cos(a), CY + r * math.sin(a), topo + 0.006))
        o = bpy.context.object
        o.data.materials.append(escoria)
        o.scale = (1, 1, 0.5)
        pop(o, f0 + 20 + 4 * i, (1, 1, 0.5))
        sujeira.append(o)
    # Etapa 4: o ourives tira a impureza, de novo e de novo.
    f0, f1 = p[3]
    for i, o in enumerate(sujeira):
        _chave(o, "location", tuple(o.location), f0 + 6 * i)
        _chave(o, "location", (o.location[0], o.location[1] - 0.2, o.location[2] + 0.15), f0 + 6 * i + 8)
        sumir(o, f0 + 6 * i + 2)
    # Etapa 5: o fogo apaga e o ouro vira espelho.
    f0, f1 = p[4]
    _energia(luz, 8, f0 + 10)
    _energia(luz, 0, f0 + 40)
    _valor(_no(liquido)["Emission Strength"], 2.0, f0 + 10)
    _valor(_no(liquido)["Emission Strength"], 0.0, f0 + 45)
    _valor(_no(liquido)["Roughness"], 0.4, f0 + 10)
    _valor(_no(liquido)["Roughness"], 0.05, f0 + 45)


def criar_diamante(col, m, faixas):
    """Carbono sob pressao, calor e tempo ate virar diamante."""
    import materiais
    _preparar(col, 7)
    p = faixas[1:6]
    z = MESA_Z
    pedra = materiais.simples("rocha", (0.17, 0.16, 0.15), 0.95, bump=0.7)
    carvao = materiais.simples("carvao", (0.025, 0.025, 0.025), 0.55, bump=0.6)
    _no(carvao)["Emission Color"].default_value = (1.0, 0.18, 0.03, 1)
    vidro = _vidro("diamante", 2.42)
    # Sem ambiente claro para refratar, o vidro puro fica preto: um brilho frio proprio resolve.
    _no(vidro)["Emission Color"].default_value = (0.75, 0.88, 1.0, 1)
    _no(vidro)["Emission Strength"].default_value = 0.25
    _caixa("laje", (CX, CY, z + 0.01), (0.32, 0.22, 0.02), pedra, col)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.05, location=(CX, CY, z + 0.065))
    c = bpy.context.object
    c.data.materials.append(carvao)
    # Etapa 1: so carbono, escuro e comum.
    f0, f1 = p[0]
    pop(c, f0, (1, 1, 1))
    _chave(c, "rotation_euler", (0, 0, 0), f0)
    _chave(c, "rotation_euler", (0, 0, 1.2), f1)
    # Etapa 2: o bloco de pressao desce.
    f0, f1 = p[1]
    bloco = _caixa("prensa", (CX, CY, z + 0.75), (0.3, 0.2, 0.2), pedra, col)
    _chave(bloco, "location", (CX, CY, z + 0.75), f0)
    _chave(bloco, "location", (CX, CY, z + 0.215), f0 + 14)
    _chave(c, "scale", (1, 1, 1), f0 + 14)
    _chave(c, "scale", (1.08, 1.08, 0.9), f0 + 18)
    # Etapa 3: o calor.
    f0, f1 = p[2]
    luz = _ponto("luz_calor", (CX, CY - 0.14, z + 0.07), (1.0, 0.25, 0.05), col)
    _energia(luz, 0, f0)
    _energia(luz, 5, f0 + 30)
    _valor(_no(carvao)["Emission Strength"], 0.0, f0)
    _valor(_no(carvao)["Emission Strength"], 1.0, f0 + 30)
    # Etapa 4: o tempo; o bloco treme e o carbono encolhe.
    f0, f1 = p[3]
    for i, f in enumerate(range(f0, f1, 3)):
        _chave(bloco, "location", (CX + (0.003 if i % 2 else -0.003), CY, z + 0.215 - 0.04 * (f - f0) / (f1 - f0)), f)
    _chave(c, "scale", (1.08, 1.08, 0.9), f0)
    _chave(c, "scale", (0.7, 0.7, 0.55), f1)
    # Etapa 5: o bloco sobe e o diamante aparece.
    f0, f1 = p[4]
    _chave(bloco, "location", (CX, CY, z + 0.175), f0)
    _chave(bloco, "location", (CX, CY, z + 0.9), f0 + 18)
    _energia(luz, 5, f0)
    _energia(luz, 0, f0 + 15)
    sumir(c, f0 + 10)
    d = bpy.data.objects.new("diamante", None)
    col.objects.link(d)
    d.location = (CX, CY, z + 0.1)
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.055, radius2=0.034, depth=0.025, location=(0, 0, 0.0125))
    coroa = bpy.context.object
    bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.055, radius2=0.0, depth=0.055, location=(0, 0, -0.0275))
    pav = bpy.context.object
    pav.rotation_euler = (math.pi, 0, 0)
    for o in (coroa, pav):
        o.data.materials.append(vidro)
        o.parent = d
    pop(d, f0 + 14, (1.4, 1.4, 1.4))
    _chave(d, "rotation_euler", (0.3, 0, 0), f0 + 14)
    _chave(d, "rotation_euler", (0.3, 0, 2 * math.pi), f1 + 120)
    brilho = _ponto("luz_brilho", (CX + 0.1, CY - 0.05, z + 0.3), (0.8, 0.9, 1), col)
    _energia(brilho, 0, f0 + 14)
    _energia(brilho, 6, f0 + 24)


def criar_ampulheta(col, m, faixas):
    """Ampulheta de 4.000 semanas: a areia cai a cada etapa da vida."""
    import materiais
    from mathutils import Matrix
    _preparar(col, 7)
    p = faixas[1:6]
    z = MESA_Z
    vidro = _vidro("vidro", 1.45)
    areia = materiais.simples("areia", (0.75, 0.55, 0.3), 0.9, bump=0.3)
    for h in (0.01, 0.355):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.095, depth=0.02, location=(CX, CY, z + h))
        bpy.context.object.data.materials.append(m["madeira"])
    for i in range(3):
        a = i * 2 * math.pi / 3 + 0.5
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.007, depth=0.34,
                                            location=(CX + 0.08 * math.cos(a), CY + 0.08 * math.sin(a), z + 0.18))
        bpy.context.object.data.materials.append(m["madeira"])
    for loc, r1, r2 in (((CX, CY, z + 0.10), 0.072, 0.009), ((CX, CY, z + 0.265), 0.009, 0.072)):
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=r1, radius2=r2, depth=0.165, location=loc)
        o = bpy.context.object
        o.data.materials.append(vidro)
        bpy.ops.object.shade_smooth()
    pesco = z + 0.183
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.003, radius2=0.056, depth=0.115)
    cima = bpy.context.object
    cima.data.transform(Matrix.Translation((0, 0, 0.0575)))
    cima.location = (CX, CY, pesco + 0.003)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.066, radius2=0.003, depth=0.1)
    baixo = bpy.context.object
    baixo.data.transform(Matrix.Translation((0, 0, 0.05)))
    baixo.location = (CX, CY, z + 0.021)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.0016, depth=1, location=(CX, CY, pesco))
    fio = bpy.context.object
    fio.data.transform(Matrix.Translation((0, 0, -0.5)))
    for o in (cima, baixo, fio):
        o.data.materials.append(areia)
    bpy.context.view_layer.objects.active = cima
    # A areia escorre de etapa em etapa; o volume vai em proporcao ao tempo vivido.
    _chave(fio, "scale", (1, 1, 0), p[0][0])
    _chave(fio, "scale", (1, 1, 0.16), p[0][0] + 8)
    for i, (f0, f1) in enumerate(p):
        for f, frac in ((f0, i / 5), (f1, (i + 1) / 5)):
            s = max(1 - frac, 0) ** (1 / 3)
            _chave(cima, "scale", (s, s, s), f)
            b = max(frac, 0.02) ** (1 / 3)
            _chave(baixo, "scale", (b, b, b), f)
    _chave(fio, "scale", (1, 1, 0.16), p[4][1])
    _chave(fio, "scale", (1, 1, 0), p[4][1] + 6)


def criar_escultura(col, m, faixas):
    """Bloco de marmore perdendo pedacos ate revelar o anjo que estava dentro."""
    import random

    import materiais
    rnd = random.Random(9)
    _preparar(col, 8)
    p = faixas[1:6]
    z = MESA_Z
    marmore = materiais.simples("marmore", (0.86, 0.84, 0.8), 0.35, sss=0.15)
    bruto = materiais.simples("marmore_bruto", (0.7, 0.68, 0.64), 0.95, bump=0.8)
    # O anjo, escondido desde o comeco dentro do bloco.
    _caixa("pedestal", (CX, CY, z + 0.012), (0.13, 0.13, 0.024), marmore, col)
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.07, radius2=0.028, depth=0.2, location=(CX, CY, z + 0.124))
    bpy.context.object.data.materials.append(marmore)
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.035, location=(CX, CY, z + 0.255))
    bpy.context.object.data.materials.append(marmore)
    bpy.ops.object.shade_smooth()
    for s in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(CX + s * 0.06, CY + 0.03, z + 0.18))
        a = bpy.context.object
        a.scale = (0.06, 0.014, 0.1)
        a.rotation_euler = (0, math.radians(-s * 28), 0)
        a.data.materials.append(marmore)
        bpy.ops.object.shade_smooth()
    # O bloco: 6 x 4 x 8 pedacos que vao caindo.
    bpy.ops.mesh.primitive_cube_add(size=0.0395)
    base = bpy.context.object
    malha = base.data
    malha.materials.append(bruto)
    bpy.data.objects.remove(base)
    blocos = []
    for i in range(6):
        for j in range(4):
            for k in range(8):
                loc = (CX - 0.1 + 0.04 * i, CY - 0.06 + 0.04 * j, z + 0.044 + 0.04 * k)
                o = bpy.data.objects.new("pedaco", malha)
                o.location = loc
                col.objects.link(o)
                dist = math.hypot(loc[0] - CX, (loc[1] - CY) * 1.3) + abs(loc[2] - z - 0.17) * 0.4
                blocos.append((dist + rnd.uniform(0, 0.03), o))
    blocos.sort(key=lambda t: -t[0])
    ordem = [o for _, o in blocos]
    partes = [(1, ordem[:10]), (2, ordem[10:110]), (3, ordem[110:170]), (4, ordem[170:])]
    for etapa, grupo in partes:
        f0, f1 = p[etapa]
        span = max(f1 - f0 - 14, 1)
        for n, o in enumerate(grupo):
            f = f0 + n * span // len(grupo)
            loc = tuple(o.location)
            _chave(o, "location", loc, f)
            _chave(o, "scale", (1, 1, 1), f)
            _chave(o, "rotation_euler", (0, 0, 0), f)
            _chave(o, "location", (loc[0] + rnd.uniform(-0.05, 0.05), loc[1] - 0.06, z - 0.02), f + 10)
            _chave(o, "rotation_euler", (rnd.uniform(-2, 2), rnd.uniform(-2, 2), 0), f + 10)
            _chave(o, "scale", (0, 0, 0), f + 12)
    f0, f1 = p[4]
    luz = _ponto("luz_anjo", (CX, CY + 0.3, z + 0.35), (1.0, 0.85, 0.6), col)
    _energia(luz, 0, f0)
    _energia(luz, 20, f0 + 40)


def criar_carta(col, m, faixas):
    """A última carta de Paulo: corrente, pergaminho, escrita, a vela do perdão, o selo e a carta enrolada."""
    import materiais
    _preparar(col, 8)
    z = MESA_Z
    etapas = faixas[1:6]
    # Etapa 1: a corrente sobre a mesa
    f0, _ = etapas[0]
    ferro = materiais.simples("ferro", (0.16, 0.15, 0.14), 0.45, metal=1.0)
    elos = []
    for i in range(7):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.032, minor_radius=0.008,
                                         location=(CX - 0.27 + i * 0.05, CY + 0.16, z + 0.012))
        e = bpy.context.object
        e.rotation_euler = (math.radians(90) if i % 2 else 0, 0, 0)
        e.data.materials.append(ferro)
        bpy.ops.object.shade_smooth()
        pop(e, f0 + 3 * i)
        elos.append(e)
    # Etapa 2: o pergaminho se desenrola
    f0, f1 = etapas[1]
    esq = CX - 0.2
    perg = _caixa("pergaminho", (CX, CY - 0.05, z + 0.006), (0.4, 0.28, 0.004), m["papel"], col)
    _chave(perg, "scale", (0, 0.28, 0.004), 0)
    _chave(perg, "location", (esq, CY - 0.05, z + 0.006), 0)
    _chave(perg, "scale", (0, 0.28, 0.004), f0 + 6)
    _chave(perg, "location", (esq, CY - 0.05, z + 0.006), f0 + 6)
    _chave(perg, "scale", (0.4, 0.28, 0.004), f0 + (f1 - f0) * 2 // 3)
    _chave(perg, "location", (CX, CY - 0.05, z + 0.006), f0 + (f1 - f0) * 2 // 3)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=0.3, location=(esq, CY - 0.05, z + 0.016), rotation=(math.radians(90), 0, 0))
    rolo = bpy.context.object
    rolo.data.materials.append(m["papel"])
    bpy.ops.object.shade_smooth()
    pop(rolo, f0)
    _chave(rolo, "location", (esq, CY - 0.05, z + 0.016), f0 + 6)
    _chave(rolo, "location", (CX + 0.2, CY - 0.05, z + 0.016), f0 + (f1 - f0) * 2 // 3)
    # Etapa 3: a pena escreve
    f0, f1 = etapas[2]
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.004, radius2=0.028, depth=0.26)
    pena = bpy.context.object
    pena.data.materials.append(m["barba"])
    pena.scale = (1, 0.25, 1)
    bpy.ops.object.shade_smooth()
    pena.rotation_euler = (math.radians(30), 0, math.radians(-35))
    pop(pena, f0, (1, 0.25, 1))
    texto = _caixa("texto", (esq + 0.02, CY - 0.05, z + 0.0095), (0, 0.24, 0.001), m["pagina"], col)
    _chave(texto, "scale", (0, 0.24, 0.001), f0)
    _chave(texto, "location", (esq + 0.02, CY - 0.05, z + 0.0095), f0)
    _chave(texto, "scale", (0.36, 0.24, 0.001), f1)
    _chave(texto, "location", (CX, CY - 0.05, z + 0.0095), f1)
    for k in range(6):
        f = f0 + (f1 - f0) * k // 5
        _chave(pena, "location", (esq + 0.04 + 0.32 * k / 5, CY - 0.05 + 0.08 * ((-1) ** k), z + 0.14), f)
    # Etapa 4: a vela do perdão acende
    f0, _ = etapas[3]
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.14, location=(CX + 0.08, CY + 0.2, z + 0.07))
    vela = bpy.context.object
    vela.data.materials.append(materiais.simples("cera", (0.92, 0.86, 0.7), 0.5))
    pop(vela, f0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(CX + 0.08, CY + 0.2, z + 0.165))
    chama = bpy.context.object
    chama.data.materials.append(m["chama"])
    pop(chama, f0 + 12, (0.011, 0.011, 0.026))
    luz = _ponto("luz_vela", (CX + 0.08, CY + 0.2, z + 0.2), (1.0, 0.62, 0.3), col)
    _energia(luz, 0, f0 + 12)
    _energia(luz, 6, f0 + 20)
    # Etapa 5: o selo de cera, a carta enrolada, a corrente some
    f0, f1 = etapas[4]
    bpy.ops.mesh.primitive_cylinder_add(radius=0.032, depth=0.01, location=(CX, CY - 0.05, z + 0.013))
    selo = bpy.context.object
    selo.data.materials.append(materiais.simples("cera_vermelha", (0.45, 0.04, 0.03), 0.35))
    bpy.ops.object.shade_smooth()
    pop(selo, f0 + 4)
    meio = f0 + (f1 - f0) // 2
    for o in (perg, texto, rolo, pena):
        sumir(o, meio)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.3, location=(CX, CY - 0.05, z + 0.03), rotation=(math.radians(90), 0, 0))
    carta = bpy.context.object
    carta.data.materials.append(m["papel"])
    bpy.ops.object.shade_smooth()
    pop(carta, meio + 2)
    _chave(selo, "location", (CX, CY - 0.05, z + 0.013), meio)
    _chave(selo, "location", (CX, CY - 0.05 - 0.0, z + 0.062), meio + 4)
    for i, e in enumerate(elos):
        sumir(e, meio + 6 + 2 * i)


def criar_babilonia(col, m, faixas):
    """Tábua de argila e moedas: a cada etapa, um décimo é guardado e a pilha cresce sozinha."""
    import materiais
    _preparar(col, 9)
    z = MESA_Z
    etapas = faixas[1:6]
    ouro = _ouro()
    argila = materiais.simples("argila", (0.55, 0.36, 0.22), 0.85, ruido=0.4, escala_ruido=60, bump=0.4)
    # Etapa 1: a tábua de argila com marcas (cuneiforme)
    f0, _ = etapas[0]
    tab = _caixa("tabua", (CX - 0.2, CY + 0.1, z + 0.02), (0.22, 0.3, 0.04), argila, col)
    tab.rotation_euler = (0, 0, math.radians(12))
    pop(tab, f0)
    for i in range(18):
        r = (i * 7919) % 100 / 100
        k = _caixa("cunha", (CX - 0.27 + (i % 3) * 0.06, CY - 0.02 + (i // 3) * 0.045, z + 0.041),
                   (0.03, 0.006, 0.004), m["madeira"], col)
        k.rotation_euler = (0, 0, math.radians(12 + 40 * r))
        pop(k, f0 + 6 + i)
    # Etapas 2 a 5: moedas ganhas (pilha da direita) e o décimo guardado (pilha da esquerda), que cresce sozinha
    def moeda(x, y, h, f):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.028, depth=0.006, location=(x, y, z + 0.004 + h * 0.0065))
        c = bpy.context.object
        c.data.materials.append(ouro)
        bpy.ops.object.shade_smooth()
        pop(c, f)
        return c
    ganho = 0
    guardado = 0
    for e, (f0, f1) in enumerate(etapas[1:]):
        n = [10, 10, 10, 10][e]
        for k in range(n):
            f = f0 + (f1 - f0) * k // (n + 4)
            if k == 0:          # o primeiro décimo vai para a pilha guardada
                moeda(CX + 0.12, CY - 0.12, guardado, f); guardado += 1
            else:
                moeda(CX + 0.26, CY - 0.05, ganho % 14, f); ganho += 1
        if e >= 1:              # o dinheiro guardado trabalha: a pilha cresce sozinha
            for k in range(guardado * (e + 1) // 2):
                moeda(CX + 0.06 + 0.06 * ((k // 8) % 2), CY - 0.12 - 0.06 * (k // 16), guardado + k % 8, f0 + (f1 - f0) // 2 + 2 * k)
        guardado += e * 2


def criar_diogenes(col, m, faixas):
    """A lamparina acesa em pleno dia e um celular cuja tela rola o feed: carro, selfie, briga; depois apaga."""
    import materiais
    from pathlib import Path
    _preparar(col, 7)
    z = MESA_Z
    etapas = faixas[1:6]
    barro = materiais.simples("barro_lamp", (0.6, 0.33, 0.18), 0.7, ruido=0.3, escala_ruido=18, bump=0.2)
    # Etapa 1: a lamparina de Diogenes, acesa em pleno dia ("procuro um homem")
    f0, _ = etapas[0]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(CX - 0.3, CY + 0.18, z + 0.035))
    lp = bpy.context.object
    lp.scale = (0.09, 0.06, 0.035)
    lp.data.materials.append(barro)
    bpy.ops.object.shade_smooth()
    pop(lp, f0)
    bico = _caixa("bico", (CX - 0.2, CY + 0.18, z + 0.05), (0.07, 0.03, 0.025), barro, col)
    pop(bico, f0 + 2)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(CX - 0.17, CY + 0.18, z + 0.09))
    ch = bpy.context.object
    ch.scale = (0.012, 0.012, 0.035)
    ch.data.materials.append(m["chama"])
    pop(ch, f0 + 10)
    luz = _ponto("luz_lamp", (CX - 0.17, CY + 0.18, z + 0.16), (1.0, 0.6, 0.3), col)
    _energia(luz, 0, f0 + 10)
    _energia(luz, 6, f0 + 18)
    # o celular, em pe num apoio, virado para a camera
    corpo_mat = materiais.simples("celular", (0.02, 0.02, 0.025), 0.25, metal=0.6)
    tela = bpy.data.materials.new("tela_feed")
    tela.use_nodes = True
    nt = tela.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(Path(__file__).parent / "texturas" / "feed-diogenes.png"))
    uv = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1, 1 / 3, 1)
    nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    loc = mp.inputs["Location"]
    forca = em.inputs["Strength"]
    pivo = bpy.data.objects.new("celular_pivo", None)
    pivo.location = (CX + 0.02, CY - 0.02, z + 0.005)
    col.objects.link(pivo)
    caixa = _caixa("celular_corpo", (0, 0, 0.14), (0.15, 0.012, 0.28), corpo_mat, col)
    caixa.parent = pivo
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -0.0065, 0.14))
    sc = bpy.context.object
    sc.name = "celular_tela"
    sc.scale = (0.138, 0.245, 1)
    sc.rotation_euler = (math.radians(90), 0, 0)
    sc.data.materials.append(tela)
    for c in sc.users_collection:
        c.objects.unlink(sc)
    col.objects.link(sc)
    sc.parent = pivo
    apoio = _caixa("apoio", (CX + 0.02, CY + 0.07, z + 0.03), (0.12, 0.1, 0.06), m["madeira"], col)
    # Etapa 2: o celular aparece no primeiro post (o carro novo)
    f0, f1 = etapas[1]
    pivo.rotation_euler = (math.radians(-18), 0, math.radians(8))
    pivo.keyframe_insert("rotation_euler", frame=0)
    pop(pivo, f0)
    pop(apoio, f0)
    _valor(forca, 0.0, f0)
    _valor(forca, 2.2, f0 + 8)
    loc.default_value = (0, 2 / 3, 0)
    loc.keyframe_insert("default_value", frame=f0)
    # Etapas 3 e 4: o dedo invisivel rola o feed (selfie com filtro, depois a briga)
    for e, alvo in ((2, 1 / 3), (3, 0.0)):
        g0, g1 = etapas[e]
        loc.keyframe_insert("default_value", frame=g0)
        loc.default_value = (0, alvo + 0.03, 0)
        loc.keyframe_insert("default_value", frame=g0 + 9)
        loc.default_value = (0, alvo, 0)
        loc.keyframe_insert("default_value", frame=g0 + 14)
    # na briga, o celular vibra
    g0, g1 = etapas[3]
    for k in range(0, min(40, g1 - g0), 3):
        pivo.rotation_euler = (math.radians(-18), 0, math.radians(8 + (2.5 if k % 2 else -2.5)))
        pivo.keyframe_insert("rotation_euler", frame=g0 + 18 + k)
    pivo.rotation_euler = (math.radians(-18), 0, math.radians(8))
    pivo.keyframe_insert("rotation_euler", frame=g0 + 18 + 42)
    # Etapa 5: "sai da frente do meu sol" - a tela apaga e o celular tomba de cara na mesa; o sol entra
    f0, f1 = etapas[4]
    _valor(forca, 2.2, f0 + 4)
    _valor(forca, 0.0, f0 + 10)
    pivo.keyframe_insert("rotation_euler", frame=f0 + 10)
    pivo.rotation_euler = (math.radians(88), 0, math.radians(8))
    pivo.keyframe_insert("rotation_euler", frame=f0 + 20)
    pivo.location = (CX + 0.02, CY - 0.02, z + 0.005)
    pivo.keyframe_insert("location", frame=f0 + 10)
    pivo.location = (CX + 0.02, CY - 0.17, z + 0.012)
    pivo.keyframe_insert("location", frame=f0 + 20)
    sol = bpy.data.objects["luz_objeto"]
    _energia(sol, 7, f0 + 8)
    _energia(sol, 30, f0 + 26)


def criar_ansiedade(col, m, faixas):
    """A ansiedade como uma criaturinha de fumaca escura com olhos acesos: chega pequena, faz o relogio
    disparar, cresce quando obedecida, recua quando a vela acende e volta ao tamanho real com o amanhecer."""
    import materiais
    _preparar(col, 3)
    z = MESA_Z
    et = faixas[1:6]
    fumaca = materiais.simples("fumaca", (0.012, 0.01, 0.02), 0.65, ruido=0.6, escala_ruido=25, bump=0.8)
    olho = bpy.data.materials.new("olho")
    olho.use_nodes = True
    nt = olho.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.85, 0.45, 1)
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    brilho = em.inputs["Strength"]

    def esfera(nome, loc, esc, mat, pai):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=loc)
        o = bpy.context.object
        o.name, o.scale = nome, esc
        o.data.materials.append(mat)
        bpy.ops.object.shade_smooth()
        for c in o.users_collection:
            c.objects.unlink(o)
        col.objects.link(o)
        o.parent = pai
        return o

    # a criatura: corpo de gota, cabeca, bracos finos caidos e dois olhos
    bicho = bpy.data.objects.new("ansiedade", None)
    bicho.location = (CX + 0.08, CY + 0.0, z)
    col.objects.link(bicho)
    corpo = esfera("ans_corpo", (0, 0, 0.07), (0.06, 0.055, 0.075), fumaca, bicho)
    tx = bpy.data.textures.new("fumaca_tx", "CLOUDS")
    tx.noise_scale = 0.25
    dp = corpo.modifiers.new("fumaca", "DISPLACE")
    dp.texture, dp.strength = tx, 0.25
    corpo.modifiers.new("liso", "SUBSURF").levels = 2
    esfera("ans_cabeca", (0, -0.005, 0.16), (0.05, 0.047, 0.045), fumaca, bicho)
    for s in (-1, 1):
        esfera("ans_olho", (s * 0.019, -0.042, 0.168), (0.011, 0.006, 0.014), olho, bicho)
        b = esfera("ans_braco", (s * 0.06, -0.01, 0.06), (0.009, 0.009, 0.05), fumaca, bicho)
        b.rotation_euler = (0, math.radians(s * 25), 0)
        esfera("ans_chifre", (s * 0.03, 0, 0.205), (0.008, 0.008, 0.022), fumaca, bicho).rotation_euler = (0, math.radians(s * 30), 0)

    def tam(v, f):
        bicho.scale = (v, v, v)
        bicho.keyframe_insert("scale", frame=f)

    # o despertador
    vermelho = materiais.simples("despertador", (0.6, 0.05, 0.04), 0.35, metal=0.4)
    branco = materiais.simples("mostrador", (0.92, 0.9, 0.85), 0.4)
    rx, ry = CX - 0.1, CY - 0.07
    rel = []
    rel.append(_caixa("rel_pe", (rx, ry, z + 0.01), (0.07, 0.03, 0.02), vermelho, col))
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.055, depth=0.035, location=(rx, ry, z + 0.075),
                                        rotation=(math.radians(90), 0, 0))
    rel.append(bpy.context.object)
    rel[-1].data.materials.append(vermelho)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.047, depth=0.004, location=(rx, ry - 0.018, z + 0.075),
                                        rotation=(math.radians(90), 0, 0))
    rel.append(bpy.context.object)
    rel[-1].data.materials.append(branco)
    for s in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=(rx + s * 0.035, ry, z + 0.13))
        rel.append(bpy.context.object)
        rel[-1].data.materials.append(vermelho)
    eixo = bpy.data.objects.new("rel_eixo", None)
    eixo.location = (rx, ry - 0.022, z + 0.075)
    col.objects.link(eixo)
    for nome, comp, larg in (("ponteiro_h", 0.026, 0.005), ("ponteiro_m", 0.038, 0.003)):
        pt = _caixa(nome, (rx, ry - 0.022, z + 0.075 + comp / 2), (larg, 0.002, comp), m["madeira"], col)
        pt.parent = eixo
        pt.location = (0, 0, comp / 2)
        rel.append(pt)
    for o in rel[1:5]:
        for c in o.users_collection:
            c.objects.unlink(o)
        col.objects.link(o)
    # a vela (apagada ate a etapa 4)
    vx, vy = CX - 0.02, CY + 0.12
    _cil_v = _caixa("vela", (vx, vy, z + 0.045), (0.035, 0.035, 0.09), materiais.simples("cera", (0.9, 0.86, 0.75), 0.6, sss=0.3), col)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(vx, vy, z + 0.105))
    chama = bpy.context.object
    chama.scale = (0.008, 0.008, 0.022)
    chama.data.materials.append(m["chama"])
    luz_vela = _ponto("luz_vela", (vx, vy - 0.04, z + 0.16), (1.0, 0.6, 0.3), col)

    # Etapa 1: ela chega, pequena, e abre os olhos
    f0, f1 = et[0]
    tam(0.0, 0)
    tam(0.0, f0)
    tam(0.6, f0 + 8)
    tam(0.5, f0 + 12)
    _valor(brilho, 0.0, f0 + 14)
    _valor(brilho, 8.0, f0 + 20)
    for o in rel:
        if o.parent is None:
            pop(o, f0 + 4)
    pop(eixo, f0 + 4)
    _chave(bicho, "rotation_euler", (0, 0, 0), f0)
    # Etapa 2: o relogio dispara; ela se vira para ele
    f0, f1 = et[1]
    _chave(eixo, "rotation_euler", (0, 0, 0), f0 + 6)
    _chave(eixo, "rotation_euler", (0, -math.tau * 10, 0), f1)
    _chave(bicho, "rotation_euler", (0, 0, 0), f0 + 6)
    _chave(bicho, "rotation_euler", (0, 0, math.radians(-35)), f0 + 20)
    for k in range(f0 + 24, f1, 4):        # o despertador treme
        for o in rel:
            if o.parent is None:
                o.location.x += 0.003 if (k // 4) % 2 else -0.003
                o.keyframe_insert("location", frame=k)
    # Etapa 3: cada vez que voce obedece, ela cresce (e o quarto escurece)
    f0, f1 = et[2]
    _chave(bicho, "rotation_euler", (0, 0, math.radians(-35)), f0)
    _chave(bicho, "rotation_euler", (0, 0, 0), f0 + 15)
    tam(0.5, f0 + 4)
    tam(1.9, f1)
    _valor(brilho, 8.0, f0)
    _valor(brilho, 25.0, f1)
    _energia(bpy.data.objects["luz_objeto"], 3, f0)
    _energia(bpy.data.objects["luz_objeto"], 0.6, f1)
    # Etapa 4: a vela acende e ela recua
    f0, f1 = et[3]
    fv = f0 + (f1 - f0) // 2
    pop(chama, fv)
    _energia(luz_vela, 0, fv)
    _energia(luz_vela, 9, fv + 10)
    tam(1.9, fv + 2)
    tam(1.15, fv + 22)
    _chave(bicho, "location", (CX + 0.08, CY, z), fv + 2)
    _chave(bicho, "location", (CX + 0.11, CY + 0.06, z), fv + 22)
    _valor(brilho, 25.0, fv + 2)
    _valor(brilho, 6.0, fv + 22)
    # Etapa 5: respira; ela volta ao tamanho que e e os olhos quase apagam
    f0, f1 = et[4]
    tam(1.15, f0)
    tam(0.25, f1 - 10)
    _valor(brilho, 6.0, f0)
    _valor(brilho, 1.0, f1 - 10)
    _energia(bpy.data.objects["luz_objeto"], 0.6, f0)
    _energia(bpy.data.objects["luz_objeto"], 4, f1)


# ---------------- pecas comuns dos videos sem mesa ----------------
def _relink(o, col):
    for c in o.users_collection:
        c.objects.unlink(o)
    col.objects.link(o)
    return o


def _esf(nome, loc, esc, mat, col, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=1, location=loc)
    o = bpy.context.object
    o.name, o.scale = nome, esc
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return _relink(o, col)


def _cilindro(nome, loc, r, h, mat, col, rot=(0, 0, 0), v=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = nome
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return _relink(o, col)


def _cone(nome, loc, r1, r2, h, mat, col, rot=(0, 0, 0), v=24):
    bpy.ops.mesh.primitive_cone_add(vertices=v, radius1=r1, radius2=r2, depth=h, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = nome
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return _relink(o, col)


def _texto(nome, txt, loc, tam, mat, col, rot=(math.radians(90), 0, 0), ext=0.01):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = nome
    o.data.body = txt
    o.data.size, o.data.extrude = tam, ext
    o.data.align_x, o.data.align_y = "CENTER", "CENTER"
    from pathlib import Path
    fonte = Path(__file__).resolve().parent.parent / "shorts" / "fontes" / "Inter-ExtraBold.otf"
    if fonte.exists():
        o.data.font = bpy.data.fonts.load(str(fonte), check_existing=True)
    o.data.materials.append(mat)
    return _relink(o, col)


def _emis(nome, cor, forca):
    mat = bpy.data.materials.new(nome)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*cor, 1)
    em.inputs["Strength"].default_value = forca
    nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return mat


def _voar(o, f, dz=0.3, d=16):
    """Sobe e some (o que perdeu o valor)."""
    _chave(o, "location", tuple(o.location), f)
    _chave(o, "scale", tuple(o.scale), f)
    _chave(o, "location", (o.location.x, o.location.y, o.location.z + dz), f + d)
    _chave(o, "scale", (0, 0, 0), f + d)


def _acender(nome, loc, energia, f, col, cor=(1.0, 0.6, 0.3), d=10):
    luz = _ponto(nome, loc, cor, col)
    _energia(luz, 0, f)
    _energia(luz, energia, f + d)
    return luz


def _lamparina_barro(loc, f, col, m, energia=6):
    """Lamparina de oleo de barro que acende no quadro f."""
    import materiais
    barro = materiais.simples("barro_lp", (0.6, 0.33, 0.18), 0.7, ruido=0.3, escala_ruido=18, bump=0.2)
    x, y, z = loc
    lp = _esf("lamparina", (x, y, z + 0.03), (0.075, 0.05, 0.03), barro, col)
    bico = _caixa("bico", (x + 0.08, y, z + 0.045), (0.06, 0.025, 0.02), barro, col)
    ch = _esf("chama", (x + 0.105, y, z + 0.08), (0.01, 0.01, 0.03), m["chama"], col, 12)
    pop(lp, max(0, f - 12))
    pop(bico, max(0, f - 10))
    pop(ch, f)
    return _acender("luz_lamparina", (x + 0.1, y - 0.03, z + 0.15), energia, f, col)


def criar_entrevista(col, m, faixas):
    """Na cadeira do candidato: a pasta cheia de diplomas que voa embora; depois pao (quem voce ajudou),
    um ramo de oliveira (quem voce perdoou), uma moeda pequena (fiel no pouco) e a luz que vem da porta."""
    import materiais
    _preparar(col, 6)
    z = MESA_Z
    et = faixas[1:6]
    couro = materiais.simples("pasta", (0.2, 0.1, 0.05), 0.5, ruido=0.2, escala_ruido=30)
    ouro = _ouro()
    f0, f1 = et[0]
    pasta = _caixa("pasta", (CX, CY + 0.05, z + 0.02), (0.3, 0.22, 0.04), couro, col)
    pop(pasta, f0)
    papeis = []
    for k in range(4):
        p = _caixa("diploma", (CX - 0.12 + k * 0.08, CY - 0.03 + 0.02 * k, z + 0.05 + 0.004 * k), (0.16, 0.12, 0.003), m["papel"], col)
        p.rotation_euler = (0, 0, math.radians(-25 + k * 16))
        pop(p, f0 + 8 + k * 5)
        selo = _cilindro("selo", (p.location.x + 0.04, p.location.y - 0.03, p.location.z + 0.003), 0.015, 0.003,
                         materiais.simples("lacre", (0.55, 0.04, 0.03), 0.4), col)
        pop(selo, f0 + 10 + k * 5)
        papeis += [p, selo]
    trofeu = _cilindro("trofeu", (CX + 0.17, CY + 0.08, z + 0.07), 0.025, 0.12, ouro, col)
    taca = _cone("taca", (CX + 0.17, CY + 0.08, z + 0.15), 0.02, 0.05, 0.06, ouro, col)
    pop(trofeu, f0 + 30)
    pop(taca, f0 + 32)
    # Etapa 2: ele nem abre - tudo sobe e some; aparece um pao
    f0, f1 = et[1]
    for k, o in enumerate(papeis + [pasta, trofeu, taca]):
        _voar(o, f0 + 4 + k * 2, 0.5, 18)
    casca = materiais.simples("casca_pao", (0.38, 0.19, 0.07), 0.7, ruido=0.4, escala_ruido=20, bump=0.6)
    pao = _esf("pao", (CX - 0.1, CY, z + 0.04), (0.1, 0.065, 0.045), casca, col)
    pop(pao, f0 + (f1 - f0) // 2)
    # Etapa 3: o ramo de oliveira
    f0, f1 = et[2]
    folha = materiais.simples("folha_oliva", (0.22, 0.32, 0.15), 0.6)
    ramo = _cilindro("ramo", (CX + 0.06, CY + 0.02, z + 0.012), 0.005, 0.24, m["madeira"], col,
                     (0, math.radians(90), math.radians(20)))
    pop(ramo, f0 + 4)
    for k in range(8):
        t = -0.1 + k * 0.028
        s = 1 if k % 2 else -1
        fl = _esf("folha", (CX + 0.06 + t * math.cos(math.radians(20)), CY + 0.02 + t * math.sin(math.radians(20)) + s * 0.014,
                            z + 0.015), (0.022, 0.007, 0.003), folha, col, 12)
        fl.rotation_euler = (0, 0, math.radians(20 + s * 40))
        pop(fl, f0 + 8 + k * 3)
    # Etapa 4: uma moeda pequena, brilhando
    f0, f1 = et[3]
    moeda = _cilindro("moeda", (CX, CY - 0.1, z + 0.004), 0.018, 0.004, ouro, col)
    pop(moeda, f0 + 6)
    _acender("luz_moeda", (CX, CY - 0.13, z + 0.08), 2.5, f0 + 8, col, (1.0, 0.8, 0.45))
    # Etapa 5: a luz da porta cobre a cadeira
    f0, f1 = et[4]
    _acender("luz_coracao", (CX, CY - 0.2, z + 0.45), 40, f0 + 4, col, (1.0, 0.88, 0.7), 40)


def criar_oitenta(col, m, faixas):
    """No caixote ao lado da cadeira de balanco: a ampulheta de um minuto corre o video todo;
    o retrato da mae, a bola de papel (a vergonha) que some, a maca, o celular que se desliga e o broto."""
    import materiais
    _preparar(col, 6)
    z = MESA_Z
    et = faixas[1:6]
    fim = faixas[-1][1]
    vidro = _vidro("vidro_amp", 1.45)
    areia = materiais.simples("areia", (0.85, 0.65, 0.35), 0.9)
    ax, ay = CX - 0.2, CY + 0.12
    for dz, r1, r2 in ((0.06, 0.05, 0.008), (0.14, 0.008, 0.05)):
        _cone("amp_vidro", (ax, ay, z + 0.02 + dz), r1, r2, 0.08, vidro, col)
    for dz in (0.01, 0.2):
        _cilindro("amp_tampa", (ax, ay, z + dz), 0.06, 0.02, m["madeira"], col)
    for a in range(3):
        aa = a / 3 * math.tau
        _cilindro("amp_haste", (ax + 0.052 * math.cos(aa), ay + 0.052 * math.sin(aa), z + 0.105), 0.005, 0.19, m["madeira"], col)
    cima = _cone("areia_cima", (ax, ay, z + 0.15), 0.006, 0.042, 0.06, areia, col)
    baixo = _cone("areia_baixo", (ax, ay, z + 0.035), 0.044, 0.004, 0.03, areia, col)
    baixo.scale = (1, 1, 0.01)
    _chave(cima, "scale", (1, 1, 1), 0)
    _chave(cima, "scale", (0.4, 0.4, 0.05), fim)
    _chave(baixo, "scale", (0.3, 0.3, 0.02), 0)
    _chave(baixo, "scale", (1, 1, 1), fim)
    # Etapa 1: o retrato da mae (moldura com foto quente)
    f0, f1 = et[0]
    mold = _caixa("moldura", (CX + 0.02, CY + 0.12, z + 0.09), (0.15, 0.015, 0.19), m["madeira"], col)
    mold.rotation_euler = (math.radians(-12), 0, math.radians(-8))
    from pathlib import Path
    fm = _emis("foto_mae", (0.75, 0.55, 0.38), 0.9)
    tx = fm.node_tree.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(str(Path(__file__).parent / "texturas" / "retrato-mae.png"))
    fm.node_tree.links.new(tx.outputs["Color"], fm.node_tree.nodes["Emission"].inputs["Color"])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(CX + 0.02, CY + 0.1, z + 0.09))
    foto = _relink(bpy.context.object, col)
    foto.name = "foto"
    foto.scale = (0.12, 0.16, 1)
    foto.data.materials.append(fm)
    foto.rotation_euler = (math.radians(90 - 12), 0, math.radians(-8))
    pop(mold, f0 + 4)
    pop(foto, f0 + 6)
    # Etapa 2: a vergonha: uma bola de papel amassado que encolhe ate sumir
    f0, f1 = et[1]
    bola = _esf("vergonha", (CX - 0.05, CY - 0.08, z + 0.04), (0.04, 0.04, 0.04), m["papel"], col, 8)
    bola.modifiers.new("amassado", "DISPLACE").strength = 0.4
    bola.modifiers["amassado"].texture = bpy.data.textures.new("amassa", "VORONOI")
    pop(bola, f0 + 4)
    _chave(bola, "scale", (0.04, 0.04, 0.04), f0 + (f1 - f0) // 2)
    _chave(bola, "scale", (0, 0, 0), f1 - 6)
    # Etapa 3: a maca
    f0, f1 = et[2]
    verm = materiais.simples("maca", (0.55, 0.04, 0.03), 0.35, ruido=0.3, escala_ruido=10)
    maca = _esf("maca", (CX - 0.05, CY - 0.06, z + 0.045), (0.045, 0.045, 0.04), verm, col)
    cab = _cilindro("cabinho", (CX - 0.05, CY - 0.06, z + 0.095), 0.003, 0.025, m["madeira"], col)
    pop(maca, f0 + 4)
    pop(cab, f0 + 8)
    # Etapa 4: o celular aceso que vira de cara para baixo e apaga
    f0, f1 = et[3]
    cel = _caixa("celular", (CX + 0.14, CY - 0.06, z + 0.006), (0.07, 0.14, 0.01),
                 materiais.simples("cel", (0.02, 0.02, 0.025), 0.25, metal=0.6), col)
    tela = _caixa("tela", (CX + 0.14, CY - 0.06, z + 0.0115), (0.064, 0.13, 0.001), _emis("tela_cel", (0.5, 0.7, 1.0), 2.5), col)
    pop(cel, f0 + 4)
    pop(tela, f0 + 4)
    vira = f0 + (f1 - f0) // 2
    _chave(tela, "scale", tuple(tela.scale), vira)
    _chave(tela, "scale", (0, 0, 0), vira + 4)
    _chave(cel, "rotation_euler", (0, 0, 0), vira)
    _chave(cel, "rotation_euler", (0, math.pi, 0), vira + 10)
    # Etapa 5: comeca - um vasinho e o broto que cresce
    f0, f1 = et[4]
    vaso = _cilindro("vasinho", (CX + 0.05, CY + 0.0, z + 0.035), 0.035, 0.07,
                     materiais.simples("terracota", (0.6, 0.3, 0.17), 0.8), col)
    pop(vaso, f0 + 2)
    caule = _cilindro("broto", (CX + 0.05, CY, z + 0.1), 0.003, 0.06, materiais.simples("verde", (0.2, 0.45, 0.1), 0.6), col)
    caule.location.z = z + 0.07
    _chave(caule, "scale", (1, 1, 0), 0)
    _chave(caule, "scale", (1, 1, 0), f0 + 10)
    _chave(caule, "scale", (1, 1, 2.0), f1)
    for s in (-1, 1):
        fo = _esf("folhinha", (CX + 0.05 + s * 0.014, CY, z + 0.135), (0.014, 0.006, 0.003),
                  materiais.simples("verde2", (0.25, 0.55, 0.12), 0.6), col, 12)
        fo.rotation_euler = (0, math.radians(-s * 25), 0)
        pop(fo, f0 + (f1 - f0) // 2 + 6)


def criar_idades(col, m, faixas):
    """Sobre o bau do sotao, um objeto por idade: o ursinho (5), o espelho (16), o capelo (25),
    o calendario que perde as folhas (30) e a vela que acende (50)."""
    import materiais
    _preparar(col, 6)
    z = MESA_Z
    et = faixas[1:6]
    xs = [-0.155, -0.07, 0.01, 0.1, 0.19]
    # 5 anos: ursinho de pelucia
    f0, _ = et[0]
    pel = materiais.simples("pelucia", (0.5, 0.32, 0.17), 0.95, ruido=0.5, escala_ruido=90, bump=0.6)
    x, y = CX + xs[0], CY + 0.02
    for nome, d, e in (("urso_corpo", (0, 0, 0.045), (0.04, 0.035, 0.045)), ("urso_cabeca", (0, -0.005, 0.11), (0.033, 0.03, 0.03)),
                       ("urso_or1", (-0.025, 0, 0.14), (0.012, 0.008, 0.012)), ("urso_or2", (0.025, 0, 0.14), (0.012, 0.008, 0.012)),
                       ("urso_braco1", (-0.042, -0.01, 0.055), (0.012, 0.012, 0.025)), ("urso_braco2", (0.042, -0.01, 0.055), (0.012, 0.012, 0.025)),
                       ("urso_fuc", (0, -0.03, 0.105), (0.013, 0.01, 0.01))):
        pop(_esf(nome, (x + d[0], y + d[1], z + d[2]), e, pel, col, 16), f0 + 4)
    for s in (-1, 1):
        pop(_esf("urso_olho", (x + s * 0.011, y - 0.03, z + 0.12), (0.004, 0.004, 0.004),
                 materiais.simples("botao", (0.01, 0.01, 0.01), 0.2), col, 8), f0 + 8)
    # 16 anos: o espelho de mao
    f0, _ = et[1]
    esp = materiais.simples("espelho", (0.95, 0.95, 0.95), 0.03, metal=1.0)
    x, y = CX + xs[1], CY + 0.06
    aro = _cilindro("espelho_aro", (x, y, z + 0.11), 0.05, 0.012, m["latao"], col, (math.radians(75), 0, 0))
    vid = _cilindro("espelho_vidro", (x, y - 0.007, z + 0.11), 0.044, 0.004, esp, col, (math.radians(75), 0, 0))
    cabo = _cilindro("espelho_cabo", (x, y + 0.012, z + 0.03), 0.008, 0.07, m["latao"], col, (math.radians(-15), 0, 0))
    for o in (aro, vid, cabo):
        pop(o, f0 + 4)
    # 25 anos: o capelo de formatura
    f0, _ = et[2]
    preto = materiais.simples("capelo", (0.02, 0.02, 0.025), 0.6)
    x, y = CX + xs[2], CY - 0.04
    base = _cilindro("capelo_base", (x, y, z + 0.025), 0.045, 0.05, preto, col)
    topo = _caixa("capelo_topo", (x, y, z + 0.052), (0.13, 0.13, 0.006), preto, col)
    topo.rotation_euler = (0, 0, math.radians(20))
    borla = _cilindro("borla", (x + 0.05, y - 0.03, z + 0.03), 0.003, 0.05, materiais.simples("borla", (0.8, 0.6, 0.15), 0.5), col)
    for o in (base, topo, borla):
        pop(o, f0 + 4)
    # 30 anos: o calendario que perde as folhas ("ainda tenho tempo")
    f0, f1 = et[3]
    x, y = CX + xs[3], CY + 0.06
    suporte = _caixa("cal_base", (x, y + 0.01, z + 0.06), (0.1, 0.01, 0.12), m["madeira"], col)
    suporte.rotation_euler = (math.radians(-15), 0, 0)
    pop(suporte, f0 + 2)
    verm = materiais.simples("cal_topo", (0.6, 0.06, 0.05), 0.5)
    for k in range(7):
        fo = _caixa("cal_folha", (x, y - 0.002 - 0.002 * k, z + 0.06), (0.09, 0.002, 0.1), m["papel"], col)
        fo.rotation_euler = (math.radians(-15), 0, 0)
        pop(fo, f0 + 4)
        if k < 6:
            fv = f0 + 14 + (6 - k) * 6
            _chave(fo, "location", tuple(fo.location), fv)
            _chave(fo, "rotation_euler", tuple(fo.rotation_euler), fv)
            _chave(fo, "location", (x + 0.15, y - 0.15, z + 0.3), fv + 14)
            _chave(fo, "rotation_euler", (math.radians(60), math.radians(80), 1), fv + 14)
            _chave(fo, "scale", tuple(fo.scale), fv + 8)
            _chave(fo, "scale", (0, 0, 0), fv + 14)
    pop(_caixa("cal_faixa", (x, y - 0.02, z + 0.115), (0.092, 0.004, 0.022), verm, col), f0 + 4)
    # 50 anos: a vela que acende ("agora e tarde demais" - nunca e)
    f0, f1 = et[4]
    x, y = CX + xs[4], CY - 0.02
    cera = materiais.simples("cera_v", (0.9, 0.86, 0.75), 0.6, sss=0.3)
    vela = _cilindro("vela", (x, y, z + 0.05), 0.017, 0.1, cera, col)
    pop(vela, f0 + 2)
    ch = _esf("chama", (x, y, z + 0.115), (0.008, 0.008, 0.022), m["chama"], col, 12)
    pop(ch, f0 + (f1 - f0) // 2)
    _acender("luz_vela", (x, y - 0.04, z + 0.17), 9, f0 + (f1 - f0) // 2, col)


def criar_judas(col, m, faixas):
    """Sobre a pedra do jardim: o diario que se escreve, a bolsa de onde saem moedas, a lamparina que
    enfraquece, as trinta moedas de prata que se derramam e, no fim, a lamparina que volta a acender."""
    import materiais
    _preparar(col, 4)
    z = MESA_Z
    et = faixas[1:6]
    prata = materiais.simples("prata", (0.85, 0.86, 0.88), 0.25, metal=1.0)
    tinta = materiais.simples("tinta", (0.05, 0.03, 0.02), 0.6)
    # Etapa 1: o diario: um pergaminho com linhas que vao surgindo; a lamparina acende
    f0, f1 = et[0]
    perg = _caixa("diario", (CX - 0.06, CY - 0.02, z + 0.004), (0.24, 0.17, 0.006), m["papel"], col)
    perg.rotation_euler = (0, 0, math.radians(-6))
    pop(perg, f0 + 2)
    for k in range(7):
        ln = _caixa("linha", (CX - 0.06 - 0.01 * (k % 2), CY + 0.06 - k * 0.022, z + 0.008), (0.17 - 0.03 * (k % 3), 0.004, 0.001), tinta, col)
        ln.rotation_euler = perg.rotation_euler
        pop(ln, f0 + 10 + k * 5)
    lamp = _lamparina_barro((CX - 0.24, CY + 0.12, z), f0 + 6, col, m, 7)
    # Etapa 2: a bolsa; algumas moedas escapam (ele tirava um pouco)
    f0, f1 = et[1]
    saco = materiais.simples("bolsa", (0.22, 0.13, 0.07), 0.8, ruido=0.5, escala_ruido=60, bump=0.5)
    bx, by = CX + 0.15, CY + 0.08
    pop(_esf("bolsa", (bx, by, z + 0.05), (0.06, 0.055, 0.055), saco, col), f0 + 2)
    pop(_cone("boca_bolsa", (bx, by, z + 0.115), 0.012, 0.035, 0.04, saco, col), f0 + 4)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.016, minor_radius=0.003, location=(bx, by, z + 0.1))
    pop(_relink(bpy.context.object, col), f0 + 6)
    bpy.context.object.data.materials.append(m["madeira"])
    for k in range(4):
        pop(_cilindro("moeda", (bx - 0.05 - k * 0.02, by - 0.05 - k * 0.01, z + 0.003), 0.012, 0.003, prata, col), f0 + 14 + k * 8)
    # Etapa 3: um reino agora - a lamparina enfraquece
    f0, f1 = et[2]
    _energia(lamp, 7, f0 + 4)
    _energia(lamp, 1.5, f1)
    # Etapa 4: trinta moedas de prata se derramam
    f0, f1 = et[3]
    import random
    rnd = random.Random(30)
    for k in range(30):
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.0, 0.09)
        mo = _cilindro("prata30", (CX + 0.05 + r * math.cos(a), CY - 0.05 + r * math.sin(a) * 0.7, z + 0.003 + 0.004 * (k % 3)),
                       0.013, 0.003, prata, col, (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), 0), 16)
        pop(mo, f0 + 4 + k)
    _acender("brilho_prata", (CX + 0.05, CY - 0.2, z + 0.2), 2.0, f0 + 4, col, (0.7, 0.8, 1.0))
    # Etapa 5: Pedro voltou - a lamparina acende de novo, mais forte
    f0, f1 = et[4]
    _energia(lamp, 1.5, f0 + 6)
    _energia(lamp, 12, f0 + 26)


def criar_socrates(col, m, faixas):
    """Sobre a caixa de som do estudio: cada convidado traz a sua certeza (o ouro, o celular com coracao,
    a balanca) e uma interrogacao dourada a derruba; no fim, a interrogacao vira para a camera e a lamparina acende."""
    import materiais
    _preparar(col, 6)
    z = MESA_Z
    et = faixas[1:6]
    ouro = _ouro()
    gold = _emis("interrog", (1.0, 0.62, 0.18), 2.2)

    def pergunta(x, f, tam=0.12):
        q = _texto("interrogacao", "?", (x, CY + 0.05, z + 0.16), tam, gold, col, ext=0.012)
        pop(q, f)
        return q

    # Etapa 1: o coach - barras de ouro; a pergunta; o ouro some
    f0, f1 = et[0]
    barras = []
    for k in range(5):
        b = _caixa("barra_ouro", (CX - 0.1 + (k % 3) * 0.075 - (k // 3) * 0.04, CY - 0.02, z + 0.015 + (k // 3) * 0.03),
                   (0.07, 0.035, 0.03), ouro, col)
        pop(b, f0 + 2 + k * 3)
        barras.append(b)
    q1 = pergunta(CX - 0.04, f0 + (f1 - f0) // 2)
    for k, b in enumerate(barras):
        _voar(b, f1 - 18 + k, 0.0, 10)
    _voar(q1, f1 - 6, 0.05, 8)
    # Etapa 2: o influencer - celular com coracao; a pergunta; o coracao apaga
    f0, f1 = et[1]
    cel = _caixa("celular", (CX - 0.02, CY + 0.0, z + 0.075), (0.075, 0.01, 0.15),
                 materiais.simples("cel2", (0.02, 0.02, 0.025), 0.25, metal=0.6), col)
    cel.rotation_euler = (math.radians(-12), 0, 0)
    vermelho = _emis("coracao", (1.0, 0.15, 0.3), 4)
    cor = bpy.data.objects.new("coracao", None)
    cor.location = (CX - 0.02, CY - 0.014, z + 0.085)
    col.objects.link(cor)
    for dx in (-0.011, 0.011):
        lb = _esf("coracao_l", (0, 0, 0), (0.014, 0.003, 0.014), vermelho, col, 12)
        lb.parent = cor
        lb.location = (dx, 0, 0.008)
    bico = _caixa("coracao_b", (0, 0, 0), (0.024, 0.004, 0.024), vermelho, col)
    bico.parent = cor
    bico.location, bico.rotation_euler = (0, 0, -0.004), (0, math.radians(45), 0)
    tela = _caixa("tela_soc", (CX - 0.02, CY - 0.0065, z + 0.075), (0.068, 0.001, 0.14), _emis("tela_soc", (0.95, 0.95, 1.0), 1.2), col)
    tela.rotation_euler = cel.rotation_euler
    cor.rotation_euler = (math.radians(-12), 0, 0)
    for o in (cel, tela, cor):
        pop(o, f0 + 3)
    q2 = pergunta(CX + 0.1, f0 + (f1 - f0) // 2)
    for o in (cor, tela, cel):
        _voar(o, f1 - 14, 0.0, 10)
    _voar(q2, f1 - 6, 0.05, 8)
    # Etapa 3: o politico - a balanca da justica, que pende para um lado
    f0, f1 = et[2]
    bx = CX - 0.02
    haste = _cilindro("bal_haste", (bx, CY, z + 0.08), 0.005, 0.16, m["latao"], col)
    base = _cilindro("bal_base", (bx, CY, z + 0.005), 0.04, 0.01, m["latao"], col)
    trave = bpy.data.objects.new("bal_trave", None)
    trave.location = (bx, CY, z + 0.16)
    col.objects.link(trave)
    for o in (haste, base):
        pop(o, f0 + 2)
    pecas = [_cilindro("bal_braco", (0, 0, 0), 0.003, 0.2, m["latao"], col, (0, math.radians(90), 0))]
    for s in (-1, 1):
        pecas.append(_cilindro("bal_prato", (s * 0.095, 0, -0.06), 0.035, 0.004, m["latao"], col))
        pecas.append(_cilindro("bal_fio", (s * 0.095, 0, -0.03), 0.0015, 0.06, m["latao"], col))
    for p in pecas:
        loc = tuple(p.location)
        p.parent = trave
        p.location = loc
    pop(trave, f0 + 4)
    _chave(trave, "rotation_euler", (0, 0, 0), f0 + (f1 - f0) // 2)
    _chave(trave, "rotation_euler", (0, math.radians(18), 0), f0 + (f1 - f0) // 2 + 14)
    q3 = pergunta(CX + 0.13, f0 + (f1 - f0) // 2 + 4)
    for o in (haste, base, trave):
        _voar(o, f1 - 12, 0.0, 10)
    _voar(q3, f1 - 6, 0.05, 8)
    # Etapa 4: "e voce, sabe o que?" - uma interrogacao grande vira para a camera
    f0, f1 = et[3]
    qg = _texto("interrogacao_grande", "?", (CX, CY + 0.02, z + 0.12), 0.22, gold, col, (math.radians(90), 0, math.radians(90)), 0.02)
    pop(qg, f0 + 2)
    _chave(qg, "rotation_euler", (math.radians(90), 0, math.radians(90)), f0 + 8)
    _chave(qg, "rotation_euler", (math.radians(90), 0, 0), f0 + 30)
    # Etapa 5: so sei que nada sei - a interrogacao baixa e a lamparina acende
    f0, f1 = et[4]
    _chave(qg, "location", tuple(qg.location), f0 + 2)
    _chave(qg, "location", (CX + 0.12, CY + 0.06, z + 0.12), f0 + 20)
    _chave(qg, "scale", tuple(qg.scale), f0 + 2)
    _chave(qg, "scale", (0.6, 0.6, 0.6), f0 + 20)
    _lamparina_barro((CX - 0.1, CY - 0.02, z), f0 + 14, col, m, 8)
