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
