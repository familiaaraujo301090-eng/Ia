import crypto from 'node:crypto';
import { q } from './db.js';

const SESSION_DAYS = 30;

export function hashPassword(password) {
  const salt = crypto.randomBytes(16).toString('hex');
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return `${salt}:${hash}`;
}

export function verifyPassword(password, stored) {
  const [salt, hash] = String(stored).split(':');
  if (!salt || !hash) return false;
  const test = crypto.scryptSync(password, salt, 64);
  const known = Buffer.from(hash, 'hex');
  return known.length === test.length && crypto.timingSafeEqual(known, test);
}

export function createSession(userId) {
  const token = crypto.randomBytes(32).toString('hex');
  const expires = new Date(Date.now() + SESSION_DAYS * 864e5).toISOString();
  q.run('INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)', token, userId, expires);
  return { token, expires };
}

export function destroySession(token) {
  if (token) q.run('DELETE FROM sessions WHERE token = ?', token);
}

function readCookie(req, name) {
  const header = req.headers.cookie || '';
  for (const part of header.split(';')) {
    const [k, ...v] = part.trim().split('=');
    if (k === name) return decodeURIComponent(v.join('='));
  }
  return null;
}

export function sessionToken(req) {
  const auth = req.headers.authorization || '';
  if (auth.startsWith('Bearer ')) return auth.slice(7);
  return readCookie(req, 'rumo_session');
}

export function setSessionCookie(res, token, expires) {
  const secure = process.env.NODE_ENV === 'production' ? '; Secure' : '';
  res.setHeader(
    'Set-Cookie',
    `rumo_session=${token}; HttpOnly; Path=/; SameSite=Lax; Expires=${new Date(expires).toUTCString()}${secure}`
  );
}

export function clearSessionCookie(res) {
  res.setHeader('Set-Cookie', 'rumo_session=; HttpOnly; Path=/; SameSite=Lax; Max-Age=0');
}

export function requireUser(req, res, next) {
  const token = sessionToken(req);
  if (!token) return res.status(401).json({ error: 'Faça login para continuar.' });
  const row = q.get(
    `SELECT u.id, u.name, u.email, u.about, u.niche, u.tone, s.expires_at
       FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?`,
    token
  );
  if (!row || new Date(row.expires_at) < new Date()) {
    destroySession(token);
    return res.status(401).json({ error: 'Sessão expirada. Entre novamente.' });
  }
  delete row.expires_at;
  req.user = row;
  req.token = token;
  next();
}
