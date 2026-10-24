import config
from database.db import execute, fetchall, now

_cache: set[int] = set()


async def _refresh() -> None:
    rows = await fetchall("SELECT telegram_id FROM admins")
    _cache.clear()
    _cache.update(r["telegram_id"] for r in rows)


async def seed() -> None:
    """ADMIN_IDS dagi adminlarni bazaga yozadi; birinchisi — bosh admin."""
    for tg_id in config.ADMIN_IDS:
        await execute(
            "INSERT OR IGNORE INTO admins (telegram_id, is_super, added_by, added_at) VALUES (?, 0, NULL, ?)",
            tg_id, now(),
        )
    await execute("UPDATE admins SET is_super = (telegram_id = ?)", config.SUPER_ADMIN_ID)
    await _refresh()


def is_admin(tg_id: int) -> bool:
    return tg_id in _cache


def is_super(tg_id: int) -> bool:
    return tg_id == config.SUPER_ADMIN_ID


def all_ids() -> list[int]:
    return sorted(_cache)


async def list_admins() -> list[dict]:
    return await fetchall("SELECT * FROM admins ORDER BY is_super DESC, added_at")


async def add_admin(tg_id: int, added_by: int) -> None:
    await execute(
        "INSERT OR IGNORE INTO admins (telegram_id, is_super, added_by, added_at) VALUES (?, 0, ?, ?)",
        tg_id, added_by, now(),
    )
    await _refresh()


async def remove_admin(tg_id: int) -> None:
    await execute("DELETE FROM admins WHERE telegram_id = ? AND is_super = 0", tg_id)
    await _refresh()
