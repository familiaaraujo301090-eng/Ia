---
name: editar-shorts
description: Cria e edita os videos curtos (Shorts, Reels, TikTok) do canal Lamparina, de filosofia e teologia, com o personagem Mestre Elias. Use quando o usuario pedir um video curto, um short, um reels, um roteiro curto do canal ou para montar/editar um video a partir de imagens e narracao.
---

# Editar videos curtos do canal Lamparina

A identidade do canal (nome, personagem, tom, cores) esta em `canal.md` na raiz do repositorio. Leia antes de escrever qualquer coisa.

## Passo a passo de cada short

1. **Tema.** Escolha um tema que ainda nao esteja em `shorts/` (veja os `video.json` existentes). Varie entre: estoicismo, filosofos classicos, Biblia e santos, perguntas existenciais, sabedoria para o dia a dia. Nunca repita a mesma ideia com outras palavras.
2. **Roteiro.** De 100 a 140 palavras (cerca de 40 a 55 segundos), na voz do Mestre Elias:
   - Gancho nos 3 primeiros segundos: uma frase que provoca ou contraria o senso comum.
   - Uma ideia so, de um pensador ou texto real. Cite com fidelidade; se nao tiver certeza da frase exata, parafraseie e diga que e parafrase.
   - Aplicacao pratica para a vida de hoje.
   - Fechamento com frase marcante e chamada curta ("Segue a Lamparina para mais").
   **Estrutura obrigatoria (pedido do usuario, 26/10):** narrativa, nao lista de fatos.
   - *Hook com o espectador dentro da historia:* a primeira frase (ate 12 palavras) poe "voce"
     numa situacao com algo em jogo ("Voce esta numa sala com sete pessoas, e todas estao erradas").
   - *Stakes:* o que voce perde ou ganha com a escolha; deixe a pessoa decidir antes de saber.
   - *Historia real* com nome, ano e lugar, contada em cenas curtas (uma por paragrafo).
   - *Virada:* a resposta surpreendente, em dourado.
   - *Payoff claro:* uma solucao pratica ou uma conclusao que justifique o tempo gasto.
   - *Pergunta final* para comentarios, antes da chamada "Segue a Lamparina."
   - Antes de escrever um tema novo, olhe a estrutura de um video viral parecido e copie a forma.
   - Ritmo e duracao (planejado para os proximos): ver `shorts/PUBLICO-E-PROGRESSAO.md` (38 a 45 s, voz ~165 palavras/min, planos de ate 3 s).
3. **Pasta.** Crie `shorts/AAAA-MM-DD-tema-curto/` com `roteiro.txt` (um paragrafo por linha; cada paragrafo e uma cena) e `video.json` (modelo em `shorts/2026-10-22-seneca-imaginacao/video.json`). O `titulo` e o gancho em ate 6 palavras. Marque com `*asteriscos*` a frase-chave (a citacao ou a virada): ela aparece em dourado na legenda. Use no maximo 2 destaques por video.
4. **Imagens.** De 6 a 7 imagens verticais, uma por paragrafo. Gere no Canva com `generate-image`, `aspectRatio: PORTRAIT_9_16`. Para cenas com o personagem, passe a foto de perfil (`MAHYw9feFys`) em `imageReferences` para manter o mesmo rosto. Estilo fixo: pintura realista, luz quente de lamparina, fundo escuro, sem texto na imagem. Para baixar em resolucao cheia (os dominios `media.canva.com` e `export-download.canva.com` precisam estar liberados na rede do ambiente): troque as imagens das paginas do design de exportacao `DAHYxf_hmrY` com `update_fill` (localizadores em `shorts/PROGRESSO.md`), salve com `commit`, exporte em JPG 1080x1920 com `export-design` e baixe cada pagina para `1.jpg`, `2.jpg`... na pasta. Gere de 6 a 7 imagens por video. Em `cenas` do json, diga em que paragrafo cada imagem entra (ex.: `[1, 2, 3, 4, 6]`) e em `focos` a altura do assunto principal de cada imagem (0.3 para rosto no alto, 0.55 para pessoa deitada ou no centro), usada nos closes.
5. **Narracao.** Rode `python shorts/gerar_voz.py shorts/<pasta>` (voz `pm_santa`, velocidade 0.87, tom 0.96: serena, como o usuario aprovou). Gera `narracao.wav` e `tempos.json` com o tempo de cada frase. Se faltar o modelo, baixe os dois arquivos citados no topo do script para `shorts/modelo-voz/` (GitHub e PyPI funcionam aqui; Hugging Face nao). Se o usuario preferir, ele pode gravar no ElevenLabs e mandar o audio; nesse caso nao use `tempos`.
6. **Montagem.** Escolha o modelo da vez (veja o ultimo usado em `shorts/PROGRESSO.md` e use
   outro) e ponha `"modelo"` no `video.json`. Rode `python shorts/editar_short.py shorts/<pasta>`.
   O classico (sem `"modelo"`) gera `short.mp4` em 1080x1920: cada imagem vira planos de no maximo 6,5 s (aberto e close, a camera sempre avancando), legendas curtas de 2 a 5 palavras sincronizadas por frase (Inter ExtraBold), titulo em Cinzel dourado, som ambiente suave por baixo da voz e musica opcional (`musica` e `volume_musica`).
7. **Conferir.** Extraia 3 quadros (`ffmpeg -ss <t> -i short.mp4 -frames:v 1 quadro.png`) e olhe: legenda legivel, nada cortado, imagem certa em cada trecho. Se a legenda adiantar ou atrasar, ajuste o roteiro para ficar igual ao audio.
8. **Publicacao.** Entregue ao usuario o titulo, a descricao (2 linhas + 3 a 5 hashtags) e lembre de marcar "conteudo alterado ou sintetico" no YouTube, porque a voz e o personagem sao feitos com IA. Quem posta e o usuario.

## Licoes aprendidas (critica de cada video)

- Imagem parada mais de 6 s cansa: por isso os planos. Prefira 5 a 6 imagens por video de 50 s.
- Legenda longa ou cortada no meio da expressao ("na sua") atrapalha; o editor ja evita isso.
- Passe de 60 s so se o tema pedir; o ideal e 45 a 55 s.
- Confira o close de cada imagem: se cortar o assunto, ajuste `focos`.
- Pausas longas deixam a fala serena, mas acima de 0,7 s entre paragrafos o video arrasta.
- Paragrafo com mais de 10 s de fala deve ser dividido, para entrar uma imagem nova (aconteceu em Eclesiastes).
- Imagem clara (toga branca, ceu) apaga a legenda: o editor ja poe uma faixa escura suave atras dela.
- Gere a imagem do personagem com a foto de perfil como referencia, para o rosto do Mestre Elias nao mudar.
- Antes de citar alguem, confira a frase e o contexto (ex.: Diogenes encontrou Alexandre em Corinto, nao em Atenas).
- Use `python shorts/revisar.py folha.png pastas...` para ver 8 quadros de cada video de uma vez.
- Edits virais trocam a imagem no tempo da musica. Ha 4 modelos em `shorts/modelos.py`
  (gravura, tipografia, citacao; a colagem foi descartada pelo usuario em 26/10, nao use), com trilha propria gerada por `shorts/trilha.py`.
  **Um modelo por video**, alternando; nunca misture modelos. Comeco imediato, sem introducao
  parada; camera so avanca (zoom que vai e volta cansa). Detalhes em `estilos-virais.md`.
- Muitos planos curtos: conte os quadros em tempo absoluto, senao o xfade corta o video no meio.

## Regras

- Qualidade acima de quantidade: no maximo 1 a 2 shorts por dia. O YouTube nao monetiza conteudo repetitivo produzido em massa.
- Respeito a todas as religioes e posicoes; o canal provoca reflexao, nao briga.
- Nada de promessas de cura, prosperidade garantida ou conselho medico.
