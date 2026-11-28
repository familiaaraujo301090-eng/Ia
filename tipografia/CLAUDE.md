# CLAUDE.md — Tipografia cinética (lyric edits pro TikTok)

Este arquivo é a memória completa do projeto. Foi escrito pela sessão na nuvem que construiu tudo,
para uma sessão local continuar **exatamente** de onde parou. Leia inteiro antes de mexer.
Responda sempre em **português do Brasil**, curto e direto.

---

## 1. Quem é o usuário e o que ele quer

- Faz **edits de tipografia/letra (lyric edits) para o TikTok**. Manda vídeos de referência (edits de
  outros criadores, geralmente com marca d'água do TikTok) e pede pra eu "fazer desse": refazer com
  **o áudio da referência** e **minha própria tipografia**.
- Gosta de: **preto, branco e vermelho**; **só letras** (quando pede "sem personagens"); **sincronia
  exata palavra por palavra**; animações **dinâmicas sem exagero**; visual que **não tenha cara de IA**.
- Às vezes manda **fotos de personagens** (fan art de anime) pra usar: aí usa as fotos dele — eu
  NUNCA desenho personagem de anime (é protegido).
- Formato padrão atual: **16:11, 1440×990** (`"w": 1440, "h": 990`). Antes era vertical 1080×1920.
  Quando ele não especifica, uso 16:11.
- Às vezes pede a letra **traduzida pro português** (fez isso no "I Was Made for Lovin' You" e no
  "GUY.exe"): eu traduzo e redistribuo as palavras PT sobre os tempos cantados em inglês.

## 2. Regras que o usuário deu (obrigatórias)

1. **Música sempre no vídeo e sincronizada.** Todo vídeo entregue vai COM áudio.
2. **Letra nunca sai da tela.** Área segura: texto ≤ 80% (caber) e trava final do bloco em 86%.
   Elementos (folhas, neve, fogo, faixa) podem encostar na borda de propósito — a letra não.
   Sempre rodar `python3 verificar_bordas.py saida/x.mp4` e olhar os quadros marcados.
3. **Frase repetida em sequência pisca no ritmo** (ex.: "muitas vezes", "me deixe", "oh why oh why"):
   `"piscar": true` (flash/gigante) ou `"piscar_inverte": true` (tela inteira inverte, foto junto).
4. **Cada música nova ganha um elemento NOVO.** Só a base preto/branco(/vermelho) se repete.
5. **Sem cara de IA:** foco de lente na entrada, grão de filme, câmera viva sutil, brancos/pretos não puros.
6. **Não quer:** letra torta demais (o estilo `inclinado` de 9° foi rejeitado; inclinação ±1,6° no
   `linhas` foi aceita), **pulso nos ataques** (rejeitado — só com `"pulsar": true` se ele pedir),
   listra sobre a letra no foco, glitch RGB.
7. Palavras **reveladas em "cortina"** (esquerda→direita) foram aprovadas; a animação da referência
   (cinza desfocado → branco, espaçamento abrindo, troca em "chicote") também.
8. Quando ele diz "do jeito que você sabe" = só letras, preto/branco/vermelho, elemento novo,
   tempos exatos da referência, 16:11, com a música.

## 3. O que eu NÃO faço (e explico com educação quando ele pede)

- **Não baixo músicas da internet** (pirataria). O áudio vem SEMPRE dos vídeos/áudios que ELE manda.
  Ele já pediu várias vezes "procure e baixe" — recuso e ofereço usar o áudio dos vídeos dele.
- **Não busco letra completa na internet pra pôr na tela.** Uso o texto que aparece no vídeo de
  referência dele (é material dele). Posso pesquisar só o NOME da música.
- **Não desenho personagens protegidos** (Gojo, Yor, Eren...). Cenários genéricos de clima de anime
  eu fiz (`cenario.py`), mas ele **não gostou** — prefere fundos lisos ou as fotos que ele manda.
- **Não subo pro GitHub** áudio, fotos ou projetos com letra (estão no `.gitignore`).

## 4. Fluxo padrão para um vídeo novo (passo a passo)

```bash
# 0) ver o vídeo de referência
ffprobe -v error -show_entries format=duration:stream=codec_type,width,height -of csv=p=0 REF.mp4

# 1) mosaico com tempo (visão geral)
ffmpeg -i REF.mp4 -vf "fps=2,scale=200:-1,drawtext=fontfile=fonts/Montserrat-Bold.ttf:text='%{pts\:flt}':x=4:y=4:fontsize=18:fontcolor=red:box=1:boxcolor=white,tile=10x7" -frames:v 1 mosaico.jpg

# 2) LER OS TEMPOS EM 5 QPS (obrigatório! a 2 qps as palavras ficaram até 0,5s atrasadas — o usuário reclamou)
ffmpeg -ss 0 -to 12 -i REF.mp4 -copyts -vf "fps=5,crop=LARG:ALT:X:Y,scale=300:-1,drawtext=...,tile=5x12" -frames:v 1 t1.jpg
#    anote o PRIMEIRO quadro em que cada palavra aparece; use tempo - 0.04 no projeto

# 3) extrair o áudio
ffmpeg -y -i REF.mp4 -vn -c:a pcm_s16le audios/NOME.wav

# 4) escrever projetos/musica_NOME.json (ver seção 5) — se o vídeo começa com vinheta, use "audio_inicio"
#    e desconte esse offset de todos os tempos
# 5) prévia: um PNG por cena
python3 tipografia.py projetos/musica_NOME.json --preview -o /tmp/prev
# 6) render com áudio + conferência
python3 tipografia.py projetos/musica_NOME.json
python3 verificar_bordas.py saida/musica_NOME.mp4
# 7) olhar quadros-chave (palavras grandes) antes de entregar
```

- Corte a **vinheta do TikTok** do final (tela "Descubra mais criadores") e intros de marca d'água.
- O "refri"/@ do criador no começo NÃO é letra (erro que já cometi: cortei o "me perdoa" achando
  que era intro — sempre confira o trecho inicial com a voz).
- `referencia.py projeto.json REF.mp4 --offset S` encaixa tempos aproximados nas trocas detectadas
  quadro a quadro (útil, mas a leitura manual a 5 qps é mais confiável).
- Render de ~40s em 1440×990 leva ~4–8 min; rode em segundo plano.

## 5. O motor (`tipografia.py` + `elementos.py`)

Projeto JSON: `{"w","h","audio","audio_inicio","duracao","fade","grao","zoom","deriva","brilho","giro",
"pb","bpm","grade","animar","identidade","assinatura","batidas","cenas":[...]}`

### Estilos de cena (`"estilo"`)
- **`linhas`** ← o principal hoje (só letras). `cena["linhas"] = [{"fonte","tamanho","cor","abrir",
  "grupos":[{"texto","tempos":[...],"fonte","tamanho","cor","soco","destaque"}]}]`.
  Cada linha tem fonte própria; os grupos trocam no MESMO lugar ("MAIS DO QUE" → "TUA VOZ").
  Animação da referência: palavra surge desfocada e cinza → clareia; espaçamento entre letras abre;
  troca de grupo e saída da cena em "chicote" (achata+borra); inclinação leve; aproximação lenta
  (`zoom_texto`); `soco` = zoom de impacto (limitado à área segura); `faixa: true` = faixa de cor
  oposta com a letra dentro; `destaque: true` = traço vermelho nasce sob a frase (marca "verso.").
  ATENÇÃO: se dois grupos começam no mesmo tempo, o segundo engole o primeiro (bug que já tive).
- `revelar` (frase palavra a palavra; `entrada: "cortina"`, `dx`/`largura` pra pôr ao lado de foto,
  `sombra`, `animar`, `pulsar`), `pilha` (caixa alta empilhada), `flash` (preto/branco alternando;
  `piscar`), `gigante` (palavra enorme; `piscar`, `dy`, `tempos` pra esperar a palavra), `serifa`,
  `cursiva`, `maquina` (sílabas com hífen), `circulo`, `inclinado` (REJEITADO pelo usuário).
- Paletas: `sangue` (vermelho `#a30000`→`#3a0000`, texto `#ff8418`), `sangue_preto`, `bordo`, `rosa`.
- `piscar_inverte: true` em qualquer cena: inverte a tela inteira em cada ataque (detectado no áudio).
- `pb: true`: preto e branco com curva de filme.
- Ataques da música: `sincronizar.detectar_batidas(y, 4, 0.6)` — calculados no render e usados por
  `piscar`, `piscar_inverte` e elementos.

### Elementos (`"elementos": [...]`) — status com o usuário
| elemento | música | status |
|---|---|---|
| `casal` (ele sopra fumaça que forma o rosto dela) | "chover" P&B | aprovado (pediu melhorias, foram feitas) |
| `porta` (luz, silhueta no vão) | "entrar" | ok |
| `vidro` (box embaçado, gotas) | "banheiro" | ok |
| `pulso` (monitor cardíaco nos ataques) | "flor" | **gostou** |
| `petalas`, `rosa`, `cidade` | "flor" | **gostou** ("pode por mais elementos") |
| `foto` (fotos dele: `dir`/`esq`/`cheio`/`topo`, `foto_fundo: "desfocado"`, `foto_fade`) | anime, Yor, Gojo | aprovado |
| `coracoes` | Yor/KISS | ok |
| `estrelas` (brilhos ✦) | Gojo | ok |
| `filme` (riscos/poeira de película) | "outra vida" | ok |
| `estouro` (estrela de pontas) | "deusa" | ok |
| `folhas`, `neve`, `fogo` | rap, again, away | entregues (sem retorno ainda) |
| `cinzas` | anime | ok |
| `perfil`, `fumaca`, `lua`, `traco`, `aneis`, `linhas`, `luz`, `chuva`, `particulas` | P&B antigos | ok |
| `fios` (marionete) | "poder" | **REJEITADO** ("ficou ruim demais") |
| `gravidade` | "poder" | **REJEITADO e apagado** |
| `eclipse` | "poder" | rejeitado nesse vídeo (ficou sem elementos) |
| `cortes` (golpes de corte) | anime | **REJEITADO e apagado** ("estranhos") |
| `horas` (relógio) | "real" | **REJEITADO** ("remova o relógio") |
| cenários (`cenario.py`: por_do_sol, muralha...) | anime | **REJEITADO** ("não queria que gerasse cenários") |

### Outras ferramentas
- `musica.py`: compõe trilhas ORIGINAIS (rnb/funk/trap) — o usuário NÃO quer instrumental no lugar
  da música real; só use pra demos sem música dele.
- `sincronizar.py`: sincronia por reconhecimento de voz (faster-whisper) ou `--modo tap`.
- `referencia.py`: encaixa tempos nas trocas de um vídeo de referência.
- `verificar_bordas.py`: acusa contorno forte nas bordas (letra ou elemento — sempre olhar o quadro).

## 6. Histórico dos vídeos (projetos em `projetos/`, saídas em `saida/`)

| projeto | música (identificada) | notas |
|---|---|---|
| musica_chover / _pb | The Weeknd – "Often" (tradução, provável) | P&B com casal+fumaça; "muitas vezes" pisca |
| musica_mestre / _pb | YC Banks – "Simon Says" (tradução) | |
| musica_entrar | não identificada | porta |
| musica_banheiro | Montell Fish – "Bathroom" (tradução, provável) | vidro; repetição pisca |
| musica_poder | não identificada | **sem elementos** (versão final) |
| musica_flor | Baco Exu do Blues – "Piscina Vazia" | pulso+rosa+pétalas+cidade (gostou) |
| musica_anime | JRP – "Nosso Fim (Eren e Mikasa)" part. Amanda Areia | 16:11, fotos dele, "ME PERDOA" no início, "TITÃ" (não "titan") |
| musica_kiss / _pt | KISS – "I Was Made for Lovin' You" | Yor/Loid; versão PT; cena vermelha com fundo contínuo da foto |
| musica_guy_pt | Superfruit – "GUY.exe" | Gojo, PT ("1,80 de altura") |
| musica_outra_vida | não identificada (PT) | só letras, animações da referência |
| musica_real | não identificada (PT, cena de Dexter) | só letras; relógio removido |
| musica_deusa | não identificada | "DEUSAAA!!", piscar_inverte, estouro |
| musica_rap | rap PT (Obito/Naruto) | folhas |
| musica_again | inglês ("...kill... to see you again") | neve; algumas palavras incertas ("IT", "nii-chan") |
| musica_away | inglês ("tell me all the ways to stay away") | fogo na parte instrumental |
| demo_* | textos e trilhas originais | demos antigos |

## 7. Em andamento quando a sessão foi interrompida

O usuário pediu: **estudar os edits mais virais do TikTok e criar uma identidade própria**.
Ele autorizou entrar no navegador dele (TikTok), mas a sessão na nuvem não tinha acesso ao
computador. **Uma sessão local deve:** abrir o TikTok no navegador dele, pesquisar "lyric edit",
"tipografia", "edit de letra", ver os mais virais (views/likes), anotar padrões, e então finalizar a
identidade abaixo e fazer um vídeo de demonstração.

Pesquisa web já feita (blogs, sem dados oficiais):
- gancho no **1º segundo** (sem tela preta no início — tela preta de 2s mata retenção);
- trocas de texto **na batida**; mudança visual a cada **2–3 s**;
- fonte estável, movimento por escala/posição/cor; **uma cor base + uma de destaque**;
- serifa = poético/triste; máquina de escrever = cru/diário; vídeos que **fazem loop** perfeito rendem replays.

Identidade proposta (já no código, falta validar com o usuário e fazer demo):
- nome provisório **"verso."** (assinatura discreta no canto, `"assinatura": "verso."`);
- `"identidade": "verso"` aplica: 16:11, estilo `linhas`, fundo preto `#060606` com respiro branco
  `#f2f1ee` a cada 3 cenas, elemento `filme`, grão 0.04, câmera sutil;
- paleta: preto, osso, **vermelho `#c4161c` só no destaque**;
- 3 vozes tipográficas: **serifa** (verso delicado), **negrito caixa alta** (impacto), **cursiva** (sentimento);
- marca registrada: **traço vermelho** que nasce sob a frase de impacto (`"destaque": true` no grupo);
- regras: palavra 1 entra até 0,3 s (sem intro preta), trocas na batida, repetição pisca, final em loop.
Perguntar ao usuário se gosta do nome/assinatura antes de usar em vídeo dele.

## 8. Setup local

```bash
pip install pillow numpy          # Pillow 12.x, numpy 2.x funcionaram
# ffmpeg 6.x no PATH
# fontes já estão em fonts/ (OFL): Anton, Bebas, DM Serif, Great Vibes, Montserrat, Oswald, Playfair
```
Os arquivos fora do git (`audios/`, `fotos/`, `projetos/musica_*.json`, `saida/musica_*.mp4`) foram
enviados ao usuário num `.zip` (`tipografia_privado.zip`): descompacte dentro de `tipografia/`.
Se não estiverem, peça ao usuário os vídeos de referência e refaça pelo fluxo da seção 4.

## 9. Branch e commits
Branch de trabalho: `ccr-7d0ddc31-1o1a9p` no repo `familiaaraujo301090-eng/ia`.
Commits terminam com as linhas de co-autoria que o ambiente pedir. Não criar PR sem o usuário pedir.
