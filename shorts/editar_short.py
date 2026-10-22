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
  "volume_musica": 0.12,
  "fonte": "Georgia"
}

Somente "roteiro" e "imagens" sao obrigatorios. Sem "roteiro" no json, o texto
vem de roteiro.txt (um paragrafo por linha). Sem "narracao", use "duracao"
(em segundos) para gerar uma previa sem audio. Opcionais:
  "tempos": arquivo json com [inicio, fim] de cada paragrafo da narracao,
            para a legenda acompanhar a fala com precisao;
  "inicios": segundo em que cada imagem entra (a primeira sempre em 0).
O resultado sai em pasta_do_video/short.mp4. Precisa do ffmpeg instalado.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

LARGURA, ALTURA, FPS = 1080, 1920, 30
TRANSICAO = 0.6  # segundos de fusao entre imagens
FOLGA_FINAL = 0.8  # segundos depois que a narracao termina
PALAVRAS_POR_LEGENDA = 5


def duracao_audio(caminho):
    saida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(caminho)],
        capture_output=True, text=True, check=True,
    )
    return float(saida.stdout.strip())


def dividir_legendas(roteiro):
    """Quebra o roteiro em pedacos curtos, respeitando a pontuacao."""
    frases = re.split(r"(?<=[.!?;:,])\s+", roteiro.strip())
    blocos = []
    for frase in frases:
        palavras = frase.split()
        while palavras:
            blocos.append(" ".join(palavras[:PALAVRAS_POR_LEGENDA]))
            palavras = palavras[PALAVRAS_POR_LEGENDA:]
    return [b for b in blocos if b]


def tempo_ass(segundos):
    h = int(segundos // 3600)
    m = int(segundos % 3600 // 60)
    s = segundos % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def distribuir(texto, inicio, fim):
    """Divide o intervalo [inicio, fim] entre os blocos do texto, pelo tamanho de cada um."""
    blocos = dividir_legendas(texto)
    pesos = [len(b) + 4 for b in blocos]  # +4 compensa as pausas entre blocos
    total, t, saida = sum(pesos), inicio, []
    for bloco, peso in zip(blocos, pesos):
        proximo = t + (fim - inicio) * peso / total
        saida.append((bloco, t, proximo))
        t = proximo
    return saida


def escrever_legendas(destino, roteiro, titulo, duracao_fala, duracao_total, fonte, tempos=None):
    """Gera um .ass com o titulo no topo e as legendas sincronizadas com a fala."""
    if tempos:
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
        # Cores ASS sao &HAABBGGRR. Legenda branca com contorno escuro; titulo dourado.
        f"Style: Legenda,{fonte},86,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,"
        "1,0,0,0,100,100,0,0,1,6,3,2,80,80,560,1",
        f"Style: Titulo,{fonte},64,&H0060C8F0,&H0060C8F0,&H00101010,&H96000000,"
        "1,0,0,0,100,100,0,0,1,5,2,8,90,90,170,1",
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
            f"{{\\fad(80,80)\\fscx92\\fscy92\\t(0,120,\\fscx100\\fscy100)}}{bloco}"
        )
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def montar(pasta):
    pasta = Path(pasta).resolve()
    cfg = json.loads((pasta / "video.json").read_text(encoding="utf-8"))
    imagens = [pasta / i for i in cfg["imagens"]]
    narracao = pasta / cfg["narracao"] if cfg.get("narracao") else None
    musica = pasta / cfg["musica"] if cfg.get("musica") else None

    duracao_fala = duracao_audio(narracao) if narracao else float(cfg["duracao"])
    duracao_total = duracao_fala + FOLGA_FINAL
    n = len(imagens)
    # Segundo em que cada imagem entra; sem "inicios", todas duram o mesmo tempo.
    inicios = cfg.get("inicios") or [i * duracao_total / n for i in range(n)]
    fins = inicios[1:] + [duracao_total]
    # Cada imagem dura um pouco a mais para cobrir a sobreposicao da transicao.
    duracoes = [b - a + (TRANSICAO if i < n - 1 else 0)
                for i, (a, b) in enumerate(zip(inicios, fins))]

    roteiro = cfg.get("roteiro") or (pasta / "roteiro.txt").read_text(encoding="utf-8")
    tempos = json.loads((pasta / cfg["tempos"]).read_text()) if cfg.get("tempos") else None
    escrever_legendas(pasta / "legendas.ass", roteiro, cfg.get("titulo", ""),
                      duracao_fala, duracao_total, cfg.get("fonte", "Georgia"), tempos)

    entradas, filtros = [], []
    for i, img in enumerate(imagens):
        entradas += ["-i", str(img)]
        quadros = int(round(duracoes[i] * FPS))
        # Alterna zoom de aproximacao e afastamento (efeito Ken Burns).
        zoom = "1+0.12*on/{q}" if i % 2 == 0 else "1.12-0.12*on/{q}"
        filtros.append(
            f"[{i}:v]scale={LARGURA * 2}:{ALTURA * 2}:force_original_aspect_ratio=increase,"
            f"crop={LARGURA * 2}:{ALTURA * 2},setsar=1,"
            f"zoompan=z='{zoom.format(q=quadros)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={quadros}:s={LARGURA}x{ALTURA}:fps={FPS},format=yuv420p[v{i}]"
        )
    atual = "v0"
    for i in range(1, n):
        deslocamento = inicios[i]
        filtros.append(
            f"[{atual}][v{i}]xfade=transition=fade:duration={TRANSICAO}"
            f":offset={deslocamento:.3f}[x{i}]"
        )
        atual = f"x{i}"
    filtros.append(
        f"[{atual}]trim=duration={duracao_total:.3f},eq=contrast=1.06:saturation=0.92,"
        f"vignette=PI/4.5,subtitles=legendas.ass,"
        f"fade=t=in:st=0:d=0.4,fade=t=out:st={duracao_total - 0.5:.3f}:d=0.5[video]"
    )

    audio = []
    if narracao:
        entradas += ["-i", str(narracao)]
        voz = n
        if musica:
            entradas += ["-stream_loop", "-1", "-i", str(musica)]
            vol = cfg.get("volume_musica", 0.12)
            filtros.append(
                f"[{n + 1}:a]volume={vol},afade=t=out:st={duracao_total - 1.5:.3f}:d=1.5[mus]"
            )
            filtros.append(f"[{voz}:a][mus]amix=inputs=2:duration=first:normalize=0[audio]")
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
