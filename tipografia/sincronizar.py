#!/usr/bin/env python3
"""
Sincroniza a letra com a música automaticamente e gera o projeto .json.

Você fornece:
  - o áudio da música (mp3/m4a/wav), de uma fonte que você tem direito de usar
  - letra.txt: um trecho por linha (cada linha vira uma cena). Opcional: prefixo de estilo
        gigante: PALAVRA
        pilha: LINHA 1 / LINHA 2
        frase normal (estilo escolhido automaticamente)

Modos de sincronia:
  auto  (padrão) reconhecimento de voz com tempo por palavra (pip install faster-whisper)
  tap   você ouve a música e aperta ENTER no começo de cada linha (não precisa instalar nada)

Exemplos:
  python3 sincronizar.py musica.mp3 letra.txt --inicio 47 --fim 62
  python3 sincronizar.py musica.mp3 letra.txt --inicio 47 --fim 62 --modo tap
  python3 sincronizar.py musica.mp3 letra.txt --inicio 47 --fim 62 --tema vermelho --render
"""
import argparse, difflib, json, os, re, subprocess, sys, time, unicodedata
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
SR = 22050

TEMAS = {
    # rotação de estilos pra linhas normais + ajustes visuais
    "noite":    {"rot": ["revelar", "flash", "revelar", "pilha"], "pilha": {"paleta": "sangue"}},
    "vermelho": {"rot": ["pilha", "revelar", "pilha", "flash"], "pilha": {"paleta": "sangue"},
                 "revelar": {"paleta": "sangue", "cor_apagada": "#5c1200"}, "gigante": {"bg": "#9a0000", "cor": "#ff8418"}},
    "rosa":     {"rot": ["revelar", "pilha", "flash", "pilha"], "pilha": {"paleta": "rosa"}},
    "bordo":    {"rot": ["serifa", "cursiva", "serifa", "revelar"], "gigante": {"fonte": "playfair", "bg": "#5e0b1c", "cor": "#cbc2b1"}},
    "cursiva":  {"rot": ["cursiva", "revelar", "cursiva", "flash"]},
}


# ------------------------------------------------------------------ áudio
def carregar(audio, inicio, fim):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(inicio)]
    if fim:
        cmd += ["-t", str(fim - inicio)]
    cmd += ["-i", audio, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32)


def detectar_batidas(y, max_por_seg=1.0, limiar=2.0):
    """Fluxo espectral nas graves/médias -> picos fortes = batidas."""
    hop, n = 512, 2048
    if len(y) < n:
        return []
    jan = np.hanning(n)
    quadros = np.lib.stride_tricks.sliding_window_view(y, n)[::hop] * jan
    mag = np.abs(np.fft.rfft(quadros, axis=1))[:, :200]  # até ~2 kHz
    mag = np.log1p(mag * 10)
    fluxo = np.maximum(0, np.diff(mag, axis=0)).sum(axis=1)
    fluxo = (fluxo - np.median(fluxo)) / (fluxo.std() + 1e-9)
    t = (np.arange(len(fluxo)) + 1) * hop / SR + n / (2 * SR)  # centro da janela
    dist = int(SR / hop / max_por_seg)
    picos = []
    for i in np.argsort(-fluxo):
        if fluxo[i] < limiar:
            break
        if all(abs(i - j) >= dist for j in picos):
            picos.append(i)
    return sorted(round(float(t[i]), 2) for i in picos)


# ------------------------------------------------------------------ letra
def ler_letra(caminho):
    linhas = []
    for bruto in open(caminho, encoding="utf-8"):
        bruto = bruto.strip()
        if not bruto or bruto.startswith("#"):
            continue
        m = re.match(r"^(revelar|pilha|flash|gigante|serifa|cursiva|maquina|circulo)\s*:\s*(.+)$", bruto, re.I)
        estilo, texto = (m.group(1).lower(), m.group(2)) if m else (None, bruto)
        linhas.append({"estilo": estilo, "texto": texto})
    return linhas


def norm(p):
    p = unicodedata.normalize("NFD", p.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in p if unicodedata.category(c) != "Mn"))


def palavras_da_linha(texto):
    return [w for w in texto.replace("/", " ").split() if norm(w)]


# ------------------------------------------------------------------ sincronia
def transcrever(audio_wav, modelo, idioma):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("Instale o reconhecimento de voz:  pip install faster-whisper\n"
                 "(ou use --modo tap pra sincronizar apertando ENTER)")
    m = WhisperModel(modelo, device="auto", compute_type="int8")
    segs, _ = m.transcribe(audio_wav, language=idioma, word_timestamps=True, vad_filter=False)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in (s.words or [])]


def alinhar(letra_palavras, transcritas):
    """Casa as palavras da letra com as reconhecidas e interpola as que faltarem."""
    a = [norm(w) for w in letra_palavras]
    b = [norm(w) for w, _, _ in transcritas]
    tempos = [None] * len(a)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                tempos[i1 + k] = transcritas[j1 + k][1]
    # palavras muito parecidas (erro de reconhecimento) dentro de blocos 'replace' desiguais
    conhecidos = [i for i, t in enumerate(tempos) if t is not None]
    if not conhecidos:
        return None
    for i in range(len(tempos)):
        if tempos[i] is None:
            antes = max([k for k in conhecidos if k < i], default=None)
            depois = min([k for k in conhecidos if k > i], default=None)
            if antes is not None and depois is not None:
                tempos[i] = tempos[antes] + (tempos[depois] - tempos[antes]) * (i - antes) / (depois - antes)
            elif antes is not None:
                tempos[i] = tempos[antes] + 0.35 * (i - antes)
            else:
                tempos[i] = max(0.0, tempos[depois] - 0.35 * (depois - i))
    # garante ordem crescente
    for i in range(1, len(tempos)):
        tempos[i] = max(tempos[i], tempos[i - 1] + 0.05)
    return [round(t, 3) for t in tempos]


def modo_tap(audio, inicio, fim, linhas):
    player = next((p for p in ("ffplay", "mpv") if subprocess.run(["which", p], capture_output=True).returncode == 0), None)
    if not player:
        sys.exit("Modo tap precisa do ffplay (vem com o ffmpeg) ou mpv pra tocar a música.")
    print("\nAperte ENTER no instante em que cada linha COMEÇA a ser cantada.\n")
    input("Pronto? ENTER pra tocar...")
    args = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-ss", str(inicio)] if player == "ffplay" \
        else ["mpv", "--no-video", "--really-quiet", f"--start={inicio}"]
    if fim:
        args += (["-t", str(fim - inicio)] if player == "ffplay" else [f"--end={fim}"])
    proc = subprocess.Popen(args + [audio])
    t0 = time.time()
    marcas = []
    for ln in linhas:
        input(f"  -> {ln['texto']}")
        marcas.append(round(time.time() - t0 - 0.08, 3))  # compensa reflexo
    proc.terminate()
    return marcas


# ------------------------------------------------------------------ projeto
def montar(linhas, inicios, tempos_palavra, dur_total, batidas, tema, audio, inicio):
    cfg = TEMAS[tema]
    cenas, rot = [], 0
    for i, ln in enumerate(linhas):
        ini = inicios[i]
        fim = inicios[i + 1] if i + 1 < len(linhas) else min(dur_total, ini + 3.0)
        n = len(palavras_da_linha(ln["texto"]))
        est = ln["estilo"]
        if not est:
            if n == 1:
                est = "gigante"
            else:
                est = cfg["rot"][rot % len(cfg["rot"])]
                rot += 1
        cena = {"estilo": est, "inicio": round(ini, 3), "fim": round(max(fim, ini + 0.4), 3), "texto": ln["texto"]}
        cena.update(cfg.get(est, {}))
        if est == "gigante":
            cena["texto"] = ln["texto"].upper()
            cena["inverter"] = (i % 2 == 1) and "bg" not in cena
        if est in ("pilha", "serifa") and "/" not in ln["texto"] and n > 2:
            # quebra em grupos de 1-2 palavras pra empilhar
            ws = ln["texto"].split()
            cena["texto"] = " / ".join(" ".join(ws[k:k + 2]) for k in range(0, len(ws), 2))
        if est == "cursiva":
            cena["claro"] = i % 2 == 0
        tp = tempos_palavra[i] if tempos_palavra else None
        if tp and est in ("revelar", "flash", "pilha", "serifa"):
            unidades = [u.strip() for u in cena["texto"].split("/")] if est in ("pilha", "serifa") and "/" in cena["texto"] else None
            if unidades:  # um tempo por bloco empilhado = tempo da 1ª palavra do bloco
                idx, ts = 0, []
                for u in unidades:
                    ts.append(tp[idx])
                    idx += len(palavras_da_linha(u))
                cena["tempos"] = [max(cena["inicio"], t) for t in ts]
            elif len(tp) == len(cena["texto"].split()):
                cena["tempos"] = [max(cena["inicio"], t) for t in tp]
        if est == "cursiva" and tp:
            cena["ritmo"] = min(0.95, max(0.3, (tp[-1] - ini + 0.3) / max(0.1, cena["fim"] - ini)))
        cenas.append(cena)
    if cenas and cenas[0]["inicio"] > 0.05:
        cenas[0]["inicio"] = 0.0  # tela não começa vazia
    return {"audio": os.path.abspath(audio), "audio_inicio": inicio, "duracao": round(dur_total, 2),
            "batidas": batidas, "cenas": cenas}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("letra")
    ap.add_argument("--inicio", type=float, default=0.0, help="segundo da música onde o vídeo começa")
    ap.add_argument("--fim", type=float, help="segundo da música onde o vídeo termina")
    ap.add_argument("--modo", choices=["auto", "tap"], default="auto")
    ap.add_argument("--modelo", default="small", help="tiny/base/small/medium/large-v3 (maior = mais preciso)")
    ap.add_argument("--idioma", help="pt, en... (auto se omitido)")
    ap.add_argument("--tema", choices=list(TEMAS), default="noite")
    ap.add_argument("-o", "--saida", help="caminho do .json (padrão: projetos/<letra>.json)")
    ap.add_argument("--render", action="store_true", help="já renderiza o MP4 com áudio")
    a = ap.parse_args()

    linhas = ler_letra(a.letra)
    if not linhas:
        sys.exit("letra.txt está vazio")
    y = carregar(a.audio, a.inicio, a.fim)
    dur = len(y) / SR
    print(f"áudio: {dur:.1f}s  |  {len(linhas)} linhas")
    batidas = detectar_batidas(y)
    print(f"batidas fortes: {len(batidas)}")

    tempos_palavra = None
    if a.modo == "tap":
        inicios = modo_tap(a.audio, a.inicio, a.fim, linhas)
    else:
        wav = os.path.join(AQUI, ".trecho_tmp.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.inicio)] + (["-t", str(a.fim - a.inicio)] if a.fim else [])
                       + ["-i", a.audio, "-ac", "1", "-ar", "16000", wav], check=True)
        print("reconhecendo a voz (pode levar 1-2 min na 1ª vez, baixa o modelo)...")
        trans = transcrever(wav, a.modelo, a.idioma)
        os.remove(wav)
        todas = [w for ln in linhas for w in palavras_da_linha(ln["texto"])]
        tp = alinhar(todas, trans)
        if tp is None:
            sys.exit("Não reconheci a letra nesse trecho. Confira --inicio/--fim ou use --modo tap.")
        tempos_palavra, k = [], 0
        for ln in linhas:
            n = len(palavras_da_linha(ln["texto"]))
            tempos_palavra.append(tp[k:k + n])
            k += n
        inicios = [t[0] if t else 0 for t in tempos_palavra]
        casadas = sum(1 for w in todas if norm(w) in {norm(x) for x, _, _ in trans})
        print(f"palavras reconhecidas: {casadas}/{len(todas)}")

    proj = montar(linhas, inicios, tempos_palavra, dur, batidas, a.tema, a.audio, a.inicio)
    saida = a.saida or os.path.join(AQUI, "projetos", os.path.splitext(os.path.basename(a.letra))[0] + ".json")
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    json.dump(proj, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("projeto ->", saida)
    if a.render:
        subprocess.run([sys.executable, os.path.join(AQUI, "tipografia.py"), saida], check=True)


if __name__ == "__main__":
    main()
