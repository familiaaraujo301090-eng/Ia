// Camada de segurança: cabeçalhos HTTP, verificação de origem (CSRF), limites de requisição,
// validação de endpoints de notificação (evita SSRF) e limites de quantidade por usuário.
import { q } from './db.js';

export const isProd = process.env.NODE_ENV === 'production';

/** Endereço público confiável do app (nunca derivado do cabeçalho Host em produção). */
export function appUrl(req) {
  if (process.env.APP_URL) return process.env.APP_URL.replace(/\/+$/, '');
  if (isProd) return null; // em produção, sem APP_URL não montamos links (evita envenenamento do Host)
  return `${req.protocol}://${req.get('host')}`;
}

// ---------- cabeçalhos ----------
const CSP = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self'",
  "connect-src 'self'",
  "media-src 'self'",
  "worker-src 'self'",
  "manifest-src 'self'",
  "object-src 'none'",
  "base-uri 'none'",
  "form-action 'self'",
  "frame-ancestors 'none'",
  ...(isProd ? ['upgrade-insecure-requests'] : []),
].join('; ');

export function securityHeaders(req, res, next) {
  res.setHeader('Content-Security-Policy', CSP);
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Referrer-Policy', 'same-origin');
  res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
  res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
  res.setHeader('Permissions-Policy', 'camera=(), geolocation=(), payment=(), usb=(), microphone=(self)');
  if (isProd) res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  if (req.path.startsWith('/api/')) res.setHeader('Cache-Control', 'no-store');
  next();
}

/** Em produção atrás de proxy, redireciona HTTP para HTTPS. */
export function forceHttps(req, res, next) {
  if (isProd && process.env.FORCE_HTTPS !== '0' && req.protocol === 'http') {
    const base = process.env.APP_URL ? process.env.APP_URL.replace(/\/+$/, '') : null;
    if (base) return res.redirect(308, base + req.originalUrl);
  }
  next();
}

// ---------- CSRF: só aceita ações vindas do próprio site ----------
const SAFE = new Set(['GET', 'HEAD', 'OPTIONS']);
export function sameOrigin(req, res, next) {
  if (SAFE.has(req.method) || !req.path.startsWith('/api/')) return next();
  // ações precisam ser JSON (formulários de outros sites não conseguem enviar JSON sem permissão)
  if (!req.is('application/json') && Number(req.headers['content-length'] || 0) > 0) {
    return res.status(415).json({ error: 'Formato não suportado.' });
  }
  const origin = req.headers.origin;
  if (origin) {
    const allowed = new Set([`${req.protocol}://${req.get('host')}`]);
    if (process.env.APP_URL) allowed.add(new URL(process.env.APP_URL).origin);
    if (!allowed.has(origin)) return res.status(403).json({ error: 'Origem não permitida.' });
  } else if (req.headers['sec-fetch-site'] && !['same-origin', 'none'].includes(req.headers['sec-fetch-site'])) {
    return res.status(403).json({ error: 'Origem não permitida.' });
  }
  next();
}

// ---------- limites de requisição (janela deslizante em memória) ----------
const buckets = new Map();
export function hit(key, max, windowMs) {
  const now = Date.now();
  const list = (buckets.get(key) || []).filter((t) => now - t < windowMs);
  if (list.length >= max) { buckets.set(key, list); return false; }
  list.push(now);
  buckets.set(key, list);
  return true;
}
export function clearHits(key) { buckets.delete(key); }
// limpeza periódica para a memória não crescer sem limite
setInterval(() => {
  const now = Date.now();
  for (const [k, list] of buckets) if (!list.length || now - list[list.length - 1] > 3600_000) buckets.delete(k);
}, 600_000).unref();

/** Middleware: no máximo `max` requisições por IP em `windowMs`. */
export function limitByIp(name, max, windowMs, msg = 'Muitas requisições. Espere um pouco e tente de novo.') {
  return (req, res, next) => (hit(`${name}|${req.ip}`, max, windowMs) ? next() : res.status(429).json({ error: msg }));
}

// ---------- notificações: só serviços de push conhecidos (evita SSRF) ----------
const PUSH_HOSTS = [
  /^fcm\.googleapis\.com$/, /^android\.googleapis\.com$/, /^updates\.push\.services\.mozilla\.com$/,
  /^[a-z0-9-]+\.push\.services\.mozilla\.com$/, /^web\.push\.apple\.com$/, /^[a-z0-9-]+\.push\.apple\.com$/,
  /^[a-z0-9-]+\.notify\.windows\.com$/, /^wns2-[a-z0-9-]+\.notify\.windows\.com$/,
];
export function isAllowedPushEndpoint(endpoint) {
  let u;
  try { u = new URL(endpoint); } catch { return false; }
  return u.protocol === 'https:' && !u.port && !u.username && !u.password && PUSH_HOSTS.some((re) => re.test(u.hostname));
}

// ---------- limites de quantidade por usuário (evita abuso de armazenamento) ----------
export const QUOTAS = { tasks: 10000, goals: 300, notes: 3000, events: 3000, habits: 100, messages: 20000, push_subs: 10 };
export function underQuota(table, userId) {
  const n = q.get(`SELECT COUNT(*) c FROM ${table} WHERE user_id = ?`, userId).c;
  return n < QUOTAS[table];
}
export function quotaGuard(table) {
  return (req, res, next) => (underQuota(table, req.user.id)
    ? next()
    : res.status(403).json({ error: 'Você atingiu o limite de itens desta área. Apague alguns antigos para continuar.' }));
}
