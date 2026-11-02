"""Gera a narração do vídeo localmente, sem API paga, com o Piper TTS.

Para cada cena do roteiro que tem "narracao", cria:
  output/audio/<cena>.wav   a fala
  output/audio/<cena>.json  {"duracao": s, "palavras": [{"w", "t0", "t1"}]}
O render.js lê esses arquivos para ajustar a duração das cenas e sincronizar
as legendas palavra por palavra.

Os áudios (output/audio/) e o modelo de voz (models/) ficam fora do Git.
Depois de clonar o repositório:

  pip install -r requirements.txt
  python3 gerar_voz.py roteiro/amigos_do_serginho.json      # baixa o modelo na 1ª vez
  npm run render

Motores: Piper (voz neural, padrão) ou, se o modelo não puder ser baixado, espeak-ng com
voz MBROLA brasileira (apt install espeak-ng mbrola mbrola-br3), mais robótica.
Opções: --motor auto|piper|espeak, --voz, --velocidade, --modelos models/
"""
import argparse
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
PONTUACAO = set(".,;:!?¡¿…—-\"'()")
PAUSA_ENTRE_FRASES = 0.12  # segundos de silêncio entre frases


def baixar_modelo(voz, pasta, sair=True):
    onnx = pasta / f"{voz}.onnx"
    if not (onnx.exists() and (pasta / f"{voz}.onnx.json").exists()):
        print(f"baixando o modelo de voz {voz} em {pasta} ...")
        pasta.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([sys.executable, "-m", "piper.download_voices", voz, "--download-dir", str(pasta)],
                           capture_output=not sair)
        if r.returncode != 0:
            if not sair:
                print(f"aviso: não consegui baixar o modelo {voz} do Piper (huggingface.co)")
                return None
            sys.exit(
                f"Não consegui baixar {voz} (precisa de acesso a huggingface.co).\n"
                f"Baixe {voz}.onnx e {voz}.onnx.json de https://huggingface.co/rhasspy/piper-voices "
                f"e coloque em {pasta}/"
            )
    return onnx


def grupos_por_palavra(voice, palavras):
    """Quantas "palavras fonéticas" cada palavra do texto vira (ex.: "42" -> "quarenta e dois" = 3)."""
    out = []
    for w in palavras:
        fon = [p for frase in voice.phonemize(w) for p in frase]
        grupos = [g for g in "".join(fon).split(" ") if any(c not in PONTUACAO for c in g)]
        out.append((max(1, len(grupos)), sum(len(g) for g in grupos) or 1))
    return out


def spans_foneticos(chunks, sr):
    """Tempo (início, fim, nº de fonemas) de cada palavra fonética, usando os alinhamentos do modelo
    quando existem; senão divide cada frase proporcionalmente ao número de fonemas."""
    spans, t = [], 0.0
    for ch in chunks:
        dur = len(ch.audio_float_array) / sr
        if ch.phoneme_alignments:
            cur, tt = None, t
            for al in ch.phoneme_alignments:
                d = al.num_samples / sr
                p = al.phoneme
                if p == " " or p in ("^", "$", "_"):
                    if cur:
                        spans.append(cur)
                    cur = None
                elif p in PONTUACAO:
                    pass
                elif cur is None:
                    cur = [tt, tt + d, 1]
                else:
                    cur[1], cur[2] = tt + d, cur[2] + 1
                tt += d
            if cur:
                spans.append(cur)
        else:
            grupos = [g for g in "".join(ch.phonemes).split(" ") if any(c not in PONTUACAO for c in g)]
            total = sum(len(g) for g in grupos) or 1
            util = dur * 0.92  # o modelo deixa um respiro no começo e no fim da frase
            tt = t + dur * 0.04
            for g in grupos:
                d = util * len(g) / total
                spans.append([tt, tt + d, len(g)])
                tt += d
        t += dur + PAUSA_ENTRE_FRASES
    return spans


def tempos_das_palavras(voice, texto, chunks, sr):
    palavras = texto.split()
    grupos = grupos_por_palavra(voice, palavras)
    spans = spans_foneticos(chunks, sr)
    out = []
    if sum(n for n, _ in grupos) == len(spans):
        i = 0
        for w, (n, _) in zip(palavras, grupos):
            out.append({"w": w, "t0": round(spans[i][0], 3), "t1": round(spans[i + n - 1][1], 3)})
            i += n
    else:
        # contagens não bateram (ex.: abreviação): distribui pelo tamanho fonético no tempo falado
        ini, fim = spans[0][0], spans[-1][1]
        total = sum(c for _, c in grupos)
        t = ini
        for w, (_, c) in zip(palavras, grupos):
            d = (fim - ini) * c / total
            out.append({"w": w, "t0": round(t, 3), "t1": round(t + d, 3)})
            t += d
    return out


def ler_wav(path):
    with wave.open(str(path), "rb") as w:
        sr, n = w.getframerate(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float32) / 32768
        if w.getnchannels() > 1:
            x = x.reshape(-1, w.getnchannels()).mean(axis=1)
    return x, sr


def trechos_falados(x, sr, silencio_min=0.12):
    """(início, fim) em segundos dos trechos com voz, separados por silêncios."""
    hop = int(sr * 0.01)
    e = np.array([np.sqrt(np.mean(x[i : i + hop] ** 2)) for i in range(0, len(x) - hop, hop)])
    voz = e > max(e.max() * 0.04, 1e-4)
    segs, ini, mudo = [], None, 0
    for i, v in enumerate(voz):
        if v:
            ini = i if ini is None else ini
            mudo = 0
        elif ini is not None:
            mudo += 1
            if mudo * 0.01 >= silencio_min:
                segs.append([ini * 0.01, (i - mudo + 1) * 0.01])
                ini, mudo = None, 0
    if ini is not None:
        segs.append([ini * 0.01, len(voz) * 0.01])
    return segs


def espeak(texto, destino, voz, wpm):
    subprocess.run(["espeak-ng", "-v", voz, "-s", str(wpm), "-w", str(destino), texto], check=True, capture_output=True)


def gerar_cena_espeak(texto, destino, voz, wpm, tmp):
    """Fala com espeak-ng (vozes MBROLA pt-BR). O tempo de cada palavra é estimado pela
    duração dela falada isoladamente, encaixada nos trechos de voz entre as pausas."""
    espeak(texto, destino, voz, wpm)
    x, sr = ler_wav(destino)
    palavras = texto.split()
    pesos = []
    for w in palavras:
        limpo = w.strip("".join(PONTUACAO))
        espeak(limpo or w, tmp, voz, wpm)
        y, _ = ler_wav(tmp)
        seg = trechos_falados(y, sr, 0.5)
        pesos.append(sum(b - a for a, b in seg) or 0.1)
    # frases: palavras até a próxima pontuação
    frases, cur = [], []
    for i, w in enumerate(palavras):
        cur.append(i)
        if w[-1] in PONTUACAO:
            frases.append(cur)
            cur = []
    if cur:
        frases.append(cur)
    segs = trechos_falados(x, sr)
    if len(segs) != len(frases):
        segs, frases = [[segs[0][0], segs[-1][1]]], [list(range(len(palavras)))]
    out = [None] * len(palavras)
    for (a, b), idx in zip(segs, frases):
        tot = sum(pesos[i] for i in idx)
        t = a
        for i in idx:
            d = (b - a) * pesos[i] / tot
            out[i] = {"w": palavras[i], "t0": round(t, 3), "t1": round(t + d, 3)}
            t += d
    return len(x) / sr, out


def carregar_piper(a, cfg):
    try:
        from piper import PiperVoice, SynthesisConfig
    except ImportError:
        return None
    voz = a.voz or cfg.get("vozLocal", "pt_BR-faber-medium")
    onnx = baixar_modelo(voz, Path(a.modelos), sair=a.motor == "piper")
    if not onnx:
        return None
    voice = PiperVoice.load(onnx)
    return voz, voice, SynthesisConfig(length_scale=a.velocidade or cfg.get("velocidadeLocal", 0.9))


def gerar_cena_piper(texto, destino, voice, syn):
    sr = voice.config.sample_rate
    chunks = list(voice.synthesize(texto, syn, include_alignments=True))
    gap = np.zeros(int(PAUSA_ENTRE_FRASES * sr), dtype=np.float32)
    partes = []
    for i, ch in enumerate(chunks):
        partes += [gap] if i else []
        partes.append(ch.audio_float_array)
    audio = np.concatenate(partes) if partes else np.zeros(1, dtype=np.float32)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    return len(audio) / sr, tempos_das_palavras(voice, texto, chunks, sr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roteiro")
    ap.add_argument("--motor", choices=["auto", "piper", "espeak"], default="auto",
                    help="auto = Piper (neural) se o modelo estiver disponível, senão espeak-ng/MBROLA")
    ap.add_argument("--voz", help="Piper: ex. pt_BR-faber-medium; espeak: ex. mb-br3")
    ap.add_argument("--velocidade", type=float, help="Piper: length_scale (menor = mais rápido); espeak: palavras/min")
    ap.add_argument("--modelos", default=str(RAIZ / "models"))
    a = ap.parse_args()

    roteiro = json.loads(Path(a.roteiro).read_text(encoding="utf-8"))
    cfg = roteiro.get("audio", {})
    piper = carregar_piper(a, cfg) if a.motor in ("auto", "piper") else None
    if piper:
        voz = piper[0]
    elif shutil.which("espeak-ng"):
        voz = a.voz if a.motor == "espeak" and a.voz else cfg.get("vozEspeak", "mb-br3")
        wpm = int(a.velocidade) if a.motor == "espeak" and a.velocidade else cfg.get("velocidadeEspeak", 165)
        print(f"usando espeak-ng com a voz {voz} (instale o modelo do Piper para uma voz mais natural)")
    else:
        sys.exit("Nenhum motor de voz disponível: rode pip install -r requirements.txt "
                 "(Piper) ou instale espeak-ng + mbrola-br3.")

    pasta = RAIZ / "output" / "audio"
    pasta.mkdir(parents=True, exist_ok=True)
    tmp = pasta / "_palavra.wav"
    for cena in roteiro["cenas"]:
        texto = cena.get("narracao")
        if not texto:
            continue
        destino = pasta / f"{cena['id']}.wav"
        if piper:
            dur, palavras = gerar_cena_piper(texto, destino, piper[1], piper[2])
        else:
            dur, palavras = gerar_cena_espeak(texto, destino, voz, wpm, tmp)
        meta = {"voz": voz, "duracao": round(dur, 3), "palavras": palavras}
        (pasta / f"{cena['id']}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{cena['id']}: {dur:.2f} s")
    tmp.unlink(missing_ok=True)

    # remove narrações antigas de outro provedor para o render não misturar
    for mp3 in pasta.glob("*.mp3"):
        if (pasta / f"{mp3.stem}.wav").exists():
            mp3.unlink()
    print("narração ->", pasta.relative_to(RAIZ))


if __name__ == "__main__":
    main()
