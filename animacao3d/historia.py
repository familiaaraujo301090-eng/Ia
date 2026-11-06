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


def _camera_tremida(cam, alvo, cfg, q0, q1, semente):
    """Camera na mao: o movimento normal do plano mais um tremor de somas de senos (amplitude em metros)."""
    amp = cfg["tremor"]
    fases = [semente * 1.7 + k * 2.3 for k in range(6)]
    for f in list(range(q0, q1 + 1, 2)) + [q1]:
        u = _suave((f - q0) / max(1, q1 - q0))
        t = f / FPS
        if cfg.get("orbita"):
            cx, cy, cz = cfg["centro"]
            a = math.radians(cfg["a0"] + (cfg["a1"] - cfg["a0"]) * u)
            pos = Vector((cx + cfg["raio"] * math.sin(a), cy - cfg["raio"] * math.cos(a), cfg["h"]))
            mira = Vector((cx, cy, cz))
        else:
            pos = Vector(cfg["de"]).lerp(Vector(cfg["ate"]), u)
            mira = Vector(cfg["alvo"]) if "alvo" in cfg else Vector(cfg["alvo_de"]).lerp(Vector(cfg["alvo_ate"]), u)
        tre = Vector([math.sin(t * (5.1 + k) + fases[k]) + 0.5 * math.sin(t * (11.3 + 2 * k) + fases[k + 3])
                      for k in range(3)])
        _chave(cam, "location", pos + tre * amp, f)
        _chave(alvo, "location", mira + Vector((tre.y, tre.z, tre.x)) * amp * 1.5, f)


def criar_cameras(planos, faixas, col, cena):
    cams = []
    for i, (plano, (q0, q1)) in enumerate(zip(planos, faixas), 1):
        cfg = plano["cam"]
        cam, alvo = _camera(f"cam{i}", cfg.get("lente", 35), col)
        if cfg.get("no_barco") and "barco" in bpy.data.objects:
            cam.parent = alvo.parent = bpy.data.objects["barco"]  # camera presa ao barco: o horizonte balanca
        if cfg.get("tremor"):
            _camera_tremida(cam, alvo, cfg, q0, q1, i)
        elif cfg.get("orbita"):
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

LIVRO_MEDIEVAL = {
    "titulo": "Como se fazia um livro",
    "inicio": {"pos": (0.85, -0.4), "rot": 90},
    "extra": "criar_livro_medieval",  # funcao de processo.py que monta o objeto passo a passo
    "passos": ["PERGAMINHO", "TINTA", "PENA", "COPIA", "ENCADERNACAO"],  # planos 2 a 6
    "roteiro": [
        "Para fazer um único livro na Idade Média, eram precisas as peles de centenas de animais. Veja o processo.",
        "Passo um: a pele era lavada, raspada e esticada num bastidor até virar pergaminho.",
        "Passo dois: a tinta vinha de galhas de carvalho, misturadas com ferro.",
        "Passo três: uma pena de ganso, cortada na ponta, virava a caneta.",
        "Passo quatro: um monge copiava cada letra à mão, durante meses.",
        "Passo cinco: as folhas eram costuradas e presas entre tábuas cobertas de couro.",
        "*Cada livro desta sala custou meses de trabalho de alguém.*",
        "Qual passo você não aguentaria fazer? Segue a Lamparina.",
    ],
    "planos": [
        {"desc": "Gancho: plano geral, Elias diante da mesa vazia.",
         "cam": {"de": (-1.3, -3.7, 1.75), "ate": (-0.5, -2.9, 1.55), "alvo": (1.3, -0.4, 1.0), "lente": 30},
         "acoes": [("olhar", 0, 1, (10, 0), (22, 0))]},
        {"desc": "Passo 1: o bastidor surge e o pergaminho se desenrola.",
         "cam": {"de": (1.55, -1.35, 1.5), "ate": (1.55, -1.1, 1.32), "alvo": (1.58, -0.45, 0.82), "lente": 38, "dof": True},
         "acoes": []},
        {"desc": "Passo 2: tinteiro e galhas de carvalho aparecem; a camera gira.",
         "cam": {"orbita": True, "centro": (1.95, -0.6, 0.86), "raio": 0.7, "a0": -25, "a1": 25, "h": 1.15, "lente": 45, "dof": True},
         "acoes": []},
        {"desc": "Passo 3: a pena de ganso surge e desce ate o tinteiro.",
         "cam": {"de": (2.4, -1.05, 1.12), "ate": (2.25, -0.95, 1.02), "alvo": (1.95, -0.64, 0.95), "lente": 50, "dof": True},
         "acoes": []},
        {"desc": "Passo 4: as linhas de texto vao sendo escritas no pergaminho.",
         "cam": {"de": (1.58, -0.95, 1.65), "ate": (1.58, -0.8, 1.38), "alvo": (1.58, -0.45, 0.83), "lente": 40},
         "acoes": []},
        {"desc": "Passo 5: o miolo cresce e a capa de couro fecha o livro; a camera gira.",
         "cam": {"orbita": True, "centro": (1.55, -0.45, 0.86), "raio": 0.85, "a0": 30, "a1": -30, "h": 1.2, "lente": 40, "dof": True},
         "acoes": []},
        {"desc": "Elias se vira para quem assiste; aproximacao ate o close.",
         "cam": {"de": (0.95, -2.7, 1.7), "ate": (0.87, -1.5, 1.68), "alvo": (0.85, -0.46, 1.66), "lente": 50, "dof": True},
         "acoes": [("olhar", 0, 0.2, (22, 0), (0, 0)), ("girar", 0, 0.35, 90, 0)]},
        {"desc": "Final: Elias olha para a camera e acena com a cabeca.",
         "cam": {"de": (0.85, -3.3, 1.5), "ate": (0.85, -2.5, 1.55), "alvo": (0.85, -0.4, 1.45), "lente": 40},
         "acoes": [("acenar", 0.3, 0.7)]},
    ],
}

VIDA_PARADA = {
    "titulo": "Sua vida nao esta parada",
    "inicio": {"pos": (0.85, -0.4), "rot": 90},
    "extra": "criar_semente",
    # Jornada: promessa no gancho, os obstaculos dia a dia e o resultado no fim.
    "contador": [("DIA 1", "ESCURO"), ("DIA 12", "PESO"), ("DIA 30", "NINGUÉM VÊ"), ("DIA 60", "PRESSÃO"),
                 ("DIA 90", "A FLOR")],
    "roteiro": [
        "Sua vida parece parada? Fica até o fim, porque eu vou te mostrar o que acontece onde ninguém vê.",
        "Dia um. A semente cai no escuro. Sozinha. Ninguém vê.",
        "Dia doze. O peso da terra em cima. Ela racha por dentro, e parece que está morrendo.",
        "Dia trinta. Lá em cima, nada mudou. Mas aqui embaixo, as raízes já se espalham.",
        "Dia sessenta. A terra resiste. E ela empurra mesmo assim.",
        "Dia noventa. E aquilo que todo mundo chama de sorte, finalmente aparece.",
        "*Tudo tem o seu tempo determinado*, diz Eclesiastes. Você não está parado. Está sendo preparado.",
        "Não arranque a semente só porque ainda não viu a flor. Segue a Lamparina.",
    ],
    "planos": [
        {"desc": "Gancho: Elias olha para a caixa de terra sobre a mesa; em cima, nada.",
         "cam": {"de": (-1.3, -3.7, 1.75), "ate": (-0.5, -2.9, 1.55), "alvo": (1.4, -0.45, 1.0), "lente": 30},
         "acoes": [("olhar", 0, 1, (10, 0), (22, 0))]},
        {"desc": "Dia 1: a semente cai e afunda no escuro do corte de terra.",
         "cam": {"de": (1.6, -1.25, 1.02), "ate": (1.6, -1.0, 0.99), "alvo": (1.6, -0.52, 0.98), "lente": 50, "dof": True},
         "acoes": []},
        {"desc": "Dia 12: a semente treme, racha e solta a primeira raiz.",
         "cam": {"de": (1.63, -0.86, 0.98), "ate": (1.61, -0.74, 0.97), "alvo": (1.6, -0.52, 0.97), "lente": 60, "dof": True},
         "acoes": []},
        {"desc": "Dia 30: as raizes se espalham embaixo enquanto a superficie segue vazia; camera gira.",
         "cam": {"orbita": True, "centro": (1.6, -0.52, 0.93), "raio": 0.75, "a0": -20, "a1": 20, "h": 0.97, "lente": 45, "dof": True},
         "acoes": []},
        {"desc": "Dia 60: o broto sobe e empurra a terra ate romper a superficie.",
         "cam": {"de": (1.6, -0.95, 0.97), "ate": (1.6, -0.88, 1.1), "alvo": (1.6, -0.5, 1.04), "lente": 50, "dof": True},
         "acoes": []},
        {"desc": "Dia 90: o caule cresce, as folhas abrem e a flor nasce; grua subindo.",
         "cam": {"de": (1.6, -1.0, 1.02), "ate": (1.6, -1.1, 1.35), "alvo": (1.6, -0.5, 1.15), "lente": 40, "dof": True},
         "acoes": []},
        {"desc": "Elias se vira para quem assiste; aproximacao ate o close.",
         "cam": {"de": (0.95, -2.7, 1.7), "ate": (0.87, -1.5, 1.68), "alvo": (0.85, -0.46, 1.66), "lente": 50, "dof": True},
         "acoes": [("olhar", 0, 0.2, (22, 0), (0, 0)), ("girar", 0, 0.35, 90, 0)]},
        {"desc": "Final: Elias acena; a flor ao lado, na mesa.",
         "cam": {"de": (1.0, -3.3, 1.5), "ate": (1.05, -2.5, 1.5), "alvo": (1.15, -0.4, 1.3), "lente": 38},
         "acoes": [("acenar", 0.3, 0.7)]},
    ],
}

def planos_jornada(cz, descs):
    """Planos padrao do formato jornada: gancho geral, 5 etapas no objeto da mesa e o fecho com Elias."""
    c = (1.6, -0.45, cz)
    cams = [
        {"de": (-1.3, -3.7, 1.75), "ate": (-0.5, -2.9, 1.55), "alvo": (1.4, -0.45, 1.0), "lente": 30},
        {"de": (1.6, -1.4, cz + 0.28), "ate": (1.6, -1.12, cz + 0.16), "alvo": c, "lente": 45, "dof": True},
        {"orbita": True, "centro": c, "raio": 0.8, "a0": -30, "a1": 0, "h": cz + 0.12, "lente": 45, "dof": True},
        {"de": (1.98, -1.02, cz + 0.06), "ate": (1.86, -0.9, cz + 0.03), "alvo": c, "lente": 55, "dof": True},
        {"orbita": True, "centro": c, "raio": 0.75, "a0": 25, "a1": -10, "h": cz + 0.2, "lente": 45, "dof": True},
        {"de": (1.6, -1.0, cz + 0.02), "ate": (1.6, -1.2, cz + 0.36), "alvo": (1.6, -0.45, cz + 0.04), "lente": 40,
         "dof": True},
        {"de": (0.95, -2.7, 1.7), "ate": (0.87, -1.5, 1.68), "alvo": (0.85, -0.46, 1.66), "lente": 50, "dof": True},
        {"de": (1.0, -3.3, 1.5), "ate": (1.05, -2.5, 1.5), "alvo": (1.15, -0.4, 1.3), "lente": 38},
    ]
    acoes = [[("olhar", 0, 1, (10, 0), (22, 0))], [], [], [], [], [],
             [("olhar", 0, 0.2, (22, 0), (0, 0)), ("girar", 0, 0.35, 90, 0)], [("acenar", 0.3, 0.7)]]
    return [{"desc": d, "cam": cam, "acoes": a} for d, cam, a in zip(descs, cams, acoes)]


def _jornada(titulo, extra, cz, contador, roteiro, descs):
    return {"titulo": titulo, "inicio": {"pos": (0.85, -0.4), "rot": 90}, "extra": extra, "contador": contador,
            "roteiro": roteiro, "planos": planos_jornada(cz, descs)}


def deslocar(hist, centro):
    """Leva a jornada para outro ponto do cenario (sem mesa): objetos, cameras e Elias andam juntos.
    centro = (x, y, z) onde ficam os objetos; o padrao e a mesa (1.6, -0.45, 0.81)."""
    dx, dy = centro[0] - 1.6, centro[1] + 0.45
    mv = lambda v: (v[0] + dx, v[1] + dy, v[2])
    for pl in hist["planos"]:
        cam = pl["cam"]
        for k in ("de", "ate", "alvo", "alvo_de", "alvo_ate", "centro"):
            if k in cam:
                cam[k] = mv(cam[k])
    x, y = hist["inicio"]["pos"]
    hist["inicio"] = dict(hist["inicio"], pos=(x + dx, y + dy))
    hist["centro"] = centro
    return hist


_FECHO = ["Elias se vira para quem assiste; aproximacao ate o close.", "Final: Elias acena ao lado da mesa."]

KINTSUGI = _jornada(
    "O vaso de ouro", "criar_kintsugi", 0.94,
    [("ETAPA 1/5", "A QUEDA"), ("ETAPA 2/5", "OS CACOS"), ("ETAPA 3/5", "A COLA"), ("ETAPA 4/5", "O OURO"),
     ("ETAPA 5/5", "MAIS FORTE")],
    ["No Japão, quando um vaso quebra, ele não vai para o lixo. Ele passa a valer mais. Veja como.",
     "Primeiro, a queda. Aquilo que parecia inteiro se parte em pedaços.",
     "Depois, os cacos. Ninguém escolhe ficar assim. Mas ninguém joga fora.",
     "Então, cada pedaço é colado de volta. Com paciência. Um por um.",
     "E as rachaduras não são escondidas. Elas são preenchidas com ouro.",
     "No fim, o vaso vale mais do que antes de quebrar. Isso se chama kintsugi.",
     "*As suas cicatrizes não te diminuem.* Elas mostram por onde a graça passou.",
     "Comenta: qual rachadura virou ouro na sua vida? Segue a Lamparina."],
    ["Gancho: Elias diante do vaso azul sobre a mesa.", "Etapa 1: o vaso aparece e se parte em seis cacos.",
     "Etapa 2: os cacos espalhados; a camera gira.", "Etapa 3: os cacos voltam ao lugar, um por um.",
     "Etapa 4: as emendas de ouro crescem pelas rachaduras.", "Etapa 5: o vaso remendado gira; grua subindo."] + _FECHO)

OURO_FOGO = _jornada(
    "O ouro no fogo", "criar_ouro_fogo", 0.95,
    [("ETAPA 1/5", "O MINÉRIO"), ("ETAPA 2/5", "O FOGO"), ("ETAPA 3/5", "A SUJEIRA SOBE"),
     ("ETAPA 4/5", "A ESPERA"), ("ETAPA 5/5", "O REFLEXO")],
    ["Sabe por que o ouro precisa passar pelo fogo? Fica até o fim, porque o final explica a sua vida.",
     "Primeiro, o minério. Ouro misturado com pedra. Ninguém vê o valor.",
     "Depois, o fogo. Mais de mil graus. Parece que vai destruir tudo.",
     "Mas é no calor que a sujeira sobe para a superfície.",
     "O ourives espera, e tira a impureza. De novo. E de novo.",
     "Conta-se que ele só para quando consegue ver o próprio rosto refletido no ouro.",
     "A Bíblia diz que a sua fé é provada *como o ouro no fogo*. O fogo não é castigo. É processo.",
     "Em que fase do fogo você está? Comenta. Segue a Lamparina."],
    ["Gancho: Elias diante da fornalha apagada.", "Etapa 1: as pedras de minerio caem no cadinho.",
     "Etapa 2: o fogo acende em volta do cadinho; a camera gira.",
     "Etapa 3: o minerio derrete e as impurezas escuras sobem.",
     "Etapa 4: as impurezas sao retiradas uma a uma.", "Etapa 5: o fogo apaga e o ouro vira espelho."] + _FECHO)

DIAMANTE = _jornada(
    "O diamante", "criar_diamante", 0.92,
    [("ETAPA 1/5", "CARBONO"), ("ETAPA 2/5", "PRESSÃO"), ("ETAPA 3/5", "CALOR"), ("ETAPA 4/5", "TEMPO"),
     ("ETAPA 5/5", "BRILHO")],
    ["O diamante e o carvão são feitos da mesma coisa. A diferença é o que um deles enfrentou.",
     "Primeiro, só carbono. Escuro, comum, sem valor nenhum.",
     "Depois vem a pressão. Toneladas em cima dele, sem aviso.",
     "Junto vem o calor. Mais de mil graus, lá no fundo da terra.",
     "E o pior: o tempo. Ninguém vê, ninguém aplaude. Por muito, muito tempo.",
     "Até que um dia ele é tirado do escuro. E brilha.",
     "*A pressão que você sente hoje* pode ser o que está te formando.",
     "Se você está debaixo de pressão, comenta: eu não desisto. Segue a Lamparina."],
    ["Gancho: Elias diante da laje de pedra.", "Etapa 1: o pedaco de carbono aparece e gira.",
     "Etapa 2: o bloco de pedra desce e esmaga; a camera gira.", "Etapa 3: o calor acende o carbono em vermelho.",
     "Etapa 4: o bloco treme e o carbono encolhe com o tempo.",
     "Etapa 5: o bloco sobe e o diamante aparece girando."] + _FECHO)

AMPULHETA = _jornada(
    "Quatro mil semanas", "criar_ampulheta", 0.99,
    [("SEMANA 1", "NASCER"), ("SEMANA 1.000", "SONHAR"), ("SEMANA 2.000", "CORRER"), ("SEMANA 3.000", "ADIAR"),
     ("SEMANA 4.000", "O QUE FICA")],
    ["Se você viver até os oitenta anos, vai ter umas quatro mil semanas. Olha quantas já passaram.",
     "Semana um. Você nasce, e a areia começa a cair.",
     "Semana mil. Você tem uns dezenove anos e acha que o tempo não acaba.",
     "Semana dois mil. Trabalho, contas, pressa. A areia cai mais rápido do que parece.",
     "Semana três mil. Você começa a contar tudo o que deixou para depois.",
     "Semana quatro mil. A areia acaba, e só fica o que você fez com ela.",
     "Sêneca escreveu: *não é que temos pouco tempo. É que perdemos muito dele.*",
     "Em que semana você está? Comenta. E segue a Lamparina."],
    ["Gancho: Elias diante da ampulheta cheia.", "Semana 1: o primeiro fio de areia cai.",
     "Semana 1.000: a areia de baixo cresce; a camera gira.", "Semana 2.000: metade da areia ja passou.",
     "Semana 3.000: quase nada em cima.", "Semana 4.000: o ultimo grao cai."] + _FECHO)

ESCULTURA = _jornada(
    "O anjo no marmore", "criar_escultura", 0.98,
    [("ETAPA 1/5", "O BLOCO"), ("ETAPA 2/5", "O PRIMEIRO GOLPE"), ("ETAPA 3/5", "MIL GOLPES"),
     ("ETAPA 4/5", "A FORMA"), ("ETAPA 5/5", "O ANJO")],
    ["Conta-se que Michelangelo olhou para um bloco de mármore e disse: tem um anjo aí dentro. Veja como ele saiu.",
     "Primeiro, o bloco. Pesado, bruto. Ninguém vê nada além de pedra.",
     "Então vem o primeiro golpe. E dói. Cai um pedaço que você achava que era seu.",
     "Depois, mil golpes. Cada um tira alguma coisa que estava sobrando.",
     "Aos poucos aparece uma forma. Ainda não dá para entender, mas já não é só pedra.",
     "E no fim aparece o que estava escondido ali desde o começo.",
     "*Talvez o que você está perdendo* seja só o excesso que esconde quem você é.",
     "O que Deus está tirando de você agora? Comenta. Segue a Lamparina."],
    ["Gancho: Elias diante do bloco de marmore.", "Etapa 1: o bloco bruto, inteiro.",
     "Etapa 2: os primeiros pedacos caem; a camera gira.", "Etapa 3: dezenas de pedacos caem.",
     "Etapa 4: a silhueta do anjo aparece.", "Etapa 5: os ultimos pedacos caem e o anjo se ilumina."] + _FECHO)

TEMPESTADE = {
    "titulo": "A tempestade",
    "cenario": "mar",  # modulo do cenario (mar.py): barco na tempestade que se acalma
    "calma": 7,  # plano em que o vento para
    "vol_trilha": 0.22,  # a trilha leva a chuva e os trovoes, entao vai mais alta
    "raios_no_corte": [1, 4, 5],  # planos (a partir de 0) que comecam com relampago
    "inicio": {"pos": (0, 0.1), "rot": 0},
    "roteiro": [
        "Se você está no meio de uma tempestade agora, não pula esse vídeo.",
        "Era noite no mar da Galileia. E o vento virou de repente.",
        "As ondas cobriam o barco. Pescadores experientes achavam que iam morrer.",
        "E Jesus? Estava dormindo. Na popa. Com a cabeça num travesseiro.",
        "Eles gritaram: Mestre, não te importa que a gente morra?",
        "Ele se levantou e disse ao mar: *Silêncio. Aquieta-te.*",
        "E o vento parou. E veio uma grande calma.",
        "Repara: ele não tirou ninguém da tempestade. *Ele estava no barco com eles.*",
        "*A tempestade não decide como a sua história termina.*",
        "Qual tempestade você está enfrentando hoje? Comenta. Segue a Lamparina.",
    ],
    "planos": [
        {"desc": "Gancho: relampago; camera na mao avanca ate Elias de pe no barco que joga.",
         "cam": {"de": (0.7, -3.4, 1.3), "ate": (0.15, -1.7, 1.6), "alvo": (0, 0.1, 1.55), "lente": 35,
                 "tremor": 0.035},
         "acoes": []},
        {"desc": "Plano aereo: o barco pequeno no meio das ondas; a camera desce; raio no ceu.",
         "cam": {"de": (7, -10.5, 7), "ate": (4.2, -6.2, 2.6), "alvo_de": (0, 2, 0), "alvo_ate": (0, 0, 0.6),
                 "lente": 24, "tremor": 0.03},
         "acoes": []},
        {"desc": "Rente a agua: as ondas passam na frente da camera; o barco arfa.",
         "cam": {"de": (-4.6, -3.0, 0.2), "ate": (-3.6, 1.6, 0.45), "alvo_de": (0, -0.6, 0.7),
                 "alvo_ate": (0, 1.0, 0.9), "lente": 28, "tremor": 0.06},
         "acoes": [("olhar", 0, 1, (0, 0), (-10, -30))]},
        {"desc": "Na popa, o travesseiro; camera presa ao barco, o horizonte balanca.",
         "cam": {"de": (0.25, -0.85, 1.35), "ate": (0.15, -1.05, 1.15), "alvo": (0, -1.75, 0.34), "lente": 40,
                 "dof": True, "no_barco": True},
         "acoes": [("olhar", 0, 0.3, (-10, -30), (0, 0))]},
        {"desc": "Grito: camera gira rapida em volta de Elias, tremendo; ele olha para o ceu.",
         "cam": {"orbita": True, "centro": (0, 0.1, 1.45), "raio": 2.5, "a0": 45, "a1": -25, "h": 1.15,
                 "lente": 30, "tremor": 0.05},
         "acoes": [("olhar", 0, 0.5, (0, 0), (-18, 0))]},
        {"desc": "Contra-plongee: Elias ergue a lamparina contra o mar; ultimo relampago.",
         "cam": {"orbita": True, "centro": (0, 0.1, 1.7), "raio": 2.2, "a0": -25, "a1": -70, "h": 0.4,
                 "lente": 24, "tremor": 0.03},
         "acoes": [("olhar", 0, 0.3, (-18, 0), (-8, 0)), ("erguer", 0.05, 0.4, 0, -80)]},
        {"desc": "A calma: as ondas baixam, a chuva para e o ceu comeca a clarear; grua subindo.",
         "cam": {"de": (-4.5, -7.5, 1.2), "ate": (-5.5, -9.5, 3.6), "alvo": (0, 0, 0.9), "lente": 28},
         "acoes": [("olhar", 0, 0.4, (-8, 0), (0, 0)), ("erguer", 0.1, 0.5, -80, 0)]},
        {"desc": "Close no rosto de Elias com o amanhecer dourado atras.",
         "cam": {"de": (0.3, -2.4, 1.72), "ate": (0.08, -1.3, 1.68), "alvo": (0, 0.05, 1.66), "lente": 50,
                 "dof": True},
         "acoes": []},
        {"desc": "Silhueta do barco no mar liso, contra o sol nascendo; a camera gira devagar.",
         "cam": {"orbita": True, "centro": (0, 0, 0.9), "raio": 7.5, "a0": -35, "a1": 12, "h": 1.3, "lente": 26},
         "acoes": []},
        {"desc": "Final: Elias olha para quem assiste e acena com a cabeca.",
         "cam": {"de": (0.2, -3.4, 1.5), "ate": (0.2, -2.6, 1.55), "alvo": (0, 0.1, 1.45), "lente": 40},
         "acoes": [("acenar", 0.35, 0.7)]},
    ],
}

CARTA = _jornada(
    "A ultima carta", "criar_carta", 0.9,
    [("ETAPA 1/5", "A CELA"), ("ETAPA 2/5", "O ABANDONO"), ("ETAPA 3/5", "A CARTA"), ("ETAPA 4/5", "O PERDÃO"),
     ("ETAPA 5/5", "A ENTREGA")],
    ["Esta é a última carta de um homem que sabia que ia morrer. E ela termina com uma frase que muda tudo.",
     "Roma, ano 67. Paulo está preso. Acorrentado, numa cela fria.",
     "Quase todos o abandonaram. Ele pede só os pergaminhos e uma capa, porque o inverno está chegando.",
     "E escreve para Timóteo, como um pai escreve para um filho.",
     "Sobre quem o deixou sozinho, ele não pede vingança. Escreve: que isso não lhes seja cobrado.",
     "A carta é selada e enviada. Dois mil anos depois, ela ainda chega até nós.",
     "*Combati o bom combate, terminei a corrida, guardei a fé.* Ele não disse venci. Disse: não desisti.",
     "Se hoje fosse a sua última carta, o que você escreveria? Comenta. Segue a Lamparina."],
    ["Gancho: Elias diante da mesa escura.", "Etapa 1: a corrente de ferro aparece sobre a mesa.",
     "Etapa 2: o pergaminho se desenrola; a camera gira.", "Etapa 3: a pena escreve sobre o pergaminho.",
     "Etapa 4: a vela acende ao lado da carta.", "Etapa 5: o selo de cera, a carta enrolada; a corrente some."] + _FECHO)
CARTA.update({"cenario": "cela", "clima": "sombria", "gancho": "A ÚLTIMA CARTA|DE UM CONDENADO"})

BABILONIA = _jornada(
    "O homem mais rico da Babilonia", "criar_babilonia", 0.86,
    [("REGRA 1/5", "A TÁBUA"), ("REGRA 2/5", "UM DÉCIMO É SEU"), ("REGRA 3/5", "CONTROLE OS GASTOS"),
     ("REGRA 4/5", "FAÇA O OURO TRABALHAR"), ("REGRA 5/5", "PROTEJA O QUE É SEU")],
    ["Um escravo virou o homem mais rico da Babilônia. E o segredo dele cabe numa moeda.",
     "É a história que George Clason escreveu em 1926, inspirada em tábuas de argila. O nome do homem era Arkad.",
     "Primeira regra: de cada dez moedas que entram, uma é sua. Guarde antes de pagar qualquer coisa.",
     "Segunda: o que você ganha não é o que você pode gastar. Viva com as nove.",
     "Terceira: faça o ouro trabalhar. A moeda guardada traz outras moedas.",
     "Quarta: proteja o que é seu. Nada de promessa de ganho fácil.",
     "*A riqueza não é o que você ganha. É o que você guarda.* E ela começa com uma moeda só.",
     "Quanto você guardou este mês? Comenta. Segue a Lamparina."],
    ["Gancho: Elias diante da mesa, uma moeda brilhando.", "Etapa 1: a tábua de argila com marcas cuneiformes.",
     "Etapa 2: a primeira moeda vai para a pilha guardada.", "Etapa 3: moedas entram; uma em cada dez é guardada.",
     "Etapa 4: a pilha guardada cresce sozinha.", "Etapa 5: as duas pilhas, a guardada maior; grua subindo."] + _FECHO)
BABILONIA.update({"cenario": "babilonia", "clima": "locrio", "gancho": "DE ESCRAVO|A MAIS RICO|DA BABILÔNIA"})

DIOGENES = _jornada(
    "Diogenes vendo o seu feed", "criar_diogenes", 0.38,
    [],
    ["Diógenes morava num barril e andava com uma lamparina acesa em pleno dia. Imagina ele vendo o seu feed.",
     "Atenas, quatrocentos anos antes de Cristo. Ele dizia que procurava um homem de verdade. Nunca achou.",
     "Primeiro post: alguém mostrando o carro novo. Diógenes riria. Quanta coisa de que eu não preciso.",
     "Segundo: uma selfie com filtro. Ele perguntaria: e quem é você quando ninguém está olhando?",
     "Terceiro: uma briga nos comentários. Você perde a paz para ganhar uma discussão.",
     "Quando Alexandre, o Grande, ofereceu dar a ele o que quisesse, Diógenes respondeu: sai da frente do meu sol.",
     "*Quem precisa de pouco é livre.* Talvez o que te falta não seja mais. Seja menos.",
     "O que Diógenes diria do seu último post? Comenta. Segue a Lamparina."],
    ["Gancho: Elias na agora, ao lado do barril e do cao.", "A lamparina acende em pleno dia sobre a pedra.",
     "O celular aparece: o carro novo; a camera gira.", "O feed rola: a selfie com filtro.",
     "O feed rola: a briga; o celular vibra.", "A tela apaga, o celular tomba; o sol entra na pedra."] + _FECHO)
deslocar(DIOGENES, (0.2, -0.3, 0.3))
DIOGENES.update({"cenario": "atenas", "clima": "piano", "gancho": "DIÓGENES|VENDO O SEU FEED"})

HISTORIAS = {"diogenes-vendo-o-seu-feed": DIOGENES, "homem-mais-rico-da-babilonia": BABILONIA, "a-ultima-carta": CARTA, "a-tempestade": TEMPESTADE, "kintsugi": KINTSUGI, "ouro-no-fogo": OURO_FOGO, "diamante": DIAMANTE,
             "quatro-mil-semanas": AMPULHETA, "anjo-no-marmore": ESCULTURA, "vida-nao-esta-parada": VIDA_PARADA, "lamparina-mais-antiga": LAMPARINA, "codex-leicester": CODEX, "livro-medieval": LIVRO_MEDIEVAL}
