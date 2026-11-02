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

Opções: --voz pt_BR-faber-medium (padrão: roteiro.audio.vozLocal), --velocidade 0.9
(menor = mais rápido), --modelos models/
"""
import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
PONTUACAO = set(".,;:!?¡¿…—-\"'()")
PAUSA_ENTRE_FRASES = 0.12  # segundos de silêncio entre frases


def baixar_modelo(voz, pasta):
    onnx = pasta / f"{voz}.onnx"
    if not (onnx.exists() and (pasta / f"{voz}.onnx.json").exists()):
        print(f"baixando o modelo de voz {voz} em {pasta} ...")
        pasta.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([sys.executable, "-m", "piper.download_voices", voz, "--download-dir", str(pasta)])
        if r.returncode != 0:
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roteiro")
    ap.add_argument("--voz")
    ap.add_argument("--velocidade", type=float)
    ap.add_argument("--modelos", default=str(RAIZ / "models"))
    a = ap.parse_args()

    try:
        from piper import PiperVoice, SynthesisConfig
    except ImportError:
        sys.exit("Piper não instalado. Rode: pip install -r requirements.txt")

    roteiro = json.loads(Path(a.roteiro).read_text(encoding="utf-8"))
    cfg = roteiro.get("audio", {})
    voz = a.voz or cfg.get("vozLocal", "pt_BR-faber-medium")
    velocidade = a.velocidade or cfg.get("velocidadeLocal", 0.9)
    voice = PiperVoice.load(baixar_modelo(voz, Path(a.modelos)))
    syn = SynthesisConfig(length_scale=velocidade)
    sr = voice.config.sample_rate

    pasta = RAIZ / "output" / "audio"
    pasta.mkdir(parents=True, exist_ok=True)
    for cena in roteiro["cenas"]:
        texto = cena.get("narracao")
        if not texto:
            continue
        chunks = list(voice.synthesize(texto, syn, include_alignments=True))
        gap = np.zeros(int(PAUSA_ENTRE_FRASES * sr), dtype=np.float32)
        partes = []
        for i, ch in enumerate(chunks):
            partes += [gap] if i else []
            partes.append(ch.audio_float_array)
        audio = np.concatenate(partes) if partes else np.zeros(1, dtype=np.float32)
        with wave.open(str(pasta / f"{cena['id']}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
        meta = {"voz": voz, "duracao": round(len(audio) / sr, 3), "palavras": tempos_das_palavras(voice, texto, chunks, sr)}
        (pasta / f"{cena['id']}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        alinhado = "alinhado" if any(c.phoneme_alignments for c in chunks) else "estimado"
        print(f"{cena['id']}: {meta['duracao']:.2f} s ({alinhado})")

    # remove narrações antigas de outro provedor para o render não misturar
    for mp3 in pasta.glob("*.mp3"):
        if (pasta / f"{mp3.stem}.wav").exists():
            mp3.unlink()
    print("narração ->", pasta.relative_to(RAIZ))


if __name__ == "__main__":
    main()
