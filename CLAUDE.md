# Projeto: renda extra com conteúdo automático

Dono(a) do projeto fala português do Brasil. Responda sempre em português, simples e direto.

## Canal cristão (atual, começou em 2026-11-05)
- Pasta `canal-jesus/`. Vídeos feitos no **Google Flow** (plano Google AI Plus), que o usuário gera
  sozinho a partir dos prompts que escrevemos. Claude escreve roteiros e prompts e edita os clipes
  com ffmpeg (ordem, transições, legendas, volume, texto final).
- Personagem fixo de Jesus: `canal-jesus/personagem/FICHA.md` + imagens de referência.
- Série diária com escolha do público: `canal-jesus/SERIE.md`.
- Prompts do Flow: sempre em português, descrição completa dos personagens em cada cena, falas
  exatas entre aspas com quem fala, "Nenhuma fala em inglês", ação segundo a segundo, e dizer
  explicitamente quem NÃO fala ou NÃO faz algo.
- Edição: `canal-jesus/edicao/` (.ass das legendas). Vídeos .mp4 não vão para o git.
- Vídeos feitos: 01 (Jesus acalma a tempestade, editado). Dia 1 da série: prompts prontos.

## Outros projetos (sessões anteriores)
- Canal **Lamparina**: shorts no TikTok, Instagram e YouTube (≈59 publicados até 2026-11-03).
- Vídeos 3D "Amigos do Serginho" (Buri): branch `claude/beautiful-galileo-sg6kgn`, pasta `video3d/`.
- Lemo-Opuscar (`lemomo-ai/lemo-opuscar`): estilos de filme feitos em código, para vídeos especiais.

## Limites do ambiente na nuvem
- Hugging Face, Google Fonts e downloads de modelos estão bloqueados (sem Whisper local).
- PyPI e clone de repositórios públicos do GitHub funcionam.
