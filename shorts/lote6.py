"""Lote 6 (videos 143-145): formatos de trends virais de nov/2026. Uso: python3 lote6.py"""
import json
from pathlib import Path

DATA = "2026-11-28"
P = "3D animated film still, adult Pixar style, "
S = " Cinematic lighting, vertical composition, no text."
E = "a wise old man with a short white beard and kind eyes, simple brown tunic"
V = [
("balada", 143, "enquanto-eles-estao-na-balada", "pulso", "ENQUANTO ELES ESTÃO|[NA BALADA]...",
 ["SEXTA, 23H", "4H59", "5H", "5H30", "6H", "7H", "1 ANO DEPOIS"],
 ["Sexta, onze da noite. Todo mundo na balada. E ele já está indo dormir.",
  "Quatro e cinquenta e nove. O despertador nem tocou, e ele já está de pé.",
  "Cinco horas. Água no rosto, joelho no chão, e uma oração em silêncio.",
  "Cinco e meia. Um livro, uma caneta e nenhuma notificação.",
  "Seis horas. Corrida na rua vazia, enquanto a cidade ainda dorme.",
  "Sete horas. Quando os outros acordam com ressaca, ele já venceu o dia.",
  "*Ninguém vê o que você faz às cinco da manhã. Mas todo mundo vê o resultado.* Comenta: amanhã eu começo."],
 ["young people dancing at a neon nightclub party at night, while in the corner window across the street "+E+" turns off his lamp to sleep",
  "close-up of "+E+" waking up in a dark simple bedroom at dawn, alarm clock showing 4:59, determined eyes",
  E+" kneeling in prayer beside his bed, first blue light of dawn through the window, peaceful",
  E+" reading an old book with a pen at a wooden desk, candle and cup of tea, phone face down",
  E+" jogging alone on an empty city street at sunrise, mist, streetlights turning off",
  "tired young people with sunglasses leaving a nightclub at morning while "+E+" walks past energized carrying bread, golden morning light",
  E+" standing on a mountain top at sunrise looking over the city, arms crossed, calm victory"]),
("carregando", 144, "carregando-disciplina", "epica", "CARREGANDO DISCIPLINA:|[0%]",
 ["0%", "12%", "37%", "58%", "79%", "94%", "100%"],
 ["Zero por cento. Ele acordava ao meio-dia, sem rumo, sem força, sem plano.",
  "Doze por cento. Um dia, arrumou a cama. Só isso. Mas foi o primeiro passo.",
  "Trinta e sete. Trocou uma hora de celular por uma hora de leitura.",
  "Cinquenta e oito. Caiu, voltou. Caiu de novo, voltou de novo.",
  "Setenta e nove. Os amigos riram. Ele continuou em silêncio.",
  "Noventa e quatro. Quase desistiu na última semana. Não desistiu.",
  "Cem por cento. *Disciplina não é talento. É carregar um pouco todo dia.* Em quantos por cento você está? Comenta."],
 ["a messy dark bedroom at noon, a young man with messy hair lying in bed scrolling his phone, pizza boxes, curtains closed",
  "the same young man with messy hair making his bed carefully, a small ray of sunlight entering the room",
  "the young man with messy hair reading a book on a chair, his phone in a drawer, warm lamp light",
  "the young man with messy hair falling on a running track in the rain and getting back up, determined",
  "friends laughing at the young man with messy hair at a bar while he drinks water, focused calm face",
  "the young man exhausted at night at a desk with papers, almost giving up, then clenching his fist",
  "the young man now confident, neat hair, fit, standing in a bright clean room at sunrise, proud smile"]),
("amor70", 145, "o-amor-que-durou-70-anos", "piano", "ELES FICARAM JUNTOS|POR [70 ANOS]. O SEGREDO:",
 ["1954", "1960", "1975", "1990", "2010", "2024", "O SEGREDO"],
 ["Setenta anos juntos. E quando perguntaram o segredo, ele respondeu em uma frase.",
  "Eles se conheceram num baile, em mil novecentos e cinquenta e quatro. Ele pisou no pé dela.",
  "Casaram sem dinheiro. A primeira casa tinha um quarto e uma goteira.",
  "Perderam um filho. Choraram juntos, em vez de se culpar.",
  "Ele perdeu o emprego. Ela vendeu as joias sem contar a ninguém.",
  "Já velhinhos, ele ainda abria a porta do carro. Ela ainda guardava o melhor pedaço para ele.",
  "O segredo? *Nós nascemos numa época em que, quando algo quebrava, a gente consertava.* Marca quem você quer do seu lado aos noventa."],
 ["an old couple in their nineties holding hands on a porch swing at sunset, gentle smiles, wedding photo on the wall",
  "a 1950s dance hall, a shy young man stepping on the foot of a young woman in a polka dot dress, both laughing",
  "the young couple in a tiny old room with a leaking roof and a bucket, hugging and laughing, rain outside",
  "the young couple sitting on the floor crying and holding each other, soft window light, grief and love",
  "the wife secretly giving her jewelry to a pawnshop owner, her husband looking at job ads at home",
  "an elderly man opening a car door for his elderly wife, she smiles at him like a young girl, autumn street",
  "the old couple in their nineties dancing slowly in their kitchen, a radio playing, warm golden light"]),
]
aqui = Path(__file__).parent
prompts = {}
for k, num, nome, clima, gancho, rot, rot_falas, imgs in V:
    prot = None
    d = aqui / f"{DATA}-{k}-criasse"
    d.mkdir(exist_ok=True)
    (d / "roteiro.txt").write_text("\n".join(rot_falas) + "\n", encoding="utf-8")
    cfg = {"titulo": "", "gancho": gancho, "fade_in": 0, "barra": True, "whoosh": True,
           "narracao": "narracao.wav", "tempos": "tempos.json",
           "imagens": [f"{i}.jpg" for i in range(1, 8)], "cenas": list(range(1, 8)),
           "focos": [0.35, 0.35, 0.4, 0.35, 0.4, 0.35, 0.3], "musica": "musica.wav",
           "volume_musica": 0.14, "idades": {str(i + 1): r for i, r in enumerate(rot)}}
    (d / "video.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
    prompts[k] = {"num": num, "nome": nome, "clima": clima, "prot": prot,
                  "prompts": [P + x + "." + S for x in imgs]}
(aqui / "prompts-lote6.json").write_text(json.dumps(prompts, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(V), "pastas")
