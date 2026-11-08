import { DatabaseSync } from 'node:sqlite';
import fs from 'node:fs';
import path from 'node:path';

const DB_PATH = process.env.DB_PATH || path.resolve('data', 'rumo.db');
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

export const db = new DatabaseSync(DB_PATH);
db.exec('PRAGMA journal_mode = WAL; PRAGMA foreign_keys = ON;');

db.exec(`
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  pass_hash TEXT NOT NULL,
  about TEXT DEFAULT '',
  niche TEXT DEFAULT '',
  tone TEXT DEFAULT 'motivador e direto',
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS goals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  why TEXT DEFAULT '',
  area TEXT DEFAULT 'geral',
  deadline TEXT,
  status TEXT DEFAULT 'ativa',
  plan TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  goal_id INTEGER REFERENCES goals(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  detail TEXT DEFAULT '',
  due_date TEXT NOT NULL,
  minutes INTEGER DEFAULT 15,
  done INTEGER DEFAULT 0,
  done_at TEXT,
  source TEXT DEFAULT 'manual',
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tasks_user_date ON tasks(user_id, due_date);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  start TEXT NOT NULL,
  end TEXT,
  notes TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_events_user_start ON events(user_id, start);
CREATE TABLE IF NOT EXISTS notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL DEFAULT 'Sem título',
  content TEXT DEFAULT '',
  kind TEXT DEFAULT 'nota',
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS checkins (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day TEXT NOT NULL,
  mood INTEGER,
  note TEXT DEFAULT '',
  UNIQUE(user_id, day)
);
`);

// Migrações simples: adiciona colunas novas em bancos já existentes.
const userCols = db.prepare('PRAGMA table_info(users)').all().map((c) => c.name);
for (const [col, def] of [['onboarded', 'INTEGER DEFAULT 0'], ['role', "TEXT DEFAULT ''"], ['daily_minutes', 'INTEGER DEFAULT 30']]) {
  if (!userCols.includes(col)) db.exec(`ALTER TABLE users ADD COLUMN ${col} ${def}`);
}

export const q = {
  get: (sql, ...p) => db.prepare(sql).get(...p),
  all: (sql, ...p) => db.prepare(sql).all(...p),
  run: (sql, ...p) => db.prepare(sql).run(...p),
};
