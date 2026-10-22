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
3. **Pasta.** Crie `shorts/AAAA-MM-DD-tema-curto/` com `roteiro.txt` (um paragrafo por linha) e `video.json` (modelo em `shorts/2026-10-22-seneca-imaginacao/video.json`). O `titulo` e o gancho em ate 6 palavras.
4. **Imagens.** De 3 a 5 imagens verticais. Gere no Canva com `generate-image`, `aspectRatio: PORTRAIT_9_16`. Para cenas com o personagem, passe a foto de perfil (`MAHYw9feFys`) em `imageReferences` para manter o mesmo rosto. Estilo fixo: pintura realista, luz quente de lamparina, fundo escuro, sem texto na imagem. Os servidores de imagem do Canva sao bloqueados neste ambiente, entao so chega uma miniatura (112x200). Ela serve para a previa; para o video final, peca ao usuario para baixar as imagens em resolucao cheia pelos links "Open generated image" e envia-las no chat, e salve como `1.png`, `2.png`... na pasta. Em `inicios` do json, faca cada imagem entrar no paragrafo que ela ilustra (veja `tempos.json`).
5. **Narracao.** Rode `python shorts/gerar_voz.py shorts/<pasta>` (voz `pm_santa`, velocidade 0.9). Gera `narracao.wav` e `tempos.json`. Se faltar o modelo, baixe os dois arquivos citados no topo do script para `shorts/modelo-voz/` (GitHub e PyPI funcionam aqui; Hugging Face nao). Se o usuario preferir, ele pode gravar no ElevenLabs e mandar o audio; nesse caso nao use `tempos`.
6. **Montagem.** Rode `python shorts/editar_short.py shorts/<pasta>`. Sai `short.mp4` em 1080x1920 com zoom suave nas imagens, transicoes, legendas grandes sincronizadas pelo texto, titulo no topo e musica opcional (`musica` e `volume_musica` no json).
7. **Conferir.** Extraia 3 quadros (`ffmpeg -ss <t> -i short.mp4 -frames:v 1 quadro.png`) e olhe: legenda legivel, nada cortado, imagem certa em cada trecho. Se a legenda adiantar ou atrasar, ajuste o roteiro para ficar igual ao audio.
8. **Publicacao.** Entregue ao usuario o titulo, a descricao (2 linhas + 3 a 5 hashtags) e lembre de marcar "conteudo alterado ou sintetico" no YouTube, porque a voz e o personagem sao feitos com IA. Quem posta e o usuario.

## Regras

- Qualidade acima de quantidade: no maximo 1 a 2 shorts por dia. O YouTube nao monetiza conteudo repetitivo produzido em massa.
- Respeito a todas as religioes e posicoes; o canal provoca reflexao, nao briga.
- Nada de promessas de cura, prosperidade garantida ou conselho medico.
