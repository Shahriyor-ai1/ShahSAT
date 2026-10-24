from aiogram.types import User

from database.db import execute, fetchall, fetchone, fetchval, now


async def upsert_user(tg: User, source: str | None) -> dict:
    """Foydalanuvchini yozadi yoki yangilaydi. Deep-link parametri bo'lsa manba yangilanadi."""
    row = await get_user(tg.id)
    if row is None:
        await execute(
            "INSERT INTO users (telegram_id, full_name, username, source, created_at) VALUES (?, ?, ?, ?, ?)",
            tg.id, tg.full_name, tg.username, source, now(),
        )
    else:
        await execute(
            "UPDATE users SET full_name = ?, username = ?, is_blocked = 0, source = COALESCE(?, source) "
            "WHERE telegram_id = ?",
            tg.full_name, tg.username, source, tg.id,
        )
    return await get_user(tg.id)


async def get_user(telegram_id: int) -> dict | None:
    return await fetchone("SELECT * FROM users WHERE telegram_id = ?", telegram_id)


async def active_ids() -> list[int]:
    rows = await fetchall("SELECT telegram_id FROM users WHERE is_blocked = 0")
    return [r["telegram_id"] for r in rows]


async def set_blocked(telegram_id: int) -> None:
    await execute("UPDATE users SET is_blocked = 1 WHERE telegram_id = ?", telegram_id)


async def count_users(since: str | None = None) -> int:
    if since:
        return await fetchval("SELECT COUNT(*) FROM users WHERE created_at >= ?", since)
    return await fetchval("SELECT COUNT(*) FROM users")
