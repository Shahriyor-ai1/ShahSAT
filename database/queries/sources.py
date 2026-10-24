from database.db import execute, fetchall, fetchone, now

DIRECT = "To'g'ridan-to'g'ri"


async def list_sources() -> list[dict]:
    return await fetchall("SELECT * FROM sources ORDER BY id")


async def get_source(source_id: int) -> dict | None:
    return await fetchone("SELECT * FROM sources WHERE id = ?", source_id)


async def add_source(code: str, title: str) -> int:
    return await execute(
        "INSERT INTO sources (code, title, created_at) VALUES (?, ?, ?)", code, title, now()
    )


async def delete_source(source_id: int) -> None:
    await execute("DELETE FROM sources WHERE id = ?", source_id)


async def title_of(code: str | None) -> str:
    """Manba kodini o'qiladigan nomga aylantiradi."""
    if not code:
        return DIRECT
    row = await fetchone("SELECT title FROM sources WHERE code = ?", code)
    return row["title"] if row else code
