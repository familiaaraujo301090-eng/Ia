// Respostas de demonstração usadas quando nenhuma chave de IA está configurada.
// Permitem testar todo o app offline; com ANTHROPIC_API_KEY o Claude assume.
import { localDate, localDateTime, addDays } from './time.js';

const NOTE = '\n\n> _Modo demonstração: configure `ANTHROPIC_API_KEY` para respostas reais da IA._';

export function chat(user, message) {
  const m = message.toLowerCase();
  let body;
  if (/trav|desanim|cansad|preguiç|procrastin/.test(m)) {
    body = `Entendo, ${user.name}. Quando trava, o passo está grande demais.\n\n**Faça só isto agora (5 min):** abra a tarefa mais fácil da lista de hoje e faça a primeira linha. Só isso. Depois me conta.`;
  } else if (/meta|objetivo|sonho/.test(m)) {
    body = `Ótimo! Vá em **Metas**, cadastre essa meta com prazo e o *porquê*, e toque em **Gerar plano com IA**. Eu quebro em tarefas diárias pequenas.`;
  } else if (/divulg|post|instagram|tiktok|legenda/.test(m)) {
    body = `Para divulgar bem: **consistência > perfeição**. Use a aba **Legendas** para criar o texto do post de hoje e importe o **Plano de divulgação de 30 dias** em Metas.`;
  } else {
    body = `Estou aqui, ${user.name}! Posso te ajudar a:\n- organizar sua **agenda**\n- quebrar **metas** em tarefas diárias\n- **amplificar ideias**\n- escrever **legendas** e textos\n\nPor onde começamos?`;
  }
  return body + NOTE;
}

const LINKS = [
  [/post|reels|vídeo|video|conteúdo|conteudo|story|stories|carrossel|grav/i, [['Canva (artes e carrosséis grátis)', 'https://www.canva.com'], ['CapCut (editar vídeos)', 'https://www.capcut.com']]],
  [/bio|perfil|instagram/i, [['Linktree (link na bio)', 'https://linktr.ee'], ['Central de Ajuda do Instagram', 'https://help.instagram.com']]],
  [/página|pagina|site|landing|captura/i, [['Carrd (página simples)', 'https://carrd.co'], ['Google Sites (grátis)', 'https://sites.google.com']]],
  [/anúncio|anuncio|impulsion|tráfego|trafego/i, [['Meta Ads (anúncios)', 'https://www.facebook.com/business/ads']]],
  [/whatsapp|mensag|direct|dm/i, [['WhatsApp Business', 'https://business.whatsapp.com']]],
  [/pagamento|cobrar|pix|venda/i, [['Mercado Pago', 'https://www.mercadopago.com.br']]],
];

function helpReply(task) {
  const links = LINKS.filter(([re]) => re.test(`${task.title} ${task.detail}`)).flatMap(([, l]) => l);
  links.push(['Pesquisar no Google', `https://www.google.com/search?q=${encodeURIComponent(task.title)}`]);
  return `Bora resolver **${task.title}** juntos 👇

**Passo a passo (${task.minutes} min):**
1. Separe ${Math.max(5, Math.round(task.minutes / 3))} minutos sem celular e abra só o que precisa.
2. Faça a versão mais simples possível primeiro. ${task.detail || ''}
3. Revise rapidinho e finalize. Feito é melhor que perfeito.
4. Volte aqui e toque em **✓ Feito**.

**Links úteis:**
${links.map(([n, u]) => `- [${n}](${u})`).join('\n')}${NOTE}`;
}

/** Turno de conversa no modo demonstração: entende alguns pedidos e age no app. */
export function chatTurn(user, message, { helpTask = null, todayTasks = [], act = () => '' } = {}) {
  if (helpTask) return helpReply(helpTask);
  const m = message.toLowerCase();
  const pending = todayTasks.filter((t) => !t.done);
  if (/terminei tudo|fiz tudo|conclu[ií] tudo/.test(m)) {
    pending.forEach((t) => act('concluir_tarefa', { task_id: t.id }));
    return `Que dia! 🔥 Marquei ${pending.length} tarefa(s) como feitas. Quer uma tarefa extra ou prefere descansar com a consciência tranquila?${NOTE}`;
  }
  if (/sem tempo|não vou conseguir|nao vou conseguir|adiar|amanhã eu faço|cansad/.test(m)) {
    const tomorrow = addDays(localDate(), 1);
    pending.slice(1).forEach((t) => act('reagendar_tarefa', { task_id: t.id, due_date: tomorrow }));
    return pending.length
      ? `Tudo bem, a vida acontece. Deixei só **${pending[0].title}** para hoje e passei o resto para amanhã. Consegue fazer essa uma?${NOTE}`
      : `Hoje está livre de tarefas pendentes. Descansa! 😌${NOTE}`;
  }
  const doneMatch = pending.find((t) => m.includes(t.title.toLowerCase().slice(0, 18)));
  if (doneMatch && /fiz|feito|terminei|concluí|conclui/.test(m)) {
    act('concluir_tarefa', { task_id: doneMatch.id });
    return `Boa! Marquei **${doneMatch.title}** como feita. ✅${NOTE}`;
  }
  if (/(agend|marc)\w*/.test(m) && /(\d{1,2}\s*(h|:)|amanh|hoje)/.test(m)) {
    const ev = parseEvent(message.replace(/^(por favor,?\s*)?(agend\w*|marc\w*)\s+(uma?\s+)?/i, ''));
    act('criar_compromisso', ev);
    return `Pronto! Coloquei na sua agenda. Quer que eu crie uma tarefa de preparação também?${NOTE}`;
  }
  if (/tarefa extra|mais uma tarefa|quero mais/.test(m)) {
    act('criar_tarefa', { title: 'Escreva 3 ideias de conteúdo sobre sua meta', detail: 'Use a aba Amplificar ideias se travar.', minutes: 10 });
    return `Adicionei uma tarefa rápida de 10 minutos na sua lista. 💪${NOTE}`;
  }
  return chat(user, message);
}

export function goalPlan(goal, days) {
  const steps = [
    ['Escreva em 3 linhas como é ter alcançado a meta', 'Seja concreto: números, datas, como você se sente.', 10],
    ['Liste 10 ações possíveis que aproximam você da meta', 'Sem filtro. Depois marque as 3 mais fáceis.', 15],
    ['Execute a ação mais fácil da lista', 'Feito é melhor que perfeito.', 25],
    ['Encontre 1 referência de alguém que já chegou lá', 'Anote 3 coisas que essa pessoa fez.', 20],
    ['Bloqueie 30 min fixos na agenda para essa meta', 'Mesmo horário todos os dias cria hábito.', 5],
    ['Conte sua meta para 1 pessoa', 'Compromisso público aumenta a chance de cumprir.', 10],
    ['Revise a semana e ajuste o plano', 'O que funcionou? O que cortar?', 15],
  ];
  return {
    summary: `Plano de demonstração para "${goal.title}": começar pequeno, criar ritmo diário e revisar semanalmente.`,
    milestones: [
      { title: 'Clareza e primeira ação', by: 'semana 1' },
      { title: 'Rotina diária consolidada', by: 'semana 2-3' },
      { title: 'Primeiro resultado mensurável', by: 'semana 4' },
    ],
    tasks: Array.from({ length: days }, (_, i) => {
      const [title, detail, minutes] = steps[i % steps.length];
      return { day_offset: i, title, detail: `${detail} (demo)`, minutes };
    }),
    first_step: 'Pegue um papel e escreva a meta em uma frase, com data.',
  };
}

export function dailyTasks(user) {
  return {
    message: `Bom dia, ${user.name}! Um passo pequeno hoje vale mais que um plano perfeito amanhã. (modo demonstração)`,
    tasks: [
      { goal_id: null, title: 'Revise suas metas por 2 minutos', detail: 'Leia cada meta e o porquê dela.', minutes: 5 },
      { goal_id: null, title: 'Faça a tarefa mais importante primeiro', detail: 'Antes de abrir redes sociais.', minutes: 30 },
      { goal_id: null, title: 'Publique ou prepare 1 conteúdo', detail: 'Use a aba Legendas para o texto.', minutes: 20 },
    ],
  };
}

export function amplify(idea) {
  return {
    headline: `${idea} — versão ampliada (demo)`,
    angles: [
      { title: 'Versão mínima', description: 'O que dá para lançar em 7 dias com zero custo?' },
      { title: 'Versão premium', description: 'Como seria se cobrasse 10x mais? O que precisaria entregar?' },
      { title: 'Versão comunidade', description: 'E se as pessoas pudessem participar e contribuir?' },
      { title: 'Versão conteúdo', description: 'Documente o processo publicamente e atraia audiência.' },
    ],
    audience: 'Defina quem sente a dor que essa ideia resolve com mais urgência.',
    monetization: ['Produto/serviço direto', 'Assinatura', 'Parcerias e patrocínio'],
    risks: ['Construir sem validar', 'Tentar agradar todo mundo'],
    content_ideas: ['Por que comecei isso', 'Bastidores da semana 1', 'O erro que quase me fez desistir'],
    next_steps: ['Converse com 5 pessoas do público', 'Crie uma página simples', 'Faça uma pré-venda ou lista de espera'],
  };
}

export function captions(topic, platform) {
  const base = topic || 'meu dia';
  return {
    options: [
      { hook: 'Ninguém te conta isso…', caption: `Ninguém te conta isso sobre ${base}.\n\nMas eu vou. 👇\n\n(Escreva aqui sua experiência real.)\n\nSalva pra lembrar depois.`, hashtags: ['#empreendedorismo', '#foco', '#metas'], cta: 'Salve e compartilhe com quem precisa.' },
      { hook: 'Dia 1 de muitos.', caption: `Dia 1 de muitos.\n\nHoje comecei ${base}. Vou mostrar tudo por aqui, erros inclusos.\n\nMe acompanha?`, hashtags: ['#jornada', '#disciplina', '#diario'], cta: 'Comenta "EU" se vai junto.' },
      { hook: '3 coisas que aprendi', caption: `3 coisas que aprendi com ${base}:\n\n1. …\n2. …\n3. …\n\nQual delas você precisava ouvir hoje?`, hashtags: ['#aprendizado', '#crescimento', '#dicas'], cta: 'Responde nos comentários.' },
    ],
    best_time: `${platform || 'Instagram'}: entre 12h-13h ou 19h-21h (teste e compare).`,
    tip: 'Modo demonstração — configure a IA para legendas personalizadas.',
  };
}

export function edit(action, input) {
  if (action === 'tarefas') return input.split(/[.\n]/).map((s) => s.trim()).filter(Boolean).map((s) => `- [ ] ${s}`).join('\n');
  if (action === 'resumir') return input.split(/[.\n]/).map((s) => s.trim()).filter(Boolean).slice(0, 5).map((s) => `- ${s}`).join('\n');
  return `${input}${NOTE}`;
}

export function parseEvent(sentence) {
  const today = localDate();
  const s = sentence.toLowerCase();
  let day = today;
  if (s.includes('depois de amanhã')) day = addDays(today, 2);
  else if (s.includes('amanhã') || s.includes('amanha')) day = addDays(today, 1);
  const time = s.match(/(\d{1,2})(?:h|:)(\d{2})?/);
  const hh = time ? time[1].padStart(2, '0') : '09';
  const mm = time && time[2] ? time[2] : '00';
  return { title: sentence.replace(/\s+(amanhã|hoje|às?|as)\s.*$/i, '').trim() || sentence, start: `${day}T${hh}:${mm}`, end: null, notes: '' };
}

export function review(summary) {
  return `**O que foi bem:** você apareceu e registrou progresso.\n\n**Onde travei:** veja as tarefas não concluídas abaixo.\n\n**Ajuste para a próxima semana:**\n1. Menos tarefas, mais foco\n2. Faça a principal antes das 10h\n3. Revise no domingo\n\n${summary}${NOTE}\n\n_${localDateTime()}_`;
}
