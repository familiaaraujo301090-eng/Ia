# Progresso: 20 shorts do Lamparina

Fluxo das imagens em alta (descoberto em 22/10): gerar no Canva (`generate-image`), colocar cada
imagem numa pagina do design de exportacao `DAHYxf_hmrY` (`add_page` + `insert_fill` com
`page_id`, varias por chamada), salvar (`commit`), exportar so as paginas novas em JPG 1080x1920
(`export-design` com `pages`) e baixar de `export-download.canva.com`.

| # | Pasta | Tema | Situacao |
|---|---|---|---|
| 1 | seneca-imaginacao | Sêneca: sofremos mais na imaginação | pronto (editor novo) |
| 2 | ilusao-de-controle | Provérbios 16:9 e Agostinho: Deus fora do tempo | pronto |
| 3 | raiva-marco-aurelio | Marco Aurélio: a raiva | pronto |
| 4 | tempo-eclesiastes | Eclesiastes 3: tempo de plantar | pronto |
| 5 | silencio-pascal | Pascal: ficar em repouso num quarto | pronto |
| 6 | socrates-exame | Sócrates: vida sem exame | pronto |
| 7 | jo-perda | Jó 1:21: o Senhor deu, o Senhor tomou | pronto |
| 8 | epicteto-opiniao | Epicteto: não são as coisas que nos perturbam | pronto |
| 9 | kierkegaard-olhar-tras | Kierkegaard: compreender para trás, viver para frente | pronto |
| 10 | filho-prodigo | Lucas 15: voltar para casa | pronto |
| 11 | memento-mori | Marco Aurélio 4.17: não viva como se fosse viver dez mil anos | pronto |
| 12 | salmo-23 | Salmo 23: o vale da sombra da morte | pronto |
| 13 | nietzsche-porque | Nietzsche: quem tem um porquê | pronto |
| 14 | agostinho-inquieto | Confissões I.1: coração inquieto | pronto |
| 15 | heraclito-rio | Heráclito: ninguém entra no mesmo rio duas vezes | pronto |
| 16 | eclesiastes-vaidade | Eclesiastes 1:2: vaidade de vaidades | pronto |
| 17 | diogenes-sol | Diógenes e Alexandre: saia da frente do meu sol | pronto |
| 18 | perdao-setenta-vezes | Mateus 18:22: setenta vezes sete | pronto |
| 19 | frankl-liberdade | Viktor Frankl: a última das liberdades | pronto |
| 20 | platao-caverna | Platão: o mito da caverna | pronto |
| 21 | obstaculo-caminho | Marco Aurélio 5.20: o obstáculo é o caminho | pronto |

## Imagens geradas (ids do Canva, na ordem 1..6 de cada pasta)
- kierkegaard-olhar-tras: MAHYxzVe9RU MAHYx1427kA MAHYx4wRxsg MAHYx5XUVQY MAHYxzFUhL8 MAHYxxbxnII
- filho-prodigo: MAHYx0JIkR8 MAHYx916cG4 MAHYx0GtBzQ MAHYx6QsL6I MAHYx8j637o MAHYx7zt9Qw
- memento-mori: MAHYx-DYN68 MAHYxyqc7AQ MAHYx2ptNFs MAHYx7bKF-Q MAHYx18OLZI MAHYx1fTblc
- salmo-23: MAHYx1qUfm0 MAHYx2z7Sgo MAHYx1S1y3M MAHYx9f-CEQ MAHYx70SSBE MAHYx_-KLGc
- design de exportacao: paginas 1..20 tem um retangulo de imagem cada; trocar com update_fill
- nietzsche-porque: MAHYx_ON_d4 MAHYx-mkDso MAHYx8Dallk MAHYx43HZX8 MAHYx0DefVI MAHYx_dIVBI
- agostinho-inquieto: (1 refazer) MAHYxyR_4qc MAHYx8kolic MAHYx_RePs4 MAHYx3-ZAP8 MAHYx6zPcbQ
- design de exportacao agora tem 24 paginas (21-24: PBlwvty7CT9wnVJp PBdMG1nWDdHZxYzN PBPySVm0vtl02g97 PBvKrJLN1dDvvR0q)
- agostinho-inquieto 1: MAHYx4j3xfw
- heraclito-rio: MAHYx1cP5iA MAHYx-qwPwI MAHYx3pucFc MAHYx_EHHGU MAHYx3z_uKo MAHYx2kyFqY
- eclesiastes-vaidade: MAHYx2VBev0 MAHYx4mQT0U MAHYx3TehUc MAHYx1CjbcI MAHYxySs_30 MAHYx-3A1nc
- localizadores das 24 paginas (para update_fill), na ordem:
  PBdWYXWM1Yt95vYD-LBMkzHdfpFxrPzJj PBKTDQyT29H00c1Y-LB1rQ9Ts2vJHLtny PBbxBtk4R8KZSX8D-LBM891ksHnqwW81p
  PBr0S07shDZL9MB7-LBcVSbh7dNC083T0 PBWyH6jt4Kgmnh8T-LB00PBxM3Jsmygzl PBrH4N80xkbgJ0fp-LBtq6lN4Q13tlMWg
  PBsH4pkcYPcbqKh2-LB37c5kK9wddt928 PBjMl0D9Nz4SMFKN-LBPZ4v8mp6TGGDVg PBx26gVrhtbdzfFW-LBX17ySyygjGpRFJ
  PBVhrB2lWv6gszTp-LBLsF86mV9js9n97 PBP7xDZgsS1hlWvw-LBC3BMMbvXV0plYR PBKphmPHjd1mTcBv-LBYqqmSf121Hx8W8
  PBq73bX4yM2WD9vX-LBB7HvJBZBm6JY4Y PBvY41tDv4Vt8F35-LBp0YD50J4mHQ182 PBbrgLJfjllqCHjx-LBGM595yPhW5LjpV
  PBrFDwP1jSM9ywjZ-LBqdNm3wqsdwPqJ3 PBgZpNrP94DpKtTS-LB2ZCvnfHhdwTbZz PBvGhRvt5bkhs2fx-LBpWJjsYt1nMYKcQ
  PBWYWS8mHwJlTw1c-LBYDKHCxKP14lBPw PBCBLqRlllxMgmMW-LBMvxqM5GJgxsfcp PBlwvty7CT9wnVJp-LBtTrqj4l6xZzymt
  PBdMG1nWDdHZxYzN-LB36Jfq7Cy3BnNCK PBPySVm0vtl02g97-LB343gQffhGDxn0b PBvKrJLN1dDvvR0q-LBk9nKsFpvCykWnR
- eclesiastes-vaidade 7 (carro): MAHY1DwLrng
- diogenes-sol: MAHY1Nhh4Gk MAHY1K1sEjM MAHY1OcNJTs MAHY1FgHT0Y MAHY1P7hCf8 MAHY1Kg_2vA
- perdao-setenta-vezes: MAHY1M-rKdo MAHY1A-D7kY MAHY1AT4vIc MAHY1Nba9JE MAHY1H7ukSI MAHY1PTxlbg
- frankl-liberdade: MAHY1CirHcw MAHY1AXV1GM MAHY1HoSPlo MAHY1MlnRhQ MAHY1GLeBxw MAHY1A2NPr0
- platao-caverna: MAHY1PlhB9s MAHY1Ftk24o MAHY1CfUgZg MAHY1KMSP0M MAHY1Edxsak MAHY1EarVmI
- pagina 25: PB5X23hYjD483Jrp-LBLb6D4XxpF26jsY
- obstaculo-caminho: MAHY1KPCJIk MAHY1LrHM00 MAHY1KzB-iA MAHY1KImcYE MAHY1A9cHPw MAHY1BeAc_0 MAHY1C4Eilg

## Modelos de edicao (25/10)
Alternar e nunca misturar. Testes feitos: gravura (memento-mori), tipografia (frankl-liberdade),
colagem (nietzsche-porque), citacao (nova: 2026-10-27-citacao-seneca-tempo, ja no modelo).
Os 21 videos publicados/postaveis continuam no classico.
- gaslighting: MAHY_VvqV2k MAHY_YB9P1M MAHY_Y9zWXA MAHY_eOR2fI MAHY_UhuSo0 MAHY_XYvny4
- goebbels-repeticao: MAHY_TiepbA MAHY_ap3CJA MAHY_So7f4w MAHY_aOokwU MAHY_X3cDwo MAHY_bpcquQ
- bernays-tochas: MAHY_UqtDaI MAHY_adNL-E MAHY_VwlBWk MAHY_WY29zM MAHY_cf69rg MAHY_dLzkbU
- voce-e-o-produto: MAHY_Zn4OEk MAHY_QI3WfU MAHY_SedG9U MAHY_a4miL4 MAHY_avVwxs MAHY_eBlgMU
- citacao-nietzsche-monstros: MAHY_QVpQj0
