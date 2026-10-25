# Publico do nicho e plano de progressao (para os proximos videos)

## Quem assiste filosofia, estoicismo e fe em video curto
Dados publicos sao poucos e vem de rastreadores de terceiros; confirmar no YouTube Studio
depois de 2 a 3 semanas de postagem.
- **Idade:** o nucleo fica entre 18 e 44 anos. Os maiores perfis de estoicismo rastreados tem
  publico de 18 a 34 (um) e de 25 a 44 (outro).
- **Genero:** a fama e de publico masculino, mas um dos maiores perfis de estoicismo tem maioria
  feminina e outro e meio a meio. Nao escrever so para homens.
- **Momento de vida:** gente ansiosa, cansada, em fase de recomeco (termino, demissao, luto,
  vicio em celular), procurando sentido e autocontrole. Muitos assistem a noite, sem som.
- **Fe:** no Brasil o publico cristao e enorme. Os videos de Biblia contada como historia
  (Jonas, Pilatos, Jo) alcancam um publico que o estoicismo puro nao alcanca.

## O que essas pessoas querem ver
1. **Algo que serve para a vida delas hoje:** ansiedade, raiva, relacionamento, dinheiro,
   celular. A filosofia e o meio, nao o assunto.
2. **Ser revelado um segredo:** manipulacao, psicologia, "o que ninguem te conta".
3. **Historia real com nome e ano:** Milgram, Socrates, Bernays. Prende mais que conceito.
4. **Uma frase para guardar ou mandar:** o dourado na legenda. E o que vira print e compartilhamento.
5. **Ser desafiado:** "o que voce faria?". Gera comentario.

## O que ja esta indo bem no nicho
- **Estoicismo aplicado a relacionamento e drama do dia a dia.** Um canal faceless de estoicismo
  com so 6.680 inscritos tem mediana de 24 mil visualizacoes por video com esse formato (OutlierKit).
- **Listas e habitos:** "5 habitos que os estoicos evitam".
- **Loop:** pergunta no comeco que so e respondida no fim, para a pessoa assistir de novo.
- **Legenda grande sempre:** cerca de 80% da geracao Z assiste com legenda.
- **Corte a cada 2 a 4 segundos** nos Shorts que mais retem.
- Shorts mais comuns tem 20 a 40 s; a retencao media do YouTube Shorts gira em 45%, e 50 a 60% e
  considerado bom.

## Progressao: como cada video deve andar
| Tempo | Parte | O que fazer |
|---|---|---|
| 0 a 2 s | **Gancho falado** | A voz comeca no primeiro quadro, sem silencio nem cena muda antes: o Mestre Elias ja fala a frase que poe voce dentro da cena, com algo em jogo (ate 10 palavras). A frase aparece escrita ao mesmo tempo, para quem esta sem som. Imagem mais forte do video por tras. |
| 2 a 6 s | **Promessa** | Por que ficar: "no fim voce vai saber..." ou a pergunta que so se responde no final. |
| 6 a 25 s | **Escalada** | A historia real em cenas de 3 a 4 s, cada uma mais tensa que a anterior. Corte a cada 2 a 3 s. |
| 25 a 32 s | **Virada** | Frase-chave em dourado; meio segundo de silencio antes dela (a musica para). |
| 32 a 40 s | **Payoff** | A solucao pratica, curta e direta. |
| 40 a 45 s | **Loop + pergunta** | Pergunta para os comentarios que conversa com a primeira frase, para o fim emendar no comeco. |

**Duracao alvo:** de 50 a 58 s hoje para **38 a 45 s**. Roteiro de 105 a 120 palavras.

## Voz e ritmo mais rapidos
- **Comeco falado:** hoje a narracao comeca com 0,3 s de silencio (`gerar_voz.py`). Cortar para quase zero (0,05 s), para a primeira palavra sair junto com a primeira imagem.
- **Hoje:** a narracao anda entre 130 e 144 palavras por minuto (medido nos 10 ultimos videos).
- **Alvo:** cerca de **165 palavras por minuto**, a faixa usada em Shorts de historia (155 a 165).
  Em `gerar_voz.py`: velocidade de 0,87 para **cerca de 1,05**, pausa entre frases de 0,25 para
  **0,12 s**, entre paragrafos de 0,6 para **0,3 s**. Manter o tom grave e sereno: rapido, mas
  nao apressado.
- **Acelerar o ritmo ao longo do video:** gancho um pouco mais lento (impacto), escalada mais
  rapida, virada lenta de novo (a frase-chave tem que pesar), payoff rapido.
- **Video:** planos de no maximo 3 s (hoje ate 6,5 s), transicoes mais curtas (0,6 para 0,3 s),
  legenda trocando no ritmo da fala mais rapida.
- **Teste antes de mudar tudo:** fazer 2 videos na velocidade nova e 2 na antiga, e comparar a
  duracao media assistida no YouTube Studio. Nao ha estudo independente mostrando que voz mais
  rapida aumenta retencao; o dado que manda e o do proprio canal.

## Fontes
- OutlierKit, analise de canal faceless de estoicismo: https://outlierkit.com/channel/thestoiclogic-m7h
- CreatorDB, publico de perfis de estoicismo: https://creatordb.app/creatorstats/pathsofstoicism/ e https://creatordb.app/creatorstats/stoicismideas/
- Subscribr, algoritmo dos Shorts e retencao: https://subscribr.ai/youtube-strategy/youtube-shorts-algorithm-explained
- AWISEE, estatisticas de Shorts: https://awisee.com/blog/youtube-shorts-statistics/
- Zebracat, loop e legendas: https://www.zebracat.ai/de/post/how-viral-youtube-shorts
- NarrationBox, ritmo de narracao: https://narrationbox.com/blog/hook-pacing-templates-for-youtube
- GoFaceless, retencao media de Shorts: https://www.gofaceless.ai/ro/blog/youtube-shorts-retention-rate-benchmarks
- Medium, cortes a cada 2 a 4 s: https://medium.com/@techwithlandon/want-over-70-retention-on-your-short-form-videos-heres-how-to-do-it-5ce7bae94a43
