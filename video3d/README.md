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

## Como usar

```bash
cd video3d && npm install
npm run render     # output/amigos_do_serginho.mp4 (720x1280, 30 fps, sem áudio)
npm run sheets     # output/sheets/*.png (personagem, cenário, storyboard)
npm run preview    # output/preview/*.jpg (2 quadros por cena, para revisar rápido)
```

Requer Node 18+, ffmpeg e Playwright com Chromium. O render usa WebGL por software
(SwiftShader), então roda em servidor sem GPU (~4–5 min para 38 s de vídeo).

Para fazer um vídeo novo, copie o roteiro JSON, troque textos, ações (`alongar`, `correr`,
`chegada`, `acenar`), tipos de câmera e cores; o motor recalcula percurso, posição do pórtico,
sheets e vídeo sozinho.

## Pesquisa: Amigos do Serginho (Buri - SP)

- Equipe de corrida de rua de Buri - SP ([Instagram @equipeamigosdoserginho_](https://www.instagram.com/equipeamigosdoserginho_/)).
- 2026: a equipe representou Buri na Meia Maratona Internacional de Balneário Camboriú (SC), nos 5, 10 e 21 km;
  Aline Cochetti e Silvia Correia foram premiadas nas categorias dos 10 km ([Buri Conectado](https://www.buriconectado.com/2026/05/equipe-de-buri-se-destaca-na-meia.html)).
- O líder da equipe, Matheus Ferreira, correu a Maratona de Assunção (Paraguai) em ~3h03 e foi premiado na categoria ([Jornal Ita News](https://jornalitanews.com.br/atleta-de-buri/)).
- A equipe aparece inscrita em provas locais como a 3ª Corrida da Amizade Shark Run - Buri 2024 ([OnSport](https://www.onsport.com.br/events/179-3-corrida-da-amizade-shark-run-buri-2024)).

## Roteiro (38,5 s)

| # | Cena | Tempo | Ação | Câmera | Legenda |
|---|------|-------|------|--------|---------|
| 1 | Abertura | 0–4,5 s | alonga e começa a trotar | grua descendo do céu | VOCÊ SABIA? Curiosidades da corrida com a equipe Amigos do Serginho |
| 2 | Maratona | 4,5–10,5 s | corre | travelling lateral | A maratona tem 42,195 km, usada pela primeira vez nos Jogos de Londres, em 1908 |
| 3 | Equipe | 10,5–16,5 s | corre | dolly frontal até o logo | Amigos do Serginho é uma equipe de corrida de rua de Buri, interior de SP |
| 4 | Camboriú | 16,5–22,5 s | corre | órbita de 240° | Em 2026 a equipe levou Buri à Meia Maratona de Balneário Camboriú e voltou com troféus |
| 5 | Assunção | 22,5–28,5 s | corre mais rápido | drone por trás | O líder Matheus Ferreira completou a Maratona de Assunção em ~3h03 |
| 6 | Chegada | 28,5–34 s | rompe a fita e comemora | câmera baixa | Correr junto motiva: cada quilômetro fica mais leve com os amigos |
| 7 | Encerramento | 34–38,5 s | acena | aproximação + logo | Siga a equipe: @equipeamigosdoserginho_ |

## Personagem

Corredor estilizado montado com primitivas: boné azul com o logo, camisa azul com o logo no
peito e "AMIGOS DO SERGINHO" nas costas, short azul com faixa verde, munhequeiras verdes, meias
brancas e tênis azuis com solado branco. Veja `output/sheets/amigos_do_serginho_personagem.png`.
