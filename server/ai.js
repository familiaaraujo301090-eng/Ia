import Anthropic from '@anthropic-ai/sdk';
import { betaZodOutputFormat } from '@anthropic-ai/sdk/helpers/beta/zod';
import { z } from 'zod';
import { q } from './db.js';
import { localDate, localDateTime, addDays, weekday } from './time.js';
import * as demo from './demo.js';

const MODEL = process.env.CLAUDE_MODEL || 'claude-opus-5-5';
// Server-side fallback: if the main model declines, the API retries on a suitable model in the same call.
const FALLBACK = { betas: ['server-side-fallback-2026-07-01'], fallbacks: 'default' };

export const aiEnabled = Boolean(process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_AUTH_TOKEN);
const client = aiEnabled ? new Anthropic() : null;

const BASE_SYSTEM = `Você é o Rumo, um parceiro de vida e de negócios que fala português do Brasil.
Seu papel: ajudar a pessoa a sair do lugar e chegar nas metas dela, um passo pequeno por vez.
Princípios:
- Seja direto, caloroso e prático. Nada de enrolação nem frases genéricas de autoajuda.
- Transforme objetivos grandes em ações pequenas e concretas (5 a 45 minutos), com verbo no imperativo.
- Use o contexto (metas, tarefas, agenda) para personalizar. Cite metas pelo nome quando fizer sentido.
- Quando a pessoa estiver travada, reduza o próximo passo até ele ficar fácil de começar hoje.
- Celebre progresso real, com honestidade. Se ela estiver se sobrecarregando, diga.
- Formate com markdown leve (listas curtas, negrito pontual). Respostas curtas por padrão.`;

/** Snapshot of the user's world that we hand to the model on every call. */
export function userContext(user) {
  const today = localDate();
  const goals = q.all(`SELECT id, title, why, area, deadline FROM goals WHERE user_id = ? AND status = 'ativa' ORDER BY id`, user.id);
  const tasks = q.all(`SELECT title, done, minutes, goal_id FROM tasks WHERE user_id = ? AND due_date = ? ORDER BY id`, user.id, today);
  const events = q.all(
    `SELECT title, start FROM events WHERE user_id = ? AND start >= ? ORDER BY start LIMIT 8`,
    user.id, today
  );
  const doneWeek = q.get(
    `SELECT COUNT(*) c FROM tasks WHERE user_id = ? AND done = 1 AND due_date >= ?`, user.id, addDays(today, -6)
  ).c;
  const lines = [
    `Agora: ${localDateTime()} (${weekday(today)}).`,
    `Pessoa: ${user.name}.${user.about ? ` Sobre: ${user.about}.` : ''}${user.niche ? ` Nicho/área: ${user.niche}.` : ''}`,
    `Tom preferido: ${user.tone || 'motivador e direto'}.`,
    goals.length
      ? `Metas ativas:\n${goals.map((g) => `- [${g.id}] ${g.title}${g.deadline ? ` (prazo ${g.deadline})` : ''}${g.why ? ` — porquê: ${g.why}` : ''}`).join('\n')}`
      : 'Ainda não cadastrou metas.',
    tasks.length
      ? `Tarefas de hoje:\n${tasks.map((t) => `- [${t.done ? 'x' : ' '}] ${t.title} (${t.minutes} min)`).join('\n')}`
      : 'Nenhuma tarefa para hoje ainda.',
    events.length ? `Próximos compromissos:\n${events.map((e) => `- ${e.start.replace('T', ' ')} ${e.title}`).join('\n')}` : 'Agenda livre.',
    `Tarefas concluídas nos últimos 7 dias: ${doneWeek}.`,
  ];
  return lines.join('\n');
}

function system(user, extra = '') {
  // Stable instructions first (cacheable), volatile user context last.
  return [
    { type: 'text', text: BASE_SYSTEM + (extra ? `\n\n${extra}` : ''), cache_control: { type: 'ephemeral' } },
    { type: 'text', text: `<contexto>\n${userContext(user)}\n</contexto>` },
  ];
}

function friendlyError(err) {
  if (err instanceof Anthropic.AuthenticationError) return new Error('Chave da IA inválida. Confira ANTHROPIC_API_KEY.');
  if (err instanceof Anthropic.RateLimitError) return new Error('A IA está ocupada agora. Tente de novo em alguns segundos.');
  if (err instanceof Anthropic.APIConnectionError) return new Error('Sem conexão com a IA no momento.');
  if (err instanceof Anthropic.APIError) return new Error(`A IA retornou um erro (${err.status}).`);
  return err;
}

async function structured(user, schema, prompt, { extra = '', effort = 'medium', maxTokens = 8000 } = {}) {
  try {
    const res = await client.beta.messages.parse({
      model: MODEL,
      max_tokens: maxTokens,
      ...FALLBACK,
      output_config: { effort, format: betaZodOutputFormat(schema) },
      system: system(user, extra),
      messages: [{ role: 'user', content: prompt }],
    });
    if (res.stop_reason === 'refusal') throw new Error('A IA não pôde atender esse pedido. Tente reformular.');
    if (!res.parsed_output) throw new Error('A IA respondeu num formato inesperado. Tente de novo.');
    return res.parsed_output;
  } catch (err) {
    throw friendlyError(err);
  }
}

async function text(user, prompt, { extra = '', effort = 'low', maxTokens = 8000 } = {}) {
  try {
    const res = await client.beta.messages.create({
      model: MODEL,
      max_tokens: maxTokens,
      ...FALLBACK,
      output_config: { effort },
      system: system(user, extra),
      messages: [{ role: 'user', content: prompt }],
    });
    if (res.stop_reason === 'refusal') throw new Error('A IA não pôde atender esse pedido. Tente reformular.');
    return res.content.filter((b) => b.type === 'text').map((b) => b.text).join('').trim();
  } catch (err) {
    throw friendlyError(err);
  }
}

// ---------- Chat (streaming) ----------

export async function chatStream(user, history, onText) {
  if (!aiEnabled) {
    const reply = demo.chat(user, history.at(-1)?.content || '');
    for (const chunk of reply.match(/.{1,24}/gs)) {
      onText(chunk);
      await new Promise((r) => setTimeout(r, 15));
    }
    return reply;
  }
  try {
    const stream = client.beta.messages.stream({
      model: MODEL,
      max_tokens: 16000,
      ...FALLBACK,
      output_config: { effort: 'low' },
      system: system(user, 'Você está no chat. Converse, faça perguntas quando precisar entender melhor, e termine com um próximo passo claro quando fizer sentido.'),
      messages: history,
    });
    stream.on('text', (t) => onText(t));
    const final = await stream.finalMessage();
    if (final.stop_reason === 'refusal') {
      const msg = '\n\n_(Não consegui responder isso. Pode reformular?)_';
      onText(msg);
    }
    return final.content.filter((b) => b.type === 'text').map((b) => b.text).join('');
  } catch (err) {
    throw friendlyError(err);
  }
}

// ---------- Goal plan + daily tasks ----------

const TaskSchema = z.object({
  day_offset: z.number().int().describe('0 = hoje, 1 = amanhã, ...'),
  title: z.string().describe('Ação curta no imperativo'),
  detail: z.string().describe('Como fazer, em 1-2 frases'),
  minutes: z.number().int(),
});

const PlanSchema = z.object({
  summary: z.string().describe('Estratégia em 2-4 frases'),
  milestones: z.array(z.object({ title: z.string(), by: z.string().describe('quando, ex: "semana 2"') })),
  tasks: z.array(TaskSchema),
  first_step: z.string().describe('O menor passo possível para começar nos próximos 10 minutos'),
});

export async function goalPlan(user, goal, days = 7) {
  if (!aiEnabled) return demo.goalPlan(goal, days);
  return structured(
    user,
    PlanSchema,
    `Crie um plano para a meta abaixo.
Meta: ${goal.title}
Por que importa: ${goal.why || '(não informado)'}
Área: ${goal.area || 'geral'}
Prazo: ${goal.deadline || '(sem prazo definido)'}

Regras:
- Gere de 3 a 6 marcos até o prazo.
- Gere tarefas para os próximos ${days} dias (day_offset de 0 a ${days - 1}), 1 a 2 por dia, 5 a 45 minutos cada.
- Tarefas progressivas: começam fáceis e vão construindo. Sem tarefas vagas ("pensar sobre", "se organizar").`,
    { effort: 'medium' }
  );
}

const DailySchema = z.object({
  message: z.string().describe('Mensagem curta de bom dia/motivação personalizada (1-2 frases)'),
  tasks: z.array(z.object({
    goal_id: z.number().int().nullable().describe('id da meta relacionada, ou null'),
    title: z.string(),
    detail: z.string(),
    minutes: z.number().int(),
  })),
});

export async function dailyTasks(user, recent) {
  if (!aiEnabled) return demo.dailyTasks(user);
  return structured(
    user,
    DailySchema,
    `Monte as pequenas tarefas de HOJE (3 a 5 no total, somando no máximo ~90 minutos), cobrindo as metas ativas.
Considere o que já existe hoje e o histórico recente para não repetir e para dar continuidade.
Histórico recente (últimos dias):
${recent || '(sem histórico)'}`,
    { effort: 'medium' }
  );
}

// ---------- Idea amplifier ----------

const AmplifySchema = z.object({
  headline: z.string().describe('A ideia reescrita numa frase forte'),
  angles: z.array(z.object({ title: z.string(), description: z.string() })).describe('4-6 ângulos/versões da ideia'),
  audience: z.string(),
  monetization: z.array(z.string()),
  risks: z.array(z.string()),
  content_ideas: z.array(z.string()).describe('Ideias de posts/vídeos para divulgar'),
  next_steps: z.array(z.string()).describe('3-5 próximos passos concretos'),
});

export async function amplify(user, idea) {
  if (!aiEnabled) return demo.amplify(idea);
  return structured(user, AmplifySchema, `Amplifique esta ideia. Explore ângulos ousados mas viáveis, seja específico.\nIdeia: ${idea}`, { effort: 'medium' });
}

// ---------- Captions (legendas) ----------

const CaptionSchema = z.object({
  options: z.array(z.object({
    hook: z.string().describe('Primeira linha que prende'),
    caption: z.string().describe('Legenda completa pronta para colar'),
    hashtags: z.array(z.string()),
    cta: z.string(),
  })).describe('3 opções com estilos diferentes'),
  best_time: z.string().describe('Melhor horário sugerido para postar'),
  tip: z.string().describe('Dica rápida para o post performar melhor'),
});

export async function captions(user, { topic, platform, style, goal }) {
  if (!aiEnabled) return demo.captions(topic, platform);
  return structured(
    user,
    CaptionSchema,
    `Escreva legendas para um post.
Plataforma: ${platform || 'Instagram'}
Sobre o quê: ${topic}
Estilo desejado: ${style || 'autêntico, humano, sem clichê'}
Objetivo do post: ${goal || 'engajamento e crescimento'}
Use quebras de linha, emojis com moderação, e hashtags relevantes (5 a 12, sem #genéricas demais).`,
    { effort: 'low' }
  );
}

// ---------- Editor ----------

const EDIT_ACTIONS = {
  melhorar: 'Melhore a escrita deste texto: mais claro, fluido e envolvente, mantendo a voz do autor.',
  corrigir: 'Corrija ortografia, gramática e pontuação. Não mude o estilo.',
  resumir: 'Resuma em tópicos curtos com o essencial.',
  expandir: 'Expanda o texto com mais detalhes, exemplos e profundidade, mantendo o tom.',
  roteiro: 'Transforme em um roteiro de vídeo curto (Reels/TikTok, 30-60s): gancho, desenvolvimento, CTA. Indique cenas.',
  post: 'Transforme em um post para redes sociais com gancho forte e CTA.',
  tarefas: 'Extraia uma lista de tarefas acionáveis (checklist markdown "- [ ]").',
  continuar: 'Continue escrevendo a partir de onde o texto parou, no mesmo estilo.',
};
export const editActions = Object.keys(EDIT_ACTIONS);

export async function edit(user, action, input, instruction) {
  const task = instruction ? `Instrução: ${instruction}` : EDIT_ACTIONS[action] || EDIT_ACTIONS.melhorar;
  if (!aiEnabled) return demo.edit(action, input);
  return text(
    user,
    `${task}\nResponda SOMENTE com o texto resultante, em markdown, sem comentários antes ou depois.\n\n<texto>\n${input}\n</texto>`,
    { effort: 'low' }
  );
}

// ---------- Natural-language agenda ----------

const EventSchema = z.object({
  title: z.string(),
  start: z.string().describe('YYYY-MM-DDTHH:mm no fuso local'),
  end: z.string().nullable().describe('YYYY-MM-DDTHH:mm ou null'),
  notes: z.string(),
});

export async function parseEvent(user, sentence) {
  if (!aiEnabled) return demo.parseEvent(sentence);
  return structured(
    user,
    EventSchema,
    `Converta em um compromisso de agenda. Agora é ${localDateTime()} (${weekday(localDate())}). Se não houver horário, use 09:00. Se não houver duração, end = null.\nFrase: ${sentence}`,
    { effort: 'low', maxTokens: 2000 }
  );
}

// ---------- Weekly review ----------

export async function weeklyReview(user, summary) {
  if (!aiEnabled) return demo.review(summary);
  return text(
    user,
    `Faça uma revisão da minha semana com base nos dados abaixo. Estrutura: **O que foi bem**, **Onde travei**, **Ajuste para a próxima semana** (3 ações), e uma frase final de incentivo honesta.\n\n${summary}`,
    { effort: 'medium' }
  );
}
