# video3d: vídeos curtos de curiosidades em 3D, gerados por código

Pipeline 100% programático, sem editor de vídeo: **roteiro JSON → cena 3D (Three.js) → Chromium headless → ffmpeg → MP4 vertical**.

```
roteiro/amigos_do_serginho.json   roteiro + "sheets" de dados (cenas, câmeras, ações, legendas)
engine/character.js               personagem 3D procedural com esqueleto (juntas) e uniforme
engine/animation.js               linha do tempo + animações (alongar, correr, chegada, acenar)
engine/environment.js             cenário procedural (rua de Buri, casas, árvores, faixas, pórtico)
engine/camera.js                  movimentos de câmera (grua, lateral, frontal, órbita, drone, baixa, aproximar)
engine/overlay.js                 legendas, selos, logo, barra de progresso e transições
engine/sheets.js                  gera os sheets de personagem, cenário e storyboard
render.js                         servidor local + Playwright + ffmpeg
assets/logo_amigos_do_serginho.png
output/                           vídeo final e sheets gerados
```

## Narração (gerar_voz.py)

Os arquivos de voz (`output/audio/`) e modelos (`models/`) ficam fora do GitHub pelo `.gitignore`.
Quem clonar o repositório gera a narração e renderiza:

```bash
cd video3d
pip install -r requirements.txt                          # edge-tts, Piper TTS, numpy
npm install                                              # three.js
python3 gerar_voz.py roteiro/amigos_do_serginho.json     # gera output/audio/<cena>.wav + .json
npm run render                                           # vídeo final com voz, música, efeitos e legendas
```

`gerar_voz.py` usa o primeiro motor disponível (ou o escolhido com `--motor`):

| motor | voz | observação |
|---|---|---|
| `microsoft` (padrão) | `pt-BR-AntonioNeural` (neural, limpa) | via edge-tts, precisa de internet; tempos exatos de cada palavra |
| `piper` | `pt_BR-faber-medium` | neural local; baixa o modelo de huggingface.co para `models/` na 1ª vez |
| `espeak` | `mb-br3` | `sudo apt install espeak-ng mbrola mbrola-br3`; mais robótica |

Ex.: `python3 gerar_voz.py roteiro/amigos_do_serginho.json --voz pt-BR-FranciscaNeural --velocidade +10%`.
Atrás de um proxy corporativo, o edge-tts usa `HTTPS_PROXY` automaticamente.

## Versão viral (áudio)

- **Narração**: `gerar_voz.py` (voz neural da Microsoft por padrão) ou, opcionalmente, ElevenLabs (`audio/elevenlabs.js`, precisa de plano pago).
  As cenas se ajustam à duração da fala e as legendas acendem palavra por palavra no ritmo da voz.
- **Trilha e efeitos por código** (`audio/trilha.py`): batida pop (124 BPM, vi-IV-I-V), whoosh nos cortes,
  "pop" nos selos, fita + torcida na chegada e "ding" no logo final. A música abaixa sozinha sob a voz (sidechain)
  e o áudio é normalizado em -14 LUFS (padrão de Reels/TikTok/Shorts).
- **Edição viral**: legendas grandes de até 3 palavras, flash branco + punch-in de zoom em cada corte, gancho "Você sabia?" no 1º segundo.

```bash
export ELEVENLABS_API_KEY=...        # chave da sua conta ElevenLabs
export ELEVENLABS_VOICE_ID=...       # opcional; padrão = roteiro.audio.vozId
npm run audio                        # output/audio/<cena>.mp3 + .json (tempo das palavras)
npm run render                       # output/amigos_do_serginho_viral.mp4 (com voz, música e efeitos)
```

Sem a chave, o render usa o tempo estimado das palavras e gera o vídeo só com música e efeitos.

## Como usar

```bash
cd video3d && npm install
npm run render     # output/amigos_do_serginho_viral.mp4 (720x1280, 30 fps, com áudio)
npm run sheets     # output/sheets/*.png (personagem, cenário, storyboard)
npm run preview    # output/preview/*.jpg (2 quadros por cena, para revisar rápido)
```

Requer Node 18+, Python 3 com numpy, ffmpeg e Playwright com Chromium. O render usa WebGL por software
(SwiftShader), então roda em servidor sem GPU (~4–5 min para 38 s de vídeo).

Para fazer um vídeo novo, copie o roteiro JSON, troque textos, ações (`alongar`, `correr`,
`chegada`, `acenar`), tipos de câmera e cores; o motor recalcula percurso, posição do pórtico,
sheets e vídeo sozinho.

## Pesquisa: Amigos do Serginho (Buri - SP)

- Equipe de corrida de rua de Buri - SP ([Instagram @equipeamigosdoserginho_](https://www.instagram.com/equipeamigosdoserginho_/)).
- 2026: a equipe representou Buri na Meia Maratona Internacional de Balneário Camboriú (SC), nos 5, 10 e 21 km;
  Aline Cochetti e Silvia Correia foram premiadas nas categorias dos 10 km ([Buri Conectado](https://www.buriconectado.com/2026/05/equipe-de-buri-se-destaca-na-meia.html)).
- O atleta de Buri Matheus Ferreira correu a Maratona de Assunção (Paraguai) em ~3h03 e foi premiado na categoria ([Jornal Ita News](https://jornalitanews.com.br/atleta-de-buri/)).
- A equipe aparece inscrita em provas locais como a 3ª Corrida da Amizade Shark Run - Buri 2024 ([OnSport](https://www.onsport.com.br/events/179-3-corrida-da-amizade-shark-run-buri-2024)).

## Roteiro (legendas da 1ª versão; a narração está em `narracao` no JSON)

| # | Cena | Tempo | Ação | Câmera | Legenda |
|---|------|-------|------|--------|---------|
| 1 | Abertura | 0–4,5 s | alonga e começa a trotar | grua descendo do céu | VOCÊ SABIA? Curiosidades da corrida com a equipe Amigos do Serginho |
| 2 | Maratona | 4,5–10,5 s | corre | travelling lateral | A maratona tem 42,195 km, usada pela primeira vez nos Jogos de Londres, em 1908 |
| 3 | Equipe | 10,5–16,5 s | corre | dolly frontal até o logo | Amigos do Serginho é uma equipe de corrida de rua de Buri, interior de SP |
| 4 | Camboriú | 16,5–22,5 s | corre | órbita de 240° | Em 2026 a equipe levou Buri à Meia Maratona de Balneário Camboriú e voltou com troféus |
| 5 | Assunção | 22,5–28,5 s | corre mais rápido | drone por trás | O corredor de Buri Matheus Ferreira completou a Maratona de Assunção em ~3h03 |
| 6 | Chegada | 28,5–34 s | rompe a fita e comemora | câmera baixa | Correr junto motiva: cada quilômetro fica mais leve com os amigos |
| 7 | Encerramento | 34–38,5 s | acena | aproximação + logo | Siga a equipe: @equipeamigosdoserginho_ |

## Vídeo "E se..." (robozinho)

`roteiro/e_se_amigos_do_serginho.json` usa o robozinho `assets/robo.glb` (CC0) e conta uma história de
crescimento: dia 1 (1 km, sozinho) → semana 1 (amigos chegam) → mês 1 (5 km) → mês 6 (10 km) → meia
maratona. Cada cena pode ter `km` (contador animado na tela) e `amigos` (quantos clones correm junto;
cores em `personagem.coresAmigos`).

```bash
python3 gerar_voz.py roteiro/e_se_amigos_do_serginho.json
node render.js roteiro/e_se_amigos_do_serginho.json      # output/e_se_amigos_do_serginho_viral.mp4
```

## Usar um personagem 3D pronto (.glb / .fbx)

O boneco feito por código é só um ponto de partida. Para um visual de animação 3D de verdade,
use um modelo esculpido e animado:

1. **Gerar o modelo**: num site de imagem→3D (ex.: Meshy ou Tripo), envie uma imagem do personagem
   (de preferência de frente, corpo inteiro, braços levemente abertos) e exporte em `.fbx` ou `.glb`.
   Use imagens próprias ou licenciadas.
2. **Animar**: envie o modelo ao Mixamo, faça o auto-rig e baixe as animações *Running*, *Waving*,
   *Victory* (ou *Jumping*) e *Idle* — cada uma em `.fbx`, a primeira **com skin**, as outras **without skin**.
3. Coloque os arquivos em `video3d/assets/` e aponte no roteiro, dentro de `personagem`:

```json
"modelo": {
  "arquivo": "assets/corredor_run.fbx",
  "altura": 2.0,
  "rotacaoY": 0,
  "animacoes": {
    "correr": "assets/corredor_run.fbx",
    "acenar": "assets/corredor_wave.fbx",
    "comemorar": "assets/corredor_victory.fbx",
    "parado": "assets/corredor_idle.fbx"
  },
  "cores": { "NomeDoMaterialDaCamisa": "#2246a8" },
  "logo": { "osso": "Spine2", "posicao": [0, 0.1, 0.15], "tamanho": 0.22 }
}
```

- `animacoes` aceita o nome de um clipe dentro do próprio modelo (ex.: `"Running"`) ou um arquivo separado.
- `rotacaoY` corrige a frente do modelo (use `3.1416` se ele aparecer de costas).
- `cores` recolore materiais pelo nome (uniforme azul); `logo` prende o logo da equipe a um osso (peito).
- Sem `modelo`, o motor usa o boneco procedural.

## Personagem

Corredor estilizado montado com primitivas: boné azul com o logo, camisa azul com o logo no
peito e "AMIGOS DO SERGINHO" nas costas, short azul com faixa verde, munhequeiras verdes, meias
brancas e tênis azuis com solado branco. Veja `output/sheets/amigos_do_serginho_personagem.png`.
Tem contorno estilo desenho animado, olhos com pálpebras e cílios que piscam, sobrancelhas e boca
que reagem na comemoração, franja sob o boné e relógio esportivo no pulso.

## Cenário

Rua de cidade do interior: calçada portuguesa em ondas, casas térreas e sobrados com telhado de
barro, janelas com venezianas, muros com portão, comércios com toldo e placa, ipês amarelos e roxos,
postes com fiação, carros estacionados, bandeirinhas perto da chegada, grama com flores, morros e
nuvens. Os trechos onde a câmera gira em volta do corredor ficam livres de carros e árvores.
