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
