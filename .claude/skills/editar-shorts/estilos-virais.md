# Estilos virais: o que aprendi desmontando 4 edits de filosofia

Analise quadro a quadro (cortes, texto, audio) de 4 videos que o usuario mandou em 25/10/2026.

## 1. "Gravura com busto" (Schopenhauer, vertical, 62 s)
- **Abertura de 5 s:** tela preta, citacao curta e pequena no meio e o busto recortado
  aparecendo devagar por baixo. O espectador para para ler: e o gancho.
- **5 a 7 s:** rajada de 8 cortes em 1,5 s (gravuras antigas): marca a entrada da voz.
- **Corpo:** a imagem de fundo troca a cada **1,27 s cravado**, no pulso da musica, dentro de
  um cartao de cantos arredondados. O filosofo recortado (sem fundo) fica fixo na frente,
  no terco de baixo: o rosto e a ancora, o fundo e o ritmo.
- **Legenda:** **uma palavra por vez**, no meio da imagem, letra gotica vermelha com brilho.
- Tudo quase preto e branco, gravuras e textura de papel velho. Audio em -14 LUFS.
- No final, retratos do proprio filosofo em tela cheia, com zoom lento.

## 2. "Citacao parada" (Schopenhauer, quadrado, 20 s)
- Uma foto so, aparecendo do preto. Citacao fixa em faixa branca no topo, letra preta grossa.
- Sem voz: so musica de piano em 4 ondas. Curto, para ser assistido em loop (o loop conta como
  visualizacao repetida). Facilimo de produzir, vive so da frase.

## 3. "Tipografia cinetica" (cavaleiro estoico, horizontal, 62 s)
- Fundo preto quase o video todo. **O texto e o espetaculo:** palavras vermelhas em serifa
  classica entram e saem uma a uma, em tamanhos diferentes. A palavra-chave vem enorme
  ("cada", "passos") e as de ligacao pequenas ("e", "serao os").
- So 3 ilustracoes em 62 s (busto com louros, cavaleiro ajoelhado) recortadas, num canto.
- Musica epica bem alta (-9 LUFS), com **um corte seco no silencio aos 25 s**: a pausa antes da
  virada prende quem esta assistindo.

## 4. "Colagem" (eterno retorno, Nietzsche/Berserk, horizontal 60 fps, 62 s)
- Troca de cenario a cada 2 a 5 s, alternando fundo preto, branco, papel amassado e mancha
  vermelha. Transicoes: clarao branco, papel rasgado, fumaca.
- Recortes de manga, rosa vermelha, Terra, fogo, grade 3D, mao apontando para a camera (meme).
- Texto dourado em serifa romana, com sombra, digitado letra por letra.
- Arranhoes e granulacao de filme por cima de tudo.
- **Fecha com pergunta direta** ("gosta dessa ideia ou detesta? ESCOLHA"): puxa comentario.

## O que todos fazem
1. **Gancho visual nos 2 primeiros segundos** que nao depende de som (citacao escrita,
   palavra grande). Muita gente assiste sem audio.
2. **Algo muda na tela a cada 1 a 2 s**: imagem, palavra ou tamanho de letra. Nunca 6 s parado.
3. **Uma palavra por vez, grande, no centro**, e nao frase inteira no rodape.
4. **Paleta de 2 ou 3 cores** (preto + branco + vermelho ou dourado) e imagens antigas
   desbotadas: parece "conhecimento proibido", combina com filosofia.
5. **Personagem recortado e fixo** enquanto o fundo muda: da identidade ao canal.
6. Final com **pergunta ou escolha**, e nao so "segue o canal".

## Como usar no editor (`video.json`)
```json
"estilo": "palavra",
"abertura": {"texto": "O que esta no caminho se torna o caminho.", "autor": "Marco Aurelio", "duracao": 3},
"cor": "pb",
"grao": true,
"ritmo": 1.6
```
- `estilo: palavra` gera legendas de 1 palavra, em Cinzel grande, com brilho; os `*destaques*`
  ficam dourados e maiores (modelos 1 e 3).
- `abertura` gera a citacao em tela preta antes da voz (modelos 1 e 2).
- `cor: pb` e `grao` dao o visual de gravura antiga (modelos 1 e 4).
- `ritmo` abaixo de 2 s alterna aberto e close com corte seco (pulso do modelo 1).
- Para testar sem mexer no original: crie `video-palavra.json` com `"saida": "short-palavra.mp4"`
  e rode `python shorts/editar_short.py shorts/<pasta> video-palavra.json`.

## Ainda falta (proximos passos)
- Mestre Elias recortado e fixo na frente (modelo 1): usar `remove-background` do Canva no
  retrato e sobrepor em PNG.
- Pergunta de escolha no fim do roteiro, em vez de so a chamada do canal (modelo 4).
- Musica de verdade com um silencio antes da virada (modelo 3): hoje so ha o som ambiente gerado.
- Versao "citacao parada" de 15 a 20 s, sem voz, para postar entre os shorts narrados (modelo 2).
