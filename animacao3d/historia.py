"""Monta a linha do tempo: acoes do personagem e um movimento de camera por plano.

Um video = um dicionario HISTORIA com o roteiro (um paragrafo por plano) e a lista de planos.
Os planos comecam quando o paragrafo comeca a ser falado (tempos.json da narracao), entao o
corte sempre cai junto com a fala.

Camera de cada plano:
    {"de", "ate", "alvo" ou "alvo_de"/"alvo_ate", "lente", "dof"}   -> travelling / grua / aproximacao
    {"orbita": True, "centro", "raio", "a0", "a1", "h", "lente"}     -> gira em volta (angulos em graus,
                                                                       0 = de frente para o personagem)
Inicio opcional: "inicio": {"pos": (x, y), "rot": graus} (posicao e direcao do personagem no quadro 0).
Acoes: ("andar", t0, t1, y_de, y_ate), ("olhar", t0, t1, (incl_de, giro_de), (incl_ate, giro_ate)), ("girar", t0, t1, graus_de, graus_ate),
       ("erguer", t0, t1, graus_de, graus_ate), ("acenar", t0, t1). t0/t1 = fracao do plano.
"""
import math

import bpy
from mathutils import Vector

FPS = 24

LAMPARINA = {
    "titulo": "A luz mais antiga do mundo",
    "roteiro": [
        "Esta chama é mais antiga do que qualquer livro desta sala.",
        "Na França, na caverna de Lascaux, encontraram uma lamparina de pedra com cerca de dezessete mil anos.",
        "Por milhares de anos, toda leitura depois do pôr do sol dependeu de uma chama assim.",
        "O filósofo Diógenes andava em pleno dia com uma lamparina acesa. Quando perguntavam por quê, respondia: procuro um homem.",
        "*Quem carrega a própria luz não tem medo do escuro.*",
        "E você, o que está procurando? Segue a Lamparina.",
    ],
    "planos": [
        {"desc": "Plano geral. Elias atravessa a biblioteca escura vindo na direcao da camera.",
         "cam": {"de": (0, -5.0, 1.65), "ate": (0, -4.0, 1.45), "alvo_de": (0, 0.8, 1.3), "alvo_ate": (0, 0, 1.3), "lente": 32},
         "acoes": [("andar", 0, 1, 1.6, 0.0)]},
        {"desc": "Close na lamparina; a camera gira devagar em volta da chama.",
         "cam": {"orbita": True, "centro": (0.04, -0.37, 1.2), "raio": 0.8, "a0": -45, "a1": 25, "h": 1.32, "lente": 55, "dof": True},
         "acoes": []},
        {"desc": "Elias se vira para as estantes e ergue a lamparina; a camera sobe como uma grua.",
         "cam": {"de": (1.9, -1.8, 0.7), "ate": (1.9, -1.8, 2.2), "alvo_de": (0, 0.6, 1.3), "alvo_ate": (0, 1.8, 2.0), "lente": 28},
         "acoes": [("girar", 0, 0.4, 0, 165), ("erguer", 0.3, 0.7, 0, -50)]},
        {"desc": "Elias volta o rosto para quem assiste; aproximacao lenta ate o close.",
         "cam": {"de": (0.25, -2.6, 1.7), "ate": (0.04, -1.1, 1.68), "alvo": (0, -0.06, 1.66), "lente": 50, "dof": True},
         "acoes": [("girar", 0, 0.3, 165, 360), ("erguer", 0, 0.3, -50, 0)]},
        {"desc": "Contra-plongee: Elias ergue a lamparina bem alto; a camera gira por baixo.",
         "cam": {"orbita": True, "centro": (0, 0, 1.55), "raio": 2.3, "a0": -55, "a1": -100, "h": 0.45, "lente": 26},
         "acoes": [("erguer", 0.1, 0.45, 0, -80)]},
        {"desc": "Final: Elias abaixa a lamparina, olha para a camera e acena com a cabeca.",
         "cam": {"de": (0, -3.3, 1.5), "ate": (0, -2.5, 1.55), "alvo": (0, 0, 1.45), "lente": 40},
         "acoes": [("erguer", 0, 0.3, -80, 0), ("acenar", 0.45, 0.8)]},
    ],
}


def tempos_dos_planos(tempos, total):
    """[(quadro_inicial, quadro_final)] de cada plano, a partir do inicio de cada paragrafo."""
    inicio = {}
    for a, _, _, par in tempos:
        inicio.setdefault(par, a)
    marcas = [0.0] + [max(0.0, inicio[p] - 0.15) for p in sorted(inicio)[1:]] + [total]
    return [(round(a * FPS), round(b * FPS) - 1) for a, b in zip(marcas, marcas[1:])]


def _chave(obj, prop, valor, quadro):
    setattr(obj, prop, valor)
    obj.keyframe_insert(prop, frame=quadro)


def _suave(t):
    return t * t * (3 - 2 * t)


def aplicar_acoes(p, planos, faixas, inicio=None):
    raiz, bracos, cab = p["raiz"], p["bracos"], p["cabeca"]
    ini = inicio or {"pos": (0, 1.6), "rot": 0}
    _chave(raiz, "location", (*ini["pos"], 0), 0)
    _chave(raiz, "rotation_euler", (0, 0, math.radians(ini["rot"])), 0)
    _chave(bracos, "rotation_euler", (0, 0, 0), 0)
    _chave(cab, "rotation_euler", (0, 0, 0), 0)
    for plano, (q0, q1) in zip(planos, faixas):
        dur = q1 - q0
        for acao in plano["acoes"]:
            nome, t0, t1 = acao[:3]
            f0, f1 = q0 + round(t0 * dur), q0 + round(t1 * dur)
            if nome == "andar":
                y0, y1 = acao[3], acao[4]
                passo = 12
                for f in range(f0, f1 + 1, 3):
                    u = (f - f0) / max(1, f1 - f0)
                    y = y0 + (y1 - y0) * u
                    fase = math.sin(math.pi * (f - f0) / passo)
                    _chave(raiz, "location", (0, y, 0.025 * abs(fase)), f)
                    _chave(raiz, "rotation_euler", (0, 0.025 * fase, 0), f)
                _chave(raiz, "location", (0, y1, 0), f1)
                _chave(raiz, "rotation_euler", (0, 0, 0), f1)
            elif nome == "girar":
                a, b = acao[3], acao[4]
                rz0 = math.radians(a)
                _chave(raiz, "rotation_euler", (0, 0, rz0), f0)
                _chave(raiz, "rotation_euler", (0, 0, math.radians(b)), f1)
            elif nome == "erguer":
                _chave(bracos, "rotation_euler", (math.radians(acao[3]), 0, 0), f0)
                _chave(bracos, "rotation_euler", (math.radians(acao[4]), 0, 0), f1)
            elif nome == "olhar":
                (i0, g0), (i1, g1) = acao[3], acao[4]
                _chave(cab, "rotation_euler", (math.radians(i0), 0, math.radians(g0)), f0)
                _chave(cab, "rotation_euler", (math.radians(i1), 0, math.radians(g1)), f1)
            elif nome == "acenar":
                meio = (f0 + f1) // 2
                _chave(cab, "rotation_euler", (0, 0, 0), f0)
                _chave(cab, "rotation_euler", (math.radians(14), 0, 0), meio)
                _chave(cab, "rotation_euler", (0, 0, 0), f1)


def _camera(nome, lente, col):
    d = bpy.data.cameras.new(nome)
    d.lens = lente
    d.sensor_width = 36
    c = bpy.data.objects.new(nome, d)
    col.objects.link(c)
    alvo = bpy.data.objects.new(nome + "_alvo", None)
    col.objects.link(alvo)
    tr = c.constraints.new("TRACK_TO")
    tr.target = alvo
    tr.track_axis, tr.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    return c, alvo


def criar_cameras(planos, faixas, col, cena):
    cams = []
    for i, (plano, (q0, q1)) in enumerate(zip(planos, faixas), 1):
        cfg = plano["cam"]
        cam, alvo = _camera(f"cam{i}", cfg.get("lente", 35), col)
        if cfg.get("orbita"):
            cx, cy, cz = cfg["centro"]
            alvo.location = (cx, cy, cz)
            for f in range(q0, q1 + 1, 3):
                u = _suave((f - q0) / max(1, q1 - q0))
                a = math.radians(cfg["a0"] + (cfg["a1"] - cfg["a0"]) * u)
                _chave(cam, "location", (cx + cfg["raio"] * math.sin(a), cy - cfg["raio"] * math.cos(a), cfg["h"]), f)
        else:
            _chave(cam, "location", cfg["de"], q0)
            _chave(cam, "location", cfg["ate"], q1)
            if "alvo" in cfg:
                alvo.location = cfg["alvo"]
            else:
                _chave(alvo, "location", cfg["alvo_de"], q0)
                _chave(alvo, "location", cfg["alvo_ate"], q1)
        if cfg.get("dof"):
            cam.data.dof.use_dof = True
            cam.data.dof.focus_object = alvo
            cam.data.dof.aperture_fstop = 2.2
        m = cena.timeline_markers.new(f"plano{i}", frame=q0)
        m.camera = cam
        cams.append(cam)
    cena.camera = cams[0]
    return cams


CODEX = {
    "titulo": "O caderno de 30 milhoes",
    "inicio": {"pos": (0.85, -0.4), "rot": 90},
    "roteiro": [
        "Existe um caderno que vale mais do que esta biblioteca inteira.",
        "No começo do século dezesseis, Leonardo da Vinci encheu suas páginas com desenhos sobre a água, a Lua e as rochas.",
        "E escreveu quase tudo ao contrário, da direita para a esquerda. Para ler com facilidade, só com um espelho.",
        "Em 1994, Bill Gates comprou esse caderno, o Codex Leicester, por mais de trinta milhões de dólares.",
        "*Uma ideia anotada à mão pode valer mais que ouro.*",
        "E você, anota as suas ideias? Segue a Lamparina.",
    ],
    "planos": [
        {"desc": "Plano geral. Elias esta de pe diante da mesa, iluminando os livros.",
         "cam": {"de": (-1.3, -3.7, 1.75), "ate": (-0.5, -2.9, 1.55), "alvo": (1.3, -0.4, 1.1), "lente": 30},
         "acoes": [("olhar", 0, 1, (10, 0), (20, 0))]},
        {"desc": "Close no livro aberto sobre a mesa; Elias aproxima a lamparina das paginas.",
         "cam": {"de": (1.55, -1.2, 1.4), "ate": (1.75, -0.9, 1.2), "alvo": (1.9, -0.5, 0.83), "lente": 45, "dof": True},
         "acoes": [("erguer", 0, 0.5, 0, 18)]},
        {"desc": "A camera gira em volta de Elias e da mesa, mostrando a biblioteca.",
         "cam": {"orbita": True, "centro": (1.2, -0.4, 1.2), "raio": 2.1, "a0": -25, "a1": 30, "h": 1.6, "lente": 30},
         "acoes": [("erguer", 0, 0.3, 18, 0), ("olhar", 0.2, 0.8, (20, 0), (5, 25))]},
        {"desc": "Elias se vira para quem assiste; aproximacao lenta ate o close.",
         "cam": {"de": (0.95, -2.7, 1.7), "ate": (0.87, -1.5, 1.68), "alvo": (0.85, -0.46, 1.66), "lente": 50, "dof": True},
         "acoes": [("olhar", 0, 0.2, (5, 25), (0, 0)), ("girar", 0, 0.35, 90, 0)]},
        {"desc": "Contra-plongee: Elias ergue a lamparina bem alto; a camera gira por baixo.",
         "cam": {"orbita": True, "centro": (0.85, -0.4, 1.55), "raio": 2.2, "a0": -40, "a1": -80, "h": 0.45, "lente": 26},
         "acoes": [("erguer", 0.1, 0.45, 0, -80)]},
        {"desc": "Final: Elias abaixa a lamparina, olha para a camera e acena com a cabeca.",
         "cam": {"de": (0.85, -3.3, 1.5), "ate": (0.85, -2.5, 1.55), "alvo": (0.85, -0.4, 1.45), "lente": 40},
         "acoes": [("erguer", 0, 0.3, -80, 0), ("acenar", 0.45, 0.8)]},
    ],
}

HISTORIAS = {"lamparina-mais-antiga": LAMPARINA, "codex-leicester": CODEX}
