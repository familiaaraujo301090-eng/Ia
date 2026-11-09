# Rumo: metas, agenda e IA

App web (funciona como app no celular) com uma IA conectada (Claude, da Anthropic) e banco de dados separado para cada usuário.

**O que ele faz:**

| Área | O que faz |
|---|---|
| **Página inicial** | Para quem ainda não tem conta: apresentação, como funciona, recursos, planos e perguntas frequentes. |
| **Boas-vindas** | Passo a passo de 8 perguntas (perfil, meta, prazo, tempo por dia, tom da IA) que já cria a meta com plano de 7 dias. Depois, um tutorial rápido. |
| **Hoje** | O dia em forma de conversa com a IA. Tarefas viram cartões com **✓ Feito** (com Desfazer), **🆘 Me ajuda** (solução pronta, passo a passo e links), **▶ Foco** (cronômetro), **💬 Falar** e **⏭ Amanhã**. Você também pode escrever ou **falar por voz** (“fiz a primeira”, “hoje não dá”) e a IA atualiza o app. Confete quando o dia fecha 🎉. |
| **Metas** | Você cadastra onde quer chegar, com prazo e motivo, e a IA cria o plano com marcos e tarefas diárias de 5 a 45 minutos. Quando as tarefas de uma meta acabam, o Hoje oferece planejar a próxima semana. Inclui o **Plano de divulgação 30 dias** pronto para importar. |
| **Hábitos** | Rotinas (ex: “ler 10 páginas”) que viram tarefa sozinhas nos dias escolhidos, com sequência 🔥 e os últimos 7 dias. |
| **Agenda** | Escreva do seu jeito (“dentista amanhã às 15h”) e a IA agenda. Também aceita cadastro manual e compromissos que se repetem (todo dia, dias úteis, semanal, mensal). |
| **Conversar** | Chat com a IA, que conhece suas metas, tarefas e agenda. As respostas aparecem em tempo real. |
| **Editor** | Notas com IA: melhorar, corrigir, resumir, expandir, continuar, virar post, virar roteiro de vídeo, extrair tarefas ou um pedido livre. |
| **Amplificar ideias** | Uma ideia crua vira ângulos, público, formas de ganhar dinheiro, riscos, ideias de conteúdo e próximos passos. Dá para salvar como nota ou transformar em meta com plano. |
| **Legendas** | Três legendas prontas por post (gancho, texto, CTA, hashtags), com melhor horário e uma dica. Dá para **anexar a foto** e a IA escreve olhando a imagem. |
| **Perfil** | Sobre você, nicho, tempo por dia e tom da IA. Plano e uso de IA do dia, **lembrete diário no celular** (notificação), troca de senha, tema claro/escuro, exportação dos dados e exclusão da conta. |
| **Conta** | Recuperação de senha por e-mail (“Esqueci minha senha”). |
| **Painel admin** | Para os e-mails em `ADMIN_EMAILS`: usuários, ativos, uso da IA, cadastros por dia e troca de plano (Grátis/Pro). |

O plano completo para divulgar o app está em **[docs/PLANO_DE_DIVULGACAO.md](docs/PLANO_DE_DIVULGACAO.md)**: 30 dias com uma tarefa por dia, posicionamento, conteúdo, canais, preços e métricas.

---

## Rodar no seu computador

Precisa do **Node.js 22.13 ou mais novo** (https://nodejs.org).

```bash
npm install
```

```bash
ANTHROPIC_API_KEY=sua-chave npm start
```

Abra http://localhost:3000 e crie sua conta.

> Sem `ANTHROPIC_API_KEY` o app funciona em **modo demonstração**, com respostas de exemplo. Pegue sua chave em https://console.anthropic.com (API Keys) e configure um limite de gastos.

## Colocar no ar (grátis ou barato)

### Opção A: Render (mais fácil)
1. Crie uma conta em https://render.com e conecte este repositório do GitHub.
2. Clique em **New → Blueprint** e escolha o repositório. O `render.yaml` já configura tudo, inclusive o disco que guarda o banco.
3. Preencha `ANTHROPIC_API_KEY` quando pedir.
4. Depois do deploy, abra o link `https://rumo-xxxx.onrender.com` e, no celular, use **Adicionar à tela inicial**.

### Opção B: Railway / Fly.io / qualquer VPS com Docker
```bash
docker build -t rumo .
```

```bash
docker run -p 3000:3000 -e ANTHROPIC_API_KEY=sua-chave -v rumo-data:/data rumo
```

**Importante:** o banco é um arquivo SQLite. Em produção ele precisa ficar num **disco persistente** (variável `DB_PATH`), senão os dados se perdem a cada deploy.

## Configurações (variáveis de ambiente)

| Variável | Padrão | Para quê |
|---|---|---|
| `ANTHROPIC_API_KEY` | (vazio, modo demonstração) | Chave do Claude |
| `CLAUDE_MODEL` | `claude-opus-5-5` | Modelo da IA |
| `DB_PATH` | `./data/rumo.db` | Onde fica o banco |
| `PORT` | `3000` | Porta HTTP |
| `TZ_APP` | `America/Sao_Paulo` | Fuso usado para definir o “hoje” |
| `AI_PER_MINUTE` | `20` | Limite de pedidos à IA por usuário por minuto |
| `FREE_AI_PER_DAY` | `30` | Ações de IA por dia no plano Grátis |
| `PRO_AI_PER_DAY` | `300` | Ações de IA por dia no plano Pro |
| `PRO_CHECKOUT_URL` | (vazio) | Link de pagamento do Pro (ex: link do Mercado Pago). Aparece no Perfil. Depois do pagamento, mude o plano no Painel admin |
| `ADMIN_EMAILS` | (vazio) | E-mails com acesso ao Painel admin, separados por vírgula |
| `APP_URL` | (endereço do pedido) | Endereço público do app, usado no link de recuperação de senha |
| `SMTP_URL` | (vazio) | Servidor de e-mail, ex: `smtps://usuario:senha@smtp.provedor.com:465`. Sem ele, o link de recuperação aparece no log |
| `MAIL_FROM` | `Rumo <no-reply@rumo.app>` | Remetente dos e-mails |
| `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | (gerados sozinhos) | Chaves das notificações. Se não definir, o app gera e guarda no banco |
| `NODE_ENV` | (vazio) | Use `production` para cookies seguros (HTTPS) |

## Como funciona por dentro

- **Servidor:** Node.js + Express (`server/`)
- **Banco:** SQLite nativo do Node (`node:sqlite`), sem instalar nada extra. Cada registro pertence a um usuário e todas as consultas filtram pelo usuário logado.
- **Login:** e-mail e senha (hash `scrypt`), sessão em cookie `HttpOnly` de 30 dias, com limite de tentativas.
- **IA:** SDK oficial `@anthropic-ai/sdk`, com saídas estruturadas (JSON validado com Zod) para planos, legendas e ideias, streaming no chat e fallback automático no servidor (`server/ai.js`). O contexto do usuário (metas, tarefas, agenda) vai junto em cada pedido.
- **Front-end:** HTML, CSS e JavaScript puros (`public/`), sem etapa de build, instalável como PWA.

```
server/
  index.js        inicia o servidor
  app.js          rotas da API
  db.js           tabelas SQLite
  auth.js         senha, sessão e cookie
  ai.js           integração com o Claude
  extras.js       planos, hábitos, repetições, senha, lembretes, admin
  push.js         notificações (Web Push)
  mail.js         envio de e-mail
  demo.js         respostas do modo demonstração
  launchPlan.js   plano de 30 dias importável
public/           interface (PWA)
test/             testes automatizados (npm test)
docs/             plano de divulgação
demo/, scripts/   versão de teste que roda só no navegador (node scripts/build-demo.mjs)
```

## Testes

```bash
npm test
```

Cobrem login, criação de planos, o plano de 30 dias, as ferramentas de IA (modo demo) e o **isolamento entre usuários** (um usuário não vê nem altera dados de outro).

## Próximas melhorias (roadmap)

- [x] Limites de IA por plano (Grátis/Pro) e link de pagamento
- [x] Lembrete diário por notificação
- [x] Eventos que se repetem e hábitos
- [x] Legenda olhando a foto do post
- [x] Recuperação e troca de senha
- [x] Painel de administração
- [ ] Pagamento automático (webhook do Mercado Pago/Stripe liberando o Pro sozinho)
- [ ] Login com Google
- [ ] Calendário de conteúdo (posts da semana planejados pela IA)
- [ ] Conversa por áudio com resposta falada
