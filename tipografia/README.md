# Tipografia cinética (estilo lyric edit do TikTok)

Motor próprio (Python + Pillow + ffmpeg) que gera vídeos verticais 1080x1920 com a
letra da música animada, sem marca d'água, a partir de um arquivo `.json`.

```bash
pip install pillow numpy          # ffmpeg precisa estar instalado
python3 tipografia.py projetos/sm_rihanna.json                    # -> saida/sm_rihanna.mp4
python3 tipografia.py projetos/sm_rihanna.json --preview          # só PNGs pra conferir
python3 tipografia.py projetos/sm_rihanna.json --audio musica.mp3 --inicio 47.2   # já com som
```

## O que aprendi estudando os 16 vídeos

| Estilo (`"estilo"`) | Como é nos vídeos | Truque |
|---|---|---|
| `revelar` | Frase se monta palavra por palavra no centro. A palavra nova entra **cinza** e acende pra branco | A linha **recentraliza** a cada palavra nova; fonte condensada (Oswald) |
| `pilha` | CAIXA ALTA bold empilhada, laranja/vermelho sobre preto/vermelho | Palavra nova entra com **glitch RGB + risco** por ~0,2s |
| `flash` | Fundo pisca **preto ↔ branco** a cada palavra, texto pequeno e limpo | Inverte a cor do texto junto com o fundo |
| `gigante` | Uma palavra ENORME e esticada na vertical ("PARTIR", "PODER", "LOVER") | Escala com "soco" (passa do tamanho e volta) + tremidinha; use nas palavras fortes |
| `serifa` | Serifa grossa, fundo **bordô/bege alternando**, linhas antigas desfocadas | Blur nas linhas anteriores, só a atual nítida |
| `cursiva` | Letra manuscrita fina sendo escrita, fundo com vinheta | Letra por letra; alterne `"claro": true/false` entre cenas |
| `maquina` | Máquina de escrever por **sílaba com hífen** ("a mi-" → "a minha"), fundos em tons de cinza | Escreva o texto com hífens: `"a mi-nha paz quan-do"`; troque `"tom"` a cada cena |
| `circulo` | Abertura: círculo branco cresce e vira faixa com o texto | Ótimo pra começar o vídeo |

Regras gerais que se repetem:
- **Ritmo = sílaba/palavra no tempo do canto.** Cada palavra entra exatamente quando é cantada.
- **Contraste extremo**: preto, branco, uma cor de destaque (vermelho, rosa, bordô).
- **Variar o estilo a cada frase**, mas manter 2–3 fontes no máximo por vídeo.
- **Palavra-chave da frase vira `gigante`**; o resto fica pequeno, e o contraste de escala é o que impacta.
- Cortes secos nas batidas (`"batidas": [...]` dá um zoom-punch nesses segundos).

## Formato do projeto

```json
{
  "musica": "Artista - Música",
  "batidas": [0.0, 3.2],
  "cenas": [
    {"estilo": "revelar", "inicio": 0.0, "fim": 2.5, "texto": "frase cantada aqui"},
    {"estilo": "gigante", "inicio": 2.5, "fim": 3.6, "texto": "PALAVRA", "inverter": true},
    {"estilo": "pilha", "inicio": 3.6, "fim": 6.0, "texto": "LINHA 1 / LINHA 2", "cores": ["#fff", "#ff5a1f"]}
  ]
}
```

- `inicio`/`fim`: segundos. Por padrão as palavras se espalham pelos primeiros 70% da cena (`"ritmo": 0.7`).
- Pra sincronizar perfeito, passe o segundo exato de cada palavra: `"tempos": [0.0, 0.42, 0.9]`.
- Opções: `fonte` (anton, bebas, black, bold, medium, oswald, serif, playfair, italico, cursiva),
  `tamanho`, `cor`, `bg`, `bg2` (degradê), `cores`, `sangrar` (palavra estoura a tela), `sub`/`sobre` (texto pequeno junto do gigante), `fade`.

### Como sincronizar com a música
1. Abra a música no CapCut/Audacity e anote o segundo em que cada frase começa.
2. Preencha `inicio`/`fim` de cada cena (e `tempos` se quiser palavra por palavra).
3. Gere o vídeo. **Recomendado:** suba o MP4 mudo no TikTok e escolha o som oficial lá
   (é licenciado e conta pra trend). Ou use `--audio` com um arquivo que você tenha direito de usar.

## Projetos prontos (`projetos/`)
- `sm_rihanna.json`: Rihanna, *S&M* (círculo → flash → gigante → pilha vermelha)
- `poderosas_anitta.json`: Anitta, *Show das Poderosas* (gigante → revelar → pilha rosa → flash)
- `earned_it_weeknd.json`: The Weeknd, *Earned It* (cursiva → serifa bordô → gigante sangrando)
- `dangerous_woman_ariana.json`: Ariana Grande, *Dangerous Woman* (máquina → gigantes → revelar)

Os tempos são aproximados: ajuste ao trecho exato que você usar.

### Mais músicas pra fazer no mesmo estilo
**Inglês:** The Weeknd – *Often*, *Wicked Games*; Zayn – *Pillowtalk*; Jason Derulo – *Talk Dirty*;
Ariana Grande – *Love Me Harder*, *Side to Side*; Beyoncé – *Partition*; Rihanna – *Kiss It Better*;
Doja Cat – *Streets*; Chris Brown – *Under the Influence*; Sabrina Carpenter – *Espresso*.
**Português:** Anitta – *Vai Malandra*, *Envolver*; Luísa Sonza – *Toma*, *Cachorrinhas*;
Pabllo Vittar – *K.O.*; Ludmilla – *Verdinha*; Matuê – *Quer Voar*; Kevin o Chris – *Ela é do Tipo*.

Fontes em `fonts/`: Google Fonts, licença SIL OFL (livres pra uso comercial).
