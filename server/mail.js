// Envio de e-mail (recuperação de senha). Configure SMTP_URL, ex:
//   smtps://usuario:senha@smtp.seuprovedor.com:465
// Sem SMTP_URL, o link é escrito no log do servidor (útil em testes).
import nodemailer from 'nodemailer';

let transport = null;
export const mailEnabled = Boolean(process.env.SMTP_URL);

export async function sendMail({ to, subject, text, html }) {
  if (!mailEnabled) {
    console.log(`[e-mail não configurado] Para: ${to}\nAssunto: ${subject}\n${text}`);
    return false;
  }
  transport ||= nodemailer.createTransport(process.env.SMTP_URL);
  await transport.sendMail({ from: process.env.MAIL_FROM || 'Rumo <no-reply@rumo.app>', to, subject, text, html });
  return true;
}
