// Notificações no celular/computador (Web Push). Funciona sem conta externa:
// as chaves VAPID são geradas uma vez e guardadas no banco (ou vêm de VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY).
import * as webpush from 'web-push';
import { q, getSetting, setSetting } from './db.js';

let ready = false;
export function vapidPublicKey() {
  let pub = process.env.VAPID_PUBLIC_KEY || getSetting('vapid_public');
  let priv = process.env.VAPID_PRIVATE_KEY || getSetting('vapid_private');
  if (!pub || !priv) {
    const keys = webpush.generateVAPIDKeys();
    pub = keys.publicKey;
    priv = keys.privateKey;
    setSetting('vapid_public', pub);
    setSetting('vapid_private', priv);
  }
  if (!ready) {
    webpush.setVapidDetails(process.env.VAPID_SUBJECT || 'mailto:contato@rumo.app', pub, priv);
    ready = true;
  }
  return pub;
}

export function saveSubscription(userId, sub) {
  if (!sub?.endpoint || !sub?.keys?.p256dh || !sub?.keys?.auth) throw new Error('Inscrição inválida.');
  q.run(`INSERT INTO push_subs (user_id, endpoint, p256dh, auth) VALUES (?, ?, ?, ?)
         ON CONFLICT(endpoint) DO UPDATE SET user_id = excluded.user_id, p256dh = excluded.p256dh, auth = excluded.auth`,
    userId, String(sub.endpoint).slice(0, 1000), String(sub.keys.p256dh).slice(0, 300), String(sub.keys.auth).slice(0, 300));
}

export function removeSubscription(userId, endpoint) {
  q.run('DELETE FROM push_subs WHERE user_id = ? AND endpoint = ?', userId, endpoint);
}

/** Envia para todos os aparelhos do usuário. Retorna quantos receberam. */
export async function pushToUser(userId, payload) {
  vapidPublicKey();
  const subs = q.all('SELECT * FROM push_subs WHERE user_id = ?', userId);
  let sent = 0;
  for (const s of subs) {
    try {
      await webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, JSON.stringify(payload), { TTL: 6 * 3600 });
      sent++;
    } catch (err) {
      // aparelho desinscrito ou expirado: remove
      if (err.statusCode === 404 || err.statusCode === 410) q.run('DELETE FROM push_subs WHERE id = ?', s.id);
    }
  }
  return sent;
}
