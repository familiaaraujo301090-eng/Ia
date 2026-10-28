#!/usr/bin/env python3
"""Quatro modelos de edicao viral, um diferente do outro, para alternar entre os videos.

Cada modelo copia um dos edits de referencia que o usuario mandou (analise em
.claude/skills/editar-shorts/estilos-virais.md). Nao misture: um video, um modelo.

    gravura     gravuras antigas trocando no tempo da musica, palavra gotica vermelha
                uma por vez, rajada de cortes no primeiro segundo (trilha "sombria", 95 BPM)
    tipografia  fundo preto, imagem so embaixo, a frase se monta palavra por palavra em
                tamanhos diferentes; a musica para antes da frase-chave (trilha "epica")
    colagem     texturas (papel, preto riscado, mancha vermelha), imagem em xerox com borda
                rasgada, transicoes variadas na batida, texto dourado digitado (trilha "pulso")
    pintura     fundo preto e a pintura numa faixa no meio que abre e fecha como cortina;
                uma palavra branca por vez; trechos so de palavra no preto (trilha "locrio")
    citacao     15 a 20 s sem voz: uma imagem surgindo do preto e a citacao fixa no topo,
                feita para assistir em loop (trilha "piano")

Uso: no video.json da pasta, "modelo": "<nome>" e rode editar_short.py como sempre, ou
    python modelos.py <modelo> <pasta> [saida.mp4]
para testar um modelo sem mexer no video.json. A camera so avanca (nunca vai e volta) e o
video comeca na primeira palavra: sem introducao parada.
"""
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

import editar_short as base
import gravura as grav
import trilha

L, A, FPS = base.LARGURA, base.ALTURA, base.FPS
FOLGA = 0.8
CLIMA = {"gravura": "sombria", "tipografia": "epica", "colagem": "pulso", "citacao": "piano",
         "pintura": "locrio"}
TEXTURAS = Path(__file__).parent / "texturas"
CORTE_SECO = 1 / FPS


# ---------- utilidades ----------

def ass_cor(hexa, alfa=0):
    """#RRGGBB -> &HAABBGGRR do ASS."""
    r, g, b = hexa[1:3], hexa[3:5], hexa[5:7]
    return f"&H{alfa:02X}{b}{g}{r}".upper()


def palavras(texto, inicio, fim):
    """Divide o intervalo da frase entre as palavras, pelo tamanho de cada uma."""
    lista = texto.split()
    pesos = [len(w.replace("*", "")) + 2 for w in lista]
    total, t, saida = sum(pesos), inicio, []
    for palavra, peso in zip(lista, pesos):
        proximo = t + (fim - inicio) * peso / total
        saida.append((palavra, t, proximo))
        t = proximo
    return saida


def cabecalho(estilos):
    linhas = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {L}", f"PlayResY: {A}", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        *estilos, "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    return linhas


def dialogo(camada, a, b, estilo, texto):
    return f"Dialogue: {camada},{base.tempo_ass(a)},{base.tempo_ass(b)},{estilo},,0,0,0,,{texto}"


def perto(t, batidas, folga=0.35):
    """Gruda o tempo na batida mais proxima, se houver uma a menos de `folga` segundos."""
    if not batidas:
        return t
    b = min(batidas, key=lambda x: abs(x - t))
    return b if abs(b - t) <= folga else t


def palavras_com_tempo(tempos):
    """[(palavra_sem_asteriscos, inicio, fim, destaque, fraca)] de toda a narracao."""
    saida, dentro = [], False
    for a, b, texto, *_ in tempos:
        for palavra, ini, fim in palavras(texto, a, b):
            comeca = palavra.startswith("*")
            destaque = dentro or comeca
            if comeca:
                dentro = True
            if palavra.rstrip(".,;:!?").endswith("*"):
                dentro = False
            limpa = palavra.replace("*", "")
            fraca = limpa.strip(".,;:!?").lower() in base.FRACAS
            saida.append((limpa, ini, fim, destaque, fraca))
    return saida


def sem_sobrepor(blocos, folga=0.25):
    """Fim de cada bloco: um pouco depois da ultima palavra, mas nunca depois do proximo comecar."""
    fins = []
    for k, bloco in enumerate(blocos):
        fim = bloco[-1][2] + folga
        if k + 1 < len(blocos):
            fim = min(fim, blocos[k + 1][0][1])
        fins.append(fim)
    return fins


def blocos_com_tempo(tempos):
    """Agrupa as palavras em blocos curtos (como as legendas classicas), com o tempo de cada uma."""
    todas = palavras_com_tempo(tempos)
    saida, k = [], 0
    for a, b, texto, *_ in tempos:
        for bloco in base.dividir_legendas(texto):
            n = len(bloco.split())
            saida.append(todas[k:k + n])
            k += n
    return saida


# ---------- dados do video ----------

def carregar(pasta, cfg, modelo):
    dados = {"pasta": pasta, "cfg": cfg, "modelo": modelo}
    dados["imagens"] = [pasta / i for i in cfg["imagens"]]
    if modelo == "citacao":
        dados["total"] = float(cfg.get("citacao", {}).get("duracao", 16))
        dados["tempos"], dados["narracao"] = [], None
        return dados
    dados["narracao"] = pasta / cfg["narracao"]
    dados["tempos"] = json.loads((pasta / cfg["tempos"]).read_text(encoding="utf-8"))
    dados["total"] = base.duracao_audio(dados["narracao"]) + FOLGA
    return dados


def faixa_musical(dados, pausa=None):
    pasta, total = dados["pasta"], dados["total"]
    clima = CLIMA[dados["modelo"]]
    destino = pasta / f"trilha-{clima}.wav"
    audio, info = trilha.compor(clima, total + 0.5, pausa)
    trilha.salvar(destino, audio, info)
    return destino, info["batidas"]


def cenas(dados, batidas):
    """(indice da imagem, inicio, fim) de cada cena, com as trocas grudadas na batida."""
    cfg, total, tempos = dados["cfg"], dados["total"], dados["tempos"]
    n = len(dados["imagens"])
    if cfg.get("cenas") and tempos:
        comeco = {}
        for a, _, _, paragrafo in tempos:
            comeco.setdefault(paragrafo, a)
        inicios = [0.0] + [perto(max(0.0, comeco[p] - 0.1), batidas) for p in cfg["cenas"][1:]]
    else:
        inicios = [i * total / n for i in range(n)]
    fins = inicios[1:] + [total]
    return list(zip(range(n), inicios, fins))


# ---------- preparo das imagens ----------

def cache(origem, sufixo):
    return origem.with_name(f"{origem.stem}_{sufixo}.jpg")


def gravura_enquadrada(origem, zoom, cx, cy):
    """Gravura feita do recorte original: a hachura fica do mesmo tamanho em todo plano."""
    destino = cache(origem, f"grav_{zoom:.2f}_{cx:.2f}_{cy:.2f}")
    if not destino.exists():
        img = Image.open(origem).convert("RGB")
        grav.gravura(grav.enquadrar(img, zoom, cx, cy)).save(destino, quality=90)
    return destino


def lateral(origem):
    """Tipografia: a imagem inteira, em preto e branco e escurecida, com uma sombra suave no
    alto onde a frase se monta. (Cortar metade da imagem no preto nao agradou ao usuario.)"""
    destino = cache(origem, "tipo2")
    if not destino.exists():
        img = grav.enquadrar(Image.open(origem).convert("RGB"))
        img = ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=1)
        img = img.point(lambda v: int(255 * 0.62 * (v / 255) ** 0.9))
        y = np.arange(A)[:, None]
        sombra = 1 - 0.55 * np.clip(1 - np.abs(y - 640) / 520, 0, 1) ** 1.5
        a = np.asarray(img, dtype=float) * np.repeat(sombra, L, axis=1)
        Image.fromarray(a.astype("uint8")).convert("RGB").save(destino, quality=92)
    return destino


def textura(nome, semente):
    """Fundos da colagem, gerados uma vez: preto riscado, papel amassado, mancha vermelha."""
    TEXTURAS.mkdir(exist_ok=True)
    destino = TEXTURAS / f"{nome}-{semente}.jpg"
    if destino.exists():
        return destino
    rng = np.random.default_rng(semente)
    ruido = lambda escala: np.asarray(
        Image.fromarray((rng.random((A // escala, L // escala)) * 255).astype("uint8"))
        .resize((L, A), Image.BICUBIC), dtype=float) / 255
    base_ruido = 0.6 * ruido(40) + 0.3 * ruido(12) + 0.1 * ruido(3)
    if nome == "papel":
        tom = 0.80 + 0.14 * base_ruido
        rgb = np.stack([tom * 236, tom * 231, tom * 220], -1)
    elif nome == "vermelho":
        mancha = np.clip((base_ruido - 0.45) * 4 + (np.arange(L)[None, :] / L - 0.55) * 3, 0, 1)
        rgb = np.stack([12 + mancha * 165, 10 + mancha * 18, 10 + mancha * 18], -1)
    else:
        tom = 0.04 + 0.08 * base_ruido
        rgb = np.stack([tom * 255] * 3, -1)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype("uint8"))
    desenho = ImageDraw.Draw(img)
    for _ in range(18):  # riscos finos de filme velho
        x = rng.integers(0, L)
        cor = (200, 200, 190) if nome != "papel" else (90, 85, 80)
        desenho.line([(x, rng.integers(0, A)), (x + rng.integers(-60, 60), rng.integers(0, A))],
                     fill=cor, width=1)
    img.filter(ImageFilter.GaussianBlur(0.6)).save(destino, quality=90)
    return destino


def colagem(origem, variacao):
    """Imagem em xerox (preto e branco duro) com borda rasgada sobre uma textura."""
    destino = cache(origem, f"col{variacao}")
    if destino.exists():
        return destino
    rng = random.Random(f"{origem}{variacao}")
    nome = ["preto", "papel", "vermelho"][variacao % 3]
    fundo = Image.open(textura(nome, variacao % 3 + 1)).convert("RGB")
    img = grav.enquadrar(Image.open(origem).convert("RGB"), 1.15, 0.5, 0.42)
    img = ImageOps.posterize(ImageOps.autocontrast(ImageOps.grayscale(img), cutoff=3), 3).convert("RGB")
    w, h = int(L * 0.86), int(A * 0.62)
    img = img.resize((w, h))
    # Borda rasgada: retangulo com a margem tremida por ruido.
    mascara = Image.new("L", (w, h), 0)
    pontos, passo = [], 14
    for x in range(0, w + 1, passo):
        pontos.append((x, rng.randint(0, 16)))
    for y in range(0, h + 1, passo):
        pontos.append((w - rng.randint(0, 16), y))
    for x in range(w, -1, -passo):
        pontos.append((x, h - rng.randint(0, 16)))
    for y in range(h, -1, -passo):
        pontos.append((rng.randint(0, 16), y))
    ImageDraw.Draw(mascara).polygon(pontos, fill=255)
    angulo = rng.uniform(-3.5, 3.5)
    img = img.rotate(angulo, expand=True, resample=Image.BICUBIC)
    mascara = mascara.rotate(angulo, expand=True, resample=Image.BICUBIC)
    sombra = Image.new("RGB", img.size)
    x0 = (L - img.width) // 2 + rng.randint(-30, 30)
    y0 = int(A * 0.30) + rng.randint(-40, 40)
    fundo.paste(sombra, (x0 + 14, y0 + 18), mascara.filter(ImageFilter.GaussianBlur(14)))
    fundo.paste(img, (x0, y0), mascara)
    fundo.save(destino, quality=92)
    return destino


def rajada(pasta, duracao):
    """Clipe de gravuras do banco trocando a cada 2 quadros (abertura do modelo gravura)."""
    if not list(grav.BANCO.glob("*.jpg")):
        grav.montar_banco()
    destino = pasta / "rajada.mp4"
    quadros = round(duracao * FPS)
    banco = sorted(grav.BANCO.glob("*.jpg"))
    escolhidas = random.Random(pasta.name).sample(banco, min(len(banco), quadros // 2 + 1))
    lista = destino.with_suffix(".txt")
    lista.write_text("".join(f"file '{c}'\nduration {2 / FPS:.5f}\n" for c in escolhidas)
                     + f"file '{escolhidas[-1]}'\n", encoding="utf-8")
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(lista), "-vf", f"scale={L}:{A},fps={FPS},format=yuv420p",
         "-frames:v", str(quadros), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         str(destino)],
        check=True,
    )
    return destino


# ---------- montagem generica ----------

def montar_video(dados, planos, legendas, musica, saida, pos="", volume_musica=-24.0):
    """planos: dicts com fonte, a, b, z0, z1, fx, fy, tipo ("imagem"/"video"/"preto"),
    transicao e fusao (passagem PARA este plano)."""
    pasta, total = dados["pasta"], dados["total"]
    (pasta / "legendas.ass").write_text("\n".join(legendas) + "\n", encoding="utf-8")
    entradas, filtros = [], []
    for k, p in enumerate(planos):
        seguinte = planos[k + 1]["fusao"] if k + 1 < len(planos) else 0
        quadros = round((p["b"] + seguinte) * FPS) - round(p["a"] * FPS)
        if p["tipo"] == "video":
            entradas += ["-i", str(p["fonte"])]
            filtros.append(f"[{k}:v]fps={FPS},settb=1/{FPS},format=yuv420p,setsar=1,"
                           f"tpad=stop_mode=clone:stop_duration=1,trim=end_frame={quadros}[v{k}]")
            continue
        entradas += ["-i", str(p["fonte"])]
        zoom = f"{p['z0']}+({p['z1'] - p['z0']})*on/{quadros}"
        x = f"max(0,min(iw-iw/zoom,iw*{p['fx']}-iw/zoom/2))"
        y = f"max(0,min(ih-ih/zoom,ih*{p['fy']}-ih/zoom/2))"
        filtros.append(
            f"[{k}:v]scale={L * 2}:{A * 2}:force_original_aspect_ratio=increase,crop={L * 2}:{A * 2},"
            f"setsar=1,zoompan=z='{zoom}':x='{x}':y='{y}':d={quadros}:s={L}x{A}:fps={FPS},"
            f"format=yuv420p[v{k}]"
        )
    atual = "v0"
    for k in range(1, len(planos)):
        p = planos[k]
        filtros.append(f"[{atual}][v{k}]xfade=transition={p.get('transicao', 'fade')}"
                       f":duration={p['fusao']:.4f}:offset={round(p['a'] * FPS) / FPS:.4f}[x{k}]")
        atual = f"x{k}"
    fontes = Path(os.path.relpath(base.FONTES, pasta)).as_posix()
    filtros.append(
        f"[{atual}]trim=duration={total:.3f},{pos}subtitles=legendas.ass:fontsdir='{fontes}',"
        f"fade=t=out:st={total - 0.4:.3f}:d=0.4[video]"
    )
    # Musica embaixo da voz, abaixando sozinha quando ele fala (sidechain), e tudo em -14 LUFS.
    n = len(planos)
    entradas += ["-i", str(musica)]
    filtros.append(f"[{n}:a]atrim=duration={total:.3f},loudnorm=I={volume_musica}:TP=-2,"
                   f"afade=t=out:st={total - 1.2:.3f}:d=1.2[mus]")
    if dados["narracao"]:
        entradas += ["-i", str(dados["narracao"])]
        filtros.append(f"[{n + 1}:a]apad=whole_dur={total:.3f},asplit=2[voz][chave]")
        filtros.append("[mus][chave]sidechaincompress=threshold=0.04:ratio=6:attack=15:release=400[fundo]")
        filtros.append("[voz][fundo]amix=inputs=2:duration=first:normalize=0,"
                       "loudnorm=I=-14:TP=-1.5:LRA=9[audio]")
    else:
        filtros.append("[mus]loudnorm=I=-14:TP=-1.5[audio]")
    comando = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *entradas,
        "-filter_complex", ";".join(filtros), "-map", "[video]", "-map", "[audio]",
        "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", "-c:v", "libx264",
        "-preset", "medium", "-crf", "20", "-r", str(FPS), "-movflags", "+faststart", saida,
    ]
    subprocess.run(comando, cwd=pasta, check=True)
    print(f"Pronto: {pasta / saida} ({total:.1f}s, modelo {dados['modelo']})")


def plano(fonte, a, b, z0=1.0, z1=1.04, fx=0.5, fy=0.5, tipo="imagem", transicao="fade",
          fusao=CORTE_SECO):
    return dict(fonte=fonte, a=a, b=b, z0=z0, z1=z1, fx=fx, fy=fy, tipo=tipo,
                transicao=transicao, fusao=fusao)


# ---------- modelo 1: gravura ----------

def modelo_gravura(dados):
    musica, batidas = faixa_musical(dados)
    focos = dados["cfg"].get("focos") or [0.36] * len(dados["imagens"])
    # Rajada no primeiro segundo, junto com a primeira frase (sem introducao parada).
    fim_rajada = perto(0.9, batidas, 0.4)
    planos = [plano(rajada(dados["pasta"], fim_rajada + 0.1), 0.0, fim_rajada, tipo="video")]
    # Enquadramentos em ordem: aberto, medio, close, um lampejo do banco, e de novo mais perto
    # em outro ponto da imagem. Cada plano e uma gravura nova, com leve avanco de camera.
    ciclo = [(1.0, 0.5, None), (1.35, 0.5, "foco"), (1.8, 0.5, "foco"), ("banco",),
             (1.5, 0.38, "foco"), (1.5, 0.62, "foco")]
    banco = sorted(grav.BANCO.glob("*.jpg"))
    sorteio = random.Random(dados["pasta"].name)
    for i, a, b in cenas(dados, batidas):
        a = max(a, fim_rajada)
        dentro = [t for t in batidas if a + 0.3 < t < b - 0.3]
        marcas = [a] + dentro[1::2] + [b]  # troca a cada 2 batidas
        for j, (ini, fim) in enumerate(zip(marcas, marcas[1:])):
            passo = ciclo[j % len(ciclo)]
            if passo[0] == "banco":
                fonte = sorteio.choice(banco)
            else:
                zoom, cx, cy = passo
                cy = focos[i] if cy == "foco" else 0.5
                fonte = gravura_enquadrada(dados["imagens"][i], zoom, cx, cy)
            planos.append(plano(fonte, ini, fim, 1.0, 1.035))

    vermelho = ass_cor("#D9262B")
    legendas = cabecalho([
        f"Style: Palavra,UnifrakturMaguntia,150,{vermelho},{vermelho},{ass_cor('#5A0A0A')},"
        "&H00000000,0,0,0,0,100,100,2,0,1,3,0,5,40,40,0,1",
    ])
    palavras = palavras_com_tempo(dados["tempos"])
    for k, (palavra, ini, fim, destaque, _) in enumerate(palavras):
        if k + 1 < len(palavras) and palavras[k + 1][1] - fim < 0.8:
            fim = palavras[k + 1][1]
        tam = "\\fscx130\\fscy130" if destaque else ""
        entrada = "\\blur8\\t(0,90,\\blur0)"
        # Brilho vermelho borrado por baixo, letra nitida por cima.
        legendas.append(dialogo(0, ini, fim, "Palavra",
                                f"{{\\pos(540,1020){tam}\\bord16\\blur18\\3c{vermelho}\\alpha&H60&}}{palavra}"))
        legendas.append(dialogo(1, ini, fim, "Palavra", f"{{\\pos(540,1020){tam}{entrada}}}{palavra}"))
    pos = "noise=alls=10:allf=t,vignette=PI/4,"
    return planos, legendas, musica, pos


# ---------- modelo 2: tipografia ----------

def modelo_tipografia(dados):
    # A musica para um instante antes da frase-chave (a primeira com *destaque*).
    pausa = next((a for a, _, texto, *_ in dados["tempos"] if "*" in texto), None)
    musica, batidas = faixa_musical(dados, pausa)
    planos = []
    for i, a, b in cenas(dados, batidas):
        planos.append(plano(lateral(dados["imagens"][i]), a, b, 1.0, 1.05, 0.5, 0.5,
                            fusao=0.8 if planos else 0))
    vermelho = ass_cor("#D41A1A")
    legendas = cabecalho([
        # Contorno e sombra escuros: agora a frase fica sobre a imagem inteira, nao no preto.
        f"Style: Frase,DM Serif Display,124,{vermelho},{vermelho},&H00000000,&H64000000,"
        "0,0,0,0,100,100,0,0,1,3,5,5,90,90,0,1",
    ])
    blocos = blocos_com_tempo(dados["tempos"])
    for bloco, fim in zip(blocos, sem_sobrepor(blocos)):
        ini = bloco[0][1]
        partes = []
        for palavra, a, _, destaque, fraca in bloco:
            # Contraste de tamanho e a assinatura do modelo: ligacao pequena, chave enorme.
            tam = 176 if destaque else (70 if fraca else 124)
            atraso = int((a - ini) * 1000)
            # Cada palavra entra no tempo da fala, desfocada, e ganha corpo em 100 ms.
            partes.append(f"{{\\fs{tam}\\alpha&HFF&\\blur6\\t({atraso},{atraso + 110},"
                          f"\\alpha&H00&\\blur0)}}{palavra}")
        legendas.append(dialogo(0, ini, fim, "Frase", "{\\pos(540,620)\\fad(0,90)}" + " ".join(partes)))
    pos = "noise=alls=5:allf=t,"
    return planos, legendas, musica, pos


# ---------- modelo 3: colagem ----------

def modelo_colagem(dados):
    musica, batidas = faixa_musical(dados)
    transicoes = ["fadewhite", "wipeleft", "smoothup", "zoomin", "hblur", "fadeblack", "slideleft"]
    planos, variacao = [], 0
    for i, a, b in cenas(dados, batidas):
        dentro = [t for t in batidas if a + 0.6 < t < b - 0.6]
        marcas = [a] + dentro[3::4] + [b]  # troca a cada 4 batidas (um compasso)
        for ini, fim in zip(marcas, marcas[1:]):
            fusao = 0 if not planos else 0.3
            # A transicao termina na batida: comeca um pouco antes dela.
            planos.append(plano(colagem(dados["imagens"][i], variacao), ini - fusao if planos else ini,
                                fim, 1.0, 1.05, transicao=transicoes[variacao % len(transicoes)],
                                fusao=fusao))
            variacao += 1
    # Ajusta o fim de cada plano ao inicio do seguinte (o seguinte comecou antes da batida).
    for k in range(len(planos) - 1):
        planos[k]["b"] = planos[k + 1]["a"]
    dourado = ass_cor("#F0C040")
    legendas = cabecalho([
        # SecondaryColour transparente: no karaoke, as letras ainda nao "digitadas" ficam invisiveis.
        f"Style: Maquina,Cinzel,98,{dourado},&HFF000000,&H00000000,&H90000000,"
        "1,0,0,0,100,100,1,0,1,5,6,5,80,80,0,1",
    ])
    blocos = blocos_com_tempo(dados["tempos"])
    for bloco, fim in zip(blocos, sem_sobrepor(blocos, 0.2)):
        ini = bloco[0][1]
        texto = " ".join(p[0] for p in bloco).upper()
        digitacao = max(0.25, (fim - ini) * 0.55)
        cs = max(1, round(digitacao * 100 / max(1, len(texto))))
        letras = "".join(f"{{\\k{cs}}}{c}" for c in texto)
        # Na faixa de textura acima da foto, como no edit de referencia.
        legendas.append(dialogo(0, ini, fim, "Maquina", f"{{\\pos(540,330)\\fad(0,80)}}{letras}"))
    pos = ("noise=alls=14:allf=t+u,eq=brightness='0.025*sin(n*1.9)':eval=frame,vignette=PI/4.5,")
    return planos, legendas, musica, pos


# ---------- modelo 4: citacao ----------

def modelo_citacao(dados):
    musica, _ = faixa_musical(dados)
    c = dados["cfg"]["citacao"]
    fonte = dados["pasta"] / c["imagem"] if c.get("imagem") else dados["imagens"][0]
    total = dados["total"]
    planos = [plano(fonte, 0.0, total, 1.0, 1.08, 0.5, 0.4)]
    legendas = cabecalho([
        # BorderStyle 3: caixa opaca atras do texto, na cor de contorno (branca).
        f"Style: Faixa,{base.FONTE_LEGENDA},58,&H00101010,&H00101010,&H00FFFFFF,&H00FFFFFF,"
        "0,0,0,0,100,100,0,0,3,18,0,8,70,70,170,1",
        f"Style: Autor,{base.FONTE_TITULO},46,&H00F0F0F0,&H00F0F0F0,&H00000000,&H00000000,"
        "1,0,0,0,100,100,3,0,1,3,0,2,70,70,170,1",
    ])
    legendas.append(dialogo(0, 0, total, "Faixa", c["texto"]))
    if c.get("autor"):
        legendas.append(dialogo(0, 1.0, total, "Autor", f"{{\\fad(600,0)}}\u2014 {c['autor'].upper()}"))
    # A imagem surge do preto devagar; o texto ja esta la desde o primeiro quadro.
    pos = "eq=saturation=0.35:contrast=1.08,fade=t=in:st=0:d=2.5,vignette=PI/4,"
    return planos, legendas, musica, pos


# ---------- modelo 5: pintura ----------

FAIXA = {"faixa": 660, "alta": 1100}  # altura do quadro aberto
CENTRO_FAIXA = 900  # centro vertical do quadro


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def video_pintura(dados, trechos, destino):
    """Desenha quadro a quadro: preto, e a pintura recortada numa faixa que abre do centro
    (como cortina), fica e fecha. A camera so avanca devagar dentro da faixa."""
    total = dados["total"]
    quadros = round(total * FPS)
    preparadas = {}
    for k, (fonte, formato, foco, a, b) in enumerate(trechos):
        if fonte is None:
            continue
        img = Image.open(fonte).convert("RGB")
        img = ImageOps.fit(img, (L, round(L * img.height / img.width)))
        # Tom de pintura antiga: um pouco menos saturada e mais escura.
        arr = np.asarray(img).astype(np.float32)
        cinza = arr.mean(2, keepdims=True)
        arr = (cinza + (arr - cinza) * 0.85) * 0.9
        # Pintura muito escura some no preto do fundo: clareia ate um brilho medio minimo.
        media = arr.mean()
        if media < 62:
            arr = 255 * (arr / 255) ** (np.log(62 / 255) / np.log(media / 255))
        preparadas[k] = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{L}x{A}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "17", "-pix_fmt", "yuv420p", str(destino)], stdin=subprocess.PIPE)
    preto = np.zeros((A, L, 3), np.uint8)
    for q in range(quadros):
        t = q / FPS
        k = next((i for i, tr in enumerate(trechos) if tr[3] <= t < tr[4]), len(trechos) - 1)
        fonte, formato, foco, a, b = trechos[k]
        if fonte is None:
            proc.stdin.write(preto.tobytes())
            continue
        cheia = FAIXA[formato]
        anterior = trechos[k - 1] if k else None
        seguinte = trechos[k + 1] if k + 1 < len(trechos) else None
        abre = not (anterior and anterior[0] is not None and anterior[1] == formato)
        fecha = not (seguinte and seguinte[0] is not None and seguinte[1] == formato)
        dur = b - a
        abertura = min(1.6, dur * 0.35) if abre else 0
        fechamento = min(0.45, dur * 0.15) if fecha else 0
        h = cheia
        if abertura and t - a < abertura:
            h = 8 + (cheia - 8) * suave((t - a) / abertura)
        if fechamento and b - t < fechamento:
            h = min(h, 8 + (cheia - 8) * suave((b - t) / fechamento))
        h = max(2, int(h) // 2 * 2)
        img = preparadas[k]
        zoom = 1.0 + 0.06 * (t - a) / max(dur, 0.1)
        larg, alt = round(L * zoom), round(img.height * zoom)
        grande = img.resize((larg, alt), Image.BILINEAR)
        # O assunto (foco) fica no centro da faixa; a faixa mostra so a fatia do meio.
        cy = foco * alt
        topo = int(min(max(cy - h / 2, 0), alt - h))
        esq = (larg - L) // 2
        fatia = np.asarray(grande.crop((esq, topo, esq + L, topo + h)))
        quadro = preto.copy()
        y0 = CENTRO_FAIXA - h // 2
        quadro[y0:y0 + h] = fatia
        proc.stdin.write(quadro.tobytes())
    proc.stdin.close()
    proc.wait()
    return destino


def modelo_pintura(dados):
    musica, batidas = faixa_musical(dados)
    cfg = dados["cfg"]
    formatos = cfg.get("formatos") or ["faixa"] * len(dados["imagens"])
    focos = cfg.get("focos") or [0.5] * len(dados["imagens"])
    trechos = []
    for i, a, b in cenas(dados, batidas):
        nome = cfg["imagens"][i]
        fonte = None if nome in (None, "preto") else dados["imagens"][i]
        trechos.append((fonte, formatos[i], focos[i], a, b))
    video = video_pintura(dados, trechos, dados["pasta"] / "pintura.mp4")
    planos = [plano(video, 0.0, dados["total"], tipo="video")]
    legendas = cabecalho([
        f"Style: Palavra,{base.FONTE_LEGENDA},84,&H00FFFFFF,&H00FFFFFF,&H00101010,&H90000000,"
        "0,0,0,0,100,100,1,0,1,2,4,5,60,60,0,1",
        f"Style: Marca,{base.FONTE_LEGENDA},30,&H00808080,&H00808080,&H00000000,&H00000000,"
        "0,0,0,0,100,100,14,0,1,0,0,5,60,60,0,1",
    ])
    lista = palavras_com_tempo(dados["tempos"])
    for k, (palavra, ini, fim, destaque, _) in enumerate(lista):
        if k + 1 < len(lista) and lista[k + 1][1] - fim < 0.8:
            fim = lista[k + 1][1]
        texto = palavra.strip(".,;:!?").upper()
        cor = "\\c&H4CC8F5&" if destaque else ""
        # Cada palavra entra com um pequeno "pulo" (de 88% a 100% em 80 ms).
        legendas.append(dialogo(0, ini, fim, "Palavra",
                                f"{{\\pos(540,1110){cor}\\fscx88\\fscy88\\t(0,80,\\fscx100\\fscy100)}}{texto}"))
    legendas.append(dialogo(0, 0, dados["total"], "Marca", "{\\pos(540,1530)}@LAMPARINA"))
    pos = "noise=alls=6:allf=t,vignette=PI/5,"
    return planos, legendas, musica, pos


MONTADORES = {"gravura": modelo_gravura, "tipografia": modelo_tipografia,
              "colagem": modelo_colagem, "citacao": modelo_citacao, "pintura": modelo_pintura}


def montar(pasta, cfg, modelo=None, saida=None):
    modelo = modelo or cfg["modelo"]
    dados = carregar(Path(pasta).resolve(), cfg, modelo)
    planos, legendas, musica, pos = MONTADORES[modelo](dados)
    montar_video(dados, planos, legendas, musica, saida or cfg.get("saida", "short.mp4"), pos)


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4) or sys.argv[1] not in MONTADORES:
        sys.exit(__doc__)
    pasta = Path(sys.argv[2]).resolve()
    cfg = json.loads((pasta / "video.json").read_text(encoding="utf-8"))
    montar(pasta, cfg, sys.argv[1], sys.argv[3] if len(sys.argv) == 4 else f"short-{sys.argv[1]}.mp4")
