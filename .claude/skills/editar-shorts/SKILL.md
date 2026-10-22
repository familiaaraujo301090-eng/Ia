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
3. **Pasta.** Crie `shorts/AAAA-MM-DD-tema-curto/` com um `video.json` (modelo em `shorts/exemplo/video.json`). O `titulo` e o gancho em ate 6 palavras.
4. **Imagens.** De 3 a 5 imagens verticais. Gere no Canva com `generate-image`, `aspectRatio: PORTRAIT_9_16`. Para cenas com o personagem, passe a foto de perfil (`MAHYw9feFys`) em `imageReferences` para manter o mesmo rosto. Estilo fixo: pintura realista, luz quente de lamparina, fundo escuro, sem texto na imagem. A previa que o Canva devolve aqui e pequena: o usuario baixa as imagens em resolucao cheia pelo link "Open generated image" e salva como `1.png`, `2.png`... na pasta.
5. **Narracao.** O usuario gera o audio com a voz fixa do Mestre Elias (ElevenLabs ou voz do CapCut) colando o roteiro, e salva como `narracao.mp3` na pasta. Voce nao gera audio.
6. **Montagem.** Rode `python shorts/editar_short.py shorts/<pasta>`. Sai `short.mp4` em 1080x1920 com zoom suave nas imagens, transicoes, legendas grandes sincronizadas pelo texto, titulo no topo e musica opcional (`musica` e `volume_musica` no json).
7. **Conferir.** Extraia 3 quadros (`ffmpeg -ss <t> -i short.mp4 -frames:v 1 quadro.png`) e olhe: legenda legivel, nada cortado, imagem certa em cada trecho. Se a legenda adiantar ou atrasar, ajuste o roteiro para ficar igual ao audio.
8. **Publicacao.** Entregue ao usuario o titulo, a descricao (2 linhas + 3 a 5 hashtags) e lembre de marcar "conteudo alterado ou sintetico" no YouTube, porque a voz e o personagem sao feitos com IA. Quem posta e o usuario.

## Regras

- Qualidade acima de quantidade: no maximo 1 a 2 shorts por dia. O YouTube nao monetiza conteudo repetitivo produzido em massa.
- Respeito a todas as religioes e posicoes; o canal provoca reflexao, nao briga.
- Nada de promessas de cura, prosperidade garantida ou conselho medico.
