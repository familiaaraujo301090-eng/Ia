#!/usr/bin/env python3
"""Pipeline completo de um curta 3D, sem editor de video:

    python gerar.py preparar [historia]  (historia: chave de historia.HISTORIAS)
    python gerar.py preparar   narracao + cena 3D (.blend) + folhas (personagem, cenario, storyboard)
    python gerar.py quadros    renderiza os quadros (retoma de onde parou; pode rodar em segundo plano)
    python gerar.py finalizar  junta quadros, voz, trilha e legendas em saida/<nome>/video.mp4

Tudo e gerado por codigo: personagem (personagem.py), cenario (cenario.py), animacao e cameras
(historia.py), render com Cycles na CPU e montagem com ffmpeg.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import bpy

AQUI = Path(__file__).resolve().parent
SHORTS = AQUI.parent / "shorts"
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(SHORTS))

import cenario  # noqa: E402
import folhas  # noqa: E402
import historia  # noqa: E402
import materiais  # noqa: E402
import personagem  # noqa: E402
import processo  # noqa: E402

NOME = sys.argv[2] if len(sys.argv) > 2 else "lamparina-mais-antiga"
HIST = historia.HISTORIAS[NOME]
SAIDA = AQUI / "saida" / NOME
LARG, ALT, AMOSTRAS = 540, 960, 8
PASSO = 2  # renderiza 1 quadro a cada 2; o ffmpeg interpola os do meio (metade do tempo)
VOZ = ("pm_alex", "1.0", "0.95")  # voz nova, a pedido do usuario (a pm_santa cansou)


def narracao():
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "roteiro.txt").write_text("\n".join(HIST["roteiro"]) + "\n", encoding="utf-8")
    if not (SAIDA / "narracao.wav").exists():
        subprocess.run([sys.executable, str(SHORTS / "gerar_voz.py"), str(SAIDA), *VOZ, "--rapido"], check=True)
    tempos = json.loads((SAIDA / "tempos.json").read_text(encoding="utf-8"))
    total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                           "csv=p=0", str(SAIDA / "narracao.wav")])) + 1.0
    return tempos, total


def construir(tempos, total):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cena = bpy.context.scene
    folhas.configurar_render(cena, LARG, ALT, AMOSTRAS)
    cena.render.fps = historia.FPS
    cena.cycles.max_bounces = 3
    cena.cycles.adaptive_threshold = 0.05
    cena.cycles.denoiser = "OPENIMAGEDENOISE"
    cena.cycles.use_adaptive_sampling = True
    cena.render.use_persistent_data = True
    col = cena.collection
    m = materiais.paleta()
    cenario.criar(col, m)
    p = personagem.criar(col, m)
    faixas = historia.tempos_dos_planos(tempos, total)
    historia.aplicar_acoes(p, HIST["planos"], faixas, HIST.get("inicio"))
    historia.criar_cameras(HIST["planos"], faixas, col, cena)
    if HIST.get("extra"):
        getattr(processo, HIST["extra"])(col, m, faixas)
    cena.frame_start, cena.frame_end = 0, faixas[-1][1]
    personagem.tremular(p, 0, cena.frame_end)
    bpy.ops.wm.save_as_mainfile(filepath=str(SAIDA / "cena.blend"))
    return cena, p, faixas


def folha_cenario(cena, p):
    for o in p["raiz"].children_recursive + [p["raiz"]]:
        o.hide_render = True
    vistas = [("VISAO GERAL", (0, -6.5, 2.4), (0, 1.5, 1.6), 24, False),
              ("PLANTA (DE CIMA)", (0, 0.4, 16), (0, 0.4, 0), 9, True),
              ("LATERAL", (-3.4, -3.4, 1.9), (1.0, 1.5, 1.4), 22, False),
              ("DETALHE: MESA", (0.9, -1.6, 1.25), (1.9, -0.35, 0.85), 30, False)]
    imgs = []
    tmp = SAIDA / "tmp"
    tmp.mkdir(exist_ok=True)
    folhas.configurar_render(cena, 540, 960, 24)
    for i, (rot, loc, alvo, lente, orto) in enumerate(vistas):
        cam, a = historia._camera(f"folha{i}", lente, cena.collection)
        cam.location, a.location = loc, alvo
        if orto:
            cam.data.type = "ORTHO"
            cam.data.ortho_scale = 13
        cena.camera = cam
        for mk in cena.timeline_markers:
            mk.camera = None  # senao o marcador troca a camera de volta
        cena.frame_set(0)
        imgs.append(folhas.foto(cena, tmp / f"cenario{i}.png"))
    for o in p["raiz"].children_recursive + [p["raiz"]]:
        o.hide_render = False
    return folhas.montar_grade(imgs, [v[0] for v in vistas], SAIDA / "folha-cenario.jpg", 4,
                               "CENARIO: BIBLIOTECA DA LAMPARINA")


def folha_storyboard(cena, faixas):
    folhas.configurar_render(cena, 360, 640, 16)
    imgs, rot, leg = [], [], []
    tmp = SAIDA / "tmp"
    for i, (plano, (q0, q1)) in enumerate(zip(HIST["planos"], faixas), 1):
        q = (q0 + q1) // 2
        cena.frame_set(q)
        cena.camera = bpy.data.objects[f"cam{i}"]
        imgs.append(folhas.foto(cena, tmp / f"story{i}.png"))
        rot.append(f"PLANO {i}  {q0 / historia.FPS:.1f}-{q1 / historia.FPS:.1f}s")
        leg.append(plano["desc"] + "  |  \"" + HIST["roteiro"][i - 1].replace("*", "") + "\"")
    return folhas.montar_grade(imgs, rot, SAIDA / "folha-storyboard.jpg", 3, "STORYBOARD: " + HIST["titulo"].upper(),
                               legendas=leg)


def preparar():
    tempos, total = narracao()
    folhas.folha_personagem(SAIDA / "folha-personagem.jpg", _tmp(), personagem.criar, materiais.paleta)
    cena, p, faixas = construir(tempos, total)
    folha_cenario(cena, p)
    bpy.ops.wm.open_mainfile(filepath=str(SAIDA / "cena.blend"))
    folha_storyboard(bpy.context.scene, faixas)
    print("Pronto: folhas e cena em", SAIDA)


def _tmp():
    t = SAIDA / "tmp"
    t.mkdir(parents=True, exist_ok=True)
    return t


def quadros():
    bpy.ops.wm.open_mainfile(filepath=str(SAIDA / "cena.blend"))
    cena = bpy.context.scene
    folhas.configurar_render(cena, LARG, ALT, AMOSTRAS)
    cena.cycles.max_bounces = 3
    cena.cycles.adaptive_threshold = 0.05
    cena.render.use_persistent_data = True
    pasta = SAIDA / "quadros"
    pasta.mkdir(exist_ok=True)
    for f in range(cena.frame_start, cena.frame_end + 1, PASSO):
        destino = pasta / f"{f:05d}.png"
        if destino.exists():
            continue
        cena.frame_set(f)
        cena.render.filepath = str(destino)
        bpy.ops.render.render(write_still=True)
        print(f"quadro {f}/{cena.frame_end}", flush=True)


def contador_de_passos(tempos):
    """Formato processo: 'PASSO n/N' + nome do passo + barra de progresso no topo, um por plano."""
    import modelos
    tot = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                         "csv=p=0", str(SAIDA / "narracao.wav")])) + 1.0
    faixas = historia.tempos_dos_planos(tempos, tot)[1:1 + len(HIST["passos"])]
    n = len(HIST["passos"])
    linhas = [
        "Style: Passo,Inter ExtraBold,64,&H004CC8F5,&H004CC8F5,&H00101010,&H96000000,0,0,0,0,100,100,2,0,1,3,2,8,60,60,150,1",
        "Style: Nome,Inter ExtraBold,40,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,0,0,0,0,100,100,6,0,1,3,2,8,60,60,235,1",
        "Style: Barra,Inter ExtraBold,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
    ]
    eventos = []
    largura = 760
    for i, (nome, (q0, q1)) in enumerate(zip(HIST["passos"], faixas), 1):
        a, b = q0 / historia.FPS, (q1 + 1) / historia.FPS
        eventos.append(modelos.dialogo(2, a, b, "Passo", f"{{\\fad(120,0)}}PASSO {i}/{n}"))
        eventos.append(modelos.dialogo(2, a, b, "Nome", f"{{\\fad(120,0)}}{nome}"))
        x0, y0 = (1080 - largura) // 2, 310
        fundo = f"{{\\pos({x0},{y0})\\c&H303030&\\alpha&H40&\\p1}}m 0 0 l {largura} 0 {largura} 14 0 14{{\\p0}}"
        cheio = largura * i // n
        antes = largura * (i - 1) // n
        barra = (f"{{\\pos({x0},{y0})\\c&H4CC8F5&\\p1\\clip(0,0,{x0 + antes},1920)\\t(0,600,\\clip(0,0,{x0 + cheio},1920))}}"
                 f"m 0 0 l {largura} 0 {largura} 14 0 14{{\\p0}}")
        eventos.append(modelos.dialogo(1, a, b, "Barra", fundo))
        eventos.append(modelos.dialogo(2, a, b, "Barra", barra))
    # Os estilos novos entram junto com os do cabecalho principal.
    return ["#ESTILOS#" + "|".join(linhas)] + eventos


def finalizar():
    import modelos
    tempos = json.loads((SAIDA / "tempos.json").read_text(encoding="utf-8"))
    pal = modelos.palavras_com_tempo(tempos)
    leg = modelos.cabecalho([
        "Style: P,Inter ExtraBold,86,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,0,0,0,0,100,100,1,0,1,4,3,2,60,60,330,1",
    ])
    for k, (w, a, b, dest, _) in enumerate(pal):
        if k + 1 < len(pal) and pal[k + 1][1] - b < 0.8:
            b = pal[k + 1][1]
        cor = "\\c&H4CC8F5&" if dest else ""
        leg.append(modelos.dialogo(0, a, b, "P", f"{{{cor}\\fscx88\\fscy88\\t(0,80,\\fscx100\\fscy100)}}{w.strip('.,;:!?').upper()}"))
    if HIST.get("passos"):
        extra = contador_de_passos(tempos)
        estilos = extra[0].replace("#ESTILOS#", "").split("|")
        i = next(k for k, l in enumerate(leg) if l.startswith("Style: P,"))
        leg[i + 1:i + 1] = estilos
        leg += extra[1:]
    (SAIDA / "legendas.ass").write_text("\n".join(leg) + "\n", encoding="utf-8")
    import trilha
    feitos = sorted(q for q in (SAIDA / "quadros").glob("*.png") if int(q.stem) % PASSO == 0)
    total = len(feitos) * PASSO / historia.FPS
    (SAIDA / "quadros.txt").write_text("".join(f"file 'quadros/{q.name}'\nduration {PASSO / historia.FPS:.5f}\n"
                                                for q in feitos), encoding="utf-8")
    audio, info = trilha.compor("piano", total + 0.5)
    trilha.salvar(SAIDA / "trilha.wav", audio, info)
    fontes = SHORTS / "fontes"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
        "-i", "quadros.txt", "-i", "narracao.wav", "-i", "trilha.wav", "-filter_complex",
        f"[0:v]fps={historia.FPS / PASSO},minterpolate=fps={historia.FPS}:mi_mode=mci:mc_mode=aobmc:vsbmc=1,"
        f"scale=1080:1920:flags=lanczos,subtitles=legendas.ass:fontsdir='{fontes}',"
        f"fade=t=in:st=0:d=0.3,fade=t=out:st={total - 0.5:.2f}:d=0.5[v];"
        "[2:a]volume=0.09[m];[1:a]apad[voz];[voz][m]amix=inputs=2:duration=shortest:normalize=0,"
        "loudnorm=I=-14:TP=-1.5[a]",
        "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "video.mp4",
    ], cwd=SAIDA, check=True)
    print("Pronto:", SAIDA / "video.mp4")


if __name__ == "__main__":
    {"preparar": preparar, "quadros": quadros, "finalizar": finalizar}[sys.argv[1]]()
