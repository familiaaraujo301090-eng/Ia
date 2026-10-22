#!/usr/bin/env python3
"""Monta um video curto vertical (1080x1920) a partir de imagens + narracao + roteiro.

Uso:
    python editar_short.py pasta_do_video/

A pasta precisa ter um arquivo video.json, por exemplo:
{
  "titulo": "Voce sofre mais na sua cabeca",
  "roteiro": "Texto completo da narracao...",
  "narracao": "narracao.mp3",
  "imagens": ["1.png", "2.png", "3.png"],
  "musica": "musica.mp3",
  "volume_musica": 0.12
}

Somente "roteiro" e "imagens" sao obrigatorios. Sem "roteiro" no json, o texto
vem de roteiro.txt (um paragrafo por linha). Sem "narracao", use "duracao"
(em segundos) para gerar uma previa sem audio. Opcionais:
  "tempos": arquivo json com [inicio, fim] de cada paragrafo da narracao, ou
            [inicio, fim, texto, paragrafo] de cada frase (gerado por gerar_voz.py),
            para a legenda acompanhar a fala com precisao;
  "cenas": numero do paragrafo do roteiro em que cada imagem entra (com "tempos"
           por frase), por exemplo [1, 2, 3, 4, 5];
  "inicios": em vez de "cenas", o segundo em que cada imagem entra;
  "focos": altura (0 = topo, 1 = base) do assunto de cada imagem, usada nos
           closes; o padrao 0.36 serve para rostos;
  "ambiente": false desliga o som ambiente suave gerado por baixo da voz.
Palavras entre *asteriscos* no roteiro aparecem em dourado na legenda.
O resultado sai em pasta_do_video/short.mp4. Precisa do ffmpeg instalado.
"""
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

LARGURA, ALTURA, FPS = 1080, 1920, 30
TRANSICAO = 0.6  # segundos de fusao entre imagens
CORTE = 0.3  # fusao curta entre dois planos da mesma imagem
PLANO_MAXIMO = 6.5  # imagem que fica mais que isso na tela ganha um segundo plano (close)
# Movimentos de camera: zoom inicial, zoom final e altura do ponto de foco (0 = topo).
MOVIMENTOS = {
    "aproxima": (1.0, 1.12, 0.5),
    "abre": (1.14, 1.0, 0.5),
    "close": (1.5, 1.36, None),  # foco vem de "focos" (padrao: terco de cima, onde ficam rostos)
}
FOLGA_FINAL = 0.8  # segundos depois que a narracao termina
MAX_PALAVRAS, MAX_LETRAS = 5, 24  # legendas curtas sao lidas num relance
# Palavras que nao devem fechar uma legenda: elas puxam a proxima ("na sua", "do que").
FRACAS = {"a", "o", "as", "os", "um", "uma", "de", "do", "da", "dos", "das", "em", "no",
          "na", "nos", "nas", "e", "que", "se", "por", "para", "com", "sem", "ao", "à",
          "mais", "sua", "seu", "suas", "seus", "meu", "minha", "não", "nem", "é", "eu",
          "como", "mas", "ou", "quando", "onde", "porque", "pelo", "pela", "entre", "até"}
FONTES = Path(__file__).parent / "fontes"
FONTE_LEGENDA, FONTE_TITULO = "Inter ExtraBold", "Cinzel"


def duracao_audio(caminho):
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(caminho)],
        capture_output=True, text=True, check=True,
    )
    return float(saida.stdout.strip())


def dividir_legendas(roteiro):
    """Quebra o roteiro em pedacos curtos, sem cortar no meio de uma expressao."""
    frases = re.split(r"(?<=[.!?;:,])\s+", roteiro.strip())
    blocos = []
    for frase in frases:
        atual, inicio_frase = [], len(blocos)
        for palavra in frase.split():
            letras = len(" ".join(atual + [palavra]).replace("*", ""))
            if atual and (len(atual) >= MAX_PALAVRAS or letras > MAX_LETRAS):
                # Leva as palavras fracas do fim para o proximo bloco.
                sobra = []
                while len(atual) > 2 and atual[-1].strip("*").lower() in FRACAS:
                    sobra.insert(0, atual.pop())
                blocos.append(atual)
                atual = sobra
            atual.append(palavra)
        if atual:
            # Uma palavra solta no fim da frase ("real.") volta para o bloco anterior.
            if len(atual) == 1 and len(blocos) > inicio_frase and \
                    len(" ".join(blocos[-1] + atual)) <= MAX_LETRAS + 8:
                blocos[-1] += atual
            else:
                blocos.append(atual)
    return [" ".join(b) for b in blocos]


def destacar(blocos):
    """Troca *palavras* por texto dourado no formato ASS, mesmo quando o destaque cruza blocos."""
    saida, dentro = [], False
    for bloco in blocos:
        partes = []
        for palavra in bloco.split():
            inicio = palavra.startswith("*")
            fim = palavra.rstrip(".,;:!?").endswith("*")
            limpa = palavra.replace("*", "")
            if dentro or inicio:
                partes.append(f"{{\\c&H4CC8F5&}}{limpa}{{\\c&HFFFFFF&}}")
            else:
                partes.append(limpa)
            if inicio:
                dentro = True
            if fim:
                dentro = False
        saida.append(" ".join(partes))
    return saida


def tempo_ass(segundos):
    h = int(segundos // 3600)
    m = int(segundos % 3600 // 60)
    s = segundos % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def distribuir(texto, inicio, fim):
    """Divide o intervalo [inicio, fim] entre os blocos do texto, pelo tamanho de cada um."""
    blocos = dividir_legendas(texto)
    pesos = [len(b.replace("*", "")) + 4 for b in blocos]  # +4 compensa as pausas entre blocos
    total, t, saida = sum(pesos), inicio, []
    for bloco, peso in zip(destacar(blocos), pesos):
        proximo = t + (fim - inicio) * peso / total
        saida.append((bloco, t, proximo))
        t = proximo
    return saida


def escrever_legendas(destino, roteiro, titulo, duracao_fala, duracao_total, tempos=None):
    """Gera um .ass com o titulo no topo e as legendas sincronizadas com a fala."""
    if tempos and len(tempos[0]) >= 3:
        trechos = [t for a, b, texto, *_ in tempos for t in distribuir(texto, a, b)]
    elif tempos:
        paragrafos = [p for p in roteiro.splitlines() if p.strip()]
        trechos = [t for p, (a, b) in zip(paragrafos, tempos) for t in distribuir(p, a, b)]
    else:
        trechos = distribuir(roteiro, 0.0, duracao_fala)
    linhas = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {LARGURA}",
        f"PlayResY: {ALTURA}",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        # Cores ASS sao &HAABBGGRR. Legenda branca com contorno escuro; titulo dourado
        # na fonte classica da marca.
        f"Style: Legenda,{FONTE_LEGENDA},92,&H00FFFFFF,&H00FFFFFF,&H00141414,&H80000000,"
        "0,0,0,0,100,100,0,0,1,7,4,2,90,90,600,1",
        f"Style: Titulo,{FONTE_TITULO},66,&H004CC8F5,&H004CC8F5,&H00101010,&H96000000,"
        "1,0,0,0,100,100,2,0,1,4,3,8,90,90,190,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    if titulo:
        linhas.append(
            f"Dialogue: 1,{tempo_ass(0)},{tempo_ass(duracao_total)},Titulo,,0,0,0,,"
            f"{{\\fad(300,300)}}{titulo.upper()}"
        )
    for bloco, inicio, fim in trechos:
        linhas.append(
            f"Dialogue: 0,{tempo_ass(inicio)},{tempo_ass(fim)},Legenda,,0,0,0,,"
            f"{{\\fad(60,60)\\fscx88\\fscy88\\t(0,110,\\fscx100\\fscy100)}}{bloco}"
        )
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def faixa_escura(destino):
    """PNG transparente que escurece de leve a area das legendas, para o texto ler bem em imagem clara."""
    from PIL import Image
    faixa = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    centro, raio = 1340, 330  # centro vertical das legendas e meia altura da faixa
    for y in range(centro - raio, centro + raio):
        alfa = int(110 * max(0.0, 1 - abs(y - centro) / raio) ** 0.8)
        faixa.paste((0, 0, 0, alfa), (0, y, LARGURA, y + 1))
    faixa.save(destino)


def montar(pasta):
    pasta = Path(pasta).resolve()
    cfg = json.loads((pasta / "video.json").read_text(encoding="utf-8"))
    imagens = [pasta / i for i in cfg["imagens"]]
    narracao = pasta / cfg["narracao"] if cfg.get("narracao") else None
    musica = pasta / cfg["musica"] if cfg.get("musica") else None

    duracao_fala = duracao_audio(narracao) if narracao else float(cfg["duracao"])
    duracao_total = duracao_fala + FOLGA_FINAL
    n = len(imagens)
    tempos = (json.loads((pasta / cfg["tempos"]).read_text(encoding="utf-8"))
              if cfg.get("tempos") else None)
    if cfg.get("cenas"):
        # A troca de imagem termina um pouco antes da primeira frase do paragrafo.
        comeco = {}
        for a, _, _, paragrafo in tempos:
            comeco.setdefault(paragrafo, a)
        inicios = [0] + [max(0, comeco[p] - TRANSICAO) for p in cfg["cenas"][1:]]
    else:
        # Segundo em que cada imagem entra; sem "inicios", todas duram o mesmo tempo.
        inicios = cfg.get("inicios") or [i * duracao_total / n for i in range(n)]
    fins = inicios[1:] + [duracao_total]

    roteiro = cfg.get("roteiro") or (pasta / "roteiro.txt").read_text(encoding="utf-8")
    escrever_legendas(pasta / "legendas.ass", roteiro, cfg.get("titulo", ""),
                      duracao_fala, duracao_total, tempos)
    fontes = Path(os.path.relpath(FONTES, pasta)).as_posix()

    # Planos: cada imagem vira um plano aberto e, se ficar muito tempo na tela,
    # tambem um close, para a imagem mudar a cada poucos segundos.
    planos = []  # (imagem, inicio, fim, movimento)
    for i, (a, b) in enumerate(zip(inicios, fins)):
        aberto = "aproxima" if i % 2 == 0 else "abre"
        partes = max(1, math.ceil((b - a) / PLANO_MAXIMO))
        for j in range(partes):
            movimento = aberto if j % 2 == 0 else "close"
            planos.append((i, a + (b - a) * j / partes, a + (b - a) * (j + 1) / partes, movimento))
    focos = cfg.get("focos") or [0.36] * len(imagens)

    faixa_escura(pasta / "faixa.png")
    entradas, filtros = [], []
    for k, (i, a, b, movimento) in enumerate(planos):
        entradas += ["-i", str(imagens[i])]
        sobra = 0 if k == len(planos) - 1 else (CORTE if planos[k + 1][0] == i else TRANSICAO)
        quadros = int(round((b - a + sobra) * FPS))
        z0, z1, foco = MOVIMENTOS[movimento]
        foco = focos[i] if foco is None else foco
        zoom = f"{z0}+({z1 - z0})*on/{quadros}"
        y = f"max(0,min(ih-ih/zoom,ih*{foco}-ih/zoom/2))"
        filtros.append(
            f"[{k}:v]scale={LARGURA * 2}:{ALTURA * 2}:force_original_aspect_ratio=increase,"
            f"crop={LARGURA * 2}:{ALTURA * 2},setsar=1,"
            f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='{y}'"
            f":d={quadros}:s={LARGURA}x{ALTURA}:fps={FPS},format=yuv420p[v{k}]"
        )
    atual = "v0"
    for k in range(1, len(planos)):
        fusao = CORTE if planos[k][0] == planos[k - 1][0] else TRANSICAO
        filtros.append(
            f"[{atual}][v{k}]xfade=transition=fade:duration={fusao}"
            f":offset={planos[k][1]:.3f}[x{k}]"
        )
        atual = f"x{k}"
    n = len(planos) + 1  # planos + faixa escura
    entradas += ["-i", "faixa.png"]
    filtros.append(f"[{atual}][{len(planos)}:v]overlay=0:0[escurecido]")
    filtros.append(
        f"[escurecido]trim=duration={duracao_total:.3f},eq=contrast=1.06:saturation=0.92,"
        f"vignette=PI/4.5,subtitles=legendas.ass:fontsdir='{fontes}',"
        f"fade=t=in:st=0:d=0.4,fade=t=out:st={duracao_total - 0.5:.3f}:d=0.5[video]"
    )

    audio = []
    if narracao:
        entradas += ["-i", str(narracao)]
        voz = n
        ambiente = cfg.get("ambiente", True)
        if ambiente:
            # Pad suave em la menor, com leve desafinacao e respiracao lenta, bem baixo.
            notas = [(110, 0.5), (110.4, 0.3), (164.8, 0.35), (220, 0.25), (261.6, 0.15),
                     (329.6, 0.08)]
            onda = "+".join(f"{a}*sin(2*PI*{f}*t)" for f, a in notas)
            filtros.append(
                f"aevalsrc='{onda}':s=44100:d={duracao_total:.3f},lowpass=f=700,"
                f"volume='0.75+0.25*sin(2*PI*0.08*t)':eval=frame,aecho=0.8:0.7:120|240:0.3|0.2,"
                f"volume={cfg.get('volume_ambiente', 0.09)},afade=t=in:d=2,"
                f"afade=t=out:st={duracao_total - 2:.3f}:d=2[amb]"
            )
        if musica:
            entradas += ["-stream_loop", "-1", "-i", str(musica)]
            vol = cfg.get("volume_musica", 0.12)
            filtros.append(
                f"[{n + 1}:a]volume={vol},afade=t=out:st={duracao_total - 1.5:.3f}:d=1.5[mus]"
            )
            fundo = "[mus][amb]" if ambiente else "[mus]"
        else:
            fundo = "[amb]" if ambiente else ""
        if fundo:
            n_fundo = fundo.count("[")
            filtros.append(f"[{voz}:a]apad=whole_dur={duracao_total:.3f}[voz]")
            filtros.append(f"[voz]{fundo}amix=inputs={1 + n_fundo}:duration=first"
                           f":normalize=0[audio]")
        else:
            filtros.append(f"[{voz}:a]anull[audio]")
        audio = ["-map", "[audio]", "-c:a", "aac", "-b:a", "192k"]

    comando = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *entradas,
        "-filter_complex", ";".join(filtros), "-map", "[video]", *audio,
        "-t", f"{duracao_total:.3f}", "-c:v", "libx264", "-preset", "medium",
        "-crf", "20", "-r", str(FPS), "-movflags", "+faststart", "short.mp4",
    ]
    # Roda dentro da pasta para o filtro de legendas achar "legendas.ass" sem
    # problemas de caminho (principalmente no Windows).
    subprocess.run(comando, cwd=pasta, check=True)
    print(f"Pronto: {pasta / 'short.mp4'} ({duracao_total:.1f}s)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    montar(sys.argv[1])
