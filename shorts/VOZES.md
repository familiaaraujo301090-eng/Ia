# Como gerar as vozes (passo a passo para qualquer sessão)

A narração é feita no próprio computador, de graça, com o **Kokoro** (modelo de voz aberto),
pelo script `shorts/gerar_voz.py`. Não usa site nem conta.

## 1. Instalar (uma vez)
```
pip install kokoro-onnx soundfile numpy
```

## 2. Baixar o modelo de voz (uma vez, ~350 MB)
Os arquivos **não vão para o GitHub** (estão no `.gitignore`), então cada sessão nova precisa baixar:
```
mkdir -p shorts/modelo-voz && cd shorts/modelo-voz
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
cd ../..
```
Confira: `ls -la shorts/modelo-voz` deve mostrar `kokoro-v1.0.onnx` (~325 MB) e `voices-v1.0.bin` (~28 MB).
Se o download falhar, a rede do ambiente precisa liberar `github.com` e `objects.githubusercontent.com`.

## 3. Escrever o roteiro
Crie uma pasta e um `roteiro.txt` dentro dela, **um parágrafo por linha** (cada linha vira uma cena).
Use `*asteriscos*` na frase-chave (ela fica dourada na legenda; os asteriscos não são falados).

## 4. Gerar a voz
```
python shorts/gerar_voz.py shorts/MINHA-PASTA pm_alex 1.12 0.95 --rapido
```
- `pm_alex`: voz masculina em português do Brasil (a atual do canal; a antiga era `pm_santa`).
- `1.12`: velocidade (1.0 = normal; 1.12 a 1.18 para shorts dinâmicos).
- `0.95`: tom (abaixo de 1 deixa mais grave).
- `--rapido`: pausas curtas entre frases (ritmo de short).

Saem dois arquivos na pasta:
- `narracao.wav`: a voz.
- `tempos.json`: início e fim de cada frase (o editor usa para sincronizar legenda e imagens).

## Problemas comuns
- `No module named kokoro_onnx` → faltou o passo 1.
- `No such file ... kokoro-v1.0.onnx` → faltou o passo 2 (o modelo não vem no git).
- Erro do `espeak`/`phonemizer` → `pip install espeakng-loader phonemizer` (já vem com o kokoro-onnx; reinstale se der erro).
- Voz muito lenta/rápida → mude o terceiro número (velocidade).
