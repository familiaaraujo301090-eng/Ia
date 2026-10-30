"""Materiais procedurais (sem texturas externas): la, pele, couro, latao, pedra, madeira, chama."""
import bpy


def _base(nome):
    m = bpy.data.materials.get(nome)
    if m:
        return m, None
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    return m, m.node_tree


def simples(nome, cor, rugosidade=0.7, metal=0.0, sss=0.0, ruido=0.0, escala_ruido=40.0, bump=0.0):
    """Principled com variacao de cor por ruido e relevo opcional (la, pele, pedra...)."""
    m, nt = _base(nome)
    if nt is None:
        return m
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = rugosidade
    p.inputs["Metallic"].default_value = metal
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.9, 0.4, 0.25)
    if ruido or bump:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = escala_ruido
        tex.inputs["Detail"].default_value = 8
        if ruido:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.inputs["Factor"].default_value = ruido
            mix.inputs[6].default_value = (*cor, 1)
            mix.inputs[7].default_value = (cor[0] * 0.55, cor[1] * 0.55, cor[2] * 0.55, 1)
            nt.links.new(tex.outputs["Fac"], mix.inputs["Factor"])
            nt.links.new(mix.outputs[2], p.inputs["Base Color"])
        else:
            p.inputs["Base Color"].default_value = (*cor, 1)
        if bump:
            b = nt.nodes.new("ShaderNodeBump")
            b.inputs["Strength"].default_value = bump
            nt.links.new(tex.outputs["Fac"], b.inputs["Height"])
            nt.links.new(b.outputs["Normal"], p.inputs["Normal"])
    else:
        p.inputs["Base Color"].default_value = (*cor, 1)
    return m


def emissao(nome, cor, forca):
    m, nt = _base(nome)
    if nt is None:
        return m
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*cor, 1)
    e.inputs["Strength"].default_value = forca
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def pagina(nome="pagina"):
    """Papel com linhas de escrita (faixas finas de tinta) e manchas de desenho."""
    m, nt = _base(nome)
    if nt is None:
        return m
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.9
    ondas = nt.nodes.new("ShaderNodeTexWave")
    ondas.bands_direction = "Y"
    ondas.inputs["Scale"].default_value = 12
    ondas.inputs["Distortion"].default_value = 2
    ondas.inputs["Detail"].default_value = 2
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].position = 0.82
    rampa.color_ramp.elements[0].color = (0.70, 0.60, 0.42, 1)
    rampa.color_ramp.elements[1].position = 0.9
    rampa.color_ramp.elements[1].color = (0.18, 0.12, 0.08, 1)
    nt.links.new(ondas.outputs["Fac"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], p.inputs["Base Color"])
    return m


def paleta():
    return {
        "la": simples("la_marrom", (0.075, 0.04, 0.022), 0.95, ruido=0.35, escala_ruido=120, bump=0.25),
        "pele": simples("pele", (0.55, 0.30, 0.20), 0.55, sss=0.15, ruido=0.15, escala_ruido=25),
        "barba": simples("barba", (0.86, 0.85, 0.83), 0.8, ruido=0.4, escala_ruido=300, bump=0.6),
        "couro": simples("couro", (0.20, 0.13, 0.08), 0.6, ruido=0.3, escala_ruido=30, bump=0.2),
        "latao": simples("latao", (0.75, 0.52, 0.22), 0.3, metal=1.0, ruido=0.2, escala_ruido=20),
        "olho": simples("olho", (0.03, 0.025, 0.02), 0.2),
        "corda": simples("corda", (0.12, 0.07, 0.04), 0.9, bump=0.4, escala_ruido=200),
        "chama": emissao("chama", (1.0, 0.55, 0.15), 10),
        "pedra": simples("pedra", (0.22, 0.20, 0.18), 0.9, ruido=0.5, escala_ruido=6, bump=0.4),
        "madeira": simples("madeira", (0.13, 0.07, 0.035), 0.7, ruido=0.45, escala_ruido=12, bump=0.15),
        "pagina": pagina(),
        "papel": simples("papel", (0.70, 0.60, 0.42), 0.9, ruido=0.2, escala_ruido=15),
        "capa1": simples("capa1", (0.30, 0.06, 0.04), 0.7, ruido=0.3, escala_ruido=20),
        "capa2": simples("capa2", (0.07, 0.12, 0.08), 0.7, ruido=0.3, escala_ruido=20),
        "capa3": simples("capa3", (0.25, 0.17, 0.08), 0.7, ruido=0.3, escala_ruido=20),
    }
