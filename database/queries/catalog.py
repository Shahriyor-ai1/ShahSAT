"""Kurslar, mentorlar va FAQ uchun umumiy CRUD so'rovlari."""
from database.db import execute, fetchall, fetchone, now

TABLES = {
    "course": ("courses", {"title", "description", "duration", "price", "schedule", "photo_id", "sort_order"}),
    "mentor": ("mentors", {"full_name", "specialty", "experience", "sat_score", "bio", "photo_id", "sort_order"}),
    "faq": ("faq", {"question", "answer", "sort_order"}),
}


def _table(ent: str) -> tuple[str, set[str]]:
    return TABLES[ent]


async def list_items(ent: str, active_only: bool = False) -> list[dict]:
    table, _ = _table(ent)
    where = " WHERE is_active = 1" if active_only and ent != "faq" else ""
    return await fetchall(f"SELECT * FROM {table}{where} ORDER BY sort_order, id")


async def get_item(ent: str, item_id: int) -> dict | None:
    table, _ = _table(ent)
    return await fetchone(f"SELECT * FROM {table} WHERE id = ?", item_id)


async def add_item(ent: str, values: dict) -> int:
    table, allowed = _table(ent)
    values = {k: v for k, v in values.items() if k in allowed}
    if ent == "course":
        values["created_at"] = now()
    cols = ", ".join(values)
    marks = ", ".join("?" for _ in values)
    return await execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", *values.values())


async def update_field(ent: str, item_id: int, field: str, value) -> None:
    table, allowed = _table(ent)
    if field not in allowed:
        raise ValueError(f"Noto'g'ri maydon: {field}")
    await execute(f"UPDATE {table} SET {field} = ? WHERE id = ?", value, item_id)


async def toggle_active(ent: str, item_id: int) -> None:
    table, _ = _table(ent)
    await execute(f"UPDATE {table} SET is_active = 1 - is_active WHERE id = ?", item_id)


async def delete_item(ent: str, item_id: int) -> None:
    table, _ = _table(ent)
    await execute(f"DELETE FROM {table} WHERE id = ?", item_id)


# --- Kurs <-> mentor bog'lanishi ---

async def mentors_of_course(course_id: int, active_only: bool = False) -> list[dict]:
    extra = " AND m.is_active = 1" if active_only else ""
    return await fetchall(
        "SELECT m.* FROM mentors m JOIN course_mentors cm ON cm.mentor_id = m.id "
        f"WHERE cm.course_id = ?{extra} ORDER BY m.sort_order, m.id",
        course_id,
    )


async def courses_of_mentor(mentor_id: int, active_only: bool = False) -> list[dict]:
    extra = " AND c.is_active = 1" if active_only else ""
    return await fetchall(
        "SELECT c.* FROM courses c JOIN course_mentors cm ON cm.course_id = c.id "
        f"WHERE cm.mentor_id = ?{extra} ORDER BY c.sort_order, c.id",
        mentor_id,
    )


async def toggle_course_mentor(course_id: int, mentor_id: int) -> None:
    row = await fetchone(
        "SELECT 1 FROM course_mentors WHERE course_id = ? AND mentor_id = ?", course_id, mentor_id
    )
    if row:
        await execute("DELETE FROM course_mentors WHERE course_id = ? AND mentor_id = ?", course_id, mentor_id)
    else:
        await execute("INSERT INTO course_mentors (course_id, mentor_id) VALUES (?, ?)", course_id, mentor_id)
