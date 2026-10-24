"""SQLite ulanish va jadvallarni yaratish."""
import os
from datetime import datetime, timezone

import aiosqlite

import config

_db: aiosqlite.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    full_name   TEXT,
    username    TEXT,
    source      TEXT,
    language    TEXT DEFAULT 'uz',
    is_blocked  INTEGER DEFAULT 0,
    created_at  TEXT
);
CREATE TABLE IF NOT EXISTS courses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT,
    duration    TEXT,
    price       TEXT,
    schedule    TEXT,
    photo_id    TEXT,
    is_active   INTEGER DEFAULT 1,
    sort_order  INTEGER DEFAULT 0,
    created_at  TEXT
);
CREATE TABLE IF NOT EXISTS mentors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT NOT NULL,
    specialty   TEXT,
    experience  TEXT,
    sat_score   TEXT,
    bio         TEXT,
    photo_id    TEXT,
    is_active   INTEGER DEFAULT 1,
    sort_order  INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS course_mentors (
    course_id INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    mentor_id INTEGER REFERENCES mentors(id) ON DELETE CASCADE,
    PRIMARY KEY (course_id, mentor_id)
);
CREATE TABLE IF NOT EXISTS leads (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER REFERENCES users(id),
    course_id     INTEGER REFERENCES courses(id) ON DELETE SET NULL,
    name          TEXT,
    phone         TEXT,
    type          TEXT,
    source        TEXT,
    status        TEXT DEFAULT 'new',
    meeting_at    TEXT,
    reject_reason TEXT,
    created_at    TEXT,
    updated_at    TEXT
);
CREATE TABLE IF NOT EXISTS lead_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id    INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT,
    admin_id   INTEGER,
    changed_at TEXT
);
CREATE TABLE IF NOT EXISTS lead_notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id    INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    admin_id   INTEGER,
    text       TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS sources (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    code       TEXT UNIQUE NOT NULL,
    title      TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS admins (
    telegram_id INTEGER PRIMARY KEY,
    is_super    INTEGER DEFAULT 0,
    added_by    INTEGER,
    added_at    TEXT
);
CREATE TABLE IF NOT EXISTS faq (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    question   TEXT NOT NULL,
    answer     TEXT,
    sort_order INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_leads_status  ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at);
CREATE INDEX IF NOT EXISTS idx_leads_phone   ON leads(phone);
"""


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


async def init_db() -> None:
    global _db
    folder = os.path.dirname(config.DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    _db = await aiosqlite.connect(config.DB_PATH)
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA foreign_keys = ON")
    await _db.executescript(SCHEMA)
    await _db.commit()


async def close_db() -> None:
    if _db is not None:
        await _db.close()


async def fetchone(sql: str, *args) -> dict | None:
    async with _db.execute(sql, args) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def fetchall(sql: str, *args) -> list[dict]:
    async with _db.execute(sql, args) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def fetchval(sql: str, *args):
    async with _db.execute(sql, args) as cur:
        row = await cur.fetchone()
    return row[0] if row else None


async def execute(sql: str, *args) -> int:
    """So'rovni bajaradi va lastrowid qaytaradi."""
    cur = await _db.execute(sql, args)
    await _db.commit()
    return cur.lastrowid


async def snapshot(path: str) -> None:
    """Bazaning izchil nusxasini faylga yozadi (backup uchun)."""
    if os.path.exists(path):
        os.remove(path)
    await _db.execute("VACUUM INTO ?", (path,))
