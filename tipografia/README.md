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

### Sincronia automática com a música (`sincronizar.py`)

Você coloca o arquivo da música (mp3/m4a/wav que você tenha: comprado, exportado do CapCut,
som do seu rascunho etc.) e a letra; a ferramenta acha o tempo de **cada palavra** e as **batidas**,
monta o projeto e renderiza **com o áudio**.

```bash
pip install faster-whisper            # reconhecimento de voz (só na 1ª vez)

# letra.txt: um trecho por linha. Prefixo opcional de estilo:
#   gigante: PALAVRA
#   pilha: LINHA 1 / LINHA 2
#   frase normal  (estilo escolhido sozinho; linha de 1 palavra vira gigante)

python3 sincronizar.py musica.mp3 letra.txt --inicio 47 --fim 62 --tema vermelho --render
```

- `--inicio/--fim`: o trecho da música (em segundos) que vira vídeo (TikTok: 10–30s).
- `--tema`: `noite`, `vermelho`, `rosa`, `bordo`, `cursiva` (define a rotação de estilos e cores).
- `--idioma pt` ou `en` ajuda o reconhecimento; `--modelo medium` é mais preciso (mais lento).
- Sem instalar nada: `--modo tap` toca a música e você aperta **ENTER** no começo de cada linha.
- Palavras que a voz não reconhecer são interpoladas pelas vizinhas; depois dá pra ajustar
  qualquer tempo no `.json` gerado e rodar `python3 tipografia.py projetos/letra.json` de novo.

Dica: pra postar, você pode subir o vídeo **com** o áudio ou mudo e escolher o som oficial no TikTok
(o vídeo continua sincronizado se você escolher o mesmo trecho).

## Música no vídeo (sempre com som)

Todo vídeo sai **com a música sincronizada**:

- **Com a música que você quiser:** mande o áudio (mp3/m4a) ou um vídeo seu com a música, e
  `sincronizar.py` acha o tempo de cada palavra e renderiza com o som.
- **Trilha original (livre de direitos):** `musica.py` compõe uma batida nova (`rnb`, `funk`, `trap`)
  e grava junto um `.json` com os tempos das batidas:
  ```bash
  python3 musica.py --estilo funk --bpm 130 --compassos 6 -o trilhas/minha.wav
  ```
  No projeto, use `"audio": "trilhas/minha.wav"` e `"bpm": 130`: **cada palavra é encaixada na
  colcheia mais próxima** (`"grade": 2`; use 4 pra semicolcheia) e as cenas trocam no compasso.

## Acabamento "sem cara de IA" (automático em todo vídeo)
- **Entrada com foco de lente:** a palavra nasce desfocada e um pouco maior e assenta no lugar. Sem listras nem glitch por cima da letra.
- **Câmera viva:** push-in lento em cada cena, deriva de mão que nunca repete e um leve giro. Soco de zoom nas batidas.
- **Gigante** entra com desfoque de movimento, não com tremedeira.
- **Brilho de lente (halation)**, **grão de filme** que não repete padrão e **flicker** sutil de exposição.
- Branco e preto nunca puros (`#eeebe5` / `#0a0a0a`), como em filme.
- Ajuste por projeto: `"zoom"`, `"deriva"`, `"giro"`, `"brilho"`, `"grao"` (0 desliga).

## Paletas (`"paleta"` em qualquer cena)
- `sangue`: vermelho puro tirado pixel a pixel do vídeo de referência (centro `#a30000` → bordas `#3a0000`), texto laranja queimado `#ff8418`
- `sangue_preto`: o mesmo vermelho com texto quase preto
- `bordo` e `rosa`

## Demos (`projetos/`, textos originais)
- `demo_noite.json`: círculo → revelar no vermelho → DEVAGAR gigante → flash → pilha sangue → pilha preta no vermelho
- `demo_bordo.json`: cursiva → serifa bordô → gigante sangrando
- `demo_rosa.json`: máquina por sílaba → pilha rosa → gigante → revelar

### Mais músicas pra fazer no mesmo estilo
**Inglês:** The Weeknd – *Often*, *Wicked Games*; Zayn – *Pillowtalk*; Jason Derulo – *Talk Dirty*;
Ariana Grande – *Love Me Harder*, *Side to Side*; Beyoncé – *Partition*; Rihanna – *Kiss It Better*;
Doja Cat – *Streets*; Chris Brown – *Under the Influence*; Sabrina Carpenter – *Espresso*.
**Português:** Anitta – *Vai Malandra*, *Envolver*; Luísa Sonza – *Toma*, *Cachorrinhas*;
Pabllo Vittar – *K.O.*; Ludmilla – *Verdinha*; Matuê – *Quer Voar*; Kevin o Chris – *Ela é do Tipo*.

Fontes em `fonts/`: Google Fonts, licença SIL OFL (livres pra uso comercial).
