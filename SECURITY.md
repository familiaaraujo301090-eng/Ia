# Segurança do Rumo

Este documento lista as proteções do app, o que configurar em produção e como reportar um problema.

## Checklist de produção

- [ ] `NODE_ENV=production` (ativa cookie `Secure`/`__Host-`, HSTS e redirecionamento para HTTPS)
- [ ] `APP_URL` com o endereço público em `https://` (sem ele, os links de recuperação de senha **não são enviados**)
- [ ] `ADMIN_SECRET` longo e aleatório (o `render.yaml` gera um sozinho). Use uma vez em `#/admin`
- [ ] `ANTHROPIC_API_KEY` só nas variáveis do servidor, nunca no código. Com **limite de gastos** no painel da Anthropic
- [ ] Disco persistente para o banco (`DB_PATH`) e **backup** periódico desse arquivo
- [ ] `SMTP_URL` de um provedor de e-mail confiável (para recuperação de senha)

## O que o app faz

### Contas e senhas
- Senhas com **scrypt** (N=32768, r=8, p=1, sal aleatório). Hashes antigos são atualizados no próximo login.
- Senha entre 8 e 200 caracteres (o teto evita travar o servidor com senhas gigantes).
- Login com **limite de tentativas** por IP (30 a cada 15 min) e por e-mail (10 a cada 15 min).
- Mesmo tempo de resposta e mesma mensagem quando o e-mail não existe (não revela quem tem conta).
- Cadastro limitado por IP (`REGISTER_PER_HOUR`).
- Recuperação de senha: token aleatório de 256 bits, guardado só como hash, vale 1 hora, uso único, e links antigos são invalidados. Trocar ou redefinir a senha **desconecta os outros aparelhos**.
- Excluir a conta exige confirmar a senha.

### Sessões
- Token aleatório de 256 bits. O banco guarda **só o hash** (se o banco vazar, as sessões não servem).
- Cookie `HttpOnly`, `SameSite=Lax`, e em produção `Secure` com prefixo `__Host-`.
- Sessões expiradas são apagadas automaticamente.

### Navegador
- **Content-Security-Policy** restrita: só scripts do próprio site, sem `eval`, sem plugins, sem ser embutido em outros sites (`frame-ancestors 'none'`).
- `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Cross-Origin-Opener-Policy`, `Permissions-Policy` (câmera e localização bloqueadas; microfone só no próprio site).
- **HSTS** e redirecionamento para HTTPS em produção.
- **XSS**: todo texto do usuário e da IA passa por escape antes de virar HTML. O markdown só gera links `http(s)` e eles abrem com `noopener noreferrer`.
- **CSRF**: ações só são aceitas em JSON, vindas do próprio site (cabeçalhos `Origin`/`Sec-Fetch-Site` conferidos), além do `SameSite`.
- Respostas da API com `Cache-Control: no-store`.

### Dados e permissões
- Toda consulta ao banco usa parâmetros (sem SQL injection) e filtra pelo usuário logado: ninguém vê ou altera dados de outra conta.
- Painel admin liberado só para quem digita o `ADMIN_SECRET` (não depende de e-mail, que não é verificado).
- Limite de itens por conta (tarefas, notas, metas…) e limite diário de IA por plano, contra abuso e custo descontrolado.
- Erros internos nunca são mostrados ao usuário (só mensagens pensadas para ele).

### Notificações
- Inscrições aceitas **só** de serviços oficiais de push (Google, Mozilla, Apple, Microsoft) via HTTPS. Isso impede usar o servidor para acessar endereços internos (SSRF).
- No máximo 10 aparelhos por conta.

### Inteligência artificial
- As ações da IA (criar, concluir, excluir tarefas…) só atingem os dados da própria pessoa e passam por validação.
- A IA é instruída a tratar páginas da web e resultados de busca como **dados, não ordens** (proteção contra *prompt injection*) e a nunca pedir senhas ou dados de cartão.
- Se a pessoa sai no meio da resposta, a IA para de gerar (economia e menos exposição).
- Fotos enviadas para legenda são reduzidas no navegador e têm tipo e tamanho validados.

### Testes
Os testes automáticos (`npm test`) verificam: cabeçalhos, bloqueio de CSRF, hash de sessões e senhas, atualização de hashes antigos, limites de força bruta, bloqueio de SSRF, exclusão de conta com senha, não vazamento de erros, isolamento entre usuários e permissões de admin.

## Limitações conhecidas
- E-mails não são verificados no cadastro (alguém pode criar conta com o e-mail de outra pessoa, mas não acessa a conta dela).
- Os limites de tentativas ficam na memória do servidor: reiniciar zera os contadores, e com várias instâncias cada uma conta separado.
- A versão de teste (link que roda só no navegador) guarda os dados no próprio navegador e não tem nenhuma dessas proteções de servidor. Ela serve só para demonstração.

## Reportar um problema
Encontrou uma falha? Não publique. Envie os detalhes para o responsável pelo app pelo e-mail de contato e aguarde a correção.
