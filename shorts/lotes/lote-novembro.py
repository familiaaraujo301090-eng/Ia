#!/usr/bin/env python3
"""Lote de novembro: 16 narrados (ritmo rapido) + 4 citacoes. Cria pastas, roteiros e video.json.

Uso: python lotes/lote-novembro.py criar   (pastas, roteiros e json)
     python lotes/lote-novembro.py voz     (narracoes com --rapido)
"""
import json, subprocess, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
P = "pintura"

# (pasta, modelo, titulo, cenas, formatos, focos, paragrafos)
NARRADOS = [
 ("2026-11-02-hipatia", P, "Pensar diferente custou a vida dela", [1,2,3,5,6,7], ["faixa","alta","faixa","faixa","preto","alta"], [0.35,0.4,0.35,0.35,0.5,0.35], [
  "Você é a pessoa mais inteligente da sua cidade. E isso vai custar a sua vida.",
  "Alexandria, ano 415. Hipátia era matemática, astrônoma e filósofa.",
  "Ela dava aulas para cristãos e pagãos. Homens importantes vinham ouvir uma mulher ensinar.",
  "Mas a cidade estava dividida numa briga política entre o governador e o bispo.",
  "E Hipátia, amiga do governador, virou o alvo perfeito.",
  "Uma multidão a arrancou da carruagem. Ela foi morta de forma brutal.",
  "*Ela não morreu por um erro. Morreu porque era fácil culpar quem pensava diferente.*",
  "Quando uma multidão procura um culpado, quase nunca procura a verdade.",
  "Você já viu alguém virar culpado só por pensar diferente? Segue a Lamparina."]),
 ("2026-11-02-ancoragem", "gravura", "O truque do preço riscado", [1,3,5,7,8], None, [0.4,0.4,0.4,0.4,0.4], [
  "Uma camisa custa mil reais. Ao lado, uma por duzentos. Parece barata, não parece?",
  "Esse truque tem nome: ancoragem.",
  "Em 1974, os psicólogos Amos Tversky e Daniel Kahneman giraram uma roda da sorte na frente de voluntários.",
  "A roda parava no 10 ou no 65. Depois vinha a pergunta: qual a porcentagem de países africanos na ONU?",
  "Quem viu o 10 chutava, em média, 25 por cento. Quem viu o 65 chutava 45.",
  "Um número sem sentido nenhum mudou a resposta de pessoas inteligentes.",
  "*O primeiro número que você vê decide o que você acha caro ou barato.*",
  "Antes de comprar, pergunte: quanto isso vale para mim, sem o preço do lado?",
  "Qual foi a última vez que um de, por te pegou? Segue a Lamparina."]),
 ("2026-11-02-escassez", "tipografia", "Só hoje: por que você cai", [1,2,4,6,7], None, None, [
  "Últimas unidades. Só hoje. Você sente o coração acelerar? É de propósito.",
  "Em 1975, o psicólogo Stephen Worchel fez um teste simples com biscoitos.",
  "Um pote tinha dez biscoitos. O outro, só dois. Os biscoitos eram iguais.",
  "As pessoas acharam os do pote quase vazio mais gostosos e mais desejáveis.",
  "Robert Cialdini chamou isso de escassez: o que parece raro, parece valioso.",
  "Por isso o cronômetro na tela, o estoque acabando, a oferta que some à meia-noite.",
  "*Quando alguém te apressa, é porque não quer que você pense.*",
  "Diante do só hoje, respire e pergunte: eu compraria isso se tivesse uma semana?",
  "Qual foi a sua compra por impulso mais cara? Segue a Lamparina."]),
 ("2026-11-02-bombardeio-de-amor", "classico", "Bom demais para ser verdade", [1,3,4,5,7], None, [0.4,0.45,0.4,0.4,0.4], [
  "Ele te conheceu há duas semanas e já diz que você é a pessoa da vida dele. Cuidado.",
  "Isso tem nome: bombardeio de amor.",
  "O termo surgiu nos anos setenta, para descrever como algumas seitas recebiam os novos membros: elogios, abraços e atenção sem fim.",
  "A pessoa se sente amada como nunca. E aí fica difícil ir embora.",
  "Em relacionamentos, o roteiro é parecido: carinho demais, rápido demais, e depois controle.",
  "Quando o carinho some, você faz de tudo para ter de volta aquele começo.",
  "*Amor de verdade não tem pressa. Quem tem pressa quer te prender.*",
  "Amor que cresce devagar dá tempo de você conhecer quem está do seu lado.",
  "Você já viveu um começo bom demais para ser verdade? Segue a Lamparina."]),
 ("2026-11-03-giordano-bruno", P, "Ele não negou nem diante da fogueira", [1,2,4,5,6,7], ["faixa","alta","faixa","preto","alta","faixa"], [0.35,0.35,0.35,0.5,0.35,0.4], [
  "Você tem uma ideia que ninguém aceita. Desistiria dela para salvar a sua vida?",
  "Giordano Bruno era um frade italiano que dizia, entre outras coisas, algo absurdo para o século dezesseis.",
  "Que o universo era infinito, e que as estrelas eram sóis, com mundos girando em volta delas.",
  "Ficou preso por oito anos. Pediram que ele negasse tudo. Ele não negou.",
  "Em 1600, em Roma, ouviu a sentença: morte na fogueira.",
  "E respondeu aos juízes: *talvez vocês tenham mais medo de pronunciar essa sentença do que eu de recebê-la.*",
  "Ele foi queimado no Campo de' Fiori. Hoje, no mesmo lugar, existe uma estátua dele.",
  "Quem tem medo da verdade, às vezes, é justamente quem tem o poder.",
  "Por qual ideia você estaria disposto a pagar caro? Segue a Lamparina."]),
 ("2026-11-03-voltaire-frase", P, "Voltaire nunca disse isso", [1,2,4,5,7,8], ["alta","faixa","faixa","faixa","preto","alta"], [0.35,0.4,0.35,0.35,0.5,0.35], [
  "Você já compartilhou esta frase de Voltaire. Só que ele nunca disse isso.",
  "Posso não concordar com uma palavra do que dizes, mas defenderei até a morte o teu direito de dizê-lo.",
  "Está em camisetas, discursos e livros. Sempre com o nome de Voltaire.",
  "Mas a frase foi escrita em 1906, por uma inglesa: Evelyn Beatrice Hall.",
  "Ela escrevia sobre a vida de Voltaire e resumiu, com palavras dela, o que ele pensava.",
  "Com o tempo, o resumo virou citação. E a citação ganhou o dono errado.",
  "*Uma frase bonita viaja mais rápido do que a verdade sobre ela.*",
  "Antes de compartilhar, pergunte: quem disse, onde e quando?",
  "Qual outra frase famosa você acha que é falsa? Segue a Lamparina."]),
 ("2026-11-03-nietzsche-deus-morto", "gravura", "Nietzsche não estava comemorando", [1,3,4,5,7], None, [0.35,0.35,0.35,0.35,0.35], [
  "Deus está morto. Você acha que Nietzsche disse isso comemorando? Ele estava de luto.",
  "A frase aparece em A Gaia Ciência, de 1882.",
  "Um louco entra na praça com uma lanterna acesa, em plena manhã, gritando: procuro Deus!",
  "As pessoas riem dele. E ele diz: Deus está morto. E nós o matamos.",
  "Mas o louco não comemora. Ele pergunta: como vamos nos consolar?",
  "Nietzsche via o que vinha: se a fé cai, o que segura o sentido da vida?",
  "*Não era uma vitória. Era um aviso.*",
  "Ele temia um mundo sem rumo, o niilismo. E o século vinte deu razão ao medo dele.",
  "O que segura o sentido da sua vida hoje? Segue a Lamparina."]),
 ("2026-11-03-sun-tzu", "tipografia", "Vencer sem lutar", [1,2,4,5,7], None, None, [
  "Você ganha a discussão, mas perde a pessoa. Isso foi uma vitória?",
  "Há uns 2.500 anos, na China, um general escreveu A Arte da Guerra.",
  "O nome dele era Sun Tzu. E o livro mais famoso sobre guerra ensina a evitar a guerra.",
  "Ele escreveu: *a suprema arte da guerra é vencer o inimigo sem lutar.*",
  "Para ele, cem vitórias em cem batalhas não eram o melhor resultado.",
  "O melhor era nem precisar da batalha: entender o outro, se preparar, e tornar a luta inútil.",
  "Na sua vida também: nem toda provocação merece resposta. Nem toda briga precisa de vencedor.",
  "Qual briga você poderia ter ganhado sem lutar? Segue a Lamparina."]),
 ("2026-11-04-arendt", P, "O monstro era um funcionário comum", [1,2,3,4,6,7], ["faixa","alta","faixa","alta","preto","faixa"], [0.4,0.35,0.35,0.35,0.5,0.35], [
  "Você imagina o monstro que organizou um genocídio. Agora imagine um funcionário comum.",
  "Jerusalém, 1961. A filósofa Hannah Arendt foi assistir ao julgamento de Adolf Eichmann.",
  "Ele organizou o transporte de milhões de judeus para os campos de extermínio.",
  "Ela esperava um demônio. Encontrou um burocrata sem graça, que repetia frases prontas.",
  "Ele dizia que só cumpria ordens. Que só fazia o trabalho dele.",
  "Arendt deu um nome a isso: *a banalidade do mal.*",
  "O mal mais perigoso não é o de quem tem ódio. É o de quem para de pensar e só obedece.",
  "Que ordem você cumpre sem nunca perguntar por quê? Segue a Lamparina."]),
 ("2026-11-04-seneca-nero", P, "O aluno mandou o mestre morrer", [1,2,4,5,6,7], ["faixa","alta","faixa","preto","alta","faixa"], [0.35,0.35,0.35,0.5,0.35,0.35], [
  "Você educa um menino por anos. Ele vira imperador. E manda você morrer.",
  "Sêneca foi o professor de Nero, o imperador de Roma.",
  "Por anos, ele tentou ensinar ao aluno o controle da raiva e da ambição.",
  "Mas Nero mandou matar a própria mãe. E, no ano 65, acusou o velho mestre de conspiração.",
  "A ordem chegou: Sêneca tinha que tirar a própria vida.",
  "Os amigos choravam. Ele, calmo, pediu que lembrassem da vida que ele tinha vivido.",
  "*Ele deixou para os amigos a única coisa que ninguém podia tirar: o exemplo.*",
  "Ninguém controla como vai ser tratado. Mas você escolhe quem vai ser até o fim.",
  "Que exemplo você está deixando? Segue a Lamparina."]),
 ("2026-11-04-mulher-de-lo", "gravura", "Não olhe para trás", [1,3,4,5,7], None, [0.4,0.4,0.4,0.35,0.4], [
  "Atrás de você, tudo está pegando fogo. A ordem é: não olhe para trás.",
  "Gênesis, capítulo dezenove. Sodoma ia ser destruída.",
  "Dois anjos tiram Ló, a mulher e as filhas da cidade, e avisam: fujam, e não olhem para trás.",
  "Eles correm. O céu cai em fogo e enxofre sobre a cidade.",
  "A mulher de Ló olha para trás. E vira uma estátua de sal.",
  "Ela estava salva. Mas o coração dela tinha ficado lá.",
  "*Quem vive olhando para o que perdeu fica parado onde perdeu.*",
  "Às vezes o passado não te segura pela mão. É você que não solta.",
  "Para o que você ainda não parou de olhar? Segue a Lamparina."]),
 ("2026-11-04-dilema-do-bonde", "classico", "Você puxaria a alavanca?", [1,2,4,6,7], None, [0.45,0.4,0.45,0.4,0.4], [
  "Um bonde desgovernado vai matar cinco pessoas. Você pode puxar uma alavanca. Mas aí ele mata uma.",
  "Esse é o dilema do bonde, criado pela filósofa Philippa Foot em 1967.",
  "A maioria das pessoas puxa a alavanca. Cinco vidas valem mais que uma.",
  "Depois, a filósofa Judith Thomson mudou uma coisa: para parar o bonde, você teria que empurrar um homem de uma ponte.",
  "A conta é a mesma: um morre, cinco vivem. Mas quase todo mundo diz não.",
  "Por quê? Porque uma coisa é deixar acontecer. Outra é sujar as próprias mãos.",
  "*A sua moral não é só matemática. Ela sente.*",
  "Filósofos discutem isso há quase sessenta anos, e ninguém fechou a resposta.",
  "E você, puxaria a alavanca? E empurraria o homem? Segue a Lamparina."]),
 ("2026-11-05-la-boetie", P, "Um só homem manda em milhões", [1,2,4,5,6,7], ["faixa","alta","faixa","alta","preto","faixa"], [0.4,0.35,0.4,0.35,0.5,0.4], [
  "Um único homem manda em milhões. Como isso é possível?",
  "França, século dezesseis. Um jovem de uns dezoito anos, Étienne de La Boétie, fez essa pergunta.",
  "E escreveu o Discurso da Servidão Voluntária.",
  "A resposta dele é desconfortável: o tirano só tem o poder que os outros entregam a ele.",
  "Ele tem dois olhos e duas mãos, como qualquer um. Os olhos e as mãos que ele usa são os do povo.",
  "*Decidam não servir mais, e vocês estarão livres.*",
  "Ele não pedia guerra. Pedia só que as pessoas parassem de sustentar o que as oprime.",
  "O que você sustenta todo dia, mesmo sem concordar? Segue a Lamparina."]),
 ("2026-11-05-boecio", P, "Do palácio para a cela", [1,2,3,5,7,8], ["alta","faixa","faixa","alta","preto","faixa"], [0.35,0.35,0.35,0.35,0.5,0.35], [
  "Ontem você era o homem mais poderoso do reino. Hoje está numa cela esperando a morte.",
  "Ano 524. Boécio era cônsul de Roma e conselheiro do rei Teodorico.",
  "Acusado de traição, perdeu tudo: cargo, fortuna e liberdade.",
  "Na prisão, ele escreveu A Consolação da Filosofia.",
  "No livro, a Filosofia aparece como uma mulher e explica para ele a roda da Fortuna.",
  "Quem sobe na roda, um dia desce. Riqueza e fama nunca foram dele: estavam só emprestadas.",
  "*O que a sorte te deu, a sorte pode tirar. O que você é, ninguém tira.*",
  "Boécio foi executado. O livro dele foi um dos mais lidos da Idade Média.",
  "O que você tem que ninguém pode tirar? Segue a Lamparina."]),
 ("2026-11-05-diabo-cita-biblia", P, "Quando o diabo citou a Bíblia", [1,2,3,5,6,7], ["faixa","alta","faixa","faixa","alta","preto"], [0.4,0.35,0.35,0.35,0.35,0.5], [
  "Alguém usa a Bíblia para te convencer de algo errado. Você perceberia?",
  "No deserto, depois de quarenta dias de jejum, Jesus foi tentado.",
  "O diabo o levou ao ponto mais alto do templo e disse: joga-te daqui.",
  "E citou as Escrituras: está escrito que os anjos te segurarão.",
  "Era um versículo verdadeiro, do Salmo 91. Usado para uma mentira.",
  "Jesus respondeu com outro: também está escrito, não tentarás o Senhor teu Deus.",
  "*Até a verdade pode te enganar, quando é arrancada do contexto.*",
  "Quem cita muito nem sempre é quem entende. Leia o texto inteiro.",
  "Você já viu alguém usar uma frase verdadeira para enganar? Segue a Lamparina."]),
 ("2026-11-05-orwell", "tipografia", "Sem a palavra, sem a ideia", [1,2,3,5,6], None, None, [
  "Se tiram uma palavra da sua língua, você ainda consegue pensar naquilo?",
  "Em 1949, George Orwell publicou 1984.",
  "No livro, o governo cria a Novilíngua: uma língua que fica menor a cada ano.",
  "Palavras como liberdade e rebeldia vão sumindo do dicionário.",
  "O objetivo, explica um personagem, é estreitar o pensamento. Sem a palavra, a ideia não se forma.",
  "*Quem controla as palavras controla o que você consegue pensar.*",
  "Por isso, desconfie quando alguém troca o nome das coisas para elas parecerem menores.",
  "Qual palavra você acha que estão tentando mudar hoje? Segue a Lamparina."]),
]

CITACOES = [
 ("2026-11-02-citacao-marco-aurelio", "A melhor vingança é não ser como quem te feriu.", "Marco Aurélio, Meditações 6.6"),
 ("2026-11-03-citacao-pascal", "O coração tem razões que a própria razão desconhece.", "Blaise Pascal, Pensamentos"),
 ("2026-11-04-citacao-eclesiastes", "O que foi, isso será; nada há de novo debaixo do sol.", "Eclesiastes 1:9"),
 ("2026-11-05-citacao-kierkegaard", "A vida só pode ser compreendida olhando para trás, mas deve ser vivida olhando para frente.", "Søren Kierkegaard, Diários (paráfrase)"),
]


def criar():
    for pasta, modelo, titulo, cenas, formatos, focos, pars in NARRADOS:
        d = RAIZ / pasta
        d.mkdir(exist_ok=True)
        (d / "roteiro.txt").write_text("\n".join(pars) + "\n", encoding="utf-8")
        n = len(cenas)
        imagens, k = [], 1
        for f in (formatos or ["faixa"] * n):
            if f == "preto":
                imagens.append("preto")
            else:
                imagens.append(f"{k}.jpg"); k += 1
        cfg = {"titulo": titulo, "narracao": "narracao.wav", "tempos": "tempos.json",
               "imagens": imagens, "cenas": cenas}
        if modelo != "classico":
            cfg["modelo"] = modelo
        else:
            cfg.update(musica="trilha-piano.wav", volume_musica=0.12)
        if formatos:
            cfg["formatos"] = ["faixa" if f == "preto" else f for f in formatos]
        if focos:
            cfg["focos"] = focos
        (d / "video.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    for pasta, texto, autor in CITACOES:
        d = RAIZ / pasta
        d.mkdir(exist_ok=True)
        (d / "video.json").write_text(json.dumps({"modelo": "citacao", "imagens": ["1.jpg"],
            "citacao": {"texto": texto, "autor": autor, "duracao": 16}}, ensure_ascii=False, indent=2),
            encoding="utf-8")


def voz():
    for pasta, modelo, *_ in NARRADOS:
        d = RAIZ / pasta
        if not (d / "narracao.wav").exists():
            subprocess.run([sys.executable, str(RAIZ / "gerar_voz.py"), str(d), "pm_santa", "1.05", "0.96",
                            "--rapido"], check=True)
        if modelo == "classico":
            dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                                 "-of", "csv=p=0", str(d / "narracao.wav")]))
            subprocess.run([sys.executable, str(RAIZ / "trilha.py"), "piano", f"{dur + 2:.1f}",
                            str(d / "trilha-piano.wav")], check=True)


if __name__ == "__main__":
    {"criar": criar, "voz": voz}[sys.argv[1]]()
