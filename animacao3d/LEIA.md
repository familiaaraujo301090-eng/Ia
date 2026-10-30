# Animacao 3D por codigo (Blender como biblioteca Python)

Gera curtas 3D de curiosidades sem editor de video: personagem, cenario, animacao, cameras,
render e montagem, tudo em Python.

Instalar uma vez: `pip install bpy==5.2.3` (Blender 5.2 como modulo). Render com Cycles na CPU.

    python gerar.py preparar   # narracao + cena .blend + folhas (personagem, cenario, storyboard)
    python gerar.py quadros    # renderiza os quadros (retoma se parar; ~10 s por quadro)
    python gerar.py finalizar  # quadros + voz + trilha + legendas -> saida/<nome>/video.mp4

Arquivos:
- `personagem.py`: Mestre Elias montado com primitivas (manto, capuz, barba, lamparina acesa),
  com pontos de controle para animar (raiz, cabeca, bracos, luz).
- `cenario.py`: biblioteca de pedra com estantes e livros aleatorios, colunas, mesa e velas.
- `materiais.py`: materiais procedurais (la, pele, latao, pedra, madeira, chama).
- `historia.py`: roteiro + planos. Cada plano tem uma camera (travelling, grua, orbita,
  aproximacao) e acoes do personagem (andar, girar, erguer a lamparina, acenar). Os cortes
  caem no inicio de cada paragrafo da narracao.
- `folhas.py`: monta as folhas de referencia a partir do proprio 3D.

Para um video novo: copie o dicionario `LAMPARINA` em `historia.py`, troque o roteiro e os
planos, e mude `NOME`/`HIST` em `gerar.py`.
