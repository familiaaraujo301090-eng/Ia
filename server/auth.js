import crypto from 'node:crypto';
import { q } from './db.js';
import { localDate } from './time.js';

const SESSION_DAYS = 30;
export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 200; // evita travar o servidor com senhas gigantes

// ---------- senhas ----------
// Formato atual: scrypt$N$r$p$salt$hash. Formato antigo (salt:hash) continua aceito e é
// atualizado automaticamente no próximo login (ver needsRehash).
const SCRYPT = { N: 2 ** 15, r: 8, p: 1, maxmem: 64 * 1024 * 1024 };

export function validPassword(pw) {
  return typeof pw === 'string' && pw.length >= PASSWORD_MIN && pw.length <= PASSWORD_MAX;
}

export function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64, SCRYPT).toString('hex');
  return `scrypt$${SCRYPT.N}$${SCRYPT.r}$${SCRYPT.p}$${salt}$${hash}`;
}

export function verifyPassword(password, stored) {
  if (typeof password !== 'string' || password.length > PASSWORD_MAX) return false;
  const s = String(stored || '');
  let test;
  let known;
  if (s.startsWith('scrypt$')) {
    const [, N, r, p, salt, hash] = s.split('$');
    known = Buffer.from(hash || '', 'hex');
    test = crypto.scryptSync(password, salt, 64, { N: Number(N), r: Number(r), p: Number(p), maxmem: SCRYPT.maxmem });
  } else {
    const [salt, hash] = s.split(':');
    if (!salt || !hash) return false;
    known = Buffer.from(hash, 'hex');
    test = crypto.scryptSync(password, salt, 64);
  }
  return known.length === test.length && crypto.timingSafeEqual(known, test);
}

export const needsRehash = (stored) => !String(stored).startsWith(`scrypt$${SCRYPT.N}$${SCRYPT.r}$${SCRYPT.p}$`);

// Hash usado quando o e-mail não existe, para o tempo de resposta não revelar quem tem conta.
const DUMMY_HASH = hashPassword(crypto.randomBytes(16).toString('hex'));
export function verifyDummy(password) { verifyPassword(String(password || '').slice(0, PASSWORD_MAX), DUMMY_HASH); }

// ---------- sessões ----------
// O banco guarda só o hash do token: se o banco vazar, as sessões não podem ser usadas.
const tokenHash = (t) => crypto.createHash('sha256').update(String(t)).digest('hex');

export function createSession(userId) {
  const token = crypto.randomBytes(32).toString('base64url');
  const expires = new Date(Date.now() + SESSION_DAYS * 864e5).toISOString();
  q.run('INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)', tokenHash(token), userId, expires);
  return { token, expires };
}

export function destroySession(token) {
  if (token) q.run('DELETE FROM sessions WHERE token = ?', tokenHash(token));
}

/** Encerra todas as sessões do usuário, exceto (opcionalmente) a atual. */
export function destroyOtherSessions(userId, keepToken) {
  if (keepToken) q.run('DELETE FROM sessions WHERE user_id = ? AND token != ?', userId, tokenHash(keepToken));
  else q.run('DELETE FROM sessions WHERE user_id = ?', userId);
}

export function purgeExpiredSessions() {
  q.run('DELETE FROM sessions WHERE expires_at < ?', new Date().toISOString());
  q.run('DELETE FROM password_resets WHERE expires_at < ? OR used = 1', new Date(Date.now() - 864e5).toISOString());
}

const isProd = () => process.env.NODE_ENV === 'production';
// Em produção o prefixo __Host- obriga HTTPS, Path=/ e nenhum domínio (cookie não vaza para subdomínios).
const COOKIE = () => (isProd() ? '__Host-rumo_session' : 'rumo_session');

function readCookie(req, name) {
  const header = req.headers.cookie || '';
  for (const part of header.split(';')) {
    const [k, ...v] = part.trim().split('=');
    if (k === name) {
      try { return decodeURIComponent(v.join('=')); } catch { return null; }
    }
  }
  return null;
}

export function sessionToken(req) {
  const auth = req.headers.authorization || '';
  const t = auth.startsWith('Bearer ') ? auth.slice(7) : readCookie(req, COOKIE());
  return t && t.length <= 200 ? t : null;
}

export function setSessionCookie(res, token, expires) {
  const secure = isProd() ? '; Secure' : '';
  res.setHeader('Set-Cookie', `${COOKIE()}=${token}; HttpOnly; Path=/; SameSite=Lax; Expires=${new Date(expires).toUTCString()}${secure}`);
}

export function clearSessionCookie(res) {
  const secure = isProd() ? '; Secure' : '';
  res.setHeader('Set-Cookie', `${COOKIE()}=; HttpOnly; Path=/; SameSite=Lax; Max-Age=0${secure}`);
}

// ---------- administração ----------
// Admin é uma marca no banco, ativada só por quem conhece ADMIN_SECRET (variável do servidor).
// Não depende do e-mail, porque e-mails não são verificados e poderiam ser cadastrados por outra pessoa.
export function adminSecretMatches(given) {
  const secret = process.env.ADMIN_SECRET || '';
  if (secret.length < 20 || typeof given !== 'string') return false;
  const a = crypto.createHash('sha256').update(given).digest();
  const b = crypto.createHash('sha256').update(secret).digest();
  return crypto.timingSafeEqual(a, b);
}

export function requireUser(req, res, next) {
  const token = sessionToken(req);
  if (!token) return res.status(401).json({ error: 'Faça login para continuar.' });
  const row = q.get(
    `SELECT u.id, u.name, u.email, u.about, u.niche, u.tone, u.role, u.daily_minutes, u.onboarded, u.plan,
            u.reminders, u.reminder_time, u.last_seen, u.is_admin, s.expires_at
       FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?`,
    tokenHash(token)
  );
  if (!row || new Date(row.expires_at) < new Date()) {
    destroySession(token);
    return res.status(401).json({ error: 'Sessão expirada. Entre novamente.' });
  }
  delete row.expires_at;
  const today = localDate();
  if (row.last_seen !== today) q.run('UPDATE users SET last_seen = ? WHERE id = ?', today, row.id);
  row.is_admin = Boolean(row.is_admin);
  req.user = row;
  req.token = token;
  next();
}
