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

## Versão viral (áudio)

- **Narração ElevenLabs** (`audio/elevenlabs.js`): gera a fala de cada cena com timestamps por palavra.
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

## Personagem

Corredor estilizado montado com primitivas: boné azul com o logo, camisa azul com o logo no
peito e "AMIGOS DO SERGINHO" nas costas, short azul com faixa verde, munhequeiras verdes, meias
brancas e tênis azuis com solado branco. Veja `output/sheets/amigos_do_serginho_personagem.png`.
